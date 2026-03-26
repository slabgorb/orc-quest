---
parent: context-epic-10.md
---

# Story 10-8: Backfill OCEAN Profiles on Existing NPC Archetypes Across Genre Packs

## Business Context

The OCEAN system is only useful if genre packs actually define baseline profiles. This story
adds `ocean_baseline` entries to every existing NPC archetype across all shipped genre packs.
It's a content task, not a code task — editing YAML files to assign personality scores that
feel right for each archetype.

**Python reference:** `sq-2/sprint/epic-64.yaml` — same backfill task was done for the Python
genre packs. The Rust port shares the same `genre_packs/` directory so this work carries over.

**Depends on:** Story 10-2 (YAML schema for ocean_baseline established).

## Technical Approach

### Process

1. List all genre packs in `genre_packs/`
2. For each pack, identify all NPC archetypes
3. Assign five OCEAN scores per archetype based on genre-appropriate personality

### Guidelines for Score Assignment

- **Openness:** High for scholars, artists, explorers. Low for traditionalists, guards.
- **Conscientiousness:** High for military, clergy, craftsmen. Low for rogues, tricksters.
- **Extraversion:** High for bards, merchants, leaders. Low for hermits, assassins.
- **Agreeableness:** High for healers, diplomats. Low for villains, misanthropes.
- **Neuroticism:** High for traumatized, paranoid. Low for stoics, veterans.

### Example Entry

```yaml
archetypes:
  grizzled_mercenary:
    # ... existing fields
    ocean_baseline:
      openness: 3.0
      conscientiousness: 6.0
      extraversion: 4.5
      agreeableness: 3.0
      neuroticism: 5.5
```

### Validation

Run genre pack deserialization tests to confirm all baselines parse. Any archetype
missing `ocean_baseline` falls back to midpoint (5.0 all) per story 10-2.

## Scope Boundaries

**In scope:**
- Add `ocean_baseline` to every NPC archetype in all genre packs
- Validate YAML parses correctly
- Scores should feel genre-appropriate

**Out of scope:**
- Named NPC override profiles (individual NPCs may differ from archetype)
- New archetypes (only backfill existing ones)
- ocean_variance tuning (defaults to 1.5 per 10-2)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| All archetypes | Every NPC archetype in every genre pack has `ocean_baseline` |
| Valid YAML | All genre packs deserialize without error after backfill |
| Score range | All values between 0.0 and 10.0 |
| Genre fit | Scores reviewed for genre appropriateness (scholar != mercenary) |
| No new archetypes | Only existing archetypes modified, none added |
| Fallback works | Removing an `ocean_baseline` still loads (midpoint default) |
