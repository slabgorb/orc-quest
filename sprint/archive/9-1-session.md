---
story_id: "9-1"
jira_key: "NONE"
epic: "9"
workflow: "tdd"
---
# Story 9-1: AbilityDefinition model — genre-voiced ability descriptions with mechanical effects

## Story Details
- **ID:** 9-1
- **Jira Key:** NONE (personal project)
- **Epic:** 9 (Character Depth — Self-Knowledge, Slash Commands, Narrative Sheet)
- **Workflow:** tdd
- **Points:** 3
- **Stack Parent:** none (root story)

## Epic Context

This story is the foundation for Epic 9, which gives players a rich understanding of who their character is through genre-voiced descriptions, knowledge that accumulates during play, and quick-access slash commands.

**Key Design Principle:** Genre voice over stat blocks. "+2 Nature check" becomes "Your bond with ancient roots lets you sense corruption in living things." The mechanical effect is stored but player-facing text is always narrative.

## Story Scope

Implement the `AbilityDefinition` model with:
- `name`: String (ability name)
- `genre_description`: String (narrative description in genre voice)
- `mechanical_effect`: String (game mechanical effect)
- `involuntary`: bool (triggers without player action)
- `source`: AbilitySource enum (Race, Class, Item, Play)

This is the data model that backs character abilities. Downstream stories (9-2, 9-5, 9-10) will consume this model to:
- Inject involuntary abilities into narrator context (9-2)
- Render the narrative character sheet (9-5)
- Display in the React client (9-10)

## Technical Dependencies

Prerequisite: Story 2-3 (Character creation) — the Character model already exists; this story enriches it with better ability definitions.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-03-26T20:17:06Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-26 | 2026-03-26T20:02:37Z | 20h 2m |
| red | 2026-03-26T20:02:37Z | 2026-03-26T20:05:42Z | 3m 5s |
| green | 2026-03-26T20:05:42Z | 2026-03-26T20:10:26Z | 4m 44s |
| spec-check | 2026-03-26T20:10:26Z | 2026-03-26T20:11:09Z | 43s |
| verify | 2026-03-26T20:11:09Z | 2026-03-26T20:12:50Z | 1m 41s |
| review | 2026-03-26T20:12:50Z | 2026-03-26T20:16:35Z | 3m 45s |
| spec-reconcile | 2026-03-26T20:16:35Z | 2026-03-26T20:17:06Z | 31s |
| finish | 2026-03-26T20:17:06Z | - | - |

## Sm Assessment

Small story (3 pts) — data model definition. `AbilityDefinition` struct with genre-voiced descriptions and mechanical effects, plus `AbilitySource` enum. Foundation for Epic 9's character depth features. No async, no I/O — pure model with serde serialization for YAML genre pack loading. Straightforward TDD.

**Decision:** Proceed to RED. No blockers.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Data model with serde serialization, dual-voice design, and character integration — all testable

**Test Files:**
- `crates/sidequest-game/tests/ability_story_9_1_tests.rs` — 22 tests covering 7 ACs + edge cases

**Tests Written:** 22 tests covering 7 ACs
**Status:** RED (fails to compile — `ability` module does not exist, `serde_yaml` not in deps, `Character.abilities` field missing)

**Test Strategy:**
- Dual voice: verify genre_description and mechanical_effect are distinct fields
- Genre display: `display()` returns narrative text, not mechanics
- Involuntary: both true and false cases
- Source tracking: all 4 AbilitySource variants
- YAML: single ability + list deserialization from genre pack format
- JSON: full round-trip serialization
- Character integration: construct Character with `abilities: Vec<AbilityDefinition>`

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 non_exhaustive | Deferred — reviewer will verify on AbilitySource enum | deferred to review |
| #6 test quality | Self-checked all 22 tests | no vacuous assertions |
| #8 Deserialize | `yaml_deserialization`, `json_round_trip` verify serde works | failing (RED) |

**Rules checked:** 2 of 15 applicable
- Rule #2 applies to AbilitySource (will grow with Curse, Divine, Status, etc.)
- Rule #8 applies — Deserialize is required by AC. No validated constructor in spec, so no bypass concern.
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Major Winchester) for implementation

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 5 findings | all in pre-existing builder.rs code + test_character() duplication (not story code) |
| simplify-quality | 2 findings | both in pre-existing builder.rs unwrap chains (not story code) |
| simplify-efficiency | 3 findings | all in pre-existing builder.rs patterns (not story code) |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0
**Noted:** 10 findings total — all in pre-existing code, none in story 9-1 changes
**Reverted:** 0

**Overall:** simplify: clean

