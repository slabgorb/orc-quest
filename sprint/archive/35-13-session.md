---
story_id: "35-13"
jira_key: "MSSCI-35-13"
epic: "MSSCI-35"
workflow: "tdd"
---
# Story 35-13: OTEL watcher events for chargen subsystems — stats, backstory, hp_formula + AudioVariation fallback

## Story Details
- **ID:** 35-13
- **Jira Key:** MSSCI-35-13
- **Epic:** MSSCI-35 (Wiring Remediation II — Unwired Modules, OTEL Blind Spots, Dead Code)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p1
- **Type:** chore

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-10T12:49:10Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-10T10:43:22Z | 2026-04-10T10:48:25Z | 5m 3s |
| red | 2026-04-10T10:48:25Z | 2026-04-10T11:01:39Z | 13m 14s |
| green | 2026-04-10T11:01:39Z | 2026-04-10T11:14:41Z | 13m 2s |
| spec-check | 2026-04-10T11:14:41Z | 2026-04-10T11:16:39Z | 1m 58s |
| verify | 2026-04-10T11:16:39Z | 2026-04-10T11:28:30Z | 11m 51s |
| review | 2026-04-10T11:28:30Z | 2026-04-10T11:37:22Z | 8m 52s |
| red | 2026-04-10T11:37:22Z | 2026-04-10T11:42:39Z | 5m 17s |
| green | 2026-04-10T11:42:39Z | 2026-04-10T11:48:39Z | 6m |
| spec-check | 2026-04-10T11:48:39Z | 2026-04-10T11:50:11Z | 1m 32s |
| verify | 2026-04-10T11:50:11Z | 2026-04-10T11:53:28Z | 3m 17s |
| review | 2026-04-10T11:53:28Z | 2026-04-10T12:05:28Z | 12m |
| spec-reconcile | 2026-04-10T12:05:28Z | 2026-04-10T12:07:28Z | 2m |
| finish | 2026-04-10T12:07:28Z | 2026-04-10T12:29:23Z | 21m 55s |
| red | 2026-04-10T12:29:23Z | 2026-04-10T12:32:30Z | 3m 7s |
| green | 2026-04-10T12:32:30Z | 2026-04-10T12:37:07Z | 4m 37s |
| spec-check | 2026-04-10T12:37:07Z | 2026-04-10T12:38:19Z | 1m 12s |
| verify | 2026-04-10T12:38:19Z | 2026-04-10T12:41:49Z | 3m 30s |
| review | 2026-04-10T12:41:49Z | 2026-04-10T12:47:44Z | 5m 55s |
| spec-reconcile | 2026-04-10T12:47:44Z | 2026-04-10T12:49:10Z | 1m 26s |
| finish | 2026-04-10T12:49:10Z | - | - |

## Story Context

This story adds OTEL watcher events to three chargen (character generation) subsystems that currently have zero observability:

1. **stats** — Character attribute calculation and advancement
2. **backstory** — Character history generation and narrative context
3. **hp_formula** — Hit point calculation and scaling

Plus: **AudioVariation fallback** — When the main audio variation path fails, emit a fallback event so the GM panel shows which subsystem recovered gracefully.

### Subsystem Locations

- **stats:** `sidequest-api/crates/sidequest-game/src/chargen/stats.rs`
- **backstory:** `sidequest-api/crates/sidequest-game/src/chargen/backstory.rs`
- **hp_formula:** `sidequest-api/crates/sidequest-game/src/chargen/hp_formula.rs`
- **AudioVariation:** `sidequest-api/crates/sidequest-daemon-client/src/audio_variation.rs` (fallback handler)

### Acceptance Criteria

1. **stats subsystem**: Emit OTEL span on attribute calculation (ability scores, modifiers)
2. **backstory subsystem**: Emit OTEL span on narrative block generation
3. **hp_formula subsystem**: Emit OTEL span on HP calculation and hit point maximum computation
4. **AudioVariation fallback**: Emit OTEL event when audio variation generation fails and system falls back to default

All events must:
- Use structured OTEL telemetry from `sidequest-telemetry` crate
- Include relevant context (character id, subsystem state, values computed)
- Be visible in the GM panel watcher
- Not impact performance of the chargen flow

### Dependencies

- Related stories: 35-8 (beat_filter, scene_relevance), 35-9 (NPC subsystems)
- Related epic: Epic 35 (Wiring Remediation II)
- Must follow OTEL watcher pattern established in 35-8 and 35-9
- Telemetry infrastructure: `sidequest-telemetry` crate with watcher macros

### Implementation Notes

Reference the completed 35-9 story for the OTEL watcher pattern:
- Use `#[watcher_span]` macro or manual span creation
- Include subsystem-specific fields in span attributes
- Ensure fallback paths emit clear failure/recovery events

## Sm Assessment

**Readiness:** Ready for TEA (RED phase).

**Scope clarity:** Tight. Four surfaces, each a single well-defined emission point:
1. `sidequest-game/src/chargen/stats.rs` — attribute calculation span
2. `sidequest-game/src/chargen/backstory.rs` — narrative block span
3. `sidequest-game/src/chargen/hp_formula.rs` — HP calc span
4. `sidequest-daemon-client/src/audio_variation.rs` — fallback event

**Pattern precedent:** 35-8 and 35-9 (recently merged) established the OTEL watcher pattern using `sidequest-telemetry` crate macros. TEA and Dev should follow those commits as templates — same crate, same macro approach, same span-attribute conventions.

**Test strategy (for TEA):** Per the project OTEL observability principle, every subsystem fix must add watcher events verifiable from the GM panel. Tests should assert that the emitted spans/events carry the subsystem-specific fields (character id, computed values, failure reason for fallback). No live-LLM calls; mock ClaudeClient if the chargen path touches it.

**Wiring gate:** Each new span must have a non-test consumer. Verify `sidequest-telemetry` watcher registration picks up the new events and the GM panel receives them. "Tests pass + file exists" is not enough — trace end-to-end before claiming done.

**Risks:**
- AudioVariation fallback path may not have a clean failure hook today. If TEA finds the fallback is implicit (silent except for returning a default), that's a CLAUDE.md "no silent fallbacks" violation to flag — fix in scope.
- hp_formula may be called from multiple call sites; place the span at the formula entry point so all callers are instrumented once.

**Handoff target:** Amos Burton (TEA) for RED phase — write failing tests that assert the four new spans/events emit with correct attributes.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Four subsystems silently emit tracing spans without reaching the GM panel's watcher broadcast channel. Failing tests force Dev to swap `info_span!` / `warn!` for `WatcherEventBuilder` calls.

**Test File:**
- `sidequest-api/crates/sidequest-game/tests/otel_chargen_subsystems_story_35_13_tests.rs` — 689 lines, 12 tests

**Tests Written:** 12 total
- 8 failing subsystem-event tests (chargen.stats × 2, chargen.hp_formula × 2, chargen.backstory × 2, music_director.variation_fallback × 2)
- 4 passing A5 wiring assertions (guard the production call sites)

**Status:** RED (8 failing, 4 passing) — verified via `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game`.

**Path corrections from session context:**
The session story context pointed at files that don't exist in the current tree:
- `chargen/stats.rs`, `chargen/backstory.rs`, `chargen/hp_formula.rs` — no `chargen/` subdirectory; all chargen logic is flat inside `builder.rs`
- `daemon-client/audio_variation.rs` — AudioVariation lives in `sidequest-genre/src/models/audio.rs`; the fallback logic lives in `sidequest-game/src/music_director.rs::select_variation()`

The tests target the actual locations. Dev will implement in `builder.rs` and `music_director.rs`.

### Rule Coverage (Rust lang-review)

| Rule | Check | Status |
|------|-------|--------|
| #1 silent error swallowing | Tests enforce that silent tracing::warn!-only fallbacks in `music_director.rs::select_variation()` surface on the watcher channel | failing (driving the fix) |
| #4 tracing coverage + correctness | Tests enforce WatcherEvent emission (not just `info_span!`) for every chargen decision | failing (driving the fix) |
| #6 test quality | Every test asserts meaningful fields (method, stat_count, formula, hp_result, con_modifier, mood, preferred, selected). Zero `let _ = result`, zero `assert!(true)`, zero vacuous `is_some()`-only checks. | passing |
| A5 wiring gate (CLAUDE.md) | 4 `include_str!`-based grep checks confirm builder.rs / music_director.rs / dispatch/connect.rs / dispatch/audio.rs still reach the subsystems in production | passing |

**Rules checked:** 4 of 15 applicable lang-review rules directly exercised by new tests (the rest — `#[non_exhaustive]`, validated constructors, deserialize bypass, public fields, tenant context, workspace deps, dev-deps, unsafe casts, unbounded input — do not apply because this story adds zero new types, zero new enums, zero new public APIs).

**Self-check:** Reviewed all 12 tests. No vacuous assertions. No zero-assertion tests. No `is_none()` on always-None values. Every failing assertion has a specific error message explaining what the GM panel needs.

**Handoff:** To Naomi Nagata (Dev) for GREEN — replace `info_span!` calls with `WatcherEventBuilder::new("chargen", WatcherEventType::StateTransition).field("action", ...).send()` pattern from the 35-8/35-9 precedent. For music_director, emit when `select_variation()` takes either fallback branch.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-api/crates/sidequest-game/src/builder.rs` — +62/-10 lines: `stats_generated` emission in `generate_stats()`, `hp_formula_evaluated` + `hp_fallback` emissions in `build()` HP section, `backstory_composed` emission after backstory composition
- `sidequest-api/crates/sidequest-game/src/music_director.rs` — +48 lines: imports, `variation_label()` helper, `variation_fallback` emissions in both `select_variation()` fallback branches

**Tests:** 12/12 passing (8 newly-GREEN + 4 A5 wiring guards)
- `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game` → all green

**Branch:** `feat/35-13-otel-chargen-watcher-events` in `sidequest-api` (pushed to origin, 2 commits: RED test + GREEN implementation)

**Lib builds clean:**
- `cargo build -p sidequest-game` → warnings only, no errors
- `cargo build -p sidequest-server` → warnings only, no errors (2m 54s build)

**Regression check:** The TELEMETRY_LOCK-using tests in sibling files (`otel_structured_encounter_story_28_2_tests`, `equipment_generation_story_31_3_tests`, `otel_npc_subsystems_story_35_9_tests`) use different `component`+`action` filter tuples — no collisions with my new events. `otel_npc_subsystems_story_35_9_tests` passes cleanly; the others fail due to pre-existing debt (see Delivery Findings below) that I confirmed was already broken on develop before my changes via a clean-tree run.

**Handoff:** To Amos Burton (TEA) for verify phase — simplify fan-out + quality-pass gate.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None
**Gate Status:** spec-check passed

### AC-by-AC verification

| AC | Spec requirement | Implementation | Verdict |
|----|-----------------|----------------|---------|
| 1. stats | OTEL span on attribute calculation (ability scores, modifiers) | `chargen.stats_generated` emitted once at end of `generate_stats()` with `method`, `stat_count`, full `stats` HashMap. Single convergence point across all three generation paths (roll_3d6_strict / standard_array / point_buy). | ✅ Satisfied |
| 2. backstory | OTEL span on narrative block generation | `chargen.backstory_composed` emitted after composition with `method` (fragments/tables/fallback) and `length`. Length instead of content — correct decision: prevents spoiler leakage and event bloat, while giving the GM panel enough signal to catch empty/fallback branches. | ✅ Satisfied |
| 3. hp_formula | OTEL span on HP calculation and hit point maximum computation | `chargen.hp_formula_evaluated` on the formula path (`formula`, `class`, `hp_result`, `con_modifier`) AND `chargen.hp_fallback` on the no-formula path (`class`, `hp_result`, `source`). At chargen, `base_hp == max_hp` (builder.rs:1089-1090), so a single emission correctly covers both AC sub-requirements. Splitting fallback into its own action is cleaner than synthesizing a formula string. | ✅ Satisfied |
| 4. AudioVariation fallback | OTEL event when audio variation generation fails and system falls back to default | `music_director.variation_fallback` (severity=Warn) emitted in BOTH silent degradation branches with `mood`, `preferred`, `selected`, `reason`, `full_available`. Distinct `reason` values (`preferred_unavailable`, `only_first_available`) let the GM panel filter the two severity tiers. | ✅ Satisfied |

### Cross-cutting requirements

| Requirement | Status | Evidence |
|------------|--------|----------|
| Uses `sidequest-telemetry` crate | ✅ | All 5 emit sites use `WatcherEventBuilder` from `sidequest_telemetry` — matches 35-8/35-9 precedent |
| Includes relevant context | ✅ | Each event carries method/source + computed values. "character id" clause is inapplicable at chargen time (character does not exist until after `build()` returns) |
| Visible in GM panel watcher | ✅ | `WatcherEventBuilder::send()` publishes to the global broadcast channel, which `/ws/watcher` is subscribed to (confirmed by A5 wiring tests — see `wiring_character_builder_reached_by_server_dispatch` and `wiring_music_director_reached_by_server_dispatch_audio`) |
| No performance impact | ✅ | Additive only; telemetry is a no-op if no subscriber. Existing logic and `info_span!`/`warn!` calls preserved alongside, so stdout observability is unchanged. No allocations in the non-emit path. |

### Design judgement

- **Reuse over invention.** Dev reused the exact `WatcherEventBuilder` pattern already live on `builder.rs:998` (the pre-existing `chargen.equipment_composed` emit). No new component, no new trait, no new protocol — just additional emission sites within the existing telemetry channel. This is the right call for Epic 35 (Wiring Remediation II).
- **`variation_label()` helper is justified.** Two call sites need the lowercase serde-equivalent string, and `#[derive(Serialize)]` would require deriving `serde::Serialize` or using `format!("{:?}")` (which gives CamelCase). A private helper with a wildcard arm is the minimum-surface solution.
- **Split `hp_formula_evaluated` / `hp_fallback` is an improvement over a single action.** Separate semantics (evaluator ran vs evaluator bypassed) deserve separate filter keys. Logged as Dev deviation with correct rationale.
- **Scope is tight.** 2 source files, 1 test file, 2 commits, ~120 production LOC. Zero scope creep. No refactors, no dead code removal, no helper extraction beyond the one justified `variation_label()`.

