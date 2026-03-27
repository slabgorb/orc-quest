---
parent: context-epic-6.md
---

# Story 6-8: Faction Agendas for elemental_harmony/shattered_accord Genre Pack Worlds

## Business Context

Same as story 6-7 but for the elemental_harmony genre pack, specifically the shattered_accord
world. This world gets faction agendas with goals, urgency, and injection rules authored in
YAML. Elemental harmony factions revolve around elemental balance, philosophical conflict
between harmony and chaos, and competing visions for how elemental forces should be wielded.

**Spoiler policy:** elemental_harmony content may contain unspoiled material — follow spoiler
protection rules for non-flickering_reach content.

## Technical Approach

Same YAML schema as story 6-7, themed for elemental harmony:

```yaml
# genre_packs/elemental_harmony/worlds/shattered_accord.yaml
factions:
  - id: accord_keepers
    name: "The Accord Keepers"
    agendas:
      - goal: "Restore the elemental balance pact"
        urgency: 0.6
        scene_injection_rules:
          - condition: { type: TurnInterval, every_n_turns: 5 }
            event_template: "Accord Keepers perform a binding ritual at the nexus"
          - condition: { type: MaturityMinimum, minimum: Mid }
            event_template: "Accord Keepers confront a rogue elementalist threatening the balance"
```

Elemental harmony factions should feel otherworldly but grounded in philosophical conflict —
competing visions of elemental stewardship with escalating consequences.

## Scope Boundaries

**In scope:**
- Faction agenda YAML for elemental_harmony/shattered_accord world
- 2-4 factions with thematically appropriate agendas
- Validation that YAML deserializes with story 6-4 types

**Out of scope:**
- Rust code changes (pure YAML content)
- mutant_wasteland content (story 6-7)
- Spoiler-sensitive plot details in event templates

## Acceptance Criteria

| AC | Detail |
|----|--------|
| YAML valid | All faction agenda YAML deserializes without error |
| Coverage | shattered_accord world has at least 2 factions with agendas |
| Thematic tone | Faction goals reflect elemental/philosophical conflict |
| Maturity gating | Some agendas gated to Early/Mid/Veteran maturity |
| Varied conditions | Mix of `TurnInterval`, `MaturityMinimum`, and `StakeActive` conditions |
| Spoiler safe | Event templates avoid revealing unspoiled plot details |
