# Context: Story 15-19 — Wire Conlang Knowledge

Story 15-19 is a wiring story. Four conlang functions are fully implemented but never called from the server dispatch pipeline. This document explains what each does and where it should be wired.

## Background: Conlang Architecture (ADR-043)

The conlang system lives in `sidequest-game/src/conlang.rs` and `sidequest-game/src/lore.rs`. It provides:

1. **MorphemeGlossary** — loaded from genre pack YAML, contains roots/prefixes/suffixes with meanings and pronunciation hints
2. **NameBank** — generated from a glossary using seeded RNG, produces GeneratedName objects with morpheme decomposition
3. **LoreStore** — can track character knowledge accumulated during play

When a name like "Zar'thi" is generated, it's decomposed: "Zar" (fire) + "thi" (one who) = "fire-one who" (gloss). This allows the narrator to reference morphemes the character knows, building linguistic coherence.

## The Four Unwired Functions

All located in `sidequest-game/src`:

### 1. record_language_knowledge()
**File:** `lore.rs:1742`

```rust
pub fn record_language_knowledge(
    store: &mut LoreStore,
    morpheme: &Morpheme,
    character_id: &str,
    turn: u64,
) -> Result<String, String>
```

**What it does:** Creates a LoreFragment in the lore store that records a character learning a conlang morpheme. The fragment includes:
- The morpheme string and its meaning
- Language ID
- Character ID
- Turn it was learned
- Source: `game_event`

**Example call:**
```rust
record_language_knowledge(&mut lore_store, &morpheme, "player-1", turn_number)?;
```

**When to call:** Post-narration, when conlang morphemes are detected in the narrator's output. If the narrator writes "The zar-keeper" (fire-keeper), that's a mention of the "zar" morpheme.

**Related OTEL event:** `conlang.morpheme_learned(character_id, language_id, morpheme)`

### 2. record_name_knowledge()
**File:** `lore.rs:1790`

```rust
pub fn record_name_knowledge(
    store: &mut LoreStore,
    generated_name: &GeneratedName,
    character_id: &str,
    turn: u64,
) -> Result<String, String>
```

**What it does:** Records that a character encountered a proper noun (NPC name, place, etc.). Creates a LoreFragment with:
- The name, gloss, and pronunciation
- Language ID
- Character ID
- Turn encountered
- Source: `game_event`

**Example call:**
```rust
let name = NameBank::generate(&glossary, &config).names[0];
record_name_knowledge(&mut lore_store, &name, "player-1", turn_number)?;
```

**When to call:** When an NPC is introduced with a generated name, or when a place name is generated for use in narration.

**Related OTEL event:** `conlang.name_recorded(name, language_id, gloss)`

### 3. query_language_knowledge()
**File:** `lore.rs:1825`

```rust
pub fn query_language_knowledge<'a>(
    store: &LoreStore,
    character_id: &str,
) -> Vec<LoreFragment>
```

**What it does:** Returns all language-related LoreFragments the character has accumulated (both morphemes and names). Used to provide context to the narrator so they stay consistent with known vocabulary.

**Example call:**
```rust
let known_language = query_language_knowledge(&lore_store, character_id);
// known_language contains all morphemes and names learned so far
```

**When to call:** During prompt building in `dispatch/prompt.rs`, to inject character's accumulated language knowledge into the narrator context.

**What the narrator does with it:** Uses the morphemes and names to maintain vocabulary consistency. Instead of improvising names, the narrator pulls from what the character already knows.

**Related OTEL event:** Logged as part of `conlang.context_injected`

### 4. format_name_bank_for_prompt()
**File:** `conlang.rs:156`

```rust
pub fn format_name_bank_for_prompt(bank: &NameBank, max_names: usize) -> String
```

**What it does:** Formats a NameBank into a markdown section suitable for prompt injection. Example output:

```
## Names (draconic)
- Zar'thi — "fire-walker" [ZAHR-thee]
- Keth'vor — "place-great" [KETH-vohr]
```

**Example call:**
```rust
let formatted = format_name_bank_for_prompt(&name_bank, 10);
// formatted is a markdown section ready to embed in the narrator prompt
```

**When to call:** During prompt building in `dispatch/prompt.rs`, when available names need to be injected for the narrator to pull from.

**What the narrator does with it:** Uses the formatted names and glosses to generate NPC introductions that feel linguistically coherent.

**Related OTEL event:** Logged as part of `conlang.context_injected`

## Dispatch Integration Points

### Point 1: NameBank → record_name_knowledge()

