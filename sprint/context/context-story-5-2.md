---
parent: context-epic-5.md
---

# Story 5-2: Combat Event Classification — Categorize Combat Outcomes as Boring/Dramatic, Track boring_streak

## Business Context

The tension tracker needs to know whether each combat turn was boring or dramatic. In
Python, `classify_event()` examines the combat outcome (damage dealt, status effects,
kills) and returns a classification. Boring turns increment `boring_streak`, which feeds
the gambler's ramp. Dramatic turns reset it and may inject an event spike.

This is the observation layer — the tracker watches what happened in combat and updates
its internal state. Without classification, the tracker has no inputs and drama_weight
stays at zero.

**Python source:** `sq-2/sidequest/game/tension.py:classify_event()`
**Depends on:** Story 5-1 (TensionTracker struct), Story 2-7 (CombatState, combat outcomes)

## Technical Approach

### CombatEvent Enum

```rust
/// Dramatic combat events that inject tension spikes.
/// Each variant carries a predefined spike magnitude and decay rate.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CombatEvent {
    CriticalHit,    // spike 0.8, decay 0.15/turn
    KillingBlow,    // spike 1.0, decay 0.20/turn
    DeathSave,      // spike 0.7, decay 0.15/turn
    FirstBlood,     // spike 0.6, decay 0.10/turn
    NearMiss,       // spike 0.5, decay 0.10/turn
    LastStanding,   // spike 0.9, decay 0.20/turn
}

impl CombatEvent {
    pub fn spike_magnitude(&self) -> f64 {
        match self {
            Self::CriticalHit  => 0.8,
            Self::KillingBlow  => 1.0,
            Self::DeathSave    => 0.7,
            Self::FirstBlood   => 0.6,
            Self::NearMiss     => 0.5,
            Self::LastStanding => 0.9,
        }
    }

    pub fn decay_rate(&self) -> f64 {
        match self {
            Self::CriticalHit  => 0.15,
            Self::KillingBlow  => 0.20,
            Self::DeathSave    => 0.15,
            Self::FirstBlood   => 0.10,
            Self::NearMiss     => 0.10,
            Self::LastStanding => 0.20,
        }
    }
}
```

### Classification Result

```rust
/// The result of classifying a combat turn's outcome.
pub enum TurnClassification {
    /// Nothing interesting happened — increment boring_streak
    Boring,
    /// Something dramatic happened — reset boring_streak, inject spike
    Dramatic(CombatEvent),
}
```

### The Classifier

```rust
impl TensionTracker {
    /// Classify a combat outcome and update boring_streak accordingly.
    /// Called once per turn after combat resolution (story 2-7).
    pub fn observe(&mut self, outcome: &CombatOutcome) -> TurnClassification {
        let classification = Self::classify(outcome);
        match &classification {
            TurnClassification::Boring => {
                self.boring_streak += 1;
                self.update_action_tension();
            }
            TurnClassification::Dramatic(_event) => {
                self.reset_action_tension();
                // Spike injection handled in story 5-3
            }
        }
        classification
    }

    /// Pure classification — examines outcome, returns boring or dramatic.
    /// Priority order matters: check killing_blow before critical_hit,
    /// because a crit that kills is a KillingBlow, not a CriticalHit.
    fn classify(outcome: &CombatOutcome) -> TurnClassification {
        // Priority-ordered checks
        if outcome.target_killed {
            return TurnClassification::Dramatic(CombatEvent::KillingBlow);
        }
        if outcome.is_last_standing {
            return TurnClassification::Dramatic(CombatEvent::LastStanding);
        }
        if outcome.death_save_required {
            return TurnClassification::Dramatic(CombatEvent::DeathSave);
        }
        if outcome.is_critical {
            return TurnClassification::Dramatic(CombatEvent::CriticalHit);
        }
        if outcome.is_first_blood {
            return TurnClassification::Dramatic(CombatEvent::FirstBlood);
        }
        if outcome.near_miss {
            return TurnClassification::Dramatic(CombatEvent::NearMiss);
        }
        TurnClassification::Boring
    }
}
```

### What Counts as "Boring"

Python's definition: a turn where damage dealt is below 10% of target max HP, no status
effects applied, no kills, no crits. Rust simplifies this — if none of the dramatic
event checks fire, the turn is boring. The `CombatOutcome` struct (from story 2-7)
carries boolean flags that make classification a series of pattern matches.

### Rust Learning Note

The `classify` function is a pure static method (`fn classify`, not `fn classify(&self)`)
since it only examines the outcome. The `observe` method wraps it with side effects
(updating boring_streak). This separation makes classify independently testable without
constructing a full TensionTracker.

## Scope Boundaries

**In scope:**
- `CombatEvent` enum with 6 variants, spike/decay constants
- `TurnClassification` enum (Boring / Dramatic)
- `classify()` pure function with priority-ordered checks
- `observe()` method that classifies and updates boring_streak
- boring_streak increment on boring, reset on dramatic
- Unit tests for each event type and priority ordering

**Out of scope:**
- Spike injection into tracker (story 5-3)
- Drama weight computation (story 5-3)
- CombatOutcome struct definition (story 2-7, already exists)
- NearMiss detection logic (assumes CombatOutcome.near_miss is set by combat system)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Event enum | `CombatEvent` has 6 variants with correct spike magnitudes and decay rates |
| Classification | `classify()` returns correct event for each outcome type |
| Priority order | Kill + crit outcome classifies as KillingBlow, not CriticalHit |
| Boring streak | 3 boring turns -> boring_streak=3, then dramatic -> boring_streak=0 |
| Action tension update | boring_streak increment triggers action_tension recalculation |
| Pure classify | `classify()` takes &CombatOutcome, returns TurnClassification with no side effects |
| observe() wires both | `observe()` classifies, updates streak, returns classification |
| Tests | Unit tests for each event type, priority ordering, streak counting |
