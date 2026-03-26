---
parent: context-epic-5.md
---

# Story 5-6: Quiet Turn Detection — Count Consecutive Low-Action Turns, Inject Escalation Beat Hints

## Business Context

Sometimes combat stalls. Five turns of misses, low damage, and no status changes. The
gambler's ramp drives up action_tension, but that only affects narration length — it
does not fix the *content* problem. Players get bored because the narrator describes
the same nothing happening in progressively longer sentences.

Python's `check_escalation()` detects these quiet stretches and injects an "escalation
beat hint" into the narrator prompt — a suggestion like "the environment shifts" or
"a new threat emerges." The narrator weaves this hint into its narration, breaking the
monotony without the engine changing game mechanics.

This is a content-level intervention, not a pacing one. It works alongside the gambler's
ramp (which handles delivery pacing) to ensure boring stretches resolve naturally.

**Python source:** `sq-2/sidequest/game/tension.py:check_escalation()`
**ADR:** `sq-2/docs/adr-pacing-detection.md`
**Depends on:** Story 5-1 (TensionTracker, boring_streak)

## Technical Approach

### Escalation Check

```rust
impl TensionTracker {
    /// Check whether the current boring_streak has crossed the escalation threshold.
    /// Returns an escalation beat hint if so.
    pub fn check_escalation(&self, escalation_streak: u32) -> Option<EscalationBeat> {
        if self.boring_streak >= escalation_streak {
            Some(self.select_escalation_beat())
        } else {
            None
        }
    }
}
```

The default `escalation_streak` is 5 turns (configurable per genre in story 5-8). Python
hardcodes this; Rust passes it as a parameter so the threshold is explicit at the call site.

### Escalation Beat Types

```rust
/// Categories of escalation beats the narrator can weave in.
/// These are hints, not game state changes — the narrator decides how to use them.
#[derive(Debug, Clone, PartialEq)]
pub enum EscalationBeat {
    /// "The environment shifts" — describe a change in surroundings
    EnvironmentShift,
    /// "A new threat emerges" — hint at danger from a new direction
    NewThreat,
    /// "An ally is in danger" — draw attention to a vulnerable character
    AllyInDanger,
    /// "The terrain becomes unstable" — physical change in the battlefield
    TerrainChange,
    /// "Something unexpected happens" — generic wild card
    Unexpected,
}

impl EscalationBeat {
    /// Narrator prompt text for this beat.
    pub fn narrator_hint(&self) -> &'static str {
        match self {
            Self::EnvironmentShift => "Describe a shift in the environment — lighting changes, sounds intensify, or the atmosphere grows heavier.",
            Self::NewThreat => "Hint at a new danger emerging — movement in the shadows, a distant rumble, or an unexpected arrival.",
            Self::AllyInDanger => "Draw attention to a vulnerable ally — their footing slips, they're flanked, or their defense weakens.",
            Self::TerrainChange => "The battlefield changes — ground cracks, a wall crumbles, fire spreads, or cover is destroyed.",
            Self::Unexpected => "Something unexpected disrupts the rhythm — a sound, a flash, an object falls, or a creature stirs.",
        }
    }
}
```

### Beat Selection

```rust
impl TensionTracker {
    /// Select an escalation beat. Rotates through types to avoid repetition.
    /// Uses boring_streak as the rotation index so the same streak length
    /// always produces the same beat (deterministic for testing).
    fn select_escalation_beat(&self) -> EscalationBeat {
        const BEATS: &[EscalationBeat] = &[
            EscalationBeat::EnvironmentShift,
            EscalationBeat::NewThreat,
            EscalationBeat::AllyInDanger,
            EscalationBeat::TerrainChange,
            EscalationBeat::Unexpected,
        ];
        let index = (self.boring_streak as usize) % BEATS.len();
        BEATS[index].clone()
    }
}
```

Python picks randomly. Rust uses deterministic rotation — same boring_streak produces
same beat type. This makes tests predictable and avoids the "random in game logic"
anti-pattern. If variety is needed, the genre pack can shuffle the beat order.

### Integration with PacingHint

The escalation beat populates the `escalation_beat` field on `PacingHint` (from story 5-4):

```rust
impl TensionTracker {
    pub fn pacing_hint(&self, thresholds: &DramaThresholds) -> PacingHint {
        let weight = self.drama_weight();
        let mut hint = PacingHint::from_drama_weight(weight);

        // Check for quiet stretch escalation
        if let Some(beat) = self.check_escalation(thresholds.escalation_streak) {
            hint.escalation_beat = Some(beat.narrator_hint().to_string());
        }

        hint
    }
}
```

### Rust Learning Note

The `const BEATS` array uses `&[EscalationBeat]` — a static slice. In Python you would
create a list each call. In Rust, `const` means this array exists at compile time with
zero runtime allocation. The `clone()` on the selected beat is cheap since EscalationBeat
is a simple enum with no heap data.

## Scope Boundaries

**In scope:**
- `EscalationBeat` enum with 5 variants and narrator hint text
- `check_escalation()` method on TensionTracker
- Deterministic beat rotation based on boring_streak
- Integration with PacingHint.escalation_beat field
- Unit tests for threshold crossing and beat rotation

**Out of scope:**
- Genre-specific escalation streak thresholds (story 5-8)
- Game state changes from escalation (this is narration guidance only)
- NPC autonomous actions triggered by quiet stretches (deferred)
- Random beat selection (deterministic rotation is sufficient)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Beat enum | EscalationBeat has 5 variants with narrator_hint() text |
| Threshold check | boring_streak < 5 -> None, boring_streak >= 5 -> Some(beat) |
| Deterministic rotation | boring_streak=5 -> EnvironmentShift, boring_streak=6 -> NewThreat |
| PacingHint integration | pacing_hint() populates escalation_beat when streak >= threshold |
| No escalation when dramatic | After a dramatic event resets boring_streak, no escalation fires |
| Configurable threshold | check_escalation() accepts threshold parameter, not hardcoded |
| Hint text useful | Each narrator_hint() is a complete directive the LLM can follow |
| Tests | Tests for threshold boundary, rotation cycle, integration with pacing_hint |
