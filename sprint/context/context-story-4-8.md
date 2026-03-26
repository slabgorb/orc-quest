---
parent: context-epic-4.md
---

# Story 4-8: TTS Streaming -- Stream Synthesized Audio Chunks to Client via WebSocket

## Business Context

This is the delivery end of the TTS pipeline. Text segmenter (4-7) produces segments,
this story synthesizes them via the daemon and streams the resulting audio chunks to the
client over WebSocket. The key design goal is pipeline parallelism: segment N+1 starts
synthesizing while segment N is being delivered to the client, so the player hears
continuous speech with minimal gaps.

In Python, this is an asyncio pipeline that streams wav chunks via WebSocket. The Rust
port uses tokio tasks with channel-based coordination between synthesis and delivery.

**Python source:** `sq-2/sidequest/voice/stream.py` (TtsStreamer)
**Depends on:** Story 4-7 (text segmentation produces the segments to synthesize)

## Technical Approach

### TTS Protocol Messages

```rust
#[derive(Debug, Clone, Serialize)]
pub struct TtsChunkPayload {
    pub audio_base64: String,   // Base64-encoded audio bytes
    pub segment_index: usize,
    pub is_last_chunk: bool,
    pub speaker: String,
    pub format: AudioFormat,
}

#[derive(Debug, Clone, Serialize)]
pub enum AudioFormat {
    Wav,
    Opus,
}

pub enum GameMessage {
    // ... existing variants
    TtsChunk(TtsChunkPayload),
    TtsStart { total_segments: usize },
    TtsEnd,
}
```

### Streaming Pipeline Architecture

```rust
pub struct TtsStreamer {
    daemon: DaemonClient,
    config: TtsStreamConfig,
}

pub struct TtsStreamConfig {
    pub prefetch_count: usize,  // How many segments to synthesize ahead (default 2)
    pub format: AudioFormat,
}

impl TtsStreamer {
    pub async fn stream(
        &self,
        segments: Vec<TtsSegment>,
        ws_tx: &broadcast::Sender<GameMessage>,
    ) -> Result<(), TtsError> {
        let total = segments.len();
        let _ = ws_tx.send(GameMessage::TtsStart { total_segments: total });

        // Channel for synthesized audio chunks
        let (audio_tx, mut audio_rx) = mpsc::channel::<SynthesizedChunk>(self.config.prefetch_count);

        // Spawn synthesis task -- produces audio chunks into channel
        let daemon = self.daemon.clone();
        let synth_handle = tokio::spawn(async move {
            for segment in segments {
                let request = TtsRequest {
                    text: segment.text.clone(),
                    model: segment.voice.preset.model.clone(),
                    voice_id: segment.voice.preset.voice_id.clone(),
                    speed: segment.voice.preset.speed,
                };
                match daemon.synthesize(&request).await {
                    Ok(resp) => {
                        let chunk = SynthesizedChunk {
                            audio_bytes: resp.audio_bytes,
                            segment,
                        };
                        if audio_tx.send(chunk).await.is_err() { break; }
                    }
                    Err(e) => {
                        tracing::warn!("TTS synthesis failed for segment {}: {}", segment.index, e);
                        // Skip failed segment, continue with next
                    }
                }
            }
        });

        // Deliver chunks to client as they arrive
        while let Some(chunk) = audio_rx.recv().await {
            let payload = TtsChunkPayload {
                audio_base64: base64::encode(&chunk.audio_bytes),
                segment_index: chunk.segment.index,
                is_last_chunk: chunk.segment.is_last,
                speaker: chunk.segment.speaker.to_string(),
                format: self.config.format.clone(),
            };
            let _ = ws_tx.send(GameMessage::TtsChunk(payload));

            // Honor pause hint between segments
            if chunk.segment.pause_after_ms > 0 && !chunk.segment.is_last {
                tokio::time::sleep(Duration::from_millis(chunk.segment.pause_after_ms as u64)).await;
            }
        }

        let _ = ws_tx.send(GameMessage::TtsEnd);
        synth_handle.await?;
        Ok(())
    }
}
```

### Prefetch Buffer

The `prefetch_count` channel capacity means the synthesis task can run ahead of delivery.
With `prefetch_count = 2`, segments N+1 and N+2 are synthesizing while segment N plays.
This hides per-segment synthesis latency (typically 200-500ms each).

### Error Handling

TTS failures are non-fatal. If a segment fails to synthesize:
- Log the error
- Skip that segment in the audio stream
- Continue with the next segment
- The client sees a brief gap but the game continues

If the entire TTS pipeline fails (daemon down), the game falls back to text-only
narration -- the NARRATION message was already sent before TTS starts.

### Session Integration

TTS streaming is triggered after narration is produced by the turn pipeline:

```rust
// In the turn pipeline (post-narration)
let segments = segmenter.segment(&narration, &voice_router, &known_npcs);
if !segments.is_empty() {
    tokio::spawn(tts_streamer.stream(segments, ws_tx.clone()));
}
```

## Scope Boundaries

**In scope:**
- `TtsStreamer` with `stream()` method
- `TtsChunkPayload`, `TtsStart`, `TtsEnd` protocol messages
- Prefetch buffer for synthesis-ahead-of-delivery
- Per-segment pause hints honored between chunks
- Graceful degradation on per-segment synthesis failure
- Base64 encoding of audio bytes for WebSocket delivery
- Session integration (spawned as background task after narration)

**Out of scope:**
- Client-side audio decoding and playback (client's responsibility)
- Audio compression beyond format selection (daemon handles encoding)
- Lip sync data generation
- Interruption handling (player sends new input during TTS)
- Audio mixer ducking coordination (that's story 4-10)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Stream start | `TtsStart` message sent before first audio chunk |
| Chunk delivery | Each segment produces a `TtsChunk` message on WebSocket |
| Stream end | `TtsEnd` message sent after last chunk |
| Prefetch | Synthesis runs ahead of delivery by `prefetch_count` segments |
| Pause hints | Inter-segment pauses match `pause_after_ms` from segmenter |
| Base64 encoding | Audio bytes encoded as base64 string in payload |
| Segment failure | Failed synthesis skips segment, continues stream |
| Total failure | Daemon down means no TTS, game continues text-only |
| Speaker included | Each chunk carries speaker identity for client display |
| Non-blocking | TTS streaming runs as background task, does not block turn loop |
