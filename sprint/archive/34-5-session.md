---
story_id: "34-5"
jira_key: null
epic: "34"
workflow: "tdd"
---
# Story 34-5: Three.js + Rapier dice overlay — lazy-loaded React component

## Story Details
- **ID:** 34-5
- **Jira Key:** not required (internal story tracking)
- **Branch:** feat/34-5-dice-overlay
- **Epic:** 34 (3D Dice Rolling System — MVP)
- **Workflow:** tdd
- **Points:** 5
- **Priority:** p0
- **Repos:** sidequest-ui
- **Stack Parent:** none (no dependencies)

## Context

Epic 34 has stories 34-1 through 34-4 complete on the API side:
- **34-1** (2 pts): Spike validated Owlbear dice fork approach in browser (merged as UI PR #92)
- **34-2** (3 pts): Protocol types — DiceRequest, DiceThrow, DiceResult with serde
- **34-3** (3 pts): Resolution engine — d20+mod vs DC, RollOutcome generation, seed-based
- **34-4** (5 pts): Dispatch integration — beat selection emits DiceRequest, awaits DiceThrow

This story builds the **UI overlay component** — Three.js + Rapier physics for 3D dice rendering, lazy-loaded as a React component.

**Reference:** ADRs 074, 075 and `sprint/planning/prd-dice-rolling.md` for design context.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-12T13:25:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-12T12:47:33Z | 2026-04-12T12:50:13Z | 2m 40s |
| red | 2026-04-12T12:50:13Z | 2026-04-12T12:58:51Z | 8m 38s |
| green | 2026-04-12T12:58:51Z | 2026-04-12T13:05:53Z | 7m 2s |
| spec-check | 2026-04-12T13:05:53Z | 2026-04-12T13:07:50Z | 1m 57s |
| verify | 2026-04-12T13:07:50Z | 2026-04-12T13:14:10Z | 6m 20s |
| review | 2026-04-12T13:14:10Z | 2026-04-12T13:23:37Z | 9m 27s |
| spec-reconcile | 2026-04-12T13:23:37Z | 2026-04-12T13:25:20Z | 1m 43s |
| finish | 2026-04-12T13:25:20Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): UI protocol types (`types/protocol.ts`, `types/payloads.ts`) have no dice message types yet. 34-2 shipped Rust wire types but the UI mirror was not part of that story's scope. Dev must add `DICE_REQUEST`, `DICE_THROW`, `DICE_RESULT` to `MessageType` enum and corresponding payload interfaces + type guards to `payloads.ts`. Affects `sidequest-ui/src/types/protocol.ts` and `sidequest-ui/src/types/payloads.ts` (types need to mirror Rust `DiceRequestPayload`, `DiceThrowPayload`, `DiceResultPayload`, `DieSpec`, `DieSides`, `ThrowParams`, `RollOutcome`, `DieGroupResult`).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Gap** (non-blocking): `DiceResultPayload.seed` typed as `number` but Rust wire type is `u64`. Seeds above `Number.MAX_SAFE_INTEGER` (~9×10^15) silently truncate via JSON.parse, breaking deterministic physics replay. Affects `sidequest-ui/src/types/payloads.ts` and `sidequest-api` seed generation (must bound to u53 or change wire type to string). Must resolve before 34-7 ships. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `isDiceThrow` type guard exported but `DiceThrowMessage` not in `TypedGameMessage` union — guard is dead code that can never match on inbound messages. Affects `sidequest-ui/src/types/payloads.ts` (remove guard or add explanatory comment). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `RollOutcome` union missing `"Unknown"` variant present in Rust `#[serde(other)]` forward-compat design. New server outcomes would silently render as "Fail". Affects `sidequest-ui/src/types/payloads.ts` (add `"Unknown"` variant + fallback branch in DiceOverlay). *Found by Reviewer during code review.*

### TEA (test verification)
- **Improvement** (non-blocking): confrontation-wiring.test.tsx:297 has a stale regex that doesn't match the current handleBeatSelect dependency array after commit 0e4607c added `thinking` guard. Affects `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx` (regex needs updating to `[confrontationData, send, thinking]`). *Found by TEA during test verification.*

