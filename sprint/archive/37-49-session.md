---
story_id: "37-49"
jira_key: null
epic: "37"
workflow: "trivial"
---
# Story 37-49: Fix @react-three/fiber useLoader mock

## Story Details
- **ID:** 37-49
- **Jira Key:** (YAML-only, no Jira)
- **Epic:** 37 (Playtest 2 Fixes)
- **Workflow:** trivial (phased: setup → implement → review → finish)
- **Points:** 1
- **Priority:** p2
- **Type:** chore
- **Stack Parent:** none

## Problem Statement

Five pre-existing dice test failures block test suite runs:
1. character-creation-wiring
2. confrontation-wiring
3. dice-overlay-wiring-34-5
4. deterministicReplay
5. DiceOverlay

Root cause: D20Mesh component in `src/dice/DiceScene.tsx:198` uses `useLoader()` from `@react-three/fiber`, which is not mocked in the test setup. Tests fail with `useLoader is not a function` errors.

Existing mock structure shows the solution: `InlineDiceTray.test.tsx` has a working @react-three/fiber mock that includes useLoader (lines 15-24). This mock returns a mock texture object with the shape expected by D20Mesh.

## Acceptance Criteria

- [ ] DiceOverlay.test.tsx has @react-three/fiber mock with useLoader
- [ ] useLoader mock returns texture object with clone() method
- [ ] deterministicReplay.test.tsx has @react-three/fiber mock with useLoader
- [ ] character-creation-wiring.test.tsx has @react-three/fiber mock with useLoader
- [ ] confrontation-wiring.test.tsx has @react-three/fiber mock with useLoader
- [ ] All 5 test files pass (npm test runs green)
- [ ] No debug code or console.logs in the fix

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-27T13:59:08Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-27T00:00:00Z | 2026-04-27T10:42:41Z | 10h 42m |
| implement | 2026-04-27T10:42:41Z | 2026-04-27T13:18:04Z | 2h 35m |
| review | 2026-04-27T13:18:04Z | 2026-04-27T13:59:08Z | 41m 4s |
| finish | 2026-04-27T13:59:08Z | - | - |

## Delivery Findings

No upstream findings during setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- ~~**Gap** (non-blocking): `character-creation-wiring.test.tsx` fails with `useRoutes() may be used only in the context of a <Router> component.`~~ **Resolved in commit ced6c70** — test now wraps `<App />` in `<MemoryRouter initialEntries={["/"]}>` and mocks the slug-mode endpoints.
- ~~**Gap** (non-blocking): `confrontation-wiring.test.tsx` source-text regex assertions stale post-refactor.~~ **Resolved in commit ced6c70** — multi-line regex updated; BEAT_SELECTION assertions rewritten to match the current physics-is-the-roll DICE_THROW + beat_id contract.
- **Gap** (non-blocking): `dice-overlay-wiring-34-5.test.ts` lazy-loads-DiceOverlay assertions stale post-refactor — full-screen DiceOverlay was retired and dice now render inline via InlineDiceTray. **Resolved in commit ced6c70** — assertions rewritten to match the InlineDiceTray-via-ConfrontationOverlay wiring. *Found by Dev during implementation, fixed same session.*
- **Gap** (non-blocking): `lobby-start-ws-open.test.tsx` — "Leave + Start opens a new WebSocket for the new slug" test fails. Affects `src/__tests__/lobby-start-ws-open.test.tsx`. Outside r3f/dice/character-creation domain — should be addressed by the team that owns the lobby-state-machine code. *Found by Dev during full-suite verification.*
- **Gap** (non-blocking): `usePeerEventCache.test.tsx` — "bumps latestSeq forward on appendEvent, monotonic" test fails. Affects `src/hooks/__tests__/usePeerEventCache.test.tsx`. Outside r3f/dice/character-creation domain — multiplayer event cache regression. *Found by Dev during full-suite verification.*

## Design Deviations

