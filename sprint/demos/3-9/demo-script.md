# Demo Script — 3-9

**Total runtime: ~8 minutes**

**Slide 1: Title** — Introduce Story 3-9. "Today we're shipping the GM Mode debug panel — real-time engine telemetry, side by side with the game."

---

**Scene 1 — The Problem (Slides 1–2, 0:00–1:30)**

Walk to Slide 2. Set the scene: "Before this, if the narrator misfired on Turn 3, we found out by reading server logs after the session. There was no way to watch the engine think."

Show the blank game screen. Point out there is nothing to help a developer understand what's happening beneath the surface.

*Fallback if live game is unavailable: stay on Slide 2 and use the screenshot of the empty game UI.*

---

**Scene 2 — Activating GM Mode (Slide 3: What We Built, 1:30–3:00)**

With the game running in a browser, press **Ctrl+Shift+G**.

The 400-pixel-wide dark panel slides in on the right. Show the header: "GM Mode — Connected" in green.

Point out each section label: Event Stream, Subsystem Activity, Trope Timeline, Game State Inspector, Validation Alerts.

*Fallback: switch to Slide 3 which has a labeled screenshot of the panel.*

---

**Scene 3 — Event Stream and Alerts (Slide 3, 3:00–5:00)**

In the Event Stream, show Turn 1 events: "narrator: invoked (green), intent_router: exploration (green)."

Show Turn 2: "entity_ref: 'rusty lockbox' not found (orange warning)."

Scroll to Validation Alerts: show the entry `⚠ entity_ref: "rusty lockbox" not found — Turn 2`.

Say: "That's an item reference that the game engine couldn't resolve. Without this panel we would have never noticed — the narration just silently skipped it."

*Fallback: Slide 3 screenshot with the alert section highlighted.*

---

**Scene 4 — Trope Timeline (Slide 3, 5:00–6:30)**

Point to the Trope Timeline. Show "suspicion: 0.75" — the bar is amber because it's above 70%, meaning the "suspicion" narrative arc is approaching a major story beat. Show "forbidden_love: 0.33" in blue, still early-stage.

Say: "A playtester can now watch this bar fill up in real time. When it turns amber, they know a dramatic scene is about to trigger. If it never moves, they know something is wrong."

*Fallback: use the Slide 3 trope timeline screenshot.*

---

**Scene 5 — URL Activation and Cleanup (Slide 4: Why This Approach, 6:30–8:00)**

Navigate to Slide 4. Show the URL bar: type `?gm=true` at the end of the address. Reload. Panel opens automatically — no keyboard shortcut needed, useful for sharing a pre-configured session link with a remote playtester.

Press **Ctrl+Shift+G** again. Panel closes. Game UI returns to full-width, completely unaffected.

Emphasize: "The panel code doesn't even load for regular players. Zero performance cost, zero risk of leaking debug information to the public."

---
