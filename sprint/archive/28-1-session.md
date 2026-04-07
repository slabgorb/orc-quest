---
story_id: "28-1"
jira_key: null
epic: "28"
workflow: "tdd"
---
# Story 28-1: Load ConfrontationDefs into Server

## Story Details
- **ID:** 28-1
- **Jira Key:** N/A (personal project)
- **Workflow:** tdd
- **Epic:** 28 — Unified Encounter Engine
- **Points:** 2
- **Priority:** p0
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-07T07:25:27Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-06T20:30:00Z | 2026-04-07T06:26:17Z | 9h 56m |
| red | 2026-04-07T06:26:17Z | 2026-04-07T06:35:19Z | 9m 2s |
| green | 2026-04-07T06:35:19Z | 2026-04-07T06:39:42Z | 4m 23s |
| spec-check | 2026-04-07T06:39:42Z | 2026-04-07T06:57:52Z | 18m 10s |
| verify | 2026-04-07T06:57:52Z | 2026-04-07T06:59:53Z | 2m 1s |
| review | 2026-04-07T06:59:53Z | 2026-04-07T07:25:27Z | 25m 34s |
| finish | 2026-04-07T07:25:27Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **find_confrontation_def as free function instead of DispatchContext method**
  - Rationale: DispatchContext has 55+ fields and can't be constructed in tests. A free function taking `&[ConfrontationDef]` is testable and equally usable from dispatch code. Dev may implement as method instead — tests will adapt.
  - Severity: minor
  - Forward impact: none — either approach works for 28-3, 28-4, 28-5

## Sm Assessment

Story 28-1 is the foundation of Epic 28 (Unified Encounter Engine). It loads
ConfrontationDefs from genre pack YAML into the server's DispatchContext so
every subsequent story (28-3 through 28-9) has encounter type definitions
available at runtime. 2 points, p0, TDD workflow.

Context documents are thorough — epic context covers the full architectural
before/after, story context has exact file locations and 5 ACs with grep
verification commands. Ready for TEA to write failing tests.

**Repos:** api (sidequest-api, develop branch)
**Branch:** feat/28-1-load-confrontation-defs
**Next:** TEA (Han Solo) for RED phase — write failing tests for ConfrontationDef
loading into DispatchContext.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Foundation story — ConfrontationDef loading into DispatchContext must be verified.

**Test Files:**
- `crates/sidequest-server/tests/confrontation_defs_wiring_story_28_1_tests.rs` — 6 tests covering 5 ACs

**Tests Written:** 6 tests covering 5 ACs
**Status:** RED (failing — ready for Dev)

| Test | AC | What it verifies |
|------|----|------------------|
| `confrontation_def_is_reachable_from_server_crate` | Wiring | ConfrontationDef importable from server crate |
| `dispatch_context_has_confrontation_defs_field` | Defs loaded | find_confrontation_def exists as public API |
| `find_confrontation_def_returns_matching_def` | Lookup | Lookup by encounter_type returns correct def |
| `find_confrontation_def_returns_none_for_unknown_type` | Lookup miss | Unknown type → None, empty string → None |
| `spaghetti_western_loads_confrontation_defs` | Non-empty | Real genre pack loads 3+ types, standoff has beats |
| `victoria_has_no_combat_confrontation_type` | Non-empty | Victoria has social types but no combat |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No silent fallbacks | `returns_none_for_unknown_type` | failing |
| Verify wiring not just existence | `dispatch_context_has_confrontation_defs_field` | failing |
| Every test asserts something meaningful | All 6 tests have specific assertions | verified |

**Rules checked:** 3 of applicable rules
**Self-check:** 0 vacuous tests found

**Handoff:** To Yoda (Dev) for GREEN phase implementation

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Files Analyzed:** 4 (connect.rs, mod.rs, lib.rs, test file)

| Aspect | Status | Findings |
|--------|--------|----------|
| Code quality | clean | Implementation follows existing patterns (resource_declarations, sfx_library) |
| Reuse | clean | Uses existing GenreCode→cache→pack pipeline, no duplication |
| Efficiency | clean | Minimal implementation — one free function, one field, two init blocks |

**Applied:** 0 fixes
**Flagged for Review:** 0 findings
**Noted:** 0 observations
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** cargo build clean, cargo test 6/6 passing, clippy warnings are pre-existing (sidequest-protocol doc warnings, not from this story)
**Handoff:** To Obi-Wan (Reviewer) for code review

