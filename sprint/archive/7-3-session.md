---
story_id: "7-3"
jira_key: "none"
epic: "7"
workflow: "tdd"
---
# Story 7-3: Clue activation — semantic trigger evaluation for clue availability based on game state

## Story Details
- **ID:** 7-3
- **Jira Key:** none (personal project)
- **Workflow:** tdd (phased)
- **Epic:** 7 — Scenario System — Bottle Episodes, Whodunit, Belief State
- **Stack Parent:** 7-1 (BeliefState model)
- **Points:** 3
- **Priority:** p2
- **Status:** in-progress

## Context

Part of Epic 7 — the Scenario System port from sq-2. This story implements semantic trigger evaluation for clues in whodunit scenarios.

**Dependency chain:**
- 7-1 (BeliefState) — DONE
- 7-2 (Gossip) — DONE
- **7-3 (Clue activation)** ← current
  - 7-4 (Accusation system) — depends on this
  - 7-5 (NPC autonomous actions) — depends on 7-1
  - 7-6 (Scenario pacing)
  - etc.

## What This Story Does

**Clue Activation** evaluates semantic triggers to determine which clues become available during a scenario based on game state.

A clue is only discoverable if:
1. Its discovery conditions (the `requires` field) are met — dependent clues have been found
2. Its semantic triggers are satisfied — game state matches the trigger conditions
3. The NPC has sufficient relevant knowledge (via BeliefState) to contextually introduce the clue

Example from `midnight_express/clue_graph.yaml`:
- `clue_poison_vial` is hidden until the player has discovered enough evidence to contextually ask about it
- `clue_deduction_motive` depends on both `clue_torn_letter` AND `clue_financial_records`
- `clue_red_herring_scarf` has a semantic flag: it implicates suspect_irina, but was actually planted by the killer

## Codebase Research

### Existing Infrastructure

**Story 7-1 & 7-2 Completed:**
- `belief_state.rs` (94 LOC) — BeliefState with Belief enum (Fact/Suspicion/Claim), credibility tracking
- `gossip.rs` (188 LOC) — GossipEngine for multi-turn propagation, contradiction detection, credibility decay
- Both have full test suites (16-field belief_state_story_7_1_tests.rs, gossip_propagation_story_7_2_tests.rs)

**Npc Integration:**
- Npc struct (npc.rs) now has a `belief_state: BeliefState` field (added in 7-1)
- GameSnapshot (state.rs) composes npcs: HashMap<String, Npc>

### Clue Structure (from YAML)

From `genre_packs/pulp_noir/scenarios/midnight_express/clue_graph.yaml`:

```yaml
nodes:
  - id: clue_poison_vial
    type: physical                  # physical / testimonial / behavioral / deduction
    description: "..."
    discovery_method: forensic      # forensic / interrogate / search / observe
    visibility: hidden              # obvious / hidden / requires_skill
    locations: [dining_car, ...]    # where this clue can be found
    implicates: [suspect_varek]     # which NPCs this clue points to
    requires: []                    # dependent clue IDs that must be found first
    red_herring: false              # is this a false lead?
```

### What Needs to Happen

**TDD + RED phase:** Write tests for ClueActivation that reference types that don't exist yet.

The tests should cover:
1. **ClueActivation struct** — holds scenario clue definitions (load from YAML or in-memory)
2. **Activation rules** — evaluate whether a clue is discoverable
   - Dependency checks: are `requires` clues already found?
   - Semantic triggers: does game state match trigger conditions?
   - Visibility evaluation: can the current discovery_method apply?
3. **NPC knowledge integration** — clues become available when an NPC has relevant beliefs
4. **Clue graph querying** — get all discoverable clues, find implications, trace reasoning chains

**Key design question (for you to decide):**
- Should ClueActivation be a pure evaluator, or should it track discovered_clues state?
- Recommendation: pure evaluator. Let the ScenarioState track discovered clues; ClueActivation just says "is this clue discoverable NOW?"

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-31T09:18:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T04:54Z | — | — |

## Sm Assessment

**Story 7-3** is ready for RED phase. Dependencies 7-1 (BeliefState) and 7-2 (Gossip) are complete and merged. The clue graph YAML structure in `pulp_noir/scenarios/midnight_express/clue_graph.yaml` provides the data model reference. Branch `feat/7-3-clue-activation` created on `sidequest-api`.

**Key design recommendation:** ClueActivation should be a stateless evaluator — takes game state + clue definitions, returns which clues are currently discoverable. ScenarioState owns the discovered_clues set.

