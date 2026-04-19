---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-2: Delete HP from CreatureCore

## Business Context

Combat HP is dead code. `CreatureCore.hp / max_hp / ac` exist on every character but
beat dispatch never calls `apply_hp_delta()` — the narrator reads a metric clock and
improvises damage with zero engine backing. This story deletes the phantom fields,
cascades the compile errors workspace-wide, and synthesizes placeholder `EdgePool`s in
constructors so the workspace reaches green before 39-3/4 fill in real values.

This is the most mechanically large story in the epic. It is intentionally before
content work (39-3) and dispatch wiring (39-4) because nothing else compiles until the
shape of `CreatureCore` is settled.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.**
2. **Every Test Suite Needs a Wiring Test.**
3. **No Silent Fallbacks.**
4. **No Stubbing.** Placeholder `EdgePool` values in constructors ARE allowed here
   because 39-3/4 fill them in immediately — they are not open-ended stubs, they are
   sequenced filler with a named successor story. Do NOT leave empty modules.
5. **Don't Reinvent — Wire Up What Exists.**

### Key Files

| File | Action |
|------|--------|
| `sidequest-api/crates/sidequest-game/src/creature_core.rs` | Delete `hp/max_hp/ac`; add `edge: EdgePool`, `acquired_advancements: Vec<String>` |
| `sidequest-api/crates/sidequest-game/src/hp.rs` | **Delete file** |
| `sidequest-api/crates/sidequest-game/src/lib.rs` | Remove `pub mod hp;` |
| `sidequest-api/crates/sidequest-game/src/combatant.rs` (or wherever `Combatant` trait lives) | Remove `hp()/max_hp()/ac()`; add `edge()/max_edge()/is_broken()` |
| **All callers of `.hp`, `.max_hp`, `.ac`, `apply_hp_delta`, `Combatant::hp()`** | Cascade fix — grep workspace-wide |
| `sidequest-api/crates/sidequest-server/src/dispatch/state_mutations.rs` | Remove level-up HP healing block |

### Patterns

- Placeholder `EdgePool` constructor: `EdgePool { current: 5, max: 5, base_max: 5, recovery_triggers: vec![RecoveryTrigger::OnResolution], thresholds: vec![] }` — values tuned per-class in 39-3
- `is_broken()` returns `self.edge().current <= 0`
- Use `cargo check --workspace` iteratively to drive cascade fixes
- If a caller's HP read was narrative-only (logging, display), convert to Edge — do NOT delete the caller

### Dependencies

- **Blocks on 39-1** (EdgePool type must exist)

## Scope Boundaries

**In scope:**
- Delete `hp/max_hp/ac` fields from `CreatureCore`
- Delete `sidequest-game/src/hp.rs`
- `Combatant` trait swap: HP methods → Edge methods
- Placeholder `EdgePool` in all constructors (`CharacterState::new`, test fixtures, monster manual generators)
- `acquired_advancements: Vec<String>` field on `CreatureCore` (empty default)
- Cascade fix every compile error — workspace reaches green
- Remove level-up HP healing from `state_mutations.rs`
- One wiring test: construct a `CharacterState` via production code path, assert `edge` field is populated

**Out of scope:**
- Real per-class `edge.max` values (39-3)
- Real `thresholds` / `recovery_triggers` values (39-3)
- YAML changes (39-3)
- Any dispatch wiring of edge_delta (39-4)
- Save migration (39-7)
- UI (39-7)

## AC Context

**AC1: `CreatureCore` shape**
- `hp`, `max_hp`, `ac` fields do not exist
- `edge: EdgePool` exists
- `acquired_advancements: Vec<String>` exists (default empty)
- `hp.rs` file does not exist

**AC2: `Combatant` trait**
- `hp()`, `max_hp()`, `ac()` methods removed
- `edge()`, `max_edge()`, `is_broken()` methods present
- All `impl Combatant for ...` blocks updated

**AC3: Workspace compiles**
- `cargo check --workspace` green
- `cargo build --workspace` green
- No `#[allow(dead_code)]` on deleted-adjacent items

**AC4: Tests pass with placeholder values**
- `cargo test --workspace` green (may require test fixture updates to use EdgePool)
- No test references to `.hp`/`.max_hp`/`.ac`/`apply_hp_delta`

**AC5: Wiring test**
- Integration test constructs a `CharacterState` through a production path (e.g.,
  chargen, monster manual) and asserts the resulting `core.edge` is a real EdgePool,
  not a default/stub

## Assumptions

- Placeholder values are acceptable because 39-3 (next story) replaces them with
  per-class YAML-driven values
- `apply_hp_delta` has no non-test callers today (per plan); if grep reveals any, they
  are converted to `edge.apply_delta` in this story
- Save/load compatibility is 39-7's problem — this story may break existing saves
