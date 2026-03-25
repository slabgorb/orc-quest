---
parent: context-epic-1.md
---

# Story 1-10: Agent Infrastructure — Agent Trait, ClaudeClient, JsonExtractor, ContextBuilder, Format Helpers

## Business Context

This is the plumbing that lets the game talk to Claude. The Agent trait defines the contract
all 8 agents implement. ClaudeClient wraps `tokio::process::Command` with timeout, error
handling, and output parsing — replacing three different subprocess patterns from Python with
one. JsonExtractor solves the "Claude returned prose around JSON" problem duplicated 4x in
Python. ContextBuilder assembles prompt sections from 1-9 into complete agent calls.

This story directly addresses three of the top technical debt items from the audit:
- Port lesson #2: JSON extraction duplicated 4+ times → single JsonExtractor
- Port lesson #3: Three different subprocess patterns → single ClaudeClient
- Port lesson #7: No agent trait → formal Agent trait
- Port lesson #8: Context building scattered → ContextBuilder

**Python sources:**
- `sq-2/sidequest/agents/claude_agent.py` — ClaudeAgent subprocess wrapper
- `sq-2/sidequest/agents/format_helpers.py` — shared formatting functions
- `sq-2/sidequest/agents/world_state.py` — JSON extraction (one of 4 copies)

## Technical Guardrails

- **Agent trait (port lesson #7):** `name()` and `system_prompt()` for identity. The async
  `execute()` and `build_context()` methods are deferred to story 1-11 where concrete
  implementations need them
- **ClaudeClient (port lesson #3):** Builder pattern, configurable timeout (default 120s),
  3 error variants (Timeout, SubprocessFailed, EmptyResponse), `#[non_exhaustive]` errors
- **JsonExtractor (port lesson #2):** 3-tier extraction:
  1. Direct parse: `serde_json::from_str(raw)`
  2. Fence strip: Extract from `` ```json ... ``` `` block
  3. Freeform search: Find first `{ ... }` block via bracket matching
- **ADR-013 (Lazy JSON Extraction):** Three-tier fallback, never panics, returns `None` on failure
- **ADR-012 (Agent Session Management):** Persistent Claude CLI sessions via `--session-id`
- **ContextBuilder (port lesson #8):** Composable sections using PromptSection from 1-9,
  zone-ordered assembly, category-based filtering, token estimation

### Format Helpers

| Function | Purpose |
|---|---|
| `character_block()` | Character summary for prompt context |
| `location_block()` | Current location description |
| `npc_block()` | NPC summary with disposition |
| `inventory_summary()` | Item list for prompt context |

## Scope Boundaries

**In scope:**
- `agent.rs`: Agent trait with `name()`, `system_prompt()`. AgentResponse struct
- `client.rs`: ClaudeClient with builder, configurable timeout, error types
- `extractor.rs`: JsonExtractor with 3-tier extraction
- `context_builder.rs`: ContextBuilder with zone-ordered composition, filtering, token estimate
- `format_helpers.rs`: character_block, location_block, npc_block, inventory_summary

**Out of scope:**
- Concrete agent implementations (story 1-11)
- Orchestrator state machine (story 1-11)
- GameService trait (story 1-11)
- Actual subprocess execution (ClaudeClient is config holder; wired up in 1-11)
- Prompt framework types (story 1-9, already built)

## AC Context

| AC | Detail |
|----|--------|
| Agent trait | `name()` returns display name, `system_prompt()` returns prompt text |
| ClaudeClient | Builder with timeout, command path. 3 error variants with context |
| JsonExtractor | Direct parse, fence extraction, freeform search. Returns `None` on failure |
| ContextBuilder | Zone-ordered build, category/zone filtering, token estimate |
| Format helpers | 4 functions producing prompt-ready text blocks |

## Assumptions

- `claude -p` CLI interface is stable and subprocess pattern works same in Rust as Python
- JsonExtractor handles all Claude response formats (pure JSON, fenced, embedded in prose)
- Agent trait is generic enough for all 8 agent types without ugly workarounds
