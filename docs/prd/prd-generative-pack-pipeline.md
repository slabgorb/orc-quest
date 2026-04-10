# PRD: Generative Pack Pipeline (Brainstorm Capture)

**Status:** Direction, not decision. Living document — expect revision.
**Captured:** 2026-04-10
**Supersedes planning for:** ADR-072 (System/Milieu Decomposition), Epic 32
**Relationship:** This document describes *where we want to land*. ADR-072 described
one possible shape; this reframes both the target and the motivation. ADR-072 is not
wrong, it's under-scoped.

---

## 1. The Core Insight (the thing this document exists to preserve)

SideQuest's real user is Keith as the **first player**, not Keith as the author.

Keith has been a forever-DM for 40 years. That means he has *never once* walked into
a campaign world he didn't already know the secrets of — every faction's betrayal,
every NPC's motive, every dungeon's trap was his idea first. This project exists to
address that specific 40-year deprivation: the chance to be surprised by a world
you're playing in.

This reframes every architectural choice:

- **Keith's own authoring is a loss of information, not a gain.** Every faction he
  writes by hand burns a surprise. The ideal pipeline minimizes Keith's visibility
  into what's actually in a pack while maximizing the model's freedom to surprise him.
- **Cliché is the adversary, not architecture.** If the pipeline generates a noir
  detective with a whiskey problem and a dead partner, the magic dies. The
  decomposition's real job is to be a *cliché-breaker* — to force unusual combinations
  the model wouldn't reach for on its own.
- **The product is the pack generator, not the runtime.** The narrator, the combat
  engine, the OTEL dashboard — those are infrastructure. The product is the thing
  that takes a friend's pitch and produces a playable, surprising pack in hours.

## 2. The Saturday Test (the load-bearing requirement)

> Keith asks his friends: "What's the place you want to roleplay in the most?"
> They say "Deadwood," or "The Expanse," or "a heist crew in 1970s Vegas."
> Keith says "give me till tomorrow."
> The next day, they play.

This is the whole design constraint. Any architectural choice that makes this take
three days is wrong, even if it's cleaner. Any choice that gets it to four hours is
right, even if it's ugly.

**The target user is Keith and his friends.** This is not a product. It is not a
content marketplace. It is not a SaaS. It is not a multi-author authoring tool. It
is a thing Keith plays with his friends. Scope accordingly.

### Implications

- **Onboarding ergonomics don't matter.** Keith is the only author. The schema can be
  whatever lets Keith move fast.
- **Documentation for others doesn't matter.** Inline YAML comments for future-Keith
  are enough.
- **Tooling investment has to pay back for one person.** UIs are usually overbuilt.
  Text files in `$EDITOR` are usually fine.
- **Validators and OTEL matter *more*, not less.** They're the automated review loop
  that replaces the team Keith doesn't have.

## 3. What's Wrong with ADR-072's 2-Axis Model

ADR-072 proposed `mechanics × milieu` as the decomposition. The Yakuza stress test
breaks it:

| Setting          | System    | Milieu                         |
|------------------|-----------|--------------------------------|
| Boardwalk Empire | gangster  | jazz_age ✓                     |
| Yakuza (Kiryu)   | gangster  | ??? (`showa_tokyo`?)           |
| The Godfather    | gangster  | ??? (`sicilian_midcentury`?)   |
| Breaking Bad     | gangster  | ??? (`contemporary_southwest`?) |
| Blade Runner     | noir      | ??? (`cyberpunk_la`?)          |

Every new gangster setting demands a brand-new milieu that shares *nothing* with the
others. The milieu layer has zero reuse — which means the decomposition has failed at
its one job.

**The underlying problem:** "Milieu" conflates three things that vary independently
in real source material:

- **Period** (tech level, clothing, transport, economics)
- **Location** (cultures, languages, geography, cuisine)
- **Tone** (noir, comedic, mythic, grimdark, stylized_action)

Noir isn't a place or a time — it's a mode. Blade Runner, Chinatown, and Altered
Carbon share tone and prose conventions but zero location or period. Any decomposition
that can't represent *"noir applied to cyberpunk Tokyo 2049"* is missing an axis.

## 4. The Axis Exploration (decomposition options)

We worked through four variants. Recording all of them so future-Keith sees the trade
space, not just the chosen answer.

### Option A — ADR-072 as written (2 axes: mechanics × milieu)
- **Yakuza test:** ❌ Fails (no milieu reuse)
- **Verdict:** Under-scoped.

### Option B — 4 axes: mechanics × period × location × tone
- **Yakuza test:** ✅ `gangster + late_showa + japan + stylized_action`
- **Pros:** Maximum combinatorial reuse. Noir-across-periods works.
- **Cons:** 4D mental model. Multi-source assembly for visuals/audio. Composition
  validator has to check compatibility across more pairs.

### Option C — 3 axes: mechanics × setting × tone (period+location merged)
- **Yakuza test:** ✅ `gangster + showa_japan + stylized_action`
- **Pros:** Tone is the highest-reuse axis and pays for itself immediately. Settings
  stay concrete as single units.
- **Cons:** `jazz_age_paris` still duplicates tech/economics with
  `jazz_age_american_northeast`. Settings remain mini-monoliths.

### Option D — ADR-072 + tone (mechanics × milieu × tone)
- **Yakuza test:** ✅ Passes, but still needs a new `showa_japan` milieu.
- **Pros:** Smallest change to existing plan. Tone is reusable.
- **Cons:** Doesn't split period from location.

**Leaning:** Some variant of C or D. The important thing is that **tone is a
first-class axis** regardless of how period and location are handled. Tone gives
the biggest narrative payoff per content dollar — changing only the tone file should
change everything about how the game feels (D&D Heroic → Dark Souls is one-axis
swap).

### Lap 2 refinement — Option E + Concept Drops

After a structured brainstorm round where the criterion was reframed from "cleanest
decomposition" to **"maximum disparate-element injection surface for forced
conceptual blending"** (see §7 for why this criterion is load-bearing), the
selection landed on a hybrid:

- **Structural scaffold: Option E (hybrid branching).** Earth branch:
  `mechanics × period × region × tone`. Realm branch: `mechanics × realm × tone`.
  Mechanics and tone live outside both branches so they reuse across earth and
  realm. This handles the runtime plumbing and all the known stress tests
  (Yakuza, Britain, Brontë-cozy, Dresden, Dark Souls vs. D&D).
- **Pynchon layer: Concept drops (new).** An open-ended `concepts/` library
  where each concept is a small, authored, reusable element (`nikola_tesla`,
  `1893_worlds_fair`, `anarchist_bombings`, `jazz_trumpets`). A pack.yaml lists
  the structural axes plus an arbitrarily-long `concepts:` array. The concept
  layer is where disparate elements go in with zero ceremony and no fixed
  ontology. See §6a.

This hybrid beat pure Option E because Option E alone still forced Keith to
categorize every new element into a fixed axis — friction against the exact
technique (§7) that the project depends on.

## 5. The Real vs Fantasy Geography Split (Keith's insight)

Geography has two fundamentally different modes:

| Type                | Ground truth      | Period coupling | Author's job           |
|---------------------|-------------------|-----------------|------------------------|
| **Real geography**  | Earth's history   | Tight           | Constrain model recall |
| **Fantasy realms**  | Author's canon    | None            | Worldbuild from scratch |

These are different enough that forcing them into one axis called "location" will
always feel wrong for one of them. Recommended: **two branches, not one axis.**

### Proposed shape