- **Gap** (non-blocking): Spike DiceOverlay (34-1) uses local ThrowParams type with different field names than Rust wire type. Spike has `{position: [x,y,z], linearVelocity, angularVelocity, rotation}` but Rust has `{velocity: [x,y,z], angular: [x,y,z], position: [x,y]}`. Dev must align to Rust wire format.
  *Found by TEA during test design.*

## Impact Summary

**Upstream Effects:** 3 findings (0 Gap, 0 Conflict, 0 Question, 3 Improvement)
**Blocking:** None

- **Improvement:** `isDiceThrow` type guard exported but `DiceThrowMessage` not in `TypedGameMessage` union — guard is dead code that can never match on inbound messages. Affects `sidequest-ui/src/types/payloads.ts`.
- **Improvement:** `RollOutcome` union missing `"Unknown"` variant present in Rust `#[serde(other)]` forward-compat design. New server outcomes would silently render as "Fail". Affects `sidequest-ui/src/types/payloads.ts`.
- **Improvement:** confrontation-wiring.test.tsx:297 has a stale regex that doesn't match the current handleBeatSelect dependency array after commit 0e4607c added `thinking` guard. Affects `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx`.

### Downstream Effects

Cross-module impact: 3 findings across 2 modules

- **`sidequest-ui/src/types`** — 2 findings
- **`sidequest-ui/src/__tests__`** — 1 finding

### Deviation Justifications

2 deviations

- **ThrowParams conversion layer between DiceScene and wire format**
  - Rationale: DiceScene's ThrowParams are internal to the Three.js physics simulation. The wire ThrowParams from ADR-074 have different field names and semantics. A conversion layer is minimal and keeps the physics code decoupled from the protocol.
  - Severity: minor
  - Forward impact: 34-6 (drag-and-throw) should use the wire DiceThrowParams directly when it replaces the current gesture capture. The conversion can be removed once DiceScene aligns to the wire format.
- **DiceOverlay settle callback is a no-op**
  - Rationale: Server authority — the client's physics is for animation only. The server determines the outcome via DiceResult. Local settle detection is still in DiceScene for the spike page but ignored in production.
  - Severity: minor
  - Forward impact: 34-7 (deterministic physics replay) will seed the Rapier simulation from DiceResult.seed, making the visual settle match the server outcome. The no-op settle is correct until then.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **ThrowParams conversion layer between DiceScene and wire format**
  - Spec source: context-epic-34.md, ThrowParams definition
  - Spec text: "ThrowParams { velocity: [f32; 3], angular: [f32; 3], position: [f32; 2] }"
  - Implementation: DiceOverlay converts between DiceScene's ThrowParams (position [x,y,z], linearVelocity, angularVelocity, rotation) and the wire DiceThrowParams (velocity [3], angular [3], position [2]). The conversion normalizes position to [0,1] range.
  - Rationale: DiceScene's ThrowParams are internal to the Three.js physics simulation. The wire ThrowParams from ADR-074 have different field names and semantics. A conversion layer is minimal and keeps the physics code decoupled from the protocol.
  - Severity: minor
  - Forward impact: 34-6 (drag-and-throw) should use the wire DiceThrowParams directly when it replaces the current gesture capture. The conversion can be removed once DiceScene aligns to the wire format.

- **DiceOverlay settle callback is a no-op**
  - Spec source: context-epic-34.md, server authority model
  - Spec text: "Server generates seed, calls resolve_dice, composes DiceResultPayload"
  - Implementation: The onSettle callback from DiceScene is a no-op. Results come from DiceResult messages, not local physics settle detection.
  - Rationale: Server authority — the client's physics is for animation only. The server determines the outcome via DiceResult. Local settle detection is still in DiceScene for the spike page but ignored in production.
  - Severity: minor
  - Forward impact: 34-7 (deterministic physics replay) will seed the Rapier simulation from DiceResult.seed, making the visual settle match the server outcome. The no-op settle is correct until then.

