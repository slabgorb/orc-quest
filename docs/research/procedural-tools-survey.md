# Procedural Tools Survey — Baked vs On-Tick

> Research compiled 2026-04-04. Surveyed donjon.bin.sh generators against SideQuest's
> content architecture and narrator-gaslighting pattern.

## The Architecture

SideQuest presents **speculative game state** to the narrator. The narrator weaves
what it chooses from that state. The system then reconciles actual game state to
match the narrator's choices. Procedural generators feed the narrator's context
window — they don't produce player-facing output directly.

This means procedural tools fall into two categories:

- **Baked in** — Generated once at world authoring time, stored in YAML. The narrator
  always has access to this as baseline world truth. Topography, demographics baseline,
  calendar systems, cultural frameworks.

- **Procedural on tick** — Generated each turn/scene and injected into the narrator's
  context as "here's what's happening right now." Weather, NPC arrivals, rumor
  availability, economic conditions, quest hooks surfacing from trope progression.
  The narrator sees proposals; whatever it uses becomes canon.

## Current State — What Exists Today

### Genre Pack Level (21 YAML files per genre)
- pack.yaml, lore.yaml, theme.yaml, char_creation.yaml, axes.yaml, rules.yaml
- visual_style.yaml, prompts.yaml, archetypes.yaml, tropes.yaml, beat_vocabulary.yaml
- openings.yaml, inventory.yaml, achievements.yaml, power_tiers.yaml, progression.yaml
- history.yaml, audio.yaml, voice_presets.yaml, cultures.yaml, cartography.yaml

### World Level (8 files per world)
- world.yaml, lore.yaml, history.yaml, cartography.yaml, cultures.yaml
- tropes.yaml, legends.yaml, portrait_manifest.yaml

### What's Missing
- No demographics / population data
- No calendar / timekeeping
- No economy / trade simulation
- No weather system
- No dungeon / interior topology
- No procedural quest templates
- No NPC schedule / routine system
- No rumor propagation model

The content is **narratively heavy, not simulation heavy.** Rich in tone, voice,
and escalation mechanics — but thin on the procedural grounding that would let
the narrator make mechanically-informed choices about "what's happening in this
town right now."

---

## The Tools — Baked vs On-Tick Classification

### 1. DEMOGRAPHICS (donjon: Medieval Demographics Calculator)

**Source data:** Population, area, density → settlement counts, profession
distribution, guard numbers, clergy, noble houses, shops per capita.

**Classification: BAKED IN (world authoring)**

Demographics are structural. A village of 200 people has ~1 inn, no dedicated
blacksmith, and a part-time militia. A city of 10,000 has guilds, a standing
guard, temples, and a merchant quarter. This doesn't change turn-to-turn.

**Where it lives:** `worlds/{world}/demographics.yaml`

**Schema sketch:**
```yaml
# demographics.yaml
population_model:
  base: "S. John Ross Medieval Demographics Made Easy"
  # or genre-appropriate alternative

settlements:
  - name: "Grimholt"
    type: "small_town"
    population: 1200
    density: "moderate"
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
    # Narrator uses this to ground descriptions —
    # "the single blacksmith" not "one of the blacksmiths"
```

**Narrator injection:** Part of location context. When player enters Grimholt,
the narrator knows it has 1200 people, one noble house, twelve guards. Descriptions
stay grounded. No village with 15 shops.

**Genre adaptation:**
- `low_fantasy` → medieval model (Ross)
- `neon_dystopia` → corporate arcology population density
- `space_opera` → station/colony crew complement
- `road_warrior` → caravan size, settlement scarcity
- `pulp_noir` → city ward population, beat cop coverage

---

### 2. WEATHER (donjon: Random Weather Generator)

**Source data:** Season, climate, terrain → temperature, precipitation, wind,
visibility, special conditions.

**Classification: PROCEDURAL ON TICK**

Weather changes. It affects mood, travel, combat. The narrator should know "it's
raining and visibility is poor" when describing a scene — but only if the weather
system says so. Otherwise the narrator will invent weather inconsistently.

**Where it lives:** Genre-level `weather.yaml` (climate rules), generated per-tick

