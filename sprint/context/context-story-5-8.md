---
parent: context-epic-5.md
---

# Story 5-8: Genre-Tunable Thresholds — drama_weight Breakpoints Configurable Per Genre Pack

## Business Context

A horror genre should stream text more aggressively than a comedy genre. A noir detective
story has different pacing rhythms than a fantasy dungeon crawl. The Python codebase
hardcodes pacing thresholds, which means every genre feels the same in terms of delivery
and narration length. This story makes all drama engine breakpoints configurable per
genre pack.

This is a small but high-impact story. The thresholds are already parameterized in the
code (stories 5-4 and 5-5 accept threshold parameters). This story loads those parameters
from genre pack YAML and passes them through the pipeline.

**Python source:** Not implemented in Python — this is a Rust-only improvement.
**Depends on:** Story 5-5 (DeliveryMode with configurable thresholds)

## Technical Approach

### DramaThresholds Struct

```rust
/// Genre-tunable breakpoints for the drama engine.
/// Loaded from genre pack YAML, with sensible defaults.
#[derive(Debug, Clone, serde::Deserialize)]
#[serde(default)]
pub struct DramaThresholds {
    /// drama_weight below this -> Instant delivery (default 0.30)
    pub sentence_delivery_min: f64,
    /// drama_weight above this -> Streaming delivery (default 0.70)
    pub streaming_delivery_min: f64,
    /// drama_weight below this -> skip image render (default 0.40)
    pub render_threshold: f64,
    /// boring_streak count before escalation beat fires (default 5)
    pub escalation_streak: u32,
    /// boring turns to reach action_tension=1.0 (default 8)
    pub ramp_length: u32,
}

impl Default for DramaThresholds {
    fn default() -> Self {
        Self {
            sentence_delivery_min: 0.30,
            streaming_delivery_min: 0.70,
            render_threshold: 0.40,
            escalation_streak: 5,
            ramp_length: 8,
        }
    }
}
```

### Genre Pack YAML Integration

Genre packs gain an optional `drama` section:

```yaml
# genre_packs/mutant_wasteland/flickering_reach/genre.yaml
name: Flickering Reach
tone: gritty post-apocalyptic survival

drama:
  sentence_delivery_min: 0.25    # more sentence-mode delivery
  streaming_delivery_min: 0.60   # stream earlier for gritty tension
  render_threshold: 0.35         # render images more often
  escalation_streak: 4           # escalate faster (wasteland is dangerous)
  ramp_length: 6                 # shorter ramp (action moves fast)
```

```yaml
# genre_packs/cozy_mystery/lavender_lane/genre.yaml
name: Lavender Lane
tone: lighthearted cozy mystery

drama:
  sentence_delivery_min: 0.40    # more instant delivery (cozy = brisk)
  streaming_delivery_min: 0.85   # only stream at peak drama
  render_threshold: 0.50         # fewer images, more text-focused
  escalation_streak: 7           # slow escalation (cozy pace)
  ramp_length: 10                # long ramp (tension builds slowly)
```

### Genre Pack Loader Changes

The genre pack loader (from Epic 1, sidequest-genre crate) adds DramaThresholds:

```rust
pub struct GenrePack {
    pub name: String,
    pub tone: String,
    pub tropes: Vec<Trope>,
    pub characters: Vec<CharacterTemplate>,
    pub drama: DramaThresholds,  // NEW: deserialized from YAML
    // ... other fields
}
```

If the `drama` section is missing from the YAML, `#[serde(default)]` kicks in and
all thresholds use their defaults. Existing genre packs that predate this feature
work without modification.

### Wiring Through the Pipeline

The orchestrator already receives `DramaThresholds` (from story 5-7). This story
ensures it comes from the genre pack:

```rust
impl Orchestrator {
    pub fn new(genre_pack: GenrePack, /* ... */) -> Self {
        let tension = TensionTracker::with_config(genre_pack.drama.ramp_length);
        Self {
            tension,
            drama_thresholds: genre_pack.drama.clone(),
            // ...
        }
    }
}
```

DeliveryMode selection uses genre thresholds:

```rust
// In PacingHint::from_drama_weight_with_thresholds:
let delivery_mode = DeliveryMode::from_weight_with_thresholds(
    drama_weight,
    thresholds.sentence_delivery_min,
    thresholds.streaming_delivery_min,
);
```

### Validation

```rust
impl DramaThresholds {
    /// Validate thresholds are sensible. Called during genre pack loading.
    pub fn validate(&self) -> Result<(), GenrePackError> {
        if self.sentence_delivery_min >= self.streaming_delivery_min {
            return Err(GenrePackError::InvalidDramaThresholds(
                "sentence_delivery_min must be less than streaming_delivery_min".into()
            ));
        }
        if self.render_threshold < 0.0 || self.render_threshold > 1.0 {
            return Err(GenrePackError::InvalidDramaThresholds(
                "render_threshold must be between 0.0 and 1.0".into()
            ));
        }
        if self.escalation_streak == 0 {
            return Err(GenrePackError::InvalidDramaThresholds(
                "escalation_streak must be at least 1".into()
            ));
        }
        Ok(())
    }
}
```

### Rust Learning Note

`#[serde(default)]` on the struct means if the entire `drama` key is missing from YAML,
serde uses `Default::default()`. Individual fields also get defaults if missing. This is
a common Rust pattern for backward-compatible configuration — add new config sections
without breaking existing files. Python achieves this with `dict.get(key, default)` calls
scattered through the code; Rust centralizes defaults in the `Default` impl.

## Scope Boundaries

**In scope:**
- `DramaThresholds` struct with serde deserialization and Default impl
- YAML schema for `drama` section in genre packs
- Validation of threshold relationships
- GenrePack gains `drama: DramaThresholds` field
- Orchestrator initializes TensionTracker with genre-specific ramp_length
- DeliveryMode and PacingHint use genre-specific thresholds
- Backward compatibility: missing `drama` section uses defaults

**Out of scope:**
- Runtime threshold changes (thresholds are set at genre pack load time)
- Per-encounter threshold overrides (all encounters in a genre use the same thresholds)
- UI for editing thresholds (YAML editing only)
- Threshold auto-tuning from playtest data (future optimization)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct defined | DramaThresholds with 5 fields, all with sensible defaults |
| Serde default | Missing `drama` key in YAML -> all defaults applied |
| Partial override | Genre sets only `ramp_length: 6` -> other fields use defaults |
| Validation | sentence_delivery_min >= streaming_delivery_min -> error at load time |
| Genre pack field | GenrePack.drama is populated from YAML |
| Orchestrator uses | TensionTracker initialized with genre-specific ramp_length |
| Delivery uses | DeliveryMode thresholds come from genre pack, not hardcoded |
| Backward compat | Existing genre packs without `drama` section load without error |
| Tests | Default construction, partial YAML, validation errors, threshold wiring |
