---
parent: context-epic-1.md
---

# Story 1-12: Server — Axum Router, WebSocket, Genres Endpoint, Service Facade, Structured Logging

## Business Context

This is the story that makes the engine accessible. Without a server, all the game logic is
a library nobody can use. The axum router exposes WebSocket for real-time gameplay and REST
for metadata. The service facade pattern (calling GameService from 1-11, never game internals
directly) is the architectural boundary that prevents the coupling mess Python accumulated.
Structured logging with tracing gives operational visibility.

This is the top of the dependency chain — it wires all 5 crates together for the first time.

**Python sources:**
- `sq-2/sidequest/server/app.py` — GameServer with aiohttp WebSocket (1177 lines)
- `sq-2/sidequest/server/session_handler.py` — character selection, recap delivery
- `sq-2/sidequest/server/cli.py` — server startup (55 lines)

## Technical Guardrails

- **Port lesson #1 (CRITICAL — server/orchestrator coupling):** Server calls `GameService`
  trait methods ONLY. Never `orchestrator.state.characters[0].hp`. The trait is defined in
  story 1-11. Server depends on the trait, not the implementation
- **Port lesson #12 (structured logging):** Configure `tracing-subscriber` with structured
  JSON output. Every request gets a span with `component`, `operation`, `player_id`
- **ADR-003 (Session as Actor):** One tokio task per WebSocket connection. Task owns a
  `Session` struct. Communication via `tokio::sync::mpsc`
- **ADR-026 (Client State Mirror):** state_delta piggybacked on narration messages
- **ADR-027 (Reactive State Messaging):** broadcast to all connected sessions

### Python → Rust Translation

| Python (aiohttp) | Rust (axum) |
|---|---|
| `GameServer` class with mutable state | `AppState` in `Arc`, routes as functions |
| `handle_ws(request)` | `async fn ws_handler(ws: WebSocketUpgrade)` |
| `self.clients: dict[str, WebSocket]` | `DashMap<PlayerId, mpsc::Sender>` |
| `broadcast_to_clients()` | `broadcast::Sender<GameMessage>` |
| `_processing` set (action gate) | Scoped `ProcessingGuard` pattern (insert on create, remove on drop) |
| `_init_orchestrator()` (lazy) | Initialized at startup, shared via `Arc` |
| Silent broadcast failures | Log every failure before evicting |

### Session Lifecycle

1. Client opens WS → server spawns tokio task, assigns PlayerId
2. Client sends `SESSION_EVENT { event: "connect" }` → server loads/creates session
3. If no character → character creation flow
4. Game loop: `PLAYER_ACTION` → `GameService::handle_action()` → response messages
5. Client disconnects → task cleans up, session persisted

### CLI Args (clap derive)

- `--port` (default 8765)
- `--genre-packs-path` (path to genre pack YAML directory)
- `--save-dir` (optional, default `~/.sidequest/saves`)

### Server Module Structure

```
sidequest-server/src/
├── main.rs     — tokio::main, clap, tracing setup, startup
├── router.rs   — axum Router assembly (/ws, /api/genres, static)
├── ws.rs       — WebSocket upgrade, message dispatch, processing gate
├── session.rs  — Per-connection Session struct, state machine
├── genres.rs   — GET /api/genres handler
└── state.rs    — AppState struct with shared config
```

## Scope Boundaries

**In scope:**
- axum Router with routes: `GET /api/genres`, WebSocket upgrade at `/ws`
- WebSocket handler dispatching GameMessage to GameService
- Session lifecycle (connect, character selection, game loop, disconnect)
- Processing gate (prevent concurrent actions from same player)
- Broadcast via tokio channels
- CORS middleware (`tower-http::cors` for dev — allow localhost:5173)
- Structured tracing with request spans
- CLI args via clap
- Graceful shutdown (SIGTERM → close connections, flush saves)

**Out of scope:**
- Game logic (behind GameService facade)
- Agent orchestration (behind GameService facade)
- TTS/audio streaming (daemon territory)
- Static file serving for production (nice-to-have)
- Multiplayer shared orchestrator (future — single-player first)
- HTTPS/TLS (reverse proxy handles this)
- Character creation agents (future story)

## AC Context

| AC | Detail |
|----|--------|
| Server starts | `cargo run` binds to configured host:port with tracing output |
| REST endpoint | `GET /api/genres` returns genre pack summaries as JSON |
| WebSocket works | Client connects, sends GameMessage, receives response |
| Service facade | Server calls GameService trait, never accesses game state directly |
| Session lifecycle | Connect → character select → game loop → disconnect |
| Processing gate | Double-submit returns ERROR, not duplicate processing |
| Structured logging | Spans with component/operation/player_id on every request |
| CORS | Cross-origin requests from React dev server allowed |
| Graceful shutdown | SIGTERM closes connections cleanly, flushes saves |

## Assumptions

- axum 0.8's WebSocket support is mature enough for the use case
- GameService trait from 1-11 provides sufficient API surface
- Single-player is first target; `Arc<RwLock<>>` multiplayer deferred
- Python's app.py is 1177 lines; Rust server should be ~300-500 lines (no media pipeline)