**Schema sketch:**
```yaml
# weather.yaml (genre pack level — rules)
climate_zones:
  temperate:
    seasons:
      spring:
        temp_range: [5, 18]  # celsius
        precipitation_chance: 0.4
        conditions: ["clear", "overcast", "rain", "fog", "storm"]
        weights: [30, 30, 25, 10, 5]
      # ...
    special_events:
      - name: "harvest_gale"
        season: "autumn"
        chance: 0.05
        duration_days: [1, 3]
        effects: ["travel_penalty", "visibility_poor"]

# Generated per tick and injected into narrator context:
# current_weather:
#   condition: "heavy_rain"
#   temp: 8
#   visibility: "poor"
#   wind: "strong"
#   special: null
#   narrative_hint: "Rain hammers the cobblestones. Torches gutter."
```

**Narrator injection:** Part of scene context on every tick. The narrator sees
weather state and can choose to foreground it or let it be ambient. Either way,
it won't contradict itself ("the sun blazed" one turn, "rain continued" the next).

**Genre adaptation:**
- `low_fantasy` → medieval seasonal weather, natural disasters
- `road_warrior` → dust storms, radiation weather, acid rain
- `neon_dystopia` → smog levels, acid rain, atmospheric processors
- `space_opera` → planetary atmosphere, void/station (no weather)
- `mutant_wasteland` → fallout zones, mutagen storms
- `elemental_harmony` → elemental weather tied to balance state

---

### 3. CALENDAR / TIMEKEEPING (donjon: Fantasy Calendar Generator)

**Source data:** Days in year, months, moons, seasons, holidays, celestial events.

**Classification: BAKED IN (world authoring)**

