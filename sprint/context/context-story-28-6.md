---
parent: context-epic-28.md
---

# Story 28-6: Narrator Outputs Beat Selections Instead of CombatPatch

## Business Context

creature_smith is not a separate agent — it's a mode of the narrator that produces
CombatPatch JSON when `TurnContext.in_combat` is true. The dialectician produces
ChasePatch when `in_chase` is true. Both patch types are agent output formats that
the server applies to CombatState/ChaseState.

In the unified system, the narrator outputs beat selections. When an encounter is
active, the narrator's JSON output includes `beat_selections` — an array of
`{actor, beat_id, target?}` objects. The server dispatches these via apply_beat()
(wired in 28-5).

## Technical Approach

### What changes in the narrator prompt

When an encounter is active, format_encounter_context() (wired in 28-4) already tells
the narrator what beats are available. The narrator's output format needs to change:

**Before:**
```json
{
  "in_combat": true,
  "hp_changes": {"Goblin": -12},
  "turn_order": ["Player", "Goblin"],
  "drama_weight": 0.8
}
```

**After:**
```json
{
  "beat_selections": [
    {"actor": "Player", "beat_id": "attack", "target": "Goblin"}
  ]
}
```

### Where the prompt is assembled

- `narrator.rs` — `build_combat_context()` (line 262) and `build_chase_context()` (line 272)
  inject combat/chase-specific rules. Replace with a unified `build_encounter_context()`
  that explains the beat system.
- `orchestrator.rs` — `build_narrator_prompt_tiered()` calls build_combat_context when
  `turn_ctx.in_combat`. Change to check for active encounter and call build_encounter_context.
- `narrator.rs` — `build_output_format()` defines the JSON schema the narrator must produce.
  Add beat_selections to the schema. Remove CombatPatch fields (in_combat, hp_changes,
  turn_order, drama_weight, advance_round).

### Where the output is extracted

- `orchestrator.rs:759` — `extract_fenced_json::<CombatPatch>()` extracts CombatPatch.
  Replace with extraction of beat_selections.
- `orchestrator.rs:765` — `extract_fenced_json::<ChasePatch>()` extracts ChasePatch.
  Remove.
- `orchestrator.rs:989` — `extract_combat_from_game_patch()` maps game_patch fields to
  CombatPatch. Remove or replace with beat_selection extraction from game_patch.

### Intent routing change

IntentRouter (intent_router.rs) routes to creature_smith when in_combat. In the unified
system, ALL encounters go through the narrator. IntentRouter no longer needs to
distinguish combat vs exploration — the narrator handles both. The encounter context
in the prompt tells the narrator what beats are available.

This simplifies IntentRouter significantly: it only needs to detect in_encounter (any
active StructuredEncounter) and ensure the narrator gets encounter context.

## Key Files

| File | Action |
|------|--------|
| `sidequest-agents/src/agents/narrator.rs` | Replace build_combat_context/build_chase_context with build_encounter_context. Update output schema. |
| `sidequest-agents/src/orchestrator.rs` | Replace CombatPatch/ChasePatch extraction with beat_selection extraction. Update build_narrator_prompt_tiered. |
| `sidequest-agents/src/agents/intent_router.rs` | Simplify: in_encounter → narrator with encounter context |

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| Beat output schema | Narrator JSON schema includes beat_selections array | Grep: "beat_selections" in narrator.rs output format |
| No CombatPatch output | Narrator no longer produces CombatPatch fields | `grep "in_combat.*hp_changes" narrator.rs` returns nothing |
| No ChasePatch output | Narrator no longer produces ChasePatch fields | `grep "in_chase.*separation_delta" narrator.rs` returns nothing |
| Extraction works | Orchestrator extracts beat_selections from narrator JSON into ActionResult | Test: mock narrator response with beat_selections → ActionResult.beat_selections is Some |
| Unified encounter rules | build_encounter_context() replaces build_combat_context + build_chase_context | Grep: "build_encounter_context" in narrator.rs, "build_combat_context" does NOT exist |
| IntentRouter simplified | IntentRouter checks in_encounter, not in_combat/in_chase separately | Code review: IntentRouter no longer has separate Combat/Chase branches |
| OTEL | encounter.agent_beat_selection event with actor, beat_id, encounter_type | Grep: WatcherEventBuilder "agent_beat_selection" in orchestrator.rs |
| Wiring | beat_selections flows from narrator output → extraction → ActionResult → dispatch | Trace: narrator JSON → orchestrator extract → ActionResult.beat_selections → state_mutations |

## Scope Boundaries

**In scope:** Narrator prompt changes, output schema changes, extraction changes, IntentRouter simplification
**Out of scope:** Removing old CombatPatch/ChasePatch types (28-9), changing GameSnapshot (28-7)
