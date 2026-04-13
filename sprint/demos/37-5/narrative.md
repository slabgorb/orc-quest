# 37-5

## Problem

**Problem:** During the April 12 playtest, the AI's semantic memory lookup was completely broken — every time the game needed to recall relevant lore, locations, or prior events, the underlying search service silently failed and returned an unhelpful "Unknown error" message with no details.

**Why it matters:** SideQuest's narrator AI uses semantic search (called RAG — Retrieval Augmented Generation) to pull relevant context before generating story beats. When this system is down, the AI narrates without memory — it can't recall that a character already explored a dungeon wing, that a deal was struck with an NPC, or that a specific item was collected three sessions ago. The story loses continuity. The entire April 12 playtest session ran with degraded narrative coherence as a result.

---

## What Changed

Imagine you have a customer service rep who, when they run into a problem, is supposed to say "I can't help because the database is offline." Instead, they go silent — they open their mouth, say nothing, and the customer stares at a blank screen.

That's exactly what was happening. When the memory-lookup service (called the "embed endpoint") hit an error, Python's error reporting produced a completely empty error message. The error got transmitted to the game engine as a blank string, and the game engine had no idea what to show — so it displayed "Unknown error."

**Two small fixes were made:**

1. **Python daemon (1 line):** If an error message is empty, automatically substitute a meaningful fallback like `"RuntimeError (no message)"` so the game engine always receives something useful.

2. **Rust client (1 line):** A data type mismatch was discovered — the Rust game engine expected the memory service's status report to be a simple number, but the service was actually sending a structured object. The type was corrected to accept whatever the service sends, without breaking anything.

Both changes are single-line fixes. 35 automated tests were written to lock in the correct behavior.

---

## Why This Approach

The team chose minimal, surgical changes rather than redesigning the error handling system:

- **The infrastructure was correct** — the embed worker, the semantic search pipeline, and the Rust client were all properly built. Nothing needed to be rebuilt, only debugged.
- **Silent failures are worse than loud ones** — the original code let empty errors pass through undetected. The fix ensures errors always carry diagnostic information, even if the original exception provided none.
- **Forward-compatible typing** — instead of rigidly defining exactly what the status response looks like (which would break every time the daemon team adds a new worker type), the Rust side now accepts the response as-is and doesn't try to parse internal details it doesn't need.

The reviewer also flagged that three other error handlers in the same file have the same empty-message vulnerability. Those are logged for a follow-up cleanup story.

---
