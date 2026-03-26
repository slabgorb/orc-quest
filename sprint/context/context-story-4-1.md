---
parent: context-epic-4.md
---

# Story 4-1: Daemon Client -- HTTP Client for sidequest-daemon Render/TTS/Audio Endpoints

## Business Context

Every media operation in SideQuest goes through the Python daemon -- image rendering,
voice synthesis, and audio track selection. The Rust server needs a typed HTTP client
that speaks the daemon's API contract. In Python, this is spread across multiple modules
in `sq-2/sidequest/media/` with ad-hoc `aiohttp` calls, inconsistent error handling,
and no shared retry logic. The Rust port consolidates all daemon communication into a
single `DaemonClient` struct with typed request/response pairs per endpoint.

This is the foundation for the entire media epic. Stories 4-2 through 4-12 all depend
on this client to reach the daemon. Getting the contract right here means every
downstream story has a reliable, tested transport layer.

**Python source:** `sq-2/sidequest/media/client.py`, `sq-2/sidequest/media/render.py`,
`sq-2/sidequest/media/voice.py`, `sq-2/sidequest/media/audio.py`
**ADRs:** ADR-006 (graceful degradation), ADR-023 (daemon boundary)
**Depends on:** Story 2-5 (orchestrator turn loop -- daemon client is called post-narration)

## Technical Approach

### DaemonClient Struct

```rust
use reqwest::Client;
use url::Url;
use std::time::Duration;

pub struct DaemonClient {
    http: Client,
    base_url: Url,
    render_timeout: Duration,
    tts_timeout: Duration,
    audio_timeout: Duration,
}

impl DaemonClient {
    pub fn new(base_url: Url, config: DaemonConfig) -> Self {
        let http = Client::builder()
            .timeout(config.default_timeout)
            .build()
            .expect("HTTP client build");
        Self {
            http,
            base_url,
            render_timeout: config.render_timeout,
            tts_timeout: config.tts_timeout,
            audio_timeout: config.audio_timeout,
        }
    }
}
```

### Typed Endpoint Methods

Each daemon endpoint gets its own request/response pair:

```rust
#[derive(Serialize)]
pub struct RenderRequest {
    pub prompt: String,
    pub art_style: String,
    pub model: String,
    pub width: u32,
    pub height: u32,
}

#[derive(Deserialize)]
pub struct RenderResponse {
    pub image_url: String,
    pub image_bytes: Option<Vec<u8>>,
    pub generation_ms: u64,
}

impl DaemonClient {
    pub async fn render(&self, req: &RenderRequest) -> Result<RenderResponse, DaemonError> {
        let url = self.base_url.join("/render")?;
        let resp = self.http.post(url)
            .json(req)
            .timeout(self.render_timeout)
            .send()
            .await?;
        self.handle_response(resp).await
    }

    pub async fn synthesize(&self, req: &TtsRequest) -> Result<TtsResponse, DaemonError> { .. }
    pub async fn select_track(&self, req: &AudioRequest) -> Result<AudioResponse, DaemonError> { .. }
}
```

### Error Handling and Retry

Python silently swallows daemon errors and falls back to text-only. Rust makes this
explicit with `DaemonError` and a retry wrapper:

```rust
#[derive(Debug, thiserror::Error)]
pub enum DaemonError {
    #[error("daemon unreachable: {0}")]
    Unreachable(#[from] reqwest::Error),
    #[error("daemon returned {status}: {body}")]
    HttpError { status: u16, body: String },
    #[error("daemon timeout after {duration:?}")]
    Timeout { duration: Duration },
    #[error("invalid response: {0}")]
    Deserialize(#[from] serde_json::Error),
}

impl DaemonClient {
    async fn with_retry<F, T>(&self, max_retries: u32, f: F) -> Result<T, DaemonError>
    where
        F: Fn() -> Pin<Box<dyn Future<Output = Result<T, DaemonError>> + Send>>,
    {
        let mut last_err = None;
        for attempt in 0..=max_retries {
            if attempt > 0 {
                tokio::time::sleep(Duration::from_millis(100 * 2u64.pow(attempt))).await;
            }
            match f().await {
                Ok(val) => return Ok(val),
                Err(e) => last_err = Some(e),
            }
        }
        Err(last_err.unwrap())
    }
}
```

### Configuration from Genre Pack

Timeouts and endpoint behavior are configurable per genre pack, but the client itself
reads from a flat `DaemonConfig`:

```rust
pub struct DaemonConfig {
    pub base_url: Url,
    pub default_timeout: Duration,
    pub render_timeout: Duration,
    pub tts_timeout: Duration,
    pub audio_timeout: Duration,
    pub max_retries: u32,
}
```

## Scope Boundaries

**In scope:**
- `DaemonClient` struct with `render()`, `synthesize()`, `select_track()` methods
- Typed request/response structs for each endpoint
- `DaemonError` enum with timeout, HTTP error, deserialization variants
- Exponential backoff retry wrapper
- `DaemonConfig` for timeouts and base URL
- Unit tests with mock HTTP server (`wiremock`)

**Out of scope:**
- Daemon health monitoring / readiness probes (deferred)
- Connection pooling tuning (reqwest defaults are fine for now)
- Streaming TTS response (that's story 4-8)
- Actual daemon endpoint implementation (daemon is already built)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Render endpoint | `DaemonClient::render()` sends POST /render with correct JSON, deserializes response |
| TTS endpoint | `DaemonClient::synthesize()` sends POST /tts with voice preset and text |
| Audio endpoint | `DaemonClient::select_track()` sends POST /audio with mood and config |
| Timeout handling | Requests exceeding configured timeout return `DaemonError::Timeout` |
| Retry logic | Transient failures retry with exponential backoff up to max_retries |
| HTTP error mapping | Non-2xx status codes produce `DaemonError::HttpError` with status and body |
| Config-driven | All timeouts and base URL come from `DaemonConfig`, not hardcoded |
| Mock tests | All three endpoints tested against wiremock with success, timeout, and error cases |
| Non-fatal | Callers can match on `DaemonError` and gracefully degrade to text-only |
