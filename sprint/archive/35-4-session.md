---
story_id: "35-4"
jira_key: "MSSCI-TBD"
epic: "MSSCI-TBD"
workflow: "tdd"
---

# Story 35-4: Wire treasure_xp into state_mutations after item acquisition

## Story Details
- **ID:** 35-4
- **Jira Key:** MSSCI-TBD (auto-create via pf jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** api (sidequest-api)
- **Points:** 3
- **Priority:** p1

## Acceptance Criteria

1. After item acquisition in state_mutations, compute gold delta from inventory changes
2. Build TreasureXpConfig from genre pack or ctx
3. Call apply_treasure_xp(&mut ctx.snapshot, gold_delta, &config, rooms)
4. Emit WatcherEventBuilder("treasure_xp", StateTransition) with applied, gold_amount, affinity_name, new_progress
5. Integration test verifying treasure_xp has a non-test consumer in state_mutations.rs

## Workflow Tracking

**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-04-09

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-09 | - | - |

## Context

`apply_treasure_xp()` in `sidequest-game/src/treasure_xp.rs` awards affinity-based XP on gold acquisition. Currently state_mutations.rs has flat 25/10 XP awards — treasure_xp adds additional affinity progress on top. It's fully implemented and tested (story 19-9) but has zero production consumers.

**Key files:**
- `sidequest-api/crates/sidequest-server/src/dispatch/state_mutations.rs` — insert after item acquisition (~line 287)
- `sidequest-api/crates/sidequest-game/src/treasure_xp.rs` — read-only, already complete

## Delivery Findings

No upstream findings.

## Design Deviations

No design deviations.