**Decision:** Proceed to verify (TEA).

## TEA Assessment (verify phase)

**Phase:** finish
**Status:** GREEN confirmed (12/12)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`builder.rs`, `music_director.rs`, `otel_chargen_subsystems_story_35_13_tests.rs`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | High-confidence: duplication between the two `variation_fallback` emission blocks in `select_variation()` |
| simplify-quality | clean | No naming, dead-code, or readability issues in the new diff |
| simplify-efficiency | clean | Each WatcherEvent field is justified; `variation_label()` wildcard arm is intentional defensive handling of `#[non_exhaustive]` |

**Applied:** 1 high-confidence fix — extracted `emit_variation_fallback(mood, preferred, selected, reason, full_available)` in `music_director.rs`, replaced both inline `WatcherEventBuilder` chains with helper calls. Commit `0296692` on `feat/35-13-otel-chargen-watcher-events`, pushed.
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: applied 1 fix (dedup variation_fallback emissions)

**Caveat on the applied fix:** This is a 2-call-site dedup with only 3 differing values — borderline premature abstraction per CLAUDE.md's "three similar lines is better than a premature abstraction" principle. The verify workflow instructs mechanical application of high-confidence reuse findings, which is what happened. Reviewer should feel free to request a revert if the inline version reads more clearly.

### Quality Checks (after simplify)

| Check | Command | Result |
|-------|---------|--------|
| Story tests | `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game` | 12/12 pass |
| Game lib build | `cargo build -p sidequest-game` | clean (warnings only, all pre-existing) |
| Server lib build | `cargo build -p sidequest-server` | clean (warnings only, all pre-existing) |

**Wiring gate (A5):** 4/4 wiring assertions pass — confirms `builder.rs::generate_stats`, `builder.rs::build()` hp_formula + backstory paths, and `music_director.rs::select_variation()` are all reachable from production code in `dispatch/connect.rs` and `dispatch/audio.rs`.

