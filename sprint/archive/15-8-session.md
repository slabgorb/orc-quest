---
story_id: "15-8"
jira_key: "none"
epic: "15"
workflow: "tdd"
---
# Story 15-8: Canonical GameSnapshot in dispatch — eliminate load-before-save round-trip on every turn

## Story Details
- **ID:** 15-8
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Epic:** 15 — Playtest Debt Cleanup — Stubs, Dead Code, Disabled Features
- **Repository:** sidequest-api (Rust backend)
- **Points:** 5
- **Priority:** p1
- **Status:** in-progress
- **Phase:** finish
- **Branch:** feat/15-8-canonical-gamesnapshot-dispatch

## Problem Statement

`persist_game_state()` in `dispatch/mod.rs` performs a full SQLite load every turn just to merge ~15 loose local variables back into a snapshot, then saves the merged result. This creates two actor-channel round-trips per player action:

1. Load round-trip: load() → request queued in persistence actor → response awaited
2. Save round-trip: save() → request queued in persistence actor → response awaited

**Root cause:** The dispatch loop scatters game state across individual locals in DispatchContext (`ctx.hp`, `ctx.inventory`, `ctx.npc_registry`, `ctx.combat_state`, etc.) instead of maintaining a canonical GameSnapshot.

## Implementation Approach

1. Carry a mutable `GameSnapshot` in `DispatchContext`
2. Patch it in-place as the turn progresses (instead of scattering to locals)
3. Save directly — one round-trip, no load needed on the hot path
4. Keep the load path for session restore on reconnect (`dispatch_connect`), which is infrequent
5. OTEL event: `persistence.save_latency_ms` (before/after comparison)

## Acceptance Criteria

- [ ] `DispatchContext` carries a canonical `GameSnapshot` instead of scattered locals
- [ ] Hot path (every turn) is save-only — no load round-trip
- [ ] Session restore on reconnect still loads from SQLite
- [ ] All existing dispatch tests pass
- [ ] OTEL span `persistence.save_latency_ms` emitted on save
- [ ] No behavioral changes to game logic

## Sm Assessment

Story 15-8 is a targeted performance optimization in the dispatch hot path. The root cause is well-understood: scattered state locals force a load-before-save pattern on every turn. The fix — carrying a canonical `GameSnapshot` in `DispatchContext` — is architecturally sound and eliminates one of two actor-channel round-trips per player action. The load path is preserved for reconnect only. TDD is the correct workflow for this 5-point story given it touches core dispatch infrastructure. Routing to TEA for RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-point story touching core dispatch infrastructure; TDD workflow mandates RED phase.

**Test Files:**
- `crates/sidequest-server/tests/canonical_snapshot_story_15_8_tests.rs` — 16 tests covering all 6 ACs

**Tests Written:** 16 tests covering 6 ACs
**Status:** RED (8 failing, 8 passing — ready for Dev)

**Failing (structural — require implementation):**
1. `dispatch_context_has_snapshot_field` — AC-1: DispatchContext needs `snapshot` field
2. `persist_game_state_does_not_load_before_save` — AC-1: Remove load() from save path
3. `persist_game_state_does_not_merge_scattered_locals` — AC-1: Remove field-by-field merging
4. `persist_game_state_uses_ctx_snapshot` — AC-1: Save ctx.snapshot directly
5. `persist_game_state_emits_save_latency_otel_event` — AC-2: OTEL save_latency_ms
6. `persist_game_state_measures_elapsed_time` — AC-2: Timing measurement
7. `persist_game_state_otel_uses_persistence_component` — AC-2: Component="persistence"
8. `lib_dispatch_context_construction_includes_snapshot` — AC-1: Wiring in lib.rs

**Passing (behavioral — infrastructure already supports approach):**
1. `snapshot_patch_in_place_preserves_fields_across_turns` — AC-3: Multi-turn mutation
2. `save_without_prior_load_succeeds` — AC-3: Save-only path works
3. `save_without_prior_load_then_load_recovers_all_fields` — AC-4/5: Full round-trip
4. `multi_turn_patch_then_save_preserves_mutations` — AC-3: Patched snapshot persists
5. `session_restore_loads_from_sqlite` — AC-4: Reconnect load path
6. `session_restore_after_multi_save_returns_latest` — AC-4: Latest save wins
7. `persist_game_state_has_error_handling_on_save` — AC-6: Error logging exists
8. `persist_game_state_traces_empty_slugs_early_return` — Rule #4: Tracing coverage

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent error swallowing | `persist_game_state_has_error_handling_on_save` | passing |
| #4 tracing coverage | `persist_game_state_traces_empty_slugs_early_return` | passing |
| #6 test quality | Self-check: no vacuous assertions found | passing |

