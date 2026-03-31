---
parent: context-epic-16.md
---

# Story 16-1: Narrator Resource Injection — Serialize Genre Resource State into Prompt Context

## Business Context

Every genre pack defines resources in rules.yaml (Luck, Humanity, Heat, etc.) but the
narrator has no structured awareness of their current values. The LLM reads the rules
once and progressively forgets. This story gets immediate value across all 9 genres by
injecting current resource state into every narrator prompt — zero new types, just wiring.

This is the 80% fix. The formal ResourcePool (16-10) adds validation and UI later.

## Technical Approach

### Parse Resource Declarations

Read `resources` from the genre pack's rules.yaml at session init. For now, track
values as a simple `HashMap<String, f64>` on the session (or GameSnapshot extras).
No ResourcePool struct yet — that's 16-10.

### Prompt Injection

In `prompt_framework/` (1,484 LOC), add a Situational zone section that serializes
current resource state:

```
[GENRE RESOURCES]
Luck: 2/6 (voluntary — player can spend)
  ⚠ Threshold at 1: "One bullet left in the chamber of fate."
Heat: 3/5 (involuntary — decays 0.1/turn)
```

This goes after the existing game state injection and before the grounding zone.

### Track Deltas from LLM Output

Parse resource mentions from narrator output (regex or extractor). When narrator says
"you spend 1 Luck," decrement the tracked value. No formal validation yet — trust the
LLM, track the state, inject it next turn. Validation comes in 16-10.

### Key Files

| File | Action |
|------|--------|
| `sidequest-genre/src/models.rs` | Add resource declaration structs to genre model |
| `sidequest-genre/src/loader.rs` | Parse `resources` from rules.yaml |
| `sidequest-agents/src/prompt_framework/mod.rs` | Add resource state section |
| `sidequest-game/src/state.rs` | Add `resource_state: HashMap<String, f64>` to GameSnapshot |

## Scope Boundaries

**In scope:**
- Parse resource declarations from rules.yaml
- Track current values as HashMap
- Inject into narrator prompt every turn
- Simple delta tracking from LLM output

**Out of scope:**
- ResourcePool struct (16-10)
- Threshold events / KnownFacts (16-11)
- UI display (16-13)
- Patch validation (16-10)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Parse | Resource declarations load from any genre pack's rules.yaml |
| Inject | Current resource state appears in narrator prompt context |
| Track | Resource values update when narrator mentions spend/gain |
| Persist | Resource values survive save/load cycle |
| All genres | Works for packs with and without resource declarations |
