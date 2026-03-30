# SideQuest — AI Dungeon Master

An AI narrator engine that runs tabletop-style RPGs in any genre, powered by coordinated
Claude agents. Players connect via browser, create characters through genre-driven
scenes, and explore procedural worlds with real-time image generation, voice synthesis,
and adaptive music. Multiplayer with turn barriers, perception rewriting, and WebRTC voice.

## Repository Ecosystem

```
┌──────────────────────────────────────────────────────────────┐
│  oq-1 (this repo) — Orchestrator                            │
│  Sprint tracking, cross-repo justfile, architecture docs     │
└──────┬──────────────┬──────────────┬──────────────┬──────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────┐ ┌───────────┐ ┌──────────────┐ ┌────────────────┐
│sidequest-api│ │sidequest- │ │sidequest-    │ │sidequest-      │
│   (Rust)    │ │  ui (TS)  │ │daemon (Py)   │ │content (LFS)   │
│             │ │           │ │              │ │                │
│ 6-crate     │ │ React 19  │ │ Flux images  │ │ Genre pack     │
│ workspace   │ │ client    │ │ Kokoro TTS   │ │ YAML + audio   │
│ 7 Claude    │ │ Audio     │ │ ACE-Step     │ │ + images       │
│ agents      │ │ engine    │ │ music        │ │ (Git LFS)      │
│ 52 game     │ │ Voice     │ │ 3-channel    │ │                │
│ modules     │ │ chat      │ │ mixer        │ │ 7 genre packs  │
└─────────────┘ └───────────┘ └──────────────┘ └────────────────┘
       ▲              │              ▲
       │  WebSocket   │   Unix sock  │
       └──────────────┘──────────────┘
```

| Repo | Language | Purpose | GitHub |
|------|----------|---------|--------|
| **oq-1** | — | Orchestrator, docs, sprint tracking | slabgorb/oq-1 |
| **sidequest-api** | Rust | Game engine, WebSocket API, agent orchestration | slabgorb/sidequest-api |
| **sidequest-ui** | TypeScript | React 19 game client, audio engine, WebRTC voice | slabgorb/sidequest-ui |
| **sidequest-daemon** | Python | Media services (Flux, Kokoro, ACE-Step, mixer) | slabgorb/sidequest-daemon |
| **sidequest-content** | YAML + LFS | Genre pack configs, audio, images, worlds | slabgorb/sidequest-content |

Subrepos are gitignored — clone them alongside this directory or use `just setup`.

## Quick Start

```bash
just setup          # Clone subrepos, install dependencies
just api-run        # Start Rust API server
just daemon-run     # Start Python media daemon
just ui-dev         # Start React dev server
just api-check      # fmt + clippy + test (API)
just status         # Git status across all repos
```

### Running a Playtest

```bash
# Terminal 1: API server
just api-run

# Terminal 2: Media daemon (needs GPU for image/voice/music)
just daemon-run

# Terminal 3: React client
just ui-dev

# Open http://localhost:5173 in browser
# Select genre → world → enter name → create character → play
```

See [`docs/playtest-script.md`](docs/playtest-script.md) for a structured test checklist.

## Genre Packs

Seven narrative worlds, each with its own rules, tropes, character creation, audio, visual style, faction agendas, OCEAN personality archetypes, and conlang morphemes:

| Pack | Theme | Worlds |
|------|-------|--------|
| **elemental_harmony** | Martial arts / elemental magic | Shattered Accord, Burning Peace |
| **low_fantasy** | Gritty medieval | — |
| **mutant_wasteland** | Post-apocalyptic mutants | Flickering Reach |
| **neon_dystopia** | Cyberpunk | — |
| **pulp_noir** | 1930s detective | — |
| **road_warrior** | Vehicular post-apocalypse | — |
| **space_opera** | Sci-fi space adventure | — |

Genre packs live in `sidequest-content/` (Git LFS) and are loaded by path reference.

## How It Works

