---
story_id: "35-8"
jira_key: ""
epic: "MSSCI-16932"
workflow: "trivial"
---

# Story 35-8: OTEL watcher events for beat_filter and scene_relevance

## Story Details
- **ID:** 35-8
- **Jira Key:** (not set in sprint YAML)
- **Workflow:** trivial
- **Epic:** MSSCI-16932 (Wiring Remediation II)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-10T06:26:59Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-10T00:00:00Z | 2026-04-10T06:14:32Z | 6h 14m |
| implement | 2026-04-10T06:14:32Z | 2026-04-10T06:19:52Z | 5m 20s |
| review | 2026-04-10T06:19:52Z | 2026-04-10T06:26:59Z | 7m 7s |
| finish | 2026-04-10T06:26:59Z | - | - |

## Delivery Findings

No upstream findings.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

### Dev (implementation)
- No deviations from spec.

## Delivery Findings

### Dev (implementation)
- No upstream findings.

### Reviewer (code review)
- **Gap** (non-blocking): `beat_filter_story_4_3_tests.rs` and `scene_relevance_story_14_7_tests.rs` have no wiring test — all tests are pure unit tests of decision logic, with no assertion that `sidequest-server::dispatch::render.rs` actually calls through to these components. Affects `sidequest-api/crates/sidequest-game/tests/{beat_filter_story_4_3_tests.rs,scene_relevance_story_14_7_tests.rs}` (needs a `#[test]` that imports from `sidequest-server` dispatch path and asserts the subsystem is invoked). Production wiring IS verified present at `dispatch/render.rs:79` (SceneRelevanceValidator) and `dispatch/render.rs:106` (BeatFilter.evaluate), so this is test-debt, not a live wiring gap. Pre-dates story 35-8 — this diff is pure additive telemetry. *Found by Reviewer during code review.*

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 low-confidence | dismissed 1 (rationale below) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 high-confidence | confirmed 2 (both flagged as pre-existing test debt, non-blocking) |

