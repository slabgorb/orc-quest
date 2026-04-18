---
story_id: "33-7"
epic: "33"
workflow: "trivial"
---
# Story 33-7: Character panel header — portrait, level, archetype display

## Story Details
- **ID:** 33-7
- **Epic:** 33
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-15T22:15:21Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-15T18:05Z | 2026-04-15T22:05:03Z | 4h |
| implement | 2026-04-15T22:05:03Z | 2026-04-15T22:08:38Z | 3m 35s |
| review | 2026-04-15T22:08:38Z | 2026-04-15T22:15:21Z | 6m 43s |
| finish | 2026-04-15T22:15:21Z | - | - |

## Target
Replace header markup in `sidequest-ui/src/components/CharacterPanel.tsx` (lines 96–116) with three-column layout:
1. Portrait slot: 48px circular placeholder (fills with actual portrait from 33-2 when available)
2. Meta column: character name in accent color + subtitle combining class + genre with `·` separator
3. Level badge: compact chip showing `Lv {level}`, right-aligned

**Design constraint:** Stay flat enough for 33-10 (conditions/wounds) to inject a row below without fighting the layout.

## SM Assessment

**Story ready for implementation.**

- **Scope:** Trivial 3-point UI polish story. Single-file change in `CharacterPanel.tsx` (lines 96-116), replacing the current header markup with a three-column layout (48px circular portrait slot, name+subtitle column, level badge chip).
- **Context:** Full story context written to `sprint/context/context-story-33-7.md` with technical guardrails, scope boundaries, AC breakdown, and visual constraints. Parent epic context `context-epic-33.md` already exists.
- **Repo:** `sidequest-ui` only. No API / daemon / content changes. Personal-project rules apply: no Jira, no 1898 org, branch off develop → PR to develop.
- **Key constraints flagged in context:**
  - Colors from CSS vars only (two-layer theming is load-bearing).
  - Portrait slot always rendered even without URL — no layout shift when 33-2 lands.
  - Genre display name must come from existing context/theme — do NOT thread new props through widget registry. Flag as design deviation if impossible.
  - Wiring test required per project rule.
- **Out of scope:** Portrait image generation (33-2), conditions/wounds (33-10), stat highlighting (33-8), new UI kit primitives.
- **Acceptance:** 7 ACs in context doc, all unit-testable in CharacterPanel.test.tsx plus one integration wiring test.

