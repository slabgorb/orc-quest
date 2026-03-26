---
parent: context-epic-8.md
---

# Story 8-2: Turn Barrier — Wait for All Players Before Resolving, Configurable Timeout

## Business Context

In multiplayer, the game cannot resolve a turn until all players have submitted actions
(or timed out). Python's `turn_manager.py` implements barrier synchronization with a
configurable timeout. This story ports the barrier to Rust, using tokio primitives
instead of Python's asyncio events.

**Python source:** `sq-2/sidequest/game/turn_manager.py` (TurnBarrier, wait_for_all)
**Depends on:** Story 8-1 (MultiplayerSession)

## Technical Approach

The `TurnBarrier` collects actions from expected players and resolves when all have
submitted or the timeout fires:

```rust
pub struct TurnBarrier {
    expected: HashSet<PlayerId>,
    received: HashMap<PlayerId, PlayerAction>,
    timeout: Duration,
}

pub struct PlayerAction {
    pub player_id: PlayerId,
    pub input: String,
    pub submitted_at: Instant,
}

pub enum BarrierResult {
    AllSubmitted(HashMap<PlayerId, PlayerAction>),
    TimedOut {
        submitted: HashMap<PlayerId, PlayerAction>,
        missing: HashSet<PlayerId>,
    },
}

impl TurnBarrier {
    pub fn new(expected: HashSet<PlayerId>, timeout: Duration) -> Self {
        Self { expected, received: HashMap::new(), timeout }
    }

    pub fn submit(&mut self, action: PlayerAction) -> bool {
        self.received.insert(action.player_id.clone(), action);
        self.is_complete()
    }

    pub fn is_complete(&self) -> bool {
        self.expected.iter().all(|p| self.received.contains_key(p))
    }

    pub async fn wait(&mut self, mut rx: mpsc::Receiver<PlayerAction>) -> BarrierResult {
        let deadline = tokio::time::sleep(self.timeout);
        tokio::pin!(deadline);

        loop {
            tokio::select! {
                Some(action) = rx.recv() => {
                    if self.submit(action) {
                        return BarrierResult::AllSubmitted(std::mem::take(&mut self.received));
                    }
                }
                _ = &mut deadline => {
                    let missing = self.expected.difference(
                        &self.received.keys().cloned().collect()
                    ).cloned().collect();
                    return BarrierResult::TimedOut {
                        submitted: std::mem::take(&mut self.received),
                        missing,
                    };
                }
            }
        }
    }
}
```

Python uses `asyncio.wait_for` with a gathered set of futures. Rust's `tokio::select!`
is more explicit about the race between action receipt and timeout. The barrier is
reset-able for the next turn via `TurnBarrier::new()`.

Missing players on timeout receive a default "wait/observe" action injected by the
orchestrator, so the turn always resolves.

## Scope Boundaries

**In scope:**
- `TurnBarrier` struct with expected/received tracking
- `wait()` method using `tokio::select!` for action collection vs timeout
- `BarrierResult` enum distinguishing full vs partial submission
- Default action injection for timed-out players
- Configurable timeout duration

**Out of scope:**
- Adaptive timeout scaling (story 8-3)
- Turn mode switching (story 8-5)
- Idle player notifications (story 8-9)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| All submit | Barrier resolves with AllSubmitted when all players act |
| Timeout | Barrier resolves with TimedOut after deadline, listing missing players |
| Partial submit | Timed-out result includes submitted actions and missing set |
| Default action | Missing players get "wait/observe" injected into the turn |
| Reset | New barrier created per turn with current player set |
| Configurable | Timeout duration set at construction, not hardcoded |
