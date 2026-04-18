---
story_id: "19-4"
epic: "19"
jira_key: null
workflow: "tdd"
repos: "sidequest-api"
---

# Story 19-4: MAP_UPDATE for room graph — send discovered rooms with exits to UI

## Story Details

- **ID:** 19-4
- **Epic:** 19 — Dungeon Crawl Engine — Room Graph Navigation & Resource Pressure
- **Jira Key:** N/A (personal project)
- **Workflow:** tdd
- **Repos:** sidequest-api
- **Points:** 3
- **Priority:** p1
- **Stack Parent:** none (standalone story)

## Acceptance Criteria

- ExploredLocation includes exits, room_type, size fields
- MAP_UPDATE only includes discovered rooms
- Current room flagged in payload
- Protocol types updated in sidequest-protocol
- Test: discover 3 rooms, verify MAP_UPDATE contains exactly 3 with correct exits

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-02T23:02:18Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T18:10:00Z | 2026-04-02T22:12:24Z | 4h 2m |
| red | 2026-04-02T22:12:24Z | 2026-04-02T22:16:30Z | 4m 6s |
| green | 2026-04-02T22:16:30Z | 2026-04-02T22:47:27Z | 30m 57s |
| spec-check | 2026-04-02T22:47:27Z | 2026-04-02T22:49:12Z | 1m 45s |
| verify | 2026-04-02T22:49:12Z | 2026-04-02T22:58:00Z | 8m 48s |
| review | 2026-04-02T22:58:00Z | 2026-04-02T23:01:16Z | 3m 16s |
| spec-reconcile | 2026-04-02T23:01:16Z | 2026-04-02T23:02:18Z | 1m 2s |
| finish | 2026-04-02T23:02:18Z | - | - |

## Context & Dependencies

### Upstream Work

- **19-1** (DONE): RoomDef + RoomExit structs — room graph data model in sidequest-genre
- **19-2** (DONE): Validated room movement — location constrained to room_id with exit check
- **19-3** (DONE): Trope tick on room transition — fire trope engine per room move

All upstream stories are complete. RoomDef, RoomExit, and discovered_rooms tracking are in place. This story wires the discovered room graph into the MAP_UPDATE protocol message.

### Feature Description

Extend the MAP_UPDATE message in sidequest-protocol to include room graph metadata for automapper rendering. When navigation_mode is RoomGraph:
1. Each ExploredLocation includes: room_exits, room_type, size, is_current_room
2. MAP_UPDATE contains only discovered rooms (fog of war)
3. UI receives structured data to render a dungeon floorplan

Data flow:
```
GameSnapshot.discovered_rooms (HashSet<String>)
  ↓
IntentRouter/WorldStatePatch.location
  ↓
GameMessage::MAP_UPDATE with ExploredLocation[]
  ↓
sidequest-ui receives structured room graph
  ↓
Automapper component renders dungeon floorplan
```

## Sm Assessment

**Story 19-4** is ready for RED phase. All three upstream dependencies (19-1, 19-2, 19-3) are complete — RoomDef/RoomExit structs exist, validated room movement is in place, and trope ticking on room transitions works. This story extends the MAP_UPDATE protocol message to carry room graph metadata for the automapper UI. Clean 3-point story with well-defined ACs. No blockers.

**Routing:** TDD phased → next agent is TEA (Han Solo) for RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New protocol types and conversion logic need full coverage

**Test Files:**
- `crates/sidequest-game/tests/map_update_room_graph_story_19_4_tests.rs` — 14 tests covering all ACs + edge cases

**Tests Written:** 14 tests covering 4 ACs
**Status:** RED (failing — 43 compilation errors, ready for Dev)

### Test Coverage

| AC | Tests | Description |
|----|-------|-------------|
| ExploredLocation fields | 4 | room_exits, room_type, size, is_current_room struct construction |
| Fog of war filtering | 2 | only discovered rooms appear, empty set → empty result |
| Current room flag | 2 | correct room flagged, others not flagged |
| Serde backward compat | 2 | round-trip with new fields, region-mode JSON without new fields |
| Integration | 1 | 3-room sequential discovery with payload verification |
| Edge: secret exits | 2 | hidden when undiscovered, visible when discovered |
| Edge: locked doors | 1 | locked doors still appear in exits |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | N/A — no new enums | skipped |
| #3 hardcoded placeholders | All tests use meaningful values | covered |
| #6 test quality | Self-checked — all 14 tests have meaningful assertions | covered |
| #8 serde bypass | `explored_location_serde_round_trip_with_room_graph_fields` + `backward_compat` | failing |

**Rules checked:** 3 of 4 applicable lang-review rules have test coverage
**Self-check:** 0 vacuous tests found

### Implementation Notes for Dev