1. **Player connects** via WebSocket from the React client
2. **Character creation** flows through genre-driven scenes (choices + freeform text)
3. **Each turn:** player action → intent classification (Haiku) → agent dispatch → state patch → narration broadcast
4. **7 agents** coordinate: Narrator, WorldBuilder, CreatureSmith, Ensemble, Dialectician, IntentRouter, Troper — all via `claude -p` subprocess
5. **Media pipeline:** narration triggers image generation (Flux), voice synthesis (Kokoro), and mood-based music (ACE-Step) in parallel — background-first, only text is critical path
6. **Pacing engine:** dual-track TensionTracker produces drama_weight (0.0-1.0) → controls narration length, delivery speed, beat escalation, and media render gating
7. **World systems:** faction agendas inject per-turn, trope engine drives narrative arcs, world materialization tracks campaign maturity
8. **NPC personality:** OCEAN Big Five profiles shape NPC voice and behavior, shift over time from game events
9. **Knowledge:** KnownFacts accumulate from play, lore fragments seed from genre packs, conlang names generated from morpheme glossaries
10. **Multiplayer:** turn barriers with adaptive timeout, 3 turn modes (FREE_PLAY/STRUCTURED/CINEMATIC), perception rewriting, WebRTC voice chat

## Rust Crate Architecture

```
sidequest-api/
├── sidequest-protocol     # GameMessage enum, 20+ typed payloads
├── sidequest-genre        # YAML genre pack loader
├── sidequest-game         # 52 modules — state, combat, NPCs, lore, audio, pacing
├── sidequest-agents       # Claude CLI subprocess, 7 agent types
├── sidequest-server       # axum HTTP/WS, session management, orchestrator
└── sidequest-daemon-client # HTTP client for Python media daemon
```

See [`docs/architecture.md`](docs/architecture.md) for the full system design.

## Documentation

### System Design
- [`docs/architecture.md`](docs/architecture.md) — Layer diagram, crate structure, game systems
- [`docs/wiring-diagrams.md`](docs/wiring-diagrams.md) — End-to-end signal traces for all 15 feature areas (Mermaid)
- [`docs/system-diagram.md`](docs/system-diagram.md) — Repository ecosystem, data flow, sequence diagrams
- [`docs/api-contract.md`](docs/api-contract.md) — WebSocket + REST protocol (23 message types)
- [`docs/tech-stack.md`](docs/tech-stack.md) — Crate and dependency choices

### Game Design
- [`docs/adr/`](docs/adr/) — 32 Architecture Decision Records

### Project Status
- [`docs/feature-inventory.md`](docs/feature-inventory.md) — Feature inventory: done, wired, planned
- [`docs/gap-analysis-rust-port.md`](docs/gap-analysis-rust-port.md) — Feature parity with Python codebase
- [`docs/port-lessons.md`](docs/port-lessons.md) — Technical debt fixes from Python

## Progress

103 of 138 stories complete across 15 epics (75%).

| Epic | Status | Description |
|------|--------|-------------|
| 1. Workspace Scaffolding | **Complete** | Rust crates, types, genre loading |
| 2. Core Game Loop | **Complete** | Turn loop, agents, persistence |
| 3. Game Watcher | **Complete** | Telemetry, GM mode |
| 4. Media Integration | **Complete** | Images, TTS, music, audio mixing |
| 5. Pacing & Drama | **Complete** | Tension model, drama-aware delivery |
| 6. Active World | **Complete** | Scene directives, faction agendas, materialization |
| 7. Scenario System | Planned | Whodunit, belief state, gossip (P2) |
| 8. Multiplayer | **Complete** | Turn barrier, perception rewriter, guest NPCs |
| 9. Character Depth | 92% | Abilities, slash commands, footnotes, journal |
| 10. OCEAN Personality | **Complete** | Big Five NPC profiles, shift tracking |
| 11. Lore & Language | **Complete** | RAG retrieval, conlang names, narrator injection |
| 12. Cinematic Audio | Planned | Score cue variations, crossfade (P2) |
| 13. Sealed Letter Turns | 20% | Simultaneous input, barrier fixes |
| 14. Session UX | Planned | Spawn, text sliders, chargen polish |
| 15. Playtest Debt | Planned | Dead code, OCEAN wiring, voice/mic |

**Sprint 1** (complete): Bootstrap — 85 stories, 672 points, 5 days
**Sprint 2** (active): Multiplayer Works For Real — sealed letter turns, session UX, text tuning

## Sprint Tracking

Sprint plans live in `sprint/` as YAML files with per-story context documents.
See `sprint/current-sprint.yaml` for active work.
