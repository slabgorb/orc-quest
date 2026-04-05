---
story_id: "16-15"
jira_key: "none"
epic: "16"
workflow: "tdd"
---
# Story 16-15: Faction music routing — trigger faction themes by context

## Story Details
- **ID:** 16-15
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Epic:** 16 — Genre Mechanics Engine — Confrontations & Resource Pools
- **Repository:** sidequest-api, sidequest-content
- **Branch:** feat/16-15-faction-music-routing
- **Points:** 3
- **Priority:** p2
- **Status:** in-progress

## Context

MusicDirector checks current location's faction, active confrontation actors' factions, and player reputation to select faction-specific tracks when available. Road warrior's 10 faction themes (Bosozoku through Dekotora) become the test case. Faction music declared in audio.yaml under faction_themes with trigger conditions.

## Acceptance Criteria

1. audio.yaml declares faction_themes section with trigger conditions
2. MusicDirector checks location faction for faction theme selection
3. MusicDirector checks active confrontation actors' factions
4. MusicDirector checks player reputation threshold for faction music
5. Road warrior faction themes (Bosozoku through Dekotora) as test case
6. Faction music overrides default mood-based selection when conditions match
7. Falls back to mood-based selection when no faction conditions match

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
**Phase Started:** 2026-04-05T10:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T10:20Z | 2026-04-05T10:20Z | 0m |
| red | 2026-04-05T10:20Z | — | — |

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings yet.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations yet.
