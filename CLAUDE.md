# CLAUDE.md — SideQuest (Rust Rewrite)

This is the orchestrator repo for the SideQuest RPG Runner/Editor It coordinates four subrepos:
- **sidequest-api** — Rust game engine and WebSocket API (workspace with 12 crates)
- **sidequest-ui** — React/TypeScript game client
- **sidequest-daemon** — Python media services (image gen, audio)
- **sidequest-content** — Genre packs (YAML configs, audio, images, world data)

## Who This Is For

SideQuest is built for a specific, real-world gaming group — not abstract personas. Design decisions should be weighed against these actual humans.

### Primary audience: Keith's playgroup

This is the group the game is *actually for*. Features must serve this group. If a decision trades playgroup quality for household reach, the playgroup wins.

- **Keith** — The builder, and the *forever-GM who finally wants to play*. Tarn-from-Dwarf-Fortress model: ~60% for himself, 40% for others. Senior architect, 40 years of tabletop, almost all of it behind the screen. Hits every axis — narrative *and* mechanical, high reading tolerance, fully bought in. **This is the single most load-bearing fact about the project:** SideQuest exists because Keith has been running games for four decades and wants the experience of being a player without losing the depth, agency, and surprise that a good human DM provides. Every design decision should ask "does this deliver a real player experience to someone who knows exactly what a good DM does?" The narrator must be *good enough to fool a career GM* — not just entertaining, but genuinely responsive, genre-true, and capable of surprising him. If the system can satisfy Keith-as-player, it can satisfy anyone.
- **James** (27, Keith's son) — Long-time playgroup member. Strong reader, narrative-first roleplayer. Played "Rux" in the Sunday caverns_and_claudes session — that save file is reference data for how he engages.
- **Alex** (playgroup) — Slower reader and typist; sometimes freezes when asked to roleplay under time pressure. Loves the game when paced inclusively. **Design implication:** sealed-letter turns, no fast-typist monopolies, generous response windows.
- **Sebastien** (Keith's nephew, ~James's age) — Plays on and off. The only **mechanics-first** player in the group — wants to know the rules, the numbers, how the system works. **Design implication:** the GM panel, OTEL visibility, and rule transparency aren't debug tools, they're a *feature* for Sebastien.

### Aspirational audience: the household

Nice-to-have, not load-bearing. If they never play, SideQuest is still a success. Don't bend primary-audience features to chase these users.

- **Sonia** (Keith's partner, lives with Keith) — The `victoria` genre pack is a love letter to her, not a feature gate. Has a nerd-force-field from years of living with nerds. Keith will live if she never plays.
- **Antonio & Pedro** (Sonia's sons, late 20s, share the household with Keith and Sonia as adults — Keith is not a parental figure to them) — Low reading tolerance, Pedro especially. Antonio is AI-skeptical and has his own playgroup; one of them is an artist. If visual/voice features happen to land for them, great — but don't compromise playgroup pacing or narrative depth to court them.

### Player-style axes

- *Narrative vs mechanical:* James/Alex narrative-first; Sebastien mechanical-first; Keith both.
- *Reading tolerance:* Keith/James high; Sebastien/Alex medium; household low.
- *RPG buy-in:* Keith/James/Sebastien/Alex committed; household ranges from skeptical to resistant.

### Using this rubric

When evaluating a feature, ask *which of these people it serves and which it loses.* Default to the playgroup. "Would Alex feel rushed by this?" and "Does Sebastien have enough mechanical visibility here?" are sharper design questions than "is this good UX?" Don't let aspirational users drag primary-audience decisions.

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

