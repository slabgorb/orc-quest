# Demo Script — 26-10

**Slide 1: Title** — set context, "this is a wiring story — the data existed, we connected the pipe."

**Slide 2: Problem** — [30 seconds] Explain the atlas analogy: the server had a complete world map in memory but stripped it out before sending anything to the browser. Show the "before" network message: just `current_location`, `region`, and `explored` — nothing structural.

**Slide 3: What We Built** — [60 seconds] Show the "after" WebSocket frame. Start a local server:

```bash
just api-run
```

Open browser devtools → Network → WS. Connect to a session. In the WebSocket messages, find a `MAP_UPDATE` frame and expand the payload. You will see:

```json
{
  "cartography": {
    "navigation_mode": "region",
    "starting_region": "shadowlands",
    "regions": {
      "shadowlands": { "name": "Shadowlands", "description": "...", "adjacent": ["brightmoor"] },
      "brightmoor": { "name": "Brightmoor", ... }
    },
    "routes": [
      { "name": "Old Road", "from_id": "shadowlands", "to_id": "brightmoor" }
    ]
  }
}
```

Point out that this fires on connect, on every player action, and on session restore — every time the UI would need to (re)draw a map.

**Fallback for Slide 3:** If the live server isn't available, switch to Slide 3 and show the screenshot of the WebSocket frame captured during QA.

**Slide 4: Why This Approach** — [30 seconds] Genre pack data was already in RAM. No new database calls. No new API endpoints. Three lines of attachment code per send site, plus the protocol types. Low cost, high leverage.

**Before/After Slide** — [30 seconds] Left: wire message with 3 fields. Right: wire message with `cartography` object containing named regions and routes. Same message, richer payload.

**Roadmap Slide** — [60 seconds] See Roadmap & Integration below.

**Questions** — open floor.

---
