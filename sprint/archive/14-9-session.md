---
story_id: "14-9"
jira_key: ""
epic: "14"
workflow: "tdd"
---

# Story 14-9: Footnote inline references — connect footnote markers in text to numbered footnotes below

## Story Details

- **ID:** 14-9
- **Epic:** 14 (Multiplayer Session UX)
- **Workflow:** tdd
- **Points:** 2
- **Priority:** p2
- **Stack Parent:** none
- **Repos:** sidequest-ui

## Story Context

**Current State:**
- Footnotes are parsed on the server and included in NARRATION payloads with a `marker` number and `summary` text
- The UI displays footnotes below narration blocks in a small footnote section
- Footnote markers in the prose text itself ([1], [2], etc.) are stripped during markdown rendering (line 69 in NarrativeView.tsx)
- Footnotes currently display but aren't linked to anything — clicking a marker number does nothing

**Acceptance Criteria:**
1. Parse footnote markers [N] from narration prose during markdown rendering
2. Render markers as superscript, numbered links (e.g., ¹, ², ³)
3. Links scroll to the corresponding numbered footnote entry below the narration block
4. Links should be keyboard accessible (tab/enter to scroll)
5. On scroll, the target footnote should have visual indication (highlight or background)
6. Both text segments and portrait-group segments should support linked footnotes
7. Graceful fallback if marker numbers don't match footnote data

## Workflow Tracking

**Workflow:** tdd  
**Phase:** finish  
**Phase Started:** 2026-03-31T11:22:36Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31 | 2026-03-31T10:38:44Z | 10h 38m |
| red | 2026-03-31T10:38:44Z | 2026-03-31T10:42:07Z | 3m 23s |
| green | 2026-03-31T10:42:07Z | 2026-03-31T10:44:19Z | 2m 12s |
| spec-check | 2026-03-31T10:44:19Z | 2026-03-31T11:22:33Z | 38m 14s |
| review | 2026-03-31T11:22:33Z | 2026-03-31T11:22:36Z | 3s |
| finish | 2026-03-31T11:22:36Z | - | - |

## Technical Notes

- NarrativeView.tsx handles markdown rendering and footnote display
- `markdownToHtml()` currently strips footnote markers — needs to preserve and link them
- Footnote markers come from server in the `footnotes` array as `marker?: number`
- Portrait-group segments have footnotes on the text portion (`txt.footnotes`)
- Use a ref-based scroll mechanism (e.g., `useRef` + `element.scrollIntoView()`) for navigation
- Consider using CSS `id` anchors (e.g., `footnote-1`) for stable link targets

## Delivery Findings

No upstream findings.

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- No upstream findings during implementation.

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `src/screens/NarrativeView.tsx` — converted footnote marker stripping to superscript link generation; added `id`, `data-footnote-id`, and `target:bg-accent/20` to footnote entry divs (both text and portrait-group segments)

**Tests:** 16/16 passing (GREEN), 76/76 total NarrativeView tests passing (no regressions)
**Branch:** feat/14-9-footnote-inline-references (pushed)

**Changes:**
1. `markdownToHtml()`: replaced `.replace(/\[\^?\d+\]/g, "")` (strip) with `.replace(/\[\^?(\d+)\]/g, '<sup><a href="#footnote-$1">$1</a></sup>')` (link)
2. Footnote entry divs: added `id="footnote-{N}"`, `data-footnote-id={N}`, `target:bg-accent/20` class, `scroll-mt-4` for scroll offset
3. Applied to both text segment and portrait-group segment footnote rendering

**Handoff:** To next phase (verify or review)

## TEA Assessment

**Tests Required:** Yes
**Reason:** New feature — footnote inline references need marker parsing, link rendering, and scroll behavior.

**Test Files:**
- `src/screens/__tests__/NarrativeView-footnotes.test.tsx` — 16 tests covering all 7 ACs

**Tests Written:** 16 tests covering 7 ACs
**Status:** RED (14 failing, 2 passing — fallback cases work with existing code)

### AC Coverage

| AC | Tests | Status |
|----|-------|--------|
| AC-1: Parse markers from prose | 4 tests (single, caret-style, multiple, not-stripped) | failing |
| AC-2: Superscript numbered links | 2 tests (anchor in sup, href to anchor) | failing |
| AC-3: Scroll to footnote entry | 2 tests (id on entry, unique ids) | failing |
| AC-4: Keyboard accessible | 2 tests (focusable, semantic anchor) | failing |
| AC-5: Target highlight | 1 test (CSS :target or data attribute) | failing |
| AC-6: Portrait-group support | 1 test (linked markers in portrait text) | failing |
| AC-7: Graceful fallback | 3 tests (unmatched marker, null marker, empty array) | 2 pass, 1 fail |
| XSS safety (TS rule #6) | 1 test (script injection with markers) | failing |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 React/JSX dangerouslySetInnerHTML | XSS safety test | failing |
| #4 Null/undefined handling | null marker fallback test | passing |

**Rules checked:** 2 of 13 applicable TS lang-review rules have test coverage (others not applicable to this UI feature)
**Self-check:** 0 vacuous tests found

**Handoff:** To Yoda (Dev) for implementation

## Sm Assessment

**Story 14-9** is a 2-point p2 story. UI-only — parse footnote markers from narration text, render as superscript links, scroll to corresponding footnote entries. Key file is NarrativeView.tsx. TDD workflow, routing to TEA (Han Solo) for RED phase.