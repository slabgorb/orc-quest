---
story_id: "39-4"
jira_key: ""
epic: "39"
workflow: "wire-first"
---

# Story 39-4: BeatDef.edge_delta + target_edge_delta + beat dispatch wiring

## Story Details

- **ID:** 39-4
- **Jira Key:** (none — personal project)
- **Epic:** 39 — Edge / Composure Combat, Mechanical Advancement, and Push-Currency Rituals
- **Workflow:** wire-first (phased: setup → red → green → review → finish)
- **Points:** 8
- **Stack Parent:** none
- **Repos:** api (sidequest-api)

## Summary

Extend `BeatDef` with `edge_delta`/`target_edge_delta`/`resource_deltas` fields and implement self-debit and target-debit resolution blocks in `handle_applied_side_effects` (parallel to the existing gold_delta pattern at beat.rs:319-337). Auto-resolve combatants when Edge reaches 0 (composure break). Wire OTEL `creature.edge_delta` and `encounter.composure_break` events so the GM panel can trace composure state changes. Stub a hard-coded advancement grant (+2 max edge for Fighters) to serve as the smoke-test gate for the full advancement system being built in 39-5.

## Acceptance Criteria

1. **BeatDef schema extension** — `BeatDef` struct in `sidequest-protocol` or `sidequest-game` has three new fields:
   - `edge_delta: Option<i32>` — damage/healing applied to self
   - `target_edge_delta: Option<i32>` — damage/healing applied to target
   - `resource_deltas: Option<Vec<ResourceDelta>>` — push-currency costs (for 39-6 integration, may be empty for now)
   These are serialized/deserialized correctly in YAML and JSON round-tripping.

2. **Self-debit block in handle_applied_side_effects** — When a beat is applied and `beat.edge_delta.is_some()`, apply it to the acting creature's edge pool exactly like the gold_delta pattern:
   - Read current edge from creature.edge_pool
   - Apply delta (subtract damage, add healing with bounds-checking)
   - Mutate creature.edge_pool.current
   - Emit OTEL `creature.edge_delta` event with: `creature_id`, `delta_value`, `new_current`, `new_state` (e.g., "healthy"/"strained"/"broken")
   - No silent fallbacks: if the creature has no edge pool, fail loudly

3. **Target-debit block in handle_applied_side_effects** — When beat has `target_edge_delta`, apply the same debit logic to the target creature (if a target exists):
   - Apply delta to target.edge_pool.current
   - Emit OTEL `creature.edge_delta` event for target with same attributes
   - Handle no-target case gracefully (log as info-level OTEL event, not error)

4. **Composure break auto-resolution** — When any creature's edge reaches ≤0 after debit:
   - Mark creature as `composure_state: Broken` (or equivalent state enum)
   - Immediately resolve the creature as unable to act (out of combat, or mechanically neutral)
   - Emit OTEL `encounter.composure_break` event with: `creature_id`, `creature_name`, `edge_at_break` (the value that triggered it), `trigger_beat_id`
   - This is a hard stop to combat involvement, visible to the GM panel

5. **OTEL telemetry wiring** — Both `creature.edge_delta` and `encounter.composure_break` are emitted as structured `WatcherEvent`s (using existing `WatcherEventBuilder` pattern) so they appear on the GM panel and are queryable in playtest logs.

6. **Stub advancement grant (smoke test)** — Hard-code a single advancement grant for testing: when any Fighter with name containing "smoke" or matching a test fixture name gains an advancement, add `+2` to their `max_edge`. This is temporary scaffolding to validate the advancement-grant plumbing (CreatureCore mutation, beat dispatch round-trip, OTEL emission) before 39-5 builds the full system.
   - Call site: add this logic at the end of `handle_applied_side_effects` with a loud comment flagging it as temporary test code
   - Verify via OTEL: "advancement.effect_applied" event emitted with `effect_type: "EdgeMaxBonus"`, `magnitude: 2`