**Handoff:** To Chrisjen Avasarala (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 blocker (fmt), 1 pre-existing noise (clippy) | confirmed 1, dismissed 1 (pre-existing), deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter` |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 high-confidence, 2 low-confidence | confirmed 1, dismissed 0, deferred 2 (low-confidence notes) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.test_analyzer` |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.comment_analyzer` |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.type_design` |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security` |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier` |
| 9 | reviewer-rule-checker | Yes | clean | none (21 rules, 47 instances, 0 violations) | N/A |

**All received:** Yes (3 enabled subagents returned, 6 pre-filled as disabled per settings)
**Total findings:** 2 confirmed, 1 dismissed (pre-existing clippy from unrelated crate), 2 deferred (low-confidence notes)

## Reviewer Assessment

**Verdict:** REJECTED

### Findings

| Severity | Tag | Issue | Location | Fix Required |
|----------|-----|-------|----------|--------------|
| [HIGH] | [SILENT] | Silent fall-through in `select_variation()`: the outer `if let Some(mood_variations) = self.themed_tracks.get(mood_key)` at line 422 has no `else` branch. When a genre pack's `themed_tracks` has no entry for the classified mood key at all (e.g. a custom mood registered in YAML without a matching theme bundle), ALL three inner emission paths are skipped and the function returns `preferred` silently at line 468. This is exactly the class of silent fallback the story was written to surface — the two emitting branches both require `mood_variations` to exist first. Directly violates CLAUDE.md "No Silent Fallbacks" and the story's own AC-4. | `crates/sidequest-game/src/music_director.rs:422-468` | Add an `else` branch on the outer `if let Some(mood_variations)` that calls `emit_variation_fallback(mood_key, preferred, preferred, "mood_not_in_themed_tracks", false)` before falling through to `preferred`. Add a new test `audio_variation_fallback_when_mood_missing_from_themed_tracks` asserting that emission happens when the genre pack has `themes` registered but no variation for the test's mood. |
| [MEDIUM] | [PREFLIGHT] | 8 new `cargo fmt` violations introduced by this branch: **1** in `builder.rs:836` (the `let mut builder = WatcherEventBuilder::new(...)` chain exceeds the column limit) and **7** in the new test file `otel_chargen_subsystems_story_35_13_tests.rs` (import ordering lines 26/32, and line-wrap preferences at 75/225/257/596/666). Verified independently: `music_director.rs` had 25 fmt violations on develop and 25 on HEAD (break-even), `builder.rs` had 13 on develop and 14 on HEAD (+1), test file had 0 on develop (new file) and 7 on HEAD (+7). Pre-existing clippy errors in `sidequest-protocol/src/message.rs` (missing-doc, 15 items) are NOT introduced by this branch — dismissed. | `builder.rs:836`, `otel_chargen_subsystems_story_35_13_tests.rs:26,32,75,225,257,596,666` | Run `cargo fmt -p sidequest-game` on the branch. The builder.rs violation at 836 is a direct consequence of the awkward `let mut builder = ... ; builder = match con_mod { ... }` pattern — see recommendation below to use `WatcherEventBuilder::field_opt()` instead, which would make the chain a single uninterrupted fluent expression and fix the fmt violation structurally. |

### Recommendation for the [MEDIUM] fix (not blocking)

The `hp_formula_evaluated` emission in `builder.rs:839-848` uses an awkward two-statement pattern because `con_mod` is an `Option<i32>`:

```rust
let mut builder = WatcherEventBuilder::new("chargen", WatcherEventType::StateTransition)
    .field("action", "hp_formula_evaluated")
    .field("formula", formula.as_str())
    .field("class", class_str)
    .field("hp_result", hp_result as i64);
builder = match con_mod {
    Some(m) => builder.field("con_modifier", m as i64),
    None => builder.field("con_modifier", serde_json::Value::Null),
};
builder.send();
```

`sidequest-telemetry::WatcherEventBuilder` already provides `field_opt(key, &Option<T>)` for exactly this case (lib.rs:122). The idiomatic form would be:

```rust
WatcherEventBuilder::new("chargen", WatcherEventType::StateTransition)
    .field("action", "hp_formula_evaluated")
    .field("formula", formula.as_str())
    .field("class", class_str)
    .field("hp_result", hp_result as i64)
    .field_opt("con_modifier", &con_mod.map(|m| m as i64))
    .send();
```

Single fluent chain, no `let mut`, no intermediate assignment, and it fits within the column limit so the fmt violation at line 836 disappears on its own.

**Caveat:** `field_opt` OMITS the key when the Option is None, whereas the current code emits an explicit `null`. If the GM panel filter logic requires `con_modifier` to always be present (even as null) to distinguish "no CON stat" from "HP formula didn't reference CON", keep the explicit match and just reformat the current chain with `cargo fmt`. The existing test `chargen_hp_formula_evaluation_emits_watcher_event` only asserts `fields.contains_key("con_modifier")`, which would FAIL under `field_opt` if `con_mod` is None — so either (a) use `field_opt` and the test still passes because CON is always rolled in the fixture, or (b) adjust the test to accept either shape. Dev's choice.

### Deferred (low-confidence, pass along to Dev for consideration)

- **[SILENT/low]** `sidequest-telemetry::emit()` discards broadcast send errors with `let _ = tx.send(event)`. Intentional fire-and-forget, but the 256-event capacity can silently drop under slow-subscriber conditions. Out of scope for 35-13 (the emit() sink predates this story). Not blocking.
- **[SILENT/low]** The backstory `fragments` branch at `builder.rs:1034` emits `method="fragments"` with a non-zero `length` even if every fragment is an empty/whitespace-only string (which could happen if a genre pack choice has a blank description field). Not blocking — would require an explicit `trim().is_empty()` guard to distinguish "joined from whitespace-only" from "joined from real content". Dev may want to add this opportunistically while fixing the [HIGH] finding.

### Rule Compliance [RULE]

Per rule-checker (21 rules, 47 instances across changed code):

| Rule | Applicable | Violations |
|------|-----------|------------|
| #1 silent error swallowing | 6 instances | 0 — poison-lock recovery in tests, fire-and-forget `send()` documented, explicit None branch for con_mod |
| #2 #[non_exhaustive] on growing enums | 0 new enums | 0 |
| #3 hardcoded placeholder values | 4 instances | 0 — `10`/"hardcoded_10" pair is documented, `"unknown"` label is a diagnostic fallback |
| #4 tracing coverage + correctness | 6 instances | 0 — Severity::Warn on degradation paths, Info on success transitions |
| #5 validated constructors at boundaries | 0 new | 0 |
| #6 test quality | 12 tests | 0 — every test has substantive multi-field assertions, no vacuous `is_some()` / `let _ = result` |
| #7 unsafe `as` casts on external input | 7 instances | 0 — all are i32→i64/u8→i32 widening from internal arithmetic or config-loaded u8; `stats.len()` and `backstory_text.len()` are internal collection sizes |
| #8 Deserialize bypass | 0 new types | 0 |
| #9 public fields on invariant types | 0 new structs | 0 |
| #10 tenant context in trait sigs | 0 new traits | 0 |
| #11 workspace dep compliance | 0 Cargo.toml changes | 0 |
| #12 dev-only deps in [dependencies] | 0 Cargo.toml changes | 0 |
| #13 constructor/deserialize consistency | 0 new types | 0 |
| #14 fix-introduced regressions | 3 refactors | 0 — HP fallback chain, backstory tuple extraction, variation_fallback helper all preserve behavior |
| #15 unbounded recursive input | 0 new parsers | 0 |
| A1 No Silent Fallbacks | 3 instances instrumented | **1 violation — see [HIGH] finding above: the outer `if let Some(mood_variations)` has no else branch and re-introduces a silent fallback at `music_director.rs:466-468`. Rule-checker missed this because it only checked the instances where WatcherEvents ARE emitted, not the surrounding control flow.** |
| A2 No Stubbing | 1 instance | 0 — all emissions carry real data |
| A3 Don't Reinvent | 1 instance | 0 — reused `WatcherEventBuilder` from 35-8/35-9 |
| A4 Verify Wiring | 2 instances | 0 — production callers confirmed |
| A5 Wiring tests | 4 tests | 0 — grep-based include_str! wiring assertions |
| A6 OTEL Observability Principle | 4 events | 0 — each event carries enough context for GM panel diagnosis |

**Note:** Rule-checker reported A1 as clean — I'm marking it as a violation based on the silent-failure-hunter's finding, which rule-checker's methodology didn't catch. Rule A1 ("No Silent Fallbacks") is not satisfied by "instrument some of the fallback paths" — it requires instrumenting ALL of them. The `themed_tracks.get(mood_key) == None` branch is a fallback path that still returns a value silently.

### Devil's Advocate

This code is broken in at least four ways I want to stress-test:

**1. The outer mood-key gap (already caught).** A genre pack author registers a new mood key in `char_creation.yaml` — say, `"saloon_tension"` for spaghetti_western — and binds a MoodKey to it in music_director's classification logic. But they forget to add a matching `AudioTheme` in `audio_config.yaml`. The mood classifier happily emits `primary: MoodKey("saloon_tension")`, `select_variation()` is called, `themed_tracks.get("saloon_tension")` returns `None`, and the function silently returns `preferred`. `evaluate()` then calls `select_track()` which falls through to the un-themed `mood_tracks` pool. The GM panel sees ZERO events about this. The game sounds subtly wrong and nobody knows why. The story was supposed to catch this class of bug. It doesn't.

**2. Threading and the fire-and-forget `send()`.** `WatcherEventBuilder::send()` calls `emit()` which does `let _ = tx.send(event)`. On broadcast channel overflow (capacity 256), events drop silently. A burst of chargen events during a multi-player session start (6 players × 4 events per character = 24 events in a single turn tick) is well within 256, so that's fine. But if a GM panel subscriber disconnects mid-session and its receiver buffers up, subsequent events from chargen could drop. Nobody sees this. Low-confidence because it's an existing property of the sink, not introduced by this story.

**3. The backstory length field can lie.** If a genre pack has a choice with `description: ""` (a common typo), that empty string gets pushed into `backstory_fragments`. At build time, `join(" ")` turns `["", "", ""]` into `"  "` (two spaces). `backstory_composed` event reports `method: "fragments"`, `length: 2`. The GM panel sees a clean emission; the player sees a blank backstory. Low-confidence, edge case.

**4. The `hp_formula_evaluated` event drops `con_modifier` under `field_opt`.** IF Dev accepts my recommendation and switches to `field_opt`, the current test `chargen_hp_formula_evaluation_emits_watcher_event` at line 306 asserts `evt.fields.contains_key("con_modifier")`. `field_opt` omits the key when None. The test fixture happens to roll 3d6 which always produces a CON value, so the test still passes — but a genre pack with non-standard ability names (no "CON") would silently drop the field in production and the test would miss it. Dev needs to either (a) keep the explicit match, or (b) add a test fixture with non-CON ability names.

Three of these four are real. Finding #1 is the blocking one. Finding #3 is worth a one-line fix. Finding #4 is a heads-up if Dev takes the `field_opt` suggestion.

### Observations (≥5)

1. [SILENT/HIGH] Outer `if let Some(mood_variations)` has no else — see [HIGH] finding. `music_director.rs:422-468`
2. [VERIFIED] `WatcherEventBuilder` is reused, not reinvented — all 5 new emission sites call the existing `sidequest-telemetry` builder with the same `StateTransition` event type as the pre-existing `chargen.equipment_composed` emission at `builder.rs:1029`. No new telemetry infrastructure. Complies with CLAUDE.md "Don't Reinvent — Wire Up What Exists."
3. [VERIFIED] A5 wiring tests use `include_str!` against production files in other crates (`../../sidequest-server/src/dispatch/connect.rs`, `../../sidequest-server/src/dispatch/audio.rs`) — the grep-based assertions are robust against refactors within the test crate but would fail loudly if production callers were removed. This is the correct wiring-test pattern per CLAUDE.md A5.
4. [VERIFIED] The refactor extracting `emit_variation_fallback()` during verify phase preserved behavior: both call sites still pass the same `(mood_key, preferred, selected, reason, full_available)` tuples they had in the inline form, and the helper signature takes `reason: &'static str` which enforces the string-literal constraint at the type level. Commit `0296692`.
5. [TYPE] `variation_label()` handles `#[non_exhaustive] TrackVariation` with a `_ => "unknown"` wildcard arm. This is correct defensive coding — a future variant that lands without a label update surfaces as "unknown" on the watcher channel rather than causing a compile error or silently omitting the event. Rule #2 satisfied.
6. [PREFLIGHT/MEDIUM] 8 new fmt violations — see [MEDIUM] finding. The `hp_formula_evaluated` builder chain specifically triggers a fmt violation because of an awkward `let mut builder = ... ; builder = match { ... }` pattern that could be replaced with `field_opt()`.
7. [PATTERN] The `(hp_value, source)` tuple extraction in the no-formula branch (`builder.rs:857-863`) is a clean pattern — it names each fallback level explicitly (`class_hp_bases`, `default_hp`, `hardcoded_10`) so the `source` field on the OTEL event is a semantic label, not a synthesized string. Good.
8. [PATTERN] The `(backstory_text, backstory_method)` tuple extraction in the backstory composition (`builder.rs:1032-1065`) uses the same pattern — each branch returns `(String, &'static str)` and the single emission site at the bottom uses the method label. Good.
9. [TEST/EDGE] The silent-failure-hunter deferred a low-confidence finding that `join(" ")` on `backstory_fragments` with only empty strings produces whitespace with method="fragments" and non-zero length. Not blocking, but worth a one-line fix if Dev is touching this area for the [HIGH] fix anyway.
10. [VERIFIED] `hp_result as i64` and `stats.len() as i64` casts are safe — rule-checker confirmed all 7 `as` casts are either i32→i64/u8→i32 widening (lossless) or internal `.len()` on small collections. Rule #7 satisfied.

### Tenant isolation audit

N/A — this is a solo RPG game engine, no multi-tenant context. No tenant IDs, no permissions, no auth data in the watcher events. The closest thing is `character.name` which is cosmetic player-chosen input, not a security boundary. Skipped.

### Data flow trace (for the HIGH finding)

User action: multiplayer session start → narrator returns `scene_mood: "saloon_tension"` (hypothetical custom mood).
→ `dispatch/audio.rs::process_audio()` calls `director.classify_mood_with_reasoning(narration, &mood_ctx)`
→ classifier returns `MoodClassification { primary: MoodKey("saloon_tension"), intensity: 0.6, confidence: 0.7 }`
→ `director.evaluate(narration, &mood_ctx)` calls `self.select_variation(&classification, ctx)`
→ `select_variation()` line 419 computes `preferred = self.score_variation(...)` → returns, say, `TrackVariation::TensionBuild`
→ line 422 `self.themed_tracks.get("saloon_tension")` → returns `None` (genre pack has no theme for this mood)
→ line 464 `}` closes the outer `if let Some`
→ line 466 comment "No themed tracks at all — return preferred anyway"
→ line 468 `preferred` is returned with **zero telemetry emitted**
→ `evaluate()` then calls `self.select_track(&classification)` which falls back to the un-themed `mood_tracks` pool
→ `AudioCue { track_id: Some(some_mood_track.ogg), ... }` is emitted to the client
→ Client plays a generic mood track instead of the themed saloon variation; GM panel sees the `music_mood_classified` event from `dispatch/audio.rs:71` but NOT any `music_director.variation_fallback` event

The story's stated test `wiring_music_director_select_variation_reached_by_evaluate` confirms the production call chain reaches `select_variation()`, so the gap is reachable in production. The failing scenario is real.

**Handoff:** Back to Naomi Nagata (Dev) for fixes.

## TEA Assessment (rework RED)

**Tests Required:** Yes
**Reason:** Reviewer's [HIGH] finding identified a fourth silent exit path in `select_variation()` that the original RED phase didn't test for. A failing test must exist before Dev implements the fix, per TDD discipline.

**Test Added:**
- `audio_variation_fallback_when_mood_missing_from_themed_tracks` in `sidequest-api/crates/sidequest-game/tests/otel_chargen_subsystems_story_35_13_tests.rs` (+138 lines including the new `audio_config_themes_for_exploration_only()` fixture)

**Fixture strategy:** Register `mood_tracks` for both exploration and combat (so `evaluate()` has material for the post-`select_variation` fallthrough) but register `themes` for exploration only. Any non-exploration classification — test uses `MoodKey::COMBAT` — hits the missing-mood-key path.

**Assertions:**
- `variation_fallback` event IS emitted when `themed_tracks.get("combat")` returns `None`
- `mood` field = "combat"
- `reason` field contains "mood" (accepts `"mood_not_in_themed_tracks"` or any `mood`-containing string for implementation flexibility)
- `full_available` = `false`

**Status:** 12 passing (all previous tests still green), 1 failing (new test) — verified via `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game`. Failure message: "Got 0 other events" — confirms the silent fall-through path at `music_director.rs:466-468`.

**Expected Dev fix:**
1. Add an `else` branch on `music_director.rs::select_variation()` line 422's `if let Some(mood_variations)` that calls `emit_variation_fallback(mood_key, preferred, preferred, "mood_not_in_themed_tracks", false)` before falling through to `preferred`.
2. Run `cargo fmt -p sidequest-game` to address the 8 pre-existing fmt violations from Pass 1 (1 at `builder.rs:836`, 7 in the test file).
3. Optional: refactor `hp_formula_evaluated` to use `WatcherEventBuilder::field_opt` — structurally fixes the line 836 fmt violation. Dev's call; see Reviewer recommendation.

**Commit:** `6eae1c1 test(35-13): RED — rework test for missing-mood-key fallback` on `feat/35-13-otel-chargen-watcher-events`, pushed.

**Handoff:** To Naomi Nagata (Dev) for GREEN — add the else branch, run cargo fmt, re-verify all 13 tests pass.

## Dev Assessment (rework GREEN)

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-api/crates/sidequest-game/src/music_director.rs` — added `else` branch to `select_variation()` outer `if let Some`, emits `variation_fallback` with `reason="mood_not_in_themed_tracks"` and `full_available=false`. Paired `tracing::warn!` preserved alongside for stdout observability.
- `sidequest-api/crates/sidequest-game/src/builder.rs` — replaced the awkward `let mut builder = ... ; builder = match con_mod { ... }` pattern at line 839 with a single fluent chain using `WatcherEventBuilder::field_opt("con_modifier", &con_mod.map(i64::from))`. Fixes the fmt violation at line 836 structurally.
- `sidequest-api/crates/sidequest-game/tests/otel_chargen_subsystems_story_35_13_tests.rs` — rustfmt-clean (imports sorted, lines wrapped per rustfmt preference).

**Tests:** 13/13 passing
- 12 from Pass 1 (chargen × 2 tests each for stats, hp_formula, hp_fallback, backstory; variation_fallback × 2; wiring × 4)
- 1 new from rework RED: `audio_variation_fallback_when_mood_missing_from_themed_tracks`

**Branch:** `feat/35-13-otel-chargen-watcher-events` in `sidequest-api` — last commit `2387746` pushed.

**Builds:** `cargo build -p sidequest-game` ✓, `cargo build -p sidequest-server` ✓. Both warnings-only, all pre-existing.

**fmt impact vs develop (break-even):**
- `builder.rs`: 13 → 13 (0 new violations)
- `music_director.rs`: 25 → 25 (0 new violations)
- `otel_chargen_subsystems_story_35_13_tests.rs`: 0 violations (entire file is new in this branch, fully clean)

**Scope discipline:** Deliberately did NOT run `cargo fmt -p sidequest-game` on the full crate. Running rustfmt once touched 388 lines of pre-existing fmt debt in builder.rs + music_director.rs that are unrelated to this story. Reverted those changes and fixed only the story's new violations: one structural fix (field_opt in builder.rs) + the test file (entirely new code). Per CLAUDE.md: "A bug fix doesn't need surrounding code cleaned up."

**Caveat on field_opt:** The previous emission sent `con_modifier: null` when CON wasn't rolled. `field_opt` OMITS the key entirely when the Option is None. Current test fixture (`rules_3d6`) always produces a CON stat, so the test `chargen_hp_formula_evaluation_emits_watcher_event` still passes. A future genre pack with non-D&D ability names (no "CON") would produce events without the key, which is a semantic change the GM panel consumer should tolerate.

**Handoff:** To Naomi Nagata (Architect, design mode) for rework spec-check.

## Architect Assessment (rework spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None
**Gate Status:** spec-check passed

### Reviewer findings → Pass 2 implementation

| Finding | Severity | Pass 2 fix | Verdict |
|---------|----------|------------|---------|
| Silent fall-through in `select_variation()` outer `if let Some` has no else branch, violates no-silent-fallbacks rule | [HIGH] | Added `else` branch at `music_director.rs:464-484` calling `emit_variation_fallback(mood_key, preferred, preferred, "mood_not_in_themed_tracks", false)` with paired `tracing::warn!` for stdout parity. The `selected == preferred` is semantically honest — the caller's preference is what gets returned because there's no themed selection to make. | ✅ Resolved |
| 8 new `cargo fmt` violations (1 in builder.rs:836, 7 in new test file) | [MEDIUM] | **builder.rs**: Replaced the awkward `let mut builder = ... ; builder = match con_mod { ... }` pattern with a single fluent chain using `WatcherEventBuilder::field_opt("con_modifier", &con_mod.map(i64::from))`. Structural fix — the violation disappears because the line structure no longer exceeds the column limit. **test file**: rustfmt-clean (imports sorted, lines wrapped). **Scope discipline**: Dev deliberately did NOT run fmt on the full crate; would have touched 388 lines of pre-existing debt. Manually fixed only story-scope violations. Net fmt state vs develop: break-even (0 new violations). | ✅ Resolved |

### Rework-specific verification

| Check | Pass 2 state | Notes |
|-------|--------------|-------|
| Rework RED test passes | ✅ | `audio_variation_fallback_when_mood_missing_from_themed_tracks` asserts `mood="combat"`, `reason` containing "mood", `full_available=false`. Dev emits exactly those fields. |
| All previous 12 tests still pass | ✅ | 13/13 total. |
| `cargo build -p sidequest-game` | ✅ | Warnings-only, all pre-existing. |
| `cargo build -p sidequest-server` | ✅ | Warnings-only, all pre-existing. |
| fmt state vs develop | break-even | builder.rs 13→13, music_director.rs 25→25, test file 0. |
| Commits are incremental and reviewable | ✅ | 5 commits total: RED, GREEN, refactor, rework-RED, rework-GREEN. Each commit has a clear scope and passes tests on its own. |

### Design judgement (rework-specific)

- **The `selected == preferred` pattern for the missing-mood-key emission is correct.** Semantically, it says: "the caller asked for X, we have no themed material for that mood at all, so we pass X through unchanged for the evaluate() layer to handle downstream." Setting `selected` to some other value (e.g., `TrackVariation::Full`) would be a lie — the director is NOT selecting Full, it's passing the preference through untouched. The test asserts `full_available=false` which distinguishes this case from the preferred_unavailable branch where Full WAS actually selected and available.

- **`field_opt` is the right primitive for Option-valued fields.** The Dev's concern about the semantic change (key omitted vs explicit null) is real but not blocking. JSON consumers should treat absence and null identically for "not applicable" values. The 35-8/35-9 precedent already uses `field_opt` for optional fields elsewhere. Future genre packs with non-D&D ability systems will simply see events without `con_modifier`, which is the correct semantic.

- **Scope discipline is good.** The fmt-revert move is exactly what the CLAUDE.md minimalist discipline calls for. Filing a delivery finding recommending a dedicated tech-debt story for the whole-crate fmt pass is the right way to surface the observation without scope-creeping the current story.

### Outstanding Reviewer low-confidence findings (deferred to future work)

- **Blank-fragments backstory edge case** (Reviewer [low]): The `fragments` branch at `builder.rs:1034` emits `method="fragments"` with non-zero length even when all fragments are whitespace-only strings. Still unaddressed — Dev did not touch this. Reasonable scope call since the [HIGH] and [MEDIUM] findings are what the Reviewer gated on. Worth a follow-up note in a future story touching backstory composition.
- **sidequest-telemetry channel overflow** (Reviewer [low]): Out of scope for this story. Unchanged.

**Decision:** Proceed to verify (TEA).

## TEA Assessment (rework verify)

**Phase:** finish (rework)
**Status:** GREEN confirmed (13/13)

### Simplify Report (Pass 2 delta)

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`builder.rs`, `music_director.rs`, `otel_chargen_subsystems_story_35_13_tests.rs`)
**Scope:** Pass 2 delta only — the else branch, field_opt refactor, and new test + fixture

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | 0 — `emit_variation_fallback()` helper is now used at 3 call sites (up from 2), all with identical schema. `field_opt` is the idiomatic telemetry primitive for Option fields. New test fixture is minimal and distinct from the existing ones. |
| simplify-quality | clean | 0 — naming consistent, comments document intent, no dead code, no unused imports. |
| simplify-efficiency | clean | 0 — no over-engineering, no premature abstraction, reuse of existing helper is the correct move. |

**Applied:** 0 fixes (all clean)
**Flagged for Review:** 0
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean

### Quality Checks (after Pass 2)

| Check | Command | Result |
|-------|---------|--------|
| Story tests | `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game` | 13/13 pass |
| Game lib build | `cargo build -p sidequest-game` | clean (warnings only, all pre-existing) |
| Server lib build | `cargo build -p sidequest-server` | clean (warnings only, all pre-existing) |
| fmt vs develop | break-even | builder.rs 13→13, music_director.rs 25→25, test file 0 |

**Wiring gate (A5):** 4/4 wiring assertions still pass — the Pass 2 changes don't touch any call-site that the wiring tests depend on.

**Rework verdict:** All three Reviewer findings from Pass 1 are resolved:
1. [HIGH] Silent fall-through on missing mood key → else branch added, new test passes
2. [MEDIUM] 8 new fmt violations → 0 new violations (structural field_opt fix + test file fmt cleanup)
3. [low deferred] Blank-fragments backstory edge case → still unaddressed, acknowledged as low-priority future work

**Handoff:** To Chrisjen Avasarala (Reviewer) for Pass 2 code review.

## Subagent Results (Pass 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | Pass 1 HIGH + MEDIUM both resolved; 13/13 tests; fmt break-even; 0 smells | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 medium-confidence (Some(empty HashMap) corner case) | confirmed 1 — see [MEDIUM] finding below |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 21 rules, 53 instances, 0 violations — confirmed Rule A1 resolved (for None case) and Rule #7 `i64::from` strictly safer than `as i64` | N/A |

**All received:** Yes (3 enabled subagents returned, 6 pre-filled as disabled per settings)
**Total findings:** 1 confirmed at [MEDIUM] (non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment (Pass 2)

**Verdict:** APPROVED (with 1 non-blocking finding)

### Pass 1 findings — resolution audit

| Pass 1 Finding | Severity | Pass 2 state | Evidence |
|----------------|----------|--------------|----------|
| Silent fall-through in `select_variation()` outer `if let Some` (None case) | [HIGH] | ✅ RESOLVED | `music_director.rs:464-484` explicit else branch emits `variation_fallback` with `reason="mood_not_in_themed_tracks"`, `full_available=false`, paired `tracing::warn!`. New test `audio_variation_fallback_when_mood_missing_from_themed_tracks` exercises the path. |
| 8 new `cargo fmt` violations | [MEDIUM] | ✅ RESOLVED | Verified independently: builder.rs 13→13, music_director.rs 25→25, test file 0. Break-even with develop. The `field_opt` refactor in builder.rs structurally eliminated the line 836 violation. |

### Pass 2 new finding

| Severity | Tag | Issue | Location | Fix Recommended |
|----------|-----|-------|----------|-----------------|
| [MEDIUM] | [SILENT][RULE] | **Residual silent path in `select_variation()`.** If a genre pack registers an `AudioTheme` with an empty `variations: []` array, `MusicDirector::new()` at line 347 inserts the mood key into `themed_tracks` via `or_default()` but populates an empty inner HashMap. `select_variation()` then hits `Some(empty_map)` — all three inner conditionals skip, control falls out of the `Some` arm WITHOUT entering the Pass 2 else branch, returns `preferred` silently. Same failure mode as the Pass 1 [HIGH], triggered by a rarer malformed input. Violates CLAUDE.md "No Silent Fallbacks" on a corner case. | `crates/sidequest-game/src/music_director.rs:343-349` (construction) AND `:422-488` (selection) | **One-line fix at construction time:** in `MusicDirector::new` around line 347, skip inserting the mood key when `theme.variations.is_empty()`. This turns `Some(empty)` into `None`, which the Pass 2 else branch already handles. Preserves the Pass 2 instrumentation without needing a fourth emission site. Also recommend a regression test with an empty-variations fixture. |

**Why this is NOT blocking:**
- Requires structurally-valid but semantically-malformed YAML (`variations: []`)
- `sidequest-genre::validate` does NOT currently reject empty variations arrays (verified — no `is_empty` checks in `validate.rs` or models). The path is reachable, but only via a specific content authoring error.
- Downstream behavior is "play un-themed mood track from `mood_tracks`" — degraded but functional. No crash, no data loss, no security issue.
- Pass 1 [HIGH] was the PRIMARY failure mode; this is a RESIDUAL corner case. Story AC-4 is substantively met.
- Rejecting for a fourth review pass on a corner case is diminishing returns after already ping-ponging RED→GREEN→review twice.

**Why it's still worth flagging (rather than dismissing):**
- Same failure class as Pass 1 [HIGH] (silent return of `preferred`)
- Directly violates CLAUDE.md "No Silent Fallbacks" rule, which is categorical
- The fix is literally one line at construction time — trivial cost
- Silent-failure-hunter and my own independent read both caught it

**Recommendation for Keith:** Dev should fix this before merge. One-line `continue` guard in `MusicDirector::new()` plus a ~10-line regression test. If you'd rather ship as-is and do it in a follow-up story, the delivery finding below tracks it. This is your call — I'm approving because the story AC is substantively met, but I want the gap documented.

### Rule Compliance (Pass 2) [RULE]

Rule-checker returned clean on all 21 rules (53 instances, 0 violations) including:
- **Rule A1 (No Silent Fallbacks):** Pass 1 violation resolved by the Pass 2 else branch. I'm OVERRIDING the clean verdict for one edge case: the `Some(empty)` path is still uninstrumented. Per the "project rules are not suggestions" critical rule, I confirm the silent-failure-hunter's finding as a Rule A1 partial violation at [MEDIUM]. Rule-checker missed it because it only checked the three explicit conditional branches, not the fall-through when `mood_variations.iter().next()` returns None on an empty map.
- **Rule #7 (unsafe `as` casts):** `con_mod.map(i64::from)` in `builder.rs:847` is *strictly safer* than the pre-existing `as i64` pattern — uses the infallible `From<i32> for i64` trait bound, compiler-enforced lossless widening.

### Devil's Advocate (Pass 2)

**What would break this code?**

1. **The `Some(empty)` silent path** — already flagged above. A genre pack author writes `themes: [{mood: 'combat', base_prompt: '...', variations: []}]`. Structurally valid. The `sidequest-genre` YAML loader accepts it. `MusicDirector::new` creates the outer key with an empty inner map. `select_variation("combat")` returns `preferred` silently. GM panel sees nothing.

2. **The `field_opt` omit-vs-null semantic change.** Pass 1 emitted `con_modifier: null` when the HP formula didn't reference CON. Pass 2 with `field_opt` omits the key entirely. A GM panel consumer that relies on `fields.contains_key("con_modifier")` regardless of value now sees fewer events with the key present. This is a schema change. Dev flagged it in deviations. Test fixture always rolls CON so existing coverage didn't catch the difference. Acknowledged; not a blocker.

3. **`preferred == selected` in the outer else.** When the missing-mood-key emission fires, both fields carry the same value. A GM panel filter that does `preferred !== selected` to detect "real" fallbacks will miss this case. Workaround: filter on `reason="mood_not_in_themed_tracks"` instead. Not a bug — the semantic is honest — but worth noting for downstream consumers.

4. **Empty backstory_fragments with whitespace-only content** (carry-over from Pass 1 low-confidence). Genre pack with `description: ""` fragments produces `join(" ") = "  "` with `method="fragments"` and non-zero length. Still unaddressed. Low-confidence, not blocking.

5. **Test lock poisoning cascade.** TELEMETRY_LOCK uses correct poison recovery, but a panic mid-test body could leave subsequent tests in a weird state. Mitigated by `fresh_subscriber` draining at start. Theoretical.

Three of these are real observations. (1) is the blocking-ish one flagged [MEDIUM]. (2)-(4) are documented known tradeoffs.

### Observations (≥5)

**Subagent dispatch tags used in this assessment:** [RULE] (reviewer-rule-checker) and [SILENT] (reviewer-silent-failure-hunter). Other subagent tags ([EDGE], [TEST], [DOC], [TYPE], [SEC], [SIMPLE]) are N/A — those subagents are disabled via `workflow.reviewer_subagents` settings.

1. **[VERIFIED] Pass 1 [HIGH] fully resolved** — Else branch at `music_director.rs:464-484` instruments the `None` path.
2. **[VERIFIED] Pass 1 [MEDIUM] fully resolved** — fmt break-even with develop (13/13, 25/25, 0/0).
3. **[SILENT][RULE][MEDIUM] Residual `Some(empty HashMap)` silent path** — See finding above.
4. **[VERIFIED] `i64::from` is strictly safer than `as i64`** — Rule #7 compliance improved, compiler-enforced widening.
5. **[VERIFIED] Scope discipline preserved** — +37/-28 lines across 3 files, zero scope creep, pre-existing fmt debt explicitly untouched.
6. **[VERIFIED] Wiring tests still pass** — 4 A5 assertions still cover the production call paths.
7. **[VERIFIED] Commits are incrementally reviewable** — 5 commits on the branch, each independently test-passing.
8. **[PATTERN] `preferred == selected` in missing-mood emission is semantically honest** — Reflects "no selection made, caller's preference passed through".
9. **[DOC] `field_opt` semantic change documented** — Dev deviation log captures the omit-vs-null difference.
10. **[DOC] Comments at `music_director.rs:465-471` clearly explain intent** — Future maintainers know why the else branch returns `preferred` after emitting.

### Tenant isolation audit

N/A — solo RPG game engine. No tenant context, no auth data, no multi-tenant boundaries.

**Handoff:** To Camina Drummer (SM) for finish-story. Dev should decide whether to fix the [MEDIUM] finding before SM merges or track it as a follow-up story per Keith's direction.

## TEA Assessment (Pass 3 RED)

**Tests Required:** Yes
**Reason:** Keith's direction: "fix all wiring immediately". Pass 2 Reviewer's [MEDIUM] non-blocking finding (residual `Some(empty HashMap)` silent path) is being closed in-pass rather than tracked as a follow-up. RED test must land before Dev implements the guard.

**Test Added:**
- `audio_variation_fallback_when_mood_has_empty_variations` in `otel_chargen_subsystems_story_35_13_tests.rs` (+138 lines including the new `audio_config_combat_theme_with_empty_variations()` fixture)

**Fixture strategy:** AudioConfig with a single `AudioTheme { mood: "combat", variations: vec![] }`. `MusicDirector::new()` iterates `audio_config.themes` and calls `themed_tracks.entry(theme.mood.clone()).or_default()` BEFORE iterating `theme.variations` — so the key is inserted with an empty inner HashMap regardless of variation count. Any subsequent `select_variation` classified as combat hits the `Some({})` fall-through.

**Assertions:** The test accepts EITHER fix strategy:
1. If Dev adds a dedicated `reason="mood_variations_empty"` emission inside `select_variation` — test matches it.
2. If Dev adds an `is_empty()` guard at `MusicDirector::new()` (preferred per Pass 2 Reviewer recommendation) — the key never gets inserted, `themed_tracks.get("combat")` returns `None`, the existing Pass 2 else branch fires with `reason="mood_not_in_themed_tracks"`, and the test matches that too.

This flexibility lets Dev pick the cleaner fix (construction-time guard) without forcing a new reason label that would also require a new emission site.

**Status:** 13 passing (existing), 1 failing (new) — verified via `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game`. Failure: "Got 0 events total" — confirms the silent path.

**Commit:** `6062600 test(35-13): RED — Some(empty HashMap) silent path in select_variation()` on `feat/35-13-otel-chargen-watcher-events`, pushed.

**Handoff:** To Naomi Nagata (Dev) for Pass 3 GREEN — add `if theme.variations.is_empty() { continue; }` in `MusicDirector::new()` around line 347 (or the alternative inline emission, but the construction-time guard is cleaner). Re-verify all 14 tests pass.

## Dev Assessment (Pass 3 GREEN)

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-api/crates/sidequest-game/src/music_director.rs` — added a construction-time guard at `MusicDirector::new()` around line 347. Before calling `themed_tracks.entry(theme.mood.clone()).or_default()`, check `theme.variations.is_empty()` and `continue` with a paired `tracing::warn!` if so. This keeps the mood key out of `themed_tracks` entirely, turning the `Some(empty_map)` path into the already-covered `None` path.

**Why this over an inline emission:** Construction-time guard is the cleanest option because:
1. It makes the `themed_tracks` invariant explicit at the point of insertion — no mood key can have an empty inner map.
2. It reuses the existing Pass 2 else branch instead of introducing a 4th emission site or a new `reason` label.
3. It's one `if` statement, not a new fallback path in the hot `select_variation()` selection logic.
4. When the malformed theme is encountered at startup, the warning fires ONCE per director construction rather than once per `select_variation` call, reducing log noise if the same malformed bundle is classified many times.

The test's permissive `reason` assertion (`"mood_variations_empty" || "mood_not_in_themed_tracks" || contains("empty") || contains("mood")`) accepts this approach because the construction-time guard routes through the Pass 2 else branch which already emits `"mood_not_in_themed_tracks"`.

**Tests:** 14/14 passing
- 13 from Pass 2 (all chargen emissions, variation_fallback preferred_unavailable / only_first_available / mood_not_in_themed_tracks, 4 wiring assertions)
- 1 new from Pass 3 RED: `audio_variation_fallback_when_mood_has_empty_variations` — now passes because the construction-time guard routes through the Pass 2 else branch

**Branch:** `feat/35-13-otel-chargen-watcher-events` in `sidequest-api` — last commit `8b67732` pushed. 7 commits total on the branch.

**Builds:** `cargo build -p sidequest-game` ✓, `cargo build -p sidequest-server` ✓. Both warnings-only, all pre-existing.

**fmt impact vs develop:** `music_director.rs` 25→25 (break-even, 0 new violations introduced).

**All four silent paths in select_variation() are now closed:**
1. ✅ `mood_variations.contains_key(&preferred)` false but Full present → `preferred_unavailable` emission
2. ✅ Neither preferred nor Full present, first_available exists → `only_first_available` emission
3. ✅ `themed_tracks.get(mood_key) == None` (mood not in themed_tracks) → `mood_not_in_themed_tracks` emission (Pass 2 else branch)
4. ✅ Empty variations bundle (`Some(empty_map)` prevented at construction) → routed through the Pass 2 else branch via the new `MusicDirector::new` guard (Pass 3)

No more silent paths. Story AC-4 fully met.

**Handoff:** To Naomi Nagata (Architect, design mode) for Pass 3 spec-check.

## Architect Assessment (Pass 3 spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None
**Gate Status:** spec-check passed

### Pass 3 fix verification

| Pass 2 Reviewer Finding | Pass 3 fix | Verdict |
|------------------------|-------------|---------|
| Residual silent path: `Some(empty HashMap)` in `select_variation()` when a genre pack has `variations: []` ([MEDIUM] non-blocking) | `music_director.rs:346-366`: added `if theme.variations.is_empty() { tracing::warn!(...); continue; }` before `themed_tracks.entry(...).or_default()`. Keeps the mood key out of `themed_tracks` entirely, so `select_variation` hits the `None` branch and the Pass 2 else branch fires with `reason="mood_not_in_themed_tracks"`. | ✅ Resolved |

### All 4 silent paths in `select_variation()` are now closed

1. ✅ Preferred variation missing but Full registered → `variation_fallback(reason="preferred_unavailable", full_available=true)` at lines 435-441
2. ✅ Neither preferred nor Full registered → `variation_fallback(reason="only_first_available", full_available=false)` at lines 455-461
3. ✅ Mood key absent from `themed_tracks` (outer `None`) → `variation_fallback(reason="mood_not_in_themed_tracks", full_available=false)` at lines 477-483
4. ✅ Mood key present but inner map empty → **prevented at construction time** by the Pass 3 guard; execution flows through path (3)

AC-4 ("Emit OTEL event when audio variation generation fails and system falls back to default") is now **fully met**. No residual silent paths.

### Design judgement (Pass 3)

- **Construction-time guard is the right choice.** Pass 2 Reviewer recommended this approach over an inline `is_empty()` check in `select_variation()` itself. Benefits Dev documented all land:
  - Makes the `themed_tracks` invariant explicit: no mood key can map to an empty inner HashMap.
  - Reuses the Pass 2 else branch instead of adding a 4th emission site with a new `reason` label (which would have required another test assertion and another GM panel filter case).
  - Warning fires ONCE per director construction, not once per `select_variation` call. In a multiplayer session start with 6 players × N turns, the inline approach would log the malformed bundle on every mood classification.
  - The `entry(...).or_default()` pattern at line 366 keeps its intended behavior for well-formed themes.

- **Paired `tracing::warn!` is preserved.** Stdout observability captures the malformed theme at startup. A developer running the server locally sees the warning immediately; a GM panel watching `/ws/watcher` sees the downstream `variation_fallback` events when moods classify to the missing key. Belt and suspenders — both channels carry the signal.

- **The test's permissive reason assertion correctly covers both implementation strategies.** TEA wrote the test to accept either `"mood_variations_empty"` OR `"mood_not_in_themed_tracks"`, explicitly allowing Dev to pick the construction-time guard. Dev picked the construction-time guard, which routes through the Pass 2 else branch's existing `"mood_not_in_themed_tracks"` reason. Test passes without modification.

- **Zero scope creep in Pass 3.** One file touched, 18 lines added, one `continue` + one `tracing::warn!` + explanatory comment. No refactoring, no pre-existing fmt debt cleanup, no drive-by improvements.

### Outstanding observations (carry-forward from Pass 2, still unaddressed — intentionally)

- **Blank-fragments backstory edge case** (Reviewer [low]): Genre pack choices with `description: ""` produce `join(" ") = "  "` with `method="fragments"` and non-zero length. Still unaddressed. Keith's "fix all wiring immediately" direction was specifically about the Pass 2 [MEDIUM] finding in `select_variation()`. The backstory edge case is a different subsystem (chargen) and a different class of issue (data validity, not silent fallback). Leaving it for a future story unless Keith says otherwise.
- **sidequest-telemetry channel overflow** (Reviewer [low]): Out of scope for this story. Unchanged.

**Decision:** Proceed to verify (TEA).

## TEA Assessment (Pass 3 verify)

**Phase:** finish (Pass 3)
**Status:** GREEN confirmed (14/14)

### Simplify Report (Pass 3 delta)

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`music_director.rs`, `otel_chargen_subsystems_story_35_13_tests.rs`)
**Scope:** Pass 3 delta only — the 18-line construction-time guard and the new test + fixture

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | 0 — new fixture is distinct from `audio_config_themes_for_exploration_only()`, warning message is context-specific, the `continue` guard is used exactly once where it applies |
| simplify-quality | clean | 0 — naming consistent, comment traces to CLAUDE.md no-silent-fallbacks rule, no dead code, no unused imports |
| simplify-efficiency | clean | 0 — guard is necessary correctness fix not over-engineering, tracing level appropriate, comment justified, no premature abstraction |

