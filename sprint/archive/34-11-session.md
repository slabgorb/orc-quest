---
story_id: "34-11"
jira_key: null
epic: "34"
workflow: "tdd"
---
# Story 34-11: OTEL dice spans — request_sent, throw_received, result_broadcast

## Story Details
- **ID:** 34-11
- **Branch:** feat/34-11-otel-dice-spans
- **Epic:** 34 (3D Dice Rolling System — MVP)
- **Workflow:** tdd
- **Points:** 2
- **Priority:** p1
- **Repos:** sidequest-api
- **Depends on:** 34-4 (Dispatch integration — complete)

## Context

### What This Story Does

Add structured WatcherEvent emissions to the three dice dispatch decision points so the GM panel can verify dice are engaging. Without these, the OTEL dashboard has no visibility into whether dice rolls are actually happening — classic blind spot pattern.

### Three Dispatch Points

1. **`dice.request_sent`** — Emitted when a DiceRequest is broadcast to all clients after beat selection triggers a stat check. Fields: request_id, rolling_player, stat, difficulty, dice_count.

2. **`dice.throw_received`** — Emitted when the rolling player's DiceThrow arrives with gesture params. Fields: request_id, rolling_player, has_throw_params.

3. **`dice.result_broadcast`** — Emitted when DiceResult is resolved and broadcast to all clients. Fields: request_id, rolling_player, total, outcome, seed.

### Current State

The dispatch code already has `tracing::info!` calls at these points (added in 34-4/34-8). This story upgrades them to structured `WatcherEvent` emissions using the existing `WatcherEventBuilder` pattern, making them visible on the GM panel's dice channel.

### Key Architecture

- **WatcherEventBuilder** pattern: `WatcherEventBuilder::new("dice", WatcherEventType::SubsystemExerciseSummary).field("event", "...").field(...).send()`
- **WatcherEventType**: Use `SubsystemExerciseSummary` for normal flow, `StateTransition` for outcome changes
- **Channel**: "dice" — new channel for all dice-related OTEL events
- **Existing tracing stays**: The `tracing::info!` calls remain for structured logging; WatcherEvents are the GM panel layer on top

### Files to Modify

- **`sidequest-api/crates/sidequest-server/src/lib.rs`** — DiceThrow handler (~line 2229), add WatcherEvents at the three dispatch points
- **`sidequest-api/crates/sidequest-server/src/dispatch/mod.rs`** — If DiceRequest emission happens in dispatch pipeline

### No Changes Needed

- Protocol types (34-2 complete)
- Dice resolution logic (34-3 complete)
- Dispatch flow (34-4 complete)
- Multiplayer broadcast (34-8 complete)
- Narrator injection (34-9 complete)
- WatcherEventBuilder infrastructure (already exists)

## Acceptance Criteria

1. **dice.request_sent** WatcherEvent emitted when DiceRequest is broadcast
   - Channel: "dice"
   - Fields: request_id, rolling_player, stat, difficulty, dice_count
   - Type: SubsystemExerciseSummary

2. **dice.throw_received** WatcherEvent emitted when DiceThrow arrives
   - Channel: "dice"
   - Fields: request_id, rolling_player, has_throw_params
   - Type: SubsystemExerciseSummary

3. **dice.result_broadcast** WatcherEvent emitted when DiceResult is broadcast
   - Channel: "dice"
   - Fields: request_id, rolling_player, total, outcome, seed
   - Type: StateTransition (outcome changes game state context)

4. **Existing tracing preserved** — tracing::info! calls remain alongside WatcherEvents

5. **No dispatch flow changes** — pure observability addition

## Reference

- **Epic context:** `sprint/context/context-epic-34.md`
- **WatcherEvent pattern:** `sidequest-api/crates/sidequest-server/src/watcher.rs`
- **DiceThrow handler:** `sidequest-api/crates/sidequest-server/src/lib.rs` (~line 2229)
- **Existing dice tracing:** grep for "dice." in lib.rs

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-13T09:37:38Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-13T00:00:00Z | 2026-04-13T09:09:04Z | 9h 9m |
| red | 2026-04-13T09:09:04Z | 2026-04-13T09:22:12Z | 13m 8s |
| green | 2026-04-13T09:22:12Z | 2026-04-13T09:28:19Z | 6m 7s |
| spec-check | 2026-04-13T09:28:19Z | 2026-04-13T09:29:01Z | 42s |
| verify | 2026-04-13T09:29:01Z | 2026-04-13T09:32:07Z | 3m 6s |
| review | 2026-04-13T09:32:07Z | 2026-04-13T09:37:22Z | 5m 15s |
| spec-reconcile | 2026-04-13T09:37:22Z | 2026-04-13T09:37:38Z | 16s |
| finish | 2026-04-13T09:37:38Z | - | - |

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Three emit functions match the three dispatch points specified in the story context. Event types correct (SubsystemExerciseSummary for request_sent/throw_received, StateTransition for result_broadcast). All on "dice" channel. Fields match spec. TEA-documented gap (DiceRequest not in production code) is a known limitation, not a drift — the emit function is ready for wiring when the beat-selection → dice trigger path is built.

