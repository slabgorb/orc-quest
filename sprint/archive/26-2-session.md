---
story_id: "26-2"
jira_key: "none"
epic: "26"
workflow: "trivial"
---

# Story 26-2: Wire exercise_tracker into orchestrator dispatch

## Story Details

- **ID:** 26-2
- **Jira Key:** none (personal project)
- **Epic:** 26 — Wiring Audit Remediation
- **Workflow:** trivial (phased: setup -> implement -> review -> finish)
- **Points:** 3
- **Repos:** api
- **Branch:** feat/26-2-wire-exercise-tracker

## Workflow Tracking

**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-06T11:26:21Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-06T07:00:00Z | 2026-04-06T11:09:12Z | 4h 9m |
| implement | 2026-04-06T11:09:12Z | 2026-04-06T11:15:39Z | 6m 27s |
| review | 2026-04-06T11:15:39Z | 2026-04-06T11:26:21Z | 10m 42s |
| finish | 2026-04-06T11:26:21Z | - | - |

## Sm Assessment

Story 26-2 is a wiring task. The exercise_tracker module is fully implemented but has zero production consumers. This story wires it into the orchestrator dispatch pipeline. Trivial workflow — straight to implementation.

## Delivery Findings

- No upstream findings during implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/main.rs` — Wire SubsystemTracker into turn_record_bridge, emit WatcherEvents

**Tests:** 20/20 passing (exercise_tracker_story_3_5_tests)
**Build:** clean (sidequest-server)
**Branch:** feat/26-2-wire-exercise-tracker (pushed)

**Wiring verified:**
- Non-test consumer: `main.rs:121` — `SubsystemTracker::new(10, 20)` in turn_record_bridge
- `tracker.record(&record.agent_name)` called on every TurnRecord
- SubsystemExerciseSummary emitted every 10 turns
- CoverageGap emitted at turn 20 if agents have zero invocations

**Handoff:** To review phase

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | clippy fail pre-existing on develop | N/A — not introduced by diff |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | dismissed 3 (pre-existing infra, dual-channel by design, low-confidence fragility) |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 1 (magic numbers), dismissed 1 (pub fields pre-existing) |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 1 confirmed, 4 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Wiring is complete — `SubsystemTracker` instantiated at `main.rs:121`, `tracker.record()` called at `main.rs:124` on every TurnRecord. Non-test consumer confirmed.
2. [VERIFIED] WatcherEvent emission — `SubsystemExerciseSummary` at `main.rs:176-184` fires every 10 turns with histogram payload. `CoverageGap` at `main.rs:187-196` fires at turn 20 with missing agent names and `Severity::Warn`. Both use existing `WatcherEventType` variants confirmed at `sidequest-telemetry/src/lib.rs:51-53`.
3. [VERIFIED] Data flow traced — `record.agent_name` (String from Orchestrator TurnRecord) → `tracker.record(&str)` → HashMap increment → periodic WatcherEvent to GM panel broadcast. No user-controlled input enters the tracker; agent names are server-internal.
4. [RULE] Magic numbers `10` and `20` at `main.rs:121` — ADR-068 requires named constants. Should be `pub const DEFAULT_SUMMARY_INTERVAL: usize = 10` and `pub const DEFAULT_GAP_THRESHOLD: usize = 20` in `exercise_tracker.rs`. **Severity: [LOW]** — the comment explains their purpose, and these are one-time initialization values in a single call site. Not blocking.
5. [VERIFIED] Error handling — `WatcherEventBuilder::send()` is fire-and-forget by design (`let _ = tx.send(event)` in telemetry crate). No error paths to handle. `tracker.record()` is infallible. `serde_json::json!` on known types cannot fail.
6. [SILENT] Dual-channel telemetry — `tracker.record()` emits `tracing::info!/warn!` internally while `main.rs` emits `WatcherEvent`s at the same boundaries. These serve different consumers (structured logs vs GM panel WebSocket). By design, not duplication.
7. [VERIFIED] No security concerns — tracker operates on server-internal data only. No tenant isolation needed (server-scoped histogram). No external input paths.

### Rule Compliance

| Rule | Applicable | Compliant | Notes |
|------|-----------|-----------|-------|
| R3: Magic numbers | Yes | No | `10, 20` should be named constants per ADR-068 |
| R4: Tracing | Yes | Yes | Both tracing and WatcherEvent channels emit at correct severity |
| R9: Pub fields | Pre-existing | N/A | SubsystemTracker pub fields predate this diff; not introduced here |
| R16: OTEL | Yes | Yes | SubsystemExerciseSummary + CoverageGap events emitted |
| R17: No silent fallbacks | Yes | Yes | Conditional emit, not fallback |
| R18: Non-test consumers | Yes | Yes | main.rs:121 is production code |

### Devil's Advocate

Could this code cause problems? The tracker lives in `turn_record_bridge`, a single tokio task processing TurnRecords sequentially from an mpsc channel. No concurrency concern — it's single-threaded within that task. Could `turn_count` overflow? On 64-bit, `usize::MAX` is ~18 quintillion — at 1 turn/second that's 584 billion years. Not a real risk. Could `summary_interval` be zero? Only if someone modifies the hardcoded `10` to `0`, which would cause a divide-by-zero panic at the modulo check. But this is a compile-time constant, not configurable. The pub fields on SubsystemTracker theoretically allow post-construction mutation, but the only consumer is `turn_record_bridge` which owns the tracker locally — no shared reference escapes. Could the HashMap grow unbounded? Only if novel agent names appear; agent names come from `AgentKind` enum variants in the orchestrator, which is a fixed set. In practice, one could send a corrupted TurnRecord with a garbage `agent_name`, but TurnRecords come from the Orchestrator over an mpsc channel — no external input path. The magic numbers are the only real finding, and they're [LOW] — a naming convention issue, not a correctness bug.

**Data flow traced:** `record.agent_name` → `tracker.record()` → HashMap + WatcherEvent broadcast (safe — server-internal data only)
**Pattern observed:** Clean wiring following existing `turn_record_bridge` patterns at `main.rs:149-173`
**Error handling:** All paths are infallible by design (telemetry is fire-and-forget)
**Handoff:** To Grand Admiral Thrawn for finish-story

### Delivery Findings (Reviewer)

- **Improvement** (non-blocking): Magic numbers 10, 20 in `SubsystemTracker::new()` should be named constants per ADR-068. Affects `crates/sidequest-server/src/main.rs:121` and `crates/sidequest-agents/src/exercise_tracker.rs` (add `pub const DEFAULT_SUMMARY_INTERVAL` and `pub const DEFAULT_GAP_THRESHOLD`). *Found by Reviewer during code review.*

## Design Deviations

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No undocumented deviations found. Dev's "no deviations" claim is accurate — the implementation matches the session spec's wiring points.

## Implementation Notes

### Module Status

The `exercise_tracker` module exists fully implemented in `sidequest-agents/src/exercise_tracker.rs`:
- Tracks agent invocation histogram: 8 expected agents (narrator, creature_smith, ensemble, troper, world_builder, dialectician, resonator, intent_router)
- Emits `tracing::info!()` summaries and coverage gap warnings
- Lives in watcher validator task (cold path)

### Wiring Points

1. **Orchestrator struct** — add `SubsystemTracker` field
2. **Orchestrator::new()** — instantiate tracker with default thresholds
3. **process_action()** — call `tracker.record(&agent_name)` after agent is determined
4. **turn_record_bridge()** — optional: emit tracker summaries as WatcherEvents