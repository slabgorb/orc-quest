# Genre Pack Status Guide

> Last updated: 2026-03-31 | Source: `sidequest-content` develop branch

## Pack Overview

| Genre Pack | Worlds | Genre YAMLs | Music | Fonts | Corpus | Images | Tier |
|-----------|--------|-------------|-------|-------|--------|--------|------|
| elemental_harmony | 2 | 14/16 | 182 | 2 | 9 | 38 | 1 |
| low_fantasy | 2 | 16/16 | 137 | 2 | 6 | 23 | 1/2 |
| mutant_wasteland | 1 | 13/16 | 150 | 1 | 7 | 3 | 2 |
| neon_dystopia | 1 | 14/16 | 48 | 1 | 7 | 8 | 1/2 |
| pulp_noir | 1 | 14/16 | 42 | 2 | 11 | 12 | 1 |
| road_warrior | 1 | 14/16 | 147 | 0 | 12 | 16 | 1 |
| space_opera | 2 | 14/16 | 60 | 0 | 8 | 0 | 2 |
| spaghetti_western | 1 | 16/16 | 18+ | 1 | 5 | 0 | 2 |
| victoria | 1 | 16/16 | 33 (PD) | 1 | 10 | 13 | 1 |

### Tiers

- **Tier 1** — Genre + world + music + images all present. Playable.
- **Tier 2** — Genre complete, world needs work or assets missing.
- **Tier 3** — Significant gaps in genre or world files.

## Missing Genre-Level Files

Standard set: pack, rules, axes, lore, cultures, archetypes, char_creation,
progression, inventory, tropes, prompts, cartography, voice_presets, theme,
visual_style, audio (16 files).

| Pack | Missing |
|------|---------|
| elemental_harmony | inventory, cartography, voice_presets |
| mutant_wasteland | inventory, cartography, voice_presets |
| neon_dystopia | cartography, voice_presets |
| pulp_noir | cartography, voice_presets |
| road_warrior | cartography, voice_presets |
| space_opera | cartography, voice_presets |
| low_fantasy | complete |
| spaghetti_western | complete |
| victoria | complete |

## World-Level Completeness

Required: world.yaml, lore.yaml. Optional: history, cartography, cultures,
archetypes, tropes, visual_style, legends.

| World | history | carto | cultures | archetypes | tropes | visual_style | legends |
|-------|---------|-------|----------|-----------|--------|-------------|---------|
| elemental/burning_peace | + | + | + | + | + | + | + |
| elemental/shattered_accord | + | + | + | — | + | — | + |
| low_fantasy/pinwheel_coast | — | + | + | — | — | — | + |
| low_fantasy/shattered_reach | + | + | + | — | — | — | + |
| mutant_wasteland/flickering_reach | — | + | + | — | — | — | + |
| neon_dystopia/franchise_nations | + | + | + | + | + | + | + |
| pulp_noir/annees_folles | + | + | + | + | + | + | + |
| road_warrior/the_circuit | + | + | + | + | + | + | + |
| space_opera/aureate_span | + | + | + | — | — | — | + |
| space_opera/coyote_reach | + | + | + | — | — | — | + |
| spaghetti_western/dust_and_lead | + | + | + | — | — | — | + |
| victoria/blackthorn_moor | + | + | + | + | + | + | + |

**Fully complete worlds (all optional files):**
burning_peace, franchise_nations, annees_folles, the_circuit, blackthorn_moor

## Missing Assets

| Issue | Packs Affected |
|-------|---------------|
| No .woff2 font | road_warrior, space_opera |
| No POI/scene images | spaghetti_western, space_opera |
| Low music count (<60) | neon_dystopia (48), pulp_noir (42), spaghetti_western (18+) |

## Unique Genre Mechanics

Each genre defines custom mechanics in rules.yaml. The engine provides generic
subsystems (combat, chase, tropes, factions); genre-specific rules are
LLM-interpreted at narration time unless noted.

| Genre | Custom Stats | Unique Mechanics | Engine Support |
|-------|-------------|-----------------|----------------|
| elemental_harmony | Harmony, Spirit + 4 | High magic, martial arts | LLM-interpreted |
| low_fantasy | Standard D&D 6 | Banned spells, gritty realism, lingering injuries | LLM-interpreted |
| mutant_wasteland | Brawn, Reflexes, Toughness, Wits, Instinct, Presence | Mutation system, no magic | LLM-interpreted |
| neon_dystopia | Body, Reflex, Tech, Net, Cool, Edge | Humanity Tracker, Street Cred, Net Combat | LLM-interpreted |
| pulp_noir | Brawn, Finesse, Grit, Savvy, Nerve, Charm | Contacts, Heat Tracker (0-5), Occult Exposure | LLM-interpreted |
| road_warrior | Grip, Iron, Nerve, Scrap, Road Sense, Swagger | **Rig HP/damage tiers, Fuel, Chase beats, Dismounted** | **Rig HP + Fuel: ENGINE IMPL** (chase_depth.rs) |
| space_opera | Physique, Reflex, Intellect, Cunning, Resolve, Influence | Ship Block, Ship Combat, Crew Bonds, Found Family | LLM-interpreted |
| spaghetti_western | GRIT, DRAW, NERVE, CUNNING, PRESENCE, LUCK | **Standoff system**, Luck resource, Bounty board, 5-faction rep | LLM-interpreted |
| victoria | **Angst, Pride, Humour, Nerve, Cunning, Passion** | Emotional ability scores, class-stratified society | LLM-interpreted |

## Content vs Engine Gap Map

