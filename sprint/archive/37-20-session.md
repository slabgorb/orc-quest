---
story_id: "37-20"
jira_key: ""
epic: "37"
workflow: "wire-first"
---

# Story 37-20: Dice-request request_id lifecycle

## Story Details
- **ID:** 37-20
- **Jira Key:** (no Jira key, personal project)
- **Workflow:** wire-first
- **Epic:** 37 — Playtest 2 Fixes — Multi-Session Isolation
- **Points:** 5
- **Priority:** p0
- **Type:** bug
- **Stack Parent:** none

## Acceptance Criteria
1. Server becomes single issuer of `request_id` on DiceRequest creation
   - Generated in `sidequest-protocol` as `DiceRequest.request_id: Uuid`
   - Serialized in the `DiceRequestPayload` sent over WebSocket
   - Call site: `dispatch/dice.rs::emit_dice_request`

2. Client echoes server-issued `request_id` in DiceResponsePayload on resolution
   - UI captures `request_id` from incoming `DiceRequestPayload`
   - DiceResponse hook sends it back in `DiceResponsePayload.request_id`
   - Call site: `src/hooks/useGameState.ts::handleDiceRoll`

3. Server adds retry/recovery mechanism to prevent wedging on lost requests
   - Store pending `request_id` in `session.pending_dice_requests: HashMap<Uuid, DiceRequest>`
   - On turn update, validate all in-flight requests have responses
   - Missing response triggers `DiceRequest` re-emission with same `request_id`
   - OTEL span: `dice_request.recovery` with severity=warning when retry needed
   - Call site: `dispatch/turn.rs::apply_turn_result`

4. End-to-end wire verified
   - TEST: `POST /turn` with pending dice request → server re-emits request with same id
   - TEST: Client receives DiceResponse with matching request_id → turns into correct state
   - No broken exports or unwired components in diff

## Workflow Tracking
**Workflow:** wire-first
**Phase:** finish
**Phase Started:** 2026-04-18T20:32:25Z
**Phase Note:** Reviewer pass 2 — rework complete, confirming findings #1–#6.

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-18T15:30Z | 2026-04-18T19:35:18Z | 4h 5m |
| red | 2026-04-18T19:35:18Z | 2026-04-18T19:51:25Z | 16m 7s |
| green | 2026-04-18T19:51:25Z | 2026-04-18T20:04:50Z | 13m 25s |
| review | 2026-04-18T20:04:50Z | 2026-04-18T20:32:25Z | 27m 35s |
| finish | 2026-04-18T20:32:25Z | - | - |

## Story Context

### Problem Statement
During playtest 2, a player lost a nat 20 defense roll when their network briefly disconnected. The dice request was issued by the server, rendered on the client, but the response was never sent back (or lost in transit). The server had no way to detect that the request was orphaned, and no mechanism to retry. The client had no way to know what `request_id` to send back. This wedged the session.

**Root causes:**
1. `DiceRequest` contained no `request_id` field — client couldn't echo back the exact request
2. Server had no registry of pending requests — no way to detect or retry
3. No contract between narrator and protocol about what constitutes a "valid" request lifecycle

