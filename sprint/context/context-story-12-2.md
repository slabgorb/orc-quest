---
parent: context-epic-12.md
---

# Story 12-2: Per-Variation Crossfade Durations — Overture Fades Slow, Tension_Build Hits Hard

## Business Context

Story 12-1 completed variation selection — the MusicDirector now picks the right variation type
(Overture, Ambient, Sparse, Full, TensionBuild, Resolution) based on narrative context. However,
all variations currently use the same crossfade timing: `MixerConfig.crossfade_default_ms` (global
default, typically 3000ms).

This creates a cinematic mismatch:
- **Overtures** should fade in slowly (5000ms), creating a grand arrival moment.
- **Tension builds** should hit hard and fast (1000ms), maximizing urgency and impact.
- **Resolutions** should fade out gracefully (4000ms), letting the player sit in the resolution.
- **Ambient/Sparse/Full** use the baseline default (3000ms).

Each variation needs its own crossfade duration, configured per variation type, so the soundtrack
pacing matches the narrative intent.

**Depends on:** Story 12-1 (Cinematic track variation selection) — assumes `TrackVariation` enum,
`select_variation()`, and `AudioCue` with action field.

## Technical Approach

### 1. AudioCue Protocol Change

Add `fade_duration_ms` field to `AudioCuePayload` in `sidequest-protocol/src/message.rs`:

```rust
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AudioCuePayload {
    // existing fields...
    pub mood: Option<String>,
    pub music_track: Option<String>,
    pub sfx_triggers: Vec<String>,
    pub channel: Option<String>,
    pub action: Option<String>,
    pub volume: Option<f32>,
    
    /// Crossfade duration in milliseconds (variation-specific).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fade_duration_ms: Option<u32>,
}
```

**Rationale:** Optional field maintains backward compat with existing clients. If unset, client
defaults to its own hardcoded baseline (typically 3000ms).

### 2. MixerConfig Extension

Add a variation crossfade map to `MixerConfig` in `sidequest-genre/src/models.rs`:

```rust
pub struct MixerConfig {
    // existing fields...
    pub music_volume: f64,
    pub sfx_volume: f64,
    pub voice_volume: f64,
    pub duck_music_for_voice: bool,
    pub duck_amount_db: f64,
    pub crossfade_default_ms: u32,
    
    /// Per-variation crossfade durations. If a variation is not present,
    /// falls back to crossfade_default_ms.
    #[serde(default)]
    pub crossfade_by_variation: HashMap<TrackVariation, u32>,
}
```

**YAML shape (in genre packs' audio.yaml mixer section):**
```yaml
mixer:
  music_volume: 0.8
  sfx_volume: 0.7
  voice_volume: 0.9
  duck_music_for_voice: true
  duck_amount_db: -6
  crossfade_default_ms: 3000
  crossfade_by_variation:
    overture: 5000
    tension_build: 1000
    resolution: 4000
    # Other variations inherit crossfade_default_ms
```

### 3. MusicDirector Integration

In `MusicDirector::evaluate()`, after selecting the variation via `select_variation()`,
look up the crossfade duration for that variation:

```rust
fn get_crossfade_for_variation(&self, variation: TrackVariation) -> u32 {
    self.config
        .mixer
        .crossfade_by_variation
        .get(&variation)
        .copied()
        .unwrap_or(self.config.mixer.crossfade_default_ms)
}
```

**Integration point:** After `select_variation()` returns `TrackVariation`, call
`get_crossfade_for_variation()` to populate `AudioCue.fade_duration_ms` before returning.

### 4. Server Wiring (dispatch/audio.rs)

No changes needed — the `AudioCue` is populated by `MusicDirector::evaluate()`, which
now includes `fade_duration_ms`. The cue is serialized directly to `AudioCuePayload`.

### 5. Client Consumption (sidequest-ui)

The React client receives `fade_duration_ms` in the `AudioCuePayload` and uses it when
applying crossfades in `AudioMixer::apply_cue()`. If unset, the client uses its default.
This is follow-up scope (12-2 backend completion, 12-2 client story separate), but
the protocol field enables it.

## Key Architectural Notes

- **No silent fallbacks:** If a variation is missing from `crossfade_by_variation`, we
  explicitly fall back to `crossfade_default_ms`. Log the substitution.
- **Backward compat:** Genre packs without `crossfade_by_variation` section work identically
  to today — all variations use `crossfade_default_ms`.
- **No new state:** The crossfade durations are config (loaded with the genre pack), not
  derived from game state. MusicDirector reads them once at construction.
- **Variation must exist first:** This story assumes 12-1 completed — `TrackVariation` enum
  and `select_variation()` are in place and tested.

## Scope Boundaries

**In scope:**
- `fade_duration_ms` field in `AudioCuePayload`
- `crossfade_by_variation` map in `MixerConfig`
- `get_crossfade_for_variation()` lookup in MusicDirector
- Integration into `evaluate()` — populate fade_duration_ms before returning AudioCue
- Config parsing from genre pack YAML (serde default)
- Telemetry: crossfade duration visible in watcher events
- Backward compat: genre packs without the map work as before

**Out of scope:**
- Client-side crossfade implementation (follow-up story in sidequest-ui)
- Per-mood variation overrides (simplicity: one duration per variation type)
- Dynamic crossfade adjustment based on intensity (fixed per variation type)
- Changes to existing genre pack audio.yaml files (future content update)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Protocol updated | `AudioCuePayload.fade_duration_ms: Option<u32>` deserializes correctly, round-trips |
| Config parsed | `MixerConfig.crossfade_by_variation: HashMap<TrackVariation, u32>` from YAML `crossfade_by_variation` section |
| Lookup works | `get_crossfade_for_variation(variation: TrackVariation) -> u32` returns configured duration or falls back to default |
| Integration wired | `MusicDirector::evaluate()` populates `AudioCue.fade_duration_ms` with result of lookup |
| Telemetry emits | `MusicTelemetry` or watcher event includes chosen fade duration and variation |
| Backward compat | Genre packs without `crossfade_by_variation` section work identically — all variations use `crossfade_default_ms` |
| No silent fallbacks | Fallback to default duration is logged (tracing::debug or span event) |
| Tests pass | Full pipeline: AudioCue includes correct fade_duration_ms for each variation type |

## Pre-Story Findings from 12-1

Story 12-1 identified 3 findings relevant to 12-2:

1. **Gap:** `scene_turn_count` uses global counter, not per-scene. Affects variation selection.
   - Impact: After 4 turns anywhere, Ambient always wins Priority 4.
   - Recommendation: Follow-up story or tech debt. Does not block 12-2.

2. **Gap:** `drama_weight` sourced from `CombatState` only, not `TensionTracker`.
   - Impact: Tension_build never fires in non-combat drama scenarios.
   - Recommendation: Follow-up story or tech debt. Does not block 12-2.

3. **Improvement:** `bpm: 100` hardcoded placeholder defeats ThemeRotator energy matching.
   - Impact: Energy-based track rotation doesn't work for themed tracks.
   - Recommendation: Follow-up improvement. Does not block 12-2.

**Conclusion:** None of these findings block 12-2 work. The variation selection is functional
for the purpose of crossfade timing, even if it could be more sophisticated later.
