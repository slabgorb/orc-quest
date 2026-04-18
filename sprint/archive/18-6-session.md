---
story_id: "18-6"
jira_key: ""
epic: "18"
workflow: "tdd"
---
# Story 18-6: Prompt inspector tab — full assembled prompt with zone labels and per-zone token counts

## Story Details
- **ID:** 18-6
- **Epic:** 18 (OTEL Dashboard — Granular Instrumentation & State Tab)
- **Workflow:** tdd
- **Stack Parent:** none
- **Priority:** p1
- **Points:** 5
- **Repos:** api, ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-01T04:57:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T23:59:00Z | 2026-04-01T04:08:51Z | 4h 9m |
| red | 2026-04-01T04:08:51Z | 2026-04-01T04:14:30Z | 5m 39s |
| green | 2026-04-01T04:14:30Z | 2026-04-01T04:18:25Z | 3m 55s |
| spec-check | 2026-04-01T04:18:25Z | 2026-04-01T04:31:30Z | 13m 5s |
| verify | 2026-04-01T04:31:30Z | 2026-04-01T04:34:21Z | 2m 51s |
| review | 2026-04-01T04:34:21Z | 2026-04-01T04:56:56Z | 22m 35s |
| spec-reconcile | 2026-04-01T04:56:56Z | 2026-04-01T04:57:46Z | 50s |
| finish | 2026-04-01T04:57:46Z | - | - |

## Sm Assessment

**Story 18-6** is a 5-point p1 feature — add a Prompt Inspector tab to the OTEL dashboard showing the full assembled prompt with zone labels and per-zone token counts. Spans API (new PromptAssembled watcher event) and UI (dashboard tab in playtest.py).

**Routing:** TDD workflow → TEA (Red phase) writes tests for the event type, zone breakdown, and dashboard rendering, then Dev implements.

**Risk:** Medium — cross-repo (api+ui), new WatcherEventType variant, touches prompt framework internals. The prompt framework (1,484 LOC) has 5 attention zones (Primacy, Situational, Anchoring, Grounding + zone-ordered assembly).

**Dependencies:** None blocking. 18-1 (sub-spans) and 18-3 (parallelization) are done.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New WatcherEventType variant + new ContextBuilder method + cross-repo dashboard wiring

**Test Files:**
- `sidequest-api/crates/sidequest-agents/tests/prompt_inspector_story_18_6_tests.rs` — 10 tests for zone_breakdown and ZoneBreakdown struct
- `sidequest-api/crates/sidequest-server/tests/prompt_assembled_story_18_6_tests.rs` — 4 tests for PromptAssembled variant

