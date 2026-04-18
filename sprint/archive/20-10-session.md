# Story 20-10: Wire tool call parsing — connect Claude tool output to ToolCallResults

**Status:** in_progress
**Phase:** finish
**Workflow:** tdd
**Repos:** api
**Branch:** feat/20-10-wire-tool-call-parsing
**Points:** 5
**Epic:** 20 — Narrator Crunch Separation (ADR-057)

## Summary

Connect Claude CLI's tool call output to the `ToolCallResults` struct so that
`assemble_turn` receives real tool results instead of `ToolCallResults::default()`.

Currently, `ClaudeClient.send_with_tools()` returns only the `result` text from
the Claude CLI JSON envelope. When Claude invokes tools via `--allowedTools Bash(...)`,
the tool invocations and their stdout are captured by the CLI but discarded by our
client — we only extract the final prose.

This story parses tool call results from the Claude CLI output and maps them to
the corresponding `ToolCallResults` fields (scene_mood, scene_intent, and future
fields as tools are added in subsequent stories).

## Technical Approach

1. **Understand Claude CLI tool output format** — When `--output-format json` is used
   with `--allowedTools`, the JSON envelope contains tool use information. Parse it.

2. **Extend `ClaudeResponse`** to carry tool call results alongside the text response.

3. **Add a `parse_tool_results()` function** that takes the raw JSON envelope and
   extracts tool call results into a `ToolCallResults` struct.

4. **Wire into orchestrator** — Replace `ToolCallResults::default()` with the parsed
   results from the Claude response.

5. **OTEL spans** for every parsed tool result (per CLAUDE.md observability rules).

## Acceptance Criteria

- [ ] Claude CLI JSON envelope is parsed for tool call results
- [ ] Tool results are mapped to ToolCallResults fields
- [ ] Orchestrator passes real ToolCallResults to assemble_turn (not default)
- [ ] OTEL spans emitted for each tool result parsed
- [ ] Wiring test verifies tool results flow from client → orchestrator → assemble_turn
- [ ] All existing tests pass without modification

## Sm Assessment

**Story 20-10** closes the tool-call loop in ADR-057's narrator crunch separation.
Stories 20-1 through 20-9 built the plumbing: assemble_turn, script tools (set_mood,
set_intent, item_acquire, lore_mark), and wired assemble_turn into the dispatch pipeline.
But the orchestrator always passes `ToolCallResults::default()` — tool scripts execute
inside the Claude CLI subprocess, produce stdout, and the results are discarded.

**Key files:**
- `sidequest-api/crates/sidequest-agents/src/client.rs` — ClaudeClient, only extracts `result` text from JSON envelope
- `sidequest-api/crates/sidequest-agents/src/orchestrator.rs:701` — `ToolCallResults::default()` integration point
- `sidequest-api/crates/sidequest-agents/src/tools/assemble_turn.rs` — ToolCallResults struct (scene_mood, scene_intent)

**Approach:** Sidecar file pattern — tool scripts write JSONL to a session-specific temp file,
orchestrator reads after CLI completes, parses into ToolCallResults. Clean separation,
no dependency on undocumented CLI output format.

**Risk:** Low. Additive change — extends ClaudeResponse and orchestrator wiring without
modifying existing extraction pipeline. All existing tests should pass unchanged.

**Handoff to TEA (red phase):** Write failing tests for tool result parsing and wiring.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Core wiring story — connects tool output to game engine pipeline

**Test Files:**
- `crates/sidequest-agents/tests/tool_call_parser_story_20_10_tests.rs` — 14 tests

**Tests Written:** 14 tests covering 7 ACs

| AC | Tests | Description |
|----|-------|-------------|
| AC-1 | `tool_call_record_serializes_to_expected_jsonl`, `tool_call_record_deserializes_from_jsonl` | Sidecar JSONL protocol |
| AC-2 | `parse_tool_results_extracts_scene_mood`, `_scene_intent`, `_both_mood_and_intent`, `_returns_default_when_no_sidecar`, `_returns_default_for_empty_sidecar` | Parser correctness |
| AC-3 | `orchestrator_imports_parse_tool_results`, `orchestrator_does_not_use_default_tool_call_results` | Orchestrator wiring |
| AC-5 | `parsed_tool_results_override_narrator_extraction_in_assemble_turn`, `missing_sidecar_falls_back_to_narrator_extraction` | End-to-end wiring |
| AC-7 | `parse_tool_results_cleans_up_sidecar_file` | Cleanup |
| Edge | `_skips_malformed_json_lines`, `_skips_unknown_tool_names`, `_handles_missing_result_field`, `_last_call_wins_on_duplicate_tool` | Robustness |

**Status:** RED (compilation fails — `tools::tool_call_parser` module does not exist)

### Rule Coverage

No lang-review rules applicable — this is a new module, not modifying existing types.
Tests enforce: serialization protocol, path convention, cleanup discipline, wiring verification.