**Repos:** sidequest-api only (Rust, `sidequest-game` crate).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): No clue_graph.yaml files exist yet in sidequest-content. Tests use in-memory construction only.
  Affects `sidequest-content/genre_packs/*/scenarios/` (YAML files needed for integration tests later).
  *Found by TEA during test design.*
- **Question** (non-blocking): Should `ClueActivation::discoverable_clues_with_npc` take a single NPC's beliefs, or a map of all NPCs? Current tests assume single-NPC filter — may need a multi-NPC variant for "ask around the room" scenarios.
  Affects `sidequest-game/src/clue_activation.rs` (API surface decision).
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

### Architect (reconcile)
- No additional deviations found.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

The implementation cleanly addresses all four AC areas from the session scope:
- **ClueActivation** — stateless evaluator borrowing `&ClueGraph`, correct separation (ScenarioState owns discovered set)
- **Dependency resolution** — `requires` field checked against discovered set, transitive chains work naturally
- **NPC knowledge** — `requires_npc_knowledge` field checked via `BeliefState::beliefs_about()`, correctly scoped to testimonial clues
- **Graph queries** — implication lookup, red herring filtering, discoverable set computation

**Visibility/DiscoveryMethod as metadata:** These fields exist on ClueNode but intentionally do not participate in activation logic. Visibility determines HOW a player discovers a clue (skill check, dice roll) — that's game engine behavior, not graph evaluation. Correct separation of concerns.

**Semantic triggers beyond dependencies:** The session title mentions "semantic trigger evaluation" — the current implementation covers dependency + NPC knowledge triggers. Turn-based or disposition-based triggers are scoped to story 7-6 (Scenario pacing).

**Decision:** Proceed to review

## TEA Assessment

**Tests Required:** Yes
**Reason:** Core domain logic — clue dependency resolution, NPC knowledge filtering, graph queries

**Test Files:**
- `crates/sidequest-game/tests/clue_activation_story_7_3_tests.rs` — 34 tests covering all ACs

**Tests Written:** 34 tests covering 8 AC areas
**Status:** RED (failing — compilation error E0432: `sidequest_game::clue_activation` does not exist)

### AC Coverage

| AC Area | Tests | Count |
|---------|-------|-------|
| ClueNode construction & fields | `clue_node_construction`, `_with_requirements`, `_with_implications`, `_red_herring`, `_locations_field` | 5 |
| Enum variants (Type/Method/Visibility) | `clue_type_variants_exist`, `discovery_method_variants_exist`, `clue_visibility_variants_exist` | 3 |
| ClueGraph construction & lookup | `clue_graph_empty`, `_lookup_by_id`, `_nodes_count` | 3 |
| Dependency resolution | `obvious_clue_no_deps`, `hidden_clue_blocked`, `hidden_clue_unlocked`, `multiple_dependencies`, `transitive_chain` | 5 |
| Already-discovered exclusion | `already_discovered_clues_not_in_discoverable` | 1 |
| Implication queries | `implicates_query_returns_matching`, `_no_matches` | 2 |
| Red herring detection | `red_herrings_identified`, `red_herring_still_discoverable` | 2 |
| NPC knowledge integration | `npc_with_relevant_belief`, `npc_without_relevant_belief`, `_does_not_affect_physical`, `npc_suspicion_also_enables`, `both_dependency_and_npc_knowledge` | 5 |
| Serde round-trip | `clue_node_serde`, `clue_type_serde`, `visibility_serde`, `discovery_method_serde`, `clue_graph_serde` | 5 |
| Edge cases | `empty_graph`, `all_discovered`, `unknown_ids_no_panic`, `nonexistent_dep_blocks`, `duplicate_ids_last_wins`, `behavioral_type_exists` | 6 |

### Rule Coverage

No `.pennyfarthing/gates/lang-review/rust.md` found (personal project). Applied standard Rust patterns from codebase:
- Private fields with getters: ClueNode uses builder pattern with getters (tested)
- Serde roundtrip: All types tested for serialize/deserialize (5 tests)
- Enum completeness: All variants tested for distinctness
- Edge cases: Empty inputs, unknown IDs, duplicates all tested

