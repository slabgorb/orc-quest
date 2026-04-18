---
story_id: "7-2"
epic: "7"
workflow: "tdd"
---
# Story 7-2: Gossip propagation — NPCs spread claims between turns, contradictions decay credibility

## Story Details
- **ID:** 7-2
- **Epic:** 7 (Scenario System — Bottle Episodes, Whodunit, Belief State)
- **Points:** 5
- **Priority:** p2
- **Workflow:** tdd
- **Stack Parent:** 7-1 (BeliefState model) — completed and merged to develop

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-30T13:28:07Z 15:30:00

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-30 15:30:00 | 2026-03-30T13:14:23Z | -8137s |
| red | 2026-03-30T13:14:23Z | 2026-03-30T13:16:39Z | 2m 16s |
| green | 2026-03-30T13:16:39Z | 2026-03-30T13:21:04Z | 4m 25s |
| spec-check | 2026-03-30T13:21:04Z | 2026-03-30T13:21:49Z | 45s |
| verify | 2026-03-30T13:21:49Z | 2026-03-30T13:24:20Z | 2m 31s |
| review | 2026-03-30T13:24:20Z | 2026-03-30T13:27:29Z | 3m 9s |
| spec-reconcile | 2026-03-30T13:27:29Z | 2026-03-30T13:28:07Z | 38s |
| finish | 2026-03-30T13:28:07Z | - | - |

## Acceptance Criteria
- [x] NPCs share new claims they've learned with neighbors during turns
- [x] Claims propagate between NPC belief states (gossip spread)
- [x] Contradictory claims are identified and credibility decays on both sides
- [x] Propagation respects NPC relationships (not everyone gossips with everyone)
- [x] Test coverage for multi-hop gossip propagation (NPC A → B → C)
- [x] Test coverage for contradiction detection and credibility decay
- [x] Integration with existing BeliefState model from 7-1

## Story Context

**Depends on:** Story 7-1 (BeliefState model) — which adds per-NPC knowledge bubbles tracking facts, suspicions, claims, and credibility scores.

**Implementation notes:**
- Gossip propagation is a core mechanic for Scenario System, enabling NPCs to spread misinformation and develop conflicting beliefs
- Contradictions between beliefs (claim X vs. claim Y) create investigative puzzle depth
- Credibility decay simulates how false information loses traction over time
- Foundation for Scenario System (whodunit, rat-hunt, accusation mechanics)

**Key references:**
- sq-2/sidequest/scenario/belief.py — gossip mechanics in Python version
- oq-2/docs/adr/030-scenario-packs.md — scenario architecture

## Sm Assessment

Story 7-2 builds directly on the BeliefState model from 7-1 (just merged). Gossip propagation is the first consumer of BeliefState — NPCs spread claims between turns, contradictions decay credibility. Pure domain logic in `sidequest-game`, no UI or server wiring. The gossip engine will be a new module or extension of `belief_state.rs`.

**Routing:** TEA (TDD red phase). Tests first for gossip mechanics, then Dev implements.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Core scenario mechanic — gossip propagation with contradiction detection

**Test Files:**
- `crates/sidequest-game/tests/gossip_propagation_story_7_2_tests.rs` — 24 failing tests

