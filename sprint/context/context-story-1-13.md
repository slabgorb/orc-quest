---
parent: context-epic-1.md
---

# Story 1-13: Extract CreatureCore — Shared Struct for Character and NPC Fields

## Business Context

A post-hoc refactor that extracted 9 shared fields and 2 shared behaviors from `Character`
and `NPC` into a single `CreatureCore` embedded struct. This is textbook "don't port the
debt" — Python had duplicated fields across character and NPC classes, leading to
inconsistent behavior when one was updated and the other was not.

By extracting a shared struct, the Rust port ensures both types stay in sync structurally.

## Technical Guardrails

- **Composition over inheritance:** `CreatureCore` is embedded via `#[serde(flatten)]`,
  not a trait or inheritance hierarchy
- **Shared fields:** name, description, personality, level, hp, max_hp, ac, inventory, statuses
- **Shared behavior:** `apply_hp_delta()` method, `Combatant` trait implementation
- **`#[serde(flatten)]`** preserves JSON wire format — Character and NPC serialize the
  same as before, with core fields at the top level

## Scope Boundaries

**In scope:**
- `creature_core.rs`: CreatureCore struct with 9 fields
- `creature_core.rs`: `apply_hp_delta()` method using `clamp_hp()`
- `creature_core.rs`: `Combatant` trait implementation
- `character.rs`: Refactored to embed `pub core: CreatureCore`
- `npc.rs`: Refactored to embed `pub core: CreatureCore`
- All existing tests updated and passing

**Out of scope:**
- New fields or behaviors beyond what Character and NPC already share
- Changes to the Combatant trait definition (story 1-6)

## AC Context

| AC | Detail |
|----|--------|
| Shared struct | CreatureCore contains exactly the 9 shared fields |
| Character embeds | `Character.core: CreatureCore` with `#[serde(flatten)]` |
| NPC embeds | `NPC.core: CreatureCore` with `#[serde(flatten)]` |
| Serde compatible | JSON output unchanged — flatten preserves wire format |
| Combatant via core | Both types delegate Combatant to CreatureCore |
| Tests pass | All existing tests pass without modification |

## Assumptions

- Shared fields are genuinely identical in semantics, not just coincidentally named
- Composition (has-a) is the right Rust idiom, not trait inheritance
