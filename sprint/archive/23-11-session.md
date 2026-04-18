---
story_id: "23-11"
jira_key: null
epic: "23"
workflow: "tdd"
---

# Story 23-11: Rework tool sections — wrapper names, env vars, compact XML format

## Story Details

- **ID:** 23-11
- **Epic:** 23 — Narrator Prompt Architecture — Template, RAG, Universal Cartography
- **Jira Key:** None (personal project)
- **Workflow:** tdd
- **Points:** 5
- **Priority:** p1
- **Type:** refactor
- **Stack Parent:** none

## Story Context

Rework the tool sections in the narrator prompt system. The current hardcoded tool definitions need to be refactored to:
1. Use consistent wrapper names (bash scripts: sidequest-npc, sidequest-encounter, sidequest-loadout)
2. Inject environment variables per-session (SIDEQUEST_GENRE, SIDEQUEST_CONTENT_PATH)
3. Adopt compact XML format for tool definitions in the prompt

This is part of the broader Epic 23 effort to restructure the narrator system from a hardcoded monolith into a structured, attention-zone-aware template with tool wrappers and RAG-based retrieval.

Related stories:
- 23-1 (done): Wire reworked narrator prompt — replace hardcoded narrator.rs with template sections

## Repository

- **Repo:** sidequest-api
- **Branch:** `feat/23-11-rework-tool-sections` (will be created from develop)
- **Target Branch:** develop

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-03T12:58:22Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-03T11:21:09Z | 2026-04-03T11:22:13Z | 1m 4s |
| red | 2026-04-03T11:22:13Z | 2026-04-03T11:29:13Z | 7m |
| green | 2026-04-03T11:29:13Z | 2026-04-03T12:10:10Z | 40m 57s |
| spec-check | 2026-04-03T12:10:10Z | 2026-04-03T12:11:33Z | 1m 23s |
| verify | 2026-04-03T12:11:33Z | 2026-04-03T12:35:04Z | 23m 31s |
| review | 2026-04-03T12:35:04Z | 2026-04-03T12:57:40Z | 22m 36s |
| spec-reconcile | 2026-04-03T12:57:40Z | 2026-04-03T12:58:22Z | 42s |
| finish | 2026-04-03T12:58:22Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- No upstream findings during test verification.

### Reviewer (code review)
- **Improvement** (non-blocking): Unused `cfg` variable in `orchestrator.rs` for loop at L305. The compact XML format no longer references `cfg.binary_path`/`cfg.genre_packs_path`. Should be `_cfg` or `_` to suppress warning. Affects `crates/sidequest-agents/src/orchestrator.rs` (rename binding). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** Unused `cfg` variable in `orchestrator.rs` for loop at L305. The compact XML format no longer references `cfg.binary_path`/`cfg.genre_packs_path`. Should be `_cfg` or `_` to suppress warning. Affects `crates/sidequest-agents/src/orchestrator.rs`.

### Downstream Effects

- **`crates/sidequest-agents/src`** — 1 finding

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Architect (reconcile)
- No additional deviations found.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 11 ACs verified against implementation:
- AC 1-4: Compact XML format with wrapper names confirmed in orchestrator.rs diff — old Markdown tables and binary paths fully removed
- AC 5-6: Env vars flow through NarratorPromptResult.env_vars → send_with_tools_and_env → Command.env(). Full pipeline wired end-to-end.
- AC 7-8: "When to call" guidance, checklists, and NPC MANDATORY rule preserved in compact format
- AC 9: Token reduction test passes (≤800 chars vs ~2000+ old format)
- AC 10: preview-prompt.py updated to match compact XML format
- AC 11: OTEL spans unchanged, 15-27 tests confirm injection reporting works

**Note:** `SIDEQUEST_CONTENT_PATH` sourced from first tool's `genre_packs_path` via `.values().next()`. Acceptable — all tools share the same path from `Args.genre_packs_path()` in main.rs. Not a deviation; just documenting the assumption.

