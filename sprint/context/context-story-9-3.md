---
parent: context-epic-9.md
---

# Story 9-3: KnownFact Model — Play-Derived Knowledge Accumulation, Persistence

## Business Context

Characters learn things during play: "The mayor is secretly a cultist," "The old well
connects to tunnels." These facts accumulate in the character's knowledge base and feed
into narrator context so Claude can reference what the character knows. Unlike backstory,
KnownFacts are earned through gameplay and persist across sessions.

**Python source:** `sq-2/sprint/epic-62.yaml` (KnownFact model)
**Depends on:** Story 2-5 (orchestrator turn loop for post-turn extraction)

## Technical Approach

Model knowledge as typed facts with provenance:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnownFact {
    pub content: String,
    pub learned_turn: u64,
    pub source: FactSource,
    pub confidence: Confidence,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FactSource {
    Observation,  // character saw/sensed something
    Dialogue,     // told by an NPC or player
    Discovery,    // found via investigation or ability
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Confidence {
    Certain,    // confirmed by direct evidence
    Suspected,  // inferred but not confirmed
    Rumored,    // hearsay, may be wrong
}
```

Facts are extracted from narration by the world state agent as part of the post-turn
update (story 2-5). The world state agent already produces `WorldStatePatch`; this story
extends that patch to include discovered facts:

```rust
pub struct WorldStatePatch {
    // ... existing fields ...
    pub discovered_facts: Vec<DiscoveredFact>,
}

pub struct DiscoveredFact {
    pub character_id: CharacterId,
    pub fact: KnownFact,
}
```

The character model gains `known_facts: Vec<KnownFact>`. Facts accumulate monotonically
(no deletion or decay in this epic). Persistence is handled by the existing game state
serialization — facts are part of the character's serialized state.

## Scope Boundaries

**In scope:**
- `KnownFact` struct with content, turn, source, confidence
- `FactSource` and `Confidence` enums
- Extension of `WorldStatePatch` for discovered facts
- Character model integration (`known_facts: Vec<KnownFact>`)
- Serde serialization for persistence

**Out of scope:**
- Fact decay or forgetting
- Fact contradiction resolution
- Narrator prompt injection (story 9-4)
- Manual fact entry by players
- Fact sharing between characters

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Model defined | KnownFact with content, learned_turn, source, confidence |
| Source types | Observation, Dialogue, Discovery supported |
| Confidence levels | Certain, Suspected, Rumored supported |
| Patch extension | WorldStatePatch carries discovered facts |
| Character storage | Facts stored in character's known_facts vec |
| Persistence | Facts survive save/load cycle via serde |
| Accumulation | New facts append; existing facts not modified |
