---
story_id: "18-1"
epic: "18"
workflow: "tdd"
---
# Story 18-1: Add sub-spans to preprocess, agent_llm, and system_tick for flame chart granularity

## Story Details
- **ID:** 18-1
- **Epic:** 18 — OTEL Dashboard — Granular Instrumentation & State Tab
- **Workflow:** tdd
- **Points:** 3
- **Type:** refactor
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** review
**Phase Started:** 2026-03-31T23:38:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-31T20:10:00Z | 2026-03-31T23:07:44Z | 2h 57m |
| red | 2026-03-31T23:07:44Z | - | - |

## Sm Assessment

**Story readiness:** Ready. Full context at sprint/context/context-story-18-1.md with technical approach, target sub-spans, and ACs. Architect already analyzed dispatch/mod.rs and identified all instrumentation points.

**Jira:** Skipped — personal project.

**Risks:** Low. Adding tracing spans is additive — no behavioral changes. Main risk is getting span nesting wrong (child vs sibling).

**Routing:** TDD workflow → TEA for RED phase, then Dev for GREEN.

## Delivery Findings

No upstream findings.

## Design Deviations

### Dev (implementation)
- **prompt_build span wraps compose() only, not full builder assembly**
  - Spec source: context-story-18-1.md, Technical Approach
  - Spec text: "turn.agent_llm.prompt_build — ContextBuilder zone assembly"
  - Implementation: Span wraps the section count calculation + compose() call, not the individual add_section() calls. All section additions happen before the span opens.
  - Rationale: The test layer captures fields at span creation time, so section_count must be known when the span is created. Moving the span to after section addition ensures the field has the actual count.
  - Severity: minor
  - Forward impact: none — the span still captures the prompt build phase; individual section additions are trivially fast compared to compose()

## Dev Assessment

### Implementation Summary
Added 9 sub-spans across 3 files and 1 helper method:

**preprocessor.rs (agents crate):**
- `turn.preprocess.llm` — wraps `client.send_with_model()` with `model` field
- `turn.preprocess.parse` — wraps `parse_response()` + validation with `response_len` field

**orchestrator.rs (agents crate):**
- `turn.agent_llm.prompt_build` — wraps ContextBuilder compose with `section_count` field
- `turn.agent_llm.inference` — wraps `client.send()` with `model` and `prompt_len` fields
- `turn.agent_llm.extraction` — wraps extraction with `narration_len` field

**dispatch/mod.rs (server crate):**
- `turn.system_tick.combat` — wraps `process_combat_and_chase()` with `in_combat` field
- `turn.system_tick.tropes` — wraps `process_tropes()` with `active_count` field
- `turn.system_tick.beat_context` — wraps beat context formatting with `beats_count` field
- `turn.preprocess.wish_check` — wraps WishConsequenceEngine with `is_power_grab` field
- `turn.barrier` — wraps `handle_barrier()` with `barrier_mode` field

**context_builder.rs:** Added `section_count()` accessor method.

### Async span handling
Used `Instrument::instrument()` for async calls (barrier, combat) to avoid `Send` issues with `EnteredSpan` guards across `.await` points. Sync spans use `.entered()` guards.

### Test Results
- agents crate: 9/9 story tests pass, 127/127 lib tests pass
- server crate: 15/15 story tests pass
- 14 pre-existing e2e test failures (unrelated — same before and after changes)

## TEA Assessment

### Test Strategy
Two test files covering all 5 ACs:

**`sidequest-agents/tests/telemetry_story_18_1_tests.rs`** (9 tests)
- 3 behavioral tests: call `preprocess_action()` under SpanCaptureLayer, assert sub-span names exist
- 3 behavioral tests: call `Orchestrator::process_action()` under SpanCaptureLayer, assert sub-span names exist
- 3 diagnostic field tests: verify each sub-span records at least one meaningful field

**`sidequest-server/tests/telemetry_story_18_1_tests.rs`** (15 tests)
- 6 structural tests: assert span name strings exist in source files (dispatch/mod.rs, preprocessor.rs, orchestrator.rs)
- 2 diagnostic field tests: verify combat/tropes sub-spans record fields
- 3 system_tick sub-span tests: combat, tropes, beat_context
- 1 wish_check sub-span test
- 1 barrier span test (AC3)
- 1 prompt_build async-aware span test (AC2)
- 1 integration wiring test: all 9 sub-spans defined across codebase

### RED State
- **agents crate:** 0 passed, 9 failed — sub-spans don't exist yet
- **server crate:** 1 passed, 14 failed — only prompt_build_has_async_aware_span passes (existing `turn.build_prompt_context` instrument matches)
- **Total:** 1 passed, 23 failed

### Rule Coverage
- Span naming convention follows existing `turn.{phase}.{sub}` pattern
- Tests verify both span existence AND diagnostic field presence (AC5)
- Wiring test ensures no sub-span is accidentally omitted
- Structural tests prevent span name typos

### Implementation Notes for Dev
- **preprocessor.rs** (agents crate): Add `turn.preprocess.llm` around `client.send_with_model()` and `turn.preprocess.parse` around `parse_response()` + validation. Model name field on LLM span.
- **orchestrator.rs** (agents crate): Add `turn.agent_llm.prompt_build` around ContextBuilder assembly (lines 190-342), `turn.agent_llm.inference` around `self.client.send()` (line 352), `turn.agent_llm.extraction` around `extract_structured_from_response()` + combat patch extraction.
- **dispatch/mod.rs** (server crate): Add `turn.system_tick.combat` around `combat::process_combat_and_chase()` (line 492), `turn.system_tick.tropes` around `tropes::process_tropes()` (line 494), `turn.system_tick.beat_context` around the fired_beats context block (lines 500-512). Add `turn.preprocess.wish_check` around the WishConsequenceEngine block (lines 247-261). Add `turn.barrier` span around `handle_barrier()` call (line 225).
- **sidequest-api branch:** `feat/18-1-otel-sub-spans` (created from feat/trope-system-wiring)