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
**Phase:** setup
**Phase Started:** 2026-04-04T10:45Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-04T10:45Z | - | - |

## Delivery Findings

No upstream findings.

## Design Deviations

None yet.

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
