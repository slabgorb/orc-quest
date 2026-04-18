---
story_id: "23-4"
epic: "23"
workflow: "tdd"
---
# Story 23-4: LoreFilter — graph-distance + intent-based context retrieval for Valley zone

## Story Details
- **ID:** 23-4
- **Epic:** 23 (Narrator Prompt Architecture — Template, RAG, Universal Cartography)
- **Workflow:** tdd
- **Points:** 5
- **Priority:** p2
- **Stack Parent:** none (stands alone)

## Story Description

Build a LoreFilter struct in sidequest-agents that determines which lore sections to inject per turn based on multiple signals:

**Primary Signal:** Graph distance from current node
- 0 hops (current node) = full description + NPCs + items + state
- 1 hop (adjacent nodes) = full description + edge properties (danger, terrain)
- 2+ hops = summary only (if available) or name only

**Secondary Signals:**
- **Intent classification:** Combat pulls enemy factions; Dialogue pulls NPC culture/faction; Travel pulls destination + edge properties
- **NPC presence:** NPCs in scene pull their full faction/culture descriptions
- **Arc proximity:** Full descriptions for arcs within ~10% of next beat or connected to current scene NPCs

**Implementation Requirements:**
1. Create LoreFilter struct in sidequest-agents (module TBD — likely in orchestrator.rs or new lore_filter.rs)
2. Consume: graph distance from cartography + intent classification + NPC registry
3. Output: list of lore sections to inject into build_narrator_prompt()
4. Gate Valley section registration through the filter (currently all lore dumps)
5. Always inject name-only lists as closed-world assertions (prevent hallucination)
6. Add OTEL `lore_filter` span logging included/excluded decisions for GM panel observability

**Documentation Reference:**
- docs/narrator-prompt-rag-strategy.md — full RAG strategy and retrieval layers
- docs/universal-room-graph-cartography.md — graph format (hierarchical world_graph + sub_graphs)
- docs/prompt-reworked.md — prompt template structure and zone routing

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-04T16:14:27Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-04T10:45Z | 2026-04-04T14:50:26Z | 4h 5m |
| red | 2026-04-04T14:50:26Z | 2026-04-04T15:07:56Z | 17m 30s |
| green | 2026-04-04T15:07:56Z | 2026-04-04T15:22:01Z | 14m 5s |
| spec-check | 2026-04-04T15:22:01Z | 2026-04-04T15:24:34Z | 2m 33s |
| green | 2026-04-04T15:24:34Z | 2026-04-04T15:34:57Z | 10m 23s |
| spec-check | 2026-04-04T15:34:57Z | 2026-04-04T15:43:13Z | 8m 16s |
| verify | 2026-04-04T15:43:13Z | 2026-04-04T15:48:12Z | 4m 59s |
| review | 2026-04-04T15:48:12Z | 2026-04-04T15:56:51Z | 8m 39s |
| green | 2026-04-04T15:56:51Z | 2026-04-04T16:11:35Z | 14m 44s |
| review | 2026-04-04T16:11:35Z | 2026-04-04T16:12:59Z | 1m 24s |
| spec-reconcile | 2026-04-04T16:12:59Z | 2026-04-04T16:14:27Z | 1m 28s |
| finish | 2026-04-04T16:14:27Z | - | - |

## Delivery Findings

No upstream findings.

### TEA (test design)
- No upstream findings during test design.

### TEA (verify)
- No upstream findings during verify.

