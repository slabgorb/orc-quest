---
name: 'step-03-research'
description: 'Deep research on source material — historical, cultural, geographical'

nextStepFile: './step-04-refine.md'
wipFile: '{wip_file}'
---

<purpose>Research the real-world source material that will inform the genre pack or world. Build a knowledge base of historical events, cultural practices, geography, conflicts, and aesthetics.</purpose>

<instructions>Use web search and Perplexity for historical/cultural research. Read existing genre content for mechanical context. Document findings in WIP.</instructions>

<output>Updated WIP with research findings, cultural notes, and sensitivity considerations. stepsCompleted: [1, 2, 3].</output>

# Step 3: Research

**Progress: Step 3 of 8**

## CONTEXT

- Requires WIP from Step 1 with mode, genre, and world/concept identified.
- This step uses `perplexity_research` for deep investigation and `perplexity_ask` for quick factual lookups.
- **New Genre mode:** Research the genre's inspirations, canonical works, tone, and mechanical identity.
- **New World mode:** Research the historical period, culture, and geography that inspire the world.

## SEQUENCE

### 1. Historical & Cultural Research

Use `perplexity_research` for deep investigation:

a) **Key historical events** — turning points, conflicts, daily life
b) **Social structures** — classes, hierarchies, power dynamics
c) **Geography and climate** — terrain, trade routes, natural resources
d) **Cultural practices** — beliefs, art, customs, taboos
e) **Naming conventions** — real linguistic patterns from the source culture
f) **Aesthetic references** — art, architecture, clothing, visual motifs

### 2. Genre Mechanical Mapping

Read the target genre's mechanical framework:
- `rules.yaml` — classes, races, magic, stats, affinities
- `lore.yaml` — cosmology, world-building conventions
- `archetypes.yaml` — existing NPC templates
- `tropes.yaml` — existing story beat patterns

Map research findings to mechanical concepts:
- Historical roles → genre classes/archetypes
- Real geography → game regions and terrain types
- Cultural conflicts → faction goals and opposing agendas
- Social structures → power dynamics and NPC hierarchies

### 3. Cultural Sensitivity Review

Document:
- What aspects of the source culture are being adapted?
- What should be handled with extra care?
- What should be avoided or abstracted?
- Are naming patterns respectful and linguistically grounded?

### 4. Update WIP

Append research section to `{wipFile}`:

```markdown
## Research Findings

### Historical Context
{key findings}

### Mechanical Mapping
| Historical Concept | Genre Equivalent |
|--------------------|-----------------|
| {role/event/place} | {class/trope/region} |

### Cultural Sensitivity
{notes}

### Naming Sources
{linguistic patterns identified}

### Aesthetic Direction
{visual and tonal references}
```

Update frontmatter: `stepsCompleted: [1, 2, 3]`

### 5. Present findings to user

Summarize the research and mapping. Ask:
- Does this direction feel right?
- Anything to add, cut, or adjust?
- Ready to proceed to the design brief?

**HALT and wait for confirmation before proceeding.**
