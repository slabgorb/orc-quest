---
story_id: 28-2
jira_key: pending
epic: "28"
epic_jira_key: pending
workflow: tdd
---

# Story 28-2: OTEL for StructuredEncounter — instrument apply_beat, metric changes, resolution

## Story Details
- **ID:** 28-2
- **Jira Key:** pending
- **Epic:** 28 (Unified Encounter Engine)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p0

## Story Summary

Before routing real traffic through StructuredEncounter, make it observable. Add
sidequest-telemetry dependency to sidequest-game (only 2 emissions exist today, both
in persistence.rs). Instrument:

- `apply_beat()` — beat_id, metric before/after, phase transition, resolved
- metric threshold checks
- phase transitions
- escalation triggers

OTEL events:
- `encounter.beat_applied` (encounter_type, beat_id, stat_check, metric_before, metric_after, phase)
- `encounter.resolved` (encounter_type, beats_total, outcome)
- `encounter.phase_transition` (encounter_type, old_phase, new_phase)
- `encounter.escalated` (from_type, to_type)

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-07T11:50:07Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-07T11:18:32Z | 2026-04-07T11:19:56Z | 1m 24s |
| red | 2026-04-07T11:19:56Z | 2026-04-07T11:27:19Z | 7m 23s |
| green | 2026-04-07T11:27:19Z | 2026-04-07T11:39:36Z | 12m 17s |
| spec-check | 2026-04-07T11:39:36Z | 2026-04-07T11:40:42Z | 1m 6s |
| verify | 2026-04-07T11:40:42Z | 2026-04-07T11:44:06Z | 3m 24s |
| review | 2026-04-07T11:44:06Z | 2026-04-07T11:48:43Z | 4m 37s |
| spec-reconcile | 2026-04-07T11:48:43Z | 2026-04-07T11:50:07Z | 1m 24s |
| finish | 2026-04-07T11:50:07Z | - | - |

## Delivery Findings

### TEA (test design)
- **Improvement** (non-blocking): sidequest-telemetry dependency already exists in sidequest-game/Cargo.toml. AC "Telemetry dep" is pre-satisfied. Affects `sidequest-game/Cargo.toml` (no change needed). *Found by TEA during test design.*
- No other upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): `emit()` in sidequest-telemetry silently drops events when global channel is uninitialized — no log, no indication. Not introduced by this diff, but all new OTEL call sites route through it. Affects `sidequest-telemetry/src/lib.rs` (add once-per-process warn log in None arm). *Found by Reviewer during code review.*
- No other upstream findings during code review.

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No additional deviations found. TEA and Dev entries are accurate.

### Architect (reconcile)
- No additional deviations found. TEA reported no deviations, Dev reported no deviations, Reviewer confirmed alignment. Story context ACs match implementation 1:1. No AC deferrals. No sibling story impact concerns — 28-12 extends this pattern to remaining game crate modules but has no dependency on specific field names or event structures established here.

## Acceptance Criteria

| AC | Detail | Verification |
|----|--------|--------------|
| Telemetry dep | sidequest-game/Cargo.toml lists sidequest-telemetry | Grep sidequest-game/Cargo.toml for "sidequest-telemetry" |
| apply_beat OTEL | Every apply_beat() emits encounter.beat_applied | Grep WatcherEventBuilder with "beat_applied" in encounter.rs |
| Resolution OTEL | Resolution emits encounter.resolved | Grep WatcherEventBuilder with "resolved" in encounter.rs |
| Phase OTEL | Phase transitions emit encounter.phase_transition | Grep WatcherEventBuilder with "phase_transition" in encounter.rs |
| Escalation OTEL | Escalations emit encounter.escalated | Grep WatcherEventBuilder with "escalated" in encounter.rs |
| HP delta OTEL | apply_hp_delta emits creature.hp_delta | Grep WatcherEventBuilder with "hp_delta" in creature_core.rs |
| Builds clean | cargo build -p sidequest-game succeeds | Build verification |
| Wiring | WatcherEventBuilder in non-test code | Grep -v test in encounter.rs and creature_core.rs |