None.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **AC item "All 5 test files pass" — initially deferred, then fully resolved per user directive**
  - Spec source: 37-49-session.md AC list ("All 5 test files pass (npm test runs green)")
  - Spec text: "All 5 test files pass (npm test runs green)"
  - Initial implementation (commit 287755f): Added the @react-three/fiber `useLoader` mock to all 4 named test files. The 2 dice files turned green (47/47); the 2 wiring files remained red for unrelated causes (Router context missing in render(); source-text regex assertions that no longer match post-refactor App.tsx/GameBoard.tsx) and were logged as upstream Findings.
  - Resolution (commit ced6c70): Per user directive ("fix the pre-existing failures, honor new code, don't revert code to fix tests"), updated the wiring tests to match the current architecture: MemoryRouter wrap + slug-mode fetch mocks for character-creation-wiring; multi-line JSX-friendly regex + new BEAT_SELECTION→DICE_THROW+beat_id contract for confrontation-wiring; replaced lazy-DiceOverlay assertions with the current InlineDiceTray-via-ConfrontationOverlay wiring for dice-overlay-wiring-34-5. All 6 r3f-touching test files are now green (118/118).
  - Severity: resolved (was minor, now closed)
  - Forward impact: none — all in-scope pre-existing failures are now green. Two remaining suite failures (`lobby-start-ws-open.test.tsx`, `usePeerEventCache.test.tsx`) are entirely outside this story's domain and are recorded as new upstream Findings.

### Reviewer (audit)
- **Dev's "AC partially deferred → fully resolved" deviation:** ✓ ACCEPTED by Reviewer. The pivot to fix wiring tests in commit ced6c70 was within story scope (Problem Statement listed all 5 files; user directive confirmed intent). Dev correctly honoured new production code instead of reverting it to satisfy stale assertions. No undocumented spec deviations identified during review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 1266/1267 (one unrelated pre-existing failure on develop, untouched by branch) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 8 | confirmed 1, dismissed 6, deferred 1 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 6 | confirmed 1, dismissed 4, deferred 1 |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 1, dismissed 4, deferred 2 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 3, dismissed 0, deferred 1 |
| 6 | reviewer-type-design | Yes | findings | 4 | confirmed 0, dismissed 4, deferred 0 |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Yes | findings | 3 | confirmed 2, dismissed 0, deferred 1 |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 1, dismissed 3, deferred 0 |

**All received:** Yes (9 returned, 7 with findings)
**Total findings:** 9 confirmed, 21 dismissed (with rationale below), 6 deferred

### Confirmed findings (incorporated into assessment)
- **[SIMPLE][TEST][RULE] 5x verbatim duplication of @react-three/fiber + rapier + drei vi.mock block** across DiceOverlay, deterministicReplay, InlineDiceTray, character-creation-wiring, confrontation-wiring. Severity: MEDIUM. SM scope explicitly endorsed extraction at >2x; we're at 5x. The diff adds the useLoader stanza to 4 files and the full block to 2 wiring tests but doesn't consolidate. Centralize to a shared helper or `setupFiles` entry. *Not blocking — refactor follow-up.*
- **[DOC] Stale fixture/comment in `character-creation-wiring.test.tsx:330`** — the GET /api/games/:slug mock returns `world_slug: "shimmering_dale"` and the comment says "Echoes the genre/world the test selected (low_fantasy default)", but `fakeGenresResponse.low_fantasy.worlds` only contains `fakeWorld("default", "Default")`. The mock world doesn't match any fixture world. Severity: LOW. Doesn't break any test (no assertion checks world_slug) but the comment misleads. Confirmed by both simplifier and comment-analyzer.
- **[DOC] Misleading 300ms-timer comment in `connectPlayer`** — comment says "SESSION_EVENT scheduled 300ms after the socket opens"; actually the 300ms `setTimeout` starts at `connect()`, not at the OPEN event (App.tsx:1243). Test still works because `shouldAdvanceTime: true` advances real time alongside fake. Severity: LOW.
- **[DOC] "useRoutes()" reference in renderApp comment is wrong** — App actually uses `<Routes>`/`<Route>` JSX components plus `useNavigate`/`useParams`, all of which still require a Router ancestor. The functional fix is correct, the cited mechanism is not. Severity: LOW.
- **[EDGE][SILENT] Fetch mock fallback returns genres for any unrecognized URL** — could mask future URL drift. Severity: LOW for current scope (no current URL drifts), HIGH for long-term resilience. Acceptable for a trivial chore but worth a follow-up to convert the fallback to a `Promise.reject(new Error('Unmocked fetch: ' + url))`.

