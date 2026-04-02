# Demo Script — 21-4

**Total runtime: ~8 minutes**

**Scene 1 — The Problem (Slide 2: Problem) | 1:30**
Open the GM dashboard. Start a game session. Trigger a combat action. Point to the Claude tab — it shows the narration result, but the tool timeline is empty or sparse. Ask the audience: "How do we know the AI actually checked the combat rules? How do we know it didn't just make something up?" Answer: before this story, we didn't.

**Scene 2 — What We Built (Slide 3: What We Built) | 1:00**
Show the Mermaid architecture diagram. Walk through the flow: server receives `--otel-endpoint`, threads it into `ClaudeClientBuilder`, builder stamps 7 env vars onto every `Command` before launch. Point to the `CLAUDE_CODE_OTEL_FLUSH_TIMEOUT_MS=3000` card — this guarantees spans flush before the subprocess exits.

**Scene 3 — Live Config Demo (Slide 3, live terminal) | 2:00**
```bash
# Start the API server with OTEL endpoint configured
cargo run -p sidequest-server -- --otel-endpoint http://localhost:4318
```
Show the startup log confirming the endpoint is threaded through. Then:
```bash
# In a second terminal, watch OTEL collector receive spans
docker logs otel-collector -f --tail=20
```
Fallback if collector isn't running: switch to Slide 3 and show the pre-recorded screenshot of the collector receiving `claude.subprocess.duration` spans.

**Scene 4 — GM Dashboard Lights Up (Slide 3, browser) | 2:00**
Trigger a narration call from the UI. Switch to the GM dashboard Claude tab. Show the tool timeline populating in real time: `claude.send`, `claude.subprocess.spawn`, `claude.subprocess.exit`, with duration in milliseconds and token counts. Point to a specific span: "This 847ms call processed 1,203 tokens and invoked the combat agent — we can prove it engaged the rules."

**Scene 5 — Negative Case (Slide 4: Why This Approach) | 1:00**
```bash
# Start without the flag — verify clean behavior
cargo run -p sidequest-server
```
Show that no OTEL env vars appear on the subprocess (grep the process env). The dashboard Claude tab shows no spans — correct behavior, no noise, no errors.

**Scene 6 — Roadmap (Slide: Roadmap) | 0:30**
Hand off to roadmap slide.

---
