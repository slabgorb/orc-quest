---
story_id: "35-9"
jira_key: "MSSCI-35-9"
epic: "MSSCI-35"
workflow: "trivial"
---

# Story 35-9: OTEL watcher events for NPC subsystems — belief, disposition, actions, gossip

## Story Details
- **ID:** 35-9
- **Jira Key:** MSSCI-35-9
- **Workflow:** trivial
- **Epic:** MSSCI-35 (Wiring Remediation II)
- **Stack Parent:** none

## Scope

This story adds OTEL watcher events to four core NPC subsystems currently wired but invisible to the GM panel:

1. **belief_state** (`sidequest-game/src/belief_state.rs`) — NPC belief tracking about player state
2. **disposition** (`sidequest-game/src/disposition.rs`) — NPC stance/alignment changes
3. **npc_actions** (`sidequest-game/src/npc_actions.rs`) — NPC turn decisions (move, attack, defend, etc.)
4. **gossip** (`sidequest-game/src/gossip.rs`) — NPC information propagation and rumor spreading

Each subsystem will emit `WatcherEvent`s at decision points so the GM panel can observe NPC decision-making in real-time without requiring code inspection.

## Workflow Tracking

**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-10T10:35:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-10T05:55:00Z | 2026-04-10T10:10:01Z | 4h 15m |
| implement | 2026-04-10T10:10:01Z | 2026-04-10T10:26:28Z | 16m 27s |
| review | 2026-04-10T10:26:28Z | 2026-04-10T10:35:46Z | 9m 18s |
| finish | 2026-04-10T10:35:46Z | - | - |

## Sm Assessment

**Ready for implementation.** Story 35-9 is a trivial (3pt) additive instrumentation task following the proven pattern from 35-8 (beat_filter/scene_relevance OTEL). Four NPC subsystems — belief_state, disposition, npc_actions, gossip — need WatcherEvent emission at decision points so GM panel can observe NPC decision-making in real time.

**Scope is bounded:** pure additive OTEL instrumentation, no logic changes. Existing subsystems are already wired; this story exposes them to the watcher pipeline.

**Routing:** Hand off directly to Dev (Naomi Nagata). Trivial workflow skips TEA — Dev implements, Reviewer gates. Wiring test assertion (per CLAUDE.md A5) must verify dispatch path reaches these subsystems and events are observable by subscribers.

**Risks:** Low. Fire-and-forget `.send()` pattern per telemetry contract — no blocking, no new deps. Main discipline point: don't silently swallow errors beyond what the contract specifies, and ensure every decision point actually emits (no dark corners).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-api):**
- `crates/sidequest-game/src/belief_state.rs` — OTEL on `add_belief` (variant, subject, content, source, turn_learned, post-count) and `update_credibility` (target, previous, requested, clamped).
- `crates/sidequest-game/src/disposition.rs` — OTEL on `apply_delta` with old/new value, old/new attitude, and threshold-crossing flag. Preserved existing tracing span.
- `crates/sidequest-game/src/npc_actions.rs` — OTEL on `select_npc_action`; reclaimed the underscored `_npc_id` parameter so the event actually names the acting NPC. Added role/variant label helpers.
- `crates/sidequest-game/src/gossip.rs` — OTEL summary on `propagate_turn` with turn, npc_count, claims_spread, contradictions_found.
- `crates/sidequest-game/tests/otel_npc_subsystems_story_35_9_tests.rs` — new integration + wiring test file (9 tests).

**Tests:** 9/9 passing (GREEN) in the new integration file. Regression suites verified:
- `gossip_propagation_story_7_2_tests` — 22/22
- `npc_actions_story_7_5_tests` — 25/25
- `disposition::tests` (unit) — 17/17

**Build:** `cargo build -p sidequest-game` green. `cargo build -p sidequest-server` green. No new warnings in the four touched source files.

**Branch:** `feat/35-9-otel-watcher-events-npc-subsystems` (pushed)
**Commit:** 76fceac

