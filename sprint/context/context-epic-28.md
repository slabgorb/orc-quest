# Epic 28: Unified Encounter Engine — Kill CombatState/ChaseState, Ship StructuredEncounter

## Why This Epic Exists

Combat wiring has failed ~13 times across Epics 5, 15, 16, 25, and 26. The root cause
is architectural: Epic 16 built StructuredEncounter to unify combat, chase, standoff,
negotiation, and all future encounter types — but never replaced the old systems. Two
encounter systems run in parallel:

**Old (runtime):** CombatState + ChaseState → state_mutations.rs → CombatPatch/ChasePatch → CombatEventPayload → CombatOverlay
**New (dead code):** ConfrontationDef (YAML) → StructuredEncounter → apply_beat() → format_encounter_context() → ConfrontationPayload → ConfrontationOverlay

The server uses the old system for all runtime decisions. It wraps old state in read-only
StructuredEncounter adapters (`from_combat_state()`, `from_chase_state()`) solely to
populate the Confrontation protocol message — but sends `beats: vec![]` every time.
The UI beat buttons render nothing. `apply_beat()` has zero non-test callers.
`format_encounter_context()` has zero non-test callers.

**This epic kills the old system and makes StructuredEncounter the sole runtime model.**

## The Five Failure Patterns (from /sq-wire-it)

1. **Component-First TDD** — build the model, test it, mark done. Integration "in another story."
2. **Deferral Cascade** — each story defers wiring to the next. Collectively: dead code.
3. **Test-Passing Illusion** — all green, but only called from test files.
4. **OTEL Blind Spots** — server says "combat happened" but the math is invisible.
5. **LLM Compensation** — Claude narrates plausible combat. No mechanics engaged.

**Every story in this epic has explicit wiring ACs that verify non-test consumers exist.**

## Architecture: Before and After

### Before (current — split brain)
```
Genre YAML → ConfrontationDef (parsed, never used at runtime)
                                          ↓ (dead)
Player action → IntentRouter → creature_smith → CombatPatch → state_mutations.rs → CombatState
                             → dialectician → ChasePatch → state_mutations.rs → ChaseState
                                                                                    ↓
                                                              from_combat_state() / from_chase_state()
                                                                                    ↓ (read-only adapter)
                                                              StructuredEncounter → ConfrontationPayload (beats: [])
                                                                                    ↓
                                                              UI ConfrontationOverlay (no beat buttons)
                                                              UI CombatOverlay (old, shows HP bars)
```

### After (this epic)
```
Genre YAML → ConfrontationDef (loaded into AppState at startup)
                    ↓
Player action → IntentRouter → narrator → beat_selection → dispatch → apply_beat(beat_id, &def)
                                                                        ↓
                                                            stat_check dispatch:
                                                              "attack" → resolve_attack() on CreatureCore
                                                              "escape" → chase escape logic
                                                              "persuade" → metric_delta only
                                                                        ↓
                                                            StructuredEncounter (sole runtime model on GameSnapshot)
                                                                        ↓
                                                            ConfrontationPayload (beats populated from def)
                                                                        ↓
                                                            UI ConfrontationOverlay (beat buttons work)
                                                            CombatOverlay DELETED
```

## Key Design Decisions

1. **Don't move the math, change the orchestration.** `resolve_attack()` stays as a function.
   It gets called when a combat beat with `stat_check: "attack"` fires. The encounter
   system orchestrates which resolution function to call — it doesn't own the math itself.

2. **HP and status effects stay on CreatureCore.** StructuredEncounter tracks the dramatic
   arc (beats, metric, phase, resolution). CreatureCore tracks creature state (HP, effects,
   inventory). These are different concerns.

3. **Genre packs declare encounter types.** Combat and chase become ConfrontationDef entries
   in rules.yaml, just like standoff, negotiation, trial, etc. Genres that don't have
   combat (victoria, star_chamber) simply don't declare a combat confrontation type.

4. **creature_smith is eliminated as a separate agent mode.** The narrator handles all
   encounter types via beat selection. No more CombatPatch. No more ChasePatch.

5. **No transition layers, no fallbacks, no save migration.** Hard cut. Save files have
   never worked reliably — not a concern.

## Current State of ConfrontationDefs in Genre Packs

