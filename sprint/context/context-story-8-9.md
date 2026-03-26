---
parent: context-epic-8.md
---

# Story 8-9: Turn Reminders — Notify Idle Players After Configurable Timeout

## Business Context

In STRUCTURED mode, one idle player blocks the entire group. Python sends a reminder
notification after a configurable idle timeout (default: 60% of the barrier timeout).
This nudges slow players without being aggressive. The reminder is a game message, not
a system intrusion.

**Python source:** `sq-2/sidequest/game/turn_reminder.py`
**Depends on:** Story 8-2 (TurnBarrier)

## Technical Approach

A reminder timer runs alongside the barrier, firing at a configurable fraction of the
barrier timeout:

```rust
pub struct ReminderConfig {
    pub threshold: f64,  // fraction of barrier timeout (default 0.6)
    pub message: String, // genre-overridable reminder text
}

impl Default for ReminderConfig {
    fn default() -> Self {
        Self {
            threshold: 0.6,
            message: "The party awaits your decision...".to_string(),
        }
    }
}

pub async fn run_reminder(
    barrier_timeout: Duration,
    config: &ReminderConfig,
    expected: &HashSet<PlayerId>,
    received: &Arc<RwLock<HashSet<PlayerId>>>,
    session: &MultiplayerSession,
) {
    let reminder_delay = barrier_timeout.mul_f64(config.threshold);
    tokio::time::sleep(reminder_delay).await;

    let submitted = received.read().await;
    let idle: Vec<_> = expected.iter()
        .filter(|p| !submitted.contains(*p))
        .collect();

    for player_id in idle {
        session.send_to(player_id, &GameMessage::TurnReminder {
            text: config.message.clone(),
        }).await;
    }
}
```

The reminder task is spawned alongside the barrier wait and cancelled when the barrier
resolves (via a `CancellationToken` or by dropping the task handle). In FreePlay mode,
no reminders are sent since there is no barrier.

## Scope Boundaries

**In scope:**
- `ReminderConfig` with threshold fraction and message text
- Reminder task spawned alongside barrier
- Targeted notification to idle players only
- Cancellation when barrier resolves early
- No reminders in FreePlay mode

**Out of scope:**
- Escalating reminders (multiple nudges)
- Auto-kick for persistent idleness
- Player-configurable reminder preferences
- Sound/notification integration on client side

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Reminder fires | Idle players notified at 60% of barrier timeout |
| Only idle | Players who already submitted do not receive reminders |
| Cancelled on resolve | Reminder task cancelled if barrier completes before threshold |
| FreePlay skip | No reminders sent in FreePlay mode |
| Configurable | Threshold and message text adjustable via ReminderConfig |
| Genre voice | Reminder message overridable per genre pack |