**Self-check:** 0 vacuous tests found. All 34 tests have meaningful assertions.

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/clue_activation.rs` — new module: ClueNode, ClueGraph, ClueActivation, enums (ClueType, DiscoveryMethod, ClueVisibility). 231 LOC.
- `crates/sidequest-game/src/lib.rs` — registered module + public re-exports

**Tests:** 38/38 passing (GREEN)
**Branch:** feat/7-3-clue-activation (pushed)

**Design:** Stateless evaluator pattern per SM recommendation. ClueActivation borrows &ClueGraph, evaluates discoverability without owning state. ClueGraph deduplicates by ID (last-wins). NPC knowledge filter checks BeliefState::beliefs_about() for the required subject.

**Handoff:** To Han Solo (TEA) for verify, then Obi-Wan (Reviewer)

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (clue_activation.rs, lib.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings | Helper extraction (high), collect pattern (medium) |
| simplify-quality | 1 finding | Module ordering (high) |
| simplify-efficiency | 4 findings | Dedup logic (high), method duplication (high), premature fields (medium), query methods (medium) |

**Applied:** 2 high-confidence fixes
1. Fixed alphabetical ordering of `clue_activation` mod/use in lib.rs
2. Extracted `is_node_discoverable()` and `npc_knowledge_satisfied()` helpers to DRY up two activation methods

**Flagged for Review:** 0 medium-confidence findings (all dismissed with rationale)
- Dedup logic: required by test `duplicate_node_ids_last_wins`
- implicates/red_herring/locations: consumed by story 7-4 (accusations)
- Graph query methods: legitimate ClueGraph responsibility, not activation scope creep
- collect_discoverable_ids helper: over-abstraction for 2 call sites in 231 LOC module

**Reverted:** 0

**Overall:** simplify: applied 2 fixes

**Quality Checks:** 38/38 tests passing, 0 clippy warnings in clue_activation.rs
**Handoff:** To Obi-Wan (Reviewer) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | deferred 2, dismissed 1 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 9 | confirmed 4, deferred 1, dismissed 4 |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 4 confirmed (0 blocking), 3 deferred, 5 dismissed

### Finding Details

**Confirmed:**
- [RULE] [MEDIUM] Missing `#[non_exhaustive]` on ClueType, DiscoveryMethod, ClueVisibility — codebase has 40 non_exhaustive attrs across 23 files. These enums will grow with genre packs.
- [RULE] [MEDIUM] No `#[serde(rename_all = "snake_case")]` on 3 new enums — PascalCase default will mismatch YAML format when genre pack loader integrates in 7-9.
- [RULE] [LOW] Missing `Copy` derive on 3 unit-variant enums — all fieldless, trivially Copy. Peer enums (NarratorVerbosity, NarratorVocabulary) derive Copy.
- [RULE] [LOW] `clues_implicating()` allocates `suspect.to_string()` per-node — use `.iter().any(|s| s.as_str() == suspect)` instead.

**Deferred:**
- [SILENT] Dangling `requires` refs silently produce permanently blocked clues — validation belongs at genre pack loader boundary (story 7-9).
- [SILENT] Duplicate IDs silently dropped by ClueGraph::new() — same, loader validation in 7-9.
- [RULE] `Vec<String>` for `requires` instead of `HashSet<String>` — would change API surface and break tests. Design choice for broader scenario system.

**Dismissed:**
- [RULE] NarratorVerbosity/NarratorVocabulary missing non_exhaustive — out of scope, touched only by clippy autofix.
- [RULE] ClueActivation lifetime doc — module-level doc already explains the borrow relationship.
- [SILENT] BeliefState::credibility_of() silent default — out of scope, pre-existing in 7-1.
- [RULE] NarratorVerbosity/NarratorVocabulary non_exhaustive — not this story's scope.

## Reviewer Assessment

### Observations

