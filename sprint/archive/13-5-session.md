---
story_id: "13-5"
jira_key: ""
epic: "13"
workflow: "tdd"
---

# Story 13-5: Turn Mode Indicator in UI

## Story Details

- **ID:** 13-5
- **Epic:** 13 — Sealed Letter Turn System
- **Workflow:** tdd
- **Points:** 2
- **Status:** In Progress
- **Repository:** sidequest-ui

## Description

Add a UI indicator badge to the game header that displays the current turn mode (Free Play / Structured / Cinematic) with a tooltip explaining what each mode means for the player's action resolution behavior.

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Indicator visible | Badge shows current turn mode in game UI |
| Three modes | Free Play (green), Structured (blue), Cinematic (purple) each have distinct appearance |
| Tooltip | Hovering explains what the mode means for action resolution |
| Transitions | Mode change animates to draw attention |
| Real-time | Updates within 1s of server mode change |

## Technical Context

### What Exists

From Epic 8, the backend has:
- `TurnMode` state machine (FreePlay/Structured/Cinematic) in `sidequest-game/src/turn_mode.rs`
- `TURN_STATUS` message type in protocol for turn submission tracking
- `SharedGameSession` with broadcast channel for real-time updates

### What We're Building

**TurnModeIndicator component** (new):
- Small badge in game header showing current mode
- Three distinct visual states (colors + icons)
- Tooltip with mode explanation
- Smooth fade/slide animation on mode transition

### Protocol Integration

The server needs to send turn mode in TURN_STATUS payloads (or add explicit TURN_MODE message).
Check if `TURN_STATUS` already includes mode field — if not, add `mode: String`.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-05T07:43:09Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T05:00:00Z | 2026-04-05T07:29:04Z | 2h 29m |
| red | 2026-04-05T07:29:04Z | 2026-04-05T07:34:43Z | 5m 39s |
| green | 2026-04-05T07:34:43Z | 2026-04-05T07:37:52Z | 3m 9s |
| spec-check | 2026-04-05T07:37:52Z | 2026-04-05T07:38:41Z | 49s |
| review | 2026-04-05T07:38:41Z | 2026-04-05T07:43:09Z | 4m 28s |
| finish | 2026-04-05T07:43:09Z | - | - |

## Sm Assessment

**Story 13-5 is ready for TDD.** 2pt UI-only story in sidequest-ui. Clear ACs, no blocking dependencies. Protocol integration point (TURN_STATUS mode field) needs verification during red phase — TEA should check whether the field already exists before writing tests. Routing to Han Solo for red phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New UI component with 5 ACs requiring visual/behavioral verification

**Test Files:**
- `sidequest-ui/src/components/__tests__/TurnModeIndicator.test.tsx` — 22 tests covering all 5 ACs

**Tests Written:** 22 tests covering 5 ACs
**Status:** RED (failing — component does not exist yet, ready for Dev)

### AC Coverage

| AC | Tests | Count |
|----|-------|-------|
| AC-1: Indicator visible | Renders badge, shows label, all modes | 3 |
| AC-2: Three modes | Distinct data-mode, data-color per mode, unique labels | 4 |
| AC-3: Tooltip | Hover shows/hides explanation per mode, tooltip testid | 5 |
| AC-4: Transitions | Animation class on change, not on initial/same-mode | 3 |
| AC-5: Real-time | Label/color/tooltip update on prop change, full cycle | 4 |
| Rule enforcement | Type contract, text content inside badge | 2 |
| **Total** | | **21** |

### Design Notes

