---
parent: context-epic-6.md
---

# Story 6-7: Faction Agendas for mutant_wasteland Genre Pack Worlds

## Business Context

The `FactionAgenda` model (story 6-4) needs content. This story authors faction agendas
for the mutant_wasteland genre pack — the spoilable test genre used for development. Each
world in the genre pack defines factions with goals, urgency levels, and scene injection
rules. This is YAML content authoring, not Rust code.

**Spoiler policy:** mutant_wasteland/flickering_reach is fully spoilable.

## Technical Approach

Faction agendas are added to existing world YAML files in `genre_packs/mutant_wasteland/`:

```yaml
# genre_packs/mutant_wasteland/worlds/flickering_reach.yaml
factions:
  - id: rust_brothers
    name: "The Rust Brothers"
    agendas:
      - goal: "Expand scrap territory into the Flickering Reach"
        urgency: 0.7
        scene_injection_rules:
          - condition: { type: TurnInterval, every_n_turns: 4 }
            event_template: "Rust Brothers scouts spotted near the settlement"
          - condition: { type: MaturityMinimum, minimum: Early }
            event_template: "Rust Brothers demand tribute from local traders"

  - id: glow_seekers
    name: "The Glow Seekers"
    agendas:
      - goal: "Locate and control radiation hotspots for power"
        urgency: 0.5
        scene_injection_rules:
          - condition: { type: MaturityMinimum, minimum: Mid }
            event_template: "Glow Seekers establish a shrine at a radiation well"
```

Each faction should have 2-4 agendas with varied urgency and conditions to create a
layered world progression.

## Scope Boundaries

**In scope:**
- Faction agenda YAML for all mutant_wasteland worlds
- 2-4 factions per world with agendas and injection rules
- Validation that YAML deserializes correctly with story 6-4 types

**Out of scope:**
- Rust code changes (pure YAML content)
- low_fantasy faction agendas (story 6-8)
- Faction relationship mechanics

## Acceptance Criteria

| AC | Detail |
|----|--------|
| YAML valid | All faction agenda YAML deserializes without error |
| Coverage | Every mutant_wasteland world has at least 2 factions with agendas |
| Varied urgency | Urgency values span 0.3-0.9 across factions |
| Maturity gating | Some agendas gated to Early/Mid/Veteran maturity |
| Turn intervals | At least some agendas use `TurnInterval` condition |
| Thematic fit | Faction goals are consistent with mutant_wasteland setting |
