---
story_id: "14-3"
jira_key: "none"
epic: "14"
workflow: "tdd"
---
# Story 14-3: Text length slider — per-session narrator verbosity control (concise / standard / verbose)

## Story Details
- **ID:** 14-3
- **Jira Key:** none (personal project)
- **Epic:** 14 (Multiplayer Session UX — Spawn, Visibility, Text Tuning, and Chargen Polish)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p1
- **Repos:** sidequest-api, sidequest-ui

## Story Context

**Problem:**
Multiplayer sessions need narrator verbosity control. In a group play setting, players with different reading speeds and attention spans need different levels of detail. A verbose narration that immersive for a solo player can be exhausting for a group. We need a UI control that maps to narrator system prompt instructions.

**Acceptance Criteria:**

1. Add `narrator_verbosity` field to SessionConfig in protocol and database (three levels: concise, standard, verbose)
2. UI exposes verbosity slider in session settings with three discrete positions labeled and persistent per-session
3. Default is "standard" for multiplayer sessions, "verbose" for solo sessions
4. Narrator system prompt receives verbosity instruction: concise = "keep descriptions to 1-2 sentences", standard = "standard descriptive prose", verbose = "elaborate with sensory details and world-building"
5. Narrator respects the instruction across all narration types (action, item pickup, NPC dialogue, scene entry)
6. Setting is persisted in session state and restored on session reload
7. Works correctly in both solo and multiplayer modes
8. End-to-end test: create session, set verbosity, trigger narration, verify output length matches setting

**Why This Matters:**
Multiplayer UX requires different defaults than solo play. A slider in session settings gives players real control over game pacing and readability without requiring code changes. This is a core multiplayer tuning control.

**Repos & Files:**

Protocol (sidequest-api/crates/sidequest-protocol/src/):
- `lib.rs` — Add narrator_verbosity to SessionConfig

Game engine (sidequest-api/crates/sidequest-game/src/):
- `session.rs` — SessionConfig, defaults based on player count
- `narrator.rs` — System prompt construction with verbosity injection

Server wiring (sidequest-api/crates/sidequest-server/src/):
- `shared_session.rs` — Handle narrator_verbosity in session state
- `handlers.rs` — Parse and persist verbosity from CLIENT_CONFIG messages

UI (sidequest-ui/src/):
- `components/SessionSettings.tsx` — Add verbosity slider with three labels
- `providers/GameContext.tsx` — Store and propagate narrator_verbosity setting
- `screens/GameScreen.tsx` — Pass setting to all narration triggers

Tests:
- `sidequest-api/tests/` — Narrator prompt generation with verbosity levels
- `sidequest-ui/src/__tests__/` — Slider interaction and setting persistence

## Workflow Tracking

**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-03-31T02:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T02:00:00Z | 2026-03-31T02:10:00Z | 10m |
| red | 2026-03-31T02:10:00Z | - | - |

## Delivery Findings

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
