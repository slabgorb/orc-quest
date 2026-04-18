---
story_id: "33-1"
jira_key: ""
epic: "EPIC-33"
workflow: "trivial"
---
# Story 33-1: Genre-themed widget chrome — archetype-specific CSS for widget borders, headers, and backgrounds

## Story Details
- **ID:** 33-1
- **Epic:** 33 — Composable GameBoard Polish
- **Jira Key:** Not yet assigned
- **Workflow:** trivial (5 pts UI polish)
- **Stack Parent:** none
- **Assigned to:** keith

## Problem Statement

The GameBoard widget system needs archetype-specific visual styling to sell the genre immersion. WidgetWrapper currently uses generic CSS and CSS variables from `useGenreTheme`/`useChromeArchetype`, but no archetype-specific rules exist for the different visual styles.

This story adds data-attribute CSS rules (`[data-archetype]`) that style widget borders, headers, and backgrounds based on the chosen archetype:
- **parchment** — warm drop shadows, corner decorations (flourishes)
- **terminal** — glow borders, scan line overlays
- **rugged** — thick weathered borders, distressed treatment

## Acceptance Criteria

- [ ] WidgetWrapper renders `[data-archetype="parchment|terminal|rugged"]` based on useChromeArchetype()
- [ ] Parchment style: warm box-shadow (gold/brown tones), corner border decorations or corner-dot glyphs, off-white header background
- [ ] Terminal style: neon glow border (matches accent color), optional scan-line animation overlay, dark header background
- [ ] Rugged style: thick (3-4px) beveled or weathered border, metal bracket corner accents, rust-toned header
- [ ] All three archetypes verified on at least 3 genre packs during testing
- [ ] No hard-coded color values — all colors come from CSS var() from useGenreTheme
- [ ] Styles compose cleanly with existing WidgetWrapper layout (padding, spacing unchanged)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-11T13:30:59Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-11 | 2026-04-11T13:00:17Z | 13h |
| implement | 2026-04-11T13:00:17Z | 2026-04-11T13:08:34Z | 8m 17s |
| review | 2026-04-11T13:08:34Z | 2026-04-11T13:16:07Z | 7m 33s |
| implement | 2026-04-11T13:16:07Z | 2026-04-11T13:23:59Z | 7m 52s |
| review | 2026-04-11T13:23:59Z | 2026-04-11T13:30:59Z | 7m |
| finish | 2026-04-11T13:30:59Z | - | - |

## SM Assessment

**Story:** 33-1 — Genre-themed widget chrome (5 pts, trivial workflow, p1)
**Epic:** 33 — Composable GameBoard Polish (dashboard polish, genre theming, mobile UX)
**Scope:** UI-only, single repo (`sidequest-ui`). No backend or protocol changes.

**Why trivial workflow:** Pure CSS/styling work on existing components. `WidgetWrapper`, `useGenreTheme`, and `useChromeArchetype` are already wired — this story adds `[data-archetype]` CSS rules for three archetype variants (parchment, terminal, rugged). No new architecture, no new types, no new tests beyond visual verification. Trivial fits.

**Risk areas for Dev:**
1. **Cross-genre verification is non-negotiable** — acceptance criteria require at least 3 genre packs (space_opera, neon_dystopia, low_fantasy recommended). Don't just style one pack and call it done.
2. **No hard-coded colors** — all colors MUST come from `var()` sourced from `useGenreTheme`. Hard-coded hex values will break theme consistency.
3. **Verify wiring** — confirm `WidgetWrapper` actually applies `data-archetype` attribute from `useChromeArchetype()`. If the hook returns the archetype but the wrapper doesn't apply it, CSS rules won't bind.
4. **Layout preservation** — padding/spacing must not shift when archetype styles apply. These are decorative additions, not layout changes.

**Definition of Done:**
- All three archetype styles render distinctly
- Verified on ≥3 genre packs via dev server (not just code review)
- No hard-coded colors anywhere in new CSS
- WidgetWrapper drag/resize still works

**Next agent:** Dev (Naomi Nagata) — implement CSS rules, verify across genre packs in dev server.

## Delivery Findings

No upstream findings at setup.

### Dev (implementation)
- No upstream findings.

### Reviewer (code review)
- **Gap** (non-blocking): Pre-existing hardcoded `rgba()` literals in `sidequest-ui/src/styles/archetype-chrome.css` at lines 18, 97-98, 110-111, 113, 191 violate the spirit of AC-6 and the file's stated structural-only contract. These are NOT in the 33-1 diff — they predate this story — but they represent latent debt that a future story in Epic 33 should clean up. Affects `sidequest-ui/src/styles/archetype-chrome.css` (replace `rgba(r,g,b,a)` with `color-mix(in srgb, var(--appropriate-token) N%, transparent)` matching the correct pattern used in the new widget rules). *Found by Reviewer during code review via reviewer-rule-checker subagent.*
- **Gap** (non-blocking): `--surface` CSS custom property has no global default in `sidequest-ui/src/index.css`. All rules that read `var(--surface)` (including pre-existing and the new widget rules) rely on `useGenreTheme` injecting the value at runtime, which creates a silent empty-fallback window during the archetype-set-before-theme-arrives interval. Affects `sidequest-ui/src/index.css` (add `--surface: <neutral default>` to `:root` alongside existing `--background`, `--primary`, `--accent`, `--border` defaults). *Found by Reviewer during code review via reviewer-silent-failure-hunter subagent.*
- **Improvement** (non-blocking): The test harness at `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts` hardcodes the three archetype string literals instead of deriving them from `ChromeArchetype` union in `useChromeArchetype.ts`. Adding a fourth archetype would silently pass tests without requiring matching CSS. Affects `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts` and `sidequest-ui/src/hooks/useChromeArchetype.ts` (export a `const ARCHETYPES = [...] as const` tuple, derive the union from it, drive the test from it). *Found by Reviewer during code review via reviewer-type-design subagent.*

