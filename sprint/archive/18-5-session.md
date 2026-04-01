---
story_id: "18-5"
jira_key: ""
epic: "18"
workflow: "tdd"
---
# Story 18-5: Structured NPC Registry and Inventory Panels in State Tab

## Story Details
- **ID:** 18-5
- **Jira Key:** (personal project, not tracked)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p1

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-01T07:59:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-01T03:45:00Z | 2026-04-01T07:41:58Z | 3h 56m |
| red | 2026-04-01T07:41:58Z | 2026-04-01T07:45:12Z | 3m 14s |
| green | 2026-04-01T07:45:12Z | 2026-04-01T07:50:52Z | 5m 40s |
| spec-check | 2026-04-01T07:50:52Z | 2026-04-01T07:52:02Z | 1m 10s |
| verify | 2026-04-01T07:52:02Z | 2026-04-01T07:54:25Z | 2m 23s |
| review | 2026-04-01T07:54:25Z | 2026-04-01T07:58:47Z | 4m 22s |
| spec-reconcile | 2026-04-01T07:58:47Z | 2026-04-01T07:59:36Z | 49s |
| finish | 2026-04-01T07:59:36Z | - | - |

## Story Context

The State tab currently dumps `GameState` as raw JSON, which is unreadable for NPCs and inventory. The game's entity model is fully implemented:

- **NPCs:** NpcInstance structs in game state, tracked by NPC ID with attributes (name, location, state)
- **Inventory:** Character inventory, equipment slots, item conditions — all modeled in GameState

The UI receives `GameStateSnapshot` events via OTEL (wired in 18-2). This story converts those snapshots into structured tables:

1. **NPC Registry Panel** — table showing all NPCs: ID, Name, Location, State, Attributes
2. **Inventory Panel** — table showing equipment/items: Slot, Item Name, Condition, Properties

This is a visualization-only story — the data model is ready, just needs UI representation.

### Acceptance Criteria
1. State tab has "NPC Registry" and "Inventory" subtabs
2. NPC Registry shows table with: ID | Name | Location | State | (expandable attributes)
3. Inventory shows table with: Slot | Item | Condition | Weight | (expandable properties)
4. Search/filter works on both tables (by NPC name, item name)
5. Tables handle empty state gracefully (no NPCs, empty inventory)
6. OTEL events flow correctly to dashboard (events already emitted from backend, just need UI to render)

## Sm Assessment

Story 18-5 is a UI-only visualization story scoped to the State tab in the OTEL dashboard. The backend data model (NpcInstance, inventory structs) and OTEL event pipeline (GameStateSnapshot) are already wired from stories 18-2 and 18-4. This story converts raw JSON dumps into structured NPC registry and inventory tables with search/filter.

**Routing:** TDD workflow → TEA (red phase) writes failing tests for the two table components, then Dev (green phase) implements.

**Risk:** Low. Data pipeline exists; this is pure UI rendering. The 3-point estimate is appropriate.

## TEA Assessment

**Tests Required:** No
**Reason:** Chore bypass — pure presentation JS in untestable format

This story enhances existing NPC registry and inventory panels in `scripts/playtest.py` (vanilla JS inline in a Python string literal). The orchestrator repo has no JS test framework (no vitest, jest, or playwright). The JS is not importable or extractable without a major refactor out of scope for this story.

**Evidence for bypass:**
1. All code changes target inline JS in `scripts/playtest.py` — no test harness exists
2. Prior dashboard stories (18-4, 18-6) only tested Rust backend changes; none tested inline JS
3. This story has zero backend changes — no new types, no new WatcherEventType variants
4. Features are all presentation: sort comparators, color thresholds, click handlers, filter functions

**What the story actually needs (for Dev):**
The State tab already renders NPC registry and inventory tables (lines 644-654 and 619-628 of `scripts/playtest.py`). The ACs add:
- Disposition column with color-coding: green (>10), gray (neutral), red (<-10)
- Sortable NPC table (name, disposition, location) — click column header to sort
- Row expansion — click NPC/item row to show full JSON detail
- Search/filter input for NPC names and item names
- HP column in NPC table (bar or fraction)

**Critical finding:** Story says `repos: ui` but code lives in `scripts/playtest.py` (orchestrator). Story context lists React component paths that don't exist. Dev must work in `scripts/playtest.py`.

### Rule Coverage

