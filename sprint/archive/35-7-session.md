---
story_id: "35-7"
jira_key: null
epic: "35"
workflow: "tdd"
---
# Story 35-7: Wire tactical_grid population into connect.rs room-graph branch

## Story Details
- **ID:** 35-7
- **Jira Key:** None (local workflow)
- **Epic:** 35 — Treasure XP Integration — Affinity-Based Gold Reward Wiring
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p0
- **Type:** chore

## Acceptance Criteria

1. In connect.rs room-graph branch, tactical_grid is populated via build_room_graph_explored() / parse_room_grid()
2. Verify full pipeline: RoomDef.grid → TacticalGrid::parse() → tactical_grid_to_payload() → ExploredLocation.tactical_grid
3. Emit WatcherEventBuilder("tactical_grid", StateTransition) when grid populated
4. Integration test: load room with ASCII grid, assert ExploredLocation.tactical_grid is Some
5. Region-mode None values in dispatch/mod.rs remain unchanged
6. Wiring test: tactical_grid population has a non-test consumer in connect.rs

## Context

`tactical_grid: None` in `dispatch/connect.rs:368` should call `build_room_graph_explored()` when room graph is available. The parsing pipeline (RoomDef → TacticalGrid::parse() → tactical_grid_to_payload()) already exists in `room_movement.rs:173-273`. Other `None` locations in dispatch/mod.rs:1089 and 2604 are CORRECT for region mode — they should stay None.

**Key files:**
- `sidequest-api/crates/sidequest-server/src/dispatch/connect.rs` — replace None at line 368
- `sidequest-api/crates/sidequest-game/src/room_movement.rs` — verify build_room_graph_explored() calls parse_room_grid()

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-04-09T16:07Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-09T16:07Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings yet.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

No deviations yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
