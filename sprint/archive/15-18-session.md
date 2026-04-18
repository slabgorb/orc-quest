---
story_id: "15-18"
jira_key: ""
epic: "15"
workflow: "tdd"
---
# Story 15-18: Wire materialize_world — world builder ignores progressive materialization

## Story Details
- **ID:** 15-18
- **Epic:** 15 (Playtest Debt Cleanup — Stubs, Dead Code, Disabled Features)
- **Jira Key:** none
- **Workflow:** tdd
- **Priority:** p2
- **Points:** 2
- **Stack Parent:** none

## Problem Statement

`materialize_world()` in `world_materialization.rs` takes `CampaignMaturity` and `HistoryChapters` and produces a narrative world description that expands as the campaign ages. The `WorldBuilderAgent` in `sidequest-agents` uses `CampaignMaturity` to build prompts but never calls `materialize_world()`.

**Root cause:** The world materialization function is fully implemented but has zero non-test callers. The agent builds its narrator prompt with maturity-aware context but skips calling the function that computes the narrative expansion.

**Impact:** World descriptions don't progressively expand as gameplay unfolds. The agent improvises world detail independent of campaign age, missing the designed progression mechanic.

## Solution

Call `materialize_world(maturity, &history_chapters)` in the `WorldBuilderAgent` and inject the materialized description into its prompt context.

### Key Changes

1. **Locate WorldBuilderAgent in sidequest-agents** — find where prompts are assembled
2. **Call materialize_world()** with the current CampaignMaturity and HistoryChapters
3. **Inject the result** into the agent's narrator prompt context
4. **Add OTEL event** `world.materialized (maturity_level, chapter_count, description_tokens)` to emit span at materialization time
5. **Add test** to verify the agent calls materialize_world() and injects result into prompt

### Backwards Compatibility

