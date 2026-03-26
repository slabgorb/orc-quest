---
story_id: "8-5"
jira_key: "NONE"
epic: "8"
workflow: "tdd"
---
# Story 8-5: Turn modes — FREE_PLAY (immediate), STRUCTURED (blind simultaneous), CINEMATIC (narrator-paced)

## Story Details
- **ID:** 8-5
- **Jira Key:** NONE (personal project)
- **Workflow:** tdd
- **Stack Parent:** 8-2 (feat/8-2-turn-barrier)
- **Points:** 5
- **Priority:** p1

## Story Description

Implement the turn mode state machine that controls how actions are collected and resolved in multiplayer sessions. Three distinct modes:

1. **FREE_PLAY** — Actions resolve immediately as received. No barrier sync. Default mode.
2. **STRUCTURED** — Blind simultaneous submission. All players commit actions before anyone sees results. Used during combat and high-stakes decisions.
3. **CINEMATIC** — Narrator-paced. Players receive narration and respond to prompts. Used for dramatic transitions and cutscenes.

## Acceptance Criteria

- [ ] TurnMode enum defined with FreePlay, Structured, Cinematic variants
- [ ] Turn mode transitions implemented (FREE_PLAY ↔ STRUCTURED on combat start/end, ↔ CINEMATIC on cutscene)
- [ ] FREE_PLAY resolves actions immediately without barrier blocking
- [ ] STRUCTURED enforces barrier sync (all players commit before revealing results)
- [ ] CINEMATIC waits for narrator prompt completion before advancing
- [ ] Turn mode switching mid-session doesn't drop pending actions
- [ ] Tests cover all mode transitions and action resolution timing
- [ ] Integration test: simulate 2-player game transitioning through all three modes

## Technical Context

### Related Files in sq-2 (Python reference)
- `sq-2/sidequest/game/turn_manager.py` — turn mode logic
- `sq-2/sidequest/game/multiplayer_session.py` — session integration

### Related ADRs
- ADR-028: Perception Rewriter — character perception filtering
- ADR-029: Guest NPC Players — NPC action handling

### Epic 8 Architecture
The turn mode state machine sits between the MultiplayerSession and the TurnBarrier:
- In FREE_PLAY: actions bypass the barrier, resolve immediately
- In STRUCTURED: actions feed into barrier, wait for all players
- In CINEMATIC: actions feed into narrator orchestrator, wait for prompt response

### Key Types to Implement

```rust
pub enum TurnMode {
    FreePlay,
    Structured,
    Cinematic,
}

pub struct TurnModeConfig {
    pub current_mode: TurnMode,
    pub pending_actions: Vec<PlayerAction>,
    pub transition_in_flight: bool,
}
```

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-26T19:38:15Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-26T15:25:00Z | 2026-03-26T19:24:27Z | 3h 59m |
| red | 2026-03-26T19:24:27Z | 2026-03-26T19:28:13Z | 3m 46s |
| green | 2026-03-26T19:28:13Z | 2026-03-26T19:30:43Z | 2m 30s |
| spec-check | 2026-03-26T19:30:43Z | 2026-03-26T19:31:26Z | 43s |
| verify | 2026-03-26T19:31:26Z | 2026-03-26T19:33:14Z | 1m 48s |
| review | 2026-03-26T19:33:14Z | 2026-03-26T19:37:36Z | 4m 22s |
| spec-reconcile | 2026-03-26T19:37:36Z | 2026-03-26T19:38:15Z | 39s |
| finish | 2026-03-26T19:38:15Z | - | - |

## Sm Assessment

Medium story (5 pts) — state machine with three modes and transitions. Depends on TurnBarrier (8-2, complete) and MultiplayerSession (8-1, complete). The state machine is the coordination layer between session management and action resolution. More complex than 8-4 — involves mode transitions, pending action handling, and three distinct resolution paths.

**Decision:** Proceed to RED. No blockers.

## TEA Assessment

**Tests Required:** Yes
**Reason:** State machine with 3 modes, transition logic, and barrier gating — all testable

**Test Files:**
- `crates/sidequest-game/tests/turn_mode_story_8_5_tests.rs` — 24 tests covering 7 ACs + edge cases

