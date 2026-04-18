# Epic 20: Narrator Crunch Separation — Tool-Based Mechanical Extraction (ADR-057)

## Overview

Replace the narrator's monolithic JSON output block with discrete tool calls during narration, assembled into `ActionResult` by a post-narration script. The narrator produces only prose; all mechanical extraction (items, quests, mood, visual scene, footnotes, resource deltas, etc.) moves to typed tool calls. Eliminates the 3-tier extraction pipeline (`extractor.rs`) and ~1,580 tokens of JSON schema documentation from the narrator system prompt.

**Priority:** p1
**Repo:** sidequest-api (crates: sidequest-agents, sidequest-server)
**Stories:** 8 (30 points)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **ADR-057** (`docs/adr/057-narrator-crunch-separation.md`) | Entire document — the architectural decision driving this epic |
| **ADR-056** (`docs/adr/056-script-tool-generators.md`) | Script tool pattern, `--allowedTools Bash` mechanism, generator catalog |
| **ADR-001** (`docs/adr/001-claude-cli-only.md`) | Constraint: CLI subprocess model, no SDK — tools via `--allowedTools Bash` |
| **ADR-031** (`docs/adr/031-game-watcher-semantic-telemetry.md`) | OTEL event patterns for GM panel visibility |

## Background

### The Problem

The narrator currently performs three jobs simultaneously: creative narration, intent interpretation, and structured JSON emission. The JSON block (~12 fields) consumes 63% of the narrator system prompt as schema documentation and forces the LLM to serialize structured data alongside prose — a dual-task penalty that produces malformed JSON, missing fields, and hallucinated values.

The server runs a 3-tier extraction pipeline (`extractor.rs`: direct parse → markdown fence → freeform regex search) to recover structured data from the narrator's output. This is fragile, expensive to maintain, and invisible to OTEL — there's no way to know if the narrator actually engaged a subsystem or just improvised.

### The Principle

> **Narration → LLM. Intent → LLM. Crunch → Scripts.**

"Crunch" includes mechanical state mutations, structured data formatting (meta-crunch), lookups against game state, and format-sensitive extraction. If the LLM's job is just formatting data that already exists in game state, it should be a script tool call.

### The Architecture

**Two-phase turn model:**

1. **During narration:** The LLM calls tools as it generates prose. When it decides to introduce an NPC, it calls `namegen`. When a player acquires an item, it calls `item_acquire`. Each tool returns JSON the LLM can reference in its prose.

2. **After narration:** `assemble_turn` collects all tool call results from the turn plus the prose output and assembles them into the `ActionResult` struct. The server never parses narrator prose for structured data.

### What This Eliminates

- The fenced JSON block in narrator output
- `extractor.rs` and the 3-tier extraction pipeline
- ~1,580 tokens of JSON schema docs in the narrator system prompt
- Silent LLM compensation (if a tool doesn't fire, the mechanical action didn't happen)

## Technical Architecture

### Key Files (Existing — Will Be Modified)

| File | LOC | Role in Migration |
|------|-----|-------------------|
| `crates/sidequest-agents/src/agents/narrator.rs` | 168 | System prompt shrinks from ~2,500 to ~600 tokens as fields migrate to tools |
| `crates/sidequest-agents/src/orchestrator.rs` | 1,151 | Prompt assembly (tool sections replace JSON schema sections), `ActionResult` struct evolves |
| `crates/sidequest-agents/src/extractor.rs` | 146 | Deleted in Phase 8 — replaced by `assemble_turn` |
| `crates/sidequest-agents/src/client.rs` | 317 | `--allowedTools` list grows with each phase |
| `crates/sidequest-server/src/dispatch/mod.rs` | ~1,900 | Consumes `ActionResult` — no changes needed until Phase 8 (dispatch reads same struct) |
| `crates/sidequest-server/src/dispatch/prompt.rs` | ~500 | Prompt builder — removes JSON schema injection as fields migrate |

### Key Files (New — Will Be Created)

| File | Purpose |
|------|---------|
| `crates/sidequest-agents/src/tools/assemble_turn.rs` | Post-narration assembler: collects tool call log + prose → `ActionResult` |
| `crates/sidequest-agents/src/tools/mod.rs` | Tool module root |
| Individual tool binaries or functions | `set_mood`, `set_intent`, `item_acquire`, `lore_mark`, `scene_render`, `quest_update`, etc. |

### ActionResult Struct (Current — 20 fields)

Fields migrating to tool calls (in phase order):

| Phase | Fields | Tool Replacement |
|-------|--------|-----------------|
| 1 | `action_rewrite`, `action_flags` | Preprocessors (run before narration) |
| 2 | `scene_mood`, `scene_intent` | `set_mood`, `set_intent` (single enum arg) |
| 3 | `items_gained`, `merchant_transactions` | `item_acquire`, `merchant_transact` |
| 4 | `footnotes`, `lore_established` | `lore_mark` |
| 5 | `visual_scene` | `scene_render` |
| 6 | `quest_updates` | `quest_update` |
| 7 | `personality_events`, `resource_deltas`, `sfx_triggers` | `personality_event`, `resource_change`, `play_sfx` |
| 8 | (none — structural) | `assemble_turn` becomes sole `ActionResult` producer |

Fields that stay on `ActionResult` unchanged: `narration`, `combat_patch`, `chase_patch`, `is_degraded`, `classified_intent`, `agent_name`, `agent_duration_ms`, `token_count_in`, `token_count_out`, `zone_breakdown`.

### Tool Call Mechanism

All tools use the existing `--allowedTools Bash(binary:*)` mechanism from ADR-056. Claude calls tools during generation, interleaved with prose. Tool call results are captured in the Claude CLI's structured output and parsed by `assemble_turn`.

### OTEL Coverage

Each tool call is a discrete subprocess invocation visible in OTEL spans. The GM panel shows exactly which tools fired, with what arguments, and what they returned. This replaces the current model where "did the narrator engage the inventory system?" requires parsing a potentially malformed JSON block.

## Cross-Epic Dependencies

**Depends on:**
- Epic 15 (Wiring Debt) — story 15-27 "Wire script tool invocation" provides the `--allowedTools` infrastructure this epic builds on
- ADR-056 (Script Tool Generators) — established the tool pattern with `sidequest-namegen`

**Depended on by:**
- Epic 16 (Genre Mechanics) — resource pools and confrontation types will benefit from tool-based extraction
- Any future epic touching narrator output or extraction pipeline