### Dismissed findings (with rationale)
- **Most edge-hunter findings (Request-object handling, slug-with-slash, URL-aware useLoader, multi-URL useLoader return-as-array)** — speculative future cases not exercised by any current test. *Dismissed: scope expansion beyond a trivial test-mock chore.*
- **type-design "useLoader mock fidelity" (4 instances)** — pre-existing pattern from InlineDiceTray.test.tsx (not in diff); the mock is shape-adequate for D20Mesh which only reads `.clone()` + `.wrapS`/`.wrapT`. *Dismissed: type rule "mock should match real signature" is satisfied by the shape the consumer actually uses; expanding to full THREE.Texture would be gold-plating.*
- **test-analyzer "source-text grep tests are fragile" (3 instances)** — true in general, but the tests exist on develop with this pattern as their established style; converting to behavior tests is a separate refactor. *Dismissed: scope expansion. Behaviour-test coverage already exists for the same paths via the renderApp() flow.*
- **rule-checker "MockWebSocket as any" + "non-null on find() results" (4 instances)** — pre-existing code on develop, not introduced by this diff. *Dismissed: not diff-introduced; would be a "fix something I didn't break" expansion.*
- **rule-checker "skipLibCheck: true in tsconfig.app.json"** — pre-existing tsconfig flag, not touched by diff. *Dismissed: not diff-introduced.*
- **silent-failure "loadSession empty catch in App.tsx:83"** — pre-existing production code, not in diff. *Dismissed: out of scope.*

### Deferred findings (worth a follow-up story)
- **Centralize r3f mocks into a single shared helper** (covered by 3 specialists; SM scope endorsed it). Deferred so this story can ship the green-tests outcome without expanding into a refactor.
- **Add slug-entry direct-link test** to character-creation-wiring (silent-failure-hunter): cold-mount at `/solo/<slug>` is currently uncovered. Genuine coverage gap, but pre-existed before this diff and is sibling-story material.
- **Convert source-text wiring assertions to behavior tests** (test-analyzer): same coverage style is used elsewhere; treat as a code-quality hygiene story.
- **Tighten `face[,\s]` regex with word boundary `\bface\b`** (edge-hunter): low priority — current handler body has no `interface` token, so no false positive today.
- **Tighten dependency-array assertion in confrontation-wiring** (silent-failure-hunter): scope-tighten the regex to handleBeatSelect's specific deps.
- **Replace `vi.advanceTimersByTime(100)` with `waitFor(MockWebSocket.instances.length > 0)`** (simplifier + test-analyzer): more semantic and less fragile, but currently passes deterministically.

### Rule Compliance

Rule-checker enumerated 47 instances across 13 numbered TypeScript checks, finding 4 violations (1 diff-introduced, 3 pre-existing). My own audit confirms:

