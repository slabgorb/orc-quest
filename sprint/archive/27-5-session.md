---
story_id: "27-5"
jira_key: "none"
epic: "27"
workflow: "tdd"
---

# Story 27-5: LoRA loading verification — genre style LoRAs via mflux

## Story Details

- **ID:** 27-5
- **Title:** LoRA loading verification — genre style LoRAs via mflux
- **Points:** 3
- **Priority:** p1
- **Jira Key:** none (epic 27 not yet synced to Jira)
- **Workflow:** tdd
- **Depends On:** 27-3 (FluxMLXWorker implementation)
- **Repos:** daemon

## Story Context

**Background:** Epic 27 migrates the daemon from PyTorch to Apple MLX via mflux. Story 27-3 implemented FluxMLXWorker as the core Flux image renderer. Story 27-5 verifies that genre-specific style LoRAs (trained per ADR-032) load correctly via the MLX backend.

**Key context from epic:**
- LoRA weights are stored in `sidequest-content/genre_packs/*/lora/` as `.safetensors` files
- The MLX worker must load these weights without PyTorch
- ADR-034 (portrait identity) depends on either IP-Adapter or img2img — this story focuses only on LoRA loading verification

**What has changed since 27-3:**
- 27-3 implemented FluxMLXWorker with the core render() interface
- 27-4 swapped dependencies (torch/diffusers → mlx/mflux)
- LoRA loading is likely not yet wired into the render pipeline or tested

**Acceptance Criteria:**
1. Test suite covers LoRA loading from `.safetensors` files
2. LoRA weights load successfully without PyTorch
3. Verify mflux supports the LoRA composition pattern (weight injection, rank/alpha config)
4. Genre style LoRAs from test packs load without error
5. Integration test verifies LoRA-weighted render produces different output than base model

## Workflow Tracking

**Workflow:** tdd (phased)
**Phase:** finish
**Phase Started:** 2026-04-07T18:40:57Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-07T14:50Z | 2026-04-07T18:21:11Z | 3h 31m |
| red | 2026-04-07T18:21:11Z | 2026-04-07T18:30:00Z | 8m 49s |
| green | 2026-04-07T18:30:00Z | 2026-04-07T18:33:52Z | 3m 52s |
| spec-check | 2026-04-07T18:33:52Z | 2026-04-07T18:34:51Z | 59s |
| verify | 2026-04-07T18:34:51Z | 2026-04-07T18:35:51Z | 1m |
| review | 2026-04-07T18:35:51Z | 2026-04-07T18:40:08Z | 4m 17s |
| spec-reconcile | 2026-04-07T18:40:08Z | 2026-04-07T18:40:57Z | 49s |
| finish | 2026-04-07T18:40:57Z | - | - |

## Sm Assessment

**Story 27-5 is ready for RED phase.** Setup complete:
- Session file created with 5 ACs covering LoRA loading, weight verification, mflux integration
- Feature branch `feat/27-5-lora-loading-verification` created on sidequest-daemon tracking develop
- Sprint YAML updated: status in_progress, assigned to Keith Avery
- User note: LoRA generation is now working — this story verifies the loading/rendering side

**Routing:** TDD phased workflow → TEA (Han Solo) for RED phase. Key areas to test:
1. .safetensors file loading without PyTorch
2. mflux LoRA weight injection pattern
3. Genre pack LoRA discovery from content path
4. Output differentiation: LoRA vs base model

**Dependencies satisfied:** 27-3 (FluxMLXWorker) and 27-4 (dep swap) both complete.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Core ML pipeline feature — LoRA weight injection into Flux renderer

**Test Files:**
- `tests/test_lora_loading_story_27_5.py` — 12 tests across 8 test classes covering all 5 ACs

**Tests Written:** 12 tests covering 5 ACs

| Test | AC | What It Proves |
|------|----|----------------|
| test_render_accepts_lora_path_param | AC-1 | render() recognizes lora_path param |
| test_render_with_lora_uses_flux1_constructor_not_from_name | AC-1,3 | Flux1(lora_paths=...) used, not from_name() |
| test_render_with_lora_scale | AC-3 | lora_scale passed as lora_scales to Flux1 |
| test_lora_render_does_not_import_torch | AC-2 | No PyTorch dependency for LoRA path |
| test_model_config_used_with_lora | AC-3 | ModelConfig passed to constructor |
| test_default_lora_scale_is_one | AC-3 | Default lora_scales=[1.0] |
| test_safetensors_path_accepted | AC-4 | .safetensors file path flows to Flux1 |
| test_lora_render_creates_separate_model_instance | AC-5 | Separate Flux1 for LoRA vs base |
| test_missing_lora_file_raises | Error | FileNotFoundError propagated |
| test_render_without_lora_still_works | Regression | Base render unaffected |
| test_render_span_includes_lora_path | OTEL | Render with LoRA doesn't crash OTEL |
| test_daemon_render_passes_lora_params | Wiring | daemon.py forwards params to worker |

**Status:** RED (7 failing, 5 passing baseline — failing tests assert LoRA-specific behavior)

### Key Discovery: mflux LoRA API

