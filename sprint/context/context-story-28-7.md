---
parent: context-epic-28.md
---

# Story 28-7: StructuredEncounter on GameSnapshot — Replace combat and chase Fields

## Business Context

GameSnapshot (`state.rs:130-139`) currently has three encounter-related fields:
```rust
pub combat: CombatState,          // line 130 — always present, default
pub chase: Option<ChaseState>,    // line 134
pub encounter: Option<StructuredEncounter>,  // line 139
```

After 28-5 and 28-6, the beat dispatch pipeline runs through StructuredEncounter.
But the server dispatch still reads/writes `ctx.combat_state` and `ctx.chase_state`
everywhere. This story makes `encounter: Option<StructuredEncounter>` the sole
encounter field and updates all dispatch references.

## Technical Approach

### GameSnapshot changes (state.rs)
- Remove `pub combat: CombatState`
- Remove `pub chase: Option<ChaseState>`
- Keep `pub encounter: Option<StructuredEncounter>`
- Remove imports of CombatState, ChaseState, ChaseType, ChaseActor, RigType, RigStats

### DispatchContext changes (dispatch/mod.rs)
Currently has:
```rust
combat_state: &'a mut CombatState,
chase_state: &'a mut Option<ChaseState>,
```
Replace with:
```rust
encounter: &'a mut Option<StructuredEncounter>,
```

### Dispatch references to update

Every `ctx.combat_state.*` and `ctx.chase_state.*` call in dispatch/ needs to change:

| Current | New |
|---------|-----|
| `ctx.combat_state.in_combat()` | `ctx.encounter.as_ref().map_or(false, \|e\| e.encounter_type == "combat" && !e.resolved)` |
| `ctx.combat_state.engage(combatants)` | Start a new StructuredEncounter from ConfrontationDef |
| `ctx.combat_state.disengage()` | Set `encounter.resolved = true` then `ctx.encounter = None` |
| `ctx.combat_state.resolve_attack(...)` | Called from beat dispatch (28-5), not directly |
| `ctx.chase_state.is_some()` | `ctx.encounter.as_ref().map_or(false, \|e\| e.encounter_type == "chase")` |

### Convenience methods

Add helper methods on StructuredEncounter or DispatchContext:
- `is_in_encounter() -> bool`
- `is_combat() -> bool` — encounter_type == "combat"
- `is_chase() -> bool` — encounter_type == "chase"
- `start_encounter(def: &ConfrontationDef, actors: Vec<EncounterActor>)`
- `end_encounter()`

### Files that reference combat_state / chase_state in dispatch/

Found via grep — every one needs updating:
- `dispatch/mod.rs` — DispatchContext fields, multiple reads/writes
- `dispatch/state_mutations.rs` — CombatPatch/ChasePatch application (lines 28-400+)
- `dispatch/combat.rs` — process_combat_and_chase() (121 LOC)
- `dispatch/prompt.rs` — encounter context injection (lines 335-374)
- `dispatch/audio.rs` — mood context (lines 19-49)
- `dispatch/session_sync.rs` — state sync (line 48)
- `dispatch/connect.rs` — session initialization

## Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/state.rs` | Remove combat/chase fields, keep encounter |
| `sidequest-server/src/dispatch/mod.rs` | Update DispatchContext, all combat_state/chase_state refs |
| `sidequest-server/src/dispatch/state_mutations.rs` | Replace CombatPatch/ChasePatch application with encounter ops |
| `sidequest-server/src/dispatch/combat.rs` | Rewrite or delete — tick effects move to encounter |
| `sidequest-server/src/dispatch/prompt.rs` | Already done in 28-4 if properly wired |
| `sidequest-server/src/dispatch/audio.rs` | Read encounter instead of combat_state/chase_state |
| `sidequest-server/src/dispatch/session_sync.rs` | Sync encounter instead of combat/chase |

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| No combat field | GameSnapshot no longer has `combat: CombatState` | `grep "pub combat:" state.rs` returns nothing |
| No chase field | GameSnapshot no longer has `chase: Option<ChaseState>` | `grep "pub chase:" state.rs` returns nothing |
| Encounter sole field | `pub encounter: Option<StructuredEncounter>` is the only encounter field | Grep confirms |
| No combat_state in dispatch | `ctx.combat_state` does not appear in dispatch/ | `grep "combat_state" dispatch/ -r` returns nothing |
| No chase_state in dispatch | `ctx.chase_state` does not appear in dispatch/ | `grep "chase_state" dispatch/ -r` returns nothing |
| Audio reads encounter | dispatch/audio.rs reads from ctx.encounter | Grep: "encounter" in audio.rs |
| Session sync | dispatch/session_sync.rs syncs encounter | Grep: "encounter" in session_sync.rs |
| Builds clean | `cargo build -p sidequest-server` succeeds | Build verification |
| Tests pass | `cargo test -p sidequest-server` — existing tests updated | Test verification |
| OTEL | encounter.started and encounter.ended events on engage/disengage | Grep: WatcherEventBuilder "encounter.started" |

## Scope Boundaries

**In scope:** GameSnapshot field change, all dispatch/ reference updates
**Out of scope:** Deleting CombatState/ChaseState source files (28-9), NPC turns (28-8)