### Scope
- Add `request_id: Uuid` to `DiceRequest` in sidequest-protocol
- Wire client to capture and echo back `request_id` in `DiceResponsePayload`
- Implement server-side pending request registry and retry logic
- Add OTEL instrumentation so GM panel can see retries happening
- No changes to narrator prompt (that's a separate concern — 37-17)

**Out of scope:**
- Persistence of pending requests across server restart (37-18 canceled, revisit if needed)
- Graceful degradation if max retries exceeded (can add if it happens)

### Related Stories
- **37-18 (canceled):** Pending requests persisted to snapshot. Rescoped here to in-memory only.
- **37-17:** Stat name casing — separate issue, not a blocker for this story.
- **37-19 (completed):** Phantom-player dedup — already fixed.

## Sm Assessment

p0 protocol bug surfaced in Playtest 2: a lost dice request (natural 20 on defend) wedged the session because client and server both believed they could be the request_id issuer. Fix is a clean contract change — server becomes the single issuer, client echoes, and server tracks pending requests with retry/recovery so a dropped WebSocket frame cannot leave the turn hung.

Wire-first is the right call: the regression was a wiring gap (client-issued ids never reconciled with server state), not a logic defect, so the RED test must ride the WebSocket boundary end-to-end. Scope is bounded to in-memory pending tracking — persistence was explicitly descoped with 37-18. Two repos (api, ui) on develop, branches up. Handing to TEA for the failing boundary test.

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): `SharedGameSession::pending_dice_requests` is a bare `HashMap` that two production call sites (`lib.rs:2343` and `lib.rs:3157`) mutate directly, including one path that adopts a client-supplied `request_id`. Affects `crates/sidequest-server/src/lib.rs` and `crates/sidequest-server/src/shared_session.rs` (add chokepoint method + retry detector + OTEL helper; funnel both lib.rs insertion sites through it). *Found by TEA during test design.*
- **Improvement** (non-blocking): The existing `emit_dice_request_sent` / `emit_dice_throw_received` / `emit_dice_result_broadcast` trio has no `dice_request.recovery` sibling. Adding it completes the dice-channel OTEL surface the GM panel needs to visualize retries. Affects `crates/sidequest-server/src/lib.rs` (add public `emit_dice_request_recovery` alongside the existing emitters). *Found by TEA during test design.*

## TEA Assessment

**Tests Required:** Yes
**Test Files:**
- `crates/sidequest-server/tests/integration/dice_request_lifecycle_story_37_20_tests.rs` — 6 tests covering insertion chokepoint, retry detection, OTEL recovery span, and single-issuer wiring.

**Tests Written:** 6 tests
**Status:** RED (compile failure on missing `insert_pending_dice_request`, `expired_pending_dice_requests`, `emit_dice_request_recovery`; wiring test will assert against current two direct `.insert` sites once the compile gate passes).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| no silent fallbacks | `resolved_requests_are_not_retried` — retry detector must respect explicit removal, not re-fire | failing (compile) |
| wiring test present | `only_shared_session_may_insert_into_pending_dice_requests` — source-grep enforces chokepoint | failing (compile) |
| OTEL on subsystem decision | `emit_dice_request_recovery_sends_watcher_event` — StateTransition on "dice" channel | failing (compile) |
| idempotent chokepoint | `insert_pending_dice_request_is_idempotent_on_same_request_id` — re-insert preserves issued_at | failing (compile) |
| meaningful assertions | every test asserts on specific request_id, count, and field values — no `let _ =`, no bare `is_some()` | pass (self-check) |

**Rules checked:** 5 of applicable lang-review rules covered (the remaining Rust-specific rules — `#[non_exhaustive]`, validated constructors, `deny_unknown_fields` — apply to new protocol types; this story adds no new wire types, so N/A).
**Self-check:** 0 vacuous tests. Every assertion names a concrete value; the grep-test asserts an empty offender list with a formatted list of offenders on failure.

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Status:** GREEN — 6/6 new tests pass, full dice suite (54 tests) clean, build clean.

**Changes:**
- `crates/sidequest-server/src/shared_session.rs`
  - Added `pending_dice_request_issued_at: HashMap<String, Instant>` (pub(crate)) alongside the existing `pending_dice_requests` map.
  - `SharedGameSession::insert_pending_dice_request(req)` — single insertion chokepoint, idempotent on same `request_id` (preserves original `issued_at`).
  - `SharedGameSession::expired_pending_dice_requests(now, timeout)` — retry detector. Iterates the canonical `pending_dice_requests` map; orphaned `issued_at` entries from direct `.remove()` callers are harmlessly ignored.
- `crates/sidequest-server/src/lib.rs`
  - `emit_dice_request_recovery(&req)` — public OTEL emitter, `StateTransition` + `Severity::Warn` on the "dice" channel, event `dice_request.recovery`.
  - Migrated both direct `pending_dice_requests.insert` call sites (server-initiated beat path at ~L2343, client-initiated beat+dice path at ~L3173) through the chokepoint.
  - Writer-loop retry tick: 5s check interval, 30s request timeout. Surfaces expired requests, fires OTEL recovery, re-broadcasts with same `request_id`. Client-side dedup (InlineDiceTray request_id check) absorbs the per-writer multiplier under N connections.

