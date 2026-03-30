# SideQuest API — Architecture

> System design for the Rust port of the SideQuest AI Narrator engine.
> 6-crate workspace, 52 game modules, 7 agent types, 3 turn modes.
>
> **Last updated:** 2026-03-30

## Architectural Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Client (sidequest-ui)                  │
│  ThemeProvider, GameLayout, NarrativeView, PartyPanel, CombatOverlay│
│  useGameSocket, useStateMirror, useVoicePlayback, useMusicPlayer   │
└────────┬──────────────────────────────────────┬─────────────────────┘
         │ WebSocket /ws (JSON + binary PCM)     │ REST /api/genres
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Transport Layer (sidequest-server)              │
│  axum Router, WebSocket upgrade, CORS, static files                 │
│  router.rs, ws.rs, telemetry.rs, render_integration.rs              │
└────────┬────────────────────────────────────────────────────────────┘
         │ GameMessage (sidequest-protocol)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Session Layer (sidequest-server)                │
│  Per-connection state machine: Connect → Create → Play              │
│  SharedGameSession for multiplayer (Arc<RwLock<>>)                  │
│  session.rs, shared_session.rs, lifecycle.rs, dispatch.rs           │
└────────┬────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Orchestrator Layer (sidequest-server/lib.rs)      │
│  Intent routing → Agent dispatch → State patching → Broadcast       │
│  Slash command interception, TurnBarrier, perception rewriting      │
│  Pacing engine (TensionTracker → drama_weight → delivery mode)      │
└────────┬──────────────────────┬─────────────────────────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────────┐ ┌────────────────────────────────────────────┐
│    Agent Layer       │ │              Game Layer (sidequest-game)    │
│  (sidequest-agents)  │ │  52 modules: state, combat, chase, tropes, │
│  Claude CLI subproc  │ │  inventory, NPCs, OCEAN, lore, conlang,    │
│  7 agent types       │ │  faction agendas, world materialization,   │
│  Timeout + recovery  │ │  music direction, voice routing, barriers  │
└──────────────────────┘ └──────────────┬─────────────────────────────┘
                                        │
         ┌──────────────────────────────┤
         ▼                              ▼
┌──────────────────────┐ ┌────────────────────────────────────────────┐
│  Genre Layer         │ │           Persistence Layer                 │
│  (sidequest-genre)   │ │  rusqlite (saves), serde_yaml (genre packs)│
│  YAML pack loader    │ │  Narrative log, KnownFact accumulation     │
│  7 genre packs       │ │  persistence.rs                            │
└──────────────────────┘ └────────────────────────────────────────────┘

         ┌────────────────────────────────────────────────────────────┐
         │              Daemon Client (sidequest-daemon-client)        │
         │  HTTP/Unix socket → sidequest-daemon (Python sidecar)      │
         │  Image gen (Flux), TTS (Kokoro), Audio mixing (pygame)     │
         └────────────────────────────────────────────────────────────┘
```

## Workspace Structure

```
sidequest-api/
├── Cargo.toml                        # [workspace] root
├── crates/
│   ├── sidequest-protocol/           # GameMessage enum, 20+ typed payloads, serde
│   ├── sidequest-genre/              # YAML loader, genre pack structs, 7 packs
│   ├── sidequest-game/               # 52 modules — state, combat, NPCs, lore, audio, etc.
│   ├── sidequest-agents/             # Claude CLI subprocess, 7 agent types, timeout/recovery
│   ├── sidequest-server/             # axum HTTP/WS, session management, orchestrator
│   └── sidequest-daemon-client/      # HTTP client for Python media daemon
└── tests/                            # Integration tests
```

**Dependency graph:**
```
sidequest-server
  ├── sidequest-agents
  │     └── sidequest-protocol
  ├── sidequest-game
  │     ├── sidequest-protocol
  │     └── sidequest-genre
  ├── sidequest-daemon-client
  └── sidequest-protocol
