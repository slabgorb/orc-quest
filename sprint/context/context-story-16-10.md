---
parent: context-epic-16.md
---

# Story 16-10: ResourcePool Struct + YAML Schema — Generic Named Resources with Thresholds

## Business Context

This formalizes what 16-1 prototyped. ResourcePool is the real struct with validation,
threshold detection, and patch integration. Every genre resource (Luck, Humanity, Heat,
Fuel-at-rest) becomes a first-class engine type.

## Technical Approach

### ResourcePool Struct

```rust
// New file: sidequest-game/src/resource_pool.rs

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourcePool {
    pub name: String,
    pub label: String,
    pub current: f64,
    pub min: f64,
    pub max: f64,
    pub voluntary: bool,
    pub decay_per_turn: f64,
    pub thresholds: Vec<ResourceThreshold>,
    #[serde(default)]
    pub fired_thresholds: HashSet<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceThreshold {
    pub at: f64,
    pub event_id: String,
    pub narrator_hint: String,
    pub direction: ThresholdDirection,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ThresholdDirection { CrossingDown, CrossingUp, Either }
```

### Core Methods

```rust
impl ResourcePool {
    pub fn apply_delta(&mut self, delta: f64) -> Vec<ThresholdEvent> { ... }
    pub fn tick_decay(&mut self) -> Vec<ThresholdEvent> { ... }
    pub fn validate_delta(&self, delta: f64) -> Result<(), ResourceError> { ... }
    pub fn from_definition(def: &ResourceDef) -> Self { ... }
}
```

`apply_delta` returns fired ThresholdEvents (checked against `fired_thresholds` for
idempotency). `validate_delta` checks bounds without applying.

### On GameSnapshot

```rust
// Replaces the HashMap<String, f64> from 16-1
pub resources: HashMap<String, ResourcePool>,
```

### ResourcePatch

```rust
// In patches.rs
pub struct ResourcePatch {
    pub deltas: Option<HashMap<String, f64>>,
}
```

### Validation Integration

PatchLegality (existing, 202 LOC) gets a new check:
- For each resource delta, call `pool.validate_delta(delta)`
- Reject if resource doesn't exist, or delta would violate bounds
- Initial mode: warn-and-clamp (log warning, clamp to bounds)

### YAML Schema (rules.yaml)

Same as 16-1 but now the loader creates ResourcePool instances:
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
```

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/resource_pool.rs` | NEW — ResourcePool, ResourceThreshold |
| `sidequest-game/src/state.rs` | resources field type upgrade |
| `sidequest-game/src/lib.rs` | Export resource_pool module |
| `sidequest-agents/src/patches.rs` | Add ResourcePatch |
| `sidequest-agents/src/patch_legality.rs` | Add resource validation |
| `sidequest-genre/src/models.rs` | ResourceDef struct (if not already from 16-1) |
| `sidequest-genre/src/loader.rs` | Load resources into ResourcePool instances |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct | ResourcePool with all fields serializes/deserializes |
| Apply delta | Positive and negative deltas change current correctly |
| Bounds | current never goes below min or above max |
| Threshold detection | Crossing a threshold fires ThresholdEvent |
| Idempotent | Re-crossing same threshold (save/load) doesn't re-fire |
| Decay | tick_decay applies decay_per_turn correctly |
| Validate | validate_delta rejects out-of-bounds deltas |
| Patch | ResourcePatch applies through existing patch pipeline |
| Load | ResourcePool created from genre pack YAML at session init |
| Persist | Resources survive save/load with correct values and fired set |
