---
parent: context-epic-3.md
---

# Story 3-4: Entity Reference Validation — Narration Mentions Checked Against GameSnapshot

## Business Context

The narrator generates prose that references characters, NPCs, items, and locations by name.
When the LLM hallucinates — mentioning an NPC who doesn't exist, referencing a sword the
player never acquired, or naming a location that isn't in the game world — the immersion
breaks. Worse, the player might try to interact with the hallucinated entity, causing confusion
cascading through subsequent turns.

Python's sq-2 has no protection against this. The narrator can freely invent entities and
the engine will happily broadcast the narration. The Game Watcher catches these by building
an entity registry from the GameSnapshot and scanning the narration for references that don't
match anything known.

This is a heuristic check, not a deterministic one. Natural language is ambiguous — "the old
keeper" might refer to NPC "Grimjaw" by role rather than name. The check errs on the side
of false negatives (missing a bad reference) rather than false positives (flagging valid
prose). Every flag is for human review, consistent with ADR-031's "God lifting rocks"
principle: the watcher surfaces; the operator judges.

**ADR:** ADR-031 (semantic telemetry, human-judgment principle)
**Depends on:** Story 3-2 (TurnRecord assembly and mpsc channel)

## Technical Approach

### Building the Entity Registry

The registry is built fresh from each TurnRecord's `snapshot_after`. It collects all named
entities the game currently knows about.

```rust
pub struct EntityRegistry {
    pub character_names: HashSet<String>,
    pub npc_names: HashSet<String>,
    pub item_names: HashSet<String>,
    pub location_names: HashSet<String>,
    pub region_names: HashSet<String>,
}

impl EntityRegistry {
    pub fn from_snapshot(snapshot: &GameSnapshot) -> Self {
        let mut registry = EntityRegistry {
            character_names: HashSet::new(),
            npc_names: HashSet::new(),
            item_names: HashSet::new(),
            location_names: HashSet::new(),
            region_names: HashSet::new(),
        };

        for character in &snapshot.characters {
            registry.character_names.insert(character.name.clone());
            for item in &character.inventory.items {
                registry.item_names.insert(item.name.clone());
            }
        }
        for npc in &snapshot.npcs {
            registry.npc_names.insert(npc.name.clone());
        }
        registry.location_names.insert(snapshot.location.clone());
        for region in &snapshot.discovered_regions {
            registry.region_names.insert(region.clone());
        }

        registry
    }

    /// Check if a candidate string matches any known entity (case-insensitive).
    /// Returns true if the candidate is a substring of any known name, or vice versa.
    pub fn matches(&self, candidate: &str) -> bool {
        let lower = candidate.to_lowercase();
        self.all_names().any(|name| {
            let name_lower = name.to_lowercase();
            name_lower.contains(&lower) || lower.contains(&name_lower)
        })
    }

    fn all_names(&self) -> impl Iterator<Item = &String> {
        self.character_names.iter()
            .chain(self.npc_names.iter())
            .chain(self.item_names.iter())
            .chain(self.location_names.iter())
            .chain(self.region_names.iter())
    }
}
```

### Extracting Potential Entity References

The extractor scans narration text for capitalized words and phrases that look like proper
nouns — the simplest heuristic that catches most entity names without NLP dependencies.

```rust
/// Extract capitalized phrases from narration that might be entity references.
/// Filters out common English words and sentence-initial capitalization.
pub fn extract_potential_references(narration: &str) -> Vec<String> {
    let stop_words: HashSet<&str> = [
        "The", "A", "An", "He", "She", "It", "They", "You", "Your",
        "His", "Her", "Its", "Their", "This", "That", "These", "Those",
        "With", "From", "Into", "Upon", "After", "Before", "Through",
        "Behind", "Beyond", "Above", "Below", "But", "And", "Or", "Not",
        "What", "Where", "When", "How", "Who", "Why",
    ].iter().copied().collect();

    let mut references = Vec::new();

    // Split into sentences, skip first word of each (sentence-initial caps)
    for sentence in narration.split(['.', '!', '?']) {
        let words: Vec<&str> = sentence.split_whitespace().collect();
        // Start from index 1 to skip sentence-initial capitalization
        let mut i = 1;
        while i < words.len() {
            let word = words[i].trim_matches(|c: char| !c.is_alphanumeric());
            if !word.is_empty()
                && word.chars().next().map_or(false, |c| c.is_uppercase())
                && !stop_words.contains(word)
            {
                // Collect consecutive capitalized words as a phrase
                let mut phrase = vec![word.to_string()];
                let mut j = i + 1;
                while j < words.len() {
                    let next = words[j].trim_matches(|c: char| !c.is_alphanumeric());
                    if !next.is_empty()
                        && next.chars().next().map_or(false, |c| c.is_uppercase())
                        && !stop_words.contains(next)
                    {
                        phrase.push(next.to_string());
                        j += 1;
                    } else {
                        break;
                    }
                }
                references.push(phrase.join(" "));
                i = j;
            } else {
                i += 1;
            }
        }
    }

    references
}
```

