---
story_id: "21-3"
epic: "21"
workflow: "tdd"
---

# Story 21-3: Dashboard Claude tab — tool timeline, token breakdown, cost accumulator

## Story Details

- **ID:** 21-3
- **Epic:** 21 — Claude Subprocess OTEL Passthrough — See Inside the Black Box (ADR-058)
- **Workflow:** tdd
- **Repos:** orchestrator (React dashboard), sidequest-api (optional for later turns)
- **Points:** 5
- **Priority:** p1

## Acceptance Criteria

- Tab 8 (Claude) appears in dashboard tab bar
- Tool call timeline renders with duration bars per tool invocation
- Token breakdown shows input/output/cache read/cache creation per turn
- Running cost accumulator displays total spend
- Tool failures highlighted with error indicator
- Events correlate to game turns via timestamp
- Tab badge shows count of tool invocations

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-02T16:40:16Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T17:32:00Z | 2026-04-02T16:13:39Z | -4701s |
| red | 2026-04-02T16:13:39Z | 2026-04-02T16:19:55Z | 6m 16s |
| green | 2026-04-02T16:19:55Z | 2026-04-02T16:23:36Z | 3m 41s |
| spec-check | 2026-04-02T16:23:36Z | 2026-04-02T16:24:50Z | 1m 14s |
| verify | 2026-04-02T16:24:50Z | 2026-04-02T16:28:37Z | 3m 47s |
| review | 2026-04-02T16:28:37Z | 2026-04-02T16:38:46Z | 10m 9s |
| spec-reconcile | 2026-04-02T16:38:46Z | 2026-04-02T16:40:16Z | 1m 30s |
| finish | 2026-04-02T16:40:16Z | - | - |

## Context & Dependencies

### Upstream Work

- **21-1** (DONE): Split playtest.py into focused modules
- **21-2** (DONE): OTLP receiver in playtest dashboard — parse and broadcast Claude Code telemetry

The playtest dashboard receives claude_otel WebSocket events with:
- Tool invocation spans (tool name, duration, success/failure)
- Token stats (input, output, cache read, cache creation tokens)
- Timestamp data for correlation to game turns

### Feature Description

Add a new "Claude" tab (tab 8) to the playtest dashboard HTML/JS. This tab consumes the OTEL telemetry data already being broadcast from the OTLP receiver (story 21-2) and presents:

1. **Tool Timeline** — Flame chart pattern (reuse from tab 1) showing tool invocations with duration bars
2. **Token Breakdown** — Table showing input/output/cache read/cache creation tokens per turn
3. **Cost Accumulator** — Running total of Claude API spend (using OpenAI pricing model)
4. **Tool Status** — Success/failure indicators on tool invocations
5. **Turn Correlation** — Events linked to game turns via timestamp proximity to watcher turn events
6. **Tab Badge** — Shows count of tool invocations

### Data Flow

```
OTLP Receiver (playtest_otlp.py)
  ↓ (POST /v1/logs, /v1/metrics, /v1/traces)
Playtest Dashboard (playtest_dashboard.py)
  ↓ WebSocket broadcast {source: "claude_otel", ...}
Dashboard Browser (orchestrator/playtest.html)
  ↓ Claude tab JS handler
Claude Tab (new)
  ├─ Tool Timeline
  ├─ Token Breakdown
  ├─ Cost Accumulator
  └─ Turn Correlation
```

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- **Improvement** (non-blocking): Pre-existing empty catch block in `ws.onmessage` at line 1042 silently swallows JSON parse errors. Affects `scripts/playtest_dashboard.py` (add `console.error` in catch). *Found by TEA during test verification.*

