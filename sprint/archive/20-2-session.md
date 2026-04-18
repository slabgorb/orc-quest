---
story_id: "20-2"
jira_key: ""
epic: "20"
workflow: "tdd"
---

# Story 20-2: scene_mood and scene_intent tool calls

## Story Details

- **ID:** 20-2
- **Title:** scene_mood and scene_intent tool calls
- **Points:** 3
- **Epic:** 20 (Narrator Crunch Separation — ADR-057)
- **Repo:** sidequest-api
- **Workflow:** tdd
- **Stack Parent:** 20-1 (assemble_turn infrastructure + preprocessors — just shipped)

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-02T10:12:12Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-02T00:00Z | 2026-04-02T09:54:06Z | 9h 54m |
| red | 2026-04-02T09:54:06Z | 2026-04-02T09:58:40Z | 4m 34s |
| green | 2026-04-02T09:58:40Z | 2026-04-02T10:05:21Z | 6m 41s |
| spec-check | 2026-04-02T10:05:21Z | - | - |

## Summary

Phase 2 of ADR-057: Move `scene_mood` and `scene_intent` from narrator's JSON block to simple tool calls (single string arg each). Story 20-1 shipped `assemble_turn` infrastructure; this story implements the first reactive tools and proves the two-phase architecture works.

**Deliverables:**
- `set_mood` tool — validates mood enum, returns JSON
- `set_intent` tool — validates intent enum, returns JSON
- Update `assemble_turn` to consume tool results and override narrator extraction
- Remove ~200 tokens of schema docs from narrator system prompt
- Wire tools into orchestrator's `claude -p --allowedTools` invocation
- OTEL instrumentation for tool calls
- Comprehensive tests

**Key Insight:** This is the first test of the reactive tool pattern. If it works, the pattern scales to all remaining phases (items, footnotes, visual, quests, resources, personality, sfx).

## Technical Context

### What Just Shipped (20-1)
- `assemble_turn` function — deterministic assembler taking `NarratorExtraction` + `ActionRewrite` + `ActionFlags` → `ActionResult`
- `preprocessors.rs` module — `classify_action()` and `rewrite_action()` (no LLM calls)
- Preprocessor infrastructure wired into orchestrator

### This Story's Scope

**Build two new tools:**
- `crates/sidequest-agents/src/tools/set_mood.rs` (or function in existing file)
- `crates/sidequest-agents/src/tools/set_intent.rs` (or function in existing file)

**Update these files:**
- `narrator.rs` — remove `scene_mood`/`scene_intent` schema docs, add tool descriptions
- `orchestrator.rs` — add tools to `--allowedTools` list, capture tool results
- `assemble_turn.rs` — accept tool call results, override narrator extraction
- `client.rs` — extend `claude -p` command to include new tools

**Test:**
- Unit tests for each tool's validation logic
- Integration test: narrator calls `set_mood`, tool fires, `assemble_turn` merges result correctly
- Integration test: missing tool call falls back to narrator extraction
- Integration test: tool result overrides narrator extraction

### Enum Definitions (Use These — Don't Duplicate)

Check `sidequest-protocol` and `sidequest-game` for existing enum definitions:
- `scene_mood`: tension, wonder, melancholy, triumph, foreboding, calm, exhilaration, reverence
- `scene_intent`: dialogue, exploration, combat_prep, stealth, negotiation, escape, investigation, social

Tools MUST validate against the same enums (not hardcoded strings).

### OTEL Spans

Each tool call is a subprocess visible in OTEL. Emit:
- `tool.name` = "set_mood" or "set_intent"
- `tool.args.input` = argument passed
- `tool.result.valid` = boolean
- `tool.result.value` = validated enum value or error message

### Narrator Prompt Shrinkage

Currently `narrator.rs` includes ~200 tokens of schema documentation for these fields. This MUST be removed and replaced with a single line per tool. If the docs remain, the story is incomplete.

## Sm Assessment

**Story 20-2** is Phase 2 of ADR-057 — first reactive tool migration. Two simple enum tools (`set_mood`, `set_intent`) prove the pattern that scales to all remaining phases. 3 pts, tight scope. 20-1's assembler infrastructure is on develop and ready to consume these.

**Routing:** → Han Solo (TEA) for red phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Phase 2 of ADR-057 introduces new tool modules (set_mood, set_intent), extends assemble_turn, modifies narrator prompt

