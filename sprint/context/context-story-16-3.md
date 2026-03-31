---
parent: context-epic-16.md
---

# Story 16-3: Confrontation YAML Schema — Genre Loader Parses Encounter Declarations

## Business Context

Genres need to declare their encounter types in rules.yaml without writing Rust code.
The genre loader already parses rules, axes, cultures, tropes — this adds confrontation
type parsing to the same pipeline.

## Technical Approach

### YAML Schema

```yaml
# In rules.yaml
confrontations:
  - type: standoff
    label: "Standoff"
    category: pre_combat       # combat | social | pre_combat | movement
    metric:
      name: tension
      direction: ascending     # ascending | descending | bidirectional
      starting: 0
      threshold_high: 10
      threshold_low: null
    beats:
      - id: size_up
        label: "Size Up"
        metric_delta: 2
        stat_check: CUNNING
        reveals: opponent_detail
        risk: null
      - id: draw
        label: "Draw"
        metric_delta: 0
        resolution: true
        stat_check: DRAW
    secondary_stats:
      - name: focus
        source_stat: NERVE
        spendable: true
    escalates_to: combat       # null if standalone
    mood: standoff
```

### Genre Model Structs

Add to `sidequest-genre/src/models.rs`:

```rust
pub struct ConfrontationDef {
    pub confrontation_type: String,
    pub label: String,
    pub category: String,
    pub metric: MetricDef,
    pub beats: Vec<BeatDef>,
    pub secondary_stats: Vec<SecondaryStatDef>,
    pub escalates_to: Option<String>,
    pub mood: Option<String>,
}
```

### Loader

In `sidequest-genre/src/loader.rs`, parse `confrontations` key from rules.yaml.
Follow existing pattern — optional field, empty vec if absent. Validate:
- Each beat has unique id
- metric direction is a known value
- stat_check references a valid ability score name from the same rules.yaml
- escalates_to references a known confrontation type or "combat"

### Key Files

| File | Action |
|------|--------|
| `sidequest-genre/src/models.rs` | Add ConfrontationDef, MetricDef, BeatDef structs |
| `sidequest-genre/src/loader.rs` | Parse confrontations from rules.yaml |
| `sidequest-genre/src/validate.rs` | Schema validation for confrontation declarations |
| `sidequest-genre/tests/` | Loader tests with sample confrontation YAML |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Parse | Confrontation declarations load from rules.yaml |
| Validate | Invalid schema (missing fields, bad references) produces clear error |
| Empty OK | Packs without confrontations load normally (empty vec) |
| Stat check | stat_check validated against genre ability_score_names |
| Round-trip | Parsed ConfrontationDef serializes back to valid YAML |
