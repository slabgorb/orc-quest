---
story_id: "20-13"
jira_key: ""
epic: "20"
workflow: "tdd"
---

# Story 20-13: lore_mark sidecar tool — narrator calls tool to emit footnotes, sidecar parser collects into lore_established

## Story Details
- **ID:** 20-13
- **Title:** lore_mark sidecar tool — narrator calls tool to emit footnotes, sidecar parser collects into lore_established
- **Jira Key:** (Personal project — no Jira)
- **Epic:** 20 — Narrator Crunch Separation — Tool-Based Mechanical Extraction (ADR-057)
- **Workflow:** tdd
- **Points:** 3
- **Priority:** p1
- **Repos:** sidequest-api
- **Stack Parent:** 20-11 (item_acquire sidecar tool)

## Context & Problem

After story 20-8 (delete extractor.rs), the lore_mark mechanical extraction is completely broken:

1. **lore_established always None** — NarratorExtraction returns None, no lore facts flow through
2. **Footnote markers in prose ([1]) have no mechanical backing** — narrator uses footnote syntax but no extraction occurs
3. **Tool definition exists** (20-4) but never wired into the sidecar tool call pipeline
4. **Narrator narrates without effect** — lore facts mentioned in prose don't persist to player knowledge; repeated playthroughs contradict earlier facts

This story completes the Epic 20 migration — all mechanical extraction flows through sidecar tools, zero narrator JSON.

Generation pattern: **Call tool to establish fact, narrate around fact** (like item_acquire and merchant_transact).

This story depends on 20-11 (item_acquire) which established the sidecar tool pattern for mechanical changes during narration.

## Acceptance Criteria

- [ ] **AC1:** lore_mark tool call is fully wired in the sidecar tool call pipeline
  - Tool definition is recognized by narrator prompt
  - Tool output is captured in ToolCallResults
  - Parser validates tool calls and extracts LoreMarkCall structs

- [ ] **AC2:** Parser validates lore facts and confidence levels
  - Category field is recognized (world, npc, faction, location, quest, custom)
  - Confidence level is validated (high, medium, low)
  - Text field is non-empty and sanitized
  - Invalid lore marks fail gracefully (error logged, no silent fallbacks)

- [ ] **AC3:** assemble_turn feeds lore_mark results into lore_established
  - lore_established vector populates from tool calls
  - State patching applies lore changes correctly
  - Lore facts persist across turns and sessions
  - OTEL spans log lore establishments (category, confidence, text origin)

- [ ] **AC4:** Tests verify full pipeline
  - Unit: parser validates category, confidence, text fields
  - Integration: tool call → parser → assemble_turn → ActionResult with lore_established
  - Wiring test: production code path exercises lore_mark (not test-only)

- [ ] **AC5:** No regressions in other tool pipelines (item_acquire, merchant_transact, scene_mood, etc.)
  - Epic 20 migration is complete — all mechanical extraction flows through sidecar tools

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-03T06:48:47Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-03T01:40Z | 2026-04-03T06:20:55Z | 4h 40m |
| red | 2026-04-03T06:20:55Z | 2026-04-03T06:24:33Z | 3m 38s |
| green | 2026-04-03T06:24:33Z | 2026-04-03T06:42:21Z | 17m 48s |
| verify | 2026-04-03T06:42:21Z | 2026-04-03T06:44:17Z | 1m 56s |
| review | 2026-04-03T06:44:17Z | 2026-04-03T06:48:47Z | 4m 30s |
| finish | 2026-04-03T06:48:47Z | - | - |

## Sm Assessment

**Story readiness:** READY. All prerequisites met:
- 20-11 (item_acquire) and 20-12 (merchant_transact) merged — sidecar tool pattern fully established
- lore_established field exists on NarratorExtraction (always None) and ActionResult
- This is the final story in Epic 20 — completes the narrator crunch separation

**Risk:** Low. Mechanical wiring following established pattern.

**Routing:** TDD phased → Han Solo (TEA) for red phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Final Epic 20 story wiring lore_mark into the sidecar tool pipeline

**Test Files:**
- `crates/sidequest-agents/tests/lore_mark_story_20_13_tests.rs` — 27 tests covering all 5 ACs

**Tests Written:** 27 tests covering 5 ACs
**Status:** RED (compilation failure — missing module, missing field)

### AC Coverage

| AC | Tests | Description |
|----|-------|-------------|
| AC1 — Tool wired in pipeline | 5 tests | Parser extracts lore, accumulates multiples, skips invalid, coexists with other tools |
| AC2 — Parser validates details | 13 tests | All 6 categories, 3 confidence levels, empty/invalid rejected, whitespace trimming, case normalization, to_lore_text conversion |
| AC3 — assemble_turn feeds results | 3 tests | Tool overrides extraction, fallback when no tool, override precedence |
| AC4 — Full pipeline tests | 5 tests | Sidecar→parse→assemble→ActionResult, wiring source verification |
| AC5 — No regressions | 2 tests | merchant_transact and item_acquire unaffected |

