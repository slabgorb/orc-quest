---
parent: context-epic-3.md
---

# Story 3-6: Watcher WebSocket Endpoint — /ws/watcher Streaming Filtered Telemetry to Viewers

## Business Context

Stories 3-1 through 3-5 build the internal telemetry pipeline: structured tracing spans
on agent calls, TurnRecord flow through the validator, and subsystem exercise tracking.
All of that data is emitted as tracing events — useful in server logs, but invisible to
a connected viewer during a live playtest.

This story creates the output side: a `/ws/watcher` WebSocket endpoint that streams
enriched telemetry events to any connected diagnostic viewer. This is the transport layer
that makes the watcher pipeline observable in real time.

ADR-031 specifies `/ws/watcher` as a separate endpoint from `/ws` (game traffic). Game
clients never see diagnostic data; watcher viewers never see raw game messages. The two
streams are completely independent.

**Python source:** No equivalent. Python debugging is printf-style in the server console.
**Depends on:** Story 3-1 (structured tracing spans on agent calls)

## Technical Approach

### Architecture: Bridging Tracing to WebSocket

The key design question is how tracing events reach the WebSocket. Three options exist:

1. Custom `tracing::Layer` that forwards to a broadcast channel
2. Validator task explicitly sends to a broadcast channel alongside tracing
3. Both — Layer for agent spans, validator for validation events

**This story uses option 3.** A custom `tracing::Layer` captures game-relevant spans and
forwards them to a `tokio::sync::broadcast` channel. The validator task (from 3-2) also
sends its own events (validation warnings, exercise summaries) to the same channel. The
WebSocket handler subscribes to the broadcast channel and streams to connected clients.

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Agent spans  │────▶│  WatcherLayer   │────▶│                 │
│ (tracing)    │     │  (tracing::Layer)│     │  broadcast::    │     ┌──────────┐
└──────────────┘     └─────────────────┘     │  Sender<        │────▶│ /ws/     │
                                             │  WatcherEvent>  │     │ watcher  │
┌──────────────┐                             │                 │     └──────────┘
│ Validator    │─────────────────────────────▶│                 │
│ task (3-2)   │                             └─────────────────┘
└──────────────┘
```

### WatcherEvent Type

```rust
use serde::Serialize;
use std::collections::HashMap;

#[derive(Clone, Debug, Serialize)]
pub struct WatcherEvent {
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub component: String,
    pub event_type: WatcherEventType,
    pub severity: Severity,
    pub fields: HashMap<String, serde_json::Value>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WatcherEventType {
    AgentSpanOpen,
    AgentSpanClose,
    ValidationWarning,
    SubsystemExerciseSummary,
    CoverageGap,
    JsonExtractionResult,
    StateTransition,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Info,
    Warn,
    Error,
}
```

### Custom Tracing Layer

The `WatcherLayer` implements `tracing::Layer` and filters for game-relevant spans:

```rust
use tokio::sync::broadcast;
use tracing::Subscriber;
use tracing_subscriber::Layer;

const WATCHED_COMPONENTS: &[&str] = &[
    "intent_router",
    "agent",
    "json_extractor",
    "state",
    "trope_engine",
    "context_builder",
    "watcher",
];

pub struct WatcherLayer {
    tx: broadcast::Sender<WatcherEvent>,
}

impl WatcherLayer {
    pub fn new(tx: broadcast::Sender<WatcherEvent>) -> Self {
        Self { tx }
    }
}

impl<S> Layer<S> for WatcherLayer
where
    S: Subscriber + for<'a> tracing_subscriber::registry::LookupSpan<'a>,
{
    fn on_new_span(
        &self,
        attrs: &tracing::span::Attributes<'_>,
        _id: &tracing::span::Id,
        _ctx: tracing_subscriber::layer::Context<'_, S>,
    ) {
        // Extract component field, check against WATCHED_COMPONENTS
        // If match, build WatcherEvent and send on broadcast channel
        // Ignore send errors — no receivers means no overhead
        let _ = self.tx.send(event);
    }

    fn on_close(
        &self,
        id: tracing::span::Id,
        ctx: tracing_subscriber::layer::Context<'_, S>,
    ) {
        // Emit AgentSpanClose with duration
    }
}
```

### Event Filtering

Only spans with a `component` field matching the watched list are forwarded:

| Component | Source |
|-----------|--------|
| `intent_router` | Intent classification spans |
| `agent` | All 8 agent type invocations |
| `json_extractor` | LLM response JSON extraction |
| `state` | Game state mutations |
| `trope_engine` | Trope evaluation |
| `context_builder` | Context assembly for LLM calls |
| `watcher` | Validator-emitted events (exercise summaries, gap warnings) |

Full `GameSnapshot` payloads are **not** sent — they are too large for a diagnostic stream.
Instead, `TurnRecord` metadata is sent: `turn_id`, `intent`, `agent_name`, `duration`,
`fields_changed`, and `validation_warnings`.

### WebSocket Endpoint

```rust
use axum::{
    extract::{State, WebSocketUpgrade},
    response::IntoResponse,
    routing::get,
    Router,
};

pub fn watcher_router() -> Router<Arc<AppState>> {
    Router::new().route("/ws/watcher", get(watcher_ws_handler))
}

async fn watcher_ws_handler(
    ws: WebSocketUpgrade,
    State(app): State<Arc<AppState>>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_watcher_connection(socket, app))
}

