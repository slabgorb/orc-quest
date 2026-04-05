---
story_id: "16-8"
jira_key: "none"
epic: "16"
workflow: "tdd"
---
# Story 16-8: Genre-specific confrontation types — net combat, ship combat, auction

## Story Details
- **ID:** 16-8
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Epic:** 16 — Genre Mechanics Engine — Confrontations & Resource Pools
- **Repository:** sidequest-api (tests), sidequest-content (YAML)
- **Branch:** feat/16-8-genre-confrontation-types
- **Points:** 5
- **Priority:** p2
- **Status:** in-progress

## Context

Declare genre-specific confrontation types: neon_dystopia net_combat (trace metric, ICE beats, deck secondary stats), space_opera ship_combat (engagement_range, broadside/evasion beats, ship_block secondary stats), victoria auction (bid metric, raise/bluff/withdraw beats, purse secondary stat). Each declared in respective genre rules.yaml.

## Acceptance Criteria

1. neon_dystopia rules.yaml declares net_combat confrontation (trace metric ascending, ICE beats, deck secondary stats)
2. space_opera rules.yaml declares ship_combat confrontation (engagement_range metric, broadside/evasion beats, ship_block secondary stats)
3. victoria rules.yaml declares auction confrontation (bid metric ascending, raise/bluff/withdraw beats, purse secondary stat)
4. Genre loader parses all three confrontation types from YAML
5. Each type has correct metric direction, beats with stat checks, and secondary stats
6. Confrontation types have mood declarations for music routing

## Workflow Phases

| Phase | Owner | Status |
|-------|-------|--------|
| setup | sm | complete |
| red | tea | in-progress |
| green | dev | pending |
| review | reviewer | pending |
| finish | sm | pending |

## Workflow Tracking

**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-04-05T10:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T10:10Z | 2026-04-05T10:10Z | 0m |
| red | 2026-04-05T10:10Z | — | — |

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings yet.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations yet.
