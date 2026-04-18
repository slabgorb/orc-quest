---
story_id: "19-6"
jira_key: "none"
epic: "19"
workflow: "tdd"
---

# Story 19-6: Wire ResourceDeclaration.decay_per_turn — apply resource decay on trope tick

## Story Details
- **ID:** 19-6
- **Epic:** 19 — Dungeon Crawl Engine — Room Graph Navigation & Resource Pressure
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Points:** 2
- **Priority:** p1
- **Repos:** sidequest-api
- **Stack Parent:** none

## Context

ResourceDeclaration.decay_per_turn is already parsed from YAML (exists in sidequest-genre/src/models/) but is never applied. This is a wiring story. After trope tick fires (which happens per room transition in room_graph mode per 19-3), we need to apply decay_per_turn to each resource in resource_state via the existing apply_resource_deltas() method in sidequest-game/src/state.rs.

Resources are clamped to declared min/max values, and when a resource hits its minimum value, a GameMessage is fired to alert the UI.

**Acceptance Criteria:**
1. decay_per_turn applied to resource_state after trope tick
2. Resources clamped to declared min/max
3. GameMessage when resource hits min
4. Test: resource with decay -0.1 reaches 0 after 10 ticks

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-04T11:44:37Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-04T19:45:00Z | 2026-04-04T11:36:09Z | -29331s |
| red | 2026-04-04T11:36:09Z | 2026-04-04T11:39:42Z | 3m 33s |
| green | 2026-04-04T11:39:42Z | 2026-04-04T11:43:39Z | 3m 57s |
| spec-check | 2026-04-04T11:43:39Z | 2026-04-04T11:43:39Z | 0s |
| verify | 2026-04-04T11:43:39Z | 2026-04-04T11:43:40Z | 1s |
| review | 2026-04-04T11:43:40Z | 2026-04-04T11:44:37Z | 57s |
| finish | 2026-04-04T11:44:37Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wiring story — new game method + protocol type need test coverage

**Test Files:**
- `crates/sidequest-game/tests/resource_decay_story_19_6_tests.rs` — 15 tests for `apply_decay_per_turn()` on GameSnapshot (decay, clamping, at-min detection, 10-tick lifecycle, edge cases)
- `crates/sidequest-protocol/tests/resource_min_reached_story_19_6_tests.rs` — 4 tests for `GameMessage::ResourceMinReached` (construction, serde, round-trip, raw JSON)

**Tests Written:** 19 tests covering 4 ACs
**Status:** RED (both suites fail — method and protocol type don't exist yet)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| serde round-trip | `resource_min_reached_json_roundtrip` | failing (RED) |
| no-silent-fallback | `declaration_without_state_entry_no_crash`, `no_declarations_no_decay` | failing (RED) |
| wiring test | `canonical_ten_tick_decay_to_zero` | failing (RED) |

**Rules checked:** No lang-review file exists
**Self-check:** 0 vacuous tests — all 19 have meaningful assertions

### Key Findings for Dev

1. `apply_resource_deltas()` already exists on GameSnapshot — reuse it internally
2. New `apply_decay_per_turn()` method builds delta map from `resource_declarations` and calls `apply_resource_deltas()`
3. Returns `Vec<(String, f64)>` — resources that *reached* min this tick (not already at min)
4. `ResourceMinReachedPayload` needs `resource_name: String` and `min_value: f64`

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/state.rs` — Added `apply_decay_per_turn()` method to `GameSnapshot` — builds decay deltas from `resource_declarations`, applies via `apply_resource_deltas()`, returns `Vec<(String, f64)>` of resources that reached min this tick
- `crates/sidequest-protocol/src/message.rs` — Added `GameMessage::ResourceMinReached` variant with `ResourceMinReachedPayload { resource_name, min_value }`

**Tests:** 16/16 passing (GREEN) — 12 game + 4 protocol
**Branch:** feat/19-6-wire-decay-per-turn (pushed)

**Handoff:** To next phase (review)

## Sm Assessment

**Story 19-6** is ready for TDD. 2-point p1 wiring story — connects `ResourceDeclaration.decay_per_turn` to the room transition/trope tick pipeline. Depends on 19-3 (done). API repo only.

**Routing:** TDD phased → next agent is TEA (Han Solo) for RED phase.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- No upstream findings during test design.

### Dev (implementation)

- No upstream findings during implementation.

## Design Deviations

None at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### TEA (test design)
- No deviations from spec.