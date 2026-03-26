---
parent: context-epic-6.md
---

# Story 6-4: FactionAgenda Model — Schema for Faction Goals, Urgency, and Scene Injection Rules

## Business Context

Factions in the world should pursue their own goals independent of the player. A bandit
clan might escalate raids; a merchant guild might tighten trade routes. In Python, faction
behavior was partially implicit in trope definitions. This story creates an explicit
`FactionAgenda` model that genre packs can define in YAML, with urgency levels that
control how often faction events inject into scene directives.

**Depends on:** Story 6-1 (scene directive formatter — FactionAgenda feeds into directives)

## Technical Approach

The `FactionAgenda` model is a serde-deserializable struct loaded from genre pack YAML:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FactionAgenda {
    pub faction_id: String,
    pub goal: String,
    pub urgency: f32,  // 0.0-1.0, higher = more frequent scene injection
    pub scene_injection_rules: Vec<InjectionRule>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InjectionRule {
    pub condition: InjectionCondition,
    pub event_template: String,  // narrator-facing description
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum InjectionCondition {
    TurnInterval { every_n_turns: u32 },
    MaturityMinimum { minimum: CampaignMaturity },
    StakeActive { stake_id: String },
    Always,
}
```

Genre pack YAML example:

```yaml
factions:
  - id: rust_brothers
    agendas:
      - goal: "Expand scrap territory into the Flickering Reach"
        urgency: 0.7
        scene_injection_rules:
          - condition: { type: TurnInterval, every_n_turns: 4 }
            event_template: "Rust Brothers scouts spotted near the settlement perimeter"
```

The `FactionAgenda` evaluator checks conditions against current game state and returns
`Vec<FactionEvent>` for the scene directive formatter.

## Scope Boundaries

**In scope:**
- `FactionAgenda`, `InjectionRule`, `InjectionCondition` types
- YAML deserialization from genre pack faction definitions
- `evaluate_agendas()` function: conditions → `Vec<FactionEvent>`
- Unit tests with fixture YAML

**Out of scope:**
- Wiring into scene directives (story 6-5)
- Actual genre pack content (stories 6-7, 6-8)
- Dynamic faction creation by LLM
- Faction relationship tracking between factions

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Deserializable | `FactionAgenda` round-trips through serde YAML |
| Condition eval | `TurnInterval` fires every N turns, `MaturityMinimum` gates on maturity |
| Urgency bounds | Urgency clamped to 0.0-1.0 on deserialization |
| Event generation | `evaluate_agendas()` returns events for factions whose conditions are met |
| No events | Returns empty vec when no conditions are satisfied |
| Multiple rules | A faction with multiple rules can fire multiple events per evaluation |
