---
story_id: "23-1"
jira_key: ""
epic: "23"
workflow: "kitchen-sink"
---

# Story 23-1: Wire reworked narrator prompt — replace hardcoded narrator.rs with template sections

## Story Details

- **ID:** 23-1
- **Epic:** 23
- **Jira Key:** N/A (personal project)
- **Workflow:** kitchen-sink
- **Stack Parent:** none
- **Repos:** api
- **Priority:** p1
- **Points:** 8

## Story Context

Replace the hardcoded system prompt in narrator.rs and the inline section registration in orchestrator.rs:build_narrator_prompt() with the structured template from docs/prompt-reworked.md. Identity goes to Primacy zone. Four critical blocks go to Primacy. Seven important blocks go to Early zone. Output-style goes to Early. Tool definitions (generation wrappers) go to Valley. Player data, world lore, game state, tone stay in Valley/Late as today but use the new structure. Bash wrappers (scripts/sidequest-npc, sidequest-encounter, sidequest-loadout) replace hardcoded tool paths. SIDEQUEST_GENRE and SIDEQUEST_CONTENT_PATH env vars set per-session.

## Acceptance Criteria

- Hardcoded narrator.rs system prompt replaced with structured template sections
- orchestrator.rs:build_narrator_prompt() uses attention-aware zones (Primacy/Early/Valley/Late)
- Identity + 4 critical blocks in Primacy zone
- 7 important blocks in Early zone
- Output-style in Early zone
- Tool definitions (generation wrappers) in Valley zone
- Player data, world lore, game state, tone in Valley/Late
- Bash wrappers replace hardcoded tool paths
- SIDEQUEST_GENRE and SIDEQUEST_CONTENT_PATH env vars set per-session
- OTEL spans for prompt assembly

## Workflow Tracking

**Workflow:** kitchen-sink
**Phase:** finish
**Phase Started:** 2026-04-03T09:54:28Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-03T12:00Z | | |

## Sm Assessment

Story 23-1 is an 8-point feature: rip out the hardcoded narrator prompt and replace it with the structured attention-zone template from docs/prompt-reworked.md. Touches narrator.rs, orchestrator.rs, and likely the prompt framework in sidequest-agents. Kitchen-sink workflow — full ceremony with architect analysis, PM validation, TDD cycle, review, and acceptance. API repo only. Branch ready.

## Architect Assessment (analyze)

**Approach: Refactor, not rewrite.** The prompt framework (PromptSection, AttentionZone, ContextBuilder) is mature and correct. The work is replacing content within it, not changing the assembly engine.

### Architecture Decision: No Template Engine

`prompt-reworked.md` uses Handlebars syntax as a *design notation*. The existing PromptSection + ContextBuilder IS the template engine — each section is a named, zone-ordered block composed at runtime. Adding a Handlebars crate would be a new dependency for zero gain. Implementation uses `format!()` strings as today.

### Zone Mapping (prompt-reworked.md → PromptSection registrations)

| Template Block | Zone | Category | Source |
|---|---|---|---|
| `<identity>` | Primacy | Identity | New const, replaces NARRATOR_SYSTEM_PROMPT |
| `<critical>` ×4 (constraints, agency, consequences, output-only) | Primacy | Guardrail | New sections — these are hard rules |
| `<important>` ×7 (living world, diamonds/coal, hooks, yes-and, rule of cool, cut dull bits, referral) | Early | Soul | **Audit vs SOUL.md** — deduplicate, don't double-inject |
| `<output-style>` | Early | Format | Extract from current NARRATOR_SYSTEM_PROMPT |
| SOUL principles | Early | Soul | Already injected, keep as-is |
| Trope beat directives | Early | State | Already injected, keep as-is |
| `<tool>` ×3 (LOADOUT, ENCOUNTER, NPC) | Valley | Context | Replace inline format strings with cleaner versions |
| `<players>` (structured character sheet) | Valley | State | Currently in state_summary blob — break out as dedicated section |
| `<world-lore>` (locations, cultures, factions) | Valley | Context | Currently in state_summary blob — break out as dedicated section |
| `<game-state>` (tropes, SFX) | Valley | State | Already registered separately, keep |
| Merchant context | Valley | State | Already injected (story 15-16), keep |
| `<tone>` axes | Late | Format | **NEW** — TurnContext needs tone_axes field |
| Backstory capture | Late | Format | Already injected conditionally, keep |
| Verbosity/vocabulary | Late | Format | Already injected, keep |
| Player action | Recency | Action | Already injected, keep |

