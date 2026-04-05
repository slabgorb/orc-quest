---
story_id: "16-14"
jira_key: "none"
epic: "16"
workflow: "tdd"
---
# Story 16-14: String-keyed moods + fallback aliases

## Story Details
- **ID:** 16-14
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Epic:** 16 — Genre Mechanics Engine — Confrontations & Resource Pools
- **Repository:** sidequest-api
- **Branch:** feat/16-14-string-keyed-moods
- **Points:** 3
- **Priority:** p1
- **Status:** in-progress

## Context

The current Mood enum has 7 hardcoded variants (Combat, Exploration, Tension, Triumph, Sorrow, Mystery, Calm). Genre packs already declare custom mood keys in mood_tracks (e.g., "standoff", "saloon") but they silently map to Exploration via key_to_mood fallback. This story replaces the enum with string-keyed moods and adds explicit alias chains in audio.yaml.

## Acceptance Criteria

1. Mood becomes a string-keyed type (not enum)
2. Core moods (tension, calm, exploration, mystery, combat, triumph, sorrow) still work
3. Genre packs declare mood_aliases in audio.yaml mapping custom→core
4. MusicDirector resolves mood string through alias chain
5. Confrontation types declare their mood string
6. Unknown moods fall back through alias chain or to a default
7. All existing mood tests pass with backward-compatible mapping

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
**Phase Started:** 2026-04-05T09:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T09:30Z | 2026-04-05T09:30Z | 0m |
| red | 2026-04-05T09:30Z | — | — |

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings yet.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations yet.