**Rules checked:** 3 of 15 applicable (rules #2,3,5,7-15 not applicable — no new enums, constructors, public types, or Cargo.toml changes in test file)
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Yoda) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-server/src/dispatch/mod.rs` — Added `snapshot` field to DispatchContext, extracted `sync_locals_to_snapshot()` helper, rewrote `persist_game_state()` to save ctx.snapshot directly with OTEL instrumentation
- `crates/sidequest-server/src/lib.rs` — Wired `snapshot` through `dispatch_message`, `dispatch_connect`, `dispatch_character_creation`; populated canonical snapshot from persistence on reconnect and from character creation on new game

**Tests:** 16/16 passing (GREEN), full server suite 0 failures
**Branch:** feat/15-8-canonical-gamesnapshot-dispatch-v2 (pushed)

**Handoff:** To TEA for verify phase

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings | test copy-paste (high), WatcherEvent boilerplate (high, pre-existing), location extraction inconsistency (medium), DispatchContext construction duplication (medium) |
| simplify-quality | clean | No issues found |
| simplify-efficiency | 3 findings | silent fallback (high, pre-existing), encounter OTEL scope (medium), location re-parsing (low) |

**Applied:** 1 high-confidence fix — extracted `extract_fn_body()` test helper, removing ~70 LOC of duplicated function extraction code
**Flagged for Review:** 3 medium-confidence findings (WatcherEvent builder pattern, DispatchContext construction helper, encounter OTEL scope — all pre-existing patterns or out of story scope)
**Noted:** 2 items (silent fallback in location extraction is pre-existing behavior moved by this story, not introduced; location re-parsing is intentional narration-to-state flow)
**Reverted:** 0

**Overall:** simplify: applied 1 fix

**Quality Checks:** 16/16 tests passing
**Handoff:** To Reviewer (Obi-Wan) for code review

## Phase History
- **setup** — 2026-04-01 (SM)
- **red** — 2026-04-01 (TEA) — 16 tests, 8 failing
- **green** — 2026-04-01 (Dev) — 16/16 GREEN, 0 regressions
- **spec-check** — 2026-04-01 (Architect) — Skipped per project policy (personal project)
- **verify** — 2026-04-01 (TEA) — 1 simplify fix applied, 16/16 GREEN

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 1 pre-existing warning (unused clean_narration param) | dismissed 1 — pre-existing, not introduced by this story |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | error | 0 (failed to read diff) | covered by manual review + rule-checker overlap |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 0, dismissed 4 (all pre-existing patterns moved, not introduced) |

**All received:** Yes (3 spawned, 6 disabled; all spawned returned)
**Total findings:** 0 confirmed blocking, 4 dismissed (pre-existing), 1 noted for improvement

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] persist_game_state() no longer calls persistence().load() — dispatch/mod.rs:1310-1399 contains only a save() call. The load-before-save round-trip is eliminated on the hot path. Complies with AC-1.
2. [VERIFIED] OTEL persistence.save_latency_ms emitted — dispatch/mod.rs:1380-1398 sends WatcherEvent with component="persistence", save_latency_ms field. Complies with AC-2.
3. [VERIFIED] DispatchContext carries snapshot field — dispatch/mod.rs:90 adds `pub snapshot: &'a mut sidequest_game::state::GameSnapshot`. Wired through lib.rs at both DispatchContext construction sites (lib.rs:1818, lib.rs:2778). Complies with AC-1.
4. [VERIFIED] Session restore preserved �� dispatch_connect (lib.rs:1953) assigns `*snapshot = saved.snapshot.clone()` after scattering locals. The load path for reconnect is untouched. Complies with AC-4.
5. [VERIFIED] Error handling on save — dispatch/mod.rs:1399 uses tracing::warn! on Err. dispatch/mod.rs:1316 traces debug on empty slug early return. Complies with AC-6.
6. [LOW] [RULE] Pre-existing: `if let Ok(ch) = serde_json::from_value(cj.clone())` at dispatch/mod.rs:1291 silently drops character narrative_state on parse failure. Moved from old persist_game_state, not introduced. Noted for future improvement — add tracing::warn on else branch.
7. [LOW] [RULE] Pre-existing: `unwrap_or_else(|| "Starting area")` at dispatch/mod.rs:1269 clobbers snapshot.location when narrator omits location header. Same pattern existed in old code. Consider guarding with `if let Some(loc) =` in a follow-up.
8. [LOW] [RULE] Pre-existing: `timestamp: 0` on NarrativeEntry at dispatch/mod.rs:1322. Same pattern in old code. Should use `chrono::Utc::now().timestamp_millis() as u64` in a follow-up.
9. [MEDIUM] [RULE] No runtime wiring test — structural source-scanning tests verify wiring exists but don't exercise the WebSocket→dispatch→persist pipeline end-to-end. Acceptable for this story's scope; a full e2e test is heavy infrastructure.
10. [VERIFIED] sync_locals_to_snapshot correctly syncs all dispatch-relevant fields — turn_manager, npc_registry, genie_wishes, axis_values, combat, chase, encounter, discovered_regions, active_tropes, achievement_tracker, quest_log, resource_state, and character stats. dispatch/mod.rs:1267-1307.

