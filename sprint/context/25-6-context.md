# Context: 25-6 Chrome archetypes

## Summary

Genre-themed panel styling via CSS custom properties. Each genre pack maps to a chrome archetype family (parchment, terminal, rugged) that sets visual identity through CSS custom properties.

## Key Files

### Content repo
- `genre_packs/*/theme.yaml` — color palette, web_font_family (all 11 genre packs have these)
- `genre_packs/*/client_theme.css` — per-genre CSS overrides (most packs have these)

### UI repo (sidequest-ui)
- Components consuming theme: CharacterPanel (25-2), GameLayout (25-4)
- Need: theme hook/provider, archetype CSS, custom property injection

### Mockups (orchestrator)
- `docs/mockups/parchment-low-fantasy.html` — warm serif, aged paper textures
- `docs/mockups/terminal-neon-dystopia.html` — CRT scanlines, monospace, neon glow
- `docs/mockups/rugged-road-warrior.html` — heavy borders, rough textures, condensed sans

## Genre → Archetype Mapping

| Archetype | Genre Packs |
|-----------|------------|
| parchment | low_fantasy, victoria, elemental_harmony, star_chamber |
| terminal | neon_dystopia, space_opera |
| rugged | road_warrior, mutant_wasteland, spaghetti_western, pulp_noir, caverns_and_claudes |

## Dependencies

- 25-2 (CharacterPanel) — done
- 25-4 (GameLayout rewire) — done

## Blocked By

Nothing — ready to implement.

## Blocks

- 25-7 (Chrome CSS — archetype rulesets) depends on this story's archetype system
