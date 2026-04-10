# Epic 35: Wiring Remediation II — Unwired Modules, OTEL Blind Spots, Dead Code

## Overview

Successor to Epic 26 (Wiring Remediation I). Discovered in the 2026-04-09 cross-repo
wiring audit: **eight fully-implemented API modules with zero production consumers,
15+ subsystems wired but invisible to the GM panel (no OTEL), and four dead UI
components.** The epic is about *integration*, not invention — every story closes a
gap between code that exists and code that is actually reachable from the production
dispatch path.

The canonical finding that motivated the epic: `patch_legality` (narrator state
validation) is fully built with OTEL attributes ready to emit, and it has **never
been called** from the production turn pipeline. It was a silent no-op for months.

**This epic must not create new debt.** Every story re-reads `CLAUDE.md` and enforces
the wiring rules. No stubs. No silent fallbacks. No half-wired features. Every wire
lands with an integration test that proves a non-test consumer exists.

## Background

### Why it exists

The SideQuest codebase has an unusually high rate of "built but unwired" features
because the project moved fast through a Python → Rust rewrite (sq-1 → oq-2) while
also decomposing monolithic crates into a 12-crate workspace. During that churn,
many modules were ported faithfully but never re-integrated into the new dispatch
pipeline. They compile. They test. They exist. They do nothing.

The cross-repo audit on 2026-04-09 found 8 such modules in the API alone. Four of
those had OTEL spans defined but never emitted, meaning the GM panel's lie-detector
function was blind to entire subsystems. Epic 35 is the remediation pass.

### The Epic 35 checklist (per-story gate)

Every story must close its gap with **all three** of these landing together:

1. **Wire** — the code is called from a production path, verified by grep for
   non-test consumers (per `feedback_wiring_checks.md` in memory).
2. **OTEL** — if the subsystem makes a decision, a `WatcherEvent` is emitted so the
   GM panel can see the decision happening (per `OTEL Observability Principle` in
   `CLAUDE.md`).
3. **Test** — at least one integration test exercises the non-test consumer end-to-
   end, not just the module in isolation.

### Progress snapshot (2026-04-10)

| Status | Count | Stories |
|--------|-------|---------|
| Done | 10 | 35-1, 35-2, 35-3, 35-4, 35-5, 35-7, 35-8, 35-9, 35-11, 35-13, 35-14 |
| Backlog | 5 | 35-6, 35-10, 35-12, 35-13, **35-15** (this story, relocated from 28-14) |
| Points done | 39 | Of 52 total |

Stories 35-13 and 35-14 closed `as_variation()` silent fallbacks in the audio
subsystem — a pattern the rest of the epic should watch for.

## Technical Architecture

### Scope

Cross-repo: `sidequest-api` (Rust, 12 crates), `sidequest-ui` (React/TS),
`sidequest-daemon` (Python media services), `sidequest-content` (YAML genre packs).
Most stories touch `sidequest-api` only — wiring is concentrated in the dispatch
pipeline and the OTEL watcher subsystem. UI-touching stories delete dead components
(35-11 done) or wire new display paths (none currently).

### Dispatch pipeline as integration point

The hot path for every turn flows through `sidequest-server/src/dispatch/mod.rs`
(3,022 LOC) and its submodules. Most wiring stories land there — they identify a
fully-built module in `sidequest-game` and add a call site in a `dispatch/*.rs`
handler. The dispatch layer is the "last mile" where unwired code becomes consumed
code.

### OTEL emission pattern

The Rust side uses `WatcherEventBuilder::new("subsystem", EventType)` to emit
structured events that surface on the GM panel. The Python daemon side uses
OTEL span attributes (e.g., `span.set_attribute("render.lora_path", ...)`) on
subprocess spans. Both matter, but the **Rust-side WatcherEvent is authoritative**
for GM panel visibility — daemon spans don't surface to the watcher WebSocket.

Rule of thumb: if a decision happens in Rust, emit a `WatcherEvent` in Rust. Don't
rely on the daemon's span to be visible.

### Constraints

- **No silent fallbacks.** If a config field is missing, fail loudly. Specifically:
  `Option::unwrap_or` with a hardcoded default is usually wrong unless the default
  is documented as the intentional contract (see `feedback_no_fallbacks.md`).
- **Verify wiring, not just existence.** Passing tests and existing files mean
  nothing if the code isn't reachable from a production path (`feedback_wiring_checks.md`).
- **Every story needs a wiring test.** Unit tests prove isolation; integration
  tests prove reachability (`CLAUDE.md` — "Every Test Suite Needs a Wiring Test").
- **Gitflow on subrepos.** `sidequest-api`, `sidequest-ui`, `sidequest-daemon`,
  `sidequest-content` all target `develop`, never `main` (`feedback_never_main_subrepos.md`).

## Planning Documents

- `CLAUDE.md` (project root) — wiring discipline, no stubs, OTEL principle
- `sidequest-api/CLAUDE.md` — quality rules, "no half-wired features"
- Sprint epic file: `sprint/epic-35.yaml` — story inventory and status
- Memory: `project_epic15_no_new_debt.md` — zero new debt rule for tech debt epics
- ADR-032 — genre LoRA style training (load-bearing for story 35-15)
- ADR-070 — MLX image renderer (load-bearing for story 35-15)
