---
parent: context-epic-11.md
---

# Story 11-1: LoreFragment Model — Indexed Narrative Fact with Category, Token Estimate, Metadata

## Business Context

The narrator suffers from "context amnesia" — it only sees the current game snapshot, not the
history of what happened. LoreFragment is the atomic unit of memory: a single indexed fact
("the merchant guild declared war on the thieves' quarter") with category, token cost, and
source tracking. This model is the foundation for the entire lore system.

**Python reference:** `sq-2/sidequest/lore/models.py` — `LoreFragment` dataclass with `id`,
`category`, `content`, `token_estimate`, `source`, `metadata`. Rust uses typed enums where
Python used string literals.

**Depends on:** Story 2-5 (game state context for turn tracking).

## Technical Approach

### Core Model

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoreFragment {
    pub id: String,
    pub category: LoreCategory,
    pub content: String,
    pub token_estimate: usize,
    pub source: LoreSource,
    pub turn_created: Option<u64>,
    pub metadata: HashMap<String, String>,
}
```

### Category Enum

```rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum LoreCategory {
    History,
    Geography,
    Faction,
    Character,
    Item,
    Event,
    Language,
    Custom(String),
}
```

The `Custom(String)` variant lets genre packs define domain-specific categories without
changing the core enum.

### Source Tracking

```rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum LoreSource {
    GenrePack,
    CharacterCreation,
    GameEvent,
}
```

### Token Estimation

```rust
impl LoreFragment {
    pub fn estimate_tokens(content: &str) -> usize {
        // Simple heuristic: ~4 chars per token for English
        (content.len() + 3) / 4
    }

    pub fn new(id: &str, category: LoreCategory, content: &str, source: LoreSource) -> Self {
        Self {
            id: id.to_string(),
            category,
            token_estimate: Self::estimate_tokens(content),
            content: content.to_string(),
            source,
            turn_created: None,
            metadata: HashMap::new(),
        }
    }
}
```

Token estimation uses a rough heuristic. Exact tokenizer integration is out of scope.

## Scope Boundaries

**In scope:**
- `LoreFragment` struct with all fields
- `LoreCategory` enum with 7 fixed variants + `Custom(String)`
- `LoreSource` enum with 3 variants
- Token estimation heuristic
- `new()` constructor
- Serialize/Deserialize derives

**Out of scope:**
- Storage and indexing (11-2 — LoreStore)
- Seeding from genre packs (11-3)
- Embedding vectors for semantic retrieval (11-6)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct compiles | `LoreFragment` with all fields derives Serialize/Deserialize |
| Category enum | All 7 fixed variants + Custom(String) usable |
| Source enum | GenrePack, CharacterCreation, GameEvent variants |
| Token estimate | 100-char string estimates ~25 tokens |
| Metadata | Arbitrary key-value pairs stored in HashMap |
| Round-trip | Serialize → deserialize preserves all fields including Custom category |
| Constructor | `new()` auto-computes token estimate |
