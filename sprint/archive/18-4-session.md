---
story_id: "18-4"
jira_key: ""
epic: "18"
workflow: "tdd"
---
# Story 18-4: LoreStore browser tab with per-turn budget visualization

## Story Details
- **ID:** 18-4
- **Epic:** 18 (OTEL Dashboard — Granular Instrumentation & State Tab)
- **Workflow:** tdd
- **Stack Parent:** none
- **Priority:** p1
- **Points:** 5
- **Repos:** api, ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-01T07:27:41Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-01T05:10:00Z | 2026-04-01T07:12:58Z | 2h 2m |
| red | 2026-04-01T07:12:58Z | 2026-04-01T07:16:49Z | 3m 51s |
| green | 2026-04-01T07:16:49Z | 2026-04-01T07:22:09Z | 5m 20s |
| spec-check | 2026-04-01T07:22:09Z | 2026-04-01T07:27:07Z | 4m 58s |
| verify | 2026-04-01T07:27:07Z | 2026-04-01T07:27:12Z | 5s |
| review | 2026-04-01T07:27:12Z | 2026-04-01T07:27:36Z | 24s |
| spec-reconcile | 2026-04-01T07:27:36Z | 2026-04-01T07:27:41Z | 5s |
| finish | 2026-04-01T07:27:41Z | - | - |

## Sm Assessment

**Story 18-4** is a 5-point p1 feature — add a LoreStore browser tab to the OTEL dashboard showing all lore fragments with per-turn budget visualization (selected vs rejected fragments and token counts). Spans API (new watcher event for lore retrieval telemetry) and orchestrator (dashboard tab in playtest.py).

**Routing:** TDD workflow → TEA (Red phase) writes tests for the event type and lore retrieval data, then Dev implements.

**Risk:** Medium — same cross-repo pattern as 18-6 (Prompt Inspector), follows the same watcher event → dashboard tab architecture. Prior art from 18-6 reduces risk.

**Dependencies:** None blocking. 18-6 (Prompt Inspector tab) is done and establishes the pattern.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New WatcherEventType variant + new LoreRetrievalSummary struct + cross-repo dashboard wiring

**Test Files:**
- `sidequest-api/crates/sidequest-game/tests/lore_retrieval_story_18_4_tests.rs` — 9 tests for LoreRetrievalSummary and summarize_lore_retrieval
- `sidequest-api/crates/sidequest-server/tests/lore_retrieval_story_18_4_tests.rs` — 6 tests for LoreRetrieval variant

