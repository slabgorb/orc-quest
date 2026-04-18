---
story_id: "35-11"
jira_key: "MSSCI-35-11"
epic: "MSSCI-35"
workflow: "trivial"
---
# Story 35-11: Delete dead UI components — LayoutModeSelector, TurnModeIndicator

## Story Details
- **ID:** 35-11
- **Jira Key:** MSSCI-35-11
- **Epic:** MSSCI-35 — Wiring Remediation II
- **Workflow:** trivial
- **Type:** chore
- **Points:** 1
- **Repos:** sidequest-ui
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-10T13:52:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-10T13:34:00Z | 2026-04-10T13:39:42Z | 5m 42s |
| implement | 2026-04-10T13:39:42Z | 2026-04-10T13:44:44Z | 5m 2s |
| review | 2026-04-10T13:44:44Z | 2026-04-10T13:52:11Z | 7m 27s |
| finish | 2026-04-10T13:52:11Z | - | - |

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): `useLayoutMode.setMode` is now orphaned — no UI consumer after LayoutModeSelector deletion. Affects `sidequest-ui/src/hooks/useLayoutMode.ts` (either delete the setter, delete the hook entirely and hardcode layout mode, or wire a replacement control). The three narrative layout components (NarrationScroll/Focus/Cards) and their dispatch in NarrativeView are still alive, but with no way for the user to switch between them, only NarrationScroll (the default) will ever render. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Pre-existing silent-fallback patterns in `sidequest-ui/src/hooks/useLocalPrefs.ts` (lines 23, 34, 44) — JSON parse failure silently defaults, localStorage write failure silently succeeds, cross-tab storage sync silently drops corrupt payloads. None are introduced by 35-11 but the LayoutModeSelector deletion increases likelihood of hitting the silent-default path. Affects `sidequest-ui/src/hooks/useLocalPrefs.ts` (add `console.warn` at each failure site, or version the storage key). Violates CLAUDE.md "No Silent Fallbacks" rule. *Found by Reviewer during code review (via silent-failure-hunter subagent).*
- **Improvement** (non-blocking): Missing invalid-mode edge case test in `sidequest-ui/src/__tests__/layout-modes.test.tsx` NarrativeView layout dispatch block — no test verifies behavior when `localStorage["sq-narrative-layout"] = { mode: "legacy" }` or similar unrecognized value. Pre-existing gap, not caused by 35-11, but would be worth addressing alongside the setMode cleanup. Affects `sidequest-ui/src/__tests__/layout-modes.test.tsx`. *Found by Reviewer during code review (via test-analyzer subagent).*
- **Gap** (non-blocking): AC banner sequence in `sidequest-ui/src/__tests__/layout-modes.test.tsx` now reads AC1, AC3, AC4, AC6 — the AC2 gap is new (correctly deleted with LayoutModeSelector tests) but unexplained. A reader auditing coverage cannot tell if AC2 is untested, relocated, or intentionally removed. Affects `sidequest-ui/src/__tests__/layout-modes.test.tsx` (trivial: renumber consecutively OR add a one-line tombstone `// AC2 (LayoutModeSelector UI) deleted in story 35-11`). *Found by Reviewer during code review (via comment-analyzer subagent).*
- **Improvement** (non-blocking): `useLayoutMode` hook return type over-specified — `{ mode, setMode }` advertises a write path that has zero production consumers after 35-11. The type system silently promises a working setter that cannot be invoked from any UI surface. Affects `sidequest-ui/src/hooks/useLayoutMode.ts:17` (either wire a new UI control that calls setMode, OR narrow the return to `{ mode: LayoutMode }` read-only). This is the same underlying issue Dev logged — Reviewer confirms via rule-checker [RULE A5] and type-design subagents. Violates CLAUDE.md "No half-wired features" rule. **Not blocking for 35-11** because: (a) the half-wired state was pre-existing (LayoutModeSelector itself had no production wiring before this change), (b) the deletion chore is 1 point and hook simplification would be scope creep, (c) Dev explicitly logged and flagged the issue before handoff. *Found by Reviewer during code review (via rule-checker and type-design subagents).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