### Reviewer (code review)
- **Gap** (blocking): switchTab(7) only calls renderClaudeTimeline(), not renderClaudeTokens(). Token breakdown blank on tab activation. Affects `scripts/playtest_dashboard.py` (add renderClaudeTokens() call). *Found by Reviewer during code review.*
- **Gap** (blocking): clearAll() does not reset S.claudeEvents, S.claudeTokens, or tab7-badge. Stale data persists after clear. Affects `scripts/playtest_dashboard.py` (reset Claude state in clearAll). *Found by Reviewer during code review.*
- **Gap** (blocking): Math.max(...S.claudeEvents.map(...)) throws RangeError at ~10k events due to V8 call stack limit on spread. Affects `scripts/playtest_dashboard.py` (use reduce instead). *Found by Reviewer during code review.*

## Design Deviations

None at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found. TEA and Dev subsections are accurate. The spec-check pricing model note (spec says "OpenAI pricing model", code uses Claude Opus pricing) was correctly identified as a trivial spec imprecision — the implementation is correct. All 3 reviewer gaps (B1/B2/B3) were fixed before merge. No AC deferrals.

## Reviewer Assessment

**Decision:** REJECT → APPROVED (after fixes)
**Subagents:** preflight, edge-hunter, security, test-analyzer, simplifier

