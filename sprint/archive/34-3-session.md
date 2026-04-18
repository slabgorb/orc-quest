---
story_id: "34-3"
jira_key: null
epic: "34"
workflow: "tdd"
---
# Story 34-3: Dice resolution engine — d20+mod vs DC, RollOutcome, seed generation

## Story Details
- **ID:** 34-3
- **Jira Key:** —
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p0
- **Epic:** 34 (3D Dice Rolling System — MVP)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-12T11:26:07Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-12T10:30:00Z | 2026-04-12T10:56:46Z | 26m 46s |
| red | 2026-04-12T10:56:46Z | 2026-04-12T11:04:20Z | 7m 34s |
| green | 2026-04-12T11:04:20Z | 2026-04-12T11:10:22Z | 6m 2s |
| spec-check | 2026-04-12T11:10:22Z | 2026-04-12T11:11:28Z | 1m 6s |
| verify | 2026-04-12T11:11:28Z | 2026-04-12T11:14:03Z | 2m 35s |
| review | 2026-04-12T11:14:03Z | 2026-04-12T11:25:14Z | 11m 11s |
| spec-reconcile | 2026-04-12T11:25:14Z | 2026-04-12T11:26:07Z | 53s |
| finish | 2026-04-12T11:26:07Z | - | - |

## Story Description

Implement the pure-function dice resolution engine in `sidequest-game/src/dice.rs`. The resolver takes a dice pool (array of `DieSpec`), a modifier, a difficulty (DC), and a seeded RNG seed, and produces a deterministic `ResolvedRoll` with individual die face results, total damage/result, and a `RollOutcome` classification.

**Key constraints:**
1. Pure function: no I/O, no wall-clock time, no shared state, no OS entropy
2. Single d20+modifier vs DC resolution model (pool support at type level; Phase 1 only uses singleton d20)
3. Crit semantics: `CritSuccess` fires iff any d20 rolls 20; `CritFail` fires iff any d20 rolls 1 (d20s unconditioned by other dice)
4. Non-d20 pools resolve on total vs DC only; outcomes are `Success` or `Fail`
5. `RollOutcome::Unknown` is wire-only (forward-compat deserialization fallback); must never be produced
6. Determinism load-bearing: same `(dice, modifier, difficulty, seed)` tuple always produces identical outcome

**Acceptance Criteria:**
- [x] `resolve_dice(dice: &[DieSpec], modifier: i32, difficulty: NonZeroU32, seed: u64) -> Result<ResolvedRoll, ResolveError>` exists and is public
- [x] Resolver uses `StdRng::seed_from_u64(seed)` (codebase convention, matches existing uses in `scenario_state.rs`, `theme_rotator.rs`, `conlang.rs`)
- [x] D20 crit detection works: any natural 20 → `CritSuccess`, any natural 1 → `CritFail`, 20 wins if both appear (2d20 edge case)
- [x] Non-d20 pools never produce crit outcomes; only `Success` or `Fail` based on `total >= difficulty`
- [x] Negative totals pass through (no clamping); e.g., 1d20 with -19 modifier vs DC 20 yields total -18
- [x] `ResolveError::UnknownDie` when any `DieSpec.sides == DieSides::Unknown`
- [x] `ResolveError::EmptyPool` when dice array is empty
- [x] Determinism validated: 100 iterations with same seed produce identical rolls; different seeds diverge
- [x] `RollOutcome` is never `Unknown` (verified by all unit tests)
- [x] Unit test coverage: DC boundaries (total==DC success, total==DC-1 fail), negative modifiers, singleton d20 crits, mixed pools, pure non-d20 pools, empty/unknown die error cases
- [x] **Wiring test in `sidequest-server/tests/dice_resolver_wiring_34_3.rs`:** constructs `DiceRequestPayload`, feeds fields to `resolve_dice`, composes `DiceResultPayload`, round-trips through serde. Proves server ↔ game ↔ protocol reachability.

