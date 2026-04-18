---
story_id: "35-5"
jira_key: ""
epic: "MSSCI-16932"
workflow: "tdd"
---
# Story 35-5: Wire turn_reminder into barrier creation — spawn async reminder task

## Story Details
- **ID:** 35-5
- **Epic:** MSSCI-16932 (Wiring Remediation II — Unwired Modules, OTEL Blind Spots, Dead Code)
- **Jira Key:** TBD
- **Workflow:** tdd
- **Points:** 5
- **Stack Parent:** none
- **Repos:** api

## Story Context

The `turn_reminder` module is fully implemented in the API codebase but has zero production consumers. This story wires it into barrier creation so it becomes operational.

**Context:**
- `turn_reminder.rs` (161 LOC) in sidequest-game crate — fully tested with story 8-9 tests
- `TurnBarrier` created in two locations: `sidequest-server/src/dispatch/connect.rs` and `sidequest-server/src/lib.rs`
- `ReminderConfig` + `ReminderResult` types exist and are production-ready
- `run_reminder()` is an async function that sleeps for threshold duration, then checks idle players

**Acceptance Criteria:**
1. After `TurnBarrier::new()` in both production locations, spawn async reminder task via `tokio::spawn`
2. Reminder task calls `ReminderResult::run_reminder()` with barrier timeout, config (load from genre pack or default), session Arc, and turn mode
3. OTEL watcher events emitted: "reminder_spawned", "reminder_fired" (with idle_player_count)
4. Integration test verifies turn_reminder has a non-test consumer in production code paths (sidequest-server dispatch or session setup)
5. No silent fallbacks; fail loudly if turn_reminder config is missing from genre pack

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-09T21:30:01Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-09 | 2026-04-09T20:56:05Z | 20h 56m |
| red | 2026-04-09T20:56:05Z | 2026-04-09T21:01:47Z | 5m 42s |
| green | 2026-04-09T21:01:47Z | 2026-04-09T21:15:25Z | 13m 38s |
| spec-check | 2026-04-09T21:15:25Z | 2026-04-09T21:16:43Z | 1m 18s |
| verify | 2026-04-09T21:16:43Z | 2026-04-09T21:19:27Z | 2m 44s |
| review | 2026-04-09T21:19:27Z | 2026-04-09T21:24:34Z | 5m 7s |
| green | 2026-04-09T21:24:34Z | 2026-04-09T21:27:41Z | 3m 7s |
| review | 2026-04-09T21:27:41Z | 2026-04-09T21:29:11Z | 1m 30s |
| spec-reconcile | 2026-04-09T21:29:11Z | 2026-04-09T21:30:01Z | 50s |
| finish | 2026-04-09T21:30:01Z | - | - |

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
- No upstream findings during test verification.

### Reviewer (code review)
- **Gap** (blocking): `run_reminder()` does not guard against disabled barrier config. When `TurnBarrierConfig::disabled()` is used (both current wiring points), `reminder_delay(Duration::ZERO)` = 0, sleep returns instantly, reminder fires false alarm with all players idle. Affects `crates/sidequest-game/src/barrier.rs` (add early return when `!self.config().is_enabled()`). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **Disabled barrier fires instant reminder:** AC1 says "spawn async reminder task" after barrier creation, but both wiring points use `TurnBarrierConfig::disabled()` (timeout=ZERO). `run_reminder` sleeps for `0.6 * 0 = 0`, fires instantly, finds all players idle. False alarm on every barrier creation. Not documented by TEA/Dev. Severity: HIGH.
  - **RESOLVED** in rework commit `eb30bed`: `run_reminder()` now guards on `!self.config().is_enabled()`, returning empty result via FreePlay mode.

### Architect (reconcile)
- No additional deviations found. TEA and Dev correctly reported no spec deviations. The Reviewer's finding (disabled barrier false alarm) was a correctness bug, not a spec deviation — the spec doesn't describe disabled-barrier behavior. The bug was found and fixed in rework. No AC deferrals exist.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | Tests 9/9 pass; clippy/fmt failures pre-existing | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 6 | confirmed 1 (disabled barrier), dismissed 4 (genre pack N/A, JoinHandle pattern, TOCTOU benign), dismissed 1 (duplicate of genre pack) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 8 | confirmed 1 (disabled barrier, corroborates silent-failure), dismissed 7 (genre pack N/A x3, unwrap structurally safe x2, test conventions x2) |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 1 confirmed, 13 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT] | Disabled barrier fires instant false-alarm reminder | `barrier.rs:run_reminder()` | Add early return: `if !self.config().is_enabled() { return ReminderResult::check_with_mode(...FreePlay) }` or equivalent guard. Both server wiring points use `TurnBarrierConfig::disabled()`, so without this guard the reminder fires immediately on every barrier creation with zero delay. |