| Rule | Applicable? | Notes |
|------|-------------|-------|
| JS #1 silent errors | Yes — at review | No tests possible; reviewer should check |
| JS #4 equality | Yes — at review | `==` vs `===` in new comparators |
| JS #5 DOM security | Yes — at review | `innerHTML` with `esc()` — existing pattern, verify new code uses it |
| JS #8 test quality | N/A | No tests to check |

**Rules checked:** 3 of 13 JS rules applicable; none testable without framework
**Self-check:** N/A (no tests written)

**Handoff:** To Dev (Yoda) for implementation in `scripts/playtest.py`

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `scripts/playtest.py` — Enhanced State tab with structured NPC registry (disposition color-coding, HP, sortable columns, row expansion) and inventory (description column, click-to-expand, filter). Added search/filter input. Added helper functions (npcDispositionColor, npcDispositionLabel, sortNpcs, toggleNpcExpand, toggleItemExpand). Added state vars (npcSort, expandedNpcs, expandedItems).

**Tests:** N/A (TEA chore bypass — no test framework for inline JS)
**Branch:** feat/18-5-npc-registry-inventory-otel (pushed)

**AC Coverage:**
1. NPC table renders with all active NPCs — ✅ enriched from npc_registry + npcs
2. Disposition color-coded — ✅ green (>10), gray (-10..10), red (<-10) per ADR-020
3. Inventory table per character with evolution stages — ✅ (pre-existing, enhanced with description + expand)
4. Gold displayed per character — ✅ (pre-existing)
5. Sortable NPC table — ✅ name, disposition, location with ▲/▼ indicators
6. Row expansion — ✅ click NPC or item row shows full JSON
7. Search/filter — ✅ filters both NPC registry (name, role, location) and inventory (item name)
8. Empty state — ✅ "No NPCs in registry yet" message when no NPCs

**Handoff:** To next phase (verify or review)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All 7 story context ACs verified against the code diff:
1. NPC table renders — ✅ npc_registry enriched via s.npcs cross-reference
2. Disposition color-coded — ✅ ADR-020 thresholds (>10 green, <-10 red) in `npcDispositionColor`
3. Inventory with evolution stages — ✅ pre-existing + enhanced with description column and expand
4. Gold per character — ✅ pre-existing, untouched
5. Sortable (name, disposition, location) — ✅ `sortNpcs()` with ▲/▼ indicators
6. Row expansion — ✅ `toggleNpcExpand` / `toggleItemExpand` with full JSON
7. Depends on 18-2 — ✅ "Waiting for GameStateSnapshot..." guard

**Dev's deviation** (cross-reference enrichment) is well-documented and architecturally sound — NpcRegistryEntry lacks disposition/HP fields, so the lookup into s.npcs is the correct approach.

**TEA findings acknowledged:** Repos field misconfiguration (ui → orchestrator) and session AC/context AC drift are non-blocking documentation issues. No code changes needed.

**Decision:** Proceed to review

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 1 (scripts/playtest.py)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | All pre-existing patterns (switchTab dispatch, event handlers, progress bars) — none in 18-5 diff |
| simplify-quality | clean | No issues found |
| simplify-efficiency | 3 findings (all low) | Color map DRY, DOM caching, filter pattern — all low-confidence, dismiss |

**Applied:** 0 high-confidence fixes (reuse findings target pre-existing code, not 18-5 changes)
**Flagged for Review:** 0 medium-confidence findings in 18-5 scope
**Noted:** 6 low-confidence observations (all pre-existing patterns)
**Reverted:** 0

**Overall:** simplify: clean (no actionable findings in story scope)

**Quality Checks:** Python syntax passes. Orchestrator repo has no lint/typecheck/test infrastructure (package.json lint is a no-op echo).
**Handoff:** To Reviewer for code review

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Story repos field is `ui` but all changes target `scripts/playtest.py` in the orchestrator repo. Story context lists non-existent React component paths (`sidequest-ui/src/components/Dashboard/tabs/State/NpcPanel.tsx` etc). Dev should work in `scripts/playtest.py`, not create React components.
  Affects `sprint/epic-18.yaml` (repos field) and `sprint/context/context-story-18-5.md` (Key Files section).
  *Found by TEA during test design.*
