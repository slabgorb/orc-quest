# Story 15-7 Session

**Story:** Wire RAG pipeline end-to-end — accumulate_lore from turns, generate embeddings via daemon, switch to semantic retrieval
**Epic:** 15 — Playtest Debt Cleanup
**Points:** 8
**Priority:** p0
**Status:** in_progress
**Workflow:** tdd
**Phase:** finish
**Repos:** api, daemon
**Branch:** feat/15-7-wire-rag-pipeline

## Description

Three broken links in the RAG pipeline:

1. **accumulate_lore() never called** — `lore_established` on `WorldStatePatch` is populated by the orchestrator but never read back in dispatch to call `accumulate_lore()`, so the lore store never grows past its initial genre-pack seed.

2. **No embedding generation** — `LoreFragment` supports optional embedding vectors and `query_by_similarity()` does cosine similarity search, but no `/embed` endpoint exists in the daemon, and no Rust code calls one.

3. **Semantic search is dead code** — `select_lore_for_prompt()` falls back to keyword substring matching because no fragments have embeddings.

## Acceptance Criteria

- [ ] `accumulate_lore()` called in post-narration dispatch when `lore_established` is present on `WorldStatePatch`
- [ ] `/embed` endpoint added to sidequest-daemon
- [ ] Rust daemon-client calls `/embed` when creating new lore fragments
- [ ] `select_lore_for_prompt()` prefers `query_by_similarity()` when embeddings available
- [ ] OTEL: `lore.fragment_accumulated` (category, turn, token_estimate)
- [ ] OTEL: `lore.embedding_generated` (fragment_id, latency_ms, model)
- [ ] OTEL: `lore.semantic_retrieval` (query_hint, top_k_scores, fallback_to_keyword)

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **Fixed flawed test assertion for cosine_similarity_orthogonal**
  - Spec source: TEA test rag_pipeline_story_15_7_tests.rs
  - Spec text: "Orthogonal-ish vectors should have low similarity"
  - Implementation: Replaced sin-based vector generation (which produced correlated vectors, sim=0.86) with actually orthogonal vectors (even/odd index partitioning, sim=0.0)
  - Rationale: Test was asserting `< 0.5` but make_embedding(0.0, 384) and make_embedding(100.0, 384) are not orthogonal. Test infrastructure was wrong, not the function under test.
  - Severity: minor
  - Forward impact: none

### Architect (reconcile)
- **AC-3 deviation RESOLVED** — Dev wired `embed().await` in `dispatch_player_action` (async context). No remaining async gap. The previous deviation entry has been updated to RESOLVED by Dev.
- **Test fix deviation** — Verified accurate. Minor, no forward impact.
- No additional deviations found. All 7 ACs fully wired end-to-end.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 8-point story with 7 ACs spanning 3 crates and 2 repos

**Test Files:**
- `sidequest-api/crates/sidequest-game/tests/rag_pipeline_story_15_7_tests.rs` — semantic search preference, accumulate_lore metadata, cosine similarity
- `sidequest-api/crates/sidequest-daemon-client/tests/embed_story_15_7_tests.rs` — EmbedParams/EmbedResult types, request envelope, OTEL fields
- `sidequest-api/crates/sidequest-server/tests/rag_wiring_story_15_7_tests.rs` — ActionResult.lore_established field
- `sidequest-daemon/tests/test_embed_story_15_7.py` — EMBED_TIERS routing, EmbedWorker class, empty text rejection, response format

**Tests Written:** 18 tests covering 7 ACs
**Status:** RED (failing — ready for Dev)

### AC Coverage

