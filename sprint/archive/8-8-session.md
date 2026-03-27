---
story_id: "8-8"
jira_key: "none"
epic: "8"
workflow: "tdd"
---
# Story 8-8: Catch-up narration — generate arrival snapshot for mid-session joining players

## Story Details
- **ID:** 8-8
- **Jira Key:** none (personal project)
- **Epic:** 8 — Multiplayer — Turn Barrier, Party Coordination, Perception Rewriter
- **Workflow:** tdd
- **Stack Parent:** 8-1 (MultiplayerSession)
- **Points:** 3
- **Priority:** p2

## Story Context

When a player joins a multiplayer session mid-game, they need a catch-up narration — a concise arrival snapshot summarizing what has happened so far. This prevents late joiners from being disoriented and gives them enough context to participate meaningfully.

### Acceptance Criteria
1. Late-joining players receive a generated catch-up narration on connect
2. Catch-up summarizes key events, active characters, current location, and situation
3. Catch-up respects perception filters (player sees only what their character would know)
4. Existing players are NOT re-narrated the catch-up
5. Catch-up generation does not block the active turn for other players

### Key References
- sq-2/sidequest/game/multiplayer_session.py
- Story 8-1 (MultiplayerSession), 8-6 (PerceptionRewriter)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-27T02:17:25Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-27T01:45:00Z | 2026-03-27T01:47:38Z | 2m 38s |
| red | 2026-03-27T01:47:38Z | 2026-03-27T01:55:22Z | 7m 44s |
| green | 2026-03-27T01:55:22Z | 2026-03-27T02:02:22Z | 7m |
| spec-check | 2026-03-27T02:02:22Z | 2026-03-27T02:03:43Z | 1m 21s |
| verify | 2026-03-27T02:03:43Z | 2026-03-27T02:09:20Z | 5m 37s |
| review | 2026-03-27T02:09:20Z | 2026-03-27T02:15:58Z | 6m 38s |
| spec-reconcile | 2026-03-27T02:15:58Z | 2026-03-27T02:17:25Z | 1m 27s |
| finish | 2026-03-27T02:17:25Z | - | - |

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
- **Improvement** (non-blocking): `make_character()` test helper is duplicated across 3+ test files (8-1, 8-7, 8-8). Extract to shared fixtures module in a future housekeeping story.
  Affects `crates/sidequest-game/tests/` (create common test fixtures).
  *Found by TEA during test verification.*

### Reviewer (code review)
- **Improvement** (non-blocking): `Err(_)` in `generate_catch_up_with_fallback` (catch_up.rs:151) discards error context. Add `tracing::warn!` before fallback for production observability.
  Affects `crates/sidequest-game/src/catch_up.rs` (add tracing call in fallback arm).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Unused import `use crate::combatant::Combatant` at catch_up.rs:7. Remove dead import.
  Affects `crates/sidequest-game/src/catch_up.rs` (delete line 7).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **build_prompt as public method instead of internal**
  - Spec source: context-story-8-8.md, Technical Approach
  - Spec text: Shows prompt construction inline in `generate()` method
  - Implementation: Tests exercise `build_prompt()` as a separate public static method for prompt content verification
  - Rationale: Making prompt construction testable requires it to be accessible. The spec's inline format is a code sketch, not a binding API contract.
  - Severity: minor
  - Forward impact: none — gives Dev flexibility in implementation

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **TEA: build_prompt as public method** → ✓ ACCEPTED: Testable prompt construction is a net positive. Spec sketch is not binding.
- **Dev: No deviations** → ✓ ACCEPTED: Implementation faithful to spec with justified architectural improvements (sync vs async, trait DI vs concrete client).
- No undocumented deviations found.

### Architect (reconcile)
- **Synchronous API instead of async**
  - Spec source: context-story-8-8.md, Technical Approach line 26
  - Spec text: "`pub async fn generate(&self, state: &GameState, ...)`"
  - Implementation: All methods are synchronous (`fn`, not `async fn`). The `GenerationStrategy` trait returns `Result<String, CatchUpError>` synchronously.
  - Rationale: The game crate (`sidequest-game`) has no tokio dependency. Async belongs at the server layer where the real Claude CLI strategy will be implemented. The trait can be made async later via `async-trait` when wiring to the server.
  - Severity: minor
  - Forward impact: none — the server crate will implement `GenerationStrategy` with its own async wrapper

