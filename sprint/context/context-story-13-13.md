---
parent: context-epic-13.md
---

# Story 13-13: Player Panel Sealed-Letter Prominence — Submission Indicators and "All In" State

## Business Context

The player panel (TurnStatusPanel) already exists and renders per-player submission status.
But during the playtest it needs to be **prominent** — not a subtle indicator tucked in a
corner. When a sealed round is in progress, every player needs to see at a glance: who's
submitted, who hasn't, and the moment everyone's in.

The sealed-letter metaphor is the design language: each player's action is a sealed letter.
When you submit, your letter is sealed. When everyone's sealed, the letters open.

## Technical Guardrails

- **TurnStatusPanel** already exists at `sidequest-ui/src/components/TurnStatusPanel.tsx` —
  enhance, don't rebuild
- **Visual prominence:** panel should be impossible to miss during a sealed round. Not a
  small badge — a clear visual block showing all players and their status.
- **Per-player indicator:** sealed letter / envelope icon or similar metaphor. Unsealed =
  still composing. Sealed = submitted. All sealed = "opening letters" transition state.
- **"All in" transition:** when all players have submitted, brief visual beat before narrator
  resolves (e.g., "All letters sealed" → action reveal → narration)
- **Hidden in single-player:** panel not shown when solo
- **Consumes existing TURN_STATUS messages** — no new protocol needed

## Scope Boundaries

**In scope:**
- Redesign TurnStatusPanel for visual prominence during sealed rounds
- Per-player sealed/unsealed indicator
- "All in" / "all sealed" transition state
- Hide for single-player sessions
- Responsive — works on both desktop and mobile layouts

**Out of scope:**
- New protocol messages (uses existing TURN_STATUS)
- Barrier logic (that's 13-11)
- Action reveal rendering (uses existing ActionReveal handling in 13-14)
- Animation/polish beyond basic "sealed" visual metaphor

## AC Context

| AC | Detail |
|----|--------|
| Prominent during sealed round | Player panel is a clear visual block, not a subtle indicator |
| Per-player status | Each player shows sealed (submitted) or unsealed (composing) state |
| "All in" state | Visual transition when all players have submitted |
| Hidden solo | Panel not rendered for single-player sessions |
| Existing messages | Consumes TURN_STATUS broadcasts, no new protocol |
| Responsive | Works on desktop and mobile layouts |

## Key Files

| File | Change |
|------|--------|
| `sidequest-ui/src/components/TurnStatusPanel.tsx` | Redesign for prominence |
| `sidequest-ui/src/components/TurnModeIndicator.tsx` | May merge into panel or update |
| `sidequest-ui/src/components/GameBoard/GameBoard.tsx` | Panel placement/visibility |
| `sidequest-ui/src/styles/` | Themed styling for sealed-letter metaphor |
