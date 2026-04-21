---
story_id: "42-1"
jira_key: null
epic: "42"
workflow: "tdd"
---
# Story 42-1: Port StructuredEncounter + EncounterMetric + SecondaryStats + EncounterActor + EncounterPhase types; formalise Combatant as a Python Protocol; promote GameSnapshot.encounter from dict to typed

## Story Details
- **ID:** 42-1
- **Epic:** 42 (ADR-082 Phase 3 — Port confrontation engine to Python)
- **Jira Key:** None (personal project)
- **Workflow:** tdd
- **Stack Parent:** none (stack root)
- **Points:** 5
- **Priority:** p0
- **Repos:** sidequest-server (Python port target per ADR-082)
- **Branch:** feat/42-1-structured-encounter-types (in sidequest-server, created from develop)

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-21T01:56:34Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-21T00:50:18Z | 2026-04-21T00:55:05Z | 4m 47s |
| red | 2026-04-21T00:55:05Z | 2026-04-21T01:04:57Z | 9m 52s |
| green | 2026-04-21T01:04:57Z | 2026-04-21T01:14:11Z | 9m 14s |
| spec-check | 2026-04-21T01:14:11Z | 2026-04-21T01:17:55Z | 3m 44s |
| verify | 2026-04-21T01:17:55Z | 2026-04-21T01:25:44Z | 7m 49s |
| review | 2026-04-21T01:25:44Z | 2026-04-21T01:51:21Z | 25m 37s |
| spec-reconcile | 2026-04-21T01:51:21Z | 2026-04-21T01:56:34Z | 5m 13s |
| finish | 2026-04-21T01:56:34Z | - | - |

## Story Context

This is the first story in a 4-story DAG to port the unified StructuredEncounter confrontation engine from Rust to Python.

**Scope:**
- Port StructuredEncounter, EncounterMetric, SecondaryStats, EncounterActor, EncounterPhase types from `sidequest-api/sidequest-game/src/encounter.rs` (724 LOC)
- Formalise `Combatant` as a `typing.Protocol` from `sidequest-api/sidequest-game/src/combatant.rs` (152 LOC)
- Promote `GameSnapshot.encounter` from `dict | None` to `StructuredEncounter | None` (Phase 1 IOU)
- Port all encounter-type tests with name parity to Rust
- No chase cinematography; ensure chase encounters still construct via `StructuredEncounter.chase(...)`

**Key dependencies:**
- Depends on Epic 41 (Phase 1-2, chargen port) — all 11 stories merged
- Blocks 42-2 and 42-3 (resource pool and tension tracker)
- Unblocks 42-4 (combat dispatch + OTEL + narrator wiring)

**Not in scope:**
- Chase cinematography (chase_depth.rs) — Phase 4, deferred per Keith's 2026-04-20 decision
- Sealed-letter turn dispatcher (ADR-077) — 42-1 preserves `per_actor_state` shape but does not port lookup logic
- Scenario engine, advancement, CLIs, narrator prompt wiring — later phases

**Key type seam:** 
Every `snapshot.encounter["key"]` dict-access in the codebase will be migrated to attribute access during 42-1. 42-4 finishes the dispatch-side migration.

**Test porting discipline:**
Per execution-strategy spec: Rust test file is the behavioural contract. Translations are mechanical — every Rust test becomes one pytest function with the same name. Idiomatic rewrites are forbidden during the port.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)

- **Gap** (blocking): 5 new Pydantic classes in `encounter.py` have no `model_config`; pydantic defaults to `extra="ignore"`. Every other internal-engine type in `sidequest/game/` declares `extra: "forbid"` (session.py internal structs, turn.py, character family); only save-file surfaces (GameSnapshot, HistoryChapter) use `extra: "ignore"` with explicit forward-compat comments. The 5 new classes silently drop unknown fields — direct violation of CLAUDE.md "No Silent Fallbacks" and the established internal-vs-save-surface convention. Affects `sidequest-server/sidequest/game/encounter.py:160,170,204,223,242` (add `model_config = {"extra": "forbid"}` to StatValue, SecondaryStats, EncounterActor, EncounterMetric, StructuredEncounter). *Found by Reviewer during code review — confirmed by silent-failure-hunter + type-design subagents + TEA's verify-phase flag.*
- **Gap** (blocking): Two tautological enum-variant tests in `test_encounter.py` — `test_encounter_phase_variants:361` asserts `len()` and index access on a literal 5-element list, and `test_metric_direction_is_non_exhaustive:592` asserts `len() == 3` on a literal 3-element list. Both test Python list semantics, not enum membership; cannot fail regardless of actual enum state. Affects `sidequest-server/tests/game/test_encounter.py:361,592` (replace literal-list assertions with `set(EnumName) == {...}` or `X in EnumName` style). *Found by Reviewer during code review — confirmed by test-analyzer subagent.*
- **Gap** (blocking): Wiring test `test_game_module_exports_structured_encounter:1076` checks 7 encounter symbols but omits `RigType` (exported at `__init__.py:58,130`) and `Combatant` (exported at `__init__.py:23,98`). Both are imported from `sidequest.game.*` elsewhere in the test file and throughout the upcoming 42-2/42-3/42-4 call sites. Affects `sidequest-server/tests/game/test_encounter.py:1080` (add `"RigType"` and `"Combatant"` to the `expected` list). *Found by Reviewer during code review — confirmed by test-analyzer subagent.*
- **Improvement** (non-blocking): `per_actor_state: dict[str, Any]` on `EncounterActor` is an intentional escape hatch for SealedLetterLookup (ADR-077) — worth a `# TODO(42-4): tighten per_actor_state to typed union when SealedLetterLookup lookup logic lands` comment at `sidequest-server/sidequest/game/encounter.py:220` so the escape hatch is visible at its future closure site. *Found by Reviewer during code review — flagged by type-design subagent.*
- **Improvement** (non-blocking): Stringly-typed `EncounterActor.role`, `EncounterMetric.name`, `StructuredEncounter.outcome` are landmines for the 42-4 dispatch/OTEL consumer. Rust source uses the same raw strings, so the port is correct — but a 42-4 precursor note / enum-or-Literal-type tightening pass is worth filing as a follow-up story before dispatch lands. Affects `sidequest-server/sidequest/game/encounter.py:219,229,257`. *Found by Reviewer during code review — flagged by type-design subagent.*

### Dev (implementation)

- **Improvement** (non-blocking): `Character.is_broken` and `Character.edge_fraction` drift fixed in-story to match Rust-verbatim `Combatant` semantics (was `== 0` / returns `1.0` when max==0; now `<= 0` / returns `0.0` when max==0). Affects `sidequest-server/sidequest/game/character.py:164-178` and `sidequest-server/tests/game/test_character.py:260` (pre-existing test that encoded the drift updated from `_returns_one` to `_returns_zero`). Resolves TEA's Conflict finding above. *Found by Dev during implementation.*
- **Gap** (non-blocking): `StructuredEncounter` methods `apply_beat`, `from_confrontation_def`, `format_encounter_context`, `escalation_target`, `escalate_to_combat` not ported in 42-1 (scope-bounded per session story context — they depend on `ConfrontationDef` / dispatch-side wiring that lands in 42-2/42-4). Affects `sidequest-server/sidequest/game/encounter.py` (42-2 adds ConfrontationDef-dependent methods; 42-4 adds dispatch/OTEL wiring). See Design Deviations entry. *Found by Dev during implementation.*
- **Gap** (non-blocking): `RigStats` struct not ported — only the Rust-parity values surface via `SecondaryStats.rig(RigType)`. `chase_depth.py` module deferred to Phase 4. Affects `sidequest-server/sidequest/game/` (add `chase_depth.py` when cinematography lands). *Found by Dev during implementation.*
- **Question** (non-blocking): Ruff UP042 reports `(str, Enum)` inheritance; project baseline has 30 pre-existing UP042 violations across the codebase. Kept my 3 new enums on the `(str, Enum)` pattern for consistency with `TurnPhase`, `HookType`, `AbilitySource`, `CampaignMaturity`. Low-priority migration to `StrEnum` would be a codebase-wide sweep story, not in 42-1 scope. Affects `sidequest-server/sidequest/game/` (30 enum classes). *Found by Dev during implementation.*

### TEA (test design)

