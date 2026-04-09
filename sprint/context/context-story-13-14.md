---
parent: context-epic-13.md
depends_on: [13-11, 13-12]
---

# Story 13-14: Sealed-Round Prompt Architecture — One Narrator Call with Initiative Context

## Business Context

Today each player action triggers a separate narrator call. The narrator responds to one
player at a time, never seeing what others are doing. This means actions can't interact
within a round, one player drives the narrative, and the AI DM has no opportunity to
resolve initiative or create dramatic tension from simultaneous choices.

This story changes the prompt to: one call per round with all player actions, encounter
type, per-player stats, and initiative rules from the genre pack. The narrator resolves
initiative order and produces one synthesized scene.

This is the hardest story in the epic — it changes how the narrator prompt is built and
what the narrator is asked to do.

## Technical Guardrails

- **One narrator call per round** when barrier resolves, not N calls
- **Prompt includes:**
  - All N player actions (presented without submission-order bias)
  - Current encounter type (from intent classifier or state)
  - Per-player stats relevant to that encounter type (from genre pack initiative rules)
  - Initiative rules text from genre pack
  - Instruction: "Determine initiative order based on encounter type and stats. Resolve
    actions in that order. All actions were submitted simultaneously — no player knew
    what others chose."
- **Narrator output** is one synthesized scene, not N independent narrations
- **Perception rewriter** (ADR-028) handles per-player view splitting — already working,
  just verify it handles the new combined-scene format
- **OTEL spans:** `narrator.sealed_round` with `player_count`, `encounter_type`,
  `initiative_order` (as determined by narrator), `combined_action_count`

## Scope Boundaries

**In scope:**
- Modify prompt builder to compose batched prompt with all actions
- Include initiative context (encounter type + stats + genre rules)
- Ensure one narrator call per round (claim election already handles this)
- Verify perception rewriter works with synthesized scene output
- ActionReveal broadcast before narration (show all sealed actions to all players)

**Out of scope:**
- Barrier activation (that's 13-11)
- Genre pack schema definition (that's 13-13 — this story consumes it)
- Player panel UI changes (that's 13-14)
- Dice resolution integration (ADR-074 — future)

## AC Context

| AC | Detail |
|----|--------|
| One narrator call per round | Barrier resolves → single orchestrator dispatch with all actions |
| Actions unordered in prompt | No submission-time bias — actions presented as a set |
| Initiative context included | Encounter type + per-player stats + genre initiative rules in prompt |
| Narrator resolves initiative | Output references initiative order, actions resolve in that order |
| Synthesized scene | One scene, not N independent narrations |
| ActionReveal broadcast | All sealed actions revealed to all players before narration |
| Perception rewriter works | Per-player views still function with combined scene |
| OTEL telemetry | `narrator.sealed_round` span with initiative metadata |

## Key Files

| File | Change |
|------|--------|
| `sidequest-server/src/dispatch/mod.rs` | Batched dispatch after barrier, ActionReveal broadcast |
| `sidequest-server/src/dispatch/prompt.rs` (or equivalent) | Prompt builder — add PARTY ACTIONS section + initiative context |
| `sidequest-agents/` | Orchestrator/narrator prompt template changes |
| `sidequest-game/src/barrier.rs` | `named_actions()` output consumed by prompt builder |
| `sidequest-genre/src/lib.rs` | Expose initiative rules from genre pack |