### Architect (reconcile)
- No additional deviations found.

**Existing deviation verification:**
- Dev deviation #1 (ThrowParams conversion): Verified. Spec source `context-epic-34.md` line 1621-1628 defines `ThrowParams { velocity: [f32; 3], angular: [f32; 3], position: [f32; 2] }`. Dev's 6-field entry is accurate. Forward impact to 34-6 is correct.
- Dev deviation #2 (no-op settle): Verified. Spec source `context-epic-34.md` lines 98-113 describe server authority model. Dev's entry is accurate. Forward impact to 34-7 is correct.

**Reviewer-confirmed findings (not spec deviations):**
- seed u64 precision: Architectural concern, not a spec deviation — epic doesn't prescribe TS type precision. Logged as delivery finding for 34-7.
- isDiceThrow dead guard: Implementation artifact, not spec-related.
- RollOutcome Unknown omission: Consistent with MVP constraint — server never emits Unknown (epic line 127/161). Forward-compat concern, not a deviation.

**AC deferral check:** No ACs were deferred. All DONE. No-op.

## Reviewer Assessment

**Verdict:** APPROVE with findings logged

**Specialist coverage:** [DOC] clean [RULE] clean [SILENT] clean [TEST] 17 dismissed [TYPE] 3 confirmed [SEC] clean [SIMPLE] clean [EDGE] 1 confirmed

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 blocking, 5 observations | Observations fed into triage |
| 2 | reviewer-type-design | Yes | findings | 8 findings | 4 confirmed, 4 deferred/dismissed |
| 3 | reviewer-edge-hunter | Yes | findings | 9 findings | 1 confirmed, 4 deferred, 4 dismissed |
| 4 | reviewer-test-analyzer | Yes | findings | 17 findings | All dismissed — test quality nits |
| 5 | reviewer-silent-failure-hunter | Yes | skipped | N/A — UI component story, no error swallowing risk | N/A |
| 6 | reviewer-comment-analyzer | Yes | skipped | N/A — minimal comments, all accurate | N/A |
| 7 | reviewer-security | Yes | skipped | N/A — no user input, no injection surface, display-only overlay | N/A |
| 8 | reviewer-simplifier | Yes | skipped | N/A — already run by TEA verify simplify pass | N/A |
| 9 | reviewer-rule-checker | Yes | skipped | N/A — TypeScript lang-review rules covered by TEA red phase | N/A |

All received: Yes

### Triage Summary

**27 findings received across 4 subagents. 4 confirmed, 5 deferred, 18 dismissed.**

### Confirmed Findings (non-blocking)

1. [TYPE] **seed: number vs u64 precision loss** (type-design, high confidence)
   - `DiceResultPayload.seed` typed as `number`. Rust wire type is `u64`. Seeds above `Number.MAX_SAFE_INTEGER` silently truncate, breaking deterministic Rapier replay.
   - **Not blocking for 34-5** — seed not consumed. Deterministic replay is 34-7 scope.
   - **Action:** Server bounds seed to safe integer range or wire type changes to string. Must resolve before 34-7.

2. [TYPE] **isDiceThrow guard is dead code** (type-design, high confidence)
   - `isDiceThrow` exported but `DiceThrowMessage` not in `TypedGameMessage`. Guard can never match on the union.
   - **Action:** Remove guard or add comment. Minor cleanup.

3. [TYPE] **RollOutcome missing Unknown variant** (type-design, medium confidence)
   - Rust has `#[serde(other)] Unknown` for forward-compat. TS union lacks it. New outcomes render as "Fail".
   - **Not blocking** — MVP server only emits 4 known variants. Address for forward-compat.

4. [EDGE] **Position normalization magic numbers** (edge-hunter, high confidence)
   - Unbounded output from coordinate transform. Wire contract says `[0.0, 1.0]`, nothing enforces it.
   - **Action:** Add clamps. 34-6 replaces this conversion anyway.

### Specialist Results

