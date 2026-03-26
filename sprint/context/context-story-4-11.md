---
parent: context-epic-4.md
---

# Story 4-11: Theme Rotation -- Anti-Repetition Track Selection Within Mood Category

## Business Context

If a genre pack has three combat tracks and every fight plays the same one, the player
notices fast. Theme rotation ensures variety by tracking recently played tracks per mood
category and selecting the least-recently-used one. This is a small but important polish
feature -- it makes the audio feel curated rather than random.

In Python, `sq-2/sidequest/audio/director.py` includes a simple rotation mechanism
using a per-mood play count. The Rust port adds a `ThemeRotator` struct that the music
director delegates to for track selection, with configurable anti-repetition rules.

**Python source:** `sq-2/sidequest/audio/director.py` (track selection logic within MusicDirector)
**Depends on:** Story 4-9 (music director calls the rotator during track selection)

## Technical Approach

### ThemeRotator

```rust
pub struct ThemeRotator {
    play_history: HashMap<Mood, VecDeque<String>>,
    config: RotationConfig,
}

pub struct RotationConfig {
    pub history_depth: usize,   // How many recent tracks to avoid (default 3)
    pub randomize: bool,        // Shuffle eligible tracks (default true)
}

impl ThemeRotator {
    pub fn select(
        &mut self,
        mood: &Mood,
        available_tracks: &[TrackInfo],
    ) -> Option<TrackInfo> {
        if available_tracks.is_empty() {
            return None;
        }

        let history = self.play_history
            .entry(mood.clone())
            .or_insert_with(VecDeque::new);

        // Filter out recently played tracks
        let eligible: Vec<&TrackInfo> = available_tracks.iter()
            .filter(|t| !history.contains(&t.track_id))
            .collect();

        // If all tracks are in history, reset and allow any
        let candidates = if eligible.is_empty() {
            history.clear();
            available_tracks.iter().collect()
        } else {
            eligible
        };

        // Select: random if configured, otherwise first eligible
        let selected = if self.config.randomize {
            use rand::seq::SliceRandom;
            candidates.choose(&mut rand::thread_rng())
        } else {
            candidates.first()
        };

        selected.map(|track| {
            // Record in history
            history.push_back(track.track_id.clone());
            if history.len() > self.config.history_depth {
                history.pop_front();
            }
            (*track).clone()
        })
    }
}
```

### Integration with MusicDirector

The music director (story 4-9) delegates track selection to the rotator:

```rust
impl MusicDirector {
    fn select_track(&mut self, classification: &MoodClassification) -> Option<TrackInfo> {
        let tracks = self.mood_tracks.get(&classification.primary)?;
        self.rotator.select(&classification.primary, tracks)
    }
}
```

### Energy Matching

When multiple tracks are eligible, prefer tracks whose energy level matches the mood
intensity:

```rust
fn score_energy_match(track: &TrackInfo, intensity: f32) -> f32 {
    1.0 - (track.energy - intensity).abs()
}

// In select(), sort eligible tracks by energy match before choosing
let mut scored: Vec<_> = eligible.iter()
    .map(|t| (t, score_energy_match(t, intensity)))
    .collect();
scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
```

### Edge Cases

- **Single track in mood:** Always plays that track (no rotation possible)
- **All tracks exhausted:** History clears, full pool available again
- **New mood category:** Empty history, any track eligible
- **Genre pack with no tracks for mood:** Returns `None`, music director skips cue

## Scope Boundaries

**In scope:**
- `ThemeRotator` with `select()` method
- Per-mood play history with configurable depth
- Anti-repetition filtering (recently played tracks excluded)
- History reset when all tracks exhausted
- Optional randomization of eligible tracks
- Energy-based preference scoring
- Integration hook for `MusicDirector::select_track()`
- Unit tests for rotation, exhaustion reset, and single-track edge case

**Out of scope:**
- Cross-session rotation persistence (history resets each session)
- Weighted random (all eligible tracks equally likely)
- Player track preferences or skip functionality
- Dynamic track generation via MusicGen
- Transition-aware selection (choosing tracks that crossfade well)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| No immediate repeat | Track A plays, next selection for same mood is not Track A |
| History depth | With depth 3, tracks played 4+ selections ago are eligible again |
| Exhaustion reset | If all 3 combat tracks played, history clears and all are eligible |
| Random selection | With randomize=true, eligible tracks selected randomly |
| Deterministic mode | With randomize=false, first eligible track selected (for testing) |
| Energy matching | Higher-energy track preferred when mood intensity is high |
| Single track | Mood with one track always returns that track |
| Empty mood | Mood with no tracks returns None |
| Per-mood history | Combat history does not affect Exploration track selection |
| Integration | MusicDirector uses rotator for all track selection |
