---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-3: Purge HP from heavy_metal YAML + RulesConfig Loader

## Business Context

Makes heavy_metal the reference HP-free genre. Strips `hp_formula`, `class_hp_bases`,
`default_hp`, `default_ac`, and the `stat_display_fields: [hp, max_hp, ac]` list from
`heavy_metal/rules.yaml` only. The other nine packs still declare HP fields (phantom but
declared) until post-playtest; the gate that makes this possible is making
`RulesConfig`'s HP fields `Option<T>` in the loader. Adds the `edge_config` block
(per-class `base_max`, `recovery_defaults`, composure thresholds) from content draft §1.

Heavy_metal-only scope is deliberate — one genre reaches HP-free cleanly and we playtest
before dragging nine more along.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** `edge_config` must be loaded and consumed.
2. **Every Test Suite Needs a Wiring Test.**
3. **No Silent Fallbacks.** If `edge_config` is missing for heavy_metal, load fails loudly.
4. **No Stubbing.**
5. **Don't Reinvent — Wire Up What Exists.** Loader patterns follow existing `rules.yaml` parsing.

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/genre_packs/heavy_metal/rules.yaml` | Strip HP fields; add `edge_config` block per draft §1 |
| `sidequest-content/genre_packs/heavy_metal/_drafts/edge-advancement-content.md` | Source — §1 lifts verbatim |
| `sidequest-api/crates/sidequest-genre/src/models/rules.rs` | `hp_formula`, `class_hp_bases`, `default_hp`, `default_ac` → `Option<T>` on `RulesConfig`; add `edge_config: Option<EdgeConfig>` |
| `sidequest-api/crates/sidequest-genre/src/models/rules.rs` | New `EdgeConfig` struct: `base_max_by_class: HashMap<String, i32>`, `recovery_defaults: RecoveryDefaults`, `thresholds: Vec<EdgeThreshold>` |
| `sidequest-api/crates/sidequest-game/src/character_build/` (wherever 39-2 placeholder is) | Replace placeholder `EdgePool` with values from `edge_config.base_max_by_class[class]` |

### Patterns

- `#[serde(default)]` on HP fields once they become `Option` — missing key → `None`
- `EdgeConfig` loads on all genres; only heavy_metal populates it in this story
- `base_max_by_class` is case-sensitive matching class names (Fighter/Barbarian/etc.)
- If a genre has neither `hp_formula` nor `edge_config` the loader must fail loudly
  (not silently default) — per no-silent-fallbacks rule

### Dependencies

- **Blocks on 39-2** (`EdgePool` + `EdgeThreshold` + `RecoveryTrigger` types exist)

## Scope Boundaries

**In scope:**
- Strip HP fields from `heavy_metal/rules.yaml` only
- Lift draft §1 `edge_config` block into `heavy_metal/rules.yaml`
- `RulesConfig` HP fields → `Option<T>`
- New `EdgeConfig` struct + serde
- Wire `edge_config.base_max_by_class` into character construction (replace 39-2 placeholders)
- Loader test: heavy_metal loads with `edge_config.is_some()` and `hp_formula.is_none()`
- Loader test: low_fantasy (or any other pack) loads with `edge_config.is_none()` and `hp_formula.is_some()`
- Wiring test: chargen for heavy_metal Fighter produces EdgePool with `base_max=6`

**Out of scope:**
- Other nine genre packs' YAML (stays HP for now)
- `BeatDef.edge_delta` (39-4)
- Advancement tree (39-5)
- Push-currency resources (39-6)
- Combat beat rewrites (39-8)

## AC Context

**AC1: heavy_metal rules.yaml has no HP keys**
- Grep `heavy_metal/rules.yaml` for `hp_formula|class_hp_bases|default_hp|default_ac` → zero matches
- `stat_display_fields` no longer contains `hp`/`max_hp`/`ac` (the new values land in 39-7 or can land here as `[edge, max_edge, composure_state]` — coordinate with 39-7 scope)

**AC2: heavy_metal rules.yaml has `edge_config`**
- `edge_config.base_max_by_class` matches draft §1 per-class values
- `edge_config.recovery_defaults` matches draft
- `edge_config.thresholds` contains at-least `at: 0` composure_break threshold

**AC3: RulesConfig HP fields are Option**
- All four HP fields on `RulesConfig` are `Option<T>`
- Existing packs (low_fantasy, space_opera, etc.) still load without error

**AC4: No silent fallback**
- A genre pack with neither `hp_formula` nor `edge_config` fails to load with a clear
  error message naming the pack

**AC5: Wiring — chargen reads edge_config**
- Constructing a heavy_metal Fighter via the production chargen path produces
  `core.edge.base_max == 6` and `core.edge.max == 6` and `core.edge.current == 6`
- Constructing a heavy_metal Warlock produces `base_max == 4`

## Assumptions

- Draft §1 block is the source of truth for per-class numbers and thresholds
- `stat_display_fields` migration to `[edge, max_edge, composure_state]` can land here
  or in 39-7 — coordinate; both options preserve the wiring rule
- The loader already has a "load all genre packs" test suite to regression-gate