## Context

**Upstream (34-2, completed):**
- Protocol types finalized: `DiceRequestPayload`, `DiceThrowPayload`, `DiceResultPayload`, `DieSpec`, `DieSides`, `DieGroupResult`, `RollOutcome`, `ThrowParams`
- Protocol crate is frozen; zero new fields can be added without ADR + version bump
- Deserialization validates: non-empty dice pool, non-zero DC, matching face count in results

**This Story (34-3):**
- Pure-function resolver: seed-driven RNG, deterministic d20+mod vs DC
- Crit rule: d20s only, unconditional on 20/1 (Keith's call 2026-04-11)
- Error handling: `UnknownDie`, `EmptyPool`
- Wiring test to verify server-layer reachability

**Downstream (34-4):**
- Dispatch integration: beat selection emits `DiceRequest`, awaits `DiceThrow`, calls `resolve_dice`, broadcasts `DiceResult`

## Guardrails

1. **Determinism is load-bearing.** Every test with a fixed seed must produce fixed face values. No `rand::rng()`, no wall-clock time inside the resolver.
2. **Single RNG source.** `StdRng::seed_from_u64` only. Do not introduce `ChaCha8Rng` or a second seeded RNG.
3. **`RollOutcome::Unknown` is wire-only.** Never produce it in server code; always assert against it in tests.
4. **No stub dispatch.** The wiring test under `sidequest-server/tests/` is mandatory; it round-trips through real protocol types, not a fake stub.
5. **Negative totals pass through.** No clamping to zero; the narrator may want to distinguish "failed by 19" from "failed by 1."

## Design Deviations

<!-- Agents: log spec deviations as they are discovered. Format: "What was changed, what the spec said, and why." -->

- **Crit rule narrowed to d20s only.** Epic spec initially said "natural max on the primary die"; Keith locked it to "any d20 rolls 20, unconditionally" on 2026-04-11. Logged here because the docstring may still reflect the broader interpretation.

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (review)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found.

**Reconciliation notes:**
- Pre-existing deviation (crit rule narrowing) is accurate: epic context line 153 says "any d20 in the pool rolls a face of 20" which matches the implementation at `dice.rs:88-91`. The `RollOutcome::CritSuccess` docstring in `message.rs:1658` still says "natural maximum on the primary die" — this is a known documentation inconsistency logged at story creation time, not a code deviation.
- TEA "no deviations" verified: all 32 tests align with ACs. Test strategy matches spec (seed-pinned determinism, brute-force seed discovery).
- Dev "no deviations" verified: function signature, error types, crit semantics, and RNG source all match the locked interface from epic context lines 119-141.
- Reviewer delivery findings (DC truncation, modifier overflow, pool size) are correctly classified as 34-4 dispatch boundary concerns, not 34-3 deviations. The resolver's spec explicitly delegates input validation to the dispatch layer (epic context line 144: "Deliberately narrower than DiceRequestPayload for testability").
- No ACs deferred — all 11 marked DONE.

## Impact Summary

**Delivery Status:** Ready for finish. All 11 acceptance criteria met. PR merged.

**Blocking Issues:** None

**Findings Count:** 3 (all non-blocking improvements for downstream 34-4 dispatch layer)

**Finding Breakdown:**
- DC truncation risk (i32::MAX boundary) — addressed by dispatch layer input validation
- Modifier overflow (unbounded addition) — dispatch layer to bound modifier range (-100..=100)
- Pool group count unbounded — dispatch layer constructs from beat definitions (bounded by design)

All findings correctly scoped to 34-4 dispatch boundary concerns. The resolver's pure-function contract explicitly delegates input validation upward (epic context line 144).

**Quality Gates:**
- 32/32 tests passing (unit + integration/wiring)
- Determinism verified (100-iteration seed sweep, identical outcomes)
- cargo clippy -D warnings clean
- cargo fmt clean
- Wiring test proves server ↔ game ↔ protocol reachability
- No `RollOutcome::Unknown` produced

**Next Steps:**
1. Proceed to story finish
2. Begin 34-4 (dispatch integration) — applies dispatch-layer input validation for findings

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (review)
- **Improvement** (non-blocking): `difficulty.get() as i32` truncates for DC > i32::MAX. Affects `crates/sidequest-game/src/dice.rs` (line 112). Dispatch layer (34-4) should validate DC is in game range before calling resolve_dice. *Found by Reviewer during review.*
- **Improvement** (non-blocking): `face_sum + modifier` has no overflow guard. Affects `crates/sidequest-game/src/dice.rs` (line 105). Dispatch layer (34-4) should bound modifier to game range (-100..=100). *Found by Reviewer during review.*
- **Improvement** (non-blocking): Pool group count is unbounded at the resolver level. Affects `crates/sidequest-game/src/dice.rs` (line 78). Dispatch layer (34-4) should cap group count before calling resolve_dice. *Found by Reviewer during review.*

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

## Tea Assessment

**Tests Required:** Yes
**Reason:** Pure-function resolver with precise determinism and crit-semantic ACs

**Test Files:**
- `crates/sidequest-game/tests/dice_resolver_story_34_3_tests.rs` — 30 unit tests covering all ACs
- `crates/sidequest-server/tests/dice_resolver_wiring_34_3.rs` — 2 integration tests (resolve + compose + serde round-trip, error handling)

**Tests Written:** 32 tests covering 11 ACs
**Status:** RED → GREEN

**Handoff:** To Naomi Nagata (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/dice.rs` — new module: `resolve_dice`, `ResolvedRoll`, `ResolveError`
- `crates/sidequest-game/src/lib.rs` — added `pub mod dice;`

**Tests:** 32/32 passing (GREEN)
**Branch:** feat/34-3-dice-resolution-engine (pushed)

**Implementation notes:**
- 113 LOC. Pure function, no dependencies beyond `rand` (workspace) and `sidequest-protocol`
- Fail-fast validation: checks all dice for `Unknown` before rolling any
- D20 crit detection scans faces during roll, not as a post-pass
- `ResolveError` has `#[non_exhaustive]`, `Display`, and `Error` impls
- `ResolvedRoll` derives `PartialEq` for test assertions

**Handoff:** To Amos Burton (TEA) for verify phase

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 11 ACs verified against implementation:
- Function signature matches locked interface from epic context (architect consultation 2026-04-11)
- Crit semantics match locked rules: d20-only, unconditional, 20-wins-ties
- `ResolveError` is `#[non_exhaustive]` per Rust review rule #2
- `StdRng::seed_from_u64` matches codebase convention (conlang.rs, scenario_state.rs, theme_rotator.rs)
- Wiring test in `sidequest-server/tests/` round-trips through real protocol types
- No scope creep: 113 LOC, zero abstractions beyond what ACs require
- Deviation subsections present for both TEA and Dev (both "no deviations")

**Decision:** Proceed to verify phase

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`dice.rs`, `lib.rs`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | Missing `pub use` re-export for dice module |
| simplify-quality | 1 finding | Missing `pub use` re-export for dice module (same) |
| simplify-efficiency | clean | No complexity issues |

**Applied:** 1 high-confidence fix — added `pub use dice::{resolve_dice, ResolveError, ResolvedRoll};` to `lib.rs`
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Quality Checks:** cargo check passes (sidequest-game + sidequest-server)
**Handoff:** To Chrisjen Avasarala (Reviewer) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | fmt violations, unused imports | Fixed during review |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (ran voluntarily — 3 delivery findings for 34-4) |
| 3 | reviewer-silent-failure-hunter | Yes | clean | No error swallowing in 123 LOC pure function — EmptyPool and UnknownDie both return Err explicitly | N/A |
| 4 | reviewer-test-analyzer | Yes | clean | 32 tests with meaningful assertions, no vacuous patterns, seed-pinned determinism | N/A |
| 5 | reviewer-comment-analyzer | Yes | clean | Doc comments accurate, crit semantics locked reference present, no stale comments | N/A |
| 6 | reviewer-type-design | Yes | findings | 4 findings (outcome invariant, serde, seed newtype, face-count) | All dismissed (over-engineering, YAGNI, wrong layer, frozen crate) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 violations (tracing, unsafe cast, test quality) | 1 dismissed (guardrail override), 2 noted |

**All received:** Yes (6 enabled returned, 3 disabled skipped)
**Total findings:** 0 confirmed, 8 dismissed (with rationale), 3 deferred (delivery findings for 34-4)

## Reviewer Assessment

**PR:** slabgorb/sidequest-api#416
**Verdict:** Approved (after mechanical fixes applied during review)

### Subagents Dispatched
- **preflight**: fmt violations, unused imports (fixed)
- **type-design**: 4 findings (all dismissed — over-engineering, YAGNI, wrong layer, frozen crate)
- **edge-hunter**: 5 findings (3 noted as delivery findings for 34-4, 2 dismissed)
- **rule-checker**: 15 rules checked, 3 violations found (1 dismissed, 2 noted)

### Findings Triage

| Finding | Tag | Decision | Rationale |
|---------|-----|----------|-----------|
| Import fmt / unused imports | [PREFLIGHT] | **Fixed** | Mechanical — applied during review |
| Missing tracing (rule #4) | [RULE] | **Dismissed** | Epic guardrail #5: "OTEL lives in dispatch layer. Pure functions stay pure." Story scope overrides lang-review rule. |
| `difficulty.get() as i32` truncation (rule #7) | [RULE] | **Delivery finding** | Real but belongs at dispatch boundary (34-4). DC values in practice are 1-30. |
| `face_sum + modifier` overflow | [TYPE] | **Delivery finding** | Dispatch layer should bound modifier range. |
| Pool group count unbounded | [TYPE] | **Delivery finding** | Dispatch layer constructs pools from beat defs — bounded by design. |
| ResolvedRoll.outcome can hold Unknown | [TYPE] | **Dismissed** | Over-engineering for Phase 1. Enforced by construction + 500-seed test sweep. |
| Missing Serialize on ResolvedRoll | [TYPE] | **Dismissed** | YAGNI. 34-4 unpacks fields into DiceResultPayload. |
| RollSeed newtype | [TYPE] | **Dismissed** | Wrong layer — server authority is dispatch concern. |
| Probabilistic diverge test | [TEST] | **Noted** | Acceptable — 0.25% spurious failure rate with 3-seed tiebreaker. |
| Wiring test doesn't pin seed=42 outcome | [TEST] | **Noted** | Wiring test purpose is reachability, not correctness. |
| No error swallowing | [SILENT] | **Clean** | EmptyPool and UnknownDie return Err explicitly, no .ok()/.unwrap_or_default() |
| Doc comments accurate | [DOC] | **Clean** | Crit semantics locked reference present, no stale comments in 123 LOC |

### Quality Gates
- 32/32 tests passing
- cargo clippy -D warnings clean
- cargo fmt clean on changed files
- Wiring test proves server → game → protocol reachability

**Handoff:** To Camina Drummer (SM) for merge and finish

## Sm Assessment

**Story 34-3 is ready for RED phase.**

- Session file created with full ACs, guardrails, and context from 34-2
- Feature branch `feat/34-3-dice-resolution-engine` created from `sidequest-api/develop`
- Upstream dependency (34-2 protocol types) is complete and frozen
- Repos: api only — pure-function resolver in `sidequest-game`, wiring test in `sidequest-server`
- No Jira key (internal tracking only)
- Workflow: TDD phased → TEA owns RED phase next
- No blockers identified