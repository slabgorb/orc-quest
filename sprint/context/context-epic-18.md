# Epic 18: OTEL Dashboard — Granular Instrumentation & State Tab

## Overview

Add sub-span instrumentation to the three dominant phases of the turn pipeline
(preprocess, agent_llm, system_tick) so the OTEL flame chart breaks down opaque
multi-second bars into their constituent operations. Fix the broken State tab
which never receives GameStateSnapshot events due to an event type naming mismatch.

**Priority:** p1
**Repos:** api, ui
**Stories:** 2 (5 pts total)

## Background

### Current Instrumentation Gap

The OTEL dashboard flame chart shows per-turn timing across 8 pipeline phases:
prompt_build, barrier, preprocess, agent_llm, state_update, system_tick, media, persist.

Three phases dominate wall time but are opaque — each is a single span with no
children, making it impossible to identify optimization targets or parallelization
opportunities:

| Phase | Typical Duration | What's Hidden Inside |
|-------|-----------------|---------------------|
| `preprocess` | ~7.2s | Haiku LLM call for STT cleanup + three-perspective rewrite |
| `agent_llm` | ~7.9s | Prompt assembly + Opus inference + response extraction |
| `system_tick` | ~6.1s | Combat processing + trope engine ticking |

### Parallelization Discovery

Analysis of `dispatch/mod.rs` revealed that `build_prompt_context()` and
`preprocess_action()` are **independent operations** currently running sequentially.
The prompt context assembles game state for the narrator; the preprocessor cleans
raw player input via Haiku. These could overlap via `tokio::join!`, potentially
saving the full duration of whichever is shorter.

Additionally, `prompt_build` and `barrier` show 0ms in the flame chart despite
wrapping real async work — they're either not instrumented or the spans don't
capture the actual operations.

### State Tab Wiring Bug

The State tab (`Dashboard/tabs/State/StateTab.tsx`) permanently shows
"Waiting for GameStateSnapshot event..." because:

- **API emits:** `WatcherEventType::GameStateSnapshot` (enum variant in `lib.rs:94`)
- **Dashboard listens for:** `event.event_type === "state_transition"` (`useDashboardSocket.ts:139`)

The serialized form of `GameStateSnapshot` is `game_state_snapshot` (serde default
snake_case), not `state_transition`. The dashboard filter never matches, so snapshots
are silently discarded. The emit code in `dispatch/mod.rs:1461-1469` correctly sends
the snapshot with turn_number and full game state — the data is there, the listener
just expects the wrong event type string.

### Key Reference Files

| File | LOC | Role |
|------|-----|------|
| `sidequest-server/src/dispatch/mod.rs` | ~1400 | Turn pipeline — all span definitions, phase sequencing |
| `sidequest-agents/src/preprocessor.rs` | 276 | Haiku LLM call for STT cleanup (preprocess phase) |
| `sidequest-server/src/dispatch/combat.rs` | — | Combat processing (inside system_tick) |
| `sidequest-server/src/dispatch/tropes.rs` | — | Trope engine ticking (inside system_tick) |
| `sidequest-server/src/lib.rs` | — | WatcherEventType enum definition |
| `sidequest-ui/src/components/Dashboard/hooks/useDashboardSocket.ts` | 263 | Event processing + snapshot extraction |
| `sidequest-ui/src/components/Dashboard/tabs/State/StateTab.tsx` | 109 | State tab UI |

## Technical Architecture

### Sub-Span Instrumentation (18-1)

Add child spans inside the three opaque phases. Target structure:

```
turn.preprocess
  turn.preprocess.llm          — Haiku subprocess call
  turn.preprocess.parse        — JSON response parsing
  turn.preprocess.wish_check   — WishConsequenceEngine evaluation

turn.agent_llm
  turn.agent_llm.prompt_build  — Context assembly (ContextBuilder zones)
  turn.agent_llm.inference     — Opus subprocess call
  turn.agent_llm.extraction    — Response parsing + patch extraction

turn.system_tick
  turn.system_tick.combat      — process_combat_and_chase()
  turn.system_tick.tropes      — process_tropes()
  turn.system_tick.beat_context — Trope beat context formatting
```

Also verify that the existing `turn.prompt_build` and `turn.barrier` spans
actually wrap their respective operations (`build_prompt_context` and
`handle_barrier`) — the 0ms readings suggest they don't.

### Parallelization Opportunity (18-1)

After sub-spans reveal the actual time distribution:

```rust
// Current (sequential):
let state_summary = prompt::build_prompt_context(ctx).await;
let barrier_combined = handle_barrier(ctx, &mut state_summary).await;
let preprocessed = preprocess_action(&effective_action, ctx.char_name);

// Target (parallel where possible):
let (state_summary, preprocessed) = tokio::join!(
    prompt::build_prompt_context(ctx),
    tokio::task::spawn_blocking(|| preprocess_action(&action, &char_name)),
);
let barrier_combined = handle_barrier(ctx, &mut state_summary).await;
```

