# Context: 25-7 Chrome CSS rulesets

## Summary

CSS archetype rulesets that use `[data-archetype="X"]` selectors to apply structural visual styling per archetype family. The texture overlays, border treatments, and header styling that make each genre family visually distinct.

## Key Files

### UI repo (sidequest-ui)
- `src/hooks/useChromeArchetype.ts` — sets `data-archetype` attr on `<html>` (from 25-6)
- `src/App.tsx` — calls `useChromeArchetype(currentGenre)` (from 25-6)
- Need: new CSS file with `[data-archetype]` rulesets

### Mockups (orchestrator)
- `docs/mockups/parchment-low-fantasy.html` — target CSS for parchment archetype
- `docs/mockups/terminal-neon-dystopia.html` — target CSS for terminal archetype
- `docs/mockups/rugged-road-warrior.html` — target CSS for rugged archetype

## Archetype CSS Patterns

| Property | Parchment | Terminal | Rugged |
|----------|-----------|----------|--------|
| Texture overlay | Radial vignette (warm) | CRT scanlines + neon bloom | Dusty vignette (dark) |
| Border width | 1px | 1px | 2px |
| Header font | serif, lowercase | monospace, uppercase + glow | condensed sans, uppercase |
| Panel background | Soft gradient from surface | Flat surface | Flat surface |
| Extra vars | — | `--glow-primary`, `--glow-accent` | `--rust`, `--chrome` |

## Dependencies

- 25-6 (Chrome archetypes) — done, provides `data-archetype` attribute

## Blocks

Nothing directly.
