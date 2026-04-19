# 39-1

## Problem

Problem: Threshold logic (the rules that decide when a character's health, stamina, or other resource crosses a meaningful boundary) was duplicated and scattered across unrelated parts of the codebase. Why it matters: Duplicated logic means bugs get fixed in one place but not the other, and adding new resource types requires hunting down every copy — a slow, error-prone process that compounds as the game grows.

---

## What Changed

Think of it like this: imagine the recipe for "how to know when a gas tank is dangerously low" was written out by hand inside both the car's dashboard code *and* the fuel pump code. If the threshold changed from 10% to 15%, you'd have to remember to update both places.

This refactor pulls that recipe into one shared file — `thresholds.rs` — and introduces a new data structure called `EdgePool` that cleanly describes any game resource: its current value, its maximum, its baseline maximum, what triggers recovery, and where the warning thresholds sit. Now every part of the engine reads from that single source of truth.

---

## Why This Approach

Rust rewards this pattern: define the shape of data once, write the logic that operates on it once, and let the compiler enforce that every consumer uses it correctly. The `EdgePool` struct is the canonical contract for "a resource that has thresholds." By isolating it in `sidequest-game/src/thresholds.rs` with its own unit tests, we get:

- **Compile-time safety** — any new resource type that doesn't satisfy the contract fails to build, not fails at runtime
- **Single point of change** — future threshold tuning (e.g., adding "bloodied" states) touches one file
- **Testability without the engine** — the logic runs without spinning up a game session

This is the standard "extract module" refactor — no new behavior, just better organization.

---
