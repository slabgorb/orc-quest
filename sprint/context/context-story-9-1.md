---
parent: context-epic-9.md
---

# Story 9-1: AbilityDefinition Model — Genre-Voiced Ability Descriptions with Mechanical Effects

## Business Context

Players should understand their abilities through narrative, not stat blocks. "+2 Nature
check" becomes "Your bond with ancient roots lets you sense corruption in living things."
The Python codebase stores both, displaying the narrative version to the player while the
mechanical version feeds game logic. This story creates the Rust model.

**Python source:** `sq-2/sprint/epic-62.yaml` (ability model definition)
**Depends on:** Story 2-3 (character creation)

## Technical Approach

Define `AbilityDefinition` as a first-class model on the character:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AbilityDefinition {
    pub name: String,
    pub genre_description: String,
    pub mechanical_effect: String,
    pub involuntary: bool,
    pub source: AbilitySource,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AbilitySource {
    Race,
    Class,
    Item,
    Play,  // acquired during gameplay
}

impl AbilityDefinition {
    pub fn display(&self) -> &str {
        &self.genre_description
    }

    pub fn is_involuntary(&self) -> bool {
        self.involuntary
    }
}
```

Genre packs define abilities with both voices:

```yaml
# genre_packs/flickering_reach/abilities.yaml
- name: Root-Bonding
  genre_description: "Your bond with ancient roots lets you sense corruption in living things within thirty paces."
  mechanical_effect: "+2 Nature, detect corruption 30ft"
  involuntary: true
  source: Race
```

The character model gains `abilities: Vec<AbilityDefinition>`, populated during character
creation from the genre pack's ability pool. The `involuntary` flag marks abilities that
trigger without player action (used by story 9-2 for narrator context).

## Scope Boundaries

**In scope:**
- `AbilityDefinition` struct with genre/mechanical dual representation
- `AbilitySource` enum (Race, Class, Item, Play)
- Serde serialization for persistence and protocol
- Genre pack YAML loading of ability definitions
- Integration into character model as `Vec<AbilityDefinition>`

**Out of scope:**
- Ability progression/leveling (future work)
- Ability activation mechanics (combat system handles)
- Narrator prompt injection (story 9-2)
- Ability UI rendering (story 9-10 via narrative sheet)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Dual voice | Each ability has genre_description and mechanical_effect |
| Genre display | `display()` returns genre-voiced text, not mechanics |
| Involuntary flag | Abilities marked involuntary for narrator context injection |
| Source tracking | Ability source (Race/Class/Item/Play) recorded |
| YAML loading | Abilities loaded from genre pack YAML |
| Serialization | AbilityDefinition round-trips through serde JSON |
| Character integration | Character model holds `Vec<AbilityDefinition>` |
