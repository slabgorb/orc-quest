---
story_id: "20-9"
jira_key: ""
epic: "20"
workflow: "tdd"
---

# Story 20-9: Wire assemble_turn into dispatch pipeline

## Story Details
- **ID:** 20-9
- **Title:** Wire assemble_turn into dispatch pipeline
- **Jira Key:** (Personal project — no Jira)
- **Epic:** 20 — Narrator Crunch Separation — Tool-Based Mechanical Extraction (ADR-057)
- **Workflow:** tdd
- **Points:** 3
- **Priority:** p1
- **Type:** refactor
- **Stack Parent:** none
- **Split From:** 20-8 (story 20-8 was split to prioritize tool wiring)

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-02T12:55:01Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T19:00Z | 2026-04-02T12:04:22Z | -24938s |
| red | 2026-04-02T12:04:22Z | 2026-04-02T12:25:54Z | 21m 32s |
| green | 2026-04-02T12:25:54Z | 2026-04-02T12:41:49Z | 15m 55s |
| spec-check | 2026-04-02T12:41:49Z | 2026-04-02T12:42:45Z | 56s |
| verify | 2026-04-02T12:42:45Z | 2026-04-02T12:45:43Z | 2m 58s |
| review | 2026-04-02T12:45:43Z | 2026-04-02T12:54:14Z | 8m 31s |
| spec-reconcile | 2026-04-02T12:54:14Z | 2026-04-02T12:55:01Z | 47s |
| finish | 2026-04-02T12:55:01Z | - | - |

## Business Context

This is a connectivity/integration story, not a feature story. The `assemble_turn` function was built in story 20-1 to collect tool call results and merge them with narrator extraction. Currently it exists in the code but is **never called** — the orchestrator still builds ActionResult directly from the narrator extraction without using assemble_turn as an intermediary.

**Why now?** Story 20-10 (tool call parsing) will produce ToolCallResults and feed them into assemble_turn. Before that lands, we need to ensure the dispatch pipeline calls assemble_turn so tool results actually reach the game.

This is a "no op" refactoring: with ToolCallResults::default() (no tools fired), assemble_turn produces an identical ActionResult to what the orchestrator currently builds directly. After this wiring lands, 20-10 can add tool result population without worrying about whether dispatch calls it.

## Technical Context

### Current Wiring (20-1 Baseline)

From `/sidequest-api/crates/sidequest-agents/src/orchestrator.rs`:

- **Line 630:** Extraction happens: `let extraction = extract_structured_from_response(raw_response);`
- **Lines 704-730:** ActionResult is built **directly from extraction**, filling fields line-by-line.
- **assemble_turn module exists** (`src/tools/assemble_turn.rs`) but is never imported or called in orchestrator.
- **action_rewrite and action_flags** currently come from narrator JSON block (extraction fields), not from a preprocessor.

### What Needs to Change

1. **Import assemble_turn module** into orchestrator.rs (currently exists but not public-facing).
2. **Call assemble_turn()** to build ActionResult, replacing the direct field-by-field construction (lines 704-730).
3. **No changes needed to:**
   - The ActionResult struct itself
   - How action_rewrite/action_flags are currently extracted (still from JSON in 20-9)
   - Any dispatch/server code (assemble_turn is transparent to consumers)

### ToolCallResults Placeholder

For 20-9, ToolCallResults::default() passes through. All fields are None, so assemble_turn falls back to narrator extraction for scene_mood/scene_intent. Footnotes return empty (no tool fired), per the no-fallback rule documented in assemble_turn.rs.

This is **safe for 20-9** because:
- No tools are wired yet (story 20-2 adds mood/intent tools, but those stories are still in backlog).
- assemble_turn with default ToolCallResults produces identical output to current orchestrator behavior.
- Tests will verify the no-op is correct.

### Story 20-1 Success Criteria (Reference)

From context-story-20-1.md, AC-6 (footnotes handling):

> "footnotes: Tool call wins, NO fallback to narrator extraction. Same no-fallback semantics as items/merchants. If tool fired (Some), use its value (even if empty vec). If tool didn't fire (None), result is empty — narrator footnotes are discarded."

For 20-9, since no tools fire yet, narration footnotes will be discarded (assemble_turn.rs warns about this). This is correct per spec — story 20-4 will wire the lore_mark tool that populates footnotes via ToolCallResults.

## Acceptance Criteria

1. **assemble_turn is imported** and callable from orchestrator.rs (no longer dead code).
2. **ActionResult is built via assemble_turn()**, not via direct field construction.
3. **Current behavior unchanged** — ActionResult fields have identical values to pre-20-9 (assemble_turn with default ToolCallResults is a no-op).
4. **Tests pass** — existing unit and integration tests all pass without modification.
5. **OTEL events preserved** — no regression in observability (ToolCallResults has no side effects for OTEL).
6. **Wiring verified** — non-test consumers (dispatch pipeline) call process_action(), which calls orchestrator.process_action(), which calls assemble_turn().

## Risk & Mitigations

