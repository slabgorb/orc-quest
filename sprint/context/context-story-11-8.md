---
parent: context-epic-11.md
---

# Story 11-8: Name Bank Generation — Produce Glossed Names with Morpheme Decomposition

## Business Context

Morpheme glossaries (11-7) define the building blocks. This story composes them into a bank
of ready-to-use names. Each name carries a gloss showing its morpheme decomposition:
`"Thal'verath" = thal(shadow) + vera(keeper) + th(honorific)`. The narrator draws from this
bank instead of inventing names, ensuring all names in a language share consistent structure.

**Python reference:** `sq-2/sprint/epic-63.yaml` — name generator combined prefix + root +
optional suffix, applied separator rules, produced glossed output. Rust follows the same
composition approach.

**Depends on:** Story 11-7 (MorphemeGlossary schema).

## Technical Approach

### GlossedName Model

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlossedName {
    pub display: String,                      // "Thal'verath"
    pub gloss: Vec<(String, String)>,         // [("thal","shadow"), ("vera","keeper"), ...]
    pub language: String,                     // "High Elvish"
}
```

### Name Bank

```rust
pub struct NameBank {
    pub language: String,
    pub names: Vec<GlossedName>,
    used: HashSet<usize>,  // track which names have been dispensed
}

impl NameBank {
    pub fn take_name(&mut self) -> Option<&GlossedName> {
        let idx = (0..self.names.len()).find(|i| !self.used.contains(i))?;
        self.used.insert(idx);
        Some(&self.names[idx])
    }
}
```

### Generation Algorithm

```rust
pub fn generate_name_bank(
    glossary: &MorphemeGlossary,
    count: usize,
    rng: &mut impl Rng,
) -> NameBank {
    let prefixes: Vec<_> = glossary.morphemes.iter()
        .filter(|m| m.position == MorphemePosition::Prefix).collect();
    let roots: Vec<_> = glossary.morphemes.iter()
        .filter(|m| m.position == MorphemePosition::Root).collect();
    let suffixes: Vec<_> = glossary.morphemes.iter()
        .filter(|m| m.position == MorphemePosition::Suffix).collect();

    let mut names = Vec::new();
    for _ in 0..count {
        // Pick prefix + root, optionally suffix
        let p = prefixes.choose(rng);
        let r = roots.choose(rng).expect("glossary must have roots");
        let s = if rng.gen_bool(0.5) { suffixes.choose(rng) } else { None };
        // Compose display form and gloss
        // ...
        names.push(glossed_name);
    }
    NameBank { language: glossary.language_name.clone(), names, used: HashSet::new() }
}
```

Names are pre-generated at session start. The `take_name()` method ensures no name is
used twice in the same session.

## Scope Boundaries

**In scope:**
- `GlossedName` struct with display form, gloss decomposition, language tag
- `NameBank` struct with take/tracking
- `generate_name_bank()` from morpheme glossary
- Composition: prefix + root + optional suffix
- Deduplication within generated bank

**Out of scope:**
- Narrator injection (11-9)
- Phonotactic enforcement (names follow morpheme forms, not phonetic rules)
- Multi-word names (place names with articles, etc.)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Names generated | Glossary with 10 morphemes → bank of N unique names produced |
| Gloss present | Each name has morpheme decomposition in `gloss` field |
| Display form | Display string concatenates morpheme forms with separator |
| No duplicates | Generated bank contains no duplicate display forms |
| Take tracking | `take_name()` never returns the same name twice |
| Exhaustion | After all names taken, `take_name()` returns None |
| Deterministic | Same seed → same name bank |
