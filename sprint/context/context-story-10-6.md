---
parent: context-epic-10.md
---

# Story 10-6: World State Agent Proposes OCEAN Shifts — Game Events Trigger Personality Evolution

## Business Context

The world state agent already runs after each turn to propose state mutations (location changes,
quest updates). This story extends it to also propose OCEAN personality shifts when game events
warrant them. A betrayal might lower agreeableness; a heroic rescue might raise neuroticism
(less fear). The agent judges significance — not every turn triggers a shift.

**Python reference:** `sq-2/sidequest/orchestrator.py` — world state response JSON gained
an `ocean_shifts` array. Rust adds the field to `WorldStatePatch`.

**Depends on:** Story 10-5 (shift log and apply_shift method).

## Technical Approach

### WorldStatePatch Extension

```rust
#[derive(Deserialize)]
pub struct WorldStatePatch {
    // ... existing fields (location, quests, etc.)
    #[serde(default)]
    pub ocean_shifts: Vec<ProposedOceanShift>,
}

#[derive(Deserialize)]
pub struct ProposedOceanShift {
    pub npc_name: String,
    pub dimension: OceanDimension,
    pub delta: f64,
    pub cause: String,
}
```

### Agent Prompt Addition

The world state agent's system prompt gains:

```
If a significant event would change an NPC's personality, propose an OCEAN shift.
Only propose shifts for major events — not routine interactions.
Keep deltas small (±0.5 to ±2.0). Personality changes are gradual.
Format: { "npc_name": "...", "dimension": "agreeableness", "delta": -1.5,
          "cause": "betrayed by the party after promising safe passage" }
```

### Patch Application

```rust
fn apply_ocean_shifts(&mut self, shifts: &[ProposedOceanShift], turn_id: u64) {
    for proposed in shifts {
        if let Some(npc) = self.state.find_npc_mut(&proposed.npc_name) {
            let shift = npc.ocean.apply_shift(
                proposed.dimension, proposed.delta, &proposed.cause, turn_id,
            );
            npc.ocean_shifts.push(shift);
        }
        // Unknown NPC name: log warning, skip
    }
}
```

### Guardrails

- Delta clamped to ±3.0 maximum per shift (even if agent proposes larger)
- Maximum 2 shifts per turn (prevents personality rewrite in one event)
- Unknown NPC names logged and skipped, not fatal

## Scope Boundaries

**In scope:**
- `ocean_shifts` field on `WorldStatePatch`
- `ProposedOceanShift` deserialization from agent JSON
- World state agent prompt addition for proposing shifts
- Guardrails: max delta, max shifts per turn
- Graceful handling of unknown NPC names

**Out of scope:**
- Player-initiated personality changes
- Multi-turn trend detection ("NPC has been getting more aggressive")
- Shift notifications to player/UI

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Patch parsed | WorldStatePatch with `ocean_shifts` array deserializes correctly |
| Shift applied | Proposed shift updates NPC's OceanProfile and shift log |
| Delta clamped | Proposed delta of ±5.0 is clamped to ±3.0 |
| Rate limited | Only first 2 shifts per turn are applied; extras are logged and dropped |
| Unknown NPC | Shift targeting nonexistent NPC logs warning, does not error |
| Prompt present | World state agent system prompt includes OCEAN shift instructions |
| No shift | Turn with no personality-relevant events produces empty `ocean_shifts` array |