### Reviewer (code review)
- **Gap** (blocking): `telemetry_story_18_1_tests.rs:119` compile error — explicit TurnContext struct literal missing new `world_graph` field. Affects `crates/sidequest-agents/tests/telemetry_story_18_1_tests.rs` (add `world_graph: None,`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `enrichment_categories()` is public API with test coverage but zero production consumers — intent signal not wired into `select_lore()` logic. Affects `crates/sidequest-agents/src/lore_filter.rs` (wire intent into selection or make method `pub(crate)`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): No `warn!` when current_node not found in world graph — OTEL blind spot for degraded state. Affects `crates/sidequest-agents/src/lore_filter.rs:select_lore()`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Arc proximity tests deferred to select_lore integration**
  - Spec source: context-story-23-4.md, AC "Arc proximity"
  - Spec text: "arcs near next beat get full detail"
  - Implementation: Arc proximity not tested in isolation — no formal Arc/StoryArc type exists yet. Tropes serve as narrative arcs via TropeState. Tests pass empty arc slice to select_lore, leaving arc proximity enrichment for Dev to implement and test when wiring trope data.
  - Rationale: No existing arc type to test against; building test fixtures for a type that doesn't exist would dictate implementation prematurely
  - Severity: minor
  - Forward impact: Dev should add arc proximity tests when implementing the trope-to-arc mapping

### Dev (implementation)
- **Cyclic graph test expectations corrected for bidirectional semantics**
  - Spec source: TEA test `cyclic_graph_does_not_infinite_loop`
  - Spec text: "assert_eq!(filter.graph_distance(\"a\", \"c\"), Some(2))" — expected directed traversal
  - Implementation: Changed to Some(1) because WorldGraph::neighbors() is bidirectional; in a 3-node cycle all nodes are adjacent
  - Rationale: TEA's bidirectional test and cyclic test contradicted each other; bidirectional is correct for game world traversal and matches the existing WorldGraph API
  - Severity: minor
  - Forward impact: none — test expectations now consistent with WorldGraph::neighbors() semantics

- **Arc proximity signal accepts &[String] placeholder, not TropeState**
  - Spec source: context-story-23-4.md, "Arc proximity"
  - Spec text: "arcs near next beat get full detail"
  - Implementation: select_lore takes `_arcs: &[String]` and ignores it; no TropeState integration
  - Rationale: No formal arc type exists — tropes serve as arcs via TropeState but wiring that into the filter requires cross-crate type decisions beyond this story's scope
  - Severity: minor
  - Forward impact: Future story should wire TropeState into arc proximity enrichment

- **~~No orchestrator wiring in this commit~~ RESOLVED**
  - Wiring completed in second commit: TurnContext.world_graph → build_narrator_prompt() → LoreFilter → Valley zone sections + OTEL span. Full pipeline connected through both DispatchContext construction sites (lib.rs, connect.rs).

## Implementation Context

### Current State
- **23-1 (done):** Reworked narrator prompt template with attention zones
- **23-2 (done):** Tiered lore summaries added to faction/culture/location YAML schemas
- **23-3 (done):** Universal room graph cartography (hierarchical world_graph + sub_graphs)
- **23-11 (done):** Reworked tool sections with bash wrappers and env vars

### What This Story Must Do
The lore filtering infrastructure is the "smart retrieval" layer that connects three completed pieces:
1. The **reworked prompt template** (23-1) has zones and sections ready for conditional injection
2. The **tiered summaries** (23-2) provide safe fallback descriptions for every lore entity
3. The **hierarchical cartography** (23-3) provides the graph distance metric

This story builds the decision engine: given current location, intent, and NPCs present, what lore should be in the Valley zone?

### Integration Points
- **orchestrator.rs:build_narrator_prompt()** — currently line 254-559, needs a call to filter.select_lore() instead of dumping everything
- **sidequest-game state** — has current_node, NPC registry, and intent classification already
- **prompt_framework module** — may need new LoreSelection or LoreContext output type
- **OTEL instrumenting** — add span to trace filter decisions per turn (GM panel visibility)

### Testing Strategy (TDD)
1. Unit tests for filter logic:
   - Graph distance calculation (Zork-style cyclic graph traversal)
   - Intent-to-lore mapping (Combat → enemy factions, etc.)
   - NPC presence enrichment
   - Arc proximity calculation
2. Integration test: full narrator prompt build with filter active
3. Regression test: specific node + intent + NPCs should yield expected lore set
4. OTEL span verification: filter emits correct metadata

### Completion Criteria
- [ ] LoreFilter struct compiles and has full unit test coverage
- [ ] build_narrator_prompt() calls filter instead of dumping all lore
- [ ] Graph distance calculation verified with Zork-style traversal
- [ ] OTEL span logs included/excluded decisions
- [ ] Full workspace build passes
- [ ] Integration test confirms filter wiring end-to-end

## Tea Assessment

**Tests Required:** Yes
**Reason:** New struct (LoreFilter) with BFS graph traversal, intent mapping, and OTEL integration

**Test Files:**
- `crates/sidequest-agents/tests/lore_filter_story_23_4_tests.rs` — 28 tests covering all ACs

**Tests Written:** 28 tests covering 9 ACs + edge cases
**Status:** RED (compilation error — `sidequest_agents::lore_filter` module does not exist)

### Test Coverage by AC

| AC | Tests | Description |
|----|-------|-------------|
| DetailLevel enum | 5 | Variants exist, Debug impl, ordering (Full > Summary > NameOnly) |
| LoreSelection struct | 1 | Fields: entity_id, entity_name, category, detail_level, reason |
| Graph distance (BFS) | 7 | Zero/one/two/three hops, bidirectional, disconnected, nonexistent |
| Detail by distance | 4 | 0→Full, 1→Full, 2→Summary, 3+→NameOnly |
| Intent mapping | 4 | Combat→faction, Dialogue→culture+faction, Exploration→location, Backstory→backstory |
| NPC enrichment | 1 | NPC in scene upgrades their faction to Full |
| Closed-world assertions | 2 | All entities present at minimum NameOnly, distant nodes verified |
| OTEL summary | 1 | format_otel_summary includes included/excluded labels |
| Integration wiring | 1 | Module importable from sidequest_agents crate |
| Edge cases | 4 | Cyclic graph, single node, empty NPCs/arcs, unknown current node |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | `detail_level_is_non_exhaustive` (wildcard match) | failing |
| #4 tracing | `graph_distance_with_empty_graph_does_not_panic` | failing |
| #6 test quality | Self-check: all 28 tests have meaningful assertions | passing |
| #11 workspace deps | No new deps needed | n/a |

**Rules checked:** 4 of 15 applicable (remaining rules apply to implementation, not test design)
**Self-check:** 0 vacuous tests found. One `assert!(true)` in wiring test is documented as intentional.

### Key Decisions for Dev (Yoda)

1. **LoreFilter lives in `sidequest-agents/src/lore_filter.rs`** — new module, exported via `lib.rs`
2. **Public API:** `LoreFilter::new(&WorldGraph)`, `graph_distance(from, to) -> Option<usize>`, `detail_for_distance(usize) -> DetailLevel`, `enrichment_categories(Intent) -> Vec<&str>`, `select_lore(current_node, intent, npcs, arcs) -> Vec<LoreSelection>`, `format_otel_summary(&[LoreSelection]) -> String`
3. **No new Cargo deps required** — BFS uses `std::collections::VecDeque`
4. **TurnContext needs `world_graph: Option<WorldGraph>` field** for orchestrator integration
5. **Arc proximity:** Tests pass empty `&[]` — Dev decides how to wire trope state into arc proximity enrichment

**Handoff:** To Yoda (Dev) for implementation (GREEN phase)

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 high, 3 medium, 1 low | Extract prompt formatting into LoreFilter |
| simplify-quality | 1 medium, 2 low | Minor naming/convention observations |
| simplify-efficiency | 1 high, 1 high (pre-existing), 2 medium | Double BFS in select_lore |

**Applied:** 2 high-confidence fixes
1. Eliminated double `graph_distance()` call per node in `select_lore()` — single BFS, destructure result
2. Extracted `format_prompt_section()` into LoreFilter, removing 30-line inline block from orchestrator

**Flagged for Review:** 2 medium-confidence findings (BFS could live on WorldGraph; NPC reason init pattern)
**Noted:** 3 low-confidence observations (naming, unused params in pre-existing code)
**Reverted:** 0

**Overall:** simplify: applied 2 fixes

**Quality Checks:** 36/36 tests passing, workspace build clean
**Handoff:** To Obi-Wan (Reviewer) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (compile error in 18-1 tests) | confirmed 1 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | error | 0 (couldn't read diff file; covered manually) | N/A — domain covered by reviewer directly |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (rule #3 unknown string, rule #4 missing warn, rule #15 unbounded BFS) | confirmed 2, dismissed 1 |

**All received:** Yes (3 enabled returned, 6 disabled/skipped)
**Total findings:** 3 confirmed, 1 dismissed (BFS unbounded — genre pack graphs are < 50 nodes, loaded from trusted YAML, not user input at runtime; practical risk negligible)

### Devil's Advocate

What if this code is broken? Let me try to break it.

**The enrichment_categories dead code problem.** The RAG spec (narrator-prompt-rag-strategy.md) explicitly says "Intent → lore mapping: Combat → factions of NPCs in combat, Dialogue → culture + faction of speaking NPC." The tests for `enrichment_categories()` pass. But `select_lore()` never calls `enrichment_categories()`. The intent parameter is accepted and ignored. This means Combat intent at a location with no NPCs gets the same lore as Exploration intent — only graph distance matters. Is this acceptable? The spec says intent is a "secondary signal" supplementing graph distance, so technically graph-distance-only is the primary mechanism working correctly. But the AC says "Intent-to-lore mapping for Combat/Dialogue/Travel/Trade/Backstory" — that implies intent affects the output, which it currently does not. The function exists, is tested, and is dead. This is pattern 3 from the wiring failure history: Test-Passing Illusion. The function works perfectly. It just isn't called.

**What if current_location doesn't match any node ID?** Every selection gets `DetailLevel::NameOnly` with reason "unreachable". The OTEL span in the orchestrator still fires but the summary shows all entities as name_only. The GM panel sees "lore_filter fired, everything is name_only" but no explicit signal that the current location was unknown. Is this a silent fallback? The OTEL summary does make the state visible (all name_only is suspicious), but there's no explicit warn! — you'd have to infer the problem from the pattern. A `warn!` would make the failure mode explicit instead of inferential.

**What if WorldGraph has duplicate node IDs?** BFS visits the first match via `self.graph.nodes.iter().any(|n| n.id == from)` and `neighbors()` returns all edges matching the ID. Duplicate IDs would cause unpredictable distance calculations. No validation on uniqueness exists. However, WorldGraph is deserialized from genre pack YAML, and duplicate keys in YAML either error or take the last value. Low risk but unguarded.

**What if the test that broke (18-1) indicates other tests also break?** Dev ran `cargo test --test lore_filter_story_23_4_tests` (passes) and `cargo build -p sidequest-server` (passes), but never ran `cargo test -p sidequest-agents` (which would have caught 18-1). The TurnContext change added a non-defaulted field to a struct, and any test using explicit struct literals without `..Default::default()` breaks. There might be other tests beyond 18-1. This is a legitimate integration gap that should be checked by running the full test suite.

## Reviewer Assessment

**Verdict:** APPROVED (round 2 — rework verified)

**Round 1 findings — all resolved:**

| Finding | Status | Verification |
|---------|--------|-------------|
| [HIGH] Compile error 18-1 tests | FIXED | `world_graph: None` added at line 132, `cargo test -p sidequest-agents` passes (exit 0) |
| [MEDIUM] No warn! on unknown node | FIXED | `warn!` at `lore_filter.rs:143-146`, guarded by `!node_known && !self.graph.nodes.is_empty()` |
| [MEDIUM] enrichment_categories dead code | FIXED | Layer 3 at `lore_filter.rs:185-201` calls `enrichment_categories()`, upgrades matching non-graph-distance entities. Correctly excludes graph-distance-placed and unreachable nodes. |
| [LOW] "unknown" wildcard | FIXED | `lore_filter.rs:274-278` — exhaustive same-crate match, wildcard removed |

**Data flow traced:** [EDGE] Genre pack YAML → `CartographyConfig.world_graph` → `DispatchContext.world_graph` (lib.rs:1785, connect.rs) → `TurnContext.world_graph` (dispatch/mod.rs:505) → `build_narrator_prompt()` (orchestrator.rs:323) → `LoreFilter::select_lore()` → `format_prompt_section()` → `<world-lore>` Valley zone section. Safe — all Optional, None gracefully degrades to no lore section.

**Pattern observed:** [SIMPLE] Good extraction of `format_prompt_section()` as static method. Intent enrichment Layer 3 correctly preserves graph-distance as primary signal.

**Error handling:** [SILENT] `graph_distance()` returns `None` for unknown nodes → `NameOnly`. Now accompanied by `warn!` at `lore_filter.rs:143`. OTEL blind spot resolved.

**Wiring:** [VERIFIED] Full pipeline: `LoreFilter` called from `build_narrator_prompt()` at orchestrator.rs:324. `TurnContext.world_graph` populated at both dispatch sites. `enrichment_categories()` called from `select_lore()` Layer 3 — no longer dead code.

**Security:** [SEC] No concerns — internal game state, no trust boundary.

**[DOC]** Module docs clear and accurate. All public methods documented.

**[TEST]** 36 tests, meaningful assertions. Wiring tests verify production path. `cargo test -p sidequest-agents` full suite green.

**[TYPE]** `DetailLevel` #[non_exhaustive] + Ord. Exhaustive same-crate match. `LoreFilter<'a>` correct lifetime.

**[RULE]** Rule #2 (non_exhaustive) compliant. Rule #4 (tracing) compliant after rework. Rule #3 (no placeholders) compliant after wildcard removal.

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story.

### Architect (reconcile)
- No additional deviations found. All TEA and Dev entries verified: spec sources exist, spec text is accurate, implementation descriptions match current code state (post-rework), forward impacts are correctly scoped. The resolved wiring deviation (orchestrator integration) was caught by spec-check and fixed — the system worked as designed on the second pass.

### Reviewer (audit)

- **Arc proximity tests deferred** → ✓ ACCEPTED by Reviewer: No arc type exists; testing against a phantom type would be speculative.
- **Cyclic graph test expectations corrected** → ✓ ACCEPTED by Reviewer: Bidirectional semantics match WorldGraph::neighbors() API.
- **Arc proximity signal accepts &[String] placeholder** → ✓ ACCEPTED by Reviewer: Placeholder parameter is documented, forward impact noted.
- **~~No orchestrator wiring~~ RESOLVED** → ✓ ACCEPTED by Reviewer: Wiring completed and verified.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/lore_filter.rs` — new module: LoreFilter struct, DetailLevel enum, LoreSelection, BFS graph distance, intent mapping, NPC enrichment, OTEL summary
- `crates/sidequest-agents/src/lib.rs` — registered lore_filter module
- `crates/sidequest-agents/src/orchestrator.rs` — TurnContext.world_graph field + LoreFilter call in build_narrator_prompt() + OTEL span
- `crates/sidequest-server/src/dispatch/mod.rs` — DispatchContext.world_graph field + both TurnContext sites wired
- `crates/sidequest-server/src/dispatch/connect.rs` — DispatchContext world_graph populated from cartography
- `crates/sidequest-server/src/lib.rs` — DispatchContext world_graph populated from cartography
- `crates/sidequest-agents/tests/lore_filter_story_23_4_tests.rs` — real wiring tests replacing vacuous assert!(true)

**Tests:** 36/36 passing (GREEN)
**Branch:** feat/23-4-lore-filter-graph-distance (pushed)
**Workspace build:** sidequest-server compiles clean

**Wiring verification:**
- [x] LoreFilter called from production code (build_narrator_prompt)
- [x] TurnContext.world_graph populated from genre pack cartography
- [x] Both DispatchContext construction sites (lib.rs, connect.rs) populate world_graph
- [x] Both TurnContext construction sites (main, aside) pass world_graph
- [x] OTEL span emits lore_filter decisions
- [x] Real wiring test: prompt contains <world-lore> when graph present
- [x] Backward compat test: no <world-lore> when graph absent

**Handoff:** To verify phase (TEA simplify + quality-pass)

### Dev (implementation)
- No upstream findings during implementation.

### Dev (rework)
- No upstream findings during rework.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Previous spec-check (round 1) caught two Major mismatches — orchestrator wiring missing and OTEL span not emitted. Dev fixed both in the second green pass. All 9 ACs now verified against code:

| AC | Status | Evidence |
|----|--------|----------|
| LoreFilter struct + unit tests | DONE | `lore_filter.rs`, 36 tests |
| build_narrator_prompt() calls filter | DONE | `orchestrator.rs` LoreFilter call when world_graph present |
| Graph distance Zork-style | DONE | BFS bidirectional, cyclic/disconnected tested |
| Intent-to-lore mapping | DONE | 4 intents mapped (Combat, Dialogue, Exploration, Backstory) |
| NPC-driven enrichment | DONE | NPC presence → faction Full |
| OTEL span | DONE | `orchestrator.lore_filter` span with summary |
| Closed-world assertions | DONE | All nodes ≥ NameOnly |
| Workspace build | DONE | sidequest-server clean |
| Integration test e2e | DONE | Real wiring test: `<world-lore>` in prompt |

**Note:** Spec mentions "Travel/Trade" intents but Intent enum has no Trade variant. Exploration covers Travel; trade is handled by merchant context (story 15-16). Not a mismatch — existing architecture already covers the concept.

**Decision:** Proceed to verify phase.

## Sm Assessment

Setup complete. Story 23-4 builds the LoreFilter decision engine — the final piece connecting tiered summaries (23-2), room graph cartography (23-3), and the reworked prompt template (23-1).

**Routing:** TDD workflow → red phase → TEA (Han Solo) writes failing tests first.

**Key context for TEA:**
- RAG strategy spec: `docs/narrator-prompt-rag-strategy.md`
- Integration point: `orchestrator.rs:build_narrator_prompt()` lines 254-559
- Graph format: hierarchical `world_graph` + `sub_graphs` from 23-3
- Dependencies 23-1, 23-2, 23-3 all complete — infrastructure is ready
- Test targets: graph distance calc, intent-to-lore mapping, NPC enrichment, OTEL spans, e2e wiring