No design deviations.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Surgical test-file edit instead of full deletion** → ✓ ACCEPTED by Reviewer: Dev's verification was correct — the test file covers five live components (NarrationScroll, NarrationFocus, NarrationCards, NarrativeView dispatch, useLayoutMode). Wholesale deletion would have destroyed live coverage. Surgical trim was the right call. SM's original file-scope claim was wrong; Dev caught it and acted correctly.
  - Spec source: `.session/35-11-session.md` SM Assessment, "Files in scope"
  - Spec text: "`src/__tests__/layout-modes.test.tsx` — delete (exists only to exercise the components above)"
  - Implementation: Removed only the `describe("LayoutModeSelector", ...)` block and the `LayoutModeSelector is importable` wiring test. Kept 31 remaining tests that exercise NarrationScroll, NarrationFocus, NarrationCards, localStorage persistence, content parity, NarrativeView layout dispatch, and useLayoutMode hook wiring.
  - Rationale: SM's file-scope claim was wrong. The test file covers five other live components in addition to LayoutModeSelector. Deleting it wholesale would have destroyed live coverage for NarrationScroll/Focus/Cards and useLayoutMode.
  - Severity: minor
  - Forward impact: none — the LayoutModeSelector tests and wiring check are gone as intended; unrelated coverage preserved.
- **Removed unused `setMode` destructure in App.tsx** → ✓ ACCEPTED by Reviewer: necessary consequence of the deletion. `setLayoutMode` was already a dead binding in App.tsx before this change — its only forward consumer was LayoutModeSelector, which had no production wiring. Trimming the destructure is correct and required by lint.
  - Spec source: Story scope ("Delete dead UI components — LayoutModeSelector, TurnModeIndicator")
  - Spec text: Only the two components are named.
  - Implementation: `src/App.tsx:127` changed `const { mode: layoutMode, setMode: setLayoutMode } = useLayoutMode()` to `const { mode: layoutMode } = useLayoutMode()` because `setLayoutMode` was only used to feed the now-deleted `LayoutModeSelector`.
  - Rationale: Required by the lint gate — unused destructure would fail `just ui-lint`.
  - Severity: minor
  - Forward impact: see Delivery Finding above — `useLayoutMode.setMode` now has no production consumer.

### Reviewer (audit)
- **Undocumented clean-up: removed `within` import and orphan `LayoutMode` type alias from `layout-modes.test.tsx`** → ✓ ACCEPTED by Reviewer: both were dead after the describe-block removal (the orphan `LayoutMode` type alias duplicated the authoritative definition in `@/hooks/useLayoutMode`, and `within` was only used by the deleted LayoutModeSelector tests). Dev didn't explicitly log these as deviations but they are lint-driven cleanups consequent to the primary deletion. Severity: none — correct mechanical follow-through.

## Scope & Context

### Components to Delete
1. **LayoutModeSelector** (`src/components/LayoutModeSelector.tsx`) — No production consumers
2. **TurnModeIndicator** (`src/components/TurnModeIndicator.tsx`) — No production consumers

### Test File
- **`src/__tests__/layout-modes.test.tsx`** — References both components; will need updating or deletion after component removal

### Verification
- Grep confirms zero imports of these components in production code
- Only appear in their own definitions and test file
- Safe to remove without breaking any wiring

## SM Assessment

**Scope:** Trivial deletion story. Two React components with zero production consumers to be removed from `sidequest-ui/src/components/`, plus a test file that references them.

**Files in scope:**
- `src/components/LayoutModeSelector.tsx` — delete
- `src/components/TurnModeIndicator.tsx` — delete
- `src/__tests__/layout-modes.test.tsx` — delete (exists only to exercise the components above)

**Wiring verification done pre-setup:** `Grep LayoutModeSelector|TurnModeIndicator` across `sidequest-ui/src` returns only the three files above. No imports elsewhere. Safe to remove without production-path impact.

**Ironic note:** commit `b4852d1` recently *recovered* `TurnModeIndicator` from a pruned `feat/13-5` branch. We are now deleting it again — it stayed unused. No dispute; the audit confirmed no consumers. Caller is OK.