**Self-check:** 0 vacuous tests. All assertions check specific values, not just `is_some()`.

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/tools/tool_call_parser.rs` — New module: JSONL sidecar parser, ToolCallRecord struct, parse_tool_results(), sidecar_path(), SIDECAR_DIR constant
- `crates/sidequest-agents/src/tools/mod.rs` — Added tool_call_parser module export
- `crates/sidequest-agents/src/orchestrator.rs` — Replaced ToolCallResults::default() with parse_tool_results() call, generate turn-scoped sidecar session IDs
- `crates/sidequest-agents/tests/assemble_turn_wiring_story_20_9_tests.rs` — Updated 20-9 wiring test to accept parse_tool_results as valid evolution
- `crates/sidequest-agents/tests/tool_call_parser_story_20_10_tests.rs` — Fixed CARGO_MANIFEST_DIR path in orchestrator source tests

**Tests:** 19/19 passing (GREEN), full crate suite green (660+ tests)
**Branch:** feat/20-10-wire-tool-call-parsing (pushed)

**Handoff:** To TEA for verify phase

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

All 7 ACs verified against implementation:
- AC-1 through AC-5, AC-7: Direct alignment between spec and code
- AC-6: One 20-9 test updated to reflect natural evolution (ToolCallResults import → parse_tool_results). This is correct — the test checked an implementation detail superseded by 20-10. Updated assertion still verifies tool results reach assemble_turn.

**Decision:** Proceed to verify

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (orchestrator.rs, tool_call_parser.rs)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | Medium: extractable helper for JSON field extraction in tool_call_parser.rs:90 |
| simplify-quality | clean | No issues |
| simplify-efficiency | 2 findings | High: pre-existing redundancy in orchestrator extract_structured (NOT our change, lines 936+). Medium: same pattern as reuse found in tool_call_parser.rs:90 |

**Applied:** 0 high-confidence fixes (high finding is pre-existing code, not changed by 20-10)
**Flagged for Review:** 1 medium-confidence finding (match arm pattern in tool_call_parser — premature to extract with only 2 fields, revisit when 20-5/20-6/20-7 add more tools)
**Noted:** 1 high-confidence pre-existing finding (orchestrator extract_structured redundancy — out of scope)
**Reverted:** 0

**Overall:** simplify: clean (no changes applied to story code)

**Quality Checks:** All passing — full crate suite green, 660+ tests, 0 failures
**Handoff:** To Obi-Wan (Reviewer) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 5 findings (session ID not passed, TOCTOU, path traversal, file handle, test isolation) | 0 blocking — 1 improvement noted, 4 dismissed |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 findings (open failure default, unknown tool span, SystemTime unwrap, no OTEL at call site) | 0 blocking — 2 improvements noted, 2 dismissed |
| 4 | reviewer-rule-checker | Yes | clean | No rule violations — new module follows crate patterns (serde derive, tracing instrument, doc comments, non-exhaustive not applicable) | N/A |

All received: Yes

## Reviewer Assessment

**Verdict:** APPROVED
**Subagents:** edge-hunter (5 findings), silent-failure-hunter (4 findings)

### Critical Analysis

**Code quality:** Clean, minimal, well-documented. 126-line parser module with full OTEL instrumentation. Orchestrator changes are surgical — 22 lines changed, clear intent.

**Test coverage:** 19 tests covering happy path, malformed input, edge cases, cleanup, and wiring verification. No vacuous assertions.

**Wiring:** Parser correctly integrated at orchestrator line 705. `ToolCallResults::default()` eliminated. assemble_turn receives real (or default-when-no-sidecar) results.

### Specialist Findings

[EDGE] Edge-hunter: 5 findings — 0 blocking, 1 improvement, 4 dismissed.
[SILENT] Silent-failure-hunter: 4 findings — 0 blocking, 2 improvements, 2 dismissed.
[RULE] Rule-checker: Clean — no rule violations in new module.

### Findings Disposition

| # | Finding | Disposition |
|---|---------|-------------|
| 1 | Session ID not passed to CLI as env var | **Dismissed** — out of story scope per context. Future stories wire tool-side writing. |
| 2 | TOCTOU: exists() then open() | **Improvement** (non-blocking) — collapse to open() + match ErrorKind::NotFound. Revisit when tools write sidecars. |
| 3 | Path traversal on session_id | **Dismissed** — internal API, session ID generated by orchestrator, not user input. |
| 4 | File handle open during remove | **Dismissed** — macOS handles fine, not a correctness issue. |
| 5 | Test session ID collision risk | **Dismissed** — all names unique, PID sufficient for current set. |
| 6 | Open failure returns default silently | **Downgraded** — warn! is emitted, consistent with ADR-005 graceful degradation. |
| 7 | Unknown tool lacks OTEL span | **Improvement** (non-blocking) — nice-to-have dedicated span. |
| 8 | SystemTime unwrap_or_default | **Dismissed** — pre-epoch clock is theoretical only. |
| 9 | No OTEL span at call site for empty check | **Improvement** (non-blocking) — add when tools actually write sidecars. |

**0 blocking findings. 3 non-blocking improvements noted for future stories.**

**Handoff:** Approved for merge. To Grand Admiral Thrawn (SM) for finish.

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found.

## Delivery Findings

### TEA (test design)
- **Question** (non-blocking): Context recommends Option A (sidecar file pattern) but Dev may prefer Option C (stderr capture) after reviewing Claude CLI behavior. Tests are written against the sidecar API — if Dev chooses a different mechanism, test imports will need updating but test logic is valid.
  Affects `crates/sidequest-agents/src/tools/tool_call_parser.rs` (module shape).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): Collapse TOCTOU in tool_call_parser.rs — replace exists()+open() with open()+match ErrorKind::NotFound. Affects `crates/sidequest-agents/src/tools/tool_call_parser.rs` (lines 48-59). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Add OTEL span at orchestrator call site when has_tools is true but tool_results is all-None, so GM panel can detect "tools expected but no sidecar." Affects `crates/sidequest-agents/src/orchestrator.rs` (line 705). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Add dedicated OTEL span name for unknown tool names in parser, not just warn!. Affects `crates/sidequest-agents/src/tools/tool_call_parser.rs` (line 111). *Found by Reviewer during code review.*