**Decision:** Proceed to verify

## Reviewer Assessment

**Verdict:** APPROVED
**Blocking Issues:** 0
**Non-blocking Findings:** 1

### Review Summary

4 files changed, 762 insertions, 148 deletions. Clean refactor of tool section format from verbose Markdown to compact XML, with env var wiring for genre/content path.

### Findings

1. **Unused `cfg` variable in for loop** (non-blocking, cosmetic) [EDGE]
   - File: `orchestrator.rs:305` — `for (tool_name, cfg) in &self.script_tools`
   - `cfg` is no longer referenced in match arms after format change. Generates compiler warning.
   - Fix: rename to `_cfg` or `_`
   - Severity: trivial — does not affect correctness

2. **[RULE] No rule violations found.** Checked rust lang-review checklist against changed files — no silent error swallowing, no missing `#[non_exhaustive]`, no hardcoded placeholders, no unsafe casts. Tool sections are static strings, not user input.

3. **[SILENT] No silent failure patterns found.** Env var injection uses explicit `cmd.env()` — no fallback if env var is missing. The `if let Some(cfg)` guard on `SIDEQUEST_CONTENT_PATH` correctly skips insertion when no tools are registered (not a silent fallback — it's correct behavior when genre is None).

### Verification

- **Wiring trace:** `build_narrator_prompt()` → `NarratorPromptResult.env_vars` → `process_action()` → `send_with_tools(&env_vars)` → `send_impl(extra_env)` → `cmd.env(key, value)` ✓
- **Tests:** 42/42 passing (27 new + 15 updated)
- **Clippy:** 0 new warnings in changed files
- **Backward compat:** `send_with_tools` signature change is internal — only caller is `process_action()`

**Decision:** Merge

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 failures, 0 new clippy warnings, 762+/148- | N/A |
| 2 | reviewer-rule-checker | Yes | clean | No rule violations in changed files | N/A |
| 3 | reviewer-edge-hunter | Yes | clean | 1 minor: unused cfg variable in for loop | Noted as non-blocking |
| 4 | reviewer-silent-failure-hunter | Yes | clean | No swallowed errors or silent fallbacks | N/A |

All received: Yes

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | 2 high (duplicated test helpers), 2 medium (extractable constants, env var abstraction) |
| simplify-quality | 3 findings | 2 high (dead code: extract_tool_text, send_with_tools), 1 medium (naming inconsistency) |
| simplify-efficiency | clean | No complexity issues |

**Applied:** 2 high-confidence fixes
- Removed dead `extract_tool_text()` helper from 23-11 tests
- Consolidated `send_with_tools_and_env()` into `send_with_tools()` (removed dead no-env variant)

**Flagged for Review:** 3 medium-confidence findings
- Duplicated test helpers across 15-27 and 23-11 test files (different genre_packs_path values)
- Tool section XML strings could be extracted to module-level constants
- Naming inconsistency: `orchestrator_with_script_tools()` vs `orchestrator_with_tools()`

**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: applied 2 fixes

**Quality Checks:** All 42 tests passing (27 story 23-11 + 15 story 15-27), full crate suite green
**Handoff:** To Reviewer for code review

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/orchestrator.rs` — Compact XML tool format, env_vars field on NarratorPromptResult, env var population in build_narrator_prompt()
- `crates/sidequest-agents/src/client.rs` — Added send_with_tools_and_env() method, extra_env parameter in send_impl()
- `crates/sidequest-agents/tests/script_tool_wiring_story_15_27_tests.rs` — Updated 8 assertions for new XML format/wrapper names/env vars
- `scripts/preview-prompt.py` — Updated to compact XML tool format (orchestrator repo)

**Tests:** 42/42 passing (27 story 23-11 + 15 story 15-27)
**Branch:** `feat/23-11-rework-tool-sections` (pushed to origin)

**AC Coverage:**
- AC-1: `<tool name="ENCOUNTER">` / `<tool name="NPC">` / `<tool name="LOADOUT">` XML format ✓
- AC-2: Wrapper names `sidequest-encounter`, `sidequest-npc`, `sidequest-loadout` ✓
- AC-3: No `--genre` or `--genre-packs-path` in prompt text ✓
- AC-4: No filesystem paths in prompt text ✓
- AC-5: `SIDEQUEST_GENRE` env var in NarratorPromptResult.env_vars ✓
- AC-6: `SIDEQUEST_CONTENT_PATH` env var in NarratorPromptResult.env_vars ✓
- AC-7: "When to call" and checklists preserved ✓
- AC-8: NPC MANDATORY rule preserved ✓
- AC-9: Tool section chars ≤800 (was ~2000+, now ~750) — >60% reduction ✓
- AC-10: preview-prompt.py updated ✓
- AC-11: OTEL tool injection already covered by 15-27 tests ✓

**Handoff:** To TEA for verify phase

## Tea Assessment

**Tests Required:** Yes
**Reason:** 5-point refactor with 11 ACs touching prompt format, env var wiring, and token budget

**Test Files:**
- `crates/sidequest-agents/tests/tool_rework_story_23_11_tests.rs` — 28 tests covering all 11 ACs

**Tests Written:** 28 tests covering 10 ACs (AC-10 is preview-prompt.py, not Rust-testable; AC-11 reused from 15-27)
**Status:** RED (compile error on `env_vars` field + assertion failures on format)

**Failure modes:**
- 6 tests fail to compile: `NarratorPromptResult` has no `env_vars` field yet — Dev must add `pub env_vars: HashMap<String, String>`
- 22 tests compile but fail: current code uses old Markdown format (`[ENCOUNTER GENERATOR]`, flag tables, `cfg.binary_path` paths, `--genre` flags)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #3 Hardcoded placeholder values | `prompt_has_no_filesystem_paths` | failing |
| #4 Tracing coverage | Covered by 15-27 OTEL tests (reused) | n/a |
| #6 Test quality | Self-check passed — all tests have meaningful assertions | pass |

**Rules checked:** 3 of 15 lang-review rules applicable (most rules target types/constructors/security — not relevant for a prompt format refactor)
**Self-check:** 0 vacuous tests found

**Implementation guidance for Dev (Yoda):**
1. Add `pub env_vars: HashMap<String, String>` to `NarratorPromptResult` (orchestrator.rs:92)
2. Rewrite 3 tool `format!()` blocks in orchestrator.rs L301-377 from Markdown → compact XML
3. Populate `env_vars` with `SIDEQUEST_GENRE` (from `context.genre`) and `SIDEQUEST_CONTENT_PATH` (from `ScriptToolConfig.genre_packs_path`) when genre is Some
4. Wire env vars through `process_action()` → `client.send_with_tools()` (client.rs needs env var support)
5. Update `narrator_allowed_tools()` to still use binary paths (unchanged)
6. Existing 15-27 tests will break on format checks — Dev should update them to match new XML format

**Handoff:** To Dev for implementation

## Sm Assessment

**Story:** 23-11 — Rework tool sections — wrapper names, env vars, compact XML format
**Phase:** finish → red (handoff to TEA)
**Workflow:** tdd (phased)

### Scope

5-point refactor touching the narrator prompt tool definitions in sidequest-api. Three deliverables:
1. Wrapper name consistency (sidequest-npc, sidequest-encounter, sidequest-loadout)
2. Per-session environment variable injection (SIDEQUEST_GENRE, SIDEQUEST_CONTENT_PATH)
3. Compact XML format for tool definitions in the prompt

### Routing

TDD workflow — TEA writes failing tests first (red phase), then Dev implements (green phase). This is a refactor of existing tool section generation, so TEA should focus on testing the new wrapper names, env var injection, and XML format output.

### Risks

- None identified. The narrator prompt system was recently reworked in 23-1, so the codebase is fresh and well-understood.