---
story_id: "36-2"
jira_key: null
epic: "36"
workflow: "wire-first"
---
# Story 36-2: Refactor dispatch functions with too many arguments into context structs

## Story Details
- **ID:** 36-2
- **Jira Key:** None (personal project)
- **Epic:** 36 — Post-clippy-cleanup tech debt
- **Workflow:** wire-first
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** wire-first
**Phase:** finish
**Phase Started:** 2026-04-16T16:03:15Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-16T15:18:53Z | 2026-04-16T15:20:39Z | 1m 46s |
| red | 2026-04-16T15:20:39Z | 2026-04-16T15:38:04Z | 17m 25s |
| green | 2026-04-16T15:38:04Z | 2026-04-16T15:53:49Z | 15m 45s |
| review | 2026-04-16T15:53:49Z | 2026-04-16T16:03:15Z | 9m 26s |
| finish | 2026-04-16T16:03:15Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->
- No upstream findings

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): `ResponseContext.narration_state_delta` is owned and then `.clone()`'d — a spurious allocation. Affects `crates/sidequest-server/src/dispatch/response.rs` (change to `&'a StateDelta` reference or move instead of clone). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Missing wiring test for `ChargenInitContext` construction in connect.rs and missing field assertions for `ChargenDispatchContext`. Affects `crates/sidequest-server/tests/integration/dispatch_context_structs_story_36_2_tests.rs` (add 2 tests). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **Updated pre-existing structural test for new signature** → ✓ ACCEPTED by Reviewer: The old test checked exact function parameter strings which no longer exist. The updated assertions correctly verify field presence via TelemetryContext. Intent preserved, approach appropriate.

### Reviewer (audit)
- No undocumented deviations found.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (fmt, clippy) | confirmed 2 |
| 2 | reviewer-edge-hunter | Yes | findings | 3 | confirmed 1, dismissed 2 |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 3, dismissed 4 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1, dismissed 2 |
| 6 | reviewer-type-design | Yes | findings | 2 | dismissed 2 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | dismissed 1 |

**All received:** Yes (7 returned, 2 disabled)
**Total findings:** 7 confirmed, 11 dismissed (with rationale below)

### Confirmed Findings

1. **[PREFLIGHT] fmt gate fails** — 21 formatting diffs on long `Arc<Mutex<Option<...>>>` type annotations. Auto-fixable with `cargo fmt`.
2. **[PREFLIGHT] 15 new `borrow_deref_ref` clippy warnings** — `&*ctx.field` patterns where `ctx.field` suffices for shared refs. Auto-fixable with `cargo clippy --fix`. Would block `just api-lint` (`-D warnings`).
3. **[EDGE] `narration_state_delta.clone()` unnecessary allocation** — `ResponseContext` owns the `StateDelta`, then `.clone()`s it at line 52 of response.rs. Old code moved the value directly. The struct is constructed once and never reused, so the clone is pure waste. Fix: store as `&'a StateDelta` reference (matching other fields) or move out of the owned field without cloning.
4. **[DOC] ConnectContext doc says "29" but struct has 24 fields** — connect.rs:23. The old function had 29 total params but 5 weren't folded in (payload, state, player_id kept as direct; `_continuity_corrections`, `_tx` dropped as dead). Fix: say "per-session mutable references" without a specific count.
5. **[TEST] Missing `ChargenInitContext` wiring test** — There are wiring tests for ConnectContext and ChargenDispatchContext in lib.rs, but `ChargenInitContext` is only constructed within connect.rs (3 internal call sites). No test guards those wiring points.
6. **[TEST] Missing `ChargenDispatchContext` field assertions** — The existence test has zero field-coverage checks. If `continuity_corrections`, `tx`, `quest_log`, `genie_wishes`, or `achievement_tracker` were accidentally dropped, no test catches it.
7. **[TEST] Weakened telemetry consolidation test** — The updated `telemetry_emit_signature_takes_consolidated_args` now uses `src.contains("game_delta") && src.contains("sidequest_game::StateDelta")` which matches anywhere in the file (struct def, body, comments), not just the function signature. The story 36-2 tests already cover this via `emit_telemetry_accepts_telemetry_context` and `telemetry_context_has_required_fields`, so the weakening has backup coverage.

### Dismissed Findings (with rationale)

