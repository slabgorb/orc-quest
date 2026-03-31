---
parent: context-epic-18.md
workflow: tdd
---

# Story 18-1: Add Sub-Spans to Preprocess, Agent LLM, and System Tick

## Business Context

The OTEL flame chart shows three pipeline phases consuming most of the turn wall time
(preprocess ~7.2s, agent_llm ~7.9s, system_tick ~6.1s), but each is a single opaque
span. Without child spans, we can't identify which sub-operations are slow, which are
parallelizable, and where optimization effort should focus.

Additionally, `prompt_build` and `barrier` spans show 0ms despite wrapping real work —
they're either not instrumented or the spans don't capture the actual async operations.

## Technical Approach

### Sub-Spans to Add

**Inside `turn.preprocess` (dispatch/mod.rs:234-263):**
- `turn.preprocess.llm` — the `ClaudeClient::send_with_model()` call in `preprocessor.rs:31`
- `turn.preprocess.parse` — the `parse_response()` + validation in `preprocessor.rs:34-58`
- `turn.preprocess.wish_check` — the `WishConsequenceEngine::evaluate()` call at dispatch/mod.rs:247-261

**Inside `turn.agent_llm` (currently a single span around the Opus call):**
- `turn.agent_llm.prompt_build` — ContextBuilder zone assembly
- `turn.agent_llm.inference` — the actual Claude subprocess call
- `turn.agent_llm.extraction` — response parsing, patch extraction, intent classification

**Inside `turn.system_tick` (dispatch/mod.rs:485-514):**
- `turn.system_tick.combat` — `combat::process_combat_and_chase()` call
- `turn.system_tick.tropes` — `tropes::process_tropes()` call
- `turn.system_tick.beat_context` — trope beat context formatting for next turn

### Fix 0ms Spans

Verify that `turn.prompt_build` wraps the `build_prompt_context(ctx).await` call
(dispatch/mod.rs:222) and `turn.barrier` wraps `handle_barrier()` (dispatch/mod.rs:225).
If the spans exist but don't capture the async work (common with sync `enter()` on
async functions), switch to `instrument` or async-aware span guards.

### Parallelization (Stretch)

Once sub-spans confirm the time distribution, the parallelization opportunity is:
`build_prompt_context()` (async) and `preprocess_action()` (sync/blocking) are
independent — they could run concurrently via `tokio::join!` with `spawn_blocking`
for the sync preprocessor call.

## Scope Boundaries

**In scope:**
- Adding `tracing::info_span!` child spans inside the three target phases
- Fixing prompt_build and barrier span instrumentation
- Recording relevant field values on spans (durations, token counts, etc.)

**Out of scope:**
- Actually parallelizing operations (that's optimization work after we can measure)
- Changing the pipeline sequencing
- UI changes to the flame chart renderer (it auto-renders any spans it receives)

## Acceptance Criteria

1. **Sub-spans visible in flame chart** — preprocess, agent_llm, and system_tick each
   show 2+ child bars in the OTEL dashboard timeline view
2. **prompt_build shows real duration** — non-zero milliseconds reflecting actual
   prompt context assembly time
3. **barrier shows real duration** — non-zero for barrier turns, 0ms for FreePlay
   (correctly reflecting no-op)
4. **Existing tests pass** — no regressions from span instrumentation changes
5. **Fields recorded** — each sub-span records at least one diagnostic field
   (e.g., preprocess.llm records model name, system_tick.combat records in_combat bool)
