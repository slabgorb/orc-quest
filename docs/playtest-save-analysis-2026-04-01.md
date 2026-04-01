# Playtest Save Analysis — 2026-04-01

Analysis of 35 active save.db files in `~/.sidequest/saves/` and 3 archived
lore.db files in `~/ArchivedProjects/sq-2/.sidequest/saves/`.

## Save File Inventory

**Active saves:** 35 character saves across 7 genres, dated Mar 27 – Mar 31.
**Archived (sq-2):** 3 lore.db files (elemental_harmony, low_fantasy, mutant_wasteland), 1.6–1.7MB each, dated Mar 24.
**JSON autosave:** 1 file from Mar 21.

### By Genre

| Genre | World | Characters | Largest Save | Last Played |
|-------|-------|------------|-------------|-------------|
| elemental_harmony | shattered_accord | 6 (aberu_kisu, windslov, splei, poo, zang, zhang) | 108K (splei) | Mar 29 |
| elemental_harmony | shattered_accord_backup | 2 (aberu_kisu, makka) | 28K | Mar 29 |
| elemental_harmony | burning_peace | 2 (aberu_kisu, kasigi_omi) | 44K | Mar 30 |
| mutant_wasteland | flickering_reach | 10 (playtest_runner, klankov, laverne, shirley, winchesterv18_2, _sweeney__todd, skate_kipper, verion, jeeves3_7, morty_richter_) | 180K (playtest_runner) | Mar 31 |
| road_warrior | the_circuit | 3 (roger_dodger, _sweeney__todd, bloody_al) | 108K (roger_dodger) | Mar 31 |
| space_opera | aureate_span | 2 (brom_the_bald, crom_the_bald) | 76K | Mar 30 |
| space_opera | coyote_reach | 5 (zanzibar_jones, captain_vex, chimi_saera, zanzi_jo, zara_kade) | 44K | Mar 29 |
| neon_dystopia | franchise_nations | 2 (kira_sato, zanzibar_jones) | 4K | Mar 29 |
| spaghetti_western | dust_and_lead | 1 (martin_martos) | 20K | Mar 31 |
| low_fantasy | pinwheel_coast | 1 (zingus) | 4K | Mar 30 |
| victoria | blackthorn_moor | 1 (_sweeney__todd) | 4K | Mar 30 |

## Finding 1: Quest-Giver Redundancy

Almost every genre opens with the same pattern: **arrive at settlement, woman at
a fixed location hands you a fetch/escort quest.**

| Genre | Quest-Giver | Type | Quest |
|-------|-------------|------|-------|
| mutant_wasteland (playtest_runner) | Toggler Copperjaw — woman at salvage stall | Fetch & carry | Sporecap Garden run |
| mutant_wasteland (skate_kipper) | Toggler Copperjaw — same NPC | Fetch/explore | Ruin Fever — find fuel cells |
| mutant_wasteland (laverne) | Toggle — woman at tire barricade | Repair | Fix water condenser |
| spaghetti_western | Unnamed cantina woman | Fetch + escort | Delgado cattle + supply run to Sierra Perdida |
| road_warrior | Job board + Stor Erik | Fetch | Fuel run |
| neon_dystopia | Anonymous voice on comm | Data job | Encrypted mesh investigation |
| space_opera (aureate_span) | **The Imperatrix — non-binary, mysterious** | **Arena challenge** | **Corona Arena to reach Castellan Dravasti** |
| space_opera (coyote_reach) | Wiry woman with silver hair, stall 14 | Find person | Looking for Zanzi |

### What Works

The **Aureate Span opening** is the outlier and it's excellent:
- Quest-giver (The Imperatrix) has agency, mystery, and presence
- The quest is an arena challenge, not a fetch errand
- The NPC doesn't explain everything — they withhold and redirect
- The player earns progression through performance, not delivery

### What Doesn't Work

Every other opening follows the same template:
1. Arrive at a settlement (dome, cantina, scrapyard, docking ring)
2. Meet a woman at a fixed location (stall, bar, barricade)
3. She gives you a fetch/carry/escort job
4. You walk somewhere to do the job