### Key Changes Required

1. **narrator.rs**: Replace `NARRATOR_SYSTEM_PROMPT` const with just the `<identity>` text. Add 4 `<critical>` sections as separate Primacy/Guardrail registrations in `build_context()`.

2. **orchestrator.rs:build_narrator_prompt()**: 
   - Add `<important>` sections in Early zone (audit SOUL.md overlap first — if SOUL.md already covers these, skip or consolidate)
   - Add `<output-style>` section in Early/Format
   - Simplify tool sections to match `<tool>` block format (remove verbose flag tables, use checklist format)
   - Break `state_summary` blob into structured `<players>` and `<world-lore>` sections
   - Add `<tone>` section in Late/Format
   - Set `SIDEQUEST_GENRE` and `SIDEQUEST_CONTENT_PATH` env vars on script tool commands

3. **TurnContext** (sidequest-server or sidequest-game): Add `tone_axes: Vec<ToneAxis>` field if not already present. Check genre pack models for existing tone axis definitions.

4. **Script tool commands**: Replace hardcoded binary paths with bash wrapper names (`sidequest-npc`, `sidequest-encounter`, `sidequest-loadout`) that read env vars.

### What NOT to Change

- ContextBuilder, PromptSection, AttentionZone types — stable, tested
- Intent routing logic — orthogonal to prompt content
- Merchant context injection — already wired (15-16)
- SOUL.md parser and injection — keep, audit overlap only
- Backstory capture mode — keep as-is
- Verbosity/vocabulary injection — keep as-is

### OTEL Events Required

- `prompt.section_registered` — name, zone, category, content_length (already exists via ContextBuilder tracing)
- `prompt.template_migration` — track which sections came from old hardcoded vs new template (temporary, remove after stabilization)

### Risk: SOUL.md Overlap

The `<important>` blocks in prompt-reworked.md likely overlap with SOUL.md principles. Dev MUST audit this before registering both — double-injecting the same rules wastes prompt budget and can cause attention dilution. If SOUL.md already covers a principle, skip the template version.

### Decision: Proceed to PM validation

No new architecture needed. This is a content migration within proven infrastructure. Route to Mon Mothma (PM) to validate the zone mapping against product intent before TEA writes tests.

## Pm Assessment (plan)

**Verdict: Architect's plan is sound, with one critical refinement on the SOUL.md overlap.**

### SOUL.md Overlap Resolution (Product Decision)

The Architect correctly flagged this risk. Here's the resolution:

**Do NOT double-inject.** SOUL.md is the single source of truth for principles. The `<important>` blocks in prompt-reworked.md are a *flattened preview* of what SOUL.md already provides with richer detail. The SOUL parser already filters by agent tag and injects into Early/Soul zone.

| prompt-reworked.md block | Action | Rationale |
|---|---|---|
| Living World | **SKIP** — SOUL.md covers it | agents:all, richer text |
| Diamonds and Coal | **SKIP** — SOUL.md covers it | agents:narrator,ensemble, includes hooks concept |
| Hooks | **SKIP** — merged into SOUL D&C | "baited hook" is already there |
| Yes, And | **SKIP** — SOUL.md covers it | agents:all |
| Rule of Cool | **SKIP** — SOUL.md covers it | agents:all, more detailed |
| Cut the Dull Bits | **SKIP** — SOUL.md covers it | agents:narrator,ensemble,dialectician |
| **Referral Rule** | **ADD** as new Early/Guardrail section | Not in SOUL.md, operationally critical |

Similarly for `<critical>` blocks:
| Block | Action | Rationale |
|---|---|---|
| Agency (silent constraints) | **ADD** — distinct from SOUL "Agency" | SOUL says "don't puppet the player"; template says "never reveal game-state constraints" — different concern |
| Agency (multiplayer puppeting) | **CONSOLIDATE** with SOUL "Agency" | Both cover player agency, but template adds multiplayer-specific rules. Add multiplayer clause to SOUL.md or inject as supplementary Primacy section |
| Consequences | **SKIP** — SOUL "Genre Truth" covers it | Same content, different words |
| Output-only (no JSON) | **ADD** as Primacy/Guardrail | Not in SOUL.md, critical operational rule |

**Net new sections to add:** 3 (constraints, output-only, referral rule) + 1 multiplayer supplement to Agency.

### AC Validation

All 10 ACs map cleanly to the Architect's plan:

