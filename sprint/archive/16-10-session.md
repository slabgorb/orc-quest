---
story_id: "16-10"
jira_key: "none"
epic: "16"
workflow: "tdd"
---
# Story 16-10: ResourcePool struct + YAML schema — generic named resource with thresholds

## Story Details
- **ID:** 16-10
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Epic:** 16 — Genre Mechanics Engine — Confrontations & Resource Pools
- **Repository:** sidequest-api (Rust backend)
- **Branch:** feat/16-10-resourcepool-struct-yaml-schema
- **Points:** 5
- **Priority:** p1
- **Status:** in-progress

## Context

Epic 16 builds two missing generic subsystems: Confrontation (universal structured encounter engine) and ResourcePool (persistent named resources). Story 16-10 is the foundational piece of the ResourcePool pillar — defining the data structure, YAML schema, and validation pipeline.

**Dependency chain:**
- 16-1 (Narrator resource injection) — COMPLETE
- 16-2 (Confrontation trait + ConfrontationState) — COMPLETE
- 16-3 (Confrontation YAML schema) — COMPLETE
- 16-4 (Migrate combat as confrontation) — COMPLETE
- 16-5 (Migrate chase as confrontation) — COMPLETE
- 16-6 (Standoff confrontation type) — COMPLETE
- 16-7 (Social confrontation types) — COMPLETE
- 16-10 (ResourcePool struct + YAML schema) ← current
- 16-11 (Resource threshold → KnownFact pipeline) — depends on this
- 16-12 (Wire genre resources) — depends on this

## What This Story Does

**ResourcePool struct + YAML schema** introduces a generic, named resource system that genres declare in YAML and the engine loads, validates, and manages. Each pool tracks current value, bounds, spend/gain/decay behavior, and thresholds that trigger narrator events.

### Acceptance Criteria

1. **ResourcePool struct** in `game_state.rs`:
   - Fields: `name`, `current`, `min`, `max`, `voluntary` (bool — player-spendable), `decay_per_turn`, `thresholds` (Vec of threshold objects)
   - Each threshold: `at` (value), `event_id` (string), `narrator_hint` (string for LLM context)
   - Part of `GameSnapshot`: `resources: HashMap<String, ResourcePool>`
   - Implements `Clone, Debug, Serialize, Deserialize`

2. **YAML schema** in `genre_loader.rs`:
   - Genre packs declare resources in `rules.yaml` under `resources:` key
   - Example:
     ```yaml
     resources:
       Luck:
         current: 3
         min: 0
         max: 6
         voluntary: true
         decay_per_turn: 0.0
         thresholds:
           - at: 1
             event_id: luck_critical
             narrator_hint: "The character's luck is nearly exhausted. Desperate times ahead."
           - at: 0
             event_id: luck_depleted
             narrator_hint: "Out of luck. Everything now depends on skill and nerve."
     ```
   - Genre loader parses into ResourcePool structs at pack init
   - Validation: ensures `min <= current <= max`, `decay_per_turn >= 0`, thresholds in order

3. **ResourcePatch for LLM-driven changes**:
   - Add `ResourcePatch` type to patch system (alongside `InventoryPatch`, `LocationPatch`, etc.)
   - Format: `resource_name: operation (add/set/subtract)` and `value`
   - Engine validates: rejects spends that would violate bounds (e.g., spend 5 Luck when current is 3 and voluntary is false)
   - Applies valid patches, updates state, triggers threshold checks

4. **Bounds validation & rejection**:
   - When a ResourcePatch attempts to change a resource:
     - If voluntary=true and spend exceeds current, reject (error response to narration pipeline)
     - If value would fall below min or exceed max, clamp or reject per validation mode
     - Log rejection with reason for debugging
   - Impossible spends don't modify state

5. **Integration with existing systems**:
   - Resources serialize/deserialize with save/load
   - Narrator context injection (from 16-1) references ResourcePool state
   - Threshold events feed into KnownFact pipeline (16-11)

### Key References
- `game_state.rs` — GameSnapshot home
- `genre_loader.rs` — Pack initialization
- `patch.rs` — Patch system (reference InventoryPatch pattern)
- Existing threshold/event infrastructure from narrative systems
- YAML schema examples from confrontation declarations (16-3)

### Non-Goals
- Threshold → KnownFact auto-trigger (that's 16-11)
- UI display (that's 16-13)
- Wiring genre-specific resources (that's 16-12)
- Decay mechanics (can stub as `decay_per_turn` field without turn-tick wiring)

## Implementation Strategy

**Phase 1 (RED):** Write acceptance tests for ResourcePool behavior:
- Create ResourcePool with bounds, current, thresholds
- Serialize/deserialize ResourcePool
- Parse genre YAML with resource declarations
- Apply ResourcePatches (add, subtract, set)
- Validate bounds and reject invalid patches
- Verify threshold detection

**Phase 2 (GREEN):** Implement ResourcePool struct and YAML schema:
- Define ResourcePool in game_state.rs
- Implement Serialize/Deserialize
- Add resources field to GameSnapshot
- Parse resources in genre_loader
- Implement ResourcePatch type and validation
- Wire into patch application pipeline

**Phase 3 (VERIFY):** Integration tests:
- Full playthrough load genre pack with resources
- Apply patches through narration pipeline
- Verify state changes in GameSnapshot
- Test save/load with resources present

## Workflow Phases

| Phase | Owner | Status |
|-------|-------|--------|
| setup | sm | in-progress |
| red | tea | pending |
| green | dev | pending |
| spec-check | architect | pending |
| verify | tea | pending |
| review | reviewer | pending |
| spec-reconcile | architect | pending |
| finish | sm | pending |

## Workflow Tracking

**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-04-05T07:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T07:20Z | — | — |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings yet.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations yet.
