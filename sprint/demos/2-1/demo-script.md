# Demo Script — 2-1

**Total runtime: ~8 minutes**

---

**Slide 1 — Title (0:00–0:30)**
Open on the title slide. Say: "Today we're showing the server that powers every player connection in SideQuest. This is the foundation — nothing else in the roadmap works without it."

---

**Slide 2 — Problem (0:30–1:00)**
"Before this sprint, the game engine existed, but there was no way to reach it. No client could connect. No data could flow. We were a kitchen with no front door."

---

**Slide 3 — What We Built (1:00–2:00)**
Walk through the architecture diagram (see Diagram Source). Point to each component: front door (WebSocket), menu window (REST), bouncer (CORS), seating tracker (connection manager), and broadcast system.

---

**Scene 1: Start the server (2:00–3:00)**

Run in terminal:
```bash
cargo run --bin sidequest-server -- --genre-packs-path ./genre_packs --port 8765
```

Expected output (point to each line):
```
INFO sidequest_server: SideQuest Server listening addr=127.0.0.1:8765
```

**Fallback:** If cargo build is slow, show Slide 3 and narrate what would appear.

---

**Scene 2: Genre list endpoint (3:00–4:00)**

Run in a second terminal:
```bash
curl -s http://localhost:8765/api/genres | python3 -m json.tool
```

Expected output — point to the specific genre slugs and world names:
```json
{
  "mutant_wasteland": {
    "worlds": ["flickering_reach", "dust_meridian"]
  },
  "cosmic_horror": {
    "worlds": ["arkham_station"]
  }
}
```

Say: "This is the menu. The browser client hits this before the game loads to know which genre packs are installed."

**Fallback:** Show Slide 3, explain the JSON structure verbally.

---

**Scene 3: WebSocket connection (4:00–5:30)**

Run in terminal (requires `websocat` installed, or use the integration test):
```bash
cargo test --test server_story_2_1_tests ws_lifecycle -- --nocapture
```

Point to the test output showing:
- Connection established with a UUID player ID (e.g., `f3a2c1d0-...`)
- Valid message received and acknowledged
- Invalid JSON returns `{"type":"ERROR","payload":{"message":"..."}}`
- Connection closes cleanly

Say: "Every player gets a unique ID the moment they connect. Invalid messages don't crash the server — it sends back a friendly error and keeps going."

**Fallback:** Show the test source file on screen, walk through what each step does.

---

**Scene 4: Graceful shutdown (5:30–6:30)**

With server still running, press `Ctrl+C` in the server terminal. Show:
```
INFO sidequest_server: SIGTERM received, initiating graceful shutdown
INFO sidequest_server: Shutdown signal received
INFO sidequest_server: Server shut down cleanly
```

Say: "Three lines, clean exit. Any in-flight requests finish before the process ends. No dropped messages, no corrupted state."

**Fallback:** Show Slide 4, describe the oneshot channel pattern in plain terms.

---

**Slide 4 — Why This Approach (6:30–7:00)**
"WebSockets for live narration. A trait boundary so tests run without a real game engine. Graceful shutdown so deploys don't interrupt players. Each choice was made to keep future features easy to add."

---

**Roadmap slide (7:00–7:30)**
"This is the server. Next up: game session management, then full message dispatch, then the narrator itself."

---

**Questions (7:30–8:00)**

---