Features defined in content YAML that have no engine-level enforcement.
These work via LLM prompt interpretation — the narrator reads rules.yaml
and applies them narratively. Risk: LLM may forget or drift mid-session.

### Gaps where engine COULD enforce but doesn't

| Feature | Content Pack | Why It Matters |
|---------|-------------|---------------|
| Standoff state machine | spaghetti_western | Pre-combat NERVE check ritual with no mechanical guardrail |
| Luck resource pool | spaghetti_western | Spendable resource with no engine tracking |
| Humanity Tracker | neon_dystopia | Degrades at thresholds (50/25/0) — engine could enforce |
| Heat Tracker | pulp_noir | 0-5 scale affecting faction behavior — engine could enforce |
| Ship Block (separate HP pool) | space_opera | Like Rig HP but for ships — pattern already exists in chase_depth.rs |
| Faction music routing | road_warrior | 10 faction themes exist as .ogg files, no trigger logic |

### Gaps where engine has data but UI doesn't show

| Feature | Engine Module | What UI Needs |
|---------|-------------|--------------|
| Rig HP / damage tiers | chase_depth.rs (RigStats) | Rig health bar + damage tier indicator |
| Fuel gauge | chase_depth.rs (fuel, fuel_warning) | Fuel resource bar with low-fuel warning |
| Chase state | chase.rs (ChaseState) | Dedicated chase UI (separation, beats, terrain) |

### MusicDirector Mood Coverage

The engine's `Mood` enum has 7 variants. Genre packs define 15+ custom moods.

| Engine Mood | Maps To |
|------------|---------|
| Combat | combat |
| Exploration | exploration |
| Tension | tension |
| Triumph | triumph |
| Sorrow | sorrow |
| Mystery | mystery |
| Calm | rest, calm |

**Custom moods that fall through to nearest match:**
standoff, saloon, betrayal, riding, convoy, speakeasy, intrigue, chase,
cyberspace, club, corporate, teahouse, spirit, ceremony, settlement, ruins,
tavern, galley, drift, docking, void

## Music Strategy by Genre

| Genre | Strategy | Track Count |
|-------|---------|-------------|
| elemental_harmony | ACE-Step generated, 2 sets, all 6 variations | 182 |
| mutant_wasteland | ACE-Step generated, all 6 variations | 150 |
| road_warrior | ACE-Step generated + 10 faction themes | 147 |
| low_fantasy | ACE-Step generated, all 6 variations | 137 |
| space_opera | ACE-Step generated | 60 |
| neon_dystopia | ACE-Step generated (needs more) | 48 |
| pulp_noir | ACE-Step generated (needs more) | 42 |
| **victoria** | **Curated public domain classical (Chopin, Strauss)** | 33 |
| spaghetti_western | ACE-Step generating (target: 54) | 18+ |

## Per-Pack Notes

### elemental_harmony
- Most musically rich (182 tracks). Gold standard for variation coverage.
- Two worlds, both well-developed. burning_peace is fully complete.
- Missing genre-level inventory, cartography, voice_presets.
- 9 corpus files covering Asian linguistic traditions.

### low_fantasy
- Genre level complete. The "default" genre — closest to traditional D&D.
- pinwheel_coast is underdeveloped (no history, no archetypes/tropes).
- shattered_reach is better but still missing world archetypes/tropes.

### mutant_wasteland
- flickering_reach (the spoilable world) needs history and world archetypes.
- Only 3 images — needs POI generation.
- Missing genre-level inventory, cartography, voice_presets.

### neon_dystopia
- franchise_nations is fully complete at world level.
- Only 48 music tracks — needs a second generation pass with variations.
- Humanity Tracker and Street Cred are the most ambitious LLM-interpreted
  mechanics; candidates for engine enforcement.

### pulp_noir
- annees_folles is fully complete at world level.
- Only 42 music tracks. Uses some public domain 1920s jazz.
- 11 corpus files — most linguistically diverse (Arabic through Swedish).
- Contacts and Heat systems are good candidates for engine tracking.

### road_warrior
- the_circuit is fully complete at world level.
- **Most engine-supported genre-specific mechanics** — Rig HP, fuel, damage
  tiers, and chase beats are all implemented in chase_depth.rs.
- 10 faction music themes (Bosozoku through Dekotora) exist as tracks but
  lack engine routing logic to play them contextually.
- **Missing font.** Needs a .woff2.

### space_opera
- Two worlds (aureate_span, coyote_reach), both missing archetypes/tropes.
- Ship Block mechanic mirrors road_warrior's Rig HP pattern — could reuse
  the same chase_depth.rs infrastructure.
- **Missing font.** No images in either world.
- 60 tracks — adequate but could use variation pass.

### spaghetti_western
- **NEW** — genre level complete (16/16 files).
- dust_and_lead world has core files + full 4-chapter history with 15 POIs.
- Music generation in progress (target: 54 tracks, 9 moods x 6 variations).
- Standoff system is the signature mechanic — no engine enforcement yet.
- Alfa Slab One font installed.
- Needs POI image generation after music completes.

### victoria
- Was invisible on main branch — fully developed on develop (10 commits).
- **Unique architecture:** emotional ability scores (Angst, Pride, Passion),
  class-stratified society (Gentry, Trade, Servant, Clergy, Bohemian, Colonial).
- **Public domain classical music** — real Chopin and Strauss recordings
  mapped to game moods. No ACE-Step generation needed.
- blackthorn_moor is fully complete with 8 POI landscapes + 5 character scenes.
- Playfair Display font. 10 class-stratified naming corpus files.
- Extra YAML files unique to victoria: achievements, beat_vocabulary, power_tiers.