**Applied:** 0 fixes
**Flagged for Review:** 0
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean

### Quality Checks (after Pass 3)

| Check | Command | Result |
|-------|---------|--------|
| Story tests | `cargo test --test otel_chargen_subsystems_story_35_13_tests -p sidequest-game` | 14/14 pass |
| Game lib build | `cargo build -p sidequest-game` | clean (pre-existing warnings only) |
| Server lib build | `cargo build -p sidequest-server` | clean (pre-existing warnings only) |
| fmt vs develop | break-even | music_director.rs 25→25 (the only file Pass 3 touched) |

**Wiring gate (A5):** 4/4 wiring assertions still pass — the Pass 3 guard at construction time doesn't touch any wiring test target.

**Silent-path closure verdict:** All 4 paths confirmed closed via `cargo test`:
1. ✅ `preferred_unavailable` — `audio_variation_fallback_to_full_emits_watcher_event`
2. ✅ `only_first_available` — `audio_variation_fallback_to_first_available_emits_watcher_event`
3. ✅ `mood_not_in_themed_tracks` (None path) — `audio_variation_fallback_when_mood_missing_from_themed_tracks`
4. ✅ Empty-variations (Some(empty) prevented at construction → routes through path 3) — `audio_variation_fallback_when_mood_has_empty_variations`

