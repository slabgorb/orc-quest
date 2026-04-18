---
story_id: "35-2"
jira_key: "MSSCI-35-2"
epic: "MSSCI-16932"
workflow: "tdd"
---

# Story 35-2: Wire entity_reference hot-path validation after NPC registry update

## Story Details

- **ID:** 35-2
- **Jira Key:** MSSCI-35-2 (creation pending — see blockers)
- **Workflow:** tdd
- **Points:** 3
- **Priority:** p1
- **Status:** in_progress
- **Stack Parent:** none (independent)

## Context

Story 35-1 wired `entity_reference` validation into the cold-path validator. This story adds **hot-path validation** — checking entity references in real-time after NPC registry update, before narration reaches the player. This enables GM panel warnings about phantom entities in real-time rather than post-hoc.

**Key files:**
- `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` — insert after `update_npc_registry()` (~line 1138)
- `sidequest-api/crates/sidequest-agents/src/entity_reference.rs` — read-only, already complete

## Acceptance Criteria

1. After `update_npc_registry()` returns, `EntityRegistry::from_snapshot(&ctx.snapshot)` is built
2. `extract_potential_references(&clean_narration)` is called on the current narration
3. For each unresolved reference, `WatcherEventBuilder::new("entity_reference", ValidationWarning)` emits with the unresolved name
4. Dispatch is NOT blocked — this is informational OTEL only
5. Integration test: dispatch with narration mentioning a non-existent NPC asserts OTEL warning fires
6. Wiring test: verify entity_reference has a non-test consumer in dispatch/mod.rs

## Workflow Tracking

**Workflow:** tdd
**Phase:** green
**Phase Started:** 2026-04-09T19:13:38Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-09T18:04:47Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** Hot-path wiring of entity_reference into dispatch pipeline requires validation

**Test Files:**
- `crates/sidequest-server/tests/entity_reference_wiring_story_35_2_tests.rs` — 10 tests (7 wiring, 3 integration)

**Tests Written:** 10 tests covering 6 ACs
**Status:** RED (7 failing, 3 passing — ready for Dev)

### Test Breakdown

| Test | AC | Type | Status |
|------|-----|------|--------|
| `dispatch_pipeline_uses_entity_reference_module` | AC-6 | wiring | FAILING |
| `dispatch_pipeline_builds_entity_registry_from_snapshot` | AC-1 | wiring | FAILING |
| `dispatch_pipeline_calls_extract_potential_references` | AC-2 | wiring | FAILING |
| `dispatch_pipeline_emits_entity_reference_validation_warning` | AC-3 | wiring | FAILING |
| `entity_reference_check_does_not_block_dispatch` | AC-4 | wiring | FAILING |
| `entity_reference_check_runs_after_update_npc_registry` | AC-1 | wiring | FAILING |
| `dispatch_otel_warning_includes_unresolved_name_field` | AC-3 | wiring | FAILING |
| `narration_with_unknown_npc_produces_unresolved_references` | AC-5 | integration | passing |
| `narration_with_only_known_npcs_produces_no_unresolved_references` | AC-5 | integration | passing |
| `multiple_unknown_npcs_each_produce_unresolved_references` | AC-5 | integration | passing |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #4 tracing | `dispatch_pipeline_emits_entity_reference_validation_warning` | failing |
| #6 test quality | Self-check: all 10 tests have meaningful assertions | passing |

**Rules checked:** 2 of 15 applicable (most rules target implementation code, not wiring tests)
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Naomi) for implementation

## Delivery Findings

### TEA (test design)
- No upstream findings during test design.

## Design Deviations

### TEA (test design)
- No deviations from spec.

## Branch & Repo Status

**Branch:** feat/35-2-wire-entity-reference-hot-path
**Repo:** sidequest-api (api)
**PR Strategy:** standard

## Blockers

**Jira creation failed with project validation error.** The story is ready for implementation but cannot be fully synced to Jira until the Jira project configuration is verified. Proceeding with implementation on the created branch.