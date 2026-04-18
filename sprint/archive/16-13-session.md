---
story_id: "16-13"
jira_key: "none"
epic: "16"
workflow: "tdd"
---
# Story 16-13: UI Resource Display — GenericResourceBar with genre theming

## Story Details
- **ID:** 16-13
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Epic:** 16 — Genre Mechanics Engine — Confrontations & Resource Pools
- **Repository:** sidequest-ui
- **Branch:** feat/16-13-ui-resource-display
- **Points:** 3
- **Priority:** p1
- **Status:** in-progress

## Context

Resources (Luck, Humanity, Heat, Fuel, etc.) are defined per genre pack and tracked as ResourcePool structs on the backend. The UI needs a GenericResourceBar component that renders any resource with genre-appropriate visual treatment, threshold markers, and audiovisual feedback on threshold crossings.

## Acceptance Criteria

1. GenericResourceBar renders with name, value, max
2. Progress bar shows correct percentage (value/max)
3. Genre-themed colors applied via data-genre attribute or className
4. Threshold markers displayed on the bar
5. Pulse animation class applied when threshold is crossed
6. Toast notification on threshold crossing
7. Audio sting triggered on threshold crossing (via AudioCue or similar)
8. Multiple resource bars render independently
9. Zero and max edge cases handled

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
**Phase Started:** 2026-04-05T10:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-05T10:00Z | 2026-04-05T10:00Z | 0m |
| red | 2026-04-05T10:00Z | — | — |

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings yet.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations yet.