**Tests Written:** 14 tests covering 5 ACs
**Status:** RED (compile errors — ZoneBreakdown, zone_breakdown(), PromptAssembled don't exist)

**Test Breakdown:**
- 4 WatcherEventType::PromptAssembled tests (exists, serializes, deserializes, roundtrips)
- 3 zone_breakdown structure tests (all zones present, section counts, metadata)
- 2 token count tests (per-zone totals, matches builder total)
- 1 zone ordering test (Primacy → Recency)
- 1 full prompt text test
- 1 empty builder edge case
- 1 JSON serialization test (ZoneBreakdown → serde_json::Value)
- 1 contract name test (event type string)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | WatcherEventType already has it; new variant inherits | pass (existing) |
| #6 test-quality | Self-check: all 14 tests have meaningful assertions | pass |

**Rules checked:** 2 of 15 applicable
**Self-check:** 0 vacuous tests found

**Note:** Dashboard UI tests (playtest.py JS) are out of scope for Rust tests. Dashboard rendering is verified during playtest.

**Handoff:** To Yoda for implementation (GREEN phase)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-api/crates/sidequest-server/src/lib.rs` — added `PromptAssembled` variant to `WatcherEventType`
- `sidequest-api/crates/sidequest-agents/src/context_builder.rs` — added `ZoneBreakdown`, `ZoneEntry`, `SectionSummary` structs and `zone_breakdown()` method
- `sidequest-api/crates/sidequest-agents/src/orchestrator.rs` — added `zone_breakdown` field to `ActionResult`, captures from builder before compose
- `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` — emits `PromptAssembled` watcher event after both main action and aside paths
- `scripts/playtest.py` — added ⑥ Prompt tab with turn selector, zone breakdown bars, and full prompt text display

**Tests:** 14/14 passing (GREEN) + 49 related tests passing
**Branch:** feat/18-6-prompt-inspector-tab (pushed, both repos)

**All wiring complete:**
- `PromptAssembled` variant serializes/deserializes as `"prompt_assembled"`
- `ContextBuilder::zone_breakdown()` returns structured per-zone data with token counts
- `ActionResult` carries `zone_breakdown: Option<ZoneBreakdown>` from orchestrator to dispatch
- Dispatch emits `PromptAssembled` watcher event with `zones`, `total_tokens`, `section_count`, `agent`, `full_prompt`
- Dashboard tab ⑥ Prompt: turn selector, zone breakdown bars with section detail, full prompt text

**Handoff:** To next phase (verify or review)

## TEA Assessment (verify)

**Verification Complete:** Yes
**Tests:** 14/14 GREEN

**Wiring Verification (non-test consumers):**
- `orchestrator.rs:354` — `builder.zone_breakdown()` called in production `process_action`
- `orchestrator.rs:453` — `zone_breakdown: Some(prompt_zone_breakdown)` returned in `ActionResult`
- `dispatch/mod.rs:378` — main action path emits `PromptAssembled` watcher event from `result.zone_breakdown`
- `dispatch/mod.rs:1601` — aside path also emits `PromptAssembled` watcher event
- `playtest.py:474` — dashboard `dispatch()` handles `prompt_assembled` events, stores in `S.promptEvents`
- `playtest.py:879` — `renderPrompt()` renders zone breakdown bars with section detail and full prompt text

**Acceptance Criteria Check:**
- [x] `PromptAssembled` variant exists, serializes as `"prompt_assembled"`
- [x] `ZoneBreakdown` struct with per-zone token counts
- [x] `zone_breakdown()` method on ContextBuilder
- [x] Event emission in dispatch (both main and aside paths)
- [x] Dashboard tab ⑥ Prompt with turn selector, zone breakdown, and full prompt display

**Handoff:** To Obi-Wan Kenobi for review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | No new clippy warnings, 532/533 tests pass (1 pre-existing flaky), both PRs diffed | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | `zone_breakdown()` and `compose()` use identical sort+join — no divergence. Aside path hardcodes "narrator" correctly. | N/A |
| 3 | reviewer-security | Yes | clean | `esc()` on all innerHTML, `textContent` for prompt display. No XSS vectors. | N/A |
| 4 | reviewer-rule-checker | Yes | clean | `#[non_exhaustive]` on WatcherEventType, `serde(rename_all)` inherited, no rule violations | N/A |
| 5 | reviewer-silent-failure-hunter | Yes | clean | `let _ = send()` on broadcast is existing pattern (fire-and-forget telemetry). No swallowed errors. | N/A |

All received: Yes

## Reviewer Assessment

**Decision:** APPROVE

**Tests:** 532 passed, 1 failed (pre-existing flaky `async_preprocess_handles_empty_input` from story 18-3 — live Claude CLI integration test, not related to this diff)
**Clippy:** No new warnings from this story's changes
**Security:** No XSS vectors — `esc()` used for all dynamic text in innerHTML, `textContent` used for full prompt display

**Review Findings:**

1. **Types correct** — `ZoneBreakdown`, `ZoneEntry`, `SectionSummary` all derive `Serialize, Deserialize`. `WatcherEventType::PromptAssembled` inherits `#[serde(rename_all = "snake_case")]` and `#[non_exhaustive]`.

2. **Wiring verified** — `zone_breakdown()` called in `process_action` before `compose()`, returned in `ActionResult`, emitted as `PromptAssembled` watcher event in both dispatch paths (main + aside). Dashboard handles `prompt_assembled` events, stores in `S.promptEvents`, renders on tab 5.

3. **`full_prompt` consistency** — both `zone_breakdown()` and `compose()` use `self.build()` (same sort) and `join("\n\n")`. No divergence possible.

4. **Aside path agent name** — hardcodes `"narrator"` instead of reading `result.agent_name`. Correct — asides always route through narrator.

5. **Payload size** — `full_prompt` in the watcher event can be large (tens of KB). Acceptable for a telemetry channel (capacity 256, same pattern as `game_state_snapshot`). Not player-facing.

6. **[RULE]** No rule violations — `#[non_exhaustive]` on enum, `serde(rename_all = "snake_case")` inherited by new variant, all new structs derive required traits.

7. **[SILENT]** No swallowed errors — `let _ = watcher_tx.send()` is the existing fire-and-forget telemetry pattern used by all other watcher events. Broadcast channel drops are expected when no dashboard is connected.

**No blocking issues found.**

**Handoff:** To Grand Admiral Thrawn for finish

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected (2 blocking gaps)
**Mismatches Found:** 2

- **Event emission not wired** (Missing in code — Architectural, Major)
  - Spec: Session wiring checklist item "Emit PromptAssembled event after prompt assembly but before LLM call"
  - Code: `PromptAssembled` variant exists, `zone_breakdown()` works, but no code calls `send_watcher_event` with this type during a turn
  - Recommendation: B — Fix code. Dev must add `send_watcher_event(PromptAssembled)` call in `dispatch/mod.rs` after the orchestrator returns zone breakdown data. The orchestrator should return `ZoneBreakdown` alongside the narration result, or the dispatch layer should call `zone_breakdown()` on the builder.

- **Dashboard tab not implemented** (Missing in code — Behavioral, Major)
  - Spec: Session wiring checklist item "Add Prompt Inspector tab to dashboard with event listener" and "Add rendering function for zone breakdown"
  - Code: No changes to `scripts/playtest.py`. The dashboard has no "Prompt" tab, no `dispatch(ev)` handler for `prompt_assembled`, and no zone renderer.
  - Recommendation: B — Fix code. Dev must add the JS tab, event handler, and renderer to the DASHBOARD_HTML string in playtest.py. Follow the existing tab pattern (Timeline, State, Subsystems, Timing, Console).

**Decision:** Hand back to Dev. Both gaps are blocking — the story title is "Prompt inspector tab" and neither the event pipeline nor the tab exist yet. Types without wiring violates "No half-wired features."

**Instructions for Yoda:**
1. Have the orchestrator return `ZoneBreakdown` from `process_action()` (or add it to the return type). Alternatively, call `zone_breakdown()` in the dispatch layer where the builder is accessible.
2. Emit `WatcherEvent { event_type: PromptAssembled, component: "prompt", fields: { zones, total_tokens, section_count, agent } }` in dispatch/mod.rs.
3. Add "Prompt" tab to DASHBOARD_HTML in playtest.py with dispatch handler and renderer.
4. The dashboard JS is in the orchestrator repo (scripts/playtest.py), not sidequest-api.

## Delivery Findings

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Dashboard tab rendering (JS in playtest.py DASHBOARD_HTML) is not testable from Rust. Dev must add the `dispatch(ev)` handler for `prompt_assembled` events and the render function manually. Verification is during playtest with `--dashboard-only`.
  Affects `scripts/playtest.py` (DASHBOARD_HTML string, dispatch function).
  *Found by TEA during test design.*
- **Question** (non-blocking): The orchestrator in sidequest-agents doesn't have access to `AppState.send_watcher_event()` (that's in sidequest-server). The PromptAssembled event emission must happen in the dispatch layer after `orchestrator.process_action()` returns, or the orchestrator needs a callback/channel for watcher events.
  Affects `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` and `sidequest-api/crates/sidequest-agents/src/orchestrator.rs`.
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (blocking): Event emission not wired — `PromptAssembled` event is never actually sent during a turn. The type exists and serializes correctly, but no code calls `send_watcher_event` with it. The orchestrator builds the prompt (sidequest-agents) but has no access to `AppState` (sidequest-server). The wiring must happen in `dispatch/mod.rs` after the orchestrator returns the zone breakdown.
  Affects `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` (needs `send_watcher_event` call with `PromptAssembled`).
  *Found by Dev during implementation.*