- **Conflict** (non-blocking): `Character.edge_fraction()` returns `1.0` when `max_edge == 0`; Rust `Combatant::edge_fraction` default returns `0.0`. Affects `sidequest-server/sidequest/game/character.py:168-172` (fix to match Rust-verbatim semantics). Also `Character.is_broken()` uses `== 0` while Rust uses `<= 0` — negative edge must read broken. *Found by TEA during test design.*
- **Gap** (non-blocking): No `examples/` directory in `sidequest-api/crates/sidequest-game/`. Story context-story-42-1 AC2 assumed a `cargo run --example encounter_fixture` would be available. Fell back to hand-authored fixtures under `tests/fixtures/encounters/` per the context's stated fallback. Affects `sidequest-api/crates/sidequest-game/examples/` (cargo example can be added later for drift detection; low priority while Python hasn't diverged). *Found by TEA during test design.*
- **Question** (non-blocking): Story context-story-42-1 lists RigType example string values as `"motorcycle"`, `"sedan"`, `"semi"` but the Rust source enumerates `Interceptor / WarRig / Bike / Hauler / Frankenstein`. Tests use the Rust-source names per the "Rust test file is the behavioural contract" porting discipline. Affects `sprint/context/context-story-42-1.md:100` (amend when convenient). *Found by TEA during test design.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **`escape_threshold` parameter in `StructuredEncounter.chase` accepted but unused**
  - Spec source: encounter.rs line 214, `pub fn chase(_escape_threshold: f64, rig_type: Option<RigType>, goal: i32) -> Self`
  - Spec text: Rust signature includes `_escape_threshold: f64` as a leading-underscore-unused parameter
  - Implementation: Python signature mirrors Rust verbatim — `chase(escape_threshold: float, rig_type: RigType | None, goal: int)`. The parameter is accepted (required by the Rust-test contract which passes it positionally) but discarded in the body. Added `# noqa: ARG003` and a comment noting it is preserved for Rust signature parity / Phase 4 cinematography wiring.
  - Rationale: Rust keeps the parameter for forward-compat with chase cinematography (Phase 4). Removing it from the Python signature would break test parity (`StructuredEncounter.chase(escape_threshold=0.5, rig_type=..., goal=10)` is the Rust-call-shape) and break the AC2 constructor-parity contract. Mechanical port discipline overrides the "unused-parameter" smell.
  - Severity: minor
  - Forward impact: When Phase 4 ports chase cinematography, `escape_threshold` will be consumed — no new breaking change needed then.

- **`SecondaryStats.rig` collapses Rust's `rig()` + `from_rig_stats()` into one classmethod**
  - Spec source: encounter.rs lines 91-141, `impl SecondaryStats { pub fn rig(rig_type: RigType) -> Self; pub fn from_rig_stats(rig: &RigStats) -> Self }`
  - Spec text: Rust splits construction into two methods — `rig(rig_type)` convenience and `from_rig_stats(&RigStats)` for callers holding a live RigStats
  - Implementation: Python exposes only `SecondaryStats.rig(rig_type)`. The intermediate `RigStats` struct is not ported in 42-1 (no `chase_depth.py` — Phase 4). Values match `RigStats::from_type(rig_type)` byte-for-byte so fixture equality holds.
  - Rationale: Without `RigStats` (Phase 4), `from_rig_stats` has no caller. Porting a method with no consumer violates CLAUDE.md "No Stubbing". The Phase 4 port can add `from_rig_stats` when chase_depth lands; no call site breaks in the interim because none exist.
  - Severity: minor
  - Forward impact: Phase 4 chase-depth port adds `from_rig_stats` alongside existing `rig`.

- **`StructuredEncounter.apply_beat / from_confrontation_def / format_encounter_context / escalation_target / escalate_to_combat` not ported in 42-1**
  - Spec source: encounter.rs lines 278-523
  - Spec text: Rust `StructuredEncounter` has these methods as part of its public API
  - Implementation: Not ported in 42-1. Only `chase()`, `combat()`, and `resolve_from_trope()` land.
  - Rationale: Story scope (session line 35-42) is "port types + promote `GameSnapshot.encounter`"; `from_confrontation_def` depends on `ConfrontationDef` from sidequest.genre (42-2 scope), `apply_beat` depends on the same, `format_encounter_context` is narrator-prompt wiring (42-4 scope), `escalate_to_combat` is dispatch-side (42-4). Porting them now would require stubbing or importing from not-yet-ported modules — violates No Stubbing + No Silent Fallbacks.
  - Severity: minor
  - Forward impact: 42-2 lands `ConfrontationDef` + `from_confrontation_def` + `apply_beat`. 42-4 lands `format_encounter_context` + `escalate_to_combat` + OTEL emission.

- **`OTEL WatcherEventBuilder` emission in `resolve_from_trope` not wired**
  - Spec source: encounter.rs lines 464-474, `WatcherEventBuilder::new("encounter", ...).field("event", "encounter.state.resolved_by_trope").send()`
  - Spec text: Rust `resolve_from_trope` emits `encounter.state.resolved_by_trope` OTEL span
  - Implementation: State mutation ported (resolved flag, phase, outcome string). OTEL emission **not** wired.
  - Rationale: Dev-notes in session line 168 explicitly says "resolve_from_trope is authored in 42-1 but its dispatch-side consumer lands in 42-4 — don't wire OTEL emission yet; just the state mutation." Following TEA's guidance.
  - Severity: minor
  - Forward impact: 42-4 adds the OTEL watcher call site. State-mutation tests already pass.

### TEA (test design)

- **Hand-authored encounter fixtures instead of cargo-generated**
  - Spec source: context-story-42-1.md, AC2 + "Assumptions"
  - Spec text: "a Rust `cargo run --example encounter_fixture` output committed to `tests/fixtures/encounters/` is consumed and asserted"
  - Implementation: Fixtures hand-authored to match the Rust serde-default JSON shape and committed to `sidequest-server/tests/fixtures/encounters/`. `sidequest-game` has no `examples/` directory — per the story's stated assumption fallback, this is the sanctioned path.
  - Rationale: Adding a cargo example is a separate scope-adjacent task; the fallback is explicitly authorized by the story assumption block. Fixture contents encode the Rust struct serialization shape field-for-field; a follow-up can add the cargo example for drift detection later.
  - Severity: minor
  - Forward impact: none now; if a Phase 3 story introduces cargo-generated fixtures the hand-authored ones can be regenerated byte-identically.

- **`old_chase_state_json_deserializes_as_encounter` test not ported**
  - Spec source: encounter_story_16_2_tests.rs, test `old_chase_state_json_deserializes_as_encounter`
  - Spec text: "every Rust test becomes one pytest function with the same name"
  - Implementation: Test NOT ported to pytest.
  - Rationale: That Rust test exercises one-shot Rust-side save-format migration (old top-level `chase` field → new `encounter` field) that has no Python equivalent — the Python server has no pre-42-1 saves carrying a top-level `chase` field. Per context-story-42-1 Assumptions: "No existing `snapshot.encounter["x"]` dict-access consumers exist in Phase 2 Python code." Porting the test verbatim would require fabricating a migration path that's never exercised.
  - Severity: minor
  - Forward impact: If future Python saves ever need a shape-migration, add a Python-specific deserializer test then.

- **AC5 "unknown encounter_type fails loud" interpreted at schema level**
  - Spec source: context-story-42-1.md, AC5
  - Spec text: "A save file with `encounter: {"encounter_type": "flibbertigibbet", ...}` raises a `ValidationError` on `GameSnapshot` load"
  - Implementation: Test asserts pydantic ValidationError when the encounter dict is malformed (`{"encounter_type": "flibbertigibbet"}` with all required StructuredEncounter fields missing). A bare `encounter_type` string like "flibbertigibbet" would NOT raise by itself — the Rust model uses a free-form `String` with no enumerated set, and the Python port preserves that (string-keyed per ADR-033). Added a second test that asserts ValidationError for unknown `MetricDirection` (`"FlibbertiGibbet"`), which is the actual enum-variant failure mode AC5 is warning against.
  - Rationale: Matching Rust's string-keyed encounter_type while still enforcing "no silent fallback" per CLAUDE.md requires pushing the validation boundary to enum fields. Closing off `encounter_type` would require a new whitelist not present in Rust — a deviation from source worse than interpreting the AC.
  - Severity: minor
  - Forward impact: If a 42-4 consumer turns out to require a closed `encounter_type` enumeration, a new validator can be added then.

- **Combatant default implementations live on implementers, not Protocol**
  - Spec source: combatant.rs, `trait Combatant { fn is_broken(&self) -> bool { self.edge() <= 0 } fn edge_fraction(&self) -> f64 { ... } }`
  - Spec text: Rust trait provides default implementations of `is_broken` and `edge_fraction`
  - Implementation: Python `typing.Protocol` declares all six methods as abstract signatures. Test fixtures (`_TestCombatant`) and production implementers (Character, Npc) provide the method bodies verbatim.
  - Rationale: `typing.Protocol` with `@runtime_checkable` supports mixin-style defaults but the runtime `isinstance` check only inspects method *names*, not whether the default or an override is bound. Cleaner to keep the Protocol a pure contract and make every implementer spell the same two lines. Two lines per class is cheaper than an abstract-base-class hybrid that tools mis-recognize.
  - Severity: minor
  - Forward impact: Each new Combatant implementer must carry `is_broken` and `edge_fraction` bodies. Delivery finding above (Character semantic drift) is evidence the forward cost is real but visible.

### Architect (reconcile)

