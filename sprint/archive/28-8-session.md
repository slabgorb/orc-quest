---
story_id: "28-8"
epic: "28"
workflow: "tdd"
branch: "feat/28-8-npc-turns-beat-system"
---
# Story 28-8: NPC turns through beat system — NPCs mechanically act every round

## Story Details
- **ID:** 28-8
- **Epic:** 28 — Unified Encounter Engine
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Stack Parent:** 28-7 (StructuredEncounter promotion complete)

## Objective

In the unified encounter engine, NPCs must act mechanically every round. Currently, the narrator says "the goblin attacks" but `resolve_attack()` is never called for the NPC. This story wires NPC beat selection and mechanical resolution into the dispatch loop.

## Acceptance Criteria

1. Each NPC actor in an encounter gets a beat selection per round
2. For combat encounters, NPC beats default to "attack" targeting a player
3. For other encounters, creature_smith selects NPC beats based on disposition and role
4. Dispatch loops through all actors, calls `apply_beat()` for each, resolves the stat_check
5. Every NPC action produces OTEL events
6. GM panel shows exactly what each NPC did mechanically

## Workflow Tracking
**Workflow:** tdd
**Phase:** verify
**Phase Started:** 2026-04-08T09:23:56Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-08T17:30Z | 2026-04-08T07:08:18Z | -37302s |
| red | 2026-04-08T07:08:18Z | 2026-04-08T07:19:41Z | 11m 23s |
| green | 2026-04-08T07:19:41Z | 2026-04-08T09:15:17Z | 1h 55m |
| spec-check | 2026-04-08T09:15:17Z | 2026-04-08T09:23:56Z | 8m 39s |
| verify | 2026-04-08T09:23:56Z | - | - |

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

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

ACs 1, 4, 5, 6 are directly implemented in the dispatch loop. ACs 2, 3 describe narrator/creature_smith beat selection behavior (what populates `beat_selections`), not dispatch wiring — correctly out of scope for this story's code change. The dispatch loop processes whatever `beat_selections` contains; the upstream agents populate it.

Implementation reuses `dispatch_beat_selection()` without modification — clean reuse of existing infrastructure. OTEL event includes all required fields (npc_name, beat_id, target, stat_check). Player filtering via case-insensitive string match is adequate.

**Decision:** Proceed to review

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/mod.rs` — Added NPC beat dispatch loop after player beat dispatch. Iterates `result.beat_selections` for non-player actors, calls `dispatch_beat_selection()` per NPC, emits `encounter.npc_beat` OTEL events.

**Tests:** 11/11 passing (GREEN)
**Branch:** feat/28-8-npc-turns-beat-system (pushed)

**Handoff:** To verify phase (TEA simplify + quality-pass)

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-point TDD story wiring NPC mechanical actions into encounter dispatch

**Test Files:**
- `crates/sidequest-server/tests/npc_turns_beat_system_story_28_8_tests.rs` — 11 tests covering 6 ACs

**Tests Written:** 11 tests covering 6 ACs
**Status:** RED (4 failing, 7 passing — ready for Dev)

### Failing Tests (what Dev must fix)
1. `dispatch_consumes_beat_selections_from_action_result` — beat_selections not read in dispatch
2. `dispatch_handles_multiple_beats_per_turn` — no iteration over multiple beats
3. `npc_beat_dispatch_function_exists` — no NPC beat dispatch code path
4. `otel_npc_beat_event_emitted` — no encounter.npc_beat OTEL event

### Passing Tests (infrastructure ready)
7 tests confirm BeatSelection struct, EncounterActor type, NPC identification, and combat/non-combat beat selection are all wired and available.

### Rule Coverage
No lang-review rules file found for Rust in this project. Tests enforce story ACs and OTEL observability principle.

**Self-check:** 0 vacuous tests found. All tests have meaningful assertions checking source patterns or struct behavior.

**Handoff:** To Dev for implementation (GREEN phase)

## Sm Assessment

Story 28-8 is ready for TDD red phase. Session file created, branch `feat/28-8-npc-turns-beat-system` exists in the API repo. No Jira (personal project). Stack parent 28-7 is complete. Scope is clear: wire NPC beat selection and mechanical resolution into the encounter dispatch loop, with OTEL instrumentation. 5-point TDD story, API-only. Handing off to TEA for failing tests.