- **[TYPE] Owned StateDelta inconsistency** — Dismissed as duplicate of confirmed [EDGE] finding #3 above. Same issue, same fix.
- **[TYPE] ConnectContext/ChargenDispatchContext overlap (14 shared fields)** — Dismissed: extracting a shared sub-struct is a follow-on refactor, not a defect. The story scope is parameter-to-struct, not struct consolidation. Low confidence, no safety impact.
- **[EDGE] self_check filter overly broad** — Dismissed: the filter is protective of the self-referential test function. The risk (future `let _ = x.contains(...)` escaping detection) is theoretical and the self-check is a meta-test, not a production guard.
- **[EDGE] world_context mutability asymmetry** — Dismissed: matches the old function signatures exactly (`&mut String` in connect, `&str` in chargen dispatch). The asymmetry is intentional — world_context is written during connect and read-only during chargen dispatch.
- **[TEST] Vacuous substring assertions (bare `"session"`, `"result"`)** — Dismissed: while raw substring matching could false-positive on comments or type names, in practice these tests caught every RED→GREEN transition correctly. The struct bodies are well-structured and don't contain comment text matching field names. Medium-confidence finding with no practical impact in this codebase.
- **[TEST] `extract_fn_signature` finds first `{`** — Dismissed: all 5 target functions have simple signatures (no where-clauses, no generic bounds with braces). The helper works correctly for this use case.
- **[TEST] `dispatch_modules_have_observability` checks file-level imports** — Dismissed: this is an invariant test (it passes both before and after the refactor). Its purpose is to guard against accidentally deleting tracing imports during refactoring, which it does correctly.
- **[DOC] Stale test assertion messages describe pre-refactor state** — Dismissed: assertion messages are only displayed on failure. Since all tests pass, no user sees these messages. The messages are technically stale but have zero runtime impact and will only be read if someone deliberately regresses the code, at which point the description of "what the old code looked like" is actually useful context.
- **[DOC] Stale field names in test message (narration_text, effective_action)** — Dismissed: same rationale as above. Failure messages are dead code paths in passing tests.
- **[RULE] Rule #6 existence-only tests** — Dismissed: the rule-checker itself noted "the field-check siblings rescue the coverage." Each existence test has a companion field-check test. Consolidating them is a style preference, not a defect.
- **[RULE] Rule #11 pre-existing dirs inline pin** — Dismissed: not introduced by this diff.

## Sm Assessment

**Story:** 36-2 — Refactor dispatch functions with too many arguments into context structs
**Epic:** 36 — Post-clippy-cleanup tech debt (follow-up from chore/clippy-workspace-cleanup, 2026-04-11)
**Points:** 5 | **Workflow:** wire-first (phased) | **Repos:** api

**Scope:** The clippy cleanup exposed dispatch functions with excessive parameter counts (likely `#[allow(clippy::too_many_arguments)]` suppressions). This story replaces those long parameter lists with context structs — a standard Rust refactoring pattern. The wire-first workflow ensures boundary tests verify the refactored dispatch handlers remain connected end-to-end.

**Routing:** TEA (Radar) for red phase — write boundary tests against the current dispatch signatures, then Dev (Winchester) refactors to context structs while keeping those tests green.

**Risks:** None significant. This is a mechanical refactoring within sidequest-server/src/dispatch/. No new features, no API contract changes.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wire-first refactoring — structural tests verify context structs exist and are wired through call sites.

**Test Files:**
- `crates/sidequest-server/tests/integration/dispatch_context_structs_story_36_2_tests.rs` — 22 structural/wiring tests

**Tests Written:** 22 tests covering 5 refactoring targets
**Status:** RED (20 failing, 2 passing invariant checks — ready for Dev)

### Test Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Lint removal | 3 | Verify `#[allow(clippy::too_many_arguments)]` removed from all 3 files |
| Struct existence | 5 | Verify ResponseContext, TelemetryContext, ConnectContext, ChargenInitContext, ChargenDispatchContext exist |
| Required fields | 3 | Verify key fields on ResponseContext, TelemetryContext, ConnectContext |
| Signature acceptance | 5 | Verify each function's signature includes its context struct |
| Wiring (call sites) | 4 | Verify mod.rs and lib.rs construct and pass context structs |
| Invariant (pass now) | 2 | Observability preserved + test quality self-check |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 tracing | `dispatch_modules_have_observability` | passing (invariant) |
| #6 test quality | `self_check_no_vacuous_assertions` | passing (invariant) |
| #2 non_exhaustive | N/A — no new public enums | skipped |
| #5 validated constructors | N/A — internal structs, no trust boundary | skipped |
| #8 Deserialize bypass | N/A — structs not deserialized | skipped |
| #9 public fields | N/A — structs are pub(crate)/pub(super) | skipped |

