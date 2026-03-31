---
parent: context-epic-16.md
---

# Story 16-7: Social Confrontation Types — Negotiation, Interrogation, Trial

## Business Context

Social encounters are the most common "structured but not combat" situation across all
genres. A tense negotiation in pulp_noir, a Parliamentary debate in victoria, a tribal
council in elemental_harmony — all follow the same shape: two sides, a leverage metric,
persuasion/threat/concession beats. Currently 100% LLM-improvised.

## Technical Approach

### Genre-Agnostic Templates

These are base templates any genre can use or override:

**Negotiation** (bidirectional metric):
```yaml
- type: negotiation
  label: "Tense Negotiation"
  category: social
  metric:
    name: leverage
    direction: bidirectional
    starting: 5
    threshold_high: 10   # total victory
    threshold_low: 0     # total defeat
  beats:
    - id: persuade
      label: "Make Your Case"
      metric_delta: 2
      stat_check: PRESENCE  # or genre equivalent
    - id: threaten
      label: "Threaten"
      metric_delta: 3
      stat_check: NERVE
      risk: "faction reputation -1 if it fails"
    - id: concede_point
      label: "Concede a Point"
      metric_delta: -1
      effect: "opponent disposition +5, reveals their real goal"
    - id: walk_away
      label: "Walk Away"
      resolution: true
      consequence: "deal collapses, reputation intact"
  mood: tension
```

**Interrogation** (descending metric — breaking resistance):
```yaml
- type: interrogation
  label: "Interrogation"
  category: social
  metric:
    name: resistance
    direction: descending
    starting: 10
    threshold_low: 0    # subject breaks
  beats:
    - id: pressure
      label: "Apply Pressure"
      metric_delta: -2
      stat_check: NERVE
      risk: "subject shuts down if check fails badly"
    - id: rapport
      label: "Build Rapport"
      metric_delta: -1
      stat_check: PRESENCE
      effect: "safe — no risk, slow progress"
    - id: evidence
      label: "Present Evidence"
      metric_delta: -3
      requires: "must have discovered relevant clue"
  mood: tension
```

### Where They Live

- Base templates in a shared location (genre-agnostic defaults)
- Genres can override with genre-flavored versions in their own rules.yaml
- pulp_noir gets interrogation. victoria gets trial/debate. All genres get negotiation.

### Key Files

| File | Action |
|------|--------|
| `sidequest-genre/src/models.rs` | Ensure ConfrontationDef supports all social beat fields |
| `sidequest-content/genre_packs/*/rules.yaml` | Add social confrontation declarations per genre |
| `sidequest-game/src/encounter.rs` | Social encounter convenience constructors |
| Integration test | Negotiation sequence: persuade → concede → threaten → resolution |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Bidirectional | Negotiation leverage swings both directions |
| Descending | Interrogation resistance decreases toward break |
| Beats | All beat types (persuade, threaten, concede, pressure, rapport, evidence) work |
| Risk | Failed stat checks on risky beats have consequences |
| Walk away | Player can exit negotiation at any point |
| Genre override | A genre can declare its own negotiation variant that replaces the default |
