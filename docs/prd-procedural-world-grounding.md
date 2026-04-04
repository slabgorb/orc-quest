# PRD: Procedural World-Grounding Systems

> **Status:** Draft
> **Author:** PM Agent (Prince Humperdinck), from GM research (Count Rugen)
> **Date:** 2026-04-04
> **Research:** `docs/research/procedural-tools-survey.md`, `docs/research/procedural-generation-lineage.md`
> **Builds On:** Monster Manual pattern (ADR-059), namegen/encountergen/loadoutgen tool binaries

## Problem

The SideQuest narrator is creative but repetitive. Left unseeded, LLMs exhibit
mode collapse on narrative detail — every tavern gets a grizzled barkeep, every
forest gets ancient twisted oaks, every guard is suspicious but helpful. This is
the same problem human DMs solve with random tables, and the same problem Keith
has been solving with procedural generators for 30+ years (populinator, townomatic,
gotown, fantasy-language-maker).

Today's genre packs are **narratively rich but simulation-thin.** They excel at
tone, voice, and escalation mechanics. They lack the procedural grounding that
tells the narrator "what's happening in this town right now" — population
constraints, weather conditions, NPC locations, economic state, time of day.

Without this grounding:
- Settlements have inconsistent scale (village with 15 shops)
- Weather contradicts itself between turns
- NPCs exist everywhere and nowhere — no sense of routine or schedule
- Prices and availability are improvised without economic logic
- The narrator invents the same details across sessions (mode collapse)
- OTEL can't verify what was proposed vs what was narrated

## Goal

A set of **procedural world-grounding systems** that inject structured, varied,
mechanically-consistent context into the narrator's prompt zones. The narrator
shifts from **invention** (where it repeats itself) to **curation** (where it
excels) — selecting from a rich catalog of generated specifics rather than
improvising from its training distribution.

These systems follow the established **narrator-gaslighting pattern:**

```
Procedural Generator → speculative state
    ↓
Prompt Zone Assembly → injected into narrator context
    ↓
Narrator → weaves selectively from state
    ↓
State Reconciliation → what narrator used becomes canon
    ↓
OTEL → verifies proposed vs used
```

## Existing Pattern: Monster Manual (ADR-059)

The Monster Manual already implements this PRD's core architecture for NPCs and
encounters. New grounding systems MUST follow the same pattern — not reinvent it.

**What exists today:**

| Component | Implementation | Location |
|-----------|---------------|----------|
| **Pre-generation binaries** | `sidequest-namegen`, `sidequest-encountergen`, `sidequest-loadoutgen` | Rust tool crates |
| **Persistent pools** | `MonsterManual` struct → `~/.sidequest/manuals/{genre}_{world}.json` | `monster_manual.rs` |
| **Lifecycle tracking** | Available → Active → Dormant transitions | `monster_manual.rs` |
| **Prompt injection** | `format_nearby_npcs()`, `format_area_creatures()` | `dispatch/mod.rs:385-405` |
| **Markov name generation** | Character-level Markov from culture corpus (ported from fantasy-language-maker → lango → Rust) | `markov.rs` |
| **OCEAN personality** | Big Five with random jitter per archetype | `sidequest-genre` models |
| **Trope connections** | Tag-based automated linking in all gen binaries | namegen, encountergen |
| **Post-narration validation** | NPC names extracted and validated against Manual | `npc_context.rs` |
| **Compound key dedup** | `(name, culture, world)` prevents duplicates | `monster_manual.rs` |
| **World materialization** | Maturity-driven history chapter filtering | `world_materialization.rs` |

**The narrator prompt template** (`docs/prompt-reworked.md`) already has injection
points for `<game-state>`, `<world-lore>`, `<players>`, and `<tone>`. New grounding
systems add new sections or extend existing ones using the same attention-zone
architecture (Primacy → Early → Valley → Late → Recency).

**Key implication:** The "Rust code" effort for each system is smaller than it
appears. The pattern for "read YAML config → generate structured data → persist →
inject into prompt zone" is established. New systems follow the template.

## Non-Goals

