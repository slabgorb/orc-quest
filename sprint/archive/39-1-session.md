---
story_id: "39-1"
jira_key: "none"
epic: "39"
workflow: "wire-first"
---
# Story 39-1: Extract Threshold Helper + EdgePool Type

## Story Details
- **ID:** 39-1
- **Jira Key:** none (personal project)
- **Workflow:** wire-first
- **Epic:** 39 — Edge / Composure Combat, Mechanical Advancement, and Push-Currency Rituals
- **Repository:** sidequest-api (Rust backend)
- **Branch:** feat/39-1-threshold-edgepool
- **Points:** 5
- **Priority:** p1
- **Status:** in-progress

## Context

Epic 39 implements first-class composure currency (EdgePool) to replace phantom HP, hard-links advancement effects to the engine, and extends beat dispatch with push-currency spellcraft. Story 39-1 is the foundation: extract shared threshold-crossing detection from `resource_pool.rs` and introduce the `EdgePool` type and related structures (`EdgeThreshold`, `RecoveryTrigger`). No engine wiring, no behavior change — pure type plumbing plus a refactor that pays down duplication before it spreads across other stories in the epic.

This story unblocks:
- **39-2** (delete HP from CreatureCore)
- **39-4** (dispatch wiring with edge_delta)

It is safe in isolation: no caller consumes `EdgePool` yet, and the extracted threshold helper is called from the same places `resource_pool.rs` already called its private equivalents.

### Key Guardrails (CLAUDE.md Mandatory)

1. **Verify Wiring, Not Just Existence.** New code must have non-test consumers.
2. **Every Test Suite Needs a Wiring Test.** At least one integration test per suite.
3. **No Silent Fallbacks.** Fail loudly on missing/unexpected inputs.
4. **No Stubbing.** No placeholder modules, no skeleton code.
5. **Don't Reinvent — Wire Up What Exists.** Check the codebase first.

## Acceptance Criteria

**AC1: `EdgePool` compiles with required fields**
- `current`, `max`, `base_max: i32`
- `recovery_triggers: Vec<RecoveryTrigger>`
- `thresholds: Vec<EdgeThreshold>`
- All types derive `Serialize, Deserialize, Debug, Clone, PartialEq`
- Serde round-trip test passes

**AC2: `apply_delta` debits correctly**
- Positive delta increases `current` (capped at `max`)
- Negative delta decreases `current` (floored at 0)
- Returns `DeltaResult { new_current, crossed }` mirroring ResourcePool shape

**AC3: Threshold crossings fire on direction-correct transitions**
- Crossing `at=1` while decreasing fires the `edge_strained` event
- Crossing `at=0` while decreasing fires the `composure_break` event
- Non-crossing deltas fire nothing

**AC4: `thresholds.rs` helpers are the single source of truth**
- `ResourcePool::apply_and_clamp` calls `thresholds::detect_crossings` — not a private copy
- Existing ResourcePool tests still pass (wiring/regression test)

**AC5: No wiring leakage**
- No reference to `EdgePool` in `dispatch/`, `server/`, or `CreatureCore` struct body
- Grep-proof: `EdgePool` appears only in `creature_core.rs` and tests

## Implementation Plan

### Phase 1: Examine Existing ResourcePool Helpers
- Read `sidequest-api/crates/sidequest-game/src/resource_pool.rs`
- Identify private `detect_crossings` and `mint_threshold_lore` functions
- Note the signature and behavior (especially the DeltaResult shape)

### Phase 2: Create thresholds.rs Module
- New file: `sidequest-api/crates/sidequest-game/src/thresholds.rs`
- Extract `detect_crossings<T: ThresholdAt>` — parameterized over threshold providers
- Extract `mint_threshold_lore` with identical behavior
- Define `ThresholdAt` trait with single `at(&self) -> i32` method
- Add helper: `fn apply_and_threshold<T>(current: i32, delta: i32, max: i32, thresholds: &[T]) -> DeltaResult`

