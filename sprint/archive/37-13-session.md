---
story_id: "37-13"
jira_key: ""
epic: "37"
workflow: "tdd"
---

# Story 37-13: Encounter creation gate silently drops new confrontation type

## Story Details
- **ID:** 37-13
- **Jira Key:** (pending creation)
- **Workflow:** tdd
- **Repo:** api
- **Type:** bug
- **Priority:** p0
- **Points:** 2
- **Stack Parent:** none

## Problem Statement

Encounter creation gate silently drops new confrontation type when an unresolved encounter is active.

**Location:** `dispatch/mod.rs:1768-1814`

**Issue:** The encounter creation logic only creates a new confrontation when:
- `is_none` (no active encounter), OR
- `resolved` (encounter is resolved)

There is **no else-branch** for the case where a new confrontation type arrives but an unresolved encounter is already active. This silent fallback violates the "No Silent Fallbacks" principle from CLAUDE.md.

**Impact:** When narrator attempts to transition to a new confrontation type mid-encounter, the game state is inconsistent — the old encounter remains active while the prose and narrator intent have moved to a new confrontation. No OTEL warning is emitted, making this undetectable without deep log inspection.

**Design Questions:**
1. Should a new confrontation type queue, transition, or error?
2. What's the expected state machine for multi-confrontation sequences?
3. When should the narrator signal the transition?

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-14T12:31:31Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-14T00:00Z | 2026-04-14T11:46:21Z | 11h 46m |
| red | 2026-04-14T11:46:21Z | 2026-04-14T11:57:12Z | 10m 51s |
| green | 2026-04-14T11:57:12Z | 2026-04-14T12:01:44Z | 4m 32s |
| verify | 2026-04-14T12:01:44Z | 2026-04-14T12:08:10Z | 6m 26s |
| review | 2026-04-14T12:08:10Z | 2026-04-14T12:14:41Z | 6m 31s |
| green | 2026-04-14T12:14:41Z | 2026-04-14T12:19:25Z | 4m 44s |
| verify | 2026-04-14T12:19:25Z | 2026-04-14T12:21:35Z | 2m 10s |
| review | 2026-04-14T12:21:35Z | 2026-04-14T12:31:31Z | 9m 56s |
| finish | 2026-04-14T12:31:31Z | - | - |

## Sm Assessment

p0 silent-fallback bug in `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs:1768-1814`. Encounter creation only handles `is_none` or `resolved`; unresolved-active path silently drops new confrontation type. Violates CLAUDE.md "No Silent Fallbacks."

**TEA scope:** Write failing test(s) exercising dispatch path where an unresolved encounter is active and a new confrontation type arrives. Assert that behavior is explicit — either transition, queue, or loud error + OTEL warning — rather than silent drop. Keith/Architect may need to weigh in on which explicit behavior is correct; default assumption is loud error + OTEL span until design question resolved.

**Design questions open** (flag to Architect if TEA hits ambiguity): transition vs queue vs error, and what state machine governs multi-confrontation sequences.

**Wiring:** Fix must add OTEL watcher event on the decision branch per OTEL Observability Principle.

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Status:** RED (6 failing tests)

**Test File:**
- `sidequest-api/crates/sidequest-server/tests/integration/encounter_creation_gate_story_37_13_tests.rs` — source-inspection tests for the encounter creation gate, matching the established pattern in `npc_turns_beat_system_story_28_8_tests`.

**Coverage:**
| AC | Test | Status |
|----|------|--------|
| AC-Explicit-Branch | `encounter_creation_has_explicit_active_unresolved_branch` | failing |
| AC-Gate-Complete | `encounter_creation_gate_covers_both_branches` | failing |
| AC-OTEL-Visibility (event) | `otel_event_emitted_on_active_unresolved_confrontation` | failing |
| AC-OTEL-Visibility (severity) | `otel_event_severity_is_elevated` | failing |
| AC-No-Silent-Drop (tracing) | `tracing_warning_emitted_for_active_unresolved_case` | failing |
| AC-No-Silent-Drop (regression guard) | `original_silent_gate_pattern_is_not_sole_guard` | failing |

**Marker strings Dev should use (pick one, or coordinate with Architect):**
- `encounter.creation_blocked` — default, implies loud error
- `encounter.creation_conflict` — implies conflict logging
- `encounter.transition_requested` — implies transition path
- `encounter.active_confrontation_conflict` — verbose alternative

Any of the four unblocks `encounter_creation_has_explicit_active_unresolved_branch` and `otel_event_emitted_on_active_unresolved_confrontation`. If Architect/Keith decide on a different string, update the test and log a deviation.

**Required fix shape:**
1. Outer gate must gain an `else` branch (or convert to `match`) for `Some(encounter) where !encounter.resolved`.
2. That branch must emit a `WatcherEventBuilder::new("encounter", ...)` with `ValidationWarning` event type OR `.severity(Severity::Warn)`.
3. That branch must emit a distinct `tracing::warn!` (the window currently has exactly 1 warn — the pre-existing ConfrontationDef-missing one).
4. The marker string must be one of the four listed above.

**Design question (unresolved, flagged to Architect):** transition vs queue vs loud-error. The tests are deliberately agnostic — any of the three satisfies the assertions as long as they're explicit and logged. Keith: if you want a specific semantics, say so now and I'll tighten the assertions.

**Self-check:** No vacuous assertions. Every test asserts a specific string-presence or count. No `let _ = ...`. No `assert!(true)`.

