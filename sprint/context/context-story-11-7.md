---
parent: context-epic-11.md
---

# Story 11-7: Morpheme Glossary Schema — Conlang Morphemes with Meaning and Pronunciation Rules

## Business Context

Genre packs need a way to define fictional languages. A morpheme glossary declares the building
blocks — small units of form and meaning — that name generation (11-8) will compose into
consistent names. "thal" means "shadow" and goes at the start of a word; "vera" means "keeper"
and is a root. This ensures every name in a language shares phonetic patterns.

**Python reference:** `sq-2/sprint/epic-63.yaml` — morpheme glossary as YAML list under
`languages` key in genre pack. Rust deserializes into typed structs.

**Depends on:** Story 11-1 (LoreFragment model — language is a lore category).

## Technical Approach

### Genre Pack YAML Schema

```yaml
languages:
  high_elvish:
    phonotactics: "CV(C) syllables, no initial clusters"
    morphemes:
      - form: thal
        meaning: shadow
        position: prefix
      - form: vera
        meaning: keeper
        position: root
      - form: th
        meaning: honorific
        position: suffix
      - form: mira
        meaning: star
        position: prefix
```

### Rust Types

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MorphemeGlossary {
    pub language_name: String,
    #[serde(default)]
    pub phonotactics: String,
    pub morphemes: Vec<Morpheme>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Morpheme {
    pub form: String,
    pub meaning: String,
    pub position: MorphemePosition,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum MorphemePosition {
    Prefix,
    Root,
    Suffix,
}
```

### Genre Pack Integration

```rust
pub struct GenrePack {
    // ... existing fields
    #[serde(default)]
    pub languages: HashMap<String, MorphemeGlossary>,
}
```

Genre packs without languages get an empty map. The language name key ("high_elvish")
is stored both in the map key and optionally in `language_name` for display.

## Scope Boundaries

**In scope:**
- `MorphemeGlossary`, `Morpheme`, `MorphemePosition` structs
- YAML schema for `languages` section of genre pack
- Deserialization into typed structs
- Phonotactics as a freeform string (descriptive, not enforced)

**Out of scope:**
- Name generation from morphemes (11-8)
- Phonotactic rule enforcement (freeform text for narrator guidance)
- Procedural language generation (morphemes are hand-authored)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Types compile | MorphemeGlossary, Morpheme, MorphemePosition derive Serialize/Deserialize |
| YAML parses | Genre pack with `languages` section deserializes correctly |
| Positions | Prefix, Root, Suffix all parse from snake_case YAML |
| No languages | Genre pack without `languages` key loads with empty map |
| Multiple languages | Genre pack with 3 languages loads all glossaries |
| Morpheme count | Glossary with 20+ morphemes loads without issue |
| Phonotactics | Optional phonotactics string preserved through round-trip |
