---
parent: context-epic-7.md
---

# Story 7-5: NPC Autonomous Actions — Scenario-Driven NPC Behaviors (Alibi, Confess, Flee, Destroy Evidence)

## Business Context

NPCs in a scenario shouldn't be passive witnesses waiting to be questioned. The guilty
NPC should try to create an alibi, a nervous NPC might flee, and a cornered NPC might
confess. These autonomous actions happen between turns based on the NPC's BeliefState and
the scenario's tension level. In Python, `npc_actions.py` used a priority-weighted action
selection. The Rust port makes the action set an enum with explicit preconditions.

**Python ref:** `sq-2/sidequest/scenario/npc_actions.py`
**Depends on:** Story 7-1 (BeliefState — NPC knowledge drives action selection)

## Technical Approach

```rust
pub enum NpcAction {
    CreateAlibi { false_claim: Claim },
    DestroyEvidence { clue_id: String },
    Flee { destination: String },
    Confess { to_npc: Option<String> },
    ActNormal,  // do nothing suspicious
    SpreadRumor { claim: Claim, target_npc: String },
}

pub fn select_npc_action(
    npc_id: &str,
    role: &ScenarioRole,       // Guilty, Witness, Innocent, Accomplice
    belief: &BeliefState,
    tension: f32,
    rng: &mut impl Rng,
) -> NpcAction {
    let options = available_actions(role, belief, tension);
    // Weighted selection: higher tension → more desperate actions
    weighted_select(&options, rng)
}

fn available_actions(
    role: &ScenarioRole,
    belief: &BeliefState,
    tension: f32,
) -> Vec<(NpcAction, f32)> {
    let mut actions = vec![(NpcAction::ActNormal, 1.0 - tension)];

    if *role == ScenarioRole::Guilty {
        actions.push((NpcAction::CreateAlibi { .. }, 0.3 + tension * 0.4));
        if tension > 0.6 {
            actions.push((NpcAction::DestroyEvidence { .. }, tension * 0.5));
        }
        if tension > 0.8 {
            actions.push((NpcAction::Flee { .. }, tension * 0.3));
            actions.push((NpcAction::Confess { .. }, 0.1));
        }
    }
    // ... witness and accomplice action sets
    actions
}
```

Higher tension makes desperate actions (flee, confess) more likely. The guilty NPC starts
by acting normal, escalates to creating alibis, then destroying evidence, and finally
might flee or confess under extreme pressure.

Actions are resolved by updating BeliefStates (false alibi adds a claim) and game state
(flee changes NPC location, destroy evidence deactivates a clue).

## Scope Boundaries

**In scope:**
- `NpcAction` enum with all action variants
- `select_npc_action()` with weighted selection
- Action resolution: effects on BeliefState and game state
- `ScenarioRole` enum (Guilty, Witness, Innocent, Accomplice)
- Tension-based action availability
- Tests with deterministic RNG

**Out of scope:**
- How actions appear in narration (narrator prompt concern, story 7-9)
- Player-initiated interrogation mechanics
- NPC personality affecting action weights (future enhancement)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Role-based actions | Guilty NPC has access to CreateAlibi, DestroyEvidence, Flee, Confess |
| Tension scaling | Higher tension increases weight of desperate actions |
| Low tension default | At low tension, most NPCs ActNormal |
| Alibi creates claim | CreateAlibi inserts a false claim into the NPC's BeliefState |
| Evidence destruction | DestroyEvidence deactivates a clue (prevents future discovery) |
| Flee changes state | Flee updates NPC location in game state |
| Deterministic test | Seeded RNG produces reproducible action selection |
