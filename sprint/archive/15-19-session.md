---
story_id: "15-19"
jira_key: "none"
epic: "15"
workflow: "tdd"
---
# Story 15-19: Wire conlang knowledge — language learning, name bank, and prompt injection all unwired

## Story Details
- **ID:** 15-19
- **Jira Key:** none (personal project)
- **Epic:** 15 — Playtest Debt Cleanup
- **Workflow:** tdd
- **Stack Parent:** none

## Story Description

Four unwired conlang functions in sidequest-game/src:
1. **record_language_knowledge()** — should fire when a character learns a conlang word in narration, never called
2. **record_name_knowledge()** — should fire when the NameBank generates a proper noun, never called
3. **query_language_knowledge()** — should feed into prompt context so the narrator stays consistent with vocabulary the character already knows, never called
4. **format_name_bank_for_prompt()** — formats NameBank for narrator prompt injection, never called

**Fix:** Wire record_name_knowledge into the NameBank generation path. Wire record_language_knowledge into narration post-processing when conlang morphemes are detected. Wire query_language_knowledge and format_name_bank_for_prompt into dispatch/prompt.rs.

**OTEL events required:**
- conlang.morpheme_learned (character_id, language_id, morpheme)
- conlang.name_recorded (name, language_id, gloss)
- conlang.context_injected (names_count, morphemes_count)

## Workflow Tracking
**Workflow:** tdd
**Phase:** green
**Phase Started:** 2026-04-06T11:48:45Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-06T07:45:00Z | 2026-04-06T11:44:34Z | 3h 59m |
| red | 2026-04-06T11:44:34Z | 2026-04-06T11:48:45Z | 4m 11s |
| green | 2026-04-06T11:48:45Z | - | - |

## Key Integration Points

1. **NameBank → record_name_knowledge()** — When names are generated for NPCs/places, record the knowledge. Location: dispatch/npc_context.rs or sidequest-agents name generation path.

2. **Narration → record_language_knowledge()** — After narration extraction, detect morpheme mentions and record them. Location: dispatch/mod.rs post-narration processing.

3. **Prompt Building → query_language_knowledge() + format_name_bank_for_prompt()** — Inject language context into narrator prompt. Location: dispatch/prompt.rs alongside other context assembly.

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Gap** (non-blocking): Story 15-19 was fully implemented and merged (PR #313, commits 23773af and 1c8accf) but sprint YAML was never updated. Story status still shows `ready`. Affects `sprint/epic-15.yaml` (needs status → done). *Found by TEA during test design.*

## Design Deviations

No design deviations.

### TEA (test design)
- No deviations from spec.

## TEA Assessment

**Tests Required:** No
**Reason:** Story 15-19 is already fully implemented and merged (PR #313). All 4 unwired functions are now wired in dispatch/mod.rs and dispatch/prompt.rs. 11 wiring tests exist and pass in `conlang_wiring_story_15_19_tests.rs`. All 3 OTEL events are present. This story needs the finish ceremony, not new tests.

**Existing Test Coverage:**
- `conlang_wiring_story_15_19_tests.rs` — 11 tests, all GREEN
- Source-code wiring assertions via `include_str!` confirm production callers exist
- Behavioral tests confirm fragment creation and prompt formatting

**Status:** Already GREEN — no red phase needed

**Handoff:** Back to Vizzini (SM) — story needs status update + finish ceremony, not TDD

## Sm Assessment

**Story readiness:** READY
- Session file created with full context and key integration points identified
- Feature branch `feat/15-19-wire-conlang-knowledge` created from `develop` in sidequest-api
- Story context available at `sprint/context/context-epic-15-story-19.md`
- Scope: 4 unwired conlang functions → 3 integration points + 3 OTEL events
- No Jira (personal project) — skipped by design
- TDD workflow → red phase → Fezzik (TEA) writes failing tests first