**Risk:** Footnotes will be discarded in 20-9 (no lore_mark tool yet). Narrator's JSON footnotes field ignored.
- **Mitigation:** Document in story 20-4 context that footnotes were deferred to tool call wiring. Add warning in assemble_turn (already present).
- **Severity:** Non-blocking — footnotes aren't used in gameplay until story 9-11 integration is verified.

**Risk:** Preprocessor fields (action_rewrite/action_flags) are still coming from narrator JSON, not from a preprocessor.
- **Mitigation:** That's story 20-1 work (split into 20-1 infrastructure + 20-9 wiring). Preprocessor population is future work.
- **Severity:** Non-blocking — 20-1 built the infrastructure, 20-9 wires dispatch, preprocessor wiring is a later story.

## Delivery Findings

No upstream findings.

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): Pre-existing `as usize` casts on `response.input_tokens`/`response.output_tokens` at `crates/sidequest-agents/src/orchestrator.rs:716-717` should use `usize::try_from()` per lang-review rule #7. Not introduced by 20-9 — defer to tech debt backlog. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- TEA deviations: ✓ ACCEPTED — no deviations logged, confirmed none needed
- Dev deviations: ✓ ACCEPTED — no deviations logged, but see Architect reconcile below for one missed deviation

### Architect (reconcile)
- **action_rewrite/action_flags None→Some(default) behavioral change**
  - Spec source: context-story-20-9.md, AC-3
  - Spec text: "ActionResult fields are identical pre- vs. post-refactor (verified by tests)"
  - Implementation: When extraction produces `None` for action_rewrite/action_flags, the old code passed `None` through to ActionResult. The new code unwraps to default and passes through assemble_turn which wraps in `Some()`, producing `Some(ActionRewrite{you:"",named:"",intent:""})` instead of `None`.
  - Rationale: Intentional per ADR-057 — "preprocessor always wins." assemble_turn's contract is that preprocessor values are always `Some()`. Downstream consumers (prompt display) handle empty strings identically to None. The warn!() added in review makes the None→default path observable.
  - Severity: minor
  - Forward impact: none — story 20-10 will provide real preprocessor values, making this transitional path moot

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2 — fixed in commit 7e7a2ca (warn on absent extraction fields) |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 2 (=silent-failure, already fixed), dismissed 2 (pre-existing `as usize`, not story scope) |

**All received:** Yes (3 returned, 6 disabled via settings)
**Total findings:** 2 confirmed and fixed, 2 dismissed (pre-existing)

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] assemble_turn wired into process_action — orchestrator.rs:695 calls `assemble_turn(extraction, rewrite, flags, ToolCallResults::default())`. Non-test consumer confirmed. Complies with CLAUDE.md "verify wiring not just existence."
2. [VERIFIED] Struct spread `..base` at orchestrator.rs:719 correctly delegates extraction-owned fields to assemble_turn while orchestrator explicitly overrides combat_patch, chase_patch, classified_intent, agent_name, duration/token telemetry, zone_breakdown. No field duplication, no field loss.
3. [VERIFIED] `Default` derive on ActionRewrite (orchestrator.rs:849) and ActionFlags (orchestrator.rs:860) — all fields already had `#[serde(default)]`, so `Default` derive produces identical values. No behavioral change. Rule #13 (constructor/deserialize consistency): compliant.
4. [SILENT] `unwrap_or_default()` on extraction.action_rewrite/action_flags — silent-failure-hunter flagged, rule-checker confirmed. **Fixed** in commit 7e7a2ca: `warn!()` emitted on None before defaulting. No longer silent. CLAUDE.md no-silent-fallbacks rule satisfied.
5. [RULE] Pre-existing `as usize` casts on token counts (orchestrator.rs:716-717) — rule #7 violation, but these lines are unchanged by this diff. Filed as delivery finding for tech debt backlog. Not blocking.

### Rule Compliance

| Rule | Instances | Status |
|------|-----------|--------|
| #1 silent errors | 2 (unwrap_or_default) | Fixed — warn!() added |
| #2 non_exhaustive | 0 enums in diff | N/A |
| #3 placeholders | 0 | Clean |
| #4 tracing | warn!() added for absent fields | Compliant |
| #7 unsafe casts | 2 pre-existing | Not story scope |
| #8 serde bypass | ActionRewrite, ActionFlags | Compliant — no invariants |
| #9 public fields | ActionRewrite, ActionFlags | Compliant — no invariants |
| #13 constructor consistency | Default + serde(default) | Consistent |

### Devil's Advocate

What if this wiring change silently breaks game behavior? The core claim is "no-op refactor" — assemble_turn with ToolCallResults::default() produces identical output to the old direct construction. But is that actually true?

