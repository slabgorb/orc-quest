---
parent: context-epic-11.md
---

# Story 11-4: Lore Injection into Agent Prompts — Relevant Lore Fragments Included in Narrator/World State Context

## Business Context

The lore store is useless if agents never see its contents. This story hooks the lore query
system into prompt composition so the narrator and world state agent receive relevant lore
context. The narrator can reference past events accurately instead of contradicting or
forgetting them.

**Python reference:** `sq-2/sidequest/lore/retriever.py` — called during prompt composition,
returns fragments within a token budget. Rust integrates with the existing `AgentContext`
builder from story 2-5.

**Depends on:** Story 11-2 (LoreStore with query method).

## Technical Approach

### Agent Context Integration

```rust
impl AgentContext {
    pub fn add_relevant_lore(&mut self, store: &LoreStore, hints: &LoreHints) {
        let query = LoreQuery {
            category: hints.preferred_category.clone(),
            keyword: hints.keyword.clone(),
            max_tokens: Some(hints.token_budget),
        };
        let fragments = store.query(query);
        if fragments.is_empty() { return; }

        let mut section = String::from("## Relevant Lore\n");
        for frag in &fragments {
            section.push_str(&format!("- [{}] {}\n",
                frag.category.display_name(), frag.content));
        }
        self.sections.push(section);
    }
}
```

### Hints per Agent

Each agent type gets different lore hints:

```rust
fn lore_hints_for_agent(agent: AgentKind, state: &GameState) -> LoreHints {
    match agent {
        AgentKind::Narrator => LoreHints {
            preferred_category: None,  // all categories
            keyword: state.location_keyword(),
            token_budget: 800,
        },
        AgentKind::WorldBuilder => LoreHints {
            preferred_category: Some(LoreCategory::Event),
            keyword: None,
            token_budget: 500,
        },
        _ => LoreHints { preferred_category: None, keyword: None, token_budget: 300 },
    }
}
```

### Token Budgeting

Lore competes with other prompt sections for context window space. The `token_budget` field
on `LoreHints` caps how much lore goes into any single prompt. Budgets are conservative
(500-800 tokens) to leave room for game state and instructions.

## Scope Boundaries

**In scope:**
- `add_relevant_lore()` on AgentContext
- `LoreHints` struct with category, keyword, token budget
- Per-agent hint configuration
- Formatted lore section in prompt

**Out of scope:**
- Semantic retrieval (11-6)
- Dynamic budget adjustment based on prompt length
- Lore relevance scoring beyond category + keyword

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Narrator sees lore | Narrator prompt contains "Relevant Lore" section with fragments |
| WorldBuilder sees lore | World state agent prompt includes Event-category lore |
| Token bounded | Lore section stays within configured token budget |
| Empty store | Empty lore store → no lore section added (no empty header) |
| Keyword filtering | Location-based keyword filters to relevant fragments |
| Category filtering | WorldBuilder gets Event fragments, not Geography |
| Format readable | Each fragment shows category tag and content on one line |