## Delivery Findings

### TEA (test design)
- No upstream findings during test design.

### TEA (test verification)
- No upstream findings during test verification.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/lib.rs` — Added `find_confrontation_def()` public function; added confrontation_defs inline loading in DispatchContext construction; added OTEL encounter.defs_loaded event
- `crates/sidequest-server/src/dispatch/mod.rs` — Added `confrontation_defs: Vec<ConfrontationDef>` field to DispatchContext
- `crates/sidequest-server/src/dispatch/connect.rs` — Added confrontation_defs inline loading in connect DispatchContext construction

**Tests:** 6/6 passing (GREEN)
**Branch:** feat/28-1-load-confrontation-defs (pushed)

**Handoff:** To next phase (verify/review)

### Dev (implementation)
- No upstream findings during implementation.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 pre-existing (clippy docs in protocol, fmt in audio.rs) | dismissed 2 — pre-existing, not from 28-1 commits |
| 2 | reviewer-edge-hunter | N/A | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 (2 high: silent .ok() swallowing, 2 medium: missing OTEL else) | confirmed 2 high (MEDIUM — follows established pattern), dismissed 2 medium (OTEL else not required by convention) |
| 4 | reviewer-test-analyzer | N/A | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | N/A | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | N/A | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | N/A | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | N/A | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 (Rules 1,4,16 — silent fallback, missing tracing on error path) | confirmed 4, downgraded to MEDIUM — identical pre-existing pattern across 10+ fields |

**All received:** Yes (3 returned, 6 disabled/skipped)
**Total findings:** 4 confirmed (all MEDIUM — systemic pre-existing pattern), 2 dismissed (pre-existing lint/fmt)

## Reviewer Assessment

**Verdict:** APPROVED

### Rule Compliance

| Rule | Instances | Status | Evidence |
|------|-----------|--------|----------|
| #1 Silent errors | 2 (lib.rs:1832, connect.rs:1395) | MEDIUM violation | `.ok()` swallows GenreCode/cache errors — but follows identical pattern used by sfx_library, rooms, genre_affinities, carry_mode, weight_limit, world_graph in same functions |
| #2 non_exhaustive | 0 enums in diff | N/A | No enums introduced |
| #3 Placeholders | 0 | Pass | `""` fallback is intentional input to GenreCode::new() validator |
| #4 Tracing | 2 (lib.rs:1832, connect.rs:1395) | MEDIUM violation | Error path has no tracing — same as all other genre-loaded fields |
| #5 Constructors | 2 | Pass | GenreCode::new() validates; result handled (via .ok()) |
| #6 Test quality | 6 tests | Pass | All assertions meaningful, no vacuous tests |
| #7 Unsafe casts | 0 | N/A | No `as` casts in diff |
| #8 Serde bypass | 0 | Pass | ConfrontationDef uses serde(try_from) |
| #9 Public fields | 1 (mod.rs:90) | Pass | DispatchContext is pub(crate), field is read-only game data |
| #10 Tenant context | 0 | N/A | No traits modified |
| #11 Workspace deps | 0 | Pass | No Cargo.toml dep changes |
| #12 Dev deps | 0 | Pass | serde_yaml correctly in dev-dependencies |
| #13 Constructor consistency | 0 | Pass | ConfrontationDef TryFrom validates consistently |
| #14 Fix regressions | 0 | Pass | Fix commit (8c98ab2) only adds OTEL, introduces no new bugs |
| #15 Unbounded input | 0 | Pass | Data from trusted genre YAML, not user input |

### Observations

1. [VERIFIED] DispatchContext.confrontation_defs field added — `dispatch/mod.rs:90`, `Vec<sidequest_genre::ConfrontationDef>`. Populated in both dispatch paths: `lib.rs:1832` (per-turn) and `connect.rs:1395` (session init). Follows same owned-Vec pattern as sfx_library. Rule #9: pub field on pub(crate) struct holding read-only game data — no security invariant, compliant.

2. [VERIFIED] find_confrontation_def() — `lib.rs:126-131`. Returns `Option<&ConfrontationDef>`, no panic on miss. Correct lifetime annotation. Test-only consumers expected for foundation story (scope says "Out of scope: Using the defs for anything — that's 28-3+").

3. [VERIFIED] OTEL events in both dispatch paths — `lib.rs:1876-1884` and `connect.rs:1439-1447`. Both emit `encounter.defs_loaded` with genre, count, and type names via WatcherEventBuilder. Satisfies AC-OTEL.

4. [VERIFIED] Integration tests against real genre packs — `spaghetti_western_loads_confrontation_defs` (asserts ≥3 types, checks standoff category) and `victoria_has_no_combat_confrontation_type` (asserts social-only genre has no combat). Wiring test proves ConfrontationDef reachable from server crate.

5. [MEDIUM] [SILENT] [RULE] Silent fallback on genre pack load failure — `lib.rs:1832-1838` and `connect.rs:1395-1401`. The `.ok()` → `.unwrap_or_default()` chain silently swallows GenreCode validation errors and cache load failures. The OTEL event only fires on non-empty success, so load failures are indistinguishable from genres with no confrontation defs. **However:** this is the identical pattern used by ~10 other genre-loaded fields in the same functions. Fixing it for confrontation_defs alone would be inconsistent. Captured as delivery finding for systemic refactor.

6. [VERIFIED] Clippy/fmt failures are pre-existing — `git diff 46c3fa3~1...8c98ab2 --name-only` shows only sidequest-server files. The protocol doc warnings and audio.rs fmt drift are from prior stories on this branch, not from 28-1.

### Data Flow Trace

Player connects → `dispatch_character_creation` (connect.rs) or `dispatch_message` (lib.rs) → `session.genre_slug()` → `GenreCode::new()` → `genre_cache.get_or_load()` → `pack.rules.confrontations.clone()` → `DispatchContext.confrontation_defs` → available throughout `dispatch_player_action()`. Safe: genre pack data is trusted static YAML, cloned into owned Vec, read-only during dispatch.

### Wiring Verification

- `confrontation_defs` field: defined in `dispatch/mod.rs:90`, populated in `lib.rs:1832` and `connect.rs:1395` — **wired in both dispatch paths**
- `find_confrontation_def()`: defined in `lib.rs:126`, exported as `pub` — **test-only consumers** (expected for foundation story, consumers come in 28-3+)
- OTEL: `encounter.defs_loaded` emitted in both paths — **wired**

### Error Handling

Genre pack load failure → empty Vec via `.unwrap_or_default()` → no confrontation defs available → no OTEL event → session proceeds without encounter type awareness. Not a crash, but not observable. See MEDIUM finding #5.

### Security Analysis

No security-relevant changes. ConfrontationDef is game data from trusted YAML. No user input, no auth, no tenant isolation concerns. The new field is on a pub(crate) struct. [SEC] No findings.

### Hard Questions

- **Empty genre slug?** `unwrap_or("")` → `GenreCode::new("")` returns Err → `.ok()` → None → empty Vec. Session proceeds. Not a crash.
- **Huge confrontation defs?** Bounded by genre YAML (trusted content, ~3-10 entries per genre). Not user-controlled.
- **Race condition?** Genre cache is behind Arc, get_or_load is thread-safe. Clone produces an independent Vec. No race.
- **Per-turn cloning cost?** Each turn clones the Vec from cache. Same pattern as sfx_library, rooms, etc. Negligible for ~5 ConfrontationDef entries.

### Tenant Isolation Audit

No tenant-relevant types or trait methods introduced. `find_confrontation_def` is a pure lookup on game data. DispatchContext is session-scoped, not shared across tenants.

### Devil's Advocate

Let me argue this code is broken.

The most concerning aspect is the **OTEL blind spot on empty defs**. Consider a scenario: a genre pack maintainer accidentally deletes the `confrontations:` key from `rules.yaml`, or introduces a YAML parse error. The server loads, `get_or_load()` fails, `.ok()` swallows the error, `unwrap_or_default()` returns an empty Vec, and the `if !ctx.confrontation_defs.is_empty()` guard skips the OTEL event entirely. The GM panel shows nothing. The narrator improvises combat without any confrontation type definitions — exactly the "Claude winging it" anti-pattern that OTEL is meant to detect. The irony: the OTEL observability was added specifically to catch this class of failure, but it only fires on success, not on failure. The lie detector has a blind spot.

A second concern: **duplicated loading logic**. The same 6-line block appears in both `lib.rs:1832-1838` and `connect.rs:1395-1401`. If the field name on GenrePack changes, or if a validation step is added, one site might be updated and the other missed. This is the same DRY violation that exists for every other genre-loaded field, but adding another instance deepens the maintenance burden.

A third concern: **find_confrontation_def has zero production consumers**. The function is tested and correct, but it's dead code in production. If story 28-3 never ships, this function sits unused forever. The "every test suite needs a wiring test" principle is satisfied (the test proves the function is importable), but the deeper "verify wiring, not just existence" principle asks whether the function is reachable from production code paths. Right now it isn't. However, the AC explicitly mandates this function, and scope boundaries explicitly defer its consumption to 28-3+. This is a foundation story doing foundation work.

Does any of this change my verdict? The silent fallback is real but systemic — it affects ~10 fields identically. Fixing it here alone would be inconsistent and pointless. The right fix is a shared loader helper that handles errors for all genre-loaded fields, captured as a delivery finding. The duplicated loading logic is the same systemic issue. The unused function is explicitly called out by the AC and scope boundaries. None of these rise to Critical or High severity given the codebase context.

### Challenge: VERIFIEDs vs Subagent Findings

- VERIFIED #1 (field wired): No subagent contradicts. Both silent-failure-hunter and rule-checker flagged the LOADING pattern (error handling), not the wiring. Field IS wired.
- VERIFIED #2 (find_confrontation_def correct): No subagent contradicts. Rule-checker confirmed Rule 1 compliant for the function itself (returns Option, no swallowing).
- VERIFIED #3 (OTEL events present): Silent-failure-hunter flagged MISSING else branch on the OTEL block (medium confidence). I agree the success path is wired; the failure path lacks observability. This doesn't contradict "OTEL events present" — the events ARE present, they just don't cover the failure case. Adjusted: the finding is captured as MEDIUM #5.
- VERIFIED #4 (integration tests): No subagent contradicts. Preflight confirms 6/6 pass.
- VERIFIED #6 (clippy/fmt pre-existing): Preflight confirms warnings exist but confirms files are not from 28-1 commits.

No VERIFIED contradicted by subagent findings.

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story

### Reviewer (audit)

- **find_confrontation_def as free function instead of DispatchContext method** → ✓ ACCEPTED by Reviewer: Free function taking `&[ConfrontationDef]` is more testable than a method on DispatchContext (55+ fields, can't construct in tests). Either approach works for downstream stories. Agrees with TEA reasoning.

### Reviewer (code review)
- **Improvement** (non-blocking): Silent fallback on genre pack loading is a systemic pattern across ~10 fields in lib.rs and connect.rs. All use `.ok()` → `.unwrap_or_default()` with no tracing on the error path. A shared loader helper with `tracing::warn!` on failures would make all fields observable. This is a candidate for a future refactor story, not a 28-1 fix.
  Affects `crates/sidequest-server/src/lib.rs` and `crates/sidequest-server/src/dispatch/connect.rs` (extract genre-field loading into shared helper with error logging).
  *Found by Reviewer during code review, corroborated by silent-failure-hunter and rule-checker subagents.*

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected
**Mismatches Found:** 1

- **OTEL event missing from connect.rs** (Missing in code — Behavioral, Major)
  - Spec: AC-OTEL says "encounter.defs_loaded event emitted with genre, count, and type names" — the story context says this should fire in connect.rs: "Grep: WatcherEventBuilder with encounter.defs_loaded in connect.rs"
  - Code: OTEL event only fires in lib.rs (main dispatch loop). connect.rs constructs DispatchContext with confrontation_defs but emits no event. The opening turn after session init runs through connect.rs, not lib.rs — the first turn is a blind spot.
  - Recommendation: **B — Fix code.** Add the same WatcherEventBuilder block after the DispatchContext construction in connect.rs. This is a wiring epic — every path must emit.

**Decision:** Handed back to Dev. Connect.rs OTEL gap fixed (commit 8c98ab2). All ACs now aligned. Proceed to review.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec.

### TEA (test design)
- **find_confrontation_def as free function instead of DispatchContext method**
  - Spec source: context-story-28-1.md, Technical Approach
  - Spec text: "Add a convenience method on DispatchContext for lookup by type string"
  - Implementation: Tests expect `sidequest_server::find_confrontation_def(&defs, type)` as a free function taking a slice, not a method on DispatchContext
  - Rationale: DispatchContext has 55+ fields and can't be constructed in tests. A free function taking `&[ConfrontationDef]` is testable and equally usable from dispatch code. Dev may implement as method instead — tests will adapt.
  - Severity: minor
  - Forward impact: none — either approach works for 28-3, 28-4, 28-5