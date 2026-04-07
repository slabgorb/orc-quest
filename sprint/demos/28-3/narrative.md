# 28-3

## Problem

**Problem:** When a confrontation scene started — a tense standoff, a fight, a social power struggle — the player saw the confrontation overlay on screen but had no buttons to click. The "beats" panel (the list of moves a player can make) was always empty, so players couldn't interact with the confrontation at all. **Why it matters:** Confrontations are the core of dramatic gameplay. Without beat buttons, the UI is a dead end during every combat and standoff — players are stuck staring at an inert screen instead of making choices.

---

## What Changed

Think of a confrontation like a poker hand. Each genre pack (Spaghetti Western, Space Opera, etc.) defines a menu of "moves" a player can make — in a Spaghetti Western standoff you might choose **Size Up**, **Bluff**, **Flinch**, or **Draw**. Those moves are called "beats."

Before this story, the game engine was shipping an empty beat list every time a confrontation started — the recipes existed in the genre pack files, but the kitchen wasn't reading them. This story wires the recipe book to the kitchen: when a confrontation starts, the server now looks up the correct genre definition, reads out every beat option with its label, stat check, and risk description, and sends all of that to the UI so the buttons appear. The GM panel also now gets a live log entry — `encounter.beats_sent` — confirming exactly which beats went out and how many, so you can verify the pipeline is working without guessing.

---

## Why This Approach

The beat definitions already existed in the genre pack YAML files and the data structures to hold them already existed in the protocol layer. Nothing needed to be invented — it just needed to be connected. The server now calls `find_confrontation_def()` at the moment it builds the confrontation message, maps each beat definition to the protocol shape, and attaches it. The fallback is safe: if a genre pack doesn't define beats for an encounter type, the list comes back empty the same way it always did — no breakage, no noise. The OTEL event was added as the verification layer so the GM panel can serve as a live "did it work?" check rather than relying on inference.

---