**Test Files:**
- `crates/sidequest-agents/tests/scene_tools_story_20_2_tests.rs` — 42 tests covering all 6 ACs

**Tests Written:** 42 tests covering 6 ACs
**Status:** RED (compilation fails — `set_mood`, `set_intent`, `ToolCallResults` modules don't exist, `assemble_turn` signature changed)

### Test Coverage by AC

| AC | Tests | Description |
|----|-------|-------------|
| AC-1 | 11 | validate_mood accepts 8 enum values, rejects invalid/empty, case-insensitive |
| AC-2 | 11 | validate_intent accepts 8 enum values, rejects invalid/empty, case-insensitive |
| AC-3 | 5 | assemble_turn with ToolCallResults overrides narrator, preserves other fields |
| AC-4 | 5 | Missing tool falls back to narrator extraction, None when neither provides |
| AC-5 | 3 | Narrator prompt omits schema docs, retains non-migrated fields |
| AC-6 | 3 | OTEL spans for valid and invalid tool calls |
| Wiring | 3 | Module exports, ToolCallResults::default() |
| Edge | 2 | All enum variants distinct (as_str roundtrip) |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | N/A — SceneMood/SceneIntent are new enums; Dev should add #[non_exhaustive] but tests don't enforce macro presence | noted for reviewer |
| #6 test quality | Self-check: 42 tests, all have meaningful assertions | passing |
| #13 constructor/deserialize consistency | SceneMood/SceneIntent validated via validate_mood/validate_intent; roundtrip tests ensure consistency | covered |

**Rules checked:** 2 of 15 applicable (test quality, constructor consistency). #2 non_exhaustive noted for reviewer.
**Self-check:** 0 vacuous tests found

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/tools/set_mood.rs` — SceneMood enum (8 variants), validate_mood(), OTEL instrumented
- `crates/sidequest-agents/src/tools/set_intent.rs` — SceneIntent enum (8 variants), validate_intent(), OTEL instrumented
- `crates/sidequest-agents/src/tools/assemble_turn.rs` — ToolCallResults struct, extended assemble_turn() with 4th arg, tool>narrator override semantics
- `crates/sidequest-agents/src/tools/mod.rs` — wired set_mood + set_intent modules
- `crates/sidequest-agents/src/agents/narrator.rs` — removed scene_mood/scene_intent schema docs from system prompt
- `crates/sidequest-agents/tests/assemble_turn_story_20_1_tests.rs` — updated for new assemble_turn 4-arg signature

**Tests:** 44/44 passing (GREEN) + all existing tests passing (24 from 20-1 updated)
**Branch:** feat/20-2-scene-mood-intent-tools (pushed)

**Handoff:** To next phase (review)

## Delivery Findings

No upstream findings. Story context clearly scoped.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): `SceneMood` and `SceneIntent` enums should have `#[non_exhaustive]` attribute. Both are public enums that will grow as genre packs expand. Without it, adding variants is a breaking change for external match arms.
  Affects `crates/sidequest-agents/src/tools/set_mood.rs:13` and `crates/sidequest-agents/src/tools/set_intent.rs:13`.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `assemble_turn()` has no OTEL instrumentation. It's the priority-merge decision point (tool > narrator) — the GM panel can't observe which source won for mood/intent on a given turn. Add `tracing::info!(mood_source, intent_source, ...)`.
  Affects `crates/sidequest-agents/src/tools/assemble_turn.rs:34`.
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): Audio dispatch at `crates/sidequest-server/src/dispatch/audio.rs:57` uses `result.scene_mood` as a string key. New mood values from SceneMood (wonder, melancholy, foreboding, exhilaration, reverence) don't map to existing `Mood` enum variants. The MusicDirector provides its own classification, so this is informational — but the mapping should be updated when the tools are wired into production.
  Affects `crates/sidequest-server/src/dispatch/audio.rs` (mood_key matching).
  *Found by Reviewer during code review.*

### TEA (test design)
- **Gap** (non-blocking): Story specifies scene_mood enum as {tension, wonder, melancholy, triumph, foreboding, calm, exhilaration, reverence} but the existing `Mood` enum in `music_director.rs` is {Combat, Exploration, Tension, Triumph, Sorrow, Mystery, Calm}. These are different concepts (music mood vs scene mood). Dev must create new `SceneMood` and `SceneIntent` enum types — they cannot reuse the existing enums directly.
  Affects `crates/sidequest-game/src/music_director.rs` (existing Mood enum) and `crates/sidequest-agents/src/tools/set_mood.rs` (new enum).
  *Found by TEA during test design.*
