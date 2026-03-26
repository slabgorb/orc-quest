---
parent: context-epic-11.md
---

# Story 11-3: Lore Seed — Bootstrap Store from Genre Pack Lore Entries and Character Creation Anchors

## Business Context

A new session shouldn't start with an empty lore store. Genre packs contain world-building
facts (geography, factions, history) and character creation produces anchor facts (backstory,
relationships). This story seeds the lore store at session start so agents have baseline
context from turn one.

**Python reference:** `sq-2/sidequest/lore/seed.py` — reads genre pack `lore` section and
character creation events, creates LoreFragment for each. Rust reads from the same YAML
genre pack structure.

**Depends on:** Story 11-2 (LoreStore with add method).

## Technical Approach

### Genre Pack Lore Section

```yaml
lore:
  - category: history
    content: "The Flickering Reach was once a unified kingdom before the Shattering."
  - category: geography
    content: "The Iron Wastes stretch north of the settlement, toxic and irradiated."
  - category: faction
    content: "The Salvage Union controls trade in recovered pre-war technology."
```

### Seed Function

```rust
pub fn seed_lore_store(genre_pack: &GenrePack, characters: &[Character]) -> LoreStore {
    let mut store = LoreStore::new();

    // Genre pack lore entries
    for (i, entry) in genre_pack.lore.iter().enumerate() {
        store.add(LoreFragment::new(
            &format!("genre-{}", i),
            entry.category.clone(),
            &entry.content,
            LoreSource::GenrePack,
        ));
    }

    // Character creation anchors
    for character in characters {
        if let Some(backstory) = &character.backstory {
            store.add(LoreFragment::new(
                &format!("char-{}-backstory", character.name),
                LoreCategory::Character,
                backstory,
                LoreSource::CharacterCreation,
            ));
        }
    }

    store
}
```

### Session Integration

The orchestrator calls `seed_lore_store()` during session initialization, after genre pack
loading and character creation/loading. The resulting store is attached to the session state.

## Scope Boundaries

**In scope:**
- `seed_lore_store()` function
- Parse genre pack `lore` YAML section into fragments
- Convert character backstory/relationships into Character-category fragments
- Assign LoreSource::GenrePack or LoreSource::CharacterCreation

**Out of scope:**
- Game-event lore accumulation (11-5)
- Lore injection into prompts (11-4)
- Custom lore from save files (persistence concern)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Genre lore seeded | Genre pack with 5 lore entries → store contains 5 fragments |
| Source tagged | Genre pack fragments have source `GenrePack` |
| Character anchors | Character with backstory → Character-category fragment created |
| No backstory | Character without backstory field → no fragment created, no error |
| Categories parsed | YAML `category: history` → `LoreCategory::History` |
| IDs unique | Each seeded fragment has a unique ID |
| Token estimates | All seeded fragments have computed token estimates |