### Phase 3: Create EdgePool and Related Types
- In `sidequest-api/crates/sidequest-game/src/creature_core.rs`, add:
  - `EdgePool` struct
  - `EdgeThreshold` struct
  - `RecoveryTrigger` enum with variants: `OnResolution`, `OnBeatSuccess { beat_id, amount, while_strained }`, `OnAllyRescue`
- Implement `EdgePool::apply_delta(&mut self, delta: i32) -> DeltaResult`
- Use the shared threshold helper from Step 2

### Phase 4: Refactor ResourcePool to Use Shared Helpers
- Replace private `detect_crossings`/`mint_threshold_lore` calls with public imports from `thresholds.rs`
- No behavior change — verify all existing ResourcePool tests still pass

### Phase 5: Write Tests
- Unit tests for `EdgePool::apply_delta`: debit, refill, clamp-at-max, threshold crossings, zero-current fires threshold
- Unit tests for shared threshold helper with multiple threshold types
- Integration test: verify `ResourcePool` behavior unchanged after refactor (wiring regression test)
- Serde round-trip test for `EdgePool`

### Phase 6: Update lib.rs
- Add `pub mod thresholds;` to `sidequest-api/crates/sidequest-game/src/lib.rs`

## Key Files

| File | Action |
|------|--------|
| `sidequest-api/crates/sidequest-game/src/thresholds.rs` | **New.** `detect_crossings<T: ThresholdAt>` + `mint_threshold_lore` |
| `sidequest-api/crates/sidequest-game/src/resource_pool.rs` | Move private helpers to `thresholds.rs`; call via shared API |
| `sidequest-api/crates/sidequest-game/src/creature_core.rs` | Add `EdgePool`, `EdgeThreshold`, `RecoveryTrigger` types |
| `sidequest-api/crates/sidequest-game/src/lib.rs` | `pub mod thresholds;` |

## Dependencies

- None. Foundation story.

## Out of Scope

- `CreatureCore.edge` field (lands in 39-2)
- Deleting `hp/max_hp/ac` (39-2)
- `BeatDef` extensions (39-4)
- Any dispatch/engine wiring
- Advancement effects (39-5)

## Assumptions

- `ResourcePool` already has private `detect_crossings`/`mint_threshold_lore` functions (verify before extraction)
- The extraction is a mechanical refactor — behavior of existing threshold-minting is preserved bit-for-bit
- `LoreFragment` minting signature doesn't change

## Workflow Phases

| Phase | Owner | Status |
|-------|-------|--------|
| setup | sm | done |
| dev | dev | pending |
| tea | tea | pending |
| review | reviewer | pending |

## Workflow Tracking

**Workflow:** wire-first
**Phase:** finish
**Phase Started:** 2026-04-19T08:26:39Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-19T15:00Z | — | — |

## Sm Assessment

Foundation story for Epic 39 (Edge/Composure combat). Pure type plumbing + mechanical refactor: extract `detect_crossings`/`mint_threshold_lore` from `resource_pool.rs` into a new shared `thresholds.rs` module, introduce `EdgePool`/`EdgeThreshold`/`RecoveryTrigger` types in `creature_core.rs`. No engine wiring yet — 39-2 (HP delete) and 39-4 (dispatch) depend on this.

Wire-first workflow: TEA writes the failing wiring/unit tests against the shared helper and EdgePool serde/apply_delta behavior, then Dev implements. AC5 (grep-proof no wiring leakage) is the gate against premature integration.

Risks: `mint_threshold_lore` signature must be preserved bit-for-bit during extraction (ResourcePool regression risk). Threshold helper must be generic over a `ThresholdAt` trait so both pools can share it.

Handing off to Amos Burton (TEA) for red phase.

## TEA Assessment

**Tests Required:** Yes
**Phase:** finish

**Test File:**
- `sidequest-api/crates/sidequest-game/tests/edge_pool_story_39_1_tests.rs` — 17 tests covering ACs 1–4, plus thresholds-module reachability (AC4 wiring).

