---
parent: context-epic-7.md
---

# Story 7-1: BeliefState Model — Per-NPC Knowledge Bubbles with Facts, Suspicions, Claims, and Credibility Scores

## Business Context

In a whodunit scenario, the barkeep shouldn't know what the guard whispered to the smith.
Each NPC needs an independent knowledge bubble — what they witnessed, what they've been
told, what they suspect, and how credible their claims are. Python's `belief_state.py`
enforced these invariants at runtime with assertions. Rust encodes them in the type system:
credibility is bounded, claims track provenance, and facts track how they were learned.

**Python ref:** `sq-2/sidequest/scenario/belief_state.py`
**Depends on:** Story 2-5 (orchestrator turn loop — NPC infrastructure in GameSnapshot)

## Technical Approach

```rust
/// Per-NPC knowledge bubble. Each NPC sees the world through their own lens.
pub struct BeliefState {
    pub npc_id: String,
    pub facts: Vec<Fact>,
    pub suspicions: Vec<Suspicion>,
    pub claims: Vec<Claim>,
    credibility: Credibility,  // private — enforced 0.0-1.0
}

/// Bounded f64 that enforces 0.0-1.0 invariant at construction.
#[derive(Debug, Clone, Copy)]
pub struct Credibility(f64);

impl Credibility {
    pub fn new(value: f64) -> Self {
        Self(value.clamp(0.0, 1.0))
    }
    pub fn decay(&mut self, factor: f64) {
        self.0 = (self.0 * factor).clamp(0.0, 1.0);
    }
    pub fn value(&self) -> f64 { self.0 }
}

pub struct Fact {
    pub content: String,
    pub source: FactSource,
    pub turn_learned: u64,
}

pub enum FactSource {
    Witnessed,
    ToldBy(String),  // npc_id
    Deduced,
}

pub struct Claim {
    pub content: String,
    pub source_npc: String,
    pub corroborated_by: Vec<String>,
    pub contradicted_by: Vec<String>,
}

pub struct Suspicion {
    pub target_npc: String,
    pub reason: String,
    pub confidence: Credibility,
}
```

The `Credibility` newtype is the key Rust win — Python uses `assert 0 <= credibility <= 1`
scattered through methods. Rust makes illegal states unrepresentable.

`BeliefState` provides methods for adding facts, registering claims, and recording
suspicions. Claims check for contradictions against existing facts on insertion.

## Scope Boundaries

**In scope:**
- `BeliefState`, `Fact`, `Claim`, `Suspicion`, `Credibility` types
- Methods: `add_fact()`, `add_claim()`, `add_suspicion()`, `has_fact()`
- Contradiction detection on claim insertion
- Serde serialization for save/load
- Comprehensive unit tests for invariant enforcement

**Out of scope:**
- Gossip propagation between NPCs (story 7-2)
- Clue activation (story 7-3)
- Scenario lifecycle (story 7-9)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Credibility bounded | `Credibility::new(1.5)` clamps to 1.0; `new(-0.3)` clamps to 0.0 |
| Fact provenance | Every fact tracks `FactSource` (Witnessed, ToldBy, Deduced) |
| Claim contradiction | Adding a claim that contradicts existing facts marks `contradicted_by` |
| Claim uniqueness | Duplicate claim content from same source is deduplicated |
| Serialization | `BeliefState` round-trips through serde JSON |
| Independent bubbles | Two NPCs' BeliefStates share no mutable state |
| Turn tracking | Facts record the turn number when learned |
