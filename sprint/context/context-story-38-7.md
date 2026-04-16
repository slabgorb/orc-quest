---
parent: context-epic-38.md
workflow: trivial
---

# Story 38-7: Hit severity column in interactions_mvp.yaml

## Business Context

The MVP interaction table resolves gun solutions as binary (you have a shot or you don't) but has no damage model. The paper playtest used ad-hoc house rules ("graze / clean / devastating, 2 grazes = kill") that need to be formalized in the content layer. Without hit severity, the engine cannot distinguish a wing-clip from a cockpit hit, and the narrator has no mechanical basis for describing damage intensity.

This is a content-only story — extending the 16 cells in `interactions_mvp.yaml` with a `hit_severity` field and defining hull damage increments per severity level. No Rust code changes required; the `PerActorDelta` schema from 38-5 already supports arbitrary field writes via `set_fields`.

## Technical Guardrails

**Key file to modify:**
- `sidequest-content/genre_packs/space_opera/dogfight/interactions_mvp.yaml` — add `hit_severity` to every cell that has `gun_solution: true` on either actor

**Patterns to follow:**
- The existing cell structure uses `red_view` / `blue_view` descriptor deltas. Hit severity is a property of the shot, not the view — it belongs at the cell level or as a per-actor field alongside `gun_solution`
- ADR-077 Risk section: "graze / clean / devastating" was the paper playtest vocabulary. Use these three tiers
- Hull damage increments must be defined relative to the `hull` secondary stat (starting value from `descriptor_schema.yaml` is not yet defined — this story must establish it)

**What NOT to touch:**
- `maneuvers_mvp.yaml` — maneuver definitions are stable
- `descriptor_schema.yaml` — hit severity is a resolution output, not a per-turn descriptor field
- Rust code — the engine reads `set_fields` generically; no schema change needed

## Scope Boundaries

**In scope:**
- Add `hit_severity` field to all 16 cells in `interactions_mvp.yaml` where at least one actor has `gun_solution: true`
- Define the three severity tiers: `graze`, `clean`, `devastating`
- Define hull damage increments per severity (e.g., graze = 10, clean = 30, devastating = 60 out of starting hull)
- Establish starting hull value if not already defined in the secondary stats

**Out of scope:**
- Rust engine changes for damage application (the `set_fields` mechanism handles this generically)
- Mutual-kill tiebreaker rules (paper playtest uses d6; formalization is a future story)
- Narrator damage description templates (38-6 handles narrator integration)

## AC Context

**AC1: All gun_solution cells have hit_severity**
- Every cell where either `red_view.gun_solution: true` or `blue_view.gun_solution: true` must have a corresponding `hit_severity` for that actor
- Cells where neither actor has a gun solution have no hit_severity (no shots fired = no damage)
- Verify: grep `gun_solution: true` count matches `hit_severity` field count

**AC2: Three-tier severity classification**
- Severities are: `graze` (glancing hit, cosmetic/minor), `clean` (solid hit, significant structural), `devastating` (critical, fight-ending potential)
- Distribution across the 16-cell table should feel balanced: most offensive-scores-on-passive cells should be `clean`, mutual gunline cells should range from `graze` to `clean` (mutual devastatings would be too lethal), and the kill_rotation back-shot cells should be `devastating` (the reward for the high-risk flip)
- Verify: review severity assignments against the RPS balance — offense-on-passive rewards should be higher severity than mutual-exposure situations

**AC3: Hull damage increments defined**
- Each severity maps to a concrete hull damage value
- Starting hull pool value must be established (consistent with `secondary_stats.hull` in the confrontation def)
- The damage model must support the paper playtest's "2 grazes = kill on a light fighter" rule as a reasonable outcome
- Verify: math checks out — two grazes should bring hull to critical or zero on a standard fighter