**Handoff:** To Chrisjen Avasarala (Reviewer) for Pass 3 code review.

## Subagent Results (Pass 3)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | Pass 2 [MEDIUM] resolved; 14/14 tests; fmt break-even; 0 smells | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 new findings; Path D structurally eliminated; one pre-existing out-of-scope note about `as_variation()` in `sidequest-genre` | noted (see delivery findings) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 21 rules, 47 instances, 0 violations. **Rule A1 (No Silent Fallbacks) explicitly FULLY SATISFIED.** | N/A |

**All received:** Yes (3 enabled subagents returned, 6 pre-filled as disabled per settings)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 noted (pre-existing out-of-scope in sidequest-genre)

## Reviewer Assessment (Pass 3) [RULE] [SILENT]

**Verdict:** APPROVED

### Pass 2 finding — resolution audit

| Pass 2 Finding | Severity | Pass 3 state | Evidence |
|----------------|----------|--------------|----------|
| Residual silent path: `Some(empty HashMap)` in `select_variation()` when a genre pack has `variations: []` | [MEDIUM] | ✅ RESOLVED | Construction-time guard at `music_director.rs:355-363`. Verified by rule-checker (Rule A1 "FULLY SATISFIED"), silent-failure-hunter (Path D "structurally eliminated"), and new regression test `audio_variation_fallback_when_mood_has_empty_variations`. The guard prevents `Some(empty_map)` from ever existing in `themed_tracks`, routing empty-variations themes through the Pass 2 else branch. |

### All 4 silent paths in `select_variation()` closed (final state)

1. ✅ **Path A** (happy path) — `contains_key(preferred)` → return preferred. Not a fallback.
2. ✅ **Path B** (`preferred_unavailable`) — preferred missing, Full registered → emits and returns Full.
3. ✅ **Path C** (`only_first_available`) — preferred and Full missing, `iter().next()` returns a variation → emits and returns it.
4. ✅ **Path D** (`Some(empty_map)`) — **structurally eliminated** by the Pass 3 construction-time guard. After the guard, any theme in `themed_tracks` has at least one variation pushed via `as_variation()`, so `iter().next()` is always `Some`. The empty inner HashMap cannot be constructed.
5. ✅ **Path E** (`mood_not_in_themed_tracks`) — outer `None`, either because the genre pack never registered the mood OR because the Pass 3 guard skipped it. Emits and returns preferred for downstream `evaluate()` fall-through.

**AC-4 fully met.** No silent paths remain in the audio variation fallback subsystem.

### Rule Compliance (Pass 3) [RULE]

Rule-checker explicit statement on A1:
> "Rule A1 is NOW FULLY SATISFIED for this file. The is_empty() guard at music_director.rs:355 prevents empty-variations themes from inserting a mood key into themed_tracks. When select_variation later calls themed_tracks.get(mood_key), it returns None, which routes to the else branch added in Pass 2, which calls emit_variation_fallback(..., 'mood_not_in_themed_tracks', ...). No silent return of preferred remains."

All 21 rules clean across 47 instances. 14/14 tests passing. Zero new fmt violations (25/25 on music_director.rs — break-even with develop).

### Devil's Advocate (Pass 3)

**What's left that could break this?**

1. **`as_variation()` silent default** (noted by silent-failure-hunter, pre-existing). `sidequest-genre::models::audio::AudioVariation::as_variation()` silently defaults unrecognized `variation_type` strings to `TrackVariation::Full` with only a `tracing::warn!` — no watcher event. This means a genre pack with `variation_type: "typo_here"` will register as `Full` in `themed_tracks`. If the subsequent `select_variation` call happens to prefer Full, it matches Path A and emits nothing. The player hears the track (labeled incorrectly), the GM panel sees nothing. **Scope:** `sidequest-genre`, NOT touched by story 35-13. Pre-existed all three passes. Not a regression. Worth tracking as a follow-up story — see delivery finding.

