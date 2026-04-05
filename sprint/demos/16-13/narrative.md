# 16-13

## Problem

**Problem:** Every genre in SideQuest has its own resources — a gunslinger's Luck, a cyberpunk's Humanity, a detective's Heat on the streets, a road warrior's Fuel. The backend tracked all of these, but players had no way to see them. The UI was blind to resource state entirely.

**Why it matters:** Resource management is core to genre identity. When your Luck hits zero in a spaghetti western, or your Humanity drops past 50 in a neon dystopia, something consequential happens. If players can't see that creeping decline in real time, the genre mechanics have no dramatic weight — they might as well not exist.

---

## What Changed

We built a single, smart component called `GenericResourceBar` that can display *any* resource in the game — regardless of genre. Hand it a resource name, a current value, and a maximum, and it renders:

- A progress bar showing how full the resource is
- Visual markers on the bar showing the danger thresholds (e.g., "Humanity below 50 is bad, below 25 is worse")
- A color scheme that shifts to match the genre's visual identity
- A pulse animation and a toast notification the moment a threshold is crossed
- An audio sting that fires on threshold crossing for visceral feedback

The same component that shows a gunslinger's Luck (0–6) also shows a cyberpunk's Humanity (0–100) — the component adapts to whatever the genre defines.

---

## Why This Approach

Genre packs are data-driven: each one declares its own resources in a config file with its own bounds, thresholds, and flavor. Building one bespoke UI component per resource (LuckBar, HumanityBar, HeatBar...) would mean rewriting the same visual logic eight times and hardcoding assumptions that belong in the content layer.

The `GenericResourceBar` approach keeps the contract simple: the component only knows "name, value, max, thresholds." Everything genre-specific — color palette, label text, threshold values — lives in the genre pack data and flows in through props. Adding a brand-new resource to a new genre pack requires zero UI code changes.

Threshold crossings are the most emotionally loaded moments in resource management. Wiring in a toast, a CSS pulse animation, and an audio sting at the same crossing point means the player gets visual + auditory confirmation simultaneously — no missed signals.

---