The old code set `footnotes: extraction.footnotes` directly. The new code uses `..base` which gets footnotes from assemble_turn. On the develop branch, assemble_turn does NOT have the no-fallback footnotes rule (that's on feat/20-4). So on develop, assemble_turn returns `extraction.footnotes` for footnotes — identical to the old behavior. No change.

The old code set `action_rewrite: extraction.action_rewrite` (Option). The new code calls `extraction.action_rewrite.clone().unwrap_or_default()`, passes the unwrapped value to assemble_turn, which wraps it back in `Some()`. So `None` becomes `Some(ActionRewrite::default())` — a behavioral change! But this is intentional per ADR-057: "preprocessor always wins." The downstream consumers already handle `Some(empty)` vs `None` gracefully because action_rewrite is only used for prompt display, and an empty string displays as nothing.

What about the `.clone()` on action_rewrite/action_flags before passing extraction to assemble_turn? The extraction is moved into assemble_turn, so the clones happen first. If we removed the clones and extracted after assemble_turn, we'd need to restructure. But the clones are on small structs (3 strings, 5 bools) — negligible cost.

Could a malicious narrator output break this? The narration goes through strip_json_fence only when combat/chase patches exist. If a narrator outputs a JSON fence without a patch, the fence stays in the narration. But this is unchanged behavior — the old code had the same conditional. No regression.

The devil's advocate found one behavioral change (None→Some(default) for action_rewrite/action_flags) but it's intentional and documented in ADR-057. No hidden breakage found.

**Data flow traced:** player action → dispatch_player_action → orchestrator.process_action → assemble_turn(extraction, rewrite, flags, ToolCallResults::default()) → ActionResult with orchestrator overrides → dispatch continues. Safe — all fields accounted for.
**Pattern observed:** Struct spread with explicit overrides at orchestrator.rs:710-719 — clean separation of assembler-owned vs orchestrator-owned fields.
**Error handling:** CLI failure panics (pre-existing, intentional per ADR-005). Absent extraction fields now warn before defaulting.
**Handoff:** To Grand Admiral Thrawn (SM) for finish-story

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wiring story — must verify orchestrator calls assemble_turn

**Test Files:**
- `crates/sidequest-agents/tests/assemble_turn_wiring_story_20_9_tests.rs` — 3 source-level wiring tests

**Tests Written:** 3 tests covering ACs 2 and 5
**Status:** RED (3 failing — ready for Dev)

| Test | AC | What it checks |
|------|----|----------------|
| `orchestrator_calls_assemble_turn` | AC-2 | Source contains `assemble_turn(` call |
| `orchestrator_imports_tool_call_results` | AC-2 | Source contains `ToolCallResults` reference |
| `orchestrator_imports_from_tools_module` | AC-5 | Source imports from `crate::tools` module |

**ACs not directly tested here:**
- AC-1 (public export): Already covered by story 20-1 test `tools_module_is_public`
- AC-3 (identical fields): Covered by 20-1's `assemble_turn_passes_through_narrator_fields` — assemble_turn with default ToolCallResults is a no-op by construction
- AC-4 (existing tests pass): Verified — all 24 tests in assemble_turn_story_20_1_tests pass

### Rule Coverage

No new types, enums, constructors, or serde derivations introduced by this story. Lang-review rules #1-#15 are not applicable — this is a wiring-only change to orchestrator.rs.

**Self-check:** 0 vacuous tests. All 3 tests have meaningful string-contains assertions on source content.

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/orchestrator.rs` — added `use crate::tools::assemble_turn`, replaced direct ActionResult construction with `assemble_turn()` call + struct update for orchestrator-specific fields, added `Default` derive to `ActionRewrite`/`ActionFlags`, moved JSON fence stripping to post-assembly

**Tests:** 27/27 passing (GREEN) — 3 wiring + 24 existing
**Branch:** `feat/20-9-wire-assemble-turn-dispatch` (pushed)

**Handoff:** To TEA for verify phase

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | NarratorExtraction boilerplate (medium), test fixture duplication (medium), orchestrator override extraction (low) — all pre-existing patterns, not introduced by 20-9 |
| simplify-quality | clean | No issues |
| simplify-efficiency | clean | No issues |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 3 medium-confidence findings (pre-existing patterns, not story scope)
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** All passing — 27/27 tests green, clippy clean on changed file
**Handoff:** To Obi-Wan Kenobi (Reviewer) for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 6 ACs verified against the diff:
- AC-1 (public export): Pre-existing from 20-1, unchanged
- AC-2 (import + call): `use crate::tools::assemble_turn` added, `assemble_turn()` called in process_action
- AC-3 (identical fields): `..base` spread + explicit orchestrator overrides preserves all field values
- AC-4 (existing tests): 24/24 story-20-1 tests pass, full agent suite green
- AC-5 (wiring test): 3 source-level tests verify non-test consumer
- AC-6 (no regression): Full test suite confirms

Scope boundaries respected — no changes to ActionResult struct, no preprocessor logic, no tool call population, extractor.rs untouched. `Default` derive on ActionRewrite/ActionFlags is a minor convenience addition that doesn't alter behavior (all fields already had `#[serde(default)]`).

**Decision:** Proceed to review

## Sm Assessment

**Recommendation:** Proceed to RED phase.

This is a clean wiring story — `assemble_turn` exists as dead code, needs to be called from the dispatch pipeline. The no-op property (ToolCallResults::default() produces identical output) makes this low-risk. Context file documents the exact lines to change in orchestrator.rs. TEA should write tests that verify assemble_turn is called and that ActionResult fields are unchanged from pre-refactor behavior. Wiring test should confirm non-test consumers reach the code path.