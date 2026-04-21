---
story_id: "42-3"
jira_key: null
epic: "42"
workflow: "tdd"
---

# Story 42-3: Port TensionTracker + PacingHint narrator wiring

## Story Details
- **ID:** 42-3
- **Title:** Port TensionTracker + PacingHint + DeliveryMode + CombatEvent classification + classify_round/classify_combat_outcome; wire PacingHint into narrator prompt zone (Rust-parity fixture suite)
- **Jira Key:** none (personal project)
- **Workflow:** tdd
- **Stack Parent:** 42-2 (completed — commit a4a5010 just merged to develop)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-21T07:21:00Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-04-21T00:00:00Z | 2026-04-21T06:11:44Z | 6h 11m |
| green | 2026-04-21T06:11:44Z | 2026-04-21T06:19:52Z | 8m 8s |
| spec-check | 2026-04-21T06:19:52Z | 2026-04-21T06:21:47Z | 1m 55s |
| verify | 2026-04-21T06:21:47Z | 2026-04-21T06:26:44Z | 4m 57s |
| review | 2026-04-21T06:26:44Z | 2026-04-21T06:52:50Z | 26m 6s |
| green | 2026-04-21T06:52:50Z | 2026-04-21T07:00:35Z | 7m 45s |
| spec-check | 2026-04-21T07:00:35Z | 2026-04-21T07:01:47Z | 1m 12s |
| verify | 2026-04-21T07:01:47Z | 2026-04-21T07:04:18Z | 2m 31s |
| review | 2026-04-21T07:04:18Z | 2026-04-21T07:21:00Z | 16m 42s |
| finish | 2026-04-21T07:21:00Z | - | - |

## Story Scope

**Port from Rust to Python:**
- `sidequest-api/crates/sidequest-game/src/tension_tracker.rs` (803 LOC)
- Types: `RoundResult`, `DamageEvent`, `PacingHint`, `DeliveryMode`, `CombatEvent`, `DetailedCombatEvent`, `TurnClassification`
- State machine: `TensionTracker` with all methods
- Free functions: `classify_round(...)`, `classify_combat_outcome(...)`

**Target files (new):**
- `sidequest/game/tension_tracker.py`
- `tests/fixtures/tension/` — JSON fixtures exported from Rust via `cargo run --example tension_fixture_export`

**Target files (modified):**
- `sidequest/agents/orchestrator.py` — add `TurnContext.pacing_hint: str | None`; register Early-zone `pacing_hint` section (match Rust placement)

**Dependencies:**
- `sidequest/genre/models/drama_thresholds.py` (existing) — confirm during red phase

**Out of scope:**
- Where `TensionTracker` instances are owned (session/encounter/connection) — 42-4
- Music director / mood integration — Python music director not ported yet
- Pacing hint persistence — snapshot integration is 42-4 scope

## Acceptance Criteria

**AC1: Classification parity**
- `classify_round(...)` and `classify_combat_outcome(...)` produce Rust-identical enum values on every input from committed fixture suite
- Edge case: `killed = None` (nobody died) distinct from `killed = ""` (empty string)

**AC2: `TensionTracker.tick(round_result)` produces Rust-parity `PacingHint`**
- Multi-round scenarios: escalating combat, stalling combat, reversal combat produce Rust-identical output byte-for-byte

**AC3: `PacingHint` narrator-zone parity**
- Python orchestrator registers `pacing_hint` in same attention zone (Early or Valley) as Rust
- When `TurnContext.pacing_hint is None`, no section registered

**AC4: `DramaThresholds` sourced from genre pack**
- Python `TensionTracker` reads threshold values from genre pack, not Python-side constants
- Test: pack with overridden thresholds produces expected `DeliveryMode` shift

**AC5: Every Rust test ports 1:1**
- Python test file matches Rust test count and naming

**AC6: Fixture regeneration is scriptable**
- `cargo run --example tension_fixture_export` documented and committed fixtures in `tests/fixtures/tension/`

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)

- **Improvement** (non-blocking): TEA's verify-phase ruff scan only covered production code (`sidequest/game/tension_tracker.py` and `sidequest/agents/orchestrator.py`); the test files in the same diff (`tests/game/test_tension_tracker.py`, `tests/agents/test_orchestrator_pacing_wiring.py`) had 5 ruff findings missed. Affects the TEA verify-phase quality-gate scope: future verify scans should cover all `.py` files in `git diff develop --name-only`, not just the production subset. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Pacing-section registration in `Orchestrator.build_narrator_prompt` does not emit an OTEL span. Architect's spec-check assessment correctly defers this to 42-4 (TensionTracker not yet wired into the production game loop, so a span at this site would be uninformative). The defer must be carried forward into the 42-4 context document so it cannot drift. Affects `sprint/context/context-story-42-4.md` (when it is authored) — must include "wire OTEL span at PacingHint registration site (deferred from 42-3)" in the AC list. *Found by Reviewer during code review.*

### Dev (implementation)

- No upstream findings during implementation — all RED-phase guidance was actionable as written. The two existing helpers TEA flagged (`register_pacing_section` already in Python, `DramaThresholds` already in `sidequest.genre.models.ocean`) made the wiring a single call-site change in `build_narrator_prompt`.

### TEA (test design)

- **Conflict** (non-blocking): AC2 in `context-story-42-3.md` names `TensionTracker.tick(round_result)`; Rust source has no such method. Rust API is `observe(round, killed, lowest_hp_ratio)` then `pacing_hint(thresholds)`. Affects `sprint/context/context-story-42-3.md` (AC2 phrasing — refresh next time the doc is touched). Tests encode the Rust call shape. *Found by TEA during test design.*
- **Conflict** (non-blocking): AC3 in `context-story-42-3.md` says the pacing section lands in Early or Valley; Rust source places it in `AttentionZone.Late` and the existing Python helper `register_pacing_section` already uses Late. Affects `sprint/context/context-story-42-3.md` (AC3 zone wording). Tests follow Rust. *Found by TEA during test design.*
- **Conflict** (non-blocking): AC3 / Technical Guardrails specify `TurnContext.pacing_hint: str | None`; a string field loses `escalation_beat` and forces pre-rendering. Tests assume `PacingHint | None` typed field, mirroring Rust which passes `&PacingHint` to its register helper. Affects `sprint/context/context-story-42-3.md`. *Found by TEA during test design.*
- **Improvement** (non-blocking): The `register_pacing_section` Python helper already exists at `sidequest/agents/prompt_framework/core.py:140` with the right signature (`narrator_directive: str, escalation_beat: str | None`) and zone (`Late`). Dev's wiring task is one call site in `Orchestrator.build_narrator_prompt`, not a new helper. Reduces 42-3 implementation surface materially. *Found by TEA during test design.*

## TEA Assessment

**Tests Required:** Yes
**Reason:** Story 42-3 is a 5-point Rust→Python port (`TensionTracker`, `PacingHint`, classifiers, narrator wiring). Fixture-driven parity is the load-bearing contract per Epic 42 / ADR-082 §test-porting discipline.

**Test Files:**
- `sidequest-server/tests/game/test_tension_tracker.py` — 29 ported Rust tests + 11 AC-driven additions (edge cases, fixture parity, scenario replays, threshold shift, 1:1 port assertion).
- `sidequest-server/tests/agents/test_orchestrator_pacing_wiring.py` — 8 tests covering `TurnContext.pacing_hint` field shape, `None`-skip behaviour, Late-zone parity, directive/escalation content, Delta-tier registration.
- `sidequest-server/tests/fixtures/tension/` — committed Rust-canonical JSON fixtures (`classify_round.json`, `classify_combat_outcome.json`, `scenario_escalating.json`, `scenario_stalling.json`, `scenario_reversal.json`) + README with regeneration command.

Companion infrastructure commit on `sidequest-api`:
- Branch: `feat/42-3-tension-fixture-export`
- File: `crates/sidequest-game/examples/tension_fixture_export.rs` — `cargo run --example tension_fixture_export -p sidequest-game` regenerates fixtures from the live Rust functions; takes optional output-path argument.

**Tests Written:** 40 pytest functions covering 6 ACs (29 Rust ports + 11 AC-driven).
**Status:** RED (verified — `ModuleNotFoundError: No module named 'sidequest.game.tension_tracker'` at collection time).

### Rule Coverage (Python lang-review checklist)

| Rule | Test(s) / Discipline | Status |
|------|---------|--------|
| #1 silent exceptions | n/a — test files contain no exception handlers | n/a |
| #2 mutable defaults | n/a — no function defs with mutable defaults in tests | n/a |
| #3 type annotations | All test helpers (`_round_from_fixture`, `_classification_from_fixture`, `_replay_scenario`, `_section`, `_make_client`, etc.) have parameter + return annotations | passing-by-design |
| #4 logging | n/a — tests use pytest assertion machinery, not logger | n/a |
| #5 path handling | All file IO uses `pathlib.Path`; `open()` is via `Path.open(encoding="utf-8")`; no string concatenation; fixture path resolved via `Path(__file__).parent` chain | passing-by-design |
| #6 test quality | Every test asserts a specific value/state — no `assert True`, no `assert result` truthy-check, no test calls a function without asserting; the rule-enforcement check itself (`test_every_rust_test_has_python_counterpart`) self-validates 1:1 mapping; no `@pytest.mark.skip` | self-checked, passing-by-design |
| #7 resource leaks | Fixture loader uses `with path.open(...)` context manager | passing-by-design |
| #8 unsafe deserialization | `json.load` on committed fixtures we authored — not user input; no `yaml.load`, no `pickle`, no `eval` | passing-by-design |
| #9 async pitfalls | No async tests — `_FakeProcess` is the only async surface and `communicate()` is properly awaitable | passing-by-design |
| #10 import hygiene | No `from x import *`; explicit imports; no circular import potential (tests import from project, not vice versa) | passing-by-design |
| #11 input validation | n/a — test surface, no user input boundaries | n/a |
| #12 dependency hygiene | No new deps added | n/a |

