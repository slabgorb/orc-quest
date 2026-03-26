---
parent: context-epic-3.md
---

# Story 3-2: TurnRecord Struct + mpsc Channel — Async Pipeline from Orchestrator to Validator

## Business Context

Story 3-1 instruments the turn loop with tracing spans — structured log lines that describe each
decision. But tracing spans are ephemeral: they flow through the subscriber and disappear. The
Game Watcher needs a durable, typed snapshot of each turn so the validator can inspect it
asynchronously. That's the TurnRecord.

The TurnRecord captures everything about a single turn: what the player said, how intent was
classified, which agent responded, what patches were applied, and what the game state looked like
before and after. It flows from the hot path (orchestrator) to the cold path (validator) through
a bounded `tokio::sync::mpsc` channel so the orchestrator never blocks waiting for validation.

This is the contract between "things that happened" and "things we want to check." Stories 3-3
through 3-5 consume TurnRecords to run specific validation checks. This story defines the struct
and wires the channel.

**Python reference:** Python has no equivalent. The orchestrator mutates state in place and logs
strings. Reconstructing "what happened on turn 17" requires parsing log files. TurnRecord makes
each turn a first-class data structure.

**ADR:** ADR-031 (Game Watcher — Semantic Telemetry), hot-path/cold-path contract
**Depends on:** Story 3-1 (agent telemetry spans)

## Technical Approach

### TurnRecord Struct

Defined in `sidequest-agents` crate alongside the orchestrator that produces it:

```rust
use chrono::{DateTime, Utc};
use sidequest_game::{GameSnapshot, StateDelta, PatchSummary};
use crate::orchestrator::Intent;

#[derive(Debug, Clone)]
pub struct TurnRecord {
    pub turn_id: u64,
    pub timestamp: DateTime<Utc>,
    pub player_input: String,
    pub classified_intent: Intent,
    pub agent_name: String,
    pub narration: String,
    pub patches_applied: Vec<PatchSummary>,
    pub snapshot_before: GameSnapshot,
    pub snapshot_after: GameSnapshot,
    pub delta: StateDelta,
    pub beats_fired: Vec<(String, f32)>,
    pub extraction_tier: u8,
    pub token_count_in: usize,
    pub token_count_out: usize,
    pub agent_duration_ms: u64,
    pub is_degraded: bool,
}
```

Every field comes from data already computed during `process_turn()`. The TurnRecord doesn't
require new computation — it assembles existing values into a single struct.

### Where TurnRecord Assembly Happens

Inside `process_turn()`, after step 9 (compute_delta) and before the return:

```rust
impl Orchestrator {
    pub async fn process_turn(
        &mut self,
        input: &str,
        player_id: &PlayerId,
    ) -> Result<TurnResult, OrchestrationError> {
        // Steps 1-6: sanitize, route, compose, build context, call agent, extract patches
        // ...

        // Step 7: snapshot before, apply patches
        let snapshot_before = self.state.snapshot();
        self.apply_patches(&patches)?;

        // Step 8: post-turn update (world state agent, trope tick, save)
        let beats_fired = self.post_turn_update(&clean_input, &narration).await?;

        // Step 9: snapshot after, compute delta
        let snapshot_after = self.state.snapshot();
        let delta = compute_delta(&snapshot_before, &snapshot_after);

        // Step 9.5: assemble and send TurnRecord (non-blocking)
        let record = TurnRecord {
            turn_id: self.next_turn_id(),
            timestamp: Utc::now(),
            player_input: clean_input.clone(),
            classified_intent: route.intent.clone(),
            agent_name: route.agent.to_string(),
            narration: narration.clone(),
            patches_applied: patches.summary(),
            snapshot_before,
            snapshot_after: self.state.snapshot(),
            delta: delta.clone().unwrap_or_default(),
            beats_fired,
            extraction_tier,
            token_count_in,
            token_count_out,
            agent_duration_ms,
            is_degraded: false,
        };

        if let Err(e) = self.watcher_tx.try_send(record) {
            tracing::warn!(
                error = %e,
                "watcher channel full or closed — dropping TurnRecord for turn {}",
                record.turn_id
            );
        }

        // Step 10: return TurnResult (unchanged from story 2-5)
        Ok(TurnResult { narration, narration_chunks: vec![], state_delta: delta, .. })
    }
}
```

The critical line is `try_send`, not `send().await`. The orchestrator must never block on the
validator. If the channel is full (validator fell behind), we log a warning and drop the record.
Gameplay continues unaffected.

### Channel Wiring

The bounded mpsc channel is created at startup and threaded through:

```rust
use tokio::sync::mpsc;

// In server startup (main.rs or app state construction):
let (watcher_tx, watcher_rx) = mpsc::channel::<TurnRecord>(32);

// Orchestrator gets the sender
let orchestrator = Orchestrator::new(
    game_service,
    intent_router,
    watcher_tx,
    // ...
);

// Validator task gets the receiver
tokio::spawn(async move {
    run_validator(watcher_rx).await;
});
```

