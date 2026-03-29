# 13-8

## Problem

**Problem:** In a multiplayer game session, when players submit their actions and the game resolves a turn, the AI narrator is called once per player — instead of once per turn. Why it matters: each of those narrator calls produces a *different* story outcome. Players sitting at the same table hear different versions of what just happened, and the game's memory of the world gets overwritten multiple times with conflicting information, corrupting future narration.

---

## What Changed

Imagine four players all shout their moves at the same time. Before this fix, the game engine woke up four separate storytellers simultaneously and each one told a slightly different version of the story — then all four tried to update the same shared history book at once, scribbling over each other's entries.

The fix appoints a single storyteller per turn. The first narrator to "claim the mic" tells the story; the other three wait and receive the same finished narration. Everyone hears the identical outcome, and the history book gets one clean, accurate entry.

There was a second bug underneath this: even when only one narrator *should* have been called, it was reading the wrong notepad for player actions — looking at a shared session log instead of the turn's own collected actions. The fix points it at the correct source, so the narrator always knows exactly what everyone did.

---

## Why This Approach

The fix uses a concurrency primitive called a **lock** — essentially a "first come, first served" token. Whoever grabs the token runs the narrator; everyone else waits on a broadcast channel for the result to arrive. This pattern (elect one, broadcast to all) is the standard solution for this class of race condition. It's low overhead, requires no central coordinator, and doesn't slow down the players who aren't narrating — they proceed in parallel the moment the result is ready.

The alternative (serializing all handlers through a queue) would have introduced latency and a single point of failure. The atomic-election approach keeps the fast path fast.

---
