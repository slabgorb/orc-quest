---
parent: context-epic-16.md
---

# Story 16-5: Migrate Chase as Confrontation — ChaseState Becomes StructuredEncounter Preset

## Business Context

The existing chase system (1,188 LOC across chase.rs + chase_depth.rs) is the prototype
for StructuredEncounter. This story expresses all chase functionality through the
StructuredEncounter interface while keeping ChaseState as a convenience API.

## Technical Approach

### Mapping

| ChaseState field | StructuredEncounter equivalent |
|-----------------|------------------------------|
| `chase_type: ChaseType` | `encounter_type: "chase_footrace"` / `"chase_stealth"` / `"chase_negotiation"` |
| `separation_distance: i32` | `metric.current` with name "separation" |
| `goal: i32` | `metric.threshold_high` |
| `escape_threshold: f64` | stored in metric or encounter config |
| `rig: Option<RigStats>` | `secondary_stats` with RigStats values |
| `actors: Vec<ChaseActor>` | `actors: Vec<EncounterActor>` with role strings |
| `beat: u32` | `beat: u32` (direct) |
| `structured_phase: Option<ChasePhase>` | `structured_phase: Option<EncounterPhase>` |
| `outcome: Option<ChaseOutcome>` | `outcome: Option<String>` ("escape", "caught", "crashed", "abandoned") |

### ChaseState as Convenience Layer

```rust
impl StructuredEncounter {
    pub fn chase(chase_type: &str, escape_threshold: f64) -> Self { ... }
    pub fn vehicle_chase(chase_type: &str, threshold: f64, rig_type: &str, goal: i32) -> Self { ... }
}

// Type alias for backward compat
pub type ChaseState = StructuredEncounter;
```

### Chase Depth Functions

All functions in chase_depth.rs (terrain_modifiers, phase_for_beat, check_outcome,
format_chase_context, cinematography_for_phase) should work on StructuredEncounter
fields. Adjust signatures to accept generic encounter fields rather than ChaseState
specifically.

### Test Strategy

Every existing test in chase.rs and chase_depth.rs must pass. Strategy:
1. Update test constructors to use StructuredEncounter::chase()
2. Update field access to go through encounter API
3. Assert identical behavior

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/chase.rs` | Thin wrapper over StructuredEncounter |
| `sidequest-game/src/chase_depth.rs` | Functions accept encounter types |
| `sidequest-game/src/encounter.rs` | Chase convenience constructors |
| All chase tests | Update constructors, same assertions |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| All chase tests pass | Every test in chase.rs passes via StructuredEncounter |
| All chase_depth tests pass | Every test in chase_depth.rs passes |
| Rig stats work | RigStats expressible through SecondaryStats, all damage/fuel tests pass |
| Cinematography | Camera modes, sentence ranges, format_chase_context all work |
| Terrain | Terrain modifiers, danger escalation all work |
| Beat system | Beat advancement, phase transitions, outcome checking all work |
| Server wiring | shared_session.rs chase references compile and function |