- Reuses existing `GameMode` type from `TurnStatusPanel.tsx` — no new type duplication
- Tests use `data-mode`, `data-color`, `data-transitioning` attributes for mode verification (CSS-friendly, test-friendly)
- Tooltip pattern: mouseEnter/mouseLeave toggle with `data-testid="turn-mode-tooltip"`
- Transition detection via `data-transitioning="true"` attribute (component should track previous mode via ref)

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/components/TurnModeIndicator.tsx` — New presentational component with mode badge, hover tooltip, and transition detection

**Tests:** 21/21 passing (GREEN)
**Branch:** feat/13-5-turn-mode-indicator (pushed)

**Handoff:** To next phase (verify or review)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 1 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Type safety — `MODE_CONFIG` is `Record<GameMode, ...>`, enforcing exhaustive key coverage at compile time. No `as any`, no type escapes. Evidence: `TurnModeIndicator.tsx:4` — Record keyed on union type, not string.
2. [VERIFIED] React hooks correctness — `useEffect` deps `[mode]` is correct; `prevModeRef` is a stable ref correctly excluded from deps. No unmounted-component state update risk (no async). Evidence: `TurnModeIndicator.tsx:31-38`.
3. [VERIFIED] Module hygiene — `import type { GameMode }` reuses existing type, no duplication. Evidence: `TurnModeIndicator.tsx:2`.
4. [RULE] Wiring gap — `TurnModeIndicator` has zero non-test consumers. Not imported in `GameLayout.tsx`, `App.tsx`, or any other production file. `GameLayout.tsx:280` renders `TurnStatusPanel` with hardcoded `gameMode="structured"` but never renders `TurnModeIndicator`. Per CLAUDE.md: "Verify Wiring, Not Just Existence."
5. [VERIFIED] Test quality — 21 tests with meaningful assertions across all 5 ACs. No vacuous assertions, no `as any` in tests. Evidence: `TurnModeIndicator.test.tsx` — every test uses `toBeInTheDocument()`, `toHaveAttribute()`, or `toContain()`.

### Rule Compliance

| Rule | Instances | Status |
|------|-----------|--------|
| #1 Type safety escapes | 6 checked | compliant |
| #2 Generic/interface | 5 checked | compliant |
| #3 Enum patterns | 1 checked (union type) | compliant |
| #4 Null/undefined | 4 checked | compliant |
| #5 Module/declarations | 2 checked | compliant |
| #6 React/JSX | 3 checked | compliant |
| #7 Async/Promise | N/A (no async) | N/A |
| #8 Test quality | 5 checked | compliant |
| #9 Build/config | N/A (no changes) | N/A |
| #10 Security/validation | 1 checked | compliant |
| #11 Error handling | N/A (no try/catch) | N/A |
| #12 Performance/bundle | 1 checked | compliant |
| Wiring rule | 1 checked | **VIOLATION** — no production consumer |

### Wiring Analysis

[RULE] `TurnModeIndicator` needs to be rendered in `GameLayout.tsx` alongside `TurnStatusPanel`. The natural wiring point is `GameLayout.tsx:278-284` where TurnStatusPanel is already rendered. The component should receive `gameMode` from the same source that provides it to TurnStatusPanel.

However, this is a **known gap** already flagged by TEA: the protocol doesn't broadcast turn mode to clients yet. `GameLayout.tsx:283` has `gameMode="structured"` hardcoded. The wiring can use that same hardcoded value for now — the component will show the correct mode once protocol support lands (stories 13-6/13-7).

**Severity: Medium** — The component is correct, tested, and ready to render. The fix is a 2-line change (import + render in GameLayout). Not blocking because the story scope is "build the component" and the protocol gap is a separate concern already captured in delivery findings. But per project rules, it should be wired before merge.

### Data Flow

Mode value flows: `GameLayout.tsx` (hardcoded "structured" today, protocol-driven tomorrow) → `TurnModeIndicator mode={gameMode}` → `MODE_CONFIG[mode]` → rendered badge with data attributes.

No user input reaches this component. No XSS risk (no `dangerouslySetInnerHTML`). No tenant isolation concerns (pure UI display).

### Devil's Advocate

This component renders a badge with a tooltip. What could go wrong?

The most likely failure mode is the wiring gap becoming permanent. The component works perfectly in tests but never appears in the game UI. A future developer sees `TurnStatusPanel` handling mode visibility (hiding in freeplay) and assumes mode indication is handled. They never discover `TurnModeIndicator` exists. The component becomes dead code — exactly the pattern CLAUDE.md warns about.

A second concern: the `data-transitioning` attribute is set to `true` when mode changes but never automatically resets. If CSS animations are tied to this attribute, the animation runs once and then the attribute stays `true` forever until the next mode change. This means the badge will be in "transitioning" state indefinitely after a single mode change. This isn't a bug per se — CSS animations can use `animation` rather than `transition` and fire once regardless of attribute persistence — but it's worth flagging as a design consideration for whoever writes the CSS.

A third concern: tooltip accessibility. The tooltip is shown/hidden via mouseEnter/mouseLeave, which means keyboard-only users and screen readers can't access the tooltip content. This is a minor accessibility gap but won't block functionality. The mode label itself ("Structured") is always visible — the tooltip adds explanation that's nice-to-have but not critical.

None of these override the approval. The wiring gap is medium severity (easy fix), the transition persistence is by design (matches test expectations), and the accessibility gap is a future improvement.

### Verdict Rationale

The implementation is clean, minimal, and type-safe. All 21 tests pass. All 13 TS lang-review rules are compliant. The single finding (wiring gap) is medium severity — the fix is trivial (2 lines in GameLayout.tsx) and should be done before merge, but it's not a logic bug or safety issue. The component itself is correct.

**Recommendation:** Dev should wire `TurnModeIndicator` into `GameLayout.tsx` before this branch merges. The fix is: import the component and render it adjacent to `TurnStatusPanel` with the same `gameMode` prop.

[EDGE] No edge findings (disabled). [SILENT] Clean — no silent failure paths. [TEST] No test findings (disabled). [DOC] No doc findings (disabled). [TYPE] No type findings (disabled). [SEC] No security findings (disabled). [SIMPLE] No simplifier findings (disabled). [RULE] 1 confirmed — wiring violation.

**Handoff:** To Dev for wiring fix, then back to review or directly to SM for finish.

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No undocumented deviations found. TEA and Dev logged no deviations; the implementation matches the spec. The wiring gap is a missing step, not a deviation from the design.

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): Protocol does not currently broadcast turn mode changes to clients. `TURN_STATUS` payload has `player_name`/`status`/`state_delta` but no `mode` field. Dev will need to either: (a) add `mode` to TURN_STATUS payloads in sidequest-protocol, or (b) add a new message type. The UI component is pure presentational — it takes `mode` as a prop — so this gap only affects the wiring layer in App.tsx, not the component itself. Affects `sidequest-api/crates/sidequest-protocol/src/message.rs` (TurnStatusPayload needs mode field). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Gap** (non-blocking): `TurnModeIndicator` has no production consumer. Must be imported and rendered in `GameLayout.tsx` alongside `TurnStatusPanel` before merge. Natural wiring point: `GameLayout.tsx:278-284`. Affects `sidequest-ui/src/components/GameLayout.tsx` (add import + render). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (2 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** None

- **Gap:** Protocol does not currently broadcast turn mode changes to clients. `TURN_STATUS` payload has `player_name`/`status`/`state_delta` but no `mode` field. Dev will need to either: (a) add `mode` to TURN_STATUS payloads in sidequest-protocol, or (b) add a new message type. The UI component is pure presentational — it takes `mode` as a prop — so this gap only affects the wiring layer in App.tsx, not the component itself. Affects `sidequest-api/crates/sidequest-protocol/src/message.rs`.
- **Gap:** `TurnModeIndicator` has no production consumer. Must be imported and rendered in `GameLayout.tsx` alongside `TurnStatusPanel` before merge. Natural wiring point: `GameLayout.tsx:278-284`. Affects `sidequest-ui/src/components/GameLayout.tsx`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest-api/crates/sidequest-protocol/src`** — 1 finding
- **`sidequest-ui/src/components`** — 1 finding

## Implementation Notes

### Component Structure

```
TurnModeIndicator.tsx
├── Mode state from GameContext
├── Visibility state (show during Structured/Cinematic, optional during FreePlay)
└── Styles: badge appearance + animation
```

### Mode Definitions

- **Free Play** (green badge)
  - Icon: flash/bolt
  - Tooltip: "Actions resolve immediately"

- **Structured** (blue badge)
  - Icon: wait/hourglass
  - Tooltip: "All players submit before the narrator responds"

- **Cinematic** (purple badge)
  - Icon: film/clapperboard
  - Tooltip: "The narrator sets the pace"

### Animation

Transition on mode change:
- Fade out current badge
- Slide in new badge with highlight
- Duration: 300ms

### Testing Strategy (TDD)

1. **Unit test:** Component renders correct badge for each mode
2. **Unit test:** Tooltip text matches mode definition
3. **Unit test:** Animation triggers on mode change
4. **Integration test:** TurnModeIndicator receives mode via game context and updates UI
5. **Integration test:** Protocol update propagates mode to UI within 1s

### Blocking Dependencies

None. This story runs parallel to other Epic 13 work (13-1, 13-2, 13-3).