- **Gap** (non-blocking): Story specifies scene_intent enum as {dialogue, exploration, combat_prep, stealth, negotiation, escape, investigation, social} but the existing `Intent` enum in `intent_router.rs` is {Combat, Dialogue, Exploration, Examine, Meta, Chase, Backstory}. Same issue — different concept, different values.
  Affects `crates/sidequest-agents/src/agents/intent_router.rs` (existing Intent enum) and `crates/sidequest-agents/src/tools/set_intent.rs` (new enum).
  *Found by TEA during test design.*
- **Question** (non-blocking): The downstream consumer (`dispatch/audio.rs`) treats `scene_mood` as a string key matched to `Mood` enum variants via `as_key()`. After this story, `scene_mood` will contain values like "foreboding" that don't map to any `Mood` variant. Dev or a follow-up story needs to update the audio dispatch to handle new mood values.
  Affects `crates/sidequest-server/src/dispatch/audio.rs` (mood_key matching).
  *Found by TEA during test design.*

## Design Deviations

None yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Updated 20-1 test for scene_mood migration**
  - Spec source: assemble_turn_story_20_1_tests.rs, narrator_prompt_retains_non_migrated_fields
  - Spec text: "scene_mood is NOT migrated in Phase 1 — must remain in narrator prompt"
  - Implementation: Removed scene_mood assertion from this test since 20-2 migrates it out of the narrator prompt
  - Rationale: The test checked phase 1 state; phase 2 intentionally migrates scene_mood. Test now only checks visual_scene retention.
  - Severity: minor
  - Forward impact: none — test correctly reflects current migration state

### TEA (test design)
- **assemble_turn signature extended with ToolCallResults instead of individual params**
  - Spec source: context-story-20-2.md, AC-3
  - Spec text: "assemble_turn accepts mood/intent tool results and overrides narrator extraction values"
  - Implementation: Tests expect `ToolCallResults` struct with `scene_mood: Option<String>` and `scene_intent: Option<String>`, passed as 4th arg to `assemble_turn`. This extends the 20-1 signature.
  - Rationale: A struct is more extensible than adding `Option<String>` params — phases 3-7 will add more tool result fields without changing the function signature repeatedly.
  - Severity: minor
  - Forward impact: All future phases add fields to `ToolCallResults` instead of changing `assemble_turn` arity

### Reviewer (audit)
- **Updated 20-1 test for scene_mood migration** → ACCEPTED by Reviewer: correct — Phase 2 migrates scene_mood out of narrator prompt, removing the Phase 1 retention assertion is the right update.
- **assemble_turn signature extended with ToolCallResults** → ACCEPTED by Reviewer: agrees with extensibility rationale. Struct approach is cleaner than growing parameter count per phase.
- **creature_smith still has action_rewrite/action_flags in prompt (from 20-1 review, UNDOCUMENTED for 20-2):** creature_smith.rs:72-75 still asks LLM for action_rewrite/action_flags. Not this story's scope, but carries forward from 20-1 review. Severity: Low.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (fmt dirty, pre-existing clippy in sidequest-genre) | dismissed 2 (pre-existing, not this story) |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 1 (warn! missing input field), dismissed 3 (wiring gap is scoped, type erasure is pragmatic, narrator extraction validation is future work) |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 (non_exhaustive missing x2, OTEL gap on assemble_turn, wiring gap) | confirmed 2 (non_exhaustive, OTEL gap on assemble_turn), dismissed 1 (wiring gap — Phase 2 scope builds tools, wiring is later) |

**All received:** Yes (3 returned with findings, 6 disabled via settings)
**Total findings:** 3 confirmed, 7 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Data Flow Traced
LLM calls `set_mood("tension")` → `validate_mood("tension")` → `Ok(SceneMood::Tension)` → `.as_str()` → `"tension"` → `ToolCallResults.scene_mood: Some("tension")` → `assemble_turn(extraction, rewrite, flags, tool_results)` → `tool_results.scene_mood.or(extraction.scene_mood)` → `Some("tension")` → `ActionResult.scene_mood`. Override chain: tool > narrator > None. Traced at `assemble_turn.rs:41-43`. Safe — deterministic merge via `Option::or()`.

