---
parent: context-epic-1.md
---

# Story 1-7: Game Subsystems — CombatState, ChaseState, NarrativeEntry, Progression

## Business Context

This is where the game engine gains interactive mechanics. CombatState and ChaseState are
the two action subsystems that make SideQuest more than a chatbot. NarrativeEntry is the
append-only log agents read to maintain story continuity. Progression governs character
growth. Without this story, you have types but no game mechanics.

**Python sources:**
- `sq-2/sidequest/game/combat_models.py` — Enemy, ActiveEffect, CombatState
- `sq-2/sidequest/game/chase.py` — ChaseState, ChaseBeat, ChasePhase, RigStats (275 lines)
- `sq-2/sidequest/game/narrative_models.py` — NarrativeEntry
- `sq-2/sidequest/game/narrative_character.py` — NarrativeCharacter, Relationship, NarrativeState
- `sq-2/sidequest/game/encounter_tag.py` — EncounterTag + query functions
- `sq-2/sidequest/game/progression.py` — 4 progression tracks (462 lines)
- `sq-2/sidequest/game/state.py:79-315` — TropeStatus, TropeState, trope lifecycle methods

## Technical Guardrails

- **Port lesson #4 (decompose GameState):** Python's `GameState` has CombatState, ChaseState,
  trope methods all inline. Story 1-7 builds standalone domain structs that story 1-8 composes
- **Port lesson #6 (HP clamping):** Progression's `check_milestone_level_up` must use
  `clamp_hp()` from `hp.rs` (story 1-6). No inline clamping
- **Port lesson #9 (validation):** Use `NonBlankString` for Enemy.name, ActiveEffect.name,
  ChaseBeat.event, EncounterTag.npc_id, etc.
- **ADR-017 (Cinematic Chase Engine):** Five-phase arc, separation tracking, rig-as-participant
- **ADR-018 (Trope Engine):** DORMANT→ACTIVE→RESOLVED lifecycle, escalation beats, passive progression
- **ADR-021 (Progression System):** Four tracks — milestones, affinities, item evolution, wealth tiers
- **ADR-014 (Diamonds and Coal):** Item evolution state machine (coal→named coal→diamond)

### Python → Rust Translation

| Python | Rust | Notes |
|---|---|---|
| `combat_models.Enemy` | `struct Enemy` implementing `Combatant` | Reuse trait from 1-6 |
| `combat_models.ActiveEffect` | `struct ActiveEffect` | `NonBlankString` for name |
| `CombatState` (inline on GameState) | `struct CombatState` standalone | Port lesson #4 |
| `chase.ChaseState` | `struct ChaseState` standalone | 6 enums + 5 sub-models |
| `chase.ChasePatch` | `struct ChasePatch` with deny_unknown_fields | Port lesson #16 |
| `TropeStatus` / `TropeState` | `struct TropeState` with lifecycle enum | ADR-018 |
| `progression.check_milestone_level_up()` | `fn check_milestone_level_up()` | Uses `clamp_hp()` |

### Trope Lifecycle State Machine

```
DORMANT → activate_trope() → ACTIVE → resolve_trope() → RESOLVED
                                ↑
                     progress_trope() (0.0..=1.0)
                     check_escalation_beats()
                     tick_passive_progression()
```

## Scope Boundaries

**In scope:**
- `combat.rs`: CombatState, CombatPatch, Enemy (implementing Combatant), ActiveEffect
- `chase.rs`: All 6 enums, RigStats, DecisionOption, DecisionPoint, ChaseBeat, ChaseState, ChasePatch
- `narrative.rs`: NarrativeEntry, NarrativeCharacter, NarrativeState, Relationship, EncounterTag
- `progression.rs`: All 4 progression tracks, journey summary generation
- `turn.rs`: TurnPhase, basic turn tracking
- Trope state and lifecycle functions

**Out of scope:**
- GameSnapshot composition (story 1-8)
- State delta computation (story 1-8)
- Session persistence / rusqlite (story 1-8)
- WorldStatePatch (agent output type, story 1-11)
- Chase cinematography/pacing formatters (agent context, story 1-11)
- Lore indexing (not in Rust port scope)

## AC Context

| AC | Detail |
|----|--------|
| CombatState round-trips | Serialize/deserialize losslessly. Enemy implements Combatant |
| ChaseState invariants | separation >= 0, names required when in_chase, rig_hp <= max |
| ChasePatch deny_unknown | LLM patches with unknown keys rejected at parse time |
| NarrativeEntry | Non-blank description. Query by NPC, encounter type, archetype |
| Trope lifecycle | activate fails if already active, progress clamps 0.0..=1.0 |
| Progression uses clamp_hp | Level-up HP delta goes through shared clamp function |
| Progression is pure | Functions take &mut Character, return event structs. No I/O |
| Item evolution gates | Naming fires at threshold, power-up fires at threshold. power_level capped at 10 |

## Assumptions

- Combat and chase mechanics are well-documented in ADRs, no design discovery needed
- These subsystems are purely domain logic — no async, no I/O, no subprocess calls
- The Combatant trait from 1-6 provides sufficient interface for combat/chase generics
