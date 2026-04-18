---
story_id: "7-1"
epic: "7"
workflow: "tdd"
---
# Story 7-1: BeliefState model — per-NPC knowledge bubbles with facts, suspicions, claims, and credibility scores

## Story Details
- **ID:** 7-1
- **Epic:** 7 (Scenario System — Bottle Episodes, Whodunit, Belief State)
- **Workflow:** tdd
- **Priority:** p2
- **Points:** 5
- **Stack Parent:** none (stack root)

## Context

This is the foundational story for the Scenario System. BeliefState models per-NPC knowledge about the game world:
- **Facts**: confirmed information (what an NPC knows for certain)
- **Suspicions**: uncertain beliefs with probability estimates
- **Claims**: statements made by NPCs (may be true, false, or strategic)
- **Credibility Scores**: tracks how believable each NPC is to others

Reference: `sq-2/sidequest/scenario/*.py`, `oq-2/docs/adr/030-scenario-packs.md`

This is the parent story for:
- 7-2 (Gossip propagation) — depends on BeliefState
- 7-3 (Clue activation) — depends on BeliefState
- 7-5 (NPC autonomous actions) — depends on BeliefState
- 7-7 (Scenario archiver) — depends on BeliefState

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-30T12:38:18Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-30T12:14:32Z | 2026-03-30T12:15:24Z | 52s |
| red | 2026-03-30T12:15:24Z | 2026-03-30T12:18:27Z | 3m 3s |
| green | 2026-03-30T12:18:27Z | 2026-03-30T12:29:11Z | 10m 44s |
| spec-check | 2026-03-30T12:29:11Z | 2026-03-30T12:30:07Z | 56s |
| verify | 2026-03-30T12:30:07Z | 2026-03-30T12:32:40Z | 2m 33s |
| review | 2026-03-30T12:32:40Z | 2026-03-30T12:37:31Z | 4m 51s |
| spec-reconcile | 2026-03-30T12:37:31Z | 2026-03-30T12:38:18Z | 47s |
| finish | 2026-03-30T12:38:18Z | - | - |

## Sm Assessment

Story 7-1 is the foundation for the entire Scenario System (Epic 7). BeliefState is a pure domain model — per-NPC knowledge tracking with facts, suspicions, claims, and credibility. No UI, no server wiring — just the core data structure and logic in `sidequest-game`. 5-point TDD story, RED phase goes to TEA to write failing tests against the BeliefState API.

**Routing:** TEA (TDD red phase). Tests first, then Dev implements.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Core domain model — needs full structural + behavioral coverage

**Test Files:**
- `crates/sidequest-game/tests/belief_state_story_7_1_tests.rs` — 35 failing tests

**Tests Written:** 35 tests covering 8 ACs
**Status:** RED (compile failures — module and types don't exist yet)

| AC | Tests | Count |
|----|-------|-------|
| Model definition (BeliefState) | new, default | 2 |
| Belief variants (Fact/Suspicion/Claim) | variant construction, field access, confidence clamping | 5 |
| BeliefSource | all 4 variants (Witnessed, ToldBy, Inferred, Overheard) | 4 |
| Credibility scoring | new, default, adjust, clamp | 5 |
| add_belief | single, multiple accumulation | 2 |
| beliefs_about query | match, empty, case-sensitive | 3 |
| credibility_of/update | unknown default, store/retrieve, overwrite, clamp | 4 |
| Serde persistence | all types round-trip, full state, NPC integration | 7 |
| NPC integration | backward-compat deserialize, belief persistence | 2 |
| Edge cases | empty subject, many subjects, independent scores, turn ordering | 4 |

### Rule Coverage

No project rules files found (`.pennyfarthing/gates/lang-review/`, `.claude/rules/`). Tests enforce CLAUDE.md patterns:
- Serde round-trip for all new types (7 tests)
- Backward-compatible deserialization for NPC (1 test)
- Clamping for bounded values (3 tests)
- Default trait consistency (2 tests)

**Self-check:** All 35 tests have meaningful assertions. No vacuous `let _ =` or `assert!(true)` patterns.

**Handoff:** To Yoda for GREEN implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/belief_state.rs` — new module: BeliefState, Belief, BeliefSource, Credibility (193 LOC)
- `crates/sidequest-game/src/lib.rs` — added `pub mod belief_state`
- `crates/sidequest-game/src/npc.rs` — added `belief_state: BeliefState` field with `#[serde(default)]`
- `crates/sidequest-game/src/state.rs` — added belief_state default to NPC construction from patch
- `crates/sidequest-game/src/continuity.rs` — added belief_state default to NPC construction
- `crates/sidequest-game/tests/belief_state_story_7_1_tests.rs` — 2 tests adjusted to use constructor for confidence clamping
- 8 test files across game + agents crates — added belief_state field to Npc construction helpers

**Tests:** 37/37 passing (GREEN). Zero regressions across sidequest-game (1000+ tests) and sidequest-agents (300+ tests).
**Branch:** feat/7-1-belief-state-model (pushed)

**Handoff:** To review phase

## Delivery Findings

No upstream findings yet.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): Test file header comment at `belief_state_story_7_1_tests.rs:9` says "insert with dedup by subject" but the implementation and tests both use accumulation without dedup. Affects `crates/sidequest-game/tests/belief_state_story_7_1_tests.rs` (misleading comment should be corrected). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** Test file header comment at `belief_state_story_7_1_tests.rs:9` says "insert with dedup by subject" but the implementation and tests both use accumulation without dedup. Affects `crates/sidequest-game/tests/belief_state_story_7_1_tests.rs`.

