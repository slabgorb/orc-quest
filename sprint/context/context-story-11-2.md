---
parent: context-epic-11.md
---

# Story 11-2: LoreStore — In-Memory Indexed Collection with Add, Query by Category, Query by Keyword

## Business Context

LoreFragments need a home. The LoreStore is an in-memory collection that supports adding
fragments and querying them by category, keyword, or both. Agents ask "give me history lore
about the merchant guild within 500 tokens" and get back relevant fragments sorted by
relevance.

**Python reference:** `sq-2/sidequest/lore/store.py` — dict-of-lists indexed by category,
keyword search via substring matching. `sq-2/sidequest/lore/static_retriever.py` — query
interface with token budgeting.

**Depends on:** Story 11-1 (LoreFragment model).

## Technical Approach

### Store Structure

```rust
pub struct LoreStore {
    fragments: Vec<LoreFragment>,
    by_category: HashMap<LoreCategory, Vec<usize>>,  // indices into fragments
}
```

### Core API

```rust
impl LoreStore {
    pub fn new() -> Self { ... }

    pub fn add(&mut self, fragment: LoreFragment) {
        let idx = self.fragments.len();
        self.by_category.entry(fragment.category.clone())
            .or_default().push(idx);
        self.fragments.push(fragment);
    }

    pub fn query_by_category(&self, cat: &LoreCategory) -> Vec<&LoreFragment> { ... }

    pub fn query_by_keyword(&self, keyword: &str) -> Vec<&LoreFragment> {
        self.fragments.iter()
            .filter(|f| f.content.to_lowercase().contains(&keyword.to_lowercase()))
            .collect()
    }

    pub fn query(&self, query: LoreQuery) -> Vec<&LoreFragment> { ... }
}
```

### Token-Budgeted Query

```rust
pub struct LoreQuery {
    pub category: Option<LoreCategory>,
    pub keyword: Option<String>,
    pub max_tokens: Option<usize>,
}

impl LoreStore {
    pub fn query(&self, q: LoreQuery) -> Vec<&LoreFragment> {
        let mut results = self.fragments.iter().filter(|f| {
            q.category.as_ref().map_or(true, |c| &f.category == c)
            && q.keyword.as_ref().map_or(true, |k|
                f.content.to_lowercase().contains(&k.to_lowercase()))
        }).collect::<Vec<_>>();

        if let Some(budget) = q.max_tokens {
            let mut total = 0;
            results.retain(|f| {
                total += f.token_estimate;
                total <= budget
            });
        }
        results
    }
}
```

### No Persistence

LoreStore is in-memory only. It's rebuilt at session start from seed (11-3) and accumulates
during play. Cross-session persistence is a future save/load concern.

## Scope Boundaries

**In scope:**
- `LoreStore` struct with `Vec<LoreFragment>` and category index
- `add()`, `query_by_category()`, `query_by_keyword()`, `query()` methods
- Token-budgeted retrieval via `LoreQuery`
- Case-insensitive keyword matching

**Out of scope:**
- Semantic/embedding retrieval (11-6)
- Persistence to disk
- Fragment deduplication
- Relevance ranking beyond insertion order

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Add and retrieve | Add fragment, query by its category, get it back |
| Category index | Query for History returns only History fragments |
| Keyword search | Query for "merchant" finds fragment containing "merchant guild" |
| Case insensitive | Keyword "MERCHANT" matches "merchant guild" |
| Token budget | Query with max_tokens 100 stops including fragments past budget |
| Combined query | Category + keyword filters both apply |
| Empty results | Query for nonexistent category returns empty vec |
| Multiple fragments | Store with 50 fragments handles queries correctly |
