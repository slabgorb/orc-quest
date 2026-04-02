---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-5: scene_render tool — visual scene via tool call

## Business Context

`visual_scene` is the image generation trigger — subject, tier, mood, tags. The narrator currently writes prose AND formats a visual description suitable for image generation. The creative work is describing the scene; decomposing it into tier/mood/tags is mechanical. Entity introductions (NPC portraits, location landscapes) may already have `visual_prompt` from generator tools (ADR-056) — `scene_render` unifies the path.

## Technical Guardrails

- `scene_render` takes: subject description (free text from narrator, ≤100 chars), tier (portrait/landscape/scene_illustration), mood (from visual mood enum), tags (from tag enum).
- Returns `VisualScene` struct JSON.
- The narrator calls this when something visually significant happens. For entity introductions where a generator tool already produced a `visual_prompt`, the narrator can pass that through.
- Remove `visual_scene` JSON schema documentation (~100 tokens) from narrator system prompt.
- `assemble_turn` merges into `ActionResult.visual_scene`.
- Key consideration: the narrator's subject description is creative (LLM decides what to paint). The tool validates and structures it. Don't over-constrain the subject text.

## Scope Boundaries

**In scope:**
- `scene_render` tool with enum validation for tier/mood/tags
- Remove visual_scene JSON schema from narrator prompt
- `assemble_turn` integration
- OTEL events

**Out of scope:**
- Changing the `VisualScene` struct
- Image generation pipeline (daemon side)
- Generator tool visual_prompt integration (future enhancement)

## AC Context

1. `scene_render` tool accepts subject, tier, mood, tags and returns `VisualScene` JSON
2. Tier, mood, and tags validated against their enums
3. Subject text passed through as-is (narrator's creative judgment)
4. Narrator prompt documents the tool instead of the JSON field schema
5. `assemble_turn` merges into ActionResult
6. OTEL span with subject text and tier for GM panel visibility