Buffer size 32 means up to 32 turns can queue before backpressure kicks in. At typical play pace
(one turn every 10-30 seconds), this is minutes of buffer. If the validator can't keep up with
32 queued turns, something is seriously wrong and dropping records is the correct response.

### Validator Task (Stub)

For this story, the validator simply logs receipt. Actual validation checks come in stories
3-3 through 3-5:

```rust
async fn run_validator(mut rx: mpsc::Receiver<TurnRecord>) {
    tracing::info!("watcher validator started, awaiting TurnRecords");

    while let Some(record) = rx.recv().await {
        tracing::info!(
            turn_id = record.turn_id,
            intent = %record.classified_intent,
            agent = %record.agent_name,
            patches = record.patches_applied.len(),
            delta_empty = record.delta.is_empty(),
            extraction_tier = record.extraction_tier,
            is_degraded = record.is_degraded,
            "received TurnRecord"
        );
    }

    tracing::info!("watcher validator shutting down (channel closed)");
}
```

The validator runs as a detached `tokio::spawn` task. When the server shuts down and the
orchestrator is dropped, `watcher_tx` drops, the channel closes, `rx.recv()` returns `None`,
and the validator exits cleanly.

### Memory Considerations

Each TurnRecord clones two `GameSnapshot`s — the before and after state. GameSnapshot contains
character lists, NPC registries, quest logs, and location data. For a typical session:

- GameSnapshot: ~2-8 KB serialized (varies with NPC count, quest complexity)
- Two snapshots per turn: ~4-16 KB
- 32-slot channel buffer worst case: ~128-512 KB

This is fine for a single-player game engine. If snapshot sizes grow (e.g., large NPC registries),
two mitigations are available:

1. **Arc wrapping:** `snapshot_before: Arc<GameSnapshot>` shares the immutable snapshot with the
   TurnResult consumer. The orchestrator takes a snapshot once; both the TurnResult and the
   TurnRecord reference the same allocation.

2. **Lazy delta:** Store only `snapshot_before` and `delta`, reconstruct `snapshot_after` on
   demand. Trades memory for CPU in the validator.

Neither is needed now — premature optimization. But the field types can change from
`GameSnapshot` to `Arc<GameSnapshot>` without breaking the validator interface.

### Crate Placement

TurnRecord lives in `sidequest-agents` alongside the Orchestrator that produces it. Rationale:

- The Orchestrator is the only producer
- TurnRecord's fields reference types from `sidequest-game` (GameSnapshot, StateDelta, Intent)
  which `sidequest-agents` already depends on
- Creating a `sidequest-watcher` crate would be premature — it would have one struct and no logic
- When stories 3-3 through 3-5 add validation logic, if the validator grows complex enough to
  warrant its own crate, TurnRecord moves then

### Rust Concept: try_send vs send

`mpsc::Sender::send()` is async — it waits for buffer space if the channel is full. This is
correct when the sender can afford to wait (e.g., a producer feeding a processing pipeline).
`try_send()` is synchronous — it returns `Err(TrySendError)` immediately if the channel is full
or closed. This is correct on the hot path where blocking is unacceptable. The pattern mirrors
Python's `queue.put_nowait()` vs `await queue.put()`, but Rust makes the distinction at the
type level: `try_send` doesn't need `.await`.

## Scope Boundaries

**In scope:**
- `TurnRecord` struct definition with all fields from ADR-031
- `tokio::sync::mpsc::channel(32)` creation at server startup
- `Orchestrator` holds `mpsc::Sender<TurnRecord>`
- TurnRecord assembly in `process_turn()` after delta computation
- `try_send` with warning on channel full (never block hot path)
- Validator stub task that logs receipt via tracing
- `turn_id` counter on Orchestrator (simple `u64` increment)
- Clean shutdown (channel close propagates to validator)

**Out of scope:**
- Patch legality validation (story 3-3)
- Entity reference validation (story 3-4)
- Subsystem exercise tracking (story 3-5)
- Watcher WebSocket endpoint (story 3-6)
- TurnRecord persistence / replay (deferred per epic-3 scope)
- Arc-wrapped snapshots (optimization, not needed yet)
- Separate sidequest-watcher crate (extract later if validator grows)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| TurnRecord defined | Struct with all 15 fields from ADR-031 in sidequest-agents crate |
| Channel created | `mpsc::channel::<TurnRecord>(32)` wired at server startup |
| Orchestrator sends | `process_turn()` assembles TurnRecord after delta computation and sends via `try_send` |
| Non-blocking send | `try_send` used, not `send().await` — hot path never waits on validator |
| Backpressure logged | Channel-full condition logs a warning with the dropped turn_id |
| Validator receives | Background task receives TurnRecords and logs structured summary |
| Clean shutdown | Dropping orchestrator closes channel; validator task exits gracefully |
| Turn ID increments | Each TurnRecord has a unique, monotonically increasing turn_id |
| Tests with mock | Unit test sends mock TurnRecords through channel, validator receives them |
| Snapshots included | TurnRecord contains snapshot_before and snapshot_after from the turn |
