---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-7: Save Migration + UI Composure Sheet + Real Wiring Test

## Business Context

Three jobs at once because they all block the acceptance playtest (39-8):

1. **Save migration.** Bump Sqlite schema in `persistence.rs` and synthesize `EdgePool`
   from legacy HP fields: `base_max = class_base_from_legacy_hp_formula / 2`. Documented
   heuristic — Edge is not HP and shouldn't inherit HP's numeric magnitude.
2. **UI composure sheet.** React character sheet reads `edge / max_edge / composure_state`
   declaratively from `stat_display_fields`. Replaces the HP bar with a composure bar.
   `composure_state` is a frontend-derived enum (Fresh / Strained / Cracked / Broken)
   from the current/max ratio; not persisted.
3. **Fix the false-positive wiring test.** Rewrite
   `beat_dispatch_wiring_story_28_5_tests.rs` from regex-source-matching to real
   DispatchContext + `apply_beat_dispatch` + `handle_applied_side_effects` + assert
   actual `ctx.snapshot.characters[0].core.edge.current` mutation. Non-negotiable per
   CLAUDE.md wiring-test rule.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** UI must render real edge state from websocket.
2. **Every Test Suite Needs a Wiring Test.** This story *creates* the real one.
3. **No Silent Fallbacks.** Legacy save without HP data → fail loudly, not default to zero.
4. **No Stubbing.**
5. **Don't Reinvent — Wire Up What Exists.** Migration pattern matches existing Sqlite v-bumps.

### Key Files

| File | Action |
|------|--------|
| `sidequest-api/crates/sidequest-game/src/persistence.rs` | Schema v-bump; legacy HP → Edge synthesis path; document the ÷2 heuristic in code |
| `sidequest-api/tests/beat_dispatch_wiring_story_28_5_tests.rs` | **Rewrite** — build DispatchContext, call real dispatch, assert mutation |
| `sidequest-ui/src/character/**` | Composure bar component; remove HP bar; read declaratively from `stat_display_fields` |
| `sidequest-ui/src/character/compositionState.ts` (or new) | `composure_state` derivation: `Fresh >75%`, `Strained 50-75%`, `Cracked 25-50%`, `Broken ≤25%` |
| `sidequest-content/genre_packs/heavy_metal/rules.yaml` | Confirm `stat_display_fields: [edge, max_edge, composure_state]` (may have landed in 39-3 — verify) |
| Protocol / WebSocket serializer | Ensure `core.edge` is included in player state snapshot |

### Patterns

- Schema version bump: follow the existing pattern in `persistence.rs` for previous
  migrations (additive column + migration function)
- Legacy save detection: check schema version column; on mismatch run migration
- Migration formula: `edge.base_max = legacy.hp_formula_base / 2`, `edge.current = edge.max = edge.base_max`
- React `composure_state` is a derived hook, not a field on a type
- The rewritten wiring test is the authoritative example of what Epic 39 means by "wiring test"

### Dependencies

- **Blocks on 39-4** (edge dispatch wired)
- **Ideally after 39-5** (advancement effects available so UI can display modifiers) but can run in parallel if UI is scoped to raw edge values only

## Scope Boundaries

**In scope:**
- Sqlite schema v-bump + migration fn
- Legacy HP → EdgePool synthesis on load (÷2 heuristic, documented)
- React composure bar + `composure_state` derivation
- Replace HP bar in character sheet — heavy_metal only (other packs still show HP)
- Rewrite `beat_dispatch_wiring_story_28_5_tests.rs` as real dispatch test
- Ensure `core.edge` is in player state over the wire
- Wiring test: end-to-end — open a pre-migration save file fixture, confirm it opens with synthesized Edge, UI renders composure bar

**Out of scope:**
- Other genres' UI (still HP)
- LoreStore scrub of old "took 4 damage" fragments (deferred, out of epic)
- Broader audit of other `*_wiring_story_*` false-positive tests (follow-up ticket)
- Authored advancement content (39-5/8)
- Pact push UI surfaces (covered by character sheet in this story if time; otherwise follow-up)

## AC Context

**AC1: Save migration works**
- Opening a pre-Epic-39 save file for heavy_metal succeeds
- Loaded character has `core.edge` populated via the ÷2 heuristic
- Loaded character has no `hp / max_hp / ac` fields (the type forbids it per 39-2)
- Schema version column updated post-migration
- Fixture test: a committed legacy save file in test assets round-trips

**AC2: Legacy save fails loudly when data is missing**
- A save with corrupt/missing HP data errors with a clear message, not silent zero-Edge

**AC3: Character sheet renders composure bar (heavy_metal)**
- UI shows Edge current/max as a bar
- `composure_state` label derives from ratio (Fresh/Strained/Cracked/Broken)
- HP bar removed from heavy_metal view

**AC4: Declarative `stat_display_fields`**
- UI reads `stat_display_fields: [edge, max_edge, composure_state]` from heavy_metal rules
- Other genres still display HP per their `stat_display_fields`

**AC5: Wiring test rewritten**
- `beat_dispatch_wiring_story_28_5_tests.rs` no longer regex-matches source files
- Builds a real `DispatchContext`, calls `apply_beat_dispatch` +
  `handle_applied_side_effects` on a real heavy_metal `strike` beat
- Asserts `ctx.snapshot.characters[0].core.edge.current` decreased by the expected amount
- Asserts OTEL `creature.edge_delta` span was emitted

**AC6: WebSocket includes edge**
- Player state over websocket includes `core.edge { current, max, base_max, ... }`
- UI receives and renders it without frontend polyfill

## Assumptions

- `stat_display_fields` for heavy_metal landed as `[edge, max_edge, composure_state]` in 39-3 (verify; if not, land here)
- `composure_state` enum lives in UI only — not a backend field
- Legacy playtest saves may be re-rolled rather than migrated if migration is lossy for specific stored NPCs; playtest saves are disposable
