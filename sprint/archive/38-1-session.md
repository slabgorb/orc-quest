---
story_id: "38-1"
jira_key: ""
epic: "38"
workflow: "tdd"
---
# Story 38-1: ResolutionMode enum and resolution_mode field on ConfrontationDef

## Story Details
- **ID:** 38-1
- **Jira Key:** (pending)
- **Epic:** 38 (Dogfight Subsystem — Sealed-Letter Fighter Combat via StructuredEncounter)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 2

## Acceptance Criteria
- ResolutionMode enum created with BeatSelection as default variant
- resolution_mode field added to ConfrontationDef struct
- Field is properly serialized/deserialized via serde
- Existing confrontations continue to work without modification (zero runtime impact)
- All tests passing

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-04-13T16:31:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-13T00:00:00Z | 2026-04-13T16:31:33Z | 16h 31m |
| red | 2026-04-13T16:31:33Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No design deviations recorded.

## Sm Assessment

**Story scope:** Additive-only change to `sidequest-api` protocol/genre types. Introduce `ResolutionMode` enum with `BeatSelection` default and add `resolution_mode: ResolutionMode` field to `ConfrontationDef`. Serde must default missing field to `BeatSelection` so existing genre packs and saved sessions load unchanged.

**Technical approach (for TEA):**
- Locate `ConfrontationDef` in `sidequest-genre` (or wherever confrontations are defined) and add the enum alongside it.
- Use `#[serde(default)]` on the new field and `#[derive(Default)]` on the enum (or `#[serde(default = "...")]`) so YAML without `resolution_mode` still deserializes.
- Serde round-trip tests: absent field → `BeatSelection`; explicit variants round-trip; existing fixture genre packs still load.
- Enum variants at minimum: `BeatSelection` (default). Epic 38 will add `Dogfight` in a later story — check epic-38 context for whether this story pre-declares additional variants or only `BeatSelection`. If unclear, TEA should flag as a Delivery Finding rather than guess.

**Acceptance:** Existing confrontations load unchanged (zero runtime impact), new field serializes, enum is extensible for Epic 38 follow-ups.

**Risks:** Only risk is forgetting `#[serde(default)]`, which would break every existing genre pack on load. TEA's failing tests must cover the "field absent in YAML" case explicitly.

**Jira:** Not tracked in Jira (no key).