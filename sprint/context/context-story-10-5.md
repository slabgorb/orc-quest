---
parent: context-epic-10.md
---

# Story 10-5: OCEAN Shift Log — Track Personality Changes with Cause Attribution

## Business Context

Personalities evolve. A trusting NPC who gets betrayed should become less agreeable over time.
This story adds structured tracking for personality changes so every shift records what
dimension changed, by how much, and why. The shift log makes personality evolution auditable
and enables future features (lore indexing, UI history).

**Python reference:** `sq-2/sprint/epic-64.yaml` — shifts stored as list of dicts with
dimension, old/new value, cause string, and turn number. Rust uses a typed struct.

**Depends on:** Story 10-1 (OceanProfile struct).

## Technical Approach

### Shift Model

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OceanShift {
    pub dimension: OceanDimension,
    pub old_value: f64,
    pub new_value: f64,
    pub cause: String,        // "betrayed by trusted ally"
    pub turn_id: u64,
}
```

### Shift Application

```rust
impl OceanProfile {
    pub fn apply_shift(
        &mut self,
        dim: OceanDimension,
        delta: f64,
        cause: &str,
        turn_id: u64,
    ) -> OceanShift {
        let old = self.get(dim);
        let new = (old + delta).clamp(0.0, 10.0);
        self.set(dim, new);
        OceanShift { dimension: dim, old_value: old, new_value: new,
                     cause: cause.to_string(), turn_id }
    }
}
```

### Shift Log on NPC

```rust
pub struct Npc {
    // ... existing fields
    pub ocean: OceanProfile,
    pub ocean_shifts: Vec<OceanShift>,
}
```

The log is append-only. Shifts are never removed or edited. The full history is available
for inspection and future lore indexing (Epic 11).

### Serialization

Shift log serializes with the NPC for save/load. The `OceanDimension` enum uses
`#[serde(rename_all = "snake_case")]` for clean JSON output.

## Scope Boundaries

**In scope:**
- `OceanShift` struct with dimension, old/new values, cause, turn_id
- `apply_shift()` method that mutates profile and returns shift record
- `ocean_shifts: Vec<OceanShift>` on NPC struct
- Serialization/deserialization of shift log

**Out of scope:**
- Who proposes shifts (10-6 — world state agent)
- Lore indexing of shifts (Epic 11)
- UI display of shift history
- Shift rate limiting or dampening

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Shift recorded | `apply_shift(Agreeableness, -2.0, "betrayed", 42)` returns OceanShift |
| Profile updated | After shift, `get(Agreeableness)` reflects new value |
| Clamped | Shift that would push value below 0.0 clamps to 0.0 |
| Log appended | Shift appears in `npc.ocean_shifts` |
| Cause preserved | Shift cause string is stored verbatim |
| Round-trip | Serialize NPC with shifts → deserialize → shifts intact |
| Append-only | No API to remove or modify existing shifts |
