---
story_id: "28-3"
jira_key: null
epic: "28"
workflow: "tdd"
---
# Story 28-3: Populate Beats in Confrontation Protocol Message

## Story Details
- **ID:** 28-3
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Stack Parent:** 28-1 (ConfrontationDefs loaded into DispatchContext)
- **Repos:** api, ui
- **Branch (api):** feat/28-3-populate-confrontation-beats
- **Branch (ui):** feat/28-3-populate-confrontation-beats

## Problem Statement

`dispatch/mod.rs` sends `beats: vec![]` in every Confrontation message. The
ConfrontationOverlay (235 LOC, fully functional) renders beat buttons from this array.
Empty array = no buttons = dead interaction loop.

The beats population code itself was partially landed in the 28-1 fix commit
(`96e5826`). The `beats: vec![]` is gone — replaced with a `def.map()` that maps
`BeatDef` structs to `ConfrontationBeat` protocol structs. However:

1. The OTEL event `encounter.beats_sent` is missing
2. There is no test file for 28-3's ACs

## What Remains

| Item | Status |
|------|--------|
| `beats: vec![]` removed, def.map() wired | Done (in 28-1 fix) |
| OTEL `encounter.beats_sent` event | Missing |
| Test: beats populated from known def | Missing |
| Test: 1:1 field mapping verified | Missing |
| Test: graceful miss (unknown encounter_type → empty beats) | Missing |
| Test: wiring check (non-test consumer exists) | Missing |

## Acceptance Criteria

| AC | Detail | Verification |
|----|--------|-------------|
| Beats populated | Confrontation message beats field is non-empty when a def exists | Test: create encounter with known type, verify beats in message |
| 1:1 mapping | Each BeatDef field maps to ConfrontationBeat (id, label, metric_delta, stat_check, risk, resolution) | Test: verify all fields present |
| Graceful miss | No ConfrontationDef for encounter_type → beats remain empty | Test: unknown type → empty beats |
| OTEL | encounter.beats_sent event with encounter_type, beat_count, beat_ids | Grep: WatcherEventBuilder "beats_sent" in dispatch/mod.rs |
| Wiring | `beats: vec![]` no longer exists at line ~2393 | `grep "beats: vec!\[\]" dispatch/mod.rs` returns nothing |

## Key Files

| File | Action |
|------|--------|
| `crates/sidequest-server/src/dispatch/mod.rs` | Add `encounter.beats_sent` OTEL event after beats are populated (~line 2458) |
| `crates/sidequest-server/tests/confrontation_beats_wiring_story_28_3_tests.rs` | New test file for all ACs |

## Implementation Notes

The OTEL event should fire inside the `if let Some(ref enc) = encounter` block in
`build_confrontation_messages()`, after the `messages.push()` call. Pattern follows
other WatcherEventBuilder usages in the same file. Emit: encounter_type, beat_count,
and beat_ids as a joined string.

The test file should follow the pattern of
`confrontation_defs_wiring_story_28_1_tests.rs`. Key tests:
- Verify `find_confrontation_def` returns beats that map correctly to protocol fields
- Verify unknown encounter_type yields empty beats (graceful miss)
- Verify `beats: vec![]` does not appear in `dispatch/mod.rs` (wiring check)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-07T11:11:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-07 | 2026-04-07T10:28:42Z | 10h 28m |
| red | 2026-04-07T10:28:42Z | 2026-04-07T10:48:33Z | 19m 51s |
| green | 2026-04-07T10:48:33Z | 2026-04-07T10:57:11Z | 8m 38s |
| spec-check | 2026-04-07T10:57:11Z | 2026-04-07T10:58:15Z | 1m 4s |
| verify | 2026-04-07T10:58:15Z | 2026-04-07T11:07:38Z | 9m 23s |
| review | 2026-04-07T11:07:38Z | 2026-04-07T11:11:11Z | 3m 33s |
| finish | 2026-04-07T11:11:11Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **Gap (non-blocking):** The beats population code from 28-1's fix commit (`96e5826`) already replaced `beats: vec![]` with the def.map() implementation. Story 28-3 therefore inherits this work. The remaining deliverables are the OTEL event and the test file. TEA should write tests first (TDD), then add the OTEL event.

## Sm Assessment

Story 28-3 setup complete. Session file created, branches created in api and ui repos. Beats population partially landed from 28-1 fix. Remaining: OTEL event + tests. Routing to TEA for RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story has 6 ACs requiring verification

**Test Files:**
- `crates/sidequest-server/tests/confrontation_beats_wiring_story_28_3_tests.rs` — 9 tests covering all ACs

**Tests Written:** 9 tests covering 6 ACs
**Status:** RED (1 failing — OTEL beats_sent event not yet emitted)

### Test Coverage

| AC | Test(s) | Status |
|----|---------|--------|
| Beats populated | `beats_populated_from_known_def` | passing |
| 1:1 mapping | `beat_def_maps_to_confrontation_beat_fields`, `beat_def_resolution_none_maps_to_false`, `beat_def_risk_none_maps_to_none` | passing |
| Graceful miss | `unknown_encounter_type_yields_no_def` | passing |
| OTEL | `otel_beats_sent_event_exists_in_dispatch` | **FAILING** |
| Wiring | `beats_vec_empty_removed_from_dispatch` | passing |
| Label/category | `label_and_category_from_def_not_hardcoded` | passing |
| Integration | `spaghetti_western_standoff_beats_map_to_protocol` | passing |

### Rule Coverage

