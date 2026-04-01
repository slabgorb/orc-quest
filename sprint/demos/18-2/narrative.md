# 18-2

## Problem

**Problem:** The State tab in the GM dashboard permanently displayed "Waiting for GameStateSnapshot event…" — it never showed any game data, no matter how many turns were played.

**Why it matters:** The State tab is the GM's primary tool for verifying that the game engine is doing real work. Without it, there's no way to confirm whether systems like combat, inventory, and NPC tracking are actually running — or whether the AI is just narrating convincingly while nothing changes under the hood. A broken State tab is a broken lie detector.

---

## What Changed

The game server was sending game state data correctly after every turn. The dashboard was receiving it correctly. But the dashboard had the wrong name written on the mailbox — it was waiting for mail addressed to `"state_transition"` when every envelope arriving from the server was addressed to `"game_state_snapshot"`.

One word, in one line of code, was changed to match what the server actually sends. The State tab now receives and displays every snapshot.

---

## Why This Approach

The root cause was a naming mismatch introduced during development — two teams (or two moments in time) used different names for the same concept. The server's name was correct and used consistently everywhere. The dashboard filter was the odd one out.

The right fix was the smallest possible change: correct the one place that had the wrong name. No architectural changes, no new abstractions. The entire data pipeline — server emit, WebSocket transport, dashboard reducer, State tab rendering — was already correct and working. Only the filter string was wrong.

Six automated tests were written to lock in the correct behavior before the fix was made, ensuring this exact class of mismatch cannot silently re-enter the codebase.

---
