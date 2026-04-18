---
story_id: "14-4"
jira_key: ""
epic: "14"
workflow: "tdd"
---

# Story 14-4: Vocabulary level slider — narrator prose complexity control (accessible / literary / epic)

## Story Details
- **ID:** 14-4
- **Jira Key:** (personal project, no Jira)
- **Workflow:** tdd
- **Stack Parent:** none

## Acceptance Criteria

From the epic description: Add a narrator_vocabulary setting controlling prose complexity. Mapped to approximate reading level guidance in the narrator prompt (e.g., "accessible" = 8th grade, "literary" = college, "epic" = unrestricted). UI slider in session settings alongside verbosity. Persisted per-session.

1. **Backend (sidequest-api):**
   - Add `narrator_vocabulary` field to session config (type: enum with variants `accessible`, `literary`, `epic`)
   - Default value per session type: standard choices (likely `literary` for multiplayer/solo)
   - Inject vocabulary guidance into the narrator system prompt based on the setting
   - Include vocabulary level in PARTY_STATUS and SESSION_UPDATE payloads
   - Persist the setting to session save/load

2. **Frontend (sidequest-ui):**
   - Add vocabulary slider to the session settings panel (alongside existing verbosity slider)
   - Slider maps to three discrete positions (accessible, literary, epic)
   - Send updated setting to API via WebSocket when changed
   - Display current vocabulary level in session UI
   - Persist locally in session state

3. **Protocol (sidequest-protocol):**
   - Update GameMessage enum with new payload variant for vocabulary setting changes
   - Include vocabulary in existing PARTY_STATUS and SESSION_UPDATE messages

## Workflow Tracking

**Workflow:** tdd  
**Phase:** red  
**Phase Started:** 2026-03-31T02:03Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T02:30Z | 2026-03-31T02:03Z | complete |
| red | 2026-03-31T02:03Z | - | - |
| green | - | - | - |
| spec-check | - | - | - |
| verify | - | - | - |
| review | - | - | - |
| spec-reconcile | - | - | - |
| finish | - | - | - |

## Delivery Findings

No upstream findings at this time.

## Design Deviations

None logged during setup.

## Context Notes

This story follows 14-3 (text length/verbosity slider). The two sliders work together to give players control over narrator output: one controls length, this one controls complexity. Both are session-level settings persisted to save files.

Repos: sidequest-api, sidequest-ui