1. **Type safety escapes** — Diff introduces no new `as any`/`@ts-ignore`. Pre-existing `MockWebSocket as any` (line 278) and `as unknown as typeof fetch` (line 349) are unchanged. Non-null assertions on `find()` results (lines 497/590/633) are pre-existing in untouched test bodies. **Compliant for this diff.**
2. **Generic/interface pitfalls** — All new `Record<string, unknown>` casts use `unknown` not `any`. Inline component types use `{ children: React.ReactNode }`. **Compliant.**
3. **Enum anti-patterns** — No enum definitions in diff. **N/A.**
4. **Null/undefined handling** — `init?.method`, `url.match()` results, regex match guards all correctly handled. **Compliant.**
5. **Module/declaration issues** — `import type` keyword used correctly for type-only imports; bundler resolution means no `.js` extension required. **Compliant.**
6. **React/JSX** — vi.mock factory inline components have no hooks, no effect deps, no `key={index}`, no `dangerouslySetInnerHTML`. **Compliant.**
7. **Async/Promise** — `await act(async () => {...})` correctly wraps timer manipulation; `json: async () => (data)` returns data, not `Promise<void>`. **Compliant.**
8. **Test quality** — 5x mock duplication is the one diff-introduced test-quality concern. Mock shapes are minimally adequate for production callers. **One finding (the duplication), non-blocking.**
9. **Build/config** — Pre-existing `skipLibCheck: true` not touched by diff. Strict mode enabled. **Compliant for diff.**
10. **Input validation** — Test fixtures only; no user input or API validation surface. **N/A.**
11. **Error handling** — No try/catch introduced. **N/A.**
12. **Performance/bundle** — Test-only imports (`MemoryRouter`, `node:fs`); no production bundle impact. **Compliant.**
13. **Fix-introduced regressions** — Re-scanned the test rewrites against checks 1–12. The `as Response` casts on Promise.resolve objects are the standard Vitest mock pattern; the `[\s\S]*?` widening is a correct multi-line fix; the `face[,\s]` loosening tolerates the new beat_id spread. **Compliant.**

### Devil's Advocate

If this code is broken, where? Let me argue the strongest case I can against approval.

**The fetch mock fallback is a time bomb.** The character-creation-wiring fetch mock has four matching branches and a final unconditional `return Promise.resolve({ ok: true, json: async () => fakeGenresResponse })`. Today every URL the production code emits hits one of the four branches. Tomorrow someone adds a new endpoint — say `GET /api/players/me` for a profile-aware lobby — and it silently receives the genres response, returns 200 OK, and the test pretends nothing changed. The assertion that ConnectScreen rendered passes because genres still loaded; nobody notices the new endpoint is broken until production. A reviewer who approves this without flagging it is approving a maintenance hazard. Counter: the mock was already a fallback before the diff; the diff added two MORE branches (POST /api/games, GET /api/games/:slug) but did not introduce the fallback pattern. The risk is pre-existing, the diff didn't make it worse — and converting to a hard-fail fallback is its own behavioural change that needs deliberate handling. I'd call this a follow-up, not a blocker, but a real reviewer would still flag it loudly.

**The `face[,\s]` regex would pass `interface` if it ever appeared in handleDiceThrow's body.** Today's App.tsx has no such word in that callback. The day someone adds a comment `// interface w/ face buffer` inside the handler body, the test silently passes regardless of whether `face` is actually a payload key. Counter: the assertion was already a source-text grep before the diff; tightening to `\bface\b[,\s]` is a one-character improvement that I should ask for. I dismissed it as low-priority, but a stricter reviewer would not.

**The 5x mock duplication doubles down on a debt the SM explicitly told Dev to clean up.** SM said "Prefer extracting the mock to a shared test helper if it duplicates more than 2x." Three subagents flagged this. The diff goes from 4x → 5x without extraction. Dev had two opportunities (initial commit, post-pivot rewrite) and took neither. Counter: the user's directive after the first commit was specifically "fix the pre-existing failures," and Dev's second commit honoured that exact scope without expanding into refactors. The duplication remains, but it's a follow-up that can be safely deferred — every test is green and the duplication is mechanical, not a semantic risk.

**The slug-entry route (`/solo/:slug` cold start) is uncovered.** All `renderApp()` calls hardcode `initialEntries={["/"]}`. Player-2's deep-link join path — the production flow that actually exercises NamePrompt + identityConfirmedForSlug + the slug-connect effect on initial mount — has zero test coverage in this file. A regression in that path would silently pass character-creation-wiring while breaking real users. Counter: this is a coverage gap that pre-existed (the test file never covered slug-entry) and is properly logged as a deferred follow-up. Not introduced by this diff.

