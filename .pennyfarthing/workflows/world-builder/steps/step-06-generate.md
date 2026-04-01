---
name: 'step-06-generate'
description: 'Generate all YAML files in dependency order'

nextStepFile: './step-07-validate.md'
wipFile: '{wip_file}'
---

<purpose>Create all content files from the approved design brief. Files are generated in dependency order so downstream files can reference upstream content.</purpose>

<instructions>Generate files in order, reading cultures.yaml before writing any names. Write to sidequest-content repo.</instructions>

<output>Complete world directory with all YAML files written. stepsCompleted: [1, 2, 3, 4, 5, 6].</output>

# Step 6: Generate Content

**Progress: Step 6 of 8**

## CONTEXT

- Requires approved design brief from Step 3.
- All files go in `{genre_packs_path}/<genre>/` or `{genre_packs_path}/<genre>/worlds/<world>/`
- **Read `cultures.yaml` BEFORE writing any names.** Every name must come from the culture's naming system.
- Respect the merge strategy: worlds override genre for lore/cartography/history, extend for cultures/archetypes/tropes, inherit rules/prompts/theme.

## GENERATION ORDER

Dependencies flow downward. Each file may reference content from files above it.

### For New Genre Pack:
1. `pack.yaml` — metadata, description, version
2. `rules.yaml` — classes, races, stats, magic, combat rules
3. `axes.yaml` — tone sliders and presets
4. `cultures.yaml` — naming patterns with corpus files
5. `lore.yaml` — genre-level cosmology
6. `archetypes.yaml` — NPC templates
7. `char_creation.yaml` — character creation scene graph
8. `progression.yaml` — affinity tiers and unlocks
9. `inventory.yaml` — item catalog
10. `tropes.yaml` — story beats with escalation
11. `voice_presets.yaml` — NPC voice configs
12. `theme.yaml` — colors, fonts, decorations
13. `visual_style.yaml` — image generation config
14. `audio.yaml` — mood tracks, SFX, mixer config
15. Create corpus files in `corpus/`

### For New World (within existing genre):
1. `world.yaml` — identity, axis_snapshot
2. `legends.yaml` — deep history (shapes everything else)
3. `lore.yaml` — present-day world informed by legends
4. `cultures.yaml` — extends genre cultures with world-specific naming
5. `cartography.yaml` — regions, routes, terrain (informed by lore + real geography)
6. `archetypes.yaml` — world-specific NPCs grounded in historical roles
7. `tropes.yaml` — story beats from historical conflicts
8. `history.yaml` — campaign progression chapters (FRESH → VETERAN)
9. `visual_style.yaml` — world-specific art direction (optional override)

### For DM Prep:
Generate only the files that need updating based on user's session goals.

## RULES

- **Every name through the conlang.** English in descriptions only.
- **Cartography adjacency is bidirectional.** If A connects to B, B must connect to A.
- **Factions must conflict.** No world where everyone gets along.
- **History chapters must have valid session_ranges.**
- **POI descriptions must be visually rich** — paint the scene for Flux.

## AFTER GENERATION

Report what was created:
```
Generated {N} files in {genre}/{world}:
- world.yaml
- legends.yaml
- ...
```

Update WIP frontmatter: `stepsCompleted: [1, 2, 3, 4, 5, 6]`

Proceed to validation.