**Handoff to Dev (Naomi Nagata):**
- Delete the three files.
- Run `just ui-lint && just ui-test` to confirm nothing else grabs on.
- No test-writing needed (trivial workflow skips RED). The only test file involved is the one being deleted.
- One-commit job.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/LayoutModeSelector.tsx` — **deleted** (40 lines removed)
- `sidequest-ui/src/components/TurnModeIndicator.tsx` — **deleted** (59 lines removed)
- `sidequest-ui/src/__tests__/layout-modes.test.tsx` — surgical edit: removed LayoutModeSelector describe block (4 tests) and the LayoutModeSelector wiring test; 31 tests preserved for NarrationScroll/Focus/Cards, localStorage persistence, NarrativeView dispatch, and useLayoutMode
- `sidequest-ui/src/App.tsx` — removed unused `setMode: setLayoutMode` destructure (single-line change)

**Tests:** 31/31 passing (GREEN) — full `layout-modes.test.tsx` suite. Lint clean.

**Branch:** `feat/35-11-delete-dead-ui-components` (to be pushed)

**Deviation from SM scope:** SM claimed the test file existed only to exercise the deleted components. Verification showed it covered five other live components. Edited surgically instead of deleting — logged as deviation above. No scope expansion.

**Consequent finding:** Deleting LayoutModeSelector leaves `useLayoutMode.setMode` with no production consumer. The three narrative layout components still exist and dispatch still works, but only the default (scroll) will ever render without a selector UI. Logged as non-blocking Improvement finding above. Out of scope for 35-11.

**Handoff:** To review phase (Reviewer — Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | PASS — lint delta -4, no new failures, no residual references |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter` |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 0, dismissed 3, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 3 | confirmed 2, dismissed 1, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 1, dismissed 2, deferred 0 |
| 6 | reviewer-type-design | Yes | findings | 3 | confirmed 1, dismissed 2, deferred 0 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security` |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier` |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1, dismissed 0, deferred 0 |

**All received:** Yes (6 returned, 3 disabled)
**Total findings:** 5 confirmed, 6 dismissed (with rationale), 0 deferred

### Dismissal Rationale

**[SILENT] All 3 findings dismissed** — All three point to `src/hooks/useLocalPrefs.ts` (lines 23, 34, 44). That file is **not in this diff**. The silent-default behavior is pre-existing and unrelated to the deletion chore. Dismissed: not introduced or modified by 35-11. A separate ticket should address the silent JSON parse/write fallback if the team wants to close them — logged as non-blocking Improvement finding below.

**[TEST] Finding #3 dismissed** — "Missing invalid-mode edge case test" at line 265 concerns coverage for a case that existed before this change and was never tested. Not introduced here. Out of scope for a deletion chore.

**[DOC] Finding #2 dismissed** — "AC4 paraphrase" is Low confidence, trivial. The banner text is close enough; not worth touching in a deletion chore.

**[DOC] Finding #3 dismissed** — "NarrativeView.tsx:12 JSDoc misleading about hook bypass" concerns a pre-existing comment on a file not in this diff. Out of scope.

**[TYPE] Findings #1 and #2 dismissed** — **Both are FALSE POSITIVES based on a stale working-tree view**. Verified against branch HEAD (`git show HEAD:src/App.tsx` and `git ls-tree HEAD`):
  - Type-design claimed App.tsx:130 still destructures `setMode: setLayoutMode`. **Evidence of falseness:** `git show HEAD:src/App.tsx` at line 130 reads `const { mode: layoutMode } = useLayoutMode();`. Destructure was trimmed as intended.
  - Type-design claimed `LayoutModeSelector.tsx` still exists on disk and the wiring test still references it. **Evidence of falseness:** `git ls-tree HEAD -- src/components/LayoutModeSelector.tsx` returns empty. The file is deleted on branch HEAD. The test file at HEAD has no `LayoutModeSelector` references (verified by grep).
  The subagent likely read a cached or developer-workspace view rather than branch HEAD. Dismissed with evidence.

## Rule Compliance

Checked the TypeScript lang-review checklist (13 categories) plus CLAUDE.md wiring and dead-code rules. One violation surfaced — see [RULE] finding below.

### Type safety escapes (#1)
No new `as any`, `@ts-ignore`, or non-null assertions introduced. Pre-existing `!` at `layout-modes.test.tsx:220` (`localStorage.getItem(LAYOUT_PREFS_KEY)!`) is unchanged and not part of this diff. **Compliant.**

