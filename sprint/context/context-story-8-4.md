---
parent: context-epic-8.md
---

# Story 8-4: Party Action Composition — Compose Multi-Character PARTY ACTIONS Block

## Business Context

The orchestrator expects a single input block per turn. In multiplayer, multiple players
submit independent actions that must be composed into a `[PARTY ACTIONS]` block before
the orchestrator processes the turn. Python builds this as a formatted string. Rust
structures it with types and renders to the orchestrator's expected format.

**Python source:** `sq-2/sidequest/game/turn_manager.py` (compose_party_actions)
**Depends on:** Story 8-2 (TurnBarrier provides collected actions)

## Technical Approach

After the barrier resolves, compose the collected actions into a structured block:

```rust
pub struct PartyActions {
    pub actions: Vec<CharacterAction>,
    pub turn_number: u64,
}

pub struct CharacterAction {
    pub character_name: String,
    pub character_id: CharacterId,
    pub input: String,
    pub is_default: bool,  // true if player timed out
}

impl PartyActions {
    pub fn from_barrier_result(
        result: BarrierResult,
        players: &HashMap<PlayerId, PlayerSlot>,
        characters: &HashMap<CharacterId, Character>,
    ) -> Self {
        // Map player actions to character actions, fill defaults for missing
        // ...
    }

    pub fn render(&self) -> String {
        let mut block = String::from("[PARTY ACTIONS]\n");
        for action in &self.actions {
            let suffix = if action.is_default { " (waiting)" } else { "" };
            block.push_str(&format!(
                "- {}: {}{}\n",
                action.character_name, action.input, suffix
            ));
        }
        block
    }
}
```

The rendered block feeds into the orchestrator's `process_turn()` as the input string,
replacing the single-player input. The orchestrator does not need to know whether the
input came from one player or many — it receives text and processes it.

## Scope Boundaries

**In scope:**
- `PartyActions` struct collecting character-attributed actions
- `from_barrier_result()` mapping player IDs to character names
- `render()` producing the `[PARTY ACTIONS]` text block
- Default action text for timed-out players
- Integration point with orchestrator input

**Out of scope:**
- Action validation or conflict resolution between players
- Action ordering or priority within the block
- Narrator-specific formatting (the narrator prompt handles presentation)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Composition | Barrier result mapped to named character actions |
| Default fill | Timed-out players get "(waiting)" default action |
| Render format | Output matches `[PARTY ACTIONS]` block format |
| Character names | Actions attributed to character names, not player IDs |
| Orchestrator input | Rendered block accepted by orchestrator as turn input |
| Turn number | PartyActions tracks which turn it belongs to |
