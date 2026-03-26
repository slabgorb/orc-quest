---
parent: context-epic-6.md
---

# Story 6-2: Narrator MUST-Weave Instruction — Scene Directive Positioned in Prompt with Narrative Primacy, Enforced Weave Rules

## Business Context

A `SceneDirective` is useless if the narrator ignores it. This story positions the
directive in the narrator prompt with explicit MUST-weave language — the narrator is
instructed that these elements are not optional. In Python, this was ad-hoc string
formatting with inconsistent enforcement. The Rust version makes directive injection a
dedicated prompt section with narrative primacy (positioned before optional context).

**Depends on:** Story 6-1 (scene directive formatter)

## Technical Approach

The prompt composer gains a new section type that renders a `SceneDirective` into a
MUST-weave block:

```rust
impl PromptComposer {
    fn render_scene_directive(&self, directive: &SceneDirective) -> Option<String> {
        if directive.mandatory_elements.is_empty() {
            return None;
        }

        let mut block = String::from(
            "[SCENE DIRECTIVES — MANDATORY]\n\
             You MUST weave at least one of the following into your response.\n\
             These are not suggestions — they are active story elements.\n\n"
        );

        for (i, elem) in directive.mandatory_elements.iter().enumerate() {
            block.push_str(&format!(
                "{}. [{}] {}\n",
                i + 1,
                elem.source.label(),
                elem.content
            ));
        }

        if !directive.narrative_hints.is_empty() {
            block.push_str("\nNarrative hints (weave if natural):\n");
            for hint in &directive.narrative_hints {
                block.push_str(&format!("- {}\n", hint));
            }
        }

        Some(block)
    }
}
```

The directive block is inserted **before** optional context sections (NPC registry, quest
log) but **after** core state (location, party). This "narrative primacy" positioning
ensures the narrator sees it early in the prompt window.

## Scope Boundaries

**In scope:**
- `render_scene_directive()` in prompt composer
- Positioning logic (after core state, before optional context)
- MUST-weave language and formatting
- Tests verifying prompt structure with directives

**Out of scope:**
- Compliance scoring (verifying the narrator actually wove it — Epic 3 concern)
- Faction events in the block (story 6-5)
- Turn loop wiring (story 6-9)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Prompt section | Scene directive renders as `[SCENE DIRECTIVES — MANDATORY]` block |
| MUST-weave language | Block contains explicit "you MUST weave" instruction |
| Narrative primacy | Directive section appears before optional context in prompt |
| Element labeling | Each element shows its source (`[Trope Beat]`, `[Active Stake]`) |
| Empty suppression | No directive block when `mandatory_elements` is empty |
| Hints section | Narrative hints render as a separate "weave if natural" list |