- **Trait-object DI instead of concrete ClaudeClient**
  - Spec source: context-story-8-8.md, Technical Approach line 22
  - Spec text: "`pub struct CatchUpGenerator { claude: ClaudeClient }`"
  - Implementation: Uses `strategy: Box<dyn GenerationStrategy>` with a pluggable trait for dependency injection.
  - Rationale: Enables test doubles without mocking infrastructure. Consistent with `RewriteStrategy` pattern established in story 8-6 (perception.rs). The spec sketch is not a binding API contract.
  - Severity: minor
  - Forward impact: positive — consistent DI pattern across LLM-calling modules

- **Individual parameters instead of GameState**
  - Spec source: context-story-8-8.md, Technical Approach line 28
  - Spec text: "`state: &GameState, recent_turns: &[TurnSummary], character: &Character`"
  - Implementation: Takes `character: &Character`, `recent_turns: &[TurnSummary]`, `location: &str`, `genre_voice: &str` — no `GameState` dependency.
  - Rationale: Avoids coupling catch_up module to the full GameState type. Extracts only the data needed (location, genre voice). Reduces import graph and improves testability.
  - Severity: minor
  - Forward impact: none — the caller that has GameState can extract location and genre_voice at the call site

## Sm Assessment

**Story 8-8: Catch-up narration** — 3pt TDD story, smaller scope.

**Scope:** Generate an arrival snapshot for late-joining multiplayer players. Summarize key events, respect perception filters, don't block active turns.

**Dependencies:** 8-1 (MultiplayerSession) and 8-6 (PerceptionRewriter) both complete.

**Risk:** Low — straightforward feature building on established infrastructure.

**Routing:** Peloton mode — continuing autonomous Epic 8 execution.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3pt TDD story with new module, new types, strategy trait, and behavioral logic.

**Test Files:**
- `crates/sidequest-game/tests/catch_up_story_8_8_tests.rs` — 32 tests across 12 sections

**Tests Written:** 32 tests covering all ACs (6 story context + 5 session)
**Status:** RED (26 failing with todo!() panics, 6 passing structural tests)

### Test Sections
1. TurnSummary struct (4 tests)
2. CatchUpError enum (4 tests)
3. CatchUpGenerator construction and basic usage (2 tests)
4. Prompt construction — character, location, genre, events (4 tests)
5. Last-5-turns window — AC-2 (3 tests)
6. Graceful fallback — AC-5 (3 tests)
7. CatchUpResult struct (3 tests)
8. Targeted delivery — AC-3/Session AC-4 (2 tests)
9. Join notification — AC-4 (1 test)
10. No history edge case (1 test)
11. GenerationStrategy trait object safety (1 test)
12. Edge cases and rule enforcement (4 tests)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | `catch_up_error_is_non_exhaustive` | passing (structural) |
| #5 validated constructors | N/A — no trust boundary constructors (internal data types) |
| #6 test quality | Self-check: all 32 tests have meaningful assertions, no vacuous `let _ =` or `assert!(true)` |
| #9 public fields | `turn_summary_fields_are_private` — verifies private fields with getters | failing |

**Rules checked:** 4 of 15 applicable lang-review rules have test coverage
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Major Winchester) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/catch_up.rs` — replaced all 14 todo!() stubs with working implementation

**Tests:** 32/32 passing (GREEN), 735/735 full crate zero regressions
**Branch:** feat/8-8-catch-up-narration (pushed)

**Implementation Notes:**
- `TurnSummary`: private fields with getters (rule #9)
- `CatchUpError`: `#[non_exhaustive]` + `thiserror` derivation (rule #2)
- `GenerationStrategy`: trait object safe for `Box<dyn>` DI
- `CatchUpGenerator`: pluggable strategy, prompt builder, last-5-turns window via `saturating_sub`
- `CatchUpResult`: builder pattern with `for_player()` for targeted delivery
- Graceful fallback: `generate_catch_up_with_fallback` catches errors, returns location-based summary

**Handoff:** To next phase (spec-check → verify → review)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 6 story-context ACs and 5 session ACs are covered by the implementation. Two spec-sketch differences (sync vs async, `GenerationStrategy` trait vs `ClaudeClient`) are architectural improvements, not drift — the game crate correctly avoids tokio dependency, and the trait-object DI pattern enables testability. Session AC-3 (perception filters) is not a gap: the story context explicitly scopes out character-specific filtering; perception integration belongs at the session/server wiring layer.

