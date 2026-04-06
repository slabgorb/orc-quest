---
story_id: "26-8"
jira_key: "none"
epic: "26"
workflow: "trivial"
---

# Story 26-8: Add OTEL watcher events for location transitions

## Story Details

- **ID:** 26-8
- **Jira Key:** none (personal project)
- **Epic:** 26 — Wiring Audit Remediation — Unwired Modules, Protocol Gaps, OTEL Blind Spots
- **Workflow:** trivial (phased: setup → implement → review → finish)
- **Points:** 2
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-06T17:50:01Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-06T17:29:16Z | 2026-04-06T17:31:31Z | 2m 15s |
| implement | 2026-04-06T17:31:31Z | 2026-04-06T17:45:27Z | 13m 56s |
| review | 2026-04-06T17:45:27Z | 2026-04-06T17:50:01Z | 4m 34s |
| finish | 2026-04-06T17:50:01Z | - | - |

## Sm Assessment

**Story 26-8** is a straightforward observability wiring task. Location transitions are a known OTEL blind spot from the Epic 26 audit — zero watcher events emitted during character movement. The fix is to add WatcherEvent emissions at transition points in sidequest-game and verify they flow through to the GM panel. 2-point trivial workflow is appropriate — no design ambiguity, clear acceptance criteria.

