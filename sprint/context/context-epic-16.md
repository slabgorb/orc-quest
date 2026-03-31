# Epic 16: Genre Mechanics Engine — Confrontations & Resource Pools

## Overview

Build two generic subsystems that let genre packs declare mechanical rules the engine
enforces, closing the content-vs-engine gap across all 9 genre packs. Plus a targeted
MusicDirector extension for genre-specific moods.

**Pillar 1: Resource Pools** — Persistent named resources (Luck, Humanity, Heat) with
spend/gain/threshold events that feed into LoreStore as permanent narrator memory.

**Pillar 2: Structured Encounters** — Generalize ChaseState into a YAML-declarable
encounter engine for standoffs, negotiations, net combat, ship combat, and any future
structured encounter type.

**Pillar 3: Mood Extension** — String-keyed mood aliases so genre-specific moods
(standoff, saloon, convoy, cyberspace) play the right music instead of falling through.

**ADR:** 033-confrontation-engine-resource-pools.md

## Background

### The Gap Map (docs/genre-pack-status.md)

Every genre pack defines unique mechanics in rules.yaml. The engine provides generic
subsystems (combat, chase, tropes, factions). Genre-specific rules are LLM-interpreted
only — the narrator reads rules.yaml and applies them narratively. The risk: narrator
drift, forgotten mechanics, contradictory state.

| Genre | Mechanic | Current Enforcement |
|-------|----------|-------------------|
| spaghetti_western | Standoff (pre-combat NERVE ritual) | LLM only |
| spaghetti_western | Luck (spendable resource, 0-6) | LLM only |
| neon_dystopia | Humanity Tracker (degrades at 50/25/0) | LLM only |
| pulp_noir | Heat Tracker (0-5, affects factions) | LLM only |
| pulp_noir | Contacts system | LLM only |
| space_opera | Ship Block (shields, hull, engines) | LLM only |
| space_opera | Crew Bonds | LLM only |
| road_warrior | Rig HP, Fuel (outside chase context) | Partial — in chase_depth.rs during chases only |
| road_warrior | 10 faction music themes | Tracks exist, no routing logic |
| All genres | 15+ custom moods (standoff, saloon, etc.) | Fall through to nearest of 7 core moods |

### Code Review Findings (ADR-033)

**CombatState** (402 LOC) is actor-centric: turn order, per-actor effects, damage log.
The metric (HP) lives on Combatant trait implementations, not the state struct.

**ChaseState** (287 LOC) + **chase_depth.rs** (901 LOC) is scene-centric: one metric
(separation), beats as a sequence, optional secondary stats (RigStats). This is the
prototype for all structured encounters.

**Key finding:** CombatState and ChaseState should NOT merge — they model fundamentally
different encounter shapes. Instead, generalize ChaseState by replacing hardcoded enums
(ChaseType, RigType, ChaseRole) with string-keyed, YAML-declared types.

**MusicDirector surprise:** `mood_tracks` is already `HashMap<String, Vec<MoodTrack>>`
internally. The Mood enum only gates classification, not track selection. The mood fix
is ~50 lines: add genre mood_aliases + fallback chain.

### Key Reference Files

| File | LOC | Role |
|------|-----|------|
| `sidequest-game/src/combat.rs` | 402 | CombatState — stays as-is |
| `sidequest-game/src/chase.rs` | 287 | ChaseState — generalized into StructuredEncounter |
| `sidequest-game/src/chase_depth.rs` | 901 | RigStats, beats, terrain, cinematography — transferred to encounter system |
| `sidequest-game/src/music_director.rs` | 667 | MusicDirector — mood aliases added |
| `sidequest-game/src/state.rs` | ~600 | GameSnapshot — gets `resources` field |
| `sidequest-game/src/trope.rs` | 225 | TropeEngine — pattern reference for threshold events |
| `sidequest-game/src/lore.rs` | 2746 | LoreStore — receives threshold KnownFacts |
| `sidequest-agents/src/patches.rs` | 74 | Patch types — gets ResourcePatch |
| `sidequest-agents/src/patch_legality.rs` | 202 | Validation — enforces resource bounds |
| `sidequest-agents/src/prompt_framework/` | 1484 | Prompt assembly — resource state injection point |

## Technical Architecture

### Resource Pool System

**On GameSnapshot:**
```rust
// state.rs
pub resources: HashMap<String, ResourcePool>,
```