### React/JSX (#6)
The two deleted components are gone cleanly. Verified via `Grep LayoutModeSelector|TurnModeIndicator` across `sidequest-ui/src`: zero remaining references in production or tests. `App.tsx:130` hook destructure change does not alter any `useEffect` deps or `useCallback` closures. **Compliant.**

### Test quality (#8)
- 31 tests preserved. No `as any` introduced in assertions. All dynamic imports use `@/` alias.
- Deleted 5 tests (4 describe-block tests + 1 wiring test), all tied to the deleted component.
- **Partial concern:** See [RULE]/[TEST] findings below about `setMode` test now exercising an unreachable production path. Logged as non-blocking.

### CLAUDE.md — Verify Wiring, Not Just Existence (A3)
Enumerated each surviving layout component to verify non-test consumers remain:
- `NarrationScroll` — imported by `src/screens/NarrativeView.tsx` ✓
- `NarrationFocus` — imported by `src/screens/NarrativeView.tsx` ✓
- `NarrationCards` — imported by `src/screens/NarrativeView.tsx` ✓
- `useLayoutMode` (read path) — imported by `src/App.tsx:19` and `src/screens/NarrativeView.tsx:4` ✓
- `useLayoutMode` (write path, i.e. `setMode`) — **zero production consumers** ✗ (see A5 violation)
- `LayoutMode` type — imported by `src/screens/NarrativeView.tsx:4` and `src/components/GameBoard/GameBoard.tsx:31` ✓

### CLAUDE.md — Every Test Suite Needs a Wiring Test (A4)
`describe("Layout modes wiring")` block retains 4 wiring tests (NarrationScroll, NarrationFocus, NarrationCards, useLayoutMode). **Compliant** — surviving components are each covered by an importability assertion. (Caveat: see [TEST] finding about the useLayoutMode wiring test being shallow — it only asserts module-level export, not production reachability.)

### CLAUDE.md — No half-wired features (A5)
**VIOLATION** — `src/hooks/useLayoutMode.ts:17` exports `setMode` with zero non-test production callers. Flagged as `[RULE]` finding below.

### Devil's Advocate

Is this diff broken?

Imagine a user who has been using layout mode switching for weeks. They have `sq-narrative-layout` set to `"cards"` in localStorage. They pull develop, run `npm run dev`, and open the game. What happens? `useLayoutMode` reads `"cards"` from localStorage, `NarrativeView.layoutMode` reads the hook, and the user sees the cards layout — same as before. No regression. Good.

Now imagine the same user wants to switch to `"focus"` mode. Before this change, they would open Settings... wait, where WAS the LayoutModeSelector rendered? I verified: it had **no production consumer** even before this change. That's the whole reason 35-11 exists. So the user had no way to switch layouts before, and has no way to switch layouts after. This deletion doesn't remove functionality; it removes an illusion of functionality. That's a net improvement by the "No Stubbing" rule.

Imagine a user with corrupted localStorage (`{ mode: "unknown" }` from an ancient build or manual tampering). `useLocalPrefs` silently reverts to `{ mode: "scroll" }`. The user sees scroll layout. They can't switch. Is this new? No — the corrupt-localStorage fallback path existed before 35-11 and has nothing to do with the deleted components.

Imagine a tab that had the selector rendered in a sidebar we're forgetting about. Could the deletion break it? I grepped the entire `sidequest-ui` tree: zero references to `LayoutModeSelector` or `TurnModeIndicator` outside of the deletions themselves and sprint YAML. There is no such tab.

Imagine a test that dynamic-imports the deleted module by string literal at runtime. `grep -r "components/LayoutModeSelector\|components/TurnModeIndicator"` — zero hits. Not happening.

Imagine a CI system that lints against `unused-imports`. The diff already trimmed `within` from `@testing-library/react`, `LayoutMode` orphan alias, and `setLayoutMode` destructure. All cleanups applied.

Imagine a new contributor reading `useLayoutMode.ts` and seeing `setMode`. They would reasonably expect it to be callable from the UI. It's not. This is the one genuine smell left behind — and it's precisely what the [RULE] and [TEST] findings flag. But it's a smell, not a failure. The hook still works. The tests still pass. The feature it enables is not reachable, but that's a follow-up, not a blocker for a 1-point deletion chore.

The only scenario where this change breaks something is: somewhere in the codebase there's an unresolved import that I missed. I ran preflight (82 pre-existing errors, zero new). I ran multiple grep passes. I read the branch HEAD directly. If there's a hidden reference, it's hidden from every tool I have.

