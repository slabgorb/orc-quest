# Epic 38: Dogfight Subsystem — Sealed-Letter Fighter Combat via StructuredEncounter

## Overview

Extend `StructuredEncounter` with a `SealedLetterLookup` resolution mode for simultaneous-commit fighter combat. Ace of Aces inspired mechanic: two pilots commit maneuvers secretly, cross-product lookup resolves outcome. Reuses TurnBarrier (Epic 13), unified narrator (ADR-067), and confrontation engine (ADR-033). No new parallel subsystem — additive extensions only.

**Priority:** P2
**Repos:** api, content
**Stories:** 10 (5 completed, 5 remaining — 10 points remaining)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **ADR-077** (`docs/adr/077-dogfight-subsystem.md`) | Full architectural decision — extensions, content plumbing, narrator integration, OTEL spans, implementation order |
| **ADR-033** (`docs/adr/033-confrontation-engine-resource-pools.md`) | Parent decision — StructuredEncounter unification, ConfrontationDef schema |
| **ADR-067** (`docs/adr/067-unified-narrator-agent.md`) | Narrator contract — no specialist agents, prompt extension only |
| **ADR-028** (`docs/adr/028-perception-rewriter.md`) | Per-player view filtering — perception_filters on SharedSession |

## Background

### The gap

Space opera ships `ship_combat` — a capital-ship confrontation where crew make collective decisions and the narrator selects beats against a shared engagement metric. That model does not cover **fighter-class single-seat dogfighting**, where two pilots each commit a hidden maneuver per turn and the resolution emerges from the cross-product of their choices. X-wing vs. TIE, Rocinante corvette vs. stealth interceptor — these encounters have a fundamentally different decision shape: per-pilot secret commits, cross-product lookup, per-actor state descriptors.

### Content-validated design

The dogfight mechanic was paper-validated before any code was written. The GM agent authored content files in `sidequest-content/genre_packs/space_opera/dogfight/`:

- `descriptor_schema.yaml` — per-pilot scene descriptor (8 MVP fields: bearing, range, aspect, closure, energy, gun_solution, environment, narration_style)
- `maneuvers_mvp.yaml` — 4-maneuver MVP menu (straight, bank, loop, kill_rotation) with rock-paper-scissors class balance
- `interactions_mvp.yaml` — 16-cell `(red_maneuver, blue_maneuver)` lookup table with per-pilot descriptor deltas and narration hints
- `pilot_skills.yaml` — 4-tier forward-capture (Rookie → Ace) aligned to existing affinity thresholds
- `playtest/duel_01.md` — paper playtest scaffold with commit/reveal/narrate protocol

### Architectural decision

ADR-077 evaluated and rejected four alternatives (parallel DogfightEngine, merge into ship_combat, pure content-only narrator resolution, dedicated Pilot class). The only viable path is **specialization of StructuredEncounter** via additive extensions that leave all existing confrontation types untouched.

### Completed foundation (38-1 through 38-5)

The engine plumbing is shipped and merged:

| Story | What shipped | Key files |
|-------|-------------|-----------|
| 38-1 | `ResolutionMode` enum + `resolution_mode` field on `ConfrontationDef` | `sidequest-genre/src/models/rules.rs` |
| 38-2 | `per_actor_state` on `EncounterActor` + serde round-trip tests | `sidequest-game/src/encounter.rs` |
| 38-3 | TurnBarrier confrontation-scope verification | `sidequest-server/src/dispatch/` |
| 38-4 | `_from:` file loader pattern for interaction tables | `sidequest-genre/` loader + tests |
| 38-5 | `SealedLetterLookup` resolution handler — match arm, barrier integration, OTEL spans | `sidequest-server/src/dispatch/sealed_letter.rs` |

### Remaining work

The 5 remaining stories cover the **content and narrator layer** — the ADR's content-side parallel work plus the narrator integration:

- **38-6**: Narrator cockpit-POV prompt extension (the wire from engine to narrator)
- **38-7**: Hit severity column in interaction table (content: damage model)
- **38-8**: Extend-and-return rule (content/engine: multi-exchange reset)
- **38-9**: Paper playtest calibration (validation: cell balance tagging)
- **38-10**: Tail-chase starting state (content: proving generalizability)

## Technical Architecture

### Engine extensions (shipped)

```
StructuredEncounter
├── ConfrontationDef
│   ├── resolution_mode: ResolutionMode  ← 38-1
│   ├── commit_options: Vec<String>       ← 38-4
│   └── interaction_table: InteractionTable ← 38-4
└── EncounterActor
    └── per_actor_state: HashMap<String, Value> ← 38-2

ResolutionMode::SealedLetterLookup handler  ← 38-5
├── Gathers commits via TurnBarrier (Epic 13 infrastructure)
├── Looks up (actor_a_commit, actor_b_commit) in interaction_table
├── Applies per-actor deltas to per_actor_state
└── Emits OTEL spans (dogfight.cell_resolved, etc.)
```

### Content files (space_opera/dogfight/)

| File | Purpose | Status |
|------|---------|--------|
| `descriptor_schema.yaml` | Per-pilot scene descriptor schema (8 MVP fields) | Authored |
| `maneuvers_mvp.yaml` | 4-maneuver menu with RPS class balance | Authored |
| `interactions_mvp.yaml` | 16-cell lookup table with deltas + narration hints | Authored, needs hit_severity (38-7) |
| `pilot_skills.yaml` | 4-tier forward-capture | Forward-capture only |
| `playtest/duel_01.md` | Paper playtest scaffold | Authored, needs calibration runs (38-9) |

### Narrator integration path (38-6)

The unified narrator (ADR-067) receives per-actor `per_actor_state` and the cell's `narration_hint`. System prompt extensions teach cockpit-POV rendering. Each pilot gets a private narration block via `SharedSession.perception_filters`. No new specialist agent.

### Key existing infrastructure reused

| Need | Infrastructure | Location |
|------|---------------|----------|
| Encounter container | `StructuredEncounter` | `sidequest-game/src/encounter.rs` |
| Commit-and-reveal | `TurnBarrier` | `sidequest-server/src/dispatch/` |
| Per-player views | `perception_filters` | `sidequest-server/src/shared_session.rs` |
| Genre YAML loading | Genre pack loader + `_from:` pattern | `sidequest-genre/` |
| Observability | OTEL span infrastructure | `sidequest-telemetry/` |

## Cross-Epic Dependencies

**Depends on:**
- Epic 13 (Sealed-letter multiplayer turns) — provides `TurnBarrier` commit infrastructure
- Epic 28 (StructuredEncounter unification via ADR-033) — provides the confrontation engine all extensions build on

**Depended on by:**
- No downstream epics currently — this is a new subsystem. Once shipped, any genre can declare a `SealedLetterLookup` confrontation type (low_fantasy dragon duel, victoria airship combat, neon_dystopia mech duel).
