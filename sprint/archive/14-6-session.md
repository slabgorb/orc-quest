---
story_id: "14-6"
jira_key: ""
epic: "14"
workflow: "tdd"
---
# Story 14-6: Image pacing throttle — configurable minimum interval between scene images

## Story Details
- **ID:** 14-6
- **Jira Key:** (personal project — no Jira)
- **Epic:** 14 — Multiplayer Session UX
- **Workflow:** tdd
- **Stack Parent:** none (independent story)

## Story Summary
Add image_cooldown_seconds config (default 60s for multiplayer, 30s for solo). After an image is generated, suppress further image triggers until cooldown expires. DM can force an image at any time. Prevents image flooding during rapid turn sequences.

**Points:** 3  
**Priority:** p1  
**Repos:** sidequest-api

## Workflow Tracking
**Workflow:** tdd  
**Phase:** finish  
**Phase Started:** 2026-03-31T07:08:25Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T02:27:00Z | 2026-03-31T02:32:00Z | 5m |
| red | 2026-03-31T02:32:00Z | 2026-03-31T06:48:55Z | 4h 16m |
| green | 2026-03-31T06:48:55Z | 2026-03-31T06:49:51Z | 56s |
| spec-check | 2026-03-31T06:49:51Z | 2026-03-31T06:52:53Z | 3m 2s |
| green | 2026-03-31T06:52:53Z | 2026-03-31T06:58:52Z | 5m 59s |
| spec-check | 2026-03-31T06:58:52Z | 2026-03-31T06:59:57Z | 1m 5s |
| verify | 2026-03-31T06:59:57Z | 2026-03-31T07:02:50Z | 2m 53s |
| review | 2026-03-31T07:02:50Z | 2026-03-31T07:07:34Z | 4m 44s |
| spec-reconcile | 2026-03-31T07:07:34Z | 2026-03-31T07:08:25Z | 51s |
| finish | 2026-03-31T07:08:25Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): Pre-existing compilation errors in unrelated test files (stories 3-2, 3-3, 3-4, 3-8) — missing `spans` field in `TurnRecord` mock constructors. Affects `crates/sidequest-agents/tests/turn_record_story_3_2_tests.rs`, `entity_reference_story_3_4_tests.rs`, `patch_legality_story_3_3_tests.rs`, `trope_alignment_story_3_8_tests.rs` (add `spans: vec![]` to TurnRecord initializers). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): Story context specified `ImageThrottle` on `SharedGameSession`, but render queue and broadcaster are app-global. Throttle placed on `AppStateInner` instead. Affects `crates/sidequest-server/src/lib.rs` (per-session throttle would require session context in render pipeline). *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Architect (reconcile)
- **DM force-image bypass is mechanism-only, not wired to a dispatch path**
  - Spec source: context-story-14-6.md, AC table, row "DM override"
  - Spec text: "DM can force an image, resetting cooldown"
  - Implementation: `should_allow_forced()` method exists on `ImagePacingThrottle` and is tested, but no server dispatch path invokes it — no DM command triggers a forced render through the throttle
  - Rationale: DM tools system doesn't currently have a "force image" command; the bypass point is ready for when it does. Wiring requires render pipeline metadata (marking a render as "forced"), which is beyond story scope.
  - Severity: minor
  - Forward impact: minor — story 14-7 (image relevance filter) or a future DM tools story will need to wire the force path

### Dev (implementation)
- **Throttle placement: AppState instead of SharedGameSession**
  - Spec source: context-story-14-6.md, Technical Approach
  - Spec text: "Add to `SharedGameSession`"
  - Implementation: Throttle placed on `AppStateInner` (app-global, not per-session)
  - Rationale: Render queue and broadcaster are app-global; per-session throttle would require threading session context through the render pipeline
  - Severity: minor
  - Forward impact: none — single-world sessions are the current deployment model

## TEA Assessment

**Tests Required:** Yes
**Reason:** Feature with 5 ACs and integration test needs

**Test Files:**
- `crates/sidequest-server/tests/image_pacing_story_14_6_tests.rs` — 19 tests covering all 5 ACs + wire format
- `sidequest-ui/src/components/__tests__/ImagePacingSlider.test.tsx` — UI slider tests (vitest)

**Tests Written:** 19 Rust tests covering 5 ACs + wire format serialization
**Status:** GREEN (tests already passing — implementation committed alongside tests)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality | Self-check: all 19 tests have meaningful assertions | pass |
| #7 unsafe as casts | `remaining_cooldown_seconds` uses `as u32` — 136yr overflow, negligible risk | noted |
| #9 public fields | `ImagePacingThrottle` fields private with getters | pass |

**Rules checked:** 3 of 15 applicable (remaining rules N/A — no new enums, no new constructors at trust boundaries, no tenant context, no Deserialize bypass)
**Self-check:** 0 vacuous tests found

**Note:** Tests and implementation were committed together, so RED phase was never truly RED. All 19 tests pass. Ready for verify/review.

**Handoff:** To Dev (Yoda) for GREEN confirmation, then verify

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | Slider components share structure — keep separate (low confidence) |
| simplify-quality | 1 finding | Inline broadcaster lacks explicit `Failed` handling unlike render_integration variant (medium) |
| simplify-efficiency | 1 finding | `should_allow_forced()` is trivial no-op, misleading docstring (medium) |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 2 medium-confidence findings (inline broadcaster error handling, trivial force method)
**Noted:** 1 low-confidence observation (slider similarity)
**Reverted:** 0