[EDGE] 3 HIGH bugs found and fixed (B1/B2/B3). 5 medium/low dismissed.
[SILENT] No silent failure patterns in new Claude code. Pre-existing ws.onmessage catch out of scope.
[TEST] 2 confirmed (missing switchTab/clearAll test coverage). 8 deferred.
[DOC] No stale or misleading comments.
[TYPE] Not applicable — embedded JavaScript.
[SEC] All 4 findings dismissed — low risk for local playtest dashboard.
[SIMPLE] 2 confirmed (overlap with B1/B2). 4 dismissed.
[RULE] All applicable JS rules satisfied: strict equality (#4), esc() (#5), no empty catches (#1).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | Pre-existing 21-2 test failure (not introduced by 21-3) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 8 findings — 3 HIGH (switchTab, clearAll, Math.max overflow) | confirmed 3, dismissed 5 |
| 3 | reviewer-silent-failure-hunter | Yes | clean | No swallowed errors in new Claude code; pre-existing ws.onmessage catch noted by TEA | N/A |
| 4 | reviewer-test-analyzer | Yes | findings | 10 findings — 3 vacuous assertions, missing clearAll/switchTab tests | confirmed 2, deferred 8 |
| 5 | reviewer-comment-analyzer | Yes | clean | No misleading comments; code is self-documenting inline JS | N/A |
| 6 | reviewer-type-design | Yes | clean | No type contracts in embedded JS dashboard; not applicable | N/A |
| 7 | reviewer-security | Yes | findings | 4 findings — innerHTML dur coercion (medium), parseInt radix (low), spread (low) | dismissed 4 (low risk for local playtest dashboard) |
| 8 | reviewer-simplifier | Yes | findings | 6 findings — switchTab/clearAll/errCount patterns | confirmed 2, dismissed 4 |
| 9 | reviewer-rule-checker | Yes | clean | Python/JS rules checked; strict equality used, esc() applied, no silent catches | N/A |

All received: Yes

### Specialist Tags

- [EDGE] 3 HIGH bugs found and fixed: switchTab wiring (B1), clearAll reset (B2), Math.max overflow (B3). 5 medium/low findings dismissed as acceptable for playtest dashboard.
- [SILENT] No silent failure patterns in new Claude tab code. Pre-existing ws.onmessage empty catch is out of scope (noted by TEA as delivery finding).
- [TEST] 2 confirmed: switchTab(7) missing renderClaudeTokens test, clearAll missing Claude reset test. 8 deferred: vacuous assertions and missing integration tests are test debt, non-blocking.
- [DOC] No misleading or stale comments. Inline JS is appropriately self-documenting.
- [TYPE] Not applicable — embedded JavaScript in HTML string, no typed interfaces.
- [SEC] All 4 findings dismissed: dur coercion is numeric in practice (OTLP spec), parseInt radix low risk, spread safe in V8, no secrets in diff.
- [SIMPLE] 2 confirmed (overlap with EDGE B1/B2). 4 dismissed: errCount O(n) filter acceptable at expected volumes, dispatch consolidation and updateAll dispatch table are out of scope.
- [RULE] Strict equality used for claude_otel check (JS #4). esc() applied in renderClaudeTimeline (JS #5). No empty catches in Claude handlers (JS #1). Rules satisfied.

### Required Fixes (blocking merge)

- **B1: switchTab(7) missing renderClaudeTokens()** — Token breakdown blank on tab switch. Half-wired. Fix: `if (i===7) { renderClaudeTimeline(); renderClaudeTokens(); }`
- **B2: clearAll() doesn't reset Claude state** — Claude tab retains stale data after clear while all other tabs reset. Fix: add `S.claudeEvents.length=0; S.claudeTokens={input:0,output:0,cache_read:0,cache_creation:0};` to clearAll()
- **B3: Math.max spread overflow** — `Math.max(...array)` throws RangeError at ~10k events. Fix: `S.claudeEvents.reduce((m, e) => Math.max(m, e.duration_ms || 1), 1)`

### Noted (non-blocking)

- [SEC] parseInt missing radix 10 (low risk, OTEL timestamps always numeric)
- [SEC] `{ ...ev }` spread copies all external fields (V8 prototype-safe)
- [TEST] 3 vacuous test assertions (test debt, not impl-blocking)
- [TEST] No end-to-end wiring test (impractical for embedded HTML/JS)
- [SILENT] No silent failure patterns in new Claude code; pre-existing ws.onmessage catch noted by TEA
- [RULE] All applicable JS rules satisfied: strict equality (#4), esc() usage (#5), no empty catches (#1)
- [DOC] No stale or misleading comments
- [TYPE] Not applicable for embedded JavaScript
- [SIMPLE] errCount O(n) filter acceptable at expected volumes
- [EDGE] 5 medium/low edge findings dismissed (NaN guards, negative values, ISO timestamps)

**Re-review:** All 3 fixes verified in commit bacf399. 31/31 GREEN.
**Final Decision:** APPROVED
**PR:** slabgorb/orc-quest#48 — merged to main (squash)
**Handoff:** To SM for finish

### Specialist Findings Summary

- [EDGE] 3 HIGH bugs found and fixed (B1/B2/B3). 5 medium/low dismissed.
- [SILENT] No silent failure patterns in new Claude code. Pre-existing ws.onmessage catch out of scope.
- [TEST] 2 confirmed (missing switchTab/clearAll test coverage). 8 deferred (vacuous assertions, integration tests).
- [DOC] No stale or misleading comments. Self-documenting inline JS.
- [TYPE] Not applicable — embedded JavaScript, no typed interfaces.
- [SEC] All 4 findings dismissed — low risk for local playtest dashboard.
- [SIMPLE] 2 confirmed (overlap with B1/B2). 4 dismissed.
- [RULE] All applicable JS rules satisfied: strict equality (#4), esc() (#5), no empty catches (#1).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 5 findings | Duplicated regex extraction in tests (3x), extractable helpers |
| simplify-quality | 3 findings | Empty catch in ws.onmessage (pre-existing), type safety, test fragility |
| simplify-efficiency | 7 findings | Token type if-chain, pricing calc duplication, test regex duplication |

**Applied:** 2 high-confidence fixes
1. Token type dispatch: 4 if-else branches → `if (tt in S.claudeTokens) S.claudeTokens[tt] += ev.value` (1 line)
2. Test helper: extracted `_find_claude_functions()` to eliminate 4x duplicated regex

**Flagged for Review:** 3 medium-confidence findings
- dispatch() claude_otel branch consolidation (would change control flow)
- updateAll() if-chain → dispatch table (out of scope, touches all tabs)
- conftest.py fixtures for dashboard tests (scope creep for single file)

**Noted:** 2 low-confidence observations
- Brittle regex in test (acceptable for test-only code)
- Type safety on tool name (existing defensive pattern is adequate)

**Reverted:** 0

**Overall:** simplify: applied 2 fixes

**Quality Checks:** 31/31 tests passing
**Handoff:** To Obi-Wan (Reviewer) for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 1 trivial

- **Pricing model label** (Ambiguous spec — Cosmetic, Trivial)
  - Spec: "using OpenAI pricing model"
  - Code: Uses Claude Opus pricing ($15/$75 per 1M input/output tokens)
  - Recommendation: A — Update spec. This is a Claude dashboard; Opus pricing is correct. The spec text was imprecise.

**Decision:** Proceed to verify phase. Implementation is clean, minimal, and fully aligned with all 7 ACs. Reuses the existing flame chart pattern from tab 0. No new abstractions introduced. No architectural concerns.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `scripts/playtest_dashboard.py` — Added Claude tab (tab 7) with tool timeline, token breakdown, cost accumulator, event routing, and state management

**Tests:** 31/31 passing (GREEN)
**Branch:** feat/21-3-dashboard-claude-tab (pushed)

**Implementation details:**
- Tab bar entry with badge (`switchTab(7)`, `tab7-badge`)
- Tab content div (`tc7`) with tool timeline, token breakdown, and cost cards
- State: `claudeEvents[]` for tool/span events, `claudeTokens{}` for token totals
- `dispatch()` routes `source === 'claude_otel'` events by type (tool_result, span, token_usage)
- `renderClaudeTimeline()` — flame chart bars with duration, error highlighting (red + ✗)
- `renderClaudeTokens()` — table with input/output/cache_read/cache_creation + per-type cost
- `updateClaudeCost()` — running cost using Opus pricing rates
- Turn correlation via `timestamp_ns`/`start_ns` proximity to game turn timestamps
- `switchTab(7)` and `updateAll()` both call Claude renders

**Handoff:** To verify phase (TEA)

## TEA Assessment

**Tests Required:** Yes
**Reason:** Full feature story — new dashboard tab with 7 ACs

**Test Files:**
- `scripts/tests/test_claude_tab.py` — 31 tests across 13 test classes

**Tests Written:** 31 tests covering 7 ACs + 3 rule enforcement checks
**Status:** RED (all 31 failing — ready for Dev)

### AC Coverage

| AC | Tests | Description |
|----|-------|-------------|
| AC-1 | 4 | Tab bar entry, label, content div, badge element |
| AC-2 | 4 | Timeline container, render function, tool name, duration |
| AC-3 | 3 | Token breakdown container, types tracked, render function |
| AC-4 | 3 | Cost container, calculation logic, input/output pricing |
| AC-5 | 2 | Error detection, visual indicator |
| AC-6 | 2 | Timestamp usage, turn correlation logic |
| AC-7 | 2 | Badge update, count display |

### Wiring & Integration Tests

| Area | Tests | Description |
|------|-------|-------------|
| Event routing | 4 | dispatch() routes claude_otel source, tool_result, token_usage, span |
| State mgmt | 2 | Claude events array, token totals in state |
| switchTab | 1 | Tab index 7 handled |
| updateAll | 1 | Claude rendering included |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| JS #1 silent errors | `test_no_empty_catch_in_claude_handlers` | failing |
| JS #4 strict equality | `test_claude_otel_check_uses_strict_equality` | failing |
| JS #5 DOM security | `test_tool_names_escaped_in_timeline` | failing |

**Rules checked:** 3 of 5 applicable JS/Python lang-review rules have test coverage
**Self-check:** 0 vacuous tests — all 31 have meaningful assertions, fixed 5 initially vacuously-passing tests

**Handoff:** To Yoda (Dev) for implementation

## Sm Assessment

Story 21-3 is well-scoped. Upstream 21-1 and 21-2 are complete — the OTLP receiver is already broadcasting `claude_otel` events over WebSocket. This story is pure frontend dashboard work: consume existing data, render new tab.

**Repos:** Orchestrator (playtest dashboard HTML/JS). API repo not needed this story.
**Risk:** Low. Data flow is established; this is visualization.
**Routing:** TEA (Han Solo) for RED phase — write failing tests for the Claude tab rendering, token breakdown, and cost accumulator.