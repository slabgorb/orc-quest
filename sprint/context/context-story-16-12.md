---
parent: context-epic-16.md
---

# Story 16-12: Wire Genre Resources — Luck, Humanity, Heat, Fuel as ResourcePool Instances

## Business Context

With ResourcePool built (16-10) and the threshold pipeline wired (16-11), declare the
actual genre resources that close the content-vs-engine gaps for spaghetti_western,
neon_dystopia, pulp_noir, and road_warrior.

## Technical Approach

### Spaghetti Western — Luck

```yaml
resources:
  - name: luck
    label: "Luck"
    min: 0
    max: 6
    starting: 3
    voluntary: true
    decay_per_turn: 0
    thresholds:
      - at: 1
        event_id: luck_desperation
        narrator_hint: "One bullet left in the chamber of fate."
        direction: crossing_down
      - at: 0
        event_id: luck_exhausted
        narrator_hint: "Luck has run dry. Every consequence is earned now."
        direction: crossing_down
```

### Neon Dystopia — Humanity

```yaml
resources:
  - name: humanity
    label: "Humanity"
    min: 0
    max: 100
    starting: 100
    voluntary: false
    decay_per_turn: 0
    thresholds:
      - at: 50
        event_id: humanity_cold
        narrator_hint: "Your chrome is showing. Emotional responses feel rehearsed. NPCs sense something off."
        direction: crossing_down
      - at: 25
        event_id: humanity_machine
        narrator_hint: "More machine than human. Empathy is a memory. The mirror shows someone you don't recognize."
        direction: crossing_down
      - at: 0
        event_id: humanity_lost
        narrator_hint: "Humanity gone. You are chrome and code. The meat is just a vehicle."
        direction: crossing_down
```

### Pulp Noir — Heat

```yaml
resources:
  - name: heat
    label: "Heat"
    min: 0
    max: 5
    starting: 0
    voluntary: false
    decay_per_turn: -0.1
    thresholds:
      - at: 3
        event_id: heat_noticed
        narrator_hint: "People are talking. The wrong people. Your name is being mentioned in rooms you've never entered."
        direction: crossing_up
      - at: 5
        event_id: heat_hunted
        narrator_hint: "Every faction knows your face. Doors that were open are closed. The Préfecture has a file with your photograph."
        direction: crossing_up
```

### Road Warrior — Fuel (at rest)

```yaml
resources:
  - name: fuel
    label: "Fuel"
    min: 0
    max: 20
    starting: 10
    voluntary: true
    decay_per_turn: 0
    thresholds:
      - at: 2
        event_id: fuel_critical
        narrator_hint: "Fumes. Maybe one more run. Maybe not."
        direction: crossing_down
      - at: 0
        event_id: fuel_empty
        narrator_hint: "Dry. The rig is dead weight now. Walk or fight for what's left."
        direction: crossing_down
```

Note: When a chase/encounter starts, fuel transfers from ResourcePool to
StructuredEncounter's SecondaryStats. When the encounter ends, remaining fuel
transfers back. This prevents double-tracking.

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/.../spaghetti_western/rules.yaml` | Add luck resource |
| `sidequest-content/.../neon_dystopia/rules.yaml` | Add humanity resource |
| `sidequest-content/.../pulp_noir/rules.yaml` | Add heat resource |
| `sidequest-content/.../road_warrior/rules.yaml` | Add fuel resource |
| Integration tests | Verify each resource loads, tracks, fires thresholds |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Luck works | Spendable, tracks 0-6, thresholds at 1 and 0 fire correctly |
| Humanity works | Involuntary, degrades from 100, thresholds at 50/25/0 |
| Heat works | Involuntary, increases from 0, decays -0.1/turn, thresholds at 3/5 |
| Fuel works | Voluntary, transfers to/from encounter SecondaryStats |
| Narrator sees them | All four resources appear in narrator prompt context |
| KnownFacts | Threshold crossings create permanent facts in LoreStore |
| No double track | Fuel not tracked in both ResourcePool and encounter simultaneously |
