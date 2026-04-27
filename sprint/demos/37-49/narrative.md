# 37-49

## Problem

**Problem:** Forty-five automated tests were crashing before they could even run, blocked by a missing setup step in the test harness. **Why it matters:** When tests can't run, the team loses its safety net. Developers can't tell whether their changes break something, which slows down every feature that follows — including the ongoing multiplayer work.

---

## What Changed

Think of automated tests like a rehearsal before opening night. For rehearsals to work, you need stand-ins for props that are too expensive or fragile to use every day. One of those props — the 3D dice roller — uses a special loading system that tests don't know how to handle on their own.

The fix installs a "stand-in" for that prop in the shared rehearsal kit. Now, every test file that involves the dice roller automatically gets a lightweight substitute instead of crashing when it tries to load the real thing.

**Before:** The rehearsal director shows up and asks for the 20-sided die. Nobody's brought a prop. The whole rehearsal shuts down.

**After:** The rehearsal director asks for the die. A clearly-labeled cardboard replica is waiting in the prop box. The show goes on.

---

## Why This Approach

The problem was in one central place — the shared mock configuration — so fixing it once fixes all five affected test files simultaneously. Adding individual workarounds to each of the five files would have meant five places to maintain, and the next developer who added a sixth test involving dice would have hit the same wall all over again.

Fixing the root cause in the shared setup costs the same effort as patching two files and prevents the problem from recurring.

---
