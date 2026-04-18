---
story_id: "35-3"
jira_key: "MSSCI-16932-35-3"
epic: "MSSCI-16932"
workflow: "tdd"
---
# Story 35-3: Wire scenario_scoring into /accuse handler with questioned_npcs tracking

## Story Details
- **ID:** 35-3
- **Jira Key:** MSSCI-16932 (Epic)
- **Workflow:** tdd
- **Type:** chore
- **Points:** 5
- **Priority:** p1
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-04-09T00:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-09T00:00:00Z | - | - |

## Context & Acceptance Criteria

### Why This Story
`score_scenario()` in `sidequest-game/src/scenario_scoring.rs` is fully implemented and tested (story 7-8) but has **zero production consumers**. The narrator currently just invents a verdict instead of computing the actual mystery endgame grade based on evidence coverage, interrogation breadth, and deduction quality.

### Acceptance Criteria
1. `questioned_npcs: HashSet<String>` added to `ScenarioState` with `#[serde(default)]` for backwards compat
2. `questioned_npcs` populated when dialogue occurs with scenario NPCs during dispatch
3. After `handle_accusation()` in `/accuse handler`, build `ScenarioScoreInput` from scenario_state, accusation result, turn count, questioned NPCs
4. Call `score_scenario()` and emit `WatcherEventBuilder("scenario", StateTransition)` with grade, evidence_coverage, deduction_quality
5. Append score summary to narration response text
6. Integration test: mock accusation resolution, assert valid grade and OTEL event

### Key Files
- `sidequest-api/crates/sidequest-server/src/dispatch/slash.rs` — /accuse handler, insertion point ~line 147
- `sidequest-api/crates/sidequest-game/src/scenario_scoring.rs` — read-only, fully implemented
- `sidequest-api/crates/sidequest-game/src/scenario_state.rs` — add questioned_npcs field
- Plan: `/Users/keithavery/.claude/plans/async-bubbling-hedgehog.md`

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
