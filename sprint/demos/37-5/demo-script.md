# Demo Script — 37-5

**Total runtime: ~8 minutes**

---

**Scene 1 — Title (0:00–0:30)**
*Slide 1: Title*
Open with: "This is a two-line fix that took down semantic memory for an entire playtest. Let me show you what happened."

---

**Scene 2 — The Problem (0:30–2:00)**
*Slide 2: Problem*
Show the GM panel screenshot from April 12 playtest. Point to the "Unknown error" toast notification that appeared during scene transitions. Explain: "Every time the narrator needed to recall prior events — rooms explored, deals made, items found — the memory lookup failed silently. The AI was narrating blind."

If you have the OTEL telemetry log, show the embed worker span with `error: ""` (empty string) as the failure payload.

**Fallback:** Skip live OTEL, stay on Slide 2, describe the symptom verbally.

---

**Scene 3 — What We Built (2:00–4:30)**
*Slide 3: What We Built*
Open two side-by-side terminal windows.

**Window 1 — Python fix:**
```bash
cd ~/Projects/sidequest-daemon
git diff HEAD~1 sidequest_daemon/media/daemon.py
```
Point to the single changed line:
```python
# Before:
error_msg = str(e)
# After:
error_msg = str(e) or f"{type(e).__name__} (no message)"
```
Say: "That's it. One line. The empty string was tunneling through three layers of infrastructure and appearing as 'Unknown error' in the GM panel."

**Window 2 — Rust fix:**
```bash
cd ~/Projects/sidequest-api
git diff HEAD~1 crates/sidequest-daemon-client/src/types.rs
```
Point to: `workers: serde_json::Value` replacing `workers: u32`.

**Fallback:** If git diff doesn't display cleanly, show Slide 3 with the before/after code blocks.

---

**Scene 4 — Test Coverage (4:30–6:30)**
*Slide 4: Why This Approach*
```bash
cd ~/Projects/sidequest-daemon
python -m pytest tests/test_embed_endpoint_story_37_5.py -v 2>&1 | tail -20
```
Expected output: `35 passed` — all green.

Point to the key test: `test_embed_error_message_is_not_empty` — this is the regression guard. It directly reproduces the April 12 failure condition.

**Fallback:** Show the test results table from the session file (35/35 passing).

---

**Scene 5 — Live Embed Request (6:30–7:30)**
*Slide 3: What We Built (reference again)*
```bash
# With daemon running:
curl -X POST http://localhost:8765 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"embed","params":{"text":"dark cavern with glowing runes"},"id":1}'
```
Expected: JSON response with `"embedding": [0.042, -0.117, ...]` (384-dimensional vector).

**Fallback:** If daemon isn't running, show the expected response on Slide 3.

---

**Scene 6 — Wrap (7:30–8:00)**
*Slide: Roadmap*
"The semantic search pipeline is now healthy. Future work will clean up three sibling error handlers with the same vulnerability pattern — that's a one-story cleanup already in the backlog."

---