**Rules checked:** 0 applicable new rules — this story adds no new types, enums, or constructors. The mapping code uses existing types (ConfrontationDef, ConfrontationBeat) that were already verified in 28-1.
**Self-check:** 0 vacuous tests found. All 9 tests have meaningful assertions.

**Handoff:** To Yoda (Dev) for GREEN — add encounter.beats_sent OTEL event

### TEA (test design)
- No upstream findings during test design.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 pre-existing (clippy docs, fmt drift) | dismissed 2 — pre-existing, not from 28-3 |
| 2 | reviewer-edge-hunter | N/A | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (2 missing-else on OTEL, 1 pre-existing .ok()) | confirmed 2 MEDIUM (systemic pattern from 28-1), dismissed 1 (pre-existing) |
| 4 | reviewer-test-analyzer | N/A | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | N/A | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | N/A | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | N/A | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | N/A | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 (Rule 15 — beat_ids unbounded) | confirmed 1 LOW — genre data, 3-10 beats typical |

**All received:** Yes (3 returned, 6 disabled/skipped)
**Total findings:** 3 confirmed (2 MEDIUM systemic, 1 LOW), 1 dismissed (pre-existing)

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] OTEL `encounter.beats_sent` event at `dispatch/mod.rs:2466-2474` — fires with encounter_type, beat_count, beat_ids. Guarded by `Some(d)` and `!d.beats.is_empty()`. Follows WatcherEventBuilder pattern. AC-OTEL met.

2. [VERIFIED] Tests 9/9 passing — all ACs covered. Wiring tests use `include_str!` per convention. Integration test against real genre pack (spaghetti_western). No vacuous assertions.

3. [VERIFIED] `beats: vec![]` removed — grep confirms absent from dispatch/mod.rs. `find_confrontation_def` wired at line 2436 with non-test consumer. AC-Wiring met.

4. [MEDIUM] [SILENT] Missing else branches on OTEL guards (lines 2467-2468) — when def is None or beats are empty, no event emits. Same systemic pattern flagged in 28-1 review. Captured as delivery finding for systemic refactor.

5. [LOW] [RULE] Rule 15 — `beat_ids` field at line 2473 collects all beat IDs with no bound. Genre pack data (3-10 beats typical), not user input. `beat_count` already provides cardinality. Low risk for internal telemetry.

**Data flow traced:** Genre YAML → ConfrontationDef.beats → find_confrontation_def() → BeatDef→ConfrontationBeat mapping → ConfrontationPayload.beats → OTEL beats_sent event. Safe: genre pack data is trusted static YAML.

**Error handling:** WatcherEventBuilder.send() is infallible (fire-and-forget telemetry, no-op if no subscribers).

**[EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE]** — No findings from disabled subagents. [SILENT] 2 MEDIUM systemic. [RULE] 1 LOW unbounded. All others clean.

### Devil's Advocate

The diff is 11 lines. What could go wrong? The OTEL event fires after the Confrontation message is pushed, so a panic in the event builder can't block message delivery — correct ordering. The `def` variable is `Option<&ConfrontationDef>` (Copy), so the fourth use at line 2467 after three `.map()` calls at lines 2440-2451 is safe — no move semantics. The `beat_ids` collect allocates a Vec per turn per active encounter — negligible for 3-10 beats. The missing-else on the OTEL guard means a genre pack with empty confrontation beats silently renders an overlay with no buttons and no telemetry — but this is the same systemic issue across all genre-loaded OTEL events, not a regression from this story.

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story

### Reviewer (audit)
- No design deviations to audit (TEA and Dev both logged "No deviations from spec").

### Reviewer (code review)
- No upstream findings during code review. The systemic OTEL missing-else pattern was already captured in 28-1's delivery findings.

### Dev (implementation)
- No deviations from spec.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

All 6 ACs verified:
- **Beats populated:** `find_confrontation_def` at `dispatch/mod.rs:2436` looks up def, `def.map()` at line 2451 maps beats — non-empty when def exists
- **1:1 mapping:** BeatDef→ConfrontationBeat maps id, label, metric_delta, stat_check, risk, resolution (Option→bool via unwrap_or(false)) at lines 2451-2458
- **Graceful miss:** `def.map(...).unwrap_or_default()` at line 2458 — unknown type yields empty vec
- **OTEL:** `encounter.beats_sent` event at lines 2466-2474 with encounter_type, beat_count, beat_ids
- **Wiring:** `beats: vec![]` confirmed absent from dispatch/mod.rs (grep returns nothing)
- **UI renders:** ConfrontationOverlay already consumes beats from ConfrontationPayload — no UI changes needed

**Decision:** Proceed to verify/review.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/mod.rs` — Added encounter.beats_sent OTEL event after confrontation beats are populated in build_confrontation_messages()

**Tests:** 9/9 passing (GREEN)
**Branch:** feat/28-3-populate-confrontation-beats (pushed)

**Handoff:** To next phase (verify/review)

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- No upstream findings during test verification.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Files Analyzed:** 2 (dispatch/mod.rs, test file)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | BeatDef→ConfrontationBeat mapping repeated in tests — dismissed: cross-crate From not appropriate, test repetition intentional |
| simplify-quality | 2 findings | Wiring tests use std::fs::read_to_string instead of include_str! |
| simplify-efficiency | clean | No over-engineering |

**Applied:** 1 high-confidence fix (include_str! convention in 2 wiring tests)
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 1 low-confidence observation (reuse — dismissed)
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Quality Checks:** 9/9 tests passing after simplify fix
**Handoff:** To Obi-Wan (Reviewer) for code review