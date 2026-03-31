---
parent: context-epic-16.md
---

# Story 16-2: StructuredEncounter Trait + State — Universal Encounter Engine

## Business Context

ChaseState (287 LOC) + chase_depth.rs (901 LOC) already implement a rich structured
encounter system — metrics, beats, phases, secondary stats, terrain, cinematography.
But it's locked to chase semantics with hardcoded enums (ChaseType, RigType, ChaseRole).
Generalizing it lets standoffs, negotiations, net combat, and ship combat reuse the
same infrastructure via YAML declarations.

## Technical Approach

### StructuredEncounter (new struct, generalizes ChaseState)

```rust
pub struct StructuredEncounter {
    pub encounter_type: String,
    pub metric: EncounterMetric,
    pub beat: u32,
    pub structured_phase: Option<EncounterPhase>,
    pub secondary_stats: Option<SecondaryStats>,
    pub actors: Vec<EncounterActor>,
    pub outcome: Option<String>,
    pub resolved: bool,
    pub mood_override: Option<String>,
    pub narrator_hints: Vec<String>,
}

pub struct EncounterMetric {
    pub name: String,
    pub current: i32,
    pub starting: i32,
    pub direction: MetricDirection,
    pub threshold_high: Option<i32>,
    pub threshold_low: Option<i32>,
}

pub enum MetricDirection { Ascending, Descending, Bidirectional }
```

### EncounterPhase (reuse ChasePhase arc — it's universal)

Setup → Opening → Escalation → Climax → Resolution

Rename `ChasePhase` to `EncounterPhase`. The narrative arc is genre-agnostic.

### SecondaryStats (generalize RigStats)

```rust
pub struct SecondaryStats {
    pub stats: HashMap<String, StatValue>,
    pub damage_tier: Option<String>,
}
pub struct StatValue { pub current: i32, pub max: i32 }
```

RigStats becomes a convenience constructor: `SecondaryStats::rig(RigType)`.

### EncounterActor (generalize ChaseActor + ChaseRole)

```rust
pub struct EncounterActor {
    pub name: String,
    pub role: String,  // was ChaseRole enum — now string-keyed
}
```

### GameSnapshot Change

```rust
// Replace: pub chase: Option<ChaseState>
pub encounter: Option<StructuredEncounter>,
```

Serde backward compat: `#[serde(alias = "chase")]` with a custom deserializer that
converts old ChaseState format into StructuredEncounter with type "chase".

### Key Constraint: All Chase Tests Must Pass

chase.rs has ~15 tests. chase_depth.rs has ~25 tests. All must pass through a
compatibility layer. ChaseState can remain as a type alias or convenience constructors
over StructuredEncounter.

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/encounter.rs` | NEW — StructuredEncounter, EncounterMetric, etc. |
| `sidequest-game/src/encounter_depth.rs` | NEW — SecondaryStats, terrain, cinematography (moved from chase_depth) |
| `sidequest-game/src/chase.rs` | Becomes thin wrapper over StructuredEncounter |
| `sidequest-game/src/chase_depth.rs` | Core logic migrates to encounter_depth.rs |
| `sidequest-game/src/state.rs` | `chase` field → `encounter` field |
| `sidequest-game/src/lib.rs` | Export new modules |
| `sidequest-agents/src/patches.rs` | ChasePatch → EncounterPatch |
| `sidequest-server/src/shared_session.rs` | Update chase_state references |

## Scope Boundaries

**In scope:**
- StructuredEncounter struct with string-keyed types
- EncounterMetric with direction and thresholds
- SecondaryStats generalizing RigStats
- EncounterActor with string roles
- Backward-compatible deserialization
- All existing chase + chase_depth tests passing

**Out of scope:**
- YAML schema loading (16-3)
- Specific encounter type declarations (16-6, 16-7, 16-8)
- UI (16-9)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct compiles | StructuredEncounter with all fields serializes/deserializes |
| Chase compat | All existing chase.rs tests pass via compatibility layer |
| Chase depth compat | All existing chase_depth.rs tests pass |
| Metric types | Ascending, Descending, Bidirectional metrics all work |
| Secondary stats | RigStats expressible as SecondaryStats |
| Backward compat | Old save files with ChaseState deserialize into StructuredEncounter |
| GameSnapshot | `encounter` field replaces `chase` field |
