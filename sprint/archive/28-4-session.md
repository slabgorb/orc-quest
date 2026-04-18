---
story_id: "28-4"
jira_key: ""
epic: "28"
workflow: "tdd"
---
# Story 28-4: Wire format_encounter_context() into narrator prompt — replace inline combat/chase context

## Story Details
- **ID:** 28-4
- **Jira Key:** (not created)
- **Workflow:** tdd
- **Stack Parent:** 28-1 (dependency)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-07T12:47:57Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-07T00:00:00Z | 2026-04-07T12:09:31Z | 12h 9m |
| red | 2026-04-07T12:09:31Z | 2026-04-07T12:16:49Z | 7m 18s |
| green | 2026-04-07T12:16:49Z | 2026-04-07T12:21:05Z | 4m 16s |
| spec-check | 2026-04-07T12:21:05Z | 2026-04-07T12:22:04Z | 59s |
| verify | 2026-04-07T12:22:04Z | 2026-04-07T12:25:41Z | 3m 37s |
| review | 2026-04-07T12:25:41Z | 2026-04-07T12:39:33Z | 13m 52s |
| green | 2026-04-07T12:39:33Z | 2026-04-07T12:42:01Z | 2m 28s |
| spec-check | 2026-04-07T12:42:01Z | 2026-04-07T12:42:40Z | 39s |
| verify | 2026-04-07T12:42:40Z | 2026-04-07T12:44:50Z | 2m 10s |
| review | 2026-04-07T12:44:50Z | 2026-04-07T12:47:13Z | 2m 23s |
| spec-reconcile | 2026-04-07T12:47:13Z | 2026-04-07T12:47:57Z | 44s |
| finish | 2026-04-07T12:47:57Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- No upstream findings during test verification.

### Reviewer (code review)
- **Gap** (non-blocking): When `find_confrontation_def` returns None for an active encounter, no OTEL event fires and encounter context is silently dropped. Affects `crates/sidequest-server/src/dispatch/prompt.rs` (add else branch with ValidationWarning). *Found by Reviewer during code review.* **RESOLVED in rework commit 8ac1da9.**

### Reviewer (code review round 2)
- No upstream findings during code review round 2.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **Encounter sync moved before prompt build instead of using ctx.encounter field** → ✓ ACCEPTED by Reviewer: DispatchContext lacks the field; snapshot.encounter is the correct path. 28-7 eliminates the sync entirely.
  - Spec source: context-story-28-4.md, Technical Approach
  - Spec text: "if let Some(ref enc) = ctx.encounter"
  - Implementation: Used ctx.snapshot.encounter populated by a pre-prompt sync in mod.rs, since DispatchContext has no top-level encounter field
  - Rationale: DispatchContext doesn't have an `encounter` field; snapshot.encounter is populated post-dispatch (line 2508). Moving the sync before build_prompt_context is minimal and correct.
  - Severity: minor
  - Forward impact: none — 28-7 (promote encounter to sole model) will clean up all sync points anyway

### Dev (rework)
- No deviations from spec — rework addressed reviewer findings directly.

### Reviewer (audit)
- **Silent drop of encounter context when ConfrontationDef missing:** Spec (context-story-28-4.md) shows `if let Some(def) = ctx.find_confrontation_def(...)` with no else branch. Code follows this exactly. However, CLAUDE.md's No Silent Fallbacks rule requires loud failure when something "isn't where it should be." A missing def for an active encounter is exactly that scenario. Not documented by TEA/Dev. Severity: High. **RESOLVED in rework — else branch added with ValidationWarning.**

### Architect (reconcile)
- No additional deviations found. All logged deviations verified:
  - Dev's `ctx.snapshot.encounter` deviation: spec source path verified (`context-story-28-4.md` exists), spec text matches actual document, implementation matches actual code, forward impact accurate (28-7 will consolidate).
  - Reviewer's silent fallback audit: correctly identified, resolved in rework commit. The rework's else branch is additive beyond spec (CLAUDE.md compliance), not a deviation from spec.

## Subagent Results (round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 15/15 tests pass | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 — previous finding resolved | N/A |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 — all 3 previous violations resolved, no new violations | N/A |

**All received:** Yes (3 returned, 6 disabled via settings)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment (round 2)

**Verdict:** APPROVED

**Rework findings resolved:**
- [VERIFIED] [SILENT] Silent fallback fixed — `prompt.rs:347-353` else branch emits `WatcherEventType::ValidationWarning` with `confrontation_def_missing`, `encounter_type`, and `available_defs`. Confirmed by silent-failure-hunter: "No remaining silent failure paths in this block."
- [VERIFIED] [RULE] Placeholder "none" replaced — `prompt.rs:341` now uses `"unphased"`. Confirmed by rule-checker: rule #3 compliant.