### Data Flow Traced
Player action → dispatch_player_action → sync_locals_to_snapshot (patches ctx.snapshot from scattered locals) → persist_game_state (appends narrative entry, saves ctx.snapshot directly via PersistenceHandle::save, emits OTEL). Safe: no load round-trip, snapshot is canonical, save failure is traced.

### Rule Compliance
- **#1 silent errors:** Pre-existing character_json parse swallow moved, not introduced. No new violations.
- **#3 placeholders:** Pre-existing "Starting area" fallback and timestamp:0 moved, not introduced.
- **#4 tracing:** New persist_game_state has proper tracing on all paths. Pre-existing gap in character_json parse path (moved).
- **#9 public fields:** DispatchContext.snapshot is pub on a pub(crate) struct — compliant.

### Devil's Advocate

What if this code is broken? The `sync_locals_to_snapshot` function clones ~15 fields from scattered locals into the snapshot on every turn. If any field is added to DispatchContext in a future story but NOT added to sync_locals_to_snapshot, that field will silently fail to persist — the snapshot will have stale data for that field. This is the classic "sync two representations" problem. The old code had the same issue (fields added to persist_game_state's merge block), so this isn't a regression, but the Dev Assessment correctly identifies this as a reason to eventually migrate to direct snapshot patching.

What about the `saved.snapshot.clone()` in dispatch_connect? If the snapshot is large (many NPCs, long narrative_log), this clone could be expensive. But it only happens on reconnect (infrequent path), so the performance impact is negligible.

Could a race condition exist? The snapshot is owned by the session handler's local scope and passed as `&mut` — Rust's borrow checker prevents concurrent access. No race possible.

What if `genre_slug` or `world_slug` is empty after character creation? The guard at dispatch/mod.rs:1315 returns early with a debug trace. But this means the initial save in dispatch_character_creation (lib.rs:2664) is the only save — subsequent turns would silently skip persistence. However, session.genre_slug() is populated during dispatch_connect before any player action can fire, so this path is unreachable in practice.

The devil's advocate found no new issues beyond the noted pre-existing patterns.

[EDGE] No new edge cases found beyond pre-existing patterns.
[SILENT] Pre-existing silent character_json parse failure noted (dispatch/mod.rs:1291).
[TEST] 16/16 tests GREEN, structural coverage adequate for story scope.
[DOC] Comments on new functions are clear and reference story 15-8.
[TYPE] No new type design issues — snapshot field is correctly typed as `&'a mut GameSnapshot`.
[SEC] No security-relevant changes — no auth, no user input parsing, no tenant isolation concerns.
[SIMPLE] sync_locals_to_snapshot is the minimal approach given the 1950-line dispatch function.
[RULE] 4 pre-existing rule violations moved (not introduced) — all LOW severity.

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story

## Phase History

### TEA (test design)
- No upstream findings during test design.

### TEA (test verification)
- No upstream findings during test verification.

### Reviewer (code review)
- **Improvement** (non-blocking): `sync_locals_to_snapshot` character_json parse failure (dispatch/mod.rs:1291) should add `tracing::warn!` on the else branch. Pre-existing pattern moved from old persist_game_state. Affects `crates/sidequest-server/src/dispatch/mod.rs` (add else branch with warn). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): NarrativeEntry `timestamp: 0` at dispatch/mod.rs:1322 should use `chrono::Utc::now().timestamp_millis() as u64`. Pre-existing. Affects `crates/sidequest-server/src/dispatch/mod.rs` (fix timestamp). *Found by Reviewer during code review.*

### Dev (implementation)
- **Improvement** (non-blocking): The `sync_locals_to_snapshot()` helper syncs ~15 fields from scattered locals to snapshot before every persist. A follow-up story could migrate dispatch_player_action to patch ctx.snapshot directly during the turn, eliminating this sync step entirely. Affects `crates/sidequest-server/src/dispatch/mod.rs` (sync_locals_to_snapshot could be removed). *Found by Dev during implementation.*

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **Sync-before-persist instead of patch-during-turn**
  - Spec source: context-story-15-8.md, Phase 2
  - Spec text: "Identify all lines in dispatch_player_action() that mutate loose locals... Add equivalent mutations to ctx.snapshot"
  - Implementation: Added sync_locals_to_snapshot() called once before persist, instead of patching ctx.snapshot at each mutation site throughout the 1950-line function
  - Rationale: Changing every mutation site in dispatch_player_action would touch hundreds of lines and risk regressions. The sync approach achieves the same result (no load round-trip, save-only hot path) with minimal blast radius. The full migration is a separate story.
  - Severity: minor
  - Forward impact: Stories 15-9, 15-20 can build on ctx.snapshot directly; sync_locals_to_snapshot shrinks as more code patches snapshot in-place
  - → ✓ ACCEPTED by Reviewer: Sound incremental approach. Full migration would be a separate story touching 1950 lines. The sync achieves the stated goal (eliminate load round-trip).

### Reviewer (audit)
- No undocumented deviations found.