**Routing:** Yoda (Dev) for implement phase.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/mod.rs` — region.transition and region.discovery watcher events
- `crates/sidequest-server/src/dispatch/connect.rs` — location.restored and location.initialized watcher events
- `crates/sidequest-server/tests/watcher_story_3_6_tests.rs` — fix pre-existing send_watcher_event → emit

**Tests:** 19/19 passing (GREEN)
**Branch:** feat/26-8-otel-location-transitions (pushed)

**OTEL Events Added:**
| Event | Component | When |
|-------|-----------|------|
| `region.transition` | location | Region-mode location change (from/to) |
| `region.discovery` | location | First visit to a new region |
| `location.restored` | location | Save file location restore |
| `location.initialized` | location | Session start (room_graph entrance or rules.yaml default) |

**Pre-existing coverage:** Room graph transitions already had `room.transition` and `room.invalid_move` events. The generic `location_changed` event also existed but lacked from_location context in region mode.

**Handoff:** To Obi-Wan Kenobi for review phase.

## Delivery Findings

### Dev (implementation)
- **Improvement** (non-blocking): The existing `location_changed` watcher event (dispatch/mod.rs:908) only includes the new location name — no `from_location` field. Room graph mode has this via `room.transition`, but region mode now gets it via the new `region.transition` event. Consider adding `from_location` to the generic event for consistency in a future pass.
- **Gap** (non-blocking): `watcher_story_3_6_tests.rs` had 6 compilation errors from stale `send_watcher_event()` calls. Fixed as part of this story since they blocked the test suite.

### Reviewer (code review)
- **Improvement** (non-blocking): Pre-existing `.unwrap_or_default()` chain at `connect.rs:1110-1116` silently swallows genre pack load failures. The new `location.initialized` event only fires on the happy path — a load failure produces zero GM panel signal. A `CoverageGap` or `ValidationWarning` event in the empty-default path would close this blind spot. Not introduced by this diff, but adjacent to the new OTEL work.
  Affects `crates/sidequest-server/src/dispatch/connect.rs` (add OTEL event for genre pack load failure path).
  *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 1 (non-blocking), dismissed 1 (duplicate of first) |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 1 confirmed (non-blocking improvement), 1 dismissed (duplicate framing of same issue)

### Rule Compliance

**Rule: No Silent Fallbacks** — The 5 new `WatcherEventBuilder` calls all emit on concrete code paths; none introduce silent fallbacks. The pre-existing `.unwrap_or_default()` at connect.rs:1110 is a pre-existing concern not introduced by this diff. Logged as delivery finding.

**Rule: No Stubbing** — All 5 emission sites are complete implementations with concrete fields. No placeholders.

**Rule: Don't Reinvent — Wire Up What Exists** — All calls use existing `WatcherEventBuilder` infrastructure. Test fix uses existing `sidequest_telemetry::emit()`. No reimplementation.

**Rule: Verify Wiring, Not Just Existence** — Verified end-to-end: `WatcherEventBuilder::send()` → `sidequest_telemetry::emit()` → `GLOBAL_TX.send()` → `subscribe_global()` receiver → watcher.rs WebSocket writer → GM panel. Pipeline confirmed at telemetry/lib.rs:196-199 and server/lib.rs:662-665.

**Rule: Every Test Suite Needs a Wiring Test** — `watcher_client_receives_broadcast_events()` in watcher_story_3_6_tests.rs is a full integration test: real TCP listener, WebSocket client, emit → receive → JSON assert. Satisfies wiring requirement.

**Rule: OTEL Observability Principle** — 5 new events cover 4 previously blind subsystem paths (region transitions, region discovery, save/load restore, session init location). Compliant.

### Observations

1. [VERIFIED] `region.transition` captures `from_location` before mutation — mod.rs:843 clones `ctx.current_location` before line 855 reassigns it. Ordering correct. Checked against No Silent Fallbacks rule — emits unconditionally in region mode.
2. [VERIFIED] `region.discovery` fires after `discovered_regions.push()` — mod.rs:857-864. `total_discovered` count includes the new region. Consistent with post-mutation snapshot pattern used by existing events.
3. [VERIFIED] `location.restored` uses `saved.snapshot.location` — connect.rs:113. Same value just assigned to `*current_location` at line 102. No stale data risk.
4. [VERIFIED] Test fix semantics preserved — `sidequest_telemetry::emit()` sends on the same `GLOBAL_TX` broadcast channel that `state.subscribe_watcher()` → `subscribe_global()` reads from. Confirmed at telemetry/lib.rs:170,188-189,196-199. `test_app_state()` → `new_with_game_service()` calls `init_global_channel()` at lib.rs:302.
5. [VERIFIED] No double-fire between `location.restored` and `location.initialized` — restore fires in reconnect path (connect.rs:110), initialized fires in new session creation path (connect.rs:1096/1127). Separate code branches, no overlap.
6. [LOW] `region.transition` fires even when from == to (same location header repeated by narrator). Not a bug — consistent with room_graph behavior where self-loop exits are valid. OTEL should record all transitions for debugging.
7. [RULE] Pre-existing `.unwrap_or_default()` at connect.rs:1110-1116 silently collapses genre pack failures to empty string. New OTEL event at line 1127 only covers success. Logged as non-blocking delivery finding — pre-existing, not introduced by this diff.
8. [SILENT] No silent failures introduced — all 5 emissions use fire-and-forget pattern consistent with telemetry CLAUDE.md design ("Zero overhead when no subscribers connected"). `emit()` no-op without channel is intentional.

**Data flow traced:** Narrator location header → `extract_location_header()` → region mode check (rooms empty) → `region.transition` event → `location_valid = true` → `is_new` check → `region.discovery` event if new → `location_changed` event → ChapterMarker → MapUpdate. New events are purely observational — they do not alter the data flow.

**Wiring:** Events flow through global broadcast channel to `/ws/watcher` WebSocket endpoint. GM panel receives all events. Verified at telemetry/lib.rs:196 → server/watcher.rs writer task.

**Error handling:** `WatcherEventBuilder::send()` is fire-and-forget by design. Channel not initialized → no-op. No subscribers → silent ignore. This is the documented contract (telemetry CLAUDE.md).

**Security:** No user input flows into event fields unvalidated. Location strings come from narrator output (already processed) or save files (trusted). No injection risk in OTEL field values.

### Devil's Advocate

What if this code is broken? Let me argue against approval.

The most concerning aspect is the field naming inconsistency across location events. Room graph transitions use `from_room`/`to_room` (mod.rs:787-789), while the new region transitions use `from_location`/`to_location` (mod.rs:846-847). The generic `location_changed` event uses just `location` (mod.rs:910). The `location.restored` event uses `location` (connect.rs:113). A GM panel dashboard consuming these events needs to handle three different field naming schemes for what is conceptually "where the player is/was." This isn't a bug — it's a consistency gap that makes dashboard development harder.

Could a malicious narrator output crash anything? The location string flows directly into `.field("to_location", &location)`. The `field()` method takes `impl serde::Serialize` and wraps in `serde_json::Value`. Extremely long strings would bloat the event but not crash — broadcast channel has a capacity limit (CHANNEL_CAPACITY) and subscribers that lag get `RecvError::Lagged`, dropping old events. No memory exhaustion risk.

Could the `from_location` clone at mod.rs:843 capture stale state from a previous turn? No — `ctx.current_location` is the mutable reference to the dispatch loop's location state, updated only at line 855 within the same function call. No async yield point between capture and use.

Could the `total_discovered` count be wrong? It's read at line 863 after `push()` at line 857. The count includes the new region. If another async task concurrently pushes to `discovered_regions`... but `DispatchContext` is `&mut`, so exclusive access is guaranteed. No race condition.

The test fix removes `broadcast_state` clones. Could this cause AppState to be dropped too early, closing the broadcast channel? No — `state` is still alive (bound at the test function scope), and the server task holds its own clone. The global `GLOBAL_TX` is a `OnceLock<Sender>` — it lives for the process lifetime regardless of AppState clones.

The devil's advocate found nothing new beyond the field naming inconsistency (LOW severity, non-blocking). The code is sound.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** Location header → extract → region mode → `region.transition` → `region.discovery` (if new) → existing `location_changed` → ChapterMarker → MapUpdate. Events are additive observation only.
**Pattern observed:** Consistent use of `WatcherEventBuilder::new("location", StateTransition).field("event", "...")` at dispatch/mod.rs:844, dispatch/connect.rs:111,1096,1127 — clean component namespace for location telemetry.
**Error handling:** Fire-and-forget OTEL emission — documented contract per telemetry CLAUDE.md. No new error paths introduced.
**Wiring verified:** emit() → GLOBAL_TX → subscribe_global() → watcher.rs WebSocket writer → GM panel. Traced at telemetry/lib.rs:170-199 and server/lib.rs:662-665.
**Tests:** 19/19 green. Pre-existing test compilation fix (send_watcher_event → emit) is semantically correct — same broadcast channel.
[EDGE] N/A (disabled) | [SILENT] Clean — no new silent failures | [TEST] N/A (disabled) | [DOC] N/A (disabled) | [TYPE] N/A (disabled) | [SEC] N/A (disabled) | [SIMPLE] N/A (disabled) | [RULE] 1 non-blocking finding (pre-existing unwrap_or_default, logged as delivery finding)

**Handoff:** To Grand Admiral Thrawn for finish-story

## Design Deviations

### Dev (implementation)
- **Fixed pre-existing test failures in watcher_story_3_6_tests.rs** → ✓ ACCEPTED by Reviewer: pre-existing compilation failures blocking `cargo test`; fix uses correct `sidequest_telemetry::emit()` which routes through the same global broadcast channel. Semantically equivalent to the intended behavior.
  - Spec source: Story 26-8 scope (OTEL watcher events only)
  - Spec text: "Add OTEL watcher events for location transitions"
  - Implementation: Also fixed 6 pre-existing compilation errors in watcher tests (`send_watcher_event` → `sidequest_telemetry::emit`)
  - Rationale: Tests were blocking `cargo test` entirely — broken tests are an observability blind spot, consistent with the story's goal
  - Severity: minor
  - Forward impact: none — tests now correctly use the global telemetry channel as production code does

## Implementation Notes

### Observability Blind Spot

Location transitions are a core game mechanic but have zero OTEL visibility. The GM panel cannot verify whether location changes are actually being processed or whether they're silently failing.

**Current State:**
- Location transitions handled in sidequest-game (character movement, location updates)
- No watcher events emitted during transitions
- GM panel has no visibility into transition state or failures
- Violates observability principle: "If a subsystem isn't emitting OTEL spans, you can't tell whether it's engaged or whether Claude is just improvising"

### Implementation Strategy

1. **Identify transition points** in `sidequest-game` where location changes occur:
   - Character movement actions
   - Teleport/warp mechanics
   - Environmental transitions (entering buildings, leaving areas)
   - Location state changes in game_state

2. **Add OTEL watcher events** for each transition:
   - Event: `LocationTransition` (or similar naming)
   - Fields: old_location, new_location, reason/action_type, character_id
   - Emitted via tracing infrastructure (matches existing WatcherEvent pattern)

3. **Verify wiring** to GM panel dashboard:
   - Ensure events flow through dispatcher to UI watcher view
   - Confirm events appear in OTEL trace spans
   - Test with actual game movement

### Key Files

- `sidequest-game/src/` — location/character state management
- `sidequest-protocol/src/messages.rs` — WatcherEvent types
- `sidequest-server/src/watcher.rs` — watcher event dispatch
- GM panel dashboard — verification point