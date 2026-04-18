---
story_id: "20-1"
epic: "20"
workflow: "tdd"
repos: "api"
---
# Story 20-1: assemble_turn infrastructure + action preprocessors

## Story Details
- **ID:** 20-1
- **Epic:** Epic 20 (Narrator Crunch Separation — ADR-057)
- **Workflow:** tdd
- **Points:** 5
- **Priority:** p1
- **Repos:** sidequest-api

## Context

Foundation story for the crunch separation (ADR-057). Builds the `assemble_turn` assembler that will grow to replace `extractor.rs`, and moves the two easiest fields (`action_rewrite`, `action_flags`) out of the narrator's JSON output into preprocessors that run before narration. This is Phase 1 of ADR-057 — proving the architecture works with zero impact on game behavior.

### Background

The narrator currently performs three simultaneous jobs: creative narration, intent interpretation, and structured JSON emission. The JSON block (~12 fields) consumes 63% of the narrator system prompt as schema documentation and forces the LLM to serialize structured data alongside prose — a dual-task penalty that produces malformed JSON, missing fields, and hallucinated values.

The server runs a 3-tier extraction pipeline (`extractor.rs`: direct parse → markdown fence → freeform regex search) to recover structured data from the narrator's output. This is fragile and invisible to OTEL — there's no way to know if the narrator actually engaged a subsystem or just improvised.

### The Principle (ADR-057)

> Narration → LLM. Intent → LLM. Crunch → Scripts.

`action_rewrite` and `action_flags` are mechanical transformations — no LLM judgment needed. They're based on the player's input text, not the narrative outcome. Moving them out of the narrator's JSON block removes two fields from the system prompt entirely and proves the two-phase architecture works.

### Technical Approach

1. **Preprocessors (runs BEFORE narration):**
   - `classify_action`: produces boolean flags (references_npc, references_inventory, etc.) from the player's input text
   - `rewrite_action`: produces you/named/intent rewrites (already partially implemented)
   - These return a struct; no narrator involvement needed

2. **`assemble_turn` (runs AFTER narration):**
   - Collects all tool call results from the turn + the prose output
   - Merges preprocessor results with narrator output
   - Produces the `ActionResult` struct the server already consumes
   - In this phase: pass-through for remaining JSON fields (still extracted from narrator via `extractor.rs`), but assembles preprocessor results alongside them

3. **Narrator system prompt:**
   - Remove `action_rewrite` schema documentation
   - Remove `action_flags` schema documentation
   - Narration output no longer includes these fields

### Scope Boundaries

**In scope:**
- Build `assemble_turn` module/function that merges tool call results + narrator JSON into `ActionResult`
- Move `action_rewrite` generation to a preprocessor (runs before narrator call)
- Move `action_flags` classification to a preprocessor (runs before narrator call)
- Remove `action_rewrite` and `action_flags` schema documentation from narrator system prompt
- OTEL events for preprocessor execution