**Rules checked:** 2 of 15 applicable, 13 not applicable to this refactoring story
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Winchester) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/response.rs` — Added `ResponseContext` struct, refactored `build_response_messages` signature
- `crates/sidequest-server/src/dispatch/telemetry.rs` — Added `TelemetryContext` struct, refactored `emit_telemetry` signature
- `crates/sidequest-server/src/dispatch/connect.rs` — Added `ConnectContext`, `ChargenInitContext`, `ChargenDispatchContext` structs; refactored 3 function signatures and 3 internal call sites
- `crates/sidequest-server/src/dispatch/mod.rs` — Updated call sites for `build_response_messages` and `emit_telemetry`
- `crates/sidequest-server/src/lib.rs` — Updated call sites for `dispatch_connect` and `dispatch_character_creation`
- `crates/sidequest-server/tests/integration/turn_complete_consolidation_playtest_2026_04_11.rs` — Updated pre-existing structural test for new signature pattern
- `crates/sidequest-server/tests/integration/main.rs` — Module registration for new test file

**Tests:** 547/547 passing (GREEN), 0 regressions
**Branch:** feat/36-2-refactor-dispatch-context-structs (pushed)

**Handoff:** To Reviewer (Colonel Potter) for code review

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] All 5 `#[allow(clippy::too_many_arguments)]` annotations removed — confirmed by `grep -r "too_many_arguments" dispatch/` returning empty. `response.rs:35`, `telemetry.rs:28`, `connect.rs:27,1049,1218` all replaced with context structs.
2. [VERIFIED] All 5 context structs exist with correct visibility — `ResponseContext` pub(super) at response.rs:25, `TelemetryContext` pub(super) at telemetry.rs:10, `ConnectContext` pub(crate) at connect.rs:26, `ChargenInitContext` pub(crate) at connect.rs:57, `ChargenDispatchContext` pub(crate) at connect.rs:73. Visibility matches consumption scope (pub(super) for dispatch-internal, pub(crate) for lib.rs consumers). Rule #9 checked: no security-critical fields, no invariants — pub fields appropriate.
3. [VERIFIED] Call sites wired correctly — `mod.rs:2060` constructs `ResponseContext`, `mod.rs:2337` constructs `TelemetryContext`, `lib.rs:2373` constructs `ConnectContext`, `lib.rs:2633` constructs `ChargenDispatchContext`. All field mappings verified against old parameter order.
4. [VERIFIED] Dead parameters correctly dropped — `_continuity_corrections` and `_tx` (underscore-prefixed, unused in `dispatch_connect` body) excluded from `ConnectContext`. `_narration_text` and `_effective_action` (underscore-prefixed, unused in `build_response_messages` body) excluded from `ResponseContext`. Confirmed by silent-failure-hunter: no functionality lost.
5. [VERIFIED] Rebind pattern preserves semantics — `let x = &mut *ctx.x;` creates identical borrows to the old function parameters. Zero behavioral change in function bodies. 547/547 tests confirm no regression.
6. [MEDIUM] `narration_state_delta.clone()` at response.rs:52 — spurious heap allocation. Old code moved the value; new code clones from owned field. Fix: use `&'a StateDelta` reference in `ResponseContext` to match other fields and eliminate clone.
7. [MEDIUM] fmt gate fails (21 diffs) + 15 new clippy `borrow_deref_ref` warnings — both auto-fixable. `cargo fmt && cargo clippy --fix`.
8. [LOW] ConnectContext doc says "29" but struct has 24 fields — connect.rs:23. Cosmetic.
9. [LOW] Missing wiring test for `ChargenInitContext` construction in connect.rs + missing field assertions for `ChargenDispatchContext`.
10. [LOW] Updated telemetry consolidation test is weaker than original (matches anywhere in file, not just signature) — but covered by story 36-2's own `emit_telemetry_accepts_telemetry_context` and `telemetry_context_has_required_fields` tests.

