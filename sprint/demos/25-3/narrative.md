# 25-3

## Problem

**Problem:** The `OverlayManager` component was responsible for too many things at once — it managed the settings panel *and* all the game data panels (character sheet, inventory, map, journal, knowledge). **Why it matters:** A component that does too many jobs becomes a liability. It's harder to test, harder to change, and harder to hand off. Any time you touched the settings overlay, you had to understand — and risk breaking — the character sheet logic, and vice versa.

---

## What Changed

Think of `OverlayManager` like a Swiss Army knife that someone kept using as a hammer. It worked, but it wasn't the right tool.

We replaced it with a purpose-built component called `SettingsOverlay`. It does exactly one thing: shows and hides the Settings panel. It handles the keyboard shortcut (Escape to close), the click-to-dismiss backdrop, and nothing else.

The character sheet, inventory, map, and journal panels — which were being funneled through `OverlayManager` for no good reason — were never actually the settings overlay's job. That data now flows directly where it belongs.

**Before:** 5 data props + settings props + overlay state all piped through one component.
**After:** 3 focused props (open, toggle, close) + settings content. Clean interface.

---

## Why This Approach

Single responsibility. Every well-designed component does one job well and hands off everything else. `OverlayManager` had accumulated responsibilities that weren't related to each other — it was a coordination point that created invisible coupling. If you wanted to change how the map panel worked, you were inside a component that also owned keyboard handling for settings. That's a maintenance trap.

The rename is also intentional signal: the *name* `OverlayManager` implied it owned all overlays. `SettingsOverlay` says exactly what it is. Future contributors won't misuse it by piling more responsibilities in.

The keyboard handling (Escape key, modifier key bypass, input field focus detection) is now local to the component that needs it — not mixed in with game data routing.

---