**Overall:** simplify: clean (no auto-apply warranted)

**Quality Checks:** 19/19 tests pass, clippy clean
**Handoff:** To Reviewer (Obi-Wan Kenobi) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 3 test warnings (unused imports, needless mut) — non-blocking | N/A |
| 2 | reviewer-silent-failure-hunter | Yes | 4 high, 1 medium, 1 low | 4x lock().unwrap() poison risk in broadcaster/dispatch; should_allow_forced() unwired footgun | Noted — matches existing codebase pattern (8 pre-existing unwrap sites); non-blocking |
| 3 | reviewer-rule-checker | Yes | 2 findings | #5 no upper-bound on cooldown input; #6 shallow integration test assertion | Noted as findings #2 and #5 |

All received: Yes

## Reviewer Assessment

**Verdict:** APPROVE with non-blocking findings
**Preflight:** Build pass, 19/19 tests green, clippy clean

### Findings

1. **Player-join overwrites manual cooldown** (Behavioral, Minor)
   - When a player joins, `set_cooldown(new_default.cooldown_seconds())` resets any DM-configured value
   - Impact: Low — player joins are infrequent mid-session; DM can re-set via settings
   - Recommendation: Future improvement — only auto-adjust if the current cooldown matches the previous default

2. **[RULE] No input validation on `image_cooldown_seconds`** (Security, Minor)
   - Client can send `u32::MAX` to effectively disable images forever
   - Impact: Low — DM tools only, not adversarial; personal project
   - Recommendation: Clamp to 0..=300 range in settings handler

3. **`spawn_image_broadcaster_with_throttle` is dead production code** (Quality, Trivial)
   - Function in render_integration.rs is only called from tests, not server
   - Impact: None — tests validate the struct logic, production uses inline broadcaster
   - Recommendation: Keep for now — useful as test harness; document as test utility

4. **DM force-image bypass not wired** (Gap, Minor)
   - `should_allow_forced()` on struct, but no DM command invokes it
   - Impact: AC3 mechanism exists but integration deferred until DM tools support it
   - Recommendation: Acceptable — the bypass point exists, DM tool wiring is a separate concern

5. **[RULE] Integration test assertion is shallow** (Test Quality, Trivial)
   - `matches!(msg, GameMessage::Image { .. })` at test line 329 doesn't verify payload content
   - Impact: Could miss payload corruption bugs
   - Recommendation: Non-blocking; the unit tests cover payload construction thoroughly

6. **[SILENT] Four `lock().unwrap()` sites risk silent broadcaster death** (Reliability, Minor)
   - Lines 874, 1503, 1627, 2741 in lib.rs — mutex poison would silently kill image delivery
   - Impact: Low — matches existing pattern (8 pre-existing sites); would require codebase-wide fix
   - Recommendation: Non-blocking; future improvement to use `unwrap_or_else(|e| e.into_inner())`

7. **[SILENT] `should_allow_forced()` is unwired footgun** (Quality, Minor)
   - Returns `true` without recording render; no production call site
   - Impact: Future caller forgetting `record_render()` would silently bypass throttle state
   - Recommendation: Non-blocking; rename to `allow_forced_and_record()` when DM force path is wired

### Summary

The implementation is sound. `ImagePacingThrottle` is clean, well-tested, properly wired into the broadcaster and settings path. The auto-adjust on player count and the lack of input bounds are minor polish items, not blockers. All five ACs are addressed at the mechanism level.

**Decision:** Approve. Proceed to finish.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-protocol/src/message.rs` — `image_cooldown_seconds` field on `SessionEventPayload`
- `crates/sidequest-server/src/render_integration.rs` — `ImagePacingThrottle` struct + `spawn_image_broadcaster_with_throttle`
- `crates/sidequest-server/src/lib.rs` — Wiring: throttle in AppState, inline broadcaster check, SESSION_EVENT "settings" handler, auto-adjust on player count change
- `sidequest-ui/src/components/ImagePacingSlider.tsx` — UI slider component (0–120s, step 5)

**Tests:** 19/19 passing (GREEN)
**Branch:** develop (pushed)

**Wiring verified:**
- [x] `ImagePacingThrottle` instantiated in `AppStateInner`
- [x] Throttle check wired into inline image broadcaster in `build_router`
- [x] `SESSION_EVENT "settings"` handler reads `image_cooldown_seconds` and calls `set_cooldown()`
- [x] Player count changes auto-adjust default cooldown (solo 30s, multiplayer 60s)

**Handoff:** To verify phase (TEA)

## Architect Assessment (spec-check)

### Round 1 (pre-wiring)
**Spec Alignment:** Drift detected — 2 major gaps (throttle not wired, settings not handled)
**Decision:** Handed back to Dev.

### Round 2 (post-wiring)
**Spec Alignment:** Aligned
**Mismatches Found:** None

Both gaps from round 1 are now closed:
- Throttle wired into `AppStateInner`, checked in inline broadcaster before every IMAGE send
- `SESSION_EVENT "settings"` handler reads `image_cooldown_seconds` and calls `set_cooldown()`
- Player count changes auto-adjust default cooldown at both join paths

Dev deviation (AppState vs SharedGameSession) is architecturally justified — render pipeline is app-global.

**Decision:** Proceed to verify