```
sidequest-content/
  systems/                    # Mechanics (authored, one-time per system)
    gangster/
    noir_detective/
    gunslinger/
    heist/
    dungeon_crawl/

  tones/                      # Tonal filters (small, high-reuse)
    noir/
    grimdark/
    heroic/
    comedic/
    stylized_action/
    operatic_tragedy/

  earth_regions/              # Real-world locations as PROMPT CONTRACTS (tiny)
    american_northeast/
    japan/
    american_frontier/
    sicily/

  earth_periods/              # Real-world periods as PROMPT CONTRACTS (tiny)
    prohibition_1920s/
    late_showa_1980s/
    frontier_1870s/
    cyberpunk_2049/

  realms/                     # Fantasy worlds as AUTHORED CANON (larger)
    middle_earth/
    lordran/
    spelljammer/

  concepts/                   # Pynchon layer — open set, no fixed ontology
    nikola_tesla/             # historical figure
    1893_worlds_fair/         # historical event
    anarchist_bombings/       # historical phenomenon
    jazz_trumpets/            # thematic motif
    the_red_baron/            # historical figure
    no_mans_land/             # thematic motif
    the_christmas_truce/      # historical event
    spiritualism/             # cultural phenomenon

  genre_packs/                # Composition manifests + generated content
    boardwalk_empire/
    gangsters_yakuza/
    deadwood/
    flying_circus/            # WWI + western_europe + aerial_chivalry
    trench_warfare/           # WWI + western_europe + industrial_futility
```

**The pack.yaml has two mutually-exclusive shapes** (earth OR realm, never both):

```yaml
# Earth-based pack
name: "Deadwood"
system: gunslinger
tone: grimdark
earth_period: frontier_1870s
earth_region: american_frontier
concepts:
  - the_telegraph_arriving
  - gold_rush_economy
  - indigenous_displacement
  - saloon_journalism
```

```yaml
# Fantasy pack
name: "Caverns and Claudes"
system: dungeon_crawl
tone: heroic
realm: generic_high_fantasy
concepts:
  - the_dungeon_as_resume
  - adventurers_guild_bureaucracy
  - magic_item_economy
```

```yaml
# Same period + region, different pack — made possible by tone + concepts
name: "Flying Circus"
system: air_combat
tone: aerial_chivalry
earth_period: wwi
earth_region: western_europe
concepts:
  - the_red_baron
  - the_ace_code
  - silk_scarves_and_superstitions
  - sopwith_camel
  - balloon_busting
```

```yaml
name: "Trench Warfare"
system: attrition_survival
tone: industrial_futility
earth_period: wwi
earth_region: western_europe
concepts:
  - gas_attacks
  - no_mans_land
  - shell_shock
  - the_christmas_truce
  - trench_rats
```

**Optional escape valve** for urban fantasy / historical fantasy:
`realm_overlay:` field on earth packs that adds canonical supernatural additions on
top of earth content. Mostly unused; exists for Dresden Files / Harry Potter cases.

## 6. Earth-as-Prompt-Contract (the architectural key)

This is the most important idea in this document.

**The LLM already knows Chicago 1925.** It has ingested Sinclair, Capone biographies,
WPA guides, Hammett, Algren, the Tribune archives, the Untouchables, Boardwalk Empire,
*and* actual street-level geography. Writing a content-heavy `earth_regions/chicago/`
file is a waste — the model will do it better than Keith can.

The earth branch's files aren't an encyclopedia. They are a **prompt contract**: a
list of deliberate constraints on what the model is allowed to freely recall.

### File shape for earth regions/periods

```
earth_regions/american_frontier/
  anchors.yaml            # 5-20 non-negotiable facts the narrator MUST respect
  deviations.yaml         # deliberate departures from real history for flavor
  hotspots.yaml           # 10-30 POIs with campaign framing (not descriptions)
  sensory_palette.yaml    # sights/sounds/smells to lean on
  name_generators/        # name corpora with period weighting
  refusals.yaml           # things the narrator should NOT invent
  research_hints.yaml     # memory probes — names for the model to reach for
```

Each file is **small**. `earth_regions/japan/` might be 150 lines of YAML total.
The model does the heavy lifting.

### Example — earth_regions/japan/

- **anchors.yaml:** "Yakuza operate semi-openly until 1992." "Foreign presence is
  limited and noticeable." "Police are aware but non-confrontational in this era."
- **sensory_palette.yaml:** "Neon reflections on wet pavement in Kabukicho." "Vending
  machines humming on empty streets." "The smell of yakitori smoke."
- **refusals.yaml:** "Don't invent fake Japanese — use real words or skip."
- **research_hints.yaml:** "Yamaguchi-gumi." "Shinjuku." "Kabukicho." "Bubble economy."

### Why this works

This is **retrieval-augmented generation where the retrieval source is the model's
own parameters.** The YAML isn't data — it's *attention guidance*. Keith is telling
the model "you already know this; here are the hooks to pull the right memories
forward."

This is a genuinely different paradigm from document-grounded RAG. It's uniquely
available to an LLM-as-game-engine architecture, and it's the reason the Saturday
Test is achievable at all.

### Authoring cost asymmetry

- **Earth region (japan):** ~150 lines of YAML. One evening.
- **Fantasy realm (middle_earth):** Thousands of lines. Canon bible. Weeks.

This asymmetry is why the two branches deserve different schemas, different
validators, and different narrator prompt templates.

### Narrator prompt shapes (different per branch)

- **Earth pack prompt:** *"You are running a campaign set in [period] [region]. You
  know this setting well from your training — lean on that knowledge, but honor the
  anchors and deviations below."*
- **Realm pack prompt:** *"Here is everything about this world. Do not invent details
  not supported by this document."*

These are opposite narrator instructions and only make sense if the two branches are
architecturally distinct.

## 6a. The Concept Layer (the Pynchon layer)

The structural scaffold in §4-6 handles *runtime plumbing* — mechanics definitions,
tonal filters, earth prompt contracts, realm canon bibles. All of that exists so
the narrator, NPC generator, and combat engine know where to find what they need
at generation time.

