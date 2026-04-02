---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-9: Wire assemble_turn into dispatch pipeline

## Business Context

**ADR-057** — Narrator Crunch Separation — aims to eliminate the monolithic JSON extraction pipeline by replacing it with discrete tool calls. The `assemble_turn` function (story 20-1) collects tool results and merges them with narrator extraction to build the final ActionResult.

**The problem:** assemble_turn exists but is dead code. The orchestrator builds ActionResult directly from narrator extraction without calling assemble_turn. This means even when story 20-10 (tool call parsing) lands and starts populating ToolCallResults, those results won't reach the game unless dispatch calls assemble_turn.

**Story 20-9 is a no-op refactor:** Swap orchestrator's direct ActionResult construction for a call to assemble_turn(). With ToolCallResults::default(), the output is identical to current behavior — this story proves the wiring works and clears the path for 20-10.

## Technical Design

### Current State (as of story 20-1 completion)

File: `/sidequest-api/crates/sidequest-agents/src/orchestrator.rs`

**Lines 621–730:** process_action() method
1. Classifies intent (line 584)
2. Calls Claude CLI with allowed_tools (lines 615–619)
3. Extracts structured data from response (line 630):
   ```rust
   let extraction = extract_structured_from_response(raw_response);
   ```
4. Handles agent-specific extraction (combat patch, chase patch, strip JSON fence)
5. **Directly constructs ActionResult** (lines 704–730):
   ```rust
   ActionResult {
       narration,
       combat_patch,
       chase_patch,
       is_degraded: false,
       classified_intent: Some(intent_str),
       agent_name: Some(agent_str),
       footnotes: extraction.footnotes,
       items_gained: extraction.items_gained,
       // ... more fields from extraction
       action_rewrite: extraction.action_rewrite,
       action_flags: extraction.action_flags,
   }
   ```

File: `/sidequest-api/crates/sidequest-agents/src/tools/assemble_turn.rs`

**Exists but never called.** Contains:
- `ToolCallResults` struct (all fields Option, default to None)
- `assemble_turn()` function that takes:
  - `extraction: NarratorExtraction`
  - `rewrite: ActionRewrite`
  - `flags: ActionFlags`
  - `tool_results: ToolCallResults`
  - Returns: `ActionResult`

### Target State (After 20-9)

**orchestrator.rs:**
1. Import assemble_turn module
2. Build default ToolCallResults (all None)
3. Call assemble_turn() instead of building ActionResult directly
4. Return result to dispatch

**assemble_turn.rs:**
1. Public API — orchestrator depends on it
2. All override logic in place:
   - scene_mood: tool_results > extraction
   - scene_intent: tool_results > extraction
   - footnotes: tool_results (no fallback to extraction)
   - action_rewrite/action_flags: preprocessor always wins (currently None in 20-9)

### Backward Compatibility