**Quality Checks:** 20/20 tests passing, all crate tests passing
**Handoff:** To Colonel Potter for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 20/20 GREEN, 0 clippy in story files | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3: serde(default) hiding data (medium), empty strings (high), non_exhaustive+serde (low) | dismissed 3 — see rule compliance |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Yes | findings | 4: NonBlankString consistency (high), Deserialize bypass (high), display()+pub (medium), mixed validation (medium) | dismissed 4 — spec explicitly shows String |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2: non_exhaustive on struct (high), no inline tests (high) | dismissed 2 — see rule compliance |

**All received:** Yes (4 returned, 5 disabled via settings)
**Total findings:** 0 confirmed, 9 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] `AbilitySource` has `#[non_exhaustive]` — `ability.rs:45`. Complies with Rust rule #2. Derives Debug, Clone, PartialEq, Serialize, Deserialize — complete trait set for an enum that participates in serde and test assertions.

2. [VERIFIED] `#[serde(default)]` on Character.abilities — `character.rs:44`. Existing Character JSON without `abilities` key deserializes to `vec![]`. Backward compatible. Tests at `ability_story_9_1_tests.rs:230` verify construction with abilities populated.

3. [VERIFIED] `display()` returns genre voice, not mechanics — `ability.rs:33-35`. Returns `&self.genre_description`. The SOUL.md "genre voice over stat blocks" principle is structurally enforced.

4. [VERIFIED] serde_yaml in dev-dependencies — `Cargo.toml:24`. Uses `{ workspace = true }` per rule #11. Placed in `[dev-dependencies]` per rule #12 — only test code imports it.