**ResourcePool struct:**
```rust
pub struct ResourcePool {
    pub name: String,           // "luck", "humanity", "heat"
    pub label: String,          // "Luck", "Humanity", "Heat"
    pub current: f64,
    pub min: f64,
    pub max: f64,
    pub voluntary: bool,        // player can spend (Luck=true, Humanity=false)
    pub decay_per_turn: f64,    // auto-change per turn (Heat decays at -0.1)
    pub thresholds: Vec<ResourceThreshold>,
    pub fired_thresholds: HashSet<String>,  // idempotent across save/load
}

pub struct ResourceThreshold {
    pub at: f64,
    pub event_id: String,
    pub narrator_hint: String,
    pub direction: ThresholdDirection,  // CrossingDown, CrossingUp, Either
}
```

**YAML declaration (rules.yaml):**
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
        narrator_hint: "Luck has run dry. Every consequence is earned."
        direction: crossing_down
```

**Patch type (patches.rs):**
```rust
pub struct ResourcePatch {
    pub deltas: Option<HashMap<String, f64>>,  // name → delta
}
```

**Threshold → KnownFact pipeline:**
1. `ResourcePool::apply_delta()` detects threshold crossing
2. Checks `fired_thresholds` set (idempotent)
3. Mints `KnownFact` with category "resource_event", event_id, narrator_hint
4. LoreStore indexes with high relevance score
5. Narrator prompt includes via existing budget-aware selection
6. Fact persists forever — narrator literally cannot forget

**Validation:**
- PatchLegality (existing, 202 LOC) validates resource deltas
- Reject if: resource doesn't exist, would go below min or above max
- Mode: warn-and-clamp initially, strict-reject later

**Loading:**
- Genre loader reads `resources` from rules.yaml at pack init
- Creates ResourcePool instances with starting values
- Adds to GameSnapshot on session creation

### Structured Encounter System

**Generalize ChaseState** by replacing hardcoded enums with string keys.

```rust
pub struct StructuredEncounter {
    pub encounter_type: String,     // "chase", "standoff", "negotiation"
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
    pub name: String,               // "separation", "tension", "leverage"
    pub current: i32,
    pub starting: i32,
    pub direction: MetricDirection,  // Ascending, Descending, Bidirectional
    pub threshold_high: Option<i32>,
    pub threshold_low: Option<i32>,
}
```

**EncounterPhase** reuses the existing ChasePhase arc (universal narrative shape):
Setup → Opening → Escalation → Climax → Resolution

**SecondaryStats** generalizes RigStats:
```rust
pub struct SecondaryStats {
    pub stats: HashMap<String, StatValue>,  // "hp", "fuel", "focus", "shields"
    pub damage_tier: Option<String>,        // computed from primary stat percentage
}
```

**YAML declaration (rules.yaml):**
```yaml
confrontations:
  - type: standoff
    label: "Standoff"
    category: pre_combat
    metric:
      name: tension
      direction: ascending
      starting: 0
      threshold_high: 10
    beats:
      - id: size_up
        label: "Size Up"
        metric_delta: 2
        stat_check: CUNNING
        reveals: opponent_detail
      - id: bluff
        label: "Bluff"
        metric_delta: 3
        stat_check: NERVE
        risk: "opponent may call it — immediate draw"
      - id: flinch
        label: "Flinch"
        metric_delta: -1
        consequence: "lose initiative if it escalates to combat"
      - id: draw
        label: "Draw"
        resolution: true
        stat_check: DRAW
        modifier: tension_bonus
    secondary_stats:
      - name: focus
        source_stat: NERVE
        spendable: true
    escalates_to: combat
    mood: standoff
    cinematography:
      camera_override: close_up_slow_motion
      sentence_range: [2, 4]
```

**Migration from ChaseState:**
- `chase_type` (enum) → `encounter_type` (string)
- `separation_distance` → `metric.current` with name "separation"
- `goal` → `metric.threshold_high`
- `rig: Option<RigStats>` → `secondary_stats`
- Existing ChasePhase, ChaseBeat, BeatDecision, TerrainModifiers transfer directly
- ChaseState remains as convenience constructor: `StructuredEncounter::chase(...)`

**On GameSnapshot:**
```rust
// Replaces: pub chase: Option<ChaseState>
pub encounter: Option<StructuredEncounter>,
```

**Backward compatibility:** Deserialize old saves with `chase` field into
`encounter` with type "chase". Serde alias handles this.

### Mood Extension (MusicDirector)

**YAML addition to audio.yaml:**
```yaml
mood_aliases:
  standoff: tension
  saloon: calm
  riding: exploration
  convoy: exploration
  betrayal: tension
  cyberspace: mystery
  club: exploration
  corporate: calm
  teahouse: calm
  spirit: mystery
  ceremony: calm
  void: sorrow