**Observations (carried from round 1, still valid):**
1. [VERIFIED] `format_encounter_context` has non-test consumer — evidence: `prompt.rs:346` calls `enc.format_encounter_context(def)` in production path.
2. [VERIFIED] Old inline formatting removed — `from_combat_state`, `from_chase_state`, `ACTIVE ENCOUNTER` absent from prompt.rs.
3. [VERIFIED] OTEL happy path — `prompt.rs:338-344` emits `context_injected` with `encounter_type`, `phase`, `beat_count`, `metric`.
4. [VERIFIED] OTEL miss path — `prompt.rs:348-352` emits `confrontation_def_missing` ValidationWarning. No silent paths remain.
5. [VERIFIED] Encounter sync correct — `mod.rs:460-466` and `mod.rs:3032-3038` populate before prompt build.
6. [VERIFIED] Data flow safe — encounter_type from internal game state, no injection risk.
7. [EDGE] No new edge cases introduced — else branch is defensive, not functional.
8. [TEST] 15/15 tests pass, all meaningful assertions per round 1 analysis.
9. [DOC] Story comment `// (story 28-4)` present at the change site.
10. [TYPE] No new types introduced — uses existing `WatcherEventType::ValidationWarning`.
11. [SEC] No security-relevant changes — encounter_type is internal state.
12. [SIMPLE] Net -8 lines vs develop (44 removed, 24+7+391 test added). Clean simplification.

### Rule Compliance (round 2)

All 3 previously-violated rules now compliant:
- **#1/16/19 Silent fallback:** Resolved — else branch emits ValidationWarning
- **#3 Placeholder:** Resolved — "unphased" replaces "none"
- **#4 Tracing miss path:** Resolved — OTEL event on both paths

### Devil's Advocate (round 2)

The else branch emits a warning but does NOT inject any encounter context into the narrator prompt. Is this correct? Yes — without a ConfrontationDef, there are no beats to list, no cinematography to suggest, and no metric thresholds to show. Injecting partial context would be worse than injecting nothing, because the narrator might reference beats that don't exist. The ValidationWarning makes the gap visible in the GM panel — the operator can then check the genre pack's rules.yaml to add the missing def. The narrator proceeds without mechanical grounding, but at least the system KNOWS it's proceeding blind. This is "fail loudly" — not "fail gracefully with partial data."

Could the `available_defs` count of 0 mislead? No — it accurately reports how many defs were loaded. If it's 0, the genre pack didn't declare any confrontation types. If it's >0 but the type doesn't match, the operator knows it's a type-name mismatch. Both diagnostics are useful.

**Handoff:** To Grand Admiral Thrawn for spec-reconcile and finish

---

## TEA Assessment (verify round 2)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** quality (rework-scoped)
**Files Analyzed:** 1 (prompt.rs only — rework was 7 lines)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-quality | clean | No findings — else branch follows existing ValidationWarning pattern |

**Applied:** 0
**Overall:** simplify: clean

**Quality Checks:** 15/15 tests passing
**Handoff:** To Obi-Wan Kenobi for review round 2

---

## Architect Assessment (spec-check round 2)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Rework addresses both reviewer findings:
- **[HIGH] Silent fallback:** else branch emits `ValidationWarning` with `confrontation_def_missing` — complies with No Silent Fallbacks rule and OTEL principle.
- **[LOW] "none" placeholder:** Changed to `"unphased"` — unambiguous sentinel per rule #3.

All 6 original ACs remain satisfied. The else branch is an additive improvement beyond the spec — it strengthens observability without changing any specified behavior.

**Decision:** Proceed to verify

---