## Key Files for Implementation

| File | Purpose |
|------|---------|
| sidequest-game/Cargo.toml | Add sidequest-telemetry dependency |
| sidequest-game/src/encounter.rs | Instrument apply_beat(), escalate_to_combat() |
| sidequest-game/src/creature_core.rs | Instrument apply_hp_delta() |

## Sm Assessment

**Story readiness:** Ready. Clear scope — add OTEL instrumentation to StructuredEncounter in sidequest-game. Three files, four event types, well-defined acceptance criteria.

**Risk:** Low. This is additive observability work — no behavioral changes to existing code. The telemetry crate already exists and is used in persistence.rs, so patterns are established.

**Routing:** TDD workflow → RED phase → Han Solo (TEA) writes failing tests for each OTEL event emission, then Yoda (Dev) implements.

## Tea Assessment

**Tests Required:** Yes
**Reason:** OTEL instrumentation must be verified — this is the observability story that makes StructuredEncounter's mechanics visible to the GM panel.

**Test Files:**
- `crates/sidequest-game/tests/otel_structured_encounter_story_28_2_tests.rs` — all 5 event types

**Tests Written:** 22 tests covering 6 ACs (telemetry dep already satisfied)
**Status:** RED (21 failing, 1 passing — the negative-case test `no_phase_transition_when_phase_unchanged`)

| AC | Tests | Count |
|----|-------|-------|
| apply_beat OTEL | beat_applied event emission + fields (encounter_type, beat_id, stat_check, metric_before/after, phase) | 6 |
| Resolution OTEL | resolved event on resolution beat + threshold crossing + fields | 3 |
| Phase OTEL | phase_transition emission + old/new phase fields + no-op when unchanged | 4 |
| Escalation OTEL | escalated event + from_type/to_type fields | 2 |
| HP delta OTEL | hp_delta emission + fields (name, old_hp, new_hp, delta, max_hp, clamped) | 5 |
| Wiring | source file grep for WatcherEventBuilder/watcher! in non-test code | 2 |

### Rule Coverage

No lang-review or project rules files found. Coverage is AC-driven only.

**Self-check:** All 22 tests have meaningful assertions. No vacuous `assert!(true)`, no `let _ =` patterns, no always-true conditions.

**Implementation notes for Yoda (Dev):**
- `sidequest-telemetry` is already a dep — no Cargo.toml change needed
- Use `WatcherEventBuilder::new("encounter", WatcherEventType::StateTransition)` pattern from persistence.rs
- Each event needs `.field("action", "<event_name>")` — tests filter on this
- `apply_beat()` needs to capture `metric_before` BEFORE applying delta, emit `beat_applied`, then conditionally emit `resolved` and `phase_transition`
- `escalate_to_combat()` emits `escalated` with `from_type` (self.encounter_type) and `to_type` ("combat")
- `apply_hp_delta()` needs to capture `old_hp` before clamp, compute `clamped` by comparing raw vs clamped result