**Complete backward compatibility.** ToolCallResults::default() (all None) means:
- scene_mood falls back to extraction.scene_mood (current behavior)
- scene_intent falls back to extraction.scene_intent (current behavior)
- footnotes becomes empty (breaking change, but tools don't fire yet, so no loss)
- action_rewrite/action_flags from extraction (current behavior)

**Footnotes edge case:** Story 20-1 AC-6 (no-fallback rule) means narrator footnotes are discarded when tool didn't fire. assemble_turn.rs already logs a warning. This is correct per spec — stories 20-2 (scene_mood/intent tools) and 20-4 (lore_mark) will populate footnotes via ToolCallResults.

## Implementation Plan

### Phase 1: Import & Call (TDD Red)

1. **Add public export** in `sidequest-agents/src/lib.rs`:
   ```rust
   pub use tools::assemble_turn::{assemble_turn, ToolCallResults};
   ```

2. **In orchestrator.rs process_action():**
   - After building `extraction` (line 630), add:
     ```rust
     let tool_results = ToolCallResults::default();
     let rewrite = extraction.action_rewrite.clone().unwrap_or_default();
     let flags = extraction.action_flags.clone().unwrap_or_default();
     ```
   - Replace lines 704–730 with:
     ```rust
     let action_result = assemble_turn(extraction, rewrite, flags, tool_results);
     ActionResult {
         narration,
         combat_patch,
         chase_patch,
         zone_breakdown: Some(prompt_zone_breakdown),
         agent_duration_ms: Some(agent_duration_ms),
         token_count_in: response.input_tokens.map(|v| v as usize),
         token_count_out: response.output_tokens.map(|v| v as usize),
         classified_intent: Some(intent_str),
         agent_name: Some(agent_str),
         is_degraded: false,
         ..action_result
     }
     ```

3. **Handle preprocessor defaults:**
   - ActionRewrite and ActionFlags currently have `Default` impls? Check assemble_turn.rs.
   - If not, derive them or make them explicit None handling.

### Phase 2: Tests (TDD Green)

1. **Existing test suite should pass unchanged.**
   - All `tests/assemble_turn_story_20_1_tests.rs` tests still pass (no changes needed).
   - All dispatch tests still pass (orchestrator.process_action behavior unchanged).

2. **Add a wiring test to assemble_turn tests:**
   ```rust
   #[test]
   fn test_assemble_turn_called_by_orchestrator() {
       // Verify that orchestrator imports assemble_turn and calls it
       // (can be a compile-time test or a mock integration)
   }
   ```

3. **Verify no-op behavior:**
   ```rust
   #[test]
   fn test_assemble_turn_with_default_tools_matches_extraction() {
       // Build extraction with known fields
       // Call assemble_turn with default ToolCallResults
       // Assert output matches what orchestrator used to build
   }
   ```

### Phase 3: Refactor (TDD Refactor)

1. **Simplify orchestrator.rs process_action().**
   - Lines 704–730 are gone, replaced by assemble_turn call.
   - Only agent-specific fields (combat_patch, chase_patch, narration cleanup) stay inline.

2. **Update CLAUDE.md** (sidequest-agents) to mark assemble_turn as "wired" not "in-progress."

3. **No changes to dispatch/mod.rs** — orchestrator is transparent, dispatch just calls process_action().

## Scope Boundaries

**In scope:**
- Import assemble_turn public API
- Call assemble_turn() in process_action()
- Preserve identical ActionResult output
- Tests verify no-op behavior

**Out of scope:**
- Changing ActionResult struct
- Implementing preprocessor logic (action_rewrite/action_flags extraction from separate phase)
- Tool call result population (story 20-10)
- Removing extractor.rs (story 20-8)

## Acceptance Criteria

1. assemble_turn is a public API exported from sidequest-agents crate
2. orchestrator.rs imports and calls assemble_turn()
3. ActionResult fields are identical pre- vs. post-refactor (verified by tests)
4. All existing tests pass without modification
5. assemble_turn has a wiring test verifying it's called by production code (not just unit tests)
6. No regressions in game behavior (playtest or quick sanity smoke test)

## Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Footnotes discarded (tools not wired) | Low — no tool yet, no loss | Document in 20-4 context. OTEL log in assemble_turn already warns. |
| Breaking change to footnotes semantics | Medium if stories 9-4/9-11 depend on narrator footnotes | Verify 9-4/9-11 status in sprint. Current tools don't produce footnotes, so safe. |
| Missed integration point | High — tool results never reach game | Add wiring test. Verify dispatch→orchestrator→assemble_turn is reachable from GameService trait. |

## Testing Strategy

### Unit Tests
- Existing `assemble_turn_story_20_1_tests.rs` — no changes needed (tests the function itself).
- Add one test in orchestrator tests to verify process_action calls assemble_turn.

### Integration Tests
- Existing dispatch tests should pass unchanged (orchestrator behavior identical with default ToolCallResults).
- Add a trace test to verify dispatch→orchestrator→assemble_turn is wired:
  ```
  dispatch_player_action()
    → app_state.orchestrator.process_action()
    → orchestrator.process_action()
    → assemble_turn()
  ```

### Regression Test
- Quick playtest with a single action (examine something, get narration + extracted fields).
- Verify footnotes field is populated (or empty if no tool fires — should be empty in 20-9).

## References

- **ADR-057:** Narrator Crunch Separation — `/docs/adr/adr-057.md`
- **Story 20-1:** assemble_turn infrastructure + action preprocessors (AC-1: assemble_turn produces ActionResult)
- **Story 20-2:** scene_mood and scene_intent tool calls (populates ToolCallResults.scene_mood/intent)
- **Story 20-4:** lore_mark tool (populates ToolCallResults.footnotes)
- **Story 20-8:** Delete extractor.rs (removes narrator JSON block from prompt)
- **Story 20-10:** Wire tool call parsing (populates ToolCallResults from Claude response)

## Prompt Changes Needed

No narrator system prompt changes (tools still use existing prompt from 20-2/20-4 when they land).

## Database/State Changes

None.