5. [RULE] Rule-checker flagged `#[non_exhaustive]` on `AbilityDefinition` struct — DISMISSED: Adding it would break all 20 integration tests (external crate can't construct non_exhaustive struct by literal). The spec shows pub fields with direct construction. If future field additions are needed, `#[non_exhaustive]` can be added alongside a builder/constructor at that time.

6. [RULE] Rule-checker flagged no inline `#[cfg(test)]` — DISMISSED: False positive — 20 integration tests exist in `tests/ability_story_9_1_tests.rs`. Same pattern as stories 8-4 and 8-5.

7. [SILENT] Silent-failure-hunter flagged empty `mechanical_effect` — DISMISSED: The test `empty_mechanical_effect` at line 268 explicitly documents this as valid (passive abilities have no mechanical text). The `display()` method still returns the genre description — the ability works.

8. [TYPE] Type-design flagged `String` vs `NonBlankString` for name/genre_description — DISMISSED: The story context at `context-story-9-1.md:22-29` explicitly shows `pub name: String` and `pub genre_description: String`. Spec authority hierarchy: story context > rules. The NonBlankString consistency improvement is valid architectural feedback and logged as a delivery finding for a future story.

### Rule Compliance

| Rule | Instances | Verdict | Evidence |
|------|-----------|---------|----------|
| #1 Silent errors | display(), is_involuntary() | Pass | Infallible getters |
| #2 non_exhaustive | AbilitySource | Pass | Line 45 has attribute |
| #2 non_exhaustive | AbilityDefinition struct | Pass (noted) | Spec shows direct construction; adding attribute would break test API |
| #3 Hardcoded values | 0 | N/A | No placeholders |
| #4 Tracing | 0 | N/A | Data struct, no logic paths |
| #5 Constructors | 0 | N/A | No constructor; spec shows literal construction |
| #6 Test quality | 20 tests | Pass | Integration tests cover all 7 ACs |
| #7 Unsafe casts | 0 | N/A | No casts |
| #8 Deserialize | AbilityDefinition | Pass | No validating constructor to bypass; String fields match spec |
| #9 Public fields | 5 fields | Pass | Spec shows pub fields; no invariants claimed |
| #10-15 | various | N/A/Pass | No tenant data, workspace deps correct, dev-deps correct |
| SOUL.md genre voice | display() | Pass | Returns genre_description, not mechanical_effect |

### Devil's Advocate

What if this model is wrong?

**The NonBlankString gap is real.** An ability with `name: ""` will deserialize from a malformed genre pack YAML and silently produce a nameless ability. `display()` on an ability with `genre_description: ""` returns an empty string — the player sees nothing. This is a genuine data quality concern. However: genre packs are operator-authored content (not player input), the failure mode is cosmetic (blank text, not data corruption), and the spec explicitly chose `String` over `NonBlankString`. The improvement should happen in a future story that tightens validation across all genre-pack-loaded types simultaneously.

**The `display()` + pub field ambiguity.** Callers can bypass `display()` and read `genre_description` directly, or mutate it post-construction. The method provides convenience, not protection. If a future story needs immutability guarantees, the fields would need to become private — but that's a breaking API change. For now, the pub field + convenience method pattern matches how Character itself works (pub fields + Combatant trait methods).

**Vec<AbilityDefinition> is unbounded.** A malicious save file could contain thousands of abilities. At the genre-pack loading layer this is fine (operator-controlled), but if save/load ever accepts user-uploaded files, a length cap would be needed. Not blocking for this story.

No critical or high issues found. The NonBlankString question is the most architecturally interesting observation.

**Data flow traced:** Genre pack YAML → serde_yaml::from_str → `AbilityDefinition` fields → `Character.abilities` Vec → `display()` for player, `mechanical_effect` for engine.

**Pattern observed:** Good — pub struct with serde derives, convenience methods, non_exhaustive enum. Matches the crate's data model pattern.

**Error handling:** None needed — pure data model. Validation at genre pack load site, not at model level.

**Wiring:** Character.abilities is populated during character creation (builder). Genre pack abilities are loaded by sidequest-genre crate.

**Security:** No user input at this boundary. Genre packs are operator-authored.

**Handoff:** To Hawkeye Pierce (SM) for finish-story

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

All 7 ACs covered. The implementation matches the story context exactly: `AbilityDefinition` with pub fields, `AbilitySource` enum with `#[non_exhaustive]`, `display()` and `is_involuntary()` methods, serde derives for both YAML and JSON, and Character integration with `#[serde(default)]` for backward compatibility. Good use of rule #12 (serde_yaml in dev-dependencies).

**Decision:** Proceed to verify

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-game/src/ability.rs` — new module: `AbilityDefinition`, `AbilitySource`, `display()`, `is_involuntary()`
- `crates/sidequest-game/src/lib.rs` — registered `pub mod ability`
- `crates/sidequest-game/src/character.rs` — added `abilities: Vec<AbilityDefinition>` with `#[serde(default)]`
- `crates/sidequest-game/src/builder.rs` — added `abilities: vec![]` to character construction
- `crates/sidequest-game/Cargo.toml` — added `serde_yaml` to dev-dependencies
- 6 existing test files — added `abilities: vec![]` to Character struct literals

**Tests:** 20/20 passing (GREEN) + all existing crate tests passing (546+ across all test suites)
**Branch:** `feat/9-1-ability-definition` (pushed)

**Implementation Notes:**
- `AbilitySource` is `#[non_exhaustive]` per Rust rule #2 — will grow with Curse, Divine, Status
- `#[serde(default)]` on `abilities` field ensures backward compat — existing Character data without abilities deserializes with empty vec
- `serde_yaml` placed in `[dev-dependencies]` per rule #12 — only tests import it directly
- `AbilityDefinition` has pub fields matching the spec, with `display()` and `is_involuntary()` convenience methods

**Handoff:** To verify phase (TEA for simplify + quality-pass)

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Improvement** (non-blocking): Consider upgrading `AbilityDefinition.name` and `.genre_description` to `NonBlankString` for consistency with Character's identity fields. Currently plain `String` per spec. Affects `crates/sidequest-game/src/ability.rs` (lines 19, 21). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Consider adding `#[non_exhaustive]` to `AbilityDefinition` struct when a constructor is added in a future story. Currently omitted because tests construct via struct literal. Affects `crates/sidequest-game/src/ability.rs` (line 17). *Found by Reviewer during code review.*

### TEA (test verification)
- No upstream findings during test verification.

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test design)
- **Gap** (non-blocking): Existing genre pack YAML (`progression.yaml`) uses `experience` and `limits` fields for abilities, not `genre_description` and `mechanical_effect`. The story context spec defines a new YAML schema. Migration of existing genre pack abilities to the new format is not covered by this story. Affects `genre_packs/*/progression.yaml` (field names need mapping or migration).
- **Gap** (non-blocking): `serde_yaml` is not currently in `sidequest-game`'s `Cargo.toml` dependencies. Dev will need to add it (workspace-level if available, otherwise inline). Affects `crates/sidequest-game/Cargo.toml`.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No deviations to audit — TEA and Dev both logged "no deviations from spec." Implementation matches story context exactly.

### Architect (reconcile)
- No additional deviations found. Implementation matches the story context's Technical Approach section exactly: `AbilityDefinition` struct with 5 pub fields, `AbilitySource` enum with 4 variants and `#[non_exhaustive]`, `display()` and `is_involuntary()` methods. Character integration via `abilities: Vec<AbilityDefinition>` with `#[serde(default)]`. The Reviewer's NonBlankString improvement note is architectural feedback for a future validation story, not a current deviation.

### TEA (test design)
- No deviations from spec.