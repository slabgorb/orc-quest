---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-7: personality_event, resource_change, play_sfx tools

## Business Context

Final batch of reactive tool migrations before the JSON block can be eliminated. Three lower-frequency fields that each follow the same pattern: narrator detects significance → calls tool → tool validates and structures.

## Technical Guardrails

- **`personality_event`**: takes npc name, event_type (enum: betrayal, near_death, victory, defeat, social_bonding), description. Returns `PersonalityEvent` JSON. Only fires on significant moments, not routine interactions.
- **`resource_change`**: takes resource name, delta (signed f64). Validates resource name against genre's `ResourceDeclaration` names. Returns `{"resource": "luck", "delta": -1.0}`.
- **`play_sfx`**: takes SFX ID string. Validates against the SFX library already loaded in the prompt context. Returns `{"sfx_id": "sword_clash"}`.
- All three are low-frequency — most turns won't invoke any of them. The narrator prompt adds one-line tool descriptions.
- `assemble_turn` collects into `ActionResult.personality_events`, `ActionResult.resource_deltas`, `ActionResult.sfx_triggers`.

## Scope Boundaries

**In scope:**
- Three tools: `personality_event`, `resource_change`, `play_sfx`
- Remove personality_events, resource_deltas, sfx_triggers JSON schemas from narrator prompt
- `assemble_turn` integration for all three
- OTEL events

**Out of scope:**
- Changing the struct types for any of these fields
- OCEAN shift pipeline (consumes personality_events downstream — no changes needed)
- Audio mixer (consumes sfx_triggers downstream — no changes needed)

## AC Context

1. `personality_event` validates event_type enum and returns `PersonalityEvent` JSON
2. `resource_change` validates resource name against genre declarations and returns delta JSON
3. `play_sfx` validates SFX ID against loaded library and returns trigger JSON
4. All three removed from narrator JSON schema documentation
5. `assemble_turn` collects all three into their respective ActionResult fields
6. OTEL spans for each invocation