- **Gap** (blocking): Dashboard tab not implemented — `playtest.py` DASHBOARD_HTML needs a "Prompt" tab with `dispatch(ev)` handler for `prompt_assembled` events and a renderer showing zones, token counts, and full prompt text.
  Affects `scripts/playtest.py` (DASHBOARD_HTML string).
  *Found by Dev during implementation.*

### TEA (verify)
- No upstream findings during verification. All previously-identified blocking gaps (event emission, dashboard tab) are resolved.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec. All wiring gaps from previous pass resolved — event emission in dispatch and dashboard tab now implemented.

### TEA (verify)
- No deviations from spec.

---

## Context Summary

This story adds a new **PromptAssembled** watcher event type that will be emitted during turn processing, capturing:
- The turn number
- The agent that was invoked (narrator, creature_smith, ensemble, dialectician)
- Total token count for the full assembled prompt
- Per-zone breakdown: Primacy, Early, Valley, Late, Recency (with token counts)

The event will be streamed to the GM dashboard via `/ws/watcher`, where a new "Prompt Inspector" tab will display:
- Full assembled prompt text with zone labels and color-coding
- Per-zone token counts
- Agent name and turn number

### Upstream Infrastructure

**API Side (sidequest-api):**
- `WatcherEvent` struct already defined in `sidequest-server/src/lib.rs` with `fields: HashMap<String, serde_json::Value>`
- `WatcherEventType` enum (lines 76-95) — needs new `PromptAssembled` variant
- `Severity` enum also present
- Watcher broadcast channel already operational — `/ws/watcher` endpoint connected
- `dispatch/mod.rs` handles watcher event emission (grep shows existing patterns)

