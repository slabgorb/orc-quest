---
story_id: "16-11"
jira_key: "none"
epic: "16"
workflow: "tdd"
branch: "feat/16-11-resource-threshold-knownfact"
repos:
  - sidequest-api
points: 3
priority: p1
---

# Story 16-11: Resource threshold → KnownFact pipeline — permanent narrator memory

## Goal
When a ResourcePool crosses a threshold, mint a LoreFragment (conceptually a "KnownFact")
in LoreStore with the threshold's event_id and narrator_hint. High relevance ensures it
surfaces in every future narrator prompt via existing budget-aware selection. The LLM
cannot forget that "Humanity hit 25" because the knowledge system tells it every turn.

## Builds On
- Story 16-10: ResourcePool struct, YAML schema, and patch pipeline (merged)

## Architecture
- ResourcePool thresholds already detect downward crossings (detect_crossings in resource_pool.rs)
- apply_resource_patch / apply_pool_decay return crossed thresholds
- New: bridge function mints LoreFragment from each ResourceThreshold crossing
- LoreFragment uses event_id as fragment id → LoreStore.add() prevents duplicates naturally
- Category: Event (high priority in budget-aware selection)
- Source: GameEvent
- turn_created set to current turn for recency sorting

## Acceptance Criteria
1. apply_resource_patch crossing → LoreFragment minted in LoreStore
2. LoreFragment has threshold's event_id (as id) and narrator_hint (as content)
3. High relevance: Event category + recent turn_created ensures budget selection picks it
4. apply_pool_decay crossings also mint LoreFragments
5. Already-crossed thresholds → no duplicate LoreFragments (LoreStore.add duplicate rejection)
6. Multiple thresholds crossed in one patch → multiple LoreFragments
7. Integration: LoreFragment appears in select_lore_for_prompt output

## Test File
`crates/sidequest-game/tests/resource_threshold_knownfact_story_16_11_tests.rs`
