---
parent: context-epic-11.md
---

# Story 11-10: Language Knowledge as KnownFact — Transliteration Comprehension Grows Through Play

## Business Context

In-game languages should feel like real barriers that the player gradually overcomes. Early in
a session, foreign text is opaque. After encountering words in context, the player begins to
understand fragments. After study or prolonged exposure, full transliteration becomes available.
This models language learning as progressive KnownFact accumulation.

**Python reference:** `sq-2/sprint/epic-63.yaml` — language morphemes tracked as KnownFact
entries with comprehension levels (unknown, partial, full). Rust implements the same
progression using the KnownFact model from Epic 9.

**Depends on:** Story 11-9 (narrator name injection), Epic 9 (KnownFact system).

## Technical Approach

### Comprehension Levels

```rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ComprehensionLevel {
    Unknown,    // "The sign reads: 'ᚦᚨᛚ ᚹᛖᚱᚨᚦ'"
    Partial,    // "The sign reads something about shadows"
    Full,       // "The sign reads: 'Thal'verath — shadow keeper'"
}
```

### Language Knowledge as KnownFact

Each morpheme the player has been exposed to is tracked as a KnownFact:

```rust
fn morpheme_known_fact(morpheme: &Morpheme, language: &str, level: ComprehensionLevel)
    -> KnownFact
{
    KnownFact {
        id: format!("lang-{}-{}", language, morpheme.form),
        category: KnownFactCategory::Language,
        content: format!("'{}' means '{}' in {}", morpheme.form, morpheme.meaning, language),
        comprehension: level,
    }
}
```

### Exposure Tracking

When a glossed name appears in narration, the morphemes in that name gain exposure:

```rust
fn process_language_exposure(
    known_facts: &mut KnownFactStore,
    name: &GlossedName,
) {
    for (form, meaning) in &name.gloss {
        let fact_id = format!("lang-{}-{}", name.language, form);
        match known_facts.get(&fact_id) {
            None => known_facts.add(morpheme_fact(form, meaning, &name.language,
                                                   ComprehensionLevel::Partial)),
            Some(f) if f.comprehension == ComprehensionLevel::Partial => {
                // Second+ exposure: upgrade to Full
                known_facts.upgrade(&fact_id, ComprehensionLevel::Full);
            }
            _ => {} // Already full
        }
    }
}
```

### Narrator Integration

The narrator receives comprehension context for foreign text rendering:

```
When rendering foreign language text, check the player's comprehension:
- Unknown morphemes: show in script/cipher form
- Partial: show vague meaning ("something about shadows")
- Full: show transliteration ("shadow keeper")
```

## Scope Boundaries

**In scope:**
- `ComprehensionLevel` enum (Unknown, Partial, Full)
- Morpheme exposure tracking via KnownFact
- Progressive comprehension: first encounter → Partial, subsequent → Full
- Narrator prompt instructions for rendering foreign text by comprehension level

**Out of scope:**
- Active study mechanic (player explicitly studying a language)
- Language skill checks or rolls
- Script/cipher rendering (narrator handles display, not the system)
- Multiple comprehension tiers beyond three levels

## Acceptance Criteria

| AC | Detail |
|----|--------|
| First exposure | Encountering "Thal'verath" creates Partial KnownFact for "thal" and "vera" |
| Second exposure | Seeing "thal" in another name upgrades to Full comprehension |
| Already full | Third exposure to Full morpheme → no change, no error |
| Narrator guided | Prompt includes instructions for rendering by comprehension level |
| Unknown default | Morpheme never encountered → not in KnownFact store → treated as Unknown |
| Per-language | Morphemes tracked per language (same form in different languages = separate facts) |
| Serializable | Comprehension state round-trips through save/load |
