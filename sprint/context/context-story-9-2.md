---
parent: context-epic-9.md
---

# Story 9-2: Ability Perception in Narrator Prompt — Involuntary Abilities Trigger in Context

## Business Context

If a character has root-bonding (involuntary: detect corruption), the narrator should
know about it and can trigger it when appropriate — "As you enter the grove, Reva feels
a deep wrongness radiating from the oldest tree." The player does not ask for this; the
narrator includes it because the ability is in the prompt context. This makes abilities
feel alive rather than menu items to click.

**Python source:** `sq-2/sprint/epic-62.yaml` (ability perception in narrator)
**Depends on:** Story 9-1 (AbilityDefinition model)

## Technical Approach

Extend the prompt composer (from story 2-5) to inject involuntary abilities into the
narrator's system prompt:

```rust
impl PromptComposer {
    fn compose_ability_context(&self, characters: &[Character]) -> String {
        let mut section = String::from("[CHARACTER ABILITIES]\n");
        for character in characters {
            let involuntary: Vec<_> = character.abilities.iter()
                .filter(|a| a.involuntary)
                .collect();
            if !involuntary.is_empty() {
                section.push_str(&format!("{}:\n", character.name));
                for ability in involuntary {
                    section.push_str(&format!(
                        "  - {} (involuntary): {}\n",
                        ability.name, ability.genre_description
                    ));
                }
            }
        }
        section
    }
}
```

The `[CHARACTER ABILITIES]` section is appended to the narrator system prompt. Only
involuntary abilities appear here — voluntary abilities are the player's to invoke. The
narrator is instructed to weave these naturally into narration when contextually appropriate,
not to force them every turn.

The prompt includes a brief instruction:

```
These characters have involuntary abilities that may trigger based on circumstances.
Weave them naturally when relevant. Do not force triggers every turn.
```

## Scope Boundaries

**In scope:**
- `compose_ability_context()` in PromptComposer
- Filter to involuntary abilities only
- `[CHARACTER ABILITIES]` section in narrator prompt
- Instruction text for Claude on natural triggering
- Multi-character support (multiplayer-ready)

**Out of scope:**
- Voluntary ability activation by player command
- Ability cooldowns or usage tracking
- Mechanical effect resolution (combat system)
- Ability acquisition during play

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Involuntary injection | Involuntary abilities appear in narrator prompt |
| Voluntary excluded | Non-involuntary abilities omitted from narrator context |
| Genre voice | Abilities described using genre_description, not mechanical_effect |
| Natural triggering | Prompt instructs Claude to trigger naturally, not forcefully |
| Multi-character | All party members' involuntary abilities included |
| No prompt when empty | Section omitted if no characters have involuntary abilities |
