---
story_id: "30-1"
jira_key: "none"
epic: "30"
workflow: "tdd"
---
# Story 30-1: Character name not saved — persists as numeric index instead of player-entered name

## Story Details
- **ID:** 30-1
- **Type:** Bug
- **Jira Key:** none (personal project)
- **Priority:** p1
- **Points:** 3
- **Workflow:** tdd
- **Stack Parent:** none

## Problem Statement
During playtesting, when creating a new character with a name like "Four-fingered Jack", the game saves the character name as a numeric index (e.g., "1") instead of the player-entered name. Throughout the game, the narrator refers to the character by this numeric index rather than the actual name.

The character name is never properly persisted from character creation into the game state or save file.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-08T12:24:05Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-08 | 2026-04-08T11:44:04Z | 11h 44m |
| red | 2026-04-08T11:44:04Z | 2026-04-08T12:01:34Z | 17m 30s |
| green | 2026-04-08T12:01:34Z | 2026-04-08T12:05:11Z | 3m 37s |
| spec-check | 2026-04-08T12:05:11Z | 2026-04-08T12:06:18Z | 1m 7s |
| verify | 2026-04-08T12:06:18Z | 2026-04-08T12:08:45Z | 2m 27s |
| review | 2026-04-08T12:08:45Z | 2026-04-08T12:24:05Z | 15m 20s |
| finish | 2026-04-08T12:24:05Z | - | - |

## Sm Assessment

Story 30-1 is ready for TDD red phase. Session file created, branch `feat/30-1-character-name-not-saved` exists in the API repo. No Jira (personal project). This is a character creation bug — the player-entered name is stored as a numeric index (e.g. "1") instead of the actual name (e.g. "Four-fingered Jack"). The save file, narration, and party display all show the wrong name. 3-point TDD bug fix, API-only. Handing off to TEA for failing tests.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The dispatch/connect.rs scene handler at line 903 defaults to `"1"` when no choice is provided, then parses it as a numeric index. For no-choice scenes, this tries `apply_choice(0)` which fails. The server should use `apply_freeform` for scenes with empty choices. Affects `crates/sidequest-server/src/dispatch/connect.rs` (line 903-914). *Found by TEA during test design.*
- **Gap** (non-blocking): Genre packs like caverns_and_claudes have no name-entry scene at all. The confirmation phase falls back to `payload.choice` which is a numeric index. The fix should either (a) validate the name in `build()` or (b) ensure the server always provides the player name when no name scene exists. Affects `crates/sidequest-game/src/builder.rs` (line 553) and `crates/sidequest-server/src/dispatch/connect.rs` (line 943-950). *Found by TEA during test design.*

## Tea Assessment

**Tests Required:** Yes
**Reason:** Bug fix — character names persisted as numeric indices

**Test File:**
- `crates/sidequest-game/tests/character_name_story_30_1_tests.rs` — 9 tests covering character name flow

**Tests Written:** 9 tests covering 5 ACs
**Status:** RED (1 failing — `build_rejects_numeric_string_as_name`)

**Root Cause Analysis:**
The caverns_and_claudes chargen has no name-entry scene. All scenes have `choices: []` and `allows_freeform: false`. The `character_name()` method returns `None`. The confirmation phase falls back to `payload.choice`, which can be "1" (a numeric UI index). The character is built with name "1".

**What Dev needs to implement:**
1. `build()` should reject purely numeric names — they indicate a UI index was mistakenly used
2. The server should ensure the fallback chain produces a real name (player_name from connect, not payload.choice)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 Test quality | Self-checked — all 9 tests have meaningful assertions | passing |

**Rules checked:** 1 of 15 applicable
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Korben Dallas) for implementation

