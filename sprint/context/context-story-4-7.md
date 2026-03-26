---
parent: context-epic-4.md
---

# Story 4-7: TTS Text Segmentation -- Break Narration into Speakable Segments for Streaming

## Business Context

The daemon's TTS endpoint synthesizes one segment at a time. Long narration paragraphs
need to be broken into sentence-level chunks so that audio can stream to the client
incrementally -- the first sentence plays while the rest are still being synthesized.
This is what makes TTS feel responsive instead of making the player wait 10 seconds
for an entire paragraph.

In Python, `sq-2/sidequest/voice/segment.py` splits text on sentence boundaries, handles
dialogue markers, and inserts pause hints between segments. The Rust port preserves these
heuristics and adds typed `Segment` structs with speaker attribution (from story 4-6's
voice routing).

**Python source:** `sq-2/sidequest/voice/segment.py` (TextSegmenter.segment)
**Depends on:** Story 4-6 (voice routing -- each segment needs a voice assignment)

## Technical Approach

### Segment Type

```rust
#[derive(Debug, Clone)]
pub struct TtsSegment {
    pub text: String,
    pub speaker: Speaker,
    pub voice: VoiceAssignment,
    pub pause_after_ms: u32,   // Pause hint for client playback
    pub index: usize,          // Position in sequence
    pub is_last: bool,
}
```

### TextSegmenter

```rust
pub struct TextSegmenter {
    sentence_splitter: SentenceSplitter,
    max_segment_length: usize,
    min_segment_length: usize,
}

impl TextSegmenter {
    pub fn segment(
        &self,
        narration: &str,
        voice_router: &VoiceRouter,
        known_npcs: &[String],
    ) -> Vec<TtsSegment> {
        // 1. Split into dialogue and narration blocks
        let blocks = self.split_dialogue_blocks(narration, known_npcs);

        // 2. Split each block into sentences
        let mut segments = Vec::new();
        for block in &blocks {
            let sentences = self.sentence_splitter.split(&block.text);
            for sentence in sentences {
                if sentence.trim().is_empty() { continue; }
                let speaker = identify_speaker(&block.text, known_npcs);
                let voice = voice_router.route(&speaker);
                segments.push(TtsSegment {
                    text: sentence,
                    speaker,
                    voice,
                    pause_after_ms: self.compute_pause(&sentence),
                    index: segments.len(),
                    is_last: false,
                });
            }
        }

        // Mark last segment
        if let Some(last) = segments.last_mut() {
            last.is_last = true;
        }
        segments
    }
}
```

### Sentence Splitting

Python uses a regex-based splitter that handles abbreviations, ellipses, and quoted
speech. Rust does the same:

```rust
pub struct SentenceSplitter {
    boundary_pattern: Regex,
    abbreviations: HashSet<String>,  // "Mr.", "Dr.", "St.", etc.
}

impl SentenceSplitter {
    pub fn split(&self, text: &str) -> Vec<String> {
        // Split on sentence-ending punctuation (.!?) followed by space + capital
        // But not on abbreviations or ellipses
        let mut sentences = Vec::new();
        let mut current = String::new();

        for segment in self.boundary_pattern.split(text) {
            current.push_str(segment);
            if self.is_sentence_boundary(&current) {
                sentences.push(current.trim().to_string());
                current = String::new();
            }
        }
        if !current.trim().is_empty() {
            sentences.push(current.trim().to_string());
        }
        sentences
    }
}
```

### Dialogue Block Splitting

Narration often interleaves narrator prose with character dialogue:

> The tavern falls silent. Grimjaw leans forward. "You want to cross the Wastes?
> Nobody crosses the Wastes." He laughs bitterly.

This should produce segments attributed to different speakers:
1. "The tavern falls silent." (Narrator)
2. "Grimjaw leans forward." (Narrator)
3. "You want to cross the Wastes? Nobody crosses the Wastes." (Grimjaw)
4. "He laughs bitterly." (Narrator)

```rust
struct DialogueBlock {
    text: String,
    speaker_hint: Option<String>,
}

fn split_dialogue_blocks(text: &str, known_npcs: &[String]) -> Vec<DialogueBlock> {
    // Regex for quoted speech preceded by "NAME says/said/shouts/..."
    // Returns alternating narration and dialogue blocks
}
```

### Pause Computation

Pauses between segments improve naturalness:

```rust
fn compute_pause(&self, sentence: &str) -> u32 {
    if sentence.ends_with('?') { 400 }
    else if sentence.ends_with('!') { 300 }
    else if sentence.ends_with("...") { 600 }
    else if sentence.ends_with('.') { 250 }
    else { 200 }
}
```

## Scope Boundaries

**In scope:**
- `TextSegmenter` with `segment()` method
- `TtsSegment` struct with text, speaker, voice, pause hint, sequence index
- Sentence boundary detection with abbreviation handling
- Dialogue block splitting with speaker attribution
- Pause hint computation based on punctuation
- Long sentence splitting (segments above max length get subdivided)
- Unit tests for segmentation edge cases

**Out of scope:**
- SSML markup generation (daemon handles voice prosody)
- Emotional tone inference (same voice, flat delivery)
- Multi-paragraph batching strategy (each segment is independent)
- Streaming the segments to the client (that's story 4-8)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Sentence splitting | "Hello. World." produces two segments |
| Abbreviation handling | "Dr. Smith arrived." stays as one segment |
| Ellipsis handling | "And then... silence." splits correctly after ellipsis |
| Dialogue attribution | Quoted speech after NPC name attributed to that NPC |
| Narrator fallback | Unattributed text attributed to Narrator speaker |
| Voice assignment | Each segment carries the correct `VoiceAssignment` from router |
| Pause hints | Question marks get longer pause than periods |
| Sequence index | Segments numbered 0..n with `is_last` on final segment |
| Max length | Segments exceeding max_segment_length are subdivided |
| Empty filtering | Blank segments filtered out |