**Rules checked:** 8 of 13 applicable Python lang-review rules carry test-design discipline; remaining 5 are n/a for test-only files (#1, #2, #4, #11, #12 don't apply to a test module that has no error handlers, no defaults with mutables, no logging, no input boundaries, no deps).

**Self-check:** Reviewed every assertion. No vacuous tests:
- All `assert X == Y` with concrete expected values
- All fixture-parity tests collect failures into a list and assert non-empty failure list message
- All boolean assertions check specific predicates (`> 0.0`, `<= 1.0`, `is None`, `is not None`)
- `test_combat_event_variants_exist` asserts both existence AND distinctness (Rust's bare `let _ = ...` would not have caught aliasing — Python version is stronger)
- `test_pacing_hint_signature_requires_thresholds` asserts the call raises `TypeError` — proves the contract, not just that the function exists

**Vacuous tests found and fixed/removed:** 0 (no pre-existing `tension_tracker` tests to triage)

### Wiring Coverage

Per CLAUDE.md "Every Test Suite Needs a Wiring Test":
- `test_orchestrator_pacing_wiring.py::test_pacing_hint_present_registers_pacing_section_in_late_zone` is the integration test — exercises `Orchestrator.build_narrator_prompt → registry.register_pacing_section` end-to-end via the production code path, not via a unit-level helper. When Dev wires this, the test confirms the field is reachable from the production prompt builder, not just constructible in isolation.
- `test_pacing_hint_registers_on_delta_tier` covers the per-turn-tier wiring path — per-turn dynamic state must be present on Delta tier per ADR-066.

### Handoff

**To Dev (Naomi Nagata) for GREEN.** Implementation surface:
1. New file: `sidequest-server/sidequest/game/tension_tracker.py` — port the Rust types and methods 1:1. The `register_pacing_section` helper already exists in Python — wire site is one call in `Orchestrator.build_narrator_prompt`.
2. Modify: `sidequest-server/sidequest/agents/orchestrator.py` — add `TurnContext.pacing_hint: PacingHint | None = None` field; in `build_narrator_prompt`, when set, call `registry.register_pacing_section(agent_name, hint.narrator_directive(), hint.escalation_beat)`.

**Branch state:**
- `sidequest-server` on `feat/42-3-tension-pacing-classify-port` — RED commit `ae6033d`.
- `sidequest-api` on `feat/42-3-tension-fixture-export` — fixture exporter commit `b75cb6e`. (Cherry-picked clean off develop after an initial misplaced commit on `feat/39-5-…`; that branch was rewound to its upstream via `git update-ref` — no work lost, no destructive ops.)

**Risk callouts for Dev:**
- The `_approx` tolerance in scenario tests is `1e-9` — Rust f64 / Python float arithmetic is bit-identical for these operations; if anything drifts, look for ordering of `clamp` vs `max` not for floating-point error.
- `escalation_beat` text is byte-identical: `"The environment shifts — introduce a new element to break the monotony."` (with em-dash). Tests compare on equality.
- `narrator_directive()` format string is byte-identical: `"Target approximately {N} sentence(s) for this narration. Drama level: {pct}%."` where `pct` is `drama_weight * 100.0` formatted as `{:.0}` (zero decimals). Match exactly.
- The `tick()` Python method takes no args (matches Rust). Do not be tempted by the AC2 phrasing.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/tension_tracker.py` — NEW (483 LOC). 1:1 port of `sidequest-api/crates/sidequest-game/src/tension_tracker.rs` (803 LOC). Types: `RoundResult`, `DamageEvent` (Pydantic, `extra='forbid'`), `PacingHint`, `TurnClassification` (frozen dataclasses), `DeliveryMode`, `CombatEvent`, `DetailedCombatEvent` (StrEnum), private `_EventSpike`. Class `TensionTracker` with all Rust methods (`new`, `with_values`, `action_tension`, `stakes_tension`, `drama_weight`, `active_spike`, `boring_streak`, `inject_spike`, `record_event`, `update_stakes`, `tick`, `pacing_hint`, `observe`). Free functions `classify_round` and `classify_combat_outcome`. Constants mirror Rust file-private items.
- `sidequest-server/sidequest/agents/orchestrator.py` — added `from sidequest.game.tension_tracker import PacingHint`; new `pacing_hint: PacingHint | None = None` field on `TurnContext` (with deviation rationale comment); new wire block in `build_narrator_prompt` that calls `registry.register_pacing_section(agent_name, hint.narrator_directive(), hint.escalation_beat)` every tier when set.

**Companion Branch (sidequest-api):**
- `feat/42-3-tension-fixture-export` (commit `b75cb6e`, pushed) — Rust example `crates/sidequest-game/examples/tension_fixture_export.rs` that emits Rust-canonical JSON fixtures consumed by the Python parity tests. Authored during RED phase by TEA; included here for context.

**Tests:** 49/49 passing on the new test files (41 in `test_tension_tracker.py`, 8 in `test_orchestrator_pacing_wiring.py`). Full server suite: 1478 passed, 0 regressions, 24 pre-existing skips.

**Branch:** `feat/42-3-tension-pacing-classify-port` on `sidequest-server` — pushed to origin. Two commits:
- `ae6033d` test(42-3): RED-phase tests + fixtures (TEA)
- `b150a18` feat(42-3): TensionTracker port + Orchestrator pacing wiring (Dev)

**Wiring verified:** `Orchestrator.build_narrator_prompt` is the single production-code call site for the new field; non-test consumers exist (test_orchestrator_pacing_wiring.py drives the production path through `build_narrator_prompt` rather than reaching into `register_pacing_section` directly).

**ACs covered:**
- AC1 — Classification parity (fixture-driven, 11+12 cases) ✓
- AC2 — Multi-round PacingHint parity (3 scenarios, replayed step-for-step) ✓
- AC3 — Narrator-zone wiring (Late zone, name "pacing", `None`-skip) ✓
- AC4 — DramaThresholds sourced from genre pack (threshold-shift tests) ✓
- AC5 — 1:1 Rust test mapping (`test_every_rust_test_has_python_counterpart`) ✓
- AC6 — Scriptable fixture regeneration (`cargo run --example tension_fixture_export`) ✓

**Handoff:** To Reviewer (Chrisjen Avasarala) for adversarial review.

## Dev Assessment (rework round 2)

**Implementation Complete:** Yes — all 11 confirmed reviewer findings addressed in commit `c23108c` (pushed).

**Files Changed (rework):**
- `sidequest/game/tension_tracker.py` — 4 hardening fixes:
  1. `assert max_hp > 0` → `if max_hp <= 0: raise ValueError(...)` (silent-fallback rule)
  2. Defensive `assert classification.event is not None` → explicit `RuntimeError` with `# pragma: no cover` (factory-method-guaranteed invariant; raise survives `-O`)
  3. `TurnClassification.kind: str` → `kind: TurnClassificationKind` (`Literal["Boring","Normal","Dramatic"]`); added `from typing import Literal`
  4. `_EventSpike` → `@dataclass(frozen=True)` (matches frozen-value-type rule)
- `sidequest/agents/orchestrator.py` — `TurnContext.pacing_hint` field comment rewritten to accurately describe the marshalling: typed-field parity with Rust's seam, helper signatures differ
- `tests/game/test_tension_tracker.py` — 6 fixes:
  1. `is not None` enum checks → value-equality (`== "Boring"` etc.)
  2. `pytest.skip` inside helper → `@pytest.mark.skipif` decorator on the AC5 test
  3. Added `len(fixture["steps"]) > 0` guard in `_replay_scenario`
  4. Module docstring `round_result` → `round`
  5. Removed unused `PacingHint` import (ruff F401)
  6. Removed needless `f` prefix on assertion message (ruff F541)
- `tests/agents/test_orchestrator_pacing_wiring.py` — 3 fixes:
  1. `_section()` now uses `registry.get_sections()` public API; signature typed `PromptRegistry → PromptSection | None`; dropped `# type: ignore`
  2. `spawn_fn`'s `env: Any` → `env: object` with comment about spawn-protocol heterogeneity
  3. Removed unused `import pytest` (ruff F401)

**Tests:** 107/107 passing (44 tension_tracker + 8 pacing_wiring + 55 orchestrator regression). Zero new regressions.
**Ruff:** Clean on every file in the 42-3 diff. Pre-existing 14 ruff findings on `orchestrator.py` (unused span/SPAN_*, SIM102/SIM108 in legacy wiring, UP037 type-quote strings) intentionally untouched — outside 42-3 scope.

**Branch:** `feat/42-3-tension-pacing-classify-port` on `sidequest-server` — pushed (`e7f3aaf..c23108c`). Commits now total:
- `ae6033d` test(42-3): RED-phase tests + fixtures (TEA)
- `b150a18` feat(42-3): TensionTracker port + Orchestrator pacing wiring (Dev)
- `e7f3aaf` chore(42-3): tea-verify ruff cleanup (TEA verify)
- `c23108c` chore(42-3): reviewer rework — silent-fallback + type-design + test hardening (Dev rework)

**Companion branch (unchanged):** `feat/42-3-tension-fixture-export` on `sidequest-api` (commit `b75cb6e`).

**Out of scope, deferred to 42-4 per Architect spec-check:** OTEL span at PacingHint registration site. Reviewer captured this in delivery findings as a forward note for 42-4 context.

**Handoff:** Back to Reviewer (Avasarala) for re-review of the rework. Expect quick re-approval — all changes are mechanical hardening, not logic changes.

## TEA Assessment (verify, round 2)

**Phase:** finish (round 2)
**Status:** GREEN HELD — all 11 reviewer findings addressed without test regression or new ruff debt.

### Simplify Decision (round 2)

**Skipped — by design.** The Dev rework commit `c23108c` exclusively addressed Reviewer's enumerated findings (silent-fallback hardening, type-design tightening, vacuous-test fix, ruff cleanup). Round 1 simplify fan-out (commit `e7f3aaf`) returned clean / out-of-scope-only findings on the same code. Re-spawning the three teammates would rediscover the same patterns Reviewer already requested be changed — tautological. Reviewer's specialists ARE adversarial reviewers of the same dimensions (test-analyzer ≈ test-quality, type-design ≈ structural simplification, silent-failure-hunter ≈ over-engineered defensive code). The rework's scope is bounded; a fresh pass adds noise without signal.

### Quality-Pass Gate (round 2 — ruff)

Ruff clean on every 42-3 diff file:

| File | Status |
|------|--------|
| `sidequest/game/tension_tracker.py` | clean ✓ |
| `tests/game/test_tension_tracker.py` | clean ✓ |
| `tests/agents/test_orchestrator_pacing_wiring.py` | clean ✓ |
| `sidequest/agents/orchestrator.py` | 14 pre-existing findings (uuid unused, SPAN_* unused, span var unused, SIM102/SIM108 in legacy wiring, UP037 type-quote strings) — **all outside 42-3 diff lines**, intentionally untouched per minimalist discipline |

### Final Test Status

107/107 passing — same as round 1 verify:
- `tests/game/test_tension_tracker.py`: 44/44 ✓
- `tests/agents/test_orchestrator_pacing_wiring.py`: 8/8 ✓
- `tests/agents/test_orchestrator.py`: 55/55 ✓ (regression check — Dev rework didn't change orchestrator behavior, only the `TurnContext.pacing_hint` docstring)

### Reviewer Finding Resolution Verification

Spot-checked each of the 11 Reviewer-confirmed findings against the rework commit:

| # | Finding | Verified |
|---|---------|----------|
| 1 | `assert max_hp > 0` → raise | `tension_tracker.py:362` `if max_hp <= 0: raise ValueError` ✓ |
| 2 | defensive `assert classification.event is not None` removed | `tension_tracker.py:435-440` explicit `RuntimeError` with `# pragma: no cover` ✓ |
| 3 | `TurnClassification.kind: str` → `Literal` | `tension_tracker.py:189-194` `TurnClassificationKind = Literal["Boring","Normal","Dramatic"]` alias added ✓ |
| 4 | `_EventSpike` → `frozen=True` | `tension_tracker.py:268` ✓ |
| 5 | vacuous `is not None` on enum members | `test_tension_tracker.py:357-360` `== "Boring"` value checks ✓ |
| 6 | silent `pytest.skip` → `@skipif` decorator | `test_tension_tracker.py:644-651` ✓ |
| 7 | `TurnContext.pacing_hint` comment rewrite | `orchestrator.py:316-329` accurate marshalling description ✓ |
| 8 | test docstring `round_result` → `round` | `test_tension_tracker.py:31-32` ✓ |
| 9 | `_replay_scenario` empty-steps guard | `test_tension_tracker.py:464-467` ✓ |
| 10 | `_section()` use public API | `test_orchestrator_pacing_wiring.py:77-89` `registry.get_sections()` ✓ |
| 11 | tighter `Any` types in test helpers | `test_orchestrator_pacing_wiring.py:60-67,77-79` `object` + `PromptRegistry` + `PromptSection` ✓ |
| OTEL | downgraded with defer-to-42-4 | Untouched as agreed; carried in Reviewer delivery findings ✓ |

### Delivery Findings (round 2)

No new findings during verify round 2. Round 1 findings (TEA's verify ruff scope, OTEL deferred to 42-4) carry forward unchanged.

**Handoff:** Back to Reviewer (Avasarala) for re-approval of the rework. All 11 confirmed findings resolved with mechanical, behaviour-preserving changes.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 5 ruff in test files (missed by TEA scope), 1 conditional pytest.skip noted | confirmed 5, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (workflow.reviewer_subagents.edge_hunter=false) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 (2 in pre-existing soul.py — out of scope; 1 confirmed assert; 1 low-confidence Rust-parity skip filter) | confirmed 1, dismissed 3 |
| 4 | reviewer-test-analyzer | Yes | findings | 6 (1 vacuous enum check, 1 silent skip on missing Rust source, 1 empty-steps guard, 1 private-API coupling, 2 weaker-than-Rust assertions) | confirmed 4, dismissed 2 (1:1 port discipline forbids tightening beyond Rust source) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (TurnContext comment partially misleading, test docstring param-name mismatch) | confirmed 2 |
| 6 | reviewer-type-design | Yes | findings | 5 (TurnClassification.kind stringly-typed, _EventSpike not frozen, broken-invariant module-dict, 2 Any annotations) | confirmed 4, dismissed 1 (module-dict — runtime KeyError caught by tests; structurally adequate) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (workflow.reviewer_subagents.security=false) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (workflow.reviewer_subagents.simplifier=false) — and was already run as TEA verify simplify fan-out (clean / out-of-scope-only findings) |
| 9 | reviewer-rule-checker | Yes | findings | 5 (2 silent-fallback asserts re-confirmed, 1 vacuous test re-confirmed, 1 OTEL span gap, 1 wiring gap) | confirmed 3, downgraded 1 (OTEL — Architect deferred to 42-4), dismissed 1 (wiring — story scope explicitly defers TensionTracker→game-loop ownership to 42-4) |

**All received:** Yes (6 returned with findings, 3 disabled via settings)
**Total findings:** 13 confirmed, 7 dismissed (with rationale), 1 downgraded (OTEL → MEDIUM with defer-to-42-4 note)

## Reviewer Assessment

**Verdict:** REJECTED — fix-iteration required (lint + type-design + silent-fallback hardening), all findings addressable by Dev in a single green-rework pass.

### Severity Table

| Severity | Tag | Issue | Location | Fix Required |
|----------|-----|-------|----------|--------------|
| [HIGH] | [SILENT] [RULE] | `assert max_hp > 0` is stripped under `python -O` — silent fallback into `ZeroDivisionError` with no domain message | `sidequest/game/tension_tracker.py:361` | Replace with `if max_hp <= 0: raise ValueError("max_hp must be positive")` — matches Python idiom for boundary validation. Rust uses `debug_assert!` (also stripped in release) but CLAUDE.md "no silent fallbacks" overrides the literal mirror |
| [HIGH] | [SILENT] [RULE] | `assert classification.event is not None` is stripped under `-O` — invariant violation reaches `event.spike_magnitude()` and raises `AttributeError` instead of clear diagnostic | `sidequest/game/tension_tracker.py:428` | Either remove (factory methods structurally guarantee the invariant — the only path to `kind == "Dramatic"` runs through `TurnClassification.dramatic(event)` which requires a non-None argument), OR replace with explicit `if classification.event is None: raise RuntimeError(...)`. Removal is preferred — the invariant is type-system-enforceable |
| [HIGH] | [TYPE] [RULE] | `TurnClassification.kind: str` is stringly-typed — only "Boring", "Normal", "Dramatic" are valid; `observe()` dispatches on `classification.kind == "Boring"` with no static protection | `sidequest/game/tension_tracker.py:203` | Change to `kind: Literal["Boring", "Normal", "Dramatic"]` (no enum needed — three string literals capture the algebraic enum well enough and the factory methods enforce construction). Matches stated PROJECT_RULES "stringly-typed APIs" rule |
| [HIGH] | [TYPE] [RULE] | `_EventSpike` is mutable `@dataclass` — value type with no identity semantics, never mutated post-construction by `TensionTracker` | `sidequest/game/tension_tracker.py:263` | Add `frozen=True`. Matches stated PROJECT_RULES "frozen=True dataclass for value types" rule. One-line change |
| [HIGH] | [TEST] [RULE] | Vacuous `is not None` checks on StrEnum members — enum members are never None, the assertion is provably true | `tests/game/test_tension_tracker.py:353` | Replace `assert CombatEvent.Boring is not None` with value-equality checks, e.g. `assert CombatEvent.Boring == "Boring"` (StrEnum members compare to their string value). Matches Python lang-review #6 (vacuous assertions) |
| [HIGH] | [TEST] [SILENT] | `pytest.skip` in `_rust_test_names()` silently passes the 1:1 port parity test in any environment where sidequest-api is not co-located | `tests/game/test_tension_tracker.py:621` | Either `pytest.fail(f"Rust source not present at {RUST_SOURCE} — cannot enforce 1:1 port parity")`, or move to a function-level `@pytest.mark.skipif(not RUST_SOURCE.exists(), reason="...")` so the skip is visible in the test report rather than buried in a helper. Matches CLAUDE.md "no silent fallbacks" |
| [MEDIUM] | [DOC] | `TurnContext.pacing_hint` field comment claims "no string-marshalling layer" but the call site DOES marshal to two strings; comment claim that it "matches Rust" overstates parity (Rust helper takes `&PacingHint`, Python helper takes two strings) | `sidequest/agents/orchestrator.py:316-323` | Rewrite the rationale block: typed field PRESERVES `escalation_beat` for the call site to marshal; Python's `register_pacing_section` takes two derived strings (different signature from Rust). The architectural intent — not pre-rendering at the field — is correct; the wording is imprecise |
| [MEDIUM] | [DOC] | Test module docstring lists `classify_round(round_result, killed)` but the actual parameter is `round` | `tests/game/test_tension_tracker.py` (module docstring near line 28) | Change `round_result` → `round` to match implementation |
| [MEDIUM] | [TEST] | `_replay_scenario` has no guard on `len(fixture["steps"]) > 0` — a regenerated scenario fixture with empty steps would silently pass the parity gate | `tests/game/test_tension_tracker.py:452` | Add `assert len(fixture["steps"]) > 0, f"scenario fixture {fixture_name} has no steps"` before the for loop, matching the `len(cases) > 0` guard already present in the two `classify_*_fixture_parity` tests |
| [MEDIUM] | [TEST] | `_section()` reaches into private `registry._sections` dict — tight coupling to PromptRegistry storage layout; a refactor of internal storage would break all 8 wiring tests with no behavioral change | `tests/agents/test_orchestrator_pacing_wiring.py:71-81` | Replace `registry._sections.get(agent_name, [])` with the public `registry.get_sections(agent_name)` (declared at `prompt_framework/core.py:105`). Drop the `# type: ignore[attr-defined]` and the `Any` registry param type — use `PromptRegistry` |
| [MEDIUM] | [TYPE] | `env: Any = None` and `_section(registry: Any, ...) -> Any | None` use `Any` without the rule-required justification comment | `tests/agents/test_orchestrator_pacing_wiring.py:60,71` | Either tighten types (`env: dict[str, str] | None = None`; `registry: PromptRegistry`; `-> PromptSection | None`) or add comments explaining why `Any` is required. Matches Python lang-review #3 |
| [MEDIUM] | [PRE] | 5 ruff findings in test files (TEA's verify-phase ruff scan only covered production code, not the test files in the diff) | `tests/game/test_tension_tracker.py:42 (I001), :55 (F401 unused PacingHint), :642 (F541 needless f-string)`; `tests/agents/test_orchestrator_pacing_wiring.py:15 (I001), :20 (F401 unused pytest)` | Run `ruff check --fix` on both test files. Manually drop the unused `PacingHint` test-file import — but check first: it IS used in test_pacing_hint_signature_requires_thresholds via `pacing_hint()` calls? No — only the production `PacingHint` is used in test_orchestrator_pacing_wiring.py. The test_tension_tracker.py only uses it in type hints inside docstrings. Verify before removing |
| [MEDIUM] | [RULE] | Pacing-section registration in `build_narrator_prompt` does not emit an OTEL span (Architect deferred to 42-4 in spec-check) | `sidequest/agents/orchestrator.py:1007-1018` | DOWNGRADED severity — Architect's 42-4 defer was logged in spec-check assessment with rationale (TensionTracker not yet wired into production game loop, so a span at this site would always fire with `pacing_hint=None`-skipped). Confirm the defer note carries forward into the 42-4 context doc so it cannot drift. Not blocking for 42-3 |

### Dismissed Findings (with rationale)

- **Test-analyzer "tighten `< before` to `== 0.0` in `test_dramatic_event_drops_action_tension`"** — Dismissed: ADR-082 §test-porting discipline says "every Rust `#[test]` becomes one pytest function with the same name. No idiomatic rewrites — Rust source is the behavioural contract." The Rust test uses `assert!(tracker.action_tension() < before)`. Tightening Python beyond Rust = port deviation. If Rust's assertion is weak, that's a Rust-test concern, not 42-3's.
- **Test-analyzer "tighten `>= 0.0` in `test_action_tension_never_goes_negative`"** — Dismissed for the same 1:1-port reason. Rust test does the same trivially-zero check.
- **Type-design "module-level `_SPIKE_MAGNITUDE` / `_DECAY_RATE` dicts can KeyError on missing variant"** — Dismissed: structurally adequate. The `DetailedCombatEvent` StrEnum is closed under Python (no `#[non_exhaustive]` semantic equivalent matters at runtime); a missing dict entry would be caught immediately by the test suite (every variant is exercised by `_SPIKE_MAGNITUDE` keys directly). The class docstring already warns "the spike_magnitude and decay_rate methods must grow a matching arm" — adequate developer signal.
- **Silent-failure-hunter "parse_soul_md silent fallback in soul.py"** and **"orchestrator.py:591 _soul_data fallback is dead code"** — Dismissed: pre-existing code, not in 42-3 diff.
- **Silent-failure-hunter "register_pacing_section silent skip on non-narrator agent"** — Dismissed: low-confidence finding, intentional Rust parity, no rule violation.
- **Rule-checker "wiring gap: TensionTracker→game-loop"** — Dismissed: story scope (highest spec authority) explicitly states "Where `TensionTracker` instances are owned (session/encounter/connection) — that's dispatch scope (42-4). For 42-3, the tracker is constructed in test scope only; production ownership lands in 42-4." This is exactly the wiring TEA will verify in 42-4 with an integration test. The 42-3 wiring test (PacingHint→TurnContext→register_pacing_section) is correctly present.
- **Rule-checker "import hygiene: `import pathlib` inside function body in orchestrator.py"** — Dismissed: pre-existing code in `_load_soul_data`, not in 42-3 diff.

### Data Flow Trace

User input → `process_action(action: str)` → `Orchestrator.process_action` → `select_prompt_tier(context)` → `build_narrator_prompt(action, context, tier)` → **(NEW)** `if context.pacing_hint is not None: registry.register_pacing_section(agent_name, hint.narrator_directive(), hint.escalation_beat)` → `registry.compose(agent_name)` → narrator-prompt string → ClaudeClient subprocess.

The PacingHint side of the wire is fully traceable. The TensionTracker→PacingHint side is **not yet wired** (per story scope, deferred to 42-4). In production today, `context.pacing_hint` is always `None` at the call site because no production code constructs a `TensionTracker` and writes to `TurnContext.pacing_hint`. **[VERIFIED]** — Story 42-3 explicitly defers ownership to 42-4. Test coverage proves the wire activates correctly when `pacing_hint` is set; 42-4 will install the producer.

### Pattern Observations

- **[VERIFIED] register_pacing_section reuse pattern** — `sidequest/agents/orchestrator.py:1014` calls the existing helper at `sidequest/agents/prompt_framework/core.py:140` rather than reimplementing section registration inline. Complies with CLAUDE.md "Don't Reinvent — Wire Up What Exists" rule.
- **[VERIFIED] Pydantic `extra='forbid'` on `DamageEvent` and `RoundResult`** — `sidequest/game/tension_tracker.py:88,102` follows the 42-2 `resource_pool.py` precedent for input-boundary types. Complies with type-design PROJECT_RULES.
- **[VERIFIED] StrEnum for enum-shaped Rust types** — `DeliveryMode`, `CombatEvent`, `DetailedCombatEvent` (lines 115, 127, 138) all use StrEnum, the right Python idiom for serde-stable enum shapes.
- **[VERIFIED] Constants byte-identical with Rust source** — Spot-checked `_BORING_BASE=0.05`, `_ACTION_DECAY=0.9`, `_DEFAULT_SPIKE_DECAY_RATE=0.15`, `_DRAMATIC_DAMAGE_THRESHOLD=15`, `_NEAR_MISS_HP_THRESHOLD=0.2` against Rust file-private const items. All match.
- **[VERIFIED] Format strings byte-identical** — `narrator_directive()` format and the em-dash escalation beat literal (`"The environment shifts — introduce a new element to break the monotony."`) match Rust source verbatim. Architect spot-check confirmed; tests pin parity via fixture-driven scenarios.
- **[VERIFIED] No new dependencies, no star imports, `__all__` declared** — `sidequest/game/tension_tracker.py:545-556` exports the public API explicitly.

### Devil's Advocate

I will argue this code is broken.

**Adversary 1 — the production deployer running `python -O`:** SideQuest will eventually be deployed, and someone will set `PYTHONOPTIMIZE=1` either deliberately (perceived perf gain) or accidentally (a Docker base image with optimization defaults). The moment that happens, two assertions in `tension_tracker.py` go silent: `assert max_hp > 0` (line 361) and `assert classification.event is not None` (line 428). The first lets a `0` HP cap reach division and produces `ZeroDivisionError` with no domain context — and the bug looks like an arithmetic bug, not an input-validation bug. The second one is more insidious: `classify_combat_outcome` could in principle return `Dramatic` with `event=None` (today the factory methods prevent this, but a future refactor that adds a code path setting `kind="Dramatic"` directly would slip through). Then `event.spike_magnitude()` raises `AttributeError: 'NoneType' object has no attribute 'spike_magnitude'`. Both errors will surface in production OTEL as opaque traces, not the clear domain errors a player or operator can act on. **CLAUDE.md is loud about this: "no silent fallbacks." This finding is real.**

**Adversary 2 — the 42-4 author wiring TensionTracker into the game loop:** The 42-4 author writes code that constructs a `TurnClassification` directly (perhaps deserialising it from a saved game state), passing `kind="Dramtic"` (typo) — a stringly-typed field accepts the typo silently, and `observe()` falls through to the `else: # Normal` branch. The encounter behaves wrong, with no error message. **A `Literal` type would force the type checker to reject the typo at construction time. This finding is real.**

**Adversary 3 — the future LoRA test designer reading `test_tension_tracker.py`:** They run the test suite in CI without sidequest-api co-located. The 1:1-port parity test silently skips. The test report shows green. They merge a Python-side refactor that breaks parity with Rust. The drift is invisible until someone runs locally with both repos checked out. **CLAUDE.md "no silent fallbacks" again — this finding is real.**

**Adversary 4 — the new contributor reading `_section()` in the wiring tests:** They see `registry._sections.get(agent_name, [])`. They assume `_sections` is a stable interface because the tests use it. They write new tests against the same private. PromptRegistry's storage gets refactored. Eight tests break in a way that has nothing to do with the behavior. **The public `get_sections()` method exists for exactly this reason. Coupling test code to private storage is a real bug magnet.**

**Adversary 5 — the maintenance engineer adding a 7th `DetailedCombatEvent` variant six months from now (e.g., `Counterspell`):** They add the variant to the StrEnum but forget to add entries to `_SPIKE_MAGNITUDE` and `_DECAY_RATE`. The first time someone hits a `Counterspell` event in production, `KeyError: <DetailedCombatEvent.Counterspell: ...>` fires from inside `observe()`. **The class docstring warns about this — "must grow a matching arm" — but documentation is not enforcement. A `match self:` statement (Python 3.10+) would warn at type-check time about non-exhaustive coverage. This is a structural concern but not blocking — the test suite would catch it the moment any test exercised the new variant, and the docstring warning is loud enough that I'm not going to require a refactor here.** Downgrade to NOTED.

**Counter-argument: the implementation is exceptionally faithful to Rust.** Constants match. Format strings match. State-mutation order matches. Fixture-parity tests cover 23 classification cases and 22 multi-step scenarios. The narrator wire-site reuses an already-correct Python helper (zone, name, agent filter). Architect's spec-check verified all 12 invariants. The findings above are real but they are **hardening** issues, not **correctness** issues — the port itself works.

**Conclusion: REJECT for hardening, but the rework is a single small green-phase pass — no test redesign needed.**

### Handoff

**Back to Dev (Naomi Nagata) for green rework.** Findings are lint/format/type-tightening/dead-defensive-code — no logic changes, no new test design needed (TEA's existing scenarios cover behaviour). Dev should:

1. Replace 2 `assert` statements with explicit `raise` (or remove the `observe()` defensive assert if invariant is structurally guaranteed, which it is).
2. Tighten `TurnClassification.kind: str` → `Literal["Boring", "Normal", "Dramatic"]` and add `from typing import Literal` import.
3. `_EventSpike` → `@dataclass(frozen=True)`.
4. Replace vacuous `is not None` checks in `test_combat_event_variants_exist` with value-equality checks against the StrEnum string values.
5. Replace `pytest.skip` in `_rust_test_names()` with `pytest.fail` OR move to function-level `@pytest.mark.skipif`.
6. Tighten `TurnContext.pacing_hint` field comment to accurately describe the marshalling.
7. Fix test docstring `round_result` → `round`.
8. Add `len(fixture["steps"]) > 0` guard in `_replay_scenario`.
9. Replace `_section()` reach-into-private with `registry.get_sections(agent_name)` filter.
10. Tighten `Any` types in test helpers OR add justification comments.
11. Run `ruff check --fix` on both test files (5 mechanical findings).
12. Re-run pytest to confirm GREEN; push.

OTEL span (item 13) deferred to 42-4 per Architect spec-check note — confirm the defer is captured in the 42-4 context doc so it cannot drift.

**Re-review estimate:** 30-45 min for Dev to apply, then quick re-run. No new RED phase needed.

## Reviewer Assessment (round 2)

**Verdict:** APPROVED

### Round 2 Methodology

The rework commit `c23108c` was strictly Reviewer-directed — every change addresses one of the 11 findings I confirmed in round 1. Re-spawning all 6 specialists on a Reviewer-driven rework risks tautological rediscovery: the test-analyzer will look at the very fix the test-analyzer asked for, the type-design specialist will look at the type tightening it requested, etc. The right round-2 method is targeted verification, not a fresh fan-out.

**Verification used:**
- TEA's verify-round-2 spot-check table (one row per finding, file:line citation) — independently confirmed each fix is in place at the cited location
- My own spot-read of all four code change sites (`tension_tracker.py:191`, `:194`, `:369-379`, `:449-460` for production code; matching test files) — confirmed the diffs match the requested changes verbatim
- Test result: 107/107 GREEN, no regressions, no new ruff debt
- Round-1 Subagent Results table remains valid — those specialists analysed the same code surface; the rework only changes the spots they flagged

### Finding Resolution Audit

All 6 HIGH findings: ✓ resolved
All 5 MEDIUM findings: ✓ resolved
1 OTEL downgrade: ✓ unchanged (deferred to 42-4 as agreed)

| # | Original Finding (Severity) | Rework Resolution | Verified |
|---|------------------------------|-------------------|----------|
| 1 | [HIGH SILENT/RULE] `assert max_hp > 0` strips under -O | `if max_hp <= 0: raise ValueError(...)` at `tension_tracker.py:377-378` with rationale docstring referencing CLAUDE.md | ✓ |
| 2 | [HIGH SILENT/RULE] `assert classification.event is not None` strips under -O | Explicit `RuntimeError` with `# pragma: no cover` at `:451-455` — coverage-honest, runtime-loud | ✓ |
| 3 | [HIGH TYPE/RULE] `TurnClassification.kind: str` is stringly-typed | `kind: TurnClassificationKind` (Literal alias) at `:191`, `:215` | ✓ |
| 4 | [HIGH TYPE/RULE] `_EventSpike` not frozen | `@dataclass(frozen=True)` at `:268` | ✓ |
| 5 | [HIGH TEST/RULE] Vacuous `is not None` on enum members | `assert CombatEvent.X == "X"` at `test_tension_tracker.py:357-360` | ✓ |
| 6 | [HIGH TEST/SILENT] `pytest.skip` in helper buries the skip | `@pytest.mark.skipif` decorator at `:644-651` — visible in pytest report | ✓ |
| 7 | [MED DOC] Inaccurate marshalling claim in TurnContext comment | Rewritten at `orchestrator.py:316-329` — distinguishes typed-field parity from helper-signature divergence | ✓ |
| 8 | [MED DOC] Test docstring `round_result` doesn't match `round` param | Fixed at `test_tension_tracker.py:31-32` | ✓ |
| 9 | [MED TEST] `_replay_scenario` no empty-steps guard | `assert len(fixture["steps"]) > 0` added at `:464-467` | ✓ |
| 10 | [MED TEST] `_section()` reaches into private `_sections` | Now uses public `registry.get_sections()` at `test_orchestrator_pacing_wiring.py:86` | ✓ |
| 11 | [MED TYPE] `Any` annotations without justification | `env: object` with comment, `_section` typed `PromptRegistry → PromptSection \| None` | ✓ |
| OTEL | [DOWNGRADED MED] No span at pacing wire site | Unchanged — Architect deferred to 42-4; Reviewer captured in delivery findings as forward note | ✓ |

### Spot-Read Observations (round 2)

- **[VERIFIED] Literal type approximates Rust algebraic enum well** — `tension_tracker.py:191` `TurnClassificationKind = Literal["Boring","Normal","Dramatic"]`. Future readers can grep for the alias name. The factory methods (`boring()`, `normal()`, `dramatic(event)`) remain the only sanctioned construction path; the type system now catches typo'd kinds at construction time.
- **[VERIFIED] `# pragma: no cover` on the structurally-impossible branch** — `:451`. Coverage tool will not flag the unreached code, while the runtime guard remains loud. Right Python idiom.
- **[VERIFIED] `_section()` uses public API** — `test_orchestrator_pacing_wiring.py:86` `for section in registry.get_sections(agent_name)`. The `# type: ignore[attr-defined]` comment is gone — clean.
- **[VERIFIED] Updated comment is accurate** — `orchestrator.py:316-329` correctly says "the *field* mirrors Rust's typed seam; the *helper signatures* differ." Old wording overstated parity; new wording is precise.
- **[VERIFIED] No regression in pre-existing orchestrator code** — ruff still shows the same 14 pre-existing findings, no new ones introduced by the field comment edit. Imports still sorted correctly post-rework.

### Devil's Advocate (round 2)

**Adversary 1 — the type-checker fundamentalist:** Could `TurnClassification.kind: Literal[...]` still be defeated? Yes — at runtime, Python doesn't enforce Literal. `TurnClassification(kind="Dragnball", event=None)` constructs successfully unless the caller runs mypy/pyright. Counter: the factory methods are the only sanctioned path; direct construction with a bad string is a deliberate type-system bypass and not a defect of the design.

**Adversary 2 — the `# pragma: no cover` skeptic:** What if a future refactor adds a `kind="Dramatic"` construction path that bypasses the factory? The runtime `if event is None: raise RuntimeError` still catches it, and the test suite would fail at the new construction site immediately. The `# pragma: no cover` only excludes the unreachable branch from coverage metrics; it does not disable the guard. Acceptable.

**Adversary 3 — the value-equality fundamentalist on enum tests:** `assert CombatEvent.Boring == "Boring"` works because `CombatEvent` is `StrEnum` (members compare equal to their string value). If a future refactor changes the enum to plain `Enum`, the assertion would break. Counter: that refactor would be a deliberate API change and would require all callers (including tests) to update; the current assertion correctly enforces the StrEnum contract that the rest of the codebase depends on.

**Adversary 4 — the OTEL hawk:** "Defer to 42-4" is a smell. What if 42-4 doesn't actually wire the span? Counter: Reviewer's delivery finding explicitly lists it as a context-doc requirement for 42-4 — "must include 'wire OTEL span at PacingHint registration site (deferred from 42-3)' in the AC list." If 42-4's context doc lacks this AC, that's a 42-4 review failure, not a 42-3 issue. The defer is properly documented and propagated.

**Conclusion: clean approval.** The rework is mechanical, behaviour-preserving (except where the silent-fallback fix INCREASES correctness), and addresses every confirmed finding. Tests still GREEN, ruff clean on diff. No new findings.

### Data Flow (re-verified)

User input → `process_action(action)` → `select_prompt_tier(context)` → `build_narrator_prompt(action, context, tier)` → `if context.pacing_hint is not None: registry.register_pacing_section(agent_name, hint.narrator_directive(), hint.escalation_beat)` → `compose(agent_name)` → narrator-prompt string. Field default is `None` in production today; 42-4 will install the upstream producer (TensionTracker → game loop → `TurnContext.pacing_hint`).

### Handoff

**To SM (Camina Drummer) for finish-story.** All 11 confirmed findings resolved. Tests GREEN. Ruff clean on the 42-3 diff. Branch ready to merge:

- `sidequest-server` — `feat/42-3-tension-pacing-classify-port` — 4 commits (`ae6033d`, `b150a18`, `e7f3aaf`, `c23108c`) — pushed
- `sidequest-api` — `feat/42-3-tension-fixture-export` — 1 commit (`b75cb6e`) — pushed

SM creates PRs and merges per the finish protocol.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with previously logged deviations)
**Mismatches Found:** 0 new — all spec-vs-implementation drift was already captured by TEA in RED phase and acknowledged by Dev in the green commit message.

### AC-by-AC Verification

| AC | Spec requirement | Implementation | Status |
|----|------------------|----------------|--------|
| AC1 | `classify_round` / `classify_combat_outcome` produce Rust-identical values across the fixture suite; `killed=None` distinct from `killed=""` | `tension_tracker.py` ports both functions verbatim; `if killed is not None: return Dramatic` correctly treats empty-string as a kill (mirrors Rust `killed.is_some()`); 11+12 fixture cases pass | ✓ |
| AC2 | Multi-round `tick(round_result)` parity (escalating/stalling/reversal) | Implemented as Rust API: `observe(round, killed, lowest_hp_ratio)` + `pacing_hint(thresholds)`. AC2 wording is wrong (no Rust `tick(round_result)` exists) — TEA-logged conflict. 3 scenarios replay byte-for-byte through 7+ steps each. | ✓ (with logged spec drift) |
| AC3 | Pacing section in same attention zone as Rust; `None` skips registration | Lands in `AttentionZone.Late` via existing `register_pacing_section` helper; AC3 said "Early or Valley" but Rust uses `Late` — spec was wrong, code follows Rust per spec authority. None-skip verified by `test_pacing_hint_none_does_not_register_section`. | ✓ (with logged spec drift) |
| AC4 | Thresholds sourced from genre pack, not Python constants | `pacing_hint(thresholds)` takes `DramaThresholds` arg; `DramaThresholds` re-exported from `sidequest.genre.models.ocean`; threshold-shift tests confirm overridden values flow through to `DeliveryMode` and `escalation_beat` | ✓ |
| AC5 | Every Rust `#[test]` ports 1:1 | `test_every_rust_test_has_python_counterpart` greps Rust source live and asserts each name has a Python counterpart — 29/29 ports verified at test run | ✓ |
| AC6 | `cargo run --example tension_fixture_export` documented and committed fixtures | Rust example at `sidequest-api/crates/sidequest-game/examples/tension_fixture_export.rs` (commit `b75cb6e` on `feat/42-3-tension-fixture-export`), 5 committed JSON files, `tests/fixtures/tension/README.md` documents the regen command | ✓ |

### Rust Parity Spot-Checks (constants, formulas, strings)

Cross-referenced `sidequest-server/sidequest/game/tension_tracker.py` against `sidequest-api/crates/sidequest-game/src/tension_tracker.rs`:

| Invariant | Rust | Python | Match |
|-----------|------|--------|-------|
| `BORING_BASE` | `0.05` | `_BORING_BASE = 0.05` | ✓ |
| `ACTION_DECAY` | `0.9` | `_ACTION_DECAY = 0.9` | ✓ |
| `DEFAULT_SPIKE_DECAY_RATE` | `0.15` | `_DEFAULT_SPIKE_DECAY_RATE = 0.15` | ✓ |
| `DRAMATIC_DAMAGE_THRESHOLD` | `15` | `_DRAMATIC_DAMAGE_THRESHOLD = 15` | ✓ |
| `NEAR_MISS_HP_THRESHOLD` | `0.2` | `_NEAR_MISS_HP_THRESHOLD = 0.2` | ✓ |
| `target_sentences` formula | `1 + (dw * 5.0).floor() as u8` | `1 + int(math.floor(dw * 5.0))` | ✓ |
| `drama_weight` aggregation | `clamp01(max(action, stakes, effective_spike))` | `_clamp01(max(self._action_tension, self._stakes_tension, self._effective_spike()))` | ✓ |
| `narrator_directive` format | `"Target approximately {} sentence(s) for this narration. Drama level: {:.0}%."` | `f"Target approximately {N} sentence(s) for this narration. Drama level: {dw*100.0:.0f}%."` | ✓ |
| Escalation beat literal (em-dash) | `"The environment shifts — introduce a new element to break the monotony."` | identical | ✓ |
| Spike effective decay | `(magnitude - decay_rate * age).max(0.0)` | `max(magnitude - decay_rate * age, 0.0)` | ✓ |
| Action ramp on boring | `action + BORING_BASE * streak` (then clamp01) | identical | ✓ |
| `observe` priority order | age_spike → classify → record/inject | identical | ✓ |
| Wire-site zone (orchestrator) | `AttentionZone::Late`, name `"pacing"`, only PACING_AGENTS | uses existing `register_pacing_section` which already enforces all three | ✓ |
| Wire-site tier | every tier (combat starts mid-session) | wire block runs outside `if is_full:` guards | ✓ |

### Spec Drift — All Previously Captured

The 3 conflicts TEA logged + 2 deviations Dev logged collectively cover every AC-vs-implementation gap. No additional drift to surface:

- AC2 `tick(round_result)` wording — TEA conflict #1, recommendation **A — Update spec**: AC2 should read "`TensionTracker.observe(...)` followed by `pacing_hint(thresholds)`". Code is correct; refresh the AC text on next context-doc touch.
- AC3 zone wording — TEA conflict #2, recommendation **A — Update spec**: AC3 should read `AttentionZone.Late`. Existing Python helper was already Rust-correct; the doc was the drift source.
- `TurnContext.pacing_hint` typing — TEA conflict #3 + Dev deviation #1, recommendation **A — Update spec**: typed `PacingHint | None` is the closer Rust parity and 42-4-friendly. Tests pin the contract.
- Per-tier registration (Full + Delta) — Dev deviation #2, recommendation **C — Clarify spec**: Spec was silent on tier; correct answer (per-turn registration on every tier) is implicit in "PacingHint changes per-turn" but worth making explicit for future ports.

### Architectural Observations

- **Reuse-first verdict**: Implementation hit the existing-infrastructure jackpot — `register_pacing_section` (with the right zone, section name, and agent filter) was already ported to Python, and `DramaThresholds` was already in `sidequest.genre.models.ocean`. Dev's net new wiring surface is one call site (5 lines). This is the cleanest possible outcome for a port story.
- **No new abstractions**: Dev did not introduce any Pythonic helpers, decorators, or Pydantic field validators that diverge from Rust. The frozen-dataclass choice for `PacingHint` and `TurnClassification` is the most faithful translation of Rust's `#[derive(Clone, PartialEq, Eq)]` structs/enums into Python.
- **Type-safety vs spec literal**: Choosing `PacingHint | None` over `str | None` for `TurnContext.pacing_hint` is the right call architecturally — it preserves `escalation_beat` and aligns with the Rust seam where `&PacingHint` is passed to the register helper. This is the kind of judgment-call deviation that should be confirmed by the spec author (Keith), not silently accepted; logged as a non-blocking deviation with rationale.
- **OTEL note (forward)**: Per CLAUDE.md "every backend fix that touches a subsystem MUST add OTEL watcher events", the pacing wire-site does not currently emit a span when `pacing_hint` is registered. Rust's equivalent does not emit either — the closest spans are upstream in the prompt-build pipeline. **Defer to 42-4** when `TensionTracker` ownership lands and there is a meaningful per-turn lifecycle to instrument. Not blocking for 42-3.

**Decision:** Proceed to TEA verify (next phase).

## Architect Assessment (spec-check, round 2)

**Spec Alignment:** Aligned (no new drift introduced by Dev rework commit `c23108c`)
**Mismatches Found:** 0 new

### What Changed in Round 2

The rework targeted reviewer findings only — no AC contract change, no scope expansion. Verified via `git diff e7f3aaf..c23108c --stat`:

- `sidequest/game/tension_tracker.py` (+39 / -14): `assert→raise` (×2), `kind: str → Literal["Boring","Normal","Dramatic"]` with `TurnClassificationKind` alias, `_EventSpike → @dataclass(frozen=True)`. All semantic-preserving.
- `sidequest/agents/orchestrator.py` (+8 / -2): docstring rewrite on `TurnContext.pacing_hint` field — no code change.
- `tests/game/test_tension_tracker.py` (+22 / -10): vacuous `is not None` → `== "literal"`, `pytest.skip` → `@pytest.mark.skipif`, fixture step-count guard, dropped unused `PacingHint` import + needless `f` prefix, doc fix.
- `tests/agents/test_orchestrator_pacing_wiring.py` (+18 / -14): `_section()` uses public API, tighter type annotations, dropped unused `pytest` import.

### AC Re-verification

All 6 ACs still satisfied — no test removed, no test weakened, behaviour unchanged. The only behaviour-observable changes:

- AC4 path (`update_stakes` with non-positive `max_hp`) now raises `ValueError` instead of `AssertionError` (and survives `python -O`). Strengthens the contract.
- AC1/AC2/AC3/AC5/AC6 — zero behaviour delta. Type-system tightening (`Literal["Boring","Normal","Dramatic"]`) is checker-time only; runtime equality dispatch unchanged.

### Reviewer Deviation Audit (carry-forward)

All previously-stamped deviations remain valid:
- Dev #1 / TEA #2 (typed `PacingHint | None`) — ✓ STILL ACCEPTED. Field type unchanged in rework.
- Dev #2 (per-tier registration) — ✓ STILL ACCEPTED. Wire site unchanged.
- TEA #1 (Late zone) — ✓ STILL ACCEPTED.
- TEA #3 (`observe()` + `pacing_hint()` instead of `tick(round_result)`) — ✓ STILL ACCEPTED.
- Reviewer's OTEL span downgrade-to-MEDIUM with defer-to-42-4 — ✓ STILL VALID. Site unchanged; defer carried in delivery findings.

### Architectural Observations (round 2)

- **`Literal["Boring","Normal","Dramatic"]` is the correct Python approximation of Rust's algebraic enum**. Type-checker now catches typo'd kind constructors at the only sanctioned paths (`TurnClassification.boring()`, `.normal()`, `.dramatic(event)`). The factory methods enforce kind/event coupling structurally — there is no public path that constructs `TurnClassification(kind="Dramatic", event=None)` or vice versa. The defensive `if event is None: raise RuntimeError` in `observe()` is now a `# pragma: no cover`-marked belt-and-braces guard, which is the right Python idiom for "should be impossible but cheap to verify loudly if I'm wrong about that."
- **`@dataclass(frozen=True)` on `_EventSpike`** is the right call for a private value type. No behaviour change (the tracker already replaced spikes whole rather than mutating them); the freeze prevents future drift toward in-place mutation.
- **Removal of `Any` annotations in test helpers** is a minor type-safety win without runtime cost.
- **`@pytest.mark.skipif` decorator** (instead of inline `pytest.skip`) makes the parity-check skip visible in the pytest report — addresses the "no silent fallbacks" concern at the test-discipline level.

### Mismatches in Spec Document Itself

These remain the same drift sources flagged in round 1 spec-check (TEA logged them as conflicts; recommendations unchanged):
- AC2 wording — `tick(round_result)` doesn't exist in Rust; should read `observe(round, killed, lowest_hp_ratio)` + `pacing_hint(thresholds)`. Recommendation **A — Update spec** on next context-doc touch.
- AC3 wording — "Early or Valley" should read `AttentionZone.Late`. Recommendation **A — Update spec**.
- Technical Guardrails — `TurnContext.pacing_hint: str | None` should read `: PacingHint | None`. Recommendation **A — Update spec**.

**Decision:** Proceed to TEA verify. The rework hit every reviewer concern without spec drift; no hand-back needed.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (107/107 tests pass after simplify cleanup)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5 (excluding fixtures/JSON/README)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 medium finding | Pre-existing `_safe_extract_optional` opportunity in `run_narration_turn` lines 1177-1201 — out of 42-3 scope |
| simplify-quality | clean | Verified `register_pacing_section` signature matches the wire-site call; no naming/dead-code/readability issues |
| simplify-efficiency | 6 findings, 1 high-confidence | High-confidence "duplicate `total_damage` summation" finding is **incorrect** — both `classify_round` and `classify_combat_outcome` compute the sum exactly once. Other 5 findings are pre-existing code (NarratorPromptTier class style, run_narration_turn fallbacks) or stylistic preferences (`_approx` vs `pytest.approx`) — out of scope or rejected on merit |

**Applied:** 0 simplify-suggested fixes (all findings dismissed: out-of-scope or incorrect)
**Flagged for Review:** 0 (no medium-confidence in-scope findings)
**Noted:** 6 (logged here for the record; none actionable in 42-3)
**Reverted:** 0

**Overall:** simplify: clean (no actionable in-scope findings)

### Quality-Pass Gate (ruff)

Initial ruff sweep on changed files surfaced 19 findings. Of those, 4 were in the 42-3 diff and were fixed in commit `e7f3aaf`:

| File | Rule | Issue | Fix |
|------|------|-------|-----|
| `tension_tracker.py:44` | F401 | unused `field` import from dataclasses | dropped |
| `tension_tracker.py:520` | SIM102 | nested `if` in `classify_combat_outcome` NearMiss check | collapsed to single `if` with `and` |
| `tension_tracker.py:549` | I001 | `DramaThresholds` import placed at file end with `noqa: E402` | moved to top imports block (over-cautious cycle-safety comment dropped — `sidequest.genre.models.ocean` does not import from `sidequest.game`) |
| `orchestrator.py:28-58` | I001 | new `from sidequest.game.tension_tracker import PacingHint` triggered re-sort of the import block | applied via `ruff check --select I001 --fix` (re-ordered Npc/NpcRegistryEntry, narrative/pack, SPAN_* alphabetically — verified zero regression on `test_orchestrator.py`) |

The remaining 15 ruff findings (F401 unused SPAN imports, F841 unused span var at line 1061, SIM102 at line 631, SIM108 at line 1278, UP037 type-quote strings) are all in **pre-existing** orchestrator code, not in the 42-3 diff. Per minimalist discipline + scope boundaries, those are NOT fixed in this story — they are pre-existing tech debt unrelated to the TensionTracker port.

**Quality Checks (changed files only):** ruff clean on `tension_tracker.py`. ruff has 14 pre-existing findings on `orchestrator.py` (none in 42-3 diff).

**Final Test Status:** 107/107 GREEN
- `test_tension_tracker.py`: 44/44 ✓
- `test_orchestrator_pacing_wiring.py`: 8/8 ✓
- `test_orchestrator.py`: 55/55 ✓ (regression check after ruff's import re-sort)

### Delivery Findings

No new upstream findings during verify. Pre-existing ruff debt in `orchestrator.py` (unused SPAN imports, unused `span` variable in `process_action`, type-annotation quote style) is captured here as a reference for any future tech-debt sweep — not a blocker for 42-3.

**Handoff:** To Reviewer (Chrisjen Avasarala) for adversarial review.

## Design Deviations

No deviations logged yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Reviewer (audit)

Stamping each previously-logged deviation:

- **Dev #1 — `TurnContext.pacing_hint` typed `PacingHint | None`** → ✓ ACCEPTED by Reviewer: typed object preserves `escalation_beat` for the call site. The rationale is sound; the *comment wording* is partially misleading (flagged separately as a HIGH-MEDIUM doc finding) but the type choice itself is correct. Aligns with sibling-story 42-4 ownership work where the typed object is the right hand-off shape.
- **Dev #2 — Pacing section registers on every tier (Full + Delta)** → ✓ ACCEPTED by Reviewer: per-turn dynamic state must reach Delta tier per ADR-066. Rust runs the same per-turn. Wiring test `test_pacing_hint_registers_on_delta_tier` codifies this.
- **TEA #1 — Pacing zone is `Late`, not `Early`/`Valley`** → ✓ ACCEPTED by Reviewer: spot-checked Rust source at `prompt_framework/mod.rs:108` — confirmed `AttentionZone::Late`. Existing Python helper already uses `Late`. Spec drift is in context-story-42-3.md, not code.
- **TEA #2 — `TurnContext.pacing_hint` typed `PacingHint | None`** → ✓ ACCEPTED by Reviewer: same rationale as Dev #1.
- **TEA #3 — `tick(round_result)` AC reads as Rust `observe(...) + pacing_hint(thresholds)`** → ✓ ACCEPTED by Reviewer: Rust source has no `tick(round_result)`; the spec AC2 wording is incorrect. Code follows Rust authority correctly. Spec text should be refreshed but is not a blocker.

### Reviewer (audit) — round 2 stamps on rework deviations

- **Dev rework #1 — `assert max_hp > 0` → `raise ValueError`** → ✓ ACCEPTED by Reviewer (round 2): correct silent-fallback fix per CLAUDE.md. Survives `python -O`; clear domain message.
- **Dev rework #2 — Defensive `assert classification.event is not None` → explicit `RuntimeError` with `# pragma: no cover`** → ✓ ACCEPTED by Reviewer (round 2): right Python idiom for "structurally impossible but I want a loud message if I'm wrong." `# pragma: no cover` correctly excludes the unreachable branch from coverage metrics without weakening the runtime guard.
- **Dev rework #3 — `TurnClassification.kind: Literal["Boring","Normal","Dramatic"]`** → ✓ ACCEPTED by Reviewer (round 2): closest Python approximation to Rust's algebraic enum. The new `TurnClassificationKind` alias is a nice touch — gives the constraint a name future readers can grep for.
- **Dev rework #4 — `_EventSpike` `@dataclass(frozen=True)`** → ✓ ACCEPTED by Reviewer (round 2): zero behaviour change with future-proofing benefit. Tracker already used spike-replacement (not in-place mutation).
- **Dev rework #5 — `TurnContext.pacing_hint` comment rewrite** → ✓ ACCEPTED by Reviewer (round 2): accurate description of the marshalling — field-vs-helper distinction is now explicit.

### Reviewer (audit) — undocumented deviations
- No undocumented deviations found. TEA, Dev, and Architect collectively captured every spec-vs-code gap in the deviation log. The Reviewer findings above are about code quality (silent fallbacks, type-design hardening, vacuous tests) rather than spec drift.

### TEA (verify)
- No deviations from spec during verify phase. Simplify fan-out produced no actionable in-scope findings; ruff fixes were mechanical and within the 42-3 diff. The "cycle-safety placement" comment Dev added on the `DramaThresholds` import was over-cautious and was removed — this is not a deviation from spec, just a cleanup.

### Dev (rework round 2 — post-review)
- No new spec deviations introduced during rework. All 11 reviewer findings addressed without changing the AC contract or test scenarios. The `Literal["Boring","Normal","Dramatic"]` tightening on `TurnClassification.kind` is a type-system improvement that aligns *more* closely with Rust's algebraic enum (Rust enforces variant exhaustiveness; the Literal approximates it). The defensive `assert` removals are silent-fallback hygiene per CLAUDE.md, not behavior changes.

### Dev (implementation)
- **`TurnContext.pacing_hint` typed `PacingHint | None` (not `str | None`)**
  - Spec source: context-story-42-3.md, Technical Guardrails / AC3
  - Spec text: "add `TurnContext.pacing_hint: str | None`"
  - Implementation: Field declared as `pacing_hint: PacingHint | None = None` in `TurnContext`. The wire site at `Orchestrator.build_narrator_prompt` calls `registry.register_pacing_section(agent_name, hint.narrator_directive(), hint.escalation_beat)`.
  - Rationale: A bare string field would discard `escalation_beat` and force callers to pre-render the directive — losing the structure that 42-4's snapshot persistence and any downstream music-director consumer will need. Rust passes `&PacingHint` to the equivalent register helper; the typed Python field is the closer parity. TEA's RED-phase tests already encoded this contract.
  - Severity: minor
  - Forward impact: 42-4 dispatch ownership work passes the tracker-produced object directly; matches Rust hand-off shape.
- **PacingHint section registers on every tier (Full + Delta), not Full-only**
  - Spec source: context-story-42-3.md (no explicit tier guidance) + Epic 42 Cross-Epic note that combat can start mid-session
  - Spec text: silent on tier
  - Implementation: The pacing register call in `build_narrator_prompt` lives outside the `if is_full:` blocks — it runs every turn so per-turn dynamic state reaches Delta-tier resumed sessions per ADR-066.
  - Rationale: Combat can start mid-session, and PacingHint changes per-turn by definition; gating it to Full would silently strip pacing once a Claude session is established. TEA's `test_pacing_hint_registers_on_delta_tier` codifies this requirement.
  - Severity: minor (clarification, not departure — Rust runs the same per-turn)
  - Forward impact: none

### TEA (test design)
- **PacingHint narrator zone is `Late`, not `Early`/`Valley`**
  - Spec source: context-story-42-3.md, Technical Guardrails ("register Early-zone `pacing_hint` section") and AC3 ("Early or Valley")
  - Spec text: "register Early-zone `pacing_hint` section (match Rust placement)"
  - Implementation: Tests assert section uses `AttentionZone.Late` (matches Rust at `sidequest-api/crates/sidequest-agents/src/prompt_framework/mod.rs:108`) and section name `"pacing"` (not `"pacing_hint"`).
  - Rationale: Story scope explicitly says "if Rust places it in Valley, follow Rust"; recon confirmed Rust source places the pacing section in `AttentionZone::Late` with section name `"pacing"`. Existing Python helper `register_pacing_section` in `sidequest/agents/prompt_framework/core.py:140` already uses `Late` + `"pacing"` — Python was already Rust-correct before this story; the story scope text is the drift.
  - Severity: minor
  - Forward impact: none — wires through existing `register_pacing_section` helper unchanged
- **`TurnContext.pacing_hint` typed as `PacingHint | None`, not `str | None`**
  - Spec source: context-story-42-3.md, Technical Guardrails ("add `TurnContext.pacing_hint: str | None`")
  - Spec text: "add `TurnContext.pacing_hint: str | None`"
  - Implementation: Tests construct `TurnContext(pacing_hint=PacingHint(...))`, expecting the typed object. The wire site calls `registry.register_pacing_section(agent, hint.narrator_directive(), hint.escalation_beat)`.
  - Rationale: A `str | None` field would lose `escalation_beat` and force callers to pre-render the directive. Rust passes `&PacingHint` to `register_pacing_section`; the typed Python field is the closer parity. The existing Python `register_pacing_section` already takes both `narrator_directive` and `escalation_beat` separately — a typed `PacingHint` field is the cleanest source.
  - Severity: minor
  - Forward impact: 42-4 dispatch ownership work passes the tracker-produced object directly; no string-marshalling layer needed
- **`tick(round_result)` AC reads as Rust `observe(round, killed, lowest_hp_ratio)` + `pacing_hint(thresholds)` two-call sequence**
  - Spec source: context-story-42-3.md, AC2 ("`TensionTracker.tick(round_result)` produces Rust-parity `PacingHint`")
  - Spec text: "`TensionTracker.tick(round_result)` produces Rust-parity `PacingHint`"
  - Implementation: Tests call `tracker.observe(round, killed, lowest_hp_ratio)` to advance state and `tracker.pacing_hint(thresholds)` to read the hint — matching the Rust API. There is no `tick(round_result)` method in Rust source (`tick(&mut self)` exists with no args, decays action_tension and ages spike).
  - Rationale: Spec text describes the *intent* (per-round pacing-hint update) but uses the wrong method name. Rust source is authority. Per spec authority hierarchy, story scope wins over context-doc text — story scope says "TensionTracker state machine + all methods" (whatever Rust has). Multi-round scenario fixtures encode `[observe → pacing_hint]` per round.
  - Severity: minor
  - Forward impact: caller code in 42-4 invokes both methods, not a single `tick(...)`

## Sm Assessment

Story 42-3 is the third in Epic 42 (ADR-082 Phase 3 combat port). Stack parent 42-2 (ResourcePool + threshold-lore minting) merged to develop on commit 6e09cb0 — clean ground for 42-3.

**Scope is well-bounded:** port `tension_tracker.rs` (803 LOC) types, state machine, and two free functions to Python; wire `PacingHint` into the narrator orchestrator's Early/Valley zone in parity with Rust. Fixture-driven Rust-parity testing is the verification spine — six ACs spell out the parity bar (classification, multi-round tick output, narrator-zone placement, genre-pack-sourced thresholds, 1:1 test mapping, scriptable fixture regen).

**Known constraints / non-scope:**
- Ownership of `TensionTracker` instances (session vs encounter vs connection) is explicitly 42-4 scope
- Snapshot persistence of pacing hint is 42-4 scope
- Music director integration is out of scope (Python music director not ported)
- AC4 depends on `sidequest/genre/models/drama_thresholds.py` already existing — TEA must confirm in red phase before writing the threshold-shift test

**Workflow:** TDD, phased. Routing TEA (Amos) to red phase to author the failing fixture-parity suite. The `cargo run --example tension_fixture_export` step in AC6 should be wired during red so green has stable JSON to chase.

**Repos:** sidequest-server only. Branch `feat/42-3-tension-pacing-classify-port` cut from develop.

**Risk callout:** AC1 edge case (`killed = None` vs `killed = ""`) is a serde-vs-Python distinction that is easy to gloss over — Amos should encode this explicitly in the fixture set, not just as a code comment.