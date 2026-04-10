# 35-11

## Problem

**Problem:** Two UI components — a narrative layout picker and a turn-mode badge — were built but never connected to anything. They sat in the codebase, untouched, doing nothing. **Why it matters:** Dead code is a liability. It confuses developers ("is this used?"), inflates test maintenance burden, and can mask real bugs by creating false confidence when tests pass for code that was never shipped.

---

## What Changed

Two small UI widgets were removed from the codebase entirely:

- **LayoutModeSelector** — a row of three buttons ("Scroll / Focus / Cards") that was supposed to let players switch how story text is displayed. It was fully built — styled, accessible, animated — but was never placed anywhere in the app. Players never saw it.
- **TurnModeIndicator** — a status badge that was supposed to show whether the game was in "Free Play," "Structured," or "Cinematic" mode, with a tooltip explaining what each means. Also fully built, also never shown to players.

Along with the components, the tests written specifically for them were removed. Tests for everything else — the actual layout behavior, persistent settings, narrative display — were preserved.

Total removal: **161 lines in, 2 lines out** (one small cleanup in App.tsx).

---

## Why This Approach

The simplest fix for dead code is deletion. These components had zero production consumers — verified by searching every file in the frontend. Leaving them in would have required maintaining their tests, keeping their dependencies current, and explaining them to every new contributor who wondered if they were supposed to be wired up somewhere. Deletion is unambiguous. If these features are needed later, they can be rebuilt from the commit history with full context.

---