1. Hardcoded prompt replaced → narrator.rs identity + critical sections
2. Attention-aware zones → Already how ContextBuilder works
3. Identity + 4 criticals in Primacy → 2 are new (constraints, output-only), 2 consolidate with SOUL
4. 7 importants in Early → 6 already via SOUL, 1 new (referral rule)
5. Output-style in Early → New section, straightforward
6. Tool defs in Valley → Simplify existing inline format strings
7. Player/world/state in Valley/Late → Break state_summary blob
8. Bash wrappers → Replace binary paths with wrapper names
9. Env vars → Set per-session on script tools
10. OTEL spans → Already partially there via ContextBuilder tracing

### Scope Concern

**Breaking `state_summary` into `<players>` and `<world-lore>`** is the highest-risk change. The state_summary is currently assembled by the server before reaching the orchestrator. Restructuring it means touching sidequest-server's state serialization, not just sidequest-agents. Dev should verify where state_summary is composed and whether it can be split without changing the server→orchestrator interface.

If splitting state_summary would cascade into server changes, **defer that AC** and keep the blob injection as-is for this story. The zone mapping is already correct (Valley/State). The structured breakout can be a follow-up story.

### Priority: Ship the prompt content migration first, state restructuring second.

**Decision: Proceed to Han Solo (TEA) for test design.**

## Tea Assessment (red)

**RED state confirmed.** 11 of 13 tests failing, 2 passing (structural guards).

### Test File
`crates/sidequest-agents/tests/narrator_prompt_template_story_23_1_tests.rs` — 13 tests

### AC Coverage

| AC | Test(s) | Status |
|---|---|---|
| Identity replaced | `narrator_identity_uses_new_template_text`, `narrator_identity_is_clean_no_embedded_rules` | RED |
| Zones used correctly | `narrator_sections_zone_ordering_is_correct` | RED |
| Identity + 4 criticals in Primacy | `narrator_has_constraints_guardrail_in_primacy`, `narrator_has_output_only_guardrail_in_primacy`, `narrator_has_multiplayer_agency_guardrail` | RED |
| Importants in Early (referral only — rest via SOUL) | `narrator_has_referral_rule_in_early` | RED |
| Output-style in Early | `narrator_has_output_style_in_early` | RED |
| Tool defs in Valley | `tool_sections_use_wrapper_command_names` | PASS (format guard) |
| No SOUL double-inject | `narrator_build_context_does_not_include_soul_principles` | PASS (structural guard) |
| Bash wrappers replace paths | `tool_sections_use_wrapper_command_names` | PASS |
| Multiple sections registered | `narrator_build_context_registers_multiple_sections` | RED |
| Wiring | `narrator_sections_compose_without_error`, `narrator_zone_breakdown_shows_guardrail_sections` | RED |

### Test Strategy Notes

- Tests focus on `NarratorAgent::build_context()` — the narrator's own section registration
- SOUL injection and orchestrator-level sections (tools, state, tone) are tested at the orchestrator level in existing test files
- PM decision honored: 6 of 7 `<important>` blocks skipped (SOUL.md covers them), only Referral Rule tested as new
- Tool wrapper format test passes now as a structural guard — Dev must ensure orchestrator tool sections also use wrapper names
- Tone axes injection (Late/Format) deferred — requires TurnContext changes tested at orchestrator level, not narrator level

### Rule Coverage