The **gender pattern** is striking — nearly every quest-giver is female. This
appears to be a Claude default when generating "helpful NPC who gives the player
a task." The conlang name generator exists specifically to give each genre its own
phonemic identity, but these names (Toggler Copperjaw, Toggle, unnamed cantina
woman) are all Claude improvisation, not conlang output.

### Root Causes

- **Conlang generator not wired into NPC name generation** — Claude is freestyling names
- **No quest archetype variety** — the narrator prompt likely doesn't constrain opening quest types
- **No genre-specific opening hooks** — every genre defaults to "settlement + helpful NPC + errand"

## Finding 2: Pacing — 100+ Turns, Going Nowhere

| Save | Turns | Campaign Maturity | Beats Fired | Quests Completed | Regions Discovered |
|------|-------|-------------------|-------------|-----------------|-------------------|
| playtest_runner | 109 | Fresh | 0 | 0 | 1 |
| roger_dodger | 25 | Mid | 12 | 0 | 0 |
| crom_the_bald | 24 | Fresh | 0 | 0 | 1 |
| martin_martos | 19 | Fresh | 0 | 0 | 1 |
| skate_kipper | 34 | Fresh | 0 | 0 | 2 |
| splei | 37 | Fresh | 0 | 0 | 3 |
| laverne | 16 | Fresh | 0 | 0 | 0 |

### Key Problems

- **109 turns and still "Fresh"** — campaign_maturity is not advancing
- **Beats fired: 0** on 6 of 7 saves — the trope/beat engine is not triggering
- **Zero quests completed** across all saves — quests are accepted but never resolved
- **Regions barely discovered** — players aren't moving through the world
- **road_warrior is the only save showing beats (12)** and maturity advancement (Mid), suggesting the system works but isn't consistently wired

### What This Means

The narrator is generating beautiful atmospheric prose but the mechanical systems
underneath — quest resolution, region discovery, campaign maturity, beat tracking
— are either not wired or not firing. The game *reads* well but doesn't *play*
well. Players are stuck in an endless loop of atmospheric vignettes without
meaningful progression.

## Finding 3: NPC Registry Inconsistency

| Save | Active NPCs | Registered NPCs | Named NPCs in Narrative |
|------|-------------|-----------------|------------------------|
| playtest_runner | 0 | 0 | Toggler Copperjaw, Yulka Thornwall, others |
| roger_dodger | 0 | 0 | Stor Erik, others |
| crom_the_bald | 0 | 0 | The Imperatrix, Castellan Dravasti |
| martin_martos | 0 | 0 | Cantina woman, Padre Esteban |
| skate_kipper | 0 | 0 | Toggler Copperjaw |
| splei | 0 | **12** | Multiple ashram NPCs |
| laverne | 0 | **16** | Toggle, others |

The registry works for splei (12) and laverne (16) but is empty for everything
else, despite those saves clearly containing named NPC interactions. This is
likely a timing or code path issue — the registration system exists but doesn't
fire consistently.

## Finding 4: Lore/RAG Database Not Active

- **sq-2 (archived):** Has 3 lore.db files, 1.6–1.7MB each — real vector data
- **Rust rewrite:** `lore_established: []` across all saves, zero lore.db files
- The RAG retrieval system that informed narration in sq-2 is not yet wired in the Rust port

**Story 18-4 (LoreStore browser tab)** is currently in progress and directly
addresses the observability side of this — building the OTEL tab that shows
whether lore retrieval is actually happening.

## Recommendations

These are game design and wiring issues, not cosmetic:

1. **Wire conlang generator into NPC name creation** — stop Claude from freestyling names
2. **Diversify opening quest archetypes per genre** — arena, mystery, chase, defense, not just fetch
3. **Investigate beat engine wiring** — why 0 beats on 6/7 saves
4. **Investigate campaign_maturity advancement** — 109 turns should not be "Fresh"
5. **Debug NPC registry inconsistency** — works for some saves, not others
6. **Complete lore/RAG wiring** — the data existed in sq-2, needs porting
7. **Complete 18-4** — LoreStore OTEL tab is the observability layer for finding these issues in real-time
