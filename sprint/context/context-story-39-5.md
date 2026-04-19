---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-5: Authored Advancement Effects + resolved_beat_for

## Business Context

Replaces the 39-4 hard-coded advancement stub with real, YAML-authored advancement
tiers that modify Edge capacity, Edge recovery, beat costs, and target-Edge leverage.
This is the first hard link between ADR-021's four-track progression and engine
mechanical state — the reason the whole epic exists.

Adds the `AdvancementEffect` enum (including GM-draft-ratified `LoreRevealBonus` and
`BeatDiscount.resource_mod`), extends `RecoveryTrigger::OnBeatSuccess` with
`while_strained: bool`, introduces `CreatureCore.acquired_advancements: Vec<String>`,
and implements `resolved_beat_for` as a pure view function. Includes a per-genre audit
pass to determine where each genre hosts effects (existing `progression.yaml` affinity
tiers vs. new `advancements.yaml`) — the loader supports both.

Ratified ADR-078 amendments (see epic context): effects host on existing progression
structures where available; four extended variants (`AllyBeatDiscount`,
`BetweenConfrontationsAction`, `AllyEdgeGrant`, `EdgeThresholdDelay`) deferred to
ADR-079.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** `resolved_beat_for` must be called by dispatch.
2. **Every Test Suite Needs a Wiring Test.**
3. **No Silent Fallbacks.** Unknown tier id in `acquired_advancements` → fail loudly.
4. **No Stubbing.** Delete the 39-4 Fighter-stub advancement.
5. **Don't Reinvent — Wire Up What Exists.** Milestone grant uses existing ADR-021 bus.

### Key Files

| File | Action |
|------|--------|
| `sidequest-api/crates/sidequest-genre/src/models/advancement.rs` | **New.** `AdvancementTree`, `AdvancementTier`, `AdvancementEffect`, `LoreRevealScope` |
| `sidequest-api/crates/sidequest-genre/src/models/progression.rs` (or equivalent) | Extend affinity-tier struct with optional `mechanical_effects: Vec<AdvancementEffect>` |
| `sidequest-api/crates/sidequest-genre/src/loader.rs` | Load `mechanical_effects` from `progression.yaml` OR standalone `{genre}/advancements.yaml`; fail loudly if both present |
| `sidequest-api/crates/sidequest-game/src/advancement.rs` | **New.** `pub fn resolved_beat_for(&CharacterState, &BeatDef, &AdvancementTree) -> ResolvedBeat` |
| `sidequest-api/crates/sidequest-server/src/dispatch/beat.rs` | Replace 39-4 hard-coded stub with `resolved_beat_for` call; use `resolved.edge_delta` / `resolved.target_edge_delta` |
| `sidequest-api/crates/sidequest-game/src/creature_core.rs` | `acquired_advancements` field already added in 39-2 — wire grant path |
| `sidequest-api/crates/sidequest-server/src/dispatch/state_mutations.rs` (or milestone handler) | Milestone event → grant matching `AdvancementTier.id` into `acquired_advancements` |
| `sidequest-content/genre_packs/heavy_metal/progression.yaml` | Add `mechanical_effects` to Iron/Pact/Court/Ruin/Craft/Lore tiers per draft §2 |
| `sidequest-content/genre_packs/heavy_metal/_drafts/edge-advancement-content.md` | Source — §2 lifts verbatim |

### Patterns

- `AdvancementEffect` enum variants (v1):
  `EdgeMaxBonus { amount }`, `EdgeRecovery { trigger, amount }`,
  `BeatDiscount { beat_id, edge_delta_mod, resource_mod: Option<HashMap<String,i32>> }`,
  `LeverageBonus { beat_id, target_edge_delta_mod }`,
  `LoreRevealBonus { scope: LoreRevealScope }`
- `resolved_beat_for` is pure: takes immutable borrows, returns a `ResolvedBeat` with
  effective `edge_delta / target_edge_delta / resource_deltas` + `source_effects: Vec<&AdvancementEffect>` for telemetry