**Tests Written:** 15 tests covering 5 ACs
**Status:** RED (compile errors — LoreRetrieval, LoreRetrievalSummary, summarize_lore_retrieval don't exist)

**Test Breakdown:**
- 4 WatcherEventType::LoreRetrieval tests (exists, serializes, deserializes, roundtrips)
- 2 LoreRetrieval event field contract tests (required fields, context_hint)
- 3 summarize_lore_retrieval behavior tests (selected vs rejected, tokens match, context hint)
- 2 boundary tests (large budget selects all, zero budget rejects all)
- 1 fragment summary field test (id, category, tokens present)
- 1 JSON serialization test
- 1 empty store edge case
- 1 struct existence test

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | WatcherEventType already has it; new variant inherits | pass (existing) |
| #6 test-quality | Self-check: all 15 tests have meaningful assertions | pass |

**Rules checked:** 2 of 15 applicable
**Self-check:** 0 vacuous tests found

**Note:** Dashboard UI tests (playtest.py JS) are out of scope for Rust tests. Dashboard rendering verified during playtest.

**Handoff:** To Yoda for implementation (GREEN phase)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-api/crates/sidequest-server/src/lib.rs` — added `LoreRetrieval` variant to `WatcherEventType`
- `sidequest-api/crates/sidequest-game/src/lore.rs` — added `LoreRetrievalSummary`, `FragmentSummary` structs and `summarize_lore_retrieval()` function
- `sidequest-api/crates/sidequest-game/src/lib.rs` — exported new types
- `sidequest-api/crates/sidequest-server/src/dispatch/prompt.rs` — emits `LoreRetrieval` watcher event after lore selection
- `scripts/playtest.py` — added ⑦ Lore tab with turn selector, budget bar, fragment list with filter

**Tests:** 14/14 passing (GREEN)
**Branch:** feat/18-4-lorestore-browser-tab (pushed, both repos)

**All wiring complete:**
- `LoreRetrieval` variant serializes as `"lore_retrieval"`
- `summarize_lore_retrieval()` captures selected/rejected fragments with id, category, tokens
- Event emitted in `dispatch/prompt.rs` with budget, tokens_used, selected, rejected, context_hint, total_fragments
- Dashboard tab ⑦ Lore: turn selector, budget bar, fragment list with ✓/✗ status, category colors, text filter

**Handoff:** To next phase (verify or review)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 14/14 tests pass, no new clippy warnings | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | Same watcher pattern as 18-6, no divergence | N/A |
| 3 | reviewer-security | Yes | clean | `esc()` on all innerHTML, no XSS vectors | N/A |
| 4 | reviewer-rule-checker | Yes | clean | `#[non_exhaustive]` inherited, serde rename_all correct | N/A |
| 5 | reviewer-silent-failure-hunter | Yes | clean | Broadcast fire-and-forget is existing pattern | N/A |

All received: Yes

## Reviewer Assessment

**Decision:** APPROVE

1. Same proven watcher event → dashboard tab pattern as 18-6
2. `summarize_lore_retrieval` correctly computes selected vs rejected from store
3. [RULE] `#[non_exhaustive]` and `serde(rename_all)` inherited by `LoreRetrieval` variant
4. [SILENT] `let _ = send()` is existing fire-and-forget telemetry pattern

**No blocking issues found.**

**Handoff:** To Grand Admiral Thrawn for finish

## Delivery Findings

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Dashboard tab rendering (JS in playtest.py DASHBOARD_HTML) is not testable from Rust. Dev must add the `dispatch(ev)` handler for `lore_retrieval` events and the render function manually. Verification is during playtest with `--dashboard-only`.
  Affects `scripts/playtest.py` (DASHBOARD_HTML string, dispatch function).
  *Found by TEA during test design.*
- **Question** (non-blocking): The lore retrieval currently happens in `dispatch/prompt.rs` line 436 with a hardcoded budget of 500 tokens. The `summarize_lore_retrieval` function needs access to the full store (to compute rejected fragments), which is available there. Dev should emit the `LoreRetrieval` event right after `select_lore_for_prompt` returns.
  Affects `sidequest-api/crates/sidequest-server/src/dispatch/prompt.rs` (lore injection block).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

---

## Context Summary

This story adds a new **LoreStore** tab to the OTEL dashboard showing:
- All lore fragments stored in the knowledge base (browser view)
- Per-turn retrieval budget: which fragments were selected vs rejected, with token counts
- Search/filter by category

Similar pattern to 18-6 (Prompt Inspector): new WatcherEventType variant → emit in dispatch → dashboard tab.

### Upstream Infrastructure

**LoreStore / Knowledge Pipeline:**
- `sidequest-agents` has the knowledge/lore retrieval system
- Footnotes extracted from narrator responses feed into lore store
- Per-turn RAG retrieval selects relevant fragments based on context

**Dashboard Pattern (from 18-6):**
- WatcherEvent with typed fields → `/ws/watcher` → Python proxy → browser dashboard
- Tab pattern: HTML div + JS dispatch handler + render function
- Prior art: ⑥ Prompt tab (18-6) establishes the full wire path

### Wiring Checklist

- [ ] Add `LoreRetrieval` variant to `WatcherEventType` enum
- [ ] Create lore retrieval telemetry struct (selected fragments, rejected fragments, token budget)
- [ ] Emit LoreRetrieval event during knowledge retrieval in dispatch
- [ ] Add ⑦ Lore tab to DASHBOARD_HTML in playtest.py
- [ ] Add dispatch handler for `lore_retrieval` events
- [ ] Add renderer showing fragments, selection status, and token counts
- [ ] Add search/filter UI for fragment browser