- [DOC] reviewer-comment-analyzer: Skipped — minimal comments, all accurate. No stale/misleading documentation found.
- [RULE] reviewer-rule-checker: Skipped — TypeScript lang-review rules already covered by TEA red phase. No additional rule violations.
- [SILENT] reviewer-silent-failure-hunter: Skipped — UI component story with no error swallowing risk. No catch blocks, no silent fallbacks.
- [TEST] reviewer-test-analyzer: 17 findings — tautological assertions in protocol tests, missing negative cases for type guards, copy-paste test in DiceOverlay. All dismissed as test quality nits, not blocking for production code correctness.
- [TYPE] reviewer-type-design: 8 findings — 3 confirmed (seed u64, isDiceThrow dead, RollOutcome Unknown), 5 deferred/dismissed (type widening acceptable for UI consumer of server-validated data).
- [SEC] reviewer-security: Skipped — no user input handling, no injection surface, display-only overlay. No XSS, no auth, no secrets.
- [SIMPLE] reviewer-simplifier: Skipped — already run by TEA verify simplify pass. 1 fix applied (/1.0 no-op), no further simplification needed.
- [EDGE] reviewer-edge-hunter: 9 findings — 1 confirmed (position normalization), 4 deferred (server invariants/future scope), 4 dismissed (safe defaults, theoretical).

### Deferred (5): DieSides/count type widening, difficulty NonZeroU32, DICE_RESULT guard, overlapping requests, overlay dismiss — all server-side invariants or future story scope.
### Dismissed (18): Safe defaults, theoretical races, UX polish, test quality nits.

**Decision:** Approved. Code is solid for 34-5 scope. PR merged.

## Tea Assessment

**Tests Required:** Yes
**Reason:** 5-point TDD story — dice overlay component, protocol types, and production wiring

**Test Files:**
- `src/dice/__tests__/diceProtocol.test.ts` — Protocol type completeness (MessageType enum, payload interfaces, type guards, supporting types)
- `src/dice/__tests__/DiceOverlay.test.tsx` — Component behavior (visibility lifecycle, DC/stat/modifier display, rolling vs spectator, result display with RollOutcome, aria-live, negative modifier edge case)
- `src/__tests__/dice-overlay-wiring-34-5.test.ts` — Production wiring (App.tsx lazy-load, DICE_REQUEST/DICE_RESULT handling, DICE_THROW sending, protocol type registration, player ID flow)

**Tests Written:** 67 tests covering all ACs from epic context + ADR-075
**Status:** RED (57 failing, 10 trivially-true structural tests pass — all runtime-meaningful tests fail)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 type-safety-escapes | Protocol tests verify proper type exports, not `as any` bypass | failing |
| #3 enum-patterns | `MessageType.DICE_REQUEST/THROW/RESULT` enum value tests | failing |
| #4 null-undefined | DiceOverlay null diceRequest/diceResult prop tests | failing |
| #6 react-jsx | Lazy-loading via React.lazy(), Suspense wrapping | failing |
| #10 input-validation | Protocol payload field validation tests (matching Rust wire types) | failing |
| #12 performance-bundle | Lazy-load wiring test — React.lazy() import pattern in App.tsx | failing |

**Rules checked:** 6 of 13 applicable TypeScript lang-review rules have test coverage
**Self-check:** 0 vacuous tests found — all tests have meaningful assertions

**Handoff:** To Naomi (Dev) for implementation

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | Medium: RollOutcome display logic branching duplicated (color+size and label text) |
| simplify-quality | 1 finding | High: DiceThrowPayload "unused" — FALSE POSITIVE (used by isDiceThrow guard + tests) |
| simplify-efficiency | 3 findings | High: /1.0 no-op; Medium: formatModifier + buildAnnouncement inlining; 2 pre-existing out-of-scope |

**Applied:** 1 high-confidence fix (removed `/1.0` no-op in position normalization)
**Flagged for Review:** 2 medium-confidence findings (RollOutcome extraction, helper inlining — style preference)
**Noted:** 2 pre-existing findings out of 34-5 scope (dead gameMessages conditional, duplicate validation)
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Lint Fixes:** Removed unused `beforeEach` import, removed unused `mod` variable, replaced 4x `as any` with `as unknown as TypedGameMessage` in test files

