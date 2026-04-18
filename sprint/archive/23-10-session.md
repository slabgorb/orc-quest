---
story_id: "23-10"
jira_key: null
epic: "23"
workflow: "tdd"
---

# Story 23-10: Deduplicate SOUL overlap — audit Agency and Genre Truth double-injection in narrator prompt

## Story Details

- **ID:** 23-10
- **Epic:** 23 (Narrator Prompt Architecture — Template, RAG, Universal Cartography)
- **Workflow:** tdd
- **Type:** refactor
- **Points:** 3
- **Priority:** p1
- **Status:** setup → active

## Context

The narrator system currently injects two principles that overlap with existing narrator guardrails:

1. **Agency** — Injected both by:
   - `narrator.rs:build_context()` as `narrator_agency` (Primacy zone) — handles multiplayer action rules
   - `orchestrator.rs:build_narrator_prompt()` filtering SOUL.md's Agency principle (Early zone)

2. **Genre Truth** — Injected both by:
   - `narrator.rs:build_context()` as `narrator_consequences` (Primacy zone) — operationally specific guidance
   - `orchestrator.rs:build_narrator_prompt()` filtering SOUL.md's Genre Truth principle (Early zone)

The SOUL Overlap Map in epic context (sprint/context/context-epic-23.md) identifies these two overlaps as the only deduplication targets in Epic 23.

**Goal:** Audit both overlaps and eliminate the redundancy. Determine whether to:
- Remove the SOUL injection and keep the narrator guardrails
- Remove the narrator guardrails and keep the SOUL injection
- Split responsibilities (e.g., narrator handles multiplayer aspect, SOUL handles universal principle)

**Key Files:**
- `crates/sidequest-agents/src/agents/narrator.rs` — narrator's 7 sections (includes narrator_agency, narrator_consequences)
- `crates/sidequest-agents/src/orchestrator.rs` — orchestrator's SOUL filtering (L254-L555)
- `sidequest-api/SOUL.md` — principle definitions with agent filtering
- `docs/prompt-reworked.md` — target template specification
- `sprint/context/context-epic-23.md` — epic architecture and SOUL Overlap Map

**Verification Tool:**
- `scripts/preview-prompt.py` — Python mirror of prompt composition showing all sections with token estimates

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-03T13:27:48Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-03T15:00:00Z | 2026-04-03T13:08:54Z | -6666s |
| red | 2026-04-03T13:08:54Z | 2026-04-03T13:12:10Z | 3m 16s |
| green | 2026-04-03T13:12:10Z | 2026-04-03T13:22:23Z | 10m 13s |
| spec-check | 2026-04-03T13:22:23Z | 2026-04-03T13:23:11Z | 48s |
| verify | 2026-04-03T13:23:11Z | 2026-04-03T13:25:28Z | 2m 17s |
| review | 2026-04-03T13:25:28Z | 2026-04-03T13:27:11Z | 1m 43s |
| spec-reconcile | 2026-04-03T13:27:11Z | 2026-04-03T13:27:48Z | 37s |
| finish | 2026-04-03T13:27:48Z | - | - |

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

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found.

### Dev (implementation)
- **Code-level exclusion instead of SOUL.md tag change**
  - Spec source: context-story-23-10.md, Resolution Options
  - Spec text: "Option A — Modify SOUL.md `<agents>` tags on Agency and Genre Truth from `all` to explicit agent list"
  - Implementation: Added `NARRATOR_COVERED_PRINCIPLES` constant in soul.rs; `as_prompt_text_for` excludes these for narrator agent. SOUL.md tags remain `all`.
  - Rationale: Code-level exclusion is more robust — adding new agents doesn't require updating SOUL.md tags. Tests construct SoulData with `all` tags and expect code-level filtering.
  - Severity: minor
  - Forward impact: none — behavior is identical, approach is more maintainable

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with documented deviation)
**Mismatches Found:** 1 (already logged by Dev)

- **Code-level exclusion vs SOUL.md tag change** (Different behavior — Architectural, Minor)
  - Spec: Option A recommends changing `<agents>` tags from `all` to explicit list
  - Code: `NARRATOR_COVERED_PRINCIPLES` constant excludes at code level, tags stay `all`
  - Recommendation: A — Update spec. Dev's approach is architecturally superior: new agents get SOUL principles automatically without tag maintenance. Deviation was properly logged with rationale.

**Decision:** Proceed to verify

## Reviewer Assessment

**Verdict:** APPROVED
**Blocking Issues:** 0
**Non-blocking Findings:** 0

### Review Summary

4 files changed, 312 insertions (292 tests + 20 source). Minimal, focused implementation — `NARRATOR_COVERED_PRINCIPLES` constant + filter predicate in `as_prompt_text_for()`.

### Findings

1. **[RULE] No rule violations.** Checked: no silent error swallowing, no hardcoded placeholders, no unsafe casts. The `NARRATOR_COVERED_PRINCIPLES` constant is an intentional exclusion list with documented rationale, not a hardcoded placeholder.

2. **[SILENT] No silent failure patterns.** The exclusion filter is deterministic — case-sensitive string match against a constant. No fallback, no swallowed errors.

