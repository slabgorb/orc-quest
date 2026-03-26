---
parent: context-epic-5.md
---

# Story 5-3: Drama Weight Computation — max(action_tension, stakes_tension), Event Spike Injection with Decay

## Business Context

This is where the two tension tracks merge into a single usable number. The Python
codebase calls `compute_weight()` to combine action tension, stakes tension, and any
active event spike into `drama_weight` — a 0.0-1.0 value that every downstream consumer
reads. Without this story, the tracker has internal state but no output.

Event spikes are the "exclamation marks" of combat. A critical hit injects a 0.8 spike
that decays by 0.15 per turn — so the turn after a crit still feels dramatic (0.65),
but three turns later it fades (0.35). This decay curve was tuned through playtesting
to match the natural "afterglow" of a dramatic moment.

**Python source:** `sq-2/sidequest/game/tension.py:compute_weight()`, spike injection logic
**Depends on:** Story 5-2 (event classification, boring_streak tracking)

## Technical Approach

### Spike Injection

When `observe()` classifies a turn as dramatic, the spike is injected:

```rust
impl TensionTracker {
    /// Inject an event spike. Replaces any existing spike (only one active at a time).
    fn inject_spike(&mut self, event: CombatEvent) {
        self.last_event_spike = Some(EventSpike {
            event,
            magnitude: event.spike_magnitude(),
            decay_rate: event.decay_rate(),
        });
        self.spike_decay_age = 0;
    }
}
```

Python allows stacking multiple spikes. The Rust port simplifies to one active spike —
playtesting showed that overlapping spikes rarely happen (dramatic events are spaced out)
and when they do, the newer spike is always more relevant.

### Spike Decay

```rust
impl TensionTracker {
    /// Current effective spike value after decay.
    /// Returns 0.0 if no spike is active or spike has fully decayed.
    fn effective_spike(&self) -> f64 {
        match &self.last_event_spike {
            Some(spike) => {
                let decayed = spike.magnitude - (spike.decay_rate * self.spike_decay_age as f64);
                decayed.max(0.0)
            }
            None => 0.0,
        }
    }

    /// Age the spike by one turn. Called at the start of each observe().
    fn age_spike(&mut self) {
        if self.last_event_spike.is_some() {
            self.spike_decay_age += 1;
            // Clean up fully decayed spikes
            if self.effective_spike() <= 0.0 {
                self.last_event_spike = None;
                self.spike_decay_age = 0;
            }
        }
    }
}
```

### Drama Weight Computation

```rust
impl TensionTracker {
    /// The single output value. All downstream consumers read this.
    /// drama_weight = max(action_tension, stakes_tension, effective_spike)
    pub fn drama_weight(&self) -> f64 {
        self.action_tension
            .max(self.stakes_tension)
            .max(self.effective_spike())
            .clamp(0.0, 1.0)
    }
}
```

The `clamp(0.0, 1.0)` is defense in depth — the individual tracks are already bounded,
but clamping at the output ensures no downstream consumer ever sees an out-of-range value.

### Updated observe() Flow

Story 5-2 defined `observe()` with a placeholder for spike injection. This story completes it:

```rust
impl TensionTracker {
    pub fn observe(&mut self, outcome: &CombatOutcome, lowest_hp_ratio: f64) -> TurnClassification {
        // 1. Age any existing spike
        self.age_spike();

        // 2. Update stakes tension (pure function of current HP)
        self.stakes_tension = self.compute_stakes_tension(lowest_hp_ratio);

        // 3. Classify the combat outcome
        let classification = Self::classify(outcome);

        // 4. Update action tension track
        match &classification {
            TurnClassification::Boring => {
                self.boring_streak += 1;
                self.update_action_tension();
            }
            TurnClassification::Dramatic(event) => {
                self.reset_action_tension();
                self.inject_spike(*event);
            }
        }

        classification
    }
}
```

### Decay Curve Examples

```
Turn 0: KillingBlow spike = 1.0
Turn 1: 1.0 - 0.20 * 1 = 0.80
Turn 2: 1.0 - 0.20 * 2 = 0.60
Turn 3: 1.0 - 0.20 * 3 = 0.40
Turn 4: 1.0 - 0.20 * 4 = 0.20
Turn 5: 1.0 - 0.20 * 5 = 0.00 (spike cleaned up)

Turn 0: CriticalHit spike = 0.8
Turn 1: 0.8 - 0.15 * 1 = 0.65
Turn 2: 0.8 - 0.15 * 2 = 0.50
Turn 3: 0.8 - 0.15 * 3 = 0.35
Turn 4: 0.8 - 0.15 * 4 = 0.20
Turn 5: 0.8 - 0.15 * 5 = 0.05
Turn 6: 0.8 - 0.15 * 6 = 0.00 (spike cleaned up)
```

## Scope Boundaries

**In scope:**
- `inject_spike()` method
- `effective_spike()` with linear decay
- `age_spike()` called per turn, cleans up fully decayed spikes
- `drama_weight()` — the single output method (max of three tracks)
- Updated `observe()` flow integrating all three concerns
- Unit tests for decay curves, weight computation, spike replacement

**Out of scope:**
- Multiple simultaneous spikes (Python supports this, Rust simplifies to one)
- Non-linear decay curves (linear is sufficient per playtesting)
- Pacing hints derived from drama_weight (story 5-4)
- Delivery mode selection (story 5-5)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Spike injection | Dramatic event sets last_event_spike with correct magnitude and decay_rate |
| Spike decay | CriticalHit spike decays from 0.8 to 0.0 over 6 turns at 0.15/turn |
| Spike cleanup | Fully decayed spike is set to None, spike_decay_age resets |
| Spike replacement | New dramatic event replaces existing spike, resets decay age |
| drama_weight | Returns max(action_tension, stakes_tension, effective_spike) |
| Clamped output | drama_weight always in 0.0-1.0 range |
| Full observe flow | observe() ages spike, updates stakes, classifies, updates action track |
| Combined scenario | boring_streak=5 (action=0.85) + HP at 60% (stakes=0.3) -> drama_weight=0.85 |
| Spike dominates | Fresh KillingBlow spike (1.0) overrides both tracks |