### The Validation Check

```rust
pub fn check_entity_references(record: &TurnRecord) -> Vec<ValidationResult> {
    let registry = EntityRegistry::from_snapshot(&record.snapshot_after);
    let candidates = extract_potential_references(&record.narration);
    let mut results = Vec::new();

    for candidate in &candidates {
        if !registry.matches(candidate) {
            tracing::warn!(
                component = "watcher",
                check = "entity_reference",
                unresolved = %candidate,
                "Narration references unknown entity"
            );
            results.push(ValidationResult::Warning(
                format!("Unresolved entity reference: '{}'", candidate)
            ));
        }
    }

    results
}
```

### Reducing False Positives

Several strategies keep the noise down without adding complexity:

1. **Stop words** — Common English words that happen to be capitalized are filtered out
2. **Sentence-initial skip** — First word of every sentence is skipped (capitalized by grammar, not naming)
3. **Substring matching** — "Old Grimjaw" matches NPC "Grimjaw" because the known name is a substring of the candidate
4. **No single-letter candidates** — Words like "I" are ignored via the trim/empty check

If the false positive rate is still too high in practice, future iterations could:
- Load genre-specific vocabulary from the genre pack (spell names, location adjectives)
- Use quoted strings in narration as higher-confidence entity references
- Weight candidates by frequency (a name appearing once is more suspicious than one appearing five times)

These are deferred — start simple, measure, iterate.

### Testing Strategy

Tests craft narrations with known entity names and verify correct flagging behavior.

```rust
#[test]
fn known_character_not_flagged() {
    let record = make_record_with_narration(
        "Kael draws his sword and charges forward.",
        vec!["Kael"],  // character names
    );
    let results = check_entity_references(&record);
    assert!(results.is_empty());
}

#[test]
fn unknown_entity_flagged() {
    let record = make_record_with_narration(
        "Suddenly, Mordecai appears from the shadows.",
        vec!["Kael"],  // Mordecai is not a known entity
    );
    let results = check_entity_references(&record);
    assert!(results.iter().any(|r| matches!(r, ValidationResult::Warning(_))));
}

#[test]
fn compound_name_substring_match() {
    let record = make_record_with_narration(
        "Old Grimjaw slams his fist on the table.",
        vec![],  // character names
        vec!["Grimjaw"],  // NPC names
    );
    let results = check_entity_references(&record);
    // "Old Grimjaw" should match NPC "Grimjaw" via substring
    assert!(results.is_empty());
}

#[test]
fn sentence_initial_caps_not_flagged() {
    let record = make_record_with_narration(
        "Darkness falls. Shadows creep across the floor.",
        vec!["Kael"],
    );
    let results = check_entity_references(&record);
    // "Darkness" and "Shadows" are sentence-initial, not entity refs
    assert!(results.is_empty());
}
```

### Rust Concept: Owned vs Borrowed in the Registry

The EntityRegistry owns its `HashSet<String>` data because it's built from a snapshot that
might be borrowed temporarily. In Python you'd just keep references to the snapshot's name
fields — in Rust the borrow checker would complain if the registry outlives the snapshot
reference. Cloning the strings into owned `HashSet<String>` is the pragmatic choice here:
entity counts are small (dozens, not thousands) and the registry is rebuilt per turn on the
cold path. No need to optimize with lifetimes.

## Scope Boundaries

**In scope:**
- `EntityRegistry` struct built from GameSnapshot (characters, NPCs, items, locations, regions)
- `extract_potential_references()` — capitalized-phrase extraction from narration text
- `check_entity_references()` — matching candidates against registry, emitting warnings for unresolved
- Substring matching (bidirectional) for compound names
- Stop word filtering and sentence-initial capitalization skip
- Unit tests with crafted narration and known/unknown entities
- Tracing events tagged `component="watcher"`, `check="entity_reference"`

**Out of scope:**
- NLP or ML-based entity recognition — no external dependencies
- Semantic understanding of descriptions ("the old keeper" -> "Grimjaw")
- Genre-specific vocabulary loading from genre packs (future improvement)
- Automated correction of unresolved references
- Levenshtein/fuzzy matching beyond substring containment (defer unless needed)
- Integration with watcher WebSocket (story 3-6)
- Trope-aware entity checks (story 3-8)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Registry built from snapshot | All character names, NPC names, item names, location, and region names extracted into EntityRegistry |
| Narration scanned | Capitalized phrases extracted from narration, excluding stop words and sentence-initial caps |
| Known entities pass | References matching known entities (exact or substring) produce no warnings |
| Unknown entities flagged | References not matching any known entity produce ValidationResult::Warning |
| Compound names handled | "Old Grimjaw" matches NPC "Grimjaw" via substring containment |
| False positives controlled | Common English words, sentence-initial caps, and single-letter words do not trigger warnings |
| Tracing events emitted | Each unresolved reference emits tracing::warn! with component="watcher" and check="entity_reference" |
| Unit tests cover key cases | Tests for: known entity, unknown entity, compound name match, sentence-initial skip, empty narration |