### Rule Coverage

No lang-review rules file. Tests enforce CLAUDE.md principles:
- No silent fallbacks: invalid lore marks rejected, not silently ignored
- Verify wiring: source verification tests check actual code paths
- Wiring test: compile-time module export + source string verification
- OTEL: structural check that parser handles lore_mark

**Self-check:** 0 vacuous tests. All 27 have meaningful assertions.

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/tools/lore_mark.rs` — NEW: validation module with `validate_lore_mark()`, `LoreMarkResult`, `InvalidLoreMark`
- `crates/sidequest-agents/src/tools/mod.rs` — Export `lore_mark` module
- `crates/sidequest-agents/src/tools/assemble_turn.rs` — Add `lore_established: Option<Vec<String>>` to `ToolCallResults`, update `assemble_turn()` to use it
- `crates/sidequest-agents/src/tools/tool_call_parser.rs` — Add `"lore_mark"` match arm, import `validate_lore_mark`

**Tests:** 924/924 passing (GREEN) — 28 new + 896 existing, 0 regressions
**Branch:** feat/20-13-lore-mark-sidecar (pushed)

**Handoff:** To next phase (verify)

## TEA Verify Assessment

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 5 findings | JSON extraction, validation templates, match arm structure — all pre-existing |
| simplify-quality | 5 findings | Unused import, personality_event unwrap, unvalidated play_sfx/resource_change — all pre-existing |
| simplify-efficiency | 1 finding | to_lore_text() thin wrapper — by design per test expectations |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings (all pre-existing)
**Noted:** 1 low-confidence observation (to_lore_text wrapper)
**Reverted:** 0

**Overall:** simplify: clean (new code follows established patterns)

**Quality Checks:** Tests GREEN (924/924), clippy clean on changed files
**Handoff:** To Obi-Wan Kenobi (Reviewer) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A |
| 2 | reviewer-edge-hunter | Yes | Skipped | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | dismissed 3 (all pre-existing patterns) |
| 4 | reviewer-test-analyzer | Yes | Skipped | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 | dismissed 2 (both pre-existing, not introduced by this diff) |

**All received:** Yes (3 returned results, 6 disabled via settings)
**Total findings:** 0 confirmed, 5 dismissed (with rationale), 0 deferred

### Dismissal Rationale

**[SILENT] #1 (file-open fallback, tool_call_parser.rs:62):** Pre-existing from 20-10. Already logged as delivery finding in 20-12 review.
**[SILENT] #2 (skipped_count not surfaced to OTEL, tool_call_parser.rs:195):** Pre-existing pattern across all tool arms. Medium confidence.
**[SILENT] #3 (missing-fields warn-only, tool_call_parser.rs:200):** Pre-existing pattern. Medium confidence.
**[RULE] #1 (assemble_turn no OTEL, assemble_turn.rs:66):** Pre-existing absence for all fields, not introduced by lore_mark. Valid improvement, logged as delivery finding.
**[RULE] #2 (file-open silent fallback, tool_call_parser.rs:55):** Same as [SILENT] #1.

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Private fields with getters — `LoreMarkResult` at `lore_mark.rs:21-25` has private `text`, `category`, `confidence` with pub getters at lines 28-40. Matches `ItemAcquireResult` and `MerchantTransactResult`. Complies with CLAUDE.md validated-type rule.

2. [VERIFIED] thiserror error type — `InvalidLoreMark` at `lore_mark.rs:52-53` uses `#[derive(thiserror::Error)]`.

3. [VERIFIED] OTEL instrumentation — `validate_lore_mark` at `lore_mark.rs:62-66` has `#[tracing::instrument]` with all 3 fields. `warn!` on every reject, `info!` on accept. Parser arm logs `info!`/`warn!` consistently.

4. [VERIFIED] No silent fallbacks in new code — Every validation failure returns `Err` at lines 77, 81, 85, 91, 95. Parser arm warns and skips invalid records — consistent with all other arms.

5. [VERIFIED] Wiring complete — Module exported (`mod.rs:12`), imported in parser (`tool_call_parser.rs:17`), match arm at line 176, field on `ToolCallResults` (line 53), consumed in `assemble_turn` (line 90), flows to `ActionResult.lore_established` (line 113). Non-test consumer chain: `orchestrator.rs` → `parse_tool_results()` → `assemble_turn()`.

6. [VERIFIED] `.or()` semantics correct — `lore_established` is `Option<Vec<String>>` on ActionResult, NarratorExtraction, and ToolCallResults. `.or()` preserves the Option wrapper. Other fields use `.unwrap_or()` because they're `Vec<T>` (not Option) on ActionResult. Type-correct dispatch.

7. [VERIFIED] Enum validation — `VALID_CATEGORIES` (6 values) and `VALID_CONFIDENCE` (3 values) defined as const slices. `.contains()` check with `.to_lowercase()` normalization. Complete and correct.

### Rule Compliance

