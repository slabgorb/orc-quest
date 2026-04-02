---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-1: assemble_turn infrastructure + action preprocessors

## Business Context

Foundation story for the crunch separation. Builds the `assemble_turn` assembler that will grow to replace `extractor.rs`, and moves the two easiest fields (`action_rewrite`, `action_flags`) out of the narrator's JSON output into preprocessors that run before narration. This is Phase 1 of ADR-057 — proving the architecture works with zero impact on game behavior.

## Technical Guardrails

- **`assemble_turn` must produce the same `ActionResult` struct** the server already consumes. No changes to `dispatch/mod.rs` in this story.
- `action_rewrite` and `action_flags` are already partially implemented as inline preprocessor fields on `ActionResult` (added in story 18-3). The narrator ALSO emits them in its JSON block. This story removes the narrator emission and makes the preprocessor the sole source.
- The preprocessor (`classify_action` / `rewrite_action`) runs BEFORE the narrator call. It does not need LLM judgment — it's mechanical text transformation.
- `assemble_turn` in this phase is a pass-through: it takes the existing JSON block from the narrator (for all other fields) and merges in the preprocessor results. It grows in subsequent stories.
- Key files: `orchestrator.rs` (prompt assembly, `ActionResult`), `narrator.rs` (remove `action_rewrite`/`action_flags` from system prompt), `extractor.rs` (still used for remaining JSON fields).

## Scope Boundaries

**In scope:**
- Build `assemble_turn` module/function that merges tool call results + narrator JSON into `ActionResult`
- Move `action_rewrite` generation to a preprocessor (runs before narrator call)
- Move `action_flags` classification to a preprocessor (runs before narrator call)
- Remove `action_rewrite` and `action_flags` schema documentation from narrator system prompt
- OTEL events for preprocessor execution

**Out of scope:**
- Migrating any other JSON fields (scene_mood, items, etc. — those are stories 20-2 through 20-7)
- Deleting `extractor.rs` (that's story 20-8)
- Changing the `ActionResult` struct shape

## AC Context

1. `assemble_turn` function exists and produces a valid `ActionResult` from narrator output + preprocessor results
2. `action_rewrite` is produced by a preprocessor before narration, not extracted from narrator JSON
3. `action_flags` is produced by a preprocessor before narration, not extracted from narrator JSON
4. Narrator system prompt no longer contains `action_rewrite` or `action_flags` schema documentation
5. OTEL events emitted for preprocessor execution (timing, field values)
6. All existing tests pass — game behavior unchanged
