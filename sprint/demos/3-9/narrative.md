# 3-9

## Problem

Problem: During playtesting, the team had no way to see what the game engine was actually doing in real time — when the narrator misfired, when a story beat was about to trigger, or when an entity reference silently failed, developers had to dig through server logs after the fact, slowing down iteration dramatically. Why it matters: Every minute spent hunting down a mystery bug in post-session log triage is a minute not spent improving the game, and subtle issues (like a missing prop or a trope stuck at 99%) could ship to players undetected.

---

## What Changed

We added a "GM Mode" panel — a debug overlay that slides in alongside the game screen and shows the engine's inner workings in real time, without touching the game itself.

Think of it like the instrument panel of an airplane: the pilots (developers and playtesters) can see altitude, airspeed, and warning lights at a glance, while passengers (players) see nothing but the cabin. The game UI is completely unchanged for normal users.

What's now visible in the panel:

- **Event Stream** — a turn-by-turn log of every subsystem that fired (narrator, intent router, creature smith, etc.) with color-coded severity: green for normal, orange for warnings, red for errors
- **Subsystem Activity** — a bar chart showing which AI agents ran most, by invocation count (e.g., "narrator: 5, intent_router: 4, creature_smith: 1")
- **Trope Timeline** — progress bars for every active narrative trope (e.g., "suspicion: 0.75 — approaching critical threshold"), turning amber when a trope is close to triggering a major beat
- **Game State Inspector** — a live snapshot of the full game state: character stats, current location, combat status, quest log
- **Validation Alerts** — flagged problems, like `entity_ref: "rusty lockbox" not found — Turn 2`, so nothing silently fails

To open it: press **Ctrl+Shift+G** during any session, or add `?gm=true` to the URL before loading.

---

## Why This Approach

The panel is invisible to players by design — it only loads its code when a developer activates it, so it adds zero weight to normal gameplay sessions. Each section can be individually collapsed or expanded so a developer can focus on just the trope timeline or just the alert feed without clutter.

It reads directly from the same data stream the game engine already sends, so there's no extra API surface, no separate server, and no risk of the debug view going out of sync with what's actually happening. The panel is an observer, not a participant — it can never accidentally change game state.

---
