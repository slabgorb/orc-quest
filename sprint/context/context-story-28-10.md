---
parent: context-epic-28.md
---

# Story 28-10: Genre Pack Combat and Chase ConfrontationDefs

## Business Context

No genre pack currently declares "combat" or "chase" as a confrontation type. They only
have social/structured encounters (standoff, negotiation, trial, etc.). Combat and chase
were implicit — hardcoded via CombatState and ChaseState. In the unified system, combat
and chase are just confrontation types declared in YAML like everything else.

Genres that don't make sense with combat (victoria, star_chamber) simply don't declare
a combat confrontation type. The system is flexible — encounter types are content, not code.

## Technical Approach

### Combat ConfrontationDef template

```yaml
- type: combat
  label: "Combat"
  category: combat
  metric:
    name: enemy_hp
    direction: descending
    starting: 100  # placeholder — actual HP from CreatureCore
    threshold_low: 0
  beats:
    - id: attack
      label: "Attack"
      metric_delta: -15
      stat_check: attack
    - id: defend
      label: "Defend"
      metric_delta: 0
      stat_check: defend
    - id: flee
      label: "Flee"
      metric_delta: 0
      stat_check: escape
      resolution: true
  mood: combat
```

Each genre customizes beats for flavor:
- **neon_dystopia** adds: `hack`, `netrun`, `jack_out`
- **spaghetti_western** adds: `fan_the_hammer`, `quick_draw`
- **space_opera** adds: `phaser_stun`, `photon_torpedo`
- **road_warrior** adds: `ram`, `sideswipe`, `nitro_boost`
- **low_fantasy** adds: `prayer`, `shield_wall`
- **pulp_noir** adds: `sucker_punch`, `dirty_trick`

### Chase ConfrontationDef template

```yaml
- type: chase
  label: "Chase"
  category: movement
  metric:
    name: separation
    direction: ascending
    starting: 0
    threshold_high: 10
  beats:
    - id: sprint
      label: "Sprint"
      metric_delta: 2
      stat_check: athletics
    - id: shortcut
      label: "Take Shortcut"
      metric_delta: 3
      stat_check: cunning
      risk: "dead end — lose 2 separation"
    - id: obstacle
      label: "Throw Obstacle"
      metric_delta: 1
      stat_check: athletics
    - id: surrender
      label: "Surrender"
      metric_delta: 0
      stat_check: none
      resolution: true
  escalates_to: combat
  mood: tension
```

Genre-specific chase flavors:
- **road_warrior**: `accelerate`, `maneuver`, `ram`, `shortcut`, `nitro` — secondary_stats for vehicle (hp, fuel, speed, armor)
- **space_opera**: `evasive_maneuver`, `jump_to_hyperspace`, `ion_cannon` — secondary_stats for ship
- **neon_dystopia**: `jack_in_and_trace`, `emp_burst`, `rooftop_leap`

### Genre-by-genre plan

| Genre | Gets combat | Gets chase | Custom beats |
|-------|-------------|------------|--------------|
| caverns_and_claudes | YES | YES | spell_cast, shield_bash |
| elemental_harmony | YES | YES | channel_element, spirit_guard |
| low_fantasy | YES | YES | prayer, shield_wall |
| mutant_wasteland | YES | YES | radiation_blast, mutant_surge |
| neon_dystopia | YES | YES | hack, netrun, emp_burst |
| pulp_noir | YES | YES | sucker_punch, dirty_trick |
| road_warrior | YES | YES (primary!) | ram, nitro_boost, sideswipe |
| space_opera | YES | YES | phaser_stun, evasive_maneuver |
| spaghetti_western | YES | YES | fan_the_hammer, quick_draw |
| star_chamber | NO | NO | (courtroom — existing trial type suffices) |
| victoria | NO | NO | (social intrigue — existing negotiation/trial/auction) |

### Validation

`sidequest-genre/src/validate.rs:149` already validates confrontation defs —
beat IDs unique, stat_checks non-empty, escalates_to references valid types.
Combat and chase defs go through this same validation.

## Key Files

| File | Action |
|------|--------|
| `sidequest-content/genre_packs/*/rules.yaml` | Add combat + chase ConfrontationDefs (9 of 11 genres) |
| `sidequest-genre/src/validate.rs` | Verify "combat" and "chase" pass existing validation |
| `sidequest-genre/src/models/rules.rs` | May need to add "combat" and "movement" to valid categories |

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| 9 genres have combat | All genres except victoria and star_chamber have a combat confrontation type | `grep -l "type: combat" genre_packs/*/rules.yaml \| wc -l` = 9 |
| 9 genres have chase | All genres except victoria and star_chamber have a chase confrontation type | `grep -l "type: chase" genre_packs/*/rules.yaml \| wc -l` = 9 |
| Victoria no combat | victoria/rules.yaml has NO combat or chase type | Grep returns nothing |
| star_chamber no combat | star_chamber/rules.yaml has NO combat or chase type | Grep returns nothing |
| Genre flavor | Each genre's combat beats have at least one unique beat beyond attack/defend/flee | Manual review per genre |
| Validation passes | `cargo test -p sidequest-validate` passes with new defs | Test verification |
| road_warrior chase has secondary_stats | road_warrior chase def includes vehicle secondary stats | Grep: "secondary_stats" in road_warrior/rules.yaml chase section |
| Categories valid | "combat" and "movement" are valid confrontation categories in the genre loader | Test: load genre pack with combat type → no validation error |

## Scope Boundaries

**In scope:** Adding combat + chase ConfrontationDefs to genre pack YAML files, validating
**Out of scope:** Any Rust code changes (beyond possible category validation) — this is content
