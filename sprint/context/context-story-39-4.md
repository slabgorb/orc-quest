---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-4: BeatDef.edge_delta + target_edge_delta + Beat Dispatch Wiring

## Business Context

The story that makes Edge real. Extends `BeatDef` with three symmetric optional fields
(`edge_delta`, `target_edge_delta`, `resource_deltas`) parallel to the existing
`gold_delta` at `beat.rs:319-337`. Implements the self-debit and target-debit handler
blocks in `handle_applied_side_effects`, emits OTEL `creature.edge_delta` and
`encounter.composure_break`, and auto-resolves the encounter on `Edge <= 0`.

Includes a **hard-coded advancement stub** (Fighter `+2 edge_max`) so Keith can run a
heavy_metal combat at story-end and *feel* whether Edge reads right before committing
39-5–39-8 effort. This is the smoke-gate for the whole epic.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** Real DispatchContext, real beat, real mutation.
2. **Every Test Suite Needs a Wiring Test.**
3. **No Silent Fallbacks.** Missing primary opponent when `target_edge_delta` is set → fail loudly.
4. **No Stubbing.** The Fighter `+2` advancement stub is named and explicitly scoped — replaced in 39-5.
5. **Don't Reinvent — Wire Up What Exists.** Mirror `gold_delta` block line-for-line.

### Key Files

| File | Action |
|------|--------|
| `sidequest-api/crates/sidequest-genre/src/models/rules.rs` | Add `edge_delta: Option<i32>`, `target_edge_delta: Option<i32>`, `resource_deltas: Option<HashMap<String, f64>>` to `BeatDef` |
| `sidequest-api/crates/sidequest-server/src/dispatch/beat.rs` | Self-debit block (parallel to gold_delta at :319-337); target-debit block; composure-break check; OTEL emits |
| `sidequest-api/crates/sidequest-server/src/dispatch/beat.rs` | Hard-coded advancement stub: if acting_char.class == "Fighter", `edge.max += 2` on build |
| `sidequest-api/crates/sidequest-telemetry/` | Register `creature.edge_delta`, `encounter.composure_break` span names |
| `sidequest-content/genre_packs/heavy_metal/rules.yaml` | Add test-fixture `edge_delta` values to at least one combat beat (e.g., `strike.target_edge_delta: 2`) so the smoke gate has something to fire |

### Patterns

- Self-debit pseudocode:
  ```
  if let Some(delta) = beat.edge_delta {
      let result = acting_char.core.edge.apply_delta(-delta); // positive = cost
      for crossed in result.crossed { mint_threshold_lore(...); }
      emit_otel("creature.edge_delta", { action, source: "beat", beat_id, delta, new_current });
  }
  ```
- Target-debit: walk `ctx.snapshot.encounter.actors`, pick first `role=opponent`, apply delta
- Composure break: check after both debits; set `encounter.resolved = true`; emit `encounter.composure_break`
- `resource_deltas` routes through existing `state_mutations.rs:328-407` path — no new code path

### Dependencies

- **Blocks on 39-1, 39-2, 39-3** (types + heavy_metal edge_config)

## Scope Boundaries

**In scope:**
- `BeatDef` three new optional fields + serde
- Self-debit block in `handle_applied_side_effects`
- Target-debit block (primary opponent only, v1)
- `resource_deltas` dispatched through existing ResourcePool path
- Auto-resolution when `Edge <= 0`
- OTEL: `creature.edge_delta`, `encounter.composure_break` spans
- Hard-coded Fighter `+2 edge_max` advancement stub (replaced in 39-5)
- Real wiring test: build DispatchContext, dispatch `strike` with `target_edge_delta: 2`, assert opponent's `core.edge.current` decreased by 2
- Smoke-gate playtest in heavy_metal — Keith-run

**Out of scope:**
- `AdvancementTree` / `resolved_beat_for` (39-5 — stub suffices here)
- Multi-target beats (deferred)
- Authored advancement YAML content (39-5)
- Pact push-currency content (39-6)
- Save migration / UI (39-7)
- Full combat beat rewrites (39-8)

## AC Context

**AC1: `BeatDef` extended**
- Three optional fields present with serde `#[serde(default)]`
- Existing beats without the keys deserialize unchanged

**AC2: Self-debit wired**
- Beat with `edge_delta: 2` dispatched → acting char's `core.edge.current` decreases by 2
- Thresholds cross correctly (e.g., LoreFragment minted at `at: 1`)
- OTEL `creature.edge_delta` span emitted with fields: `action`, `source`, `beat_id`, `delta`, `new_current`, `advancements_applied`

**AC3: Target-debit wired**
- Beat with `target_edge_delta: 2` dispatched → primary opponent's `core.edge.current` decreases by 2
- If no primary opponent found, load/dispatch fails loudly (no silent skip)

**AC4: Composure break auto-resolves**
- When `Edge <= 0` on acting char or primary opponent → `encounter.resolved = true`
- OTEL `encounter.composure_break` span emitted
- Existing resolution branch at `beat.rs:396` handles the rest unchanged

**AC5: resource_deltas path**
- Beat with `resource_deltas: { voice: -1 }` → ResourcePool for `voice` debits by 1
  (voice pool doesn't exist in heavy_metal yet until 39-6, so test against a fabricated
  ResourcePool or a genre that has one)

**AC6: Wiring test (replaces the false-positive)**
- Integration test builds real `DispatchContext`, calls `apply_beat_dispatch` +
  `handle_applied_side_effects` on a real `strike` beat from `heavy_metal/rules.yaml`
- Asserts `ctx.snapshot.characters[0].core.edge.current` decreased
- Asserts OTEL span emitted
- This is NOT regex-source-matching

**AC7: Smoke gate**
- Keith runs a heavy_metal combat end-to-end. Acceptance subjective: Edge visibly ticks
  down through beats; composure_break fires; GM panel OTEL shows causality; narration
  still reads as prose

## Assumptions

- Primary-opponent selection v1 = first actor with `role=opponent`; multi-target is
  follow-up per plan
- Fighter `+2 edge_max` stub applied in `CharacterState::new` or equivalent — OK to put
  an explicit comment tagging it `// REPLACED IN 39-5 (ADR-078)`
- The false-positive `beat_dispatch_wiring_story_28_5_tests.rs` is rewritten in 39-7;
  this story's wiring test is additive (new file or new test fn), not a rewrite