```

## Key Design Decisions

### ADR-001: Claude CLI Only

All LLM calls use `claude -p` subprocess via `tokio::process::Command`. No Anthropic SDK. Claude Max subscription handles billing. The agent layer wraps this with timeout, stdout parsing, and error recovery across 7 agent types: Narrator, WorldBuilder, CreatureSmith, Ensemble, Dialectician, IntentRouter, Troper.

### ADR-002: Typed Protocol

Strongly-typed Rust structs for every message payload using `serde(tag = "type")` on the `GameMessage` enum. 20+ message types. The type system catches payload mismatches at compile time — eliminates the `KeyError` class of bugs from the Python codebase.

### ADR-003: Session as Actor

Each WebSocket connection spawns a tokio task owning a `Session`. Single-player: one session, one orchestrator, no contention. Multiplayer: sessions share a `SharedGameSession` behind `Arc<RwLock<>>` with `TurnBarrier` for coordinated turn resolution.

### ADR-004: Genre Packs as YAML

7 genre packs loaded via `serde_yaml` into typed structs. Read-only at runtime. Shared with sq-2 and sidequest-content repo. Each pack defines: world topology, NPC archetypes (with OCEAN profiles), item catalogs, trope definitions, audio themes, visual style, conlang morphemes, and faction agendas.

### ADR-005: Background-First Pipeline

Only the text narration response is on the critical path. Everything else spawns as background tasks: image generation, TTS synthesis, music cue selection, state delta computation, trope tick, lore accumulation. The player sees narration immediately; media arrives asynchronously.

### ADR-006: Persistence via SQLite

`rusqlite` for structured persistence (game state, character data, saves). Wrapped in `spawn_blocking` at the async boundary. Narrative log is append-only. KnownFacts persist and accumulate across turns with provenance tracking.

## Game Systems (sidequest-game, 52 modules)

### Core State
- **GameState:** Central state composition — characters, NPCs, world, combat, chase
- **State deltas:** JSON patches for incremental updates, broadcast to all clients
- **Session persistence:** Save/load GameSnapshot via SQLite

### Combat & Chase
- **Combat:** Turn-based with combatant tracking, HP management, ability resolution
- **Chase:** Beat-based cinematic chases with Lead variable and rig mechanics (ADR-017)
- **Consequences:** Action outcome tracking

### Characters & NPCs
- **Character:** Unified model — narrative identity + mechanical stats (ADR-007)
- **NPC:** OCEAN personality profiles (0.0-10.0), disposition system, behavioral summaries
- **Guest NPCs:** Human-controlled NPCs in multiplayer (ADR-029)
- **Character builder:** Genre-driven scene-based creation state machine (ADR-015/016)

### Narrative Systems
- **KnownFact:** Play-derived knowledge with tiered injection by relevance
- **Lore:** LoreFragment/LoreStore, genre pack seeding, semantic retrieval
- **Conlang:** Morpheme glossary, name bank generation, transliteration growth
- **Scene directives:** Mandatory narrator instructions with engagement multiplier
- **Footnotes:** Structured output with discovery/callback typing

### World Systems
- **Faction agendas:** Goals + urgency, injected into scenes per turn
- **World materialization:** Campaign maturity levels (fresh/early/mid/veteran)
- **Trope engine:** Genre-defined narrative pacing via lifecycle management (ADR-018)
- **Cartography:** Graph-based topology with fog of war (ADR-019)

### Pacing & Drama
- **TensionTracker:** Dual-track model — gambler's ramp + HP stakes + event spikes
- **Drama-aware delivery:** INSTANT (<0.30) / SENTENCE (0.30-0.70) / STREAMING (>0.70)
- **Quiet turn detection:** Escalation beat injection after sustained low drama
- **Beat filter:** Suppress media renders for low-weight beats

### Multiplayer
- **TurnBarrier:** Wait for all players, adaptive timeout (3s for 2-3, 5s for 4+)
- **Turn modes:** FREE_PLAY, STRUCTURED, CINEMATIC
- **Party action composition:** Multi-character PARTY ACTIONS block
- **Perception rewriter:** Per-player narration variants based on status effects
- **Catch-up narration:** Snapshot + "Previously On..." for mid-session joins

### Media Integration
- **Music director:** Mood extraction from narration → audio cue selection
- **Voice router:** Character voice mapping from genre pack presets
- **TTS streaming:** Text segmentation → Kokoro synthesis → binary PCM frames
- **Render queue:** Speculative prerendering with hash-based cache dedup
- **Subject extractor:** Prose → visual description via Claude CLI

### Player Interface
- **Slash router:** Server-side /command interception before intent classification
- **Commands:** /status, /inventory, /map, /save, /help, /tone, /gm suite
- **Inventory:** Items by type, equipped state, merchant transactions
- **Progression:** Milestones, affinities, item evolution, wealth (ADR-021)

## Multiplayer Architecture

```
Client A ──ws──► Session A ─┐
                             ├──► SharedGameSession (Arc<RwLock<>>)
Client B ──ws──► Session B ─┘        │
                                     ├── TurnBarrier (adaptive timeout)
Client C ──ws──► Session C ──────────┤   └── Resolution lock (one narrator call)
                                     ├── Game State (single source of truth)
                                     ├── Orchestrator (agent dispatch)
                                     ├── Perception rewriter (per-player variants)
                                     └── State deltas broadcast to all sessions
```

Three turn modes govern coordination:
- **FREE_PLAY:** Actions process immediately, no barrier
- **STRUCTURED:** Sealed letter pattern — all submit, then barrier resolves, one narrator call
- **CINEMATIC:** DM-driven, players observe

## What Stays in Python (sidequest-daemon)

The ML inference pipeline stays in Python as a sidecar service. Rust communicates via `sidequest-daemon-client` crate over HTTP/Unix socket.

| Subsystem | Stack | Notes |
|-----------|-------|-------|
| Image generation | Flux.1 (schnell + dev) | 6 render tiers, scene cache, beat filter |
| TTS synthesis | Kokoro (54 voices) | Streaming, per-character voice routing |
| Audio mixing | pygame mixer | 3-channel (music/SFX/ambience), speech ducking |
| Scene interpretation | Pattern matching | Narrative text → structured stage cues |
| Subject extraction | Claude CLI | Prose → visual descriptions |

```
sidequest-api (Rust)  ◄──── HTTP / Unix socket ────►  sidequest-daemon (Python)
     │                                                        │
     ├── Sends: narrative text, scene context                 ├── Returns: image URLs, audio paths
     ├── Sends: voice synthesis requests                      ├── Returns: binary PCM frames
     └── Shares: genre_packs/ (read-only assets)              └── Reads: genre_packs/ visual/audio config
```

## ADR Index

32 Architecture Decision Records govern the system. See [docs/adr/README.md](adr/README.md) for the full index covering: core architecture (7), prompt engineering (2), agent system (4), game systems (12), frontend/protocol (2), multiplayer (3), and media pipeline (12 from sq-2).

## Wiring Diagrams

For end-to-end signal traces showing every feature's path from UI input through server layers to storage, see [docs/wiring-diagrams.md](wiring-diagrams.md). Covers all 15 feature areas with Mermaid flowcharts, file paths, and function names.
