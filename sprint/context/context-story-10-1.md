---
parent: context-epic-10.md
---

# Story 10-1: OCEAN Profile on NPC Model — Add Five Float Fields (0.0-10.0) to NPC Struct

## Business Context

Every NPC needs a persistent personality anchor so the narrator produces consistent behavior
across turns. Without it, the same NPC can be bold in one scene and timid in the next because
the LLM has no personality state to reference. The OCEAN model gives five continuous dimensions
that are compact to store and intuitive to interpret.

**Python reference:** `sq-2/sprint/epic-64.yaml` — added `ocean_profile` dict to NPC model
with five float fields. The Rust port uses a dedicated struct with `f64` fields instead of
a loose dict.

**Depends on:** Story 2-5 (NPC struct must exist in game state).

## Technical Approach

Add `OceanProfile` as a standalone struct and attach it to the NPC model:

```rust
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct OceanProfile {
    pub openness: f64,
    pub conscientiousness: f64,
    pub extraversion: f64,
    pub agreeableness: f64,
    pub neuroticism: f64,
}

impl OceanProfile {
    pub fn default_midpoint() -> Self {
        Self { openness: 5.0, conscientiousness: 5.0, extraversion: 5.0,
               agreeableness: 5.0, neuroticism: 5.0 }
    }

    pub fn clamp(&mut self) {
        self.openness = self.openness.clamp(0.0, 10.0);
        // ... same for all five
    }
}
```

The `OceanDimension` enum enables generic operations over any dimension:

```rust
pub enum OceanDimension {
    Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism,
}

impl OceanProfile {
    pub fn get(&self, dim: OceanDimension) -> f64 { ... }
    pub fn set(&mut self, dim: OceanDimension, value: f64) { ... }
}
```

NPC struct gains `pub ocean: OceanProfile` field. Existing NPCs without profiles get
`default_midpoint()` on deserialization via `#[serde(default)]`.

## Scope Boundaries

**In scope:**
- `OceanProfile` struct with five `f64` fields, `Serialize`/`Deserialize`
- `OceanDimension` enum with get/set accessors
- `clamp()` to enforce 0.0-10.0 bounds
- `default_midpoint()` constructor
- Add `ocean` field to NPC struct with `#[serde(default)]`

**Out of scope:**
- Genre archetype baselines (10-2)
- Behavioral summary text (10-3)
- Shift tracking (10-5)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct exists | `OceanProfile` with five `f64` fields compiles and derives Serialize/Deserialize |
| NPC has field | NPC struct carries `ocean: OceanProfile` |
| Clamping | Values outside 0.0-10.0 are clamped after set |
| Default | `default_midpoint()` returns all 5.0 |
| Enum access | `get(OceanDimension::Openness)` returns the openness value |
| Backward compat | Deserialization of NPC JSON without `ocean` field succeeds via serde default |
| Round-trip | Serialize → deserialize preserves all five values |