2. **The "happy" Path A under Full-preference genre packs.** If a genre pack registers ONLY Full variations and the scorer happens to prefer Full (e.g., combat at high intensity), Path A fires and returns Full with no emission. This is correct — it's not a fallback. But a genre pack author who removes all non-Full variations could create a situation where `select_variation` never emits any `variation_fallback` event despite the pack being effectively un-themed. **Judgement:** not a bug; the spec is "emit when fallback occurs". A pack that always matches the preference is not falling back.

3. **The blank-fragments backstory case** (Reviewer [low], pre-existing from Pass 1/Pass 2). Still unaddressed. Keith's "fix all wiring immediately" direction was explicit about the audio-variation silent path; the backstory edge case is a different subsystem and a different class of issue (data validity). Leaving for a future story unless Keith says otherwise.

4. **Per-turn log volume** for the Pass 3 warning. `tracing::warn!` fires at MusicDirector construction time, not per-turn. Construction happens once per director (once per session start, typically), so the warning is emitted at most once per malformed genre pack per session. Not a log-flood risk.

5. **Test regression coverage for the guard.** The Pass 3 test asserts on the event emission but NOT on the guard log. A future change that accidentally removes the guard (but adds a different fix) would still satisfy the test. **Judgement:** acceptable — the test's job is to assert the behavior (no silent path), not to freeze the implementation. The test lets future Dev refactor the guard without breaking.

### Observations (≥5)

1. **[VERIFIED] Pass 2 [MEDIUM] fully resolved** — Construction-time guard at `music_director.rs:355-363` prevents `Some(empty_map)` from ever existing in `themed_tracks`.
2. **[VERIFIED] All four silent paths in `select_variation()` are now closed** — Path enumeration confirmed by silent-failure-hunter and independently by my own read. [SILENT]
3. **[RULE] Rule A1 (No Silent Fallbacks) FULLY SATISFIED** — Explicit rule-checker verdict after three review passes. The story's primary goal is met. [RULE]
4. **[VERIFIED] Scope discipline preserved** — Pass 3 is 18 lines added, 0 removed in `music_director.rs`, plus a 138-line regression test. No scope creep. No pre-existing fmt debt touched.
5. **[VERIFIED] Construction-time guard is cleaner than an inline emission** — Reuses the Pass 2 else branch instead of adding a 4th emission site. Warning fires once per director construction, not per turn. The `themed_tracks` invariant is now explicit.
6. **[VERIFIED] `tracing::warn!` preserved for stdout observability** — Both the construction-time guard (line 356-362) and the `select_variation` fallback branches preserve paired `tracing::warn!` calls. Belt and suspenders — watcher channel and stdout both carry the signal.
7. **[VERIFIED] 14/14 tests passing** — 4 chargen × 2 tests, 3 audio fallback variants × 1 test each, 4 wiring tests, +1 new Pass 3 regression test.
8. **[VERIFIED] fmt break-even** — music_director.rs 25→25 (the only file Pass 3 touched).
9. **[VERIFIED] Both library crates still build clean** — `cargo build -p sidequest-game` and `cargo build -p sidequest-server`, warnings-only.
10. **[SILENT] One pre-existing out-of-scope observation** — `sidequest-genre::models::audio::AudioVariation::as_variation()` silently defaults unknown `variation_type` strings to `TrackVariation::Full`. Not touched by this story. Filed as a delivery finding for a follow-up.

### Tenant isolation audit

N/A — solo RPG game engine, no multi-tenant context.

### Data flow trace (Pass 3 — confirming the guard)

Genre pack YAML (malformed): `themes: [{name: "battle", mood: "combat", base_prompt: "...", variations: []}]`.

→ `GenrePack` loads successfully (sidequest-genre does not reject empty variations)
→ `MusicDirector::new(&audio_config)` at startup
→ iterates `audio_config.themes`, hits the combat theme with empty variations
→ **Pass 3 guard fires at line 355:** `tracing::warn!(mood="combat", theme_name="battle", "audio theme has no variations — skipping themed-track registration")`
→ `continue` — combat key is NOT inserted into `themed_tracks`
→ `themed_tracks = { /* other well-formed moods only */ }`
→ Later, during combat, mood classifier returns `primary: MoodKey::COMBAT`
→ `select_variation(&classification, &ctx)` at line 417
→ line 422: `self.themed_tracks.get("combat")` → `None` (because the guard skipped insertion)
→ **Pass 2 else branch fires** at line 464-484: `emit_variation_fallback("combat", preferred, preferred, "mood_not_in_themed_tracks", false)`
→ event lands on `/ws/watcher` broadcast channel
→ GM panel displays the variation_fallback event with `reason="mood_not_in_themed_tracks"`
→ line 488: `preferred` is returned
→ `evaluate()` falls through to un-themed `mood_tracks` pool via `select_track()`
→ Client plays a generic combat track (degraded but functional)

The malformed theme is now fully observable: the startup warning tells a developer running locally, and the per-turn `variation_fallback` events tell the GM panel. Both channels carry the signal.

**Handoff:** To Naomi Nagata (Architect, design mode) for spec-reconcile.

### TEA (test design)
- **Gap** (non-blocking): Story context pointed at `sidequest-api/crates/sidequest-game/src/chargen/{stats,backstory,hp_formula}.rs` and `sidequest-api/crates/sidequest-daemon-client/src/audio_variation.rs`, none of which exist. Actual locations are `crates/sidequest-game/src/builder.rs` (all three chargen paths) and `crates/sidequest-game/src/music_director.rs::select_variation()` (audio fallback). *Found by TEA during test design.*
- **Improvement** (non-blocking): The SM handoff pattern had a gap — `sm-setup` wrote the session file to `sprint/{story-id}-session.md` but `pf handoff complete-phase` reads from `.session/{story-id}-session.md`. Filed as slabgorb/pennyfarthing#11. Unblocked by manually moving the file. Worth fixing upstream so the next story doesn't repeat the workaround. *Found by TEA during test design.*
- **Question** (non-blocking): `builder.rs` line 998 already uses `WatcherEventBuilder` for `chargen.equipment_composed`. Should Dev match that exact component/event-type shape for the three new chargen events, or use a different `WatcherEventType` variant (e.g., one specific to chargen)? Recommend: keep `component="chargen"` + `WatcherEventType::StateTransition` for consistency with the existing emit. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): Five sibling test files in `sidequest-game/tests/` are pre-existing broken on develop due to fixture field drift — they predate additions to `RulesConfig::initiative_rules`, `GenrePack::equipment_tables`, `MechanicalEffects::{stat_generation, equipment_generation}`, `CharCreationScene::mechanical_effects`, and the `MusicEvalResult` signature change. Affected: `builder_story_2_3_tests.rs`, `treasure_xp_story_19_9_tests.rs`, `hp_formula_story_31_4_tests.rs`, `backstory_tables_story_31_2_tests.rs`, `cinematic_variation_story_12_1_tests.rs`. Plus an inline module `crates/sidequest-game/src/lore/tests.rs` missing `equipment_tables`. None are blockers for 35-13 — they just prevent running `cargo test -p sidequest-game` without a filter. Recommend a dedicated tech-debt story to re-green them. *Found by Dev during implementation.*
- **Gap** (non-blocking): `otel_structured_encounter_story_28_2_tests.rs` has 20/22 failing tests on clean develop — appears to be a TELEMETRY_LOCK poisoning cascade because its `fresh_subscriber` uses `.unwrap()` on the lock (no poison-recovery like 35-9 and 35-13 do). One initial panic poisons every subsequent test in the file. Recommend a one-line fix: switch the `.unwrap()` to the poison-recovery pattern from `otel_npc_subsystems_story_35_9_tests.rs`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `builder.rs::build()` still carries `let _span = info_span!("chargen.hp_formula", ...)` and similar `info_span!` calls alongside the new WatcherEventBuilder emissions. They're not harmful, but once the GM panel consumes the WatcherEvents directly there's a case for retiring the tracing spans to avoid double-recording. Out of scope for 35-13 but worth a follow-up. *Found by Dev during implementation.*

### TEA (test verification)
- No upstream findings during test verification.

### TEA (rework RED)
- **Improvement** (non-blocking): The original AC-4 phrasing ("emit OTEL event when audio variation generation fails and system falls back to default") is ambiguous about whether "falls back to default" means only the intra-mood fallbacks inside `select_variation()` or also the outer missing-mood-key path. Both are "fallbacks to default" in the sense that `evaluate()` then falls through to `mood_tracks`. Future ACs around subsystem observability should enumerate the fallback paths explicitly, not rely on a single catch-all phrase. Affects `sprint/epic-35.yaml` (AC wording for future similar stories). *Found by TEA during rework RED.*

### Dev (rework GREEN)
- **Gap** (non-blocking): Running `cargo fmt -p sidequest-game` on the full crate would rewrite 388 lines of pre-existing fmt debt in `builder.rs` (13 violations) and `music_director.rs` (25 violations), entirely unrelated to this story. Worked around by manually fixing only the story's new violations. Recommend a dedicated tech-debt story to run `cargo fmt` across the whole sidequest-game crate in a single dedicated commit — it's a ~400-line cleanup that touches no logic. Affects `sidequest-api/crates/sidequest-game/src/*.rs` (whole-crate fmt pass). *Found by Dev during rework GREEN.*
- **Gap** (non-blocking): `WatcherEventBuilder::field_opt("con_modifier", &con_mod.map(i64::from))` in `builder.rs:839` omits the `con_modifier` key entirely when the rules don't include a CON stat. The previous code emitted explicit `null`. GM panel consumers that expect `con_modifier` to always be present may need a schema note or a filter change. Current test fixture always rolls CON so no test change was needed. Affects GM panel consumer code (not in scope for this story). *Found by Dev during rework GREEN.*

### TEA (rework verify)
- No upstream findings during rework verify. Simplify fan-out returned clean on all three lenses (reuse, quality, efficiency) for the Pass 2 delta.

### TEA (Pass 3 verify)
- No upstream findings during Pass 3 verify. Simplify fan-out clean on all three lenses for the 18-line construction-time guard delta.

### Reviewer (Pass 3 code review)
- **Gap** (non-blocking, pre-existing, OUT OF SCOPE for 35-13): `sidequest-genre::models::audio::AudioVariation::as_variation()` silently defaults unrecognized `variation_type` strings to `TrackVariation::Full` with only a `tracing::warn!` — no watcher event. A genre pack with `variation_type: "typo_here"` will register as Full in `themed_tracks`, and if the subsequent `select_variation` call happens to prefer Full, Path A fires and returns Full with no emission. This is a different subsystem (sidequest-genre, not sidequest-game) and pre-existed all three passes of story 35-13. Recommend a follow-up story to either (a) emit a watcher event from `as_variation()` when it falls back, or (b) add a sidequest-genre::validate rule that rejects unknown variation_type strings. Affects `sidequest-api/crates/sidequest-genre/src/models/audio.rs:222-228`. *Found by Reviewer during Pass 3 code review (noted by silent-failure-hunter).*

### Reviewer (Pass 2 code review)
- **Gap** (non-blocking, [MEDIUM]): `music_director.rs::select_variation()` has a residual silent path when `themed_tracks` contains a mood key with an empty inner HashMap. `MusicDirector::new` at line 347 inserts the outer key via `or_default()` before iterating `theme.variations`; an `AudioTheme` with `variations: []` produces `Some(empty_map)`, and all three inner branches skip, bypassing the Pass 2 else branch and returning `preferred` silently. Same failure class as the Pass 1 [HIGH] on a rarer trigger. `sidequest-genre::validate` does not currently reject empty variations arrays (verified). Recommended fix: one-line `continue` guard in `MusicDirector::new()` when `theme.variations.is_empty()` — turns `Some(empty)` into `None`, which the Pass 2 else branch already handles. Affects `crates/sidequest-game/src/music_director.rs:343-349`. *Found by Reviewer during Pass 2 code review.*

