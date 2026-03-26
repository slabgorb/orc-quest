# 2-1

## Problem

**Problem:** The game had no server — no way for the browser client to connect, request data, or exchange real-time game events. Without a running server, every other feature is blocked. **Why it matters:** A server is the foundation everything else is built on. Until this exists, no player can connect, no game can start, and no team can test anything end-to-end.

---

## What Changed

Think of this like opening a restaurant. Before this work, there was a kitchen (the game engine) but no front door, no host stand, and no way for customers to come in.

We built the front-of-house:

- **A front door** (`/ws`) — players' browsers connect here and stay connected for the whole game session, receiving live updates as the story unfolds
- **A menu window** (`GET /api/genres`) — the browser can peek in and ask "what genre packs are available?" before anyone sits down
- **A bouncer** (CORS) — only the official game client at `localhost:5173` is allowed to connect; random websites cannot
- **A clean closing routine** (graceful shutdown) — when the server is told to stop, it finishes whatever it's doing before the lights go out; nothing gets cut off mid-sentence
- **A seating tracker** (connection management) — the server always knows exactly which players are connected and can broadcast a message to all of them at once

---

## Why This Approach

Three reasons this was built the way it was:

1. **WebSockets over polling.** A game narrator speaks in real time — the AI can start sending narration before it's done generating. WebSockets let the server push updates the instant they're ready, rather than waiting for the client to ask "are we there yet?" every second.

2. **One trait, not one implementation.** The server doesn't care how the game logic works internally — it talks to an abstract "game service." This means the server can be tested with a fake game engine and swapped for a real one without rewriting a line of server code. It's the same reason a restaurant POS system works whether the kitchen uses a grill or a fryer.

3. **Graceful shutdown from the start.** It would have been faster to skip this and just kill the process. But a live game server with active players needs to finish its sentences before going offline. Building this in now means player connections will never be severed mid-narration by a deploy.

---