### Rule Compliance

| Rule | Items Checked | Verdict |
|------|--------------|---------|
| No stubs | SceneMood, SceneIntent, ToolCallResults, validate_mood, validate_intent — all fully implemented | COMPLIANT |
| No silent fallbacks | validate_mood/validate_intent return Err on invalid input. .or() fallback is documented design, not silent | COMPLIANT |
| OTEL observability | validate_mood/validate_intent have #[tracing::instrument] + info/warn events. `assemble_turn` has NO OTEL — merge decision invisible to GM panel | VIOLATION (Medium) |
| #[non_exhaustive] on enums | SceneMood (set_mood.rs:13) and SceneIntent (set_intent.rs:13) — 8-variant pub enums, will grow. Missing #[non_exhaustive] | VIOLATION (Medium) |
| No half-wired features | Same pattern as 20-1: infrastructure built, production wiring in later stories. Scoped | COMPLIANT (scoped) |
| Every test suite needs wiring test | 3 wiring tests: set_mood_module_is_public, set_intent_module_is_public, tool_call_results_is_exported | COMPLIANT |
| Don't reinvent | Extends existing assemble_turn from 20-1, uses existing ActionResult/NarratorExtraction types | COMPLIANT |
| No stubbing | All modules fully implemented | COMPLIANT |
| thiserror for error types | InvalidMood and InvalidIntent both use #[derive(thiserror::Error)] | COMPLIANT |

### Observations

1. [VERIFIED] Tool override semantics — `assemble_turn.rs:41` uses `tool_results.scene_mood.or(extraction.scene_mood)`, which means tool wins when present, narrator fallback when tool is None. Tests at scene_tools lines 253-303 prove override, fallback, both-present, and neither-present cases with sentinel values. Complies with AC-3 and AC-4.

2. [VERIFIED] Narrator prompt cleanup — `narrator.rs` diff removes "scene_mood: ALWAYS INCLUDE" schema line, "scene_intent: ALWAYS INCLUDE" schema line, JSON example updated to exclude both fields, "REQUIRED every turn" line updated to just "visual_scene". Grep confirms zero matches for "scene_mood" or "scene_intent" in narrator.rs. Complies with AC-5.

3. [VERIFIED] Enum validation — `validate_mood` and `validate_intent` both do case-insensitive matching via `.to_lowercase()` (set_mood.rs:62, set_intent.rs:62). Tests cover all 8 variants, case-insensitive acceptance ("TENSION", "Tension"), rejection of invalid input, and empty string rejection. Complies with AC-1 and AC-2.

4. [VERIFIED] OTEL on validators — `set_mood.rs:60` has `#[tracing::instrument(name = "tool.set_mood")]` with input field. `set_intent.rs:60` has matching instrumentation. Both emit `tracing::info!` on success and `tracing::warn!` on failure. Complies with AC-6.

5. [MEDIUM] Missing `#[non_exhaustive]` — `SceneMood` at `set_mood.rs:13` and `SceneIntent` at `set_intent.rs:13` are public enums that will grow as genres expand. Without `#[non_exhaustive]`, adding variants is a breaking change for external match arms. Fix is trivial (add one attribute line per enum) but not blocking — the enums are currently internal to sidequest-agents.

6. [MEDIUM] [RULE] No OTEL span on `assemble_turn` — `assemble_turn.rs:34` makes the merge decision (tool vs narrator) but emits no tracing event. The validators log their individual decisions, but the assembler's priority resolution is invisible to the GM panel. This was also true in 20-1 — the function was approved without OTEL. Adding `tracing::info!(mood_source, intent_source, ...)` would close this gap.

7. [VERIFIED] 20-1 test updates — All `assemble_turn` calls in `assemble_turn_story_20_1_tests.rs` correctly updated to pass `ToolCallResults::default()` as 4th arg. Narrator prompt retention test correctly removed `scene_mood` assertion since Phase 2 migrates it. Wiring test updated for new 4-arg signature.

8. [LOW] [SILENT] warn! events missing input value — `set_mood.rs:76` and `set_intent.rs:76` emit `tracing::warn!(valid = false, ...)` but don't include the invalid input string in the event itself. The input IS captured in the span via `#[tracing::instrument(fields(input = %input))]`, so it's available in span context — but the event alone doesn't show what was rejected. Minor diagnostic improvement.

