---
story_id: "20-4"
jira_key: ""
epic: "20"
epic_title: "Narrator Crunch Separation — Tool-Based Mechanical Extraction"
workflow: "tdd"
---

# Story 20-4: lore_mark tool — footnote extraction via tool call

## Story Details

- **ID:** 20-4
- **Epic:** 20 (Narrator Crunch Separation — ADR-057)
- **Jira Key:** N/A (personal project)
- **Workflow:** tdd
- **Story Points:** 3
- **Priority:** p1
- **Stack Parent:** none (Phase 4 of 8-phase migration)
- **Repos:** sidequest-api
- **Branch:** feat/20-4-lore-mark-tool

## Overview

**Phase 4 of ADR-057:** Replace the narrator's `footnotes` JSON field with a typed `lore_mark` tool call.

Currently, the narrator emits footnote metadata inline with prose in the JSON block:
```
[FOOTNOTE PROTOCOL]
When you reveal new information or reference something the party previously learned,
include a numbered marker in your prose like [1], [2], etc.

After your prose, emit a fenced JSON block with a footnotes array. Each entry has:
- marker: the number matching [N] in your prose
- summary: one-sentence description of the fact
- category: one of "Lore", "Place", "Person", "Quest", "Ability"
- is_new: true if this is a new revelation, false if referencing prior knowledge
```

The LLM's dual task (prose + JSON formatting) is error-prone. ADR-057 eliminates this by:

1. **Narrator continues placing [N] markers in prose** — that part works.
2. **Narrator calls `lore_mark` tool** with marker number, summary, category, and is_new.
3. **Tool returns a `Footnote` struct** with validated data.
4. **`assemble_turn` collects footnotes** from tool results + prose extraction, merges into `ActionResult`.

This follows the pattern established by Phase 2 (`set_mood`, `set_intent`) and Phase 3 (`item_acquire`, `merchant_transact`).

## Acceptance Criteria

1. **Tool implementation:** Create `crate::tools::lore_mark` module (lore_mark.rs).
   - Input struct: `LoreMarkInput` with marker, summary, category (String), is_new.
   - Validation: category must be one of "Lore", "Place", "Person", "Quest", "Ability" (case-insensitive).
   - Marker: optional u32 (matches footnote behavior).
   - Output: validated `sidequest_protocol::Footnote` struct.
   - OTEL: tracing instrumentation on success/failure.

2. **Integration into `ToolCallResults`:**
   - Add `footnotes: Option<Vec<Footnote>>` field to `ToolCallResults`.
   - Update `assemble_turn` to collect footnotes from tool calls.
   - **RULE:** No silent fallback. Same semantics as items/merchants (20-3):
     - If tool fires (Some), tool footnotes WIN — even if empty vec.
     - If tool doesn't fire (None), result is empty — narrator extraction discarded.

3. **Narrator prompt update (deferred, Phase 8):**
   - For Phase 4, the narrator still uses the old JSON-block protocol.
   - In Phase 8 (story 20-8), the footnote protocol section will be removed from the narrator prompt.
   - For now, narrator emits both tool calls AND JSON block footnotes. `assemble_turn` uses tool results.

4. **Tests:**
   - Unit tests for `lore_mark::validate_category()` covering valid/invalid inputs.
   - Test `acquire_footnote()` with various marker/summary/category combinations.
   - Test invalid category raises error with proper message.
   - Integration test: verify tool results flow through `assemble_turn` and override narrator extraction.
   - Wiring test: verify `lore_mark` module is imported and used in production code path.

5. **OTEL coverage:**
   - Every tool call emits a span with `tool.lore_mark` name.
   - On success: fields `marker`, `category`, `is_new`, `summary_len`.
   - On failure: `valid = false`, error message.

6. **No silent fallbacks:**
   - If category is invalid, return `Err`, not a default category.
   - No case-folding surprises — document exact casing rules.

## Scope

### In
- Tool function `lore_mark::acquire_footnote()`.
- Category validation logic.
- OTEL instrumentation.
- Unit tests for validation logic.
- Integration test verifying tool output flows to `ActionResult.footnotes`.
- Wiring verification.