```

**Resolution chain in MusicDirector:**
1. If active StructuredEncounter has `mood_override` → use that
2. Classify mood from narration keywords (existing, already string-keyed)
3. Look up classified mood in `mood_tracks` HashMap
4. If not found → follow `mood_aliases` chain
5. If still not found → fall back to "exploration" (safe default)

**Genre mood_keywords addition:**
```yaml
mood_keywords:
  standoff:
    - standoff
    - duel
    - draw
    - face off
    - stare down
  saloon:
    - saloon
    - bar
    - tavern
    - drink
    - cards
```

### UI Components

**GenericResourceBar:**
- Props: `name`, `value`, `max`, `color`, `thresholds`, `genreTheme`
- Renders in character sheet footer
- Threshold crossings trigger pulse animation + toast
- Audio sting via existing AudioCue on threshold
- v1: simple colored bar with genre accent colors
- v2: genre-specific visualizations (revolver cylinder, circuit board, thermometer)

**EncounterOverlay:**
- Replaces/wraps existing CombatOverlay for non-combat encounters
- Shows: metric bar, available beats as action buttons, actor portraits
- Active StructuredEncounter's `encounter_type` determines visual treatment
- Standoff: letterbox framing, extreme close-up portraits
- Chase: existing chase visualization
- Falls back to generic metric + beats for undefined types

### WebSocket Protocol

**New message types:**
```rust
// Resource state update (server → client)
ResourceUpdate {
    resources: HashMap<String, ResourceState>,  // name → {current, max, label}
}

// Resource threshold event (server → client)
ResourceThresholdEvent {
    resource: String,
    event_id: String,
    narrator_hint: String,
}

// Encounter state update (server → client, replaces CHASE_UPDATE)
EncounterUpdate {
    encounter_type: String,
    metric: EncounterMetricState,
    beat: u32,
    phase: String,
    secondary_stats: Option<HashMap<String, f64>>,
    available_beats: Vec<BeatOption>,
}
```

## Story Dependency Graph

```
16-1 (prompt injection) ─── standalone quick win
16-14 (mood aliases) ────── standalone quick win

16-10 (ResourcePool) ────→ 16-11 (threshold→KnownFact) ──→ 16-12 (wire genres)
         │
         └──────────────→ 16-13 (UI ResourceBar)

16-2 (StructuredEncounter) → 16-4 (migrate combat*) ─┐
         │                   16-5 (migrate chase) ────┤
         │                                            └→ 16-6 (standoff)
         │                                               16-7 (social)
         │                                               16-8 (genre-specific)
         └──────────────→ 16-9 (UI EncounterOverlay)

16-16 (content audit) ──── after all other stories

* 16-4 is a no-op refactor — combat stays as CombatState, just verified compatible
```

## Acceptance Criteria Summary

| Story | Key ACs |
|-------|---------|
| 16-1 | Resource state appears in narrator prompt context. All 9 genres improved. |
| 16-2 | StructuredEncounter struct compiles. All existing chase tests pass via compatibility layer. |
| 16-3 | Genre loader parses `confrontations` from rules.yaml. Schema validation on load. |
| 16-4 | CombatState unchanged. Verified no interference with StructuredEncounter. |
| 16-5 | ChaseState expressed as StructuredEncounter. All chase_depth tests pass. |
| 16-6 | Standoff playable: beats resolve, tension builds, escalates to combat. Integration test. |
| 16-7 | Negotiation and interrogation encounter types declared and functional. |
| 16-8 | Net combat, ship combat, auction declared in respective genre packs. |
| 16-9 | EncounterOverlay renders any encounter type. Standoff gets letterbox treatment. |
| 16-10 | ResourcePool loads from YAML, tracks state, validates patches, persists. |
| 16-11 | Threshold crossing mints KnownFact. Fact appears in narrator prompt. Idempotent on reload. |
| 16-12 | Luck, Humanity, Heat functional as ResourcePool instances. |
| 16-13 | ResourceBar renders in character sheet. Threshold animation works. |
| 16-14 | Custom moods resolve via alias chain. Genre-specific tracks play. |
| 16-15 | Faction themes trigger by location/NPC context. Road warrior 10 factions tested. |
| 16-16 | All 9 genre packs updated. genre-pack-status.md reflects new completeness. |

## Planning Documents

| Document | Path |
|----------|------|
| ADR-033 | docs/adr/033-confrontation-engine-resource-pools.md |
| Gap Analysis | docs/genre-pack-status.md |
| Chase ADR | docs/adr/017-chase-types.md |
| Patch ADR | docs/adr/011-structured-patches.md |
| Epic YAML | sprint/epic-16.yaml |
