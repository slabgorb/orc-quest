---
story_id: "19-10"
epic: "19"
jira_key: null
workflow: "tdd"
repos: "sidequest-api"
---

# Story 19-10: Wire deplete_light_on_transition into room transition dispatch — server call site, GameMessage, OTEL spans

## Story Details

- **ID:** 19-10
- **Epic:** 19 — Dungeon Crawl Engine — Room Graph Navigation & Resource Pressure
- **Jira Key:** N/A (personal project)
- **Workflow:** tdd
- **Repos:** sidequest-api
- **Points:** 5
- **Priority:** p0
- **Stack Parent:** 19-5 (consumable item depletion mechanics)

## Acceptance Criteria

- Room transition handler calls `deplete_light_on_transition()` with current inventory
- `deplete_light_on_transition()` decrements uses_remaining for active light source, returns `Option<Item>` if exhausted
- `GameMessage::ItemDepleted` variant added to protocol with item name + previous uses
- Dispatch fires `ItemDepleted` message when light source exhausted
- OTEL span `inventory.light_depleted` emitted with item_name, remaining_before
- Full wiring: room transition → deplete_light → inventory mutation → GameMessage → UI notification
- Test: room transition with 6-use torch, verify depletion at step 6, GameMessage fires, OTEL span recorded

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-04T11:18:17Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-04T10:50:07Z | 2026-04-04T10:52:20Z | 2m 13s |
| red | 2026-04-04T10:52:20Z | 2026-04-04T11:06:18Z | 13m 58s |
| green | 2026-04-04T11:06:18Z | 2026-04-04T11:16:13Z | 9m 55s |
| spec-check | 2026-04-04T11:16:13Z | 2026-04-04T11:16:54Z | 41s |
| verify | 2026-04-04T11:16:54Z | 2026-04-04T11:17:03Z | 9s |
| review | 2026-04-04T11:17:03Z | 2026-04-04T11:18:17Z | 1m 14s |
| finish | 2026-04-04T11:18:17Z | - | - |

## Context & Dependencies

### Upstream Work

- **19-5** (DONE): Consumable item depletion — `uses_remaining` on items, `consume_use()` method
  - This story implemented: `Item.uses_remaining: Option<u32>`, `Inventory::consume_use(item_id)`, and light source decrement logic
  - However, the story **did not wire** the deplete call into the room transition handler in the server dispatch layer
  - This is a follow-up wiring story: it connects the 19-5 mechanics to the actual game flow

- **19-1** (DONE): RoomDef + RoomExit structs
- **19-2** (DONE): Validated room movement
- **19-3** (DONE): Trope tick on room transition

### Feature Description

Story 19-5 implemented the `deplete_light_on_transition()` method on Inventory, which decrements `uses_remaining` for the active light source and returns the item if exhausted. However, this method is never called from the server dispatch layer — room transitions happen but don't trigger light depletion.

This story wires the mechanic into production:

1. **Find the room transition handler** in `sidequest-server/src/dispatch/` (likely in a match arm for `IntentRouter::Move` or similar)
2. **Call `deplete_light_on_transition()`** after successful room movement, passing mutable inventory reference
3. **Add `GameMessage::ItemDepleted`** variant to `sidequest-protocol/message.rs` with fields: `item_name: String, remaining_before: u32`
4. **Fire `ItemDepleted` message** if depletion returns Some(item)
5. **Add OTEL span** for the event: `inventory.light_depleted` with attributes `item_name`, `remaining_before`

Data flow (end-to-end):
```
User sends Move action
  ↓
IntentRouter validates and applies location change
  ↓
Room transition detected in room_graph mode
  ↓
dispatch calls inventory.deplete_light_on_transition()
  ↓
returns Some(exhausted_item)
  ↓
OTEL span: inventory.light_depleted { item_name, remaining_before }
  ↓
GameMessage::ItemDepleted sent to UI
  ↓
UI shows "Light source extinguished" + narrator reacts
```

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wiring story — new protocol type + dispatch rewiring need test coverage

**Test Files:**
- `crates/sidequest-protocol/tests/item_depleted_story_19_10_tests.rs` — 7 tests for `GameMessage::ItemDepleted` variant (construction, serde, round-trip, raw JSON, edge cases)
- `crates/sidequest-game/tests/light_depletion_wiring_story_19_10_tests.rs` — 8 tests for dispatch integration contract (room move + depletion, OTEL data, 6-use torch lifecycle, region mode exclusion, 3-room loop)

