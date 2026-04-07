---
parent: context-epic-28.md
---

# Story 28-8: NPC Turns Through Beat System

## Business Context

Story 15-6's original sin: NPCs never mechanically act. The narrator says "the goblin
attacks" but resolve_attack() is never called for the NPC's turn. The current server
(state_mutations.rs:288-383) has a hardcoded NPC turn loop that iterates through
combat_state.turn_order() and calls resolve_attack() for each NPC. This works but is
locked to combat — NPCs can't take beats in negotiation, standoff, or any other
encounter type.

In the unified system, every actor in the encounter gets beat selections per round.
The narrator selects beats for NPCs alongside the player's beats. Dispatch applies
all beat selections in order.

## Technical Approach

### How NPC beats work

The narrator's beat_selections output (from 28-6) includes entries for ALL actors,
not just the player:

```json
{
  "beat_selections": [
    {"actor": "Player", "beat_id": "attack", "target": "Goblin"},
    {"actor": "Goblin", "beat_id": "attack", "target": "Player"},
    {"actor": "Bandit", "beat_id": "attack", "target": "Player"}
  ]
}
```

### Dispatch loop

In state_mutations (the beat dispatch from 28-5), iterate through ALL beat_selections:

```rust
for selection in &beat_selections {
    // 1. Look up the actor (player or NPC)
    // 2. Call apply_beat(selection.beat_id, &def)
    // 3. Dispatch stat_check resolution
    //    - For "attack": find actor's CreatureCore, find target's CreatureCore,
    //      call resolve_attack(), apply HP delta to target
    //    - For other stat_checks: metric_delta already handled by apply_beat
    // 4. Check resolution after each beat
    // 5. Emit OTEL per-actor
}
```

### What this replaces

The current NPC turn loop in state_mutations.rs:288-383:
```rust
let max_npc_turns = ctx.combat_state.turn_order().len();
for _ in 0..max_npc_turns {
    // ... hardcoded resolve_attack for each NPC
}
```

This entire block gets replaced by the generic beat dispatch loop that handles
all actors uniformly.

### NPC beat selection strategy

For combat encounters, NPC default beat is "attack" targeting the player (or
weakest opponent). For social encounters, the narrator chooses based on NPC
disposition and role. The narrator prompt (28-6) presents available beats
for all actors and asks for selections.

If the narrator doesn't provide NPC beat selections (defensive coding), dispatch
should select a default beat for each NPC actor — typically the first non-resolution
beat in the ConfrontationDef.

## Key Files

| File | Action |
|------|--------|
| `sidequest-server/src/dispatch/state_mutations.rs` | Replace hardcoded NPC combat loop with generic actor beat loop |
| `sidequest-agents/src/agents/narrator.rs` | Prompt instructs narrator to select beats for ALL actors |

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| All actors get beats | Beat dispatch loop processes beat_selections for NPCs, not just player | Test: 3-actor encounter, all 3 get beat_selections, all 3 apply_beat calls |
| NPC damage applies | NPC "attack" beat → resolve_attack → player HP decreases | Test: NPC attack beat → player HP before > HP after |
| Player damage applies | Player "attack" beat → resolve_attack → NPC HP decreases | Test: player attack beat → NPC HP before > HP after |
| Default beats | If narrator omits NPC beat selections, NPCs get default beat | Test: empty NPC selections → default beat applied |
| Generic across types | Same loop handles combat, chase, standoff, negotiation actors | Test: negotiation encounter with NPC "pressure" beat → metric changes |
| Old NPC loop removed | Hardcoded NPC combat loop (state_mutations.rs:288-383) is gone | `grep "max_npc_turns" state_mutations.rs` returns nothing |
| OTEL per actor | encounter.npc_beat event with npc_name, beat_id, target, stat_check_result | Grep: WatcherEventBuilder "npc_beat" |
| Death check | Player death during NPC beats ends encounter | Test: NPC attack reduces player to 0 HP → encounter resolves |
| Victory check | All NPC HP at 0 during combat → encounter resolves as victory | Test: last NPC killed → encounter.resolved = true |

## Scope Boundaries

**In scope:** Generic actor beat loop, NPC beat defaults, replacing hardcoded NPC combat loop
**Out of scope:** Multiplayer (multiple players as actors) — future work