- Visual map generation (no tile renderers, no image output)
- Replacing the narrator's creative authority (generators propose, narrator disposes)
- Simulation fidelity (tabletop granularity, not Dwarf Fortress)
- Procedural *narrative* generation (the narrator writes prose, not the generators)
- New UI elements (this feeds the narrator's context, not the player's screen)

## Design Principles

### 1. Mad Libs, Not Manuscripts
Generators produce structured fill-in-the-blank state (names, numbers, tags,
short descriptions). The narrator turns this into prose. Never generate prose
that the narrator has to reconcile with its own style.

### 2. Genre-Native, Not Generic
Every generator has genre-specific rules. `low_fantasy` weather is medieval
seasonal. `road_warrior` weather is dust storms and radiation. `neon_dystopia`
weather is smog indices and acid rain. No one-size-fits-all fantasy defaults.

### 3. Baked + Tick
Some state is authored once at world creation (demographics, calendar, economy
baseline). Some state is generated per scene/turn (weather, NPC schedules, price
fluctuations). The architecture supports both, and some systems are hybrid (baked
baseline + tick-driven variation).

### 4. Trope-Connected
Generated state should connect to active tropes whenever possible. Tavern rumors
reference active story threads. Economic disruptions trace to trope escalations.
Weather events can trigger or accelerate tropes. This prevents "disconnected
flavor" — everything feeds the narrative engine.

### 5. OTEL-Observable
Every generator emits spans for what it proposed. The narrator emits spans for
what it used. The delta between proposed and used is visible in the GM dashboard.
This is how we catch mode collapse — if the narrator ignores 90% of weather
proposals and always says "a clear day," OTEL reveals it.

---

## Systems

### Tier 1 — High Priority (prevents narrator improvisation)

#### 1.1 Weather System