## Dev Assessment (rework)

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/prompt.rs` — Added else branch with `ValidationWarning` OTEL event when `find_confrontation_def` returns None; replaced `"none"` sentinel with `"unphased"`

**Tests:** 15/15 passing (GREEN)
**Branch:** feat/28-4-wire-format-encounter-context (pushed)
**Review Findings Addressed:**
- [HIGH] Silent fallback → Added `confrontation_def_missing` ValidationWarning with encounter_type and available_defs count
- [LOW] `"none"` placeholder → Changed to `"unphased"`

**Handoff:** To next phase

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (pre-existing failures only) | none (28-4 specific) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 — missing else on def miss | confirmed 1 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 — silent fallback (rules 1,4,16,19), "none" placeholder (rule 3), aside behavior change (rule 14) | confirmed 2, dismissed 1 |

**All received:** Yes (3 returned, 6 disabled via settings)
**Total findings:** 2 confirmed, 1 dismissed (aside behavior change: aside HARD CONSTRAINTS section overrides encounter context at narrator level — not a correctness regression)

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | [SILENT][RULE] Silent fallback: when `find_confrontation_def` returns None for an active encounter, no OTEL event fires and encounter context is silently dropped. Two subagents independently flagged this. Violates CLAUDE.md `<critical>` No Silent Fallbacks rule and OTEL observability principle. | `prompt.rs:336-347` | Add else branch emitting `WatcherEventType::ValidationWarning` with action `"confrontation_def_missing"`, `encounter_type`, and available def count. |
| [LOW] | [RULE] Literal `"none"` used as OTEL phase field fallback. Ambiguous — GM panel can't distinguish "no phase" from "field absent." | `prompt.rs:341` | Use `"unphased"` or conditionally omit the field. |

### Rule Compliance

| Rule | Changed Code | Compliant? |
|------|-------------|------------|
| #1 Silent errors | `unwrap_or_else(\|\| "none")` at prompt.rs:341 | Yes (OTEL formatting, not user input) — but see LOW finding re: placeholder |
| #3 Placeholders | `"none"` literal at prompt.rs:341 | Violation (LOW) — ambiguous sentinel in OTEL field |
| #4 Tracing | Happy path OTEL at prompt.rs:338-344 | Compliant. Miss path: VIOLATION — no event emitted |
| #6 Test quality | 15 tests, all meaningful assertions | Compliant — no vacuous tests |
| No Silent Fallbacks | `find_confrontation_def` None path at prompt.rs:336 | VIOLATION (HIGH) — active encounter silently dropped |
| OTEL principle | Happy path emits context_injected | Miss path: VIOLATION — zero GM panel signal |
| Wiring | `format_encounter_context` called at prompt.rs:346 | Compliant — non-test consumer exists |
| #2,5,7-15 | No new enums, constructors, casts, derives, traits, deps | N/A to changed lines |

### Observations

1. [VERIFIED] `format_encounter_context` has non-test consumer — evidence: `prompt.rs:346` calls `enc.format_encounter_context(def)` in production path. Complies with CLAUDE.md wiring rule.
2. [VERIFIED] Old inline formatting removed — evidence: `prompt.rs` no longer contains `from_combat_state`, `from_chase_state`, or `ACTIVE ENCOUNTER`. Grep confirmed.
3. [VERIFIED] OTEL event on happy path — evidence: `prompt.rs:338-344` emits `context_injected` with `encounter_type`, `phase`, `beat_count`, `metric`. Complies with OTEL principle for the success path.
4. [SILENT] Missing OTEL on def-miss path — `prompt.rs:337` inner `if let Some(def)` has no else. When encounter active but def missing: zero signal. Confirmed by both silent-failure-hunter and rule-checker independently.
5. [VERIFIED] Encounter sync is correct — evidence: `mod.rs:460-466` and `mod.rs:3032-3038` populate `ctx.snapshot.encounter` from `combat_state`/`chase_state` before `build_prompt_context` is called. Order of operations is sound.
6. [VERIFIED] Data flow is safe — encounter_type comes from internal game state (`CombatState`/`ChaseState`), not user input. No injection risk in OTEL fields or prompt string.
7. [RULE] `"none"` placeholder in OTEL field — `prompt.rs:341` uses literal `"none"` for missing phase. Rule #3 flags hardcoded placeholder values.

### Devil's Advocate

What if this code is broken? The most dangerous scenario: a genre pack defines encounter types that don't match any ConfrontationDef. This happens when encounter types are created by `from_combat_state` (which hardcodes `"combat"`) or `from_chase_state` (which hardcodes `"chase"`), but the genre pack's `rules.yaml` uses different type strings — say `"melee_combat"` or `"foot_chase"`. The `find_confrontation_def` does a string equality match on `confrontation_type`. A mismatch means the narrator gets ZERO encounter context — no beats, no metric, no phase, no cinematography. The narrator improvises freely. The GM panel shows nothing. This is exactly the "LLM Compensation" failure pattern from Epic 28's context — Claude narrates plausible combat with no mechanics engaged.

How likely is this? The `from_combat_state` function produces `encounter_type: "combat"` and `from_chase_state` produces `encounter_type: "chase"`. If the genre pack uses those exact strings in its ConfrontationDef `type` field, it works. If not — silent failure. There's no compile-time or runtime validation that encounter types match between the old adapter constructors and the genre pack defs. This is a stringly-typed boundary with no validation.

Could a confused developer make this worse? Yes — any new call site to `build_prompt_context` that doesn't first sync `ctx.snapshot.encounter` will silently produce no encounter context. The sync is done by the caller (mod.rs), not by prompt.rs itself. There's no assertion or warning if the caller forgets.

Could a malicious user exploit this? No — encounter_type is internal state, not user-controllable.

The fix is trivial: add an else branch that emits a ValidationWarning. The risk of NOT fixing it is the entire encounter engine going dark without anyone noticing — the exact failure mode this epic exists to kill.

**Handoff:** Back to Yoda (Dev) for fixes — add OTEL warning on def-miss path.

---

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No findings — sync duplication flagged by Architect as deferred to 28-7 |
| simplify-quality | clean | No findings |
| simplify-efficiency | 1 finding | Test helper struct duplication (high confidence) — dismissed: 2 call sites, premature abstraction |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 1 low-priority observation (test helper duplication, dismissed as premature abstraction)
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** 15/15 tests passing, clippy clean on sidequest-server
**Handoff:** To Obi-Wan Kenobi for code review

---

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 6 ACs verified against the diff:
- **Replaces inline:** `from_combat_state`/`from_chase_state` + `ACTIVE ENCOUNTER` formatting removed from prompt.rs. Confirmed absent.
- **Calls format_encounter_context:** Present in prompt.rs production path via `enc.format_encounter_context(def)`.
- **Includes beats:** Delegated to `format_encounter_context()` which produces "Available:" with beat labels, stat_checks, reveals, risk, resolution.
- **Includes cinematography:** Same function produces "Camera:" line with pace guidance.
- **OTEL:** Event emits `context_injected` action with `encounter_type`, `phase`, `beat_count` fields.
- **Wiring:** `format_encounter_context` has non-test consumer in `dispatch/prompt.rs`.

**Deviation review:** Dev logged one deviation (ctx.snapshot.encounter vs ctx.encounter). Accurate, well-justified, minor severity. 28-7 will resolve the underlying gap.

**Observation (non-blocking):** Encounter sync block duplicated in two call sites in mod.rs. Acceptable — extraction would be scope creep; 28-7 eliminates both.

**Decision:** Proceed to verify

---

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/prompt.rs` — Replaced inline encounter formatting (lines 335-374) with format_encounter_context() call via find_confrontation_def
- `crates/sidequest-server/src/dispatch/mod.rs` — Added pre-prompt encounter sync to snapshot.encounter at both prompt build sites

