---
parent: context-epic-1.md
---

# Story 1-5: Trope Inheritance + Scenario Packs — Extends Resolution, Cycle Detection, ScenarioPack

## Business Context

Tropes are the creative backbone of SideQuest — they define character archetypes, narrative
patterns, and world flavor. Inheritance (`extends`) lets genre authors compose tropes without
duplication (e.g., a "grizzled veteran" trope extending a base "fighter" trope). Cycle
detection prevents infinite resolution loops.

ScenarioPack is the unit of playable content — without it, there is no "what are we playing
today?" This story turns raw genre data into composable, playable content definitions.

**Python sources:**
- `sq-2/sidequest/genre/resolve.py` — trope inheritance resolution
- `sq-2/sidequest/scenario/` — scenario pack models and loading

## Technical Guardrails

- **Port lesson #14 (trope inheritance):** Python only resolves one level of `extends`.
  Rust resolves multi-level chains with topological sorting
- **Cycle detection:** Genre pack authors can create circular `extends` references. Detect
  and report clear errors before infinite recursion
- **ADR-018 (Trope Engine):** DORMANT-to-RESOLVED lifecycle, escalation beats, passive progression
- **ADR-030 (Scenario Packs):** ScenarioPack bundles scenario metadata, assignment matrices
- **Merge semantics:** Child trope fields override parent. Missing child fields inherit
  from parent. Arrays are replaced, not merged

## Scope Boundaries

**In scope:**
- `resolve_trope_inheritance()` with multi-level extends resolution
- Cycle detection with clear error messages
- `ScenarioPack` struct and loading through the unified loader from 1-4
- Tests for multi-level inheritance, cycle detection, and scenario loading

**Out of scope:**
- Trope runtime state machine (story 1-7)
- Lore RAG system (future epic)
- Scenario execution logic (whodunit, rat-hunt — future epic)
- Corpus text loading (used by RAG, not core loader)

## AC Context

| AC | Detail |
|----|--------|
| Multi-level extends | A->B->C chains resolve correctly, grandparent fields propagated |
| Cycle detection | A->B->A produces a clear error, not infinite recursion |
| ScenarioPack loads | Scenario packs load through unified loader |
| Merge semantics | Child fields override parent; missing fields inherit |
| Real YAML | Tests verify against actual genre pack trope definitions |

## Assumptions

- The `extends` resolution algorithm is well-documented in ADRs and Python source
- ScenarioPack is a read-only structure resolved at session start, not mutated during play
- Cycle detection is needed because genre pack authors are humans who make mistakes
