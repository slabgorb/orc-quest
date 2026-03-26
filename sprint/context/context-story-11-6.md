---
parent: context-epic-11.md
---

# Story 11-6: Semantic Retrieval — Optional Embedding-Based RAG for Lore Query

## Business Context

Category + keyword search works for targeted queries but misses semantic connections. "Tell me
about the war" should find a fragment about "the siege of the northern fortress" even though
it doesn't contain the word "war." Embedding-based retrieval enables semantic similarity
search. This is optional — the system works without it, falling back to static retrieval.

**Python reference:** `sq-2/sidequest/lore/embedding_retriever.py` — uses sentence-transformers
to embed fragments and queries, cosine similarity for ranking. Rust defines the trait interface;
the embedding backend is pluggable.

**Depends on:** Story 11-2 (LoreStore).

## Technical Approach

### Retriever Trait

```rust
pub trait LoreRetriever {
    fn query(&self, store: &LoreStore, query: &str, max_tokens: usize)
        -> Vec<&LoreFragment>;
}

pub struct StaticRetriever;  // category + keyword (already in 11-2)
pub struct SemanticRetriever {
    embeddings: HashMap<String, Vec<f32>>,  // fragment_id → embedding
}
```

### Embedding Storage

```rust
impl SemanticRetriever {
    pub fn index(&mut self, fragment: &LoreFragment) {
        let embedding = self.embed(&fragment.content);
        self.embeddings.insert(fragment.id.clone(), embedding);
    }

    pub fn query(&self, store: &LoreStore, query: &str, max_tokens: usize)
        -> Vec<&LoreFragment>
    {
        let query_emb = self.embed(query);
        let mut scored: Vec<_> = store.all_fragments().iter()
            .filter_map(|f| {
                let emb = self.embeddings.get(&f.id)?;
                Some((f, cosine_similarity(&query_emb, emb)))
            })
            .collect();
        scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        // Take fragments within token budget
        token_bounded_take(scored, max_tokens)
    }
}
```

### Embedding Backend

The actual embedding call is behind a trait so tests can use mock embeddings:

```rust
pub trait Embedder: Send + Sync {
    fn embed(&self, text: &str) -> Vec<f32>;
}
```

Production could use a local model (via candle), an API call, or Claude's embedding endpoint.
The choice is deferred to implementation time per the epic context.

### Optional Activation

```rust
pub enum LoreRetrieverKind {
    Static(StaticRetriever),
    Semantic(SemanticRetriever),
}
```

Configuration flag determines which retriever is used. Missing embedder config falls back
to static retrieval with a log warning.

## Scope Boundaries

**In scope:**
- `LoreRetriever` trait with `query()` method
- `SemanticRetriever` struct with embedding index and cosine similarity
- `Embedder` trait for pluggable embedding backend
- Fallback to static retrieval when semantic is unavailable
- Token-budgeted results

**Out of scope:**
- Choosing a specific embedding model
- Persisting embeddings to disk
- Re-indexing on fragment update
- Hybrid retrieval (combining static + semantic scores)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Trait defined | `LoreRetriever` trait with query method compiles |
| Static works | StaticRetriever implements trait, behaves like 11-2 query |
| Semantic works | SemanticRetriever finds semantically related fragments with mock embedder |
| Cosine similarity | Higher similarity fragments ranked first |
| Token bounded | Results stay within max_tokens budget |
| Fallback | Missing embedder config → static retrieval used, warning logged |
| Pluggable | Custom Embedder impl can be injected for testing |