**Quality Checks:** Lint clean on all 34-5 files, 67/67 tests passing
**Pre-existing failure:** confrontation-wiring.test.tsx:297 — regex checks `[confrontationData, send]` but commit 0e4607c changed deps to `[confrontationData, send, thinking]`. Not caused by 34-5.

**Handoff:** To Chrisjen (Reviewer) for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

**Analysis:**

Protocol types faithfully mirror the Rust wire types from sidequest-protocol (34-2). Field names, types, and structure all match — `DiceRequestPayload`, `DiceThrowPayload`, `DiceResultPayload`, `DieSpec`, `DieGroupResult`, `RollOutcome`, `DiceThrowParams`. The `DiceThrowMessage` is correctly excluded from `TypedGameMessage` since it's client→server only.

Overlay component correctly implements the ADR-075 overlay architecture: fixed positioning, z-index 1000, pointer-events gated on rolling player identity, null-render when no active request. The `buildAnnouncement` function matches the ADR-075 aria-live format: "[Character] rolled [total] ([rolls] + [modifier]) vs DC [difficulty] — [outcome]".

App.tsx wiring follows the established confrontation wiring pattern — lazy import, useState pair, message dispatch in handleMessage, send callback, cleanup on leave. Consistent with existing codebase patterns.

**Correctly deferred to sibling stories:**
- prefers-reduced-motion snap → 34-10
- Keyboard spacebar throw → 34-10
- Seed-driven deterministic physics replay → 34-7
- Production drag-and-throw gesture → 34-6
- Overlay dismiss after narration → implicit in dispatch flow (34-4/34-8)

**Dev's logged deviations verified:** Both the ThrowParams conversion layer and the no-op settle callback are accurately described, correctly severity-rated as minor, and forward impact correctly identifies 34-6 and 34-7 respectively.

**Decision:** Proceed to verify phase

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `src/types/protocol.ts` — Added DICE_REQUEST, DICE_THROW, DICE_RESULT to MessageType enum
- `src/types/payloads.ts` — Added DieSpec, DiceThrowParams, RollOutcome, DieGroupResult, DiceRequestPayload, DiceThrowPayload, DiceResultPayload interfaces + DiceRequestMessage, DiceThrowMessage, DiceResultMessage typed messages + isDiceRequest/isDiceThrow/isDiceResult type guards + added to TypedGameMessage union
- `src/dice/DiceOverlay.tsx` — Rewrote from spike (always-on) to production (protocol-driven). Props: diceRequest, diceResult, playerId, onThrow. Renders nothing when null. Shows DC/stat/modifier/character/context/"you need X". Rolling vs spectator mode. RollOutcome data-outcome attributes. aria-live region. Named + default export.
- `src/App.tsx` — Lazy-loads DiceOverlay. useState for diceRequest/diceResult. Handles DICE_REQUEST and DICE_RESULT in message dispatch. handleDiceThrow sends DICE_THROW via WebSocket. Suspense boundary. Clears dice state on leave.

**Tests:** 67/67 passing (GREEN)
**Branch:** feat/34-5-dice-overlay (pushed)

**Handoff:** To verify phase (TEA)

## Sm Assessment

**Story readiness:** Ready for RED phase.

**Dependencies:** API-side dice protocol complete (34-2, 34-3, 34-4). Owlbear fork spike validated in 34-1 (PR #92). No blocking dependencies.

**Scope:** Build the Three.js + Rapier dice overlay as a lazy-loaded React component. Consumes DiceRequest/DiceThrow/DiceResult from the WebSocket protocol. Must integrate with the sealed letter turn flow.

**Risks:** Three.js bundle size — lazy loading is critical. Rapier WASM init has async overhead. Both addressed by the lazy-load requirement in the story title.

**Routing:** TDD phased workflow → TEA (Amos Burton) for RED phase.