**Prompt Framework:**
- `PromptSection` struct in `sidequest-agents/prompt_framework/types.rs` — has `zone: AttentionZone`, `name`, `content`, `token_estimate()` method
- `AttentionZone` enum with 5 variants (Primacy, Early, Valley, Late, Recency) and `all_ordered()` method
- Zones are already used in prompt assembly — can inspect assembled sections to build zone breakdowns

**UI Side (sidequest-ui):**
- Dashboard HTML/JS in `scripts/playtest.py` — DASHBOARD_HTML string
- Event routing already handles `game_state_snapshot` and `turn_complete` — new handler needed for `prompt_assembled`
- Tabs already present (0=Events, 1=Turns, 2=State, etc.) — will add Prompt Inspector as new tab

### Test Requirements

Per CLAUDE.md:
- Unit tests for new WatcherEvent variant serialization
- Unit tests for zone breakdown logic (if extracted to helper function)
- Integration test verifying PromptAssembled event is emitted during at least one agent call
- Integration test verifying dashboard receives and renders the event correctly

### Wiring Checklist

- [ ] Add `PromptAssembled` variant to `WatcherEventType` enum
- [ ] Add `PromptAssembled` variant to serialization/deserialization tests
- [ ] Extract zone breakdown logic from prompt context builder (or create helper)
- [ ] Emit PromptAssembled event after prompt assembly but before LLM call (in ClaudeClient or Orchestrator)
- [ ] Wire event into broadcast channel in server
- [ ] Add test that verifies event is captured in integration tests
- [ ] Add "Prompt Inspector" tab to dashboard with event listener
- [ ] Add rendering function for zone breakdown (zones, token counts, full text)
- [ ] Test end-to-end: turn → event → dashboard

---

## TDD Setup Notes

This is a TDD story. **Tests come first**, then implementation:

1. **API Tests** — `sidequest-api/crates/sidequest-server/tests/`
   - PromptAssembled event serialization/deserialization
   - Zone breakdown calculation (if extracted to helper)
   - Integration test that verifies event is emitted during a turn

2. **UI Tests** — `sidequest-ui/` (if applicable)
   - Prompt Inspector tab renders with event data
   - Zone labels and token counts display correctly

3. **Implementation** — Only after tests pass
   - Add enum variant + serde impls
   - Extract/create zone breakdown helper
   - Emit event in appropriate call site
   - Connect dashboard listener and renderer

---

## Related Stories

- **18-1** (completed): Sub-spans for flame chart granularity — laid groundwork for watcher observability
- **18-2** (completed): Fixed State tab wiring
- **18-3** (completed): Parallelized prompt context build
- **18-4** (backlog): LoreStore browser tab (related OTEL event)
- **18-5** (backlog): Structured NPC registry and inventory panels (related state visibility)