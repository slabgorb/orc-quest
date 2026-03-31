---
parent: context-epic-16.md
---

# Story 16-16: Content Audit Pass — All Genre Packs Declare Resources and Confrontations

## Business Context

With the engine infrastructure in place (ResourcePool, StructuredEncounter, mood aliases),
update all 9 genre packs to use the new schemas. Validate everything loads. Update
docs/genre-pack-status.md with new completeness criteria.

## Technical Approach

### Per-Genre Updates

| Genre | Resources to Declare | Confrontations to Declare | Mood Aliases |
|-------|---------------------|--------------------------|-------------|
| spaghetti_western | Luck (done in 16-12) | Standoff (done in 16-6) | standoff, saloon, betrayal, riding |
| neon_dystopia | Humanity (done in 16-12) | Net Combat (done in 16-8) | cyberspace, club, corporate |
| pulp_noir | Heat (done in 16-12) | Interrogation (done in 16-7) | speakeasy, intrigue, chase |
| road_warrior | Fuel (done in 16-12) | — (chase already exists) | convoy |
| space_opera | — | Ship Combat (done in 16-8) | galley, drift, docking, void |
| victoria | — | Auction (done in 16-8), Trial | teahouse (reuse?), ceremony |
| elemental_harmony | — | — | teahouse, spirit, ceremony |
| low_fantasy | — | — | tavern, mystery |
| mutant_wasteland | — | — | settlement, mystery, ruins |

### Validation

Run the genre loader against all 9 packs and verify:
- All resource declarations parse
- All confrontation declarations parse
- All mood_aliases reference valid moods or chains to valid moods
- No stat_check references invalid ability scores

### Documentation Update

Update `docs/genre-pack-status.md`:
- Add "Resources" column to pack overview table
- Add "Confrontations" column
- Add "Mood Aliases" column
- Update gap map to reflect closed gaps

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/genre_packs/*/rules.yaml` | Add resources/confrontations as needed |
| `sidequest-content/genre_packs/*/audio.yaml` | Add mood_aliases and mood_keywords |
| `docs/genre-pack-status.md` | Update with new completeness criteria |
| Integration test | Load all 9 genre packs, verify no parse errors |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| All packs load | All 9 genre packs parse without errors with new schema |
| Resources declared | spaghetti_western, neon_dystopia, pulp_noir, road_warrior have resources |
| Confrontations declared | Packs with unique encounter types have them in rules.yaml |
| Mood aliases | All packs have mood_aliases for their custom moods |
| Docs updated | genre-pack-status.md reflects current state |
| No regressions | Existing genre loader tests still pass |