Note: `preprocess_action` is synchronous (blocking subprocess call), so it needs
`spawn_blocking` to run concurrently with async prompt context assembly.

### State Tab Fix (18-2)

Two possible fixes (choose during implementation):

**Option A — Fix the dashboard listener (minimal change):**
```typescript
// useDashboardSocket.ts:139
// From:
if (event.event_type === "state_transition" && event.fields.snapshot) {
// To:
if (event.event_type === "game_state_snapshot" && event.fields.snapshot) {
```

**Option B — Fix the API enum serialization:**
Add `#[serde(rename = "state_transition")]` to the `GameStateSnapshot` variant.

Option A is preferred — it matches the actual enum name and avoids misleading
serde overrides. The dashboard should speak the API's language, not the other way.

### LoreStore Browser + Budget Visualization (18-4)

New `Lore` tab in the OTEL dashboard. Two parts:

**Part 1 — LoreStore browser:** Searchable table of all LoreFragments in the store.
Columns: id, category, source, content (truncated), token count, keywords.
Filterable by category (place, npc, event, faction, item, custom).

**Part 2 — Per-turn budget visualization:** Each turn shows which fragments were
selected for the prompt vs rejected (over budget). Emit a `lore_selection` watcher
event from `select_lore_for_prompt()` (lore.rs:354) with:
- `selected_fragments` — ids + token counts of fragments included
- `rejected_fragments` — ids + token counts of fragments that didn't fit
- `total_budget` — the token budget passed in
- `tokens_used` — actual tokens consumed
- `relevance_keyword` — the keyword used for prioritization

**API change:** Add new `WatcherEventType::LoreSelection` variant. Emit from
`select_lore_for_prompt()` or its caller in the prompt framework.

### Structured NPC Registry + Inventory Panels (18-5)

Sub-views within the State tab (once 18-2 fixes it). Instead of navigating a raw
JSON tree to find NPCs and items, render structured panels:

**NPC Registry table:**
- Columns: name, pronouns, role, location, last_seen_turn, disposition attitude
- Source: `GameSnapshot.npcs[]` (Npc structs) + NpcRegistryEntry data
- Sortable by last_seen_turn, filterable by location

**Inventory panel (per character):**
- Columns: item name, narrative_weight, evolution stage, description
- Gold total
- Source: `GameSnapshot.characters[].inventory`

**UI only** — no API changes needed. Data already flows through GameStateSnapshot.

### Prompt Inspector Tab (18-6)

New `Prompt` tab showing the exact prompt sent to Claude each turn.

**API change:** Emit a `prompt_assembled` watcher event from ContextBuilder
(prompt_framework/) after zone assembly. Fields:
- `full_prompt` — the complete assembled prompt text
- `zones` — array of `{ name, start_offset, end_offset, token_count }`
  (Primacy, Situational, Anchoring, Grounding)
- `total_tokens` — sum of all zones
- `turn_number` — for correlation

**UI:** New tab with:
- Syntax-highlighted prompt text with zone boundary markers (colored left border)
- Zone summary bar showing relative token allocation per zone
- Turn selector to compare prompts across turns
- Search within prompt text

Add new `WatcherEventType::PromptAssembled` variant.

### Parallelization (18-3)

After 18-1 confirms timing via sub-spans, `tokio::join!` the prompt context build
and the Haiku preprocess call. See epic context "Parallelization Opportunity" section.

## Story Dependency Graph

```
18-1 (sub-spans) ──→ 18-3 (parallelize)
18-2 (state tab) ──→ 18-5 (NPC/inventory panels)
18-4 (lore browser) ── standalone
18-6 (prompt inspector) ── standalone
```

18-1 and 18-2 are quick wins that unblock downstream stories.
18-4 and 18-6 are independent feature work.

## Acceptance Criteria Summary

| Story | Key ACs |
|-------|---------|
| 18-1 | Sub-spans visible in flame chart for preprocess, agent_llm, system_tick. prompt_build and barrier show non-zero durations. Existing tests pass. |
| 18-2 | State tab shows game state tree after first turn. Diff view shows state changes between turns. No "Waiting for GameStateSnapshot" message after turn completes. |
| 18-3 | Preprocess and prompt build overlap in flame chart. Total turn time reduced by min(preprocess, prompt_build) duration. |
| 18-4 | Lore tab shows all fragments with search/filter. Per-turn view shows selected vs rejected with token counts. |
| 18-5 | NPC table and inventory panel render within State tab. Sortable, filterable. |
| 18-6 | Prompt tab shows zone-labeled prompt with per-zone token counts. Turn selector for comparison. |

## Planning Documents

| Document | Path |
|----------|------|
| OTEL Principle | CLAUDE.md (OTEL Observability Principle section) |
| Epic YAML | sprint/epic-18.yaml |
| LoreStore | sidequest-game/src/lore.rs (2,746 LOC) |
| Prompt Framework | sidequest-agents/src/prompt_framework/ (1,484 LOC) |
| NPC Registry | sidequest-game/src/npc.rs (NpcRegistryEntry at line 499) |
