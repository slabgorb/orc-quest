# Procedural Generation Lineage — From Encounter Tables to SideQuest

> Research compiled 2026-04-04 during GM audit of slabgorb GitHub repos against
> donjon.bin.sh generator patterns.

## Thesis

SideQuest is not a 2026 project. It is the culmination of 30+ years of procedural
RPG world generation work — much of it predating GitHub (2008). The public repos
under `github.com/slabgorb` are snapshots of a design lineage that stretches back
to hand-rolled encounter tables and early personal tooling.

donjon.bin.sh represents the **static generation ceiling** that this lineage kept
pushing against. Every repo below was trying to do what donjon does but with more
mechanical grounding, more relational coherence, and more narrative depth. SideQuest
is what happens when an LLM narrator finally bridges the gap between "generated
content" and "living world."

---

## The Repos — Chronological Lineage

### NPC Generation: Genetic Inheritance

**populinator-0** (Ruby, ~2013, 497 commits)
- Generated RPG towns populated with interconnected NPCs
- Core innovation: **genetic simulation using hex-code inheritance** — children
  inherit trait colors from parents, creating visual family resemblance
- Purpose: "When players unexpectedly venture off the planned story path"
- This is not random NPC generation. This is **relational NPC generation** —
  characters exist in family trees with hereditary traits

**populinator** (Ruby, later iteration)
- Continued development of the same concept

**SideQuest descendant:** NPC Registry, Creature Smith, archetype system. The
insight that NPCs need *relationships* (not just stats) is foundational to how
SideQuest's creature_smith generates characters that feel connected to their world.

### Language Generation: Corpus-Based Markov Chains

**fantasy-language-maker** (Python, ~2014, 11 stars, 6 forks)
- Markov chain analysis of text corpuses (Project Gutenberg samples)
- Generates phonetically coherent fantasy vocabulary
- Configurable lookback depth and dictionary sources
- Not random syllable smashing — **statistical phonetic modeling**

**lango** (Go, 2017)
- Go port of the same algorithm
- Represents the pattern of rebuilding core ideas in systems languages

**SideQuest descendant:** The conlang system. World-specific Markov language
generation that produces names consistent with a world's linguistic identity.
This is why SideQuest names sound *coherent within a world* rather than like
random draws from cultural buckets (the donjon approach).

### Settlement Generation: Mechanically Grounded Towns

**townomatic** (CoffeeScript/MongoDB, ~2014, 160 commits)
- "Makes towns and communities on the fly for RPG referees"
- Web application with persistent data (MongoDB)
- The key word is "on the fly" — runtime generation, not pre-authored content

**town-o-matic** (Ruby, parallel implementation)
- Server-side town generation

**steading-o-matic** (CoffeeScript, ~2016, 127 commits)
- Settlement generation, likely based on Dungeon World's steading mechanics
- Dungeon World steadings use **tag-based mechanical descriptions** — a town
  isn't just a name and population, it has tags like "Steady," "Guard," "Market,"
  "Resource (iron)" that mechanically define what it *is*

**Steadingomatic** (Swift, 2016)
- Native port attempt of the same concept

**SideQuest descendant:** World YAML structure, POI system, faction territories.
The insight that a settlement needs *mechanical tags* (not just flavor text) is
exactly how SideQuest genre packs define locations — with structured YAML that
the narrator can query, not prose descriptions it has to parse.

### Spatial Generation: Dungeon Topology

