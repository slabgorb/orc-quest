---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-8: Playtest heavy_metal with Full New System (Acceptance Gate)

## Business Context

The Sebastien-gate. Epic 39 ships only if the GM panel can explain every Edge change,
every advancement effect, and every push cost with OTEL-backed causality — and the
narrator never violates SOUL §12 (describes the player doing something they didn't ask).

This story is content + playtest, not engine. It authors the heavy_metal advancement
tree (`mechanical_effects` on Iron/Pact/Court/Ruin/Craft/Lore affinity tiers per draft
§2), rewrites `confrontations[type=combat]` beats with real `edge_delta` /
`target_edge_delta` values, authors three sample pact invocations
(Frost-Letter / Borrowed-Year / Ledger-Refused) as playtest fixtures, and runs the full
heavy_metal playtest with Keith.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** The playtest IS the wiring check.
2. **Every Test Suite Needs a Wiring Test.** The OTEL-trail audit serves as wiring test.
3. **No Silent Fallbacks.**
4. **No Stubbing.**
5. **Don't Reinvent — Wire Up What Exists.**

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/genre_packs/heavy_metal/progression.yaml` | Author `mechanical_effects` on all six affinity tiers per draft §2; Craft and Lore tiers 2-3 carry `mechanical_effects: []  # TODO ADR-079` stubs |
| `sidequest-content/genre_packs/heavy_metal/rules.yaml` | Rewrite `confrontations[type=combat]` beats with real `edge_delta`/`target_edge_delta` values per draft §5 |
| `sidequest-content/genre_packs/heavy_metal/_drafts/edge-advancement-content.md` | Source — §2 + §5 + §6 lift here |
| `sidequest-content/genre_packs/heavy_metal/playtest/` (new dir) | Three sample pact fixtures: Frost-Letter, Borrowed-Year, Ledger-Refused |
| `scripts/playtest/heavy_metal_edge_acceptance.md` (new) | Playtest script with expected OTEL checkpoints |

### Patterns

- Combat beat tuning (first pass):
  - `strike { edge_delta: 0, target_edge_delta: 2 }`
  - `brace { edge_delta: -1, target_edge_delta: 0 }`
  - `committed_blow { edge_delta: 3, target_edge_delta: 4 }`
  - `break_contact` — resolution beat, no deltas
  - `read_the_opponent` — patience beat (ratified in ADR-078 amendments)
- Advancement tree (first pass for Fighter per draft §2):
  - Steel Lungs → `EdgeMaxBonus { amount: 2 }`
  - Second Wind → `EdgeRecovery { trigger: OnBeatSuccess { beat_id: "strike", while_strained: false }, amount: 1 }`
  - Headlong → `BeatDiscount { beat_id: "committed_blow", edge_delta_mod: -1 }`
  - Cleaver → `LeverageBonus { beat_id: "strike", target_edge_delta_mod: 1 }`
- Parallel trees for Warlock / Bard / Sorcerer land in this story; other classes can
  follow post-playtest
- Sample pact fixtures are narrative scaffolds — scene-start, expected beat order,
  expected resource spends, expected OTEL checkpoints

### Dependencies

- **Blocks on 39-5, 39-6, 39-7** — needs advancement engine, push-currency content,
  save/UI all landed

## Scope Boundaries

**In scope:**
- heavy_metal `progression.yaml` `mechanical_effects` (all six affinity tiers, tuned per draft §2)
- heavy_metal combat beats rewritten with real edge/target_edge values
- Three sample pact fixtures authored
- Playtest script with OTEL checkpoints
- Full end-to-end playtest with Keith
- GM-panel audit: every Edge change, advancement effect, push cost has OTEL trail with causality

**Out of scope:**
- Other nine genre packs (post-playtest rollout)
- Additional class advancement trees beyond Fighter/Warlock/Bard/Sorcerer
- Tuning passes beyond first-pass numbers (follow-up retune ticket if playtest demands)
- Four deferred advancement variants (ADR-079)

## AC Context

**AC1: heavy_metal progression.yaml authored**
- All six affinity tiers have `mechanical_effects` (Craft/Lore 2-3 may be stubbed per ratified amendment)
- Loader accepts the YAML without error
- `resolved_beat_for` returns non-empty `source_effects` on matching beats

**AC2: Combat beats rewritten**
- `strike`, `brace`, `committed_blow`, `break_contact`, `read_the_opponent` have real
  `edge_delta` / `target_edge_delta` values
- Existing combat flow (beat selection, resolution branch) works unchanged

**AC3: Three sample pacts run end-to-end**
- Frost-Letter: spends Voice + Flesh as expected; narrator honors `category: ritual` hints
- Borrowed-Year: spends Ledger as expected
- Ledger-Refused: player refuses `commit_cost`; narrator handles refusal gracefully
- All three OTEL trails are coherent and causality-complete

**AC4: Combat encounter resolves via Edge**
- A combat confrontation runs from engagement to composure_break
- `encounter.composure_break` OTEL span fires
- Narrator describes the resolving hit; engine owns state mutation

**AC5: Advancement earned and applied mid-playtest**
- A milestone fires during the playtest
- Matching `AdvancementTier` lands in `acquired_advancements`
- Subsequent beat dispatch reflects the effect
- `advancement.tier_granted` + `advancement.effect_applied` OTEL spans fire

**AC6: Sebastien-panel check**
- For every Edge change, the GM panel shows: source (beat_id), magnitude (delta),
  advancements applied, resulting state
- For every push cost, the panel shows: pool, delta, beat_id
- Narrator never contradicts engine state (HP never mentioned; state stays consistent)

**AC7: SOUL §12 test**
- No narrator output during the playtest describes the player doing something they
  didn't ask to do
- No "you take 4 damage" where the player didn't choose the beat that cost Edge
- Failure here = epic fails acceptance; loop back

**AC8: Save/reload during playtest**
- Saving mid-playtest and reloading preserves Edge, `acquired_advancements`, and push-pool state
- Round-trip verified against OTEL state before save and after load

## Assumptions

- Playtest save may be a fresh roll (legacy-save migration was verified in 39-7 with
  fixture tests; this playtest starts clean)
- First-pass combat numbers are tuning targets, not permanent — if playtest reveals
  miscalibration, retune in YAML and document; re-running is cheap
- Keith is the playtest driver; scribe captures OTEL trails and SOUL §12 test outcomes
- This story closes the epic on success; failure opens a retune/scope follow-up, not a
  revert
