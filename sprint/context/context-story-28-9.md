---
parent: context-epic-28.md
---

# Story 28-9: Delete CombatState, ChaseState, CombatPatch, ChasePatch, All Adapters

## Business Context

After 28-7 (StructuredEncounter on GameSnapshot) and 28-8 (NPC turns through beats),
the old combat and chase systems have zero consumers. This story deletes them. Hard cut.
No compatibility. No adapters. No re-exports.

## Technical Approach

### Files to DELETE entirely

| File | LOC | Reason |
|------|-----|--------|
| `sidequest-game/src/combat.rs` | 420 | CombatState — replaced by StructuredEncounter |
| `sidequest-game/src/chase.rs` | 133 | ChaseState — replaced by StructuredEncounter |
| `sidequest-game/src/chase_depth.rs` | ~900 | RigStats, ChasePhase, cinematography — replaced by SecondaryStats, EncounterPhase |
| `sidequest-server/src/dispatch/combat.rs` | 121 | process_combat_and_chase — replaced by beat dispatch |

### Functions to MOVE before deleting

`resolve_attack()` in combat.rs contains the damage calculation math (level scaling,
defense reduction, stun check). This math is still needed by the "attack" stat_check
resolver. **Move resolve_attack logic** to a `resolution.rs` module in sidequest-game,
or inline it in encounter.rs. The function signature changes — it no longer operates
on CombatState, it takes two CreatureCore references and returns damage.

Similarly, any chase escape/separation math that stat_check resolvers need should be
preserved in encounter.rs or resolution.rs.

### Types to DELETE from patches.rs

```rust
pub struct CombatPatch { ... }  // line 45-61
pub struct ChasePatch { ... }   // line 66-79
```

### Types to DELETE from protocol (message.rs)

- `CombatEventPayload` (and GameMessage::CombatEvent variant)
- Any protocol types only used by CombatEvent

### Fields to DELETE from ActionResult (orchestrator.rs)

```rust
pub combat_patch: Option<CombatPatch>,    // line 34
pub chase_patch: Option<ChasePatch>,      // line 36
```

### Extraction to DELETE from orchestrator.rs

- `extract_fenced_json::<CombatPatch>()` — line 759
- `extract_fenced_json::<ChasePatch>()` — line 765
- `extract_combat_from_game_patch()` — line 989

### Adapters to DELETE from encounter.rs

- `from_combat_state()` — line 278
- `from_chase_state()` — line 347

### UI to DELETE

- `CombatOverlay.tsx` — old combat overlay
- CombatState type import in App.tsx
- COMBAT_EVENT handler in App.tsx
- CombatOverlay rendering in GameLayout.tsx

### Exports to update (lib.rs files)

- sidequest-game/src/lib.rs — remove CombatState, ChaseState, ChaseType exports
- sidequest-agents/src/lib.rs — remove CombatPatch, ChasePatch re-exports
- sidequest-protocol/src/lib.rs — remove CombatEventPayload

### Test files to update or delete

- `sidequest-server/tests/combat_wiring_story_15_6_tests.rs` — DELETE (tests old system)
- `sidequest-game/tests/encounter_story_16_2_tests.rs` — UPDATE (remove from_combat_state tests)
- Any test that constructs CombatState or ChaseState directly

## Key Files

See tables above — this is a large deletion story touching every crate.

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| CombatState gone | `grep -r "CombatState" crates/ --include="*.rs" \| grep -v target \| grep -v test` returns nothing | Verified |
| ChaseState gone | `grep -r "ChaseState" crates/ --include="*.rs" \| grep -v target \| grep -v test` returns nothing | Verified |
| CombatPatch gone | `grep -r "CombatPatch" crates/ --include="*.rs" \| grep -v target \| grep -v test` returns nothing | Verified |
| ChasePatch gone | `grep -r "ChasePatch" crates/ --include="*.rs" \| grep -v target \| grep -v test` returns nothing | Verified |
| from_combat_state gone | `grep "from_combat_state" crates/ -r` returns nothing | Verified |
| from_chase_state gone | `grep "from_chase_state" crates/ -r` returns nothing | Verified |
| CombatOverlay gone | `CombatOverlay.tsx` does not exist | `ls` verification |
| COMBAT_EVENT gone | `grep "COMBAT_EVENT" sidequest-ui/src/ -r` returns nothing | Verified |
| resolve_attack preserved | Attack resolution math exists somewhere (encounter.rs or resolution.rs) | Grep: damage calculation function exists |
| Builds clean | `cargo build` (full workspace) succeeds | Build verification |
| Tests pass | `cargo test` (full workspace) succeeds | Test verification |
| UI builds | `npm run build` in sidequest-ui succeeds | Build verification |
| UI tests pass | `npm test` in sidequest-ui succeeds | Test verification |

## Scope Boundaries

**In scope:** Deleting all old combat/chase code, moving resolution math, updating all imports
**Out of scope:** Adding new functionality — this is pure deletion + moves