**Tests Written:** 17 tests covering 4 ACs
**Status:** RED — confirmed via `cargo test -p sidequest-game --test edge_pool_story_39_1_tests --no-run`. Compile fails on:
- `sidequest_game::creature_core::{DeltaResult, EdgePool, EdgeThreshold, RecoveryTrigger}` unresolved
- `sidequest_game::thresholds` module unresolved
These are exactly the symbols Dev must introduce to turn the suite green.

### AC Coverage

| AC | Tests | Notes |
|----|-------|-------|
| AC1 EdgePool compiles + serde | `edge_pool_has_required_fields`, `edge_pool_serde_round_trip`, `recovery_trigger_on_beat_success_carries_all_fields` | Pins every field and every RecoveryTrigger variant |
| AC2 apply_delta debits | `apply_delta_positive_caps_at_max`, `apply_delta_negative_floors_at_zero`, `apply_delta_zero_is_noop`, `apply_delta_returns_delta_result_shape` | Last test compile-pins `DeltaResult { new_current, crossed }` field names |
| AC3 crossings | `crossing_at_one_while_decreasing_fires_edge_strained`, `crossing_at_zero_while_decreasing_fires_composure_break`, `non_crossing_delta_fires_nothing`, `ascending_delta_does_not_fire_downward_threshold`, `single_delta_crossing_multiple_thresholds_fires_all`, `threshold_already_below_does_not_re_fire` | Downward-only semantics + multi-threshold single-delta |
| AC4 shared helper single source of truth | `resource_pool_still_mints_lore_after_extraction`, `resource_pool_decay_path_still_works_after_extraction`, `thresholds_module_is_publicly_accessible` | Guards both ResourcePool call sites (`apply_resource_patch` + `apply_pool_decay`); final test forces `pub mod thresholds;` in lib.rs |
| AC5 no wiring leakage | N/A — grep-verifiable by Reviewer | Test file itself does not import EdgePool from `dispatch/` or `server/`; real enforcement is reviewer grep |

### Rule Coverage

| CLAUDE.md Rule | Test(s) | Status |
|---|---|---|
| Verify wiring, not just existence | `resource_pool_still_mints_lore_after_extraction`, `resource_pool_decay_path_still_works_after_extraction` | failing (RED) |
| Every test suite has a wiring test | `thresholds_module_is_publicly_accessible` + the two regression tests above | failing (RED) |
| No silent fallbacks | `apply_delta_negative_floors_at_zero` (explicit floor, not silent NaN), `non_crossing_delta_fires_nothing` (no spurious fire) | failing (RED) |
| Composition type plumbing (no stubbing) | Serde round-trip forces real types, not empty shells | failing (RED) |

**Self-check:** No vacuous tests. Every test has at least one `assert_eq!`/`assert!`/`assert_matches!` against meaningful state. No `let _ = result;` patterns. The two compile-pin tests (`apply_delta_returns_delta_result_shape`, `thresholds_module_is_publicly_accessible`) carry their assertion in the type system (the `let _: Vec<EdgeThreshold> = ...` binding fails to compile if the shape is wrong) — documented so the reviewer doesn't mistake them for no-ops.

### Design Decisions Pinned by Tests

- `EdgePool` fields: `current: i32, max: i32, base_max: i32, recovery_triggers: Vec<RecoveryTrigger>, thresholds: Vec<EdgeThreshold>` — pinned by the struct-literal constructor in tests.
- `EdgeThreshold` shape: `{ at: i32, event_id: String, narrator_hint: String }` — pinned by `strained_at`/`break_at` helpers.
- `RecoveryTrigger` enum: `OnResolution | OnAllyRescue | OnBeatSuccess { beat_id, amount: i32, while_strained: bool }` — pinned by serde round-trip.
- `DeltaResult { new_current: i32, crossed: Vec<EdgeThreshold> }` — pinned by explicit type annotations.
- `pub mod thresholds;` in `sidequest-game/src/lib.rs` — pinned by reachability test.

### Notes for Dev (Naomi)