- **Gap** (non-blocking): Session ACs (#1-4) reference "subtabs", "ID column", "Slot column", "Condition column" that don't match the existing State tab structure or the story context ACs. Dev should follow the story context ACs (which reference disposition, sortable, row expansion) as spec authority, not the session ACs.
  Affects `.session/18-5-session.md` (Acceptance Criteria section).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test verification)
- No upstream findings during test verification.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | No code smells, valid syntax, 5 new functions | N/A |
| 2 | reviewer-security | Yes | findings | XSS via single-quote injection in onclick handlers (lines 665, 734) | Fix required — FIXED in 7068e8a |
| 3 | reviewer-edge-hunter | Yes | findings | Same onclick issue (high), expand key collision (medium), filter asymmetry (medium) | onclick fixed; medium items noted, non-blocking |
| 4 | reviewer-rule-checker | Yes | clean | JS lang-review rules checked inline during security scan; no violations in new code | N/A |
| 5 | reviewer-silent-failure-hunter | Yes | clean | No error handling, catches, or fallbacks in new code — pure presentation logic | N/A |

All received: Yes (5/5 subagents returned results)

## Reviewer Assessment

**Verdict:** REJECT — 1 blocking finding, 2 non-blocking observations

### Blocking

- **Single-quote injection in onclick handlers** (lines 665, 734)
  `esc()` escapes HTML entities (`<`, `>`, `&`, `"`) but NOT single quotes. The onclick attributes use single-quoted JS strings: `onclick="toggleNpcExpand('${esc(n.name)}')"`. Any NPC or item name with an apostrophe (e.g., "O'Brien", "Kira's Guard") will break the JS string literal, crashing expand/collapse.
  **Fix:** Replace `'${esc(name)}'` with `${JSON.stringify(name)}` in both onclick attributes. `JSON.stringify` produces double-quoted strings with proper escaping of all special characters. Two lines to change:
  - Line 665: `onclick="toggleItemExpand(${JSON.stringify(c.name)},${JSON.stringify(item.name||String(item))})"`
  - Line 734: `onclick="toggleNpcExpand(${JSON.stringify(n.name)})"`

### Non-blocking observations

- **Expand state key collision** (medium): `S.expandedNpcs` is keyed by exact name but enrichment lookup is case-insensitive. Two NPCs differing only in case would share expand state. Unlikely in practice — note for awareness.
- **Filter asymmetry** (medium): Character cards are hidden when filter matches no items, even if character name matches. NPC registry filters by name/role/location. Different filtering philosophies — acceptable UX trade-off since character cards are item-focused.

**Action required:** Dev fixes the two onclick lines, commits, pushes. Then re-submit for review.

### Re-review (commit 7068e8a)

**Verdict:** APPROVE

Both onclick handlers now use `JSON.stringify()` instead of single-quoted `esc()` strings. Fix is correct — `JSON.stringify` produces escaped double-quoted strings that handle apostrophes, backslashes, and all special characters. Python syntax verified. No new issues introduced.

[RULE] JS lang-review checklist: No violations. `===` used throughout, `esc()` applied to all innerHTML content, no empty catches, no floating promises, no eval(). `JSON.stringify` fix addresses the only DOM security finding.

[SILENT] No silent failure patterns in new code. Pure presentation logic — no try/catch, no error swallowing, no fallback paths. Null/undefined guards use `||''` and `??0` patterns consistently.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **NPC data enrichment via cross-reference instead of single source**
  - Spec source: context-story-18-5.md, Technical Approach
  - Spec text: "All data already exists on GameSnapshot: snapshot.npcs[]"
  - Implementation: Used npc_registry as primary source, cross-referenced s.npcs by name for disposition/HP enrichment. NpcRegistryEntry lacks disposition/HP fields, so lookup is needed.
  - Rationale: npc_registry is the existing data source for the NPC table; npcs may not always have matching entries. Cross-reference preserves existing behavior while adding new columns.
  - Severity: minor
  - Forward impact: none — display-only change

### Architect (reconcile)
- No additional deviations found.

**Deviation audit notes:**
- TEA (test design): "No deviations" — correct. Test bypass documented in TEA Assessment with justification (no test framework for inline JS). Not a spec deviation.
- Dev (implementation): Cross-reference enrichment — verified. Spec source quote matches `context-story-18-5.md:19`. Implementation description accurate. All 6 fields present and substantive. Forward impact correctly assessed as none.
- No AC deferrals to reconcile (all ACs marked DONE in Dev Assessment).