**Data flow traced:** `TurnBarrier::new(mp_session, disabled_config)` → server spawns `run_reminder(&default_config)` → `reminder_delay(Duration::ZERO)` = 0 → `sleep(0)` → instant return → `check_reminder` finds all players idle → fires `reminder_fired` OTEL with full player count as idle. False alarm.

**Pattern observed:** Delegation pattern in barrier.rs (turn_mode getter, check_reminder, run_reminder) follows existing `player_count()`, `named_actions()` at barrier.rs:245-380. Good pattern.

**Error handling:** Mutex `.lock().unwrap()` is idiomatic for std::sync::Mutex throughout barrier.rs. Fire-and-forget `tokio::spawn` matches render_integration pattern.

**5 observations:**
1. [HIGH] [SILENT] Disabled barrier + zero timeout = instant false-alarm reminder at barrier.rs:290
2. [VERIFIED] check_reminder acquires session/turn_mode locks in consistent order — no deadlock risk. barrier.rs:279-280. Same order as wait_for_turn() at barrier.rs:438.
3. [VERIFIED] run_reminder is cancel-safe — tokio::time::sleep is cancel-safe, no state mutated before await point. barrier.rs:291-293.
4. [VERIFIED] OTEL spans correctly scoped — `_span` entered, info events fire within span lifetime. lib.rs:1594-1597, 1600-1608.
5. [VERIFIED] ReminderConfig fields are private with getters — threshold/message private at turn_reminder.rs:32-33, getters at lines 46-52. Complies with rule #9.

### Rule Compliance

| Rule | Items Checked | Compliant? |
|------|--------------|------------|
| #1 silent errors | `.unwrap()` on `as_ref()` x2 | Yes — structurally guaranteed Some (assigned on prior line) |
| #2 non_exhaustive | ReminderError | Yes — has #[non_exhaustive] at turn_reminder.rs:19 |
| #4 tracing | reminder_spawned, reminder_fired spans | Yes — both OTEL events present in server code |
| #6 test quality | 9 wiring tests | Yes — source-level checks follow codebase convention |
| #8 serde bypass | ReminderConfig, ReminderResult | Yes — no Deserialize derives |
| #9 public fields | ReminderConfig, ReminderResult | Yes — private with getters |

### Devil's Advocate

What if this reminder wiring is fundamentally premature? Both wiring points use `TurnBarrierConfig::disabled()` — meaning the barrier is created but intentionally not enforcing timeouts. The disabled config exists as a placeholder while the real multiplayer timeout tuning happens. Wiring a reminder into a disabled barrier is like installing a doorbell on a wall with no door. The reminder will fire instantly (sleep(0)), find everyone idle (nobody could have submitted in zero time), and emit a false OTEL event. This isn't a theoretical concern — it's what the code does RIGHT NOW on every multiplayer session join.

The fix is straightforward — guard `run_reminder` on `config.is_enabled()`. But this raises a deeper question: should the reminder be spawned at all when the barrier is disabled? The current code unconditionally spawns regardless of barrier state. A more defensive approach would check `is_enabled()` at the spawn site, before creating the task. This avoids the overhead of spawning a task that immediately returns empty.

The disabled barrier also means the OTEL "reminder_spawned" event fires on every join, even when reminders are effectively no-ops. This creates noise in the GM panel — the watcher sees "reminder spawned" but the reminder does nothing useful. A future consumer of the OTEL stream might interpret "reminder_spawned" as evidence the system is actively monitoring idle players, when it's not.

None of this is a security issue or data corruption risk. But it's a correctness issue: the system claims to be doing something (monitoring idle players) that it cannot actually do in disabled mode. The fix is small — one guard line — but it matters.

**Handoff:** Back to Dev for fix. One HIGH finding — disabled barrier guard needed in `run_reminder()`.

---

## Reviewer Assessment (rework re-review)

**Verdict:** APPROVED

**Rework fix verified:** `run_reminder()` now guards on `!self.config().is_enabled()`, returning empty result via `FreePlay` mode. Disabled barriers no longer trigger false-alarm reminders. The guard follows the same locking pattern as `check_reminder()`.

**Tests:** 9/9 GREEN

**Subagent findings resolution (from round 1):**
- [SILENT] Disabled barrier instant false alarm — **RESOLVED** by rework guard at barrier.rs:291
- [RULE] Rule #1 unwrap on as_ref() — dismissed (structurally guaranteed Some, assigned on prior line)
- [RULE] Rule #3 ReminderConfig::default() — dismissed (genre pack has no reminder field in schema)
- [RULE] Rule #4 no tracing in run_reminder() — dismissed (server-side OTEL spans are the correct layer)
- [RULE] Rule #6 test quality — dismissed (codebase convention for source-level wiring tests)