**Pattern:** Follows 35-8 (beat_filter + scene_relevance) — `WatcherEventBuilder::new(component, StateTransition).field(...).send()`, fire-and-forget via the global broadcast channel (`.send()` is a no-op if `init_global_channel` hasn't been called, so CLI tools and unit tests remain unaffected).

**Wiring verification (A5):** The integration test file includes four grep-based wiring assertions that will fail loudly if any production caller is removed:
1. `dispatch/connect.rs` calls `belief_state.add_belief`
2. `state.rs` calls `disposition.apply_delta`
3. `scenario_state.rs` calls `GossipEngine::propagate_turn` and `select_npc_action`
4. `dispatch/mod.rs` calls `scenario_state.process_between_turns`

All four were verified by grep before implementation and are now guarded by assertion tests.

**Handoff:** To review phase (Reviewer / Avasarala).

### Dev (implementation)
- No deviations from spec.

## Subagent Results

Only the enabled subagents (per `workflow.reviewer_subagents` settings) were spawned. Disabled subagents are pre-filled as Skipped.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — all green |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 1 (deferred, non-blocking), dismissed 1 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 (LOW severity, non-blocking) |

**All received:** Yes (3 active subagents returned, 6 disabled via settings)
**Total findings:** 2 confirmed (1 MEDIUM deferred, 1 LOW), 1 dismissed (with rationale)

### Finding Disposition

**[SILENT-1] weighted_select ActNormal fallback blindness** — `crates/sidequest-game/src/npc_actions.rs` around the new OTEL emission at the end of `select_npc_action`
- Source: silent-failure-hunter (medium confidence)
- Issue: `weighted_select` has two silent `ActNormal` fallback paths (zero-total-weight guard and tail fallback) that are indistinguishable in the telemetry from a legitimate weighted selection. Both emit `selected_variant = "act_normal"`.
- **Decision: CONFIRMED, DEFERRED (non-blocking).** The fallback paths pre-date this story and are not in the diff. Instrumenting them properly requires refactoring `weighted_select` to return a tagged enum (`Weighted { action } | ZeroWeightFallback | TailFallback`) and threading that through `select_npc_action`. That is scope expansion — the story is "add OTEL to existing decision points", not "refactor the RNG fallback logic". Logged as an upstream Improvement finding (non-blocking) per ADR-0031 for a follow-up story.

**[SILENT-2] Poison-lock recovery in test `fresh_subscriber()`** — `crates/sidequest-game/tests/otel_npc_subsystems_story_35_9_tests.rs:48`
- Source: silent-failure-hunter (low confidence, watchlist)
- Issue: `unwrap_or_else(|poisoned| poisoned.into_inner())` could mask a real panic if this pattern migrated into production lock sites.
- **Decision: DISMISSED.** Rule-checker confirmed this is the canonical Rust pattern for test-harness cascade prevention and complies with rule #14. The mutex lives only in the test file; no production code acquires `TELEMETRY_LOCK`. Dismissal rationale: `rule #14 compliant (fresh_subscriber() line 44)` per rule-checker's explicit assessment: *"unwrap_or_else(|p| p.into_inner()) is the canonical Rust pattern for lock-poisoning cascade prevention... correct isolation, not a symptom mask."*

**[RULE-6] `selected_variant` test assertion is vacuous** — `crates/sidequest-game/tests/otel_npc_subsystems_story_35_9_tests.rs:~265`
- Source: rule-checker (high confidence, rule #6 violation)
- Issue: `select_npc_action_emits_watcher_event` asserts `selected_variant.is_some()` but the field is never `None` in this code path. With the fixed seed `[42u8;32]`, `Guilty` role, and `tension=0.9`, the output is deterministic and could be pinned to an exact variant — OR, more robustly, to a `matches!` against the legal Guilty-role variant set (`create_alibi | destroy_evidence | flee | confess | act_normal | spread_rumor`).
- **Decision: CONFIRMED, LOW severity.** This is a rule violation and cannot be dismissed, but severity is LOW because: (a) the other 8 tests in the file make field-level assertions that cover most regression surface, (b) the instrumentation itself is verified by the build (the `action_variant` helper does exhaustive matching so label errors are caught at compile time), and (c) pinning an exact variant risks flakiness across `rand` crate version bumps. Rule-matching finding — included in assessment, not dismissed. Non-blocking per severity table (Low does not block PR).

### Rule Compliance

Enumerated the Rust lang-review checklist (`.pennyfarthing/gates/lang-review/rust.md`, 15 rules) against every function, type, and field in the diff. Rule-checker performed the same exhaustive sweep; my read agrees with its 46-of-47 compliant result.

- **[VERIFIED] Rule #1 (silent errors):** Six new code sites, zero `.ok()` / `.unwrap_or_default()` / `.expect()` on user-controlled paths. `BeliefState::add_belief`, `update_credibility`, `belief_signature`, `Disposition::apply_delta`, `select_npc_action`, `GossipEngine::propagate_turn` — all emit via builder then proceed.
- **[VERIFIED] Rule #2 (non_exhaustive):** No new `pub enum` declarations. `role_label` and `action_variant` use exhaustive wildcard-free matches on existing `ScenarioRole` / `NpcAction` — compile-time failure if new variants are added without telemetry updates, which is the correct guardrail.
- **[VERIFIED] Rule #3 (placeholders):** Source labels `witnessed`/`inferred`/`overheard`/`told_by:{name}` are semantic values, not trace-ID placeholders. Event action names (`belief_added`, `credibility_updated`, `disposition_shifted`, `action_selected`, `turn_propagated`) are protocol-fixed.
- **[VERIFIED] Rule #4 (tracing coverage):** New code has no error paths. `disposition.rs` preserves the pre-existing `tracing::info_span!("disposition.shift", ...)` alongside the new OTEL emission — no regression in trace coverage.
- **[VERIFIED] Rule #5 (validated constructors):** Not at a trust boundary. `Credibility::new(score)` clamps internally; not an API entry point.
- **[RULE-6 VIOLATION] Rule #6 (test quality):** 1 violation (see finding above). 8 other tests compliant.
- **[VERIFIED] Rule #7 (unsafe casts):** Zero new `as` casts. Pre-existing `as u32` in `gossip.rs:101` is unchanged and out of scope.
- **[VERIFIED] Rule #8 (Deserialize bypass):** `BeliefState` and `Credibility` have `#[derive(Deserialize)]` but their `new()` constructors have no runtime-enforced invariants beyond clamping — and the Deserialize path is trusted-save-file restoration by design. Pre-existing and not altered by this diff.
- **[VERIFIED] Rule #9 (public fields):** `BeliefState.beliefs` / `credibility_scores` remain private with getters. `Contradiction` and `PropagationResult` have pub fields but no invariants or security semantics.
- **[VERIFIED] Rule #10 (tenant context):** No new trait methods. N/A.
- **[VERIFIED] Rule #11 (workspace deps):** No Cargo.toml changes.
- **[VERIFIED] Rule #12 (dev-only deps):** `sidequest-telemetry` is used in production `src/*.rs` files, correctly in `[dependencies]`.
- **[VERIFIED] Rule #13 (constructor/Deserialize consistency):** Pre-existing asymmetry on `Credibility`, not introduced by this diff.
- **[VERIFIED] Rule #14 (fix regressions):** No re-review fixes (this is the first review pass). `fresh_subscriber()` poison recovery is canonical test-harness idiom, not a symptom mask.
- **[VERIFIED] Rule #15 (unbounded recursion):** No recursive parsers. `detect_contradictions` is pre-existing O(n²) over a local Vec with no recursion.

**Compliance: 14 of 15 rules fully clean, 1 rule with 1 LOW-severity test violation.**

### Devil's Advocate

*What if this code is broken? Arjun, argue against approval.*

**Hot-path cost.** The new OTEL emissions fire unconditionally from every call site, including inside `propagate_turn` which calls `add_belief` in the inner loop. For a fully-connected N-NPC scenario, `propagate_turn` emits up to O(N × beliefs × neighbors) `belief_added` events plus one summary event. A 10-NPC scenario with 20 beliefs each and full adjacency generates ~2000 events per turn. Each event allocates: a `HashMap<String, serde_json::Value>`, a `String` for the component name, multiple `Value::String` entries, and for `told_by:{name}` sources an additional `format!` allocation. If a subscriber is connected (the GM panel), every turn will pay this cost. The `fire-and-forget` contract says `.send()` is no-op when no subscriber, which is fine — but the moment a GM panel connects, turn latency will bump. No benchmark, no budget, no throttle. *Counter:* This matches the 35-8 pattern which is already in production; if it were a real issue, 35-8 would have surfaced it. The hot path during an actual scenario turn is dominated by the Claude LLM call (seconds), not HashMap allocation (microseconds). Accept as acknowledged cost — watchlist for sprint metrics.

**Missing NPC id in belief_state events.** `BeliefState::add_belief` fires the event from inside the container type, which has no knowledge of which NPC owns it. The GM panel sees "a belief was added with subject=X content=Y" but cannot tell whose belief state it landed in. For the credibility_updated path, `target_npc` is a trust-target label, not the opining NPC. If Alice updates her credibility of Bob and Charlie updates his credibility of Bob in the same turn, the GM panel sees two events with `target_npc=bob` and no way to distinguish who changed their view. *Counter:* The story's implementation pattern says "emit from the subsystem module"; Dev followed that. Adding owner context would require changing `add_belief` and `update_credibility` signatures to take `&str npc_name`, which ripples through every caller and is genuine scope expansion. A follow-up story could thread this — log as upstream finding.

**Redundant `attitude_changed` field.** The consumer can derive this from `old_attitude != new_attitude`. Storing the boolean adds noise. *Counter:* It's a UX convenience for the GM panel query layer. No harm. Keep.

**`previous_score` as JSON null on first update.** The test explicitly pins `previous_score = null` on first update. A consumer iterating events and pattern-matching on `previous_score` must handle the null case or crash. *Counter:* Documented in the test, serde_json standard behavior. Acceptable.

**Devil's Advocate conclusion:** Two watchlist items (hot-path cost, missing owner context in belief_state events) surface as legitimate upstream findings but neither blocks this story. The one rule violation (test assertion vacuity) stands as a LOW severity confirmed finding.

## Deviation Audit

### Dev (implementation)
- No deviations from spec. → ✓ ACCEPTED by Reviewer: confirmed no undocumented divergences from the story session scope or implementation pattern. The choice to emit from subsystem functions (rather than callers with NPC context) is consistent with the session's "Import WatcherEventBuilder into each subsystem module" directive. Gossip summary (vs per-claim) event is not mandated either way by the session. No hidden scope creep.

### Reviewer (audit)
- No undocumented deviations observed.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** LLM produces a state patch → `sidequest-server::dispatch` applies the patch → `state.rs::apply_patch` calls `npc.disposition.apply_delta(delta)` at line 549 → `Disposition::apply_delta` mutates `self.0` via `saturating_add` and fires `WatcherEventBuilder::new("disposition", StateTransition).field(...).send()` → event lands on the global broadcast channel initialized by `sidequest-server` at startup → `/ws/watcher` subscribers (GM panel) receive it. Safe because: no user-controlled allocation loop, no blocking I/O, no error path that could panic the dispatch handler.

**Pattern observed:** Consistent additive instrumentation following the 35-8 template. `WatcherEventBuilder::new(component, WatcherEventType::StateTransition).field(...).send()` — four files, four emissions, one summary emission. `belief_state.rs:45-58` (add_belief), `belief_state.rs:80-96` (update_credibility), `disposition.rs:77-91` (apply_delta), `npc_actions.rs:74-90` (select_npc_action), `gossip.rs:108-118` (propagate_turn summary).

**Error handling:** Fire-and-forget by contract — `.send()` is a documented no-op when the global channel is uninitialized (`sidequest-telemetry/src/lib.rs:155-160`). No new error paths introduced in any of the four subsystem functions. `Vec::push` in `add_belief` and `HashMap::insert` in `update_credibility` only panic on OOM (system-level abort). `belief_signature`'s `format!("told_by:{name}")` has the same allocation-failure profile.

**Wiring verification:** All four wiring tests in the new integration file use `include_str!` with compile-time path validation. The production call sites are present at `dispatch/connect.rs:1164` (belief_state), `state.rs:549` (disposition), `scenario_state.rs:290,318` (gossip + npc_actions), and `dispatch/mod.rs:522` (scenario_state). CLAUDE.md A5 rule satisfied — every test suite has at least one integration-level wiring test and the wiring tests are reachable from production via grep.

**Confirmed findings (non-blocking):**

| Severity | Issue | Location | Source |
|----------|-------|----------|--------|
| [MEDIUM] [SILENT] | weighted_select ActNormal fallback paths indistinguishable from legitimate selection in telemetry — deferred as upstream finding | `crates/sidequest-game/src/npc_actions.rs:~215-230` | silent-failure-hunter |
| [LOW] [RULE] | `selected_variant` asserted `.is_some()` only; should `matches!` against legal Guilty-role variant set | `crates/sidequest-game/tests/otel_npc_subsystems_story_35_9_tests.rs:~265` | rule-checker (rule #6) |

Neither Critical nor High — no blocking issues. Clippy clean on touched files, 9/9 tests pass, working tree clean, branch pushed, builds green for both `sidequest-game` and `sidequest-server`.

**Good pattern observations:**
- Exhaustive matches without wildcards in `role_label` and `action_variant` — adding a new enum variant is a compile error, which is the correct guardrail.
- Preserving the existing `tracing::info_span!` in `disposition.rs` alongside the new OTEL emission — no regression in span-based observability.
- `attitude_changed` boolean as a derived convenience — saves consumers from having to compare strings.
- `previous_score` as `Option<f32>` serializing to `null` — explicit "first time" signal rather than a hidden default.

**Handoff:** To SM for finish-story (Drummer).

### Reviewer (code review)
- **Improvement** (non-blocking): `weighted_select` in `crates/sidequest-game/src/npc_actions.rs` has two silent `ActNormal` fallback paths (zero-total-weight guard and tail fallback). The new OTEL telemetry cannot distinguish them from a legitimate weighted selection of `ActNormal`. Affects `crates/sidequest-game/src/npc_actions.rs` (refactor `weighted_select` to return a tagged selection enum so `selection_path` can be emitted as a telemetry field). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `BeliefState::add_belief` and `update_credibility` emissions have no owning-NPC identifier because `BeliefState` is a container with no self-awareness of its owner. The GM panel must correlate belief events by subject/content rather than owner. Affects `crates/sidequest-game/src/belief_state.rs` (thread an `&str npc_name` parameter through `add_belief`/`update_credibility` and update all callers). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Test `select_npc_action_emits_watcher_event` asserts `selected_variant.is_some()` instead of verifying the emitted label is in the valid variant set. Affects `crates/sidequest-game/tests/otel_npc_subsystems_story_35_9_tests.rs:~265` (replace `is_some()` with `matches!(variant, Some("create_alibi" | "destroy_evidence" | "flee" | "confess" | "act_normal" | "spread_rumor"))`). Rule #6 violation, low severity. *Found by Reviewer during code review.*

## Delivery Findings

No upstream findings.

### Dev (implementation)
- No upstream findings.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

None at setup.

## Implementation Pattern

Based on story 35-8 (beat_filter and scene_relevance OTEL):

1. Import `sidequest-telemetry::WatcherEventBuilder` into each subsystem module
2. Call `WatcherEventBuilder::new()` at key decision points
3. Populate fields with decision data (NPC id, old/new values, decision reason)
4. Emit via broadcast channel (fire-and-forget pattern)
5. No blocking — `.send()` errors are discarded per telemetry contract

Subsystems already have full logic; story is pure additive instrumentation.

## Dependencies

- Must have `sidequest-telemetry` crate accessible (already in workspace)
- No new external dependencies
- Depends on existing `sidequest-server` dispatch pipeline (story 35-7)

## Test Requirements

Per CLAUDE.md A5 (Every Test Suite Needs a Wiring Test):
- Unit tests in each subsystem verify emitted events have correct fields
- Integration test verifies GM panel (or test harness) can subscribe and receive events from the dispatch pipeline
- Wiring test assertion: `sidequest-server::dispatch` calls these subsystems AND they emit events visible to subscribers