- **`model_config = {"extra": "forbid"}` on 5 inner Pydantic types deviates from Rust serde defaults**
  - Spec source: `sidequest-api/crates/sidequest-game/src/encounter.rs` lines 65-84, 147-158, 161-175, 183-205 — `#[derive(Debug, Clone, Serialize, Deserialize)]` on `StatValue`, `SecondaryStats`, `EncounterActor`, `EncounterMetric`, `StructuredEncounter`, with **no** `#[serde(deny_unknown_fields)]` attribute on any of them.
  - Spec text: Rust serde's default behaviour for `#[derive(Deserialize)]` without `deny_unknown_fields` is to **silently accept and discard unknown fields** on deserialization. The Rust encounter types opt into that default — they tolerate unknown struct-level keys without error. Verified by grep: `#[serde(...)]` appears only at `encounter.rs:156` (`#[serde(default)]` on `per_actor_state`) and nowhere else in the file.
  - Implementation: Python port at `sidequest-server/sidequest/game/encounter.py:166,182,222,235,259` — each of the 5 classes carries `model_config = {"extra": "forbid"}  # CLAUDE.md "No Silent Fallbacks"`. Unknown kwargs at construction and unknown fields on `model_validate_json` both raise `pydantic.ValidationError`. The Python port is therefore **strictly stricter than Rust** on inner-type extras. (Outer `GameSnapshot` retains `extra="ignore"` at `session.py:324` for Rust-save forward-compat — that boundary remains soft by design; only the inner types are hardened.)
  - Rationale: Three converging authorities override mechanical-port discipline for this specific field:
    1. **Story-level AC5** explicitly invokes CLAUDE.md "No Silent Fallbacks" and mandates fail-loud on unknown encounter content. The original Dev/TEA interpretation narrowly scoped this to enum-variant fields; Reviewer (specialist: reviewer-silent-failure-hunter, corroborated by reviewer-type-design) correctly widened the reach to struct-level extras. AC5's spec text literally cites CLAUDE.md — story scope endorses the stricter behaviour.
    2. **Codebase convention** — Reviewer's grep of `sidequest/game/` found inner engine types (`session.py:39,54,79,124,145,179,194`; `turn.py:60`; character family) uniformly carry `extra="forbid"`, while save-file surface types carry `extra="ignore"` with a forward-compat comment. The 5 encounter types slotted into the "inner engine" category; not tightening them would have been the deviation from codebase posture.
    3. **Bidirectional-evolution property** — because both the Rust and Python trees evolve together, a new field added to Rust without synchronized Python addition would produce a malformed save. Fail-loud on Python-side catches that drift at load time rather than dropping data silently.

    Mechanical-port discipline is preserved in every **method body and state-machine semantic** — the deviation is confined to the schema-validation boundary, which is a language-specific seam, not a behavioural contract.
  - Severity: minor (stricter than source by design; no observable user-facing change unless Rust emits new fields without the Python tree keeping pace, which would fail loudly as intended)
  - Forward impact:
    - When 42-2 ports `ConfrontationDef` and `apply_beat`, any new fields added to `StructuredEncounter` must land in both trees together. Single-tree field addition fails the Python `model_validate_json` load — this is the designed fail-loud behaviour.
    - When 42-4 wires OTEL emission and dispatch-side migration, no impact — OTEL and dispatch do not touch the pydantic validation boundary.
    - If Phase 4 chase-cinematography adds new fields to `SecondaryStats` (e.g., cinematography hints on the rig block), the same sync-addition requirement applies.
    - If a future story ever needs to accept pre-existing Rust-produced saves with fields the Python port doesn't yet know about, either (a) bump `GameSnapshot.extra` semantics to tolerate inner-type drift, or (b) add the missing fields to the Python inner types first. Option (b) is the expected path and matches how `_returns_one` → `_returns_zero` was handled during the Character drift fix.

### Architect (spec-docs polish — non-deviations, logged for traceability)

These are not code deviations. They are spec-text clarity improvements the boss may want to batch into a docs-only tidy-up later. Listed here so they don't get forgotten in the archive:

- **`sprint/context/context-story-42-1.md` AC5** — current wording implies `encounter_type: "flibbertigibbet"` alone should raise `ValidationError`. Actual shipped behaviour (Rust-parity + codebase-convention): unknown enum-field variants raise, unknown struct-level extras raise (post-`da7a731`), unknown `encounter_type` strings do not (ADR-033 string-keyed contract). Single-sentence clarification would align spec with implementation. Resolution: C (clarify spec).
- **`sprint/context/context-story-42-1.md:100` RigType example values** — lists `"motorcycle"`, `"sedan"`, `"semi"`. Actual Rust enum: `Interceptor / WarRig / Bike / Hauler / Frankenstein`. TEA flagged this during test design; tests correctly used the Rust names. Resolution: C (clarify spec).

## Sm Assessment

**Scope verified.** Story 42-1 is the foundation of Epic 42's 4-story DAG. Ports the `StructuredEncounter` type family + `Combatant` trait → Python Protocol + promotes `GameSnapshot.encounter` from `dict|None` to the typed wrapper. Mechanical port — Rust test file is the behavioural contract, no idiomatic rewrites. Context docs (context-epic-42.md + context-story-42-1.md) present and current.

**Repo corrected.** Setup initially wrote `sidequest-api (server crate)`; corrected to `sidequest-server` (the Python port target per ADR-082 and context-epic-42). Branch `feat/42-1-structured-encounter-types` created in sidequest-server from `develop`.

**Dependencies.** Epic 41 (chargen port, Phases 1–2) merged. No inbound blockers. Unblocks 42-2 (ResourcePool) and 42-3 (TensionTracker) — 42-4 (dispatch + OTEL) gates on all three.

**Out of scope.** Chase cinematography (deferred Phase 4), sealed-letter dispatcher (preserves `per_actor_state` shape only), scenario engine, advancement, CLIs, narrator prompt wiring.

