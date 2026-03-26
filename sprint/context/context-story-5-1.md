---
parent: context-epic-5.md
---

# Story 5-1: TensionTracker Struct — Dual-Track Model with Action Tension and Stakes Tension

## Business Context

Every combat turn in the Python codebase produces the same length of narration regardless
of whether a character missed a swing or landed a killing blow. The TensionTracker fixes
this by computing a single `drama_weight` (0.0-1.0) from two independent tension tracks.
This is the foundation struct that the entire pacing engine builds on — nothing in Epic 5
works without it.

The dual-track model emerged from playtesting in sq-2. Action tension uses a "gambler's
ramp" — the longer nothing dramatic happens, the higher the tension climbs, because
*something has to happen soon*. Stakes tension is purely HP-based — when a character is
close to death, tension is high regardless of what just happened.

**Python source:** `sq-2/sidequest/game/tension.py` (TensionTracker class, `__init__`, `observe`)
**ADR:** `sq-2/docs/adr-dual-track-tension-model.md`
**Depends on:** Story 2-7 (CombatState with HP tracking and combat outcomes)

## Technical Approach

### The Struct

```rust
/// Tracks dramatic tension across two independent channels.
/// Both tracks produce values in 0.0-1.0. The final drama_weight
/// is the max of both tracks (plus any decaying event spike).
pub struct TensionTracker {
    /// Consecutive turns classified as "boring" (miss, low damage, no status change)
    boring_streak: u32,
    /// Computed from boring_streak via gambler's ramp formula
    action_tension: f64,
    /// Computed from lowest friendly HP ratio — pure function of game state
    stakes_tension: f64,
    /// Most recent dramatic event spike, if any, with its original magnitude
    last_event_spike: Option<EventSpike>,
    /// How many turns since the last spike (for decay)
    spike_decay_age: u32,
    /// Tunable: how many boring turns to reach action_tension = 1.0 (default 8)
    ramp_length: u32,
}

pub struct EventSpike {
    pub event: CombatEvent,
    pub magnitude: f64,
    pub decay_rate: f64,
}
```

### Gambler's Ramp (Action Tension)

```rust
impl TensionTracker {
    /// Recalculate action tension from boring_streak.
    /// Formula: min(base + 0.15 * boring_streak, 0.85)
    /// The 0.85 cap ensures action tension alone never hits 1.0 —
    /// only event spikes or stakes can drive to maximum.
    fn update_action_tension(&mut self) {
        let base = 0.1;
        self.action_tension = (base + 0.15 * self.boring_streak as f64).min(0.85);
    }
}
```

Python uses `boring_streak / ramp_length` capped at 1.0. The Rust version uses the
explicit 0.15 coefficient from playtesting, capped at 0.85. This is a deliberate
refinement — action tension alone should feel like *rising anticipation*, not peak drama.

### Stakes Tension (HP-Based)

```rust
impl TensionTracker {
    /// Pure function: compute stakes tension from the lowest friendly HP ratio.
    /// No memory — recalculated fresh each turn from CombatState.
    fn compute_stakes_tension(&self, lowest_hp_ratio: f64) -> f64 {
        match lowest_hp_ratio {
            r if r > 0.75 => 0.0,
            r if r > 0.50 => 0.3,
            r if r > 0.25 => 0.5,
            r if r > 0.0  => 0.7,
            _              => 1.0,  // downed character
        }
    }
}
```

### Construction and Reset

```rust
impl TensionTracker {
    pub fn new() -> Self {
        Self::with_config(8) // default ramp_length
    }

    pub fn with_config(ramp_length: u32) -> Self {
        Self {
            boring_streak: 0,
            action_tension: 0.0,
            stakes_tension: 0.0,
            last_event_spike: None,
            spike_decay_age: 0,
            ramp_length,
        }
    }

    /// Reset action tension track (called when a dramatic event fires).
    pub fn reset_action_tension(&mut self) {
        self.boring_streak = 0;
        self.action_tension = 0.0;
    }
}
```

### Rust Learning Note

The `TensionTracker` is a good example of *interior state with controlled mutation*.
In Python, `self.boring_streak += 1` is trivial. In Rust, you need `&mut self` — the
borrow checker ensures only one thing can mutate the tracker at a time. This matters
when the tracker is shared across the turn pipeline (story 5-7).

## Scope Boundaries

**In scope:**
- `TensionTracker` struct with both tension tracks
- `EventSpike` struct for spike storage
- Gambler's ramp calculation (action_tension from boring_streak)
- HP-based stakes calculation (stakes_tension from lowest HP ratio)
- Constructor with configurable ramp_length
- Reset method for action tension track
- Unit tests for ramp curve and HP threshold boundaries

**Out of scope:**
- Event classification logic (story 5-2)
- Drama weight combination and spike decay (story 5-3)
- Pacing hints and delivery modes (stories 5-4, 5-5)
- Quiet turn detection (story 5-6)
- Integration with orchestrator (story 5-7)
- Genre-tunable thresholds (story 5-8)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct compiles | `TensionTracker` with all fields, `EventSpike` with event + magnitude + decay_rate |
| Gambler's ramp | `boring_streak=0` -> action_tension ~0.1, `boring_streak=5` -> ~0.85 (capped) |
| HP thresholds | >75% -> 0.0, 50-75% -> 0.3, 25-50% -> 0.5, <25% -> 0.7, downed -> 1.0 |
| Reset works | After reset, boring_streak=0 and action_tension=0.0 |
| Configurable ramp | `with_config(ramp_length)` accepted and stored |
| Default construction | `TensionTracker::new()` uses ramp_length=8 |
| Unit tests pass | Tests for ramp boundaries, HP thresholds, reset behavior |
