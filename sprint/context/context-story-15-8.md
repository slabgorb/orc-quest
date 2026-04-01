# Story 15-8: Canonical GameSnapshot in dispatch — eliminate load-before-save round-trip on every turn

## Overview

**Problem:** Every player action incurs two actor-channel round-trips to the persistence worker:
1. `persistence().load()` to fetch the previous snapshot from SQLite
2. Merge 15+ local variables into it
3. `persistence().save()` to persist the merged result

This creates unnecessary latency on the hot path (every turn). With 6-player multiplayer, per-player delays compound.

**Solution:** Carry a mutable `GameSnapshot` as the canonical source in `DispatchContext`. Patch it in-place during turn processing. Save it directly without loading first.

**Impact:** Cuts persistence round-trips from 2 to 1 on the hot path (turn processing). Load remains only for session restore (infrequent).

**Priority:** p1 / 5 points

## Key Files & Current Architecture

### Current State: dispatch/mod.rs (lines 1254–1368)

The `persist_game_state()` function currently:
```rust
async fn persist_game_state(ctx, narration_text, clean_narration) {
    // LINE 1267: LOAD round-trip
    match ctx.state.persistence().load(genre, world, player) {
        Ok(Some(saved)) => {
            let mut snapshot = saved.snapshot;
            
            // LINES 1272-1338: Merge 15+ fields into the loaded snapshot
            snapshot.location = extract_location(...);
            snapshot.turn_manager = ctx.turn_manager.clone();
            snapshot.npc_registry = ctx.npc_registry.clone();
            snapshot.genie_wishes = ctx.genie_wishes.clone();
            snapshot.axis_values = ctx.axis_values.clone();
            snapshot.combat = ctx.combat_state.clone();
            snapshot.chase = ctx.chase_state.clone();
            // ... more fields ...
            
            // LINE 1339: SAVE round-trip
            ctx.state.persistence().save(genre, world, player, &snapshot).await
        }
    }
}
```

### DispatchContext: dispatch/mod.rs (lines 45–89)

Currently holds 37 individual fields (all refs/muts):
- State: `hp`, `max_hp`, `level`, `xp`, `current_location`
- Inventory: `inventory`, `character_json`
- Combat: `combat_state`, `chase_state`
- World: `npc_registry`, `turn_manager`, `quest_log`, `trope_states`
- Narrative: `narration_history`, `discovered_regions`, `lore_store`
- Audio: `music_director`, `audio_mixer`
- And more...

**Missing:** No `snapshot: GameSnapshot` field.

### GameSnapshot: sidequest-game/src/state.rs (lines 42–138)

The canonical game state struct (~140 fields covering):
- Characters, NPCs, location, time_of_day
- quest_log, notes, narrative_log
- combat, chase, encounter, active_tropes
- atmosphere, current_region, discovered_regions, discovered_routes
- turn_manager, lore_established, campaign_maturity, world_history
- npc_registry, genie_wishes, axis_values
- achievement_tracker, scenario_state, resource_state

**All fields** that are scattered in DispatchContext as individual locals are composed into GameSnapshot.

### Session Initialization: dispatch/mod.rs dispatch_connect() (lines ~1355–1740)

Currently:
1. Calls `persistence().load()` to fetch the previous snapshot
2. Deserializes genre pack, creates character, etc.
3. Populates DispatchContext with extracted fields
4. **Returns** messages, not the snapshot

After story 15-8:
1. Calls `persistence().load()` → deserializes into `snapshot: GameSnapshot`
2. Creates character, populates world context
3. **Returns** both messages and the snapshot
4. Snapshot is carried forward into `dispatch_player_action()`

### Turn Loop: dispatch_player_action() (lines ~92–4000)

Currently receives a `DispatchContext<'_>` with 37 individual fields. Line 686 calls `persist_game_state(ctx, ...)` which re-loads the entire snapshot just to merge these fields back.

After story 15-8:
1. DispatchContext includes `snapshot: GameSnapshot`
2. As the turn progresses, patch `ctx.snapshot` in-place
3. At turn end, `persist_game_state()` calls `save()` directly without `load()`

## Technical Details

### What Changes

**DispatchContext struct:**
```rust
pub(crate) struct DispatchContext<'a> {
    // ... existing 37 fields ...
    pub snapshot: &'a mut GameSnapshot,  // NEW: canonical game state
}
```

**Merge sites in persist_game_state():**
Instead of merging into a loaded snapshot:
```rust
// OLD (line 1264–1268):
let loaded = ctx.state.persistence().load(...).await;
let mut snapshot = loaded.snapshot;

// NEW:
// No load! Use ctx.snapshot directly.
// It's already been patched throughout the turn.
```

