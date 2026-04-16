# 36-2

## Problem

**Problem:** Five dispatch functions in the game server's connection layer had grown to accept between 15 and 34 individual arguments each — so many that Rust's code quality tool flagged them as violations. The `#[allow(clippy::too_many_arguments)]` suppression comment was the engineering team's way of writing "we know this is bad, fix it later."

**Why it matters:** Functions with that many arguments are fragile. One misplaced argument causes a silent bug, refactoring is risky, and reading the code is exhausting. As the server grows, every new piece of session state would have made these already unwieldy signatures even longer.

---

## What Changed

Imagine a function that takes 34 separate sticky notes as input. Every caller has to pass exactly the right note in exactly the right slot — if you swap two, the game breaks. This PR replaces those 34 sticky notes with five labeled envelopes. Each envelope has named compartments, so the caller fills in what they have by name, and the function opens the envelope to find what it needs.

Concretely, five functions across three files now accept one structured object each:

| Old | New |
|-----|-----|
| `dispatch_connect(29 args…)` | `dispatch_connect(ctx: ConnectContext)` |
| `start_character_creation(15 args…)` | `start_character_creation(ctx: ChargenInitContext)` |
| `dispatch_character_creation(34+ args…)` | `dispatch_character_creation(ctx: ChargenDispatchContext)` |
| `build_response_messages(N args…)` | `build_response_messages(ctx: ResponseContext)` |
| `emit_telemetry(N args…)` | `emit_telemetry(ctx: TelemetryContext)` |

The game logic inside every function is **identical** — only the packaging changed.

---

## Why This Approach

Long argument lists are a symptom of a missing abstraction. The data these functions need — session state, character data, shared infrastructure handles — naturally belongs together. Grouping it into named structs does three things at once:

1. **Eliminates a whole class of bugs.** Named fields can't be silently swapped the way positional arguments can.
2. **Unlocks future growth.** Adding a new piece of session state now means adding one field to a struct, not updating every call site in sequence.
3. **Restores the linter's ability to find real problems.** The `#[allow(clippy::too_many_arguments)]` suppressions were hiding actual quality signals. With those gone, the linter is telling the truth again.

This is a pure structural cleanup — no behavior changed, no new features added, no migration needed.

---
