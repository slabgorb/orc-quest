---
parent: context-epic-4.md
---

# Story 4-12: Speculative Prerendering -- Queue Image Generation During Voice Playback Window

## Business Context

Image generation takes 2-8 seconds. Voice narration playback takes 5-15 seconds. If we
start rendering the next image while the current narration is still being read aloud,
the image is ready by the time the voice finishes -- zero perceived latency. This is the
most impactful optimization in the media pipeline.

In Python, speculative prerendering is woven into the orchestrator with fire-and-forget
asyncio tasks. The Rust port makes this explicit: a `PrerenderScheduler` observes TTS
streaming state and the render queue, injecting speculative render jobs during the voice
playback window. If the speculation is wrong (next narration produces a different subject),
the prerender is simply wasted -- no harm done.

**Python source:** `sq-2/sidequest/renderer/speculative.py` (SpeculativeRenderer)
**Depends on:** Story 4-4 (render queue for submitting jobs) and Story 4-8 (TTS streaming
for knowing the playback window)

## Technical Approach

### PrerenderScheduler

```rust
pub struct PrerenderScheduler {
    config: PrerenderConfig,
    pending_prerender: Option<PrerenderJob>,
}

pub struct PrerenderConfig {
    pub enabled: bool,
    pub min_tts_duration_ms: u64,  // Only prerender if TTS is long enough (default 3000)
    pub max_speculative_jobs: u32, // Max concurrent speculative renders (default 1)
}

pub struct PrerenderJob {
    pub subject: RenderSubject,
    pub queued_at: Instant,
    pub tts_remaining_ms: u64,
}
```

### Speculation Strategy

The scheduler decides what to prerender based on the current game state. The idea is
to predict what the next scene will look like:

```rust
impl PrerenderScheduler {
    pub fn on_tts_start(
        &mut self,
        tts_duration_estimate_ms: u64,
        current_state: &GameState,
        extractor: &SubjectExtractor,
        render_queue: &RenderQueue,
    ) -> Option<()> {
        if !self.config.enabled { return None; }
        if tts_duration_estimate_ms < self.config.min_tts_duration_ms { return None; }

        // Speculate: what's the most likely next subject?
        let speculative_subject = self.predict_next_subject(current_state, extractor)?;

        // Submit to render queue (it handles dedup if this subject already rendered)
        render_queue.enqueue(
            speculative_subject.clone(),
            &current_state.genre_art_style(),
            &current_state.image_model(),
        );

        self.pending_prerender = Some(PrerenderJob {
            subject: speculative_subject,
            queued_at: Instant::now(),
            tts_remaining_ms: tts_duration_estimate_ms,
        });

        Some(())
    }

    pub fn on_tts_end(&mut self) {
        self.pending_prerender = None;
    }
}
```

### Subject Prediction Heuristics

```rust
fn predict_next_subject(&self, state: &GameState, extractor: &SubjectExtractor) -> Option<RenderSubject> {
    // Strategy 1: If in combat, predict the next combat scene
    if state.combat.in_combat {
        return Some(RenderSubject {
            entities: state.combat.active_combatants(),
            scene_type: SceneType::Combat,
            tier: SubjectTier::Scene,
            prompt_fragment: format!("combat scene with {}", state.combat.description()),
            narrative_weight: 0.8,
        });
    }

    // Strategy 2: If moving to a new location, predict the location
    if let Some(destination) = &state.pending_destination {
        return Some(RenderSubject {
            entities: vec![],
            scene_type: SceneType::Exploration,
            tier: SubjectTier::Landscape,
            prompt_fragment: format!("view of {}", destination),
            narrative_weight: 0.7,
        });
    }

    // Strategy 3: If talking to an NPC, predict a portrait
    if let Some(npc) = &state.active_dialogue_npc {
        return Some(RenderSubject {
            entities: vec![npc.clone()],
            scene_type: SceneType::Dialogue,
            tier: SubjectTier::Portrait,
            prompt_fragment: format!("portrait of {}", npc),
            narrative_weight: 0.6,
        });
    }

    None  // Can't predict, skip prerender
}
```

### TTS Duration Estimation

The scheduler needs to know how long TTS will play to decide if there's enough time:

```rust
pub fn estimate_tts_duration(segments: &[TtsSegment]) -> u64 {
    // Rough estimate: ~150ms per word + pause hints
    segments.iter().map(|s| {
        let word_count = s.text.split_whitespace().count() as u64;
        let speech_ms = word_count * 150;
        let pause_ms = s.pause_after_ms as u64;
        speech_ms + pause_ms
    }).sum()
}
```

### Waste Budget

Speculative renders consume GPU time. To avoid excessive waste:

```rust
pub struct WasteTracker {
    speculative_renders: u32,
    hits: u32,  // Prerender matched actual next render
    misses: u32,  // Prerender wasted
}

impl WasteTracker {
    pub fn hit_rate(&self) -> f32 {
        if self.speculative_renders == 0 { return 0.0; }
        self.hits as f32 / self.speculative_renders as f32
    }

    // Disable speculation if hit rate drops below threshold
    pub fn should_continue(&self, min_hit_rate: f32) -> bool {
        self.speculative_renders < 10 || self.hit_rate() >= min_hit_rate
    }
}
```

### Integration Points

```rust
// After TTS segments are computed and streaming begins:
let duration_est = estimate_tts_duration(&segments);
prerender_scheduler.on_tts_start(duration_est, &game_state, &extractor, &render_queue);

// When TTS finishes:
prerender_scheduler.on_tts_end();

// When actual next render is requested, check for prerender hit:
// (The render queue's dedup handles this -- if the speculative hash matches,
//  the actual request gets Deduplicated and the prerender result is used)
```

## Scope Boundaries

**In scope:**
- `PrerenderScheduler` with `on_tts_start()` / `on_tts_end()` lifecycle
- Subject prediction heuristics (combat, location, dialogue)
- TTS duration estimation for playback window sizing
- Integration with render queue (speculative jobs go through normal dedup)
- `WasteTracker` for monitoring hit rate
- Configurable enable/disable and minimum TTS duration threshold
- Unit tests for prediction heuristics and duration estimation

**Out of scope:**
- LLM-based next-scene prediction (heuristics only)
- Multi-image speculative batches (one speculative render at a time)
- Client-side image prefetch (server decides, client displays)
- Cross-session speculation learning
- Priority elevation for speculative jobs

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Trigger on TTS start | Speculative render queued when TTS begins and duration exceeds minimum |
| Duration gate | TTS under 3 seconds does not trigger speculation |
| Combat prediction | In-combat state produces combat scene prerender |
| Location prediction | Pending destination produces landscape prerender |
| Dialogue prediction | Active NPC dialogue produces portrait prerender |
| Dedup integration | Speculative render with same hash as actual request is deduplicated |
| Waste tracking | Hit/miss rate tracked, speculation disabled if hit rate too low |
| Configurable | Enabled/disabled via config, minimum TTS duration configurable |
| Non-blocking | Speculation does not delay TTS streaming or game loop |
| Graceful no-op | If prediction fails (returns None), no job queued, no error |