Calendar is structural world-building. It establishes time vocabulary ("the third
moon of Ashfall") and grounds seasonal/festival content. The narrator needs to
know what day it is, what season, whether a holiday is approaching.

**Where it lives:** `worlds/{world}/calendar.yaml`

**Schema sketch:**
```yaml
# calendar.yaml
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
    - name: "Greenrise"
      days: 30
      season: "spring"
      festivals: []
    # ...
  moons:
    - name: "The Pale"
      cycle_days: 28
      lore: "Full moon drives wolves to frenzy"
  time_tracking:
    precision: "quarter_day"  # dawn/midday/dusk/night
    # Not hour-by-hour — tabletop granularity
```

**Narrator injection:** Current date/season/time-of-day as part of world state.
The narrator knows "it's Restday evening in late Ashfall, the Pale is full" and
can weave that into descriptions and NPC behavior (shops closed on Restday, wolves
active under full moon).

**Genre adaptation:**
- `low_fantasy` → lunar calendars, agricultural festivals, saint days
- `space_opera` → standard galactic time, local planetary cycles
- `neon_dystopia` → corporate fiscal quarters as cultural time (Q3 crunch)
- `road_warrior` → seasons known by survival impact ("the dry," "burn season")
- `elemental_harmony` → elemental cycles, alignment days

---

### 4. ECONOMY / TRADE (no direct donjon equivalent — implicit in demographics)

**Source data:** Settlement wealth, trade routes, commodity availability,
price fluctuation.

**Classification: BAKED IN (baseline) + PROCEDURAL ON TICK (fluctuation)**

The baseline economy is structural — Grimholt is a mining town, iron is cheap
here, grain is imported. But prices shift with supply/demand, trade disruption,
and narrative events (trope: "bandit blockade" → grain prices spike).

**Where it lives:** `worlds/{world}/economy.yaml` (baseline), tick-generated fluctuation

**Schema sketch:**
```yaml
# economy.yaml
trade_routes:
  - from: "Grimholt"
    to: "Thornwall"
    goods: ["iron_ore", "tools"]
    return_goods: ["grain", "wool"]
    danger: "moderate"  # bandits, terrain
    status: "active"  # can be disrupted by tropes

commodity_baseline:
  iron_ore: { base_price: 5, abundance: "high", source: "Grimholt mines" }
  grain: { base_price: 3, abundance: "low", source: "Thornwall farms" }
  healing_herbs: { base_price: 15, abundance: "scarce", source: "forest foragers" }

# On tick, price modifier injected to narrator:
# economy_state:
#   iron_ore: { price: 5, modifier: 1.0, reason: null }
#   grain: { price: 6, modifier: 2.0, reason: "trade_route_disrupted" }
```

**Narrator injection:** When player enters a shop or discusses trade, the narrator
knows what's available, what's expensive, and *why*. "Grain's dear this month —
the road to Thornwall's been cut" is mechanically grounded, not improvised.

**Genre adaptation:**
- `low_fantasy` → medieval commodities, guild pricing
- `neon_dystopia` → corporate supply chains, black market margins
- `space_opera` → interstellar freight, fuel costs, contraband
- `road_warrior` → barter economy, fuel/water/ammo as currency
- `pulp_noir` → protection rackets, bootleg pricing, fence rates

---

### 5. INTERIOR TOPOLOGY / DUNGEON LAYOUT (donjon: Random Dungeon Generator)

**Source data:** Room count, connectivity, room types (entry, puzzle, trap, boss,
treasure), corridor style, motif.

**Classification: PROCEDURAL ON TICK (location entry)**

When a player enters a ruin, cave, or building interior, the system generates a
topology and presents it to the narrator. The narrator describes rooms as the
player explores. Rooms don't need D&D grid maps — they need **narrative topology**:
what connects to what, what's in each space, what's between them.

**Where it lives:** Generated on location entry, not pre-authored

**Schema sketch:**
```yaml
# Generated when player enters an interior location
interior_topology:
  name: "The Undercroft of Saint Venna"
  motif: "abandoned_holy"
  rooms:
    - id: "entry"
      type: "threshold"
      description_seed: "collapsed nave, rubble, faint light from above"
      exits: ["corridor_1"]
    - id: "corridor_1"
      type: "passage"
      description_seed: "narrow, water-damaged murals, dripping"
      exits: ["entry", "shrine", "trap_room"]
      obstacle: { type: "locked_gate", check: "dexterity", dc: 12 }
    - id: "shrine"
      type: "puzzle"
      description_seed: "intact altar, three candle holders, inscription"
      exits: ["corridor_1", "hidden_vault"]
      puzzle_hint: "light order matches saint's virtues in inscription"
    - id: "trap_room"
      type: "hazard"
      description_seed: "wide chamber, tiled floor, ceiling holes"
      exits: ["corridor_1"]
      trap: { type: "dart_volley", trigger: "pressure_plate", damage: "2d6" }
    - id: "hidden_vault"
      type: "reward"
      description_seed: "small sealed room, reliquary, dust undisturbed"
      exits: ["shrine"]
      treasure: { quality: "rare", thematic: "holy_relic" }
  structure: "five_room_dungeon"
  # Entrance → Puzzle → Hazard → (Boss optional) → Reward
```

**Narrator injection:** The narrator gets the full topology and reveals rooms as
the player explores. It knows what's behind the locked gate without the player
knowing. It can drop hints ("you hear dripping from the left passage").

**The Five Room Dungeon pattern** (from donjon) is a reusable structural template:
1. Entrance/Guardian — threshold with a cost to enter
2. Puzzle/Roleplay — non-combat challenge
3. Trick/Setback — complications, resource drain
4. Boss/Climax — major confrontation
5. Reward/Twist — payoff with a hook forward

This maps directly to confrontation phase progression.

**Genre adaptation:**
- `low_fantasy` → dungeons, ruins, cave systems, castle interiors
- `neon_dystopia` → corporate tower floors, sewer networks, data vaults
- `space_opera` → ship interiors, station sections, derelict hulks
- `road_warrior` → bunker complexes, mine shafts, wrecked convoys
- `pulp_noir` → warehouse layouts, speakeasy back rooms, sewer tunnels

---

### 6. INN / ESTABLISHMENT GENERATOR (donjon: Random Inn Generator)

**Source data:** Quality tier, menu, staff, patrons, rumors, atmosphere.

**Classification: BAKED IN (notable establishments) + PROCEDURAL ON TICK (generic)**

Named establishments in the world YAML are pre-authored. But when the player
walks into an unnamed tavern in a settlement, the system generates one and
presents it to the narrator.

**Schema sketch:**
```yaml
# Generated on entering an unnamed establishment
establishment:
  name: "The Broken Cask"  # from conlang/culture name patterns
  type: "tavern"
  quality: "common"  # derived from settlement wealth
  atmosphere: "rowdy"
  innkeeper:
    name: "Marta Voss"
    archetype: "shrewd_matron"
    disposition: "neutral"
    knows_rumors: [0, 2]  # indices into rumor list
  menu:
    - { item: "mutton stew", price: 3, quality: "filling" }
    - { item: "dark ale", price: 1, quality: "decent" }
    - { item: "hard bread", price: 1, quality: "stale" }
  patrons:
    - { archetype: "off_duty_guard", disposition: "wary", hook: "complains about increased patrols" }
    - { archetype: "traveling_merchant", disposition: "friendly", hook: "looking for escort to next town" }
  rumors:
    - { content: "Miners found something under the north shaft", veracity: "true", source_trope: "undercroft_discovery" }
    - { content: "The lord's son hasn't been seen in weeks", veracity: "partial", source_trope: "noble_intrigue" }
    - { content: "Wolves took three sheep last full moon", veracity: "true", source_trope: null }
```

**Narrator injection:** When the player asks "I look for a tavern," the narrator
gets a fully-realized establishment with named staff, a menu with prices that
match the local economy, patrons with hooks, and rumors that **connect to active
tropes**. The narrator picks what to foreground.

The rumor system is where this gets powerful — rumors are **trope-sourced**, so
they're not random flavor. They're narrative hooks that point at active or upcoming
story threads. The narrator presents them as tavern gossip; the player decides
what to pursue.

---

### 7. ADVENTURE / QUEST STRUCTURE (donjon: Random Adventure Generator)

**Source data:** Theme, goal, story hook, plot structure, climax type, villain,
supporting cast, encounters.

**Classification: PROCEDURAL ON TICK (trope-driven)**

This is where SideQuest diverges most from donjon. donjon generates a static
adventure outline. SideQuest's trope engine already does this *dynamically* —
tropes escalate on tick, surface quest hooks when they reach thresholds, and
resolve based on player engagement.

**What's missing:** Structural templates for *how* tropes manifest as playable
sequences. The trope says "bandit_blockade escalates to confrontation." But
what's the *shape* of that confrontation sequence?

**Schema sketch — quest shapes (baked into genre):**
```yaml
# quest_shapes.yaml (genre level)
shapes:
  investigation:
    phases: ["hook", "clues", "false_lead", "revelation", "confrontation"]
    min_turns: 3
    pacing: "slow_build"
    # Narrator gets: "this quest is in the 'clues' phase, player has found 1 of 3"

  rescue:
    phases: ["plea", "journey", "obstacle", "discovery", "extraction"]
    min_turns: 4
    pacing: "urgent"

  heist:
    phases: ["recruitment", "planning", "infiltration", "complication", "escape"]
    min_turns: 5
    pacing: "escalating"

  dungeon_crawl:
    structure: "five_room_dungeon"
    phases: ["threshold", "puzzle", "setback", "climax", "reward"]
    min_turns: 5
    pacing: "exploration"

  diplomatic:
    phases: ["audience", "demand", "negotiation", "test_of_faith", "accord_or_betrayal"]
    min_turns: 3
    pacing: "tension"
```

**Narrator injection:** When a trope escalates to "active quest," the system
assigns a quest shape and tracks phase progression. The narrator knows "this is
a rescue quest, we're in the 'journey' phase" and paces accordingly.

---

### 8. NPC SCHEDULES / ROUTINES (no donjon equivalent)

**Source data:** NPC role, location, time of day, day of week.

**Classification: PROCEDURAL ON TICK**

NPCs should be *somewhere* at any given time. The blacksmith is at the forge by
day, the tavern by night. The lord is in the great hall for audiences at midday.
The thief operates at night. This is Living World (SOUL #2).

**Schema sketch:**
```yaml
# Generated from archetype + settlement + calendar
npc_schedule:
  - npc: "Marta Voss"
    routine:
      dawn: { location: "kitchen", activity: "preparing breakfast" }
      midday: { location: "tavern_floor", activity: "serving patrons" }
      dusk: { location: "tavern_floor", activity: "busy evening crowd" }
      night: { location: "upstairs_quarters", activity: "sleeping", available: false }
    exceptions:
      - { day: "Markday", override: "market_square", reason: "buying supplies" }
```

**Narrator injection:** When the player looks for Marta at dawn, the narrator
knows she's in the kitchen. If the player comes at night, the narrator knows
she's unavailable. Consistency without the narrator having to remember or invent.

---

### 9. FRACTAL WORLD MAP (donjon: Fractal World Generator)

**Source data:** Water %, ice %, terrain generation parameters.

**Classification: BAKED IN (world authoring tool)**

Not a runtime system. A tool for the world-builder to generate geographic seeds
when authoring new worlds. The output informs the cartography.yaml navigation
graph — continent shapes, coastlines, mountain ranges, river basins.

**Current state:** cartography.yaml already has world_graph with nodes and edges.
The fractal generator would be an authoring aid, not a game system.

---

## Summary Matrix

| Tool | Classification | When Generated | Where Stored | Genre-Variable |
|------|---------------|----------------|--------------|----------------|
| Demographics | Baked | World authoring | `demographics.yaml` | Yes — model per genre |
| Weather | On Tick | Every scene/travel | Generated, not stored | Yes — climate per genre |
| Calendar | Baked | World authoring | `calendar.yaml` | Yes — time model per genre |
| Economy | Baked + Tick | Baseline authored, fluctuation on tick | `economy.yaml` + generated | Yes |
| Interior Topology | On Tick | Location entry | Generated, not stored | Yes — motifs per genre |
| Establishments | Baked + Tick | Notable authored, generic on tick | Part of world YAML + generated | Yes |
| Quest Shapes | Baked | Genre authoring | `quest_shapes.yaml` | Yes — shapes per genre |
| NPC Schedules | On Tick | NPC interaction | Generated from archetype + time | Partially |
| World Maps | Baked (tool) | World authoring | Informs `cartography.yaml` | No — authoring aid |

## The LLM Problem: Creative but Repetitive

Left to its own devices, the LLM narrator WILL make things up on the fly. It's
good at this — convincing, fluent, genre-appropriate. The problem is that it will
make up **the same things every time.** Every tavern has a grizzled barkeep. Every
forest has ancient twisted oaks. Every guard is suspicious but ultimately helpful.

LLMs have mode collapse on narrative detail. Without seeded variety, the narrator
converges on its training distribution — the most statistically likely fantasy
tavern, the most common guard encounter, the median weather description.

**The solution is mad libs.** Seed the game state with procedurally generated
specifics BEFORE the narrator sees it. The narrator doesn't invent "what's in
this tavern" — it receives "this tavern has a young innkeeper named Della who
inherited the place last month, serves eel pie, and has a patron who's an
off-duty guard complaining about double shifts." The narrator's job shifts from
**invention** (where it repeats itself) to **narration** (where it excels).

The procedural generators are anti-mode-collapse tools. They force variety into
the narrator's input so the narrator's output stays fresh.

This is the same problem human DMs have always had — and the same solution.
Random encounter tables, d100 rumor charts, and NPC generators exist because
human DMs have their own mode collapse. The third session where "you meet a
merchant on the road" isn't creative failure — it's the DM's training
distribution asserting itself. Gygax was solving this in the 1970s with
percentile tables. donjon solves it with web generators. SideQuest solves it
with procedural YAML injected into the narrator's context window. Same problem,
same solution, different DM.

---

## The Narrator-Gaslighting Pattern

All "on tick" generators follow the same flow:

```
[Procedural Generator] → speculative state
        ↓
[Prompt Zone Assembly] → injected into narrator context
        ↓
[Narrator] → weaves selectively from state
        ↓
[State Reconciliation] → what narrator used becomes canon
        ↓
[OTEL] → verifies what was proposed vs what was used
```

The generators don't need to be perfect. They need to be **plausible enough that
the narrator can select from them without contradicting itself.** The narrator is
the curator. The generators are the catalog.

## Priority Assessment

Based on narrative impact and mechanical grounding:

### High Priority (directly prevents narrator improvisation)
1. **Weather** — narrator invents weather inconsistently without it; cheap to implement
2. **Demographics** — prevents absurd settlements (village with 15 shops); baked, low effort
3. **NPC Schedules** — Living World principle; NPCs should be *somewhere*

### Medium Priority (enriches narrator choices)
4. **Economy / Trade** — grounds price conversations, creates narrative hooks via disruption
5. **Establishments** — taverns are the #1 player social space; they need mechanical backing
6. **Calendar** — time vocabulary, festivals as narrative hooks, seasonal grounding

### Lower Priority (structural enrichment)
7. **Quest Shapes** — trope engine already handles quest emergence; shapes add pacing structure
8. **Interior Topology** — five-room-dungeon pattern for dungeon crawl sequences
9. **World Maps** — authoring tool only, not runtime

## Implementation Note

These are NOT code tasks. They are:
- **YAML schema definitions** (what fields exist)
- **Genre pack content** (filling in the schemas per genre)
- **Prompt zone wiring** (telling the narrator about the state)

The Rust code that reads YAML and injects it into prompt zones already exists
(`sidequest-genre` crate). The gap is **content**, not code.
