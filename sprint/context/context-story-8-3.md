---
parent: context-epic-8.md
---

# Story 8-3: Adaptive Action Batching — Collection Window Scales by Player Count

## Business Context

A fixed timeout punishes small groups (waiting too long) or rushes large groups (not enough
time). Python's turn manager scales the collection window: 3 seconds for 2-3 players,
5 seconds for 4+. This story adds that scaling logic to the Rust TurnBarrier.

**Python source:** `sq-2/sidequest/game/turn_manager.py` (adaptive_timeout)
**Depends on:** Story 8-2 (TurnBarrier)

## Technical Approach

Extract batching configuration into a dedicated struct that computes timeout from player count:

```rust
pub struct BatchingConfig {
    pub solo_timeout: Option<Duration>,   // None = immediate
    pub small_group_timeout: Duration,    // 2-3 players
    pub large_group_timeout: Duration,    // 4+ players
    pub small_group_max: usize,           // threshold (default 3)
}

impl Default for BatchingConfig {
    fn default() -> Self {
        Self {
            solo_timeout: None,
            small_group_timeout: Duration::from_secs(3),
            large_group_timeout: Duration::from_secs(5),
            small_group_max: 3,
        }
    }
}

impl BatchingConfig {
    pub fn timeout_for(&self, player_count: usize) -> Option<Duration> {
        match player_count {
            0 | 1 => self.solo_timeout,
            n if n <= self.small_group_max => Some(self.small_group_timeout),
            _ => Some(self.large_group_timeout),
        }
    }
}
```

The `MultiplayerSession` uses `BatchingConfig` when constructing each turn's barrier:

```rust
let timeout = self.batching_config
    .timeout_for(self.players.len())
    .unwrap_or(Duration::from_secs(3));
let barrier = TurnBarrier::new(player_ids, timeout);
```

Solo play (1 player) bypasses the barrier entirely, preserving the single-player experience.

## Scope Boundaries

**In scope:**
- `BatchingConfig` with configurable thresholds and durations
- `timeout_for()` computing appropriate window from player count
- Integration with TurnBarrier construction
- Solo bypass (no barrier for single player)

**Out of scope:**
- Dynamic adjustment mid-turn based on submission speed
- Per-player timeout history or adaptive learning
- Network latency compensation

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Solo bypass | Single player gets no barrier wait |
| Small group | 2-3 players get 3-second window (default) |
| Large group | 4+ players get 5-second window (default) |
| Configurable | Thresholds and durations adjustable via BatchingConfig |
| Integration | MultiplayerSession uses config when creating barriers |
| Default impl | BatchingConfig::default() provides sensible values |
