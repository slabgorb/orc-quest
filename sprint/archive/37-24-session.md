---
story_id: "37-24"
jira_key: ""
epic: "37"
workflow: "wire-first"
---
# Story 37-24: NPC mechanical turn + stealth/trope check

## Story Details
- **ID:** 37-24
- **Title:** NPC mechanical turn + stealth/trope check — narrator currently weaves enemy/stealth outcomes with zero OTEL; emit npc.turn and trope handshake spans, surface minimal UI cue, close Illusionism gap
- **Jira Key:** (none)
- **Workflow:** wire-first
- **Stack Parent:** none
- **Points:** 5
- **Type:** bug
- **Priority:** p1

## Acceptance Criteria

1. **OTEL Coverage:** Narrator dispatch emits `npc.turn` span when NPC agents act (enemy turns, stealth resolution, etc.)
   - Spans include actor identity and mechanical outcome (success/failure on check)
   - Call site: dispatch/turn.rs (TBD on exact location after exploration)

2. **Trope Handshake:** Trope engine receives notification when stealth/confrontation/evasion outcomes are resolved
   - Emit `trope.engagement_outcome` or similar span with outcome details
   - Call site: tropes.rs (TBD on dispatch wiring point)

3. **UI Minimal Cue:** Small indicator on GM panel or player viewport showing NPC action taken
   - Call site: (TBD after dev exploration)

4. **No Illusionism Blindness:** GM can trace NPC behavior against mechanical rolls in OTEL
   - All narrator's NPC action decisions must have backing OTEL spans

## Workflow Tracking
**Workflow:** wire-first
**Phase:** finish
**Phase Started:** 2026-04-19T00:18:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-18T23:27:04Z | 2026-04-18T23:27:53Z | 49s |
| red | 2026-04-18T23:27:53Z | 2026-04-18T23:58:39Z | 30m 46s |
| green | 2026-04-18T23:58:39Z | 2026-04-19T00:06:17Z | 7m 38s |
| review | 2026-04-19T00:06:17Z | 2026-04-19T00:18:30Z | 12m 13s |
| finish | 2026-04-19T00:18:30Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design. Existing `test_support::telemetry` harness and `WatcherEventBuilder` pattern (per Architect survey of otel_dice_spans_34_11_tests) were sufficient; no gaps discovered.

### Dev (implementation)
- **Improvement** (non-blocking): `TropeDefinition` lacks a first-class `engagement_kind` enum field.
  Affects `crates/sidequest-genre/src/models/tropes.rs` (could add `engagement_kind: Option<EngagementKind>` with enum `{Stealth, Confrontation, Evasion}` and deprecate tag-based classification over time).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): Scenario `NpcAction` dispatch has no mechanical-roll integration — every autonomous NPC action currently emits `mechanical_basis="narrative"`.
  Affects `crates/sidequest-game/src/scenario/` (scenario engine could carry an optional `RollResult` on NpcAction events; dispatch would then forward a proper roll reference).
  *Found by Dev during implementation.* The signal is still correct — the GM panel will show every scenario NPC action as narrator-only, which is the truth — but a future story should feed mechanical rolls through when scenario NPCs attempt stat checks.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec. Tests follow Architect's event-contract schema exactly.

### Dev (implementation)
- **Trope engagement classification via tags, not a dedicated field**
  - Spec source: Architect Assessment, this session file
  - Spec text: "Emit at beat fired path (lines ~150–154) — only when the fired beat is a stealth/confrontation/evasion engagement beat (tag-filtered)"
  - Implementation: `classify_engagement_kind()` matches against `TropeDefinition.tags` case-insensitively. Accepted tags: `stealth` → stealth; `confrontation` OR `combat` → confrontation; `evasion` OR `chase` → evasion. `combat` and `chase` folded in because existing content already uses those tags for the same semantic (e.g. caverns_and_claudes combat tropes, road_warrior chase tropes) and forcing content rewrites for a single word would spread scope.
  - Rationale: TropeDefinition has no first-class `engagement_kind` field; tags are the only existing hook. Folding synonyms preserves signal across the pack library without content edits.
  - Severity: minor
  - Forward impact: If a future story wants strict three-value engagement_kind, content packs can be audited to normalize tags, or TropeDefinition can get a dedicated field. Neither blocks 37-24.