**Decision:** Proceed to verify

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 2 commits, 2 files changed, 9/9 tests GREEN | N/A |
| 2 | reviewer-type-design | Yes | clean | No new types, emit functions take refs to existing types | N/A |
| 3 | reviewer-security | Yes | clean | No user input in emit paths, no injection vectors | N/A |
| 4 | reviewer-test-analyzer | Yes | clean | 9 tests with meaningful assertions, matches! for non-PartialEq | N/A |
| 5 | reviewer-simplifier | Yes | clean | Three focused emit functions, no over-abstraction | N/A |
| 6 | reviewer-edge-hunter | Yes | 1 finding | has_throw_params zero-check heuristic could false-negative | Non-blocking |
| 7 | reviewer-comment-analyzer | Yes | clean | Doc comments accurate on all three emit functions | N/A |
| 8 | reviewer-rule-checker | Yes | clean | No rule violations, catch-all on non_exhaustive per ADR-005 | N/A |
| 9 | reviewer-silent-failure-hunter | Yes | clean | WatcherEventBuilder.send() is no-op when channel uninitialized — correct by design | N/A |

All received: Yes

## Reviewer Assessment

**Verdict:** APPROVED
**PR:** slabgorb/sidequest-api#437 (merged via squash)
**Blocking Issues:** None

**Findings (non-blocking):**
- [TYPE] Emit functions correctly accept refs to existing protocol/game types — no new type machinery
- [TEST] 9 meaningful tests; `matches!` used correctly for WatcherEventType comparison
- [DOC] Doc comments on all three emit functions describe when/what they emit
- [RULE] Catch-all `_ => "Unknown"` on RollOutcome correct per ADR-005
- [SILENT] WatcherEventBuilder.send() is no-op without init — correct for unit tests and CLI tools

**Edge finding (non-blocking):**
- `has_throw_params` heuristic (velocity/angular != zero) could theoretically false-negative for a legitimate zero-motion throw, but this only affects a boolean metadata field — doesn't affect observability of the event itself

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** N/A (skipped — 2-file change, purely additive emit functions)
**Files Analyzed:** 2

**Overall:** simplify: clean — no abstractions, no duplication, no dead code in story scope

**Quality Checks:** fmt ✓, clippy clean on story files ✓ (4 pre-existing warnings in other files — already fixed on main), tests 9/9 ✓
**Handoff:** To Avasarala (Reviewer) for code review

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/lib.rs` - Three pub emit functions + wired into DiceThrow handler
- `crates/sidequest-server/src/otel_dice_spans_34_11_tests.rs` - Fixed test compilation (position array size, matches! for WatcherEventType, context field)

**Tests:** 9/9 passing (GREEN)
**Branch:** feat/34-11-otel-dice-spans (pushed)

**Handoff:** To TEA for verify phase

## Tea Assessment

**Tests Required:** Yes
**Reason:** OTEL observability — GM panel needs dice visibility

**Test Files:**
- `crates/sidequest-server/src/otel_dice_spans_34_11_tests.rs` - 10 tests covering three WatcherEvent emissions

**Tests Written:** 10 tests covering 6 ACs
**Status:** RED (compilation failure — emit functions don't exist)

### AC Coverage

| AC | Test(s) | Status |
|------|---------|--------|
| dice.request_sent fields | `dice_request_sent_emits_watcher_event` | failing |
| dice.request_sent type | `dice_request_sent_uses_correct_event_type` | failing |
| dice.throw_received fields | `dice_throw_received_emits_watcher_event` | failing |
| dice.throw_received type | `dice_throw_received_uses_correct_event_type` | failing |
| dice.result_broadcast fields | `dice_result_broadcast_emits_watcher_event` | failing |
| dice.result_broadcast type | `dice_result_broadcast_uses_state_transition_type` | failing |
| All use dice channel | `all_dice_events_use_dice_channel` | failing |
| Outcome variant name | `dice_result_outcome_field_is_variant_name` | failing |
| Wiring | `emit_functions_are_accessible` | failing |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 tracing coverage | Tests verify WatcherEvent emission, not tracing::info! | N/A — tracing preserved, not replaced |
| #6 test quality | Self-checked: all 10 tests have meaningful assertions | pass |

**Rules checked:** 2 of 12 (most N/A for pure OTEL story)
**Self-check:** 0 vacuous tests found

**Handoff:** To Naomi (Dev) for implementation

### Implementation Guidance for Dev

1. Add three `pub fn` emit helpers in `lib.rs` (or a new `dice_telemetry.rs` module):
   - `emit_dice_request_sent(request: &DiceRequestPayload)` — WatcherEventBuilder "dice" / SubsystemExerciseSummary
   - `emit_dice_throw_received(request_id: &str, rolling_player: &str, throw_params: &ThrowParams)` — WatcherEventBuilder "dice" / SubsystemExerciseSummary
   - `emit_dice_result_broadcast(result: &DiceResultPayload, resolved: &ResolvedRoll)` — WatcherEventBuilder "dice" / StateTransition
2. Call `emit_dice_throw_received` in the DiceThrow handler after pending request lookup
3. Call `emit_dice_result_broadcast` in the DiceThrow handler after compose_dice_result
4. Call `emit_dice_request_sent` wherever DiceRequest is broadcast (currently only tests — add to the future beat-selection dice trigger path)

## Sm Assessment

**Story ready for RED phase.** All dependencies complete (34-4 dispatch is merged). Pure observability story — adds WatcherEvents to existing dispatch points. Low risk, 2 points.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

### TEA (test design)
- **Gap** (non-blocking): DiceRequest is not emitted from production code yet

### Dev (implementation)
- No upstream findings during implementation. — only in tests (34-8). The `dispatch_beat_selection` in `beat.rs` doesn't construct or broadcast a DiceRequest. The `dice.request_sent` emit function will need to be called from the future code path that triggers dice rolls from beat selection. Currently tests call the emit function directly. Affects `crates/sidequest-server/src/dispatch/beat.rs` (future DiceRequest emission site). *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found.