The dispatch pipeline generates names for NPCs and places. This happens in:
- NPC introduction/creation (when the narrator introduces a new character)
- Place name generation (when revealing a location)

**Location to add the call:** Wherever `NameBank::generate()` is called or wherever a GeneratedName is put into use. Likely in:
- `dispatch/npc_context.rs` when updating NPC registry with generated names
- `sidequest-agents` when the WorldBuilderAgent or NamegenAgent generates a name

**Code pattern:**
```rust
let name_bank = NameBank::generate(&glossary, &config);
for generated_name in &name_bank.names {
    if is_this_name_used_in_narration(&generated_name) {
        record_name_knowledge(
            &mut lore_store,
            &generated_name,
            snapshot.character.id(),
            snapshot.turn,
        )?;
    }
}
```

### Point 2: Narration → record_language_knowledge()

After narration is extracted, the dispatch pipeline should scan for morpheme mentions. This happens in:
- `dispatch/mod.rs` post-narration processing

**Location to add the call:** In the narration post-processing path (around `dispatch_player_action` or similar), after the narrator's response is extracted and parsed.

**Code pattern:**
```rust
// After narration extraction
let detected_morphemes = detect_morpheme_mentions(&narration_text, &glossary);
for morpheme in detected_morphemes {
    record_language_knowledge(
        &mut lore_store,
        &morpheme,
        snapshot.character.id(),
        snapshot.turn,
    )?;
    emit_otel("conlang.morpheme_learned", &[
        ("character_id", snapshot.character.id()),
        ("language_id", morpheme.language_id.clone()),
        ("morpheme", morpheme.morpheme.clone()),
    ]);
}
```

### Point 3: Prompt Building → query_language_knowledge() + format_name_bank_for_prompt()

The narrator prompt is built before each turn. This happens in:
- `dispatch/prompt.rs` in the context assembly phase

**Location to add the calls:** Alongside existing context injection (lore context, tone context, etc.), inject language context.

**Code pattern:**
```rust
// In dispatch/prompt.rs, alongside lore/tone context assembly
let language_fragments = query_language_knowledge(&lore_store, character_id);
let language_context = format_language_fragments_for_prompt(&language_fragments);

let name_bank = /* load from snapshot or genre pack */;
let name_bank_formatted = format_name_bank_for_prompt(&name_bank, 10);

let prompt_context = PromptContext {
    // ... existing fields ...
    language_knowledge: language_context,
    available_names: name_bank_formatted,
};

emit_otel("conlang.context_injected", &[
    ("names_count", name_bank.names.len().to_string()),
    ("morphemes_count", language_fragments.len().to_string()),
]);
```

## Testing Strategy

Every wiring point needs:

1. **Unit tests** — verify the function works in isolation (already exist in lore.rs and conlang.rs)
2. **Integration tests** — verify the function is called from production code paths

For example, if you wire `record_name_knowledge()` into NPC creation:
- Unit test: `record_name_knowledge()` creates a LoreFragment (exists)
- Integration test: NPC creation calls `record_name_knowledge()` and the fragment appears in lore store

Use the existing test helpers in the codebase (MockLoreStore, TestGameSnapshot) to build these.

## OTEL Observability

Each wiring point must emit OTEL events so the GM panel shows what's happening:

- **conlang.morpheme_learned** — when a morpheme is recorded
  - Fields: `character_id`, `language_id`, `morpheme`
- **conlang.name_recorded** — when a name is recorded
  - Fields: `name`, `language_id`, `gloss`
- **conlang.context_injected** — when language context is injected into narrator prompt
  - Fields: `names_count`, `morphemes_count`

All three events should be emitted during a single turn where all four functions are wired and active.

## Files to Modify

1. **dispatch/mod.rs** — Add morpheme detection and `record_language_knowledge()` call
2. **dispatch/prompt.rs** — Add `query_language_knowledge()` and `format_name_bank_for_prompt()` calls
3. **dispatch/npc_context.rs** or **sidequest-agents** — Add `record_name_knowledge()` call for name generation
4. **tests** — Add integration tests verifying end-to-end wiring

## Success Metrics

Once wired:
- OTEL shows `conlang.morpheme_learned` events (narrator mentions morphemes)
- OTEL shows `conlang.name_recorded` events (names are generated and used)
- OTEL shows `conlang.context_injected` events (prompt includes language context)
- Narrator stays consistent with learned vocabulary (e.g., reuses the same name for NPCs)
- GM panel displays all three event types with meaningful telemetry
