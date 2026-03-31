---
parent: context-epic-16.md
---

# Story 16-4: Migrate Combat as Confrontation — Verify CombatState Coexistence

## Business Context

CombatState stays as-is (per ADR-033 — combat is actor-centric, encounters are
scene-centric). This story verifies that StructuredEncounter and CombatState coexist
cleanly on GameSnapshot and that encounter escalation into combat works.

## Technical Approach

### Coexistence Model

```rust
pub struct GameSnapshot {
    pub combat: CombatState,                    // always present, actor-centric
    pub encounter: Option<StructuredEncounter>,  // scene-centric, replaces chase
}
```

Both can be active simultaneously — a standoff (encounter) that escalates to combat
should transition cleanly: encounter resolves, combat engages with initiative informed
by encounter outcome (e.g., tension bonus → initiative advantage).

### Escalation Pipeline

When a StructuredEncounter with `escalates_to: "combat"` resolves:
1. Read encounter outcome and metric state
2. Derive combat modifiers (e.g., standoff tension → initiative bonus)
3. Call `combat.engage()` with participants from encounter actors
4. Set encounter to resolved
5. Optionally clear encounter from GameSnapshot

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/state.rs` | Verify combat + encounter fields coexist |
| `sidequest-game/src/combat.rs` | No changes — verify all tests still pass |
| `sidequest-server/src/shared_session.rs` | Escalation wiring |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Coexist | combat and encounter fields both present on GameSnapshot |
| Combat unchanged | All existing combat.rs tests pass with zero modifications |
| Escalation | Encounter with escalates_to="combat" transitions to combat state |
| Initiative | Encounter outcome can modify combat initiative order |
| Serialize | Snapshot with both combat and encounter serializes/deserializes |