**Out of scope:**
- Migrating any other JSON fields (scene_mood, items, etc. — those are stories 20-2 through 20-7)
- Deleting `extractor.rs` (that's story 20-8)
- Changing the `ActionResult` struct shape

## Acceptance Criteria

1. `assemble_turn` function exists and produces a valid `ActionResult` from narrator output + preprocessor results
2. `action_rewrite` is produced by a preprocessor before narration, not extracted from narrator JSON
3. `action_flags` is produced by a preprocessor before narration, not extracted from narrator JSON
4. Narrator system prompt no longer contains `action_rewrite` or `action_flags` schema documentation
5. OTEL events emitted for preprocessor execution (timing, field values)
6. All existing tests pass — game behavior unchanged

## Key Files (To Be Modified)

| File | LOC | Role in This Story |
|------|-----|-------------------|
| `crates/sidequest-agents/src/orchestrator.rs` | 1,151 | Remove action_rewrite/action_flags schema docs from system prompt |
| `crates/sidequest-agents/src/narrator.rs` | 168 | System prompt shrinks, no longer includes these fields |
| `crates/sidequest-agents/src/client.rs` | 317 | May add OTEL event infrastructure |
| `crates/sidequest-agents/src/extractor.rs` | 146 | Still used for remaining JSON fields (unchanged) |
| `crates/sidequest-server/src/dispatch/mod.rs` | ~1,900 | No changes needed yet (consumes ActionResult struct) |

## Key Files (To Be Created)

| File | Purpose |
|------|---------|
| `crates/sidequest-agents/src/tools/assemble_turn.rs` | Post-narration assembler: collects tool call log + prose → `ActionResult` |
| `crates/sidequest-agents/src/tools/mod.rs` | Tool module root |
| Preprocessor functions (TBD location) | `classify_action`, `rewrite_action` |

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-02T09:30:06Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T09:05:22Z | 2026-04-02T09:07:26Z | 2m 4s |
| red | 2026-04-02T09:07:26Z | 2026-04-02T09:14:09Z | 6m 43s |
| green | 2026-04-02T09:14:09Z | 2026-04-02T09:21:04Z | 6m 55s |
| spec-check | 2026-04-02T09:21:04Z | - | - |

## Sm Assessment

**Story 20-1** is Phase 1 of ADR-057 (Narrator Crunch Separation). Builds the `assemble_turn` assembler and moves `action_rewrite`/`action_flags` out of the narrator JSON block into preprocessors. 5 pts, TDD workflow, API repo only.

**Dependency note:** Story 15-27 (script tool invocation wiring) is shipping in a parallel session. 15-27 wires the tool_use call path that 20-1's assembler will collect from. Pull 15-27's branch into develop before starting the red phase to ensure tests can reference real tool call flows.

**Routing:** → Han Solo (TEA) for red phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Phase 1 of ADR-057 introduces new modules (assemble_turn, preprocessors) and modifies narrator system prompt

**Test Files:**
- `crates/sidequest-agents/tests/assemble_turn_story_20_1_tests.rs` — 25 tests covering all 6 ACs

**Tests Written:** 25 tests covering 5 ACs (AC-6 verified by test runner)
**Status:** RED (compilation fails — `tools` module does not exist)

### Test Coverage by AC

| AC | Tests | Description |
|----|-------|-------------|
| AC-1 | 4 | assemble_turn produces valid ActionResult, passes through narrator fields, preserves extraction_tier |
| AC-2 | 6 | preprocessor rewrite wins over narrator, rewrite_action produces 3 forms (you/named/intent) |
| AC-3 | 8 | preprocessor flags win over narrator, classify_action detects inventory/npc/ability/location/power_grab, multi-flag, default case |
| AC-4 | 3 | narrator prompt omits action_rewrite + action_flags schema, retains non-migrated fields |
| AC-5 | 2 | OTEL spans emitted for classify_action and rewrite_action |
| Wiring | 2 | tools module public, preprocessor functions accessible |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | N/A — no new public enums in this story | not applicable |
| #5 validated constructors | N/A — ActionRewrite/ActionFlags use serde defaults, no validation invariants | not applicable |
| #6 test quality | Self-check: 25 tests, all have meaningful assertions, no vacuous patterns | passing |
| #8 Deserialize bypass | N/A — no new types with validating constructors | not applicable |
| #9 public fields | N/A — ActionRewrite/ActionFlags fields have no security/validation invariants | not applicable |
| #10 tenant context | N/A — no trait methods touching tenant data | not applicable |

**Rules checked:** 1 of 15 applicable (test quality self-check). Others not applicable — this story creates mechanical preprocessors and an assembler, no new types with invariants.
**Self-check:** 0 vacuous tests found

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/tools/mod.rs` — module root, exports assemble_turn + preprocessors
- `crates/sidequest-agents/src/tools/assemble_turn.rs` — post-narration assembler, merges NarratorExtraction + preprocessor results into ActionResult
- `crates/sidequest-agents/src/tools/preprocessors.rs` — mechanical classify_action (keyword flags) + rewrite_action (text transforms), OTEL instrumented
- `crates/sidequest-agents/src/lib.rs` — wired `pub mod tools`
- `crates/sidequest-agents/src/agents/narrator.rs` — removed action_rewrite/action_flags schema from system prompt

**Tests:** 24/24 passing (GREEN) + all existing tests passing
**Branch:** feat/20-1-assemble-turn-infrastructure (pushed)

**Handoff:** To next phase (review)

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Gap** (non-blocking): `creature_smith.rs:72-75` still contains `action_rewrite`/`action_flags` schema in its system prompt. Phase 1 only migrated narrator — creature_smith needs the same treatment in a later story.
  Affects `crates/sidequest-agents/src/agents/creature_smith.rs` (system prompt needs schema removal when creature_smith is migrated).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `strip_pronouns()` at `preprocessors.rs:110` silently returns the original input when all words are pronouns. Per "no silent fallbacks" rule, an empty string would be more honest. Low severity — degenerate input edge case.
  Affects `crates/sidequest-agents/src/tools/preprocessors.rs` (strip_pronouns fallback behavior).
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): `assemble_turn` hardcodes `classified_intent`, `agent_name`, `agent_duration_ms`, `token_count_in/out`, `zone_breakdown` to `None`. When later stories wire this into the production path, these telemetry fields must be threaded through as parameters to avoid silently blinding the GM Dashboard.
  Affects `crates/sidequest-agents/src/tools/assemble_turn.rs` (function signature will grow).
  *Found by Reviewer during code review.*

### TEA (test design)
- **Gap** (non-blocking): `NarratorExtraction` struct fields are all `pub` but the struct is constructed manually in tests. If Dev changes the struct shape, tests need updating. Consider a builder or `Default` impl for test ergonomics.
  Affects `crates/sidequest-agents/src/orchestrator.rs` (NarratorExtraction struct).
  *Found by TEA during test design.*
- **Question** (non-blocking): Story says preprocessors are "mechanical text transformation" (no LLM). The existing `preprocessor.rs` uses Haiku LLM. The new `classify_action`/`rewrite_action` in `tools/preprocessors` must be purely mechanical (keyword matching, string manipulation). The old LLM-based `preprocessor.rs` may be redundant after this epic completes.
  Affects `crates/sidequest-agents/src/preprocessor.rs` (existing LLM preprocessor).
  *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec.

### TEA (test design)
- **Narrator prompt tests use Agent trait instead of standalone function**
  - Spec source: context-story-20-1.md, AC-4
  - Spec text: "Narrator system prompt no longer contains action_rewrite or action_flags schema documentation"
  - Implementation: Tests use `NarratorAgent::new().system_prompt()` via the Agent trait rather than a new `narrator_system_prompt()` public function. This tests the actual prompt the orchestrator uses.
  - Rationale: The Agent trait already exposes `system_prompt()` publicly; adding a redundant free function would violate DRY. This approach tests the real code path.
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **Narrator prompt tests use Agent trait instead of standalone function** → ACCEPTED by Reviewer: agrees with author reasoning. Agent trait's system_prompt() is the production code path — testing it directly is correct.
- **creature_smith.rs still contains action_rewrite/action_flags schema (UNDOCUMENTED):** Spec said narrator prompt loses these fields. Code removes them from narrator only. creature_smith at `agents/creature_smith.rs:72-75` still asks the LLM for these fields. Not documented by TEA/Dev. Severity: Low — out of scope for Phase 1 (narrator only), but creates inconsistency when Phase 2+ migrates creature_smith. Captured as delivery finding.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (fmt dirty, clippy blocked, all tests green) | confirmed 1 (fmt on new files), dismissed 2 (pre-existing clippy in sidequest-genre, not this story) |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 1 (strip_pronouns fallback), dismissed 4 (hardcoded None fields are Phase 1 by design — assembler not yet wired into production path) |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (rules 3 & 5: no non-test consumers) | dismissed 2 (story scope explicitly builds infrastructure for later phases — wiring into dispatch is stories 20-2+; not a half-wired feature but a deliberate phase boundary) |

**All received:** Yes (3 returned with findings, 6 disabled via settings)
**Total findings:** 1 confirmed, 6 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Data Flow Traced
Player input → `classify_action(input)` → `ActionFlags` + `rewrite_action(input, char_name)` → `ActionRewrite` → `assemble_turn(extraction, rewrite, flags)` → `ActionResult`. The assembler discards `extraction.action_rewrite`/`extraction.action_flags`, always using preprocessor values. Traced at `assemble_turn.rs:48-49`. Safe — deterministic merge with no I/O.

### Rule Compliance

| Rule | Items Checked | Verdict |
|------|--------------|---------|
| No stubs | `assemble_turn`, `classify_action`, `rewrite_action`, `strip_first_person`, `strip_pronouns`, 5 keyword classifiers — all fully implemented | COMPLIANT |
| No silent fallbacks | `strip_pronouns` returns original input when all words are pronouns — this is a silent fallback per rule. Severity: Low | VIOLATION (Low) |
| OTEL observability | `classify_action` has `#[tracing::instrument]` + `tracing::info!` with all 5 flags. `rewrite_action` has `#[tracing::instrument]` + `tracing::info!` with all 3 forms. Both at `preprocessors.rs:14,50` | COMPLIANT |
| No half-wired features | Module is `pub` in `lib.rs:24`, tests verify compilation. No production callers yet — but story scope explicitly builds infrastructure for Phase 1, with wiring in 20-2+. The session's "Out of scope" section excludes dispatch changes | COMPLIANT (scoped) |
| Every test suite needs a wiring test | `tools_module_is_public` at test line 408, `preprocessor_functions_are_public` at test line 415 — compile-time wiring checks | COMPLIANT |
| Don't reinvent | Uses existing `ActionResult`, `ActionFlags`, `ActionRewrite`, `NarratorExtraction` types from `orchestrator.rs`. No parallel types created | COMPLIANT |
| No stubbing | All modules have full implementations, no `todo!()` or `unimplemented!()` | COMPLIANT |

### Observations

1. [VERIFIED] Preprocessor override invariant — `assemble_turn.rs:48-49` always wraps preprocessor values in `Some()`, ignoring `extraction.action_rewrite`/`extraction.action_flags`. Tests at lines 146 and 179 use "NARRATOR SHOULD NOT WIN" sentinel values to prove this. Complies with AC-2 and AC-3.

2. [VERIFIED] Narrator prompt cleanup — `narrator.rs` no longer contains "action_rewrite" or "action_flags" anywhere (grep confirms zero matches). JSON example at line 151 never included these fields. Complies with AC-4. Checked against: no silent fallback rule (removal is clean, no alternative path).

3. [VERIFIED] OTEL instrumentation — `preprocessors.rs:14` and `preprocessors.rs:50` have `#[tracing::instrument]` with meaningful span names (`turn.preprocessor.classify_action`, `turn.preprocessor.rewrite_action`) and field values logged via `tracing::info!`. Complies with AC-5 and OTEL observability principle.

4. [VERIFIED] Module wiring — `lib.rs:24` declares `pub mod tools`, `tools/mod.rs` exports `pub mod assemble_turn` and `pub mod preprocessors`. Compile-time tests at test lines 408-715 verify function signatures are accessible. Complies with wiring test rule.

5. [VERIFIED] No LLM involvement — `preprocessors.rs` imports only `crate::orchestrator::{ActionFlags, ActionRewrite}`. No `ClaudeClient`, no `tokio`, no async. Pure synchronous keyword matching and string manipulation. This is the "crunch not fluff" principle from ADR-057.

6. [LOW] `strip_pronouns` silent fallback — `preprocessors.rs:110`: when all words are pronouns, returns original input instead of empty string. Input "I him her them" would produce intent="I him her them" rather than "". This violates the "no silent fallbacks" rule, but severity is Low — degenerate input that doesn't occur in gameplay.

7. [RULE] creature_smith still contains `action_rewrite`/`action_flags` schema at `agents/creature_smith.rs:72-75`. Story scope is narrator-only, so this is not a violation of *this* story's ACs, but it's an inconsistency that later phases must address.

8. [EDGE] Keyword classifier false positives — "him"/"her"/"them" in `has_npc_reference` trigger on common pronouns. "take" in `has_inventory_reference` triggers on "I take a look around." These are broad classification hints, not hard gates — false positives are acceptable for the use case (informing downstream processing, not blocking actions). Not a bug.

9. [SILENT] `assemble_turn` hardcodes `combat_patch: None`, `chase_patch: None`, `is_degraded: false`, `classified_intent: None`, `agent_name: None`, `agent_duration_ms: None`, `token_count_in/out: None`, `zone_breakdown: None`. These fields are populated from different sources in the current orchestrator path (`orchestrator.rs:701-727`). This is by design — `assemble_turn` is Phase 1 infrastructure not yet integrated into the production path. When it replaces the orchestrator construction (later stories), these parameters must be threaded through. Not a bug now, but a design gap to track.

10. [VERIFIED] Existing tests unbroken — Preflight reports 521/521 tests passing, 0 failures. `cargo test -p sidequest-agents` GREEN. Complies with AC-6.

### Error Handling
Functions are infallible by design — no `Result<>`, no panics, no I/O. `classify_action` returns bools, `rewrite_action` returns Strings, `assemble_turn` returns a fully populated struct. Empty input produces sensible defaults (all flags false, "You " prefix). This is appropriate for deterministic mechanical transforms.

### Security Analysis
No user input reaches unsafe operations. String operations use `to_lowercase()` and `contains()` — no regex, no format string injection, no deserialization of untrusted input. No tenant isolation concerns — these are pure functions with no state access.

### Devil's Advocate

What if this code is broken? Let me argue the case.

**The "no production callers" argument is the strongest attack.** The rule-checker flagged it, and the CLAUDE.md is clear: "No half-wired features — connect the full pipeline or don't start." This code is tested infrastructure with zero production consumers. You could delete the entire `tools/` module and nothing in the game would change. The wiring tests at lines 408-715 only prove compilation — they don't prove the functions are reachable from any code path a player would trigger. This is, by a strict reading, a half-wired feature.

**Counter-argument:** The story's scope explicitly says "Build assemble_turn module/function" and "Out of scope: Deleting extractor.rs." This is Phase 1 of a multi-story epic. The wiring happens in 20-2+. Requiring end-to-end wiring in a Phase 1 infrastructure story would mean either (a) shipping the entire epic as one story or (b) wiring prematurely before the other migrated fields exist. Both are worse outcomes.

**The strip_pronouns fallback is subtle.** "I me my" → all words are pronouns → `filtered` is empty → returns "I me my" unchanged. The intent field would contain raw pronouns. Is this harmful? The intent field is used for... what? Let me check. It's part of `ActionRewrite.intent`, which feeds into the game loop's preprocessed action. If the intent is garbage, it could confuse downstream processing. But the fallback only fires on inputs that are *entirely* pronouns — a degenerate case that no real player would trigger. The empty string alternative could also cause issues downstream. So this is a genuine but trivial design choice.

**The keyword classifiers are brittle.** "I cast my line into the river" triggers `references_ability` (due to "cast ") even though the player is fishing, not casting a spell. "I check my watch" triggers `references_inventory` (due to "check my"). These are not bugs per se — they're the expected behavior of a keyword classifier — but the false-positive rate could be high in natural language. The question is: do downstream consumers handle false positives gracefully? Since this is Phase 1 infrastructure without production consumers, the answer is unknown. This is a design risk, not a code bug.

**The hardcoded None fields in assemble_turn are a ticking bomb.** When a later story wires `assemble_turn` into the production path, if the developer forgets to add `classified_intent`, `agent_name`, and telemetry fields as parameters, the GM Dashboard will silently go blind. The function signature doesn't remind the caller that these fields exist and need filling. A builder pattern or a separate `TelemetryContext` struct parameter would make the API harder to misuse. But adding that now would be gold-plating for Phase 1.

**Verdict after devil's advocacy:** The strongest concerns (no production callers, hardcoded None telemetry fields) are both explicitly scoped out by the story definition. The strip_pronouns fallback is real but Low severity. The keyword false positives are inherent to the approach and expected. Nothing here reaches Critical or High severity. APPROVED stands.

### Handoff
To Grand Admiral Thrawn (SM) for finish-story.

[EDGE] — Keyword classifier false positives noted but acceptable for classification hints.
[SILENT] — `strip_pronouns` fallback and `assemble_turn` hardcoded None fields noted. Fallback is Low severity; None fields are Phase 1 by design.
[TEST] — 24 tests covering all 6 ACs with meaningful assertions. Compile-time wiring checks present.
[DOC] — Module docs are clear and accurate. ADR-057 referenced correctly.
[TYPE] — Uses existing types from orchestrator.rs. No new type design concerns.
[SEC] — Pure functions, no I/O, no unsafe, no deserialization of untrusted input.
[SIMPLE] — Implementation is appropriately simple for mechanical transforms.
[RULE] — Rules 3 & 5 (no half-wired features / verify non-test consumers) dismissed due to explicit Phase 1 scope boundary. All other rules compliant.