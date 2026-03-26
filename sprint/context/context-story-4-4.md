---
parent: context-epic-4.md
---

# Story 4-4: Render Queue -- Async Image Generation Queue with Hash-Based Cache Dedup

## Business Context

Image generation is slow (2-8 seconds per render). The render queue decouples the game
loop from image generation by accepting render jobs asynchronously and processing them
in the background. It also deduplicates requests using content hashing -- if two turns
produce narration about the same scene, only one render fires.

In Python, `sq-2/sidequest/renderer/` uses asyncio tasks for background rendering with
an in-memory dict for dedup. The Rust port uses a `tokio::sync::mpsc` channel for the
job queue and a `HashMap<u64, RenderStatus>` for hash-based dedup. This is the component
that makes image generation feel seamless -- the player never waits for a render.

**Python source:** `sq-2/sidequest/renderer/queue.py` (RenderQueue)
**Depends on:** Story 4-2 (subject extraction produces `RenderSubject` fed into the queue)

## Technical Approach

### RenderJob and Status

```rust
pub struct RenderJob {
    pub id: Uuid,
    pub subject: RenderSubject,
    pub content_hash: u64,
    pub genre_art_style: String,
    pub image_model: String,
    pub created_at: Instant,
    pub status: RenderStatus,
}

#[derive(Debug, Clone, PartialEq)]
pub enum RenderStatus {
    Queued,
    InProgress,
    Complete { image_url: String, generation_ms: u64 },
    Failed { error: String },
    Deduplicated { original_id: Uuid },
}
```

### Queue Architecture

The render queue runs as a background tokio task. The game loop sends jobs through a
channel; the queue worker processes them sequentially (daemon has limited GPU):

```rust
pub struct RenderQueue {
    job_tx: mpsc::Sender<RenderJob>,
    cache: Arc<Mutex<HashMap<u64, CacheEntry>>>,
    result_tx: broadcast::Sender<RenderResult>,
}

struct CacheEntry {
    job_id: Uuid,
    status: RenderStatus,
    created_at: Instant,
}

impl RenderQueue {
    pub fn spawn(daemon: DaemonClient, config: RenderQueueConfig) -> Self {
        let (job_tx, job_rx) = mpsc::channel(config.queue_depth);
        let (result_tx, _) = broadcast::channel(config.result_buffer);
        let cache = Arc::new(Mutex::new(HashMap::new()));

        tokio::spawn(Self::worker(job_rx, daemon, cache.clone(), result_tx.clone()));

        Self { job_tx, cache, result_tx }
    }

    pub async fn enqueue(&self, subject: RenderSubject, art_style: &str, model: &str) -> EnqueueResult {
        let hash = compute_content_hash(&subject);

        // Check cache for dedup
        {
            let cache = self.cache.lock().unwrap();
            if let Some(entry) = cache.get(&hash) {
                return EnqueueResult::Deduplicated { original_id: entry.job_id };
            }
        }

        let job = RenderJob {
            id: Uuid::new_v4(),
            subject,
            content_hash: hash,
            genre_art_style: art_style.to_string(),
            image_model: model.to_string(),
            created_at: Instant::now(),
            status: RenderStatus::Queued,
        };

        self.job_tx.send(job).await.map_err(|_| QueueError::Full)?;
        EnqueueResult::Queued { job_id: job.id }
    }
}
```

### Worker Loop

```rust
async fn worker(
    mut job_rx: mpsc::Receiver<RenderJob>,
    daemon: DaemonClient,
    cache: Arc<Mutex<HashMap<u64, CacheEntry>>>,
    result_tx: broadcast::Sender<RenderResult>,
) {
    while let Some(job) = job_rx.recv().await {
        let request = RenderRequest {
            prompt: job.subject.prompt_fragment.clone(),
            art_style: job.genre_art_style.clone(),
            model: job.image_model.clone(),
            width: tier_to_width(&job.subject.tier),
            height: tier_to_height(&job.subject.tier),
        };

        let result = match daemon.render(&request).await {
            Ok(resp) => RenderResult::Success {
                job_id: job.id,
                image_url: resp.image_url,
                generation_ms: resp.generation_ms,
            },
            Err(e) => RenderResult::Failed {
                job_id: job.id,
                error: e.to_string(),
            },
        };

        // Update cache
        {
            let mut cache = cache.lock().unwrap();
            cache.insert(job.content_hash, CacheEntry {
                job_id: job.id,
                status: result.to_status(),
                created_at: Instant::now(),
            });
        }

        let _ = result_tx.send(result);
    }
}
```

### Content Hashing

Dedup key is a hash of the subject's entities + scene type + tier, ignoring minor
prompt wording differences:

```rust
fn compute_content_hash(subject: &RenderSubject) -> u64 {
    let mut hasher = DefaultHasher::new();
    for entity in &subject.entities {
        entity.to_lowercase().hash(&mut hasher);
    }
    subject.scene_type.hash(&mut hasher);
    subject.tier.hash(&mut hasher);
    hasher.finish()
}
```

### Result Subscription

Downstream consumers (the IMAGE broadcast in story 4-5) subscribe to render results:

```rust
pub fn subscribe(&self) -> broadcast::Receiver<RenderResult> {
    self.result_tx.subscribe()
}
```

## Scope Boundaries

**In scope:**
- `RenderQueue` with channel-based job submission and background worker
- Hash-based content dedup with in-memory cache
- `RenderJob` and `RenderStatus` types
- Worker loop calling `DaemonClient::render()`
- Result broadcasting via `tokio::sync::broadcast`
- Tier-based image dimensions (Portrait = tall, Landscape = wide)
- Cache TTL expiry for stale entries
- Unit tests with mock daemon client

**Out of scope:**
- Persistent cache (disk-backed, cross-session dedup)
- Priority ordering (all jobs are FIFO)
- Concurrent worker pool (single worker, daemon GPU is the bottleneck)
- Speculative prerendering (that's story 4-12)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Async enqueue | `enqueue()` returns immediately, render happens in background |
| Dedup | Second enqueue with same content hash returns `Deduplicated` |
| Worker processes | Queued job sent to daemon via `DaemonClient::render()` |
| Result broadcast | Subscribers receive `RenderResult` when job completes |
| Failure handling | Daemon error produces `RenderStatus::Failed`, not a panic |
| Cache update | Completed renders stored in cache with hash key |
| Tier dimensions | Portrait gets tall aspect ratio, Landscape gets wide |
| Queue depth | Queue rejects when full (backpressure, not unbounded growth) |
| Cache TTL | Stale cache entries evicted after configurable duration |
| Non-blocking | Game loop never blocks waiting for render completion |
