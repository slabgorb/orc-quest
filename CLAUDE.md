# CLAUDE.md — SideQuest (Rust Rewrite)

This is the orchestrator repo for the SideQuest RPG Runner/Editor It coordinates four subrepos:
- **sidequest-api** — Rust game engine and WebSocket API (workspace with 12 crates)
- **sidequest-ui** — React/TypeScript game client
- **sidequest-daemon** — Python media services (image gen, audio)
- **sidequest-content** — Genre packs (YAML configs, audio, images, world data)

## Repository Structure

```
orc-quest/                    # This repo (orchestrator, also cloned as oq-1 / oq-2)
├── sprint/                   # Sprint tracking
├── docs/                     # Architecture docs and ADRs
│   ├── api-contract.md       # WebSocket + REST contract (from UI)
│   ├── tech-stack.md         # Crate choices
│   ├── architecture.md       # System design and layer diagram
│   └── adr/                  # Architecture Decision Records
├── scripts/                  # Cross-repo scripts (playtest, music gen, etc.)
├── scenarios/                # Test/playtest scenarios
└── justfile                  # Cross-repo task runner

sidequest-content/            # Genre packs — single source of truth (subrepo)
├── genre_packs/
│   ├── caverns_and_claudes/
│   ├── elemental_harmony/
│   ├── low_fantasy/
│   ├── mutant_wasteland/
│   ├── neon_dystopia/
│   ├── pulp_noir/
│   ├── road_warrior/
│   ├── space_opera/
│   ├── spaghetti_western/
│   ├── victoria/
│   └── <genre>/worlds/<world>/
└── CLAUDE.md

sidequest-api/                # Rust backend (subrepo)
├── Cargo.toml                # [workspace] root
├── crates/
│   ├── sidequest-protocol/   # GameMessage, typed payloads (serde)
│   ├── sidequest-genre/      # YAML genre pack loader
│   ├── sidequest-game/       # State, characters, encounters, tropes
│   ├── sidequest-agents/     # Claude CLI subprocess orchestration
│   ├── sidequest-daemon-client/ # Client for Python media daemon
│   ├── sidequest-server/     # axum HTTP/WebSocket, sessions, dispatch
│   ├── sidequest-telemetry/  # OTEL span definitions and watcher macros
│   ├── sidequest-promptpreview/ # CLI: prompt preview and inspection
│   ├── sidequest-encountergen/ # CLI: enemy stat block generator
│   ├── sidequest-loadoutgen/ # CLI: starting equipment generator
│   ├── sidequest-namegen/    # CLI: NPC identity block generator
│   └── sidequest-validate/   # Genre pack validation utilities
└── tests/

sidequest-ui/                 # React frontend (subrepo)
├── src/
│   ├── __tests__/
│   ├── assets/
│   ├── audio/                # Music + SFX playback (no TTS)
│   ├── components/
│   ├── dice/                 # 3D dice overlay (Three.js + Rapier)
│   ├── hooks/
│   ├── lib/
│   ├── providers/
│   ├── screens/
│   ├── styles/
│   └── types/
└── package.json

sidequest-daemon/             # Python media services (subrepo)
├── sidequest_daemon/         # Package root
│   ├── audio/                # Music library, SFX mixer, scene interpreter
│   ├── genre/
│   ├── media/                # Flux image generation pipeline
│   ├── ml/
│   └── renderer/
├── tests/
└── pyproject.toml
```

## Architecture

- **API communicates via WebSocket** for real-time game events (narration, state updates)
- **Small REST surface** for save/load, character listing, genre pack metadata
- **Claude CLI (`claude -p`)** for all LLM calls — subprocess, not SDK
- **Genre packs** live in `sidequest-content/genre_packs/` (single source of truth), loaded by the API from a configured path
- **Media daemon** (`sidequest-daemon`) stays in Python as a sidecar for image/audio generation
- **Save files** live at `~/.sidequest/saves/` (SQLite `.db` files, one per genre/world session) — not in the repo. See `.pennyfarthing/guides/save-management.md` for cleanup, inspection, and migration procedures

## Commands

```bash
# From orchestrator root:
just api-test          # Run Rust tests
just api-build         # Build Rust backend
just api-run           # Run API server (builds CLI tools first)
just api-lint          # cargo clippy -- -D warnings
just api-fmt           # cargo fmt
just api-check         # fmt + clippy + test (full gate)
just ui-dev            # Start React dev server
just ui-test           # Run frontend tests (vitest)
just ui-build          # Build frontend
just ui-lint           # Run frontend linter
just daemon-run        # Start media daemon with warmup
just daemon-test       # Run daemon pytest suite
just daemon-lint       # ruff check
just check-all         # api-check + ui-lint + ui-test
just tmux              # tmuxinator dev session (4 panes)
```
## Development Principles


<critical>

### No Silent Fallbacks
If something isn't where it should be, fail loudly. Never silently try an alternative
path, config, or default. Silent fallbacks mask configuration problems and lead to
hours of debugging "why isn't this quite right."

</critical>



<critical>

### No Stubbing
Don't create stub implementations, placeholder modules, or skeleton code. If a feature
isn't being implemented now, don't leave empty shells for it. Dead code is worse than
no code.
</critical>

<critical>

### Don't Reinvent — Wire Up What Exists
Before building anything new, check if the infrastructure already exists in the codebase.
Many systems are fully implemented but not wired into the server or UI. The fix is
integration, not reimplementation.
</critical>

<critical>

### Verify Wiring, Not Just Existence
When checking that something works, verify it's actually connected end-to-end. Tests
passing and files existing means nothing if the component isn't imported, the hook isn't
called, or the endpoint isn't hit in production code. Check that new code has non-test
consumers.
</critical>

<critical>

### Every Test Suite Needs a Wiring Test
Unit tests prove a component works in isolation. That's not enough. Every set of tests
must include at least one integration test that verifies the component is wired into the
system — imported, called, and reachable from production code paths.
</critical>

<information>
### Rust vs Python Split
If it doesn't involve operating LLMs, it goes in Rust. If it needs to run model inference
(Flux, ACE-Step — not Claude), use Python for library maturity. Claude calls go
through Rust as CLI subprocesses
</information>

<important>
## OTEL Observability Principle

Every backend fix that touches a subsystem MUST add OTEL watcher events so the GM panel
can verify the fix is working. Claude is excellent at "winging it" — writing convincing
narration with zero mechanical backing. The only way to catch this is OTEL logging on
every subsystem decision.

The GM panel is the lie detector. If a subsystem isn't emitting OTEL spans, you can't
tell whether it's engaged or whether Claude is just improvising.
</important>

