---
parent: context-epic-7.md
---

# Story 7-3: Clue Activation — Semantic Trigger Evaluation for Clue Availability Based on Game State

## Business Context

Clues shouldn't just appear — they activate when conditions are met. The bloody glove
becomes discoverable only after the player visits the crime scene and the guard hasn't
cleaned it up yet. Python's `clue_activation.py` evaluated semantic triggers against game
state to determine which clues are available. The Rust port makes trigger conditions
exhaustively typed so new trigger types produce compile errors until handled.

**Python ref:** `sq-2/sidequest/scenario/clue_activation.py`
**Depends on:** Story 7-1 (BeliefState model — activated clues become facts)

## Technical Approach

Clues are defined in scenario YAML with semantic triggers:

```rust
pub struct Clue {
    pub id: String,
    pub description: String,
    pub trigger: SemanticTrigger,
    pub reveals: FactKind,
    pub activated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SemanticTrigger {
    StateMatch {
        requires: Vec<String>,   // state flags that must be present
        excludes: Vec<String>,   // state flags that must be absent
    },
    NpcInteraction {
        npc_id: String,
        interaction_type: InteractionType,  // Talk, Examine, Accuse
    },
    LocationVisit {
        location_id: String,
    },
    TurnThreshold {
        minimum_turn: u64,
    },
    Compound {
        all: Vec<SemanticTrigger>,  // all must match
    },
}

pub fn evaluate_triggers(
    clues: &mut [Clue],
    state: &GameSnapshot,
) -> Vec<ActivatedClue> {
    clues.iter_mut()
        .filter(|c| !c.activated)
        .filter(|c| c.trigger.matches(state))
        .map(|c| {
            c.activated = true;
            ActivatedClue::from(c)
        })
        .collect()
}
```

The `matches()` method on `SemanticTrigger` evaluates recursively for `Compound` triggers.
Each trigger variant has clear semantics — no stringly-typed condition parsing.

Activated clues are injected into the narrator context so the player can discover them
through roleplay.

## Scope Boundaries

**In scope:**
- `Clue`, `SemanticTrigger`, `ActivatedClue` types
- `evaluate_triggers()` function
- `matches()` implementation for each trigger variant
- YAML deserialization of clue definitions
- Unit tests with varied trigger combinations

**Out of scope:**
- How activated clues appear in narration (narrator prompt concern)
- Accusation system (story 7-4)
- Clue graph visualization

## Acceptance Criteria

| AC | Detail |
|----|--------|
| StateMatch trigger | Requires present flags and absent excludes to activate |
| NpcInteraction trigger | Fires when player interacts with specific NPC |
| LocationVisit trigger | Fires when player enters specified location |
| Compound trigger | All sub-triggers must match for compound to match |
| One-shot activation | A clue activates once and stays activated |
| YAML deserialization | Clue definitions with triggers deserialize from scenario YAML |
| No false activation | Clue with unmet trigger stays inactive |