- `EdgeMaxBonus` effects apply to `core.edge.max` on grant (when tier lands in
  `acquired_advancements`) — not on every read
- `BeatDiscount.resource_mod` subtracts from `beat.resource_deltas` (Pact-affinity tiers
  make pushes cheaper)
- Per-genre audit: document each genre's effect-host decision in a table in the ADR or
  a new reference doc

### Dependencies

- **Blocks on 39-4** (`BeatDef` fields + dispatch wiring live, stub to replace)

## Scope Boundaries

**In scope:**
- `AdvancementEffect` enum (5 v1 variants)
- `LoreRevealScope` enum
- `AdvancementTree` / `AdvancementTier` types + loader (dual-location)
- `RecoveryTrigger::OnBeatSuccess` gains `while_strained: bool`
- `resolved_beat_for` view function
- Dispatch wiring: replace 39-4 stub with `resolved_beat_for` call
- Milestone-grant path: Milestone event → `acquired_advancements` push
- `EdgeMaxBonus` applied on grant (mutates `core.edge.max`)
- Per-genre audit completed (doc artifact, 10 genres)
- heavy_metal `progression.yaml` `mechanical_effects` (draft §2) authored
- `advancement.effect_applied` + `advancement.tier_granted` OTEL spans
- Wiring test: grant Fighter tier 1 → `core.edge.max` increases; dispatch `strike` → `resolved.source_effects` includes the granted effect

**Out of scope:**
- Four deferred variants (ADR-079)
- Other genres' `mechanical_effects` content
- Pact push-currency resources (39-6)
- Save migration / UI (39-7)
- Full acceptance playtest (39-8)

## AC Context

**AC1: AdvancementEffect enum complete**
- All 5 v1 variants compile, serde round-trip, have `Debug/Clone/PartialEq`
- YAML shape matches existing enum conventions (tagged variants, snake_case)

**AC2: Loader supports both locations**
- heavy_metal: `mechanical_effects` under `progression.yaml` affinity tiers loads
- A genre without `progression.yaml` affinity tiers but with `{genre}/advancements.yaml` loads
- If both are present for the same genre, loader fails loudly

**AC3: `resolved_beat_for` semantics**
- Pure — no mutation
- With empty `acquired_advancements`, returns beat fields unchanged
- With a Fighter `EdgeMaxBonus { amount: 2 }` in acquired, `resolved.source_effects` lists it (but this effect changes `max`, not `edge_delta`; validate via state, not return)
- With `BeatDiscount { beat_id: "committed_blow", edge_delta_mod: -1 }`, a committed_blow beat's `resolved.edge_delta` is `original - 1`
- With `LeverageBonus { beat_id: "strike", target_edge_delta_mod: 1 }`, a strike's `resolved.target_edge_delta` is `original + 1`

**AC4: Dispatch uses `resolved_beat_for`**
- 39-4 hard-coded Fighter stub is deleted
- Beat dispatch reads `resolved.edge_delta` and `resolved.target_edge_delta`
- OTEL `creature.edge_delta` span now includes non-empty `advancements_applied` when applicable

**AC5: Milestone grant path**
- Milestone event (ADR-021) triggers engine to push matching `AdvancementTier.id` into
  `acquired_advancements` and apply `EdgeMaxBonus` effects immediately
- Unknown tier id → fail loudly
- OTEL `advancement.tier_granted` span emitted

**AC6: Per-genre audit**
- A doc artifact (ADR annex or `docs/` file) lists all 10 genres and their effect-host
  decision (progression.yaml vs advancements.yaml)

**AC7: Wiring test**
- Build CharacterState, grant a Fighter tier via milestone path, dispatch a beat,
  assert the resolved beat reflects the effect and OTEL spans fired

## Assumptions

- `progression.yaml` affinity-tier struct already exists; extending it is additive
- `EdgeMaxBonus` mutates state on grant (one-shot); other effects are view-time resolution
- `RecoveryTrigger.while_strained` uses `current <= max/4` (matches UI Cracked state)
- The per-genre audit produces decisions, not content — content for non-heavy_metal
  genres lands in their own future stories