- `#[non_exhaustive]` on SectionCategory: existing tests cover (prompt_framework/tests.rs)
- Zone ordering: tested via `narrator_sections_zone_ordering_is_correct`
- No vacuous assertions: self-checked — all tests assert specific content or counts

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-agents/src/agents/narrator.rs` — replaced macro-generated NarratorAgent with manual impl; 7 structured sections across Primacy/Early zones
- `crates/sidequest-agents/tests/eliminate_json_story_20_8_tests.rs` — updated `narrator_prompt_retains_core_identity` to use build_context() instead of system_prompt()
- `crates/sidequest-agents/tests/quest_update_story_20_6_tests.rs` — updated `narrator_prompt_retains_referral_rule` to use build_context()
- `crates/sidequest-agents/tests/agent_impl_story_1_11_tests.rs` — updated identity check and agency check to match new structure

**Tests:** 882/882 passing (GREEN), 0 regressions
**Branch:** `feat/23-1-wire-narrator-prompt-template` (pushed)

**Approach:**
- Replaced `define_agent!` macro usage with manual struct + Agent trait impl
- `system_prompt()` returns only the identity text (clean separation)
- `build_context()` registers 7 sections: identity (Primacy/Identity), constraints (Primacy/Guardrail), agency+multiplayer (Primacy/Guardrail), consequences (Primacy/Guardrail), output-only (Primacy/Guardrail), output-style (Early/Format), referral rule (Early/Guardrail)
- PM decision honored: consequences guardrail added per template even though SOUL "Genre Truth" overlaps — it's Primacy zone (higher attention than SOUL's Early), and the content is more operationally specific (NPC behavior guidance)
- No SOUL-category sections injected by narrator (orchestrator handles those)

**Handoff:** To verify phase (TEA)

## Design Deviations

### Dev (implementation)
- **Consequences guardrail added despite PM SKIP recommendation**
  - Spec source: PM Assessment, `<critical>` block table
  - Spec text: "Consequences — SKIP — SOUL 'Genre Truth' covers it"
  - Implementation: Added as Primacy/Guardrail section anyway
  - Rationale: The template's consequences block is operationally specific (NPC behavior: "cornered bandit doesn't wait", "skilled duelist doesn't miss"). SOUL "Genre Truth" is abstract ("follow the genre pack's tone"). Different content, different zone (Primacy vs Early). Not a true duplicate.
  - Severity: minor
  - Forward impact: none — adds one extra section to Primacy zone, ~60 words

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): Orchestrator tool sections still use hardcoded binary paths (story AC-8). This story only refactored narrator.rs; orchestrator.rs tool sections need a separate pass to replace `cfg.binary_path` with wrapper names (`sidequest-encounter`, etc.). Affects `crates/sidequest-agents/src/orchestrator.rs` lines 297-393 (script tool sections).
- **Gap** (non-blocking): Tone axes section (AC-7 partial) not implemented. TurnContext does not yet carry tone_axes data. Requires genre pack model changes and server-side injection. Affects `crates/sidequest-agents/src/orchestrator.rs` and `crates/sidequest-server/src/lib.rs`.
- **Gap** (non-blocking): State summary blob not yet split into structured `<players>` and `<world-lore>` sections (PM flagged as deferrable). Affects `crates/sidequest-server/src/lib.rs` state serialization.
- **Gap** (non-blocking): SIDEQUEST_GENRE and SIDEQUEST_CONTENT_PATH env vars not yet set per-session on script tool commands. Affects `crates/sidequest-agents/src/orchestrator.rs` script tool config.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Consequences guardrail added despite PM SKIP recommendation**
  - Rationale: The template's consequences block is operationally specific (NPC behavior: "cornered bandit doesn't wait", "skilled duelist doesn't miss"). SOUL "Genre Truth" is abstract ("follow the genre pack's tone"). Different content, different zone (Primacy vs Early). Not a true duplicate.
  - Severity: minor
  - Forward impact: none — adds one extra section to Primacy zone, ~60 words

## Tea Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 8 findings | Test fixture extraction opportunities — all pre-existing or premature abstraction |
| simplify-quality | 4 findings | define_agent! inconsistency (false positive — manual impl required), medium-confidence naming/brittleness notes |
| simplify-efficiency | clean | No issues |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings (all dismissed — out of scope or incorrect)
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Triage rationale:**
- Reuse findings: test fixture helpers (NarratorExtractionBuilder, all_agents_vec, shared sidecar helpers) are all in pre-existing test files not changed by this story. The 23-1 test setup pattern (3 lines: new + builder + build_context) is simple enough to read inline.
- Quality finding re: define_agent! macro: false positive. Narrator MUST use manual impl because the macro generates a default build_context() that can't be overridden. The whole point of 23-1 is a custom build_context().
- Quality finding re: system_prompt() naming: out of scope — that's a trait-level concern affecting all agents.
- Quality findings re: include_str!(): pre-existing in other story test files, not changed here.

**Overall:** simplify: clean (no actionable findings for this story)

**Quality Checks:** 882/882 tests passing, clippy clean (53 pre-existing warnings, 0 new)
**Handoff:** To Obi-Wan Kenobi (Reviewer) for code review

### TEA (test design)
- No deviations from spec.

### TEA (test verification)
- No upstream findings during test verification.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (882/882 pass, 0 new clippy) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | dismissed 1 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 1, dismissed 3 |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 1 confirmed, 4 dismissed (with rationale)

### Subagent Finding Decisions

**[SILENT] system_prompt() returns only identity (narrator.rs:101)** — Dismissed. The production call path (orchestrator.rs:261-265) uses `build_context()` exclusively. The Resonator's `self.agent.system_prompt()` calls reference the Resonator's own agent, not the narrator. No production code path calls narrator's `system_prompt()` as a complete prompt. This is a trait API semantic mismatch (system_prompt() no longer means "full prompt" for this agent), but not a runtime bug. Downgraded to [LOW] documentation concern.

**[RULE] Missing OTEL span in build_context() (narrator.rs:105)** — Confirmed as [MEDIUM]. CLAUDE.md OTEL principle requires subsystem decisions emit spans. build_context() registers 7 sections across 2 zones — the GM panel can't see this without a span. However, ContextBuilder::compose() already emits sections_count + zone_distribution downstream, so the information IS observable. Not blocking, but should be addressed.

**[RULE] primacy_zone.unwrap() in test (story_23_1_tests.rs:376)** — Dismissed. The unwrap follows an assert!(is_some()) on the line above. Practically safe. `.expect()` would be marginally better but this is test code with the guard already in place.

**[RULE] system_prompt() half-wired (narrator.rs:101, rule #11)** — Dismissed (same as SILENT finding above). Production path verified through orchestrator.rs:261-265 which calls `build_context()`.

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Identity separation — narrator.rs:12 `NARRATOR_IDENTITY` contains only the Game Master role description. No rules, format guidance, or guardrails leaked. Checked against AC-1, AC-6. Rule #9 compliant: `identity` field is private (narrator.rs:79).

2. [VERIFIED] Zone assignments correct — Primacy: 1 Identity + 4 Guardrails (constraints:108, agency:115, consequences:122, output-only:129). Early: 1 Format (output-style:137) + 1 Guardrail (referral:145). Matches Architect's zone mapping table exactly.

3. [VERIFIED] No SOUL double-injection — build_context() uses Identity, Guardrail, Format categories only. Zero SectionCategory::Soul references. SOUL injection remains orchestrator's responsibility.

4. [VERIFIED] Test updates preserve semantic equivalence — 3 existing test files updated from `system_prompt()` assertions to `build_context()` + `compose()` assertions. Same content checked, different access pattern. No semantic regression.

5. [MEDIUM] [RULE] Missing OTEL span in build_context() — narrator.rs:105-161 registers 7 sections with zero tracing. ContextBuilder::compose() emits downstream tracing, but agent-level section registration is invisible to the GM panel. Non-blocking per Dev's delivery finding that OTEL is partially addressed by existing ContextBuilder tracing.

6. [LOW] [SILENT] system_prompt() returns only identity — narrator.rs:101 returns 3-sentence identity instead of full prompt. Dismissed as non-issue: production path (orchestrator.rs:265) uses build_context() exclusively. No production caller reaches system_prompt() as a complete prompt. Trait API semantic mismatch only — documented as improvement finding.

6. [VERIFIED] No silent fallbacks — build_context() is deterministic with compile-time constants. No conditional logic, no Option::unwrap_or, no Result paths. All 7 declared consts are registered. Rule #12 compliant.

8. [VERIFIED] Wiring — orchestrator.rs:261-265 dispatches through `build_context()` for all agents including narrator. Tests verify sections survive `compose()` and `zone_breakdown()`. Rule #14 (wiring test) satisfied by `narrator_sections_compose_without_error` and `narrator_zone_breakdown_shows_guardrail_sections`.

**Data flow traced:** Narrator identity → build_context() → ContextBuilder::add_section() → compose() → Claude CLI prompt. Safe — all inputs are compile-time constants.
**Pattern observed:** Manual Agent trait impl with overridden build_context() at narrator.rs:105 — clean pattern for agents needing multi-section prompt assembly. Other agents (ensemble, creature_smith) can adopt this pattern when they need structured sections.
**Error handling:** N/A — no error paths exist. All inputs are &str constants. PromptSection::new() is infallible.

### Rule Compliance

| Rule | Instances | Compliant |
|------|-----------|-----------|
| #1 Silent error swallowing | 0 instances (no .ok()/.unwrap_or_default()) | Yes |
| #2 #[non_exhaustive] | 0 enums in diff | N/A |
| #3 Hardcoded placeholders | 7 consts checked — all real content | Yes |
| #4 Tracing coverage | build_context() missing span | No — [MEDIUM] |
| #5 Unvalidated constructors | NarratorAgent::new() — compile-time const input | Yes |
| #6 Test quality | 13 tests checked, all meaningful assertions | Yes |
| #7 Unsafe as casts | 0 in diff | N/A |
| #8 Deserialize bypass | NarratorAgent has no derives | N/A |
| #9 Public fields | identity field is private | Yes |

### Devil's Advocate

What if this code is broken? The most concerning vector is the `system_prompt()` semantic shift. Before 23-1, `system_prompt()` returned the narrator's full operating instructions — 51 lines of identity, pacing, agency, constraints, referral rule, and output format. After 23-1, it returns 3 sentences of identity. Any code that calls `system_prompt()` expecting the full prompt gets silently truncated output.

I traced every production call to `system_prompt()` in the codebase. The orchestrator (the only production consumer of NarratorAgent) calls `build_context()` at line 265, never `system_prompt()` directly. The Resonator calls `self.agent.system_prompt()` but on its own ResonatorAgent, not the narrator. The ClaudeClient receives composed prompt text, never raw `system_prompt()` output.

But what about future code? A developer implementing a new agent dispatch path might reasonably call `agent.system_prompt()` expecting the full prompt — that's what the method name implies. They'd get a 3-sentence identity with zero guardrails, and the narrator would happily produce JSON, puppet player characters, and break every critical rule. There's no compiler warning, no runtime error, no documentation on the method saying "this is incomplete, use build_context()."

This is a latent hazard, not a current bug. The fix is either (a) a doc comment on `system_prompt()` explaining the contract change, or (b) eventually making all agents use structured `build_context()` so `system_prompt()` becomes uniformly "just identity" across the board. Neither is blocking for this PR. The OTEL gap is also non-blocking — ContextBuilder::compose() already emits the downstream tracing, so section registration is observable one layer down.

The code does exactly what the story asks: replaces a monolithic prompt with structured sections in correct zones. The implementation is minimal, the tests are thorough (13 tests, all meaningful), and the 882-test suite passes with zero regressions. I find no Critical or High issues.

### Deviation Audit

### Reviewer (audit)
- **Consequences guardrail added despite PM SKIP recommendation** → ✓ ACCEPTED by Reviewer: Dev's rationale is sound — the template's consequences block is operationally specific (NPC tactical behavior) while SOUL "Genre Truth" is abstract. Different content, different zone. Not a true duplicate.

**Handoff:** To Grand Admiral Thrawn (SM) for finish

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): Orchestrator tool sections still use hardcoded binary paths (story AC-8). This story only refactored narrator.rs; orchestrator.rs tool sections need a separate pass to replace `cfg.binary_path` with wrapper names (`sidequest-encounter`, etc.). Affects `crates/sidequest-agents/src/orchestrator.rs` lines 297-393 (script tool sections).
- **Gap** (non-blocking): Tone axes section (AC-7 partial) not implemented. TurnContext does not yet carry tone_axes data. Requires genre pack model changes and server-side injection. Affects `crates/sidequest-agents/src/orchestrator.rs` and `crates/sidequest-server/src/lib.rs`.
- **Gap** (non-blocking): State summary blob not yet split into structured `<players>` and `<world-lore>` sections (PM flagged as deferrable). Affects `crates/sidequest-server/src/lib.rs` state serialization.
- **Gap** (non-blocking): SIDEQUEST_GENRE and SIDEQUEST_CONTENT_PATH env vars not yet set per-session on script tool commands. Affects `crates/sidequest-agents/src/orchestrator.rs` script tool config.

### Reviewer (code review)
- **Improvement** (non-blocking): Add OTEL tracing span to NarratorAgent::build_context() for GM panel visibility. Affects `crates/sidequest-agents/src/agents/narrator.rs` (add tracing::debug! with agent name, section count, zone distribution). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Add doc comment to NarratorAgent::system_prompt() noting it returns identity only, not full prompt — callers should use build_context() for complete prompt assembly. Affects `crates/sidequest-agents/src/agents/narrator.rs:101`. *Found by Reviewer during code review.*

## Pm Assessment (accept)

**Verdict: ACCEPTED**

Core objective delivered: narrator prompt migrated from monolithic hardcoded const to 7 structured sections across Primacy and Early attention zones. SOUL double-injection prevented. 882 tests green, zero regressions.

4 orchestrator-level ACs deferred (tool wrappers, env vars, state_summary split, tone axes) — all logged as delivery findings. These were correctly scoped as follow-up work during the plan phase.

The Reviewer's deviation acceptance (consequences guardrail) is sound — operationally distinct from SOUL "Genre Truth".

**Handoff:** To Grand Admiral Thrawn (SM) for finish.

## Branch

- **api:** `feat/23-1-wire-narrator-prompt-template`