---
story_id: "13-5"
jira_key: ""
epic: "13"
workflow: "tdd"
---

# Story 13-5: Turn Mode Indicator in UI

## Story Details

- **ID:** 13-5
- **Epic:** 13 — Sealed Letter Turn System
- **Workflow:** tdd
- **Points:** 2
- **Status:** In Progress
- **Repository:** sidequest-ui

## Description

Add a UI indicator badge to the game header that displays the current turn mode (Free Play / Structured / Cinematic) with a tooltip explaining what each mode means for the player's action resolution behavior.

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Indicator visible | Badge shows current turn mode in game UI |
| Three modes | Free Play (green), Structured (blue), Cinematic (purple) each have distinct appearance |
| Tooltip | Hovering explains what the mode means for action resolution |
| Transitions | Mode change animates to draw attention |
| Real-time | Updates within 1s of server mode change |

## Technical Context

### What Exists

From Epic 8, the backend has:
- `TurnMode` state machine (FreePlay/Structured/Cinematic) in `sidequest-game/src/turn_mode.rs`
- `TURN_STATUS` message type in protocol for turn submission tracking
- `SharedGameSession` with broadcast channel for real-time updates

### What We're Building

**TurnModeIndicator component** (new):
- Small badge in game header showing current mode
- Three distinct visual states (colors + icons)
- Tooltip with mode explanation
- Smooth fade/slide animation on mode transition

### Protocol Integration

The server needs to send turn mode in TURN_STATUS payloads (or add explicit TURN_MODE message).
Check if `TURN_STATUS` already includes mode field — if not, add `mode: String`.

## Workflow Tracking

**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-04-05T05:00:00Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T05:00:00Z | - | - |

## Delivery Findings

No upstream findings at setup.

## Design Deviations

None at setup.

## Implementation Notes

### Component Structure

```
TurnModeIndicator.tsx
├── Mode state from GameContext
├── Visibility state (show during Structured/Cinematic, optional during FreePlay)
└── Styles: badge appearance + animation
```

### Mode Definitions

- **Free Play** (green badge)
  - Icon: flash/bolt
  - Tooltip: "Actions resolve immediately"
  
- **Structured** (blue badge)
  - Icon: wait/hourglass
  - Tooltip: "All players submit before the narrator responds"
  
- **Cinematic** (purple badge)
  - Icon: film/clapperboard
  - Tooltip: "The narrator sets the pace"

### Animation

Transition on mode change:
- Fade out current badge
- Slide in new badge with highlight
- Duration: 300ms

### Testing Strategy (TDD)

1. **Unit test:** Component renders correct badge for each mode
2. **Unit test:** Tooltip text matches mode definition
3. **Unit test:** Animation triggers on mode change
4. **Integration test:** TurnModeIndicator receives mode via game context and updates UI
5. **Integration test:** Protocol update propagates mode to UI within 1s

### Blocking Dependencies

None. This story runs parallel to other Epic 13 work (13-1, 13-2, 13-3).