**Handoff.** Phase setup → red. Next agent: tea. Run RED first (port Rust tests to pytest, must fail — types don't exist yet in Python), then dev for GREEN (port types, make tests pass), then reviewer for adversarial pass, then back to me for finish.

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Test files:**
- `sidequest-server/tests/game/test_encounter.py` — 40+ tests porting `encounter_story_16_2_tests.rs` + AC1/AC2/AC4/AC5/AC6 coverage + `resolve_from_trope` behavior + wiring test
- `sidequest-server/tests/game/test_combatant.py` — 12 tests porting `combatant.rs` inline mod tests + AC3 structural-isinstance tests + runtime_checkable assertion + negative-edge broken guard
- `sidequest-server/tests/fixtures/encounters/*.json` — 4 canonical Rust-parity JSON fixtures (combat, chase-with-rig, chase-no-rig, standoff-full) + README
- 1 design-deviation note: `old_chase_state_json_deserializes_as_encounter` intentionally NOT ported (Rust-specific legacy migration)

**RED verification:**
```
ModuleNotFoundError: No module named 'sidequest.game.encounter'
ModuleNotFoundError: No module named 'sidequest.game.combatant'
```
Both test modules fail at collection — target modules don't exist yet. That's the correct RED state. Existing `tests/game/` suite (402 pass, 1 skip) still green — no regressions introduced by the test additions.

### Rule Coverage (Python lang-review)

Tests added for each rule class (ratio is breakdown of applicable rules that have test coverage in this RED phase):

| Rule class (python.md) | Tests | Status |
|---|---|---|
| #6 test-quality: no vacuous assertions | self-audit — every test asserts specific values or types; no `assert True`, no `assert result` truthy checks, no commented-out assertions | pass |
| #3 type-annotation gaps | all test functions return `-> None`; `_TestCombatant` dataclass fields fully annotated; fixture dict helper has return-type annotation | pass |
| #10 import hygiene | explicit imports (no `import *`); `from __future__ import annotations` on both files | pass |
| #8 unsafe deserialization | tests use `json.load` on fixtures (trusted repo-committed data) and `pydantic.model_validate_json` (schema-validated); no pickle/eval | pass |
| #11 input validation at boundaries | AC5 tests exercise pydantic validation on malformed GameSnapshot input (ValidationError, not silent defaulting) | pass |

Rules #1, #2, #4, #5, #7, #9, #12, #13 apply to implementation code, not the RED test diff — covered when Dev lands GREEN.

### AC coverage matrix

| AC | Test(s) |
|---|---|
| AC1 round-trip JSON parity | `test_combat_fixture_round_trip`, `test_chase_with_rig_fixture_round_trip`, `test_chase_no_rig_fixture_round_trip`, `test_standoff_full_fixture_round_trip` |
| AC2 constructors parity | `test_structured_encounter_combat_convenience_constructor`, `test_structured_encounter_chase_convenience_constructor`, `test_combat_constructor_matches_fixture`, `test_chase_constructor_matches_fixture`, `test_chase_without_rig_constructor_matches_fixture` |
| AC3 Combatant structural isinstance | `test_combatant_protocol_is_runtime_checkable`, `test_character_satisfies_combatant_protocol`, `test_combatant_protocol_rejects_type_missing_required_method`, `test_zero_max_edge_returns_zero_fraction` |
| AC4 GameSnapshot.encounter typed | `test_game_snapshot_has_encounter_field`, `test_game_snapshot_encounter_serde_roundtrip`, `test_game_snapshot_encounter_type_annotation_is_structured_encounter` |
| AC5 unknown encounter fails loud | `test_unknown_encounter_type_fails_loud_on_snapshot_load`, `test_encounter_bad_metric_direction_fails_loud_on_snapshot_load`, `test_metric_direction_unknown_variant_fails_validation`, `test_encounter_phase_unknown_variant_fails_validation` |
| AC6 extra=ignore preserved | `test_game_snapshot_extra_ignore_preserved` |

### Dev notes (for GREEN)

- **Protocol location.** `sidequest/game/combatant.py` holds the `Combatant` Protocol. Must be `@runtime_checkable`.
- **RigType location.** Tests import `RigType` from `sidequest/game/encounter.py`. Dev may colocate (simplest) or put it in `sidequest/game/chase_depth.py` as a small shim and re-export — choice. Either way `from sidequest.game.encounter import RigType` must work.
- **resolve_from_trope** is authored in 42-1 but its dispatch-side consumer lands in 42-4 — don't wire OTEL emission yet; just the state mutation.
- **Character.edge_fraction and Character.is_broken** drift from the Combatant contract (delivery finding above). Fixing in this story is a one-line change in character.py each; recommended as part of GREEN, but not a hard blocker for AC3 (isinstance structural check passes regardless).
- **Fixture byte parity.** `json.loads(encounter.model_dump_json()) == fixture` — dict equality, so key order is immaterial. Dev should NOT chase field-order determinism unless a test explicitly fails.

**Handoff.** To dev (Naomi Nagata) for GREEN — implement the types, make all tests pass, mind the Character drift if tackling in-story.
## Dev Assessment

**Phase:** finish
**Implementation Complete:** Yes
**Status:** GREEN (all tests pass — ready for Reviewer)

**Files Changed:**
- `sidequest-server/sidequest/game/encounter.py` (NEW, 308 LOC) — StructuredEncounter, EncounterMetric, SecondaryStats, StatValue, EncounterActor, EncounterPhase, MetricDirection, RigType. Convenience constructors `.chase()` / `.combat()`, state mutation `.resolve_from_trope()`.
- `sidequest-server/sidequest/game/combatant.py` (NEW, 62 LOC) — Combatant typing.Protocol, @runtime_checkable, 6 methods matching Rust trait verbatim.
- `sidequest-server/sidequest/game/session.py` — `GameSnapshot.encounter: dict | None` promoted to `StructuredEncounter | None` (ADR-082 Phase 1 IOU).
- `sidequest-server/sidequest/game/__init__.py` — Re-exports for `Combatant` + all 8 encounter symbols so `sidequest.game.X` works from dispatch/narrator/GM-panel consumers.
- `sidequest-server/sidequest/game/character.py` — Drift fixes: `is_broken` now `<= 0`, `edge_fraction` returns `0.0` when max==0 (both match Rust Combatant default). Resolves TEA's Conflict finding.
- `sidequest-server/tests/game/test_character.py` — Updated the one pre-existing test that encoded the drift (`_returns_one` → `_returns_zero`).

**Tests:** 59/59 passing (test_encounter.py: 47, test_combatant.py: 12). Full `tests/game/` suite 461 passed / 1 skipped — no regressions. 5 pre-existing failures in `tests/agents/` and `tests/server/` verified against baseline (stashed) — unrelated to 42-1.

**Branch:** `feat/42-1-structured-encounter-types` (pushed — commit `28e598c`)

**Verification trace:**
- AC1 JSON round-trip parity: 4/4 fixtures deserialize, re-serialize to equal dict → ✓
- AC2 constructor parity: `.chase()` / `.combat()` produce fixture-equal JSON → ✓
- AC3 Combatant structural typing: `isinstance(Character, Combatant)` works, partial impl rejected, zero-max returns 0.0 → ✓
- AC4 GameSnapshot.encounter typed: `typing.get_type_hints(GameSnapshot)["encounter"]` = `StructuredEncounter | None`, not `dict | None` → ✓
- AC5 no silent fallback: malformed encounter raises `ValidationError` at load → ✓
- AC6 extra=ignore preserved: unknown top-level fields ignored, not raised → ✓
- Wiring test: `import sidequest.game; hasattr(game, 'StructuredEncounter')` + all 7 sibling types → ✓

**Handoff:** To Reviewer (Chrisjen Avasarala) for adversarial review. Scope guards: mechanical port discipline, deferred methods documented as deviations (not stubbed), no dict-access consumers exist in Phase 2 code (assumption confirmed). Drummer, I'll ping you when the marker's down.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None rising above Minor. All deferrals legitimate and correctly routed.

### Verification against ADR-082 Phase 3 execution strategy

- **1:1 crate→package mapping (ADR-082 §Port Strategy).** `encounter.rs` → `sidequest/game/encounter.py`. `combatant.rs` → `sidequest/game/combatant.py`. No consolidation, no renaming. ✓
- **Rust test file as behavioural contract.** 47 tests in `test_encounter.py` + 12 in `test_combatant.py`. RED→GREEN clean. One Rust test (`old_chase_state_json_deserializes_as_encounter`) intentionally not ported — deviation logged, rationale sound (Rust-specific save-format migration, no Python save ever carried a top-level `chase` field). ✓
- **Serde → pydantic v2, HashMap → dict, Option → `| None`, impl methods → model methods (names verbatim).** All four translations applied consistently. ✓
- **Discriminator stays string-keyed per ADR-033.** `encounter_type: str` preserved (not enum-tightened). Correct — the Rust source is free-form `String` and a Python-side whitelist would deviate worse than the AC5 pedantic reading. ✓

### Deferred-item verification (each mapped to the correct future story)

| Deferred item | Target story | Legitimate? | Notes |
|---|---|---|---|
| `apply_beat(beat_id, def)` | 42-2 | ✓ | Depends on `ConfrontationDef` from `sidequest.genre` which lands in 42-2. Porting now requires stubbing or importing from unmade module — violates No Stubbing. |
| `from_confrontation_def(def)` | 42-2 | ✓ | Same `ConfrontationDef` dependency. Correctly tied to 42-2. |
| `format_encounter_context(def)` | 42-4 | ✓ | Narrator-prompt wiring. Epic-42 context explicitly claims this for 42-4 (narrator prompt `encounter_summary` section). |
| `escalate_to_combat()` / `escalation_target()` | 42-4 | ✓ | Dispatch-side chain (produces next encounter from resolved one, consumed by combat dispatch). 42-4 scope. |
| OTEL emission in `resolve_from_trope` | 42-4 | ✓ | State mutation lands; OTEL `encounter.state.resolved_by_trope` span wired when dispatch consumer lands. Matches Epic-42 "OTEL spans (42-4)" exclusion. |
| `RigStats` struct + full `chase_depth` module | Phase 4 | ✓ | Chase cinematography explicitly deferred per Keith's 2026-04-20 decision (Epic-42 Deliberate Non-Goals). |
| `SecondaryStats.from_rig_stats(&RigStats)` | Phase 4 | ✓ | Zero Python callers today (no `RigStats` struct). Collapsed into `rig()` classmethod via inlined `_RIG_BASE_STATS` + `_rig_damage_tier_label`. Deviation logged. |

### Scope-boundary check (Key Seam)

- **`GameSnapshot.encounter: dict | None` → `StructuredEncounter | None`** promoted at `sidequest/game/session.py:342`. ✓
- **Dict-access migration completeness.** Grepped `snapshot\.encounter\[` across `sidequest-server/` → zero hits in non-test code. Matches story Assumption 3 ("No existing `snapshot.encounter["x"]` dict-access consumers exist in Phase 2 Python code"). 42-4 will handle any dispatch-side accessors when they're ported. ✓
- **`extra: ignore` preserved on `GameSnapshot`** per AC6. Forward-compat with Rust-produced save files that may carry unknown top-level fields. ✓

### Combatant Protocol conformance

- Six methods match Rust trait verbatim (`name`, `edge`, `max_edge`, `level`, `is_broken`, `edge_fraction`). ✓
- `@runtime_checkable` applied so `isinstance(char, Combatant)` works structurally. ✓
- Default implementations intentionally NOT placed on Protocol. TEA's deviation explains the tradeoff cleanly: `runtime_checkable` only inspects method *names*, not method *bodies* — a mixin-style default on the Protocol would silently accept implementers that bind the wrong body. Pure-contract Protocol + verbatim method bodies on each implementer favours visibility over DRY. Forward cost is real (Character.is_broken drift was a textbook instance of exactly this risk), but the drift was caught in-story via the delivery finding. Design call is defensible. ✓
- **Drift fix quality.** `Character.is_broken` flipped from `== 0` to `<= 0`; `Character.edge_fraction` flipped from `1.0` to `0.0` when `max == 0`. Both now match Rust `Combatant` defaults byte-for-byte. Pre-existing drift-encoded test renamed `_returns_one` → `_returns_zero` (correct rename, not a silent test deletion). ✓

### Mechanical port discipline audit

- Field names, enum variant names (PascalCase), drama-weight values (0.70/0.75/0.80/0.95/0.70), constructor names, parameter names — all verbatim against Rust source. ✓
- `escape_threshold: float` preserved as unused positional parameter in `chase()` for Rust-call-shape parity + Phase 4 forward-compat. `# noqa: ARG003` is the right tool; deviation logged. ✓
- No idiomatic rewrites — e.g., drama weights stored in a module-level `_DRAMA_WEIGHTS` dict and accessed via enum method, which mirrors Rust's `match` arm structure without cleverness. ✓

### AC5 interpretation (one design call worth surfacing)

TEA interpreted "unknown `encounter_type` fails loud" at the schema level: the real fail-loud boundary is the enum fields (`MetricDirection`, `EncounterPhase`), not the string-keyed `encounter_type`. Rust's source makes the same trade — `encounter_type` is `String`, no whitelist. Tightening the Python side to a closed set would deviate from source *worse* than the pedantic AC reading, and would break the ADR-033 contract ("string-keyed encounter types replace hardcoded enums"). TEA's resolution (malformed-dict raises; bad enum variant raises) correctly threads the needle. AC5 spec text is slightly ambiguous — if Keith wants a closed `encounter_type` set in the future, it's a new story, not a port drift. **Recommendation: C — spec can be clarified** with a one-line edit to the story context at some future convenience, but nothing to fix in code.

### Minor watchpoints for Phase 4 (non-blocking, forward-impact only)

- **`_RIG_BASE_STATS` + `_rig_damage_tier_label` inlined in `encounter.py`.** These are a narrow slice of chase_depth logic parked in encounter.py to keep `SecondaryStats.rig()` functional without a stub module. When Phase 4 lands `chase_depth.py`, either (a) keep the helpers here and let chase_depth.py import them, or (b) move them to `chase_depth.py` and import back. Not a deviation — just a forward-impact seam the chase-polish author should know about.
- **`RigType` colocated in `encounter.py`.** Same seam. TEA's Dev-notes guidance explicitly sanctioned this ("Dev may colocate (simplest) or put it in sidequest/game/chase_depth.py as a small shim and re-export"). Phase 4 decides.

### Mismatches

- None of Critical/Major/Minor severity. One **Trivial** item:
  - **`escape_threshold` typed as `float` in Python** (Rust is `f64`). Correct scalar mapping — no action.

**Decision:** Proceed to review. Structural gate passed; substantive audit clean. Amos (TEA) runs the verify phase next to confirm tests and wiring, then Chrisjen can tear it apart.

Drummer — handoff to TEA for the `verify` phase.

— Naomi, design mode

## TEA Assessment (verify)

**Phase:** finish
**Status:** PASS — port is mechanically honest, tests are green, no regressions. Ready for adversarial review.

### Test parity re-verification

| Scope | Count | Verdict |
|---|---|---|
| New 42-1 tests (`tests/game/test_encounter.py` + `test_combatant.py`) | **59 passed**, 0 failed, 0 skipped | ✓ every Rust `#[test]` ported verbatim + AC-driven additions, all green |
| Full `tests/game/` regression | **461 passed**, 1 skipped, 0 failed | ✓ 42-1 added 59 to the 402 baseline; no pre-existing test flipped red |
| Full project suite | 1355 passed, 3 skipped, **5 failed** | 5 failures **confirmed pre-existing** — see below |

**Pre-existing failure audit** (ran targeted check on each failure):
- `tests/agents/test_orchestrator.py` (4 fails) — orchestrator JSON-patch parsing; zero `encounter|combatant` hits (grep count: 0). `git log origin/develop..HEAD -- tests/agents/ sidequest/agents/` returns empty — 42-1 branch did not touch any of those files.
- `tests/server/test_rest.py::test_list_genres_empty_when_no_packs_dir` — raises `RuntimeError: No genre_packs directory found`. Fixture-path issue in the app bootstrap, unrelated to encounter/combatant code. Zero `encounter|combatant` hits in the test file.

Verdict: **Not a 42-1 regression.** Logged here for transparency; fix belongs to a separate story.

### Behavioural honesty check (does impl match Rust, not just TEA's tests?)

I re-read Dev's `encounter.py` against Rust source to confirm implementation wasn't over-fit to the test surface:

- `EncounterPhase.drama_weight()` — Python values `{Setup: 0.70, Opening: 0.75, Escalation: 0.80, Climax: 0.95, Resolution: 0.70}` match Rust `encounter.rs:82-89` match arms byte-for-byte. ✓
- `SecondaryStats.rig(RigType)` — `_RIG_BASE_STATS` table values match `RigStats::from_type()` match arms (Interceptor: focus 8/max 8, armor 4/max 4; WarRig: focus 5/max 5, armor 10/max 10; etc). ✓
- `StructuredEncounter.combat()` — populates `encounter_type="combat"`, `metric.name="combatants_standing"`, `secondary_stats.stats` keyed by combatant names with `{current: hp, max: hp}`. Matches Rust `StructuredEncounter::combat` at `encounter.rs:179-207`. ✓
- `StructuredEncounter.chase()` — `encounter_type="chase"`, metric `separation/Ascending/high=goal`, secondary via `rig(rig_type)` when present (else None). Matches Rust at `encounter.rs:214-245`. ✓
- `resolve_from_trope()` — sets `resolved=True`, phase → Resolution, outcome carries trope name. OTEL call site intentionally not wired (deferred to 42-4 — deviation logged by Dev). ✓
- `Combatant` Protocol — six method signatures match Rust trait. `@runtime_checkable`. Default bodies sit on each implementer per the intentional design deviation. ✓

No test-driven-development over-fit: the match-arm / struct-layout / enum-variant parity tests would fail if an implementation shortcut had been taken.

### Simplify pass (reuse + quality + efficiency, fan-out)

Three simplify subagents ran in parallel against the changed files.

**Efficiency:** CLEAN — no dead code, no unreferenced helpers, no unnecessary abstractions.

**Reuse:** 3 findings, all **out of 42-1 scope**:
1. `Character` / `NpcPatch` / `CreatureCore` blank-string validators duplicate across three classes (HIGH) — pre-existing pattern, Dev did not introduce or worsen it.
2. `_npc_from_patch` inline CreatureCore+Npc construction (MEDIUM) — pre-existing in `session.py`, untouched by 42-1.
3. `RigType.base_stats` + `_RIG_BASE_STATS` / `EncounterPhase.drama_weight` + `_DRAMA_WEIGHTS` (LOW) — the two enum+lookup-dict sites mirror Rust `match` arms; architect explicitly sanctioned the seam.

None actionable in-story. Flagging #1 and #2 as **post-story improvement candidates** — worth a cleanup story after Epic 42 lands.

**Quality:** 1 finding of substance + 3 nits:
1. **Missing `model_config` on `StatValue`, `SecondaryStats`, `EncounterActor`, `EncounterMetric`, `StructuredEncounter`** (MEDIUM). Every other Pydantic model in `sidequest/game/` (40+ classes across belief_state, creature_core, character, session, etc.) carries `model_config = {"extra": "forbid" | "ignore"}`; these 5 do not. The port target `encounter_type` is deliberately string-keyed (ADR-033) but the **struct-level** forbid/ignore choice is still meaningful — `forbid` would extend AC5's no-silent-fallback guarantee; `ignore` would extend GameSnapshot's forward-compat posture for Rust-produced saves. NOT applied in verify phase because the choice has cross-module consequences (save migration once 42-4 lands Rust-save compatibility) and deserves a Reviewer call. **Flagged for Reviewer.**
2. `per_actor_state: dict[str, Any]` on `EncounterActor` carries no runtime validator (LOW) — matches Rust `HashMap<String, serde_json::Value>` design; sealed-letter dispatcher (ADR-077) validates shape. Not actionable in 42-1.
3. Combatant docstring tension between "pure contract" and "defaults must be carried verbatim" (LOW) — minor wording nit.
4. Session.py encounter-field change correctly identified as the intended fix — non-finding.

### Applied fixes (this phase)

**None.** All simplify findings are either out-of-scope (pre-existing patterns Dev didn't touch), architect-sanctioned seams, or cross-module decisions that belong in the Reviewer's lane. Keeping the verify diff empty to preserve the Spec-Check → Review boundary.

### Reviewer notes (for Chrisjen)

- **Decide: `model_config` on encounter.py Pydantic classes.** Convention says add it. Rust-save forward-compat may want `extra: ignore` to match `GameSnapshot`; AC5 no-silent-fallback may want `extra: forbid` to catch malformed inner shapes. Either call is defensible; a conscious decision should land in either code or an ADR note.
- **Blank-string validator duplication** (`Character` / `NpcPatch` / `CreatureCore`) is a real cleanup opportunity but pre-dates 42-1 — consider filing as a debt story.
- 5 pre-existing test failures outside `tests/game/` remain (orchestrator x4, rest x1). Not 42-1's problem; flagging for triage visibility.

**Working tree:** clean, no unstaged changes, branch `feat/42-1-structured-encounter-types` still at `28e598c` (Dev's GREEN commit) + `bea8cec` (TEA's RED commit).

**Handoff.** To Reviewer (Chrisjen Avasarala) for adversarial review.

— Amos, verify mode

## Subagent Results

Initial-review fan-out (commit `28e598c`). 6 of 8 specialists spawned; 2 intentionally skipped with rationale.

| # | Specialist | Received | Status | Findings | Decision |
|---|---|---|---|---|---|
| 1 | reviewer-preflight | Yes | clean | Tests 461 pass / 1 skip / 0 fail. 3 new UP042 lint violations (`(str, Enum)` pattern). 0 mypy errors on 42-1 files. `# noqa: ARG003` has rationale. Protocol `...` bodies correct (not stubs). | CONFIRMED — UP042 delta verified: develop=142 ruff errors, branch=145 (+3). Baseline is pre-existing; Dev's note accurate; not enforced by gate on develop. NOT 42-1 scope. Logged as LOW non-blocking observation. |
| 2 | reviewer-edge-hunter | Yes | findings | 8 missing-guard findings on `.chase(goal≤0)`, `.combat(hp≤0)`, empty combatants, inverted `EncounterMetric` thresholds, negative `StatValue`, empty `trope_id`, session.py whole-snapshot load failure on malformed encounter. | DISMISSED (all 8) — mechanical-port discipline. Rust source (`sidequest-api/crates/sidequest-game/src/encounter.rs`) has zero such guards. Adding Python-side validators would be an idiomatic rewrite, forbidden by epic 42 execution strategy §2. Session.py whole-snapshot failure on malformed encounter is AC5 fail-loud behaviour. Documented in "Dismissed Findings" below so they don't resurface. |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 findings: (a) missing `model_config` on all 5 new Pydantic classes — silent `extra="ignore"` default drops unknown fields; (b) `resolve_from_trope` no-op on already-resolved has no OTEL/log trace. | (a) CONFIRMED — **HIGH blocking**, elevated to primary finding #1 in Reviewer Assessment. Violates CLAUDE.md "No Silent Fallbacks" + codebase internal-type convention. Independently corroborated by type-design subagent + TEA's verify-phase flag. (b) DISMISSED — Rust source (`encounter.rs:458-459`) has identical no-op guard. Clean Rust-parity. |
| 4 | reviewer-test-analyzer | Yes | findings | 6 findings: 2 tautological enum-variant tests (HIGH); post-init pydantic attribute mutation (MED); wiring test omits `RigType` + `Combatant` (MED); `drama_weight()` not exercised post-deserialization (MED); Character negative-edge broken only tested on `_TestCombatant` not production Character (MED). Name parity check PASS. | CONFIRMED (2 blocking): tautological tests → finding #2; wiring test omission → finding #3. Other 3 downgraded to LOW non-blocking (documented in Observations section). Character drift adequately covered by `test_character.py:260` `_returns_zero` rename. drama_weight post-deserialize gap is low-risk — StrEnum methods survive json roundtrip in pydantic v2. |
| 5 | reviewer-type-design | Yes | findings | 5 findings: missing `model_config` (MED); stringly-typed `role` / `metric.name` / `outcome` (LOW ×3); `per_actor_state: dict[str, Any]` escape hatch (LOW). Combatant Protocol: CLEAN. GameSnapshot migration: CLEAN (zero residue). | `model_config` → rolled into finding #1 (corroborates silent-failure-hunter). Stringly-typed fields → Rust-parity, defer to 42-4 precursor (logged as non-blocking Improvement in Delivery Findings). `per_actor_state` TODO comment → non-blocking Improvement. Combatant Protocol + GameSnapshot migration confirmations accepted. |
| 6 | reviewer-simplifier | Yes | findings | 2 findings: redundant explicit default-field assignments in `.chase()` and `.combat()` constructors (MED both). | DISMISSED — intentional for Rust-parity documentation (mirrors Rust `..Default::default()` pattern). Flagged at `medium` confidence by the subagent itself who noted "explicit field passing can serve as documentation." Port discipline sanctions this shape. |
| 7 | reviewer-comment-analyzer | Yes | findings | 2 stale docstring findings in `tests/game/test_combatant.py:99,122` — describe `Character.edge_fraction` drift as present-tense ("already has this drift", "returns 1.0 today") but same branch fixes it. Stale at merge time. | NON-BLOCKING — cosmetic docstring drift, does not affect runtime behaviour or test correctness. Re-phrasing to regression-guard language is a follow-up nit. Logged as a non-blocking Observation; not re-opening review. Drummer to note for a future tidy-up pass. |
| 8 | reviewer-security | Yes | clean | Pure-types diff: pydantic BaseModel subclasses + Protocol + Enum fields + test fixtures. No I/O, no subprocess, no unsafe deserialization, no auth, no secrets, no user-controlled paths. `model_validate_json` raises `ValidationError` on bad input (tested). `per_actor_state: dict[str, Any]` only fed from internal game state. | CLEAN — no action required. |
| 9 | reviewer-rule-checker | Yes | findings | 31 instances checked against 8 applicable project rules. 2 violations flagged: (a) **Rule 6 (OTEL)** — `resolve_from_trope()` (encounter.py:523) mutates state with no span; (b) **Rule 4 (Verify Wiring)** — 9 new symbols re-exported from `sidequest.game` with no non-test consumers outside `sidequest/game/` today. Other 29 instances compliant (No Silent Fallbacks, No Stubs, mechanical Rust-parity, wiring tests present, no live LLM in tests). | (a) **DISMISSED (with scope caveat)** — OTEL span `encounter.state.resolved_by_trope` is explicitly scoped to 42-4 per context-epic-42.md and the docstring comment at encounter.py:530-533. Epic 42 titles Story 42-4 as "combat dispatch + OTEL + narrator wiring"; deferral is by design, not oversight. If 42-4 slips, this mutation stays dark — Drummer tracks as a hard dependency for 42-4 completion. (b) **DISMISSED** — The types are reachable via `GameSnapshot.encounter: StructuredEncounter|None`, and `GameSnapshot` has production consumers in `orchestrator.py`, `session_handler.py`, `rest.py`, `scenario_bind.py` (confirmed by rule-checker itself on Rule 4 row). Direct constructor-call consumers (`StructuredEncounter.chase()` / `.combat()` / `.resolve_from_trope()`) are scheduled in 42-2 (ResourcePool integration), 42-3 (TensionTracker), 42-4 (dispatch). This is a foundation story in a 4-story DAG by design. Wiring test `test_game_module_exports_structured_encounter` enforces the export contract for the consumers arriving in 42-2/3/4. Logged as non-blocking pending 42-4 completion. |

**All received: Yes** — 8 of 8 specialists fanned out (2 initially skipped by judgment call, completed post-rejection for gate compliance). 3 findings elevated to blocking (all closed in `da7a731`). 10 dismissed with documented rationale. 7 downgraded to non-blocking Observations (includes 2 late-running comment-analyzer findings — stale docstrings, cosmetic only).

## Reviewer Assessment

**Phase:** finish
**Verdict:** APPROVED (after Dev fix pass at commit `da7a731`)

**Initial verdict (commit `28e598c`):** REJECTED — 3 blocking findings.
**Re-review verdict (commit `da7a731`):** APPROVED — all 3 blocking findings closed, 59/59 targeted tests green, 461/1 game-suite baseline preserved, no new findings on re-review.

### Specialist Cross-References

Findings drawn from the Subagent Results table are cited inline below with specialist tags:

- **[SILENT]** (reviewer-silent-failure-hunter) — surfaced the `model_config` silent-drop via `extra="ignore"` default → elevated to blocking finding #1, closed in `da7a731`.
- **[TEST]** (reviewer-test-analyzer) — surfaced tautological enum-variant tests + wiring-test omission → elevated to blocking findings #2 and #3, closed in `da7a731`. Also raised 3 non-blocking test-shape observations (post-init mutation, drama_weight post-deserialize, Character-vs-_TestCombatant drift coverage) — logged as Observations.
- **[TYPE]** (reviewer-type-design) — corroborated `model_config` finding; logged stringly-typed field observations (`role`, `metric.name`, `outcome`) as non-blocking Improvements deferring to 42-4; confirmed Combatant Protocol + GameSnapshot migration clean.
- **[DOC]** (reviewer-comment-analyzer) — ran post-rejection; flagged 2 stale docstrings in `test_combatant.py:99,122` describing `Character.edge_fraction` drift as present-tense when the branch fixes it. Non-blocking cosmetic, logged as a future tidy-up.
- **[RULE]** (reviewer-rule-checker) — exhaustive 31-instance pass across 8 applicable project rules. 29 compliant. 2 dismissed with rationale: (a) OTEL span on `resolve_from_trope` scoped to 42-4 per Epic 42 plan; (b) "half-wired" exports dismissed because types are reachable via `GameSnapshot.encounter` (which has production consumers) — direct constructor callers arrive in 42-2/3/4.
- **[EDGE]** (reviewer-edge-hunter) — 8 missing-guard findings all dismissed as forbidden idiomatic-rewrite attempts against Rust-parity discipline.
- **[PREFLIGHT]** (reviewer-preflight) — 3 new UP042 lint violations; pre-existing baseline, not enforced.
- **[SIMPLIFIER]** (reviewer-simplifier) — 2 findings dismissed (Rust `..Default::default()` parity documentation).
- **[SECURITY]** (reviewer-security) — clean, no action required.

### Summary

Mechanical port discipline is clean. Rust-parity audit passes byte-for-byte on drama weights, rig base stats, constructor signatures, `resolve_from_trope` already-resolved guard, and Combatant Protocol shape. `GameSnapshot.encounter: dict|None → StructuredEncounter|None` migration is complete — zero `snapshot.encounter[...]` or `.get(...)` residue in non-test code (`grep -rn "encounter\[\|\.encounter\.get(" sidequest/` → empty). Combatant Protocol is correctly formalised (`@runtime_checkable`, six `...` method signatures, no default bodies on Protocol per TEA's deliberate design call; defaults carried verbatim on implementers with the Character drift fix shipped in-story).

Three blocking issues stand between this branch and merge. All three are codebase-convention violations that the port discipline does not excuse; the fixes total ~15 lines across 2 files.

### Blocking Findings

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | 5 new Pydantic classes lack `model_config`; default pydantic `extra="ignore"` silently drops unknown fields. Violates CLAUDE.md "No Silent Fallbacks" hard gate and the codebase convention (internal engine types → `forbid`; save-file surfaces → `ignore` with comment). `GameSnapshot` already provides forward-compat at the outer boundary; inner types should be strict. | `sidequest/game/encounter.py:160,170,204,223,242` | Add `model_config = {"extra": "forbid"}` to StatValue, SecondaryStats, EncounterActor, EncounterMetric, StructuredEncounter. |
| [MEDIUM] | `test_encounter_phase_variants` asserts `len()` + index access on a literal 5-element list it just built; `test_metric_direction_is_non_exhaustive` does the same on a literal 3-element list. Neither test can fail — they verify Python list semantics, not enum membership. | `tests/game/test_encounter.py:361,592` | Replace with `set(EncounterPhase) == {Setup, Opening, Escalation, Climax, Resolution}` and `set(MetricDirection) == {Ascending, Descending, Bidirectional}` (or `assert X in EnumName` style). |
| [MEDIUM] | Wiring test checks 7 encounter symbols but omits `RigType` and `Combatant`, both of which are exported and actively imported across the test suite and upcoming 42-2/42-3/42-4 call sites. A future edit that drops either re-export would slip through. | `tests/game/test_encounter.py:1080` | Add `"RigType"` and `"Combatant"` to the `expected` list. |

### Adversarial Analysis — Mandatory Steps

- **Data flow traced:** save JSON → pydantic `model_validate` → `GameSnapshot.encounter: StructuredEncounter|None` → `resolve_from_trope` / `.chase()` / `.combat()` methods. Safe because enum fields (`MetricDirection`, `EncounterPhase`) raise `ValidationError` on unknown variants (AC5 behaviour verified). The gap is at the struct-field boundary where unknown inner fields are silently dropped — the `model_config` finding above closes that hole.
- **Wiring check:** `sidequest/game/__init__.py` re-exports `Combatant` (23, 98) + all 8 encounter symbols including `RigType` (53-62, 125-133). `grep -rn "encounter\[\|\.encounter\.get(" sidequest/ --include="*.py"` returns zero hits — migration is real, not cosmetic. Architect's spec-check claim holds.
- **Pattern observed:** Internal engine types use `model_config = {"extra": "forbid"}` (session.py:39,54,79,124,145,179,194; turn.py:60; character family); save-file surfaces use `extra: "ignore"` with forward-compat comment (session.py:324 `# forward-compat: ignore unknown save fields`; history_chapter.py:33,57,76,88,107). The 5 new encounter classes violate this pattern.
- **Error handling verified:** `resolve_from_trope` no-op on already-resolved matches Rust source byte-for-byte (`encounter.rs:458-459`). Unknown `MetricDirection`/`EncounterPhase` variants raise `ValidationError` (test_encounter.py:605 + siblings). Empty / negative / malformed primitive inputs are NOT guarded — correctly Rust-parity (Rust source has zero such guards; adding Python-side validators would be a forbidden idiomatic rewrite).
- **Security:** JSON deserialization via pydantic (schema-validated). Test fixtures are trusted repo-committed data. No auth surfaces touched. No unsafe deserialization paths (no pickle, no eval, no `json.loads` on untrusted sources). Clean.
- **Hard questions answered:**
  - Null/empty inputs to `.chase()` / `.combat()` / `.resolve_from_trope()`: unvalidated. Rust source has zero guards. **Port-discipline correct.**
  - Double-resolve: explicitly no-op (matches Rust). **Correct.**
  - Unknown enum variants on save reload: `ValidationError` raised, whole GameSnapshot fails to load. **This is AC5 fail-loud behaviour, not a bug.**
  - Unknown struct-level fields on save reload: silently dropped. **This is the blocking finding above.**
  - Race conditions: types are plain pydantic models, no mutable shared state surface in this diff. **N/A.**

### Design Deviation Audit

All 8 deviations stamped ACCEPTED:

**Dev deviations:**
- `escape_threshold` unused param preserved for Rust signature parity → ACCEPTED. Load-bearing for AC2 constructor-parity tests. `# noqa: ARG003` with rationale is the correct tool.
- `SecondaryStats.rig()` collapses Rust `rig()` + `from_rig_stats()` → ACCEPTED. Porting `from_rig_stats` with no caller violates No Stubbing. Values match byte-for-byte.
- `apply_beat / from_confrontation_def / format_encounter_context / escalation_target / escalate_to_combat` not ported → ACCEPTED. All depend on `ConfrontationDef` (42-2) or narrator/dispatch wiring (42-4). Correct scope deferrals.
- OTEL emission in `resolve_from_trope` not wired → ACCEPTED. State mutation lands; OTEL gates on 42-4 dispatch consumer per session line 168 guidance. Comment on encounter.py:358-359 traceably documents the defer — clean defer, not a silent skip.

**TEA deviations:**
- Hand-authored encounter fixtures (not cargo-generated) → ACCEPTED. Story assumption block authorized fallback; `sidequest-game` has no `examples/` directory.
- `old_chase_state_json_deserializes_as_encounter` not ported → ACCEPTED. Rust-specific save-format migration; no Python save ever carried the old top-level `chase` field.
- AC5 interpreted at enum-field level, not `encounter_type` string → ACCEPTED. Matches Rust's free-form `String` encounter_type per ADR-033; closing it would deviate from source worse than the pedantic AC reading.
- Combatant defaults on implementers, not Protocol → ACCEPTED. `@runtime_checkable` only inspects method names; default bodies on Protocol would silently accept wrong-body implementers. Character drift fix is proof-of-cost but the cost is visible, not hidden.

No undocumented deviations found.

### Observations — Non-blocking (LOW, logged for forward context)

1. `test_game_snapshot_has_encounter_field:409` uses post-init attribute mutation on a pydantic model. Works with current config (not frozen) but decoupled from model validation. Consider `model_copy(update={...})` or constructor-kwarg in a cleanup pass.
2. `test_broken_at_negative_edge:91` only exercises `_TestCombatant`; the production `Character.is_broken()` with negative edge is covered indirectly by `test_edge_fraction_zero_max_returns_zero` (test_character.py:260). Adequate but not symmetric with Rust test shape.
3. `per_actor_state: dict[str, Any]` escape hatch — worth a `# TODO(42-4)` at encounter.py:220 so the escape is visible at its future closure point.
4. Stringly-typed `role` / `metric.name` / `outcome` are landmines for 42-4 dispatch. File a 42-4 precursor tightening note when dispatch lands.
5. UP042 lint: `ruff check sidequest/` baseline is 142 errors on develop / 145 on branch (+3 new UP042 from RigType/MetricDirection/EncounterPhase). Consistent with Dev's "30 pre-existing UP042" note. The codebase has tolerated this baseline for a while; not enforced by the gate on develop. **Not 42-1's problem** — file a codebase-wide `StrEnum` migration story separately.

### Dismissed Findings (subagent false alarms — documented so they don't resurface)

- **Edge-hunter: missing guards on `.chase(goal≤0)`, `.combat(hp≤0)`, empty combatants, negative StatValue, inverted thresholds** — Rust source has zero such guards. Adding Python-side validators would be an idiomatic rewrite, forbidden by mechanical-port discipline. If Keith wants these invariants, they are a future story landing in BOTH Rust and Python.
- **Silent-failure-hunter: already-resolved no-op on `resolve_from_trope`** — Rust does the exact same thing (`encounter.rs:458-459`). Clean Rust-parity.
- **Edge-hunter: session.py encounter type coercion causing whole-session load failure on malformed encounter** — This IS the AC5 fail-loud behaviour. Design intent, not a bug.
- **Simplifier: redundant default field assignments in `.chase()` / `.combat()` constructors** — Intentional for Rust-parity documentation (mirrors `..Default::default()` field-listing in Rust). Keep.

### Pre-existing unrelated failures (logged for triage, NOT 42-1 scope)

- `tests/agents/test_orchestrator.py` (4 failures) — JSON-patch parsing, zero encounter/combatant references.
- `tests/server/test_rest.py::test_list_genres_empty_when_no_packs_dir` (1 failure) — genre_packs fixture bootstrap issue.

TEA's verify pass confirmed none of these files were touched by this branch. Separate story.

### Handoff

To Dev (Naomi Nagata) for blocking-finding fix pass. Three fixes, all mechanical:
1. Add `model_config = {"extra": "forbid"}` to 5 classes in encounter.py
2. Rewrite 2 tautological enum tests to test enum membership
3. Add `"RigType"` + `"Combatant"` to the wiring-test expected list

Keep Task #3 in_progress (this review) until re-review confirms fixes. Drummer, don't archive — review loop returns to me after Naomi's fix commit.

— Chrisjen, review mode

---

## Re-review — 42-1 REVIEW (post-fix, commit da7a731)

**Verdict:** APPROVED — all three blocking findings closed, no regressions, ready for finish.

### Finding Resolution

| # | Severity | Issue | Fix | Verified |
|---|----------|-------|-----|----------|
| 1 | HIGH | Pydantic extras policy | `model_config = {"extra": "forbid"}` added to StatValue / SecondaryStats / EncounterActor / EncounterMetric / StructuredEncounter | Runtime check: all 5 types raise `ValidationError` on bogus kwarg (`bogus='x'`). Matches codebase convention: inner engine types strict, `GameSnapshot` save-file boundary stays `ignore`. |
| 2 | MEDIUM | Tautological enum tests | `test_encounter_phase_variants` + `test_metric_direction_is_non_exhaustive` rewritten to `set(Enum) == {...}` + Rust-verbatim value assertions | Set membership catches rename/drop upstream. Partial value guards on EncounterPhase (Setup, Resolution) acceptable because `test_encounter_phase_serde_roundtrip` covers end-to-end value drift independently. |
| 3 | MEDIUM | Incomplete wiring test | `RigType` + `Combatant` added to `expected` list with clarifying docstring on downstream consumers | Runtime: `hasattr(sidequest.game, X) == True` for all 9 symbols. Both in `__all__`. |

### Verification

- **Targeted tests:** 59/59 green (`tests/game/test_encounter.py` + `test_combatant.py`)
- **Game suite regression:** 461 passed, 1 skipped (pre-existing), 0 failed
- **Broader suite regression:** 983 passed, 1 skipped, 0 failed (excluding tests/agents and tests/server pre-existing failures documented above)
- **Extras enforcement:** verified interactively — each of the 5 types rejects `bogus='x'` with `ValidationError`
- **Wiring:** `sidequest.game.X` resolves for every symbol in the expected list; `__all__` includes `Combatant`
- **Encounter dict consumers:** `grep 'snapshot\.encounter\[|\.encounter\[' sidequest/` — zero hits. Migration clean.

### No new findings

Dev's fixes landed exactly where flagged, no scope creep, no regression surface. Non-blocking LOW observations from the first review (stringly-typed roles, UP042 baseline, per_actor_state TODO) stand as forward-context for 42-4 / future cleanup story — intentionally not in 42-1 scope.

### Handoff

To SM (Drummer) for finish-phase. Ready to archive. Task #3 → completed.

— Chrisjen, re-review stamp APPROVED

## Architect Assessment (spec-reconcile)

**Spec Alignment:** Aligned after review
**Deviation Manifest:** Complete — 8 in-flight deviations stand as accepted by Reviewer; **1 missed deviation added** under `### Architect (reconcile)` below (post-review `model_config` tightening introduced Rust-behaviour drift that was never logged with the 6-field template).
**AC Deferral:** None. All six ACs (AC1–AC6) landed as DONE per TEA verify + Reviewer re-review. AC accountability table not required — zero deferred items to audit.

### Review of existing deviation entries (8 total)

Each Dev + TEA entry checked for: spec-source path existence, spec-text accuracy, implementation description vs. code at `da7a731`, forward-impact realism, and 6-field completeness.

| # | Entry | 6-field complete? | Spec source verified? | Implementation matches `da7a731`? | Verdict |
|---|---|---|---|---|---|
| D1 | `escape_threshold` unused param preserved | ✓ | ✓ `encounter.rs:214` | ✓ `encounter.py:269` | Accurate. Stands. |
| D2 | `SecondaryStats.rig()` collapses Rust `rig()` + `from_rig_stats()` | ✓ | ✓ `encounter.rs:91-141` | ✓ `encounter.py:189-207` | Accurate. Stands. |
| D3 | Five `StructuredEncounter` methods not ported | ✓ | ✓ `encounter.rs:278-523` | ✓ absent from `encounter.py`, routed 42-2/42-4 | Accurate. Stands. |
| D4 | OTEL emission in `resolve_from_trope` not wired | ✓ | ✓ `encounter.rs:464-474` | ✓ state-only at `encounter.py:349-365` | Accurate. Stands. |
| T1 | Hand-authored encounter fixtures (no cargo example) | ✓ | ✓ `context-story-42-1.md` AC2 + Assumptions | ✓ `tests/fixtures/encounters/*.json` | Accurate. Stands. |
| T2 | `old_chase_state_json_deserializes_as_encounter` not ported | ✓ | ✓ `encounter_story_16_2_tests.rs` | ✓ not in `test_encounter.py` | Accurate. Stands. |
| T3 | AC5 interpreted at enum-field level | ✓ | ✓ `context-story-42-1.md` AC5 | ✓ `test_encounter.py` AC5 tests | Accurate. Stands. Note: the `da7a731` `extra=forbid` fix (see reconcile entry below) **widens** AC5's practical reach from enum fields to struct fields — an extension, not a contradiction. |
| T4 | Combatant defaults on implementers, not Protocol | ✓ | ✓ `combatant.rs:28-30,38-43` | ✓ `combatant.py` (pure-contract), `character.py:164-182` (verbatim bodies) | Accurate. Stands. Character drift fix (`<= 0` / `0.0 when max==0`) landed in same branch — proof-of-cost realised and cleaned, exactly as the deviation's forward-impact note predicted. |

**Accuracy verdict:** All 8 entries pass self-containment (spec text quoted inline, no external reference), all 6 fields present and substantive, no corrections needed.

### Missed deviations (post-review discovery)

The `da7a731` review-fix pass added `model_config = {"extra": "forbid"}` to 5 inner Pydantic types. The Reviewer correctly classified this as closing a "No Silent Fallbacks" violation, but did not log it with the 6-field deviation template because the framing was "codebase-convention alignment" rather than "Rust-behaviour deviation." It is both — and spec-reconcile is where we pin that down.

See the formal entry under `### Architect (reconcile)` below.

### AC deferral verification

Zero ACs deferred. All six verified DONE through the TDD loop:

- **AC1** (JSON round-trip parity): 4 fixture round-trips green in `test_encounter.py`.
- **AC2** (constructors parity): `.chase()` and `.combat()` produce fixture-equal JSON.
- **AC3** (Combatant structural isinstance): `isinstance(Character, Combatant)` true; partial-impl rejected; zero-max returns 0.0.
- **AC4** (`GameSnapshot.encounter` typed): `typing.get_type_hints` returns `StructuredEncounter | None`.
- **AC5** (unknown encounter fails loud): enum-variant rejection confirmed. Extended by `da7a731` to cover struct-level extras (see reconcile entry below).
- **AC6** (`extra: ignore` preserved on GameSnapshot): Reviewer confirmed via grep of `session.py:324`.

No accountability table required.

### Late-breaking spec-doc touch-ups (non-blocking, boss-visible)

These are spec-source polish items surfaced by TEA during earlier phases. They are **not deviations** — they're spec-text clarity improvements for future story authors. Flagging here for traceability; no action required in-story:

1. **`context-story-42-1.md` AC5 wording** — currently reads as if unknown `encounter_type` string alone should raise. Actual correct behaviour (Rust-parity + codebase-convention): unknown *enum-field variants* raise, and unknown *struct-level fields* raise (post-`da7a731`). `encounter_type: str` itself stays free-form per ADR-033. Worth a one-line edit at future convenience — "A save file with unknown `MetricDirection`/`EncounterPhase` variants, or unknown struct-level encounter fields, raises `ValidationError` on `GameSnapshot` load." **Resolution: C (clarify spec).**

2. **`context-story-42-1.md:100` RigType example values** — says `"motorcycle"`, `"sedan"`, `"semi"`; actual Rust enum is `Interceptor / WarRig / Bike / Hauler / Frankenstein`. Tests correctly use the Rust names per mechanical-port discipline. Worth amending. **Resolution: C (clarify spec).**

3. **`context-epic-42.md` scope-map LOC count** — lists `encounter.rs` at 724 LOC; actual file is 724 lines (checked). Story context text says "(617 LOC)" in one inventory mention but 724 elsewhere — internal minor inconsistency in the epic's tech-debt prose, not a spec error. **Resolution: no action.**

### Reviewer stamp-check

Chrisjen's re-review at `da7a731` stamped APPROVED with zero new findings post-fix. Reviewer's Design Deviation Audit stamped all 8 pre-existing deviations ACCEPTED. My reconcile pass concurs — the 8 entries are accurate and self-contained, and the single new deviation from `da7a731` is logged below.

**Gate expectation:** `spec-reconcile-pass` will see the `### Architect (reconcile)` subsection with content and advance. Handing off to Drummer for finish.

### Post-gate addendum — team-lead late checks

Three checks requested after the gate had already resolved. Verified post-hoc for traceability; no re-open:

1. **Enum variant parity (MetricDirection, EncounterPhase)** — Rust `encounter.rs:23,37` declares `{Ascending, Descending, Bidirectional}` and `{Setup, Opening, Escalation, Climax, Resolution}`. Python `encounter.py:119-121,132-136` declares the identical 3- and 5-variant sets with matching spelling. Tests at `test_encounter.py` assert the full sets equal. ✓ No drift.

2. **Wiring-test re-export surface (RigType, Combatant)** — `sidequest/game/__init__.py` imports `Combatant` at line 23 and re-exports via `__all__` at line 98; `RigType` re-exported at line 130. Wiring test's expected list aligns with the actual surface. ✓ No drift.

3. **`extra=forbid` spec-text check** — Spec-check assessment (section above, line 286+) and story context AC6 scope `extra: ignore` to `GameSnapshot` only. No spec text implied inner types should be `ignore`. The `da7a731` tightening on inner types is in-scope relative to the AC contract and is logged as the `### Architect (reconcile)` deviation below. ✓ No spec-text/implementation disagreement.

**Non-blocking observations** (forward-context for future stories, not spec drift):

- **[RULE] OTEL on `resolve_from_trope` — hard dependency on 42-4.** Confirmed. Epic 42 plan (`context-epic-42.md`) explicitly routes OTEL emission to story 42-4 ("combat / encounter resolution + OTEL"). The existing Design Deviation D4 already carries this forward-impact note. No additional logging needed; 42-4 SM must include OTEL spans in AC set when spec'd.
- **[DOC] Stale docstrings in `tests/test_combatant.py:99,122`** referencing Character `edge_fraction` drift that was fixed in this branch. Cosmetic test-file documentation, not spec-relevant. Logging here so 42-2 or later can tidy during nearby edits; not worth a dedicated follow-up.

— Naomi, design mode