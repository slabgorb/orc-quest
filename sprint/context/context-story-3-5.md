---
parent: context-epic-3.md
---

# Story 3-5: Subsystem Exercise Tracker — Agent Invocation Histogram, Coverage Gap Detection

## Business Context

During a playtest, SideQuest has 8 agent types that should each be invoked under the right
conditions. If a 20-turn combat encounter never triggers CreatureSmith, something is wrong
with intent routing. If Dialectician never fires during a dialogue-heavy session, the
conversation system isn't being reached. These bugs are invisible without instrumentation
— the game still "works," the narrator still talks, but the experience is flat because
specialized subsystems aren't contributing.

The Python engine has no equivalent. Debugging agent invocation in `sq-2` means grepping
server logs for `calling_agent=` lines and manually counting. This story replaces that
with structured, automatic tracking inside the validator task from story 3-2.

**Depends on:** Story 3-2 (TurnRecord pipeline — validator receives TurnRecords via `tokio::mpsc`)

## Technical Approach

### Histogram Tracking

The validator task (spawned in 3-2) already receives every `TurnRecord` over a
`tokio::mpsc::Receiver`. This story adds a `HashMap<String, usize>` that counts
invocations per agent type.

```rust
use std::collections::HashMap;

struct SubsystemTracker {
    counts: HashMap<String, usize>,
    turn_count: usize,
    summary_interval: usize,    // emit summary every N turns (default: 5)
    gap_threshold: usize,       // warn about zero-invocation agents after N turns (default: 10)
}

const EXPECTED_AGENTS: &[&str] = &[
    "narrator",
    "creature_smith",
    "ensemble",
    "troper",
    "world_builder",
    "dialectician",
    "resonator",
    "intent_router",
];

impl SubsystemTracker {
    fn new(summary_interval: usize, gap_threshold: usize) -> Self {
        let counts = EXPECTED_AGENTS.iter()
            .map(|&name| (name.to_string(), 0))
            .collect();
        Self { counts, turn_count: 0, summary_interval, gap_threshold }
    }

    fn record(&mut self, agent_name: &str) {
        *self.counts.entry(agent_name.to_string()).or_insert(0) += 1;
        self.turn_count += 1;
    }
}
```

### Periodic Summary Emission

Every `summary_interval` turns, emit a `tracing::info!` with the full histogram:

```rust
if self.turn_count % self.summary_interval == 0 {
    tracing::info!(
        component = "watcher",
        check = "subsystem_exercise",
        turn_count = self.turn_count,
        histogram = ?self.counts,
        "Agent invocation histogram"
    );
}
```

### Coverage Gap Detection

After `gap_threshold` turns, if any expected agent has zero invocations, emit a warning:

```rust
if self.turn_count >= self.gap_threshold {
    let gaps: Vec<&str> = EXPECTED_AGENTS.iter()
        .filter(|&&name| self.counts.get(name).copied().unwrap_or(0) == 0)
        .copied()
        .collect();

    if !gaps.is_empty() {
        tracing::warn!(
            component = "watcher",
            check = "subsystem_exercise",
            turn_count = self.turn_count,
            missing_agents = ?gaps,
            "Coverage gap: agents with zero invocations after {} turns",
            self.turn_count,
        );
    }
}
```

### Agent Invocation Patterns

Not all agents fire every turn. Understanding the expected patterns helps calibrate thresholds:

| Agent | Expected Pattern |
|-------|-----------------|
| `intent_router` | Every turn — classifies player intent |
| `narrator` | Every turn — produces narration text |
| `world_builder` | Post-turn — updates world state |
| `creature_smith` | Combat turns only — manages creatures |
| `ensemble` | NPC interaction turns — manages NPC behavior |
| `troper` | Periodic — evaluates narrative tropes |
| `dialectician` | Dialogue turns only — manages conversation |
| `resonator` | Periodic — evaluates emotional resonance |

The interesting signal is whether combat, dialogue, and chase agents are being reached
when the game scenario should invoke them. IntentRouter and Narrator having high counts
is expected and not a concern.

### Integration with Validator Task

The tracker lives inside the validator task's main loop:

```rust
async fn validator_task(mut rx: mpsc::Receiver<TurnRecord>) {
    let mut tracker = SubsystemTracker::new(5, 10);

    while let Some(record) = rx.recv().await {
        tracker.record(&record.agent_name);
        // ... existing validation logic from 3-2 ...
    }
}
```

### Configuration

Thresholds are struct fields, not environment variables. This is an internal diagnostic
tool — configuration happens at construction time:

```rust
// Default for playtesting
let tracker = SubsystemTracker::new(5, 10);

// Aggressive detection for short sessions
let tracker = SubsystemTracker::new(3, 5);
```

### Reset Behavior

The tracker resets when a new session starts. No persistence — this is ephemeral,
session-scoped data. If the validator task is restarted (new game session), a fresh
`SubsystemTracker` is created.

## Scope Boundaries

**In scope:**
- `SubsystemTracker` struct with `HashMap<String, usize>` histogram
- Recording agent invocations from each `TurnRecord`
- Periodic `tracing::info!` summary emission at configurable interval
- `tracing::warn!` for coverage gaps after configurable threshold
- Structured tracing fields: `component="watcher"`, `check="subsystem_exercise"`
- Reset on session start (new tracker instance per session)

**Out of scope:**
- Persistence of histograms across sessions
- Visualization or UI rendering (stories 3-7, 3-9)
- Per-session comparison or trending
- Streaming histogram data to the watcher WebSocket (story 3-6 handles transport)
- Alerting or automated remediation

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Histogram maintained | Each TurnRecord increments the correct agent_name counter |
| Expected agents pre-seeded | All 8 agent types present in histogram from turn 0 with count 0 |
| Periodic summary | `tracing::info!` emitted every N turns with full histogram (default N=5) |
| Coverage gap warning | `tracing::warn!` emitted when any expected agent has 0 invocations after threshold turns |
| Structured fields | All tracing events include `component="watcher"` and `check="subsystem_exercise"` |
| Configurable thresholds | Summary interval and gap threshold are struct fields, adjustable at construction |
| Session reset | New session creates a fresh tracker with all counts at zero |
| Unknown agents tracked | Agents not in EXPECTED_AGENTS are still counted (no warning, just tracked) |
