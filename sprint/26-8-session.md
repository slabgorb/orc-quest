---
story_id: "26-8"
jira_key: "none"
epic: "26"
workflow: "trivial"
---

# Story 26-8: Add OTEL watcher events for location transitions

## Story Details

- **ID:** 26-8
- **Jira Key:** none (personal project)
- **Epic:** 26 — Wiring Audit Remediation — Unwired Modules, Protocol Gaps, OTEL Blind Spots
- **Workflow:** trivial (phased: setup → implement → review → finish)
- **Points:** 2
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** trivial
**Phase:** setup
**Phase Started:** 2026-04-06T17:29:16Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-06T17:29:16Z | - | - |

## Delivery Findings

No upstream findings.

## Design Deviations

None yet.

## Implementation Notes

### Observability Blind Spot

Location transitions are a core game mechanic but have zero OTEL visibility. The GM panel cannot verify whether location changes are actually being processed or whether they're silently failing.

**Current State:**
- Location transitions handled in sidequest-game (character movement, location updates)
- No watcher events emitted during transitions
- GM panel has no visibility into transition state or failures
- Violates observability principle: "If a subsystem isn't emitting OTEL spans, you can't tell whether it's engaged or whether Claude is just improvising"

### Implementation Strategy

1. **Identify transition points** in `sidequest-game` where location changes occur:
   - Character movement actions
   - Teleport/warp mechanics
   - Environmental transitions (entering buildings, leaving areas)
   - Location state changes in game_state

2. **Add OTEL watcher events** for each transition:
   - Event: `LocationTransition` (or similar naming)
   - Fields: old_location, new_location, reason/action_type, character_id
   - Emitted via tracing infrastructure (matches existing WatcherEvent pattern)

3. **Verify wiring** to GM panel dashboard:
   - Ensure events flow through dispatcher to UI watcher view
   - Confirm events appear in OTEL trace spans
   - Test with actual game movement

### Key Files

- `sidequest-game/src/` — location/character state management
- `sidequest-protocol/src/messages.rs` — WatcherEvent types
- `sidequest-server/src/watcher.rs` — watcher event dispatch
- GM panel dashboard — verification point
