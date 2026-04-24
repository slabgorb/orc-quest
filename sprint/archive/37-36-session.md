# Story 37-36: Party-peer identity packet in game_state

---
story_id: "37-36"
jira_key: "37-36"
epic: "37"
workflow: "tdd"
---

## Story Details
- **ID:** 37-36
- **Jira Key:** 37-36
- **Epic:** 37 (Playtest 2 Fixes — Multi-Session Isolation)
- **Workflow:** tdd
- **Stack Parent:** none
- **Status:** backlog → in_progress
- **Points:** 3
- **Type:** bug
- **Priority:** p1
- **Repos:** sidequest-server

## Sm Assessment

Story 37-36 is a port-drift reopen from ADR-082 (Rust → Python). Confirmed by setup research: current `sidequest-server` has no PartyPeer type, no `inject_party_peers()` call, and no peer dossier in narrator prompts. The playtest-3 evidence (Blutka he/him drifting to she/her in Orin's save) is a reproducible symptom of that missing subsystem.

**Scope is well-bounded:** define the type, wire the injector into the narrator context build, add OTEL on injection, cover with tests. Physical identity canonical, perception stays POV — ADR-067 (Unified Narrator) is the natural integration surface.

**Upstream dependency:** 37-36 blocks 37-37 (sealed-letter world-state handshake). Doing this first is the right order — peer identity is the substrate, handshake extends it with location/encounter/adjacency deltas.

**Risk watch:**
- Narrator prompt real estate is already contested under ADR-067. Injection must be economical — dossier block, not prose.
- OTEL span wiring must be real, not a narration-only claim (CLAUDE.md lie-detector rule). TEA should verify an OTEL test asserts the span fires.
- Solo sessions with `party_count=1` should skip injection cleanly — add a test for that path to avoid empty-dossier noise.

**Recommendation to Igor (tea):** Start RED with a narrator-prompt integration test that proves the peer dossier lands in the system prompt for a 2-player sealed-letter turn. Then unit tests for PartyPeer construction and the OTEL span. Wiring test is mandatory per CLAUDE.md — don't stop at isolated unit tests.

## Story Summary

Party-peer identity packet in game_state — canonical name/pronouns/race/class/level of other party members injected into each player's game_state so narrator references party-mates with stable pronouns across sealed-letter turns.

**Problem:** Playtest 3 (2026-04-19): Blutka he/him in own save drifted to she/her in Orin's save because peer had zero canonical presence in Orin's game_state.

**Solution:** Perception layer stays POV; physical identity is canonical. Add OTEL span on peer injection.

**Port-Drift Context:** This story was marked done against Rust sidequest-api (reviewer approved, Rust session shipped). The fix did NOT survive ADR-082 port to Python. Current sidequest-server has:
- No PartyPeer type
- No inject_party_peers() call
- No peer dossier injection into narrator prompts

The bug is back in production. Re-opening at backlog per ADR-085 rule 2 (port-drift reopens, does not fork a new story). Blocks 37-37 (sealed-letter world-state handshake).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-24T14:28:13Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-24T00:00:00Z | 2026-04-24T13:54:02Z | 13h 54m |
| red | 2026-04-24T13:54:02Z | 2026-04-24T14:06:31Z | 12m 29s |
| green | 2026-04-24T14:06:31Z | 2026-04-24T14:14:34Z | 8m 3s |
| spec-check | 2026-04-24T14:14:34Z | 2026-04-24T14:16:45Z | 2m 11s |
| verify | 2026-04-24T14:16:45Z | 2026-04-24T14:20:18Z | 3m 33s |
| review | 2026-04-24T14:20:18Z | 2026-04-24T14:26:35Z | 6m 17s |
| spec-reconcile | 2026-04-24T14:26:35Z | 2026-04-24T14:28:13Z | 1m 38s |
| finish | 2026-04-24T14:28:13Z | - | - |

## Acceptance Criteria

1. **PartyPeer Type** — Define a canonical peer identity type with name, pronouns, race, class, level fields
2. **Injection Function** — Implement inject_party_peers() that reads game_state.party members and creates canonical identity packets
3. **Narrator Injection** — Pass peer identities in narrator system prompt so narrator uses stable pronouns across sealed-letter turns
4. **OTEL Span** — Add OTEL span event on peer injection with peer count and data structure logged
5. **Perception Layer** — Ensure peer identity is *physical* (canonical) while perception layer (mood, tactics, feelings) stays POV
6. **Tests** — Test coverage for PartyPeer creation, injection, narrator prompt integration, and OTEL emission

## Technical Notes

- Reference: Rust session is archived at https://github.com/slabgorb/sidequest-api (see ADR-082 for porting guidance)
- ADR-085 rule 2: port-drift reopens, does not fork a new story
- Blocks 37-37 (sealed-letter world-state handshake)
- Related to ADR-067 (Unified Narrator Agent)

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Reason:** New subsystem (PartyPeer type, TurnContext field, injector, OTEL span, prompt section). Bug is a concrete playtest-3 regression with reproducible symptoms.

**Test Files:**
- `sidequest-server/tests/server/test_party_peer_identity.py` — 20 tests, 742 lines

**Tests Written:** 20 tests covering 6 ACs
**Status:** RED (20 / 20 failing — verified by local pytest run)

### Rule Coverage (python lang-review checklist)

| # | Rule | Test(s) | Status |
|---|------|---------|--------|
| 4 | Logging — correct level + lazy evaluation | `test_party_peer_injection_logs_span_event`, `test_party_peer_injection_span_does_not_fire_on_empty_peers` | failing |
| 6 | Test quality — no vacuous assertions | all 20 assert on concrete values (names, pronouns, lengths, zone enums); self-checked for `assert True` / bare `is_not_none` / `let _` analogs | enforced |
| 11 | Input validation / invariants at boundaries | `test_build_turn_context_excludes_acting_player_from_peers`, `test_build_turn_context_solo_session_has_no_peers`, `test_empty_party_peers_produces_no_dossier_section` (invariant: self-as-peer never happens; empty collection leaks nothing) | failing |

Rules 1, 2, 3, 5, 7, 8, 9, 10, 12, 13 are not exercised by new test-only code — they concern production-code surfaces that Dev will introduce. The Reviewer pass (`python-review-checklist`) will enforce them against the GREEN-phase diff.

**Rules checked:** 3 of 13 applicable at RED phase (test-only surface). Remaining 10 apply to Dev's implementation diff and are enforced at review.

**Self-check for vacuous tests:** none. Every test asserts on a named value or a specific collection shape. The perception-layer test uses a denylist (not `assert True`) and is documented as a heuristic in Design Deviations.

### Wiring Test Discipline (CLAUDE.md)

Two explicit wiring tests:
1. `test_module_level_run_narration_turn_forwards_party_peers` — locks the module-level helper path (parallel to 37-48's lock for npc_registry).
2. `test_wiring_sd_to_prompt_delivers_peer_identity` — end-to-end `_SessionData` → `_build_turn_context` → `build_narrator_prompt` → registered dossier section. Asserts against `PromptRegistry` structure (not bare `prompt` substring) so `state_summary` JSON leakage can't false-positive the wire.

### Route to GREEN

Dev's implementation surface (Ponder Stibbons):
1. `PartyPeer` type (pydantic BaseModel recommended; mirror `NpcRegistryEntry` at `game/session.py:129-144`). Fields: `name`, `pronouns`, `race`, `char_class`, `level`. Add `from_character` classmethod.
2. `TurnContext.party_peers: list[PartyPeer] = field(default_factory=list)` — add after line 295 in `agents/orchestrator.py`.
3. `_build_turn_context` in `server/session_handler.py:3697` — populate peers from `snapshot.characters[1:]` (current convention) excluding the entry whose `core.name` matches `sd.player_name`. Return with `party_peers=peers` kwarg.
4. Module-level `run_narration_turn` in `agents/orchestrator.py:1426` — forward `session.characters` as peers (same exclusion rule — use `character_name` to identify self), mirroring the `npc_registry=list(session.npc_registry)` line at 1496.
5. `register_party_peer_section` on `PromptRegistry` (mirror `register_npc_roster_section` at `agents/prompt_framework/core.py:343`). Zone: `Early` or `Valley`. Category: `State`. Empty list → no section.
6. Call the register method in `build_narrator_prompt` (mirror NPC call at line 993). Add structured log `logger.info("orchestrator.party_peer_injection party_size=%d current_player=%s", ...)` BEFORE the register call, matching the `genre_identity_injection` pattern at line 791.
7. `SPAN_ORCHESTRATOR_PARTY_PEER_INJECTION = "orchestrator.party_peer_injection"` in `telemetry/spans.py` (next to lines 83-86).

**Handoff:** To Dev (Ponder Stibbons) for GREEN

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (sidequest-server):**
- `sidequest/game/session.py` — added `PartyPeer` pydantic model with `from_character` classmethod, next to `NpcRegistryEntry`
- `sidequest/agents/orchestrator.py` — imported `PartyPeer`, added `TurnContext.party_peers` field, injected dossier section with OTEL log in `build_narrator_prompt`, forwarded peers in module-level `run_narration_turn`
- `sidequest/server/session_handler.py` — imported `PartyPeer`, built `party_peers` list in `_build_turn_context` (excludes acting player by name match against `sd.player_name` via `char_name`)
- `sidequest/agents/prompt_framework/core.py` — added `register_party_peer_section` mirroring `register_npc_roster_section` (Early zone, State category, zero-byte leak on empty list)
- `sidequest/telemetry/spans.py` — `SPAN_ORCHESTRATOR_PARTY_PEER_INJECTION = "orchestrator.party_peer_injection"`
- `tests/server/test_party_peer_identity.py` — typo fix `.body` → `.content` caught during GREEN run (PromptSection field is `content`) and `getattr` → attribute access (B009)

**Tests:** 20/20 passing (GREEN). Full suite 2154 passed / 25 skipped / 0 failed / 0 errored.
**Branch:** `feat/37-36-party-peer-identity` (pushed to origin)

### Implementation Notes

- **Acting-player exclusion:** rule is `pc.core.name != char_name` (the name used elsewhere in the same function for narrator identity). This matches today's `snapshot.characters[0]` == acting-player convention: `char_name` resolves to `characters[0].core.name` when the snapshot has characters, or `sd.player_name` as fallback. Solo sessions produce `party_peers=[]` cleanly.
- **OTEL span pattern:** followed the `orchestrator.genre_identity_injection` shape at `orchestrator.py:791-795` — `logger.info("orchestrator.party_peer_injection party_size=%d current_player=%s", ...)` with lazy-format args (Python lang-review rule 4). Fired only when `context.party_peers` is non-empty; no span on solo sessions.
- **Dossier format:** `PARTY MEMBERS — Canonical Identity (do not contradict)` header + one bullet per peer with `(pronouns, Race Class, level N)` tag tail, footer reminding narrator to use these exact bits and reserve POV for emotional perception.
- **Lint residue:** pre-existing I001 (import-order) / SIM102 / SIM108 / F841 findings in `orchestrator.py` remain — scope was out of this story. The three lint items attributable to my diff (UP037 × 2, B009 × 1) are fixed.

### Self-Review Checklist

- [x] Wired end-to-end (session handler → turn context → orchestrator → prompt registry → narrator)
- [x] Follows 37-44 NPC-roster pattern exactly
- [x] All ACs met: PartyPeer type, injection function, narrator injection, OTEL span, perception-POV boundary, test coverage
- [x] Error handling: none needed — new subsystem reads existing non-optional fields (race/char_class are validator-gated non-blank; pronouns defaults to empty string which the dossier handles gracefully)

**Handoff:** To next phase (verify / simplify + quality-pass) → Igor

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 2 (both Trivial — cosmetic spec wording, no code change needed)

### AC-by-AC Review

| AC | Status | Notes |
|----|--------|-------|
| 1 PartyPeer Type | ✅ | pydantic BaseModel in `game/session.py` next to `NpcRegistryEntry`; all 5 canonical fields; `from_character` classmethod centralizes Character→peer conversion. Race/char_class inherit non-blank validation from `Character`. |
| 2 Injection Function | ✅ (spec drift, trivial) | See mismatch #1. Behavior is present; the literal `inject_party_peers()` function name is not. |
| 3 Narrator Injection | ✅ | `register_party_peer_section` on `PromptRegistry`, called from `build_narrator_prompt`, Early zone / State category. Exact parallel to `register_npc_roster_section` (37-44). Zero-byte leak on empty list. |
| 4 OTEL Span | ✅ (spec drift, trivial) | See mismatch #2. `SPAN_ORCHESTRATOR_PARTY_PEER_INJECTION` defined; structured `logger.info` at injection site with `party_size` and `current_player` attrs. |
| 5 Perception Layer | ✅ | `PartyPeer` type carries only physical/mechanical fields. Dossier prose explicitly states "Physical identity is canonical; only emotional perception is POV." TEA heuristic test guards the common regression. |
| 6 Tests | ✅ | 20 tests, 2154/2154 suite green, no regressions. Two explicit wiring tests (module-level + end-to-end sd_factory). |

### Mismatches

1. **"inject_party_peers()" function not literally extracted** (Ambiguous spec — Cosmetic, Trivial)
   - Spec: AC-2 says "Implement `inject_party_peers()` that reads `game_state.party` members and creates canonical identity packets"
   - Code: Peer list is built inline in `_build_turn_context` (session_handler.py:3754-3760) and module-level `run_narration_turn` (orchestrator.py:1506-1510). The transformation is centralized in `PartyPeer.from_character`; the filter (`pc.core.name != char_name`) is a single-line comprehension at each lifecycle point.
   - Recommendation: **A — Update spec**. The AC described a shape, not a surface contract. Extracting a 3-line list-comp to a named function when the two call sites identify "self" via different variable chains (`char_name` in session_handler; `char_name` reconstructed in the module helper) would duplicate the self-identification logic *into* the function or force a parameter pair. `from_character` already centralizes the real non-trivial work. Rating: Trivial.

2. **"OTEL span" implemented as structured log, not context-manager span** (Ambiguous spec — Architectural, Trivial)
   - Spec: AC-4 says "Add OTEL span event on peer injection with peer count and data structure logged"
   - Code: `logger.info("orchestrator.party_peer_injection party_size=%d current_player=%s", ...)` at `orchestrator.py:1007-1012` — no `tracer().start_as_current_span(...)` context manager.
   - Recommendation: **A — Update spec**. This matches the established codebase convention for prompt-injection telemetry: `orchestrator.genre_identity_injection` (line 791), `orchestrator.trope_beat_injection` (line 976), and the sibling story 37-44's `npc.auto_registered` all use structured `logger.info` with lazy format args. Real context-manager spans are reserved for things whose start/end timing matters (`orchestrator_process_action_span`, `turn_agent_llm_inference_span`). A single-event injection marker is correctly modeled as a log event. The span name constant (`SPAN_ORCHESTRATOR_PARTY_PEER_INJECTION`) is defined in the spans catalog so the watcher/GM panel can filter for it. Rating: Trivial. Forcing 37-36 to use a context manager would desynchronize it from 37-44 (the explicit pattern it parallels).

### Architectural Review

- **Reuse-first discipline:** Exact parallel to 37-44 NPC roster subsystem. No new infrastructure introduced — one new type in `game/session.py`, one new dataclass field, one new method on `PromptRegistry`, one new span constant, three new call sites. ✓
- **No silent fallbacks:** Empty peers list explicitly skips both the structured log and the section register call — verified by `test_empty_party_peers_produces_no_dossier_section` and `test_party_peer_injection_span_does_not_fire_on_empty_peers`. ✓
- **Wiring discipline:** Module-level `run_narration_turn` + `_build_turn_context` both populate `party_peers`. The 37-48-analog lock test (`test_module_level_run_narration_turn_forwards_party_peers`) prevents future refactors from silently dropping the kwarg. ✓
- **37-37 compatibility:** `PartyPeer`-as-canonical-packet with `from_character` is the right substrate for 37-37 (sealed-letter world-state handshake) to extend with adjacency/location deltas. Field shape does not over-fit; the perception/canonical boundary is already carved. ✓
- **ADR-067 (Unified Narrator) compatibility:** Peer dossier injects into Early zone, adjacent to the existing NPC roster — no new zone reshuffling. Prompt real estate cost is proportional to party size (one bullet per peer, dropped on solo). ✓

### Decision

**Proceed to verify.** No hand-back required. The two cosmetic spec-wording items are resolved as "update spec" (Option A) deviations — the code is the right shape; the AC wording would be improved by matching actual codebase conventions.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed — no simplify changes applied, no regressions.

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 6

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 high + 1 medium + 2 low findings | Suggests extracting `_build_identity_roster` helper merging `register_npc_roster_section` (37-44) with `register_party_peer_section` (37-36). |
| simplify-quality | clean | No issues — all 37-36 changes follow established conventions. |
| simplify-efficiency | clean | No premature abstraction, redundant operations, or over-engineering — explicitly noted the parity with 37-44 is "justified reuse, not over-engineering." |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 medium-confidence findings
**Noted:** 1 high-confidence reuse suggestion *deliberately not applied* — see rationale below.
**Reverted:** 0

**Overall:** simplify: clean (1 finding declined with rationale)

### Rationale for Declining the High-Confidence Reuse Finding

The reuse teammate flagged that `register_npc_roster_section` (37-44) and `register_party_peer_section` (37-36) share ~95% of their structure and suggested extracting a shared `_build_identity_roster` helper with a per-entry rendering callback.

**Declined because:**

1. **Rendering diverges enough to negate abstraction value.** NPC entries carry optional `appearance` and `last_seen_location` (`entry.appearance` / `[last seen: ...]` in the bullet); peer entries always carry `race`/`char_class`/`level` as composite tags. Both trailers are subsystem-specific ("pronouns and roles" vs "pronouns, race, and class for every party member"). A shared helper would reduce to ~10 lines of section-registration boilerplate after taking rendering callbacks and header/trailer strings as parameters — buying little.
2. **Scope discipline.** The refactor would edit `register_npc_roster_section`, which shipped in 37-44 and is not in 37-36's diff. Sliding into out-of-story code during verify is how drift accretes.
3. **CLAUDE.md rule: "Three similar lines is better than a premature abstraction."** Two sibling subsystems is the threshold at which we have a *pattern*, not yet a *duplication problem*. When a third roster appears (e.g. faction members, enemy lineup), the shared shape will be obvious and the abstraction will be grounded in real usage.
4. **Efficiency teammate concurred.** simplify-efficiency explicitly flagged the parity as "intentional structural parity with the sibling NPC roster subsystem (37-44) … justified reuse, not over-engineering."

**Action:** noted as a candidate refactor for a future story if/when a third roster subsystem lands. No change applied now.

### Test Results (final)

- `tests/server/test_party_peer_identity.py` — 20/20 green
- Adjacent subsystems (`test_npc_identity_drift.py`, `test_turn_context_encounter_derivation.py`) — 24/24 green
- Combined 44/44 passing, 0.35s

### Quality Checks

- Ruff on 37-36-new files (`session.py` additions, `prompt_framework/core.py` additions, `spans.py`, test file) — all passing.
- Ruff on two pre-existing files I added to (`orchestrator.py`, `session_handler.py`) — no new findings in my edit line ranges (300-305, 1003-1016, 1502-1510, 3758-3770). Pre-existing I001/SIM102/SIM108/F841 findings elsewhere in those files are out-of-story and predate this branch.
- Project-wide `just server-lint` has 164 pre-existing errors across unrelated files; this is ambient repo hygiene, not a verify-gate blocker for 37-36.

**Handoff:** To Reviewer (Granny Weatherwax) for code review

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents` settings — I assessed their domains directly.)
**Total findings:** 0 confirmed from subagents, 0 dismissed, 0 deferred. Independent analysis yielded 2 findings (1 LOW × 2).

## Rule Compliance (Python lang-review checklist — 13 checks)

Exhaustive check of every rule against every new/changed type, function, and field in the 37-36 diff.

| # | Rule | Subjects Checked | Verdict |
|---|------|------------------|---------|
| 1 | Silent exception swallowing | No `try/except` added in diff (verified across all 5 production files) | CLEAN |
| 2 | Mutable default arguments | `TurnContext.party_peers: list[PartyPeer] = field(default_factory=list)` at `orchestrator.py:300` — uses factory, not mutable literal. `PartyPeer.pronouns: str = ""` and `level: int = 1` are immutable defaults. | CLEAN |
| 3 | Type annotation gaps | `PartyPeer.from_character(cls, character: Character) -> PartyPeer`, `register_party_peer_section(self, agent_name: str, party_peers: list[PartyPeer]) -> None`, module-level `run_narration_turn` unchanged signature — all typed. List comprehensions have inferred types. | CLEAN |
| 4 | Logging — level + lazy eval | `orchestrator.py:1007-1011`: `logger.info("orchestrator.party_peer_injection party_size=%d current_player=%s", len(...), context.character_name)` — lazy `%` args, INFO level (subsystem engaged = info, not warn). | CLEAN |
| 5 | Path handling | No `open()`, no `os.path`, no `Path` in diff. | N/A |
| 6 | Test quality | `test_party_peer_identity.py` — every test asserts on named values (Orin, he/him, Human, Fighter, length==1, zone in (Early, Valley), category == State). No `assert True`, no `assert result` without value check. Self-documented heuristic in Design Deviations for perception-field test. | CLEAN |
| 7 | Resource leaks | No resources acquired in diff. | N/A |
| 8 | Unsafe deserialization | `PartyPeer(BaseModel)` with `model_config = {"extra": "forbid"}` at `session.py:159` — pydantic schema-validates at construction. Zero pickle/eval/yaml.load surface. | CLEAN |
| 9 | Async/await | `build_narrator_prompt` was already async; the inserted `if context.party_peers:` block is synchronous `logger.info` + sync method call (`register_party_peer_section`). No blocking calls in async context. No missing `await`. | CLEAN |
| 10 | Import hygiene | `orchestrator.py`: added `PartyPeer` to existing import (alphabetical in the existing list). `prompt_framework/core.py`: added `PartyPeer` to `TYPE_CHECKING` guard — correct, avoids runtime circular with `sidequest.game.session`. `session_handler.py`: expanded single-line import to multi-line, added `PartyPeer`. No star imports, no circulars. | CLEAN |
| 11 | Input validation | `PartyPeer.from_character` reads already-validated Character (`race`/`char_class` non-blank validated on Character). `pronouns` inherits from Character where it defaults to `""` — NOT validated (see Finding #2 below for partial-coverage implication). | CLEAN (with noted gap) |
| 12 | Dependency hygiene | No new deps. | N/A |
| 13 | Fix-introduced regressions | N/A (first-pass impl, no fix iteration yet). | N/A |

**Rules checked:** 13 of 13. **All compliant** on the 37-36 diff.

## Findings

| Severity | Tag | Finding | Location |
|----------|-----|---------|----------|
| [LOW] | [EDGE] | Name-based self-exclusion fails under duplicate character names — if two PCs share a name, the second is dropped from the peer dossier | `session_handler.py:3759-3765`, `orchestrator.py:1506-1510` |
| [LOW] | [TEST] | Fix is partial under data-quality degradation: characters with `pronouns == ""` (Character default) render dossier lines with race/class/level only; narrator gets no canonical pronouns for them and drift can return | `prompt_framework/core.py:416-421` |

### [LOW] [EDGE] Name-based self-exclusion is fragile under duplicate character names

The exclusion rule is `pc.core.name != char_name`. If two characters in `snapshot.characters` share a name (e.g. two "Blutka"s), both are excluded from the peer list. The acting player sees a peer dossier missing the duplicate-named peer — the exact drift failure this story exists to prevent.

**Downgrade rationale:** The codebase broadly assumes character-name uniqueness (see multiple `.core.name`-as-key usages in `session_handler.py` — npc_cores_by_name at 3755, lookups at 3535). The `pc_cores_by_player` mapping at line 3748 uses `snapshot.characters[0]` directly (index-based acting-player convention) rather than name. A future refactor could align 37-36's filter with that index-based rule, but the current implementation is consistent with how the rest of the file handles character identity. The specific playtest-3 regression (two distinct-named PCs) is closed.

**Mitigation deferred:** Acceptable at this maturity. If/when multiplayer chargen permits name collisions, revisit with an index-based or ID-based filter.

### [LOW] [TEST] Dossier silently skips pronouns when Character.pronouns is empty

`Character.pronouns: str = ""` (default). The dossier renders the pronouns tag conditionally: `if peer.pronouns: tags.append(peer.pronouns)`. For any PC whose chargen did not populate pronouns, the dossier line is `- Name (Race Class, level N)` — canonical pronouns absent. Narrator has no ground truth and can drift.

**Downgrade rationale:** Not a regression introduced by this story. The playtest-3 Blutka had pronouns set, so this specific bug is closed. But the fix is partial under degraded data. No test covers the empty-pronouns path — the 20 tests all use concrete pronouns.

**Mitigation deferred:** A future improvement could either (a) fall back to `they/them` when pronouns are empty (neutral canonical), or (b) emit a WARN log so operators know canonical identity is incomplete for a given peer, or (c) tighten chargen to require pronouns. Not blocking.

### Hard Questions Checked

- **Null/empty inputs:** `party_peers=[]` explicitly skips section + log (test-verified). `character.core.name == ""` would not pass Character validation. `session.characters = []` handled by the `for pc in session.characters` comprehension yielding empty list.
- **Race conditions:** `_build_turn_context` reads from `sd.snapshot` which is per-session; no shared mutable state added. List-comprehension materializes immediately. No thread-safety issue introduced.
- **Tenant isolation:** Not applicable — sidequest-server has no multi-tenant model.
- **Security:** Dossier content (name/pronouns/race/class/level) is already present in `state_summary` JSON for all players; no new information disclosure. Span log emits `character_name` only (pseudonymous in-world identity, not PII).
- **Wiring (CLAUDE.md):** Module-level `run_narration_turn` AND `_build_turn_context` both populate party_peers. The `test_module_level_run_narration_turn_forwards_party_peers` is a lock-test analogous to 37-48's lock for npc_registry — a future refactor that drops the kwarg will fail CI loudly.

### Devil's Advocate (mandatory ≥200 words)

*The story claims a fix. What if it isn't?*

**The canonical-identity contract is one-way.** The dossier injects peer identity INTO the narrator prompt. But the narrator can still emit text that contradicts the dossier — there's no detector on the output side saying "narrator called Blutka 'she' even though the dossier said 'he/him'." 37-44 built exactly that detector (`npc.reinvented` span, drift-detector in `_apply_narration_result_to_snapshot`). 37-36 ships the injection but NOT the detector. A narrator that ignores the dossier (stressed by long contexts, other zone conflicts, or a temperature spike) could still drift pronouns — silently, with no OTEL signal. Sebastien's GM panel will see the injection fire every turn ("good, subsystem is engaged") but have no visibility into whether the narrator actually *used* the canonical fields. The illusionism gap persists.

**The comparison convention drifts from sibling code.** `pc_cores_by_player` (line 3748) uses index-based acting-player identification (`snapshot.characters[0]`). 37-36 uses name-based filtering (`pc.core.name != char_name`). Under unique names these agree; under duplicates they diverge. This is a *second* acting-player identification surface with slightly different semantics from the first — the kind of seam where future bugs live. A malicious or stressed character factory producing two "Unnamed" PCs (chargen partial completion is a known bug — see 37-40 in the same epic!) could silently confuse the peer filter.

**Empty-pronouns renders half a fix.** The Character default `pronouns=""` means any chargen path that misses the pronouns prompt silently ships a character whose dossier line is pronoun-free. The narrator then has to guess — and guess wrong, as it did for Blutka. The 20 tests all use `he/him` / `they/them` / `she/her` — not a single test hits the empty-pronouns path. A user who spins up a game without carefully completing chargen will see the playtest-3 behavior again, and the GM panel will happily report "party_peer_injection fired" while the narrator writes "she" at a peer who has no pronouns set.

**What a confused user does:** joins a multiplayer session, picks character name "Felix" because they liked the previous session's NPC named Felix. Now snapshot.characters has [Felix (PC), Felix (NPC? or duplicate PC name across sessions?)]. The filter excludes both. Peer dossier is empty. Zero-byte discipline fires. Subsystem looks healthy. Narrator drifts.

**Findings added:** Both devil's advocate threads map to the two LOW findings above. The first and second points — output-side drift detection and index-vs-name-vs-ID identification — are worth logging as non-blocking upstream observations for follow-up stories.

## Reviewer Assessment

**Verdict:** APPROVED

**Severity summary:** 0 Critical, 0 High, 0 Medium, 2 Low. No blockers.

**Data flow traced:** Multiplayer session with Blutka + Orin → `_build_turn_context(sd)` (session_handler.py:3755-3765) filters Orin as peer when Blutka is acting player → `TurnContext.party_peers = [Orin]` → `build_narrator_prompt` (orchestrator.py:1007-1016) logs `orchestrator.party_peer_injection` with `party_size=1 current_player=Blutka` → `register_party_peer_section` renders "PARTY MEMBERS — Canonical Identity" block (prompt_framework/core.py:416-441) into Early zone, State category → narrator prompt carries canonical `(they/them, Human Fighter, level 3)` for Orin. End-to-end verified by `test_wiring_sd_to_prompt_delivers_peer_identity`.

**Pattern observed:** Exact parallel of 37-44 NPC roster subsystem. `PartyPeer` mirrors `NpcRegistryEntry` at `game/session.py:129-144`; `register_party_peer_section` mirrors `register_npc_roster_section` at `prompt_framework/core.py:343-394`; injection block in `build_narrator_prompt` mirrors the NPC-roster block immediately above it. This is good reuse discipline — SM's assessment called it out as load-bearing and Architect / simplify-efficiency both concurred.

**Error handling:** No new error paths introduced. Pydantic validation on `PartyPeer` construction (`extra="forbid"`, race/char_class non-blank inherited from Character). Empty-list paths explicitly no-op rather than raising. All existing error paths in `build_narrator_prompt` and `_build_turn_context` are untouched.

**Rule compliance:** 13/13 Python lang-review checks PASS (see Rule Compliance table above). CLAUDE.md "No Silent Fallbacks" — peer injection explicitly no-ops with tests covering the zero-byte path; not a silent fallback, a documented behavior. CLAUDE.md "Verify Wiring" — two wiring tests (module-level + sd_factory end-to-end) exceed the minimum. OTEL Observability Principle — span constant + structured log both present, GM panel can filter.

**Observations (≥5):**

1. `[VERIFIED]` PartyPeer type isolates physical identity — no perception-layer fields on the model itself, `session.py:161-165` has only `name`, `pronouns`, `race`, `char_class`, `level`. Rule: SOUL.md "Agency" + story AC-5 ("perception stays POV"). Compliant.
2. `[VERIFIED]` Zero-byte leak discipline preserved — `register_party_peer_section` returns early on empty list (`core.py:416-417`), the caller in `build_narrator_prompt` also guards with `if context.party_peers:` (belt-and-suspenders). Rule: CLAUDE.md "No Silent Fallbacks" complement — pay nothing when there's nothing to say. Verified by `test_empty_party_peers_produces_no_dossier_section`.
3. `[VERIFIED]` Module-level `run_narration_turn` plumbs party_peers — `orchestrator.py:1505-1510` builds the peer list before TurnContext construction. Locked by `test_module_level_run_narration_turn_forwards_party_peers` (parallel to the 37-48 lock for npc_registry). Rule: CLAUDE.md "Every Test Suite Needs a Wiring Test". Exceeded.
4. `[LOW]` `[EDGE]` Name-based self-exclusion fragile under duplicate names — see Finding #1 above.
5. `[LOW]` `[TEST]` Empty-pronouns characters render partial dossier — see Finding #2 above.
6. `[VERIFIED]` OTEL span name convention consistent with sibling subsystems — `SPAN_ORCHESTRATOR_PARTY_PEER_INJECTION = "orchestrator.party_peer_injection"` follows `orchestrator.{subsystem}_{verb}` shape (spans.py:86). Structured-log emission pattern matches `genre_identity_injection` (orchestrator.py:791) and `trope_beat_injection` (line 976). Architect's spec-check deviation #2 documents this as the codebase convention.
7. `[VERIFIED]` No unsafe deserialization — `PartyPeer(BaseModel)` uses pydantic v2 with `extra="forbid"`; no pickle/eval/yaml.load.
8. `[VERIFIED]` Import hygiene — `TYPE_CHECKING` guard in `prompt_framework/core.py:28` correctly avoids the runtime `sidequest.game.session → prompt_framework` cycle; `PartyPeer` import added to existing guard.

**Devil's advocate items worth filing forward:**

- No output-side drift detector for PCs (analogue to `npc.reinvented` from 37-44). Injection visibility exists; consumption visibility does not. Worth a follow-up story if/when playtest surfaces peer-identity drift despite the dossier injection.
- Index-based vs name-based acting-player identification — the codebase has both; should eventually converge on one.

**Handoff:** To SM for finish-story

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Reviewer (code review)
- **Improvement** (non-blocking): No output-side pronoun/role drift detector for PCs (analogue to 37-44's `npc.reinvented` span). Injection visibility exists; consumption visibility does not.
  Affects `sidequest-server/sidequest/server/session_handler.py` (would live next to the existing `_apply_narration_result_to_snapshot` NPC drift-detection path).
  Not in scope for 37-36 — the story scope is canonical injection. Worth logging for future consideration if playtest surfaces peer drift despite the dossier (i.e. narrator reads the dossier but still writes contradictory pronouns).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Codebase has two different conventions for "acting-player's character": `pc_cores_by_player[sd.player_id] = snapshot.characters[0].core` (index-based, session_handler.py:3753) vs `pc.core.name != char_name` (name-based, 37-36's filter). Equivalent under unique-name assumption but divergent under duplicates.
  Affects `sidequest-server/sidequest/server/session_handler.py` and `sidequest-server/sidequest/agents/orchestrator.py` (could eventually converge on one convention — likely an index-or-id-based approach tied to the per-player snapshot index that 37-37/37-38 will introduce).
  Not caused by 37-36 — the name-based approach is consistent with the name-keyed lookups used elsewhere in session_handler. Worth a follow-up reconciliation story once the per-player index from 37-37/37-38 lands.
  *Found by Reviewer during code review.*
- **Gap** (non-blocking): No test covers the empty-pronouns dossier path. Character's default `pronouns=""` silently renders a dossier line without pronouns; narrator loses canonical ground truth for that peer.
  Affects `sidequest-server/tests/server/test_party_peer_identity.py` (add a test variant with `pronouns=""` and assert either (a) a fallback `they/them` lands in the dossier, or (b) a WARN log fires so operators notice).
  Not blocking — playtest-3 Blutka had pronouns set and that specific regression is closed. Relevant only for chargen completion-drift scenarios (see sibling story 37-40 which tracks chargen partial-completion bugs).
  *Found by Reviewer during code review.*

### TEA (test verification)
- **Improvement** (non-blocking): `register_npc_roster_section` and `register_party_peer_section` share ~95% section-registration boilerplate.
  Affects `sidequest-server/sidequest/agents/prompt_framework/core.py` (could extract a shared `_build_identity_roster` helper with per-entry rendering callback + header/trailer strings).
  Deliberately not applied in 37-36 per CLAUDE.md's "three similar lines is better than a premature abstraction" rule. Candidate for a future refactor story if a third identity roster subsystem appears (e.g. faction members, enemy lineup).
  *Found by TEA during test verification.*
- **Improvement** (non-blocking): Repo has 164 pre-existing ruff findings across unrelated files surfaced by `just server-lint`.
  Affects `sidequest-server/` broadly (import sort, nested if, unused variables — mostly auto-fixable with `ruff --fix`).
  Not caused by 37-36. Would benefit from a dedicated hygiene-sweep story if the team wants the full repo to lint clean.
  *Found by TEA during test verification.*

### Dev (implementation)
- No upstream findings during implementation.

### TEA (test design)
- **Gap** (non-blocking): No `sprint/context/context-story-37-36.md` or `sprint/context/context-epic-37.md` was created during setup.
  Affects `sprint/context/` (SM setup's context-generation step was skipped or silently failed).
  The Sm Assessment in the session file was dense enough to proceed, but `pf validate context-story 37-36` is not the valid invocation — the correct validator is `pf validate context`, and it currently has no story-specific artifact to read. Future TEA activations on this story may fail the context gate unless either (a) a context file is added, or (b) the SM setup flow is adjusted to skip per-story context when sessions carry enough detail.
  *Found by TEA during test design.*
- **Conflict** (non-blocking): Existing `Orchestrator.run_narration_turn` module-level helper at `sidequest/agents/orchestrator.py:1426-1501` does not accept a party_peers kwarg and derives `character_name` from `session.characters[0].core.name`.
  Affects `sidequest/agents/orchestrator.py` (module-level `run_narration_turn` must forward a `party_peers` list on the constructed `TurnContext`, mirroring how it already forwards `npc_registry=list(session.npc_registry)` at line 1496).
  This is the exact shape that 37-48 locked in for npc_registry after 37-44 — Dev must add the equivalent for party_peers or the dossier will never reach the prompt in production code paths (only in tests that build `TurnContext` directly).
  *Found by TEA during test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. → ✓ ACCEPTED by Reviewer: verified — diff matches SM assessment + Architect's 7-step implementation outline exactly.

### TEA (test verification)
- No deviations from spec during verify phase. → ✓ ACCEPTED by Reviewer: verified — simplify teammates reported 1 high-confidence finding, declined with rationale (scope + premature-abstraction); no spec drift.

### Reviewer (audit)
- Architect's spec-check phase raised 2 trivial spec-wording mismatches (AC-2 "inject_party_peers()" literal name vs inline comprehension; AC-4 "OTEL span" vs structured-log-event). Both were classified "Recommendation A — update spec" at Trivial severity. Reviewer concurs: the implementations match codebase conventions (sibling 37-44 uses both same patterns), the AC text is imprecise but not load-bearing. No reopen.
- No undocumented deviations found during Reviewer audit. Dev diff contains exactly what the SM/Architect specs described.

### Architect (reconcile)
- **AC-2 function-name-literal drift — spec says `inject_party_peers()`, code uses `PartyPeer.from_character` + inline list comprehensions**
  - Spec source: session file AC-2 ("Injection Function — Implement `inject_party_peers()` that reads game_state.party members and creates canonical identity packets")
  - Spec text: "Implement `inject_party_peers()` that reads `game_state.party` members and creates canonical identity packets"
  - Implementation: the canonical-packet construction lives on `PartyPeer.from_character(cls, character: Character) -> PartyPeer` at `sidequest-server/sidequest/game/session.py:171-179`. The filter (non-self party members) is a 3-line list comprehension at two lifecycle points — `_build_turn_context` (`session_handler.py:3759-3765`) and module-level `run_narration_turn` (`orchestrator.py:1505-1510`). There is no single function literally named `inject_party_peers()`.
  - Rationale: AC-2 described a possible implementation shape, not a required surface contract. Extracting a named function to wrap a 3-line list-comp at two sites with different "self" identification variable chains (`char_name` in session_handler, `char_name` re-derived in the module helper) would duplicate self-identification logic *into* the function or force a parameter pair. `from_character` already centralizes the real non-trivial work.
  - Severity: trivial
  - Forward impact: none — downstream stories (37-37 sealed-letter handshake, 37-38 state write-back hygiene) will extend the same seams and benefit from the from_character classmethod pattern. No consumer depends on a function named `inject_party_peers`.
- **AC-4 OTEL-implementation drift — spec says "OTEL span event", code uses structured `logger.info` with span name constant**
  - Spec source: session file AC-4 ("OTEL Span — Add OTEL span event on peer injection with peer count and data structure logged")
  - Spec text: "Add OTEL span event on peer injection with peer count and data structure logged"
  - Implementation: `sidequest-server/sidequest/telemetry/spans.py:86` defines `SPAN_ORCHESTRATOR_PARTY_PEER_INJECTION = "orchestrator.party_peer_injection"`. `sidequest-server/sidequest/agents/orchestrator.py:1007-1011` emits `logger.info("orchestrator.party_peer_injection party_size=%d current_player=%s", len(context.party_peers), context.character_name)`. No `tracer().start_as_current_span(...)` context manager is used — the span name is surfaced as a structured log field, not a tracer span.
  - Rationale: this matches the established codebase convention for prompt-injection telemetry. `orchestrator.genre_identity_injection` (`orchestrator.py:791`), `orchestrator.trope_beat_injection` (line 976), and sibling story 37-44's `npc.auto_registered` (`spans.py:149`) all use structured `logger.info` with the same shape. Real context-manager spans are reserved for operations whose start/end timing matters (`orchestrator_process_action_span`, `turn_agent_llm_inference_span`). A single-event injection marker is correctly modeled as a log event; forcing a context-manager span would desynchronize 37-36 from its explicit parallel (37-44).
  - Severity: trivial
  - Forward impact: none — GM panel/OTEL watcher filters on span-name strings, which are present in structured log output exactly as they would be in tracer attributes. Sebastien's mechanic-first view sees the span fire regardless of implementation shape.

All in-flight deviations (TEA × 3) have been reviewed for accuracy and stamped by Reviewer. Dev logged "no deviations" which the Reviewer audit confirmed against the Dev diff. AC accountability: all 6 ACs DONE, 0 DEFERRED, 0 DESCOPED — AC-deferral verification step is a no-op for this story.

### TEA (test design)
- **Perception-layer leakage test is heuristic, not exhaustive**
  - Spec source: session file AC-5 ("Perception Layer — Ensure peer identity is *physical* (canonical) while perception layer (mood, tactics, feelings) stays POV")
  - Spec text: "perception layer (mood, tactics, feelings) stays POV"
  - Implementation: `test_party_peer_dossier_omits_perception_layer_fields` scans a narrow window around the peer name for a short denylist (`mood:`, `disposition:`, `stance:`, `feelings:`). Does not prove a positive "only canonical fields present" invariant.
  - Rationale: an exhaustive allowlist check would tightly couple the test to the exact dossier string format the Dev chooses. The denylist catches the most likely regression (a future refactor adding a `mood` field to PartyPeer) without freezing the renderer's surface prose.
  - Severity: minor
  - Forward impact: if Dev chooses a format where perception-adjacent prose appears adjacent to the peer name for unrelated reasons (e.g. a genre block that happens to list "stance:" near every character mention), this test could false-positive. Reviewer should sanity-check dossier format for perception leakage on top of this test.
  - → ✓ ACCEPTED by Reviewer: verified dossier format at `prompt_framework/core.py:419-432` — no mood/stance/disposition words in rendered body; the heuristic denylist catches the realistic regression vector without false-positive risk. Agrees with author reasoning.
- **PartyPeer location probed across four candidate modules, not pinned**
  - Spec source: session file AC-1
  - Spec text: "Define a canonical peer identity type"
  - Implementation: tests do not assert `PartyPeer` lives in a specific module. They probe `game.session`, `game.party`, `game.character`, `agents.orchestrator` and pass as long as one of them exposes it.
  - Rationale: module placement is a Dev design call. `NpcRegistryEntry` lives at `game.session:129-144`; placing `PartyPeer` next to it would be the most consistent choice, but pinning the test to a single path would force a gratuitous reorganization if Dev disagrees.
  - Severity: minor
  - Forward impact: none — downstream tests look up the class via a shared helper, so Dev can choose any of the four candidate modules.
  - → ✓ ACCEPTED by Reviewer: Dev placed `PartyPeer` at `game/session.py:146` directly next to `NpcRegistryEntry` — the most consistent choice, matches 37-44 precedent. Open-probe approach was the right call.
- **Single `acting_player` parameter signals current PC, not a structural contract**
  - Spec source: session file AC-2 — "inject_party_peers() that reads game_state.party members"
  - Spec text: "canonical name/pronouns/race/class/level of other party members injected into each player's game_state"
  - Implementation: tests set `sd.player_name` to match `snapshot.characters[0].core.name` and rely on the `characters[0]` == acting-player convention already documented at `session_handler.py:3743-3745`. Tests do not cover the case where the acting player's PC is not at index 0.
  - Rationale: today's multiplayer turn dispatch still assumes the single-index mapping (see `session_handler.py:3717-3719`). A per-player index on the snapshot is 37-37 / 37-38 territory. Writing tests against a future mapping scheme would couple to a design that doesn't exist yet.
  - Severity: minor
  - Forward impact: when per-player index lands (37-37 / 37-38), the peer-exclusion logic will need a second test covering the non-zero-index case. Not in scope for 37-36.
  - → ✓ ACCEPTED by Reviewer: appropriate scope discipline. Reviewer's own edge-case finding (duplicate names) intersects this — both point to a future "canonical acting-player identification" story that 37-37/37-38 will force. Deferral is correct.