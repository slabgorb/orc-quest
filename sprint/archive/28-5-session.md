---
story_id: "28-5"
jira_key: null
epic: "28"
workflow: "tdd"
---
# Story 28-5: Wire apply_beat() into dispatch — beat selection drives encounter progression

## Story Details
- **ID:** 28-5
- **Jira Key:** N/A (personal project)
- **Workflow:** tdd
- **Epic:** 28 — Unified Encounter Engine
- **Points:** 5
- **Priority:** p0
- **Stack Parent:** none

## Problem Statement

The core wiring for the unified encounter engine. When creature_smith (or the player via UI beat buttons) selects a beat, dispatch must call `apply_beat(beat_id, &def)` on the live StructuredEncounter. The beat's `stat_check` field names the mechanic to resolve:
- `"attack"` → calls `resolve_attack()` on CreatureCore
- `"escape"` → calls chase escape logic
- `"persuade"`/`"intimidate"`/etc. → use the confrontation metric directly (already handled by apply_beat's metric_delta)

After `apply_beat()`, check resolution. If resolved, handle outcome (victory/defeat/escape/etc.). If `escalates_to` is set and threshold crossed, start the escalation encounter.

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| Beat dispatch routing | dispatch_turn calls apply_beat when beat_id is present in action | Grep: apply_beat non-test call in dispatch/turn.rs |
| Stat check resolution | "attack" beat calls resolve_attack, "escape" beat calls escape resolver, others use metric_delta only | Test: beat with stat_check: attack → CreatureCore.apply_hp_delta called |
| Resolution handling | After apply_beat, check encounter.is_resolved() and handle outcome (victory/defeat/escape) | Test: resolved encounter triggers outcome dispatch |
| Escalation dispatch | If escalates_to is set and threshold crossed, start new encounter of escalation type | Test: beat that triggers escalation threshold → new encounter created |
| OTEL events | encounter.beat_dispatched (beat_id, stat_check, resolver), encounter.stat_check_resolved (stat_check, result) | Grep: WatcherEventBuilder with "encounter.beat_dispatched" and "encounter.stat_check_resolved" |
| Non-test consumer | apply_beat has at least one non-test caller in dispatch/turn.rs or related dispatch modules | `grep -r "apply_beat" crates/sidequest-server/src/dispatch/ --include="*.rs" \| grep -v test` returns results |

## Key Files

| File | Action |
|------|--------|
| `sidequest-server/src/dispatch/turn.rs` | Main dispatch entry point — add apply_beat routing here |
| `sidequest-server/src/dispatch/mod.rs` | Dispatch context and routing |
| `sidequest-game/src/encounter.rs` | apply_beat() already exists — verify beat.stat_check field |
| `sidequest-game/src/creature_core.rs` | resolve_attack() already exists — will be called by stat_check routing |
| `sidequest-game/src/chase.rs` | Chase escape logic (to be called for escape beats) |

## Technical Notes

- StructuredEncounter.apply_beat() is already implemented (story 28-3)
- CreatureCore.resolve_attack() is already implemented
- Beat.stat_check is already part of BeatDef
- Dispatch context has access to confrontation defs (story 28-1)
- Format_encounter_context is already wired (story 28-4)
- GameSnapshot.encounter field will exist after story 28-7

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-07T13:28:04Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-07T22:15:00Z | 2026-04-07T12:58:03Z | -33417s |
| red | 2026-04-07T12:58:03Z | 2026-04-07T13:03:17Z | 5m 14s |
| green | 2026-04-07T13:03:17Z | 2026-04-07T13:07:39Z | 4m 22s |
| spec-check | 2026-04-07T13:07:39Z | 2026-04-07T13:14:16Z | 6m 37s |
| verify | 2026-04-07T13:14:16Z | 2026-04-07T13:20:04Z | 5m 48s |
| review | 2026-04-07T13:20:04Z | 2026-04-07T13:27:16Z | 7m 12s |
| spec-reconcile | 2026-04-07T13:27:16Z | 2026-04-07T13:28:04Z | 48s |
| finish | 2026-04-07T13:28:04Z | - | - |

## Sm Assessment

Story 28-5 is the core wiring for the unified encounter engine. All prerequisites are in place:
- `apply_beat()` exists on StructuredEncounter (28-3)
- `resolve_attack()` exists on CreatureCore (28-2)
- `format_encounter_context` is wired into narrator prompt (28-4)
- Beat definitions with `stat_check` field exist in BeatDef

**Routing:** TDD workflow → RED phase → Han Solo (TEA) writes failing tests for beat dispatch, stat check resolution, encounter resolution handling, escalation, and OTEL events. Then GREEN phase → Yoda (Dev) implements.

**Risk:** Moderate complexity — stat_check routing spans multiple subsystems (encounter, creature_core, chase). Integration surface is wide but each piece is already implemented.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

## Design Deviations

None yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **beat_selection source uses scene_intent temporarily**
  - Spec source: context-story-28-5.md, Technical Approach
  - Spec text: "the action contains: { type: beat_selection, beat_id: attack }"
  - Implementation: Uses result.scene_intent as temporary carrier for beat_id until story 28-6 adds dedicated beat_selection field to ActionResult
  - Rationale: Story 28-6 adds the narrator beat_selection output; this story only wires the dispatch side
  - Severity: minor
  - Forward impact: Story 28-6 must replace scene_intent check with dedicated beat_selection field

### Architect (reconcile)
- No additional deviations found.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Core wiring story — apply_beat into dispatch pipeline with stat_check routing, resolution handling, escalation, and OTEL

**Test Files:**
- `crates/sidequest-server/tests/beat_dispatch_wiring_story_28_5_tests.rs` — 22 tests (wiring + unit)

**Tests Written:** 22 tests covering 10 ACs
**Status:** RED (9 failing wiring tests, 13 passing unit tests — ready for Dev)

### Failing Tests (Dev Must Fix)
| Test | AC |
|------|----|
| dispatch_has_beat_selection_handler | AC-Beat-Dispatch-Entry |
| dispatch_routes_attack_stat_check | AC-Attack-Beat-Routing |
| dispatch_routes_escape_stat_check | AC-Escape-Beat-Routing |
| dispatch_handles_escalation | AC-Escalation-Trigger |
| dispatch_emits_beat_dispatched_otel | AC-OTEL-Beat-Dispatched |
| beat_dispatched_otel_includes_beat_id | AC-OTEL-Beat-Dispatched |
| beat_dispatched_otel_includes_stat_check | AC-OTEL-Beat-Dispatched |
| dispatch_emits_stat_check_resolved_otel | AC-OTEL-Stat-Check-Resolved |
| beat_dispatch_reachable_from_dispatch_player_action | AC-Wiring-Dispatch-Pipeline |

### Passing Tests (Already Working)
Unit tests for apply_beat mechanics (13): metric delta, resolution detection, escalation target, phase transitions, error handling, beat counter — all pass because apply_beat/escalate_to_combat are already implemented in sidequest-game.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 Silent error swallowing | apply_beat_unknown_beat_id_returns_error, apply_beat_on_resolved_encounter_returns_error | passing |
| #3 Hardcoded placeholders | N/A — no new types with IDs |  |
| #4 Tracing | dispatch_emits_beat_dispatched_otel, dispatch_emits_stat_check_resolved_otel | failing (need impl) |
| #6 Test quality | Self-check: all 22 tests have meaningful assert_eq!/assert! — no vacuous assertions | passing |

**Rules checked:** 4 of 15 applicable (others N/A for this wiring story — no new types, no constructors, no Deserialize, no public structs, no tenant context)
**Self-check:** 0 vacuous tests found

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/mod.rs` — Added `dispatch_beat_selection()` function (164 LOC) and wired into dispatch_player_action pipeline after state_mutations

**Implementation Details:**
- `dispatch_beat_selection(ctx, beat_id)` — routes beat_id through apply_beat() on live StructuredEncounter
- stat_check routing: attack/strength → resolve_attack path, escape → separation metric, others → metric_delta only
- Resolution check after apply_beat — handles escalation via escalation_target() + escalate_to_combat()
- OTEL events: encounter.beat_dispatched (beat_id, stat_check, resolver), encounter.stat_check_resolved (stat_check, metric_current, resolved)
- Pipeline integration: called from dispatch_player_action after state_mutations when encounter is active

**Tests:** 22/22 passing (GREEN)
**Branch:** feat/28-5-wire-apply-beat-dispatch (pushed)

**Handoff:** To next phase (spec-check)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

All 10 ACs verified against the diff. Wiring check passed — `dispatch_beat_selection` has a non-test consumer at mod.rs:1251, `apply_beat` has a non-test consumer at mod.rs:3190. OTEL covers all three decision points (beat_dispatched, stat_check_resolved, escalation_started).

The scene_intent temporary carrier is a documented deviation (Dev logged it). Runtime activation depends on story 28-6 — acceptable per scope boundaries ("Out of scope: narrator logic").

**Decision:** Proceed to verify

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | Duplicate beat lookup, repeated test helper pattern |
| simplify-quality | 1 finding | unwrap_or_default masks invalid beat_id |
| simplify-efficiency | 3 findings | Redundant operations, duplicate match, over-engineering |

**Applied:** 1 high-confidence fix (consolidated beat lookup + eliminated duplicate match — 20 lines removed, 10 added)
**Flagged for Review:** 2 medium-confidence findings (match arms as scaffolding, unwrap_or_default error handling)
**Noted:** 1 low-confidence observation (0-damage attack logging gap)
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Quality Checks:** Build clean, clippy clean on changed files, 22/22 tests passing
**Handoff:** To Obi-Wan Kenobi (Reviewer) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 22/22 tests, clippy clean, 3 commits | N/A |
| 2 | reviewer-rule-checker | Yes | 3 violations | Silent error swallowing (#1), magic literals (#3), wiring test (#6) | #1 fixed, #3 fixed, #6 dismissed (covered by existing test) |
| 3 | reviewer-edge-hunter | Yes | 6 findings | Beat-not-found silent path, escalation None, ordering, stale flag, OTEL to_type, double None-check | 2 fixed, 4 dismissed |
| 4 | reviewer-silent-failure-hunter | Yes | 4 findings | Silent defaults, missing else on escalation, missing trace in default arm | 2 fixed (overlap with edge-hunter), 2 dismissed |

All received: Yes

## Reviewer Assessment

**Verdict:** APPROVE with fixes applied

[PREFLIGHT] Clean — 22/22 tests, clippy clean, 3 commits
[RULE] 3 violations: #1 silent error swallowing (fixed), #3 magic literals (fixed), #6 wiring test (dismissed — existing test covers)
[EDGE] 6 findings: beat-not-found (fixed), escalation None (fixed), 4 dismissed
[SILENT] 4 findings: silent defaults (fixed), escalation missing-else (fixed), 2 dismissed

### Findings Triage

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | **Major** | Beat not found silently produces empty stat_check/0 metric_delta, emits wrong OTEL | **Fixed** — early return with warn on beat not found |
| 2 | Medium | escalate_to_combat() None silently discarded | **Fixed** — added warn in else branch |
| 3 | Minor | Magic resolver strings without comment | **Fixed** — added comment explaining the closed set |
| 4 | Medium | No specific `dispatch_beat_selection(` wiring test | **Dismissed** — existing test at line 291 covers via `beat_selection` + `apply_beat` pattern match |
| 5 | Low | Ordering: beat dispatch after state_mutations | **Dismissed** — correct per story design, documented in comment |
| 6 | Low | Default `_` match arm has no trace | **Dismissed** — metric_delta is the common path, logging would be noise |
| 7 | Low | OTEL to_type uses escalation_target vs escalated.encounter_type | **Dismissed** — escalate_to_combat always produces "combat" type, matching the escalation_target value |

### Commits After Review
- `69101bf` — fix: eliminate silent fallbacks in dispatch_beat_selection

**Tests:** 22/22 GREEN after fixes
**Decision:** Approved — create PR and merge