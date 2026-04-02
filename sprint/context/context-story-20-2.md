---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-2: scene_mood and scene_intent tool calls

## Business Context

First reactive tool migration. `scene_mood` and `scene_intent` are single-enum fields — the simplest possible tool calls. Proves the narrator can call tools during generation and `assemble_turn` can consume the results. After this, the narrator no longer emits these in its JSON block.

## Technical Guardrails

- Both tools take a single string argument and validate against an enum. `scene_mood`: combat, exploration, tension, triumph, sorrow, mystery, calm. `scene_intent`: Combat, Dialogue, Exploration, Examine, Chase.
- Tools should be lightweight scripts (or Rust binary subcommands) that validate the enum and return JSON `{"scene_mood": "tension"}`.
- The narrator system prompt replaces the `scene_mood`/`scene_intent` JSON schema docs with tool descriptions (one line each).
- `assemble_turn` merges tool call results into `ActionResult.scene_mood` and `ActionResult.scene_intent`.
- If the narrator doesn't call the tool (e.g., forgets), the field is `None` on `ActionResult` — this is the "fail loudly" signal. No fallback extraction from JSON.
- Key files: `narrator.rs` (prompt), `orchestrator.rs` (tool registration), `assemble_turn` (merge logic).

## Scope Boundaries

**In scope:**
- `set_mood` tool callable via `--allowedTools Bash`
- `set_intent` tool callable via `--allowedTools Bash`
- Remove `scene_mood` and `scene_intent` from narrator JSON schema docs
- `assemble_turn` consumes these tool results
- OTEL events for tool invocations

**Out of scope:**
- Other JSON fields (items, footnotes, etc.)
- Changing the mood/intent enum values

## AC Context

1. `set_mood` tool validates against the mood enum and returns structured JSON
2. `set_intent` tool validates against the intent enum and returns structured JSON
3. Narrator system prompt documents both tools instead of JSON field schemas
4. `assemble_turn` merges tool results into `ActionResult`
5. Missing tool calls result in `None` fields — no fallback extraction
6. OTEL spans for each tool invocation