**OTEL instrumentation:**
```rust
async fn persist_game_state(ctx, ...) {
    let start = std::time::Instant::now();
    
    ctx.state.persistence().save(
        ctx.genre_slug,
        ctx.world_slug,
        ctx.player_name_for_save,
        ctx.snapshot,
    ).await?;
    
    let elapsed_ms = start.elapsed().as_millis() as u64;
    ctx.state.send_watcher_event(WatcherEvent {
        component: "persistence".to_string(),
        event_type: WatcherEventType::Subsystem,
        fields: {
            let mut f = HashMap::new();
            f.insert("save_latency_ms".to_string(), json!(elapsed_ms));
            f
        },
    });
}
```

## Implementation Plan

### Phase 1: Modify DispatchContext & dispatch_player_action signature
1. Add `snapshot: &'a mut GameSnapshot` to DispatchContext
2. Find all call sites of `dispatch_player_action()` in `lib.rs`
3. Ensure caller populates the snapshot from `dispatch_connect()` result

### Phase 2: Migrate patching from locals to snapshot
1. Identify all lines in `dispatch_player_action()` that mutate loose locals (hp, inventory, etc.)
2. Add equivalent mutations to `ctx.snapshot`
3. Maintain any locals needed for intermediate calculations, but sync final state to snapshot

### Phase 3: Rewrite persist_game_state()
1. Remove lines 1264–1268 (load round-trip)
2. Change merge logic (lines 1272–1338) to simple direct access
3. Call `state.persistence().save(ctx.snapshot)` directly (lines 1342–1348)
4. Add OTEL span `persistence.save_latency_ms`

### Phase 4: Session restore (dispatch_connect)
1. Keep `persistence().load()` call — this is infrequent and necessary
2. Ensure loaded snapshot is returned/propagated to dispatch_player_action

### Phase 5: Testing
1. **Unit test:** Verify persist_game_state() never calls load on the save path
2. **Integration test:** Multi-turn game with latency measurement before/after
3. **Wiring test:** Confirm OTEL event is emitted on each persist call
4. **Multiplayer test:** 6-player session shows latency improvement

## Wiring Checklist

- [ ] `persist_game_state()` is called from line 686 in dispatch_player_action
- [ ] `dispatch_player_action()` called from `lib.rs` dispatch handler
- [ ] Snapshot initialization in `dispatch_connect()` → passed to first `dispatch_player_action()`
- [ ] OTEL event `persistence.save_latency_ms` emitted and visible in watcher
- [ ] Tests verify: no load on hot path, save still succeeds
- [ ] Tests verify: session reconnect (dispatch_connect) still loads for restoration

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Keep load on reconnect** | Necessary for session restoration; infrequent path, not a bottleneck |
| **Patch snapshot in-place** | Avoids clone overhead; snapshot is already mutable |
| **OTEL before/after latency** | Proves the optimization works; GM can see the improvement |
| **No behavioral change to clients** | Game logic unchanged, only persistence architecture |

## Acceptance Criteria

1. [ ] `persist_game_state()` does NOT call `persistence().load()` on the save path
2. [ ] OTEL span `persistence.save_latency_ms` emits on every turn
3. [ ] Multi-turn session completes without errors
4. [ ] Session restore on reconnect still works (loads from SQLite)
5. [ ] Unit tests pass; integration tests show latency reduction
6. [ ] Code review confirms: no silent fallbacks, proper error handling

## Related Stories

**Dependent stories:**
- **15-9 (Wire narrative_log SQLite table)** — depends on 15-8, uses the canonical snapshot for narrative appending
- **15-20 (Wire StateDelta computation)** — will snapshot before turn, compute delta, broadcast

**Related debt items:**
- Epic 15 overall: eliminate scattered local state pattern
- 15-9, 15-11, 15-12, 15-13, 15-14, 15-15, 15-16, 15-17 all use the canonical snapshot pattern

## Reference

| File | Role |
|------|------|
| `crates/sidequest-server/src/dispatch/mod.rs:45–89` | DispatchContext struct |
| `crates/sidequest-server/src/dispatch/mod.rs:92–4000` | dispatch_player_action() |
| `crates/sidequest-server/src/dispatch/mod.rs:1254–1368` | persist_game_state() |
| `crates/sidequest-game/src/state.rs:42–138` | GameSnapshot struct |
| `crates/sidequest-server/src/lib.rs` | dispatch_player_action call sites |
| `sprint/epic-15.yaml` | Full epic definition |
