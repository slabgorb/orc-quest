---
story_id: "14-2"
jira_key: ""
epic: "14"
workflow: "tdd"
---
# Story 14-2: Player location on character sheet — show current location for each party member

## Story Details
- **ID:** 14-2
- **Epic:** 14 (Multiplayer Session UX — Spawn, Visibility, Text Tuning, and Chargen Polish)
- **Workflow:** tdd
- **Points:** 2
- **Priority:** p0
- **Stack Parent:** none

## Description

Add current_location field to PARTY_STATUS and CHARACTER_SHEET payloads. UI displays location under each player's name in the party panel. When players are in different locations, visually group or flag the difference.

## Acceptance Criteria

1. PARTY_STATUS protocol message includes current_location field for each player
2. CHARACTER_SHEET payload includes current_location field
3. UI party panel displays location label under each player's name
4. When party members are in different locations, there is a visual indicator (grouping or flag)
5. Location names derive from the current world location or scene context
6. Tests cover all protocol changes and UI rendering logic

## Implementation Approach

**API side (sidequest-api):**
- Add `current_location: String` field to CHARACTER_SHEET variant in sidequest-protocol
- Add `current_location: String` field to PARTY_STATUS payload
- Update game state to track and emit current location for each player
- Wire location updates through IntentRouter and shared_session
- Add tests for protocol serialization and game state updates

**UI side (sidequest-ui):**
- Read current_location from CHARACTER_SHEET and PARTY_STATUS payloads
- Render location label in party member cards
- Add visual styling to group or flag players in different locations
- Add tests for location rendering and grouping logic

## Key References
- sidequest-api/crates/sidequest-protocol/src/lib.rs (message types)
- sidequest-api/crates/sidequest-server/src/lib.rs (state routing)
- sidequest-api/crates/sidequest-game/src/state.rs (character state)
- sidequest-ui/src/components/PartyPanel.tsx
- docs/api-contract.md

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-31T09:54:49Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T09:48:23Z | 2026-03-31T09:49:32Z | 1m 9s |
| red | 2026-03-31T09:49:32Z | 2026-03-31T09:54:43Z | 5m 11s |
| green | 2026-03-31T09:54:43Z | 2026-03-31T09:54:46Z | 3s |
| review | 2026-03-31T09:54:46Z | 2026-03-31T09:54:49Z | 3s |
| finish | 2026-03-31T09:54:49Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

### TEA (test design)
- **Gap** (non-blocking): Story 14-2 was already fully implemented and merged (API PR #183, UI PR #37) before sprint setup created it as a backlog item. Sprint YAML status was `ready` but the work was already on develop. *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

## TEA Assessment

**Tests Required:** No
**Reason:** Story 14-2 is already fully implemented and merged on both repos.

**Evidence:**
- API: commit `b1dd687` — `feat(14-2): add current_location to party/character protocol and wire through server` (PR #183, merged to develop)
- UI: commit `0e61394` — `feat(14-2): render player location on PartyPanel and CharacterSheet` (PR #37, merged to develop)

**Implementation verified:**
- `PartyMember.current_location: String` exists in protocol (sidequest-protocol/src/message.rs)
- `CharacterSheetPayload.current_location: String` exists in protocol
- Server wires `display_location` from `PlayerState` into `PartyMember` for multiplayer
- Server wires `current_location` from `GameSnapshot` into `CharacterSheetPayload`
- UI `PartyPanel.tsx` renders location badge with `data-testid="location-badge"`
- UI `isSplitParty()` detects when players are in different locations
- UI tests cover location display and split-party grouping (PartyPanel.test.tsx lines 399-472)

**Status:** Already GREEN (all tests passing, feature merged)
**Handoff:** Back to SM for finish ceremony — no TDD cycle needed.

## Sm Assessment

**Story 14-2** is a clean 2-point p0 story with well-defined scope: add `current_location` to protocol messages and display in the UI party panel. No dependencies, no blockers. Repos are api and ui — branches created on both. TDD workflow, routing to TEA (Han Solo) for RED phase to write failing tests covering protocol fields, game state tracking, and UI rendering.