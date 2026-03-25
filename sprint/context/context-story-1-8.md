---
parent: context-epic-1.md
---

# Story 1-8: Game State Composition — GameSnapshot, Typed Patches, State Delta, TurnManager, Session Persistence

## Business Context

This is the integration layer that turns isolated subsystems into a coherent game state.
GameSnapshot is what gets saved and loaded. Typed patches replace the Python god-object's
255-line `apply_patch()` method — the single worst piece of technical debt identified in
the audit. TurnManager sequences player/agent turns. Session persistence via rusqlite
enables save/load. This story makes the game "resumable."

**Python sources:**
- `sq-2/sidequest/game/state.py:120-155` — GameState field definitions
- `sq-2/sidequest/game/state.py:545-800` — `apply_patch()` (decompose, don't copy)
- `sq-2/sidequest/game/state_delta.py` — snapshot_state, compute_state_delta (91 lines)
- `sq-2/sidequest/game/turn_manager.py` — TurnManager barrier sync (108 lines)
- `sq-2/sidequest/game/session.py` — SessionManager save/load (175 lines)
- `sq-2/sidequest/game/persistence.py` — NarrativeLog JSONL (38 lines)

## Technical Guardrails

- **Port lesson #4 (decompose GameState):** GameSnapshot composes domain structs from 1-7.
  No 30-field god object. Each domain struct owns its mutations
- **Port lesson #11 (complete deltas):** Python's `snapshot_state()` only captures characters,
  location, quest_log. Rust version must snapshot ALL client-visible fields: combat, chase,
  NPCs, atmosphere, tropes, discovered regions
- **ADR-006 (Persistence — SQLite):** Use rusqlite. Schema: `game_saves` table (id,
  genre_slug, world_slug, state_json, metadata, created_at, updated_at) and
  `narrative_log` table (id, save_id, turn, agent, input, response, location, timestamp)
- **ADR-023 (Session Persistence):** Auto-save after every turn, atomic writes via SQLite transactions
- **ADR-026 (Client State Mirror):** Server piggybacks state_delta on narration messages
- **ADR-027 (Reactive State Messaging):** State changes broadcast to all connected sessions

### GameSnapshot Composition

```rust
pub struct GameSnapshot {
    pub genre_slug: String,
    pub world_slug: String,
    pub characters: Vec<Character>,
    pub npc_registry: NpcRegistry,
    pub location: String,
    pub time_of_day: String,
    pub quest_log: HashMap<String, String>,
    pub notes: Vec<String>,
    pub narrative_log: Vec<NarrativeEntry>,
    pub combat: CombatState,           // from 1-7
    pub chase: ChaseState,             // from 1-7
    pub active_tropes: Vec<TropeState>, // from 1-7
    pub atmosphere: String,
    pub current_region: String,
    pub discovered_regions: Vec<String>,
    pub discovered_routes: Vec<String>,
    pub last_saved_at: Option<DateTime<Utc>>,
}
```

### Typed Patch Decomposition

The 255-line `apply_patch(dict)` becomes per-domain typed patch application:
- `WorldStatePatch` applies to location, atmosphere, quest_log, notes, regions
- `CombatPatch` applies to CombatState
- `ChasePatch` applies to ChaseState
- Each domain struct has an `apply_patch(&mut self, patch: &XPatch)` method

## Scope Boundaries

**In scope:**
- `state.rs`: GameSnapshot struct composing all domain types
- `state.rs`: Typed patch application (decomposed `apply_patch`)
- `delta.rs`: StateSnapshot, StateDelta, `snapshot()`, `compute_delta()`
- `turn.rs`: TurnPhase, TurnManager with barrier semantics
- `persistence.rs`: rusqlite save/load/list, narrative log append/query
- `session.rs`: SessionManager, SaveInfo, session lifecycle

**Out of scope:**
- Domain struct definitions (story 1-7)
- WorldStatePatch struct definition (agent output type, story 1-11)
- WebSocket message broadcasting (story 1-12)
- Lore indexing (not in Rust port scope)
- Backup/restore versioning (nice-to-have, not MVP)

## AC Context

| AC | Detail |
|----|--------|
| GameSnapshot round-trips | Serialize to JSON and back, all fields preserved |
| StateDelta complete | Captures ALL client-visible changes (combat, chase, NPCs, etc.) |
| TurnManager barrier | Single-player: immediate. Two-player: waits for both |
| Persistence round-trip | Save to rusqlite, load back, assert equality |
| Narrative log | Append entries, load back in order |
| Auto-save atomic | Interrupted save preserves previous valid state (SQLite transactions) |
| last_saved_at | UTC timestamp set on every save |

## Assumptions

- 3 points may be tight for 5 deliverables — monitor scope during implementation
- Domain structs from 1-7 are clean and composable
- rusqlite schema is straightforward (saves table + narrative_log table)
- `tokio::task::spawn_blocking` wraps synchronous rusqlite calls
