---
parent: context-epic-5.md
---

# Story 5-5: Drama-Aware Text Delivery — INSTANT/SENTENCE/STREAMING Modes Based on drama_weight Thresholds

## Business Context

Text delivery speed is a powerful pacing tool. In Python, low-drama turns dump the full
narration to the client instantly. Medium-drama turns reveal text sentence by sentence
with pauses. High-drama turns stream word by word, creating a typewriter effect that
builds suspense. Players consistently reported that streaming delivery made critical hits
"feel" more impactful even before they read the words.

This is the client-facing output of the drama engine. The server tags each narration with
a `DeliveryMode`, and the UI client decides how to render the text based on that tag.

**Python source:** `sq-2/sidequest/voice/delivery.py` (DeliveryMode, select_delivery)
**ADR:** `sq-2/docs/adr-drama-aware-delivery.md`
**Depends on:** Story 5-3 (drama_weight computation)

## Technical Approach

### DeliveryMode Enum

```rust
/// How the client should reveal narration text.
/// Sent as part of the NARRATION_START protocol message.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum DeliveryMode {
    /// Full text appears at once. For routine, low-drama turns.
    Instant,
    /// Text reveals sentence by sentence with brief pauses.
    Sentence,
    /// Text streams word by word (typewriter effect). For peak drama.
    Streaming,
}
```

### Threshold Selection

```rust
impl DeliveryMode {
    /// Select delivery mode from drama_weight using default thresholds.
    pub fn from_weight(drama_weight: f64) -> Self {
        Self::from_weight_with_thresholds(drama_weight, 0.30, 0.70)
    }

    /// Select delivery mode with genre-tunable thresholds.
    /// A horror genre might use (0.20, 0.50) for more streaming.
    /// A comedy genre might use (0.40, 0.85) for more instant delivery.
    pub fn from_weight_with_thresholds(
        drama_weight: f64,
        sentence_min: f64,
        streaming_min: f64,
    ) -> Self {
        if drama_weight >= streaming_min {
            Self::Streaming
        } else if drama_weight >= sentence_min {
            Self::Sentence
        } else {
            Self::Instant
        }
    }
}
```

### Protocol Integration

The delivery mode flows through the WebSocket protocol. The `NARRATION_START` message
(from Epic 1, story 1-7) needs a `delivery_mode` field:

```rust
/// Part of the NARRATION_START GameMessage payload.
pub struct NarrationStart {
    pub delivery_mode: DeliveryMode,
    pub estimated_chunks: Option<u32>,  // hint for UI progress
}
```

When delivery mode is `Instant`, the server sends a single `NARRATION_END` with full text.
When `Sentence`, it sends one `NARRATION_CHUNK` per sentence. When `Streaming`, it sends
`NARRATION_CHUNK` messages as fast as the agent produces them (one per word or phrase).

### Sentence Splitting for Sentence Mode

```rust
/// Split narration into sentence-sized chunks for Sentence delivery.
/// Uses a simple heuristic: split on sentence-ending punctuation followed by space.
pub fn split_sentences(text: &str) -> Vec<String> {
    let mut sentences = Vec::new();
    let mut current = String::new();

    for ch in text.chars() {
        current.push(ch);
        if (ch == '.' || ch == '!' || ch == '?') {
            // Peek: if this looks like end-of-sentence, split
            let trimmed = current.trim().to_string();
            if !trimmed.is_empty() {
                sentences.push(trimmed);
            }
            current = String::new();
        }
    }

    // Remaining text (no trailing punctuation)
    let trimmed = current.trim().to_string();
    if !trimmed.is_empty() {
        sentences.push(trimmed);
    }
    sentences
}
```

This is intentionally simple. Python uses a regex-based splitter with abbreviation
handling (Mr., Dr., etc.). The Rust version starts simple and can be refined if
playtesting reveals issues with false splits.

### Server-Side Delivery Logic

```rust
impl GameSession {
    async fn deliver_narration(
        &self,
        text: &str,
        mode: DeliveryMode,
        tx: &broadcast::Sender<GameMessage>,
    ) {
        match mode {
            DeliveryMode::Instant => {
                tx.send(GameMessage::NarrationEnd { text: text.to_string() }).ok();
            }
            DeliveryMode::Sentence => {
                let sentences = split_sentences(text);
                for sentence in &sentences {
                    tx.send(GameMessage::NarrationChunk { text: sentence.clone() }).ok();
                    tokio::time::sleep(Duration::from_millis(300)).await;
                }
                tx.send(GameMessage::NarrationEnd { text: text.to_string() }).ok();
            }
            DeliveryMode::Streaming => {
                // Chunks arrive from agent stream — forwarded as-is
                // NarrationEnd sent after stream completes
            }
        }
    }
}
```

## Scope Boundaries

**In scope:**
- `DeliveryMode` enum with Instant, Sentence, Streaming variants
- `from_weight()` and `from_weight_with_thresholds()` selection logic
- Sentence splitting utility function
- `NarrationStart` payload with delivery_mode field
- Server-side delivery dispatch (Instant full-send, Sentence chunked, Streaming pass-through)
- Unit tests for threshold boundaries and sentence splitting

**Out of scope:**
- Client-side rendering of delivery modes (sidequest-ui responsibility)
- Streaming backpressure or rate limiting (optimization)
- Audio/TTS synchronization with text delivery (daemon territory)
- Genre-specific threshold configuration (story 5-8)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Enum defined | DeliveryMode with Instant, Sentence, Streaming; derives Serialize/Deserialize |
| Default thresholds | <0.30 -> Instant, 0.30-0.70 -> Sentence, >0.70 -> Streaming |
| Custom thresholds | from_weight_with_thresholds(0.5, 0.20, 0.50) -> Streaming |
| Boundary exact | drama_weight=0.30 -> Sentence (not Instant), drama_weight=0.70 -> Streaming |
| Sentence split | "You miss. The goblin laughs." -> ["You miss.", "The goblin laughs."] |
| Protocol payload | NarrationStart message includes delivery_mode field |
| Instant delivery | Instant mode sends single NarrationEnd with full text |
| Sentence delivery | Sentence mode sends NarrationChunk per sentence, then NarrationEnd |
| Tests | Threshold boundary tests, sentence splitting edge cases |