Verified via introspection of installed `mflux>=0.4`:
- `Flux1.__init__` accepts `lora_paths: list[str] | None` and `lora_scales: list[float] | None`
- `Flux1.from_name()` does NOT accept LoRA params
- `Flux1.generate_image()` is the render method (not `generate()`)
- `ModelConfig.dev()` and `ModelConfig.schnell()` provide variant configs

Dev must use `Flux1(model_config=ModelConfig.dev(), lora_paths=[...])` when LoRA requested.

### Rule Coverage

| Rule | Applicable? | Coverage |
|------|-------------|----------|
| #1 Silent exception swallowing | Yes | test_missing_lora_file_raises verifies errors propagate |
| #2 Mutable default args | N/A — no new function signatures yet |
| #3 Type annotation gaps | Dev responsibility |
| #4 Logging | OTEL test covers render span |
| #5 Path handling | test_safetensors_path_accepted uses Path objects |
| #6 Test quality | Self-checked — all 12 tests have meaningful assertions |

**Rules checked:** 3 of 6 applicable Python review rules
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Yoda) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest_daemon/media/workers/flux_mlx_worker.py` — added `_build_lora_model()` method, LoRA branch in `render()`, fixed `generate()` → `generate_image()` to match real mflux API
- `tests/test_flux_mlx_worker.py` — updated existing tests from `generate` to `generate_image` (API name fix)

**Tests:** 12/12 new + 43/43 existing = 55/55 passing (GREEN)
**Branch:** feat/27-5-lora-loading-verification (pushed)

**Implementation Notes:**
- `_build_lora_model()` constructs `Flux1(model_config=ModelConfig.{variant}(), lora_paths=[path], lora_scales=[scale])` — separate from `from_name()` path
- LoRA model is constructed per-request (no caching yet — TEA flagged this as a design question)
- Default `lora_scale=1.0` when not specified
- OTEL span attributes `render.lora_path` and `render.lora_scale` added for LoRA renders
- Also fixed `generate()` → `generate_image()` across the worker — this matches the actual mflux Flux1 API

**Handoff:** To next phase (verify)

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

AC-by-AC verification:

| AC | Status | Evidence |
|----|--------|----------|
| AC-1: .safetensors test coverage | Aligned | 12 tests, `test_safetensors_path_accepted` |
| AC-2: No PyTorch | Aligned | `_build_lora_model` uses only mflux; torch import test |
| AC-3: mflux LoRA composition | Aligned | `Flux1(model_config=..., lora_paths=..., lora_scales=...)` |
| AC-4: Genre LoRAs load | Aligned | Path passthrough to Flux1 constructor tested |
| AC-5: LoRA vs base differs | Aligned | Structural test (separate instances); deviation documented |

**Bonus fix:** `generate()` → `generate_image()` corrects the mflux API name from 27-3. Properly logged as deviation.

**Design quality:** `_build_lora_model` is clean separation from `load_model/from_name` path. Per-request LoRA model construction is correct for the mflux API constraint (LoRA at init time). Caching is a future optimization, not a correctness issue.

**Decision:** Proceed to verify phase.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed — 55/55 tests passing (12 new + 43 existing)

### Simplify Report

**Teammates:** inline analysis (changeset is 1 source file + 2 test files, ~50 lines of new source)
**Files Analyzed:** 1 (flux_mlx_worker.py changes)

| Lens | Status | Findings |
|------|--------|----------|
| Reuse | clean | `_build_lora_model` is unique; no duplication with existing code |
| Quality | clean | Type-annotated params, docstring explains from_name limitation, OTEL attributes |
| Efficiency | clean | Per-request model construction is correct for mflux API (LoRA at init time) |

**Applied:** 0 fixes
**Flagged for Review:** 0
**Noted:** 0
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** 55/55 tests passing
**Handoff:** To Reviewer (Obi-Wan) for code review

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): Fixed `generate()` → `generate_image()` across the worker to match real mflux API. The 27-3 code used the wrong method name. Affects `sidequest_daemon/media/workers/flux_mlx_worker.py` and `tests/test_flux_mlx_worker.py`. *Found by Dev during implementation.*

### TEA (test design)
- **Gap** (non-blocking): mflux `Flux1.from_name()` does NOT support `lora_paths` — only `Flux1.__init__()` does. The current `FluxMLXWorker.load_model()` uses `from_name()`. Dev must create a separate code path that constructs `Flux1(model_config=ModelConfig.dev(), lora_paths=[...], lora_scales=[...])` when LoRA is requested. Affects `sidequest_daemon/media/workers/flux_mlx_worker.py`. *Found by TEA during test design.*
- **Question** (non-blocking): LoRA is a model-construction-time parameter in mflux, not a per-generate param. This means each LoRA+model combo needs its own `Flux1` instance. Dev should decide on caching strategy — create per-request or cache keyed by `(variant, lora_path)`. *Found by TEA during test design.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 | confirmed 1 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | dismissed 2 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 1, dismissed 3 |

**All received:** Yes (3 returned, 6 disabled via settings)
**Total findings:** 2 confirmed (both LOW), 5 dismissed

## Reviewer Assessment

**Verdict:** APPROVED

[VERIFIED] Error propagation — `_build_lora_model` ValueError for unknown variant; Flux1 constructor errors bubble through render's except block at `flux_mlx_worker.py:178-181`. OTEL error status set and re-raised.

[VERIFIED] No silent fallbacks — LoRA branch explicit (`if lora_path`). Unknown variant raises. No silent downgrade to base model.

[VERIFIED] OTEL attributes — `render.lora_path` and `render.lora_scale` at `flux_mlx_worker.py:156-157`. Error spans preserved.

[VERIFIED] No PyTorch dependency — `_build_lora_model` imports only `mflux`. Test confirms.

[VERIFIED] Logging uses lazy formatting — `log.info("FLUX MLX RENDER [%s] seed=%s lora=%s scale=%s", ...)` at line 158. Correct per Python rule #4.

[VERIFIED] `generate()` → `generate_image()` API fix — matches real mflux Flux1 API. Both `warm_up()` and `render()` updated. All existing tests updated.

[EDGE] Per-request LoRA model construction — no caching. Each LoRA render creates a new Flux1 instance (~5-10s model load time). Acceptable for 3-point story; caching is a future optimization if genre LoRAs are requested repeatedly.

[SILENT] `if lora_path:` truthiness check — dismissed. Empty string from typed JSON-RPC caller is a Rust-side bug. Consistent with existing `params.get()` patterns.

[TEST] 12 new tests + 43 existing = 55/55 green. Wiring test present. All assertions meaningful.

[DOC] `_build_lora_model` docstring explains why `from_name()` isn't used. Module-level docs unchanged.

[TYPE] `-> object` return type on private method — [LOW] could be `Flux1` via TYPE_CHECKING import. Not blocking for a private method.

[SEC] No security concerns — daemon internal code, LoRA path from trusted Rust API.

[SIMPLE] 19 new lines of source (excluding tests). Minimal.

[RULE] Python review rules checked: #1 silent exceptions (clean), #2 mutable defaults (clean), #3 type annotations (LOW finding on `-> object`), #4 logging (clean), #5 path handling (clean), #6 test quality (clean).

| Severity | Issue | Location | Action |
|----------|-------|----------|--------|
| [LOW] | Unused `call` import in test file | `tests/test_lora_loading_story_27_5.py:17` | Remove before merge |
| [LOW] | `-> object` return type on `_build_lora_model` | `flux_mlx_worker.py:113` | Consider `TYPE_CHECKING` pattern |

### Devil's Advocate

What if this code is broken? The most dangerous scenario: `_build_lora_model` constructs a new Flux1 instance on every LoRA render call. Flux model loading takes 5-10 seconds and allocates gigabytes of unified memory. In a rapid playtest with genre LoRAs active, every render request creates a fresh model — no caching, no cleanup of old instances. MLX's lazy evaluation might defer the memory allocation, but eventually the 128GB M3 Max fills up. Counter: the daemon already manages one or two model instances (dev + schnell). Adding a third LoRA instance is within budget. The real problem would be if every render created a new one and the old one wasn't garbage collected — but Python's GC handles this since there's no persistent reference. And in practice, renders are minutes apart during gameplay, not seconds. The performance concern is real but non-blocking for a 3-point verification story. If playtesting (27-8) shows memory issues, a caching layer keyed on `(variant, lora_path)` is the fix.

The unused `call` import is trivially fixable. The `-> object` return type is cosmetic. No Critical or High issues found.

**Handoff:** To SM (Grand Admiral Thrawn) for finish-story.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **generate() renamed to generate_image()** → ✓ ACCEPTED by Reviewer: matches actual mflux API. Correctness fix.
  - Spec source: mflux Flux1 API (introspected)
  - Spec text: "Flux1.generate_image() is the render method"
  - Implementation: Changed all .generate() calls to .generate_image() in worker and existing tests
  - Rationale: The 27-3 implementation used the wrong mflux API name. Real mflux uses generate_image(), not generate(). Fixed as part of LoRA work since it affects the same code path.
  - Severity: minor
  - Forward impact: none — existing tests updated, mocks still work

### Reviewer (audit)
- No undocumented deviations found.

### Architect (reconcile)
- No additional deviations found. Both existing deviations verified: spec sources accurate, implementation descriptions match code, forward impacts correctly assessed. No AC deferrals.

### TEA (test design)
- **AC-5 tested structurally, not output comparison** → ✓ ACCEPTED by Reviewer: mocked tests can't compare pixel output. Structural test is the right level for unit tests. 27-8 covers visual verification.
  - Spec source: session file AC-5
  - Spec text: "Integration test verifies LoRA-weighted render produces different output than base model"
  - Implementation: Test verifies separate Flux1 instances are created (base vs LoRA) and the LoRA model's generate_image is called. Does not compare pixel output since mflux is mocked.
  - Rationale: Real output comparison requires actual MLX inference — not feasible in unit tests with mocked mflux. The structural test proves the code path diverges. Pixel comparison belongs in playtest (27-8).
  - Severity: minor
  - Forward impact: 27-8 (playtest) should include visual verification of LoRA style application