---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-4: lore_mark tool — footnote extraction via tool call

## Business Context

Footnotes are the narrator's knowledge discovery mechanism — `[1]` markers in prose with structured metadata (summary, category, is_new). The narrator's creative job is deciding what's notable and placing the marker. Structuring it as `{marker, summary, category, is_new}` is mechanical. The tool handles the formatting; the LLM handles the judgment.

## Technical Guardrails

- `lore_mark` takes: marker number, summary text, category (Lore/Place/Person/Quest/Ability), is_new boolean.
- Returns valid `Footnote` struct JSON.
- The narrator still places `[N]` markers in its prose — this is creative judgment. It calls `lore_mark` for each marker to register the structured metadata.
- `lore_established` field (story 15-7) also feeds through this tool — lore fragments are a superset of footnotes.
- Remove footnote protocol documentation (~150 tokens) from narrator system prompt. Replace with tool description.
- `assemble_turn` collects all `lore_mark` calls into `ActionResult.footnotes` and optionally `ActionResult.lore_established`.

## Scope Boundaries

**In scope:**
- `lore_mark` tool
- Remove footnote JSON schema from narrator prompt
- `assemble_turn` collects footnote tool calls
- OTEL events per footnote

**Out of scope:**
- Changing footnote categories or the `Footnote` struct
- LoreStore integration (already wired)
- RAG pipeline changes

## AC Context

1. `lore_mark` tool accepts marker, summary, category, is_new and returns `Footnote` JSON
2. Narrator places `[N]` in prose and calls `lore_mark` for each
3. Narrator prompt contains tool description instead of footnote JSON schema
4. `assemble_turn` collects all `lore_mark` results into `ActionResult.footnotes`
5. Footnotes not registered via tool don't appear in ActionResult
6. OTEL span per lore_mark invocation