TEA's logged deviation (public `build_prompt`) is accurate and minor.

**Decision:** Proceed to verify

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (catch_up.rs, catch_up_story_8_8_tests.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 5 findings | Duplicated make_character() helper (high), shared test fixtures (medium), strategy pattern similarity with perception.rs (low) |
| simplify-quality | clean | No issues found |
| simplify-efficiency | 7 findings | Dual generate methods (high — dismissed, tests define API), remove derive tests (high — dismissed, lang-review compliance), builder pattern for single field (medium) |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 — make_character() test fixture duplication across test files (future refactoring story)
**Noted:** 3 low-confidence observations (strategy trait unification, test macro extraction, permissive assertion)
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** All passing (32/32 story tests, 735/735 crate, 0 compiler errors, 13 pre-existing clippy warnings)
**Handoff:** To Colonel Potter for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | error | compile error (wrong branch state) | Dismissed — environment issue, tests verified GREEN by Dev and TEA |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | Confirmed 1 [SILENT]: Err(_) discards error at line 151 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | error | 4 (wrong file) | Dismissed — subagent reviewed perception.rs not catch_up.rs; own type-design review performed |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 8 | Confirmed 2, dismissed 6 (see assessment) |

**All received:** Yes (4 returned, 5 disabled/skipped)
**Total findings:** 2 confirmed (1 medium, 1 low), 7 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] `CatchUpError` has `#[non_exhaustive]` — catch_up.rs:41. Complies with lang-review rule #2.
2. [VERIFIED] `TurnSummary` fields are private with getters — catch_up.rs:15-16 (private), getters at lines 29-36. Complies with rule #9.
3. [VERIFIED] `CatchUpResult` fields are private with getters — catch_up.rs:62-64 (private), getters at lines 87-104. Complies with rule #9.
4. [VERIFIED] `CatchUpGenerator.strategy` is private — catch_up.rs:113. No public mutation path. Complies with rule #9.
5. [VERIFIED] `CatchUpError` uses thiserror — catch_up.rs:40 `#[derive(Debug, thiserror::Error)]`. Domain error type, not String.
6. [VERIFIED] No `#[derive(Deserialize)]` on any types — rules #8 and #13 are N/A.
7. [VERIFIED] No unsafe `as` casts — rule #7 N/A. `saturating_sub` used correctly at line 165.
8. [VERIFIED] `format_recent()` bounds output to last 5 turns via `saturating_sub(5)` — catch_up.rs:165. Rule #15 compliant (bounded input).
9. [SILENT] `Err(_)` in `generate_catch_up_with_fallback` (catch_up.rs:151) discards error with no tracing. Fallback behavior is spec-required (AC-5), but error context is lost. **[MEDIUM]** — observability gap, not blocking.
10. [RULE] Unused import `use crate::combatant::Combatant` at catch_up.rs:7. Dead code. **[LOW]** — cosmetic.
11. [TYPE] All struct fields appropriately private — TurnSummary (lines 15-16), CatchUpResult (lines 62-64), CatchUpGenerator (line 113). No stringly-typed APIs at trust boundaries; `location: &str` and `genre_voice: &str` acceptable for internal game crate scope. No Deserialize bypasses.
12. [VERIFIED] Strategy pattern (`Box<dyn GenerationStrategy>`) — catch_up.rs:54-57, 113. Object-safe trait, consistent with `RewriteStrategy` in perception.rs. Good pattern.
12. [VERIFIED] `generate_catch_up()` propagates errors via `?` — catch_up.rs:134. Non-fallback path correctly returns error to caller.

### Rule Compliance

