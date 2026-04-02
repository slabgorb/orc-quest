---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-6: quest_update tool — quest state transitions

## Business Context

Quest state transitions are the narrator's interpretation of what happened ("the player found the macguffin" → quest status changes). The LLM decides THAT a quest changed. The tool formats the state transition. Currently the narrator emits `quest_updates` as a JSON object keyed by quest name — this is both intent interpretation (LLM) and structured formatting (crunch) mashed together.

## Technical Guardrails

- `quest_update` takes: quest name, new status string. Status follows the existing format: `"active: description (from: NPC)"`, `"completed: outcome"`, `"failed: reason"`.
- Returns structured JSON `{"quest_name": "The Corrupted Grove", "status": "completed: the source was purified"}`.
- Multiple quest updates per turn are possible — narrator calls the tool once per changed quest.
- The referral rule ("never send player back to quest giver") remains in the narrator's behavioral prompt — it's intent judgment, not crunch.
- Remove quest protocol documentation (~100 tokens) from narrator system prompt. Keep referral rule.
- `assemble_turn` collects all `quest_update` calls into `ActionResult.quest_updates` HashMap.

## Scope Boundaries

**In scope:**
- `quest_update` tool
- Remove quest JSON schema from narrator prompt (keep referral rule)
- `assemble_turn` collects quest tool calls into HashMap
- OTEL events per quest update

**Out of scope:**
- Quest state machine (no such thing exists yet — quests are free-form strings)
- Changing the quest_updates HashMap type
- Scenario system (Epic 7)

## AC Context

1. `quest_update` tool accepts quest name and status string, returns structured JSON
2. Narrator calls tool once per changed quest
3. Narrator prompt keeps referral rule but removes quest JSON schema
4. `assemble_turn` collects into `ActionResult.quest_updates`
5. OTEL span per quest update with quest name