**Classification:** Procedural on tick
**Effort:** Small (YAML rules + Rust generator + prompt zone injection)
**SOUL Alignment:** Living World (#2), Genre Truth (#3)

**What it does:** Generates weather state per scene based on genre climate rules,
season, and location. Injected into narrator context. Weather persists across
turns until the generator advances it.

**Content deliverable (per genre):** `weather.yaml` at genre pack level

```yaml
climate_zones:
  temperate:
    seasons:
      spring:
        temp_range: [5, 18]
        precipitation_chance: 0.4
        conditions: ["clear", "overcast", "rain", "fog", "storm"]
        weights: [30, 30, 25, 10, 5]
    special_events:
      - name: "harvest_gale"
        season: "autumn"
        chance: 0.05
        duration_days: [1, 3]
        effects: ["travel_penalty", "visibility_poor"]
```

**Runtime output (injected into narrator):**
```yaml
current_weather:
  condition: "heavy_rain"
  temp: 8
  visibility: "poor"
  wind: "strong"
  narrative_hints: ["puddles forming", "torch guttering", "reduced visibility"]
```

**Genre examples:**
| Genre | Climate Identity |
|-------|-----------------|
| `low_fantasy` | Medieval seasonal — frost, harvest storms, spring thaw |
| `road_warrior` | Hostile — dust storms, radiation weather, acid rain, heat death |
| `neon_dystopia` | Urban pollution — smog index, acid rain, atmospheric processor status |
| `space_opera` | Per-planet — void has no weather, stations have climate control failures |
| `mutant_wasteland` | Fallout weather — mutagen storms, glowing fog, ash rain |
| `elemental_harmony` | Elemental cycles — fire season, water tides, earth tremors as "weather" |

**Acceptance criteria:**
- [ ] `weather.yaml` schema defined and validated
- [ ] Climate rules authored for all 7 active genres
- [ ] Rust generator produces weather state from rules + RNG seed
- [ ] Weather state injected into narrator prompt zone
- [ ] Weather persists across turns (no contradictions)
- [ ] OTEL span: `weather.generate` with proposed conditions
- [ ] Special events can trigger/accelerate tropes

---

#### 1.2 Demographics

**Classification:** Baked in (world authoring)
**Effort:** Small (YAML content per world)
**SOUL Alignment:** Living World (#2), Diamonds and Coal (#8)

**What it does:** Defines settlement population, profession distribution, and
service availability. Prevents absurd settlements. Gives the narrator concrete
numbers to reference ("the town's twelve guards" not "the guards").

**Content deliverable (per world):** `demographics.yaml` at world level

```yaml
settlements:
  - name: "Grimholt"
    type: "small_town"
    population: 1200
    profile:
      noble_houses: 1
      guard_force: 12
      clergy: 3
      taverns: 2
      shops:
        blacksmith: 1
        general: 2
        apothecary: 1
      guilds: ["merchant", "mason"]
    wealth: "modest"
```

**Genre models:**
| Genre | Demographics Shape |
|-------|-------------------|
| `low_fantasy` | Medieval (S. John Ross model) — agriculture-based, feudal hierarchy |
| `neon_dystopia` | Corporate arcology — floors/sectors, employee tiers, security levels |
| `space_opera` | Station/colony — crew complement, department heads, civilian ratio |
| `road_warrior` | Scarcity — caravan headcount, settlement defensibility, resource per capita |
| `pulp_noir` | Urban wards — precinct beat cops, speakeasies per block, syndicate territory |

**Acceptance criteria:**
- [ ] `demographics.yaml` schema defined
- [ ] Demographics authored for all existing worlds (14 worlds across 7 genres)
- [ ] Settlement data injected into location context prompt zone
- [ ] Narrator references specific numbers, not vague plurals
- [ ] OTEL: demographic data present in `render_pipeline` spans

---

#### 1.3 NPC Schedules

**Classification:** Procedural on tick
**Effort:** Medium (archetype-based routine generation + time-of-day tracking)
**SOUL Alignment:** Living World (#2), Diamonds and Coal (#8)

**What it does:** Places named NPCs at specific locations based on time of day,
day of week, and role. The narrator knows where NPCs are — they don't appear and
disappear on demand.

**Content deliverable (per genre):** Schedule templates in `archetypes.yaml`

```yaml
# Added to existing archetype definitions
schedule_template:
  blacksmith:
    dawn: { location: "forge", activity: "stoking fire" }
    midday: { location: "forge", activity: "working" }
    dusk: { location: "tavern", activity: "drinking" }
    night: { location: "home", activity: "sleeping", available: false }
  merchant:
    dawn: { location: "warehouse", activity: "inventory" }
    midday: { location: "market", activity: "selling" }
    dusk: { location: "home", activity: "counting coin" }
    night: { location: "home", activity: "sleeping", available: false }
```

**Runtime output (injected into narrator):**
```yaml
npcs_present:
  - name: "Marta Voss"
    location: "The Broken Cask"
    activity: "serving patrons"
    disposition: "busy but approachable"
  - name: "Tomas the Smith"
    location: "The Broken Cask"
    activity: "drinking alone"
    disposition: "tired, talkative after ale"
npcs_absent:
  - name: "Lord Ashford"
    reason: "retired to quarters — audiences resume at midday"
```

**Acceptance criteria:**
- [ ] Schedule templates added to archetypes for all 7 genres
- [ ] Rust generator resolves NPC locations from archetype + time + calendar
- [ ] Present/absent NPC list injected into location prompt zone
- [ ] OTEL span: `npc_schedule.resolve` with NPC placements
- [ ] Named NPCs are consistently findable at generated locations

---

### Tier 2 — Medium Priority (enriches narrator choices)

#### 2.1 Economy / Trade

**Classification:** Baked (baseline) + procedural on tick (fluctuation)
**Effort:** Medium
**SOUL Alignment:** Living World (#2), Genre Truth (#3)

**What it does:** Defines trade routes, commodity baselines, and settlement
wealth. On tick, generates price fluctuations linked to trope state (e.g.,
"bandit_blockade" trope active → grain prices double on affected route).

**Content deliverables:**
- `economy.yaml` per world (baseline: trade routes, commodity sources)
- Economic disruption hooks in `tropes.yaml` (existing file, new field)

```yaml
# economy.yaml
trade_routes:
  - from: "Grimholt"
    to: "Thornwall"
    goods: ["iron_ore", "tools"]
    return_goods: ["grain", "wool"]
    danger: "moderate"
    status: "active"  # disrupted by tropes

commodity_baseline:
  iron_ore: { base_price: 5, abundance: "high", source: "Grimholt mines" }
  grain: { base_price: 3, abundance: "low", source: "Thornwall farms" }
```

**Acceptance criteria:**
- [ ] `economy.yaml` schema defined
- [ ] Economy authored for at least 2 worlds (proof of concept)
- [ ] Trope escalation can mark trade routes as disrupted
- [ ] Price modifiers injected into narrator context during shop/trade scenes
- [ ] OTEL: economy state in prompt zone spans

---

#### 2.2 Establishment Generator

**Classification:** Baked (notable) + procedural on tick (generic)
**Effort:** Medium
**SOUL Alignment:** Living World (#2), Diamonds and Coal (#8), Yes And (#9)

**What it does:** When a player enters an unnamed establishment, generates a
complete tavern/shop/temple with staff, menu/inventory, patrons, and — critically
— **trope-sourced rumors**. Named establishments are pre-authored in world YAML.

**Content deliverables:**
- Establishment templates per genre (quality tiers, menu items, patron archetypes)
- Rumor generation rules linking to active tropes

```yaml
# establishment_templates.yaml (genre level)
tavern:
  tiers:
    poor: { menu_quality: "gruel and ale", patron_count: [2, 4], rumors: 1 }
    common: { menu_quality: "stew and beer", patron_count: [4, 8], rumors: 2 }
    fine: { menu_quality: "roast and wine", patron_count: [6, 12], rumors: 3 }
  menu_items:
    - { name: "mutton stew", tier: "common", price_range: [2, 5] }
    - { name: "dark ale", tier: "poor", price_range: [1, 2] }
```

**Acceptance criteria:**
- [ ] Establishment templates for all 7 genres
- [ ] Generator produces named staff (from conlang), menu, patrons
- [ ] Rumors connect to active tropes (not random flavor)
- [ ] Establishment quality derived from settlement wealth (demographics)
- [ ] OTEL: `establishment.generate` span with composition

---

#### 2.3 Calendar / Timekeeping

**Classification:** Baked in (world authoring)
**Effort:** Small
**SOUL Alignment:** Living World (#2), Genre Truth (#3)

**What it does:** Establishes genre-appropriate time vocabulary, day/week/month
names, seasons, festivals, and celestial events. The narrator knows what day it
is, what season, and whether a festival is approaching.

**Content deliverable (per world):** `calendar.yaml`

```yaml
calendar:
  name: "The Turning"
  days_in_year: 360
  days_in_week: 6
  day_names: ["Swordsday", "Markday", "Ashday", "Fieldsday", "Starday", "Restday"]
  months:
    - name: "Thawmelt"
      days: 30
      season: "spring"
      festivals: ["First Planting — seeds blessed by clergy"]
  moons:
    - name: "The Pale"
      cycle_days: 28
      lore: "Full moon drives wolves to frenzy"
  time_precision: "quarter_day"  # dawn/midday/dusk/night
```

**Acceptance criteria:**
- [ ] `calendar.yaml` schema defined
- [ ] Calendar authored for at least 2 worlds per genre
- [ ] Current date/time/season injected into narrator context
- [ ] Festivals surface as narrative hooks at appropriate times
- [ ] Moon phases affect relevant mechanics (wolf behavior, magic, tides)

---

### Tier 3 — Lower Priority (structural enrichment)

#### 3.1 Quest Shapes

**Classification:** Baked in (genre authoring)
**Effort:** Small (YAML templates)
**SOUL Alignment:** Cut the Dull Bits (#10)

**What it does:** Defines structural templates for how tropes manifest as
playable sequences. When a trope escalates to "active quest," the system assigns
a quest shape and tracks phase progression. The narrator knows "this is a rescue
quest in the 'journey' phase" and paces accordingly.

**Content deliverable (per genre):** `quest_shapes.yaml`

```yaml
shapes:
  investigation:
    phases: ["hook", "clues", "false_lead", "revelation", "confrontation"]
    min_turns: 3
    pacing: "slow_build"
  rescue:
    phases: ["plea", "journey", "obstacle", "discovery", "extraction"]
    min_turns: 4
    pacing: "urgent"
  dungeon_crawl:
    structure: "five_room_dungeon"
    phases: ["threshold", "puzzle", "setback", "climax", "reward"]
    min_turns: 5
    pacing: "exploration"
```

**Acceptance criteria:**
- [ ] Quest shape schema defined
- [ ] 5+ shapes per genre (genre-appropriate variations)
- [ ] Trope escalation assigns quest shapes
- [ ] Current quest phase injected into narrator context
- [ ] OTEL: quest phase transitions observable

---

#### 3.2 Interior Topology

**Classification:** Procedural on tick (location entry)
**Effort:** Medium-Large (generator + narrator contract)
**SOUL Alignment:** Living World (#2), Tabletop First (#5)

**What it does:** When a player enters an interior space (dungeon, building,
cave), generates a narrative topology — rooms connected by passages, each with
type tags, obstacles, and content seeds. Based on the Five Room Dungeon pattern.

**Content deliverable (per genre):** Interior motifs and room type palettes

**Acceptance criteria:**
- [ ] Interior topology schema defined
- [ ] Room type palettes per genre
- [ ] Five Room Dungeon as default structural template
- [ ] Narrator receives full topology, reveals progressively
- [ ] OTEL: topology generation and room exploration spans

---

## Work Decomposition

### Phase 1: Schemas + Proof of Concept (1 epic)
Define YAML schemas for all 9 systems. Author content for `low_fantasy` as
the reference genre. Wire weather + demographics into prompt zones. Validate
with playtest.

**Stories:**
1. Define schemas for all 9 systems (YAML validation, schema docs)
2. Author `low_fantasy` weather rules
3. Author `low_fantasy/pinwheel_coast` demographics
4. Author `low_fantasy/pinwheel_coast` calendar
5. Rust: weather generator (rules + RNG → state)
6. Rust: prompt zone injection for weather + demographics
7. OTEL: weather and demographics spans
8. Playtest validation: narrator uses grounding data

### Phase 2: Genre Rollout (1 epic per tier)
Extend Tier 1 systems to all 7 genres. Author NPC schedules. Begin Tier 2.

### Phase 3: Full Suite (1 epic)
Economy, establishments, quest shapes. Interior topology as stretch.

## Sizing Estimate

Given that the Monster Manual pattern exists and `sidequest-genre` already reads
arbitrary YAML, the code effort is much smaller than a greenfield build:

| Phase | Content (YAML) | Code (Rust) | Prompt Wiring | Total |
|-------|----------------|-------------|---------------|-------|
| Phase 1 | 3-5 stories | 2-3 stories | 1-2 stories | 6-10 stories |
| Phase 2 | 10-14 stories | 2-3 stories | 1 story | 13-18 stories |
| Phase 3 | 6-8 stories | 3-5 stories | 1-2 stories | 10-15 stories |

**Content-to-code ratio: ~4:1.** Most work is authoring YAML and validating
narrator usage via `preview-prompt.py`. Rust code follows the namegen/encountergen
template — read YAML, apply RNG, emit structured JSON.

## Risks

### Mode Collapse Detection
Without OTEL verification, we can't tell if the narrator is using the grounding
data or ignoring it. OTEL spans on both the proposed state and the narrator's
usage are essential — not optional.

### Context Window Pressure
Every grounding system adds tokens to the narrator's prompt. Weather + demographics
+ NPC schedules + economy could add 500-1000 tokens per turn. Must be managed
through the existing prompt zone tier system — include what's relevant to the
current scene, not everything always.

### Content Authoring Scale
9 systems × 7 genres × 2+ worlds = significant content authoring. The world-builder
agent can handle bulk generation, but schemas must be locked before bulk authoring
begins. Phase 1's single-genre proof validates the schema before committing to
rollout.

### Genre Fitness
Not every system applies equally to every genre. `space_opera` stations may not
have weather. `road_warrior` may not have formal economy. Each genre should declare
which systems it uses and which are null/simplified.

## Testing Strategy

### Prompt Preview Loop (Primary)

Use `scripts/preview-prompt.py` for rapid iteration. This reconstructs the full
narrator prompt with attention-zone ordering — the exact text Claude receives.

**The loop:**
1. Author YAML content (e.g., `weather.yaml` for low_fantasy)
2. Wire into prompt zone (add section to template)
3. Run `python scripts/preview-prompt.py` to verify injection
4. Check: Is the grounding data in the right zone? Is it concise enough?
   Does it give the narrator what it needs without bloating the context?
5. Iterate YAML/template until the preview looks right
6. Then (and only then) test with a live narrator call

This is dramatically faster than full playtest cycles. Most of the work is
getting the YAML schema and prompt injection right — that's all testable
without spinning up the game engine.

### Scripted Scenario Validation (Secondary)

Once prompt injection is verified via preview, run scripted scenarios
(`scripts/playtest.py --scenario`) to confirm the narrator actually uses the
injected data. Compare narrator output across multiple runs to verify variety
(anti-mode-collapse).

### OTEL Dashboard Verification (Ongoing)

The GM dashboard (`scripts/playtest_dashboard.py`) must show:
- What grounding data was proposed (generated state)
- What the narrator actually referenced (extracted from narration)
- The delta between proposed and used

This is how we catch mode collapse in production — if the narrator ignores
90% of weather proposals, OTEL reveals it.

## Success Metric

**Prompt preview validation:** `preview-prompt.py` shows grounding data in the
correct attention zones, at reasonable token cost, with genre-appropriate content.

**Narrator usage validation:** Across 5+ scripted scenario runs, the narrator
produces measurably more varied and consistent descriptions with grounding active
vs without. No weather contradictions, no villages with 15 shops, no NPCs
appearing in impossible locations.

The narrator's job shifts from **invention to curation**. That's the win.

---

## Implementation Pattern: Follow the Monster Manual

Each new system follows the established Monster Manual pipeline (ADR-059):

1. **YAML schema** — define the content format in genre packs
2. **Content authoring** — fill schemas per genre/world (world-builder agent)
3. **Rust generator** — tool binary or module that reads YAML + RNG → structured output
   (follow `sidequest-namegen` as template — these are small binaries, not frameworks)
4. **Prompt zone injection** — add section to narrator template in appropriate attention zone
5. **OTEL spans** — emit proposed state, verify against narrator usage

The Rust infrastructure for all of this already exists:
- `sidequest-genre` reads arbitrary YAML from genre packs
- `dispatch/mod.rs` assembles prompt zones and injects game state (lines 385-405)
- `markov.rs` generates culture-appropriate names from corpus
- `monster_manual.rs` demonstrates persistent pool + lifecycle pattern
- Attention zones (Primacy/Early/Valley/Late/Recency) are already ordered
- `preview-prompt.py` enables rapid iteration without full playtest cycles

**The gap is content + prompt wiring, not architecture.**

For **baked** systems (demographics, calendar): YAML authoring + prompt injection only.
For **on-tick** systems (weather, NPC schedules): small Rust generator + prompt injection.
For **hybrid** systems (economy, establishments): YAML baseline + Rust modifier + prompt injection.

**Existing prompt template zones** (`docs/prompt-reworked.md`):
- `<world-lore>` — demographics, calendar fit here naturally
- `<game-state>` — weather, economy fluctuations, NPC schedules inject here
- `<players>` — loadout already injected here
- New systems may need new sections (e.g., `<environment>` for weather/time)

---

## Appendix: The Anti-Mode-Collapse Thesis

Random encounter tables have been anti-mode-collapse tools since the 1970s. DMs
reach for d100 charts not because they can't invent — but because they know their
own training distribution will converge on familiar patterns. The procedural
generators in this PRD serve the same function for an LLM narrator.

This is also a 30-year personal design lineage — from MUSHcode through populinator,
fantasy-language-maker, townomatic, steading-o-matic, gotown, and finally
SideQuest. The LLM narrator was the missing piece that made the vision buildable.
The generators were always the plan.

See `docs/research/procedural-generation-lineage.md` for the full history.
