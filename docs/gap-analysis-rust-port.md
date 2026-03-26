# Gap Analysis: SideQuest Rust Port vs Python Feature Set

**Date:** 2026-03-25
**Author:** Architect (Major Margaret Houlihan)
**Sources:** sq-2/docs/features.md, sq-2 codebase inventory, sq-2 sprint epics 59-64, oq-2 epics 1-3

## Executive Summary

The Python SideQuest engine (sq-2) has 30+ features across 25 subsystems. The Rust port
(oq-2) currently covers the foundation (Epic 1, done), core game loop (Epic 2, planned),
and observability (Epic 3, planned). This leaves significant feature gaps in media
integration, pacing/drama, multiplayer, scenarios, and several planned enhancements from
sq-2's active sprint.

**Epics 1-3 total:** 33 stories, 195 points
**New epics needed:** 8 epics, ~68 stories, ~265 points (estimated)
**Total to feature-complete:** ~460 points across 11 epics

## Coverage Matrix

### Fully Covered by Epics 1-3

| Feature | Python Source | Rust Epic | Status |
|---------|-------------|-----------|--------|
| Protocol / message types | server/protocol.py | Epic 1 | Done |
| Genre pack loading | genre/*.py | Epic 1 | Done |
| Character model | game/character.py | Epic 1 | Done |
| NPC model | game/npc.py | Epic 1 | Done |
| Combat state types | game/combat_models.py | Epic 1 | Done |
| Chase state types | game/chase.py | Epic 1 | Done |
| Inventory system | game/character.py | Epic 1 | Done |
| Trope types | game/state.py | Epic 1 | Done |
| State composition | game/state.py | Epic 1 | Done |
| State delta | state_processor.py | Epic 1 | Done |
| Agent infrastructure | agents/*.py | Epic 1 | Done |
| Prompt framework | prompt_composer.py | Epic 1 | Done |
| JSON extraction | agents/world_state.py | Epic 1 | Done |
| Server skeleton | server/app.py | Epic 1 | Done |
| Session lifecycle | server/session_handler.py | Epic 2 | Planned |
| Character creation | game/character_builder.py | Epic 2 | Planned |
| Orchestrator turn loop | orchestrator.py | Epic 2 | Planned |
| Intent routing | agents/intent_router.py | Epic 2 | Planned |
| Agent execution | agents/claude_agent.py | Epic 2 | Planned |
| State patching | orchestrator.py | Epic 2 | Planned |
| SQLite persistence | game/session.py | Epic 2 | Planned |
| Trope runtime | game/state.py | Epic 2 | Planned |
| E2E integration | — | Epic 2 | Planned |
| Agent telemetry | — | Epic 3 | Planned |
| Semantic validation | — | Epic 3 | Planned |

### NOT Covered — New Epics Required

| Feature | Python Source | Priority | New Epic |
|---------|-------------|----------|----------|
| **Media pipeline** (image/TTS/audio) | media/, voice/, audio/ | P1 | Epic 4 |
| **Pacing & drama engine** | game/tension.py, ADRs | P1 | Epic 5 |
| **Active world pacing** | sq-2 Epic 61 | P1 | Epic 6 |
| **Scenario system** | scenario/*.py | P1 | Epic 7 |
| **Multiplayer** | game/multiplayer_session.py | P1 | Epic 8 |
| **Character depth** | sq-2 Epic 62 + slash commands | P1 | Epic 9 |
| **NPC personality (OCEAN)** | sq-2 Epic 64 | P2 | Epic 10 |
| **Lore & language** | lore/*.py + sq-2 Epic 63 | P2 | Epic 11 |

## Detailed Gap Descriptions

### Epic 4: Media Integration (P1)
Wire sidequest-daemon for images, TTS, and audio. The daemon stays Python; the Rust
server sends requests and receives results. Three subsystems:
- **Image rendering:** Subject extraction from narration, render queue, beat filter
  (suppress mundane scenes), speculative prerendering, hash-based cache
- **TTS/voice:** Kokoro + Piper dual engine, character voice routing, effects
  (reverb, pitch, EQ), text segmentation, streaming delivery
- **Audio/music:** Mood detection from narration, genre track selection, 3-channel
  mixing (music + SFX + ambience), ducking during speech, theme rotation

### Epic 5: Pacing & Drama Engine (P1)
Port the dual-track tension model and drama-aware delivery. This is the "game engine
tuning" from extensive playtesting:
- **TensionTracker:** Gambler's ramp (boring_streak → escalation) + HP stakes +
  event spikes (critical hits, death saves). Produces drama_weight 0.0-1.0.
- **Drama-aware delivery:** Three text reveal modes — INSTANT (<0.30), SENTENCE
  (0.30-0.70), STREAMING (>0.70) with genre-tunable thresholds
- **Pacing detection:** Quiet turn counting, escalation beat injection
- **Beat filter:** Suppress media renders for low-weight beats
- **Narrator length targeting:** drama_weight drives narration sentence count

### Epic 6: Active World & Scene Directives (P1)
Port sq-2 Epic 61. Make the world an active agent — NPCs and factions pursue agendas
independent of player input:
- **Scene directives:** Mandatory narrator instructions ("MUST weave at least one")
- **Engagement multiplier:** Scale trope progression by player engagement
- **Faction agendas:** FactionAgenda model, world YAML support, scene injection
- **World materialization:** Campaign maturity levels (fresh/early/mid/veteran),
  history chapter application

### Epic 7: Scenario System (P1)
Bottle episodes with whodunit/mystery mechanics:
- **Belief state:** Per-NPC knowledge bubbles (facts, suspicions, claims)
- **Gossip propagation:** NPCs spread claims, contradictions decay credibility
- **Clue activation:** Semantic triggers for clue availability
- **Accusation system:** Evidence evaluation, NPC reactions
- **NPC autonomous actions:** Alibi, confess, flee, destroy evidence
- **Scenario pacing:** Turn-based pressure escalation

### Epic 8: Multiplayer (P1)
Multi-player coordination:
- **Turn barrier:** Wait for all players before resolving
- **Party coordination:** Add/remove players mid-session
- **Perception rewriter:** Per-character narration variants (ADR-028)
- **Guest NPC players:** Human-controlled NPCs (ADR-029)
- **Catch-up narration:** Snapshot for joining players
- **Turn modes:** FREE_PLAY, STRUCTURED, CINEMATIC

### Epic 9: Character Depth (P1)
Combines sq-2 Epic 62 (Character Self-Knowledge) with slash commands:
- **Ability descriptions:** Genre-voiced ability text
- **Narrator perception:** Ability-aware narration (involuntary abilities trigger)
- **Narrative character sheet:** Genre-voiced to_narrative_sheet()
- **KnownFact accumulation:** Play-derived knowledge persistence
- **Slash commands:** /status, /inventory, /map, /save, /tone, /gm (server-side)

### Epic 10: NPC Personality Engine — OCEAN (P2)
Port sq-2 Epic 64:
- **OCEAN profiles:** Big Five personality scores on NPCs (0.0-10.0)
- **Behavioral summaries:** Scores → narrator prompt text
- **Shift tracking:** OCEAN changes logged as lore fragments
- **World state integration:** Agent proposes OCEAN shifts from events
- **Disposition connection:** Agreeableness dimension feeds disposition

### Epic 11: Lore & Language (P2)
Port lore/RAG system and sq-2 Epic 63 (Conlang Name Banks):
- **Lore fragments:** Indexed narrative facts with token estimates
- **Static retrieval:** By category or keyword
- **Semantic retrieval:** Embedding-based RAG (optional)
- **Lore seed:** Bootstrap from genre pack + character creation
- **Morpheme glossary:** Conlang name generation with glosses
- **Language knowledge:** Transliteration grows through play

## Dependency Graph

```
Epic 1 (Done) ──► Epic 2 (Core Loop) ──► Epic 3 (Watcher)
                      │
                      ├──► Epic 4 (Media) ──► Epic 5 (Pacing)
                      │
                      ├──► Epic 6 (Active World)
                      │
                      ├──► Epic 7 (Scenarios) ──► depends on Epic 9 (slash commands)
                      │
                      ├──► Epic 8 (Multiplayer)
                      │
                      ├──► Epic 9 (Character Depth)
                      │
                      └──► Epic 11 (Lore) ──► Epic 10 (OCEAN, uses lore for shifts)
```

## Recommended Sequencing

1. **Epic 2** — Core game loop (in progress, blocks everything)
2. **Epic 3** — Game Watcher (unblocks playtesting observability)
3. **Epic 5** — Pacing & Drama (core to game feel, informs all other epics)
4. **Epic 4** — Media Integration (makes playtesting rich)
5. **Epic 6** — Active World (makes the game feel alive)
6. **Epic 9** — Character Depth (player-facing quality)
7. **Epic 7** — Scenarios (advanced game mode)
8. **Epic 8** — Multiplayer (expansion)
9. **Epic 11** — Lore & Language (enrichment)
10. **Epic 10** — OCEAN (measurement/tuning)