**Tests:** 15/15 passing (GREEN)
**Branch:** feat/28-4-wire-format-encounter-context (pushed)

**Handoff:** To Han Solo for verify phase

---

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-point API wiring story — replaces inline encounter formatting with format_encounter_context()

**Test Files:**
- `crates/sidequest-server/tests/encounter_context_wiring_story_28_4_tests.rs` — 15 tests covering all 6 ACs

**Tests Written:** 15 tests covering 6 ACs
**Status:** RED (8 failing, 7 passing — ready for Dev)

### Failure Breakdown
| Category | Tests | Status |
|----------|-------|--------|
| AC-Replaces-Inline (removal) | 3 tests | FAILING — from_combat_state, from_chase_state, ACTIVE ENCOUNTER still in prompt.rs |
| AC-Calls-FEC (addition) | 2 tests | FAILING — format_encounter_context, find_confrontation_def not in prompt.rs |
| AC-Includes-Beats | 2 tests | PASSING — format_encounter_context already produces correct output |
| AC-Includes-Cinema | 1 test | PASSING — cinematography hints present in output |
| AC-OTEL | 3 tests | 1 PASSING (encounter_type), 2 FAILING (context_injected event name, beat_count field) |
| AC-Wiring | 2 tests | FAILING — non-test consumer doesn't exist yet |
| Regression | 2 tests | PASSING — header format and combat type work |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 Test quality | Self-check: all 15 tests have meaningful assert! or assert_eq! | verified |
| Wiring verification | format_encounter_context_has_non_test_consumer_in_server, prompt_rs_uses_confrontation_defs | failing |
| No silent fallbacks | from_combat_state_removed, from_chase_state_removed (ensures old fallback path is gone) | failing |

**Rules checked:** 3 of 15 applicable (most rules apply to implementation, not test writing)
**Self-check:** 0 vacuous tests found — all assertions check specific string content or boolean conditions

**Handoff:** To Yoda for implementation (GREEN phase)

---

## Sm Assessment

**Story:** 28-4 — Wire `format_encounter_context()` into narrator prompt
**Routing:** TDD workflow → red phase → Han Solo (TEA)
**Rationale:** 3-point API story with clear wiring scope. Dependency 28-1 (ConfrontationDefs loaded) is complete. `format_encounter_context()` exists and needs to be integrated into the narrator prompt path, replacing inline combat/chase context construction. TDD is appropriate — tests first to define the expected prompt structure, then wire the function in.
**Risk:** Low. Function exists, this is integration work.
**Branch:** `feat/28-4-wire-format-encounter-context`