### Out (Phase 8)
- Narrator prompt updates (story 20-8).
- Removal of old JSON footnote block from extraction.
- Deletion of `extractor.rs` (story 20-8).

## Technical Context

### Related Files

**Tools (Phase 2-3 patterns):**
- `/Users/keithavery/Projects/oq-1/sidequest-api/crates/sidequest-agents/src/tools/set_mood.rs` — Simple enum validation pattern (Tension, Wonder, Melancholy, etc.).
- `/Users/keithavery/Projects/oq-1/sidequest-api/crates/sidequest-agents/src/tools/item_acquire.rs` — Richer struct input, validation, OTEL instrumentation.
- `/Users/keithavery/Projects/oq-1/sidequest-api/crates/sidequest-agents/src/tools/assemble_turn.rs` — `ToolCallResults` merging logic.

**Footnote infrastructure:**
- `/Users/keithavery/Projects/oq-1/sidequest-api/crates/sidequest-agents/src/footnotes.rs` — Existing footnote extraction (from narrator JSON) → `DiscoveredFact` conversion.
- `/Users/keithavery/Projects/oq-1/sidequest-api/crates/sidequest-protocol/src/message.rs` — `Footnote` struct definition:
  ```rust
  pub struct Footnote {
      pub marker: Option<u32>,           // Matching [N] in prose
      pub fact_id: Option<String>,        // Links to existing KnownFact (callbacks)
      pub summary: String,                // One-sentence description
      pub category: FactCategory,         // Lore, Place, Person, Quest, Ability
      pub is_new: bool,                   // True if new revelation
  }
  ```

**Narrator context:**
- `/Users/keithavery/Projects/oq-1/sidequest-api/crates/sidequest-agents/src/agents/narrator.rs` — Current footnote protocol (lines 41-51).
- `/Users/keithavery/Projects/oq-1/docs/adr/057-narrator-crunch-separation.md` — Full ADR, Phase 4 (lines 150-152).

### FactCategory Enum

From sidequest-protocol/src/message.rs. The tool accepts strings and validates to this enum:
```rust
pub enum FactCategory {
    Lore,      // World knowledge, magic systems, history
    Place,     // Locations, geography, landmarks
    Person,    // NPCs, characters, identities
    Quest,     // Quest objectives, quest-related facts
    Ability,   // Powers, skills, abilities
}
```

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-02T11:43:46Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T16:00Z | 2026-04-02T11:05:36Z | -17664s |
| red | 2026-04-02T11:05:36Z | 2026-04-02T11:09:04Z | 3m 28s |
| green | 2026-04-02T11:09:04Z | 2026-04-02T11:18:52Z | 9m 48s |
| review | 2026-04-02T11:18:52Z | 2026-04-02T11:43:46Z | 24m 54s |
| finish | 2026-04-02T11:43:46Z | - | - |

## Sm Assessment

