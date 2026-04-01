---
name: 'step-01-orient'
description: 'Select mode, identify target genre/world, check for WIP'

nextStepFile: './step-02-riff.md'
skipToStepFile: './step-03-research.md'
wipFile: '{wip_file}'
---

<purpose>Determine what kind of content work the user needs, identify the target genre pack and world, and check for existing work-in-progress.</purpose>

<instructions>Check WIP, ask user for mode, identify target, read existing content for context.</instructions>

<output>Initialized WIP file with mode, target genre/world, and session goals.</output>

# Step 1: Orient

**Progress: Step 1 of 8**

## SEQUENCE

### 0. Check for Work in Progress

a) Check if `{wipFile}` exists.

b) **IF WIP EXISTS:**
1. Read frontmatter: `mode`, `genre`, `world`, `stepsCompleted`
2. Present:
```
Found world-builder session in progress:

**{genre}/{world}** — Mode: {mode}, Step {lastStep} of 6

[Y] Continue where I left off
[N] Start fresh
```
3. **HALT and wait for user selection.**
   - **[Y]** → Jump to next incomplete step
   - **[N]** → Archive WIP to `.session/world-builder-{genre}-{world}-archived-{date}.md`

### 1. Mode Selection

Ask the user which mode:

1. **New Genre Pack** — Create a genre from scratch
2. **New World** — Build a world within an existing genre pack
3. **Asset Management** — Fonts, visual style, theme, audio config
4. **DM Prep** — Between-session tuning (NPCs, regions, tropes, audio)
5. **Playtest & Iterate** — Run playtest, interpret results, fix content

**HALT and wait for selection.**

### 2. Identify Target

Based on mode:
- **New Genre:** Ask for genre concept, inspirations, tone
- **New World:** Which genre pack? What historical/cultural concept?
- **Asset Management:** Which genre/world? What assets?
- **DM Prep:** Which active campaign?
- **Playtest:** Which genre/world to test?

### 3. Read Existing Content

- Read `{genre_packs_path}/<genre>/pack.yaml` (if existing genre)
- Read `{genre_packs_path}/<genre>/rules.yaml` — understand the mechanical framework
- Read `{genre_packs_path}/<genre>/cultures.yaml` — **CRITICAL: internalize naming patterns**
- Read `{genre_packs_path}/<genre>/axes.yaml` — tone configuration
- Scan existing worlds in the genre for reference

### 4. Initialize WIP

Create `{wipFile}`:
```yaml
---
mode: '{mode}'
genre: '{genre}'
world: '{world}'
created: '{date}'
status: 'in-progress'
stepsCompleted: [1]
concept: '{brief concept description}'
---
```

### 5. Mode-Based Routing

| Mode | Next Step |
|------|-----------|
| New Genre | step-02-riff |
| New World | step-02-riff |
| Asset Management | step-07-validate (skip to validation) |
| DM Prep | step-06-generate (skip to generation) |
| Playtest | step-08-playtest (skip to end) |

Present the routing decision and **continue to the appropriate step**.
