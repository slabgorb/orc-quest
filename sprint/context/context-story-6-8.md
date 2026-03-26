---
parent: context-epic-6.md
---

# Story 6-8: Faction Agendas for low_fantasy Genre Pack Worlds

## Business Context

Same as story 6-7 but for the low_fantasy genre pack. Each low_fantasy world gets faction
agendas with goals, urgency, and injection rules authored in YAML. Low fantasy factions
tend toward political intrigue, resource control, and religious conflict rather than the
territorial warfare of mutant_wasteland.

**Spoiler policy:** low_fantasy content may contain unspoiled material — follow spoiler
protection rules for non-flickering_reach content.

## Technical Approach

Same YAML schema as story 6-7, themed for low fantasy:

```yaml
# genre_packs/low_fantasy/worlds/example_world.yaml
factions:
  - id: merchant_league
    name: "The Merchant League"
    agendas:
      - goal: "Monopolize river trade routes"
        urgency: 0.6
        scene_injection_rules:
          - condition: { type: TurnInterval, every_n_turns: 5 }
            event_template: "Merchant League raises tariffs at the river crossing"
          - condition: { type: MaturityMinimum, minimum: Mid }
            event_template: "Merchant League hires mercenaries to enforce trade exclusivity"
```

Low fantasy factions should feel grounded — no world-ending threats, just competing human
interests with escalating stakes.

## Scope Boundaries

**In scope:**
- Faction agenda YAML for all low_fantasy worlds
- 2-4 factions per world with thematically appropriate agendas
- Validation that YAML deserializes with story 6-4 types

**Out of scope:**
- Rust code changes (pure YAML content)
- mutant_wasteland content (story 6-7)
- Spoiler-sensitive plot details in event templates

## Acceptance Criteria

| AC | Detail |
|----|--------|
| YAML valid | All faction agenda YAML deserializes without error |
| Coverage | Every low_fantasy world has at least 2 factions with agendas |
| Grounded tone | Faction goals reflect political/economic conflict, not cosmic threats |
| Maturity gating | Some agendas gated to Early/Mid/Veteran maturity |
| Varied conditions | Mix of `TurnInterval`, `MaturityMinimum`, and `StakeActive` conditions |
| Spoiler safe | Event templates avoid revealing unspoiled plot details |