**Tests run:**
- `cargo test -p sidequest-server --test integration dice` → 54 passed, 0 failed.
- `cargo test -p sidequest-server --test integration -- --test-threads=1` → 534 passed, 4 pre-existing failures (genre-pack path + narration_single_send; verified against baseline `origin/develop`, unrelated to this diff).

**Branch pushed:** `feat/37-20-dice-request-lifecycle` on `sidequest-api`.

**Out of scope / follow-up:**
- UI-side `crypto.randomUUID()` mint at `sidequest-ui/src/App.tsx:589` on the client-initiated beat+dice path. This is a residual dual-issuer wart that's benign today (the chokepoint accepts the client-minted id verbatim and the id space is uuid-wide so collisions are impossible), but strict single-issuer requires moving mint to the server and adding a "beat-select" pre-phase. Out of scope for a 5pt p0 bug fix per the 34-12 physics-is-the-roll design.

**Handoff:** To TEA (Amos Burton) for verify (simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (all low) | confirmed 0, dismissed 3, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled via settings | N/A |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (1 high, 2 low) | confirmed 1, dismissed 2, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (1 high, 3 med, 1 low) | confirmed 1, dismissed 3, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (both high) | confirmed 2, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | findings | 3 (1 med, 2 low) | confirmed 0, dismissed 1, deferred 2 |
| 7 | reviewer-security | Yes | Skipped | disabled via settings | N/A |
| 8 | reviewer-simplifier | Yes | Skipped | disabled via settings | N/A |
| 9 | reviewer-rule-checker | Yes | findings | 3 (all high) | confirmed 3, dismissed 0, deferred 0 |

**All received:** Yes (6 enabled subagents returned, 3 disabled pre-skipped)
**Total findings:** 7 confirmed, 6 dismissed (with rationale), 3 deferred

## Reviewer Assessment

**Verdict:** CHANGES REQUESTED. Core wiring is sound (single-issuer chokepoint, end-to-end retry tick, OTEL emission all verified in production paths, wiring test present), but three project-rule violations and two stale-comment issues must be resolved before merge.

### Confirmed Findings (must fix)

1. **[SILENT] [RULE] Silent idempotency drop — `shared_session.rs:~497`.** `insert_pending_dice_request` early-returns when `request_id` already exists with no log and no OTEL. The client-initiated beat+dice path at `lib.rs:3209` trusts client-supplied `request_id`; a client that replays a stale id silently wedges the session in exactly the 37-20 failure mode. Violates the project's "No Silent Fallbacks" rule. **Fix:** emit `tracing::warn!` (and ideally a `WatcherEvent` on the "dice" channel) when a duplicate is detected, especially if the incoming payload differs from the stored one.

2. **[RULE] OTEL recovery span missing context anchor — `lib.rs:~144`.** `emit_dice_request_recovery` emits `event / request_id / rolling_player / stat / difficulty` but omits the human-readable `context` field from `DiceRequestPayload`. The GM panel can see "retry fired for player X on stat Y" but cannot answer "retry for which beat." Violates the OTEL completeness rule. **Fix:** add `.field("context", &request.context)` to the builder chain.

3. **[RULE] [TYPE] Orphan `issued_at` leak — `dice_dispatch.rs:215` and `lib.rs:~2557`.** `pending_dice_requests.remove()` and `.clear()` leave `pending_dice_request_issued_at` entries behind. Safe for retry correctness (detector iterates the canonical map) but the secondary map grows monotonically for session lifetime. Two rule-checker agents flagged this; type-design flagged the same invariant as a medium-confidence drift hazard. **Fix:** add `remove_pending_dice_request(&mut self, id: &str)` chokepoint that cleans both maps, and update `dice_dispatch.rs:215` + `lib.rs:~2557` (session-clear path) to use it. This also closes the type-design finding on parallel-map drift.

4. **[TEST] OTEL channel race in `emit_dice_request_recovery_sends_watcher_event` — `dice_request_lifecycle_story_37_20_tests.rs:221`.** Test calls `init_global_channel` + `subscribe_global` without draining stale events or serializing via a telemetry lock, then drains at most 16 events with silent break on `Err`. Under concurrent test runs with other dice-channel emitters (e.g., `otel_dice_spans_34_11_tests.rs`), the real recovery event can land beyond the drain budget and the test emits a false negative. Consistent with the OTEL cross-test pollution already observed on the sealed_letter suite. **Fix:** drain `while rx.try_recv().is_ok() {}` immediately after subscribe, before calling the emitter. Optionally expose `pub fn` helpers from `test_support` so integration tests share the `TELEMETRY_LOCK`.

5. **[DOC] Stale interval-setup comment — `lib.rs:~47`.** Comment "First tick fires immediately; skip it so we don't retry at t=0" implies `set_missed_tick_behavior(Delay)` is what skips the first tick. It is not — `MissedTickBehavior::Delay` governs late-tick bunching during the loop, not the first tick. The actual skip is the unconditional `ticker.tick().await` call. **Fix:** split the comment to describe each call's purpose correctly.

6. **[DOC] Stale RED-harness framing in test module — `dice_request_lifecycle_story_37_20_tests.rs:~16–46`.** Block comment says "there are currently TWO sites that insert into pending_dice_requests directly" and "will not compile today because (A)–(C) do not exist" — both true pre-fix, both false in the merged diff since the green implementation ships in the same PR. **Fix:** recast historical phrasing to past tense ("before this story, two sites inserted directly; the green fix funnels both through `insert_pending_dice_request`"), or drop "currently" / "today" language.

### Dismissed Findings (with rationale)

- [SILENT low] `expired_pending_dice_requests` silent skip on missing `issued_at` — dismissed as dup of #1 above; fixing #3 (orphan cleanup) + #1 (chokepoint warning) together removes the only production paths that could produce the missing state.
- [SILENT low] Retry tick silent no-op when `shared_session` is `None` — pre-connect behavior is correctly modeled; no action until session exists is the intent. Dismissed.
- [TEST low] Test drain loop treats `Lagged` identically to `Empty` — subsumed by fix #4; the drain-before-emit pattern handles lag equivalently.
- [TEST med] No test for orphan `issued_at` bound — subsumed by fix #3; after symmetric cleanup the orphan scenario cannot arise and the test is unnecessary.
- [TEST med] No test exercising `saturating_duration_since` underflow path — deferred; `Instant::now() - Duration` panics on some targets and the defensive code is exercised implicitly by the wedge-never-retries-prematurely assertions in test A.1/A.2.
- [TYPE med] Collapse parallel maps into `struct PendingDiceRequest { payload, issued_at }` — subsumed by fix #3; once `remove_pending_dice_request` is the chokepoint the drift hazard is gone, and the struct collapse becomes a cosmetic refactor rather than a correctness fix.

### Deferred Findings

- [TYPE low] `DiceRequestId` newtype wrapping `String` — deferred; the cross-map keying hazard is eliminated by fix #3 and the protocol-layer typing story is already explicitly out of scope (Dev deviation, accepted).
- [TYPE low] `PlayerId::server()` sentinel instead of `"server".to_string()` — deferred; the magic-string pattern predates this story and is used in every existing server-originated broadcast (`dice_req.rs`, `narrative.rs`, `audio.rs`). Out of scope.
- [TEST low] Concurrent `expired_pending_dice_requests` invocation test — deferred; the `Mutex<SharedGameSession>` serializes at runtime, and no concurrency invariant of this story is provable only by a racy test.
- [TEST med] Wiring-test allowlist uses file-name suffix instead of `#[cfg(test)]` — acknowledged but out of scope; the `*_tests.rs`-in-`src/` files are ancient project convention, not a new artifact of this story. Worth a follow-up story if the convention ever drifts.

### Rule Compliance

- No Silent Fallbacks: **VIOLATED** (finding #1).
- No Stubbing: compliant.
- Don't Reinvent: compliant — chokepoint funnels existing `.insert` sites through a single entry point.
- Verify Wiring: compliant — all three new symbols have non-test consumers in `lib.rs`.
- Every Test Suite Needs a Wiring Test: compliant (Contract D).
- OTEL on Every Subsystem Decision: **PARTIALLY VIOLATED** (finding #2 — span missing correlation anchor).
- Single Insertion Chokepoint: compliant — wiring test enforces.
- Retry Mechanism Fully Wired: compliant — 5/5 links present.
- No Half-Wired Features: compliant.
- Branch Base: compliant (develop).

**Handoff:** To Dev (Naomi Nagata) for rework on findings #1–#6. After fixes, dev re-runs the target dice suite and pushes; reviewer re-enters for a confirmation pass on just the delta.

## Dev Assessment — Reviewer Pass 1 Rework

**Status:** GREEN — all 6 reviewer findings addressed, 56/56 dice suite tests pass (was 54; added 2 new tests).

**Changes (commit 6ca4637):**
- `shared_session.rs`
  - `insert_pending_dice_request` now compares the incoming payload against the stored one. On mismatch it fires `tracing::warn!` AND a `WatcherEvent` (`dice.duplicate_id_mismatch`, `ValidationWarning`, `Warn` severity) so the GM panel surfaces the bypass / replay condition. Idempotency still wins (stored payload preserved). [finding #1]
  - `remove_pending_dice_request(id) -> Option<payload>` — new chokepoint; drops the `issued_at` sidecar alongside the canonical entry. [finding #3]
  - `clear_pending_dice_requests()` — new chokepoint; clears both maps together. [finding #3]
  - `pending_dice_request_issued_at_contains(id)` and `_len()` — read-only accessors so integration tests can assert the lockstep invariant without requiring the sidecar to go `pub`.
  - `expired_pending_dice_requests` — the silent `?` skip on missing `issued_at` is now a loud `tracing::warn!` naming "chokepoint bypass suspected." [finding #1 / #3 symmetric]
  - Docstrings updated to reflect the new invariant.
- `lib.rs`
  - `emit_dice_request_recovery` now rides `character_name` and `context` on the span so the GM panel can correlate retry → beat / character, not just retry → player. [finding #2]
  - Retry tick's interval-setup comment split into two parts that correctly name what each call does. [finding #5]
  - Session-clear path at `~L2564` routed through `clear_pending_dice_requests()`. [finding #3]
- `dice_dispatch.rs`
  - Resolution path at `L215` routed through `remove_pending_dice_request(...)`. [finding #3]
- `tests/integration/dice_request_lifecycle_story_37_20_tests.rs`
  - OTEL test pre-drains the global channel before emitting + asserting. [finding #4]
  - RED-harness framing recast to past tense; no more "currently TWO sites" / "will not compile today." [finding #6]
  - Test `resolved_requests_are_not_retried` now uses the removal chokepoint and asserts the `issued_at` sidecar is dropped.
  - Two new tests: `duplicate_request_id_with_different_payload_emits_warning_event` (finding #1 coverage) and `clear_pending_dice_requests_drops_both_maps` (finding #3 coverage).

**Tests run:** `cargo test -p sidequest-server --test integration dice` → 56 passed, 0 failed.

**Branch pushed:** `feat/37-20-dice-request-lifecycle` @ `6ca4637`.

**Handoff:** back to Reviewer (Chrisjen Avasarala) for pass 2 confirmation.

## Reviewer Assessment — Pass 2

**Verdict:** APPROVED.

**Scope:** Confirmation pass on the rework delta `8881f1d..6ca4637` (4 files, 210 insertions, 29 deletions). Full delta read manually; no new subagent spawn warranted on a targeted rework of previously-enumerated findings.

### Finding-by-finding disposition

| # | Original finding | Fix landed | Evidence | Status |
|---|------------------|------------|----------|--------|
| 1 | [SILENT][RULE] Silent idempotency drop — `insert_pending_dice_request` returned `()` on duplicate `request_id` with no log/OTEL | `shared_session.rs:497` — compares stored payload to incoming; on mismatch fires `tracing::warn!` + `WatcherEvent` on "dice" channel (`ValidationWarning`, Severity::Warn, event `dice_request.duplicate_id_mismatch`, carrying `request_id` + `rolling_player`). Idempotency still wins — stored payload preserved. | Test `duplicate_request_id_with_different_payload_emits_warning_event` — drains channel first, asserts both payload preservation AND event emission. | Resolved |
| 2 | [RULE] OTEL recovery span missing correlation anchor | `lib.rs:144` — adds `.field("character_name", ...)` + `.field("context", &request.context)` to the builder chain, with inline rationale in the comment. | Test C.1 still asserts the required fields; new fields are additive and GM-panel-visible. | Resolved |
| 3 | [RULE][TYPE] Orphan `issued_at` leak — `remove` / `clear` bypassed sidecar; type-design flagged parallel-map drift hazard | `shared_session.rs` adds `remove_pending_dice_request` + `clear_pending_dice_requests` chokepoints. `dice_dispatch.rs:215` and `lib.rs:~2567` migrated. Doc comment on `expired_pending_dice_requests` updated to reflect lockstep invariant. | Test `resolved_requests_are_not_retried` now asserts sidecar cleanup via `pending_dice_request_issued_at_contains`; new test `clear_pending_dice_requests_drops_both_maps` pins the clear-chokepoint invariant. | Resolved |
| 4 | [TEST] OTEL test race (no pre-drain) | `dice_request_lifecycle_story_37_20_tests.rs:289` — `while rx.try_recv().is_ok() {}` immediately after `subscribe_global`. Same pattern applied in new A.3 test. | Both OTEL-asserting tests drain before emit. | Resolved |
| 5 | [DOC] Stale interval-setup comment misattributed first-tick skip to `MissedTickBehavior::Delay` | `lib.rs:1648` — comment split into two blocks, each correctly scoped to the call it annotates. | Diff read; comment now accurate. | Resolved |
| 6 | [DOC] Stale RED-harness "currently" / "will not compile today" framing | Test module header recast to past tense; compiler line numbers dropped; contract clauses retained with descriptive roll-up of test coverage. | Diff read. | Resolved |

### Specialist tag coverage (pass 2 roll-up)

Pass 2 confirms disposition of every pass-1 confirmed finding. Tags carried forward from the pass-1 specialists:
- [SILENT] — finding #1 (silent-failure-hunter + rule-checker) now emits `tracing::warn!` + WatcherEvent on duplicate-id mismatch; symmetric fix in `expired_pending_dice_requests` logs chokepoint bypass.
- [RULE] — findings #1, #2, #3 (rule-checker) all resolved; No Silent Fallbacks + OTEL completeness + symmetric chokepoint rules now pass.
- [TEST] — finding #4 (test-analyzer) resolved via pre-drain pattern; two new tests added (`duplicate_request_id_with_different_payload_emits_warning_event`, `clear_pending_dice_requests_drops_both_maps`).
- [DOC] — findings #5, #6 (comment-analyzer) both resolved.
- [TYPE] — finding #3 subsumed the parallel-map drift concern (type-design medium). With `remove_pending_dice_request` / `clear_pending_dice_requests` chokepoints, the two maps are structurally kept in lockstep — the drift vector is closed without needing the `struct PendingDiceRequest` collapse. The remaining [TYPE] low-confidence notes (`DiceRequestId` newtype, `PlayerId::server()` sentinel) stay deferred with the same rationale as pass 1.

### Bonus improvement (unrelated to findings but caught in rework)

- The previously-silent `?` short-circuit in `expired_pending_dice_requests` now emits `tracing::warn!("chokepoint bypass suspected")` before returning `None`. This closes the symmetric silent path on the detector side — fully compliant with "No Silent Fallbacks" in both directions.

### Rule Compliance (pass 2)

- No Silent Fallbacks: **compliant** — every idempotency / missing-sidecar path now logs.
- OTEL on Every Subsystem Decision: **compliant** — recovery span carries request_id, rolling_player, character_name, stat, difficulty, context.
- Single Insertion Chokepoint: compliant (pass 1 gate held).
- Symmetric Removal Chokepoint: **now compliant** — insert + remove + clear all funnel through single-owner methods.
- Every Test Suite Needs a Wiring Test: compliant (Contract D, unchanged).
- No Half-Wired Features: compliant — retry mechanism end-to-end wired + duplicate-id observability + removal lockstep all hold.
- Branch Base: compliant (`develop`).

### Test results

- `cargo test -p sidequest-server --test integration dice` → **56 passed, 0 failed** (up from 54; two new tests for the duplicate-id warning and the clear-chokepoint lockstep).
- All previously deferred non-blocking findings remain deferred — none escalated by the rework.

**Handoff:** to SM (Camina Drummer) for finish phase.

## Design Deviations

### TEA (test design)
- **`request_id` stays `String`, not `Uuid` newtype**
  - Spec source: session ACs, AC-1 bullet "Generated in sidequest-protocol as DiceRequest.request_id: Uuid"
  - Spec text: "Generated in `sidequest-protocol` as `DiceRequest.request_id: Uuid`"
  - Implementation: Tests treat `request_id` as the existing `String` field. Retyping to `Uuid` would touch every consumer in protocol / server / test-support / UI in a single story.
  - Rationale: Scope protection. The session wedge is caused by dual issuance + no retry, not by the string/uuid split. `uuid::Uuid::new_v4().to_string()` already guarantees uniqueness; the value is an opaque identifier on the wire. The real contract under test is the single-issuer chokepoint + retry detection.
  - Severity: minor
  - Forward impact: none — if a future story wants strong typing, it can land as a protocol-only refactor without reopening 37-20.

- **Retry-tick integration is tested via `expired_pending_dice_requests` API, not a live WebSocket round-trip**
  - Spec source: session ACs, AC-3 and AC-4
  - Spec text: "On turn update, validate all in-flight requests have responses / TEST: `POST /turn` with pending dice request → server re-emits request with same id"
  - Implementation: Tests exercise the detection API (`expired_pending_dice_requests`) and the OTEL recovery emitter. They do NOT stand up an axum server + WebSocket client to simulate a dropped frame.
  - Rationale: Follows the 37-19 / 34-11 pattern in this crate — integration tests target the module boundary, not the transport. A WebSocket round-trip test would triple the harness complexity for no additional signal on the core contract. Dev is free to wire the retry tick anywhere (ws reader loop, turn barrier heartbeat, etc.) as long as it calls `expired_pending_dice_requests` and `emit_dice_request_recovery`.
  - Severity: minor
  - Forward impact: none — if playtest 3 reveals the retry doesn't actually fire on the live path, that's a wiring-gate failure, caught at the same level as any other dispatch wiring bug.

### Dev (implementation)
- **Retry tick runs per-writer-loop, not once per session**
  - Spec source: session AC-3
  - Spec text: "On turn update, validate all in-flight requests have responses"
  - Implementation: Retry detector is driven by a `tokio::time::interval` branch inside each player's writer task. With N players connected, N retry ticks fire and (if a request is expired) all N re-broadcast.
  - Rationale: A single session-scoped retry task would require new lifecycle management (spawn on first shared_session attach, cancel on last disconnect, handle race with reconnects). The per-writer tick is 40 lines of localized code; duplication is absorbed by the existing client-side dedup in `InlineDiceTray.tsx:193` (skip if `request_id === lastRequestIdRef.current`). OTEL fires N times per retry, which is visible rather than hidden — GM panel sees exactly how many writers are awake.
  - Severity: minor
  - Forward impact: minor — if the OTEL noise under large multiplayer sessions becomes annoying, promote to a session-scoped task later. No API change needed, it's a local refactor of the tick owner.

- **Chokepoint is insertion-only; `.remove()` stays a direct map call**
  - Spec source: session AC-3 "store pending `request_id` in `session.pending_dice_requests: HashMap<Uuid, DiceRequest>`"
  - Spec text: described the map as the pending registry; implied symmetric chokepoint for every mutation.
  - Implementation: `insert_pending_dice_request` is the chokepoint; resolution-time removal continues to call `pending_dice_requests.remove(&key)` directly in `dice_dispatch.rs`, `shared_session.rs::reconcile_removed_player`, and the session-clear branch in `lib.rs`.
  - Rationale: `expired_pending_dice_requests` iterates the canonical map, so orphaned `issued_at` entries cannot surface as retries — removal-via-raw-map is safe for correctness. Adding a `remove_pending_dice_request` chokepoint would touch three more call sites for zero behavior change. The single-issuer invariant only cares about ids *being born* in one place; where they die is not load-bearing.
  - Severity: minor
  - Forward impact: none — `issued_at` map grows slowly (one entry per directly-removed request) and resets on session shutdown. If it ever becomes a real leak, adding a removal chokepoint is a 10-minute follow-up.