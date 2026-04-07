---
parent: context-epic-28.md
---

# Story 28-13: Dead Export Cleanup

## Business Context

The 2026-04-06 audit found 22 API pub exports and 9 UI exports with zero non-test
consumers. After the encounter unification (28-9 deletes many combat/chase related
exports), audit what remains and remove or downgrade to pub(crate).

## Technical Approach

### API exports to evaluate (post 28-9)

Many of these will be gone after 28-9 deletes combat.rs, chase.rs, etc. Audit the
survivors:

**sidequest-game:**
- `dedup_window` (beat_filter.rs:148) — accessor, likely unused
- `format_narrator_context` (scenario_state.rs:377) — Epic 7 scenario system, check 7-9 dependency
- `handle_accusation` (scenario_state.rs:354) — Epic 7, check 7-9 dependency
- `last_narration` (multiplayer.rs:285) — check if 26-4/26-5 needs it
- `requires_npc_knowledge` (clue_activation.rs:159) — Epic 7
- `try_claim_resolution` (barrier.rs:385) — check if multiplayer needs it
- `with_dedup_window` (beat_filter.rs:112) — builder, unused
- `with_prompt_fragment` (subject.rs:110) — builder, unused

**sidequest-agents:**
- `acquire_footnote` (tools/lore_mark.rs:55) — check if lore pipeline uses it
- `add_ambiguity_context` (intent_router.rs:281) — check if encounter changes use it
- `send_with_tools` (client.rs:132) — tool-use client path
- `transact_merchant` (tools/merchant_transact.rs:47) — check 15-16 wiring
- `troper` / `troper_mut` (orchestrator.rs:264/269) — troper agent accessors
- `with_client` (agents/resonator.rs:152) — resonator builder

**sidequest-server:**
- `debug_state` (debug_api.rs:59) — debug endpoint
- `describe_player_effects` (shared_session.rs:271) — perception
- `has_perception_effects` (shared_session.rs:265) — perception
- `loadoutgen_binary_path` (lib.rs:522) — CLI tool path
- `new_with_options` (lib.rs:451) — constructor variant
- `trace` (lib.rs:182) — logging helper

### UI exports to evaluate

- CartographyMetadata/Region/Route/ExploredLocation (MapOverlay.tsx) — check 26-10
- buttonVariants (button.tsx) — shadcn pattern, may be required by convention
- toggleVariants (toggle.tsx) — same
- CreationChoice (CharacterCreation.tsx) — type, no consumers
- OverlayManagerProps (OverlayManager.tsx) — remove export, keep type
- TurnModeIndicatorProps (TurnModeIndicator.tsx) — remove export, keep type

### Decision per export

For each: verify still unused after 28-9. Then:
- If truly dead → remove entirely or make `pub(crate)`
- If needed by a backlog story (7-9, 26-4, 26-5) → leave but add `// Used by story X-Y` comment
- If shadcn convention → leave (buttonVariants, toggleVariants)

## Key Files

All files listed above — this is a sweep story.

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| Audit complete | Every export from the 2026-04-06 list has a disposition (removed, kept with reason, or gone after 28-9) | Documented in session file |
| Removed exports | Dead exports with no backlog dependency are removed or pub(crate) | Grep: each removed name no longer in public API |
| Backlog preserved | Exports needed by 7-9, 26-4, 26-5 are kept with comments | Grep: comment references story ID |
| Builds clean | Full workspace builds | `cargo build` + `npm run build` |
| Tests pass | Full test suites pass | `cargo test` + `npm test` |

## Scope Boundaries

**In scope:** Auditing and removing dead exports found in the 2026-04-06 wiring audit
**Out of scope:** Finding new dead exports (future audit)