**Handoff:** To Dev for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/encounter.rs` — Added WatcherEventBuilder emissions to apply_beat() (beat_applied, resolved, phase_transition) and escalate_to_combat() (escalated)
- `crates/sidequest-game/src/creature_core.rs` — Added WatcherEventBuilder emission to apply_hp_delta() (hp_delta with clamped detection)
- `crates/sidequest-game/tests/otel_structured_encounter_story_28_2_tests.rs` — Added TELEMETRY_LOCK mutex for test isolation with shared broadcast channel

**Tests:** 22/22 passing (GREEN)
**Existing tests:** 503 unit tests + 66 integration tests (standoff + encounter) all passing
**Branch:** feat/28-2-otel-structured-encounter (pushed)

**Handoff:** To verify phase (TEA for simplify + quality-pass)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 8 ACs verified against implementation:
- Telemetry dep: pre-existing in Cargo.toml (confirmed by TEA)
- apply_beat OTEL: WatcherEventBuilder at encounter.rs:517 with beat_applied action
- Resolution OTEL: WatcherEventBuilder at encounter.rs:529 with resolved action
- Phase OTEL: WatcherEventBuilder at encounter.rs:542 with phase_transition action (conditional on phase change)
- Escalation OTEL: WatcherEventBuilder at encounter.rs:567 with escalated action
- HP delta OTEL: WatcherEventBuilder at creature_core.rs:52 with hp_delta action
- Builds clean: confirmed by Dev (503 unit tests + 66 integration tests passing)
- Wiring: all 5 emissions in non-test production code

**Decision:** Proceed to verify

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No duplication — each WatcherEventBuilder call has unique fields per event type |
| simplify-quality | clean | Naming consistent with existing persistence.rs patterns, no dead code |
| simplify-efficiency | clean | Builder chains are zero-cost when no subscribers, no unnecessary allocations |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** All passing (22/22 tests, clippy clean on changed files, fmt clean on changed files)
**Handoff:** To Reviewer for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 warning (unused import) | confirmed 1 (low) |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (emit() drops silently) | dismissed — pre-existing in telemetry crate, not introduced by diff; logged as delivery finding |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations, 5 rules checked | N/A |

**All received:** Yes (3 returned results, 6 disabled via settings)
**Total findings:** 1 confirmed (low — unused import), 1 dismissed (pre-existing telemetry behavior), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Pre-mutation capture ordering correct — `metric_before` (encounter.rs:463) and `old_phase` (encounter.rs:464) captured before any mutation at lines 467-508. Evidence: variable declarations precede all mutation lines.

2. [VERIFIED] Phase transition guard correct — `if self.structured_phase != old_phase` at encounter.rs:538 correctly gates emission. Negative test `no_phase_transition_when_phase_unchanged` confirms this at the test level. Complies with "no silent fallbacks" — not emitting a no-op event is correct behavior, not a fallback.

3. [VERIFIED] Clamped flag computation correct — creature_core.rs:49 uses i64 arithmetic matching clamp_hp internals (hp.rs:15). `(self.hp as i64) != (old_hp as i64 + delta as i64)` handles i32 overflow edge cases. Evidence: both sides widen to i64 before comparison.

4. [VERIFIED] Error paths don't emit — `apply_beat()` returns Err at lines 452-453 and 459-460 before reaching any OTEL code. Resolved/unknown beats never emit beat_applied. Correct: we should not observe rejected operations.

5. [LOW] Unused import `EncounterPhase` in test file line 19. Cosmetic, non-blocking. [PREFLIGHT]

6. [VERIFIED] Wiring tests exist — test file lines 631-656 read source files and assert WatcherEventBuilder/watcher! presence. Satisfies "every test suite needs a wiring test." Evidence: `encounter_rs_uses_watcher_event_builder` and `creature_core_rs_uses_watcher_event_builder`.

7. [VERIFIED] Test isolation via TELEMETRY_LOCK — static Mutex at test file line 95 serializes all telemetry tests. `fresh_subscriber()` acquires lock + drains stale events. No cross-test contamination possible while guard is held.

8. [VERIFIED] `escalate_to_combat()` takes `&self` (immutable) — OTEL emission at encounter.rs:567-571 occurs before constructing the return value. No mutation risk, correct placement.

### Rule Compliance

| Rule | Instances Checked | Compliant |
|------|-------------------|-----------|
| No silent fallbacks | 5 emission sites | Yes — `send()` no-op is documented design, not a fallback |
| No stubbing | 5 emission sites | Yes — all concrete implementations |
| Wire up what exists | WatcherEventBuilder reuse | Yes — uses existing telemetry crate |
| Verify wiring (non-test consumers) | encounter.rs, creature_core.rs | Yes — both are called from production code paths |
| Every test suite needs wiring test | 2 wiring tests | Yes — file-read assertions verify production usage |
| OTEL observability | 5 event types | Yes — this IS the OTEL story |

[EDGE] N/A — disabled via settings
[SILENT] 1 finding dismissed — pre-existing `emit()` behavior in telemetry crate, not introduced by this diff. Logged as delivery finding for future story.
[TEST] N/A — disabled via settings
[DOC] N/A — disabled via settings
[TYPE] N/A — disabled via settings
[SEC] N/A — disabled via settings (no auth/tenant/security surface in this diff — pure observability instrumentation)
[SIMPLE] N/A — disabled via settings
[RULE] 0 violations found by rule-checker across 5 CLAUDE.md rules

### Devil's Advocate

What if this code is broken? Let me try to break it.

**Scenario 1: Channel never initialized.** If `init_global_channel()` is never called (e.g., a new binary entry point or a misconfigured test harness), every `.send()` in this diff becomes a no-op. The GM panel shows nothing. There's no way to distinguish "telemetry working, nothing happened" from "telemetry silently discarded." This is a real concern — but it's pre-existing behavior in the telemetry crate (not introduced by this diff), and it's documented at telemetry/src/lib.rs:156-160. Logged as a delivery finding for a future hardening story.

**Scenario 2: `format!("{:?}", phase)` changes.** The Debug representation of EncounterPhase produces strings like "Setup", "Opening". If someone adds a custom Debug impl or renames a variant, the OTEL field values change silently. GM panel dashboards or filters keyed on these strings would break. However, this is standard Rust telemetry practice — you trade compile-time safety for observability convenience. The phase strings are internal telemetry, not API contracts. Acceptable risk.

**Scenario 3: Malicious beat_id.** `beat_id` is passed as a `.field()` value to the telemetry builder, which serializes it as JSON. If `beat_id` contains special characters or very long strings, the JSON serialization handles it safely (serde_json escapes everything). No injection risk.

**Scenario 4: High-frequency emission.** In a combat encounter with 50 rapid beats, each `apply_beat()` emits 1-3 events. The broadcast channel has capacity 256 (telemetry/src/lib.rs:168). At worst, 150 events. Well within capacity. No backpressure risk.

**Scenario 5: `self.outcome` is always None.** Looking at the code, `self.outcome` is `None` in every `apply_beat` path — it's never set by the current code. So the resolved event always emits `outcome: "none"`. This is technically correct (the outcome hasn't been assigned yet — that happens in a future story when the narrator describes what happened). But it could confuse GM panel consumers expecting an outcome description. This is a documentation gap, not a code bug. The spec says `outcome` is a field but doesn't specify who sets it.

None of these scenarios reveal a critical or high-severity issue. The code is correct for its scope.

**Data flow traced:** `apply_beat("size_up", &def)` → captures metric_before=0, old_phase=Setup → delta +2 → metric=2 → beat++ → not resolved → phase=Opening → emits beat_applied(standoff, size_up, CUNNING, 0→2, Opening) → skips resolved → emits phase_transition(standoff, Setup→Opening) → Ok(()). All fields match test expectations.

**Pattern observed:** Consistent use of `WatcherEventBuilder::new(component, StateTransition).field("action", event_name)` across all 5 emission sites. Clean, readable, follows builder pattern from telemetry crate.

**Error handling:** Early returns at encounter.rs:452-453 and 459-460 prevent OTEL emission for invalid operations. `send()` is infallible (no-op on error).

**Handoff:** To Grand Admiral Thrawn for finish-story

## Scope Boundaries

**In scope:**
- Add sidequest-telemetry dependency to sidequest-game
- Instrument StructuredEncounter methods in encounter.rs
- Instrument CreatureCore::apply_hp_delta()

**Out of scope:**
- OTEL for other game crate modules (tropes, disposition, etc.) — that's 28-12