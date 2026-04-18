---
story_id: "15-21"
jira_key: null
epic: "15"
workflow: "tdd"
---
# Story 15-21: Wire level_to_defense — defense scaling ignored in combat resolution

## Story Details
- **ID:** 15-21
- **Jira Key:** (personal project, none)
- **Epic:** 15 (Playtest Debt Cleanup — Stubs, Dead Code, Disabled Features)
- **Workflow:** tdd
- **Points:** 2
- **Priority:** p2
- **Status:** backlog → in progress

## Problem

`level_to_defense()` in `progression.rs` is implemented but never called. Its sister function `level_to_damage()` IS wired into `CombatState::resolve_attack()` and correctly scales attacker damage based on level.

The defender's level has **zero effect on damage mitigation**. All defenders take the same damage regardless of their level, breaking the progression system's symmetry.

## Context

**Current state in combat.rs (lines 218-226):**
```rust
let base_damage = 5;
let damage = level_to_damage(base_damage, attacker.level());

let event = DamageEvent {
    attacker: attacker_name.to_string(),
    target: target_name.to_string(),
    damage,
    round: self.round,
};
```

**The functions in progression.rs (lines 30-40):**
```rust
pub fn level_to_damage(base: i32, level: u32) -> i32 {
    if level <= 1 {
        return base;
    }
    base + (base as f64 * 0.1 * (level - 1) as f64) as i32
}

pub fn level_to_defense(base: i32, level: u32) -> i32 {
    soft_cap_stat(base, level)
}
```

## Fix

1. Call `level_to_defense(defender.level())` in `resolve_attack()` with a base defense value (tentatively 3, matching the progression philosophy)
2. Subtract the computed defense from the attacker's damage: `damage = (damage - defense).max(1)` (ensure minimum 1 damage)
3. Emit OTEL event: `combat.defense_applied` with fields:
   - `defender_name`
   - `defender_level`
   - `defense_value`
   - `damage_before` (pre-defense)
   - `damage_after` (post-defense)

## Wiring Checklist

- [ ] Add `level_to_defense()` call in `CombatState::resolve_attack()` 
- [ ] Factor defense into damage calculation
- [ ] Add OTEL span with `combat.defense_applied` event
- [ ] Verify no existing tests break
- [ ] Add test case for defense scaling

## Workflow Tracking

**Workflow:** tdd
**Phase:** setup → dev
**Phase Started:** 2026-04-02T00:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T00:00:00Z | - | - |

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

None yet — spec is clear and implementation path is straightforward.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
