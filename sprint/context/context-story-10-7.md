---
parent: context-epic-10.md
---

# Story 10-7: Connect Agreeableness to Disposition — A-Dimension Feeds into Disposition System

## Business Context

Disposition (-15 to +15) tracks how an NPC feels about the player. Agreeableness describes
how cooperative the NPC is by nature. This story bridges the two: a high-agreeableness NPC
forgives faster (disposition recovers more quickly), while a low-agreeableness NPC holds
grudges (disposition drops stick longer). Agreeableness modulates the *rate* of disposition
change, not the target value.

**Python reference:** `sq-2/sprint/epic-64.yaml` — agreeableness multiplier applied to
disposition delta calculations. Rust implements the same multiplier approach.

**Depends on:** Story 10-1 (OceanProfile on NPC).

## Technical Approach

### Disposition Modifier

```rust
impl OceanProfile {
    /// Returns a multiplier for disposition changes.
    /// High agreeableness (10.0) → 1.5x positive changes, 0.7x negative changes
    /// Low agreeableness (0.0)  → 0.7x positive changes, 1.3x negative changes
    /// Mid agreeableness (5.0)  → 1.0x (neutral)
    pub fn disposition_modifier(&self, delta: f64) -> f64 {
        let a = self.agreeableness;
        if delta > 0.0 {
            // Positive disposition change: high A amplifies
            0.7 + (a / 10.0) * 0.8  // range: 0.7 to 1.5
        } else {
            // Negative disposition change: high A dampens
            1.3 - (a / 10.0) * 0.6  // range: 1.3 to 0.7
        }
    }
}
```

### Integration Point

The existing disposition update function multiplies the raw delta by the modifier:

```rust
fn update_disposition(npc: &mut Npc, raw_delta: i32) {
    let modifier = npc.ocean.disposition_modifier(raw_delta as f64);
    let adjusted = (raw_delta as f64 * modifier).round() as i32;
    npc.disposition = (npc.disposition + adjusted).clamp(-15, 15);
}
```

### Edge Cases

- Zero delta: no modification needed (modifier irrelevant)
- NPC at disposition cap (-15 or +15): clamping still applies after modification
- Default midpoint agreeableness (5.0): modifier is 1.0, no behavioral change

## Scope Boundaries

**In scope:**
- `disposition_modifier()` method on OceanProfile
- Integration with existing disposition update logic
- Unit tests for modifier math at low/mid/high agreeableness

**Out of scope:**
- Other OCEAN dimensions affecting disposition
- Disposition decay over time
- Player visibility of the modifier

## Acceptance Criteria

| AC | Detail |
|----|--------|
| High A positive | Agreeableness 9.0, +2 raw delta → adjusted > +2 |
| High A negative | Agreeableness 9.0, -2 raw delta → adjusted magnitude < 2 |
| Low A positive | Agreeableness 1.0, +2 raw delta → adjusted < +2 |
| Low A negative | Agreeableness 1.0, -2 raw delta → adjusted magnitude > 2 |
| Midpoint neutral | Agreeableness 5.0 → modifier is 1.0, no change |
| Clamped | Disposition never exceeds -15 to +15 after modification |
| Zero delta | Raw delta of 0 → disposition unchanged regardless of agreeableness |