**Tests Written:** 24 tests covering 7 ACs
**Status:** RED (compile failure — `gossip` module doesn't exist yet)

| AC | Tests | Count |
|----|-------|-------|
| GossipEngine construction | new with adjacency, neighbors query | 2 |
| Claim sharing to neighbors | share to neighbor, block non-neighbor, source attribution, turn number | 4 |
| Duplicate suppression | don't re-share known beliefs | 1 |
| Multi-hop propagation | A→B→C across turns, chain attribution | 2 |
| Contradiction detection | conflicting claims, consistent beliefs, different subjects, carries both beliefs | 4 |
| Credibility decay | reduce trust, floor at 0.0 | 2 |
| PropagationResult | claims_spread count, contradictions_found count | 2 |
| Serde persistence | Contradiction round-trip | 1 |
| Edge cases | empty NPCs, isolated NPC, empty beliefs, bidirectional gossip | 4 |
| Integration with BeliefState | all tests use BeliefState API from 7-1 | 24 |

### Rule Coverage

No project rules files found. Tests enforce CLAUDE.md patterns:
- Serde round-trip for new types (1 test)
- Edge case coverage for empty/boundary inputs (4 tests)
- Integration with existing BeliefState API (all tests)

**Self-check:** All 24 tests have meaningful assertions. No vacuous patterns.

**Handoff:** To Yoda for GREEN implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/gossip.rs` — new module: GossipEngine, Contradiction, PropagationResult (190 LOC)
- `crates/sidequest-game/src/lib.rs` — added `pub mod gossip` + re-exports (GossipEngine, PropagationResult; Contradiction not re-exported due to name collision with continuity::Contradiction)

**Tests:** 22/22 passing (GREEN). Zero regressions across sidequest-game.
**Branch:** feat/7-2-gossip-propagation (pushed)

**Handoff:** To review phase

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Reviewer (code review)
- **Improvement** (non-blocking): Contradiction re-detection across turns causes cumulative credibility decay for stale pairs. Affects `crates/sidequest-game/src/gossip.rs:96` (consider tracking processed contradictions if count inflation becomes a problem in 7-9). *Found by Reviewer during code review.*

### Dev (implementation)
- **Improvement** (non-blocking): `gossip::Contradiction` cannot be re-exported from lib.rs because `continuity::Contradiction` already occupies the name. Tests import via `sidequest_game::gossip::Contradiction` which works, but if both types need to be used together in server code, one will need a type alias. Affects `crates/sidequest-game/src/lib.rs` (consider renaming one type). *Found by Dev during implementation.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- TEA and Dev both report no deviations — confirmed accurate. The implementation directly matches the test contract. No undocumented deviations found.

### Architect (reconcile)
- No additional deviations found. TEA and Dev both report clean alignment, confirmed by Reviewer. No context files or AC deferral records exist to cross-reference. The gossip engine implementation matches the test contract and all 7 ACs without deviation.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | deferred 1 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | dismissed 4 |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 0 confirmed, 4 dismissed, 1 deferred

### Subagent Finding Dispositions

**[SILENT] Contradiction re-detection across turns** — Deferred: valid observation that same contradiction pairs are re-detected each turn, causing cumulative credibility decay. This is reasonable game behavior (unresolved contradictions erode trust). The 0.0 floor prevents runaway. If `contradictions_found` count inflation becomes a problem during scenario integration (7-9), add a processed-contradiction tracker.

**[RULE] Contradiction re-export** — Dismissed: known naming collision documented as delivery finding by Dev. Accessible via module path.

**[RULE] No pipeline wiring** — Dismissed: correct scope for foundational model. Story 7-9 (ScenarioEngine integration) wires it into the game loop.

**[RULE] Bare String for NPC names** — Dismissed: the entire NPC system uses String for names (NonBlankString for display, String for keys). NpcName newtype would be a cross-cutting refactor beyond this story.

**[RULE] Direct mutation vs typed patch** — Dismissed: typed patches are for agent→state pipeline. Internal gossip decay is domain logic analogous to Credibility::adjust().

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Snapshot-then-mutate for bidirectional gossip — Phase 1 collects all beliefs into `pending` vec before Phase 2 mutates. Evidence: `gossip.rs:43-71` (snapshot), `gossip.rs:73-92` (mutate). Tests `bidirectional_gossip_both_npcs_share` confirms both directions work.

2. [VERIFIED] Source attribution preserves gossip chain — Propagated beliefs become `Claim { source: ToldBy(gossiper) }`, attributing to the immediate gossiper not the original source. Evidence: `gossip.rs:61-67`. Tests: `propagate_turn_marks_source_as_told_by`, `multi_hop_preserves_chain_attribution`.

3. [VERIFIED] Duplicate suppression by subject+content — `beliefs_about(subject).any(b.content() == content)` prevents re-sharing known information. Evidence: `gossip.rs:80-83`. Test: `propagate_does_not_duplicate_existing_belief`.

4. [VERIFIED] Contradiction detection — O(n^2) pair comparison with same-subject different-content rule. Appropriate for per-NPC belief counts (<50). Evidence: `gossip.rs:117-140`. Tests: 4 contradiction tests covering positive, negative, cross-subject, and field verification.

5. [VERIFIED] Credibility decay with floor — Uses `CREDIBILITY_DECAY` constant (0.1), reads via `credibility_of()`, writes via `update_credibility()` which clamps at 0.0. Evidence: `gossip.rs:143-154`. Test: `decay_credibility_does_not_go_below_zero`.

6. [VERIFIED] Belief::source() accessor added in verify — Parallels existing subject/content/turn_learned pattern. Evidence: `belief_state.rs:137-143`. Simplifies `extract_source_name` from 7-line match to 4-line match.

7. [SILENT] Re-detection deferred — valid observation, reasonable game behavior, floor prevents runaway. Tracked for 7-9.
8. [RULE] All 4 rule-checker findings dismissed — naming collision known, pipeline wiring deferred to 7-9, String keys match codebase, direct mutation is domain-internal.
9. [EDGE] N/A — disabled. 10. [TEST] N/A — disabled. 11. [DOC] N/A — disabled.
12. [TYPE] N/A — disabled. 13. [SEC] N/A — disabled. 14. [SIMPLE] N/A — disabled.

### Rule Compliance

| Rule | Instances | Compliant |
|------|-----------|-----------|
| No stubs/hacks | 7 methods | Yes — all fully implemented |
| No half-wired | Module export + re-export | Yes for story scope; server wiring in 7-9 |
| Composition | GossipEngine operates on &mut HashMap | Yes — engine doesn't own state |
| Newtype | Credibility used, String for NPC names | Matches existing codebase pattern |

### Data Flow Trace

NPC beliefs → `propagate_turn(npcs, turn)` → Phase 1: snapshot beliefs per gossiper → Phase 2: add Claims to neighbors (dedup by subject+content) → Phase 3: `detect_contradictions` per NPC → `decay_credibility` for each source → returns `PropagationResult { claims_spread, contradictions_found }`. All typed, all tested.

### Devil's Advocate

Could the snapshot phase create an explosion of pending beliefs? Each gossiper shares all their beliefs with all neighbors. If NPC A has 10 beliefs and 5 neighbors, that's 50 pending items. With 30 NPCs averaging 10 beliefs each and 5 neighbors, that's 1500 pending items per turn — still trivial for Vec allocation. But note: gossip is recursive — each turn adds more beliefs, which get shared next turn. Without belief pruning, this grows. The duplicate suppression gates this: once Bob knows about "weapon:Dagger", he won't get it again. So growth is bounded by unique subject+content pairs × NPC count. Manageable for scenario scale.

Could contradiction detection produce O(n^2) contradictions? If an NPC has 10 beliefs about the same subject with different content, that's C(10,2) = 45 contradictions, each decaying two sources. With 0.1 decay per contradiction, a source named in 45 contradictions loses 4.5 credibility in one turn (clamped to 0.0). This is extreme but the scenario would need to be pathological. Normal play produces 2-3 beliefs per subject at most.

Could the HashMap iteration order cause non-deterministic gossip? Yes — `npcs.keys()` on HashMap has arbitrary order. In Phase 1, the order gossipers are processed affects which pending items are generated first. But since Phase 2 processes all pending items and dedup is content-based, the final state is order-independent. The `claims_spread` count is deterministic. Correct.

**Handoff:** To Grand Admiral Thrawn for finish

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (gossip.rs, lib.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | **applied 1** (Belief::source() accessor); dismissed 2 (decay helper premature, Contradiction naming known) |
| simplify-quality | 2 findings | dismissed — re-export asymmetry already documented; module docstring is style |
| simplify-efficiency | 4 findings | **applied 1** (remove unnecessary rebind); dismissed 3 (borrow checker constraints, defensive coding, scope creep) |

**Applied:** 2 high-confidence fixes (Belief::source() accessor + remove unnecessary rebind)
**Flagged for Review:** 0
**Noted:** 7 observations dismissed with rationale
**Reverted:** 0

**Overall:** simplify: applied 2 fixes

**Quality Checks:** 22/22 gossip tests + 37/37 belief_state tests passing
**Handoff:** To Obi-Wan Kenobi for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 7 ACs map directly to the implementation: adjacency-based propagation (AC 1,2,4), contradiction detection with credibility decay (AC 3), multi-hop test coverage (AC 5), contradiction/credibility test coverage (AC 6), and full BeliefState integration (AC 7). The snapshot-then-mutate pattern for bidirectional gossip is architecturally sound. Dev's delivery finding about `Contradiction` name collision is noted — minor naming issue, not a spec deviation.

**Decision:** Proceed to verify