---
parent: context-epic-16.md
---

# Story 16-11: Resource Threshold → KnownFact Pipeline — Permanent Narrator Memory

## Business Context

When Humanity hits 25, the narrator should know forever — not just the turn it happens.
This story wires ResourcePool threshold events into LoreStore as KnownFacts, making
resource milestones permanent narrator memory via the existing budget-aware selection.

## Technical Approach

### Pipeline

1. `ResourcePool::apply_delta()` fires a `ThresholdEvent`
2. Handler creates a `KnownFact`:
   - category: `"resource_event"`
   - keyword: event_id (e.g., `"humanity_cold"`)
   - content: narrator_hint (e.g., `"Your chrome is showing. NPCs notice."`)
   - relevance: 0.9 (high — always surfaces in budget selection)
3. `LoreStore::add_fact()` indexes it
4. Every subsequent narrator prompt includes the fact via existing budget-aware
   knowledge selection in prompt_framework

### LoreStore Integration

LoreStore (2,746 LOC) already has `KnownFact` with category, keyword, and content
fields. It already does budget-aware selection for narrator prompts. We're adding
facts, not changing the system.

```rust
// In the threshold event handler (likely in state.rs or a new resource_events.rs)
fn handle_threshold_event(event: &ThresholdEvent, lore_store: &mut LoreStore) {
    let fact = KnownFact {
        category: "resource_event".to_string(),
        keyword: event.event_id.clone(),
        content: event.narrator_hint.clone(),
        relevance: 0.9,
        // ... other KnownFact fields
    };
    lore_store.add_fact(fact);
}
```

### Idempotency

`ResourcePool.fired_thresholds: HashSet<String>` prevents re-firing on save/load.
LoreStore should also handle duplicate facts gracefully (upsert by keyword).

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/resource_pool.rs` | ThresholdEvent struct |
| `sidequest-game/src/lore.rs` | Verify add_fact handles resource_event category |
| `sidequest-game/src/state.rs` or new `resource_events.rs` | Threshold → KnownFact handler |
| `sidequest-agents/src/prompt_framework/mod.rs` | Verify resource facts appear in narrator context |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Threshold fires | Crossing a resource threshold creates a KnownFact |
| In LoreStore | Fact indexed with category "resource_event" and high relevance |
| In prompt | Fact appears in narrator prompt context on subsequent turns |
| Idempotent | Save/load doesn't duplicate facts |
| Multiple resources | Multiple resources can fire thresholds independently |
| Content correct | KnownFact content matches the narrator_hint from YAML |
