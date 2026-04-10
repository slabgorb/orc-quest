# 27-9

## Problem

**Problem:** After removing the voice-acting feature, the game's communication layer was still sending around empty envelopes labeled "voice data coming." The app's narration system was waiting for audio chunks that would never arrive, using a timer-based buffer designed for streaming audio that no longer existed.

**Why it matters:** Dead code in active pipelines is a liability — it makes the system harder to read, test, and change. More practically, any future developer (or AI agent) touching the narration system would have to understand and work around plumbing designed for a feature that no longer exists. The buffer watchdog timer in particular was an active time-bomb: it could fire in unpredictable scenarios and corrupt narration delivery.

---

## What Changed

Imagine a mailroom that was originally set up to receive packages in multiple small boxes, assemble them, and then deliver the complete package after a timer expired. Then the shipping company changed to only send complete packages in one box — but the mailroom still had all the assembly machinery running, waiting for the small boxes that would never come.

This story **tore out the mailroom assembly line**:

- Removed the `NarrationChunk` message type from the API — the server can no longer even send partial-narration signals
- Deleted the chunk accumulator and watchdog timer from the front-end app
- Simplified the "narration done" flush function from a complex multi-path flow to a single straightforward call
- Removed the matching TypeScript type definition so the compiler enforces the new contract
- Updated documentation to describe what the system actually does today, not what it did when TTS was alive

The narration system still works exactly the same from the player's perspective — text still arrives and state updates (HP, inventory, location) still apply atomically. The machinery delivering it is just cleaner.

---

## Why This Approach

**Remove the dead code entirely rather than leaving it dormant.** The alternative — leaving `NarrationChunk` in place but unused — creates a false affordance. Any agent or developer reading the protocol would assume the variant is live and design around it. The Rust compiler itself would stop enforcing exhaustive match coverage on a real enum variant.

**Atomic PR across both repos (API + UI).** The message type and its consumer are a matched pair. Removing one without the other would create a window where the type system lies — the UI would still import a type that the server can never produce. By merging both repos simultaneously, the contract is consistent at every point in git history.

**TDD workflow for a deletion story.** The red phase wrote tests asserting `NarrationChunk` is absent from the compiled binary and that the UI buffer has no chunk-accumulation paths. Green phase was simply making those tests pass by deleting the code. This is the correct way to use TDD for removals: the tests prove the absence, not just the presence.

---
