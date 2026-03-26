---
parent: context-epic-6.md
---

# Story 6-3: Engagement Multiplier — Scale Trope Progression Rate by Player Engagement Signal

## Business Context

When a player goes passive (repeating "I look around" or doing nothing meaningful), the
world should push harder — trope beats should fire faster, forcing events that demand a
response. Conversely, when the player is actively driving the story, tropes can progress
at normal speed. Python tracked "turns since last meaningful action" and used it as a
multiplier on trope tick progression. The Rust port makes this a first-class function
with clear bounds.

**Python ref:** `sq-2/docs/architecture/active-world-pacing-design.md` (engagement multiplier section)
**Depends on:** Story 2-8 (trope engine runtime — provides `tick_progression()`)

## Technical Approach

The engagement multiplier is a scaling factor applied to the trope engine's tick amount:

```rust
/// Turns since last meaningful action → multiplier on trope tick rate.
/// Returns 0.5x (very active) to 2.0x (very passive).
pub fn engagement_multiplier(turns_since_meaningful: u32) -> f32 {
    match turns_since_meaningful {
        0..=1 => 0.5,   // player is driving — slow trope escalation
        2..=3 => 1.0,   // normal pace
        4..=6 => 1.5,   // player drifting — world pushes harder
        _     => 2.0,   // player passive — world takes the wheel
    }
}
```

"Meaningful action" is defined by intent classification — Combat, Dialogue with purpose,
quest-advancing Exploration. Meta actions and idle exploration do not reset the counter.

The trope engine's `tick()` call becomes:

```rust
let multiplier = engagement_multiplier(state.turns_since_meaningful);
trope_engine.tick(base_tick * multiplier);
```

The `turns_since_meaningful` counter lives on `GameSnapshot` and resets when the intent
router classifies an action as meaningful.

## Scope Boundaries

**In scope:**
- `engagement_multiplier()` pure function
- `turns_since_meaningful` field on `GameSnapshot`
- Counter reset logic tied to intent classification
- Integration point with trope engine `tick()`
- Unit tests for multiplier curve and counter behavior

**Out of scope:**
- Changing what qualifies as "meaningful" per genre (future tuning knob)
- UI display of engagement level
- Multiplier affecting anything other than trope progression

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Multiplier range | Returns values between 0.5 and 2.0 inclusive |
| Passive acceleration | 4+ turns without meaningful action → multiplier > 1.0 |
| Active deceleration | 0-1 turns since meaningful → multiplier 0.5 |
| Counter resets | Meaningful intent (Combat, purposeful Dialogue) resets counter to 0 |
| Counter increments | Non-meaningful turns increment `turns_since_meaningful` |
| Trope integration | `tick()` receives `base_tick * multiplier` |
| Pure function | `engagement_multiplier()` has no side effects |