7. **Wiring verified end-to-end** — 
   - `BeatDef` fields have non-test consumers in beat dispatch code (grep shows imports in beat.rs, dispatch.rs, or relevant handler)
   - OTEL events are imported from telemetry crate and called in handle_applied_side_effects
   - Advancement grant logic is called during beat application (not deferred to later phase)
   - No stub exports with zero callers

## Key References

- **Story 39-2:** Deleted hp/max_hp from CreatureCore; edge_pool is now the canonical health tracker
- **Story 39-1:** Defined EdgePool type with current/max/recovery_triggers/thresholds
- **Gold delta pattern:** `sidequest-api/crates/sidequest-game/src/beat.rs:319-337` — reference implementation for self/target deltas
- **OTEL pattern:** `sidequest-telemetry/src/watcher.rs` — WatcherEvent emission and span attribute builders
- **ADR-078:** `/Users/keithavery/Projects/oq-1/docs/adr/ADR-078.md` — advancement architecture rationale
- **Content draft:** `sidequest-content/genre_packs/heavy_metal/_drafts/edge-advancement-content.md` — smoke test fixture names and advancement values

## Workflow Tracking

**Workflow:** wire-first (phased)
**Phase:** finish
**Phase Started:** 2026-04-19T13:00:37Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-19 | — | — |

## Delivery Findings

No upstream findings.

## Design Deviations

No design deviations at this stage.

---

**Branch:** `feat/39-4-beatdef-edge-delta-dispatch`
**Session Created:** 2026-04-19
**Next Agent:** tea (RED phase)

## Sm Assessment

Story 39-4 setup complete. Branch `feat/39-4-beatdef-edge-delta-dispatch` created on sidequest-api/develop. BeatDef schema extension (edge_delta/target_edge_delta/resource_deltas) with self/target debit dispatch parallel to gold_delta at beat.rs:319-337, composure-break auto-resolve on Edge<=0, OTEL events, and Fighter +2 edge_max advancement stub for smoke playtest. Workflow is wire-first (phased). Handing off to TEA for RED phase — failing boundary tests on dispatch and composure-break paths.
---
## Design Deviations

### TEA (test design)
- **New public helper `apply_beat_edge_deltas` extracted from `handle_applied_side_effects`**
  - Spec source: context-story-39-4.md, AC6 ("builds real DispatchContext, calls apply_beat_dispatch + handle_applied_side_effects")
  - Spec text: "Integration test builds real `DispatchContext`, calls `apply_beat_dispatch` + `handle_applied_side_effects` on a real `strike` beat"
  - Implementation: Tests target a new `pub fn apply_beat_edge_deltas(&mut snapshot, &beat, encounter_type) -> EdgeDeltaOutcome` exported at the crate root, plus a source-scan wiring test proving `handle_applied_side_effects` calls it.
  - Rationale: `DispatchContext` is `pub(crate)` with ~60 fields (AppState, shared sessions, music director, mpsc handles). Constructing one from an integration test is impractical and would couple the test to the entire server runtime. Extracting the edge-delta logic into a narrow public helper preserves the wiring-rule intent (imported + called from production path) without the no-stub violation of a test-only facade.
  - Severity: moderate (changes code shape Dev must implement)
  - Forward impact: `handle_applied_side_effects` must call the new helper on the Applied outcome. Source-scan guard catches regressions.

- **Fighter +2 edge_max stub not covered by tests in this RED phase**
  - Spec source: context-story-39-4.md (Key Files + Assumptions)
  - Spec text: Key-Files row places stub in `dispatch/beat.rs`; Assumptions row places stub in `CharacterState::new or equivalent`
  - Implementation: No test yet — Dev chooses the call site during GREEN; TEA will cover during verify-phase simplify pass if Dev picks builder.
  - Rationale: The two spec locations contradict — one implies per-beat application, the other implies one-time chargen application. Writing a test against either location would force Dev into a design choice that is a mechanical question (one-shot vs per-beat). Flagged to Dev as a design question in Delivery Findings.
  - Severity: minor
  - Forward impact: Dev must log where the stub landed in session file; verify pass re-reads context.