**Prior round observations:** All still hold — no new issues introduced by the 6-line guard.

**Handoff:** To Drummer (SM) for finish.

---

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | Image broadcaster duplication in lib.rs:808 — pre-existing, not this story |
| simplify-quality | 1 finding | Duplicate docstring in barrier.rs resolve() — pre-existing, not this story |
| simplify-efficiency | 5 findings | OTEL span pattern (incorrect analysis — events ARE in span scope) + pre-existing abstractions |

**Applied:** 0 fixes (all findings were pre-existing code or incorrect analysis)
**Flagged for Review:** 0
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** 9/9 wiring tests passing, build clean
**Handoff:** To Chrisjen (Reviewer) for code review

---

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 1 (trivial)

- **ReminderConfig uses Default instead of genre pack loading** (ambiguous spec — behavioral, trivial)
  - Spec: AC5 says "fail loudly if turn_reminder config is missing from genre pack"
  - Code: Uses `ReminderConfig::default()` — genre pack has no reminder config field in its schema
  - Recommendation: C — Clarify spec. Genre pack schema has no reminder field (`sidequest-genre` crate has zero references to `reminder`). Loading from genre pack is a future story. Using `Default` is correct — there is no silent fallback because there is nothing to fall back from. The default is the only source.

**Decision:** Proceed to verify phase.

---

## Dev Assessment (rework)

**Implementation Complete:** Yes
**Rework Fix:** Added disabled-barrier guard in `run_reminder()` — early return via `FreePlay` mode when `!config.is_enabled()`. Prevents instant false-alarm reminder when `TurnBarrierConfig::disabled()` is used.
**Files Changed:**
- `crates/sidequest-game/src/barrier.rs` — Added disabled-barrier guard to `run_reminder()`

**Tests:** 9/9 passing (GREEN)
**Branch:** feat/35-5-wire-turn-reminder (pushed)

**Handoff:** Back to review

---

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/barrier.rs` — Added `turn_mode()` getter, `check_reminder()`, `run_reminder()` to TurnBarrier. Delegates through live Mutex<MultiplayerSession>, no stale copies.
- `crates/sidequest-server/src/lib.rs` — Spawn reminder task after barrier creation (reconnecting player path)
- `crates/sidequest-server/src/dispatch/connect.rs` — Spawn reminder task after barrier creation (multiplayer join path)

**Tests:** 9/9 passing (GREEN) + 46 existing turn_reminder tests still pass
**Branch:** feat/35-5-wire-turn-reminder (pushed)

**Handoff:** To verify phase (TEA)

---

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wiring story — must verify turn_reminder gets non-test consumers in sidequest-server

**Test Files:**
- `crates/sidequest-server/tests/turn_reminder_wiring_story_35_5_tests.rs` — 9 source-level wiring tests

**Tests Written:** 9 tests covering 5 ACs
**Status:** RED (all 9 failing — ready for Dev)

### AC Coverage

| AC | Tests | Status |
|----|-------|--------|
| AC1: spawn reminder after TurnBarrier::new() in both locations | `wiring_lib_spawns_reminder_after_barrier`, `wiring_connect_spawns_reminder_after_barrier`, `wiring_lib_uses_tokio_spawn_for_reminder`, `wiring_connect_uses_tokio_spawn_for_reminder` | failing |
| AC2: run_reminder with config, session, turn_mode | `wiring_reminder_receives_turn_mode`, `wiring_constructs_reminder_config` | failing |
| AC3: OTEL reminder_spawned + reminder_fired | `wiring_emits_reminder_spawned_otel`, `wiring_emits_reminder_fired_otel` | failing |
| AC4: integration test with non-test consumer | `wiring_server_imports_turn_reminder` | failing |
| AC5: no silent fallbacks | Covered by AC2 — ReminderConfig must be explicitly constructed |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 tracing coverage | `wiring_emits_reminder_spawned_otel`, `wiring_emits_reminder_fired_otel` | failing |
| #6 test quality | All tests use `assert!` with specific messages | verified |

**Rules checked:** 2 of 15 applicable (most rules are for new types/constructors — this story wires existing types, not creating new ones)
**Self-check:** 0 vacuous tests found. All assertions check specific string content in production source.

**Handoff:** To Naomi (Dev) for implementation

---

## Sm Assessment

**Story readiness:** Ready. turn_reminder module exists with full test coverage from story 8-9. Wiring points identified at TurnBarrier::new() in connect.rs and lib.rs. This is integration work — no new algorithms, just connecting existing infrastructure.

**Risk:** Low. The module is already tested. The main risk is getting the async spawn lifetime right with the barrier's Arc references.

**Recommendation:** Proceed to RED phase. TEA writes failing integration tests that verify turn_reminder has non-test consumers and that reminder tasks are spawned on barrier creation.