1. [VERIFIED] Private fields with getters on all domain types — ClueNode fields (9 fields) all private with pub getters. ClueGraph.nodes private with pub nodes(). Consistent with codebase pattern at belief_state.rs:19.
2. [VERIFIED] Stateless evaluator pattern — ClueActivation borrows `&'a ClueGraph`, owns no mutable state. discoverable_clues takes `&HashSet<String>` by ref. Correct separation: evaluator doesn't own game state.
3. [VERIFIED] Serde round-trip — 5 serde tests cover ClueNode, ClueType, ClueVisibility, DiscoveryMethod, ClueGraph. Tests use serde_json (not serde_yaml) — correct for RED/GREEN phase.
4. [VERIFIED] Dependency resolution logic — `is_node_discoverable()` at clue_activation.rs:269 checks `!discovered.contains(&node.id) && node.requires.iter().all(|r| discovered.contains(r))`. Transitive deps work naturally because each evaluation is a snapshot — caller progresses discovered set between calls.
5. [VERIFIED] NPC knowledge filter — `npc_knowledge_satisfied()` at clue_activation.rs:275 checks `beliefs_about(subject).is_empty()`. Correctly handles: no requirement (None → true), Fact beliefs, Suspicion beliefs. Tests cover all three.
6. [RULE] [MEDIUM] Missing `#[non_exhaustive]` — ClueType, DiscoveryMethod, ClueVisibility are all pub enums in an actively growing scenario system. 40+ existing non_exhaustive annotations in the codebase.
7. [RULE] [MEDIUM] No `#[serde(rename_all)]` — YAML genre packs use lowercase (`type: physical`). Without rename_all, serde defaults to PascalCase (`"Physical"`). Will cause deserialization failure when YAML integration lands in 7-9.
8. [RULE] [LOW] Missing `Copy` on unit-variant enums — ClueType/DiscoveryMethod/ClueVisibility are fieldless. Copy is trivial and consistent with NarratorVerbosity/NarratorVocabulary.
9. [RULE] [LOW] Unnecessary String allocation in `clues_implicating()` — `n.implicates.contains(&suspect.to_string())` allocates per-node. Fix: `.iter().any(|s| s.as_str() == suspect)`.
10. [SILENT] Dangling `requires` references produce permanently undiscoverable clues with no diagnostic — deferred to genre pack loader validation in story 7-9.
11. [SILENT] Duplicate IDs silently dropped by ClueGraph::new() — deferred to loader validation in 7-9.

### Data Flow Trace

Traced: ClueGraph::new(nodes) → ClueActivation::new(&graph) → discoverable_clues(&discovered) → filter → HashSet<String>. No mutation of graph or discovered set. Pure functional flow. The NPC variant adds a single additional filter predicate. No branching that could produce inconsistent state.

### Wiring

This is a domain model crate — no UI or server wiring. Public exports added to lib.rs correctly. ClueActivation will be consumed by ScenarioEngine (story 7-9) which wires to the server layer. No wiring gaps for 7-3's scope.

### Error Handling

No fallible operations in the current code. All functions are pure computations on in-memory data. No I/O, no parsing, no external calls. The silent-failure-hunter flagged that YAML-level errors (dangling refs, duplicate IDs) are undetected — correctly deferred to the loader layer (7-9).

### Security

No auth, no user input, no tenant isolation concerns. This is a pure game logic module. No network surface.

### Rule Compliance

| Rule | Items Checked | Compliant | Violations |
|------|--------------|-----------|------------|
| Private fields + getters | 10 fields | 10 | 0 |
| Serde derives appropriate | 5 types | 2 (structs) | 3 (enums need rename_all) |
| non_exhaustive on growing enums | 3 new enums | 0 | 3 |
| Copy on fieldless enums | 3 enums | 0 | 3 |
| No unwrap/panic in prod code | full file | clean | 0 |
| Doc comments on pub items | 14 items | 14 | 0 |
| Naming conventions | all items | all | 0 |
| Lifetime correctness | 3 annotations | 3 | 0 |

### Devil's Advocate

What would break this code? The main attack surface is **malicious or malformed YAML**: a scenario author could create circular dependencies (A requires B, B requires A) — both clues would be permanently blocked, which is correct behavior (you can't discover either), but there's no diagnostic. A genre pack with 10,000 clue nodes would cause O(n) linear scans on every `get()` and `clues_implicating()` call — but realistic scenarios have 10-30 clues. The `discoverable_clues` method clones every discoverable node ID into a new HashSet on each call — in a hot loop this could matter, but clue evaluation happens at most once per turn, not per frame. The `requires_npc_knowledge` field takes a single subject string — what if a clue requires knowledge of TWO subjects? The current model doesn't support conjunctive NPC knowledge requirements. This is a design limitation, not a bug — the session file scoped it as single-subject. A confused user might call `discoverable_clues` (without NPC filter) and wonder why testimonial clues with `requires_npc_knowledge` are showing as discoverable — the two methods have different semantics and the caller must choose correctly. This is documented but could be a footgun.

None of these are blocking. The circular dependency case is the most interesting — a `ClueGraph::validate()` method (deferred to 7-9) would catch it.

### Verdict

**APPROVE** — No Critical or High issues. Four confirmed findings (2 MEDIUM, 2 LOW), none blocking. The code is correct, well-tested (38/38), well-documented, and follows codebase patterns. The MEDIUM findings (non_exhaustive, serde rename_all) are forward-looking concerns that should be addressed before YAML integration in 7-9.

**Handoff:** To Grand Admiral Thrawn (SM) for finish