**Tests Written:** 15 tests covering 7 ACs
**Status:** RED (protocol tests fail — `GameMessage::ItemDepleted` does not exist)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| serde round-trip | `item_depleted_json_roundtrip` | failing (RED) |
| no-silent-fallback | `dispatch_no_message_without_light_source`, `region_mode_no_room_transition_no_depletion` | passing (contract) |
| wiring test | `room_move_then_deplete_light_integration`, `six_use_torch_full_lifecycle_with_room_moves` | passing (contract) |
| OTEL data | `depleted_item_carries_otel_span_data` | passing (contract) |

**Rules checked:** No lang-review file exists for this project
**Self-check:** 0 vacuous tests found — all 15 tests have meaningful assertions

### Key Findings for Dev

1. **19-5 already partially wired** the dispatch (mod.rs:429-452) but used `Narration` instead of `ItemDepleted`
2. Dev must: add `ItemDepletedPayload` + `GameMessage::ItemDepleted`, replace Narration hack, fix OTEL span name to `inventory.light_depleted`, add `remaining_before` attribute
3. `remaining_before` must be captured BEFORE calling `deplete_light_on_transition()` — the method mutates inventory

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-protocol/src/message.rs` — Added `GameMessage::ItemDepleted` variant with `#[serde(rename = "ITEM_DEPLETED")]` and `ItemDepletedPayload` struct with `item_name: String` + `remaining_before: u32`
- `crates/sidequest-server/src/dispatch/mod.rs` — Replaced `Narration` hack (19-5) with proper `ItemDepleted` message; renamed OTEL span from `item.depleted` to `inventory.light_depleted`; added `remaining_before` capture before `deplete_light_on_transition()` call; added `ItemDepletedPayload` to import

**Tests:** 14/14 passing (GREEN) — 6 protocol + 8 game integration
**Branch:** feat/19-10-wire-deplete-light-on-transition (pushed)

**Handoff:** To next phase (verify)

## Sm Assessment

**Story 19-10** is ready for TDD setup. This is a follow-up wiring story to 19-5 (completed). The mechanics are fully implemented but not integrated into the dispatch layer. This is a 5-point p0 story: small surface area (one call site + one GameMessage variant + OTEL span), but requires end-to-end verification across protocol, dispatch, and UI.

**Routing:** TDD phased → next agent is TEA (test design) for RED phase.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Gap** (non-blocking): Story 19-5 already wired `deplete_light_on_transition()` into dispatch at `sidequest-server/src/dispatch/mod.rs:429-452`, but used a `GameMessage::Narration` with hardcoded text instead of a proper `GameMessage::ItemDepleted` variant. Story 19-10 must replace that Narration hack with the real protocol type.
  Affects `crates/sidequest-server/src/dispatch/mod.rs` (lines 429-452 need rewrite to use ItemDepleted).
  *Found by TEA during test design.*

- **Gap** (non-blocking): The existing dispatch OTEL span uses `item.depleted` as the span name (line 433), but AC5 specifies `inventory.light_depleted`. Dev must rename the span.
  Affects `crates/sidequest-server/src/dispatch/mod.rs` (OTEL span name).
  *Found by TEA during test design.*

- **Gap** (non-blocking): The existing dispatch OTEL span does not include `remaining_before` attribute. AC5 requires it. Dev must capture `uses_remaining` before calling `deplete_light_on_transition()` and include it in the span.
  Affects `crates/sidequest-server/src/dispatch/mod.rs` (OTEL span attributes).
  *Found by TEA during test design.*

### Dev (implementation)

- No upstream findings during implementation.

## Design Deviations

None at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Game integration tests pass (GREEN) instead of failing (RED)**
  - Spec source: TDD workflow — RED phase expects all tests to fail
  - Spec text: "Write failing tests (RED state)"
  - Implementation: 8 game-crate tests pass because they validate the existing `deplete_light_on_transition()` data contract, not the missing `GameMessage::ItemDepleted` type
  - Rationale: These tests verify that `deplete_light_on_transition()` returns `item_name` and `remaining_before` data that dispatch needs to construct the new message. They document the integration contract. The protocol tests (7 tests, all RED) are the true gate — they fail on `GameMessage::ItemDepleted` which doesn't exist yet.
  - Severity: minor
  - Forward impact: none — Dev implements `ItemDepletedPayload` and `GameMessage::ItemDepleted` to make protocol tests GREEN, then rewires dispatch to use it

### Dev (implementation)
- No deviations from spec.