| AC | Test(s) | Status |
|----|---------|--------|
| AC-1: accumulate_lore called | `action_result_has_lore_established_field`, `accumulate_lore_sets_turn_and_category_for_otel` | failing |
| AC-2: /embed endpoint | `test_embed_tier_constant_exists`, `test_embed_worker_class_exists`, `test_embed_request_*` | failing |
| AC-3: Rust daemon-client calls /embed | `embed_params_*`, `embed_result_*`, `embed_request_builds_correct_envelope` | failing |
| AC-4: select_lore_for_prompt prefers semantic | `select_lore_prefers_semantic_when_embeddings_available`, `select_lore_falls_back_to_keyword_when_no_embeddings`, `select_lore_accepts_query_embedding_parameter` | failing |
| AC-5: OTEL lore.fragment_accumulated | `accumulate_lore_sets_turn_and_category_for_otel` | failing |
| AC-6: OTEL lore.embedding_generated | `embed_result_has_model_for_otel` | failing |
| AC-7: OTEL lore.semantic_retrieval | Covered by `select_lore_prefers_semantic_when_embeddings_available` (tests the retrieval path that should emit the event) | failing |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | LoreCategory and LoreSource already have it (verified by reading source) | n/a |
| #5 validated constructors | `accumulate_lore_rejects_empty_description` | failing |
| #6 test quality | Self-check: all 18 tests have meaningful assertions, no vacuous tests | pass |
| #8 Deserialize bypass | `embed_result_deserializes_from_daemon_response` tests serde round-trip | failing |

