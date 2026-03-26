---
parent: context-epic-4.md
---

# Story 4-5: IMAGE Message Broadcast -- Deliver Rendered Images to Connected Clients via WebSocket

## Business Context

This is the final step in the image pipeline: taking a completed render from the queue
and broadcasting it to the React client as an IMAGE message over WebSocket. The client
already knows how to display IMAGE messages -- it just needs them delivered with the
right payload (image URL, scene description, tier for layout hints).

In Python, the render result is pushed directly to the WebSocket in the render callback.
The Rust port subscribes to the render queue's broadcast channel (from story 4-4) and
translates `RenderResult` into protocol-level `GameMessage::Image` for WebSocket delivery.

**Python source:** `sq-2/sidequest/media/render.py` (on_render_complete callback)
**Depends on:** Story 4-4 (render queue broadcasts `RenderResult` that this story consumes)

## Technical Approach

### IMAGE Protocol Message

```rust
#[derive(Debug, Clone, Serialize)]
pub struct ImagePayload {
    pub image_url: String,
    pub description: String,
    pub tier: String,           // "portrait", "scene", "landscape", "abstract"
    pub scene_type: String,     // "combat", "dialogue", "exploration", etc.
    pub generation_ms: u64,
}

// In sidequest-protocol:
pub enum GameMessage {
    // ... existing variants
    Image(ImagePayload),
}
```

### Broadcast Listener

A background task subscribes to the render queue's result channel and forwards
completed renders to the session's WebSocket broadcast:

```rust
pub async fn spawn_image_broadcaster(
    mut render_rx: broadcast::Receiver<RenderResult>,
    ws_tx: broadcast::Sender<GameMessage>,
) {
    while let Ok(result) = render_rx.recv().await {
        match result {
            RenderResult::Success { image_url, generation_ms, subject, .. } => {
                let msg = GameMessage::Image(ImagePayload {
                    image_url,
                    description: subject.prompt_fragment,
                    tier: subject.tier.to_string(),
                    scene_type: subject.scene_type.to_string(),
                    generation_ms,
                });
                let _ = ws_tx.send(msg);
            }
            RenderResult::Failed { error, .. } => {
                tracing::warn!("render failed, skipping IMAGE broadcast: {}", error);
                // Non-fatal: game continues without image
            }
        }
    }
}
```

### Session Integration

The image broadcaster is spawned when a session enters the Playing phase (from story 2-2).
It lives for the duration of the session:

```rust
impl GameSession {
    fn start_media_tasks(&mut self) {
        let render_rx = self.render_queue.subscribe();
        let ws_tx = self.ws_broadcast.clone();
        self.image_task = Some(tokio::spawn(
            spawn_image_broadcaster(render_rx, ws_tx)
        ));
    }
}
```

### Client Contract

The React client expects this JSON shape on the WebSocket:

```json
{
    "type": "IMAGE",
    "payload": {
        "image_url": "http://daemon:8081/renders/abc123.png",
        "description": "A dark cavern lit by bioluminescent fungi",
        "tier": "landscape",
        "scene_type": "exploration",
        "generation_ms": 3200
    }
}
```

The client uses `tier` for layout decisions (portrait images are smaller, landscapes
fill the width) and `description` as alt text.

## Scope Boundaries

**In scope:**
- `ImagePayload` struct in sidequest-protocol
- `GameMessage::Image` variant
- Background task subscribing to render queue results
- Translation from `RenderResult` to `GameMessage::Image`
- WebSocket broadcast to connected clients
- Graceful handling of failed renders (log, skip, no crash)
- Integration with session lifecycle (spawn on Playing, cancel on disconnect)

**Out of scope:**
- Image compression or resizing (daemon delivers final format)
- Client-side image caching (client's responsibility)
- Image history / gallery (deferred feature)
- Multiple concurrent sessions sharing renders

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Broadcast on success | Completed render produces IMAGE message on WebSocket |
| Payload shape | JSON matches client contract (type, image_url, description, tier, scene_type) |
| Failed render silent | Render failure logs warning but does not send error to client |
| Tier included | SubjectTier serialized as lowercase string in payload |
| Scene type included | SceneType serialized as lowercase string in payload |
| Session-scoped | Broadcaster task spawned per session, cancelled on disconnect |
| Non-blocking | IMAGE broadcast does not block the game loop or render queue |
| Latency metadata | `generation_ms` passed through for client-side metrics |
| Protocol type | `GameMessage::Image` variant added to sidequest-protocol crate |