| Genre | Existing Confrontation Types | Needs combat | Needs chase |
|-------|------------------------------|--------------|-------------|
| caverns_and_claudes | (none) | YES | YES |
| elemental_harmony | negotiation | YES | YES |
| low_fantasy | negotiation | YES | YES |
| mutant_wasteland | negotiation | YES | YES |
| neon_dystopia | negotiation, net_combat | YES | YES |
| pulp_noir | negotiation, interrogation, roulette, craps | YES | YES |
| road_warrior | negotiation | YES | YES (primary genre mechanic) |
| space_opera | negotiation, ship_combat | YES | YES |
| spaghetti_western | standoff, negotiation, poker | YES | YES |
| star_chamber | (none) | NO (courtroom drama) | NO |
| victoria | negotiation, trial, auction | NO (social intrigue) | NO |

## Key Files

| File | Current Role | After This Epic |
|------|-------------|-----------------|
| `sidequest-game/src/combat.rs` | CombatState runtime model (420 LOC) | **DELETED** — resolve_attack() moves to encounter or resolution module |
| `sidequest-game/src/chase.rs` | ChaseState runtime model (133 LOC) | **DELETED** — escape logic moves similarly |
| `sidequest-game/src/chase_depth.rs` | Chase cinematography/rig stats | **DELETED** — SecondaryStats in encounter.rs replaces RigStats |
| `sidequest-game/src/encounter.rs` | StructuredEncounter (dead code, 664 LOC) | **PROMOTED** — sole runtime encounter model |
| `sidequest-game/src/state.rs` | GameSnapshot with combat + chase + encounter fields | `combat` and `chase` fields removed, `encounter` remains |
| `sidequest-game/src/combatant.rs` | Combatant trait (HP, AC, level) | Stays — CreatureCore still implements it |
| `sidequest-game/src/creature_core.rs` | HP, apply_hp_delta | Stays — encounter calls into it |
| `sidequest-agents/src/patches.rs` | CombatPatch, ChasePatch, WorldStatePatch | CombatPatch + ChasePatch **DELETED** |
| `sidequest-agents/src/orchestrator.rs` | Extracts CombatPatch/ChasePatch from narrator JSON | Extracts beat_selections instead |
| `sidequest-agents/src/agents/narrator.rs` | Combat/chase rules sections | Unified encounter rules section |
| `sidequest-server/src/dispatch/state_mutations.rs` | Applies CombatPatch/ChasePatch (800 LOC) | Applies beat selections via apply_beat() |
| `sidequest-server/src/dispatch/combat.rs` | process_combat_and_chase (121 LOC) | **DELETED** |
| `sidequest-server/src/dispatch/prompt.rs` | Inline combat/chase context (lines 335-374) | Replaced by format_encounter_context() |
| `sidequest-server/src/dispatch/audio.rs` | Reads combat_state/chase_state for mood | Reads encounter for mood |
| `sidequest-protocol/src/message.rs` | CombatEventPayload + ConfrontationPayload | CombatEventPayload **DELETED** |
| `sidequest-ui/src/components/CombatOverlay.tsx` | Old combat overlay | **DELETED** |
| `sidequest-ui/src/components/ConfrontationOverlay.tsx` | Universal encounter overlay (235 LOC) | Sole overlay — already ready |
| `sidequest-genre/src/models/rules.rs` | ConfrontationDef, BeatDef, MetricDef | Add "combat" and "chase" categories |
| `sidequest-content/genre_packs/*/rules.yaml` | Social confrontation types only | Add combat + chase defs per genre |

## Story Dependency Graph

```
28-1  Load ConfrontationDefs ────┬──→ 28-3  Populate beats in protocol
                                 ├──→ 28-4  Wire format_encounter_context
28-2  OTEL for StructuredEncounter ──→ 28-5  Wire apply_beat into dispatch
                                              ↓
                                        28-6  Narrator outputs beat selections
                                              ↓
                                        28-7  StructuredEncounter on GameSnapshot
                                              ↓
                                        28-8  NPC turns through beats
                                              ↓
28-10 Genre pack combat/chase defs ──→ 28-9  DELETE CombatState/ChaseState/Patches
                                              ↓
                                        28-11 Playtest verification

28-2 ──→ 28-12 Remaining game crate OTEL
28-9 ──→ 28-13 Dead export cleanup
```

## ADR References

- ADR-017: Cinematic chase system
- ADR-033: Confrontation resource pools (Epic 16 design)
- ADR-057: Narrator-crunch separation
- ADR-067: Unified narrator agent (no keyword matching)
- ADR-031: Game watcher semantic telemetry
