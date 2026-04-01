---
parent: context-epic-18.md
workflow: tdd
---

# Story 18-2: Fix State Tab — Wire GameStateSnapshot to Dashboard Listener

## Business Context

The OTEL dashboard State tab has never worked. It permanently displays "Waiting for
GameStateSnapshot event..." despite the API correctly emitting snapshot data after
every turn. The GM panel's state explorer is a critical debugging tool — it shows the
full game state tree and turn-over-turn diffs, which is the only way to verify that
subsystems are actually mutating state vs Claude just narrating convincingly.

## Technical Approach

### Root Cause

Event type naming mismatch between emitter and listener:

- **API emits:** `WatcherEventType::GameStateSnapshot` which serializes to `"game_state_snapshot"` via serde snake_case
- **Dashboard expects:** `event.event_type === "state_transition"` (useDashboardSocket.ts:139)

The filter never matches. Snapshots arrive over the WebSocket but are silently discarded
into the raw event stream (visible in the Console tab as uncorrelated events).

### Fix

Update the dashboard listener to match the actual event type:

```typescript
// useDashboardSocket.ts:139
// From:
if (event.event_type === "state_transition" && event.fields.snapshot) {
// To:
if (event.event_type === "game_state_snapshot" && event.fields.snapshot) {
```

### Verification

The API emit code (dispatch/mod.rs:1461-1469) already sends a well-formed event with:
- `component: "game"`
- `event_type: GameStateSnapshot`
- `fields.turn_number` (for turn correlation)
- `fields.snapshot` (full game state JSON)

The `findOrCreateTurn` function (useDashboardSocket.ts:27-51) already sets
`previousSnapshot` from the prior turn, so the DiffViewer will work automatically
once snapshots start flowing.

### Key Files

| File | Change |
|------|--------|
| `sidequest-ui/src/components/Dashboard/hooks/useDashboardSocket.ts` | Fix event type string on line 139 |
| `sidequest-api/crates/sidequest-server/src/lib.rs` | No change — enum is correct |
| `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` | No change — emit is correct |

## Scope Boundaries

**In scope:**
- Fix the event type string match in useDashboardSocket.ts
- Verify State tab renders tree view after a turn completes
- Verify Diff view shows state changes between consecutive turns

**Out of scope:**
- Adding new fields to the GameStateSnapshot
- Changing the snapshot structure or content
- State tab UI enhancements (filtering, search improvements)

## Acceptance Criteria

1. **State tab shows game state** — after completing at least one turn, the State tab
   displays a JSON tree of the full game state (not "Waiting for GameStateSnapshot")
2. **Tree view navigable** — state tree is expandable/collapsible with search filtering
3. **Diff view works** — after two+ turns, Diff view highlights state changes between
   selected turns
4. **Turn selector populated** — dropdown shows all turns with snapshots, labeled by
   turn number and classified intent
5. **Console tab confirms** — raw events in Console tab show `game_state_snapshot` events
   being received and correlated to turns