| Rule | Instances Checked | Compliant |
|------|-------------------|-----------|
| No stubs | 4 | All compliant |
| No skipping tests | 1 (28 external tests) | Compliant |
| No half-wired | 5 (export, import, parser arm, field, assembler) | All compliant |
| No silent fallbacks | 3 (validator, parser arm, assembler) | Compliant in new code |
| Wire up what exists | 2 | Compliant |
| Verify wiring | 3 (all have non-test consumers) | All compliant |
| Wiring test | 5 wiring tests in external file | Compliant |
| OTEL | 3 (instrument, warn/info on both paths) | Compliant in new code |
| thiserror | 1 (InvalidLoreMark) | Compliant |
| Private fields + getters | 2 (LoreMarkResult, ToolCallResults) | Compliant |
| tracing::instrument | 1 (validate_lore_mark) | Compliant |

### Devil's Advocate

This is the third tool following the same pattern. The risk of cargo-culting is real — but the pattern is correct, and consistency across the tool pipeline is a feature, not a bug. Every tool validates the same way, wires the same way, and fails the same way. That means debugging one teaches you all.

The most interesting difference from merchant_transact: `lore_established` uses `.or()` instead of `.unwrap_or()` because it's `Option<Vec<String>>` all the way through (ActionResult, NarratorExtraction, ToolCallResults). The other fields that use `.unwrap_or()` unwrap from `Option<Vec<T>>` to `Vec<T>` because their ActionResult target is a plain Vec. This is correct type-driven dispatch — not inconsistency. A reviewer might flag it as "different from the others" but it's the right choice for the type.

What if a narrator floods lore_mark calls — 1000 lore facts in a single turn? The Vec grows unbounded. But this is sidecar JSONL — the file size is bounded by Claude CLI's output limits, and the sidecar is deleted after parsing. Practically, a turn produces 1-5 lore marks. Not a realistic concern.

What if category or confidence values change? The `VALID_CATEGORIES` and `VALID_CONFIDENCE` const slices are the single source of truth. Adding a new category requires one line in lore_mark.rs. No other file needs changing.

Could the `.or()` produce surprising behavior? If `tool_results.lore_established` is `Some(vec![])` (tool fired but produced empty lore), `.or()` returns `Some(vec![])` — the tool's answer wins, even though it's empty. This is correct: "the tool fired and found no lore" is different from "the tool didn't fire" (None). The test `assemble_turn_tool_results_override_extraction_lore_established` verifies this.

**Data flow traced:** Sidecar JSONL `{"tool":"lore_mark","result":{"text":"...","category":"world","confidence":"high"}}` → `parse_tool_results()` → deserialize `ToolCallRecord` → match `"lore_mark"` → extract 3 fields → `validate_lore_mark()` trims/lowercases/validates → `LoreMarkResult` → `.to_lore_text()` → pushed to `ToolCallResults.lore_established` → `assemble_turn()` `.or()` fallback → `ActionResult.lore_established` → dispatch pipeline → `accumulate_lore()`. Safe end-to-end.

**Pattern observed:** Validated-newtype with const enum validation at `lore_mark.rs:10-13,21`. Clean.

**Error handling:** Invalid inputs rejected at lines 77, 81, 85, 91, 95. No panics, no silent defaults.

[EDGE] No edge-hunter findings (disabled).
[SILENT] 3 findings, all dismissed as pre-existing.
[TEST] No test-analyzer findings (disabled).
[DOC] No comment-analyzer findings (disabled).
[TYPE] No type-design findings (disabled).
[SEC] No security findings (disabled).
[SIMPLE] No simplifier findings (disabled).
[RULE] 2 findings, both dismissed as pre-existing.

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story — Epic 20 complete.

## Delivery Findings

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- No upstream findings during test verification.

### Reviewer (code review)
- **Improvement** (non-blocking): `assemble_turn()` has no OTEL instrumentation — the tool-vs-extraction merge decision for all fields (lore_established, scene_mood, items_gained, etc.) is invisible to the GM panel. Affects `crates/sidequest-agents/src/tools/assemble_turn.rs` (add `#[tracing::instrument]` and merge-outcome logging). *Found by Reviewer during code review.*

## Design Deviations

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No undocumented deviations found.

### TEA (test design)
- **LoreMarkResult outputs plain string (not struct) for lore_established** → ✓ ACCEPTED by Reviewer: Correct — `lore_established` is `Option<Vec<String>>` throughout the codebase, so a plain string output is the right type match. The category and confidence serve as validation metadata and OTEL span data, not as stored fields.
  - Spec source: session file AC3, assemble_turn.rs
  - Spec text: "lore_established vector populates from tool calls"
  - Implementation: Tests expect `to_lore_text()` returns `String`, pushed into `Vec<String>` — simpler than merchant_transact which outputs a struct
  - Rationale: `lore_established` is `Option<Vec<String>>` throughout the codebase; no struct needed
  - Severity: minor
  - Forward impact: none — matches existing type