But the structural scaffold alone can't deliver the project's aesthetic signature:
**Pynchon-esque productive blending of disparate conceptual elements.** Fixed axes
force Keith to categorize every new element ("is Nikola Tesla a period thing or a
location thing?") when what he actually wants is to *drop elements in without
categorizing them* and let the frictions between them shape the pack. That's the
forced-blending technique (§7) applied at the pack-composition level.

The concept layer is the open-ended library where those droppable elements live.

### What a concept is

A concept is a small, authored, reusable element with its own self-contained
content. It has no fixed category. It might be:

- A **historical figure** (`nikola_tesla`, `ida_b_wells`, `the_red_baron`)
- A **historical event** (`1893_worlds_fair`, `the_christmas_truce`, `the_great_smog`)
- A **historical phenomenon** (`anarchist_bombings`, `spiritualism`, `the_great_migration`)
- A **thematic motif** (`jazz_trumpets`, `no_mans_land`, `missing_persons_bureau`)
- A **cultural practice** (`black_bottom_dance`, `silk_scarves_and_superstitions`)
- A **technology or artifact** (`radio_pirates`, `pneumatic_tubes`, `sopwith_camel`)
- A **social institution** (`adventurers_guild_bureaucracy`, `the_molly_maguires`)

The list of possible categories is open. New concept types can be added whenever
Keith has a new idea to drop into a pack. The schema does not attempt to enumerate
them.

### What a concept contributes

Each concept is a bag of **append-only contributions** to well-defined subsystem
namespaces. A concept can contain any of the following, all optional:

```yaml
# concepts/nikola_tesla/concept.yaml
name: "Nikola Tesla"
type: historical_figure
scale: global_presence      # hints at how widely the concept affects the pack

anchors:
  # Non-negotiable facts the narrator MUST respect if this concept is in play
  - "In the 1920s Tesla is alive, elderly, and largely forgotten."
  - "He lives in the New Yorker Hotel and feeds pigeons."
  - "His lab notebooks are rumor; his patents are weapons."

refusals:
  # Things the narrator must NOT do with this concept
  - "Never give Tesla a romantic subplot. He is chaste to an almost religious degree."
  - "Don't make him a villain. He is strange, not evil."

attractor_blocklist:
  # Specific overused defaults to route around for this concept
  - "The mad scientist rival (Edison is too obvious)"
  - "Death rays (historically inaccurate and boring)"
  - "Naming any assistant 'Kael'"

research_hints:
  # Memory probes — names for the model to reach for from its own training
  - "Wardenclyffe"
  - "The New Yorker Hotel"
  - "Pigeon #5"
  - "Westinghouse"

inspiration_refs:
  # Source material to steer toward
  - "The Prestige (Bowie's Tesla, not Jackman's)"
  - "Tesla: Inventor of the Modern"
  - "The Invention of Morel (for the mad-science tone)"

anti_inspiration_refs:
  # Source material to steer AWAY from
  - "Any pop-science 'mad genius' framing"
  - "The 'Tesla vs Edison' internet discourse"
```

That's the whole schema. 30-60 lines per concept, authored once, reusable forever.

### The no-connection-seeds rule (important)

**An earlier version of this design proposed `connection_seeds`** — a mechanism
where each concept would declare "things to notice when you see this other concept
in the room." That idea was removed because it is self-defeating: *pre-authoring
connections between concepts is done by the same cliché-engine that the whole
architecture is designed to route around*. If Keith (or Claude) sits down to write
"when Tesla and the 1893 World's Fair appear together, foreground the AC lighting
demo," that is *literally* the Wikipedia-known connection. It is the most obvious
possible pairing. Pre-authored connections produce cliché connections. The whole
point is lost.

**The correct mechanism is that blending happens at generation time, driven by the
sheer co-presence of whatever concepts Keith dropped into the pack.** When the
pack roller sees `nikola_tesla + jazz_trumpets + anarchist_bombings + missing_persons_bureau`
all in the same pack.yaml, the prompt it builds looks something like:

> "You are generating factions, NPCs, and hotspots for a pack that has committed
> to the following as simultaneously-present concerns: [all concept payloads
> inlined, in order]. Your job is to find *non-obvious* connections between these
> elements that can structure the pack. Avoid the most direct or Wikipedia-like
> linkages. Reach for the oblique, the contingent, the historically plausible but
> rarely noticed. Surface at least one unexpected connection per pair that
> wouldn't appear in the first page of a search engine result."

The generator has to synthesize *fresh, every time*, under the pressure of all
those concepts coexisting. No lookup. No shortcut. That is how the Pynchon move
is actually produced — by denying the generator both the cliché path *and* the
pre-authored path, leaving only the synthesis path.

### How concepts compose into packs

A pack.yaml's `concepts:` array is just a list of refs. The loader resolves each
ref, collects the append-only contributions into the appropriate subsystem
namespaces, and hands the blended assembly to the pack roller:

```yaml
name: "The Dynamo and the Tommy Gun"
system: gangster
tone: conspiratorial_sprawl
earth_period: prohibition_1920s
earth_region: american_midwest
concepts:
  - nikola_tesla
  - 1893_worlds_fair
  - anarchist_bombings
  - jazz_trumpets
  - spiritualism
  - radio_pirates
  - missing_persons_bureau
  - black_bottom_dance
```

At generation time, the resolved concept bundle is inlined into the pack roller
prompt *alongside* the structural scaffold. The model sees eight historically
grounded, stylistically disparate elements and has to build factions, NPCs, and
hotspots that honor all of them. It cannot retreat to a default gangster pack
because none of the defaults connect Tesla to jazz trumpets to radio piracy. It
has to think.

### The composition contract (append-only, not merge-based)

This is how the concept layer satisfies the no-merge rule without losing
flexibility. Contributions from concepts **accumulate** within subsystem
namespaces; they never override each other.

- If `nikola_tesla` contributes 4 research_hints and `1893_worlds_fair` contributes
  6 research_hints, the pack's research_hints list is *10 entries long*, not
  "whichever one won."
- If two concepts both declare the same attractor in their `attractor_blocklist`,
  the entry appears once (set semantics) but neither overrides the other.
- Structural axes (mechanics, tone, earth/realm) remain strict single-source.
  Only the concept layer is append-based, and only within the well-defined
  namespaces listed above.

This preserves the no-silent-fallbacks / no-merge principle at the structural
layer while giving the concept layer the openness it needs for Pynchon-mode.

### Concepts and attractors

Concepts can carry their own `attractor_blocklist` entries because specific
concepts tend to trigger specific attractors. Tesla triggers the "mad scientist
rival Edison" attractor. Noir detectives trigger the "whiskey problem" attractor.
Dwarves trigger the "Toggle Copperjaw" naming attractor. Each concept's blocklist
is small and targeted at the attractors Keith has *actually observed* Claude
reaching for when that concept is in the room.

This is complementary to mechanical substitution (see §7) — some attractors
(names especially) are strong enough that even blocklist entries aren't sufficient
and need to be routed through mechanical generators. The concept layer can point
at mechanical generators via its contributions; that's a forward-looking feature
and not required for the first version of the system.

### Authoring cost

Concepts are cheap to write. A single concept file is 30-60 lines, takes 15-30
minutes to draft, and is reusable across any pack that wants to include the
element. The library compounds: every new concept Keith authors becomes available
for every future pack. Over time, the `concepts/` directory becomes the real
creative asset — a library of specific, grounded, reusable elements that can be
combined into configurations the model can't anticipate.

### Authoring discipline: write essence, not expression

**A concept file should be written at the level of its essence, not at the
level of how it gets expressed in any particular pack.** The blend at
generation time — tone plus co-present concepts — is what renders a concept
into a specific expression. Pre-authoring the expression costs flexibility
and produces cliché.

Concrete example (from §14b): "Liberty" has different valences in the French
Revolution (collective, `liberté/égalité/fraternité`, republican virtue) and
the American Revolution (individual, contractual, life/liberty/pursuit of
happiness). Do *not* fork the concept into `liberty_french` and
`liberty_american`. Write one `enlightenment_liberty` that describes the
essence — *"the rejection of inherited or divinely-ordained authority,
variably expressed as individual rights or collective virtue depending on
intellectual heritage"* — and let the pack's tone and co-present concepts
produce the correct valence at generation time. Drop it into a pack with
`paranoid_terror + committee_of_public_safety` and the French valence
emerges. Drop it into a pack with `founding_earnest + continental_congress`
and the American valence emerges. Same file. Different blend. Different
result.

This is the same principle as the no-connection-seeds rule, applied at a
finer grain: **pre-authoring flattens; blending produces.** Whenever you're
tempted to hard-code a specific expression into a concept file, ask whether
the co-presence of other elements in a real pack would produce that
expression naturally. If yes, don't author it — trust the blend. If no,
the concept is probably too abstract and needs to be written with more
concrete essence, not more concrete expression.

## 7. Attractors as the Real Adversary (not tropes)

**Important correction:** This section is not about "avoiding clichés" in the broad
sense. That framing is wrong and would flatten the grounded-ness that makes genre
fiction readable. The real target is *attractors* — specific, reliably-observed
default behaviors the model reaches for when asked to generate content in a given
register — not *tropes*, which are load-bearing for narrative legibility.

### Tropes vs. attractors

| | Trope | Attractor |
|---|---|---|
| **What it is** | A recognizable structural beat that helps the audience orient | A specific over-used default that no longer carries information |
| **Role** | Narrative grammar — the thing that makes a genre readable | Noise — the thing that makes a genre feel stale |
| **Examples** | "The mentor dies in act two" / "The heist crew assembles before the job" / "The noir detective has one unbreakable rule" | "His name is Kael" / "Toggle Copperjaw" / "She has a whiskey problem and a dead partner" |
| **Treatment** | **Preserve.** Tropes do real work and players need them to orient. | **Route around.** Blending and (for known-strong cases) mechanical substitution. |

**Gangster pack should still have gangster tropes** — loyalty codes, territorial
disputes, the promising newcomer who gets in over his head, betrayal from an
unexpected direction. Those are how the audience knows what kind of story they're
in. What the pack should *not* have is the five specific guys Claude reaches for
when asked to name a gangster, or the three specific opening beats Claude always
writes, or the stock "grizzled lieutenant who secretly resents the new boss" *in
exactly the same phrasing Claude produces every time.*

The distinction is whether the specificity still carries information or whether
it's become so automatic that it carries nothing. A trope tells the audience
"this is how the genre works." An attractor tells the audience "the model wrote
this."

### The primary technique: forced conceptual blending

**This is the cliché-breaker that actually works**, validated empirically by Keith
on Claude over many sessions. The technique:

> Pile on so many specific, disparate constraints that the cliché paths aren't
> available anymore. The default solution space gets closed off by the incompatibility
> of the combined requirements, and the model has to actually synthesize instead of
> retrieve.

**Why this works:** Telling the model *"don't use the whiskey cliché"* requires the
model to think about whiskey in order to refuse it — the instruction reaches *toward*
the cliché. Forcing *"noir detective in 1890s Tehran investigating the disappearance
of a Qajar court poet during a cholera outbreak"* closes the Chandler context entirely.
None of the stock noir material applies. The model has to think fresh.

**Why the pitch is the primary fuel for this.** A friend's weird, specific pitch is
already an act of forced blending. "British veterinarian + detective + small village"
is much harder to flatten to a template than "cozy mystery." The pipeline's job is
to **preserve and amplify the specificity of the pitch**, not flatten it toward the
nearest template in the library. Blending more constraints on top of the pitch is
the main work of the pack generator.

**Concrete blending moves the generator should make:**

- **Combine axes that don't usually travel together.** `gangster + eastern_europe_contemporary + mournful_tone + anti-mob-family-dynasty` beats `gangster + default defaults`.
- **Inject an unexpected constraint.** "One major faction is a women's collective that came out of the bubble-era hostess industry." Specificity the model wouldn't volunteer.
- **Borrow a technique from a different genre.** "Run this noir pack with pacing lifted from a wuxia serial — revelations should arrive in coordinated setpieces rather than gradual disclosure."
- **Invert a core assumption.** "The detective is happily married, sober, and well-adjusted. The instability comes from the case, not the investigator."
- **Pull from a reference the model wouldn't reach for.** "Treat this village mystery as if Iris Murdoch and Donna Leon co-wrote it, not Christie or Midsomer."

### Supporting technique: attractor blocklists

Blocklists are a **safety net**, not the main event. They catch the drift *after*
blending has done its work, for cases where the model still defaults to something
lazy. They target specific named attractors, not clichés-in-general.

- **Per-system attractor files.** `systems/noir_detective/attractors.yaml` lists
  the specific defaults Claude reaches for in that register: whiskey problem,
  dead partner, femme fatale, rain on venetian blinds. Same file structure for
  every system.
- **Per-concept attractor lists.** Each concept file (§6a) can carry its own
  `attractor_blocklist` entries for attractors that are specific to that concept
  (e.g., Tesla triggers the "mad scientist rival Edison" attractor).
- **Anti-examples beat negative instructions.** Instead of "no dead partner,"
  ship *"here are three detective backgrounds where the investigator's family is
  alive and present, and that changes how they approach the case — [examples]."*
  Positive substitutes reshape the probability surface more effectively than
  negative prohibitions.
- **Forced diversity at generation.** Roll multiple drafts, pick the least
  attractor-laden one by embedding distance from a reference "generic [genre]"
  corpus. Expensive in tokens, cheap in authoring.

### Second technique (forward-looking): mechanical substitution

**Some attractors are strong enough that blocklists and blending alone cannot
shake them loose.** The canonical example: Claude reliably picks the name "Kael"
for fantasy characters regardless of what context is set around it. Telling
Claude "don't use Kael" requires Claude to think about Kael to avoid it — the
instruction reaches *toward* the attractor — and blending doesn't help because
the attractor survives almost any amount of conceptual weirdness surrounding
the naming decision.

The solution is **mechanical substitution**: remove the model from the decision
point entirely. The conlang / corpus / Markov generator in `sq-world-builder`
already does this for fantasy names — it picks the name from a different
probability surface and hands it to Claude as a fact, so Claude never gets the
chance to Kael-default.

This is a different technique from blending. Blending operates at the *synthesis*
stage, reshaping the prompt so attractors aren't reachable. Mechanical
substitution operates at *specific known decision points* where the model has
proven bias that blending cannot dislodge. Both are needed in a complete
anti-attractor architecture.

**Scope:** Mechanical substitution is a forward-looking feature for this PRD.
The name generator already exists. Other candidate decision points (default NPC
professions, default physical descriptions, default faction names, default
opening beats) would need their own generators built one at a time as attractors
are observed and cataloged. Not required for the first version of the system,
but worth knowing about as a second axis of attack.

### Why this matters for the pitch-to-parameters step

The implication for `/sq-world-builder` is strong: the skill should treat the
pitch as *raw material to blend further*, not as a classification target. Its job
isn't to match the pitch to the closest template; its job is to preserve the
pitch's specificity and add 3-5 more disparate constraints on top, then hand the
composite to the pack roller. A pitch that arrives with 2 constraints should leave
with 5-7. That's the mechanism that produces fresh content.

### Surprise budget (a tuning knob)

A dial from "play it straight" to "the werewolves are a metaphor for the housing
market." Different campaigns want different positions. Concrete behavior:

- **Low budget (0.2):** Faithful Deadwood. Gem Saloon is a saloon. Swearengen runs it.
- **High budget (0.8):** Gem Saloon is a front for a timber cartel run by nuns.

Needs to be defined as an actual parameter with observable generator behavior, not a
vibe. (Open question — see §11.)

## 8. The Pack Generator is the Real Product

Not the runtime. Not the narrator. Not the content files. **The thing that takes a
pitch and produces — in hours, surprising even Keith — a playable pack.**

**The authoring interface already exists.** It is `/sq-world-builder` plus `$EDITOR`
plus the validator gauntlet. Nothing new needs to be built for UX. What needs to
change is the *prompt discipline* of the world-builder skill and the *parameters it
accepts* — it needs to be taught the new axis set, the cliché subsystem, the
surprise budget, and the summarize-at-shape-level output rule.

### Pipeline shape

```
Friend's pitch (natural language)
        ↓
  /sq-world-builder reads pitch, proposes parameters
        ↓
  Keith approves / edits parameters + concept drops
        ↓
  sq-world-builder composes refs (system + tone + earth/realm + concepts)
        ↓
  Attractor blocklists collected (system + concept-level)
        ↓
  Pack roller generates:
    - factions
    - named NPCs (routed through mechanical name generator)
    - hotspots
    - opening situation
  under blending pressure from the full concept bundle
        ↓
  Validators run (sidequest-validate + sq-audit)
        ↓
  sq-world-builder reports shape-level summary only
        ↓
  Pack sealed, ready to play
```

### Keith's role in this pipeline

- **At the start:** Hand the pitch to `/sq-world-builder` and approve or edit the
  proposed parameters — structural axes (system, tone, earth/realm refs) *and*
  the concept drops the skill proposes. Concept drops are where Keith does most
  of his steering work.
- **At the end:** Review a shape-level summary — "4 factions, themes: X Y Z,
  tone: W, one unusual element: V" — and approve or reroll. 30 seconds per pack.
- **NOT in the middle:** Keith does not read the rolled faction details, NPC
  backstories, or specific opening content. **That is the point.** Those are the
  surprises he's going to discover in play.

### sq-world-builder output discipline (the "deliberate blindness" rule)

This is a prompt discipline, not a UI. The world-builder skill, when finishing a
pack generation run, should **report shape without dumping content**.

- **Safe to report:** Faction count, hotspot count, tonal themes, system, validator
  results, cliché-filter rejection count, one-sentence "unusual element" teaser.
- **Not safe to report:** Faction names and goals, NPC names and backstories,
  opening situation, specific hotspot framings.

The generated files exist on disk as normal YAML. Keith *could* open them — nothing
stops him. The discipline is about what the skill *tells him in chat*, because the
chat is where the spoiler damage happens. Once the game starts, the runtime's GM
panel is fine — the surprise has already happened by then.

**Reference point:** Dwarf Fortress world-gen is the closest existing pattern. Tarn
Adams runs the generator, watches the log scroll, then plays the world he didn't
author. Same shape, no new software required.

## 9. Parameter Set Summary (the smallest viable decomposition)

Working backward from "what does the pack generator actually need":

| Parameter              | Role                                      | Authoring cost          |
|------------------------|-------------------------------------------|-------------------------|
| **System**              | Mechanics (stats, combat, progression)                  | One-time per system     |
| **Tone**                | Tonal filter (noir, grimdark, heroic, warmth_under_shadow) | Small, high reuse       |
| **Earth period**        | Real-world time prompt contract                         | ~80 lines per period    |
| **Earth region**        | Real-world place prompt contract                        | ~150 lines per region   |
| **Realm** (alternative) | Fantasy canon bible (mutually exclusive with earth)     | Large, realm-dependent  |
| **Concepts**            | Open-ended disparate-element drops (§6a)                | 30-60 lines per concept |
| **Attractor blocklist** | Per-system + per-concept attractor entries              | Small                   |
| **Surprise budget**     | Single generator tuning knob                            | One number              |

Eight parameters. Most are tiny and reusable. Total per-pack authoring cost is
maybe an hour of Keith composing refs and dropping concepts, and the generator
does the rest. The concept layer is where most of Keith's creative steering
energy goes — the other seven are structural scaffolding.

## 10. Impact on Epic 32

Epic 32 as written is about decomposing existing monolithic packs into cleaner
library layers under ADR-072's 2-axis model. That's still useful — you can't
generate new packs from libraries that don't exist — but **the endgame has shifted**
and epic 32 needs a rewrite after this brainstorm settles.

### What stays

- Schema extension to pack.yaml (story 32-1) — still needed, but with more fields
  than just `system_ref` and `milieu_ref`.
- Three-path loader (story 32-2) — shape changes but the concept holds.
- Layer boundary validator (story 32-3) — more important than ever as the automated
  review loop.
- Extracting systems from existing packs (32-5 and its siblings) — still needed.
- Legacy loader fallback removal (32-18) — still needed as the cleanup gate.

### What changes

- Milieu extraction stories (32-4, etc.) become **three separate extractions** —
  period, region (or realm), and tone. ADR-072's single `jazz_age` milieu splits
  into `earth_periods/prohibition_1920s/ + earth_regions/american_northeast/ +
  tones/noir/`.
- World-level override stripping (32-19) becomes more aggressive — worlds become
  *just* geography and instances, not lore.
- The archetype/persona split needs a third piece: **period dressing** and **tonal
  rendering**. Or collapsed back into a simpler two-piece split if we find the
  four-piece split too much.

### What's new (probably a follow-up epic 33)

- **`concepts/` library** — the entire concept layer from §6a. New top-level
  directory. Schema for `concept.yaml`. Append-only contribution mechanism.
  First handful of concepts extracted from the existing packs as anchors
  (`nikola_tesla`, `the_red_baron`, `no_mans_land`, etc.).
- **Attractor blocklist subsystem** — per-system `attractors.yaml` files, per-concept
  attractor entries, anti-example corpora. Not "cliché blocklists" — specifically
  named attractors that have been observed.
- **Pack roller** — the generator that takes structural refs + concept drops and
  produces factions, NPCs, hotspots, and openings under blending pressure.
- **Surprise budget** as a real parameter with observable generator behavior.
- **`/sq-world-builder` prompt discipline update** — accept the new parameter
  set including concept drops, apply attractor filters, hand off to pack roller,
  report shape-level summary instead of full content dump.
- **`/sq-world-builder` pitch intake** — skill accepts a natural-language pitch,
  proposes structural parameters *and concept drops*, surfaces them for Keith
  to approve or edit. Concept proposal is where the skill does most of its
  creative work.
- **Mechanical substitution extension (forward-looking)** — the existing conlang
  name generator integrates as the first instance of the mechanical substitution
  pattern. Other attractor decision points (faction names, default NPC
  professions, stock physical descriptions) get their own generators as they
  are observed and cataloged.

**No new UI.** Authoring is text files + existing skill. The build log is whatever
the skill prints to chat, constrained by the output discipline rule in §8.

Epic 32 is the **prerequisite** for epic 33. Epic 33 is the thing that delivers the
Saturday Test.

## 11. Open Questions (next threads to pull)

### Closed by Lap 2

- ~~Period+location merge vs. split~~ → **split**. WWI and Britain both demonstrate
  the need for independent period and region axes.
- ~~Option B vs C vs D vs E~~ → **Option E + concept drops**. Hybrid branching
  scaffold with open concept layer on top.
- ~~connection_seeds mechanism~~ → **removed**. Pre-authoring connections is
  self-defeating; blending happens at generation time from sheer co-presence.
- ~~"Cliché" as blanket target~~ → **refined to attractors**. Tropes are preserved;
  specific named attractors are routed around.

### Still open

1. **Concept library seeding strategy.** How many concepts does the library need
   before the first real pack is buildable? Start with 20? 50? Extract from
   existing packs, or author fresh against a target pack? This decides the ramp
   curve for epic 33.

2. **One real concept file, written end-to-end.** `concepts/nikola_tesla/` or
   `concepts/the_red_baron/` are strong candidates — historically rich, well-
   understood by the model, Pynchon-adjacent. If a single concept feels right
   at 30-60 lines, the shape is validated. If it wants to be 300 lines, the
   schema is wrong.

3. **One real `earth_regions/` file set, written end-to-end.** Pick
   `american_frontier`, `japan`, or `western_europe` (for the WWI stress test)
   and write the actual YAML. Validates the prompt-contract shape. If the files
   feel right at 150 lines, we're on the right track.

4. **One real `tones/` file set, written end-to-end.** `warmth_under_shadow`
   (for Brontë-cozy) or `industrial_futility` (for Trench Warfare) are strong
   candidates because they're hybrid or unusual tones that would stress-test
   the shape hardest. A pure `noir` tone would be too easy and wouldn't
   validate the schema under load.

5. **Surprise budget as an actual parameter.** What does budget=0.2 vs.
   budget=0.8 actually change in the generator? Name two concrete differences
   per level or the knob is vapor.

6. **Concept layer validator rules.** What does `sidequest-validate` check on
   a concept file? Required fields (name, type), optional fields (anchors,
   refusals, etc.), type enum enforcement (or open), warning on concepts with
   zero contributions to any namespace. Needs a concrete spec.

7. **What NOT to report from sq-world-builder at end-of-generation.** Full
   inventory of safe-to-report vs. spoiler-surface fields for the skill's
   summary output. This is the same spoiler-protection problem Keith has
   already partially solved for content repos — reuse that pattern.

8. **Earth vs realm count in the roadmap.** If it's 10 earth + 0 realm, realms
   are YAGNI until later and the branch can be stubbed. If it's 8 earth + 3
   realm, both branches are load-bearing.

9. **Narrator prompt templates for earth vs. realm packs, side by side.**
   Validates the architectural split at the level that actually matters — what
   the LLM sees. Also needs a variant for concept-heavy packs to see how
   concept payloads flow into the prompt.

10. **How tone interacts with earth regions.** "Dramatized vs. grounded Chicago"
    is a tone decision that has to reach into earth prompt assembly. Is that a
    clean cross-axis reference, or does it contaminate the no-merge rule?

11. **Does the archetype split go 2, 3, or 4 ways?** Mechanical archetype,
    cultural persona, period dressing, tonal rendering — or simpler? This is
    the hottest code path for the NPC generator, and concepts add a fifth
    possible contributor (concept-level archetype overrides).

12. **Pitch-to-parameters flow.** When `/sq-world-builder` reads a pitch, how
    does it propose concept drops? Does it search the existing concept library
    for matches? Does it suggest new concepts for Keith to author? Does it
    trust the pitch to name them? This is the load-bearing entry point for the
    whole pipeline and deserves its own detailed design pass.

13. **Mechanical substitution attractor catalog.** What other attractors
    besides names need mechanical routing? Candidate decision points: faction
    names, default NPC professions, default physical descriptions, default
    opening beats. Needs empirical observation — hit an attractor enough times
    during playtest, then build a generator for it.

14. **System abstraction level — one-with-parameters or many-distinct?**
    Surfaced by §14b (Late 18th C. Revolutions). Options: (a) separate
    `revolutionary_intrigue` and `frontier_insurrection` systems, justified by
    different session hot loops (denunciation politics vs. coalition
    warfighting); or (b) one `revolutionary_politics` system with parameters
    (paranoid vs. coalitional, centralized vs. distributed, purge-economy vs.
    coalition-economy) that can serve every future revolutionary pack with
    just parameter swaps and new concept drops. The parameterized version is
    more Pynchon-mode-friendly because future packs get cheaper; the
    distinct-systems version is more mechanically honest because the hot
    loops genuinely differ. **Resolve empirically:** write the first system
    file and see whether the parameter space holds together. Not a PRD
    decision.

## 12. What This Document Is NOT

- Not an ADR. ADRs are decisions. This is direction.
- Not a spec. Specs are implementable. This is a target to aim at.
- Not a replacement for ADR-072. ADR-072 should be amended or superseded once this
  direction firms up — probably with a new ADR that cites this PRD.
- Not exhaustive. Several open questions in §11 need real work before the full
  picture is clear.
- Not final. Expect this document to be revised as the open questions close.
- **Not a product plan.** Authoring is `/sq-world-builder` + `$EDITOR`. No new UIs,
  no onboarding flows, no tutorial modes. Anything that smells like "product" is
  overscoping — this is for Keith and his friends.

## 13. The Nerd Force Field (onboarding, not architecture)

**Keith's target audience includes at least one person with a well-developed nerd
immune response.** Keith's girlfriend has spent years adjacent to Keith and her
sons doing nerd stuff. The accumulated exposure has produced an identity-level
category filter: anything that reads as "the hobby the guys do" triggers a refusal
reflex that operates *before* content evaluation.

### Why this matters for the PRD

None of the architectural work in §§1-12 addresses this. A technically perfect pack
that is presented as *"hey, want to roleplay?"* has already lost, because "roleplay"
is pre-filed under the nerd category and the filter fires on the word, not the
content.

This is a **pitch framing problem**, not an architecture problem, and it lives at a
completely different layer than the pack generator. But it's load-bearing for the
Saturday Test, so it needs to be named.

### Requirements this adds

- **The Saturday Test is really two tests.** (a) Can Keith produce a pack that would
  work. (b) Can the pack be presented in a frame that doesn't trigger the category
  filter. Passing (a) without (b) produces a beautiful unplayed pack.
- **The pitch layer sits on top of the pack layer.** What Keith says to invite
  someone into the game is *not* the same thing as what the pack contains. Framing
  matters as much as content.
- **"Do you want to roleplay" is a losing opener for nerd-allergic targets.** Better
  openers lean on adjacent categories that aren't nerd-coded:
  - *"I'm writing a story and I need you to tell me what this character would do."*
  - *"I found this cool British village thing, want to see what happens?"*
  - *"Remember [TV show she likes]? I built a version where you're one of the
    characters."*
  - The word "game" may or may not survive the filter depending on the person. Keith
    is the judge of what reads as nerd-coded to his specific target.
- **The pack's self-presentation should match the frame.** If the pitch is "an
  interactive story," the pack's opening beats should feel like the opening of a
  story she'd watch, not like character creation in D&D. This has implications for
  how chargen is framed in a cold-start session.

### Requirements this does NOT add

- No new architecture. The decomposition, the earth-as-prompt-contract, the cliché
  system, the pack roller — all untouched.
- No new code. Pitch framing is something Keith does in conversation, not something
  the system does for him.
- No scope creep toward "onboarding flows" or "tutorial mode." Those are product
  concepts. This is a personal problem with a specific person, solved by Keith
  knowing his audience.

### Design heuristic: the category check

Before presenting any pack, Keith can mentally run this check: *"What category will
she file this under in the first 10 seconds?"* If the answer is anything nerd-coded,
the presentation needs to change — even if the content is perfect. The pack stays
the same; the wrapper changes.

## 14. Case Study: The Brontë/Britpop Girlfriend Pitch

This case is the one that cracked the whole milieu concept open, so it deserves to
be captured as a concrete worked example.

### The situation

Keith's girlfriend likes **both** Brontë (gothic, moody, restrained passion) **and**
contemporary British cozies (village mysteries, Britpop cultural wash, warm
procedurals). She is currently inside the nerd force field (§13) and has not said
yes to SideQuest. Keith is running multiple trial pitches to see what sticks. One
of them: *"a British village veterinarian who solves crimes with a detective."*

### Why this pitch is a perfect architectural stress test

The existing Victoria pack is set up for `blackthorn_moor` — a Yorkshire gothic
country house mystery with Brontë / Wilkie Collins / Turn of the Screw DNA. Under
the current monolithic structure, Victoria bundles:

- **Period:** 1840s-1880s (strict Victorian)
- **Location:** English country house / moors
- **Tone:** Gothic, simmering tension, restrained passion, moral reckoning
- **Premise shape:** Locked-room, reading-of-the-will, secrets-in-silk

The cozy-vet pitch needs some of this (Englishness, class-awareness, restraint,
a mystery at the core) and conflicts with other parts (period is wrong, tone is
at least partially wrong, premise shape is episodic not locked-room). **And
critically, she likes Brontë *too*, which means the right pitch isn't "pure cozy"
— it's something that sits in the overlap between Brontë warmth-under-menace and
modern village procedural.** That register is its own thing: a village where the
warmth is real, the shadows are real, the darkness isn't a monster-of-the-week,
and the vet has a complicated inner life.

### Under current ADR-003 (monoliths)
Build an entirely new genre pack. Zero reuse from Victoria even though 40% applies.
**Saturday test: ❌ fails hard.**

### Under ADR-072 (mechanics × milieu)
Marginal improvement. New milieu duplicates most of Victoria's content because the
tone is different. **Saturday test: ❌ fails for the same reason Yakuza failed.**

### Under the new decomposition (system × tone × earth_period × earth_region)

```yaml
# genre_packs/the_village_and_the_vet/pack.yaml
name: "The Village and the Vet"
system: cozy_procedural        # episodic, low-lethality, relationship-weighted
tone: warmth_under_shadow      # the Brontë/cozy overlap — NOT pure cozy, NOT pure gothic
earth_period: postwar_britain  # or contemporary — Keith decides based on which
                               # visual palette lands
earth_region: english_village  # Cotswolds / Dales / West Country
concepts:
  - veterinary_practice_rural
  - the_village_green_as_stage
  - postwar_rationing_lingering
  - church_as_civic_center
  - the_outsider_doctor_trope_subverted
  - correspondence_as_plot_device
inspirations:
  - "All Creatures Great and Small (warmth)"
  - "Father Brown (moral weight under geniality)"
  - "Grantchester (period atmosphere, layered protagonist)"
  - "Jane Eyre (emotional interiority, restraint, shadow)"
  - "Iris Murdoch village novels (psychological texture)"
anti_inspirations:
  - "Midsomer Murders (too formulaic, murder-a-week pacing)"
  - "Pure whodunit mechanics (the mystery is not the point; the people are)"
```

**Every axis is reusable.** `cozy_procedural` could run Murder She Wrote, Only
Murders, Knives Out. `warmth_under_shadow` could apply to low_fantasy or to a
post-apocalyptic pack at low surprise budget. `postwar_britain` could serve a
kitchen-sink drama or a spy thriller. `english_village` pairs with any British
period.

### What this case reveals about the decomposition

- **"Tone" is confirmed load-bearing for the second time.** Flipping tone from
  `gothic_menace` → `warmth_under_shadow` changes everything while keeping system,
  period, and region constant. This is exactly what a first-class tone axis buys.
- **Tone is not binary.** `warmth_under_shadow` is neither gothic nor cozy — it's
  a specific overlap that wouldn't exist if tones were a short enumerated list.
  This argues for tones being *authored documents* (prose style, pacing rules,
  tonal filter, mood guidance) rather than a dropdown of presets.
- **Period and location want to split, not merge, for Britain.** Britain has
  meaningfully different era-location combinations that matter: postwar village,
  Victorian country house, contemporary London, WWII coastal, Regency drawing
  room. This argues for Option B (4 axes) over Option C (merged setting) at
  least for countries with deep period variation. Japan in Yakuza only really
  needs one combination; Britain needs many.
- **The character hook is separate from the genre pack.** "Village vet and
  detective partnership" is a *starting character configuration*, not a genre
  feature. The pack provides a world where this is plausible; the chargen flow
  instantiates the specific character. Keep these layers distinct.

### What this case reveals about the girlfriend problem

- **She likes both Brontë and Britpop cozies.** That's a person with taste that
  spans registers, not someone who wants "the cozy version." Building a pure cozy
  pack would underestimate her. The right pitch is the hybrid — which is exactly
  what forced conceptual blending (§7) is designed to produce.
- **The nerd force field (§13) is still the primary obstacle.** Even a perfect
  Brontë/cozy hybrid pack fails if it's presented as "want to try my RPG." The
  framing layer is independent and has to be solved independently.
- **The right pitch phrase probably involves a show she already watches.**
  "Remember Grantchester? I made a version where you're the vet." That opens a
  door the word "roleplay" closes.

### Status

This pack does not yet exist. When the new decomposition is in place, building it
is a candidate for the **first pack built under the new model**, precisely because
it's the one with the clearest real-world stakes and the clearest anchor in Keith's
actual life. It would also be the ideal first stress test for the
`/sq-world-builder` prompt discipline update and the cliché blending technique.

## 14a. Case Study: WWI — Flying Circus vs. Trench Warfare

The single cleanest stress test for tone + system + concepts. Same period
(WWI, 1914-1918). Same region (western_europe). Same *war*. And yet two
completely different games.

| | Flying Circus | Trench Warfare |
|---|---|---|
| **System** | `air_combat` — dogfights, maneuver, individual glory | `attrition_survival` — collective endurance, incremental territory, low agency |
| **Tone** | `aerial_chivalry` — romantic, heroic, doomed elegance | `industrial_futility` — grim, absurd, gallows-humored |
| **Period** | `wwi` ← *same* | `wwi` ← *same* |
| **Region** | `western_europe` ← *same* | `western_europe` ← *same* |
| **Concepts** | `the_red_baron`, `the_ace_code`, `silk_scarves_and_superstitions`, `sopwith_camel`, `balloon_busting`, `jasta_squadrons` | `gas_attacks`, `no_mans_land`, `shell_shock`, `the_christmas_truce`, `trench_rats`, `the_great_letter_writing` |
| **Inspirations** | Snoopy vs. the Red Baron, The Blue Max, Biggles, Wings | All Quiet on the Western Front, Paths of Glory, Blackadder Goes Forth, Johnny Got His Gun |

**These are not the same game in different clothes.** They have different
mechanical scaffolds (air combat vs. attrition), different tonal filters
(romantic heroism vs. industrial despair), and different concept drops (none
overlap). The *only* things they share are the period and region scaffolds —
and those are exactly the things that should be reusable.

### Why this case is architecturally decisive

1. **Two axes (period + region) are insufficient.** Under ADR-072 or any
   axis-heavy model that puts the war into a "setting" bucket, Flying Circus
   and Trench Warfare would collide on the setting ref. The new decomposition
   separates the period/region (which they share) from the system and tone
   (which they don't), and the concept layer lets them diverge completely on
   the ground-level content.

2. **Tone alone isn't enough to distinguish them.** Even with tone as a separate
   axis, the two packs would share too much if the concept layer didn't exist.
   Flying Circus *needs* `the_red_baron` and `silk_scarves`. Trench Warfare
   *needs* `gas_attacks` and `shell_shock`. Those aren't period/region facts
   (the period and region know about both); they're *foregrounding decisions*,
   and foregrounding decisions live in the concept layer.

3. **The system axis is doing real work.** Air combat and attrition survival
   are genuinely different mechanical treatments. The narrator prompt for
   Flying Circus needs to handle dogfight choreography; the prompt for Trench
   Warfare needs to handle crushing-stasis-with-occasional-horror. This
   validates `system` as a separate axis even when period and region are
   shared.

4. **Keith can build both from one set of libraries.** Same
   `earth_periods/wwi/` file set. Same `earth_regions/western_europe/` file
   set. Same tone library (authoring `aerial_chivalry` and `industrial_futility`
   as separate tones, but they live in the same shared `tones/` directory).
   Different system files. Different concept drops. **The reuse is total
   across the shared axes and the divergence is total across the unshared
   ones.** That's the architecture working correctly.

### What this reveals that the other case studies didn't

- **Yakuza proved the `gangster` system could travel to different settings.**
  One axis of reuse (system) across different period/region combinations.
- **Britain proved period and region want to split.** Two axes of independent
  variation within a country.
- **Brontë-cozy proved tone can be an overlap document, not a preset.** One
  axis expressing a hybrid aesthetic.
- **WWI proves *the concept layer is load-bearing*.** Same period+region+tone
  scaffold could support both packs if tone were granular enough, but the
  *specific foregrounding decisions* (Red Baron vs. Gas Attacks) are what
  differentiate the games, and those live in concepts, not axes. Without the
  concept layer, both packs would produce vaguely-WWI content instead of
  specifically-Flying-Circus and specifically-Trench-Warfare content.

### Pack sketches

```yaml
# genre_packs/flying_circus/pack.yaml
name: "Flying Circus"
system: air_combat
tone: aerial_chivalry
earth_period: wwi
earth_region: western_europe
concepts:
  - the_red_baron
  - the_ace_code
  - silk_scarves_and_superstitions
  - sopwith_camel
  - balloon_busting
  - jasta_squadrons
  - the_blue_max
  - letters_home_from_the_mess
inspirations:
  - "Snoopy vs. the Red Baron (the doomed romance framing)"
  - "The Blue Max (ambition and class collision)"
  - "Biggles (unironic adventure)"
```

```yaml
# genre_packs/trench_warfare/pack.yaml
name: "Trench Warfare"
system: attrition_survival
tone: industrial_futility
earth_period: wwi
earth_region: western_europe
concepts:
  - gas_attacks
  - no_mans_land
  - shell_shock
  - the_christmas_truce
  - trench_rats
  - the_great_letter_writing
  - tunnel_warfare
  - the_lottery_of_the_whistle
inspirations:
  - "All Quiet on the Western Front (the generational grief)"
  - "Blackadder Goes Forth (gallows humor without looking away)"
  - "Paths of Glory (command malice)"
  - "Johnny Got His Gun (embodied futility)"
```

**Notice that `the_christmas_truce` appears in Trench Warfare but not Flying
Circus**, even though it happened in both contexts historically. That's a
*foregrounding* decision — Trench Warfare wants it as a concept drop because
it's one of the few moments of agency in an otherwise agency-stripped pack;
Flying Circus doesn't need it because its tone is already oriented around
individual chivalry. Two different packs, two different choices about which
historical elements to foreground, both justified by what each pack is *for*.

This is how the concept layer does its work: **Keith steers what the pack is
about not by authoring content, but by choosing which disparate elements to
put in the room together.**

## 14b. Case Study: Late 18th Century Revolutions — France vs. America

The inverse of the WWI case. WWI shares period + region and diverges on
concepts. Late 18th Century Revolutions share period and *some* concepts, but
diverge on region, tone, and system. Where WWI proves that the concept layer
enables *divergence* under a shared scaffold, this case proves that the concept
layer enables *partial sharing* across packs — and that the concept library is
a **reuse graph**, not a flat per-pack bag.

### The two packs

```yaml
# genre_packs/liberté_égalité_fraternité/pack.yaml
name: "Liberté, Égalité, Fraternité"
system: revolutionary_intrigue
tone: paranoid_terror
earth_period: late_18th_century
earth_region: france
concepts:
  # Shared with the American Revolution pack
  - enlightenment_philosophy
  - no_more_kings
  - citizen_identity
  - the_social_contract
  - republican_virtue
  # French-specific
  - the_committee_of_public_safety
  - the_guillotine
  - sans_culottes
  - thermidor
  - denunciation_as_civic_duty
  - the_cult_of_the_supreme_being
```

```yaml
# genre_packs/these_united_colonies/pack.yaml
name: "These United Colonies"
system: frontier_insurrection
tone: founding_earnest
earth_period: late_18th_century
earth_region: american_colonies
concepts:
  # Shared with the French Revolution pack
  - enlightenment_philosophy
  - no_more_kings
  - citizen_identity
  - the_social_contract
  - republican_virtue
  # American-specific
  - committees_of_correspondence
  - the_continental_congress
  - valley_forge
  - the_pamphlet_as_weapon
  - the_frontier_as_escape_valve
  - slavery_as_hypocrisy_underneath
```

### The concept library as a reuse graph

Before this case, the PRD could be read as saying "concepts are per-pack drops
and the library is just where they live." This case upgrades that: the library
is a **graph**, where some concepts connect to many packs and others connect
to one.

- **Broad concepts** — `enlightenment_philosophy`, `no_more_kings`, `the_social_contract`, `republican_virtue`. Thematic. Reusable across any revolution, any intellectual-movement pack, any founding-document scenario. Future packs (Haitian Revolution, 1848, Russian 1917, Chinese 1949, Bolivarian liberations) will reach for these unchanged.
- **Narrow concepts** — `the_committee_of_public_safety`, `valley_forge`, `thermidor`, `the_pamphlet_as_weapon`. Specific to one historical moment. Non-reusable, but that's the point — they're the foregrounding decisions that make each pack *of* its place.

**A well-designed concept library has both scales.** The narrow concepts ground
each pack; the broad concepts create the cross-pack resonances that make the
library feel like a single intellectual universe rather than a bag of
unconnected drops.

This is where **Pynchon compounding starts paying off for real.** Every new
pack contributes narrow concepts unique to itself, *and* reinforces the broad
concepts it shares with other packs. The library gets smarter every time it's
used. A future Haitian Revolution pack doesn't start from zero — it inherits
everything the French and American packs contributed to `enlightenment_philosophy`
and `no_more_kings`, and adds its own narrow concepts on top
(`the_night_of_fire`, `toussaint_as_type`, `the_black_jacobins`).

This is not a property the first three test cases exposed. It only becomes
visible once you have *two* packs that share *some* concepts, which is exactly
what this case delivers.

### The valence problem

"Liberty" means different things in each pack. In France it is `liberté,
égalité, fraternité` — collective, paired with brotherhood and equality,
leaning republican-virtue, "I die for the republic." In America it is
paired with "life" and "the pursuit of happiness" — individual,
property-coupled, contractual, "I die before being a subject." Same concept.
Different valence.

This is a real design question for the concept layer. Three possible answers:

1. **Fork the concept.** Author `liberty_french_valence` and `liberty_american_valence` as separate files. Simple, produces library bloat.
2. **Make concepts tone-aware.** Add `expressions:` to the concept schema, keyed by tone or co-present concepts. Expressive, reintroduces merge semantics that the no-merge rule was designed to escape.
3. **Let the blend do the work.** The concept file contributes its essence; the pack's tone and other co-present concepts produce the valence at generation time.

**Option 3 is correct.** It is consistent with the no-connection-seeds rule
(§6a): the concept contributes essence, the blend produces expression. No
authoring of valences, no merge semantics, no library bloat. Drop
`enlightenment_liberty` into a pack with `tone: paranoid_terror` and
`committee_of_public_safety` and the French valence emerges naturally because
the rest of the blend pulls in that direction. Drop it into a pack with
`tone: founding_earnest` and `continental_congress` and the American valence
emerges naturally. The concept file stays the same.

**This gives us a concept-authoring discipline that should be a rule in §6a:**
*author concepts at the level of essence, not expression. Let the blend produce
the expression.* A concept file describing Liberty should write about "the
rejection of inherited or divinely-ordained authority, variably expressed as
individual rights or collective virtue depending on intellectual heritage,"
not pick one expression and hard-code it. The essence-level write-up leaves
room for the blend to render whichever valence the surrounding elements call
for.

### A secondary question: one system or two?

This case uses `revolutionary_intrigue` and `frontier_insurrection` as two
separate systems. That's one choice. The alternative is a single
`revolutionary_politics` system with parameters (paranoid vs. coalitional,
centralized vs. distributed, purge-economy vs. coalition-economy) that can
serve every revolutionary pack forever.

Argument for separate: the mechanics you'd actually run in a session are
different. French sessions center on denunciation, committee politics, and
self-consuming purge dynamics. American sessions center on coalition building,
militia logistics, and negotiation with European powers. Different hot loops.

Argument for shared: parsimony. Adding a fifth or sixth revolutionary pack
(Haitian, 1848, Russian, Chinese, Bolivarian) doesn't need a new system each
time, just new parameter configurations and new concept drops.

**This is a judgment call that doesn't get resolved at the PRD level.** It
gets resolved when the first `revolutionary_politics` system file is written
and Keith sees whether the parameter space holds together mechanically. Flag
as §11 open question, move on.

### What this case adds to the architecture

| Before this case | After this case |
|---|---|
| Concepts are per-pack drops | Concepts form a *reuse graph* with broad and narrow scales |
| Concepts are unique to one pack | Concepts can be shared across packs with different valences |
| Concept authoring is open | Concept authoring has a rule: **write essence, not expression** |
| Library value is flat (one concept = one pack's worth of value) | Library value *compounds* — broad concepts get richer every time a new pack reaches for them |

The Pynchon-compounding property is the biggest win. It means that the concept
library is not just a decomposition of existing packs, but a *compounding
creative asset* that becomes more generative over time. Every new pack Keith
authors makes every future pack easier and richer.

### Status

Neither pack exists yet. When the architecture is in place, this case is the
ideal *second* validation after WWI — it tests the cross-pack concept sharing
that WWI couldn't reach, and it exercises the essence/expression authoring
rule that nothing else in the current test set forces.

## 15. The Emotional Core (in case this document is ever reread cold)

Keith has been a forever-DM for 40 years. He has never been surprised by his own
game. Every architectural choice in this project ultimately answers the question
*"does this preserve the surprise?"* If a decision makes Keith more of an author
and less of a player, it's probably wrong. If it makes the model more of an author
and Keith more of a player, it's probably right.

That is the whole thing.