## Design Deviations

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): `build()` numeric check has vacuous truth on empty string — `"".chars().all(...)` returns true. Guard should be `!trimmed.is_empty() && trimmed.chars().all(...)`. Affects `crates/sidequest-game/src/builder.rs` (line 566). *Found by Reviewer during code review.*

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/builder.rs` — Added `NumericName` error variant to `BuilderError`, added validation in `build()` to reject purely numeric names

**Tests:** 9/9 passing (GREEN), 51/51 existing builder tests passing
**Branch:** feat/30-1-character-name-not-saved (pushed)

**Handoff:** To verify phase (TEA)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

The implementation addresses the core bug — `build()` now rejects purely numeric names with a `NumericName` error variant. TEA suggested two fixes: (1) validate in `build()` and (2) fix the server fallback chain. Dev implemented (1), which is the correct defense-in-depth: even if the server sends a numeric index, the builder rejects it. The server fallback chain fix (dispatch/connect.rs:943-950) is noted in TEA's delivery findings as non-blocking — it's a belt-and-suspenders improvement but not required for this story's scope.

**Decision:** Proceed to verify

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 1 (+ 1 test file)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | All pre-existing patterns (phase extraction duplication, hook boilerplate, accumulated() repetition, MechanicalEffects default) — outside story scope |
| simplify-quality | 3 findings | All pre-existing (error-handling gap, dead anchor code, unwrap consistency) — outside story scope |
| simplify-efficiency | 8 findings | All pre-existing (accumulated() verbosity, phase matching duplication, etc.) — outside story scope |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 (all outside story scope)
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean (no changes needed for this story's code)

**Quality Checks:** All passing (60/60 tests)
**Handoff:** To Reviewer for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | dismissed 2 (pre-existing, not in diff) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 3 as MEDIUM/LOW (non-blocking) |

**All received:** Yes (3 returned, 6 disabled via settings)
**Total findings:** 3 confirmed (non-blocking), 2 dismissed (pre-existing)

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] `BuilderError` has `#[non_exhaustive]` — rule #2 compliant. Evidence: builder.rs:155.
2. [VERIFIED] `NumericName(String)` variant follows thiserror pattern with `#[error(...)]` and positional `{0}`. Evidence: builder.rs:181-182.
3. [VERIFIED] Validation in `build()` correctly rejects `"1"`, `"42"`, `"007"` — all pure-digit strings. Evidence: builder.rs:566-569, `chars().all(|c| c.is_ascii_digit())`.
4. [VERIFIED] 60/60 tests pass (9 story + 51 existing builder). Evidence: preflight.
5. [MEDIUM] [RULE] [SILENT] Vacuous truth: `"".chars().all(|c| c.is_ascii_digit())` returns `true` in Rust. `build("")` returns `NumericName("")` instead of reaching the blank-name check. The error message "is purely numeric" is misleading for empty strings. Fix: `if !trimmed.is_empty() && trimmed.chars().all(...)`. Not data-corrupting — empty strings ARE rejected, just with wrong error variant.
6. [LOW] [RULE] Test `build_rejects_numeric_string_as_name` uses `assert!(result.is_err())` — should match `Err(BuilderError::NumericName(_))` for specificity.
7. [LOW] [RULE] No tracing on NumericName rejection path. sidequest-game is a pure engine crate without tracing dependency — dispatch layer surfaces errors. Non-blocking.

### Rule Compliance

| Rule | Instances | Status |
|------|-----------|--------|
| #2 non_exhaustive | BuilderError enum | PASS |
| #4 Tracing | NumericName rejection | NOTE — sidequest-game has no tracing dep |
| #5 Constructors | build() validation | MEDIUM — vacuous truth on empty string |
| #6 Test quality | 9 tests | LOW — 1 assertion could be tighter |

### Devil's Advocate

What if someone names their character "007"? It's a valid character name (James Bond reference) but it's purely numeric — the guard would reject it. What about "42" as a name? Hitchhiker's Guide fans might object. The validation is correct for catching UI index bugs but slightly over-broad for intentional numeric names. However: (1) No real player would type "1" as a character name, (2) "007" is extremely unlikely in a fantasy RPG, (3) The error message clearly explains what happened, and (4) The server fallback chain is the real fix — this is defense-in-depth. Acceptable trade-off for a 3-point bug fix.

The empty string vacuous truth is the real edge case — but it's non-corrupting (still rejected) and the wrong error message is only visible in OTEL/logs, not to the player. MEDIUM, not blocking.

### Data Flow Trace

Player types name → UI sends `payload.choice: "Four-fingered Jack"` → dispatch/connect.rs confirmation phase → `character_name()` returns None (no name scene) → falls back to `payload.choice` → `build("Four-fingered Jack")` → passes numeric check → `NonBlankString::new()` succeeds → Character created with correct name. If `payload.choice` is "1" → `build("1")` → numeric check fires → `Err(NumericName("1"))` → error_response to client. Bug prevented. ✓

**Handoff:** To Ruby Rhod (SM) for finish

### Reviewer (audit)

- TEA: "No deviations from spec" → ✓ ACCEPTED by Reviewer
- Dev: "No deviations from spec" → ✓ ACCEPTED by Reviewer
- Architect: "No additional deviations found" → ✓ ACCEPTED by Reviewer

### Architect (reconcile)
- No additional deviations found.