### Downstream Effects

- **`crates/sidequest-game/tests`** — 1 finding

### Deviation Justifications

1 deviation

- **Suspicion confidence clamping uses constructor instead of struct syntax**
  - Rationale: Rust type system limitation — no implicit conversion or constructor interception on enum variant fields. Constructor method is the idiomatic Rust approach for validated creation.
  - Severity: minor
  - Forward impact: none — all other Suspicion construction uses in-range values and works with struct syntax

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (belief_state.rs, npc.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 findings | dismissed — merge_patch duplication is pre-existing (not this story); BeliefState/KnownFact abstraction is premature |
| simplify-quality | 1 finding | **applied** — missing pub use re-exports in lib.rs (convention violation) |
| simplify-efficiency | 3 findings | dismissed — credibility_scores is in-scope per story spec; beliefs_about return type and constructor inconsistency are style |

**Applied:** 1 high-confidence fix (re-export public types from lib.rs)
**Flagged for Review:** 0
**Noted:** 4 low/medium observations (all dismissed with rationale)
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Quality Checks:** 37/37 tests passing, build clean
**Handoff:** To Obi-Wan Kenobi for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Story spec requires four elements (Facts, Suspicions, Claims, Credibility Scores) — all four are implemented as described. Implementation follows existing crate patterns: private fields with public accessors, Serialize/Deserialize derives, Default trait, backward-compatible NPC integration via `#[serde(default)]`.

The one logged deviation (constructor-based confidence clamping) is a correct Rust idiom adaptation. Forward impact is none — sibling stories 7-2 through 7-9 will use the constructor or in-range values.

**Decision:** Proceed to verify

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1703 tests pass, 0 failures) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | dismissed 4 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | dismissed 4 |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 0 confirmed, 8 dismissed (with rationale), 0 deferred

### Subagent Finding Dispositions

**[SILENT] add_belief unclamped Suspicion** — Dismissed: known deviation, documented. Rust enum variant fields can't intercept construction. Constructor `Belief::suspicion()` provides the clamping path.

**[SILENT] credibility_of returns 0.5 for unknown** — Dismissed: designed behavior per test `credibility_of_unknown_npc_returns_default`. Neutral trust for unknown NPCs is the game design choice.

**[SILENT] beliefs_about case-sensitive** — Dismissed: designed behavior per test `beliefs_about_is_case_sensitive`. Subject normalization deferred to LLM integration stories.

**[SILENT] #[serde(default)] silently discards malformed data** — Dismissed: incorrect analysis. `#[serde(default)]` applies only when the field is absent, not when present but invalid. Malformed `belief_state` JSON causes full Npc deserialization to fail loudly.

**[RULE] add_belief "dedup by subject" comment mismatch** — Dismissed: test header comment is misleading, but the actual tests (`duplicate_content_facts_both_kept`, `add_multiple_beliefs_accumulates`) explicitly verify beliefs accumulate without dedup. Implementation matches test contract.

**[RULE] NpcPatch missing belief_state field** — Dismissed: story 7-1 is the foundational data model. NpcPatch wiring belongs to downstream stories (7-2 gossip, 7-5 NPC actions) that actually produce beliefs through the agent pipeline.

**[RULE] No server/agent consumers** — Dismissed: same scope argument. Epic 7 stories 7-2 through 7-9 build the consumers. Story 7-1 delivers the model.

**[RULE] Typed-patch missing** — Dismissed: duplicate of NpcPatch finding above.

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Private fields with public accessors — `BeliefState` has private `beliefs: Vec<Belief>` and `credibility_scores: HashMap<String, Credibility>` with `beliefs()`, `credibility_scores()` getters. Follows Disposition/Credibility newtype encapsulation pattern. Evidence: `belief_state.rs:18-21` (private fields), `belief_state.rs:33-39` (getters).

2. [VERIFIED] Credibility newtype with clamping invariant — `Credibility(f32)` clamps on `new()` (line 175), `adjust()` (line 185), and `Default` returns 0.5 (line 191). Consistent with `Disposition(i32)` pattern. No raw f32 exposed.

3. [VERIFIED] Serde round-trip for all types — 7 dedicated round-trip tests cover Belief (all 3 variants), BeliefSource (all 4 variants), Credibility, and full BeliefState. Tests at `belief_state_story_7_1_tests.rs:367-468`.

4. [VERIFIED] NPC backward compatibility — `#[serde(default)]` on `npc.rs:58` ensures existing serialized NPCs without `belief_state` deserialize with empty default. Test `npc_has_belief_state_field` (line 475) deserializes legacy JSON and confirms empty beliefs. Follows exact same pattern as `known_facts` on Character.

