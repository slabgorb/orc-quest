---
parent: context-epic-9.md
---

# Story 9-4: Known Facts in Narrator Prompt — Character Perception Includes Accumulated Knowledge

## Business Context

A character who discovered the mayor is a cultist should react differently when meeting
the mayor again. By injecting known facts into the narrator prompt, Claude can reference
what the character knows and produce narration that reflects their accumulated knowledge.
Without this, the narrator treats every encounter as if the character has amnesia.

**Depends on:** Story 9-3 (KnownFact model)

## Technical Approach

Extend the prompt composer to include a `[CHARACTER KNOWLEDGE]` section:

```rust
impl PromptComposer {
    fn compose_knowledge_context(
        &self,
        character: &Character,
        scene_context: &SceneContext,
    ) -> String {
        let relevant = self.filter_relevant_facts(
            &character.known_facts,
            scene_context,
        );
        if relevant.is_empty() {
            return String::new();
        }

        let mut section = format!("[{}'s KNOWLEDGE]\n", character.name);
        for fact in &relevant {
            let confidence_tag = match fact.confidence {
                Confidence::Certain => "certain",
                Confidence::Suspected => "suspected",
                Confidence::Rumored => "rumored",
            };
            section.push_str(&format!(
                "- {} ({})\n", fact.content, confidence_tag
            ));
        }
        section
    }

    fn filter_relevant_facts(
        &self,
        facts: &[KnownFact],
        scene: &SceneContext,
    ) -> Vec<&KnownFact> {
        // Include all facts for now; future: filter by scene relevance
        // Cap at 20 most recent to avoid prompt bloat
        facts.iter().rev().take(20).collect()
    }
}
```

The confidence tag gives Claude a hint about how the character would reference the
knowledge. "Certain" facts are stated directly; "rumored" facts are hedged.

The section is appended to the narrator prompt alongside the existing character and
location context. A cap of 20 facts prevents prompt bloat for long-running sessions.

## Scope Boundaries

**In scope:**
- `compose_knowledge_context()` in PromptComposer
- `[CHARACTER KNOWLEDGE]` section in narrator prompt
- Confidence tags for narrator voice calibration
- Recency cap (20 facts) to bound prompt size
- Per-character knowledge (multiplayer: each character's own facts)

**Out of scope:**
- Scene-relevance filtering (keyword or embedding match — future optimization)
- Fact importance ranking
- Cross-character knowledge sharing
- Player-visible knowledge log (story 9-5 handles via narrative sheet)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Knowledge injected | Character's known facts appear in narrator prompt |
| Confidence tagged | Facts labeled certain/suspected/rumored |
| Recency capped | Maximum 20 facts included, most recent first |
| Empty omitted | Section omitted if character has no known facts |
| Per-character | Each character's knowledge is separate |
| Narrator behavior | Claude references known facts naturally in narration |
