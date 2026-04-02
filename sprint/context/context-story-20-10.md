---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-10: Wire tool call parsing — connect Claude tool output to ToolCallResults

## Business Context

**ADR-057** — Narrator Crunch Separation — replaces the narrator's monolithic JSON block
with discrete tool calls. Stories 20-1 through 20-9 built the infrastructure: assemble_turn,
script tools (set_mood, set_intent, item_acquire, lore_mark), and wired assemble_turn into
the dispatch pipeline.

**The gap:** Claude CLI invokes tools via `--allowedTools Bash(...)` and the tools execute
and produce stdout. But `ClaudeClient` currently extracts only the `result` (final prose)
from the JSON envelope and discards everything else. Tool call results never reach
`ToolCallResults` — the orchestrator always passes `ToolCallResults::default()`.

**This story closes the loop.** After 20-10, when Claude calls `set_mood "tension"` during
narration, the orchestrator captures that result and passes `ToolCallResults { scene_mood: Some("tension"), .. }` to `assemble_turn`.

## Technical Design

### Current State

**ClaudeClient (`client.rs`):**
- Lines 130–277: `send_impl()` runs `claude -p --output-format json --allowedTools ...`
- Line 225: Parses JSON envelope, extracts `result` field as text
- Lines 226–236: Extracts `usage.input_tokens` and `usage.output_tokens`
- **Does NOT extract tool call information from the envelope**

**Orchestrator (`orchestrator.rs`):**
- Line 701: `let mut base = assemble_turn(extraction, rewrite, flags, ToolCallResults::default());`
- Always passes default (empty) tool results

**ToolCallResults (`tools/assemble_turn.rs`):**
- Two fields: `scene_mood: Option<String>`, `scene_intent: Option<String>`
- Will grow as more tools land (20-5 scene_render, 20-6 quest_update, etc.)

### Claude CLI JSON Output Format

When `--output-format json` is used, Claude CLI returns:
```json
{
  "type": "result",
  "subtype": "success",
  "result": "The narrator's prose output...",
  "session_id": "...",
  "usage": { "input_tokens": N, "output_tokens": N },
  "total_cost_usd": 0.0N
}
```

When tools are invoked during the session, the tool invocations happen internally
within the CLI subprocess. The tools' stdout goes to the LLM as tool results.
The `result` field contains only the final text output.

**Key insight:** The tool calls happen as Bash subprocess invocations WITHIN the
Claude CLI session. The tool scripts (set_mood, set_intent, etc.) write their
results to stdout, which Claude CLI feeds back to the LLM. But the structured
JSON output from those scripts is NOT directly available in the envelope's `result` field.

**Approach:** Parse tool results from the Claude CLI's conversation log, OR have
the tool scripts write results to a sidecar file that the orchestrator reads after
the CLI subprocess completes.

### Implementation Options

**Option A — Sidecar file pattern:**
Tool scripts write JSON results to a temp file (e.g., `/tmp/sidequest-tools-{session}.jsonl`).
Each line is `{"tool": "set_mood", "result": {"mood": "tension"}}`.
After CLI completes, orchestrator reads and parses the sidecar file.
Pro: Simple, reliable, no CLI output parsing.
Con: Temp file management, cleanup.

**Option B — Parse tool output from CLI conversation log:**
Use `--output-format stream-json` or examine the verbose output for tool invocations.
Pro: No sidecar files.
Con: Depends on undocumented CLI output format.

**Option C — Tool scripts echo to stderr + capture:**
Tools write structured results to stderr (not stdout, which goes to LLM).
Orchestrator captures stderr from CLI subprocess and parses tool results.
Pro: No temp files, stderr is available.
Con: Mixing tool results with error output.

**Recommended: Option A (sidecar file).** Most reliable, cleanest separation of concerns.

### Target State

1. **Tool result sidecar:** Each tool script writes a JSON line to a session-specific
   sidecar file when invoked.

2. **ToolCallParser module:** New module in sidequest-agents that reads the sidecar file
   after CLI completes and produces a `ToolCallResults` struct.

3. **Orchestrator integration:** After `client.send_with_tools()` returns, call
   `parse_tool_results(session_id)` to get populated `ToolCallResults`. Pass to
   `assemble_turn()`.

4. **Cleanup:** Delete sidecar file after parsing.

## Acceptance Criteria

1. Tool scripts write structured results to a sidecar file during CLI execution
2. New `parse_tool_results()` function reads sidecar and produces `ToolCallResults`
3. Orchestrator passes real `ToolCallResults` (not default) to `assemble_turn`
4. OTEL spans emitted for each parsed tool result
5. Wiring test: tool result flows from script → sidecar → parser → orchestrator → assemble_turn
6. All existing tests pass unchanged
7. Sidecar file is cleaned up after parsing

## Scope Boundaries

**In scope:**
- Sidecar file protocol (JSONL format, path convention)
- ToolCallParser module
- Orchestrator wiring to use parsed results
- OTEL spans for tool result parsing
- Tests for parser and wiring

**Out of scope:**
- Adding new tool scripts (those are 20-5, 20-6, 20-7)
- Modifying existing tool scripts to write sidecar (unless set_mood/set_intent already exist)
- Removing extractor.rs (story 20-8)
- UI changes

## References

- **ADR-057:** Narrator Crunch Separation
- **Story 20-1:** assemble_turn infrastructure
- **Story 20-2:** set_mood / set_intent tools
- **Story 20-9:** Wire assemble_turn into dispatch pipeline
- **client.rs:** ClaudeClient subprocess wrapper
- **orchestrator.rs:** process_action() — line 701 is the integration point