**maze-maker** (Ruby, 2015)
- Multiple maze generation algorithms (Prim's as default)
- ImageMagick rendering
- "Generally suitable for geeky stuff like D&D"
- Customizable complexity, density, and visual styling

**SideQuest descendant:** Location topology concepts, confrontation arena layout.
The understanding that spatial environments have *algorithmic structure* informs
how SideQuest handles location connectivity and movement.

### Data Visualization as Identity

**chernoff-faces** (Ruby, 2013, 3 stars)
- SVG Chernoff face library
- Maps multivariate data to facial features (eye size, nose length, mouth shape)
- Turns numbers into recognizable, distinguishable visual identities

**SideQuest descendant:** Conceptual ancestor of NPC portraiture. The insight
that you can map *data dimensions to visual features* is a generalized version
of what portrait generation does — turning archetype parameters into distinct
visual identities.

### The Synthesis: GoTown

**gotown** (Go, ~2017, 305 commits)
- The most SideQuest-shaped repo in the lineage
- Modules: `heraldry`, `inhabitants`, `locations`, `timeline`, `mapper`, `words`,
  `random`, `resource`, `persist`
- Dockerized web application
- **This is the proto-SideQuest** — a single system combining inhabitants,
  locations, heraldry (visual identity), timeline (history), and words (language)
  into one coherent world generator
- 305 commits suggests serious, sustained development — not a weekend experiment

**SideQuest descendant:** The entire architecture. GoTown's module structure maps
almost directly to SideQuest's crate structure:
- `inhabitants` → `sidequest-game` (characters, NPCs)
- `locations` → POI system, world YAML
- `words` → conlang system
- `timeline` → campaign history, trope engine progression
- `heraldry` → visual identity / portrait system
- `mapper` → location topology
- `persist` → save system

### The Direct Predecessor

**sidequest** (Python, 2026)
- "An AI Dungeon Master powered by coordinated Claude agents, so everyone gets to play"
- The proof-of-concept that validated the LLM narrator as the missing piece
- Everything before this was procedural generation without narrative coherence
- Everything after this (sidequest-api, Rust) is the production-grade rebuild

---

## The Convergence Pattern

```
~1996        MUSHcode — procedural world-building on text-based MUSHes
    │         (pre-web, pre-GitHub, pre-pictures-on-the-internet)
    │
    │         ORIGIN: ASYMMETRIC INFORMATION — Keith built a drivable car
    │         object (a mobile room that moved between rooms) where speech
    │         only propagated to outside listeners if the windows attribute
    │         was set to "down." Same physical space, different information
    │         access, gated by object state. The car also had a RADIO
    │         (channel-based group communication) and a HORN (always-
    │         broadcast to parent room, content-free presence signal).
    │
    │         Two information channels with different propagation rules:
    │         - Speech + radio (window-gated) → sealed turns, per-player
    │           narration — content scoped by game state
    │         - Horn (always-broadcast, content-free) → presence notification
    │           that punches through scope boundaries
    │
    │         The horn pattern — "something is here" without revealing
    │         details — is the ancestor of asymmetric event notifications:
    │         you know something happened, but not what. Sprint 2's
    │         multiplayer information architecture was prototyped on a
    │         MUSH in the 1990s.
    │
    │         KEY INSIGHT: The MUD→MUSH split IS the "Yes, And" principle.
    │         MUDs were hardcoded: players operated within fixed verbs and
    │         systems defined by the server. MUSHes were softcoded: players
    │         could CREATE objects, rooms, and behaviors — the world said
    │         "yes, and" to player creativity. MUSH didn't just allow
    │         player agency, it made players co-authors of the world.
    │
    │         SideQuest's SOUL principle #9 ("Yes, And — canonize player-
    │         introduced details that fit genre truth") wasn't named yet —
    │         improv theater popularized the term later. But the principle
    │         was already the lived practice in MUSHcode: the best worlds
    │         are the ones players help build. The term caught up to what
    │         MUSH builders already knew.
    │
    ├── 2013  populinator-0 ── genetic NPC inheritance
    ├── 2013  chernoff-faces ── data as visual identity
    ├── 2014  fantasy-language-maker ── corpus Markov conlang
    ├── 2014  townomatic ── runtime town generation
    ├── 2015  maze-maker ── algorithmic spatial generation
    ├── 2016  steading-o-matic ── tag-based settlement mechanics
    │
    ├── 2017  gotown ── SYNTHESIS: all systems in one app (305 commits)
    ├── 2017  lango ── language gen ported to systems language (Go)
    │
    │   [gap — the static ceiling holds]
    │
    ├── 2026  sidequest (Python) ── LLM narrator breaks the ceiling
    └── 2026  sidequest-api (Rust) ── production rebuild
```

The pattern is clear: **every 2-3 years, a new attempt to synthesize procedural
RPG generation into a coherent whole.** Each attempt added a dimension (NPCs →
language → settlements → spatial → all-in-one). The static generation ceiling
held until LLMs provided the narrative glue.

---

## What This Means for Content Architecture

1. **The conlang system is not experimental.** It's the fourth iteration of an
   approach Keith has been refining since 2014. Treat it as mature design.

2. **NPC generation should be relational, not random.** populinator proved that
   genetic/hereditary NPC generation creates more believable worlds than stat
   rolling. The creature_smith and archetype system carry this forward.

3. **Settlements need mechanical tags.** The steading-o-matic lineage shows that
   tag-based settlement definitions (Dungeon World style) produce more usable
   content than prose descriptions. World YAML should be queryable, not readable.

4. **GoTown's module structure is a design document.** Its division into
   inhabitants/locations/heraldry/timeline/words is a validated decomposition
   that directly informed SideQuest's crate architecture.

5. **donjon is a peer, not a source.** Both donjon and SideQuest descend from
   the same DM need (procedural content for tabletop RPGs), but SideQuest's
   lineage has always pushed for more depth — relational NPCs, phonetic language
   coherence, mechanical settlement tags — where donjon optimized for breadth
   and accessibility.

---

## donjon Feature Comparison

For reference — what donjon offers and where SideQuest's lineage diverges:

| donjon Generator | SQ Equivalent | Key Difference |
|------------------|---------------|----------------|
| Fantasy Name Generator | Conlang Markov system | Phonetic coherence vs random cultural buckets |
| Random Town Generator | World YAML + POI system | Mechanical tags vs description lists |
| Random Dungeon Generator | Location topology | Living environment vs static map |
| Random NPC Generator | Creature Smith + archetypes | Relational/hereditary vs stat block |
| Random Encounter Generator | Trope engine | Narrative-driven vs CR math |
| Medieval Demographics | (potential import) | Population grounding — useful pattern |
| Five Room Dungeon | (structural pattern) | Encounter arc template — useful for confrontation phases |
| Fractal World Generator | (seed inspiration) | Geographic imagination starter |
| Fantasy Calendar | (potential feature) | Genre-specific timekeeping |
| Star System Generator | space_opera worlds | Structural reference for system layout |

### Patterns Worth Adopting

- **Demographics calculator** — Grounding POI density and NPC variety in population
  math prevents absurdities (village of 200 with 15 shops)
- **Five Room Dungeon structure** — Entrance/Guardian → Puzzle/RP → Trick/Setback →
  Boss → Reward/Twist as a universal encounter arc template for confrontation phases
- **Fractal world generation** — As geographic seed when authoring new worlds
