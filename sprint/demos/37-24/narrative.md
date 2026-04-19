# 37-24

## Problem

**Problem:** The AI narrator was describing enemy attacks, stealth checks, and trope activations convincingly — but with zero mechanical backing. The game engine had no way to prove whether those outcomes came from actual dice rolls and rule checks, or whether the AI was just making up plausible-sounding results. **Why it matters:** Players (especially mechanically-minded ones) lose trust in the game when they suspect the AI is winging it. A career GM can smell improvisation. Without proof that the mechanics fired, every dramatic moment is on thin ice.

---

## What Changed

Think of it like a restaurant adding a kitchen window. The food was already being made — but you couldn't see it. Now you can.

We added two "I actually ran the math" signals to the game engine:

1. **NPC Turn Signal** — Every time an enemy takes its turn (attacks, moves, acts), the engine now records a timestamped entry: what the NPC did, what rules governed it, and what the outcome was.

2. **Trope Handshake Signal** — Tropes are genre-specific story patterns (the ambush, the betrayal, the last stand). When one activates, the engine now logs the keyword that triggered it, the check that confirmed it, and the result.

A small indicator appears in the GM panel when these signals fire — a subtle confirmation that the mechanics engine, not the narrator's imagination, drove that outcome.

---

## Why This Approach

The AI narrator is very good at sounding like it ran the numbers even when it didn't. The only reliable defense against this is mandatory logging at the mechanical decision point — not after the fact, not inferred from narration, but at the exact moment the engine fires.

We chose the lightest possible UI footprint (a small panel indicator, not a full overlay) because the goal is a confidence signal for the GM, not a stats dashboard that breaks immersion for players. The logging format matches the existing telemetry system, so it integrates with the GM panel the team already knows.

---
