---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-8: Eliminate narrator JSON block — delete extractor.rs

## Business Context

The capstone. After stories 20-1 through 20-7, every field that was in the narrator's fenced JSON block is now produced by either a preprocessor or a reactive tool call. The JSON block in the narrator's output, the schema documentation in the system prompt, and the 3-tier extraction pipeline in `extractor.rs` are all dead code. This story removes them.

## Technical Guardrails

- **Prerequisite:** ALL of stories 20-1 through 20-7 must be complete and verified in playtesting before this story starts. This is the point of no return for the extraction pipeline.
- Remove the entire `[JSON BLOCK]` section from `NARRATOR_SYSTEM_PROMPT` in `narrator.rs` (~700 tokens of schema docs, ~200 tokens of example JSON).
- Remove the JSON extraction call from `orchestrator.rs` — `assemble_turn` is now the sole producer of `ActionResult`.
- Delete `extractor.rs` (146 LOC) and remove `JsonExtractor` from the crate's public API.
- `ActionResult.extraction_tier` field becomes permanently `None` (or remove it — it only existed to report which extraction tier succeeded).
- Verify narrator output is pure prose — no fenced code blocks expected.
- Run full playtest to confirm no regressions.

## Scope Boundaries

**In scope:**
- Remove JSON block instructions from narrator system prompt
- Remove JSON extraction call from orchestrator
- Delete `extractor.rs`
- Remove or deprecate `extraction_tier` field on ActionResult
- Full regression test suite

**Out of scope:**
- Changing any tool behavior (tools are already working from prior stories)
- `assemble_turn` changes (already complete from prior stories)

## AC Context

1. `narrator.rs` system prompt contains no JSON schema documentation — only identity, pacing, agency, constraint handling, and tool descriptions
2. `extractor.rs` deleted from the crate
3. `JsonExtractor` no longer in crate public API
4. `orchestrator.rs` does not call any JSON extraction function — `assemble_turn` produces `ActionResult`
5. `extraction_tier` removed or permanently None on ActionResult
6. All existing tests pass
7. Playtest confirms narration quality and mechanical accuracy maintained
