---
parent: context-epic-1.md
---

# Story 1-6: Game Core Types — Disposition, NonBlankString, clamp_hp, Combatant Trait, Character, NPC, Inventory

## Business Context

This is the type foundation for all game logic. Every story after this that touches
characters, NPCs, combat, or inventory depends on these types being correct. The specific
items — `Disposition`, `NonBlankString`, `clamp_hp` — are all responses to documented
Python debt:
- Duplicate enums with conflicting thresholds (port lesson #5)
- Unvalidated strings causing empty-name bugs (port lesson #9)
- HP clamping bug in `progression.py` (port lesson #6)

This story is where "don't port the debt" becomes concrete.

**Python sources:**
- `sq-2/sidequest/game/character.py` — Character, ProgressionState, NarrativeHook
- `sq-2/sidequest/game/npc.py` — NPC, NPCRegistry, Attitude, derive_attitude
- `sq-2/sidequest/game/item.py` — Item, ItemCategory, ItemRarity, Inventory
- `sq-2/sidequest/game/validators.py` — shared validation helpers

## Technical Guardrails

- **Port lesson #5 (Disposition newtype):** `Disposition(i8)` replaces both `Attitude` (+-10)
  and `DispositionLevel` (+-25) with a single type and single threshold definition
- **Port lesson #6 (HP clamping):** Single `fn clamp_hp(current: i32, delta: i32, max: i32) -> i32`
  that clamps to `0..=max`. Fixes Python bug where `progression.py` allows negative HP
- **Port lesson #9 (validation):** `NonBlankString` newtype validates at construction. All
  inline `if not v.strip()` validators become type-level guarantees
- **Port lesson #10 (Combatant trait):** Characters, NPCs, and enemies implement a shared
  trait with `name/hp/max_hp/ac/level` methods. Eliminates duplicated field definitions
- **ADR-007 (Unified Character Model):** Single character model for player and NPC types
- **ADR-020 (NPC Disposition System):** Disposition as clamped numeric value

### Python -> Rust Translation

| Python | Rust |
|---|---|
| `Attitude` enum (friendly/neutral/hostile, +-10) | `Disposition(i8)` with `attitude()` method |
| `DispositionLevel` enum (same values, +-25) | Same `Disposition` — one type, one threshold |
| `validate_not_blank()` in validators.py | `NonBlankString::new() -> Result` |
| `Character` (Pydantic) | `struct Character` with `CreatureCore` composition |
| `NPC` (Pydantic) | `struct NPC` with `CreatureCore` composition |
| `Inventory` (list + helpers) | `struct Inventory` with typed items |

## Scope Boundaries

**In scope:**
- `Disposition` newtype with validated construction (-15..=15), `attitude()` method
- `NonBlankString` newtype with construction-time validation
- `clamp_hp()` function fixing the Python floor bug
- `Combatant` trait shared by Character and NPC
- `Character`, `NPC`, `Inventory`, `Item` structs with serde derives
- Unit tests proving validation rejects bad inputs

**Out of scope:**
- `Enemy` type (story 1-7, combat subsystem)
- Combat/chase state machines (story 1-7)
- Game state composition (story 1-8)
- NPC dialogue/behavior (story 1-11, agent layer)

## AC Context

| AC | Detail |
|----|--------|
| Disposition newtype | Validates -15..=15, derives attitude from thresholds |
| NonBlankString | `::new("")` returns Err, `::new("valid")` returns Ok |
| clamp_hp | `clamp_hp(5, -10, 20)` returns 0, not -5 |
| Combatant trait | Character and NPC both implement it |
| Serde round-trips | All structs serialize/deserialize losslessly |
| deny_unknown_fields | Unexpected JSON keys are rejected |

## Assumptions

- Combatant trait abstraction works for both Character and NPC without awkward workarounds
- Inventory is simple enough to be part of core types rather than its own subsystem
- CreatureCore extraction (story 1-13) will follow to DRY up shared fields