**Verdict from advocacy:** Two of the four arguments (the fallback hazard, the regex looseness) are real but pre-existing and small. The duplication is a deliberate scope choice with a clear follow-up. The coverage gap is pre-existing. None rise to blocking severity. The diff's job — make tests green to unblock the suite — is done correctly. I'm reaffirming APPROVE while explicitly noting these as worth a refactor story.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** A user clicks "Start Adventure" in the lobby. ConnectScreen.handleStart calls POST /api/games (now mocked). The mock returns `{slug, mode}`. ConnectScreen.navigate(`/solo/<slug>`) updates the URL inside MemoryRouter. AppInner re-mounts with the slug param, fires the slug-connect effect, fetches GET /api/games/:slug (now mocked), constructs the WebSocket via `connect()`, and 300ms later sends `SESSION_EVENT{connect}` over the open socket. The test's `connectPlayer()` advances 100ms (effect flush), simulates OPEN, then advances 500ms (passes the 300ms send). All 16 character-creation tests now exercise this end-to-end flow successfully.

**Pattern observed:** Source-text regex wiring tests at `src/__tests__/dice-overlay-wiring-34-5.test.ts:357` and `src/__tests__/confrontation-wiring.test.tsx:295`. These are wiring smoke checks that read `App.tsx` / `GameBoard.tsx` / `ConfrontationOverlay.tsx` source via `node:fs` and grep for prop names. Pattern pre-exists on develop; Dev correctly updated the regexes to match new architecture rather than reverting production code. Acceptable for a trivial chore; behaviour-level integration tests would be stronger and are deferred as a follow-up.

**Error handling:** Test mocks return `ok: true` for all branches. No 4xx/5xx error path is exercised in the new fetch mock; AppInner's `setGameMetaError` branch (App.tsx:1262) is therefore uncovered by these tests. Pre-existing coverage gap, deferred.

**Tags incorporated:** [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE] — see Confirmed/Dismissed sections.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| MEDIUM | 5x mock duplication of r3f+rapier+drei vi.mock block — SM scope endorsed extraction at >2x | All 5 r3f-touching test files | Follow-up story: centralize to setupFiles or a shared helper |
| LOW | world_slug "shimmering_dale" in GET /api/games/:slug mock doesn't match low_fantasy fixture (which has "default") | `character-creation-wiring.test.tsx:333` | Change to `"default"` or document the decoupling |
| LOW | "300ms after the socket opens" comment misstates timer start (it starts at connect(), not OPEN) | `character-creation-wiring.test.tsx:163` | Reword comment |
| LOW | "useRoutes()" cited as the API requiring Router; App actually uses Routes/Route + useNavigate/useParams | `character-creation-wiring.test.tsx:48` | Reword comment |
| LOW | Fetch mock unconditional fallback to genres response masks future URL drift | `character-creation-wiring.test.tsx:345` | Convert fallback to `Promise.reject` for a hard-fail on unmocked URLs |

**No CRITICAL or HIGH severity issues.** All findings are LOW–MEDIUM, several are doc-only, and the most actionable (mock extraction) is explicitly endorsed as a follow-up by the original SM scope. The 118/118 green count across all 6 r3f-touching test files matches the story Problem Statement's intent, and no production code was touched. Pre-existing failures in `lobby-start-ws-open.test.tsx` and `usePeerEventCache.test.tsx` are correctly logged as out-of-scope upstream findings.

**Handoff:** To SM for finish-story.

### Reviewer (code review)
- **Improvement** (non-blocking): Centralize the @react-three/fiber + rapier + drei vi.mock block into a shared setup file. Affects all 5 r3f-touching test files (4 in this diff + InlineDiceTray.test.tsx on develop). Three review specialists confirmed the duplication; SM scope endorsed extraction at >2x. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Convert the fetch-mock unconditional fallback in `character-creation-wiring.test.tsx:345` to `Promise.reject(new Error('Unmocked fetch: ' + url))` so future URL drift in the lobby code surfaces immediately. *Found by Reviewer during code review.*
- **Gap** (non-blocking): Slug-entry direct-link path (`/solo/:slug` cold mount) is not exercised by any character-creation-wiring test — `renderApp()` hardcodes `initialEntries={["/"]}`. Pre-existing coverage gap. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Replace `vi.advanceTimersByTime(100)` in `connectPlayer` with `waitFor(() => expect(MockWebSocket.instances.length).toBeGreaterThan(0))` for a more semantic flush. *Found by Reviewer during code review.*