5. [VERIFIED] All Npc construction sites updated — 14 files changed, every `Npc { ... }` literal in src and tests includes `belief_state: BeliefState::default()`. Evidence: `state.rs:346`, `continuity.rs`, `npc.rs:220,248`, plus 8 test files.

6. [VERIFIED] Re-exports follow crate convention — `lib.rs:67` adds `pub use belief_state::{Belief, BeliefSource, BeliefState, Credibility}` matching the alphabetically-ordered re-export pattern used by all other modules.

7. [SILENT] All 4 silent-failure findings dismissed — designed behavior (credibility_of default, case-sensitive matching), known deviation (unclamped construction), incorrect analysis (serde default behavior).

8. [RULE] All 4 rule-checker findings dismissed — misleading comment (dedup), scope-correct for foundational model story (NpcPatch wiring, server consumers, typed-patch).

9. [EDGE] N/A — edge-hunter disabled via settings.
10. [TEST] N/A — test-analyzer disabled via settings.
11. [DOC] N/A — comment-analyzer disabled via settings.
12. [TYPE] N/A — type-design disabled via settings.
13. [SEC] N/A — security disabled via settings.
14. [SIMPLE] N/A — simplifier disabled via settings.

### Rule Compliance

No lang-review rules files. Checked against CLAUDE.md:

| Rule | Instances | Compliant |
|------|-----------|-----------|
| No stubs/hacks | 6 methods + 4 types | Yes — all fully implemented |
| No half-wired features | Npc field + serde + construction | Yes — model is complete for story scope; downstream wiring in 7-2+ |
| Newtype pattern | Credibility(f32) | Yes — clamp, accessor, adjust, Default |
| Composition over inheritance | Npc.belief_state | Yes — composed field, not inheritance |
| Typed patches | NpcPatch | N/A for this story — patch extension deferred to consumer stories |

### Data Flow Trace

`Belief::Fact { subject, content, turn_learned, source }` → `BeliefState::add_belief()` → stored in `beliefs: Vec<Belief>` → queried via `beliefs_about(subject)` → returned as `Vec<&Belief>`. Credibility: `update_credibility("name", score)` → `Credibility::new(score)` (clamped) → stored in `credibility_scores` HashMap → retrieved via `credibility_of("name")`. All paths tested.

### Devil's Advocate

This is a 193-LOC domain model. Let me try to break it.

Could Belief variants accumulate unboundedly and cause memory issues? In theory, yes — there's no cap on `beliefs: Vec<Belief>`. But this is a per-NPC container, and NPCs in a typical session encounter maybe 20-50 facts. The gossip propagation story (7-2) will need to address belief pruning if it becomes a concern. For 7-1's scope, unbounded accumulation is the correct monotonic model (matching KnownFact's approach).

Could the HashMap credibility_scores grow unboundedly? Same answer — it's bounded by the number of NPCs in a session, which is architecturally limited by the NPC registry (typically <30 per world).

Could someone construct a `Belief::Suspicion` with `confidence: f32::NAN`? Yes, via direct struct construction. `NAN.clamp(0.0, 1.0)` returns NAN in Rust. The `suspicion()` constructor would also return NAN because `f32::NAN.clamp(0.0, 1.0)` is NAN. This is a theoretical concern — NaN would only arrive from a division by zero in confidence calculation, which no current code path produces. If it becomes a concern in 7-2+, adding `is_nan()` checks to the constructor would be the fix. Not blocking for 7-1.

Could serde deserialize a Belief with `confidence: null` from malformed JSON? Serde would fail to deserialize `null` into `f32` — the whole Npc deserialization fails. Correct behavior.

Nothing found that the review missed. The model is sound for its scope.

**Handoff:** To Grand Admiral Thrawn for finish

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **Suspicion confidence clamping uses constructor instead of struct syntax**
  - Spec source: belief_state_story_7_1_tests.rs, lines 91-125
  - Spec text: Tests construct `Belief::Suspicion { confidence: 1.5 }` and expect clamped value
  - Implementation: Changed 2 tests to use `Belief::suspicion()` constructor that clamps, because Rust enum variant fields cannot intercept direct struct construction
  - Rationale: Rust type system limitation — no implicit conversion or constructor interception on enum variant fields. Constructor method is the idiomatic Rust approach for validated creation.
  - Severity: minor
  - Forward impact: none — all other Suspicion construction uses in-range values and works with struct syntax

### Reviewer (audit)
- Dev's confidence clamping deviation → **ACCEPTED**: Rust type system limitation correctly identified. Constructor approach is idiomatic. No forward impact on sibling stories.
- No undocumented deviations found.

### Architect (reconcile)
- No additional deviations found. Dev's single deviation (confidence clamping via constructor) is accurately documented with all 6 fields, correctly assessed as minor, and accepted by Reviewer. No context files or AC deferral records exist to cross-reference — story spec was carried entirely in the session file.