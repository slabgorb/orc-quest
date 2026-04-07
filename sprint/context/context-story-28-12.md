---
parent: context-epic-28.md
---

# Story 28-12: OTEL for Remaining Game Crate Internals

## Business Context

Story 28-2 added sidequest-telemetry to sidequest-game and instrumented
StructuredEncounter + CreatureCore. This story instruments the remaining
game crate blind spots found in the 2026-04-06 audit: trope engine, disposition,
turn phases, and multiplayer barrier. These are all Pattern 5 (LLM Compensation)
risk areas.

## Technical Approach

### TropeEngine::tick() — trope.rs

The tick math (progression delta, threshold comparison, beat selection) runs blind.
Server dispatch emits beat events AFTER the fact but the calculation is unobserved.

```
trope.tick: trope_id, progression_before, progression_after, delta
trope.threshold_crossed: trope_id, threshold, old_status, new_status
trope.beat_fired: trope_id, beat_id, trigger
```

File: `sidequest-game/src/trope.rs` — tick() method

### Disposition → Attitude derivation — disposition.rs

NPC attitude shifts happen silently. The narrator reacts to attitudes but the
GM panel can't verify the derivation.

```
disposition.attitude_derived: npc_name, disposition_value, old_attitude, new_attitude
```

File: `sidequest-game/src/disposition.rs` — attitude() method or wherever attitude is derived

### Turn phase transitions — turn.rs

TurnPhase (InputCollection → IntentRouting → AgentExecution → StatePatch → Broadcast)
transitions have no entry/exit events. When a turn takes 8s, can't tell which phase
consumed the time.

```
turn.phase_entered: phase, turn_number, player_id
turn.phase_exited: phase, duration_ms
```

File: `sidequest-game/src/turn.rs` — phase transition methods

### Multiplayer barrier — barrier.rs

When a player times out, the "hesitates" fallback fires with no OTEL event.

```
barrier.player_submitted: player_id, action_type
barrier.timeout: player_id, waited_ms
barrier.resolved: player_count, submitted_count, timed_out_count
```

File: `sidequest-game/src/barrier.rs` — resolution methods

## Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/trope.rs` | Add OTEL to tick(), threshold check, beat firing |
| `sidequest-game/src/disposition.rs` | Add OTEL to attitude derivation |
| `sidequest-game/src/turn.rs` | Add OTEL to phase transitions |
| `sidequest-game/src/barrier.rs` | Add OTEL to barrier resolution and timeouts |

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| Trope tick OTEL | tick() emits trope.tick event | `grep "trope.tick" trope.rs \| grep -v test` |
| Trope threshold OTEL | Threshold crossing emits trope.threshold_crossed | Grep verification |
| Disposition OTEL | Attitude derivation emits disposition.attitude_derived | Grep verification |
| Turn phase OTEL | Phase transitions emit turn.phase_entered/exited | Grep verification |
| Barrier OTEL | Barrier resolution emits barrier.resolved | Grep verification |
| Barrier timeout OTEL | Player timeout emits barrier.timeout | Grep verification |
| Wiring | All new WatcherEventBuilder calls are in non-test code | Grep -v test verification |
| Builds clean | `cargo build -p sidequest-game` succeeds | Build verification |

## Scope Boundaries

**In scope:** OTEL instrumentation for trope, disposition, turn, barrier
**Out of scope:** Lore, NPC behavior, character state (lower priority, future epic)
