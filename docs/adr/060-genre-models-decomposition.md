# ADR-060: Genre Models Decomposition — Split models.rs by Domain

**Status:** Proposed
**Date:** 2026-04-04
**Deciders:** Keith
**Relates to:** ADR-003 (Genre Pack Architecture), ADR-007 (Unified Character Model)

## Context

`sidequest-genre/src/models.rs` has grown to 2,651 lines containing 102 struct/enum
definitions and 18 impl blocks. Every genre pack feature that adds a new model type
appends to this single file. The file now spans at least 10 distinct domains:

- **Character creation** — `CharCreationScene`, `CharCreationChoice`, `MechanicalEffects`
- **OCEAN personality** — `OceanProfile`, `OceanDimension`, `OceanShift`, `OceanShiftLog`
- **Narrative/drama** — `DramaThresholds`, `GenreTheme`, `Dinkus`, `SessionOpener`, `Prompts`, `OpeningHook`
- **Lore** — `Lore`, `WorldLore`, `Faction`, `NpcArchetype`
- **Progression** — `PassiveProgression`, `ProgressionConfig`, `Affinity`, `AffinityTier`, `PowerTier`
- **Confrontation/combat** — `ConfrontationDef`, `BeatDef`, `MetricDef`, `SecondaryStatDef`
- **Audio** — `AudioConfig`, `AudioAiGeneration`, `MoodTrack`, `AudioTheme`, `AudioVariation`
- **World/cartography** — `WorldConfig`, `WorldGraph`, `WorldGraphNode`, `CartographyConfig`, `Region`, `Route`
- **Scenario** — `ScenarioPack`, `PlayerRole`, `ClueGraph`, `AssignmentMatrix`, `Suspect`
- **Inventory/economy** — `InventoryConfig`, `CurrencyConfig`, `CatalogItem`, `WealthTier`
- **Voice/culture** — `Culture`, `CultureSlot`, `CorpusRef`, `VoicePresets`, `VoiceConfig`, `CreatureVoicePreset`

This makes the file a merge-conflict magnet and violates Rust's locality principle —
types are separated from related behavior, and unrelated types share a namespace.

## Decision

**Split `models.rs` into a `models/` directory with domain-grouped submodules.**

### Module Structure

```
sidequest-genre/src/models/
├── mod.rs              # Re-exports all public types (preserves API)
├── pack.rs             # GenrePack, PackMeta, Inspiration, ResourceDeclaration, RulesConfig
├── world.rs            # World, WorldConfig, WorldGraph, WorldGraphNode, GraphEdge,
│                       #   SubGraph, CartographyConfig, Region, Route, Legend,
│                       #   TerrainScar, FactionGrudge, RoomDef, RoomExit, Terrain,
│                       #   NavigationMode
├── character.rs        # CharCreationScene, CharCreationChoice, MechanicalEffects,
│                       #   VisualStyle, LevelBonuses
├── ocean.rs            # OceanProfile, OceanDimension, OceanShift, OceanShiftLog,
│                       #   DramaThresholds
├── narrative.rs        # GenreTheme, Dinkus, SessionOpener, Prompts, OpeningHook,
│                       #   BeatVocabulary, BeatObstacle, Achievement
├── lore.rs             # Lore, WorldLore, Faction, NpcArchetype
├── progression.rs      # PassiveProgression, ProgressionConfig, Affinity,
│                       #   AffinityUnlocks, AffinityTier, PowerTier, Ability,
│                       #   ItemEvolution
├── confrontation.rs    # ConfrontationDef, BeatDef, MetricDef, SecondaryStatDef,
│                       #   AxesConfig, AxisDefinition, AxisPreset
├── audio.rs            # AudioConfig, AudioAiGeneration, MoodTrack, AudioTheme,
│                       #   AudioVariation, TrackVariation, AudioEffect, MixerConfig,
│                       #   CreatureVoicePreset
├── scenario.rs         # ScenarioPack, PlayerRole, RoleHook, Pacing, Act,
│                       #   PressureEvent, EscalationBeat, AssignmentMatrix, Suspect,
│                       #   ClueGraph, ClueNode, AtmosphereMatrix, ScenarioNpc,
│                       #   InitialBeliefs, Suspicion, WhenGuilty, WhenInnocent
├── inventory.rs        # InventoryConfig, CurrencyConfig, CatalogItem, WealthTier,
│                       #   InventoryPhilosophy
└── culture.rs          # Culture, CultureSlot, CorpusRef, VoicePresets, VoiceConfig
```

### Migration Strategy

1. `mod.rs` re-exports everything via `pub use submodule::*` — downstream crates see
   no API change. Zero-breakage migration.
2. Move types one domain at a time, running `cargo check` after each move.
3. Move `impl` blocks with their types — keep behavior next to data.
4. Raw/validated pairs (e.g., `RawBeatDef` + `BeatDef` + `TryFrom`) stay together.

## Alternatives Considered

### Keep single file, add section comments
Already the status quo (the file has section separators). Doesn't solve merge conflicts
or the 2,651-line cognitive load. Rejected.

### Split into separate crates
Over-engineering. These types all serve genre pack deserialization and share serde
derives. Crate boundaries would add inter-crate dependency overhead with no visibility
benefit. Rejected.

## Consequences

- **Positive:** Each domain module is 150-300 lines. Merge conflicts between unrelated
  features drop to near zero. Types live next to their impl blocks.
- **Positive:** New genre features have a clear home — add a trope type? `narrative.rs`.
  Add a room variant? `world.rs`.
- **Negative:** One-time migration churn. Mitigated by the re-export strategy.
- **Risk:** Over-splitting. If a domain module ends up under 50 lines, fold it back into
  its nearest neighbor.