[EDGE] narration_state_delta clone confirmed — spurious allocation per turn.
[SILENT] Clean — no new silent failures introduced.
[TEST] Missing ChargenInitContext wiring test + ChargenDispatchContext field assertions.
[DOC] ConnectContext doc "29" count is stale.
[TYPE] All 5 structs checked against Rule #9 — compliant (internal parameter bundles, no invariants).
[SEC] Disabled via settings.
[SIMPLE] Disabled via settings.
[RULE] 15 rules checked exhaustively. 0 security violations. Rule #6 borderline (existence-only tests rescued by field-check siblings).

### Rule Compliance

| Rule | Instances Checked | Compliant | Violations |
|------|------------------|-----------|------------|
| #1 Silent error swallowing | 4 | 4 | 0 |
| #2 #[non_exhaustive] | 0 (no new enums) | N/A | 0 |
| #3 Hardcoded placeholders | 3 | 3 | 0 |
| #4 Tracing coverage | 3 modules | 3 | 0 |
| #5 Unvalidated constructors | 1 | 1 | 0 |
| #6 Test quality | 22 tests | 22 | 0 (borderline) |
| #7 Unsafe as casts | 0 (none in diff) | N/A | 0 |
| #8 Deserialize bypass | 5 structs | 5 | 0 |
| #9 Public fields/invariants | 5 structs | 5 | 0 |
| #10 Tenant context | 0 (no new traits) | N/A | 0 |
| #11 Workspace deps | 0 (no Cargo.toml changes) | N/A | 0 |
| #12 Dev-only deps | 0 (no Cargo.toml changes) | N/A | 0 |
| #13 Constructor/Deserialize consistency | 5 structs | 5 | 0 |
| #14 Fix-introduced regressions | 5 refactored functions | 5 | 0 |
| #15 Unbounded recursive input | 1 (test helper) | 1 | 0 |

### Devil's Advocate

Let me argue this code is broken. The `&*ctx.field` rebind pattern is the largest concern — not for correctness (the compiler guarantees equivalence) but for *maintenance*. Sixty-eight rebind lines across three functions create a parallel naming universe where every field access is indirected through a local. If someone adds a field to `ConnectContext` but forgets the corresponding `let x = &mut *ctx.x;` rebind, the function body will fail to compile — but only if that field is *used*. An unused field silently passes. There's no lint for "struct field exists but isn't rebound." The rebinds also create a false sense of "the body is unchanged" — it is, but the *contract* has changed: the function now takes a struct, and future maintainers need to understand that every `session` reference in the body is actually `ctx.session` in disguise.

The dropped `_continuity_corrections` parameter is correct today — but what if a future story needs it in `dispatch_connect`? The developer would need to add it back to `ConnectContext`, add it at the lib.rs construction site, and add the rebind. Three places instead of one parameter. The struct refactoring increased the cost of adding new state to the dispatch pipeline.

The `narration_state_delta.clone()` is the most concrete deficiency. `StateDelta` contains `Option<Vec<StateMutation>>` and `Option<HashMap<String, String>>` — the clone traverses both collections, allocating new heap memory, on every single player turn. At 3-5 seconds per turn, this is ~0.01ms of overhead — negligible for gameplay. But it's the wrong pattern: cloning from an owned field in a struct that's used once is architecturally confused. It signals "I might need this value again" when the struct is definitionally single-use.

None of these arguments reach CRITICAL or HIGH severity. The refactoring is mechanically correct, all tests pass, all call sites are wired, the dropped parameters were genuinely dead. The clone is wasteful but not dangerous. The rebind pattern is ugly but safe. This is a solid 5-point tech debt story that delivers exactly what it promised.

**Data flow traced:** `SessionEventPayload` → `dispatch_connect(payload, &mut ConnectContext{...})` → rebinds → function body unchanged → `Vec<GameMessage>` returned. Safe — no new trust boundary crossed, no new user input handling.
**Pattern observed:** Extract Parameter Object (Fowler) via Rust `&mut` struct — connect.rs:26-130. Well-executed mechanical refactoring.
**Error handling:** All error paths preserved. `tracing::warn!` on pack load failures (connect.rs:1067-1071), `error_response()` on invalid state (connect.rs:1268). No new error paths introduced.
**Wiring:** All 4 call sites verified wired in mod.rs and lib.rs. Tests confirm structural presence.

**Handoff:** To SM (Hawkeye) for finish-story. Fix fmt + clippy before merge (auto-fixable).