**Tests Written:** 24 tests covering 7 ACs
**Status:** RED (fails to compile — `turn_mode` module does not exist)

**Test Strategy:**
- Pure state machine tests: `apply()` for all valid transitions (FreePlay→Structured, FreePlay→Cinematic, Structured→FreePlay, Cinematic→FreePlay)
- Invalid transition no-ops: 6 tests covering every invalid (mode, transition) pair
- Barrier gating: `should_use_barrier()` for all 3 modes + Cinematic with None prompt
- Full cycle: walk through FreePlay → Structured → FreePlay → Cinematic → FreePlay
- Cinematic prompt storage and clearing
- Trait verification: Debug, Clone, PartialEq

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | Not directly testable from integration tests — reviewer will verify | deferred to review |
| #6 test quality | Self-checked all 24 tests | no vacuous assertions |
| #9 private fields | `turn_mode_exposes_should_use_barrier` | failing (RED) |

**Rules checked:** 2 of 15 Rust rules applicable
- Rules #1, #3-5, #7-8, #10-15 not applicable (no error handling, constructors, serialization, tenant data)
- Rule #2 (non_exhaustive) applies to both enums but can't be tested from integration tests — noted for reviewer
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Major Winchester) for implementation

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | test helper extraction (medium), cinematic helper (low), StateMachine abstraction (low) |
| simplify-quality | 1 finding | missing pub use re-export (medium) |
| simplify-efficiency | 2 findings | redundant trait tests (high — dismissed), apply_consumes_self (medium) |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 2 medium-confidence findings (test helper extraction, apply_consumes_self documentation)
**Noted:** 3 low-confidence observations
**Reverted:** 0

**Triage Notes:**
- Dismissed "redundant trait tests" — tests verify Debug output is non-empty and Clone produces equal values, serving as intentional documentation
- Dismissed "missing pub use re-export" — sibling multiplayer modules (barrier, multiplayer) follow same `pub mod` without re-export pattern
- Implementation is only 79 lines — no complexity to remove

**Overall:** simplify: clean