**Wiring test:** The integration test file is registered in `tests/integration/main.rs` (mod declaration added), so it runs as part of the standard `cargo test --test integration` invocation. The tests exercise production source directly via `include_str!`.

**Handoff:** To Naomi Nagata (Dev) for GREEN implementation.

## Dev Assessment

**Phase:** finish
**Implementation Complete:** Yes
**Status:** GREEN (6/6 tests passing)

**Files Changed:**
- `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` — added explicit `else` branch on the encounter creation gate. On active-unresolved-encounter + new confrontation type, emits `encounter.creation_blocked` OTEL ValidationWarning with `requested_type`, `active_type`, `active_metric`, `reason`, plus a distinct `tracing::warn!`. Current encounter continues running; new confrontation is dropped (loud, not silent).

**Semantics chosen:** **block** (loud-error default per SM assessment). Transition vs queue vs error was flagged as an open design question; the test suite is agnostic to which one wins, so I went with the safest path — no state-machine surgery, narrator learns via OTEL that their attempted swap was rejected. If Architect later decides transition/queue is correct, this branch is the obvious hook to extend.

**Marker string:** `encounter.creation_blocked` (first of the four TEA offered).

**Verification:**
- `cargo test -p sidequest-server --test integration encounter_creation_gate_story_37_13` → 6/6 pass
- `cargo clippy -p sidequest-server -- -D warnings` → clean
- Fix touches only one `if let Some(ref confrontation_type)` block — no collateral damage to surrounding dispatch logic.

**Wiring verified:** The `else` branch sits inside the same production dispatch path that the narrator hits every turn (`dispatch_action_result` → confrontation handling). No new code paths, no optional hookup — the fix runs automatically whenever the narrator emits `confrontation` during an active unresolved encounter. OTEL emission uses the existing `WatcherEventBuilder` already imported in this module.

**Branch:** `feat/37-13-encounter-creation-gate` (pushed to origin)