## Sm Assessment

**Story type:** Trivial chore — fix shared @react-three/fiber test mock so useLoader is provided. Pattern exists in `InlineDiceTray.test.tsx:15-24` (working reference).

**Scope:** UI-only. Add useLoader to the @react-three/fiber mock in 4 test files (DiceOverlay, deterministicReplay, character-creation-wiring, confrontation-wiring). Mock returns texture object with `.clone()` method.

**Risk:** Low. Pre-existing test failures unrelated to in-flight work. No production code touched.

**Verification:** `npm test` (or vitest) on the 5 named test files turns green.

**Handoff:** Inigo Montoya (Dev) — implement directly, no TEA red phase needed (trivial workflow). Prefer extracting the mock to a shared test helper if it duplicates more than 2x; otherwise per-file is fine.

## Dev Assessment

**Implementation Complete:** Yes — story Problem Statement now fully satisfied.

**Files Changed:**

*Commit 287755f — useLoader mock additions (initial story scope):*
- `sidequest-ui/src/dice/__tests__/DiceOverlay.test.tsx` — added `useLoader` to @react-three/fiber mock
- `sidequest-ui/src/dice/__tests__/deterministicReplay.test.tsx` — added `useLoader` to @react-three/fiber mock
- `sidequest-ui/src/__tests__/character-creation-wiring.test.tsx` — added @react-three/fiber + rapier + drei mocks
- `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx` — added @react-three/fiber + rapier + drei mocks

*Commit ced6c70 — wiring-test updates per user directive ("fix the pre-existing failures, honor new code"):*
- `sidequest-ui/src/__tests__/character-creation-wiring.test.tsx` — wrap `<App />` in MemoryRouter; mock POST /api/games + GET /api/games/:slug for slug-mode lobby; loosen connect-button regex to include "start"; advance timers between click and simulateOpen.
- `sidequest-ui/src/__tests__/confrontation-wiring.test.tsx` — multi-line JSX-friendly regex for `<ConfrontationWidget>`; rewrite BEAT_SELECTION assertion to match the current physics-is-the-roll DICE_THROW + beat_id contract.
- `sidequest-ui/src/__tests__/dice-overlay-wiring-34-5.test.ts` — replace lazy-DiceOverlay assertions with the current InlineDiceTray-via-ConfrontationOverlay wiring; check `currentPlayerId` and `onDiceThrow` flow through GameBoard; loosen face-in-payload regex (beat_id spread now follows face).

**Tests (after both commits):**
- DiceOverlay: 21/21 ✓
- deterministicReplay: 26/26 ✓
- InlineDiceTray: 18/18 ✓
- character-creation-wiring: 16/16 ✓ (was 0/16)
- confrontation-wiring: 22/22 ✓ (was 20/22)
- dice-overlay-wiring-34-5: 29/29 ✓ (was 25/29)
- **All 6 r3f-touching test files: 118/118 green** (1267 total tests in suite, 1265 pass — remaining 2 failures in `lobby-start-ws-open.test.tsx` and `usePeerEventCache.test.tsx` are unrelated to dice/r3f/character-creation, pre-existed on develop, out of story scope)
- No `useLoader is not a function` errors anywhere.

**Branch:** feat/37-49-useloader-mock-fix — pushed (commits 287755f, ced6c70)

**Handoff:** Back to review phase — Westley (Reviewer). Reviewer was mid-review when user interrupted to request these fixes; the second commit changes test code only (no production code touched), so the original review's preflight conclusion ("diff is safe — all failures pre-existing on develop") stands and now extends to the wiring tests too.