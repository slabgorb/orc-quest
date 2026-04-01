---
name: 'step-05-design-brief'
description: 'Present design brief for user approval before generating content'

nextStepFile: './step-06-generate.md'
wipFile: '{wip_file}'
---

<purpose>Synthesize research into a concrete design brief. Map historical concepts to game mechanics, lay out faction conflicts, propose cartography, and get user approval before generating files.</purpose>

<instructions>Build design brief from research, present for approval, iterate until user signs off.</instructions>

<output>Approved design brief in WIP. stepsCompleted: [1, 2, 3, 4, 5].</output>

# Step 5: Design Brief

**Progress: Step 5 of 8**

## SEQUENCE

### 1. Build the Brief

From research findings, produce:

a) **World Identity**
   - Name (from cultures.yaml naming patterns — NOT English descriptive)
   - Tagline (one sentence capturing the tone)
   - Axis snapshot (tone slider values from axes.yaml)

b) **Faction Design** (minimum 3, ideally 4-5)
   - Name, description, goal, urgency level
   - Relationships to other factions (hostile/wary/allied/dismissive)
   - Scene injection text
   - **Factions MUST have conflicting goals** — this generates story

c) **Cartography Sketch**
   - Regions with terrain types and descriptions
   - Routes connecting regions (adjacency must be bidirectional)
   - Key landmarks and points of interest

d) **NPC Archetypes** (6-10)
   - Historical role → genre archetype mapping
   - Disposition tendencies, motivations
   - Voice preset suggestions

e) **Trope Beats**
   - Story arcs drawn from historical conflicts
   - Escalation from FRESH through VETERAN maturity
   - Which factions drive which tropes

f) **Aesthetic Direction**
   - Visual style notes (Flux prompt suffix, negative prompt)
   - Music mood mapping
   - Font suggestion if new genre

### 2. Present Brief

Show the complete brief to the user. Format as a structured document, not a wall of text.

### 3. Iterate

**HALT and wait for feedback.**

Common adjustments:
- Faction balance (too many allied, not enough conflict)
- Tone drift (too dark, too light for the genre)
- Naming issues (sounds wrong for the culture)
- Scope (too many regions, too few NPCs)

Revise and re-present until user says "go."

### 4. Update WIP

Append approved brief to `{wipFile}`.
Update frontmatter: `stepsCompleted: [1, 2, 3, 4, 5]`