### Reviewer (code review) — Round 2
- **Improvement** (non-blocking): **Vacuous-pass risk in AC-7 composition guard and rugged-section regression guard.** Both tests rely on `.not.toMatch` against strings returned by `extractWidgetBlock` and `extractArchetypeSection`, both of which return empty string on parse failure. If the CSS file is ever reformatted (e.g., newline before `{`, grouped selectors rearranged), the helpers return empty, and `not.toMatch` passes vacuously — silently defeating the regression guard that pins the round-1 HIGH finding. Affects `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts:144` (AC-7 guard) and `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts:188` (rugged negative-offset guard). Fix: add `expect(widgetBlock).toBeTruthy()` / `expect(section).toBeTruthy()` immediately before the `.not.toMatch` assertion. Found by Reviewer during round-2 code review via reviewer-silent-failure-hunter AND reviewer-test-analyzer subagents (independently corroborated). **Recommend addressing in a small follow-up before the next Epic 33 story touches this file.**

- **Improvement** (non-blocking): **Regression guard regex has `\b` word-boundary false-positive risk.** The pattern `/\b(top|left|bottom|right)\s*:\s*-\d/` would match `border-left: -3px` or `margin-left: -1px` because `\b` matches between the hyphen and the property suffix in compound names. Today no such declarations exist in the rugged section; the test works correctly on the current code. But the guard is semantically imprecise — it cannot distinguish the standalone `left` property (layout offset) from the `left` suffix of `border-left` / `margin-left` (shorthand direction). If someone later adds a legitimate negative margin anywhere in the rugged section, the test would false-fail. Affects `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts:189`. Fix: replace `\b` with `(?:^|\s)` (line-start or whitespace anchor) plus the `/m` flag, or use a negative lookbehind `(?<![\w-])`. Found by Reviewer during round-2 code review via reviewer-test-analyzer subagent. **Group with the vacuous-pass fix in the same follow-up.**

## Impact Summary

