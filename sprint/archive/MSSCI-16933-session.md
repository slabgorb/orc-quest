---
story_id: "35-1"
jira_key: "MSSCI-16933"
epic: "MSSCI-16932"
workflow: "tdd"
---
# Story 35-1: Wire patch_legality into turn validator cold path

## Story Details
- **ID:** 35-1
- **Jira Key:** MSSCI-16933
- **Epic:** MSSCI-16932 (Wiring Remediation II)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/35-1-wire-patch-legality-turn-validator

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-04-09T00:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-09T00:00:00Z | - | - |

## Context

### Why
`run_legality_checks()` prevents invalid narrator state mutations (HP bounds, dead entity actions, location validity). Security-grade gap — narrator can write arbitrary HP, revive dead entities, teleport to nonexistent locations. Already has OTEL instrumentation built in.

### Approach
Wire into the cold-path `run_validator` in `turn_record.rs`, which already receives complete `TurnRecord` objects with both snapshots. This is the intended architecture per the hot-path/cold-path contract — legality checks are post-hoc detection + OTEL alerting, not gating.

### Key Files
- `sidequest-api/crates/sidequest-agents/src/turn_record.rs` — add call inside `run_validator()`
- `sidequest-api/crates/sidequest-agents/src/patch_legality.rs` — read-only, already complete

### Acceptance Criteria
1. `run_legality_checks(&record)` is called inside `run_validator()` for every TurnRecord
2. `ValidationResult::Violation` emits `WatcherEventBuilder("patch_legality", ValidationWarning)` with check name and violation text
3. Summary `WatcherEventBuilder("patch_legality", SubsystemExerciseSummary)` emitted per turn with total checks, warnings, violations
4. Integration test: TurnRecord with HP-exceeding snapshot_after triggers violation OTEL event
5. `entity_reference::check_entity_references()` is exercised transitively (already inside run_legality_checks)

### Note
`entity_reference::check_entity_references()` is already called inside `run_legality_checks()` (line 132 of `patch_legality.rs`), so this story automatically wires entity_reference validation too.

## Delivery Findings

No upstream findings at setup.

## Design Deviations

### Dev (implementation)
- No deviations from spec.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-api/crates/sidequest-agents/src/turn_record.rs` - wired run_legality_checks() into run_validator() with OTEL emission
- `sidequest-api/crates/sidequest-agents/tests/patch_legality_wiring_story_35_1_tests.rs` - TEA's 10 integration tests (added by TEA, committed together)

**Tests:** 10/10 passing (GREEN) — requires `--test-threads=1` due to shared global broadcast channel (pre-existing infrastructure concern, not story-specific)
**Branch:** feat/35-1-wire-patch-legality-turn-validator (pushed)

**Handoff:** To next phase (verify or review)

## Delivery Findings

### Dev (implementation)
- **Improvement** (non-blocking): Broadcast channel tests share a global OnceLock, causing cross-test event bleed when run in parallel. Tests pass with `--test-threads=1`. Affects `sidequest-api/crates/sidequest-telemetry/src/lib.rs` (could benefit from per-test channel isolation helper). *Found by Dev during implementation.*

## Architect Assessment

**Verdict:** PASS — all 5 ACs satisfied, no spec drift.

### AC-by-AC Verification

| AC | Status | Evidence |
|----|--------|----------|
| 1. `run_legality_checks(&record)` called for every TurnRecord | **PASS** | `turn_record.rs:153` — `let results = run_legality_checks(&record);` inside the `while let Some(record)` loop. Every record goes through it. |
| 2. Violation emits `WatcherEventBuilder("patch_legality", ValidationWarning)` with check name + violation text | **PASS** | `turn_record.rs:161-166` — builder with component `"patch_legality"`, type `ValidationWarning`, fields `check` and `violation`, severity `Warn`. |
| 3. Summary `SubsystemExerciseSummary` emitted per turn with total/warnings/violations | **PASS** | `turn_record.rs:182-187` — emits after the results loop with fields `turn_id`, `total_checks`, `violations`, `warnings`. |
| 4. Integration test: HP-exceeding snapshot triggers violation OTEL event | **PASS** | Test `ac4_integration_hp_violation_through_full_pipeline` — NPC with HP 30 > max 15, verifies ValidationWarning event arrives on broadcast channel. Full pipeline: mpsc → run_validator → run_legality_checks → check_hp_bounds → WatcherEventBuilder → global channel. |
| 5. `entity_reference::check_entity_references()` exercised transitively | **PASS** | `patch_legality.rs:131` already includes `check_entity_references` in the checks vec. Test `ac5_entity_reference_check_exercised_through_validator` confirms narration with unknown "Grimjaw" produces warning through the full pipeline. |

### Architecture Alignment

- **Cold-path contract (ADR-031):** Preserved. Legality checks run inside `run_validator()` which is the cold-path consumer. No hot-path impact.
- **OTEL principle:** Both per-violation and per-turn summary events emitted. GM panel can distinguish individual violations from aggregate health.
- **No silent fallbacks:** Violations emit `Severity::Warn` — visible in telemetry. No silent swallowing.
- **Minimal scope:** Only `turn_record.rs` modified (14 lines of new code). `patch_legality.rs` untouched as specified.
- **Wiring verified:** `run_legality_checks` now has a non-test production consumer in `run_validator()`.

### Non-blocking Finding

- **Test isolation:** Tests require `--test-threads=1` due to shared global broadcast channel. Pre-existing infra concern (not introduced by this story). Dev already documented this. Consider a `TestChannelGuard` helper for future telemetry tests — but not in scope for 35-1.