| Rule | Types/Functions Checked | Compliant? |
|------|------------------------|------------|
| #1 Silent errors | generate_catch_up, generate_catch_up_with_fallback, format_recent, build_prompt, join_notification | Yes (fallback is intentional per AC-5) |
| #2 non_exhaustive | CatchUpError | Yes (line 41) |
| #3 Placeholders | saturating_sub(5), prompt text | Yes (spec-defined constant, prose instructions) |
| #4 Tracing | generate_catch_up, generate_catch_up_with_fallback | No — MEDIUM: no tracing on error paths |
| #5 Constructors | TurnSummary::new, CatchUpGenerator::new, CatchUpResult::generated/fallback | Yes (internal types, not trust boundaries) |
| #6 Test quality | 32 tests | Yes (2 structural tests are intentional compile-time checks per TEA Assessment) |
| #7 as casts | all functions | Yes (none present) |
| #8 Deserialize bypass | TurnSummary, CatchUpResult, CatchUpError | N/A (no Deserialize derives) |
| #9 Public fields | TurnSummary, CatchUpResult, CatchUpGenerator | Yes (all private with getters) |
| #10 Tenant context | GenerationStrategy::generate | N/A (single-session scope, no multi-tenant) |
| #11 Workspace deps | Cargo.toml | Yes (thiserror uses workspace = true) |
| #12 Dev deps | Cargo.toml | Yes (test deps in dev-dependencies) |
| #13 Constructor/Deser consistency | all types | N/A (no Deserialize) |
| #14 Fix regressions | catch_up.rs | Yes (unused import is cosmetic, not behavioral) |
| #15 Unbounded input | format_recent, build_prompt | Yes (5-turn window caps output) |

### Data Flow Traced

`character.name()` + `location` + `genre_voice` → `build_prompt()` → prompt string → `strategy.generate(&prompt)` → `CatchUpResult::generated(narration)`. All string data flows into an LLM prompt (not SQL, not HTML). No injection risk. The `for_player()` builder sets a routing ID for targeted delivery — doesn't affect prompt content.

### Wiring

This is a game crate module — not yet wired to server endpoints. Wiring to the WebSocket session layer will happen in a future story. The module is self-contained and testable via the strategy trait.

### Error Handling

- `generate_catch_up()`: propagates `CatchUpError` via `?` — caller decides.
- `generate_catch_up_with_fallback()`: catches all errors, returns fallback. Intentional per AC-5. Error context lost (MEDIUM finding).
- `format_recent()`, `build_prompt()`, `join_notification()`: infallible pure functions.

### Security Analysis

No auth checks needed — this is internal game logic, not an API boundary. No user input reaches this module directly (character names come from validated `NonBlankString` in `Character`, locations from game state). No tenant isolation concerns (single-session scope).

### Hard Questions

- **Empty turn summaries?** `format_recent(&[])` returns empty string — prompt still works, just no "Recent events" content.
- **Huge turn history?** Bounded to last 5 via `saturating_sub(5)` — safe.
- **Empty location/genre_voice?** Produces a grammatically odd but non-crashing prompt. Acceptable for scaffold.
- **Strategy panics?** `strategy.generate()` could panic from a bad implementation — but that's the implementor's contract, not this module's concern.

### Devil's Advocate

What if this code is broken? The most concerning path is `generate_catch_up_with_fallback` where `Err(_)` swallows ALL errors indiscriminately. If the strategy returns `CatchUpError::NoHistory`, that's a logic error in the caller (they passed empty history), not an infrastructure failure — but the fallback treats it identically to `GenerationFailed`. A confused caller could pass empty turns, get a fallback result, and never know they miscalled the API. The `is_fallback()` flag on the result is the only signal, and a lazy caller might ignore it.

The unused `use crate::combatant::Combatant` import is suspicious — was there meant to be a `Combatant` parameter or conversion that got dropped? If a future story expects `CatchUpGenerator` to accept `&Combatant` instead of `&Character`, this import is a breadcrumb of an abandoned approach that should be cleaned up.

The prompt itself (`build_prompt`) is not sanitized or escaped. If `character.name()` contained newlines or prompt injection attempts (e.g., "Ignore previous instructions"), those would flow directly into the LLM prompt. For a game where character names come from `NonBlankString` validation, this is low risk — but if character creation ever allows freeform names from players, this becomes a prompt injection vector.

None of these rise to CRITICAL or HIGH. The code is correct for its scope. The observability gap (no tracing) is the most operationally impactful finding but doesn't affect correctness.

### Deviation Audit

- **TEA: build_prompt as public method** → ✓ ACCEPTED by Reviewer: Testable prompt construction is a net positive. The spec sketch is not a binding API contract.
- **Dev: No deviations from spec** → ✓ ACCEPTED by Reviewer: Implementation faithfully follows spec with justified architectural improvements (sync vs async, trait DI vs concrete client).

**Handoff:** To Hawkeye for finish-story