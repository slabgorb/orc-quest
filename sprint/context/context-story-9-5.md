---
parent: context-epic-9.md
---

# Story 9-5: Narrative Character Sheet — Genre-Voiced to_narrative_sheet() for Player Display

## Business Context

The character sheet should read like a passage from a novel, not a stat block. "Reva
Thornwhisper, root-bonded warden of the Flickering Reach" instead of "Name: Reva,
Class: Warden, HP: 24." The narrative sheet is the player-facing summary of who their
character is and what they know, rendered in genre voice.

**Python source:** `sq-2/sprint/epic-62.yaml` (narrative sheet generation)
**Depends on:** Story 9-1 (AbilityDefinition)

## Technical Approach

Implement `to_narrative_sheet()` on Character, composing genre-voiced sections:

```rust
impl Character {
    pub fn to_narrative_sheet(&self, genre_voice: &str) -> NarrativeSheet {
        NarrativeSheet {
            identity: self.compose_identity(genre_voice),
            abilities: self.compose_abilities(),
            knowledge: self.compose_knowledge(),
            status: self.compose_status(),
        }
    }

    fn compose_abilities(&self) -> Vec<AbilityEntry> {
        self.abilities.iter().map(|a| AbilityEntry {
            name: a.name.clone(),
            description: a.genre_description.clone(),
            involuntary: a.involuntary,
        }).collect()
    }

    fn compose_knowledge(&self) -> Vec<KnowledgeEntry> {
        self.known_facts.iter().map(|f| KnowledgeEntry {
            content: f.content.clone(),
            confidence: f.confidence.clone(),
        }).collect()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NarrativeSheet {
    pub identity: String,       // genre-voiced name + role + backstory summary
    pub abilities: Vec<AbilityEntry>,
    pub knowledge: Vec<KnowledgeEntry>,
    pub status: CharacterStatus, // HP, conditions in narrative voice
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AbilityEntry {
    pub name: String,
    pub description: String,   // genre_description, never mechanical_effect
    pub involuntary: bool,
}
```

The sheet is a structured type (not a rendered string) so the UI can format it. The
identity line is the one place where a Claude call might be warranted to produce a
genre-voiced summary, but for v1 it can be template-composed from character fields.

## Scope Boundaries

**In scope:**
- `NarrativeSheet` struct with identity, abilities, knowledge, status
- `to_narrative_sheet()` on Character
- Genre-voiced ability descriptions (never mechanical)
- Knowledge entries with confidence levels
- Serde serialization for protocol transmission

**Out of scope:**
- LLM-generated identity prose (template for v1, LLM enhancement later)
- Character portrait/image reference
- Edit capability (sheet is read-only display)
- Wire to React client (story 9-10)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Structured output | NarrativeSheet is a typed struct, not raw text |
| Genre voice | Abilities use genre_description, never mechanical_effect |
| Knowledge included | Known facts listed with confidence tags |
| Status included | Current HP and conditions in narrative form |
| Serializable | NarrativeSheet serializes to JSON for protocol |
| No stat blocks | No raw numbers exposed in player-facing fields |