**Upstream Effects:** 1 findings (1 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** None

- **Gap:** `--surface` CSS custom property has no global default in `sidequest-ui/src/index.css`. All rules that read `var(--surface)` (including pre-existing and the new widget rules) rely on `useGenreTheme` injecting the value at runtime, which creates a silent empty-fallback window during the archetype-set-before-theme-arrives interval. Affects `sidequest-ui/src/index.css`.

### Downstream Effects

- **`sidequest-ui/src`** — 1 finding

### Deviation Justifications

1 deviation

- **WidgetWrapper does not self-apply the data-archetype attribute; descendant CSS selectors from the document root are used instead.**
  - Rationale: The existing `archetype-chrome.css` already uses this descendant-selector pattern for `.character-panel`, `.running-header`, and `.input-area`. Duplicating the attribute onto every widget would be redundant, create multiple call sites of `useChromeArchetype`, and violate the "don't reinvent — wire up what exists" principle. The visual effect (and acceptance criteria AC-2, AC-3, AC-4) is achieved identically.
  - Severity: minor
  - Forward impact: none — the attribute is still present in the DOM (on `<html>`), so any future code that reads `data-archetype` from an ancestor selector works unchanged.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **Rugged metal bracket corners are invisible.** `::before`/`::after` pseudo-elements at `top/left/bottom/right: -3px` are clipped by `overflow-hidden` on the WidgetWrapper root. AC-4 explicitly requires "metal bracket corner accents." Screenshot `.playwright-mcp/33-1-rugged.png` confirms they do not render — Dev misread the visual output. | `sidequest-ui/src/styles/archetype-chrome.css:253-268` vs `sidequest-ui/src/components/GameBoard/WidgetWrapper.tsx:27` | Move the rugged `::before`/`::after` offsets inside the clip region (positive values like parchment uses). Recommended: `top: 0; left: 0` / `bottom: 0; right: 0` with decorations drawn entirely inside the border box, OR use `inset: 0` with inner-positioned L-shapes via `border-top` / `border-left` on the pseudo-element itself. Re-screenshot and visually confirm corners render before re-submitting. |
| [MEDIUM] | [DOC] **Lying-docstring comments violate the file's structural-only contract.** New inline comments make color claims ("warm shadow" line 47, "off-white header" line 47, "dark header" line 145, "rust-toned header" line 227) in a file whose header at lines 3-4 explicitly states it "only sets structural properties." The claims depend on theme vars that are not guaranteed to produce those colors. | `sidequest-ui/src/styles/archetype-chrome.css:47, 145, 227` | Rewrite the three widget section comments using structural language only. Suggestions: "primary-tinted drop shadow" / "8% primary blended into surface header", "background-dominant header (70% bg / 30% surface)", "accent-tinted surface header (12% accent)". |
| [MEDIUM] | [TEST] **Zero dedicated test coverage for the 80+ new CSS lines.** The entire deliverable of the story is the three new `[data-widget]` rulesets, and none of them are asserted by `chrome-archetype-css.test.ts`. The existing tests only validate pre-existing structural rules; the diff's new content slips through untested. The existing suite passes only because assertions are vacuous for the new rules. | `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts` | Extend the existing test file with one describe block per archetype that asserts: (1) the section contains `[data-widget]` selector, (2) the widget ruleset contains `box-shadow`, (3) the pseudo-element selectors for corner decorations exist (parchment/rugged only), (4) no `padding`, `margin`, `width`, or `height` declarations appear inside the `[data-widget]` blocks (AC-7 composition guarantee). This does not require new test infrastructure — reuse the existing `extractArchetypeSection` helper. |

**Non-blocking observations (noted for visibility, not required for approval):**

- [VERIFIED] Wiring intact — `index.css:5 @import "./styles/archetype-chrome.css"` confirms the file reaches production. `useChromeArchetype.ts:64` sets `data-archetype` on `document.documentElement`, and `useChromeArchetype.test.ts` plus non-test callers in providers cascade the attribute to descendant widgets. Complies with CLAUDE.md wiring rule.
- [VERIFIED] AC-6 for the NEW diff content — every color declaration added in this story uses `var()` or `color-mix()` sourced from theme vars. Enumerated all 11 color-bearing lines in the new blocks; none contain hardcoded literals. Complies with AC-6 locally, even though the pre-existing code around them does not.
- [VERIFIED] AC-7 layout preservation — the new rules set `position: relative`, `border-width`, `border-color`, `border-style`, `box-shadow`, and pseudo-element properties. They do NOT set `padding`, `margin`, `width`, `height`, or flex properties. `WidgetWrapper`'s layout utilities (Tailwind `flex flex-col h-full`, padding on drag handle, etc.) are preserved.
- [RULE] **AC-1 literal non-compliance** — Rule-checker flagged that `data-archetype` lives on `<html>` not on WidgetWrapper itself. Dismissed because Dev's deviation log justifies this as consistent with the existing archetype-chrome.css pattern for `.character-panel`, `.running-header`, and `.input-area`. The AC is best interpreted as "WidgetWrapper responds to", and the cascade works correctly. Accepted in Deviation Audit above.
- [TYPE] Low-confidence future-drift risk: `ChromeArchetype` union and test file both hardcode the three archetype strings independently. Adding a fourth archetype would not fail any test. Documented in Delivery Findings as an Improvement, but out of scope for trivial story 33-1.
- [SILENT] `--surface` missing from `index.css` `:root` defaults is pre-existing debt inherited by this diff. Non-blocking — pre-existing code relies on the same behavior.
- [SILENT] `--glow-primary` / `--glow-accent` defined only inside `[data-archetype="terminal"]` block (lines 97-98) means the inherited vars cascade correctly into the new terminal widget rules. I traced this: `[data-archetype="terminal"] [data-widget] .widget-drag-handle text-shadow: 0 0 6px var(--glow-primary)` resolves because the `--glow-primary` property is set on a strict ancestor of the drag handle (the `<html>` element when `data-archetype="terminal"` is active), and CSS custom properties inherit by default. Verified in Dev's own Playwright `getComputedStyle` check of the terminal archetype (inset box-shadow value contained the resolved color). Complies.
- [SIMPLE] No subagent returned (disabled). I did not find any dead code or over-engineering in the diff beyond what is already called out above — 120 lines of pure CSS with no redundant declarations.
- [EDGE] No subagent returned (disabled). Manual check: archetype attribute transitions (genre changes) will re-apply rules atomically via the root attribute swap. No boundary conditions in CSS.
- [SEC] No subagent returned (disabled). CSS has no security surface — no JS execution, no injection path, no auth data.

**Devil's Advocate**

Let me argue this code is broken beyond the HIGH finding.

If a user plays `space_opera` (which maps to `terminal` archetype) and the game sets `--accent: #39ff14` (neon green), the `[data-archetype="terminal"] [data-widget] .widget-drag-handle` rule applies `text-shadow: 0 0 6px var(--glow-primary)`. But `--glow-primary` is defined as hardcoded `rgba(0, 255, 255, 0.15)` — cyan, not the accent green. This is a pre-existing mismatch inherited by the new terminal widget rules: the neon glow on widget headers does not match the accent color claimed by the "neon glow border" comment. A user looking at the terminal widget will see a cyan text-shadow on a green-bordered header. Dev's screenshot likely masked this because the test palette used cyan `--primary` directly. This is NOT introduced by the diff — the `--glow-primary` literal predates 33-1 — but the diff's new comment "neon glow border (matches accent color)" is a doubly-false claim: the glow on text uses `--glow-primary` (cyan), not `--accent` (whatever the genre sets). This is a DOCUMENTATION bug reinforcing the existing MEDIUM finding.

If a user plays `mutant_wasteland` (rugged), the `::after` terminal scanline overlay does not apply — correct. The rugged widget will show the thick 3px border, dark inset box-shadow, and accent-tinted header. But the "metal bracket corners" that are promised and commented in the CSS and claimed in the Dev Assessment do not render at all, because they're clipped. A stressed player looking at the rugged widget sees only a generic bordered box. AC-4 is not met.

If the window is resized small, the drag handle becomes cramped and the header's uppercase letterspaced title may wrap or clip. WidgetWrapper sets `truncate` on the title span so text ellipsis applies. The new rules do not break this. OK.

If the user rapidly switches genres, `useChromeArchetype`'s effect cleanup removes and re-sets CSS custom properties. During the swap, `data-archetype` is present but the custom properties may briefly be in a transition state. Cosmetic flash, non-blocking.

Devil's advocate confirms the HIGH finding (rugged corners) and the MEDIUM doc finding, and adds one extra contradiction (the comment claim that the glow "matches accent color" when the glow is cyan). Rolling this into the existing MEDIUM doc finding.

**Data flow traced:** `useChromeArchetype(genreSlug)` → sets `document.documentElement.setAttribute("data-archetype", archetype)` → descendant CSS selectors match on `<html data-archetype="X">` → cascade to `WidgetWrapper`'s rendered `<div data-widget="...">` → new archetype rules apply border, box-shadow, pseudo-element decorations. Chain is intact. Failure mode is in the final pseudo-element rendering (rugged clipping).

**Pattern observed:** [BAD] Pseudo-elements with negative offsets for decoration outside the parent box, combined with a parent that has `overflow: hidden`, is a classic CSS pitfall. This is Dev's introduction of a latent layout failure that was not caught because the visual verification harness did not include any element with negative pseudo-element offsets where clipping would be obvious.

**Error handling:** CSS has no error handling per se. Silent failures (missing vars falling back to empty) are the runtime equivalent — noted as pre-existing debt.

**Handoff:** Back to Dev (Naomi Nagata) for fixes. Findings are CSS-side only (rework via `green` phase, not `red` — no new failing tests to write first).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/styles/archetype-chrome.css` — added three widget chrome rulesets targeting `[data-archetype="X"] [data-widget]` selectors (parchment, terminal, rugged). Each ruleset extends the existing archetype section with widget-specific borders, box-shadows, header treatments, and pseudo-element corner decorations. All colors reference theme CSS vars via `var()` and `color-mix()` — zero hard-coded color values.

**Archetype rules added:**
- **Parchment:** 1px border with warm drop shadow (color-mix from `var(--primary)` at 15% alpha), gradient header blending primary into surface, serif-style `var(--font-ui)`, pseudo-element corner flourishes at top-left/bottom-right (1px L-shapes using `var(--primary)` at 50% opacity).
- **Terminal:** 1px border colored by `var(--accent)`, outer neon glow (8px at 40% alpha) + inset glow (6px at 15% alpha), dark header (`color-mix` of `var(--background)` into `var(--surface)`), uppercase letterspaced title with `text-shadow` using `var(--glow-primary)`, full-widget scan-line overlay via `::after` with 2px repeating gradient from `var(--accent)` at 4% alpha.
- **Rugged:** 3px solid border in `var(--border)`, heavy inset bevel + 3px drop shadow from `var(--background)`, rust-toned header (`color-mix` of `var(--accent)` at 12% into surface), uppercase letterspaced title, pseudo-element metal bracket corners (12x12px L-shapes in `var(--accent)`) at top-left/bottom-right.

**Tests:** 860/872 passing (16/16 archetype CSS tests GREEN; 12 pre-existing failures in `confrontation-wiring.test.tsx` are unrelated to this story and predate the branch). TypeScript compiles clean.

**Visual verification:** Dev server running, cycled `data-archetype` attribute through parchment → terminal → rugged with representative theme vars (low_fantasy, neon_dystopia, road_warrior palettes). All three archetypes render distinctly:
- Computed `border-color` resolves from `var(--border)` / `var(--accent)` per archetype
- Computed `box-shadow` resolves `color-mix()` values correctly against live theme vars
- Corner decorations visible on parchment and rugged; scanlines visible on terminal
- No hard-coded colors in any computed style — all values trace back to the theme vars
- Screenshots saved: `.playwright-mcp/33-1-parchment.png`, `33-1-terminal.png`, `33-1-rugged.png`

**Branch:** `feat/33-1-genre-themed-widget-chrome` (orchestrator; CSS file is in `sidequest-ui` but this is a trivial workflow and the story repos list says `ui` — will commit and push on both repos).

**Handoff:** To review phase (Chrisjen Avasarala / Reviewer).

## Dev Assessment — Round 2 (rework)

**Implementation Complete:** Yes
**Review findings addressed:** 3/3

**Files Changed (rework round):**
- `sidequest-ui/src/styles/archetype-chrome.css`
  - **[HIGH fix]** Rugged `[data-widget]::before` / `::after` offsets changed from `-3px` to `0` — brackets now sit inside the overflow:hidden clip region and actually render. Bracket size increased from 12px to 14px for better visibility, and `z-index: 2` added to ensure they paint above the inset box-shadow bevel layer.
  - **[MEDIUM fix]** Three widget-section inline comments rewritten to use structural language only:
    - Parchment: "primary-tinted drop shadow, L-shaped corner flourishes, primary-into-surface gradient header"
    - Terminal: "accent-colored border with outer + inset accent glow, full-widget scanline ::after overlay, background-dominant (70% background / 30% surface) header with uppercase letter-spaced title"
    - Rugged: "3px solid border with inset bevel, accent-tinted surface header, L-shaped accent brackets at inner top-left and bottom-right corners drawn inside the border box so they survive the parent's overflow:hidden clip"

- `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts`
  - **[MEDIUM fix]** Added new `describe("widget chrome rules")` block with 16 new tests:
    - Per-archetype existence/assertion tests: `[data-widget]` selector present, `box-shadow` declared, widget-drag-handle styled, AC-7 composition guard (no padding/margin/width/height/flex on `[data-widget]` root) — 4 tests × 3 archetypes = 12 tests
    - Parchment corner flourish pseudo-elements exist
    - Terminal scanline `::after` overlay uses `repeating-linear-gradient`
    - Rugged metal bracket pseudo-elements exist
    - **Regression guard:** "rugged section has no negative offsets" — scans the whole rugged archetype section for any `top/left/bottom/right: -Npx` declaration. This directly pins the HIGH finding's root cause and prevents silent regression if a future edit reintroduces negative offsets inside the overflow:hidden clip parent.
  - Added two helper functions `extractRuleBlock` (walks braces to find matching close) and `extractWidgetBlock` (anchors on the literal `[data-widget] {` root selector, not descendant or pseudo-element selectors).

**Tests:** 880/892 passing (16/16 original archetype tests + 16/16 new widget chrome tests = 32/32 in `chrome-archetype-css.test.ts`; 12 pre-existing confrontation-wiring failures unchanged). TypeScript compiles clean.

**Visual verification (round 2):** Re-ran dev server and Playwright, cycled all three archetypes. **Screenshots saved to `.playwright-mcp/33-1-{parchment,terminal,rugged}-rework.png`.** Key verification: I zoomed in on the rugged corners this round to avoid repeating my mistake from round 1.
- **Rugged brackets now visibly render** at top-left and bottom-right of each widget — clear L-shapes just inside the 3px border. `.playwright-mcp/33-1-rugged-rework.png` shows them unmistakably.
- Parchment flourishes still render (unchanged — always worked).
- Terminal scanline overlay still renders (unchanged).
- Computed `::before` values for rugged confirm `top: 0px; left: 0px` positions and `14px × 14px` dimensions, `border-top: 3px`. Inside the box.

**Branch:** `feat/33-1-genre-themed-widget-chrome` (sidequest-ui), updated with rework commit.

**Acknowledgment of round-1 mistake:** In round 1, I wrote Dev Assessment claiming "Corner decorations visible on parchment and rugged" based on a rugged screenshot that showed only the border edge — I mistook the border for bracket decorations. Avasarala was correct: I hadn't verified the brackets actually rendered. Fix: added the regression guard test so future edits cannot silently reintroduce the bug.

**Handoff:** Back to review phase (Chrisjen Avasarala / Reviewer).

## Subagent Results — Round 2

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 880/892 pass (32/32 archetype tests including 16 new widget chrome tests); TSC + lint clean; 12 pre-existing confrontation-wiring failures unchanged |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 2 (vacuous-pass risk in AC-7 composition guard and rugged-section regression guard — both rely on `not.toMatch` against helper-returned strings that could be empty on parse failure), dismissed 1 (low-confidence asymmetry note about extractRuleBlock's empty-string return) |
| 4 | reviewer-test-analyzer | Yes | findings | 3 | confirmed 2 (same vacuous-pass as silent-failure found — independent corroboration, plus a regex false-positive: `\b(top\|left\|bottom\|right)\s*:\s*-\d` matches `border-left: -3px` due to `\b` word-boundary behavior), dismissed 1 (medium implementation-coupling on grouped-selector string matching — nit) |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 1 (low — "inset bevel" in rugged comment is mild linguistic stretch), dismissed 3 (all three other findings target PRE-EXISTING section-header comments at lines 8, 92, 183 and the pre-existing `--glow-primary` rgba literal — none in the round-2 diff, all identified as pre-existing debt in round-1 assessment) |
| 6 | reviewer-type-design | Yes | clean | none | N/A — no type design issues in a pure-CSS + test-helper diff |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none | N/A — **All 12 rules clean across 47 instances.** Rule-checker explicitly validates that all three round-1 findings are mechanically resolved: AC-4 bracket visibility (offsets at 0, inside border box), AC-6 color compliance for new diff, AC-7 composition guard implemented both in CSS and in test. |

**All received:** Yes (9 rows filled; 3 skipped via settings, 6 returned with findings assessed)
**Total findings:** 5 confirmed (2 MEDIUM test-quality, 3 LOW/nit), 8 dismissed (mostly pre-existing debt not in this diff)

## Reviewer Assessment — Round 2

**Verdict:** APPROVED

**All three round-1 findings are resolved:**

1. **[HIGH round-1 — FIXED]** Rugged metal bracket corners now visibly render. Screenshot evidence at `.playwright-mcp/33-1-rugged-rework.png` shows L-brackets clearly drawn at top-left and bottom-right of both widgets, inside the 3px border box. Dev changed pseudo-element offsets from `-3px` to `0`, increased size from 12px to 14px, and added `z-index: 2` to paint above the inset bevel shadow. Computed styles verified: `top: 0px; left: 0px; border-top: 3px`. The fix is mechanical and trivially verifiable.

2. **[MEDIUM round-1 — FIXED]** Three widget-section inline comments rewritten with structural language. New comments at `archetype-chrome.css:47, 146, 230` name the CSS variables and structural techniques used (`color-mix(var(--primary) 15%, transparent)`, `70% background / 30% surface`, `L-shaped accent brackets`, etc.) without any residual color-naming claims. Comment-analyzer confirmed all three rewrites are structurally accurate against the underlying rules.

3. **[MEDIUM round-1 — FIXED]** Added 16 new tests under `describe("widget chrome rules")` in `chrome-archetype-css.test.ts`. Coverage includes: per-archetype widget selector existence, box-shadow on root, widget-drag-handle descendant styling, AC-7 composition guard (no padding/margin/width/height/flex on `[data-widget]` root), parchment/rugged corner pseudo-element existence, terminal scanline `::after` overlay containing `repeating-linear-gradient`, and a **regression guard** scanning the whole rugged section for any negative top/left/bottom/right offsets. Test count went from 16 to 32 in this file, all passing.

**Deviation audit (round 2):** Dev's note "No new deviations from spec" is accepted. The rework is purely corrective — no new architectural choices, no new spec interpretations.

**New findings from round 2 subagent pass (non-blocking, MEDIUM test-quality):**

| Severity | Issue | Location | Recommended Fix |
|----------|-------|----------|-----------------|
| [MEDIUM] [TEST] [SILENT] | **Vacuous-pass risk in AC-7 composition guard and rugged-section regression guard.** Both `extractWidgetBlock` and `extractArchetypeSection` return empty string on parse failure (e.g., if someone later reformats the CSS with a newline before `{`). `expect(empty).not.toMatch(regex)` passes vacuously. The guard that specifically pins the round-1 HIGH finding is vulnerable to silent breakage under hypothetical future CSS reformats. Both silent-failure-hunter and test-analyzer independently flagged this. | `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts:144, 188` | Add `expect(widgetBlock).toBeTruthy()` / `expect(section).toBeTruthy()` (or `.not.toBe("")`) immediately before the `.not.toMatch` assertion. This is a 2-line addition per test and closes the vacuous-pass hole. |
| [MEDIUM] [TEST] | **Regression guard regex has `\b` word-boundary false-positive risk.** The pattern `/\b(top\|left\|bottom\|right)\s*:\s*-\d/` would match `border-left: -3px` because `\b` matches between `-` and `l` in the compound property name. Today, no such declaration exists in the rugged section, so the test passes correctly. But if someone adds `margin-left: -1px` for a legitimate negative margin, the test would false-fail. More subtly, if the actual layout-offset check were intended, it's not correctly isolated from border/margin/padding shorthand property names. | `sidequest-ui/src/__tests__/chrome-archetype-css.test.ts:189` | Replace `\b` with a tighter anchor: `/(?:^\|\s)(top\|left\|bottom\|right)\s*:\s*-\d/m` (line start or whitespace before property) or use a negative lookbehind: `/(?<![\w-])(top\|left\|bottom\|right)\s*:\s*-\d/`. Either form correctly distinguishes standalone `left` from `border-left`. |

**Why these are non-blocking per review rules:**
- The severity table states "Any Critical or High = REJECT." MEDIUM does not block.
- Both issues manifest in HYPOTHETICAL future states (CSS reformats, new negative-margin declarations), not in the current code.
- The tests are currently working as intended — the vacuous-pass would only trigger if the anchor selector strings drift, and the false-positive would only trigger if someone adds a specific kind of negative shorthand value.
- The HIGH finding itself (rugged bracket visibility) is mechanically fixed in CSS; the test is a belt-and-suspenders regression guard on top of that fix.

**I strongly recommend** these be addressed as a small follow-up before the next story in Epic 33 touches this file. Captured as delivery findings below. I am APPROVING this round despite the findings because:
(a) they are about test robustness, not production correctness;
(b) they affect a safety net, not the safety net's primary mechanism (the CSS offset fix stands on its own);
(c) the rework would bounce on test-quality polish is the kind of ceremony this team's trivial workflow is meant to avoid.

**Non-blocking observations (MEDIUM-LOW, captured):**

- [VERIFIED] AC-4 bracket visibility — screenshot at `.playwright-mcp/33-1-rugged-rework.png` confirms brackets render. Computed `::before` values: `top: 0px, left: 0px, width: 14px, height: 14px, border-top: 3px`. Dev's round-1 mistake (misreading the screenshot) is not repeated — this round's evidence is zoomed and unambiguous.
- [VERIFIED] AC-7 composition guaranteed — the root `[data-widget]` rule blocks contain only `position`, `border-*`, and `box-shadow` properties. No padding/margin/width/height/flex. WidgetWrapper's Tailwind layout classes are not overridden.
- [VERIFIED] Regression guard functionality — the current rugged CSS contains `top: 0; left: 0; bottom: 0; right: 0` — the regression regex scans the whole rugged section and finds zero negative offsets. If someone reintroduces `top: -3px`, the regex `\b(top|...)\s*:\s*-\d` matches at position `top: -3`. Works correctly today.
- [RULE] Rule-checker returned clean on all 12 rules across 47 instances. The most important validation: **AC-4 "metal bracket corner accents" explicitly verified compliant** — the rule-checker traced the pseudo-element offsets, border-color, z-index, and positioning and confirmed the brackets sit inside the clip region.
- [DOC] "Inset bevel" in the new rugged comment (css:231) is a mild linguistic stretch — a single 1px inset box-shadow is more accurately an "inset inner stroke" than a bevel. Comment-analyzer confirmed the claim is "not actively misleading." LOW severity, not worth reworking.
- [DOC] Pre-existing section-header comments for parchment ("warm vignette"), terminal ("neon glow"), and the pre-existing `--glow-primary: rgba(0,255,255,0.15)` hardcoded definition still violate the file's structural-only contract. These are all PRE-EXISTING debt not introduced by this story. Already documented in round-1 delivery findings. Not blocking.
- [TEST] Comment-analyzer finding about grouped-selector string matching in test helpers is LOW coupling risk — current CSS uses grouped selectors and tests match accordingly. Acceptable.
- [SIMPLE] Round-2 diff is minimal and surgical — 24 CSS lines changed for the fix, 134 test lines for the coverage. No over-engineering.

**Devil's Advocate (round 2)**

Is the rework actually correct? Let me try to break it.

The rugged bracket at `top: 0; left: 0` with `width: 14px; height: 14px` draws a 14x14 pseudo-element in the top-left corner of the widget's padding box (since the parent has `position: relative` and the pseudo is `position: absolute`). The parent has `border-width: 3px` plus `overflow: hidden`. The pseudo's offsets are relative to the parent's padding-box edge, which is inside the 3px border. So the 14x14 box sits at coordinates (3px from widget edge, 3px from widget edge) measuring 14x14 — well inside the widget body, NOT overlapping the border itself. The L-shape is drawn via `border-top: 3px solid` + `border-left: 3px solid`, so the visible bracket is a 3px-wide L at the pseudo's top-left corner. Subtracting the 3px L from the 14x14 box leaves an 11x11 empty interior. The visible L is drawn from (0,0) to (14,3) horizontal and (0,0) to (3,14) vertical in pseudo-local coordinates, which means (3,3) to (17,6) horizontal and (3,3) to (6,17) vertical in widget-box coordinates. All inside the body — visible, not clipped. ✓

The rugged `widget-drag-handle` spans the top of the widget's body at full width. The top-left bracket sits at widget-box (3,3) to (17,17). The drag handle starts at widget-box y=3 (just inside border) and extends down for its own height. The bracket overlaps the drag handle visually. Is that a problem? The bracket has `pointer-events: none`, so it doesn't block clicks on the drag handle. Visually, the bracket accent color sits over the drag handle's header background (accent-tinted surface). It may look like a small decorative accent inside the drag handle corner — which is arguably a nice visual touch rather than a bug. Dev's screenshot shows the bracket at the top-left corner of the header, which is the intended effect.

The rugged bottom-right bracket at `bottom: 0; right: 0` sits at the bottom-right of the widget body, overlapping the scroll area. Again, `pointer-events: none` so no interaction blocking. `z-index: 2` paints it above the scrollbar thumb if present, but scroll still works. Minor cosmetic stacking; acceptable.

What about when the user minimizes the widget? `WidgetWrapper.tsx` toggles `{!minimized && <body />}`. The body div is conditionally rendered. But the root `[data-widget]` always stays, so the `::before`/`::after` pseudo-elements always render. When minimized, the widget is just the header bar — and the `::before` bracket still sits at top-left of the remaining element. The `::after` at `bottom: 0; right: 0` would sit at the bottom-right of the header-only widget. That's still visible and inside the overflow:hidden clip. Cosmetically correct.

What about keyboard focus? CSS has no focus styles. Not this story's scope.

The two MEDIUM test-quality findings are real but narrow. Nothing else jumps out as broken.

**Data flow traced:** `useChromeArchetype(genreSlug)` → `document.documentElement.setAttribute("data-archetype", "rugged")` → `[data-archetype="rugged"] [data-widget]` selector matches → new CSS rules apply (border-width: 3px, box-shadow bevel, ::before/::after brackets at 0 offset, z-index 2) → brackets rendered inside overflow-hidden clip → visible. Chain intact.

**Pattern observed:** [GOOD] Regression guard test that directly encodes the failure mode of the rejected bug. The existence of the test makes future reviewers aware of the clip constraint, even if they never see the original screenshot. Good institutional memory.

**Error handling:** CSS has no runtime errors. Test helpers return empty string on missing selector (vacuous-pass risk noted above).

**Handoff:** To SM for finish-story.

## Design Deviations

### Dev (implementation)
- **WidgetWrapper does not self-apply the data-archetype attribute; descendant CSS selectors from the document root are used instead.**
  - Spec source: story 33-1 AC-1
  - Spec text: "WidgetWrapper renders `[data-archetype="parchment|terminal|rugged"]` based on useChromeArchetype()"
  - Implementation: Left WidgetWrapper.tsx unchanged. Widget chrome rules are written as `[data-archetype="X"] [data-widget] { ... }`, cascading from the `data-archetype` attribute that `useChromeArchetype` already sets on `document.documentElement` at app level.
  - Rationale: The existing `archetype-chrome.css` already uses this descendant-selector pattern for `.character-panel`, `.running-header`, and `.input-area`. Duplicating the attribute onto every widget would be redundant, create multiple call sites of `useChromeArchetype`, and violate the "don't reinvent — wire up what exists" principle. The visual effect (and acceptance criteria AC-2, AC-3, AC-4) is achieved identically.
  - Severity: minor
  - Forward impact: none — the attribute is still present in the DOM (on `<html>`), so any future code that reads `data-archetype` from an ancestor selector works unchanged.
  - **→ ✓ ACCEPTED by Reviewer:** Agrees with author reasoning. The existing archetype-chrome.css pattern for `.character-panel`, `.running-header`, and `.input-area` all use descendant selectors from the root `[data-archetype="X"]` attribute set by `useChromeArchetype` on `document.documentElement`. Duplicating the attribute onto every WidgetWrapper instance would violate the codebase's established pattern, create multiple hook call sites, and add no functional value. AC-1's literal text ("WidgetWrapper renders [data-archetype=...]") is best interpreted as "WidgetWrapper responds to [data-archetype=...]", consistent with the existing structural pattern. The rule-checker flagged this as literal non-compliance (AC-1 finding) — I am confirming the deviation is sound and dismissing the finding.

### Reviewer (audit)
- No undocumented deviations discovered beyond the one Dev logged above.

### Dev (implementation) — Round 2 (rework)
- No new deviations from spec. The rework aligns the implementation closer to the ACs:
  - Rugged corner brackets now actually render (AC-4 satisfied by visible output, not just CSS declarations).
  - Structural-language comments align with the file header's stated contract.
  - New tests provide content assertions for the 80+ new CSS lines.
  - **→ ✓ ACCEPTED by Reviewer (round 2):** No deviations introduced. The round-2 changes are purely corrective and the rework addresses all three round-1 findings mechanically. Rule-checker confirmed clean across 47 instances.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 860/872 pass, 12 pre-existing failures confirmed, TSC + lint clean |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 1 (z-index stacking cosmetic, LOW), dismissed 2 (both pre-existing debt — `--surface` missing global default and `--glow-primary` scoped only to terminal block — neither introduced by this diff) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 1 (no dedicated tests for new [data-widget] rules, MEDIUM), dismissed 3 (pre-existing extractArchetypeSection fragility, pre-existing --glow-* hardcoded literals, AC-5 playtest verification is out of static-analysis scope), deferred 1 (composition layout assertion — good suggestion, not blocking trivial workflow) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 5 — all four "lying-docstring" findings on new inline comments ("warm shadow", "off-white header", "dark header", "rust-toned header") are valid per the file's explicit structural-only contract at lines 3-4; rolled up as ONE MEDIUM finding |
| 6 | reviewer-type-design | Yes | findings | 1 | dismissed 1 (low-confidence future-drift — tests hardcode archetype string literals; out of scope for trivial story and not a current bug) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 9 | confirmed 1 (AC-1 attribute-on-html deviation is literal non-compliance but architecturally sound — see Deviation Audit below), dismissed 8 (six AC-6 rgba-literal violations are all in PRE-EXISTING code lines 18/97-98/110-111/113/191 not in this diff; two semantic "off-white"/"rust-toned" AC-lawyering dismissed as unverifiable by static analysis for genre-dependent theme vars) |

**All received:** Yes (9 rows filled; 3 skipped via settings, 6 returned with findings)
**Total findings:** 8 confirmed / rolled up into 4 distinct issues; 16 dismissed with rationale; 1 deferred

**Reviewer's independent finding (not from subagents):**
- **[HIGH] Rugged metal bracket corners are CLIPPED and do not render.** The new `[data-archetype="rugged"] [data-widget]::before` and `::after` rules at `archetype-chrome.css:256,263` use negative offsets (`top: -3px; left: -3px` / `bottom: -3px; right: -3px`) to place 3px L-brackets outside the widget's border box. But `WidgetWrapper.tsx:27` applies Tailwind's `overflow-hidden` to the widget root, which clips ALL pseudo-element content outside the box. Screenshot evidence at `.playwright-mcp/33-1-rugged.png` confirms: there are NO metal bracket corners visible in the rendered rugged widgets, only the 3px solid border and header tint. Dev claimed "Corner decorations visible on parchment and rugged" in the Dev Assessment (line 93), but the rugged screenshot proves otherwise — Dev misread the visual output. This violates AC-4: "metal bracket corner accents." The subagents missed this because they analyzed CSS in isolation without cross-referencing WidgetWrapper's class list.

## Implementation Notes

### Related Files
- `sidequest-ui/src/components/WidgetWrapper.tsx` — wrapper component applying [data-archetype] attribute
- `sidequest-ui/src/hooks/useGenreTheme.ts` — CSS var definitions
- `sidequest-ui/src/hooks/useChromeArchetype.ts` — archetype selection hook
- `sidequest-ui/src/styles/` — where archetype CSS rules should live
- Playtest on: space_opera, neon_dystopia, low_fantasy (verify cross-genre consistency)

### Testing Strategy
1. Verify WidgetWrapper correctly reads and applies [data-archetype] attribute
2. Test each archetype on at least 3 genre packs to ensure colors and shadows compose correctly
3. Check widget resize/drag interaction doesn't break visual styling
4. Verify on both light and dark backgrounds (genre-dependent)

---

**Next step:** Transition to dev phase. Dev will implement the CSS rules and verify styling across genre packs.