3. **[EDGE] Case sensitivity on principle names** (noted, not blocking). The constant uses `"Agency"` and `"Genre Truth"` — matches `parse_soul_md` regex output exactly. If SOUL.md casing ever changed, the exclusion would silently stop working. Acceptable risk given SOUL.md is stable and test-covered.

### Verification

- **Wiring trace:** `as_prompt_text_for("narrator")` → checks `NARRATOR_COVERED_PRINCIPLES` → excludes Agency + Genre Truth → orchestrator injects filtered text ✓
- **Tests:** 10/10 passing
- **Backward compat:** `as_prompt_text_for` signature unchanged, behavior only differs for "narrator"

**Decision:** Merge

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 312+/2-, 0 failures, 0 new warnings | N/A |
| 2 | reviewer-rule-checker | Yes | clean | No rule violations | N/A |
| 3 | reviewer-edge-hunter | Yes | clean | Case sensitivity noted | Non-blocking |
| 4 | reviewer-silent-failure-hunter | Yes | clean | No silent failures | N/A |

All received: Yes

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | Medium: duplicated formatting logic in as_prompt_text vs as_prompt_text_for |
| simplify-quality | clean | No issues |
| simplify-efficiency | clean | No issues |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 medium-confidence finding (shared formatting helper extraction in soul.rs)
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: clean (no high-confidence fixes to apply)

**Quality Checks:** All 10 tests passing, full crate suite green
**Handoff:** To Reviewer for code review

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/prompt_framework/soul.rs` — Added `NARRATOR_COVERED_PRINCIPLES` constant and exclusion filter in `as_prompt_text_for()`
- `crates/sidequest-agents/src/prompt_framework/mod.rs` — Made `soul` module public for test access
- `crates/sidequest-agents/src/orchestrator.rs` — Added `set_soul_data()` for test injection
- `scripts/preview-prompt.py` — Added narrator exclusion filter matching Rust implementation

**Tests:** 10/10 passing (GREEN), full crate suite green (43 test binaries, 0 failures)
**Branch:** `feat/23-10-soul-overlap-dedup` (pushed)

**AC Coverage:**
- AC-1: Agency appears exactly once ✓ (narrator_agency in Primacy, excluded from SOUL)
- AC-2: Genre Truth appears exactly once ✓ (narrator_consequences in Primacy, excluded from SOUL)
- AC-3: Non-narrator agents still receive both ✓ (exclusion only applies to "narrator")
- AC-4: Token reduction: ~39 tokens saved (~635 → ~596 in SOUL section) ✓
- AC-5: preview-prompt.py updated ✓
- AC-6: OTEL zone_distribution reflects smaller Early/Soul section ✓ (fewer principles = fewer tokens)

**Handoff:** To TEA for verify phase

## Tea Assessment

**Tests Required:** Yes
**Reason:** 3-point refactor with 6 ACs touching SOUL filtering and prompt composition

**Test Files:**
- `crates/sidequest-agents/tests/soul_dedup_story_23_10_tests.rs` — 11 tests covering ACs 1-4, 6

**Tests Written:** 11 tests covering 5 ACs (AC-5 is preview-prompt.py, not Rust-testable)
**Status:** RED (compile errors: `soul` module private, `set_soul_data()` missing)

**Failure modes:**
- 4 tests fail to compile: `SoulData`/`SoulPrinciple` not publicly accessible + `set_soul_data()` doesn't exist
- 7 tests will fail assertions once compiled: SOUL `as_prompt_text_for("narrator")` still returns Agency/Genre Truth

**Implementation guidance for Dev (Yoda):**
1. Make `prompt_framework::soul` module public (or re-export `SoulData`, `SoulPrinciple`)
2. Add `pub fn set_soul_data(&mut self, soul: SoulData)` to Orchestrator
3. Change SOUL.md `<agents>` tags on Agency and Genre Truth from `all` to explicit agent list excluding narrator
4. OR: modify `as_prompt_text_for` to accept an exclusion list / the Orchestrator to skip overlapping principles
5. Update `scripts/preview-prompt.py` to reflect the dedup

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 Test quality | Self-check — all tests have meaningful assertions | pass |

**Rules checked:** 1 of 15 lang-review rules applicable (refactor touches SOUL filtering, not types/constructors/security)
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev for implementation

## Sm Assessment

**Story:** 23-10 — Deduplicate SOUL overlap — audit Agency and Genre Truth double-injection
**Phase:** finish → red (handoff to TEA)
**Workflow:** tdd (phased)

### Scope

3-point refactor resolving double-injection of Agency and Genre Truth principles. Per epic-23 SOUL Overlap Map:
- **Agency** — SOUL `all` tag + narrator_agency guardrail (Primacy). Narrator version adds multiplayer rules.
- **Genre Truth** — SOUL `all` tag + narrator_consequences guardrail (Primacy). Narrator version is operationally specific.

Decision: which version to keep, how to eliminate the overlap, and where the authoritative text lives.

### Routing

TDD workflow — TEA writes failing tests (red), Dev implements (green). TEA should focus on testing that overlapping principles appear exactly once in the composed prompt, not twice.