**Handoff to Dev (Naomi Nagata) for implement phase.**

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/CharacterPanel.tsx` — replaced header block (lines 96-116) with three-column enriched header: circular 48px portrait slot (img or initials placeholder), name + "Class · Genre" subtitle, and bordered "Lv N" badge chip.
- `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx` — added 7 new cases under "33-7: enriched header" describe block covering layout structure, placeholder rendering, badge content, subtitle composition, sizing, and name accent color.

**Tests:** 1122/1122 passing (37/37 CharacterPanel file). Lint clean (0 errors, 1 pre-existing warning in unrelated ImageBusProvider.tsx). Typecheck clean.

**Branch:** `feat/33-7-character-panel-header` pushed to origin.

**Scope wins flagged in context held up:**
- `genreSlug` was already threaded through `GameBoard → CharacterWidget → CharacterPanel` — no new prop plumbing needed, as anticipated.
- `toAvatarInitials` and `toDisplayName` helpers already in the file, reused directly.
- Two-layer theming preserved: all colors read `var(--primary)` and `var(--surface)` from the cascade.
- 33-10 headroom preserved: header row is flat (portrait · meta · badge); a conditions row can slot below the name without restructuring.

**Handoff:** To Reviewer (Chrisjen Avasarala) for review phase.

## Delivery Findings

- No upstream findings during implementation.

## Design Deviations

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 0, dismissed 3, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 3, dismissed 2, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | confirmed 1, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | findings | 5 | confirmed 0, dismissed 2, deferred 3 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 | confirmed 0, dismissed 0, deferred 3 |

**All received:** Yes
**Total findings:** 4 confirmed, 7 dismissed (with rationale), 4 deferred

## Reviewer Assessment

**Decision:** CHANGES REQUESTED → APPLIED → APPROVED

### Confirmed (must-fix, applied during review)

1. **[TEST] Test-analyzer #1 — `toHaveTextContent("Lv 3")` is substring match** (high confidence)
   - Rule source: `PROJECT_RULES` passed to test-analyzer, verbatim: "toHaveTextContent is substring-matching by default — 'Lv 3' matches 'Lv 3000'; use exact match when numbers matter."
   - Cannot dismiss under `<critical>PROJECT RULES ARE NOT SUGGESTIONS</critical>` — rule-matching finding with no contradicting rule.
   - Fix: change to exact regex `/^Lv 3$/`.

2. **[DOC] Comment-analyzer #1 — Removed `current_location` rationale comment** (high confidence)
   - Load-bearing documentation of why the field exists on the type but is not rendered. House style at lines 74-75 keeps the analogous "Backstory removed" one-liner — the location comment should follow the same pattern.
   - Fix: restore condensed one-liner comment matching house style.

3. **[TEST] Test-analyzer #2 — `header.children.length === 3` couples to DOM structure** (high confidence)
   - Future tooltip/fragment wrapper will break this without changing behavior.
   - Fix: query by testid/role for the three meaningful pieces instead of counting raw children.

4. **[TEST] Test-analyzer #4 (partial) — Missing two-word initials case** (medium confidence)
   - Cheap to add, protects `toAvatarInitials` branch that single-word test doesn't cover.
   - Fix: add two-word name test.

### Dismissed (with rationale)

5. **[SILENT] Silent-failure #1 — `level: 0` renders "Lv 0"** (medium confidence) → **DISMISSED**
   - Rationale: `character.level: number` is typed by the protocol contract, and `Lv 0` is the correct render for a genuine level-0 character. The concern is a data-integrity question for the WebSocket boundary, not a UI concern. Out of scope for 33-7. No project rule mandates display guarding on numeric fields.

6. **[SILENT] Silent-failure #2 — `toAvatarInitials("")` renders empty placeholder** (high confidence) → **DISMISSED**
   - Rationale: `character.name: string` is non-optional per type. An empty-string name is a protocol-boundary violation, not a UI concern. The empty circle renders cleanly (no crash, no layout break). Handling empty name in the UI would mask the real upstream problem — violates the project's "No Silent Fallbacks" principle. Defer enforcement to WebSocket deserialization.

7. **[SILENT] Silent-failure #3 — `genreSlug === ""` silently drops genre segment** (medium confidence) → **DISMISSED**
   - Rationale: Treating empty-string as absent is the correct display behavior — the subtitle-fallback test already covers it. The pre-existing `genreSlug ?? ""` at line 153 (StatusContent, pre-existing, not in diff) has a separate semantics for SFX routing; aligning the two call sites is a design question outside this story. Filed as a follow-up note, not a blocker.

8. **[TEST] Test-analyzer #3 — Subtitle fallback test `getByText(/Ranger/)` could match `<h2>`** (high confidence) → **DISMISSED**
   - Rationale: The test data `CHARACTER.name = "Kael"` → `<h2>Kael</h2>`. The string "Ranger" appears only in the subtitle, never in the heading. `getByText(/Ranger/)` will match the subtitle `<p>`, and will THROW if that element is removed (testing-library's default behavior). The test does protect against subtitle deletion. The subagent's concern applies only if a future test changes the name to something containing "Ranger" — that would be a test-data problem, not a logic bug in this assertion.

9. **[TEST] Test-analyzer #6 — Wiring test only checks module export** (medium confidence) → **DISMISSED**
   - Rationale: `CharacterWidget.tsx` is a confirmed 6-line passthrough that renders `CharacterPanel`. The rule-checker independently verified this (rule 15, "wiring is real"). The existing export test plus the GameBoard integration path (GameBoard.tsx:305 renders CharacterWidget) satisfies the project rule. Adding a redundant integration test here is ceremony without protection.

### Deferred (pre-existing or out-of-diff)

10. **[TEST] Test-analyzer #5 — Missing level=0 test** (low confidence) → **DEFERRED**
    - Edge case worth documenting but not load-bearing for this story's ACs.

11. **[TYPE] Type-design #4 — `character.class: string` stringly-typed** (low confidence) → **DEFERRED (pre-existing)**
    - Tech debt on `CharacterSheetData`, not introduced by this diff. Candidate for a future branded-type chore story.

12. **[TYPE] Type-design #2 — `portrait_url: ""` divergence from `CharacterSheet.tsx`** (medium confidence) → **DEFERRED (pre-existing)**
    - `CharacterSheet.tsx:27` uses `&&` without placeholder fallback. Inconsistency is pre-existing; 33-7 only touches `CharacterPanel.tsx`. Flagged for a future consistency pass — file as a follow-up chore.

13. **[TYPE] Type-design #5 — Party row line 210 renders `c.class` raw without `toDisplayName`** (high confidence, pre-existing) → **DEFERRED**
    - Legitimate bug in sibling code untouched by this diff. Party rows will display snake_case class identifiers inconsistently with the new header. **Filed as a finding for a follow-up patch/chore — do not bundle into this PR.**

14. **[RULE] Rule-checker #1-3 — `bg-green-500`/`bg-amber-500`/`bg-red-500` on HP bar (lines 215-217)** → **DEFERRED (pre-existing)**
    - Hardcoded Tailwind palette colors violating the CSS-var rule. Pre-existing, not in diff. Filed as a follow-up for an epic-33 polish chore.

### Applied fixes

See commit `{pending}` on branch `feat/33-7-character-panel-header`:
- `test.tsx`: exact regex for "Lv 3" badge assertion
- `test.tsx`: replaced `children.length === 3` with testid/role queries
- `test.tsx`: added two-word-name initials test ("Lyra Dawnforge" → "LD")
- `CharacterPanel.tsx`: restored condensed one-liner comment explaining `current_location` omission

### Post-fix verification

- 1122→1123 tests passing (one new two-word-name test added)
- Lint clean
- TypeScript clean

### Delivery Findings (added by reviewer)

- **Improvement** (non-blocking): Party row at `sidequest-ui/src/components/CharacterPanel.tsx:210` renders `c.class` raw without `toDisplayName`, inconsistent with the new header treatment. Affects `CharacterPanel.tsx` (party-member-row rendering). *Found by Reviewer during 33-7 review.*
- **Improvement** (non-blocking): `CharacterPanel.tsx:215-217` uses hardcoded Tailwind palette colors (`bg-green-500`/`bg-amber-500`/`bg-red-500`) for HP bar states, violating the CSS-var rule. Affects `CharacterPanel.tsx` HP indicator. *Found by Reviewer during 33-7 review.*
- **Improvement** (non-blocking): `CharacterSheet.tsx:27` uses `portrait_url &&` without placeholder fallback, now divergent from `CharacterPanel.tsx:98` behavior. Affects `CharacterSheet.tsx` portrait slot. *Found by Reviewer during 33-7 review.*

### Dev (implementation)

- **Portrait placeholder uses initials instead of lozenge glyph**
  - Spec source: `sprint/context/context-story-33-7.md`, Technical Guardrails section + mockup `.playwright-mcp/mockups/epic-33-panel-improvements.html#s33-7`
  - Spec text: "render a circular div at the same 48px footprint with a centered glyph (mockup uses `◈` / Lozenge U+25C8)"
  - Implementation: Rendered `toAvatarInitials(character.name)` (e.g. "K" for "Kael", "SV" for "Sable Vostok") in the placeholder div, centered, same 48px footprint.
  - Rationale: The `toAvatarInitials` helper was already defined in `CharacterPanel.tsx` (lines 49-54) with a comment explaining its 2-char cap for avatar badges — it exists for exactly this purpose and was previously unused. Initials carry character identity (they read as "this is Kael"), while the lozenge glyph `◈` is generic decoration that reads the same for every character. The spec's visual constraint (48px circle, accent color, surface bg) is preserved; only the centered content differs. Aligns with "wire up what exists" principle from project CLAUDE.md.
  - Severity: cosmetic (minor)
  - Forward impact: minor — if 33-2 (portrait system) later wants to show a spinner or loading state before image is ready, the placeholder can swap back to a glyph at that point. No downstream story assumes the lozenge specifically.