---
parent: context-epic-39.md
workflow: wire-first
---

# Story 39-6: Heavy_metal Pact Push Currencies (Content + Prompt Wiring)

## Business Context

Makes heavy_metal's pact_working confrontation cost something the engine remembers.
Adds three `ResourcePool`s (`voice`, `flesh`, `ledger`) with `voluntary: true` and
**no auto-refill** (narrative recovery only — per ratified ADR-078 amendment). Extends
the existing five pact_working beats (invoke / commit_cost / steady_the_rite /
force_completion / close_the_book) with `resource_deltas`, so the narrator's prose
("an hour of life, a memory, a name, a year") is now typed mechanical debit.

Also changes pact_working's `category` from `social` to `ritual`, and adds a prompt
conditional in the unified narrator (ADR-067) for `category == "ritual"` that mirrors
the existing `in_combat` conditional — injecting the genre's ritual_narration_hints.

**Zero new engine code** — `resource_deltas` dispatch already wired in 39-4.

## Technical Guardrails

### CLAUDE.md Wiring Rules (MANDATORY — applies to ALL stories in this epic)

1. **Verify Wiring, Not Just Existence.** Prompt conditional must fire; run the narrator.
2. **Every Test Suite Needs a Wiring Test.**
3. **No Silent Fallbacks.** Pact beat missing a declared resource pool → fail loudly.
4. **No Stubbing.**
5. **Don't Reinvent — Wire Up What Exists.** ResourcePool + `in_combat` conditional patterns.

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/genre_packs/heavy_metal/rules.yaml` | Add three `resources` (voice/flesh/ledger); change `pact_working.category` to `ritual`; add `resource_deltas` to all five pact_working beats |
| `sidequest-content/genre_packs/heavy_metal/_drafts/edge-advancement-content.md` | Source — §3 (resources) + §4 (beat deltas) lift verbatim |
| `sidequest-api/crates/sidequest-agents/src/narrator/prompt.rs` (or wherever unified narrator prompt assembly lives — ADR-067) | Add `category == "ritual"` conditional mirroring `in_combat` |
| `sidequest-api/crates/sidequest-genre/src/models/rules.rs` | Add `ritual_narration_hints` field on `ConfrontationDef` (optional); or reuse existing `narrator_hints` |

### Patterns

- Resource schema per draft §3:
  ```yaml
  resources:
    - { name: voice,  label: "Voice",  min: 0, max: 10, starting: 10, voluntary: true }
    - { name: flesh,  label: "Flesh",  min: 0, max: 10, starting: 10, voluntary: true }
    - { name: ledger, label: "Ledger", min: 0, max: 10, starting: 10, voluntary: true }
  ```
- Beat deltas per draft §4 (final tuning is Keith's call):
  - `invoke.resource_deltas: { voice: -1 }`
  - `commit_cost.resource_deltas: { flesh: -2 }`
  - `steady_the_rite.resource_deltas: { voice: -1 }`
  - `force_completion.resource_deltas: { ledger: -3, flesh: -1 }`
  - `close_the_book.resource_deltas: {}` (or whatever §4 specifies)
- No auto-refill: resources have no `recovery_on_resolution` block
- Prompt conditional: when active `confrontation.def.category == "ritual"`, inject
  `ritual_narration_hints` into the narrator prompt just like `in_combat` injects combat hints

### Dependencies

- **Blocks on 39-4** (`resource_deltas` dispatch path wired)

## Scope Boundaries

**In scope:**
- Three ResourcePools in `heavy_metal/rules.yaml`
- `pact_working.category` → `ritual`
- `resource_deltas` on all five pact_working beats
- `ritual_narration_hints` prompt path (or reuse existing narrator_hints)
- `category == "ritual"` prompt conditional in unified narrator
- Wiring test: dispatch `commit_cost` beat → `flesh` pool decreases by 2; OTEL
  `resource_pool.debited` span emitted with `source: beat`
- Wiring test: narrator called with active ritual confrontation → prompt contains ritual hints

**Out of scope:**
- Voice/Flesh/Ledger UI (surfaces as part of character sheet work in 39-7)
- `BeatDiscount.resource_mod` advancement effects consuming resource_mod — the capability
  lands in 39-5; authored Pact-affinity tiers exercising it land in 39-8
- Combat beat rewrites (39-8)
- Sample pact invocations (39-8)

## AC Context

**AC1: Three resources declared**
- `heavy_metal/rules.yaml` has `resources:` with voice/flesh/ledger matching draft §3
- All three are `voluntary: true`, starting=max=10, no recovery block

**AC2: pact_working is a ritual**
- `pact_working.category == "ritual"` (was `social`)
- All five beats have `resource_deltas` matching draft §4

**AC3: Narrator prompt conditional fires**
- When an active confrontation has `category: "ritual"`, the unified narrator prompt
  includes the ritual hints block
- When `in_combat`, combat hints block still fires unchanged (no regression)

**AC4: Resource debits work end-to-end**
- Dispatch `commit_cost` beat → `voice/flesh/ledger` pools update correctly
- `resource_pool.debited` OTEL span fires with correct `delta` and `beat_id`
- Threshold hints fire where declared (e.g., `voice` at=1 `voice_spent` hint)

**AC5: No fallback**
- If a pact beat references an undeclared pool, loader/dispatch fails loudly

**AC6: Wiring tests**
- Integration test exercises the full path: load heavy_metal, start pact_working,
  dispatch commit_cost, assert pool state + OTEL + narrator-prompt content

## Assumptions

- `ConfrontationDef.category` is a free-form string or enum that accepts `ritual` — verify and extend if enum-bounded
- Existing `narrator_hints` on pact_working can be promoted to `ritual_narration_hints` if the prompt assembler pattern prefers a dedicated field
- `resource_deltas` dispatch path from 39-4 already routes through
  `state_mutations.rs:328-407` — this story adds the content, not the path