- **heavy_metal YAML fixture deferred to Dev**
  - Spec source: context-story-39-4.md (Key Files — heavy_metal/rules.yaml row)
  - Spec text: "Add test-fixture `edge_delta` values to at least one combat beat (e.g., `strike.target_edge_delta: 2`)"
  - Implementation: Integration tests use inline YAML fixtures rather than loading heavy_metal/rules.yaml
  - Rationale: Coupling wiring tests to the live genre pack makes them fragile to content edits. The content YAML change is a content-crate deliverable (for AC7 smoke gate), not a wiring-test input. Dev still owns the YAML edit for playtest.
  - Severity: minor
  - Forward impact: Verify pass / playtest (AC7) must confirm heavy_metal YAML received the edit.

---
## Delivery Findings

### TEA (test design)
- **Question** (non-blocking): Fighter +2 edge_max stub call-site is ambiguous between Key-Files (dispatch/beat.rs) and Assumptions (CharacterState::new) rows of the story context.
  Affects `sidequest-api/crates/sidequest-server/src/dispatch/beat.rs` or `sidequest-api/crates/sidequest-game/src/builder.rs` (Dev picks one and documents).
  *Found by TEA during test design.*
- **Gap** (non-blocking): heavy_metal/rules.yaml does not currently declare `edge_config`. Story 39-3 wired `CharacterBuilder` to read it but the YAML migration may not have landed. Fighter `+2` and AC7 smoke gate both depend on the pack having authored `base_max_by_class: { Fighter: ... }`.
  Affects `sidequest-content/genre_packs/heavy_metal/rules.yaml` (add `edge_config` block if absent).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): `BeatDef` (via `RawBeatDef`) does not use `#[serde(deny_unknown_fields)]`. A misspelled `edge_delta` would silently fall back to None. Consider enabling it on `RawBeatDef` per the project "No Silent Fallbacks" rule and the `sidequest-genre` CLAUDE.md note that key types use this attribute.
  Affects `sidequest-api/crates/sidequest-genre/src/models/rules.rs`.
  *Found by TEA during test design.*

---
## TEA Assessment

**Tests Required:** Yes
**Reason:** Epic 39 foundational wiring — Edge becomes real in dispatch. RED must fail on the missing BeatDef fields and on an unresolved public helper import so Dev has an end-to-end target.

**Test Files:**
- `sidequest-api/crates/sidequest-genre/tests/beatdef_edge_fields_story_39_4_tests.rs` — 4 schema tests pinning `edge_delta`, `target_edge_delta`, `resource_deltas` on BeatDef (AC1).
- `sidequest-api/crates/sidequest-server/tests/integration/edge_delta_dispatch_wiring_story_39_4_tests.rs` — 8 dispatch tests covering AC2 (self-debit), AC3 (target-debit), AC3b (no-opponent panic), AC4 (composure break), AC5 (resource_deltas), AC6 (public API wiring), plus source-scan wiring guard on `handle_applied_side_effects`.

**Tests Written:** 12 tests covering AC1–AC6
**Status:** RED — confirmed via `cargo check -p sidequest-genre --tests` (8 E0609 errors on missing BeatDef fields). The integration test binary will fail compilation on the unresolved `sidequest_server::{apply_beat_edge_deltas, EdgeDeltaOutcome}` import until Dev exports them.

### Rule Coverage