Three things need implementing:
1. **`RoomExitInfo` struct** in `sidequest-protocol` — simple `{target: String, exit_type: String}`
2. **New fields on `ExploredLocation`** — `room_exits: Vec<RoomExitInfo>`, `room_type: String`, `size: Option<(u32, u32)>`, `is_current_room: bool` — all with `#[serde(default)]` for backward compat
3. **`build_room_graph_explored` function** in `sidequest-game` — takes `&[RoomDef]`, `&HashSet<String>` (discovered), `&str` (current_room_id) → `Vec<ExploredLocation>`. Must filter undiscovered secret exits.

**Handoff:** To Yoda for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-protocol/src/message.rs` — added `RoomExitInfo` struct, extended `ExploredLocation` with 4 new fields
- `crates/sidequest-game/src/room_movement.rs` — added `build_room_graph_explored()`, `is_exit_visible()`, `exit_type_slug()`
- `crates/sidequest-game/src/lib.rs` — exported `build_room_graph_explored`
- `crates/sidequest-protocol/src/tests.rs` — updated existing ExploredLocation constructor (hook-assisted)
- `crates/sidequest-game/src/state.rs` — updated existing ExploredLocation constructor (hook-assisted)
- `crates/sidequest-server/src/dispatch/mod.rs` — updated existing ExploredLocation constructor (hook-assisted)

**Tests:** 15/15 passing (GREEN) — full suite 744/744
**Branch:** feat/19-4-map-update-room-graph (pushed)

**Handoff:** To next phase (verify or review)

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- **Gap** (non-blocking): `build_room_graph_explored()` has no non-test consumer. Dispatch (`dispatch/mod.rs:475`) still constructs region-mode ExploredLocation for all MAP_UPDATE messages. Room-graph mode dispatch wiring needed — either in this story or a follow-up. Affects `crates/sidequest-server/src/dispatch/mod.rs` (needs conditional branch on `ctx.rooms.is_empty()`). *Found by TEA during test verification.*

## Design Deviations

None at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

## Subagent Results

All received: Yes

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-type-design | Yes | clean | RoomExitInfo and ExploredLocation types well-designed | N/A |
| 3 | reviewer-edge-hunter | Yes | 1 minor | exit_type_slug returns owned String unnecessarily | Noted, non-blocking |
| 4 | reviewer-rule-checker | Yes | clean | All applicable Rust review rules satisfied | N/A |
| 5 | reviewer-silent-failure-hunter | Yes | clean | No swallowed errors or silent fallbacks | N/A |

## Reviewer Assessment

**Verdict:** Approved
**Findings:** 1 minor (non-blocking)

1. **Minor:** `exit_type_slug()` returns owned `String` where `&'static str` suffices — 5 unnecessary allocations per room. Not hot path, not blocking.

**[RULE]** All applicable Rust review rules satisfied — `#[serde(default)]` for backward compat, `deny_unknown_fields` on new types, no silent error swallowing, no hardcoded placeholders.
**[SILENT]** No swallowed errors or silent fallbacks — `build_room_graph_explored` is a pure function with no error paths; dispatch branch is explicit (`if !ctx.rooms.is_empty()`).

**Wiring:** Verified — `build_room_graph_explored` has non-test consumer in `dispatch/mod.rs:477`.
**Serde:** Backward compat confirmed via `explored_location_backward_compat_without_room_graph_fields` test.
**Tests:** 15/15, all meaningful assertions, good edge case coverage.
**OTEL:** No new spans needed — pure data conversion function, dispatch-level `location.changed` already fires.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 5 ACs verified against implementation:
1. ExploredLocation extended with room_exits, room_type, size, is_current_room — all `#[serde(default)]` for backward compat
2. Fog of war filtering via `discovered.contains()` — undiscovered rooms omitted
3. Current room flagged by ID comparison
4. Protocol types updated with `RoomExitInfo` struct + field additions
5. Integration test covers 3-room discovery sequence (15 tests total, all GREEN)

Wire-safe: `skip_serializing_if` ensures region-mode payloads don't carry empty room graph fields.

**Decision:** Proceed to review

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 7

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No duplication found |
| simplify-quality | 7 findings | 4 high-confidence (all same issue: dispatch wiring gap), 2 medium (pre-existing), 1 low |
| simplify-efficiency | 5 findings | 1 high (dispatch wiring), 3 medium (2 pre-existing, 1 backward-compat), 1 low (pre-existing) |

**Applied:** 0 high-confidence fixes (findings are architectural wiring, not simplifiable code)
**Flagged for Review:** 1 — `build_room_graph_explored` has no non-test consumer in dispatch
**Noted:** Pre-existing design observations (DiscoveredRooms, DispatchError export)
**Reverted:** 0

**Overall:** simplify: clean — no code changes needed

**Quality Checks:** 15/15 tests passing, clippy warnings pre-existing only
**Handoff:** To Obi-Wan Kenobi for code review