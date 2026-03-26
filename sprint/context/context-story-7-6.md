---
parent: context-epic-7.md
---

# Story 7-6: Scenario Pacing — Turn-Based Pressure Escalation, Tension Ramp Over Scenario Arc

## Business Context

A whodunit that stays at the same tension level is boring. Pressure should escalate:
early turns are calm investigation, mid-game raises stakes with new discoveries and NPC
nervousness, and late-game creates urgency — the culprit might flee, evidence might be
destroyed. Python's `pacing.py` managed this with a tension curve. The Rust port makes
the tension ramp configurable per scenario template.

**Python ref:** `sq-2/sidequest/scenario/pacing.py`
**Depends on:** Story 7-2 (gossip propagation — gossip events feed tension)

## Technical Approach

```rust
pub struct ScenarioPacing {
    pub base_tension_curve: TensionCurve,
    pub event_modifiers: Vec<TensionModifier>,
}

pub enum TensionCurve {
    Linear { rate: f32 },           // steady ramp
    Exponential { base: f32 },      // slow start, fast finish
    StepFunction { steps: Vec<(u64, f32)> }, // discrete jumps at turn thresholds
}

impl ScenarioPacing {
    pub fn tension_at_turn(&self, turn: u64, events: &[ScenarioEvent]) -> f32 {
        let base = self.base_tension_curve.value_at(turn);
        let modifier: f32 = events.iter()
            .filter_map(|e| self.modifier_for(e))
            .sum();
        (base + modifier).clamp(0.0, 1.0)
    }
}

pub struct TensionModifier {
    pub event_type: ScenarioEventType,
    pub tension_delta: f32,  // positive = raises tension
}

pub enum ScenarioEventType {
    ClueActivated,
    ContradictionFound,
    NpcFled,
    EvidenceDestroyed,
    AccusationMade,
}
```

Tension drives two downstream systems: NPC autonomous actions (story 7-5) use tension
to weight desperate actions, and scene directives (if Epic 6 is integrated) can use
tension to increase narrator urgency.

Scenario templates define the base curve in YAML. Events during play modify tension
additively — finding a clue bumps it up, an NPC fleeing spikes it.

## Scope Boundaries

**In scope:**
- `ScenarioPacing`, `TensionCurve`, `TensionModifier` types
- `tension_at_turn()` calculation combining base curve + event modifiers
- Three curve types: Linear, Exponential, StepFunction
- YAML deserialization of pacing configuration
- Unit tests for tension calculation at various turns

**Out of scope:**
- How tension affects narration tone (narrator prompt concern)
- Player-visible tension meter (UI concern)
- Dynamic curve adjustment based on player skill

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Base curve | Linear, Exponential, and StepFunction curves compute correctly |
| Event modifiers | Scenario events (clue found, NPC fled) modify tension |
| Tension bounds | Output clamped to 0.0-1.0 |
| Early calm | Tension at turn 1 is near 0.0 for linear/exponential curves |
| Late urgency | Tension at final turns approaches 1.0 |
| YAML config | Pacing configuration deserializes from scenario template |
| Modifier stacking | Multiple events stack additively |