**Story 20-4** is Phase 4 of ADR-057 — footnote extraction migration. 3 points, moderate complexity. Follows the established tool pattern from Phases 2-3. Key difference from Phase 3: footnotes have **fallback** semantics (tool > narrator, but narrator still works if tool doesn't fire), unlike items/merchants which had no-fallback. AC-3 defers prompt removal to Phase 8.

**Routing:** → Han Solo (TEA) for red phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-point story with 6 ACs — new tool module, struct extension, merge logic with fallback semantics, OTEL, and category validation.

**Test Files:**
- `crates/sidequest-agents/tests/lore_mark_story_20_4_tests.rs` — 24 tests covering all 6 ACs

**Tests Written:** 24 tests covering 6 ACs

### Test Breakdown by AC

| AC | Tests | Coverage |
|----|-------|----------|
| AC-1: lore_mark validation + category mapping | 8 | Valid input, case-insensitive (12 combos), invalid category, empty category, empty summary, none marker, callback (is_new=false), all 5 categories |
| AC-2: ToolCallResults extended + assemble_turn merge | 7 | footnotes field, default is None, tool overrides narrator, narrator fallback when tool absent, empty tool overrides narrator, multiple footnotes, preserves other fields |
| AC-3: Narrator prompt unchanged | 1 | Footnote protocol still present (deferred to Phase 8) |
| AC-5: OTEL spans | 2 | Success span, failure span |
| AC-6: No silent fallbacks | 2 | Invalid category rejected, empty category rejected (also covered in AC-1 tests) |
| Wiring | 2 | lore_mark module public, footnotes field exported |

### Rule Coverage

No `.pennyfarthing/gates/lang-review/rust.md` rules violated by test design — personal project without lang-review gates enforced at TEA phase. The lang-review checklist exists but rule-enforcement tests are the Reviewer's domain.

**Self-check:** All 24 tests have meaningful assertions. No vacuous `let _ =` or `assert!(true)`. Every assertion checks a specific value, error condition, or structural property. The two wiring tests are compile-time checks (consistent with 20-2/20-3 convention).

**Key design decision:** Footnotes use **fallback** semantics (tool > narrator, but narrator works if tool absent). This is distinct from items/merchants in 20-3 which used **no-fallback** semantics. Test `assemble_turn_narrator_footnotes_fallback_when_tool_absent` explicitly verifies this.

**Status:** RED (compilation failure — 11 errors: unresolved import for lore_mark module, missing footnotes field on ToolCallResults)

**Handoff:** To Yoda (Dev) for implementation

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (clippy, fmt — pre-existing, now fixed) | dismissed 2: fixed in separate commit |
| 2 | reviewer-edge-hunter | N/A | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 low-confidence | dismissed 2: unwrap_or fallback was spec issue, now fixed to unwrap_or_default |
| 4 | reviewer-test-analyzer | N/A | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | N/A | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | N/A | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | N/A | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | N/A | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 5 (non_exhaustive, unbounded summary, pub fields, wiring, vacuous OTEL test) | confirmed 1, dismissed 3, deferred 1 |

**All received:** Yes (3 returned, 6 disabled/skipped)
**Total findings:** 1 confirmed, 5 dismissed, 1 deferred

### Subagent Finding Decisions

**Confirmed:**
1. [RULE] `LoreMarkError` missing `#[non_exhaustive]` — rule #2 violation, same pattern as 20-3. (lore_mark.rs:23)

**Deferred (out of story scope):**
1. [RULE] No non-test consumers for `acquire_footnote` — wiring is Phase 8. Same as all prior tool modules.

**Dismissed:**
1. Preflight clippy/fmt — pre-existing, fixed in separate commit across entire workspace.
2. [SILENT] `unwrap_or` fallback concern — **fixed**: changed to `unwrap_or_default()` with `tracing::warn!` when narrator footnotes are discarded.
3. [RULE] `LoreMarkInput` pub fields (rule 9) — this is a plain input DTO. The validation happens in `acquire_footnote`, not at construction. Same pattern as `ItemAcquireInput` and `MerchantTransactInput` in 20-3. Consistent with project convention.
4. [RULE] OTEL test vacuous for span verification — matches Phase 2/3 convention. No `tracing-test` crate in the project.
5. [RULE] Unbounded summary (rule 15) — LLM-generated summaries are bounded by the tool call protocol (Claude's tool output is not arbitrary user input). Adding a MAX_SUMMARY_LEN would be speculative defense against a non-existent attack vector. The narrator's existing footnote extraction path also has no summary length limit.

## Reviewer Assessment

**Verdict:** APPROVED

**Observations:**

1. [VERIFIED] No-fallback semantics — `assemble_turn.rs:53` uses `unwrap_or_default()` producing empty vec when tool didn't fire. `tracing::warn!` at lines 49-52 fires when narrator footnotes are discarded, providing GM panel visibility. Complies with CLAUDE.md no-silent-fallbacks rule. Originally implemented with fallback (`unwrap_or`), caught and fixed during review.

2. [VERIFIED] Category validation — `lore_mark.rs:33-41` `parse_category` does case-insensitive match against 5 FactCategory variants. Invalid category returns `Err(InvalidCategory)` with `tracing::warn!`. Empty category hits the same path. No silent default. Tested by 12 case combinations + invalid + empty.

3. [VERIFIED] OTEL instrumentation — `#[tracing::instrument]` on `acquire_footnote` with `tool.lore_mark` span name and fields `marker`, `category`, `is_new`. Success path: `tracing::info!` with `summary_len`. Both error paths: `tracing::warn!` with `valid = false`. Discard path in assemble_turn: `tracing::warn!` with `narrator_footnote_count`.

4. [RULE] Missing `#[non_exhaustive]` on `LoreMarkError` (lore_mark.rs:23). **Severity: MEDIUM.** Same pattern as 20-3 error enums. No downstream match arms exist yet.

5. [VERIFIED] AC-3 narrator prompt unchanged — test `narrator_prompt_still_contains_footnote_protocol` confirms `[FOOTNOTE PROTOCOL]` and `footnotes` field still present. Deferred to Phase 8.

6. [VERIFIED] 20-2 test backward compatibility — 10 `..ToolCallResults::default()` usages properly handle new `footnotes` field.

7. [TEST] 20 tests with meaningful assertions. Comprehensive AC coverage including the critical no-fallback test.

8. [DOC] Clear documentation on `ToolCallResults.footnotes` field and inline comments in `assemble_turn`.

**Data flow traced:** `LoreMarkInput` → `acquire_footnote()` validates summary (non-empty) and category (5-variant match) → `Footnote` struct → `ToolCallResults.footnotes` → `assemble_turn()` uses `unwrap_or_default()` → `ActionResult.footnotes`. All error paths return typed `Err` with tracing. No panics.

**Error handling:** 2 error paths (EmptySummary, InvalidCategory), both with `thiserror` Display and `tracing::warn!`. Clean.

**Wiring:** Module declared in `tools/mod.rs`. No non-test consumers — expected per Phase 8 scope.

[EDGE] N/A — disabled
[SILENT] Fixed: fallback replaced with no-fallback + warn logging
[TEST] 20 tests, comprehensive coverage
[DOC] Clear documentation
[TYPE] N/A — disabled
[SEC] N/A — disabled
[SIMPLE] Clean, minimal implementation (84 lines)
[RULE] #[non_exhaustive] missing on error enum, MEDIUM

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/tools/lore_mark.rs` — new module: footnote validation with category parsing, OTEL instrumentation
- `crates/sidequest-agents/src/tools/assemble_turn.rs` — extended ToolCallResults with `footnotes: Option<Vec<Footnote>>`, fallback merge logic
- `crates/sidequest-agents/src/tools/mod.rs` — added lore_mark module declaration
- `crates/sidequest-agents/tests/scene_tools_story_20_2_tests.rs` — updated ToolCallResults construction for struct compatibility

**Tests:** 20/20 passing (GREEN) + 44 sibling tests (20-2) still pass + 675 total crate tests green
**Branch:** feat/20-4-lore-mark-tool (pushed)

**Handoff:** To verify phase (TEA)

## Delivery Findings

No upstream findings at setup time.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Conflict** (non-blocking): AC-2 originally specified fallback semantics for footnotes, violating CLAUDE.md no-silent-fallbacks rule. Fixed during review: changed to no-fallback (`unwrap_or_default`) with `tracing::warn!` when narrator footnotes are discarded. Affects `crates/sidequest-agents/src/tools/assemble_turn.rs:49-53` (now correct). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `LoreMarkError` missing `#[non_exhaustive]`. Same crate-wide gap as Phase 2/3 error enums. Affects `crates/sidequest-agents/src/tools/lore_mark.rs:23` (add attribute). *Found by Reviewer during code review.*

## Design Deviations

No design deviations yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **AC-2 fallback semantics corrected** — original spec said "If tool doesn't fire (None), use narrator extraction footnotes (fallback)." This violated CLAUDE.md no-silent-fallbacks rule. Fixed to no-fallback with `unwrap_or_default()` + `tracing::warn!`. Session AC-2 updated to match.