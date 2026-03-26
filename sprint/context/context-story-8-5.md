---
parent: context-epic-8.md
---

# Story 8-5: Turn Modes — FREE_PLAY, STRUCTURED, CINEMATIC

## Business Context

Not all game moments need the same coordination. Exploration is free-form, combat requires
simultaneous blind submission, and dramatic cutscenes are narrator-paced. Python's turn
manager switches between these modes based on game state transitions. This story implements
the turn mode state machine in Rust.

**Python source:** `sq-2/sidequest/game/turn_manager.py` (TurnMode, mode transitions)
**Depends on:** Story 8-2 (TurnBarrier)

## Technical Approach

Model turn modes as an enum with transition logic:

```rust
#[derive(Debug, Clone, PartialEq)]
pub enum TurnMode {
    FreePlay,
    Structured,
    Cinematic { prompt: Option<String> },
}

pub enum TurnModeTransition {
    CombatStarted,
    CombatEnded,
    CutsceneStarted { prompt: String },
    SceneEnded,
}

impl TurnMode {
    pub fn apply(self, transition: TurnModeTransition) -> TurnMode {
        match (self, transition) {
            (TurnMode::FreePlay, TurnModeTransition::CombatStarted) => TurnMode::Structured,
            (TurnMode::FreePlay, TurnModeTransition::CutsceneStarted { prompt }) =>
                TurnMode::Cinematic { prompt: Some(prompt) },
            (TurnMode::Structured, TurnModeTransition::CombatEnded) => TurnMode::FreePlay,
            (TurnMode::Cinematic { .. }, TurnModeTransition::SceneEnded) => TurnMode::FreePlay,
            (mode, _) => mode,  // no-op for invalid transitions
        }
    }
}
```

Each mode changes how the barrier and batching behave:

- **FreePlay:** Actions resolve immediately. No barrier. Solo-like experience for each player.
- **Structured:** Blind simultaneous. Barrier waits for all players. Actions hidden until resolution.
- **Cinematic:** Narrator sends a prompt, players respond. One-at-a-time or all-at-once
  depending on the prompt.

```rust
impl MultiplayerSession {
    pub fn should_use_barrier(&self) -> bool {
        matches!(self.turn_mode, TurnMode::Structured | TurnMode::Cinematic { .. })
    }
}
```

The orchestrator checks state transitions after each turn (combat started? ended?)
and applies the appropriate `TurnModeTransition` to update the session's mode.

## Scope Boundaries

**In scope:**
- `TurnMode` enum with FreePlay, Structured, Cinematic variants
- `TurnModeTransition` enum for valid state changes
- `apply()` pure function for mode transitions
- Barrier behavior per mode (use/skip)
- Mode broadcast to connected clients (TURN_MODE_CHANGED message)

**Out of scope:**
- Automatic detection of when to switch modes (orchestrator decides)
- Per-player mode overrides
- Custom mode definitions in genre packs

## Acceptance Criteria

| AC | Detail |
|----|--------|
| FreePlay default | New sessions start in FreePlay mode |
| Combat transition | CombatStarted switches FreePlay to Structured |
| Cutscene transition | CutsceneStarted switches FreePlay to Cinematic |
| Return to FreePlay | CombatEnded and SceneEnded return to FreePlay |
| Barrier gating | Structured and Cinematic use barrier; FreePlay does not |
| Client notification | Mode changes broadcast as TURN_MODE_CHANGED |
| Invalid no-op | Invalid transitions leave mode unchanged |