### Reviewer (code review)
- **Gap** (blocking): `music_director.rs::select_variation()` has no `else` branch on the outer `if let Some(mood_variations)` — mood keys absent from `themed_tracks` silently return `preferred` with zero telemetry. Affects `crates/sidequest-game/src/music_director.rs:422-468` (add else branch emitting `variation_fallback` with `reason="mood_not_in_themed_tracks"`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `WatcherEventBuilder` already has `field_opt(key, &Option<T>)` at `sidequest-telemetry/src/lib.rs:122`, which would eliminate the awkward `let mut builder = ... ; builder = match con_mod` pattern in `builder.rs:839-848` and resolve the fmt violation at line 836 structurally. Caveat: `field_opt` omits the key when None, whereas the current code emits explicit null — behavior differs if the GM panel needs `con_modifier` always present. Affects `crates/sidequest-game/src/builder.rs:839` (optional refactor). *Found by Reviewer during code review.*
- **Question** (non-blocking): The backstory `fragments` branch at `builder.rs:1034` emits `method="fragments"` with a non-zero `length` even when every fragment is an empty/whitespace-only string (which can happen with a genre pack choice that has a blank description). The OTEL event can report a clean backstory when the player sees a blank one. Should this branch guard on `trim().is_empty()` and fall through to tables/fallback? Affects `crates/sidequest-game/src/builder.rs:1034`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Test exercises chargen subsystems through the builder pipeline, not direct calls**
  - Spec source: session story context, "Test strategy (for TEA)"
  - Spec text: "Tests should assert that the emitted spans/events carry the subsystem-specific fields"
  - Implementation: Tests drive `CharacterBuilder::build()` through minimal C&C scenes rather than calling `generate_stats()` / `evaluate_hp_formula()` directly, because both are private methods. The public `build()` entry point exercises all three chargen subsystems in a single pass.
  - Rationale: Preserves encapsulation and matches how production actually reaches these subsystems. Fits the A5 wiring rule — the test exercises the same code path the server does.
  - Severity: minor
  - Forward impact: none — Dev will emit the events inside `generate_stats`, `evaluate_hp_formula`, and the backstory composition block in `build()`, all of which the test path hits.

- **No direct test for point-buy stats path**
  - Spec source: session story context, AC 1 ("stats subsystem")
  - Spec text: "Emit OTEL span on attribute calculation (ability scores, modifiers)"
  - Implementation: The test fixture uses `stat_generation: roll_3d6_strict` only. It does not exercise the `standard_array` or `point_buy` branches of `generate_stats()`.
  - Rationale: All three branches converge on a single `chargen.stats_generated` emission (Dev should emit once at the end of `generate_stats`, not per-branch). Testing one branch is sufficient to prove the event is reachable; testing all three would duplicate coverage without adding signal.
  - Severity: minor
  - Forward impact: if Dev chooses to emit per-branch instead of once at the end, future tests may want a per-method assertion.

### Dev (implementation)
- **Single stats_generated emission covers all three stat-gen paths**
  - Spec source: TEA assessment, "No direct test for point-buy stats path" deviation + session AC 1
  - Spec text: "Emit OTEL span on attribute calculation (ability scores, modifiers)"
  - Implementation: Emitted `chargen.stats_generated` once at the end of `generate_stats()` (after stat_bonuses + standard_array differentiation), not per-branch inside the `roll_3d6_strict` / `standard_array` / `point_buy` match arms.
  - Rationale: Single convergence point captures the final stat state regardless of which method produced it. Matches TEA's stated preference. Simpler code, single emission per chargen, and the `method` field on the event still records which path ran.
  - Severity: minor
  - Forward impact: none — any future test that wants per-branch granularity can check the `method` field value.

- **Included full stats HashMap as an event field**
  - Spec source: TEA test `chargen_stats_generation_records_stat_values`
  - Spec text: "The event should carry at least one rolled stat value so the GM panel can sanity-check the roll distribution"
  - Implementation: Emitted the entire stats HashMap as a single `stats` JSON field rather than flattening into individual `stat_STR`, `stat_CON`, etc. fields.
  - Rationale: Serde serializes HashMap as a nested JSON object. GM panel can drill into the object. Flattening would have required ordered iteration and variable field count.
  - Severity: minor
  - Forward impact: none — field consumers read `event.fields.stats.CON` instead of `event.fields.stat_CON`.

- **hp_fallback is a distinct action, not an hp_formula_evaluated variant**
  - Spec source: TEA test `chargen_hp_formula_fallback_emits_watcher_event_when_no_formula`
  - Spec text: "must emit a chargen HP watcher event even when hp_formula is None"
  - Implementation: Used a new `action: "hp_fallback"` when no formula is set (the class_hp_bases / default_hp / hardcoded_10 chain), instead of reusing `hp_formula_evaluated` with a synthetic formula string.
  - Rationale: The two code paths represent semantically different decisions — "the evaluator ran this formula" vs "the evaluator did not run because no formula was configured". Separate action names let the GM panel filter on either mode without string-parsing a formula field. The test accepts either action name explicitly, so this satisfies the spec.
  - Severity: minor
  - Forward impact: none.

- **variation_fallback includes both `reason` and `full_available` fields**
  - Spec source: TEA test `audio_variation_fallback_to_first_available_emits_watcher_event`
  - Spec text: "must record why first-available was used (either a `reason` field or a `full_available=false` flag)"
  - Implementation: Emitted BOTH `reason` (string: "preferred_unavailable" | "only_first_available") AND `full_available` (bool). The test required either-or; I sent both.
  - Rationale: `reason` is human-readable for the GM panel label; `full_available` is a boolean the UI can use for color coding / severity. Cost is two extra JSON fields per fallback emission, which happens at most once per turn.
  - Severity: minor
  - Forward impact: none.

### TEA (test verification)
- **Applied simplify-reuse dedup against CLAUDE.md "premature abstraction" guidance**
  - Spec source: global CLAUDE.md (user memory) and simplify-reuse finding
  - Spec text: "Three similar lines of code is better than a premature abstraction"
  - Implementation: Extracted `emit_variation_fallback()` helper from two 10-line `WatcherEventBuilder` chains in `select_variation()`. Dedup is a 2-call-site, 3-param-difference refactor — borderline on the abstraction threshold.
  - Rationale: Verify workflow instructs TEA to mechanically apply `confidence: high` reuse findings. Applied per workflow. Flagged in assessment so Reviewer can choose to revert if the inline version reads more clearly.
  - Severity: trivial
  - Forward impact: none. Future field additions land in one place instead of two; inline readability trades off against centralized schema.
  - **→ ✓ ACCEPTED by Reviewer:** The helper is cleaner than the inline form at this call-site count. The `reason: &'static str` parameter type enforces the string-literal constraint at the type level — a small but real win. Keeping it.

### TEA (rework RED)
- No deviations from spec. The new test `audio_variation_fallback_when_mood_missing_from_themed_tracks` directly implements the Reviewer's [HIGH] finding as a failing assertion — same field shape, same `reason` convention, same `full_available=false` contract as the two existing variation_fallback tests. No spec interpretation required.

### TEA (rework verify)
- No deviations from spec during rework verify. Pass 2 delta is 37 insertions / 28 deletions across 3 files, all simplify-clean on first pass. Zero fixes applied, zero reverts, zero flagged findings.
  - **→ ✓ ACCEPTED by Reviewer (Pass 2):** Simplify fan-out returned clean on all three lenses. No deviations to stamp.

### TEA (Pass 3 RED)
- No deviations from spec. The new test `audio_variation_fallback_when_mood_has_empty_variations` directly implements the Pass 2 Reviewer's [MEDIUM] finding as a failing assertion. Deliberately written with a permissive `reason` field check (accepts `"mood_variations_empty"` OR `"mood_not_in_themed_tracks"` OR any "empty"/"mood" substring) so Dev can pick the cleaner implementation (construction-time guard vs inline emission) without the test forcing a specific approach. Keith directed "fix all wiring immediately" — Pass 3 closes the fourth silent path in-story rather than tracking as a follow-up.

### Dev (Pass 3 GREEN)
- No deviations from spec. Took the construction-time guard approach recommended by Pass 2 Reviewer: added `if theme.variations.is_empty() { continue; }` at `music_director.rs:347` with a paired `tracing::warn!`. This is the minimum change that closes the `Some(empty_map)` path while reusing the Pass 2 else branch — no new `reason` label, no new emission site, no hot-path cost.

### TEA (Pass 3 verify)
- No deviations from spec. Pass 3 delta (18 lines of guard + 138 lines of test) came back clean on all three simplify lenses. Zero fixes applied, zero reverts, zero flagged findings.
  - **→ ✓ ACCEPTED by Reviewer (Pass 3):** All three simplify lenses clean.

### Dev (Pass 3 GREEN)
- **→ ✓ ACCEPTED by Reviewer (Pass 3):** Construction-time guard is the cleanest option. It reuses the Pass 2 else branch, fires the warning once per director construction (not per-turn), and makes the `themed_tracks` invariant explicit. Zero scope creep. The `tracing::warn!` provides stdout coverage alongside the downstream watcher events.

### TEA (Pass 3 RED)
- **→ ✓ ACCEPTED by Reviewer (Pass 3):** Permissive `reason` field assertion was the right call — it let Dev pick the cleaner construction-time approach without forcing a new reason label.

### Dev (rework GREEN)
- **Switched con_modifier emission from explicit-null to field_opt (omit-on-None)**
  - Spec source: Reviewer Assessment recommendation, Pass 1 review
  - Spec text: "`field_opt` OMITS the key when the Option is None, whereas the current code emits an explicit `null`. If the GM panel filter logic requires `con_modifier` to always be present (even as null) to distinguish 'no CON stat' from 'HP formula didn't reference CON', keep the explicit match"
  - Implementation: Used `field_opt("con_modifier", &con_mod.map(i64::from))`. The field is omitted when `con_mod` is None instead of emitted as `null`.
  - Rationale: Reviewer's preferred form (structural fmt fix + cleaner fluent chain). Current test fixture always rolls CON so the existing test still passes. Schema change is forward-compatible — consumers that previously saw `"con_modifier": null` will now see the key absent, which is the conventional JSON way to express "not applicable" and matches how other optional OTEL fields are handled in the existing 35-8/35-9 emissions.
  - Severity: minor
  - Forward impact: GM panel consumer code reading this event must handle missing keys (which it should anyway). A future story touching genre packs with non-CON ability systems will see the difference; existing D&D-style genre packs are unaffected.
  - **→ ✓ ACCEPTED by Reviewer (Pass 2):** `i64::from` is strictly safer than `as i64` (compile-time enforced lossless widening, Rule #7 improvement). `field_opt` matches the 35-8/35-9 precedent. Semantic change documented and forward-compatible. Good call.

- **Did not run `cargo fmt` on the full crate**
  - Spec source: Reviewer Assessment [MEDIUM] finding + global CLAUDE.md minimalist discipline
  - Spec text: Reviewer said "Run `cargo fmt -p sidequest-game` on the branch"; CLAUDE.md says "A bug fix doesn't need surrounding code cleaned up"
  - Implementation: Ran `rustfmt` on all three changed files, saw that builder.rs and music_director.rs had 388 lines of pre-existing fmt debt that would be rewritten, reverted those files, and fixed only the story's new violations manually. Test file kept fully formatted (entirely new code, no pre-existing debt to avoid).
  - Rationale: Running fmt on the whole crate would conflate a minor story-scope fmt cleanup with a significant pre-existing tech-debt cleanup, making the diff noisy and harder to review. The Reviewer's intent was "don't leave new fmt violations"; that intent is satisfied with the minimal approach. Filed a delivery finding recommending a dedicated tech-debt story for the whole-crate pass.
  - Severity: minor
  - Forward impact: none — net fmt state vs develop is break-even (0 new violations introduced by this story).
  - **→ ✓ ACCEPTED by Reviewer (Pass 2):** Correct scope call. The Reviewer's intent was "don't leave new fmt violations", not "also clean up 388 lines of unrelated debt". Minimalist discipline is the right move. Dedicated follow-up story is the right way to address the pre-existing debt.

### Reviewer (audit)

#### TEA design deviations
- "Test exercises chargen subsystems through the builder pipeline, not direct calls" → ✓ ACCEPTED: Correct call. `generate_stats()` and `evaluate_hp_formula()` are private; exercising via the public `build()` entry point matches production paths and keeps the test wired to how the server reaches chargen.
- "No direct test for point-buy stats path" → ✓ ACCEPTED: Single convergence point at the end of `generate_stats()` is exactly what landed. All three branches (roll_3d6, standard_array, point_buy) funnel into one emission with a `method` field, so branch coverage of the EMISSION is guaranteed — branch coverage of the stat-generation LOGIC belongs to other test suites.

#### Dev design deviations
- "Single stats_generated emission covers all three stat-gen paths" → ✓ ACCEPTED: Confirmed by reading `builder.rs:1388-1397`. The emission is post-`generate_stats()` convergence, reached by all branches.
- "Included full stats HashMap as an event field" → ✓ ACCEPTED: HashMap<String, i32> serializes to a nested JSON object, which is readable on the GM panel and future-proof against renaming individual stats. Not sensitive data — stats are cosmetic/gameplay, not security boundaries.
- "hp_fallback is a distinct action, not an hp_formula_evaluated variant" → ✓ ACCEPTED: Two semantically distinct decisions (evaluator ran vs evaluator bypassed) deserve two action names. Clean schema.
- "variation_fallback includes both `reason` and `full_available` fields" → ✓ ACCEPTED: Both fields serve different consumers (human-readable label vs machine-filterable bool). The cost is 2 extra JSON fields per emission, which happens at most once per turn. Not wasteful.

#### Undocumented spec deviations
- **Missing AC-4 coverage for themed_tracks-missing-mood scenario:** AC-4 says "Emit OTEL event when audio variation generation fails and system falls back to default". Dev and TEA both treated "falls back to default" as "the intra-mood fallback inside `select_variation()`", but the outer `if let Some(mood_variations)` path — where the mood key isn't in `themed_tracks` at all — is ALSO a fallback to default (`evaluate()` then falls through to `mood_tracks`). This wasn't logged as a scope reduction by TEA or Dev. Flagged as [HIGH] in the Reviewer Assessment above. Dev to add an `else` branch and a new test.
  - **Pass 2 resolution:** Dev added the else branch at `music_director.rs:464-484` emitting `variation_fallback` with `reason="mood_not_in_themed_tracks"`. TEA added a regression test. Pass 2 Reviewer confirmed this path is now covered.

### Architect (reconcile)

**Audit scope:** Story 35-13 (OTEL watcher events for chargen subsystems + AudioVariation fallback). 5 commits across 2 reviews passes. 4 acceptance criteria. 6 existing deviation entries (2 TEA test design, 4 Dev implementation) plus 2 rework entries (TEA rework verify, 2 Dev rework GREEN) plus 1 Reviewer audit. Final AC coverage: 3/4 fully met, 1/4 (AC-4) substantially met with one residual non-blocking corner case.

**Existing deviation entries — verification:**

All 8 pre-reconcile deviation entries verified against the current code state:

1. **TEA — "Test exercises chargen subsystems through the builder pipeline, not direct calls"** ✓ Accurate. `build_test_character()` helper at test file line ~200 drives the full `CharacterBuilder::new → apply_freeform → apply_choice → build` sequence, exercising `generate_stats()` and the inline hp_formula + backstory blocks inside `build()` without calling them directly. Spec source reference (session story context) is valid; spec text quote is faithful.

2. **TEA — "No direct test for point-buy stats path"** ✓ Accurate. Test fixture uses `stat_generation: roll_3d6_strict` exclusively. The single convergence emission in `generate_stats()` at `builder.rs:1392-1397` makes branch-per-method testing redundant for the OTEL concern. Forward impact note ("if Dev chooses to emit per-branch") correctly describes what would have invalidated this call; Dev did converge, so the deviation is fully resolved.

3. **Dev — "Single stats_generated emission covers all three stat-gen paths"** ✓ Accurate. Verified at `builder.rs:1388-1397`. All three `match self.stat_generation.as_str()` arms flow through the post-match emission. The `method` field captures which path ran.

4. **Dev — "Included full stats HashMap as an event field"** ✓ Accurate. `builder.rs:1396` uses `.field("stats", &stats)` with `HashMap<String, i32>`. Serializes to a nested JSON object. No privacy concerns — stats are mechanical gameplay values, not PII.

5. **Dev — "hp_fallback is a distinct action, not an hp_formula_evaluated variant"** ✓ Accurate. Two separate `WatcherEventBuilder::new("chargen", ...)` emissions at `builder.rs:839-848` (action=hp_formula_evaluated) and `builder.rs:864-869` (action=hp_fallback). The `source` field on hp_fallback names which fallback level resolved.

6. **Dev — "variation_fallback includes both `reason` and `full_available` fields"** ✓ Accurate. All three call sites (via `emit_variation_fallback()` helper at `music_director.rs:41-57`) include both fields. Test assertions at lines 596-660 accept the union for test flexibility; Dev shipped both.

7. **TEA (rework verify) — "No deviations from spec during rework verify"** ✓ Accurate. Simplify fan-out came back clean on all three lenses. Zero applied fixes, zero reverts.

8. **Dev (rework GREEN) — "Switched con_modifier emission from explicit-null to field_opt (omit-on-None)"** ✓ Accurate and **important**. Verified at `builder.rs:847`. This IS a schema change to the `chargen.hp_formula_evaluated` event: previously `con_modifier: null` when CON absent, now the key is absent entirely. Dev's forward-impact note ("GM panel consumer code reading this event must handle missing keys") is correct. Reviewer Pass 2 accepted with rationale that it matches 35-8/35-9 precedent. **Confirmed accepted.**

9. **Dev (rework GREEN) — "Did not run `cargo fmt` on the full crate"** ✓ Accurate. Dev applied fmt only to story-scope changes; reverted pre-existing-debt lines touched by rustfmt. Net fmt state: break-even with develop (13/13, 25/25, 0/0 across the three files). Reviewer Pass 2 accepted.

**No inaccuracies found in existing entries.** All 6 required fields (spec source, spec text, implementation, rationale, severity, forward impact) are present and substantive across all 8 entries. No placeholder text.

**Missed deviations — added:**

- **Residual `Some(empty HashMap)` silent path in `select_variation()`** — PARTIALLY COMPLETE AC-4
  - Spec source: session file AC-4 ("Emit OTEL event when audio variation generation fails and system falls back to default") + CLAUDE.md "No Silent Fallbacks" categorical rule
  - Spec text: "Emit OTEL event when audio variation generation fails and system falls back to default" AND "If something isn't where it should be, fail loudly. Never silently try an alternative path, config, or default."
  - Implementation: Pass 2 covers THREE of FOUR silent-fallback paths in `select_variation()`: (a) preferred unavailable but Full exists → instrumented, (b) preferred and Full unavailable but something else exists → instrumented, (c) mood key not in `themed_tracks` at all (None case) → instrumented by Pass 2 else branch. The FOURTH path — `themed_tracks` contains the mood key but the inner `HashMap<TrackVariation, Vec<MoodTrack>>` is empty — is NOT instrumented. When `MusicDirector::new()` encounters a theme bundle with `variations: []`, the outer key gets inserted via `or_default()` but the inner map stays empty, producing `Some({})`. `select_variation()` then takes the `Some` arm but all three inner conditionals skip, control falls out without entering the else branch, and `preferred` is returned silently.
  - Rationale: Dev and TEA did not anticipate this edge case during either Pass 1 or Pass 2. The Reviewer's Pass 2 silent-failure-hunter caught it. Reviewer flagged at [MEDIUM] non-blocking because: (1) the trigger is a malformed YAML (`variations: []`) which is a content authoring error rather than a code defect, (2) `sidequest-genre::validate` does not currently reject this, verified, (3) downstream behavior is "play un-themed mood track from `mood_tracks`" — degraded but functional, (4) Pass 1 HIGH was the primary failure; this is a residual corner case. **The fix is one line at construction time:** skip inserting the mood key in `MusicDirector::new()` when `theme.variations.is_empty()`, which turns `Some(empty)` into `None` and lets the existing Pass 2 else branch handle it.
  - Severity: minor (residual edge case; primary AC-4 path is met)
  - Forward impact: A genre pack author who writes `variations: []` in a theme bundle will see the un-themed mood track play with zero watcher telemetry. The GM panel cannot distinguish this from "mood correctly themed". Recommend either (a) one-line fix in `MusicDirector::new()` as a follow-up chore, or (b) a `sidequest-genre::validate` rule rejecting empty variations arrays. Option (a) is preferred because it makes the construction-time invariant explicit rather than relying on upstream validation. Keith to decide fix-before-merge vs follow-up story.

**AC deferral verification:**

No ACs were deferred on this story. All 4 ACs (stats, backstory, hp_formula, AudioVariation fallback) were in scope for Pass 1, and the ac-completion gate did not record any deferrals. AC-4 is substantially but not fully met due to the residual deviation above — this is documented as a known gap rather than a deferral. Reviewer approved with that understanding; the gap will either be fixed pre-merge or tracked as a follow-up per Keith's direction.

**Final deviation manifest (post-Pass 2):** 9 total entries across the story — 2 TEA (test design), 4 Dev (implementation), 1 TEA (rework verify), 2 Dev (rework GREEN), plus 1 Architect (reconcile) entry added above. All accepted by Reviewer or carried forward as Pass 2 non-blocking findings. Story AC-1, AC-2, AC-3 fully met. AC-4 substantially met with one documented residual edge case.

---

### Architect (reconcile) — Pass 3 update

**Status change:** The reconcile section above was written after Pass 2 and described the `Some(empty HashMap)` residual silent path as "PARTIALLY COMPLETE AC-4" with a recommendation for a fix-before-merge vs follow-up decision. Keith decided: "fix all wiring immediately we have too many problems." Pass 3 closed the gap.

**Pass 3 summary (2 new commits):**
- `6062600 test(35-13): RED — Some(empty HashMap) silent path in select_variation()` — TEA added failing test `audio_variation_fallback_when_mood_has_empty_variations` with fixture `audio_config_combat_theme_with_empty_variations()` (+138 lines). Test accepts either `mood_variations_empty` OR `mood_not_in_themed_tracks` as the reason field, giving Dev implementation flexibility.
- `8b67732 fix(35-13): skip empty-variations themes in MusicDirector::new` — Dev added an 18-line construction-time guard at `music_director.rs:355-363`: `if theme.variations.is_empty() { tracing::warn!(...); continue; }` before `entry(mood).or_default()`. Structurally eliminates `Some(empty_map)` from `themed_tracks`, routing empty-variations themes through the existing Pass 2 else branch.

**Verification:**
- 14/14 tests passing (13 carried from Pass 2 + 1 new from Pass 3 RED)
- Rule-checker Pass 3 explicitly states: "Rule A1 is NOW FULLY SATISFIED for this file... No silent return of preferred remains."
- Silent-failure-hunter Pass 3: "clean" — Path D (`Some(empty_map)`) is "structurally eliminated"
- Preflight Pass 3: tests green, fmt break-even (25/25 on music_director.rs vs develop), 0 code smells
- `cargo build -p sidequest-game` and `cargo build -p sidequest-server` both clean

**Pass 3 deviation entries — verification:**

10. **TEA (Pass 3 RED) — "No deviations from spec. The new test ... directly implements the Pass 2 Reviewer's [MEDIUM] finding"** ✓ Accurate. Test file line ~799 (`audio_variation_fallback_when_mood_has_empty_variations`) and fixture at line ~758 (`audio_config_combat_theme_with_empty_variations`). Permissive reason field assertion accepts both strategies, correctly giving Dev flexibility.

11. **Dev (Pass 3 GREEN) — "No deviations from spec. Took the construction-time guard approach"** ✓ Accurate. Verified at `music_director.rs:355-363`. One `if`, one `tracing::warn!`, one `continue`. No new emission site, no new reason label, no hot-path cost. Reuses the Pass 2 else branch via `mood_not_in_themed_tracks` reason.

12. **TEA (Pass 3 verify) — "No deviations from spec. Pass 3 delta came back clean on all three simplify lenses"** ✓ Accurate. Simplify fan-out (reuse, quality, efficiency) all returned `status: clean` with 0 findings each.

**No additional deviations missed by the agents.** The Pass 3 delta is 2 commits, 2 files, 156 lines total. All changes are directly targeted at closing the Pass 2 [MEDIUM] finding. Zero scope creep.

**AC coverage — FINAL state:**

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-1 | stats subsystem: OTEL span on attribute calculation | ✅ FULLY MET | `chargen.stats_generated` emitted in `generate_stats()` at `builder.rs:1388-1397` with method, stat_count, full stats HashMap |
| AC-2 | backstory subsystem: OTEL span on narrative block generation | ✅ FULLY MET | `chargen.backstory_composed` emitted after composition at `builder.rs:1068-1075` with method and length |
| AC-3 | hp_formula subsystem: OTEL span on HP calculation | ✅ FULLY MET | `chargen.hp_formula_evaluated` at `builder.rs:839-848` (formula path) and `chargen.hp_fallback` at `builder.rs:864-869` (no-formula path). At chargen, base_hp == max_hp so a single emission covers both |
| AC-4 | AudioVariation fallback: OTEL event on audio fallback | ✅ FULLY MET (after Pass 3) | All 4 silent paths in `select_variation()` closed: preferred_unavailable (Path B), only_first_available (Path C), Some(empty_map) structurally eliminated by Pass 3 construction-time guard (Path D), mood_not_in_themed_tracks (Path E). Rule A1 (No Silent Fallbacks) explicitly "FULLY SATISFIED" per Pass 3 rule-checker |

**All 4 ACs fully met. No residual gaps. Story is ready for finish.**

**Final deviation manifest (post-Pass 3):** 12 total entries across the story — 2 TEA (test design), 4 Dev (implementation), 1 TEA (rework verify), 2 Dev (rework GREEN), 1 TEA (Pass 3 RED), 1 Dev (Pass 3 GREEN), 1 TEA (Pass 3 verify), plus 1 Architect (reconcile) + 1 Architect (reconcile Pass 3 update). All accepted by Reviewer. Story spec is substantively and completely met.

**Outstanding observations (intentionally out of scope):**
- **`as_variation()` silent default** (Pass 3 Reviewer delivery finding): `sidequest-genre::models::audio::AudioVariation::as_variation()` silently defaults unknown `variation_type` strings to `TrackVariation::Full`. Different subsystem (sidequest-genre, not sidequest-game), different class of issue, pre-existed all 3 passes of story 35-13. Filed as a follow-up for a dedicated story.
- **Blank-fragments backstory edge case** (Pass 1 Reviewer low-confidence): Genre pack with `description: ""` fragments produces whitespace-only backstory with `method="fragments"` and non-zero length. Low-confidence, not blocking. Unaddressed — different subsystem than the audio variation focus of this story.
- **sidequest-telemetry channel overflow** (Pass 1 Reviewer low-confidence): Out of scope for story 35-13 (the emit() sink predates this work). Unchanged.
- **Pre-existing fmt debt in builder.rs and music_director.rs** (Dev Pass 2 delivery finding): 38 fmt violations across the two files on develop. Net story impact is 0 new violations (break-even). Recommended as a dedicated tech-debt story to run whole-crate `cargo fmt` in a single commit.

These are all documented and tracked as delivery findings, not gaps in this story's scope.