---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-1: Extract Threshold Helper + EdgePool Type

## Business Context

Foundation story for Epic 39. Introduces the `EdgePool` type that will replace phantom
HP as the first-class combat currency, and extracts the threshold-crossing detection
logic out of `resource_pool.rs` into a shared helper so both `ResourcePool` and the new
`EdgePool` mint LoreFragments via the same path. No engine wiring, no behavior change —
pure type plumbing plus a refactor that pays down duplication before it spreads.

This story unblocks 39-2 (delete HP) and 39-4 (dispatch wiring). It is safe in isolation:
no caller consumes `EdgePool` yet, and the extracted helper is called from the same
places `resource_pool.rs` already called its private equivalents.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** New code must have non-test consumers.
2. **Every Test Suite Needs a Wiring Test.** At least one integration test per suite.
3. **No Silent Fallbacks.** Fail loudly on missing/unexpected inputs.
4. **No Stubbing.** No placeholder modules, no skeleton code.
5. **Don't Reinvent — Wire Up What Exists.** Check the codebase first.

### Key Files

| File | Action |
|------|--------|
| `sidequest-api/crates/sidequest-game/src/thresholds.rs` | **New.** `detect_crossings<T: ThresholdAt>` + `mint_threshold_lore` |
| `sidequest-api/crates/sidequest-game/src/resource_pool.rs` | Move private `detect_crossings`/`mint_threshold_lore` to `thresholds.rs`; call via shared API |
| `sidequest-api/crates/sidequest-game/src/creature_core.rs` | Add `EdgePool`, `EdgeThreshold`, `RecoveryTrigger` types; **do NOT add `edge` field to `CreatureCore` yet** (that lands in 39-2) |
| `sidequest-api/crates/sidequest-game/src/lib.rs` | `pub mod thresholds;` |

### Patterns

- `EdgePool::apply_delta(&mut self, delta: i32) -> DeltaResult` with `crossed: Vec<EdgeThreshold>`
- Reuse the DeltaResult/crossed shape already used by `ResourcePool::apply_and_clamp`
- `ThresholdAt` trait with a single `at(&self) -> i32` method (sealed/unsealed — whatever matches ResourcePool's current pattern)
- `RecoveryTrigger::OnBeatSuccess { beat_id, amount, while_strained: bool }` — `while_strained = current <= max/4`
- All types derive `Serialize, Deserialize, Debug, Clone, PartialEq`

### Dependencies

- None. Foundation story.

## Scope Boundaries

**In scope:**
- `EdgePool`, `EdgeThreshold`, `RecoveryTrigger` types in `creature_core.rs`
- `thresholds.rs` module with shared helpers
- Refactor `resource_pool.rs` to call the shared helpers (no behavior change)
- Unit tests: `EdgePool::apply_delta` debit, refill, clamp-at-max, threshold crossings,
  `current == 0` threshold fires
- One wiring test: `ResourcePool` still mints threshold lore identically after refactor
  (regression gate on the extraction)

**Out of scope:**
- `CreatureCore.edge` field (39-2)
- Deleting `hp/max_hp/ac` (39-2)
- `BeatDef` extensions (39-4)
- Any dispatch/engine wiring

## AC Context

**AC1: `EdgePool` compiles with required fields**
- `current`, `max`, `base_max: i32`; `recovery_triggers: Vec<RecoveryTrigger>`;
  `thresholds: Vec<EdgeThreshold>`
- Serde round-trip test passes

**AC2: `apply_delta` debits correctly**
- Positive delta increases `current` (capped at `max`)
- Negative delta decreases `current` (floored at 0 — do NOT go negative)
- Returns `DeltaResult { new_current, crossed }` mirroring ResourcePool shape

**AC3: Threshold crossings fire on direction-correct transitions**
- Crossing `at=1` while decreasing fires the `edge_strained` event
- Crossing `at=0` while decreasing fires the `composure_break` event
- Non-crossing deltas (current=5, delta=-1, no thresholds between 5 and 4) fire nothing

**AC4: `thresholds.rs` helpers are the single source of truth**
- `ResourcePool::apply_and_clamp` calls `thresholds::detect_crossings` — not a private copy
- Existing ResourcePool tests still pass (wiring/regression test)

**AC5: No wiring leakage**
- No reference to `EdgePool` in `dispatch/`, `server/`, or `CreatureCore` struct body
- Grep-proof: `EdgePool` appears only in `creature_core.rs` and tests

## Assumptions

- `ResourcePool` already has private `detect_crossings`/`mint_threshold_lore` functions (verify before extraction; if the names differ, match the existing helper naming)
- The extraction is a mechanical refactor — behavior of existing threshold-minting is preserved bit-for-bit
- `LoreFragment` minting signature doesn't change
