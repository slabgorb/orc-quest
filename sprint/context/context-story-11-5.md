---
parent: context-epic-11.md
---

# Story 11-5: Lore Accumulation — World State Agent Writes New Lore Fragments from Game Events

## Business Context

The lore store starts with seed data but must grow as the game progresses. When significant
events happen ("the party burned the bridge," "the NPC revealed the secret passage"), the
world state agent should emit new lore fragments. This makes past events retrievable in
future turns, solving the context amnesia problem for long sessions.

**Python reference:** `sq-2/sidequest/lore/worker.py` — background worker that processes
world state agent output, extracts lore-worthy events, creates fragments. Rust integrates
this into the existing post-turn world state agent response processing.

**Depends on:** Story 11-2 (LoreStore with add method).

## Technical Approach

### WorldStatePatch Extension

```rust
#[derive(Deserialize)]
pub struct WorldStatePatch {
    // ... existing fields
    #[serde(default)]
    pub new_lore: Vec<ProposedLore>,
}

#[derive(Deserialize)]
pub struct ProposedLore {
    pub category: LoreCategory,
    pub content: String,
}
```

### Agent Prompt Addition

The world state agent's system prompt gains:

```
If something narratively significant happened this turn, emit a lore entry.
Only create lore for facts worth remembering across future turns:
- Major events (battle outcomes, discoveries, betrayals)
- World state changes (locations destroyed, factions shifted)
- Character revelations (secrets revealed, alliances formed)
Do NOT create lore for routine actions or trivial dialogue.
```

### Post-Turn Processing

```rust
fn process_new_lore(&mut self, proposed: &[ProposedLore], turn_id: u64) {
    for entry in proposed {
        let id = format!("event-turn-{}-{}", turn_id, self.lore_store.len());
        let mut fragment = LoreFragment::new(
            &id, entry.category.clone(), &entry.content, LoreSource::GameEvent,
        );
        fragment.turn_created = Some(turn_id);
        self.lore_store.add(fragment);
    }
}
```

### Guardrails

- Maximum 3 lore fragments per turn (prevents flooding)
- Content length capped at 500 chars per fragment
- Duplicate-ish detection: skip if content is >80% similar to existing fragment (simple check)

## Scope Boundaries

**In scope:**
- `new_lore` field on WorldStatePatch
- `ProposedLore` deserialization
- World state agent prompt instructions for lore emission
- Post-turn processing to add fragments to LoreStore
- Rate limiting (max 3 per turn, length cap)

**Out of scope:**
- Lore editing or deletion
- Cross-session lore persistence
- Semantic deduplication (only simple substring check)
- Player-created lore

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Patch parsed | WorldStatePatch with `new_lore` array deserializes correctly |
| Fragment added | Proposed lore creates LoreFragment in store with GameEvent source |
| Turn tracked | Fragment has `turn_created` set to current turn ID |
| Rate limited | Only first 3 lore entries per turn are stored; extras dropped |
| Length capped | Content over 500 chars is truncated |
| Empty array | Turn with no significant events → empty `new_lore`, no fragments added |
| Queryable | Accumulated lore appears in subsequent lore queries |