- `materialize_world()` is a pure function — no side effects
- Injection into narrator prompt is non-breaking (adds context, doesn't change existing fields)
- No schema or protocol changes required

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-05T14:12:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T15:00:00Z | 2026-04-05T13:49:00Z | -4260s |
| red | 2026-04-05T13:49:00Z | 2026-04-05T13:54:25Z | 5m 25s |
| green | 2026-04-05T13:54:25Z | 2026-04-05T14:00:30Z | 6m 5s |
| spec-check | 2026-04-05T14:00:30Z | 2026-04-05T14:02:08Z | 1m 38s |
| verify | 2026-04-05T14:02:08Z | 2026-04-05T14:09:01Z | 6m 53s |
| review | 2026-04-05T14:09:01Z | 2026-04-05T14:11:35Z | 2m 34s |
| spec-reconcile | 2026-04-05T14:11:35Z | 2026-04-05T14:12:26Z | 51s |
| finish | 2026-04-05T14:12:26Z | - | - |

## Sm Assessment

Story 15-18 is a 2-point wiring fix in the API repo. `materialize_world()` exists and is tested but has no production callers. The WorldBuilderAgent needs to call it and inject the result into its prompt context, plus emit an OTEL span. Straightforward TDD — TEA writes failing tests for the wiring gap, Dev connects it.

**Routing:** TEA (Han Solo) for red phase — write failing tests that prove the wiring gap exists.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wiring gap — WorldBuilderAgent exists but orchestrator never uses it

**Test Files:**
- `crates/sidequest-agents/tests/world_builder_materialize_story_15_18_tests.rs`

**Tests Written:** 6 tests covering 4 ACs + 1 wiring test
**Status:** RED (compile errors — TurnContext missing fields)

### Wiring Gap Analysis

The WorldBuilderAgent has `materialized_world_context()` with OTEL spans and chapter filtering fully implemented. But:
1. `TurnContext` has no `history_chapters` or `campaign_maturity` field
2. `build_narrator_prompt_tiered()` never instantiates or calls WorldBuilderAgent
3. The server calls `materialize_world()` directly in connect.rs for session creation, but that's snapshot mutation — not prompt injection

### What Dev Needs To Do

1. Add `history_chapters: Vec<HistoryChapter>` and `campaign_maturity: CampaignMaturity` to `TurnContext`
2. In `build_narrator_prompt_tiered()`, create a `WorldBuilderAgent` with the context's chapters/maturity and call its `build_context()` to inject the materialized world section
3. In the server dispatch, populate `TurnContext.history_chapters` and `TurnContext.campaign_maturity` from the session's genre pack data
4. Fix `Orchestrator::new()` — tests need a way to construct without a real mpsc channel (or provide a test helper)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Wiring verification | `orchestrator_uses_world_builder_agent_for_materialization` | failing |
| No dead code | All 6 tests prove WorldBuilderAgent should have non-test consumers | failing |
| OTEL observability | `narrator_prompt_includes_materialized_world_when_chapters_present` (exercises code path with OTEL span) | failing |

**Self-check:** 0 vacuous tests — all have meaningful assertions on prompt_text content

**Handoff:** To Yoda for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/orchestrator.rs` — Added `history_chapters` + `campaign_maturity` to TurnContext, imported WorldBuilderAgent, injected materialized world context in build_narrator_prompt_tiered(), added new_for_test() helper
- `crates/sidequest-server/src/dispatch/mod.rs` — Populated new TurnContext fields from snapshot in both dispatch sites (normal + aside)
- `crates/sidequest-agents/tests/world_builder_materialize_story_15_18_tests.rs` — Updated to use new_for_test()

**Tests:** 6/6 passing (GREEN)
**Branch:** feat/15-18-wire-materialize-world (pushed)

**Handoff:** To next phase (verify or review)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

The story spec called for: (1) adding history_chapters/campaign_maturity to TurnContext, (2) wiring WorldBuilderAgent into build_narrator_prompt_tiered(), (3) populating from server dispatch, (4) OTEL span world.materialized. All four are present in the diff. Implementation is minimal — 29 lines of production code across 2 files. The WorldBuilderAgent is reused as-is, not reimplemented.

**Decision:** Proceed to review

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Files Analyzed:** 2 (orchestrator.rs, dispatch/mod.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | skipped | 29-line change, no duplication opportunity |
| simplify-quality | clean | No naming, dead code, or readability issues |
| simplify-efficiency | clean | No over-engineering — minimal wiring code |

**Applied:** 0 fixes
**Flagged for Review:** 0
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** clippy clean (no new warnings), 6/6 tests passing
**Handoff:** To Obi-Wan Kenobi for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 29-line diff, 2 production files, 1 test file | N/A |
| 2 | reviewer-type-design | Yes | clean | No new types — reuses existing WorldBuilderAgent, CampaignMaturity, HistoryChapter | N/A |
| 3 | reviewer-edge-hunter | Yes | clean | Empty chapters guard present, aside handler defaults correctly | N/A |
| 4 | reviewer-rule-checker | Yes | clean | No rule violations — fields documented, types reused from existing crates | N/A |
| 5 | reviewer-silent-failure-hunter | Yes | clean | No swallowed errors — empty chapters guard is explicit, not silent | N/A |

All received: Yes

## Reviewer Assessment

**Verdict:** Approved and merged
**PR:** slabgorb/sidequest-api#309 (squash-merged to develop)
**Findings:** None — clean 29-line wiring change, reuses existing WorldBuilderAgent
- [PREFLIGHT] Clean: 2 production files, 1 test file, 29 lines added
- [TYPE] Clean: No new types introduced — reuses WorldBuilderAgent, CampaignMaturity, HistoryChapter
- [EDGE] Clean: Empty chapters guard present, aside handler uses correct defaults
- [RULE] Clean: No rule violations — doc comments on new fields, types from existing crates
- [SILENT] Clean: No swallowed errors — empty chapters guard is explicit skip, not silent fallback

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found.

## Delivery Findings

- **Gap** (non-blocking): `Orchestrator::new()` requires an mpsc channel, making test construction awkward. A `test_new()` or `Default` impl would improve testability. Affects `crates/sidequest-agents/src/orchestrator.rs` (add test helper constructor). *Found by TEA during test design.*
- **Improvement** (non-blocking): `new_for_test()` added to Orchestrator resolves the TEA finding above. *Found by Dev during implementation.*

## Design Deviations

None at this time.

## Implementation Notes

### Files to Modify

- **sidequest-agents/src/world_builder_agent.rs** (or equivalent location in agents)
  - Locate prompt assembly code
  - Call `materialize_world(maturity, &history_chapters)`
  - Inject materialized description into prompt context
  - Add OTEL event emission

- **sidequest-game/src/world_materialization.rs** (possible updates)
  - Export function visibility check
  - Verify function signature matches expected call site

### Testing Strategy

1. **Unit test** — verify WorldBuilderAgent calls materialize_world()
2. **Unit test** — verify materialized description is injected into prompt
3. **Integration test** — verify OTEL event fires with correct parameters
4. **Wiring test** — grep for non-test callers of materialize_world() to confirm production usage

### Wiring Verification

- **Function location:** Find materialize_world() definition in world_materialization.rs
- **Agent location:** Find WorldBuilderAgent in sidequest-agents
- **Injection point:** Identify where agent prompts are built
- **OTEL event:** Verify world.materialized span fires during agent execution