- Fixture: `make_pool_with_thresholds` helper in `resource_threshold_knownfact_story_16_11_tests.rs` shows the existing ResourcePool construction pattern — mirror for EdgePool.
- The shared `thresholds::detect_crossings` must be generic over the threshold type's value (ResourceThreshold carries `at: f64`, EdgeThreshold carries `at: i32`). A `ThresholdAt` trait with an associated `Value: PartialOrd + Copy` type is the cleanest path; alternative: two typed helpers that share a private inner function. Either satisfies AC4 — the tests only require that `ResourcePool` and `EdgePool` produce identical behavior, and that `sidequest_game::thresholds` is a real public module.
- `mint_threshold_lore` currently takes `&[ResourceThreshold]`. To share across pool types, it either needs to become generic over a trait that exposes `event_id` and `narrator_hint`, OR stay typed and each pool calls its own minter. The AC4 regression test only pins the ResourcePool side — the EdgePool side is tested through `apply_delta` returning the right `crossed` vec, not through lore minting.
- AC5 grep: ensure `grep -R "EdgePool" sidequest-api/crates/sidequest-server/ sidequest-api/crates/sidequest-game/src/dispatch/` returns nothing, and that `CreatureCore`'s struct body remains HP-only (edge field is 39-2's work).

**Handoff:** To Naomi Nagata (Dev) for green phase.

## Dev Assessment

**Phase:** finish → review
**Status:** GREEN — all 16 story tests pass, all 11 ResourcePool + 16-11 regression tests pass, full crate builds clean.

### Implementation Summary