**Rules checked:** 4 of 15 applicable lang-review rules have test coverage (remaining rules not applicable to new types in this story)
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Yoda) for implementation

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): `LoreStore` has no `get(id)` method for retrieving a single fragment by ID. Tests work around this using `query_by_category()`, but Dev may want to add `get()` for the dispatch wiring. Affects `crates/sidequest-game/src/lore.rs` (LoreStore impl). *Found by TEA during test design.*
- **Gap** (non-blocking): `ActionResult` in `sidequest-agents` does not currently carry `lore_established`. The world_patch's `lore_established` field exists on `WorldStatePatch` in both `sidequest-game/state.rs` and `sidequest-agents/patches.rs`, but it's never extracted during dispatch. Dev needs to either add `lore_established: Option<Vec<String>>` to `ActionResult` or extract it from the existing `WorldStatePatch`. Affects `crates/sidequest-agents/src/orchestrator.rs` (ActionResult struct). *Found by TEA during test design.*
- **Gap** (non-blocking): `sentence-transformers` is not in `sidequest-daemon/pyproject.toml` dependencies. Dev must add it for the embed worker. Affects `sidequest-daemon/pyproject.toml`. *Found by TEA during test design.*

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-api/crates/sidequest-game/src/lore.rs` — Added `query_embedding` parameter to `select_lore_for_prompt()`, semantic ranking, `fragments_with_embeddings_count()`
- `sidequest-api/crates/sidequest-daemon-client/src/types.rs` — Added `EmbedParams` and `EmbedResult` types
- `sidequest-api/crates/sidequest-daemon-client/src/client.rs` — Added `embed()` method with OTEL tracing
- `sidequest-api/crates/sidequest-agents/src/orchestrator.rs` — Added `lore_established` to `ActionResult`, `NarratorExtraction`, `NarratorStructuredBlock`; wired through all extraction strategies
- `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` — Made `lore_store` mutable in `DispatchContext`; call `accumulate_lore()` when `lore_established` present; emit `lore.fragment_accumulated` WatcherEvent (AC-1, AC-5)
- `sidequest-api/crates/sidequest-server/src/dispatch/prompt.rs` — Updated `select_lore_for_prompt` to 4-arg form; emit `lore.semantic_retrieval` WatcherEvent (AC-7)
- `sidequest-daemon/sidequest_daemon/media/daemon.py` — Added `EmbedWorker` class, `EMBED_TIERS`, `elif method == "embed"` handler routing (AC-2)
- `sidequest-daemon/pyproject.toml` — Added `sentence-transformers>=2.2` dependency
- Updated 3 existing test files for new `lore_established` field and 4-arg `select_lore_for_prompt`

**Tests:** 25/25 passing (GREEN) — 16 Rust + 9 Python
**Branch:** feat/15-7-wire-rag-pipeline (pushed in both repos)

**Handoff:** To next phase

### Dev (implementation)
- **AC-3 RESOLVED:** embed() now called in dispatch_player_action (async) after accumulate_lore(). Embedding attached via LoreStore::set_embedding(). Query embedding generated in prompt assembly from location hint. No remaining wiring gaps.

## Architect Assessment (spec-check) — Round 1

**Decision:** Handed back to Dev — 4 wiring gaps found. See round 2 below.

## Architect Assessment (spec-check) — Round 2

**Spec Alignment:** Aligned (with one logged deviation)
**Mismatches Found:** 0 remaining

**Resolved since round 1:**
- AC-1: `accumulate_lore()` now called in `dispatch/mod.rs` after state mutations — ✅
- AC-2: Daemon `_handle_client()` now routes `embed` method to `EmbedWorker` — ✅
- AC-5: `lore.fragment_accumulated` WatcherEvent emitted with category/turn/token_estimate — ✅
- AC-7: `lore.semantic_retrieval` WatcherEvent emitted in prompt assembly with fallback_to_keyword flag — ✅

**Accepted deviations:**
- AC-3 (embed call from dispatch): Dev logged deviation — sync `apply_state_mutations` cannot call async daemon `embed()`. The `DaemonClient::embed()` method and daemon handler are fully wired; the async bridge is the gap. Fragments accumulate without embeddings. Deviation severity correctly assessed as minor — semantic search degrades gracefully to keyword fallback.
- AC-6 (OTEL `lore.embedding_generated`): Follows from AC-3 — since embed is not called from dispatch, the OTEL event has no emission site. Will activate when the async bridge is added.

**Decision:** Proceed to verify

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 7

| Teammate | Status | Findings |
|----------|--------|---------|
| simplify-reuse | 6 findings | 1 story-specific (daemon-client deserialize pattern), 5 pre-existing |
| simplify-quality | 7 findings | 2 known deviations (AC-3/AC-6), 2 pre-existing, 1 already-handled, 2 minor completeness |
| simplify-efficiency | 6 findings | 1 story-specific (EmbedWorker per-request), 5 pre-existing |

**Applied:** 0 high-confidence fixes (none warranted — findings are either pre-existing, known deviations, or minor scope creep)
**Flagged for Review:** 3 medium-confidence findings
  - EmbedWorker instantiated per-request instead of via WorkerPool (daemon.py:317)
  - WorkerPool.status() omits embed worker (daemon.py:147)
  - DaemonClient 3 methods share identical deserialize pattern (client.rs:166)
**Noted:** 9 low-confidence observations (all pre-existing patterns)
**Reverted:** 0

**Overall:** simplify: clean (no auto-applied changes)

**Quality Checks:** All passing (cargo test, cargo build — no failures)
**Handoff:** To Obi-Wan Kenobi for code review

## Delivery Findings

### TEA (test verification)
- **Improvement** (non-blocking): EmbedWorker is instantiated fresh per embed request in daemon.py:317. Should be managed by WorkerPool like other workers (flux, tts, acestep) for model reuse. Affects `sidequest-daemon/sidequest_daemon/media/daemon.py` (WorkerPool class). *Found by TEA during test verification.*

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | Full diff data gathered, no structural issues | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 9 findings: per-request EmbedWorker (high), dimension mismatch silent (medium), zero-magnitude query (medium) | confirmed 1 (EmbedWorker), dismissed 6 (pre-existing or low-risk edge cases), deferred 2 (dimension/magnitude — single model, not reachable now) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 findings: embed() zero callers (high), query_embedding always None (high), no embedding generation (high), observability gap (medium) | confirmed 0, dismissed 4 (all known AC-3 deviation, accepted by Architect) |
| 4 | reviewer-rule-checker | Yes | clean | 15/15 rules pass, 0 violations across 32 instances | N/A |
| 5 | reviewer-test-analyzer | Yes | findings | 14 findings: tautological tests (high x3), missing integration tests (high x3), missing edge cases (medium x4), low-priority (x4) | confirmed 0, dismissed 14 (structural tests valid for RED phase — verify wiring exists, not behavior) |
| 6 | reviewer-comment-analyzer | Yes | findings | 2 findings: misleading "world_patch" docstring (high), missing _load_model docstring (medium) | confirmed 1 (misleading docstring), dismissed 1 (private method doc not required) |
| 7 | reviewer-type-design | Yes | findings | 6 findings: semantic search never activated (high), OTEL false positive (high), runtime lore no embeddings (high), stringly-typed (medium x2), no lore validation (medium) | confirmed 0, dismissed 6 (all consequences of known AC-3 deviation — semantic search deferred) |
| 8 | reviewer-security | Yes | findings | 1 finding: CWE-209 info leakage in embed error response (medium) | dismissed 1 (daemon is Unix socket sidecar, not exposed to untrusted clients — follows existing pattern) |
| 9 | reviewer-simplifier | Yes | findings | 5 findings: EmbedWorker per-request (high), double empty-text check (high), dead semantic path (medium x2), verbose timing (low) | confirmed 0, dismissed 3 (pre-existing patterns or deferred scope), deferred 2 (EmbedWorker pooling + double validation — minor, non-blocking) |

All received: Yes

## Reviewer Assessment

**Verdict:** BLOCKED — 1 blocking finding, 2 non-blocking

### Blocking

1. **AC-6: `lore.embedding_generated` OTEL WatcherEvent never written** (Missing code)
   - AC-6 requires a WatcherEvent with fields `fragment_id`, `latency_ms`, `model`.
   - The `DaemonClient::embed()` method has a basic `tracing::info_span` but no WatcherEvent emission. The Architect accepted this as "follows from AC-3" but that's wrong — the emission code should exist inside `embed()` so that when the method IS called (now or later), the OTEL event fires. The event code is independent of whether dispatch calls embed() today.
   - **Fix:** Add `lore.embedding_generated` WatcherEvent emission inside `DaemonClient::embed()` after successful deserialization. Fields: `fragment_id` (from caller context — pass as param or emit at call site), `latency_ms` (from `EmbedResult`), `model` (from `EmbedResult`).
   - Note: Since `DaemonClient` doesn't have access to `AppState::send_watcher_event`, the tracing::info! approach is acceptable here — the GM panel reads tracing spans too. But the event name and fields must match the AC.

### Non-blocking

2. **Misleading docstring on lore_established field** (Comment)
   - `orchestrator.rs:68` says "Extracted from the narrator's world_patch" but `lore_established` comes directly from `NarratorStructuredBlock` (the fenced JSON), not from a separate world_patch. Fix: "Extracted from narrator structured JSON block."

3. **EmbedWorker per-request instantiation** (Efficiency)
   - `EmbedWorker()` is created fresh on every `embed` request in `daemon.py:317`. The model lazy-loads so it survives within a single request, but the worker object is discarded and recreated next time. Should be managed by `WorkerPool` like flux/tts/acestep workers.
   - Not blocking because the sentence-transformers library caches the model weights internally.

4. **Embedding dimension mismatch silent degradation** (Edge case)
   - `select_lore_for_prompt` with a query embedding of different dimensionality than stored fragment embeddings will get `cosine_similarity` returning 0.0 for mismatched lengths, silently falling back to effectively random ordering.
   - Not blocking because all embeddings come from the same model (all-MiniLM-L6-v2, 384-dim).

### Rule Compliance [RULE]
- 15/15 Rust lang-review rules pass. No violations.

### Silent Failure Analysis [SILENT]
- 4 findings from silent-failure-hunter, all confirmed as known AC-3 deviation (embed() not called from dispatch). Accepted by Architect. No NEW silent failures introduced.

### Re-review (round 2)
- Blocking #1 resolved: `lore.embedding_generated` tracing::info! emitted in `DaemonClient::embed()` with `latency_ms`, `model`, `embedding_dim`. `fragment_id` deferred to call site.
- Non-blocking #2 resolved: docstring corrected.
- Non-blocking #3, #4 remain — deferred.

### Re-review (round 3)
- AC-3 wired: `embed().await` called in dispatch loop, embedding attached via `LoreStore::set_embedding()` — verified in diff
- AC-6 wired: `lore.embedding_generated` WatcherEvent with `fragment_id`, `latency_ms`, `model` emitted at call site — verified in diff
- AC-4 completed: query embedding generated from location hint, passed to `select_lore_for_prompt` — semantic search is live
- Error paths: daemon connect failure and embed failure both log loudly with `tracing::warn!`, no silent fallbacks
- Previous AC-3 deviation entry updated to RESOLVED by Dev

### Decision
**APPROVED.** All ACs wired end-to-end. No half-wired features. Proceed to spec-reconcile.