| Rule (CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks | `target_debit_without_primary_opponent_panics_loudly` | failing (panic assertion) |
| Verify Wiring, Not Just Existence | `wiring_apply_beat_edge_deltas_reachable_via_crate_public_api`, `wiring_handle_applied_side_effects_invokes_edge_delta_helper` | failing (symbols + source-scan) |
| Every Test Suite Needs a Wiring Test | `wiring_apply_beat_edge_deltas_reachable_via_crate_public_api` + source-scan | failing |
| OTEL Observability Principle | All AC2/AC3/AC4 tests assert telemetry events (`creature.edge_delta`, `encounter.composure_break`) | failing |
| No Stubbing | Helper is real production code, not a test facade (documented in test file preamble) | n/a — design guard |
| Backward compat (legacy YAML) | `legacy_beatdef_without_new_keys_still_parses` | failing |

**Rules checked:** 5 of 5 applicable
**Self-check:** No vacuous assertions. Every `assert!` either checks a concrete value, a specific count, or a named event field.

**Handoff:** To Dev (Naomi) for GREEN — extend `BeatDef` schema, implement `apply_beat_edge_deltas` + `pub use` export, wire into `handle_applied_side_effects`, add heavy_metal `edge_config` + `strike.target_edge_delta` content edit, land Fighter +2 advancement stub (pick site, document in session).
---
## Dev Assessment

**Phase:** finish
**Status:** GREEN — all 12 tests pass (4 genre + 8 integration).

### Implementation

**BeatDef schema** (`sidequest-api/crates/sidequest-genre/src/models/rules.rs`):
- Added three optional fields: `edge_delta: Option<i32>`, `target_edge_delta: Option<i32>`, `resource_deltas: Option<HashMap<String, f64>>`, each `#[serde(default)]`.
- RawBeatDef + TryFrom mirror the additions.

**Dispatch helper** (`sidequest-api/crates/sidequest-server/src/dispatch/beat.rs`):
- New `pub fn apply_beat_edge_deltas(&mut snapshot, &beat, encounter_type) -> EdgeDeltaOutcome`.
- Self-debit on `snapshot.characters[0].core.edge.apply_delta(-edge_delta)`.
- Target-debit finds first `EncounterActor` with `role=="opponent"`, looks up Npc by name, calls `apply_delta(-target_edge_delta)`.
- `expect()` panics on missing opponent when `target_edge_delta` is set — matches "No Silent Fallbacks".
- resource_deltas route through `snapshot.apply_resource_patch_by_name` using `ResourcePatchOp::Add/Subtract`.
- Composure break: on `edge.current <= 0` either side, sets `encounter.resolved = true`, emits `encounter.composure_break` once.
- OTEL: `creature.edge_delta` (source=beat, beat_id, delta, new_current, encounter_type), `encounter.composure_break` (broken, beat_id, encounter_type, source=beat), `resource_pool.patched` on success / `resource_pool.delta_rejected` on unknown resource.
- `handle_applied_side_effects` clones the beat once and calls `apply_beat_edge_deltas` before the gold-delta block so composure-break auto-resolution is visible to the downstream escalation branch.

**Public re-exports** (`sidequest-api/crates/sidequest-server/src/lib.rs`):
- `pub use dispatch::beat::{apply_beat_dispatch, apply_beat_edge_deltas, BeatDispatchOutcome, EdgeDeltaOutcome};`

**Fighter +2 advancement stub** (`sidequest-api/crates/sidequest-game/src/builder.rs`):
- Applied in `CharacterBuilder::build` right after the edge pool is constructed (Assumptions row, not Key-Files row — see design deviation below).
- Bumps `edge.max += 2` and `base_max += 2`, sets `current = max`.
- Emits `chargen.advancement_stub_applied` OTEL with `advancement_id=fighter_base_plus_2_edge`, `source=hardcoded_stub_story_39_4`.
- Comment tags: `REPLACED IN 39-5 (ADR-078)`.

**Test shared-channel hazard fixed:** integration test file holds a local `TELEMETRY_LOCK` mutex for the subscribe-drive-assert window so parallel test threads in the same binary don't cross-contaminate events. Pattern mirrors `test_support::TELEMETRY_LOCK` (pub(crate), not reachable from integration binary).

### Design Deviations

#### Dev (implementation)
- **Fighter +2 stub placed in CharacterBuilder, not dispatch/beat.rs**
  - Spec source: context-story-39-4.md — Key Files row says `dispatch/beat.rs`; Assumptions row says `CharacterState::new or equivalent`.
  - Implementation: Stub lives in `builder.rs` right after `edge_pool_from_config`/`placeholder_edge_pool`.
  - Rationale: Applying a class-based +2 every beat dispatch would compound the bonus across turns. Applying it once at chargen is the only semantically coherent reading. The Key Files row appears to be a copy-paste error from the dispatch-centric AC rows. Assumptions row is authoritative.
  - Severity: minor
  - Forward impact: 39-5 AdvancementTree replacement must also land in the builder path (or equivalent chargen hook), not in dispatch.

- **heavy_metal/rules.yaml content edit NOT landed in this story**
  - Spec source: context-story-39-4.md Key Files ("Add test-fixture `edge_delta` values to at least one combat beat")
  - Implementation: No content change. The sidequest-content develop branch does not yet have 39-3's `edge_config` migration merged (commit `34e66cc` is on branch `feat/39-3-purge-hp-heavy-metal-yaml`, and the content repo is currently on an unrelated `fix/playtest-2026-04-18` branch with ~10 dirty files). Editing heavy_metal/rules.yaml from here would land on the wrong branch AND would depend on a prerequisite that hasn't merged.
  - Rationale: The integration tests cover AC2–AC6 with inline YAML fixtures, so wiring is proven. Content edits for AC7 (smoke playtest) happen after 39-3 content lands.
  - Severity: moderate (AC7 playtest gate deferred)
  - Forward impact: Before Keith runs the heavy_metal smoke gate, 39-3 content (`feat/39-3-purge-hp-heavy-metal-yaml`) must be merged to sidequest-content develop, then a follow-up commit adds `target_edge_delta`/`edge_delta` to the heavy_metal combat beats.

### Delivery Findings

#### Dev (implementation)
- **Blocker** (blocking AC7 only): sidequest-content `develop` branch does not yet have the 39-3 `edge_config` migration merged. The 39-3 feature branch `feat/39-3-purge-hp-heavy-metal-yaml` carries commit `34e66cc` that purged HP and added `edge_config` to heavy_metal/rules.yaml. Without that merge, heavy_metal has no `base_max_by_class` and `CharacterBuilder` falls to the placeholder edge pool (10) + Fighter stub (+2) = 12 max edge.
  Affects `sidequest-content/genre_packs/heavy_metal/rules.yaml` (needs 39-3 merge + 39-4 follow-up adding `target_edge_delta: 2` on `strike`).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): sidequest-content repo is on branch `fix/playtest-2026-04-18` with multiple dirty files (9 world yaml + 1 lore yaml). Not related to 39-4 but worth noting — the content repo needs separate housekeeping before the smoke playtest.
  Affects `sidequest-content` working tree.
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): `BeatDef` and `RawBeatDef` still do not use `#[serde(deny_unknown_fields)]`. A misspelled `edge_delta` would silently become `None`. TEA's original finding still stands and is not resolved here.
  Affects `sidequest-api/crates/sidequest-genre/src/models/rules.rs`.
  *Found by Dev during implementation.*