| File | Change |
|------|--------|
| `crates/sidequest-game/src/thresholds.rs` | **New.** `ThresholdAt` trait with associated `Value: PartialOrd + Copy`; generic `detect_crossings<T>`; generic `mint_threshold_lore<T>`. Shared helpers both ResourcePool (f64) and EdgePool (i32) route through. |
| `crates/sidequest-game/src/creature_core.rs` | Added sibling types: `EdgeThreshold` (impl ThresholdAt<Value=i32>), `RecoveryTrigger` (OnResolution / OnAllyRescue / OnBeatSuccess{beat_id, amount, while_strained}), `DeltaResult{new_current, crossed}`, `EdgePool` with `apply_delta(delta: i32) -> DeltaResult` using `saturating_add` + `clamp(0, max)`. `CreatureCore` struct body untouched — no `edge` field (39-2's work). |
| `crates/sidequest-game/src/resource_pool.rs` | `ResourceThreshold` implements `ThresholdAt<Value=f64>`. Private `detect_crossings` removed; both call sites (`apply_and_clamp`, `apply_pool_decay`) call `thresholds::detect_crossings`. `mint_threshold_lore` public API preserved as a thin wrapper over `thresholds::mint_threshold_lore` (keeps 16-11 tests green). |
| `crates/sidequest-game/src/lib.rs` | Added `pub mod thresholds;`. |

### AC Status

| AC | Status | Evidence |
|----|--------|----------|
| AC1 EdgePool + serde | ✅ | `edge_pool_has_required_fields`, `edge_pool_serde_round_trip`, `recovery_trigger_on_beat_success_carries_all_fields` pass |
| AC2 apply_delta debits | ✅ | 4 apply_delta tests pass; `saturating_add` prevents overflow, `clamp(0, max)` enforces floor/cap |
| AC3 crossings direction-correct | ✅ | 6 crossing tests pass — downward only, multi-threshold single-delta, threshold-at-current holds |
| AC4 shared helper single source | ✅ | `resource_pool_still_mints_lore_after_extraction` + `resource_pool_decay_path_still_works_after_extraction` + `thresholds_module_is_publicly_accessible` all pass; private `detect_crossings` no longer exists in resource_pool.rs |
| AC5 no wiring leakage | ✅ | `grep -rn EdgePool crates/sidequest-server/ crates/sidequest-game/src/` → only matches `creature_core.rs` struct and impl. No dispatch/server references. |

### Regression

- `resource_pool_story_16_10_tests` + `resource_threshold_knownfact_story_16_11_tests`: **11/11 pass** — threshold-to-LoreFragment pipeline behaviourally unchanged.
- `wire_genre_resources_story_16_12_tests`: **30/41 fail** — pre-existing environment issue. Local `sidequest-content/genre_packs/` is missing `neon_dystopia`, `pulp_noir`, `road_warrior`, `low_fantasy`, and `victoria` packs. Tests fail with `No such file or directory` on `rules.yaml` load, not on any threshold/pool behaviour. Would fail identically on `develop`. Not caused by this story.

### Design Notes

- `ThresholdAt` uses an associated type rather than a generic parameter so `detect_crossings<T: ThresholdAt>(&[T], T::Value, T::Value)` resolves cleanly without extra generics at call sites.
- `mint_threshold_lore` is re-exported through a wrapper in `resource_pool` to preserve the existing public API consumed by 16-11 tests — keeps the refactor invisible to callers.
- `EdgePool::apply_delta` uses `saturating_add` before clamping to `[0, max]`. This avoids i32 overflow on pathological deltas (e.g., `i32::MIN`) without changing observable behaviour for normal values.
- `base_max` is distinct from `max` so 39-4/39-5 can temporarily reduce `max` (e.g., exhaustion) while `base_max` remains the recovery ceiling.

### Design Deviations

See `## Design Deviations → ### Dev (implementation)` — none.

**Handoff:** To Chrisjen Avasarala (Reviewer) for review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|------------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 code smells, 534+/39-, 5 files | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 9 (4 high, 3 medium, 2 informational) | 2 fixed (non_exhaustive, silent add); 7 scoped out (invariant/authoring concerns inherited or for 39-4+, tracked in Delivery Findings) |
| 3 | reviewer-rule-checker | Yes | findings | 3 high | All 3 addressed: #[non_exhaustive] on RecoveryTrigger (applied), tracing::warn on LoreStore Err (applied), OTEL on apply_delta (scoped to 39-4 per rule-checker's own note) |
| 4 | reviewer-type-design | Yes | findings | 4 (1 high, 1 medium, 2 low) | Stringly-typed event_id/beat_id (high) and EdgePool serde validation (medium) tracked as Delivery Findings for later stories — both pre-exist on ResourceThreshold and are broader than 39-1 scope; sealed trait (low) and shared generic DeltaResult (low) dismissed |
| 5 | reviewer-silent-failure-hunter | Yes | findings | 3 (2 medium, 1 low) | `store.add` swallow (medium) — fixed via `tracing::warn!`. Set-op silent clamp (medium) and HP-delta return type (low) — pre-existing ResourcePool/CreatureCore issues, out of scope; tracked |
| 6 | reviewer-test-analyzer | Yes | findings | 5 (4 medium, 1 low) | Wiring test upgrade to real function call — applied. Overflow, re-fire-below-zero, mint duplicate tests — valuable but additive; current suite pins every AC; tracked for follow-up |
| 7 | reviewer-comment-analyzer | Yes | findings | 2 (1 high, 1 medium) | Both applied: resource_pool.rs:107 docstring updated to reflect tracing::warn! behavior (no longer claims "silently skipped"); creature_core.rs module doc extended to mention the 39-1 EdgePool additions |

**All received: Yes**

## Reviewer Assessment

**Verdict:** APPROVED
**Phase:** finish → finish

### Verification

| Check | Result |
|-------|--------|
| `cargo clippy -p sidequest-game --all-targets -- -D warnings` | ✅ clean |
| `cargo fmt -p sidequest-game --check` | ✅ clean (after module-order fix commit d49ae8e) |
| `cargo test -p sidequest-game --lib` | ✅ 491/491 passing |
| `cargo test -p sidequest-game --test edge_pool_story_39_1_tests` | ✅ 16/16 passing |
| `cargo test -p sidequest-game --test resource_pool_story_16_10_tests` | ✅ passing (regression) |
| `cargo test -p sidequest-game --test resource_threshold_knownfact_story_16_11_tests` | ✅ 11/11 passing (regression) |

### AC Audit

- **AC1 (EdgePool + serde):** Struct derives `Debug, Clone, PartialEq, Serialize, Deserialize` as required. Round-trip test covers all RecoveryTrigger variants including the struct variant.
- **AC2 (apply_delta):** `saturating_add` + `clamp(0, max)` is the right construction — overflow-safe, and the floor/cap semantics match the spec. Tests pin cap, floor, zero-delta, and the DeltaResult field names via explicit type annotations.
- **AC3 (crossings):** Downward-only semantics delegated to `thresholds::detect_crossings` (`old > at && new <= at`). Multi-threshold single-delta path covered. "At-or-below and holding" correctly does not re-fire.
- **AC4 (shared helper single source of truth):** `resource_pool.rs` private `detect_crossings` is gone — both call sites (`apply_and_clamp`, `apply_pool_decay`) route through `thresholds::detect_crossings`. `mint_threshold_lore` is a thin wrapper preserving the 16-11 public API. The 16-10/16-11 regression tests prove bit-identical behavior.
- **AC5 (no wiring leakage):** `grep -rn EdgePool crates/sidequest-server/ crates/sidequest-game/src/` shows only `creature_core.rs:161` (struct) and `creature_core.rs:175` (impl). No dispatch or server references. `CreatureCore` struct body is unchanged — no `edge` field added.

### Quality Notes

- `ThresholdAt` trait uses an associated type for the value (f64 vs i32), which is exactly right — avoids extra generics bleeding into call sites. The generic `detect_crossings<T: ThresholdAt + Clone>` is tight.
- `EdgePool::apply_delta` uses `saturating_add` before clamping — guards against `i32::MIN`-style pathological deltas without changing observable behavior for normal values. Appropriate belt-and-suspenders for a foundation type that other stories will feed untrusted deltas into.
- `base_max` is declared but not yet consumed — that is *intentional* per scope (recovery semantics land in 39-4/39-5). Comment on the field documents why. Acceptable.
- `mint_threshold_lore` being a wrapper avoids breaking 16-11 tests and keeps the refactor invisible to callers. Clean migration path.
- No use of `unsafe`, no `unwrap()` on fallible paths, no `panic!`. No silent fallbacks. No stubs. Wiring test for the thresholds module presence is included (pins `pub mod thresholds;`).

### CLAUDE.md Rule Compliance

- ✅ No silent fallbacks — all paths explicit, no `Result::ok()` swallowing.
- ✅ No stubbing — every type and function is fully implemented; `base_max` is a real field that the next stories will consume.
- ✅ Don't reinvent — reuses `ResourceThreshold`/`LoreFragment`/`LoreStore` infrastructure via the shared trait.
- ✅ Verify wiring, not just existence — both ResourcePool call sites rewired to the shared helper; test suite includes regression + module-reachability wiring tests.
- ✅ Every test suite has a wiring test — `resource_pool_still_mints_lore_after_extraction`, `resource_pool_decay_path_still_works_after_extraction`, `thresholds_module_is_publicly_accessible`.

### Specialist Incorporation

- **[RULE]** `#[non_exhaustive]` added to `RecoveryTrigger` (creature_core.rs:129). `tracing::warn!` replaces silent `let _ = store.add(...)` in `thresholds::mint_threshold_lore`. OTEL on `EdgePool::apply_delta` noted as a 39-4 AC (not a 39-1 violation — dispatch wiring doesn't land here).
- **[SILENT]** The `store.add` swallow is no longer silent — replaced with `tracing::warn!` including event_id + turn + error. Pre-existing `apply_and_clamp` Set-op silent-clamp and `apply_hp_delta` bare return are out of scope; tracked in Delivery Findings.
- **[TYPE]** Stringly-typed `event_id`/`beat_id` (high confidence) and `EdgePool` Deserialize invariant validation (medium) are both real improvements but broader than 39-1 — they also affect pre-existing `ResourceThreshold`. Tracked in Delivery Findings for a follow-up story. Sealed `ThresholdAt` and shared generic `DeltaResult<T>` dismissed as over-engineering for the current call-site count.
- **[TEST]** `thresholds_module_is_publicly_accessible` upgraded from compile-only to an actual `detect_crossings::<EdgeThreshold>` call with an `assert_eq!` on the returned vec. Additional suggestions (i32::MIN overflow, re-fire-below-zero, mint duplicate coverage) are valuable but additive; current 16-test suite pins every AC and the three CLAUDE.md wiring-test rules. Tracked for follow-up.
- **[DOC]** `resource_pool.rs` wrapper docstring updated to reflect the new `tracing::warn!` behavior (was still claiming "silently skipped"). `creature_core.rs` module doc extended to mention the 39-1 `EdgePool` type family additions so readers don't mistake the file for a 1-13-only extraction.

### Risks / Watch Items

- None blocking. Clean foundation for 39-2 (HP delete + EdgePool field on CreatureCore) and 39-4 (BeatDef edge_delta).
- Pre-existing failures in `wire_genre_resources_story_16_12_tests` are missing-genre-pack environment issues, confirmed unrelated to this story — already flagged in Dev's Delivery Findings.

**Handoff:** To Camina Drummer (SM) for finish phase — approved for merge.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- **Improvement** (non-blocking): Several genre pack directories are missing from the local `sidequest-content` clone (`neon_dystopia`, `pulp_noir`, `road_warrior`, `low_fantasy`, `victoria`), breaking `wire_genre_resources_story_16_12_tests` (30/41 fail). Pre-existing, not caused by 39-1. Affects `sidequest-content/genre_packs/` (sync or regenerate missing packs). *Found by Dev during green.*

### Reviewer (review)
- **Improvement** (non-blocking): `event_id` and `beat_id` are raw `String` across `EdgeThreshold`, `ResourceThreshold`, and `RecoveryTrigger::OnBeatSuccess`. Typos fail silently at runtime (LoreStore dedup / dispatch no-match). Newtype candidates: `EventId`, `BeatId` with validated constructors. Affects `crates/sidequest-game/src/creature_core.rs`, `crates/sidequest-game/src/resource_pool.rs`. *Found by Reviewer during review.*
- **Improvement** (non-blocking): `EdgePool` derives `Deserialize` with no invariant checks — a payload with `current > max` or `max > base_max` is structurally accepted and stays corrupted until first `apply_delta`. Consider `#[serde(try_from = "EdgePoolRaw")]` with invariant validation. Same concern applies pre-existing to `ResourcePool`. Affects `crates/sidequest-game/src/creature_core.rs`, `crates/sidequest-game/src/resource_pool.rs`. *Found by Reviewer during review.*
- **Improvement** (non-blocking): `ResourcePool::apply_and_clamp` silently clamps `Set` operations with no signal in `ResourcePatchResult`. Callers cannot distinguish "value honored" from "value truncated." Pre-existing, not 39-1. Affects `crates/sidequest-game/src/resource_pool.rs`. *Found by Reviewer during review.*
- **Gap** (non-blocking for 39-1, **must be AC for 39-4**): `EdgePool::apply_delta` is a subsystem decision point (clamps, detects crossings, produces DeltaResult). Per project OTEL principle, 39-4 (dispatch wiring) must add a `creature.edge_delta` watcher event before going green. Not a 39-1 violation because dispatch wiring doesn't land until 39-4. Affects `crates/sidequest-game/src/creature_core.rs` (apply_delta). *Found by Reviewer during review.*
- **Improvement** (non-blocking): `ResourceThreshold.at: f64` — NaN silently becomes a permanently inert threshold via `PartialOrd` semantics. Pre-existing pool concern, not introduced by 39-1. Affects `crates/sidequest-game/src/resource_pool.rs`. *Found by Reviewer during review.*
- **Improvement** (non-blocking): Test coverage additions that would strengthen the suite: (a) `apply_delta` with `delta=i32::MIN` and `current=i32::MAX`, (b) pool already at 0 with further negative delta (re-fire clamp scenario), (c) duplicate-event_id mint behavior. Affects `crates/sidequest-game/tests/edge_pool_story_39_1_tests.rs`. *Found by Reviewer during review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (review)
- No deviations from spec.