**Handoff:** To Amos Burton (TEA) for verify phase — simplify + quality-pass.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (6/6 37-13 tests + 385/385 previously-passing integration tests)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (dispatch/mod.rs, encounter_creation_gate_story_37_13_tests.rs, tests/integration/main.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | no duplication introduced; existing OTEL+tracing pattern is context-specific per subsystem |
| simplify-quality | clean | naming consistent, no dead code, follows "No Silent Fallbacks" correctly |
| simplify-efficiency | 3 findings (1 high, 1 medium, 1 low) | see triage below |

**Triage:**
- **Dismissed — high-conf "extract marker-string helper across 4 tests":** The finding misreads minimalism. Extracting a helper to consolidate a 4-string marker list across 4 tests is *adding* abstraction, not removing it. The project stance is "three similar lines is better than a premature abstraction" — each test asserts a different AC and the marker-string repetition is load-bearing: it lets the test failure messages point at the specific AC violated. Keeping as-is.
- **Flagged — medium-conf `.unwrap_or((String::new(), 0))`:** Technically the `else` branch proves `encounter.is_some()`, so `.unwrap_or` is defensive noise. But `.unwrap()` risks a panic if future refactors change the outer guard, and the defensive form is safer without measurable cost. Per workflow rules medium findings are flagged-not-applied. Leaving for Reviewer's call.
- **Flagged — low-conf indirect `} else {` count:** The test counts `} else {` occurrences (must be >= 2, since one pre-exists for ConfrontationDef-missing). Suggestion is to switch to a more direct check, but the count approach is robust and well-commented. Leaving as-is.

**Applied:** 0 fixes
**Flagged for Review:** 2 (medium + low)
**Noted:** 1 (dismissed high)
**Reverted:** 0

**Overall:** simplify: clean (no fixes required)

### Quality Checks

- `cargo test -p sidequest-server --test integration` — 385 passed, 39 failed, 4 ignored. **The 39 failures are pre-existing on develop** (verified by running the suite on develop baseline: 379 passed, same 39 failed). My branch adds 6 new passing tests with zero regressions.
- `cargo clippy -p sidequest-server -- -D warnings` — clean.
- `cargo fmt --check` — my file is formatted; pre-existing drift exists in `crates/sidequest-server/src/lib.rs` but is out of scope for this story. Not touching it.

### Regression Guard

Before any simplify changes were considered, I ran `cargo test` on develop baseline to establish the regression floor. This is the only way to distinguish 37-13 breakage from pre-existing breakage on develop, per `feedback_verify_e2e`. Confirmed: all 39 failures are present on develop at the current HEAD.

**Handoff:** To Chrisjen Avasarala (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (1 high, 1 medium) | 1 confirmed (high unwrap_or), 1 deferred (duplicate-type sub-case — scope creep) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (1 high, 2 medium, 1 low) | 1 confirmed (duplicate test logic), 1 downgraded (wiring test → medium), 1 deferred (severity anchor), 1 dismissed (implementation coupling — established convention) |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (1 high) | 1 confirmed (deferred note without anchor) |
| 6 | reviewer-type-design | Yes | findings | 3 (2 medium, 1 low) | 1 confirmed (missing metric.name), 1 merged-into-high (unwrap_or — same as silent-failure finding), 1 dismissed (stringly-typed encounter_type — pre-existing, out of scope) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (2 high) | 1 confirmed (Rule #1 unwrap_or — third independent confirmation), 1 downgraded (Rule #18 wiring test → medium with rationale) |

**All received:** Yes (6 returned, 3 with findings of note)
**Total findings:** 4 confirmed (1 high, 3 medium), 2 dismissed, 2 deferred

## Rule Compliance

Rust lang-review checklist applied exhaustively to diff:

| # | Rule | Status | Evidence |
|---|------|--------|----------|
| 1 | Silent error swallowing | **FAIL** | `dispatch/mod.rs:1829` — `.unwrap_or((String::new(), 0))` on `ctx.snapshot.encounter` with no documentation of why the default is safe. The `else` branch logically guarantees `Some(unresolved)`, making the fallback dead code that masks the invariant. |
| 2 | #[non_exhaustive] on enums | PASS | No new enums in diff |
| 3 | Hardcoded placeholders | PASS | `"active_unresolved_encounter"` and `"encounter.creation_blocked"` are semantically meaningful event/reason strings |
| 4 | Tracing coverage/correctness | PASS | New `tracing::warn!` on the blocked path; `warn!` (not `error!`) is correct for narrative conflict, not server error |
| 5 | Validated constructors | N/A | No new constructors |
| 6 | Test quality | **FAIL** | `original_silent_gate_pattern_is_not_sole_guard` (lines 256-282) duplicates `encounter_creation_gate_covers_both_branches` (lines 139-168) logic — both count `} else {` ≥ 2 on the same window. When the original gate pattern is still present (which it always is after a correct fix), the two tests are functionally identical and cannot independently catch regressions. |
| 7 | Unsafe `as` casts | PASS | No `as` casts in diff |
| 8 | Deserialize bypass | N/A | No Deserialize derives |
| 9 | Public fields | N/A | No new structs |
| 10 | Tenant context | N/A | Not a multi-tenant system |
| 11 | Workspace deps | N/A | No Cargo.toml changes |
| 12 | Dev-only deps | N/A | No Cargo.toml changes |
| 13 | Constructor/Deserialize consistency | N/A | No new types |
| 14 | Fix-introduced regressions | **FAIL** | Check #14 is the meta-check: the fix for a "No Silent Fallbacks" violation introduces a `.unwrap_or((String::new(), 0))` fallback — the same class of bug the story was fixing. This is exactly the "fix re-introduces the same bug" pattern check #14 exists to catch. |
| 15 | Unbounded recursion | N/A | No recursive parsers |
| — | CLAUDE.md No Silent Fallbacks | **FAIL** | Same root cause as Rule #1 — the defensive fallback produces empty OTEL fields if the outer invariant ever changes |
| — | CLAUDE.md OTEL Observability | **PARTIAL** | Event fires, but `active_metric` is emitted without its `metric.name` label — GM panel sees a bare number (3) without knowing if it's HP, separation distance, leverage, or beats. See type-design finding. |
| — | Every Test Suite Needs a Wiring Test | PARTIAL (downgraded) | All 6 tests are source-inspection. Rule normally demands an integration test that exercises the code path from a production entry. **Downgraded with rationale:** the new `else` branch is inside `dispatch_player_action`, which is already proven wired by `encounter_context_wiring_story_28_4_tests` — no new component is being wired, only a new branch in an existing wired function. This is adjacent to the rule's intent, not a violation of it. |

## Devil's Advocate

The narrator, in a hot playtest, sends `confrontation: "combat"` every turn out of LLM habit. The first turn creates an encounter and fires `encounter.created`. The second turn hits the new `else` branch and fires `encounter.creation_blocked` — the GM panel now shows a `ValidationWarning` every turn until the encounter resolves. Over a 20-turn combat, that's 19 false positives in the GM panel lie-detector feed. The operator's eyes glaze over and real `ValidationWarning`s get buried. This is the "alert fatigue" failure mode that Rule #4 specifically warns about. The silent-failure-hunter's medium finding about the duplicate-type sub-case is actually a prevention mechanism for this exact scenario — distinguishing `requested == active` (idempotent re-emit, lower severity) from `requested != active` (genuine conflict, ValidationWarning).

A paranoid user creates a genre pack with an `encounter_type` that is an empty string. The `else` branch now emits `active_type = ""` into the OTEL event. The GM panel shows `active_type: ""` with no warning. The narrator re-emits `"combat"`. The test's `requested_type` is valid; `active_type` is garbage. No log explains it. This is the classic "silent stringly-typed mismatch" and the type-design subagent's low finding about `EncounterTypeKey` is pointing at a real (pre-existing) weakness that this diff makes more load-bearing.

A future engineer refactors the outer gate from `is_none() || resolved` to a more complex condition that admits a third case. The `.unwrap_or((String::new(), 0))` silently becomes reachable. The GM panel suddenly shows encounter.creation_blocked events with empty `active_type` fields, and no test fails because the source-inspection tests only check that the string "ValidationWarning" is present — they do not exercise the actual code path. This is the invariant-masking risk that three independent subagents flagged.

A narrator emits `confrontation: "Combat"` with a capital C. `StructuredEncounter.encounter_type` is lowercase `"combat"` from the ConfrontationDef. The else branch fires `encounter.creation_blocked` with `requested_type: "Combat"` and `active_type: "combat"` — the GM panel sees a "conflict" that is actually a casing bug in the narrator prompt. Nothing in the fix normalizes. Out of scope for this story, but the fix shouldn't add another comparison surface that bakes in the fragility.

**The Devil's Advocate uncovered one thing the review missed:** alert-fatigue risk from narrator habitually emitting the same confrontation type every turn. This corroborates the silent-failure-hunter's duplicate-type sub-case finding and upgrades its severity from "deferred" to "should fix with the unwrap_or fix."

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Tag | Issue | Location | Fix Required |
|----------|-----|-------|----------|--------------|
| [HIGH] | [SILENT][TYPE][RULE] | `.unwrap_or((String::new(), 0))` masks the else-branch invariant and produces empty OTEL fields if the outer guard is ever refactored. Flagged HIGH by three independent subagents. Violates Rust lang-review Rule #1 (undocumented defensive default) AND Rule #14 (fix-introduced regression — the fix for a silent-fallback bug introduces a defensive fallback of its own). Directly contradicts the story's "No Silent Fallbacks" theme. | `crates/sidequest-server/src/dispatch/mod.rs:1825-1830` | Restructure using `if let Some(active) = ctx.snapshot.encounter.as_ref()` in the outer guard, so the `else` branch binds `active` directly and can read `active.encounter_type.clone()` and `active.metric.current` without any Option unwrap. OR: use `.expect("else branch guarantees Some(unresolved encounter)")` with a diagnostic message. First option is preferred — it encodes the invariant structurally. |
| [HIGH] | [RULE] | Alert fatigue from same-type re-emission. When the narrator emits the same `confrontation` type every turn (normal LLM behavior during a combat), the `else` branch fires a `ValidationWarning` every turn for the duration of the encounter. Over a 20-turn combat, 19 false positives bury real conflicts in the GM panel feed. Surfaced via Devil's Advocate + corroborated by [SILENT] duplicate-type finding. | `crates/sidequest-server/src/dispatch/mod.rs:1831-1842` | Add a sub-branch: if `confrontation_type == active.encounter_type`, emit `encounter.creation_duplicate` at `StateTransition` severity (lower, non-alerting) — this is an idempotent re-emit. Reserve `ValidationWarning` + `encounter.creation_blocked` for genuine type-conflict (`requested != active`). Two distinct OTEL event names, two distinct severity levels. |
| [MEDIUM] | [TEST] | Duplicate test logic: `original_silent_gate_pattern_is_not_sole_guard` and `encounter_creation_gate_covers_both_branches` both count `} else {` occurrences ≥ 2 on the same window. When the original gate pattern is still present (it always is after a correct fix), the two tests are functionally identical — one cannot independently catch a regression the other misses. Flagged HIGH by test-analyzer; downgraded to medium since it's duplication, not a logic bug. | `crates/sidequest-server/tests/integration/encounter_creation_gate_story_37_13_tests.rs:139-168 and 256-282` | Delete `original_silent_gate_pattern_is_not_sole_guard` OR give it a genuinely different assertion — e.g., verify the original `is_none() || is_some_and(|e| e.resolved)` condition string is still present (confirming it wasn't accidentally deleted during restructuring), as a complement rather than a duplicate. |
| [MEDIUM] | [DOC] | Deferred design note without anchor: `dispatch/mod.rs:1774` contains "Transition/queue semantics are a future design question" with no ADR reference, no story link, no owner. The codebase has 78 ADRs and the project's own feedback memory flags unanchored deferrals as a rot pattern. | `crates/sidequest-server/src/dispatch/mod.rs:1774` | Either open Story 37-14 (or equivalent) for transition/queue design and cite it in the comment, OR delete the aspirational note. No floating deferrals. |
| [MEDIUM] | [TYPE] | Missing `metric.name` in OTEL emission: `active_metric` is emitted as a bare `i32` with no metric name label. The GM panel sees a number (e.g., `3`) without knowing if it's HP, separation distance, leverage, or beats. `EncounterMetric` already carries a `name` field. One-line fix. | `crates/sidequest-server/src/dispatch/mod.rs:1835` | Add `.field("active_metric_name", &active.metric.name)` alongside the existing `.field("active_metric", ...)`. Self-describing telemetry. |

**Pattern observed:** Good — the `else` branch correctly uses `WatcherEventType::ValidationWarning` (the right severity for a narrative conflict), and the `tracing::warn!` is separate from the pre-existing `encounter.creation_failed` warn, so the OTEL+tracing dual-emission pattern matches the rest of the dispatch module (see `dispatch/mod.rs:1062, 1128` for `guest_npc` ValidationWarning usage).

**Data flow traced:** Narrator `ActionResult.confrontation: Some("combat")` → `dispatch_player_action` → encounter creation block → outer `is_none() || resolved` guard → (new) else branch → OTEL WatcherEvent + tracing warn → current encounter continues running unchanged. The flow is correct; the implementation details inside the else branch are what need revision.

**Wiring verified:** The new `else` sits inside `dispatch_player_action`, which is called from `lib.rs` WebSocket handler via the existing dispatch pipeline. `encounter_context_wiring_story_28_4_tests` independently proves this entry point is wired. No new wiring gap from this diff.

**Error handling:** The `.unwrap_or` fallback is the only concern — see HIGH finding #1.

**[VERIFIED] 6 tests all pass post-fix** — evidence: `cargo test -p sidequest-server --test integration encounter_creation_gate_story_37_13` returned 6/6 passing. Complies with TDD RED→GREEN flow.

**[VERIFIED] Fix does not touch security-critical types** — evidence: diff contains no `tenant_id`, `auth_token`, `signature`, or `permissions` references. Rule #9 (public fields on security-critical types) is N/A here.

**[VERIFIED] Fix uses established dual-emission pattern (OTEL + tracing)** — evidence: matches `dispatch/mod.rs:1062` (guest_npc ValidationWarning + tracing) and `dispatch/mod.rs:1846` (player_beat_from_narrator_ignored). This is the correct pattern for narrative conflicts in this codebase.

**Handoff:** Back to Naomi Nagata (Dev) for green-phase rework. Findings are implementation changes (unwrap_or restructuring, duplicate-type sub-branch, metric.name field, deferred comment cleanup) plus one test-quality cleanup. No new failing tests required — existing tests will still pass after the impl fixes, and the duplicate test removal is a direct deletion.

## Dev Assessment (rework round 2)

**Phase:** finish (rework round 1 from review)
**Implementation Complete:** Yes
**Status:** GREEN (7/7 tests passing, clippy clean)

**Reviewer findings addressed:**

| Severity | Finding | Fix | Commit |
|----------|---------|-----|--------|
| HIGH | `.unwrap_or((String::new(), 0))` masks else-branch invariant | Restructured outer guard as `if let Some(active) = ctx.snapshot.encounter.as_ref().filter(\|e\| !e.resolved)`. The blocked path binds `active` directly — the invariant is now encoded in the type system, not defended via runtime fallback. Zero `.unwrap_or` in the diff. | 6026bd5 |
| HIGH | Alert-fatigue on same-type re-emission | Split blocked path into two sub-branches: `requested == active.encounter_type` emits `encounter.creation_duplicate` at `StateTransition` severity (idempotent, non-alerting); `requested != active.encounter_type` emits `encounter.creation_blocked` at `ValidationWarning` severity (genuine conflict). A 20-turn combat with repeated narrator emits no longer spams the GM panel. | 6026bd5 |
| MEDIUM | Duplicate test logic (`original_silent_gate_pattern_is_not_sole_guard` vs `encounter_creation_gate_covers_both_branches`) | Deleted `original_silent_gate_pattern_is_not_sole_guard`. Added two replacement tests that assert genuinely new behavior: `duplicate_confrontation_type_uses_lower_severity_event` and `encounter_conflict_event_includes_metric_name`. | 6026bd5 |
| MEDIUM | Deferred comment without anchor ("Transition/queue semantics are a future design question") | Deleted the floating note. The duplicate-vs-conflict split is now the semantics. If transition/queue is ever needed, open a new story — no aspirational comments in the code. | 6026bd5 |
| MEDIUM | Missing `metric.name` in OTEL emission | Added `.field("active_metric_name", &active.metric.name)` to both the duplicate and blocked event builders. GM panel can now interpret `active_metric: 3` as e.g. "HP" or "separation_distance". | 6026bd5 |

**Files Changed (since last review round):**
- `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` — restructured the encounter creation block. The full outer guard is now a three-branch chain: `if let Some(active) = ...unresolved...` (blocked, split into duplicate/conflict) → `else if let Some(def) = ...` (create) → `else` (missing def warn).
- `sidequest-api/crates/sidequest-server/tests/integration/encounter_creation_gate_story_37_13_tests.rs` — deleted duplicate regression test, added two new tests (duplicate-severity, metric-name-included). Test count: 6 → 7.

**Tests:** 7/7 passing (was 6/6 pre-rework)
**Clippy:** clean
**Branch:** `feat/37-13-encounter-creation-gate` (pushed, head `6026bd5`)

**[VERIFIED] Zero `.unwrap_or` in diff:** `grep 'unwrap_or' crates/sidequest-server/src/dispatch/mod.rs` shows no matches inside the encounter creation block. The invariant is now encoded via `.filter()` on the Option.

**[VERIFIED] Duplicate-vs-conflict distinction works structurally:** `active.encounter_type == *confrontation_type` uses PartialEq on String (the existing field type). If Keith decides to normalize encounter_type keys later (the type-design subagent's low finding), the comparison is a single call site.

**[VERIFIED] GM panel receives metric name:** both the StateTransition and ValidationWarning events emit `active_metric_name` alongside `active_metric`. OTEL consumers can now self-describe the number.

**Unaddressed findings (with rationale):**
- **[SILENT] duplicate-type sub-case** — ADDRESSED via the split (this was the same finding as the HIGH alert-fatigue one).
- **[TEST] severity test anchor fragility** (medium): `window.contains("ValidationWarning")` could theoretically match a comment. Not addressed — the window is tightly scoped and the current code uses `WatcherEventType::ValidationWarning` which would be caught by either anchor. Low practical risk. Flagged for future hardening if Keith wants the stricter anchor.
- **[TEST] wiring test gap** (downgraded to medium): The else branch is inside `dispatch_player_action` which is independently proven wired by `encounter_context_wiring_story_28_4_tests`. No new wiring gap. Reviewer already downgraded this with rationale.
- **[TYPE] stringly-typed encounter_type** (low): Pre-existing weakness, out of scope. Reviewer already dismissed.

**Handoff:** To Amos Burton (TEA) for verify phase — simplify + quality-pass on the reworked files.

## TEA Assessment (verify round 2)

**Phase:** finish (round 2, post-rework)
**Status:** GREEN confirmed (7/7 37-13 tests, clippy clean, zero regressions)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (dispatch/mod.rs, encounter_creation_gate_story_37_13_tests.rs, tests/integration/main.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | no findings — two-branch duplicate/blocked emission is logically distinct and not extractable without obscuring the event type distinction |
| simplify-quality | clean | no findings — uses idiomatic `.filter()`/`.as_ref()` patterns, no unsafe casts, proper imports, follows project conventions |
| simplify-efficiency | clean | no findings — considered `HashMap::new()` duplication in actor loops, dismissed (pre-existing, 2-use not enough for abstraction) |

**Applied:** 0 fixes
**Flagged for Review:** 0
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean

### Quality Checks

- `cargo test -p sidequest-server --test integration encounter_creation_gate_story_37_13` — 7/7 passing (includes 2 new rework tests: `duplicate_confrontation_type_uses_lower_severity_event`, `encounter_conflict_event_includes_metric_name`)
- `cargo clippy -p sidequest-server -- -D warnings` — clean
- Zero `.unwrap_or` in the encounter creation block (verified by reading the diff)
- The 39 pre-existing integration failures on develop remain unchanged — no new regressions

### Rework Delta Verified

Each of the 5 reviewer findings was verified against the current diff:

1. **HIGH [.unwrap_or masked invariant]** — FIXED. New structure uses `if let Some(active) = ctx.snapshot.encounter.as_ref().filter(|e| !e.resolved)`. No defensive `unwrap_or` in the block.
2. **HIGH [alert fatigue]** — FIXED. Two distinct events: `encounter.creation_duplicate` (StateTransition, non-alerting) vs `encounter.creation_blocked` (ValidationWarning, alerting). Narrator repetition no longer spams the GM panel.
3. **MEDIUM [duplicate test logic]** — FIXED. `original_silent_gate_pattern_is_not_sole_guard` deleted; replaced with two genuinely different tests asserting new behavior.
4. **MEDIUM [deferred comment without anchor]** — FIXED. "Transition/queue semantics are a future design question" removed.
5. **MEDIUM [missing metric.name]** — FIXED. Both events now include `.field("active_metric_name", &active.metric.name)`.

**Handoff:** To Chrisjen Avasarala (Reviewer) for re-review.

## Subagent Results (round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (1 high, pre-existing) | 1 deferred (scope: `encounter.rs:290` pre-existing `MetricDirection` default is out of 37-13 scope; captured as delivery finding) |
| 4 | reviewer-test-analyzer | Yes | findings | 2 (1 high, 1 medium) | 1 confirmed (severity test matches new prose comment — test fragility realized by rework), 1 confirmed (duplicate severity not negatively tested) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — round 1 finding confirmed resolved |
| 6 | reviewer-type-design | Yes | findings | 1 (1 medium, pre-existing) | 1 dismissed (pre-existing `EncounterActor.role` stringly-typed pattern; diff doesn't introduce — only reorders) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (3 high) | 1 confirmed (Rule #1 resolved), 1 downgraded (Rule #4/#14 duplicate branch no tracing — see rationale), 1 re-raised-then-dismissed (Rule #18 wiring — already downgraded in round 1 with rationale, same rationale stands) |

**All received:** Yes (6 returned, 4 with findings of note)
**Total findings:** 2 confirmed (both medium), 3 deferred/dismissed (with rationale), 0 high after triage

## Rule Compliance (round 2)

| # | Rule | Status | Evidence |
|---|------|--------|----------|
| 1 | Silent error swallowing | **PASS** | Round 1 `.unwrap_or` finding resolved via `.filter(\|e\| !e.resolved)` + `if let Some(active)` restructure. Zero `.unwrap_or` in the encounter creation block. |
| 2 | #[non_exhaustive] | N/A | No new enums |
| 3 | Hardcoded placeholders | PASS | All string literals are semantic (event names, reason tags, role strings) |
| 4 | Tracing coverage/correctness | **PARTIAL/PASS** | Rule-checker flagged the duplicate branch as missing a tracing call. **Downgraded:** Rule #4 applies to *error paths* ("Error paths MUST have tracing::error! or tracing::warn!"). The duplicate path is an idempotent state transition, not an error — a `tracing::warn!` there would reintroduce the exact alert-fatigue issue that the duplicate/blocked split was designed to prevent. The `OTEL StateTransition` event is the correct single-channel emission for this case. `tracing::info!` could arguably be added but is not required by Rule #4. |
| 5 | Validated constructors | N/A | No new constructors |
| 6 | Test quality | **FAIL (medium)** | `otel_event_severity_is_elevated` uses `window.contains("ValidationWarning")` which now matches the new prose comment "ValidationWarning stream" added in the rework. Test still passes on correct code (real `WatcherEventType::ValidationWarning` token is present) but would *also* pass on broken code where the blocked WatcherEventBuilder was deleted and only the comment remained. The round 1 test-analyzer finding that I downgraded has been realized by the rework. |
| 7–13 | — | N/A/PASS | No applicable patterns in diff |
| 14 | Fix-introduced regressions (meta) | **PARTIAL** | Round 1's `.unwrap_or` class of bug eliminated. No NEW instances of Rules #1-#13 introduced. The test fragility under Rule #6 is a new instance but is a test-quality concern, not a production-code regression. |
| 15 | Unbounded recursion | N/A | No recursive patterns |
| — | CLAUDE.md No Silent Fallbacks | **PASS** | All three post-rework branches (duplicate/blocked/create/missing-def) handle their cases explicitly with OTEL and/or tracing emission |
| — | CLAUDE.md OTEL Observability | **PASS** | Both blocked AND duplicate paths emit WatcherEvents. Metric name now included. GM panel can distinguish the two cases. |
| — | Every Test Suite Needs a Wiring Test | PARTIAL (downgraded, same rationale as round 1) | Else branch is inside already-wired `dispatch_player_action` (proven by `encounter_context_wiring_story_28_4_tests`). No new component requires wiring. |

## Devil's Advocate (round 2)

A future engineer deletes the `WatcherEventBuilder::new("encounter", WatcherEventType::ValidationWarning)` call by accident during a refactor, leaving only the surrounding comment that says "conflicts in the GM panel ValidationWarning stream." What does `otel_event_severity_is_elevated` do? It searches for `"ValidationWarning"` in the window. The comment contains that string. The test passes. The production code is broken. The test suite is now false-negative. This is exactly the fragility I flagged at medium in round 1 and downgraded with rationale — the rationale was "the current code looks fine." The rework proved the rationale wrong by adding a comment that contains the target token. The test needs tightening — `window.contains("WatcherEventType::ValidationWarning")` (the enum-qualified form) cannot match a prose comment. Trivial one-line fix.

A future engineer reads the duplicate branch and notices it has no tracing call. They add `tracing::warn!(...)` to match the sibling pattern. This reintroduces the alert-fatigue issue: a 20-turn combat now produces 19 `warn!` lines in the operator log. The silent-failure hunter would flag this immediately, and so would the Devil's Advocate from round 1. This is why the duplicate branch intentionally has no tracing::warn — it's a state transition, not a warning. The Rule #4 finding from rule-checker is misclassifying the branch. Downgraded.

A narrator emits `confrontation: "Combat"` (capital C) while the active encounter has `encounter_type: "combat"`. The `active.encounter_type == *confrontation_type` comparison uses String PartialEq, which is case-sensitive. The test falls through to the BLOCKED branch and emits `encounter.creation_blocked` as a genuine conflict — when actually it's a casing typo in the narrator prompt. This is the low-confidence stringly-typed finding from round 1 type-design, still present, still out of scope for 37-13. Capturing as delivery finding for a future hardening story.

A narrator re-emits `confrontation: "combat"` on every turn of a 20-turn combat. The duplicate branch fires 20 `encounter.creation_duplicate` StateTransition events. The GM panel shows 20 StateTransitions in the encounter feed. Is that itself noise? Not really — StateTransitions are passive state snapshots, not alerts. Operators filter to ValidationWarning in the GM panel. The 20 StateTransitions get grouped and don't generate notifications. The fix is working as designed.

A genre pack author writes a ConfrontationDef with a misspelled `metric.direction` field ("ascendinig"). The pre-existing `from_confrontation_def` silently defaults to Ascending. The encounter creates with wrong mechanics. This is the silent-failure-hunter HIGH finding. It's pre-existing code in `encounter.rs`, not touched by this diff, but the new creation path (`else if let Some(def)`) is the narrator-triggered entry point. **Capturing as a delivery finding** — it's a real bug but out of 37-13 scope. A new story should be opened for `from_confrontation_def` validation.

**The Devil's Advocate uncovered:** (1) the severity test fragility that was mine to catch in round 1 but I deferred; (2) confirmation that the rule-checker Rule #4 finding is a misclassification; (3) the pre-existing MetricDirection silent default is a separate story; (4) the stringly-typed encounter_type casing issue is a separate story.

## Reviewer Assessment

**Verdict:** APPROVED

| Severity | Tag | Issue | Location | Disposition |
|----------|-----|-------|----------|-------------|
| [MEDIUM] | [TEST] | `otel_event_severity_is_elevated` bare-token `"ValidationWarning"` search now matches the new prose comment added in the rework. Test passes on correct code (real token is present) but would also pass on broken code (comment-only). | `crates/sidequest-server/tests/integration/encounter_creation_gate_story_37_13_tests.rs:169` | **Non-blocking.** Flagged for follow-up story. Trivial one-line fix: tighten to `window.contains("WatcherEventType::ValidationWarning")`. Not merge-blocking because production code is correct and the fragility only manifests under a hypothetical future regression. |
| [MEDIUM] | [TEST] | `duplicate_confrontation_type_uses_lower_severity_event` checks for the marker but doesn't verify the duplicate path uses StateTransition (not ValidationWarning). A regression that bumped the duplicate path to ValidationWarning would pass this test. | `crates/sidequest-server/tests/integration/encounter_creation_gate_story_37_13_tests.rs:216` | **Non-blocking.** Flagged for follow-up. Could add negative assertion (`window` count of `ValidationWarning` occurrences == 1) to the same test. |

**Pattern observed:** [VERIFIED] — The rework correctly uses the `.filter()`+`if let Some(active)` pattern to encode the unresolved-encounter invariant structurally rather than via runtime fallback. Evidence: `dispatch/mod.rs:1774-1778` binds `active_unresolved` with the filter predicate, and the `if let Some(active)` arm directly reads `active.encounter_type` and `active.metric.name` without any `Option` unwrap. Compliant with Rust idioms AND Rule #1 (no undocumented defensive defaults).

**Pattern observed:** [VERIFIED] — Duplicate-vs-conflict split at `dispatch/mod.rs:1785-1791 vs 1793-1805`. Evidence: StateTransition severity for idempotent re-emit (non-alerting, preserves GM panel signal-to-noise), ValidationWarning severity for genuine type-conflict (alerting). Consistent with sibling patterns in the same file (see `dispatch/mod.rs:1846` `encounter.player_beat_from_narrator_ignored`). Addresses the alert-fatigue HIGH from round 1.

**Data flow traced:** Narrator `ActionResult.confrontation: Some("combat")` → `dispatch_player_action` → `let active_unresolved = ctx.snapshot.encounter.as_ref().filter(|e| !e.resolved)` → three-way branch (blocked+split / create / missing-def) → appropriate OTEL + tracing emissions → current encounter state preserved. All paths explicit, all paths logged per their severity. ✓

**Error handling:** Missing ConfrontationDef (genre pack config error) is handled at `dispatch/mod.rs:1845` with `tracing::warn!`. No OTEL event on that path (pre-existing, preserved — not a story 37-13 concern). All other paths have appropriate emissions.

**Security analysis:** N/A — no trust boundaries, no user input parsing, no auth, no tenant isolation in this dispatch path.

**Wiring verified:** [VERIFIED] — `dispatch_player_action` is the production narrator-turn entry point and is called from the WebSocket handler. The new three-branch chain sits inline; no separate wiring hook required. Evidence: `encounter_context_wiring_story_28_4_tests` independently proves `dispatch_player_action` is reachable from production code paths.

**[VERIFIED] All round-1 findings addressed:**
- HIGH `.unwrap_or` masked invariant — RESOLVED (eliminated via restructure)
- HIGH alert fatigue on same-type re-emission — RESOLVED (duplicate/blocked split)
- MEDIUM duplicate test logic — RESOLVED (old test deleted, two new tests added)
- MEDIUM deferred comment without anchor — RESOLVED (removed)
- MEDIUM missing metric.name — RESOLVED (`active_metric_name` field added to both events)

**[VERIFIED] Dispatch tags represented:** [SILENT] pre-existing finding deferred, [TEST] 2 findings medium (non-blocking), [DOC] clean, [TYPE] pre-existing finding deferred, [SIMPLE] N/A (disabled), [SEC] N/A (disabled), [EDGE] N/A (disabled), [RULE] Rule #1/#14 resolved, Rule #4 downgraded, Rule #18 downgraded.

**Handoff:** To Camina Drummer (SM) for finish-story. PR creation and merge is SM's responsibility.

## Delivery Findings

- **Gap** (non-blocking): `sidequest-game::encounter::StructuredEncounter::from_confrontation_def` silently defaults unknown `MetricDirection` strings to `Ascending` via a `_ => MetricDirection::Ascending` wildcard arm. A genre pack with a misspelled direction (e.g. `"descendinig"`) creates an encounter with mechanically wrong resolution thresholds. Affects `crates/sidequest-game/src/encounter.rs:290` (change the wildcard to an explicit error + OTEL warn; return `Result<Self, String>` and have `dispatch/mod.rs` fall through to the existing `tracing::warn!` missing-def path). *Found by Reviewer during code review (round 2, silent-failure-hunter).*
- **Improvement** (non-blocking): `EncounterActor.role` is a raw `String` accepting `"player"` / `"npc"` magic literals. Define an `ActorRole` enum (Player, Npc) to make exhaustiveness compiler-enforced. Affects `crates/sidequest-game/src/encounter.rs:184` and all call sites. *Found by Reviewer during code review (round 2, type-design).*
- **Improvement** (non-blocking): `StructuredEncounter.encounter_type: String` comparison is case-sensitive. A narrator prompt casing typo (`"Combat"` vs `"combat"`) produces a false ValidationWarning conflict. Add an `EncounterTypeKey` newtype that normalizes on construction, OR normalize at the comparison site in `dispatch/mod.rs:1785`. Affects `crates/sidequest-game/src/encounter.rs:186` and `crates/sidequest-server/src/dispatch/mod.rs:1785`. *Found by Reviewer during code review (round 1, type-design).*
- **Improvement** (non-blocking): Tighten test assertion anchors in `encounter_creation_gate_story_37_13_tests.rs` — `otel_event_severity_is_elevated` should use `WatcherEventType::ValidationWarning` (enum-qualified) and `duplicate_confrontation_type_uses_lower_severity_event` should add a negative assertion on the duplicate path severity. Affects `crates/sidequest-server/tests/integration/encounter_creation_gate_story_37_13_tests.rs:169 and 216`. *Found by Reviewer during code review (round 2, test-analyzer).*

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Dev (rework round 1)
- No deviations from spec. All reviewer findings addressed per the severity table in Dev Assessment (rework round 2).

### TEA (verify)
- No deviations from spec.

### TEA (verify round 2)
- No deviations from spec. All reviewer findings addressed, simplify clean.

### Reviewer (audit round 2)
- **Dev rework round 1** → ✓ ACCEPTED: all 5 reviewer findings from round 1 addressed, no new deviations from spec.
- **TEA verify round 2** → ✓ ACCEPTED: simplify clean, all round-1 findings verified in-diff.

### Reviewer (audit)
- **TEA red phase deviations** → ✓ ACCEPTED by Reviewer: "No deviations" is accurate — tests match the AC list in the SM assessment.
- **Dev green phase deviations** → ✓ ACCEPTED by Reviewer: "No deviations" is accurate at the spec level — the loud-error semantics choice was explicitly sanctioned by SM as the default. The implementation-level issues (unwrap_or, metric.name, duplicate-type handling) are code quality, not spec deviations.
- **TEA verify phase deviations** → ✓ ACCEPTED by Reviewer: "No deviations" is accurate. The simplify triage decisions are documented and sound.
- **Undocumented: `.unwrap_or` fallback introduces defensive noise in a No-Silent-Fallbacks story** — TEA/Dev did not log this as a deviation. Spec source: CLAUDE.md "No Silent Fallbacks" + Rust lang-review Rule #1. Code does: uses `.unwrap_or((String::new(), 0))` with no rationale comment. Severity: HIGH. This should have been flagged during Dev green phase or TEA verify phase but was not — surfacing it as a reviewer finding instead.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->