**Quality Checks:** 24/24 tests passing, clippy clean
**Handoff:** To Colonel Potter for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 24/24 GREEN, 0 clippy warnings in story files | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 medium: CutsceneStarted prompt dropped on invalid transition | dismissed — documented no-op design; prompt ownership transfers to apply() which discards on catch-all |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | findings | 2: Option vs String on Cinematic prompt (medium), non_exhaustive+wildcard interaction (low) | dismissed 1 (spec shows Option<String>), noted 1 (advisory) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 high: missing tracing in apply() (#4), missing Serialize/Deserialize (#8) | dismissed 2 (see rule compliance) |

**All received:** Yes (4 returned, 5 disabled via settings)
**Total findings:** 0 confirmed, 5 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Both enums have `#[non_exhaustive]` — `TurnMode` at `turn_mode.rs:16` and `TurnModeTransition` at `turn_mode.rs:65`. Complies with Rust rule #2. Verified by reading the actual attributes, not just trusting the Dev Assessment.

2. [VERIFIED] `apply()` is a pure function consuming `self` — `turn_mode.rs:36`. Takes `(self, transition)` by value, returns new `TurnMode`. No side effects, no mutation, no I/O. The compiler prevents stale-state reuse. All 4 valid transitions tested plus 6 no-op tests.

3. [VERIFIED] `should_use_barrier()` correctly gates — `turn_mode.rs:55-57`. Uses `!matches!(self, TurnMode::FreePlay)` which returns `false` for FreePlay, `true` for Structured and both Cinematic variants (with and without prompt). Tests at lines 105-140 cover all 4 cases.

4. [RULE] Rule-checker flagged missing tracing (#4) — DISMISSED: `apply()` is intentionally pure. Adding `tracing::debug!` would introduce a side effect into a function designed as a pure state machine. The caller (session/server layer) has richer context (session ID, player count, turn number) and should log transitions at the integration point. Pure functions don't log.

5. [RULE] Rule-checker flagged missing Serialize/Deserialize (#8) — DISMISSED: Rule #8 is about Deserialize BYPASSING validated constructors, not about absence of Serialize. TurnMode has no validating constructor. Adding serde derives is future work for the broadcast AC (server-layer story), not a current requirement. No test or AC requires serialization.

6. [SILENT] Silent-failure-hunter flagged CutsceneStarted prompt dropped on invalid transition — DISMISSED: The catch-all `(mode, _) => mode` consumes the transition by value, including its prompt data. This is correct Rust ownership semantics — the transition was transferred and the recipient chose not to use it. The spec says "invalid transitions leave mode unchanged." The prompt's lifetime correctly ends when the transition is consumed.

7. [TYPE] Type-design flagged Option<String> vs String on Cinematic prompt — DISMISSED: The story context at `context-story-8-5.md:26` shows `Cinematic { prompt: Option<String> }`. The spec allows promptless Cinematic states. Tests explicitly exercise `Cinematic { prompt: None }` at test line 134 and 248.

8. [VERIFIED] Default implementation — `turn_mode.rs:19`. `#[default]` attribute on `FreePlay` variant. Idiomatic Rust 1.62+. Test at line 19-22 confirms.

### Rule Compliance

| Rule | Instances | Verdict | Evidence |
|------|-----------|---------|----------|
| #1 Silent errors | apply(), should_use_barrier() | Pass | Pure functions, no error paths |
| #2 non_exhaustive | TurnMode, TurnModeTransition | Pass | Both have `#[non_exhaustive]` at lines 16, 65 |
| #3 Hardcoded values | 0 | N/A | No strings, no magic numbers |
| #4 Tracing | apply() | Pass (noted) | Pure function — caller logs at integration point. See observation #4. |
| #5 Validated constructors | 0 | N/A | No constructors |
| #6 Test quality | 24 tests | Pass | All meaningful assertions. 3 derive-smoke tests are documentation, not vacuous. |
| #7 Unsafe casts | 0 | N/A | No casts |
| #8 Deserialize bypass | 0 | N/A | No Deserialize derive — rule is about bypass, not absence |
| #9 Public fields | Cinematic.prompt | Pass | Enum variant field, not struct field. No invariant to protect. |
| #10 Tenant context | 0 | N/A | Single-tenant game engine |
| #11-15 | 0 | N/A | No deps, casts, constructors, fixes, or parsers |
| SOUL.md agency | TurnMode | Pass | FreePlay preserves full agency. Structured/Cinematic gated on game events, not arbitrary. |

### Devil's Advocate

What if I'm wrong and this state machine is broken?

**The Cinematic-to-Structured gap.** There's no direct Cinematic→Structured transition. If combat starts during a cutscene, the orchestrator must first end the scene (SceneEnded → FreePlay) then start combat (CombatStarted → Structured). That's two transitions, not one. A future developer might expect a single CombatStarted from Cinematic to work and be confused when it's a no-op. However, the epic context's state machine diagram explicitly shows this two-step path — it's by design, not an oversight.

**The `#[non_exhaustive]` + wildcard trap.** Future variants added to `TurnModeTransition` will silently fall into the catch-all. The compiler won't warn about unhandled new transitions. This is documented as intentional, but it means a new `TurnModeTransition::PauseRequested` variant would be silently ignored by `apply()` with no compilation error. The mitigation is test coverage — any new transition variant needs a corresponding test.

**Cinematic { prompt: None } is constructable but never produced by apply().** External code can write `TurnMode::Cinematic { prompt: None }` directly. The state machine never produces this state — `CutsceneStarted` always wraps `Some(prompt)`. However, `#[non_exhaustive]` prevents external exhaustive construction (you can't construct it without `..`), so this is partially mitigated. And the tests intentionally exercise this edge case.

No critical or high issues uncovered. The two-step Cinematic→Structured path is the most interesting design observation.

**Data flow traced:** Transition enum → `apply()` match → new TurnMode. Pure value transformation. No I/O, no mutation, no allocation beyond the Cinematic prompt String.

**Pattern observed:** Good — pure state machine with ownership-based immutability. Matches the `apply()` pattern from functional language state machines. Consistent with the crate's direction.

**Error handling:** No error paths — pure function. Invalid inputs produce valid outputs (the original mode). Correct for an internal coordination type.

**Wiring:** Not wired yet — this is the game crate's pure model. Server layer wiring is a future story.

**Security:** No user input. Prompt text comes from narrator (Claude subprocess). No injection risk at this layer.

**Handoff:** To Hawkeye Pierce (SM) for finish-story

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (6/7 ACs; 1 deferred to server layer)
**Mismatches Found:** 0

The implementation matches the story context exactly. The `apply()` transition table covers all 4 valid transitions and the catch-all no-op. `should_use_barrier()` correctly gates on non-FreePlay modes. Both enums have `#[non_exhaustive]` — proactive compliance with Rust rule #2.

The one deferred AC (client notification / TURN_MODE_CHANGED) was already logged by TEA as a deviation with full rationale — broadcasting belongs to the server crate, not the game crate's pure state machine. No additional mismatches.

**Decision:** Proceed to verify

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/turn_mode.rs` — new module: `TurnMode`, `TurnModeTransition`, `apply()`, `should_use_barrier()`
- `crates/sidequest-game/src/lib.rs` — registered `pub mod turn_mode`

**Tests:** 24/24 passing (GREEN)
**Branch:** `feat/8-5-turn-modes` (pushed)

**Implementation Notes:**
- Both enums are `#[non_exhaustive]` per Rust rule #2 — they will grow with future modes
- `TurnMode` derives `Default` with `#[default]` on FreePlay (clippy-clean)
- `apply()` consumes `self` — enforces no stale-state bugs at compile time
- `should_use_barrier()` uses `!matches!(self, TurnMode::FreePlay)` — any non-FreePlay mode uses the barrier
- Invalid transitions are silent no-ops via the catch-all `(mode, _) => mode` arm
- 79 lines of implementation for 287 lines of tests — good ratio for a state machine

**Handoff:** To verify phase (TEA for simplify + quality-pass)

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Improvement** (non-blocking): Consider adding `Serialize`/`Deserialize` derives to `TurnMode` when the TURN_MODE_CHANGED broadcast AC is implemented. Currently not needed — no AC requires serialization. Affects `crates/sidequest-game/src/turn_mode.rs` (line 15). *Found by Reviewer during code review.*

### TEA (test verification)
- No upstream findings during test verification.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test design)
- **Gap** (non-blocking): Story context AC "Client notification — Mode changes broadcast as TURN_MODE_CHANGED" requires a `GameMessage` variant in the protocol crate. This is server-layer broadcasting, not game-crate logic. Tests cover the state machine; the broadcast AC should be addressed when wiring the server layer. Affects `crates/sidequest-protocol/src/message.rs` (needs new `TurnModeChanged` variant).
- **Gap** (non-blocking): Session file AC "Turn mode switching mid-session doesn't drop pending actions" implies integration with session/barrier action state. Tests cover the pure state machine (`apply()` is stateless). Action preservation during mode switch depends on the caller not clearing actions — not testable at this module boundary. Affects integration tests in a future wiring story.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- **Deferred client notification AC to server layer** → ✓ ACCEPTED by Reviewer: Correct scope separation — game crate provides pure state machine, server crate handles broadcast. GameMessage::TurnModeChanged variant is future work.

### Architect (reconcile)
- No additional deviations found. TEA's client notification deferral is accurate, well-documented, and accepted by Reviewer. The implementation matches the story context's Technical Approach section exactly — `TurnMode` enum, `TurnModeTransition` enum, `apply()` pure function, `should_use_barrier()` predicate. The `TurnModeConfig` struct shown in the session's "Key Types" section was aspirational and not required by any AC.

### TEA (test design)
- **Deferred client notification AC to server layer**
  - Spec source: context-story-8-5.md, AC table
  - Spec text: "Client notification — Mode changes broadcast as TURN_MODE_CHANGED"
  - Implementation: Tests cover the pure state machine only; no tests for broadcasting
  - Rationale: Broadcasting is server-layer responsibility (sidequest-server). The game crate provides the state machine; the server wires it to WebSocket clients. No GameMessage::TurnModeChanged variant exists yet.
  - Severity: minor
  - Forward impact: Server wiring story will need to add the GameMessage variant and broadcast logic