**Conclusion:** This diff is a clean removal of code that was already dead. It exposes one follow-up (setMode orphaning) that Dev flagged proactively and documented. Nothing else is broken.

## Reviewer Assessment

**Verdict:** APPROVED with acknowledged follow-up

**Data flow traced:**
- User's stored layout mode (`localStorage["sq-narrative-layout"]`) → `useLocalPrefs` → `useLayoutMode.mode` → `NarrativeView.layoutMode` → renders `NarrationScroll | NarrationFocus | NarrationCards`. Read path intact.
- Write path (`useLayoutMode.setMode` → `setPref` → `localStorage.setItem`): exists but unreachable from production. Exercised by tests only.

**Pattern observed:** Pure deletion with surgical test trim. Test file at `sidequest-ui/src/__tests__/layout-modes.test.tsx` preserved 31 live tests while dropping exactly the 5 that exercised the deleted component — good discipline. App.tsx destructure trimmed to match the now-unused setter.

**Error handling:** N/A — deletion diff. No new error paths introduced. Pre-existing silent fallbacks in `useLocalPrefs.ts` (flagged by [SILENT] but out of scope) remain unchanged.

**Findings by source:**

| Severity | Tag | Issue | Location | Action |
|----------|-----|-------|----------|--------|
| [MEDIUM] | [RULE][TYPE][TEST] | `useLayoutMode.setMode` is half-wired — exported and test-exercised, zero non-test production callers. Users cannot change layout mode through any UI surface. Violates CLAUDE.md "No half-wired features" rule. | `sidequest-ui/src/hooks/useLayoutMode.ts:17` | **Not blocking** — Dev logged as delivery finding. Rule violation was pre-existing (LayoutModeSelector had no production consumer before this change either) and is now simply exposed. Follow-up ticket should either: (a) wire a replacement UI entry (settings panel, slash command, keybinding), or (b) simplify hook to `{ mode: LayoutMode }` read-only. |
| [LOW] | [DOC] | AC banner sequence has gap after deletion: AC1, AC3, AC4, AC6. AC2 banner was correctly removed with the describe block, but the gap is unexplained. A reader auditing coverage cannot tell if AC2 is untested or deleted. | `sidequest-ui/src/__tests__/layout-modes.test.tsx:29-262` | **Not blocking** — trivial fix, cosmetic. Either renumber consecutively or add a one-line tombstone. Noted but not demanded for this chore. (AC5 gap was pre-existing.) |

**VERIFIED items** (each checked against subagent findings and project rules):

- [VERIFIED] LayoutModeSelector.tsx fully removed — evidence: `git ls-tree HEAD -- src/components/LayoutModeSelector.tsx` returns empty; grep across `sidequest-ui/src` returns zero hits. Complies with "No Stubbing" and "dead code" rules.
- [VERIFIED] TurnModeIndicator.tsx fully removed — evidence: `git ls-tree HEAD` empty; grep returns zero hits; **no orphaned test file** (verified `Glob **/turn-mode*` returns no files). TurnModeIndicator had no tests before and has none after. Complies with dead-code rule.
- [VERIFIED] `App.tsx:130` destructure trimmed — evidence: `git show HEAD:src/App.tsx` line 130 reads `const { mode: layoutMode } = useLayoutMode();`. No unused destructure binding. Complies with TypeScript lint rules.
- [VERIFIED] Surviving test coverage for live components — evidence: `reviewer-preflight` confirms 31 tests green; NarrationScroll/Focus/Cards wiring tests at `layout-modes.test.tsx:299-319`. Complies with "Every Test Suite Needs a Wiring Test" rule.
- [VERIFIED] Linked `LayoutMode` type still alive — evidence: `useLayoutMode.ts:3` exports it, consumed by `NarrativeView.tsx:4`, `GameBoard.tsx:31`, `App.tsx` (transitively). Deletion of duplicate orphan alias in test file was correct. No regression.
- [VERIFIED] No new lint or test regressions — evidence: preflight branch lint = 82 errors vs develop baseline = 86 errors (delta -4); test failure count identical to develop (all pre-existing). Branch is strictly less broken than develop on the lines it touches.

**Handoff:** To SM (Drummer) for finish-story.