async fn handle_watcher_connection(
    mut socket: WebSocket,
    app: Arc<AppState>,
) {
    let mut rx = app.watcher_tx.subscribe();

    while let Ok(event) = rx.recv().await {
        let json = serde_json::to_string(&event).unwrap();
        if socket.send(Message::Text(json)).await.is_err() {
            break; // Client disconnected
        }
    }
}
```

### Broadcast Channel Setup

The broadcast channel is created at server startup and stored in `AppState`:

```rust
pub struct AppState {
    // ... existing fields from 2-1 ...
    pub watcher_tx: broadcast::Sender<WatcherEvent>,
}

impl AppState {
    pub fn new(/* ... */) -> Self {
        let (watcher_tx, _) = broadcast::channel(256); // buffer 256 events
        Self {
            // ...
            watcher_tx,
        }
    }
}
```

The `_rx` receiver is immediately dropped. New receivers are created per-connection via
`watcher_tx.subscribe()`. When no viewers are connected, `send()` returns an error
(no receivers), which is intentionally ignored — zero overhead when nobody is watching.

### Router Integration

The watcher route is added alongside the existing game WebSocket and REST routes:

```rust
let app = Router::new()
    .route("/ws", get(ws_handler))
    .route("/api/genres", get(list_genres))
    .merge(watcher_router())  // adds /ws/watcher
    .with_state(app_state);
```

### Tracing Layer Registration

The `WatcherLayer` is added to the tracing subscriber stack at startup:

```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

let (watcher_tx, _) = broadcast::channel(256);

tracing_subscriber::registry()
    .with(tracing_subscriber::fmt::layer())     // stdout logging
    .with(WatcherLayer::new(watcher_tx.clone())) // watcher broadcast
    .init();
```

## Scope Boundaries

**In scope:**
- `/ws/watcher` WebSocket endpoint on the axum router
- `tokio::sync::broadcast` channel for fan-out to multiple viewers
- `WatcherEvent` struct with timestamp, component, event_type, severity, fields
- Custom `tracing::Layer` filtering game-relevant spans to the broadcast channel
- Validator task sending its events to the same broadcast channel
- JSON serialization of events over WebSocket
- Zero overhead when no viewer is connected (broadcast send errors ignored)
- Connection lifecycle: connect, receive stream, disconnect at any time

**Out of scope:**
- Authentication or access control (this is a dev/playtest diagnostic tool)
- Viewer UI rendering (story 3-7 for terminal viewer, story 3-9 for browser viewer)
- Event persistence or replay
- Backpressure or rate limiting (broadcast channel has a fixed buffer; lagging receivers get `Lagged` error)
- Binary frame support (all events are JSON text frames)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Endpoint serves WebSocket | `/ws/watcher` accepts WebSocket upgrade and holds connection |
| Telemetry stream | Connected client receives JSON-serialized `WatcherEvent` messages |
| Multiple clients | Two viewers can connect simultaneously and both receive all events |
| Zero overhead | When no viewer is connected, `broadcast::send` errors are silently ignored |
| Component filtering | Only events with component in the watched list are forwarded to viewers |
| Event structure | Each event includes timestamp, component, event_type, severity, and fields |
| Validation events included | Validator warnings and exercise summaries appear in the stream |
| No GameSnapshot payloads | Full state snapshots are never sent — only TurnRecord metadata |
| Clean disconnect | Viewer can disconnect at any time without affecting game traffic on /ws |