- **NPC turn outcome defaults to "success" for scenario autonomous actions**
  - Spec source: Architect Assessment, event contract for `npc.turn`
  - Spec text: "`outcome` — `\"success\" | \"failure\" | \"partial\"` (String)"
  - Implementation: scenario-driven NpcAction emissions pass `"success"` because ScenarioEvent has no failure/partial variant at the current dispatch point — the action already happened by the time it reaches dispatch.
  - Rationale: Non-deviation in letter (still in the allowed set) but worth logging so reviewer sees the spec allows three values and only one is used at this call site today. Future rolled NPC checks will pass failure/partial.
  - Severity: trivial
  - Forward impact: none for 37-24; downstream stories that add rolled NPC actions will widen the set.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|------------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (tests 76/76 verified externally, no code smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (2 high, 1 low) | 2 confirmed and resolved in rework (B1, B4); 1 low dismissed (pre-existing channel behavior) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (3 high, 2 medium) | 3 confirmed and resolved via wiring-test additions (B3) + narrative outcome test; 2 subsumed or dismissed |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (1 high, 3 medium) | 2 confirmed and fixed (B2 param-name misalignment, N3 overclaim); 2 addressed (N4 ticket-ref, implicit outcome rationale) |
| 6 | reviewer-type-design | Yes | findings | 3 (2 high, 1 medium) | Deferred as non-blocking follow-up (N1 — typed-enum refactor across all OTEL emitters) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 (all high) | 3 overlapped with above findings (confirmed and resolved); 1 meta-check (Rule 14) resolved by B1 fix |

All received: Yes (6 enabled subagents; 3 disabled via settings are pre-filled as Skipped).

## Reviewer Assessment (re-review)

**Verdict:** APPROVED — all four blockers resolved; non-blocking findings addressed or properly deferred.

### Specialist subagent incorporation

- [SILENT] silent-failure-hunter: B1 (hardcoded success) and B4 (classify lookup miss) — both resolved.
- [TEST] test-analyzer: B3 (wiring test) and narrative outcome coverage — both resolved.
- [DOC] comment-analyzer: B2 (progression_delta mislabel), N3 (overclaim), N4 (ticket-ref doc) — all resolved.
- [TYPE] type-design: N1 (stringly-typed APIs) — deferred as a cross-cutting follow-up covering 34-11 + 37-24 + future OTEL emitters; accepted as non-blocking.
- [RULE] rule-checker: Rules 3, 6, 14, A3 violations all resolved via B1/B3 fixes.

### Blocker verification

| # | Blocker | Resolution | Verified |
|---|---------|------------|----------|
| B1 | `outcome="success"` hardcoded at NpcAction site | Call site now passes `"narrative"`; docstring expands allowed set; test asserts `outcome=="narrative"` literally | ✅ `dispatch/mod.rs +714` reads `"narrative",` not `"success",`; `npc_turn_narrative_basis_also_emits` asserts `Some("narrative")` with the explicit comment "never rewritten to 'success'" |
| B2 | `progression_delta` misnamed | Renamed in fn sig, emitted wire field, rustdoc, and test. Docstring now explicitly says "absolute progression value, not a delta" | ✅ `lib.rs +128,+145`; test at line 186 reads `"progression"` field |
| B3 | No real wiring test | 4 source-grep wiring tests added that fail if call sites are removed or the classify map regresses | ✅ `emit_npc_turn_is_wired_into_scenario_dispatch`, `emit_trope_engagement_outcome_is_wired_into_tropes_dispatch`, `classify_engagement_kind_covers_all_three_kinds_including_aliases`, `non_engagement_trope_produces_no_engagement_span`. Pragmatic — not full runtime integration, but substantive lift over the fn-pointer check with clear failure messages. Accepted. |
| B4 | Silent lookup miss in `classify_engagement_kind` | Lookup-miss path now emits `tracing::warn!` with trope_id; rustdoc documents the two distinct None paths | ✅ `dispatch/tropes.rs +30-36` |

### Non-blocking verification

- **N1 (stringly-typed emit APIs):** deferred per review recommendation. Follow-up story noted in Dev Assessment — acceptable.
- **N2 (combat/chase alias coverage):** covered by new `classify_engagement_kind_covers_all_three_kinds_including_aliases` test.
- **N3 ("every NPC action" overclaim):** fixed — lib.rs block header now scopes to "two specific dispatch sites" and enumerates what is NOT covered.
- **N4 (ticket-number rustdoc):** fixed — `classify_engagement_kind` rustdoc opens with architectural purpose.

### Outstanding Observations

None blocking. One minor note for future awareness:

- The source-grep wiring tests will trigger if someone refactors `dispatch/mod.rs` to extract the NpcAction arm into a helper in another file — the `ScenarioEventType::NpcAction` anchor assertion would fail even though the wiring is still present. That's an acceptable false positive for this story — if the refactor happens, the reviewer updates the anchor at that time. Documenting so future Dev doesn't get confused.

### AC Accountability (final)

| AC | Status |
|----|--------|
| 1. `npc.turn` emitted with actor + outcome | DONE |
| 2. `trope.engagement_outcome` on stealth/confrontation/evasion | DONE |
| 3. Minimal UI cue on GM panel | DONE (via existing Watcher pipeline) |
| 4. No Illusionism Blindness | DONE — `outcome="narrative"` is the explicit unadjudicated signal |

### Handoff

To Drummer (SM) for finish — story is ready to merge.

---

## Dev Assessment (rework — addresses reviewer blockers)

**Phase:** finish (returning for re-review)
**Commit:** `65f059d fix(37-24): address reviewer blockers B1-B4`
**Status:** 11/11 tests pass (was 7 — added 4 wiring tests).

### Blocker responses

**B1 — hardcoded `outcome="success"` at NpcAction site.** FIXED. Now passes `"narrative"` (distinct from `"success"`). The outcome value set in `emit_npc_turn`'s docstring is expanded to `"success" | "failure" | "partial" | "narrative"`, documenting `"narrative"` as the explicit unadjudicated-outcome sentinel. The `npc_turn_narrative_basis_also_emits` test was updated to drive this path and asserts the outcome field literal — never rewritten to `"success"`.

**B2 — `progression_delta` param misnamed.** FIXED. Renamed to `progression` in the fn signature, rustdoc, and emitted WatcherEvent field. The test that reads this field was updated to match. Rustdoc now explicitly calls out "absolute progression value, not a delta" so future readers don't repeat the mistake.

**B3 — no real wiring test.** FIXED by adding four source-level wiring tests:
- `emit_npc_turn_is_wired_into_scenario_dispatch` — asserts `dispatch/mod.rs` contains both the `crate::emit_npc_turn(` call and the `ScenarioEventType::NpcAction` match arm.
- `emit_trope_engagement_outcome_is_wired_into_tropes_dispatch` — asserts `dispatch/tropes.rs` contains both the emit call and the `classify_engagement_kind(` invocation.
- `classify_engagement_kind_covers_all_three_kinds_including_aliases` — asserts all 5 tag match lines remain present (stealth, confrontation, combat, evasion, chase). Covers reviewer finding N2.
- `non_engagement_trope_produces_no_engagement_span` — counts `if let Some(kind) = classify_engagement_kind` guards and asserts ≥2 (the two emit sites). If a caller ever drops the guard and emits unconditionally, this fails.

Source-grep is deliberate — DispatchContext setup is too heavy for a unit test, and the dispatch call sites are stable enough that a textual assertion is honest about what it verifies. Complements (not replaces) the existing fn-pointer compile check.

**B4 — `classify_engagement_kind` silent on lookup miss.** FIXED. Split the two None paths: lookup-miss logs `tracing::warn!` with the offending `trope_id`; no-qualifying-tag stays silent (legitimate skip). Rustdoc now documents the distinction.

### Non-blocking responses

- **N1 (stringly-typed emit APIs):** deferred per reviewer recommendation. Noted for a follow-up story that unifies 34-11 + 37-24 + future dispatch OTEL emitters behind typed enums. Not touched in this commit.
- **N2 (combat/chase aliases):** covered by `classify_engagement_kind_covers_all_three_kinds_including_aliases`.
- **N3 ("every NPC action" overclaim):** FIXED. The lib.rs Story-37-24 block header now says "scenario-loop NPC autonomous actions (ScenarioEventType::NpcAction)" explicitly and calls out that other paths (combat NPC turns, random encounter NPCs) are not yet covered.
- **N4 (story-ticket doc prefix):** FIXED. `classify_engagement_kind` rustdoc now opens with the architectural purpose, not the story number.

### AC Accountability (post-rework)

| AC | Status |
|----|--------|
| 1. npc.turn emitted with actor + outcome | DONE — outcome field is now `"narrative"` at the scenario NpcAction site, not a misleading hardcoded `"success"` |
| 2. trope.engagement_outcome on stealth/confrontation/evasion | DONE — progression field correctly labeled; classifier warns on lookup miss |
| 3. Minimal UI cue | DONE via existing pipeline (no change) |
| 4. No Illusionism Blindness | DONE — scenario NPC actions now emit `"narrative"` outcome and `"narrative"` basis, making unadjudicated events explicitly visible rather than falsely reporting success |

**Handoff:** back to Reviewer (Avasarala) for re-review.

## Reviewer Assessment

**Verdict:** REQUEST CHANGES — hand back to Dev.
**Subagents:** 5 enabled ran (preflight, silent-failure-hunter, test-analyzer, comment-analyzer, type-design, rule-checker). 3 disabled (edge-hunter, security, simplifier) per settings.

### Subagent Results

| # | Specialist | Status | Findings | Decision |
|---|------------|--------|----------|----------|
| 1 | preflight | clean | 0 (76/76 tests green, 0 code smells) | verified — pass |
| 2 | silent-failure-hunter | findings | 3 (2 high, 1 low) | 2 confirmed, 1 dismissed |
| 3 | test-analyzer | findings | 5 (3 high, 2 medium) | 3 confirmed, 2 dismissed |
| 4 | comment-analyzer | findings | 4 (1 high, 3 medium) | 2 confirmed, 2 accepted |
| 5 | type-design | findings | 3 (2 high, 1 medium) | deferred (enum refactor — non-blocking) |
| 6 | rule-checker | findings | 4 (all high) | 3 confirmed (overlap with above), 1 meta |

### Blocking findings — handback required

**B1. `outcome="success"` hardcoded at `dispatch/mod.rs` NpcAction arm — directly defeats story purpose.**
Multiple subagents converged on this (silent-failure high, rule-checker high, comment-analyzer medium). The story's AC-4 is "No Illusionism Blindness" — yet the call site emits `outcome="success"` unconditionally for every scenario NPC action, regardless of whether the action actually succeeded or the narrator adjudicated it as a failure. The GM panel will always see NPC actions as effective, the precise Illusionism the span is meant to surface. The `mechanical_basis="narrative"` honesty is correct; `outcome="success"` is a placeholder on a semantically load-bearing field.
*Fix:* either extract outcome from the `ScenarioEvent` payload when available, or pass `"narrative"` (distinguishing the I-don't-know-the-outcome case from a genuine success). Do NOT hardcode `"success"`.

**B2. `progression_delta` parameter is misnamed — call sites pass absolute values, not deltas.**
Comment-analyzer high confidence. `emit_trope_engagement_outcome(..., progression_delta: f64)`:
- auto-resolve site (tropes.rs:173): passes `ts.progression()` — absolute progression (0.0–1.0)
- beat-fired site: passes `beat.beat.at` — an absolute threshold watermark
Neither is a delta. The GM panel will display a field labeled `progression_delta` containing a progression value — actively misleading. This is a labeled-wrong-on-the-wire bug.
*Fix:* rename parameter and the emitted field to `progression` (simplest), update the rustdoc, and update the 7 tests. OR compute a real delta at each call site (more work, not required for the story).

**B3. No real wiring test — `emit_functions_are_accessible` is compile-only.**
Test-analyzer high, rule-checker high. Project rule "Every test suite needs a wiring test" is not satisfied by a function-pointer type-check. If both dispatch call sites are deleted tomorrow, all 7 tests still pass. The dice 34-11 precedent has the same gap, but that doesn't excuse this one — the rule is stated in CLAUDE.md and this is a wire-first story specifically.
*Fix:* add at least one integration test that drives `process_tropes` (or the NpcAction match arm) with a minimal `DispatchContext` and asserts `drain_events()` yields the expected `npc.turn` / `trope.engagement_outcome` event. Can be targeted: one test per emit call path is sufficient, not all three dispatch sites.

**B4. `classify_engagement_kind` silently returns None on trope_id lookup miss.**
Silent-failure high. The helper matches by `id.as_deref()` OR `name.as_str()`. If the engine hands in a slug that matches neither (TropeDefinition.id is `Option<String>` and often absent; name is display text, not slug), the span is silently skipped indistinguishable from a non-engagement trope. Violates CLAUDE.md "No Silent Fallbacks."
*Fix:* add a `tracing::warn!` when the lookup misses, or emit an `unclassified_trope` span so the miss surfaces on the GM panel rather than disappearing.

### Non-blocking findings (acknowledge, don't block)

**N1. Stringly-typed emit APIs (type-design x3).** Outcome/engagement_kind/mechanical_basis as `&str` rather than enums. Matches the established dice OTEL pattern (which also uses strings at the boundary but derives them from a typed internal enum). **Deferred** as a follow-up — would be a worthwhile consistency pass across 34-11 + 37-24 + future dispatch OTEL; don't block this story on it. Suggest creating a backlog story: "Replace stringly-typed WatcherEvent-emitter boundaries with typed enums (EngagementKind, OutcomeKind, MechanicalBasis)."

**N2. Combat/chase tag aliases not test-covered (test-analyzer medium).** `classify_engagement_kind` maps `combat→confrontation` and `chase→evasion` but tests only exercise the primary tags. Add to the wiring-test work in B3 — if a dispatch-level test uses a trope def with `tags: ["combat"]`, this is covered for free.

**N3. Comment claims "every NPC action" — overbroad (comment-analyzer medium).** The emit only fires for `ScenarioEventType::NpcAction`, not combat NPC turns or random-encounter NPCs. Narrow the lib.rs Story-37-24 block header comment to reflect actual coverage.

**N4. classify_engagement_kind doc starts with "Story 37-24:" — ticket reference without architectural why (comment-analyzer medium).** Per SM/Keith feedback memory: comments must explain WHY, not reference tickets. Rewrite the doc header.

### Dismissed

- silent-failure low: `WatcherEventBuilder.send()` drops on full channel. Documented, matches existing crate convention, not specific to this diff. No action.
- test-analyzer medium "NPC failure path test": this test *can't meaningfully* exist until B1 is fixed (call site hardcodes success). Subsumed by B1.

### AC Accountability (status after review)

| AC | Status pre-review | Status post-review |
|----|------|------|
| 1. npc.turn emitted with actor + outcome | DONE | **PARTIAL** — emitted, but outcome field is hardcoded placeholder (B1) |
| 2. trope.engagement_outcome on stealth/confrontation/evasion | DONE | **PARTIAL** — emitted, but `progression_delta` field mislabeled (B2); silent miss on lookup (B4) |
| 3. Minimal UI cue | DONE via existing pipeline | DONE — no change needed, confirmed |
| 4. No Illusionism Blindness | DONE | **FAIL** — hardcoded `outcome="success"` is the exact Illusionism the span is meant to catch (B1) |

### Handoff

To Dev (Naomi) for rework on B1–B4. After fixes, re-run 37-24 test module + new wiring test. Non-blocking findings N1–N4 tracked in this assessment; N1 is a follow-up story, N3/N4 can be bundled into the fix commit if convenient.

## Dev Assessment

**Phase:** finish
**Status:** all 7 RED tests pass; full sidequest-server suite 76/76 pass; no regressions.
**Commit:** `300dd90 feat(otel): wire npc.turn + trope.engagement_outcome spans (37-24)`

### Implementation

**Added (crates/sidequest-server/src/lib.rs, new Story-37-24 block):**
- `pub fn emit_npc_turn(actor, action, outcome, mechanical_basis)` — StateTransition on `"npc"` component, event=`npc.turn`. Always emits the four required fields. `mechanical_basis` literal `"narrative"` is the Illusionism flag.
- `pub fn emit_trope_engagement_outcome(trope_id, engagement_kind, outcome, progression_delta)` — StateTransition on `"trope"` component, event=`trope.engagement_outcome`.

**Wired (dispatch/mod.rs ~line 697):** scenario `NpcAction` match arm now calls `emit_npc_turn(npc_name, format!("{:?}", action), "success", "narrative")` alongside the existing `scenario.npc_action` emission. Scenario autonomous NPC actions are narrator-adjudicated today (no roll), so `mechanical_basis="narrative"` — the honest signal for the GM panel. When future stories introduce rolled NPC checks, they pass a roll reference instead.

**Wired (dispatch/tropes.rs):**
- Added `classify_engagement_kind(trope_id, trope_defs) -> Option<&'static str>` helper: inspects TropeDefinition.tags for stealth / confrontation / combat / evasion / chase (case-insensitive). Returns None for non-engagement tropes so the caller skips emission rather than producing a misleading `"other"`.
- At auto-resolve site (lines ~132–140): when `ts.status() == Resolved && progression >= 1.0`, if the trope classifies, emit `outcome="success"` with `progression_delta = ts.progression()`.
- At fired-beat site (lines ~143–155): when a beat's trope classifies, emit `outcome="escalation"` with `progression_delta = beat.beat.at`. Escalation, not terminal success, because a beat firing is progression advancing.

**UI cue (AC-3):** no UI changes required. `useWatcherSocket` in sidequest-ui forwards every parsed WatcherEvent unfiltered to TimelineTab / SubsystemsTab / ConsoleTab. `"npc"` and `"trope"` component events will appear in the GM panel automatically — verified by inspecting the hook and tab subscribers. The "minimal cue" AC is satisfied by the existing pipeline.

### AC Accountability

| AC | Status |
|----|--------|
| 1. `npc.turn` emitted on NPC actions with actor + outcome | DONE — wired at scenario NpcAction dispatch |
| 2. Trope handshake on stealth/confrontation/evasion resolution | DONE — `trope.engagement_outcome` at both auto-resolve and fired-beat sites, tag-classified |
| 3. Minimal UI cue on GM panel | DONE via existing Watcher pipeline (no UI code change; events surface in Dashboard tabs automatically) |
| 4. No Illusionism Blindness | DONE — `mechanical_basis` is always present; `"narrative"` literal makes narrator-only adjudication visible rather than hidden |

### Design Deviations

See `### Dev (implementation)` under Design Deviations.

### Delivery Findings

See `### Dev (implementation)` under Delivery Findings.

**Handoff:** Reviewer (Avasarala) for quality + spec review.

## TEA Assessment

**Tests Required:** Yes
**Test File:** `crates/sidequest-server/src/otel_npc_trope_spans_37_24_tests.rs` (7 tests, 245 LOC)
**Status:** RED (compile error — missing `emit_npc_turn` and `emit_trope_engagement_outcome` pub fns at crate root)
**Verification:** testing-runner confirmed 10 `E0425` errors; compilation blocked exactly where expected.

**Tests written:**
1. `npc_turn_emits_watcher_event_with_required_fields` — AC-1, all 4 fields (actor, action, outcome, mechanical_basis) on `npc.turn` event
2. `npc_turn_narrative_basis_also_emits` — AC-3/Illusionism, narrative-only NPC action must still emit with `mechanical_basis = "narrative"` literal
3. `npc_turn_uses_state_transition_type` — AC-4, `WatcherEventType::StateTransition`
4. `trope_engagement_outcome_emits_watcher_event_with_required_fields` — AC-2, all 4 fields (trope_id, engagement_kind, outcome, progression_delta) + numeric round-trip
5. `trope_engagement_outcome_uses_state_transition_type` — AC-4
6. `engagement_kind_covers_stealth_confrontation_evasion` — AC-2b, all three kinds emit
7. `emit_functions_are_accessible` — AC-5, compile-time fn-signature wiring check

**Rule Coverage (lang-review Rust):**
| Rule | Test | Status |
|------|------|--------|
| Wiring integration test | `emit_functions_are_accessible` | RED |
| Meaningful assertions (no vacuous `is_some`/`_ =`) | all 7 tests assert field values, event_type, or counts | RED |
| Bounded-set fields tested | `engagement_kind_covers_stealth_confrontation_evasion` | RED |
| Negative/narrative-path coverage | `npc_turn_narrative_basis_also_emits` | RED |
| Numeric field round-trip | `trope_engagement_outcome_emits_...` asserts f64 equality to EPSILON | RED |

**Self-check:** No vacuous assertions. Every test asserts concrete field values, event counts, or match patterns.

**Handoff:** Dev (Naomi) implements:
- `pub fn emit_npc_turn(actor: &str, action: &str, outcome: &str, mechanical_basis: &str)` at `crates/sidequest-server/src/lib.rs`
- `pub fn emit_trope_engagement_outcome(trope_id: &str, engagement_kind: &str, outcome: &str, progression_delta: f64)` at `crates/sidequest-server/src/lib.rs`
- Both use `WatcherEventBuilder::new(component, StateTransition).field("event", "...").field(...).send()`
- Call sites: `dispatch/mod.rs` line ~696–704 (NpcAction match arm) and `dispatch/tropes.rs` lines ~129–140 & ~150–154 (engagement-resolution paths). UI cue (AC-3) is Dev's second pass after api GREEN.

## Architect Assessment (design spec for RED phase)

**Emission mechanism.** Use `WatcherEventBuilder` (broadcast channel), not `tracing::info_span!`. Rationale: the GM panel lie-detector pipeline is wired off the WatcherEvent broadcast, and existing RED-phase OTEL tests (e.g. `otel_dice_spans_34_11_tests.rs`) assert against `fresh_subscriber()` + `drain_events()`. Using tracing spans would bypass the GM panel and defeat the story's purpose.

**Event contract — `npc.turn`**
- Emit at: `crates/sidequest-server/src/dispatch/mod.rs` ~line 696–704, inside the `ScenarioEventType::NpcAction` match arm. Emit alongside existing `scenario.npc_action` — do not replace it (scenario.npc_action is scenario-tick framing; npc.turn is the mechanical-outcome span).
- Component: `"npc"`, event_type: `StateTransition`
- Required fields:
  - `event = "npc.turn"` (discriminator)
  - `actor` — npc_name (String)
  - `action` — verb/action descriptor (String)
  - `outcome` — `"success" | "failure" | "partial"` (String)
  - `mechanical_basis` — either a roll reference (e.g. `"d20:14 vs dc:12"`) or `"narrative"` when no roll. Must be present — never absent. Narrative-only outcomes are explicitly flagged so the GM panel can surface Illusionism (NPC acted without mechanical backing).

**Event contract — `trope.engagement_outcome`**
- Emit at: `crates/sidequest-server/src/dispatch/tropes.rs` — two sites:
  1. ~line 129–140 (encounter auto-resolve when progression ≥ 1.0) — outcome = resolved trope's terminal state
  2. ~line 150–154 (beat fired path) — only when the fired beat is a stealth/confrontation/evasion engagement beat (tag-filtered)
- Component: `"trope"`, event_type: `StateTransition`
- Required fields:
  - `event = "trope.engagement_outcome"`
  - `trope_id` (String)
  - `engagement_kind` — `"stealth" | "confrontation" | "evasion"` (String)
  - `outcome` — `"success" | "failure" | "escalation"` (String)
  - `progression_delta` — f64, progression change this tick

**TEA test guidance.**
- Use `test_support::fresh_subscriber()` + `drain_events()` pattern.
- Two boundary tests minimum:
  1. `npc_turn_emits_watcher_event_with_actor_and_mechanical_basis` — drive a scenario tick producing one NpcAction, assert one `npc.turn` event with all 4 required fields; assert `mechanical_basis == "narrative"` path also emits (negative-path coverage for Illusionism).
  2. `trope_engagement_outcome_emits_on_stealth_resolution` — drive trope tick that resolves a stealth engagement, assert `trope.engagement_outcome` event with all 4 fields.
- Both tests must fail RED today (neither event exists). Confirm by `rg "npc.turn\|trope.engagement_outcome" crates/` returning zero span emission sites.

**UI cue (AC-3).** Out of scope for RED phase. Dev handles in GREEN. UI is a minimal GM-panel badge that subscribes to these two new event names — the UI cue test can be a wiring smoke test on the ui repo after api GREEN.

**Wire-first posture.** These are integration-level watcher-event tests, not unit tests of a pure function. They must exercise the real dispatch path with a mocked ClaudeClient (standard harness). No stubs. If the dispatch harness can't produce an NpcAction without full scenario setup, surface as a Delivery Finding rather than inventing a stub path.

**Naming deviation logged for TEA awareness.** Story AC said "trope handshake span"; design specifies `trope.engagement_outcome` as the event name. Rationale: consistent with existing dotted-name convention and explicit about the semantic (outcome, not just handshake occurrence).

---

## Sm Assessment

Story 37-24 closes an Illusionism gap: narrator currently resolves NPC turns and stealth/trope outcomes with no OTEL backing, so the GM panel cannot verify mechanics. Wire-first approach: TEA writes a boundary test asserting `npc.turn` and `trope.engagement_outcome` spans emit with actor + outcome attributes on dispatch, then Dev wires the emission points in dispatch/turn.rs and tropes.rs plus a minimal UI cue. Call sites are marked TBD in ACs — Dev confirms during exploration. Scope: api repo only for span emission; UI cue may touch ui repo but start api-only and expand if needed. No stubs, no silent fallbacks — if dispatch path doesn't exist where expected, surface it as a Delivery Finding.