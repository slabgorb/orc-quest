---
parent: context-epic-16.md
---

# Story 16-5: Migrate Chase as Confrontation — Bridge Pattern

## Business Context

The chase system (1,188 LOC across chase.rs + chase_depth.rs) was the prototype for
StructuredEncounter. This story ensures chase state is expressible through the
StructuredEncounter model for narrator prompt injection, UI rendering, and save/load
compatibility — while keeping ChaseState as the authoritative owner of chase game
mechanics.

## Architectural Decision: Bridge, Not Replacement

**ChaseState stays.** It owns chase-specific game logic: advance_beat(), record_roll(),
terrain damage, rig damage, format_context(), outcome checking. These are chase
*mechanics*, not generic encounter operations.

**StructuredEncounter is the universal snapshot format.** It's how encounters appear in
narrator prompts, UI overlays, and cross-system communication. The conversion functions
(`from_chase_state()`, `chase()`) translate between the domain model and the snapshot.

**Why not type alias?** Making `ChaseState = StructuredEncounter` would force all chase
mechanics into encounter.rs — terrain modifiers, rig damage tiers, cinematography,
beat decisions — turning the generic encounter module into a chase-specific god module.
The bridge pattern keeps concerns separated: chase.rs + chase_depth.rs own mechanics,
encounter.rs owns the universal snapshot format.

**Pattern:** Same as 16-4 (combat migration). CombatState stays as the combat domain
model; `from_combat_state()` converts to StructuredEncounter for snapshot purposes.

## Current State (What's Done)

All core bridge infrastructure is implemented and tested (39 tests passing):

| Component | Status | File |
|-----------|--------|------|
| `StructuredEncounter::chase()` constructor | Done | encounter.rs:208 |
| `StructuredEncounter::from_chase_state()` | Done | encounter.rs:345 |
| `SecondaryStats::from_rig_stats()` | Done | encounter.rs:98 |
| `SecondaryStats::rig()` convenience | Done | encounter.rs:90 |
| `GameSnapshot.encounter` field | Done | state.rs:135 |
| All 5 rig archetypes convert | Done | tested |
| Serde roundtrip (encounter + snapshot) | Done | tested |
| Phase/drama weight parity | Done | tested |
| ChaseState behavioral regression | Done | tested |

## What Remains

The bridge exists but isn't **wired into the dispatch pipeline**. When a chase is
active, the narrator prompt still reads from `ChaseState` directly. The encounter
snapshot isn't populated during gameplay, only available via explicit conversion.

### AC-1: Dispatch wiring — chase auto-populates encounter snapshot

During dispatch, when `ctx.chase_state` is `Some`, automatically convert to
`StructuredEncounter` and set `ctx.snapshot.encounter`. This ensures:
- The narrator sees chase state through the universal encounter format
- The UI can render chase state through the generic EncounterOverlay (story 16-9)
- Save files include both `chase` (for game mechanics) and `encounter` (for snapshot)

**Location:** `sidequest-server/src/dispatch/mod.rs` — after chase state mutations,
before prompt building.

### AC-2: Narrator prompt uses encounter format

The narrator prompt should include chase state in the `<game_state>` section via the
StructuredEncounter format when a chase is active. This replaces or supplements
the existing `format_chase_context()` output with the generic encounter representation.

**Key:** The StructuredEncounter snapshot provides a universal format that works for
ALL encounter types. Once the narrator sees chases through this format, it's the same
format it will see for standoffs, poker games, and Russian roulette.

### AC-3: Backward-compatible save/load

Old saves with `chase` field but no `encounter` field must load correctly. On load,
if `chase` is Some and `encounter` is None, auto-populate encounter from chase state.

**Already partially done:** Both fields coexist in GameSnapshot. The auto-populate
on load is the remaining piece.

### AC-4: All existing tests pass

No behavioral changes to ChaseState. All 39 existing 16-5 tests continue to pass.
All chase.rs and chase_depth.rs tests continue to pass.

### AC-5: OTEL observability

When the encounter snapshot is populated from chase state, emit a watcher event:
`encounter.synced_from_chase` with the encounter_type, metric values, and phase.

## Acceptance Criteria

| AC | Detail |
|----|--------|
| AC-1 | Dispatch auto-populates `snapshot.encounter` from active chase state |
| AC-2 | Narrator prompt includes chase as StructuredEncounter in game_state |
| AC-3 | Old saves without encounter field auto-populate from chase on load |
| AC-4 | All existing chase, chase_depth, and 16-5 tests pass (no regressions) |
| AC-5 | OTEL watcher event on encounter sync from chase state |

## Key Files

| File | Action |
|------|--------|
| `sidequest-server/src/dispatch/mod.rs` | Wire chase → encounter sync after chase mutations |
| `sidequest-game/src/encounter.rs` | No changes needed (bridge already exists) |
| `sidequest-game/src/chase.rs` | No changes needed |
| `sidequest-game/src/state.rs` | Add auto-populate on deserialization (AC-3) |
| `sidequest-game/src/persistence.rs` | Verify save/load handles both fields |
| `sidequest-game/tests/chase_as_confrontation_story_16_5_tests.rs` | Add tests for AC-1,2,3,5 |
