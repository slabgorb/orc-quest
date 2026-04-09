---
parent: context-epic-13.md
---

# Story 13-12: Initiative Stat Mapping — Genre Pack Schema + Caverns Authoring

## Business Context

Stats need to mean something mechanically. Initiative is the first system where stats have
concrete gameplay impact beyond HP. Different encounter types should weight different stats:
combat → DEX (reflexes), chase → DEX (speed), social → CHA (personality), trials → WIS
(judgment). This mapping lives in the genre pack so each genre can define its own encounter
types and stat weights.

For the 2026-04-13 playtest, only caverns_and_claudes needs authoring. The schema must be
generic enough for other genres but we're not authoring them yet.

## Technical Guardrails

- **Schema location:** `genre_packs/<genre>/rules.yaml` (or a new `initiative.yaml` — check
  what pattern the genre pack already uses for mechanical rules)
- **Schema shape:**
  ```yaml
  initiative_rules:
    <encounter_type>:
      primary_stat: <stat_name>
      description: "<narrator-facing description of what this stat means for initiative>"
  ```
- **Encounter types for caverns_and_claudes:** combat, chase, social, exploration (minimum).
  Check existing encounter/intent types in the codebase to align naming.
- **Stats for caverns:** STR, DEX, CON, INT, WIS, CHA (standard 6-stat D&D array, already
  used in chargen `stat_generation`)
- **Loader:** `sidequest-genre` crate must parse and expose initiative rules. Fail loudly
  if the field is missing (no silent fallback to hardcoded defaults).
- **Consumer:** dispatch/prompt builder (story 13-12) reads initiative rules via genre pack

## Scope Boundaries

**In scope:**
- Define YAML schema for initiative rules in genre pack
- Author initiative rules for caverns_and_claudes
- Add serde struct + loader in sidequest-genre
- Validation: genre pack validation tool checks initiative rules if present
- Expose via GenrePack API so dispatch can read it

**Out of scope:**
- Authoring for other genres (future — each genre gets its own pass)
- Complex initiative formulas (weighted multi-stat, dice-based) — primary_stat is sufficient
- Runtime initiative calculation — the narrator interprets the rules, not a formula engine
- Prompt integration (that's 13-12)

## AC Context

| AC | Detail |
|----|--------|
| Schema defined | `initiative_rules` with encounter_type → primary_stat + description |
| Caverns authored | combat, chase, social, exploration entries with appropriate stats |
| Loader works | `GenrePack.initiative_rules()` returns parsed rules |
| Loud failure | Missing initiative_rules in a genre pack → error, not silent default |
| Validation | `sidequest-validate` checks initiative rules against known stat names |

## Key Files

| File | Change |
|------|--------|
| `sidequest-content/genre_packs/caverns_and_claudes/rules.yaml` | Author initiative rules |
| `sidequest-genre/src/lib.rs` (or model file) | `InitiativeRules` struct + serde |
| `sidequest-genre/src/loader.rs` (or equivalent) | Parse initiative_rules from YAML |
| `sidequest-validate/` | Validate initiative rules against stat names in genre |
