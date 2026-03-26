---
parent: context-epic-10.md
---

# Story 10-2: Genre Archetype OCEAN Baselines — Default Profiles per NPC Archetype, Random Generation

## Business Context

Genre packs define NPC archetypes (scholarly wizard, grizzled mercenary, devout priest). Each
archetype should carry a baseline OCEAN profile so that all scholarly wizards start with similar
personality traits (high openness, high conscientiousness, low extraversion). When the system
generates unnamed NPCs, it applies random variance to the baseline so they feel distinct but
genre-consistent.

**Python reference:** `sq-2/sprint/epic-64.yaml` — archetype YAML gained `ocean_baseline` dict;
random gen applied `±1.5` variance per dimension, clamped to 0.0-10.0.

**Depends on:** Story 10-1 (OceanProfile struct).

## Technical Approach

### Genre Pack YAML Extension

```yaml
archetypes:
  scholar_wizard:
    ocean_baseline:
      openness: 8.5
      conscientiousness: 7.0
      extraversion: 3.0
      agreeableness: 6.0
      neuroticism: 4.0
    ocean_variance: 1.5  # optional, defaults to 1.5
```

### Deserialization

```rust
#[derive(Deserialize)]
pub struct ArchetypeOcean {
    pub ocean_baseline: OceanProfile,
    #[serde(default = "default_variance")]
    pub ocean_variance: f64,
}

fn default_variance() -> f64 { 1.5 }
```

### Random Generation

```rust
impl OceanProfile {
    pub fn with_variance(&self, variance: f64, rng: &mut impl Rng) -> Self {
        let mut profile = self.clone();
        for dim in OceanDimension::all() {
            let offset = rng.gen_range(-variance..=variance);
            profile.set(dim, (profile.get(dim) + offset).clamp(0.0, 10.0));
        }
        profile
    }
}
```

The `rng` parameter keeps generation deterministic in tests. Production passes
`thread_rng()`.

## Scope Boundaries

**In scope:**
- `ocean_baseline` and `ocean_variance` fields in genre pack archetype YAML
- Deserialization into `OceanProfile` from archetype config
- `with_variance()` method for random NPC generation
- Fallback to `default_midpoint()` if archetype has no baseline

**Out of scope:**
- Behavioral summary text (10-3)
- Backfilling existing genre packs (10-8)
- Named NPC overrides (named NPCs may have hand-set profiles in YAML)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| YAML parsed | Genre pack archetype with `ocean_baseline` deserializes to `OceanProfile` |
| Missing baseline | Archetype without `ocean_baseline` defaults to midpoint (5.0 all) |
| Variance applied | `with_variance(1.5)` produces values within ±1.5 of baseline |
| Clamped | Random generation never produces values outside 0.0-10.0 |
| Deterministic | Same seed + same baseline = same generated profile |
| Genre consistent | Two NPCs from same archetype have correlated but not identical profiles |