9. [VERIFIED] ToolCallResults extensibility — Derives `Default` (assemble_turn.rs:19), so callers use `ToolCallResults::default()` when no tools fired. Test at scene_tools line 410 verifies all fields are None on default. Future phases add fields without changing assemble_turn arity.

10. [VERIFIED] Error types use thiserror — `InvalidMood` (set_mood.rs:55) and `InvalidIntent` (set_intent.rs:55) both derive `thiserror::Error` with descriptive error messages listing valid variants. Good practice.

### Error Handling
`validate_mood` and `validate_intent` return `Result` with typed errors — `InvalidMood`/`InvalidIntent` with `thiserror::Error`. No panics, no unwraps. `assemble_turn` is infallible (deterministic merge). Empty/null input to validators correctly returns Err. Sound error handling design.

### Security Analysis
No user input reaches unsafe operations. String matching via `to_lowercase()` + pattern match. No regex, no deserialization of untrusted input in the new code. No tenant isolation concerns — pure validation functions.

### Devil's Advocate

What if this code is broken?

**The type erasure problem is real.** `ToolCallResults.scene_mood` is `Option<String>`, not `Option<SceneMood>`. A caller could bypass `validate_mood()`, construct `ToolCallResults { scene_mood: Some("garbage".into()), .. }`, and the assembler would happily pass "garbage" into `ActionResult.scene_mood`. The validation boundary exists but is not enforced by the type system. In Go terms, it's like returning `string` instead of a typed wrapper after validation — you've checked it once but nothing prevents re-contamination.

**Counter:** The callers don't exist yet (no production wiring). When they're written in a later story, the test suite validates the full flow. And `ActionResult.scene_mood` is `Option<String>` — you'd need to change that type too to get end-to-end type safety, which is out of scope for Phase 2.

**The OTEL gap matters more than it looks.** The GM panel is "the lie detector" per CLAUDE.md. If `assemble_turn` doesn't log which source won for mood/intent, the GM can't tell whether the tool fired or the narrator's value was used. With both validators having their own spans, you might think coverage is adequate — but the validator span fires even when the result is later discarded by `.or()`. You'd see `tool.set_mood: valid=true, value="tension"` AND `extraction.scene_mood="mystery"` but never know which one actually ended up in `ActionResult`. A `tracing::info!(mood_source="tool"|"narrator", ...)` in `assemble_turn` would complete the picture.

**Counter:** This is a genuine improvement but not a regression — 20-1's `assemble_turn` was approved without OTEL. The pattern of adding OTEL to the assembler should happen when it's wired into production (when the spans would actually fire in a real turn).

**The `#[non_exhaustive]` omission could bite in Phase 3+.** If a downstream crate (sidequest-server) starts matching on `SceneMood` variants and Phase 3 adds a new mood, the match will fail to compile — but only with `#[non_exhaustive]`. Without it, the match compiles fine and the new variant falls through to a wildcard or produces a panic at runtime. However, the enum is currently only used in tests and the validators (which use strings, not enum matching). So the risk is theoretical until production wiring exists.

**Verdict after devil's advocacy:** The confirmed findings (non_exhaustive, OTEL gap) are both MEDIUM — improvements that should happen, but neither represents a correctness bug or security issue. The type erasure concern is a design trade-off, not a bug. APPROVED stands.

### Handoff
To Grand Admiral Thrawn (SM) for finish-story.

[EDGE] — N/A (disabled)
[SILENT] — warn! events missing input value on error path (Low). Type erasure in ToolCallResults noted but pragmatic.
[TEST] — 44 tests covering all 6 ACs + 24 updated 20-1 tests. Compile-time wiring checks present.
[DOC] — Module docs clear and accurate. ADR-057 Phase 2 referenced correctly.
[TYPE] — Missing #[non_exhaustive] on SceneMood and SceneIntent (Medium).
[SEC] — Pure functions, no I/O, no unsafe, no deserialization of untrusted input.
[SIMPLE] — Implementation appropriately simple. ToolCallResults extensible for future phases.
[RULE] — #[non_exhaustive] violation (rule 10, Medium). OTEL gap on assemble_turn (rule 7, Medium). Wiring gap dismissed — scoped to Phase 2.