**All received:** Yes (3 returned, 6 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 2 confirmed (pre-existing test debt, non-blocking), 1 dismissed (rationale), 0 deferred

### Dismissal Rationale

- **[SILENT] (low): `debug_assert!` guard on telemetry channel init** — dismissed. Finding suggests adding `debug_assert!(GLOBAL_TX.get().is_some(), ...)` inside `sidequest-telemetry::emit()` (`lib.rs:197`) as defensive hardening. This is a suggestion for a file NOT in the diff (`sidequest-telemetry/src/lib.rs`), the no-op-when-uninitialized behavior is explicitly documented as intentional in `sidequest-telemetry/CLAUDE.md`, and production startup order in `sidequest-server` guarantees the channel is initialized before dispatch. Not a bug — a defensive improvement out of this story's additive-telemetry scope.

## Devil's Advocate

If this code is broken, where does it break? Let me argue against it.

**Attack 1 — NaN/Infinity in narrative_weight.** `serde_json::json!(f32::NAN)` produces JSON `null` (or errors), potentially dropping telemetry silently. Rebuttal: `RenderSubject::new()` at `subject.rs:69` validates `(0.0..=1.0).contains(&narrative_weight)` at construction. Because NaN comparisons always return false, `contains()` returns false for NaN — construction rejects NaN. Any `RenderSubject` that survives construction holds a finite, bounded float. Attack vector closed at the type boundary.

**Attack 2 — The refactor silently dropped a suppression path.** Could `evaluate_inner` skip a return? Rebuttal: `git diff --stat` shows 61 additions, **0 deletions**. Every existing return path inside the body is preserved. I read the full `evaluate_inner` body and every previous return statement is still present, in the same order, with the same formatted reason strings. The diff moved code; it did not remove code.

**Attack 3 — `tracing::instrument` span divergence from OTEL field.** Tracing's `history_len` captures entry-time history_len; OTEL emission captures post-decision history_len. A debugger correlating spans to WatcherEvents might see a 1-unit discrepancy on Render decisions (because record_render incremented history between capture points). Rebuttal: this is intentional — OTEL reflects the post-decision state (what the GM panel cares about), tracing reflects the entry state (what the span entry saw). Both are correct; documenting either one alone would be accurate. Not a bug, a design choice worth a footnote.

**Attack 4 — `compute_verdict`'s `tracing::warn!` calls lost their parent span after the refactor.** The `#[instrument]` attribute is on `evaluate_with_override`, not on `compute_verdict`. Rebuttal: tracing spans propagate via thread-local current-span context. Calling `compute_verdict` synchronously from inside the instrumented `evaluate_with_override` means the warn!/info! calls emit within the parent's active span context. No span is lost.

**Attack 5 — Broadcast channel backpressure.** If the GM panel subscribes, then disconnects, and the broadcast buffer fills, does `.send()` block or drop? Rebuttal: `tokio::sync::broadcast::Sender::send()` is non-blocking; it returns `Err(SendError)` if there are no active receivers, and `Err(Lagged(n))` (via receive side) if slow consumers cause overflow. The sender-side error is explicitly discarded (`let _ = tx.send(event)` per `sidequest-telemetry/lib.rs:197`). This is fire-and-forget by design per the telemetry crate contract. Not a concern in an additive telemetry path.

**Attack 6 — A stressed filesystem or OOM condition.** `WatcherEventBuilder` allocates a `HashMap<String, Value>` and a few small Strings per call. Under severe allocator pressure, allocation could panic (Rust allocator default). Rebuttal: every Rust program has this attack surface on every heap allocation. It is not this story's responsibility to make telemetry allocation-free, and the overhead (~8 small allocations per decision) is negligible on a path that already allocates for the FilterDecision reason String and `format!("{:?}", ...)`.

**Verdict of devil's advocate:** No hidden bugs uncovered. The one subjective note (attack 3) is a documentation-only observation about OTEL vs tracing field semantics — worth logging as a LOW observation but not a correctness issue.

## Rule Compliance

Rule-checker enumerated 18 rules (15 lang-review + 6 additional project rules) across 47 instances in the diff. Results:

- **Rules 1–15 (lang-review/rust.md):** all pass. No silent error swallowing, all enums `#[non_exhaustive]`, no placeholder values, tracing preserved with correct severity, no trust-boundary constructors, no vacuous assertions, no unsafe `as` casts on user input (only `.count() as u32` on a bounded internal `VecDeque` — pre-existing, not introduced), no Deserialize bypass (neither type derives Deserialize), no public fields with invariants (all config fields private with getters, FilterContext booleans carry no invariant), no trait signatures needing tenant context, `sidequest-telemetry` correctly path-dep'd as workspace-internal, no dev-only deps misplaced, no Deserialize/new() divergence, no fix-introduced regressions (verified by zero deletions), no unbounded recursion.
- **A1 No Silent Fallbacks:** compliant — OTEL field values are real decision data, no fallback strings, `.send()` fire-and-forget is documented telemetry contract.
- **A2 No Stubbing:** compliant — `evaluate_inner` / `compute_verdict` contain the full prior logic, not skeletons.
- **A3 Don't Reinvent:** compliant — uses existing `WatcherEventBuilder` from `sidequest-telemetry`.
- **A4 Verify Wiring (non-test consumers):** compliant — `BeatFilter` instantiated at `sidequest-server/src/lib.rs:449`, `evaluate()` called at `dispatch/render.rs:106`; `SceneRelevanceValidator::new()` at `dispatch/render.rs:78`, `evaluate()` at `:79`. Verified by grep.
- **A5 Every Test Suite Needs a Wiring Test:** **VIOLATION (pre-existing)** — neither `beat_filter_story_4_3_tests.rs` nor `scene_relevance_story_14_7_tests.rs` contains a test asserting the server pipeline calls through. This test debt pre-dates story 35-8; the diff adds telemetry only. Captured in Delivery Findings, not blocking.
- **A6 OTEL Observability Principle:** compliant — both subsystems now emit StateTransition events with decision, reason, and context fields sufficient for the GM panel lie detector.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** Narration text → `SubjectExtractor` → `RenderSubject` → `dispatch/render.rs` builds `ExtractionContext` and `FilterContext` → `SceneRelevanceValidator::evaluate()` (emits scene_relevance_evaluated OTEL) → if approved, `BeatFilter::evaluate()` (emits beat_filter_evaluated OTEL) → if Render, queued to daemon. Both decision points are now visible to the GM panel. Safe because all telemetry fields derive from already-validated internal state; no user-controlled data reaches serialization without prior bounds-checking at `RenderSubject` construction.

**Pattern observed:** Outer-wrapper telemetry pattern (`evaluate` calls `evaluate_inner`, emits once, returns captured decision) at `beat_filter.rs:229-256` and `scene_relevance.rs:98-124`. Matches the `encounter.rs:394-408` pattern used elsewhere in the codebase for multi-exit-point decisions. Cleaner than embedding `.send()` calls at every early return; makes adding new decision branches safe-by-default for observability.

**Error handling:** No new error paths introduced. Telemetry `.send()` is fire-and-forget per `sidequest-telemetry` contract (verified at `lib.rs:197` — no-op when channel uninitialized, discards `broadcast::Sender::send()` error when no subscribers). Both are documented, intentional design choices.

**Wiring verification:** `sidequest-server/src/dispatch/render.rs:79` calls `validator.evaluate()`; `:106` calls `beat_filter.evaluate()`. Both are the production call sites. Confirmed via grep on `BeatFilter|SceneRelevanceValidator` excluding test files — only hits outside the subsystem files are `lib.rs:276,449-450` (AppState instantiation) and `dispatch/render.rs:78,106`. Production wiring is live.

### Observations

- [VERIFIED] All return paths in `BeatFilter::evaluate_inner` and `SceneRelevanceValidator::compute_verdict` flow through the wrapper's single OTEL emission point. Evidence: `beat_filter.rs:230-255` captures `decision` once, emits, returns; every early return in `evaluate_inner` (lines 262-335) lands back in the outer wrapper. Same structure at `scene_relevance.rs:104-123` / `compute_verdict` at `:127`. Pattern matches `encounter.rs:394-430` — complies with the OTEL Observability principle.
- [VERIFIED] Refactor is byte-for-byte structural. Evidence: `git diff --stat develop...HEAD` reports 61 additions, **0 deletions**. The entire prior `evaluate()` body is preserved inside `evaluate_inner` with identical return statements and reason strings. No logic was altered. Complies with the project rule against fix-introduced regressions.
- [VERIFIED] `FilterDecision` and `ImagePromptVerdict` remain `#[non_exhaustive]`. Evidence: `beat_filter.rs:22`, `scene_relevance.rs:19`. No new variants added; rule-checker confirmed no new pub enums introduced. Complies with lang-review rule 2.
- [VERIFIED] NaN/infinity cannot reach telemetry serialization. Evidence: `RenderSubject::new()` at `subject.rs:69` validates `(0.0..=1.0).contains(&narrative_weight)` at construction, which returns false for NaN (NaN comparisons are never true). Any `RenderSubject` that survives construction holds a finite bounded float. `serde_json::json!(f32)` is safe for finite values.
- [VERIFIED] Production wiring is live, not stubbed. Evidence: `sidequest-server/src/lib.rs:449` instantiates `BeatFilter::new(BeatFilterConfig::default())` inside AppState; `dispatch/render.rs:78-79` instantiates `SceneRelevanceValidator::new()` and calls `evaluate()`; `:100-106` locks the AppState `beat_filter` Mutex and calls `evaluate()`. Complies with the project's "wire, don't reinvent" rule.
- [VERIFIED] Tracing instrumentation preserved. Evidence: `#[tracing::instrument]` remains on `BeatFilter::evaluate` at `beat_filter.rs:220-225` and on `SceneRelevanceValidator::evaluate_with_override` at `scene_relevance.rs:92-97`. `compute_verdict`'s `tracing::warn!`/`info!` calls emit within the parent span via thread-local span propagation.
- [RULE] [MEDIUM] Wiring-test gap in `beat_filter_story_4_3_tests.rs` and `scene_relevance_story_14_7_tests.rs` — pre-existing. Neither file asserts that `dispatch/render.rs` invokes its subsystem. A future refactor silently unwiring either component would leave all 51 tests green. **Non-blocking** because: (a) the story's scope is additive OTEL only; (b) production wiring is verified present at `render.rs:79` and `:106`; (c) this test debt pre-dates story 35-8 and applies equally to the untouched `develop` tree. Captured in Delivery Findings — should be picked up as a separate 1-2pt chore under Epic 35 (Wiring Remediation II).
- [SIMPLE] [LOW] OTEL vs tracing field divergence on `history_len`. The `#[tracing::instrument]` on `BeatFilter::evaluate` captures `history_len` at function entry (pre-record), while the OTEL emission captures post-decision history_len (after record_render on Render paths). Intentional — OTEL reflects the state the GM panel cares about — but worth a one-line code comment if anyone hits confusion debugging span vs watcher-event correlation. Not blocking.
- [EDGE] `BeatFilter::evaluate_inner` force-render bypass paths (scene_transition, player_requested) call `record_render` before returning, while the rule-threshold and cooldown/burst/dedup paths do not. The OTEL emission therefore sees `history_len` incremented for force-render/Render decisions and unchanged for suppression decisions. This is the intended semantic and matches pre-refactor behavior (zero deletions confirms).
- [SILENT] Not a concern for this diff. The `WatcherEventBuilder::send()` no-op-when-channel-uninitialized is documented in `sidequest-telemetry/CLAUDE.md` and production guarantees initialization before dispatch. Defensive-hardening suggestion from the subagent dismissed (see rationale above).
- [TEST] No new tests required for an additive-telemetry refactor; the existing 51 tests (33 beat_filter + 18 scene_relevance) cover the decision logic and still pass. Test-debt flagged separately under [RULE].
- [DOC] Doc comments on the new `evaluate_inner` and `compute_verdict` helpers are present (`beat_filter.rs:258`, `scene_relevance.rs:126`) and accurate. The OTEL block has a 3-line rationale comment at both sites. No stale or misleading documentation.
- [TYPE] No type design changes. The refactor does not introduce new types, doesn't change visibility of existing types, doesn't alter trait implementations. The `(decision_str, reason)` destructuring tuple at `beat_filter.rs:234` and the `(verdict_str, reason)` tuple at `scene_relevance.rs:109` are local throwaways, not public API.
- [SEC] No security surface. Game engine telemetry on an internal decision path. No user input reaches serialization without type-level validation at `RenderSubject` construction. No tenant isolation concerns — this is a single-player/small-party game engine, not a multi-tenant SaaS.
- [SIMPLE] The outer-wrapper refactor is marginally more verbose than inlining `.send()` at each return, but it is the correct trade for maintainability. Adding a new suppression branch to `evaluate_inner` now automatically emits OTEL without the author having to remember — the kind of safe-by-default pattern the OTEL Observability rule exists to enforce.

**Handoff:** To Camina Drummer (SM) for finish-story.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-api/crates/sidequest-game/src/beat_filter.rs` — Added `WatcherEventBuilder` emission at end of `BeatFilter::evaluate()`. Refactored decision body into private `evaluate_inner()` helper so telemetry captures the post-decision state uniformly across all return paths. Fields: `action="beat_filter_evaluated"`, `decision` (render/suppress), `reason`, `subject_weight`, `in_combat`, `scene_transition`, `player_requested`, `history_len`.
- `sidequest-api/crates/sidequest-game/src/scene_relevance.rs` — Added `WatcherEventBuilder` emission at end of `SceneRelevanceValidator::evaluate_with_override()`. Refactored decision body into private `compute_verdict()` helper. Fields: `action="scene_relevance_evaluated"`, `verdict` (approved/rejected), `reason`, `entity_count`, `scene_type`, `in_combat`, `dm_override`.

**Pattern:** Followed `encounter.rs` `WatcherEventBuilder::new(component, StateTransition).field(...).send()` idiom. Both modules already had telemetry dep (`sidequest-telemetry = { path = "../sidequest-telemetry" }`).

**Wiring verified end-to-end:**
- `BeatFilter` instantiated at `sidequest-server/src/lib.rs:449` (AppState).
- `SceneRelevanceValidator` instantiated at `sidequest-server/src/dispatch/render.rs:78`.
- Both `evaluate()` calls live in production code at `render.rs:79` and `render.rs:106`. Non-test consumers confirmed via grep.

**Tests:** 51/51 passing (GREEN) — 33 beat_filter + 18 scene_relevance. No new tests required (additive telemetry; existing wiring tests cover both modules per story scope).

**Build:** `cargo build -p sidequest-game` clean (pre-existing doc warnings only, unrelated).

**Branch:** `feat/35-8-otel-beat-filter-scene-relevance` (pushed to origin, worktree at `/Users/keithavery/Projects/oq-1/sidequest-api-35-8`).

**Worktree note:** `sidequest-api` develop had pre-existing dirty state (TTS-cleanup edits across ~15 files). Per memory policy, used `git worktree add` off develop rather than disturbing Bossmang's in-progress work. Worktree will need cleanup after story finish.

**Handoff:** To review phase (Chrisjen Avasarala).

## SM Assessment

Trivial workflow — additive OTEL instrumentation only. Both `beat_filter.rs` and
`scene_relevance.rs` are fully wired and tested in `sidequest-game`. Scope is
strictly: emit `StateTransition` watcher events at existing decision points so
the GM panel can verify these subsystems are engaged (per CLAUDE.md OTEL
Observability Principle — subsystems without OTEL spans cannot be distinguished
from Claude improvising).

No new modules, no new tests, no structural changes. Follow the `encounter.rs`
watcher-event pattern. Handoff to Naomi (dev) for implement phase.

---

## Implementation Context

### Overview
Add OTEL watcher events (telemetry observability) to `beat_filter.rs` and `scene_relevance.rs`
in the `sidequest-game` crate. These subsystems are fully wired and functional, but emit
no OTEL events to the GM panel. The GM panel cannot currently verify whether these
subsystems are actually engaged or whether Claude is improvising image suppression decisions.

### Subsystems to Instrument

#### 1. beat_filter.rs (~322 LOC)
- **Location:** `sidequest-api/crates/sidequest-game/src/beat_filter.rs`
- **Primary Decision Point:** `BeatFilter::evaluate()` (lines 226-309)
- **Decision Type:** `FilterDecision::Render { reason } | FilterDecision::Suppress { reason }`
- **Context:** Suppresses low-narrative-weight image renders based on:
  - Weight threshold (combat-aware, lower during combat)
  - Cooldown timer (minimum time between renders)
  - Burst rate limit (max renders per window)
  - Duplicate subject suppression (time-bounded dedup)

**Watcher Events Needed:**
- When a render decision is made, emit `StateTransition` event with:
  - `action`: "beat_filter_evaluated"
  - `subject_weight`: narrative weight of the subject
  - `decision`: "render" or "suppress"
  - `reason`: the FilterDecision reason string
  - `in_combat`: whether combat is active
  - `context_scene_transition`: scene transition flag
  - `context_player_requested`: player-requested flag
  - `history_len`: current render history length

#### 2. scene_relevance.rs (~203 LOC)
- **Location:** `sidequest-api/crates/sidequest-game/src/scene_relevance.rs`
- **Primary Decision Points:** `SceneRelevanceValidator::evaluate()` (lines 79-128) and helpers
- **Decision Type:** `ImagePromptVerdict::Approved | ImagePromptVerdict::Rejected { reason }`
- **Context:** Validates art prompts against scene state (NPCs present, location, combat status)

**Watcher Events Needed:**
- When a verdict is made, emit `StateTransition` event with:
  - `action`: "scene_relevance_evaluated"
  - `entity_count`: number of entities in prompt
  - `verdict`: "approved" or "rejected"
  - `reason`: rejection reason (empty if approved)
  - `in_combat`: whether active combat
  - `dm_override`: whether DM override was applied

### Testing Requirements
- Both subsystems already have full test suites with wiring tests
- No new tests required; only add OTEL emissions to production code
- Verify wiring: both beat_filter and scene_relevance are imported and used in
  `render_queue.rs` and the dispatch pipeline

### No New Stubs or Dead Code
- Do NOT create new modules or types
- Do NOT add placeholder fields
- Only add watcher events at decision points that already exist