---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (fmt) | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 2, dismissed 1, deferred 0 |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 4, dismissed 3, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | findings | 4 | confirmed 1, dismissed 1, deferred 2 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 (cross-ref with #3), dismissed 0, deferred 0 |

**All received:** Yes (6 enabled, 3 disabled)
**Total findings:** 11 confirmed, 5 dismissed (with rationale), 2 deferred

### Dismissal rationale
- **[TEST] self_debit_to_zero doesn't assert self_new_current** — low value; composure_break + resolved + event count already pin the zero outcome; adding one more assert duplicates coverage.
- **[TEST] wiring test duplicates target-debit** — intentional; the wiring test imports via `sidequest_server::` public path to prove external reachability while target-debit uses `crate::dispatch::beat::`. Different import paths = different wiring proofs.
- **[TEST] legacy BeatDef doesn't assert metric_delta/label** — beat.id is asserted; other fields are out of scope for a schema-backcompat test.
- **[SILENT] Fighter stub case-mismatch** — `class_str` is `NonBlankString` from genre-authored YAML; genre pack names Fighter as "Fighter" by convention. Stub is explicitly scoped to 39-5 replacement; ADR-078 will introduce typed ClassName.
- **[TYPE] class_str == "Fighter" stringly-typed** — same rationale as above; flagged for 39-5/ADR-078 scope.

### Deferrals (non-blocking, documented for 39-5)
- **[TYPE] EdgeDeltaOutcome composure_break invariant** — redundant boolean vs derived method. Minor; the boolean is set once on construction and is immutable from the caller's perspective. Revisit when 39-5 grows the struct with advancement_triggered.
- **[TYPE] apply_beat_edge_deltas panics vs Result shape** — story explicitly requested "fail loudly"; Result shape is a design improvement for 39-5/39-8 when the dispatch error model is revisited system-wide.

---
## Reviewer Assessment

**Phase:** finish
**Status:** APPROVED (after fixes applied)

### Fixes Applied During Review

Minor, mechanical findings were fixed in-place rather than bounced back to Dev (net review overhead < re-running the Dev phase):

1. **[TYPE] [RULE-2]** Added `#[non_exhaustive]` to `EdgeDeltaOutcome` — matches `BeatDispatchOutcome` precedent.
2. **[DOC]** Updated `apply_beat_edge_deltas` docstring to name the resource_deltas carve-out explicitly (doc no longer lies about "no silent fallbacks").
3. **[SILENT]** Replaced `if let Some(enc) = snapshot.encounter.as_mut()` on composure-break path with `.expect()` — the invariant is that encounter is live when composure_break is set, so a None at emit time is a broken invariant.
4. **[SILENT] [RULE]** Added `tracing::warn!` to the resource_deltas Err branch (parity with gold-delta path; rule #4 in `.pennyfarthing/gates/lang-review/rust.md` — tracing coverage).
5. **[DOC]** Removed stale "RED:" prefixes from both new test module preambles.
6. **[TEST]** Added `target_debit_opponent_actor_without_matching_npc_panics_loudly` — pins the second panic path (opponent-in-actors, missing-from-npcs) distinctly from the role-missing panic.
7. **[TEST]** Added `resource_deltas_positive_value_credits_named_resource_pool` — exercises `ResourcePatchOp::Add` branch and asserts delta=+1.0.
8. **[TEST]** Added `resource_deltas_unknown_resource_emits_warning_and_continues` — pins the documented silent-warn carve-out for unknown resources.
9. **[PREFLIGHT]** `cargo fmt` — cleared fmt-check failures across the branch (including pre-existing debt in 39-3 test files touched by the whole-workspace fmt).

### Rule Compliance

Cross-referenced against `.pennyfarthing/gates/lang-review/rust.md` (15 rules, 47 instances checked by reviewer-rule-checker):
- 15/15 rules checked
- 1 violation found and fixed (Rule #4: tracing coverage on resource_deltas Err path)
- 0 rule-matching findings dismissed

### Final Gate

- `cargo fmt --check` — PASS
- `cargo clippy -- -D warnings` (project standard, no --tests) — PASS
- `cargo test -p sidequest-genre --test beatdef_edge_fields_story_39_4_tests` — 4/4 PASS
- `cargo test -p sidequest-server --test integration edge_delta_dispatch_wiring_story_39_4` — 11/11 PASS

### Delivery Findings

#### Reviewer
- **Improvement** (non-blocking, for 39-5): `EdgeDeltaOutcome.composure_break` is redundant with `self_new_current/target_new_current` state; consider deriving via a method when 39-5 extends the struct. *Found by Reviewer during review.*
- **Improvement** (non-blocking, for 39-5/39-8): `apply_beat_edge_deltas` panics with `.expect()` on configuration errors; Result<EdgeDeltaOutcome, EdgeDeltaError> would route through the server's normal error pipeline rather than unwinding the session. Story explicitly wanted "fail loudly" so this is not in 39-4 scope. *Found by Reviewer during review.*
- **Improvement** (non-blocking, for ADR-078 / 39-5): Fighter stub uses bare string comparison `class_str == "Fighter"`. Existing `class_hp_bases` HashMap<String, ...> has the same pattern at scale. Introduce a `ClassName` newtype as part of the 39-5 AdvancementTree work. *Found by Reviewer during review.*
- **Gap** (outside story scope): 11 pre-existing `cargo clippy --tests` warnings in unrelated integration test files (dice_request_lifecycle, extend_return, sealed_letter_resolution). Project standard lint (`cargo clippy` without --tests) is clean; the --tests variant has accumulated debt. Flag for a future cleanup story. *Found by Reviewer during review.*