---
parent: context-epic-18.md
workflow: tdd
---

# Story 18-3: Parallelize Prompt Context Build and Preprocess Haiku Call

## Business Context

After 18-1 adds sub-spans confirming the time distribution, this story overlaps
two independent operations that currently run sequentially: `build_prompt_context()`
(async game state assembly) and `preprocess_action()` (sync Haiku LLM call for
STT cleanup). The preprocess call takes ~7.2s — any work done in parallel with it
is essentially free.

## Technical Approach

### Current Sequential Flow (dispatch/mod.rs)

```rust
let state_summary = prompt::build_prompt_context(ctx).await;  // async
let barrier_combined = handle_barrier(ctx, &mut state_summary).await;  // needs state_summary
let preprocessed = preprocess_action(&effective_action, ctx.char_name);  // sync, ~7.2s
```

### Target Parallel Flow

```rust
// Clone what preprocess needs — it only uses action string + char name
let action_owned = effective_action.to_string();
let char_name_owned = ctx.char_name.to_string();

let (state_summary, preprocessed) = tokio::join!(
    prompt::build_prompt_context(ctx),
    tokio::task::spawn_blocking(move || {
        preprocess_action(&action_owned, &char_name_owned)
    }),
);
let preprocessed = preprocessed.expect("preprocess task panicked");

// barrier still needs state_summary, runs after
let barrier_combined = handle_barrier(ctx, &mut state_summary).await;
```

### Key Constraints

- `preprocess_action` is synchronous (blocking subprocess call) — must use
  `spawn_blocking` to avoid blocking the tokio runtime
- `build_prompt_context` borrows from `ctx` — may need to restructure borrows
  or clone necessary fields before the join
- `handle_barrier` mutates `state_summary` — must run after prompt build, but
  can overlap with preprocess since it doesn't depend on preprocessed output
- The Wish Consequence Engine reads `preprocessed.is_power_grab` — must follow preprocess

## Scope Boundaries

**In scope:**
- Restructuring the dispatch pipeline to run prompt build and preprocess concurrently
- Using `spawn_blocking` for the sync preprocess call
- Verifying via flame chart that the operations actually overlap

**Out of scope:**
- Parallelizing other pipeline phases
- Changing preprocess to async (would require async ClaudeClient)
- Performance benchmarking beyond visual flame chart confirmation

## Acceptance Criteria

1. **Operations overlap in flame chart** — preprocess and prompt_build bars overlap
   temporally in the OTEL timeline view
2. **Turn wall time reduced** — total turn time decreases by approximately
   min(preprocess_duration, prompt_build_duration)
3. **Correctness preserved** — barrier still receives completed state_summary,
   Wish Consequence Engine still receives preprocessed output
4. **Existing tests pass** — no regressions
5. **spawn_blocking used** — preprocess runs on blocking thread pool, not the
   async executor
