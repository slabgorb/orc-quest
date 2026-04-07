---
parent: context-epic-28.md
---

# Story 28-11: Playtest Verification — Combat and Chase Through Unified System

## Business Context

Combat has been "done" ~13 times. Each time, tests pass and code review approves.
Then playtest reveals it doesn't work. This story IS the playtest. It doesn't ship
until a human plays through combat and chase in two genres and the OTEL dashboard
proves every mechanical decision was real.

## Technical Approach

### Playtest scenario requirements

Two genre packs, minimum. One fantasy (low_fantasy or caverns_and_claudes), one
non-fantasy (spaghetti_western or neon_dystopia).

Each playtest must exercise:

**Combat flow:**
1. Narrator initiates combat encounter (starts StructuredEncounter with type "combat")
2. UI ConfrontationOverlay appears with beat buttons (attack, defend, flee + genre specials)
3. Player selects a beat via UI button
4. Server dispatches beat → apply_beat() → stat_check "attack" → resolve_attack() → HP delta
5. NPC gets a beat selection (narrator selects for NPC) → same dispatch pipeline
6. Player HP decreases from NPC attack (visible in UI character sheet)
7. NPC HP decreases from player attack (visible in ConfrontationOverlay metric bar)
8. Combat resolves when threshold crossed (NPC HP at 0 = victory)
9. ConfrontationOverlay disappears

**Chase flow:**
1. Narrator initiates chase encounter (starts StructuredEncounter with type "chase")
2. UI shows chase beats (sprint, shortcut, obstacle)
3. Player selects chase beat
4. Separation metric increases per beat
5. Chase resolves when separation threshold crossed
6. If chase has escalates_to: combat and doesn't escape, combat starts

**OTEL verification (non-negotiable):**
Every step above MUST produce visible events in the GM panel dashboard:
- encounter.started (type, actors)
- encounter.beat_applied (beat_id, stat_check, metric change)
- creature.hp_delta (for combat beats)
- encounter.npc_beat (NPC actions)
- encounter.phase_transition (setup → opening → escalation → climax → resolution)
- encounter.resolved (outcome, total_beats)

If the narrator produces "the goblin attacks for 12 damage" but no encounter.beat_applied
or creature.hp_delta event appears in OTEL, **the story fails**. That's Pattern 5
(LLM Compensation) and the whole reason this epic exists.

### How to run

```bash
just tmux          # Start 4-pane dev session
just api-run       # Panel 1: API server
just ui-dev        # Panel 2: UI dev server
just daemon-run    # Panel 3: Daemon (optional for media)
# Panel 4: open browser to localhost:5173
# Open second tab to localhost:5173/dashboard (GM panel)
```

Play through character creation, get into the world, trigger combat via player action.
Watch the OTEL dashboard timeline. Verify every event.

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| Combat plays | Player can fight an enemy through beat selection, damage applies both ways | Playtest observation |
| Chase plays | Player can chase/be chased, separation metric advances, resolves | Playtest observation |
| Beat buttons work | UI ConfrontationOverlay shows beat buttons, clicking them sends action | Playtest observation |
| NPC fights back | NPC beat selections produce real HP damage on player | OTEL: creature.hp_delta for NPC attack |
| Victory works | Defeating all enemies resolves combat encounter | OTEL: encounter.resolved with outcome |
| Escalation works | Standoff/chase that resolves can escalate to combat | Playtest observation + OTEL |
| OTEL complete | Every mechanical decision visible in GM panel | OTEL dashboard timeline review |
| No LLM compensation | Narrator damage numbers match OTEL hp_delta values | Compare narration text to OTEL events |
| Two genres | Tested in at least 2 different genre packs | Playtest in both |
| CombatOverlay gone | Old CombatOverlay does not appear in UI at any point | Visual verification |

## Scope Boundaries

**In scope:** Playing the game, verifying in OTEL, documenting results
**Out of scope:** Fixing bugs found — those become follow-up stories or hotfixes within this epic
