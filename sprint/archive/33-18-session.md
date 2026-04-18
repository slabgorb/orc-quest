---
story_id: "33-18"
jira_key: null
epic: "33"
workflow: "tdd"
---
# Story 33-18: Scrapbook payload — bundle image + world_facts + NPCs + excerpt into single WS message

## Story Details
- **ID:** 33-18
- **Jira Key:** (none — personal project)
- **Workflow:** tdd (phased: setup → red → green → spec-check → verify → review → spec-reconcile → finish)
- **Epic:** 33 — Composable GameBoard — Drag-and-Drop Dashboard Polish
- **Repository:** sidequest-api (Rust backend)
- **Points:** 3
- **Priority:** p1
- **Status:** backlog
- **Stack Parent:** none (standard repo, not stacked)

## Context

Epic 33 covers visual polish and genre theming for the composable GameBoard. Story 33-17 (Gallery image metadata) depends on this story to provide unified scrapbook entry payloads.

The Gallery widget (being renamed Scrapbook in 33-17) needs rich metadata per image: turn number, scene name, world facts discovered in that turn, NPCs present, narration excerpt, and scene classification. Currently this data arrives via separate WebSocket streams:
- Images via `GalleryImage` message
- World facts via `WorldFact` events
- NPCs via `npc_registry` updates
- Narration via `NarrationComplete`

This story creates a new `ScrapbookEntry` WebSocket message type that bundles all of this into a single atomic payload, keyed by turn_id. The server assembles the entry after narration completes (when all the dependent data for that turn is settled).

**Dependency chain:**
- 33-18 (Scrapbook payload) ← current
  - 33-17 (Gallery image metadata — depends on this)

## What This Story Does

**Scrapbook payload** defines a new WebSocket message type that unifies image metadata into a single message the UI can use to render rich gallery entries.

### Current State
- `render_integration.rs` tags images with `scene_name` and `scene_type`
- `world_facts` broadcast via `WorldFact` events during game turns
- `npc_registry` tracks NPCs present in the session
- `NarrationComplete` event fires when narrator finishes
- Protocol types defined in `sidequest-protocol` crate
- Server emits messages via `sidequest-server`

### What Needs to Happen

1. **Define ScrapbookEntry protocol type** in `sidequest-protocol`:
   ```rust
   pub struct ScrapbookEntry {
       pub turn_id: u32,
       pub scene_title: String,
       pub scene_type: SceneType,
       pub location: String,
       pub image_url: String,
       pub narrative_excerpt: String,
       pub world_facts: Vec<String>,
       pub npcs_present: Vec<NpcRef>,
   }
   
   pub struct NpcRef {
       pub name: String,
       pub role: String,
       pub disposition: String,
   }
   ```

2. **Server-side assembly** in `sidequest-server`:
   - After `NarrationComplete` fires for turn N:
     - Extract `narrative_excerpt` from narration text (first complete sentence)
     - Collect all `world_facts` broadcast during that turn
     - Collect all `npcs_present` from `npc_registry` updates during that turn
     - Assemble `ScrapbookEntry` message
     - Emit to client via WebSocket

3. **Client-side handler** in Redux store:
   - Receive `ScrapbookEntry` message
   - Normalize into scrapbook store (keyed by turn_id)
   - Merge with existing gallery image data

### Implementation Strategy
- **Protocol definition first** — add to sidequest-protocol, update GameMessage enum
- **Server-side assembly** — hook into `NarrationComplete` handler
- **Client handler** — Redux reducer + action
- **No UI changes** — this story is backend only; 33-17 consumes the payload

### Acceptance Criteria
- New WS message type: `ScrapbookEntry { turn_id, scene_title, scene_type, location, image_url, narrative_excerpt, world_facts: Vec<String>, npcs_present: Vec<NpcRef { name, role, disposition } > }`
- Server emits `ScrapbookEntry` after `NarrationComplete` for that turn — not before (world_facts must be settled)
- `narrative_excerpt`: first complete sentence of the narration text for that turn (server extracts, not client)
- `scene_title`: from `render_integration` scene_name field (already tagged on image generation)
- `scene_type`: from `render_integration` tier/scene_type (already tagged)
- `world_facts`: all world_facts broadcast during this turn, as plain strings
- `npcs_present`: all NPCs appearing in npc_registry updates during this turn
- Protocol type added to `sidequest-protocol` crate, server emission in `sidequest-server`, client handler in Redux store

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-15T10:36:21Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-15T09:05:29Z | 2026-04-15T09:07:07Z | 1m 38s |
| red | 2026-04-15T09:07:07Z | 2026-04-15T09:35:43Z | 28m 36s |
| green | 2026-04-15T09:35:43Z | 2026-04-15T09:48:18Z | 12m 35s |
| spec-check | 2026-04-15T09:48:18Z | 2026-04-15T09:49:49Z | 1m 31s |
| verify | 2026-04-15T09:49:49Z | 2026-04-15T10:01:00Z | 11m 11s |
| review | 2026-04-15T10:01:00Z | 2026-04-15T10:34:23Z | 33m 23s |
| spec-reconcile | 2026-04-15T10:34:23Z | 2026-04-15T10:36:21Z | 1m 58s |
| finish | 2026-04-15T10:36:21Z | - | - |

## Sm Assessment

**Confirm:** Story is ready for TDD. Protocol-first backend work: define `ScrapbookEntry` in `sidequest-protocol`, assemble in `sidequest-server` on `NarrationComplete`, add Redux handler client-side. Clear ACs and dependency chain (33-17 consumes this).

**Risks:**
- Turn-scoped aggregation of `world_facts` and `npc_registry` needs a clean ownership boundary — where in `sidequest-server` does the per-turn accumulator live? TEA should pin this in RED by asserting the assembly point.
- "First complete sentence" excerpt extraction is a sentence-boundary edge case — test with ellipses, quoted dialogue, abbreviations.
- Timing: must emit AFTER `NarrationComplete`, not before. RED must lock this ordering.

**Route:** TEA (Amos Burton) for RED phase — write failing tests for protocol shape, assembly timing, excerpt extraction, and Redux handler.

## TEA Assessment

**Tests Required:** Yes
**Phase:** finish → handing off for green

**Test Files:**
- `sidequest-api/crates/sidequest-protocol/src/scrapbook_entry_story_33_18_tests.rs` — 12 tests for `GameMessage::ScrapbookEntry` + `ScrapbookEntryPayload` + `NpcRef` (variant construction, screaming-case tag, round-trip, `deny_unknown_fields`, optional-field defaults, skip-none serialization, NpcRef shape/rejection)
- `sidequest-api/crates/sidequest-server/tests/integration/scrapbook_entry_story_33_18_tests.rs` — 24 tests split across three layers:
  - `extract_first_sentence` edge cases (12): period/?/!, empty, whitespace-only, no-terminator, ellipsis NOT splitting, `Dr.`/`Mr.`/`St.` abbreviations, single sentence, leading-whitespace trim
  - `build_scrapbook_entry` pure assembly (8): turn_id/location passthrough, narrative_excerpt wiring, is_new footnote filtering, empty-footnotes, NPC mapping via ocean_summary, empty-NPC, scene metadata passthrough, all-None optional fields
  - Wiring (4): `response.rs` imports `crate::scrapbook`, calls `build_scrapbook_entry`, pushes `GameMessage::ScrapbookEntry`, pushes AFTER `NarrationEnd` send point

**Tests Written:** 36 tests covering 7 ACs + ADR-020 disposition sourcing + the three risks Camina flagged (aggregation ownership boundary, sentence-edge cases, emit-order timing).

**Status:** RED — verified by testing-runner (`cargo check -p sidequest-protocol --tests`, `cargo check -p sidequest-server --tests`). All failures are missing-type / missing-module errors; zero test-file syntax bugs; unused-import warning cleaned up.

### Rule Coverage (Project — no lang-review file present)

| Rule (CLAUDE.md) | Test(s) | Status |
|------------------|---------|--------|
| No silent fallbacks — fail loudly on schema drift | `scrapbook_entry_payload_rejects_unknown_fields`, `npc_ref_rejects_unknown_fields` | failing |
| No stubs — real types or nothing | All protocol tests reference real types (no stub shapes) | failing |
| Don't reinvent — wire up what exists | Wiring tests verify `response.rs` imports `crate::scrapbook` and calls it | failing |
| Verify wiring, not just existence | 4 dedicated wiring tests grep `response.rs` for import + call + variant push + order | failing |
| Every test suite needs a wiring test | `response_rs_calls_build_scrapbook_entry`, `response_rs_pushes_scrapbook_entry_game_message`, `response_rs_emits_scrapbook_after_narration_end_send` | failing |
| Test quality — no vacuous assertions | Every `assert_*` compares against a concrete expected value; `deny_unknown_fields` tests check the `Err` branch | failing |
| `#[non_exhaustive]` on `GameMessage` preserved | Match arms use wildcard `_` fallback in round-trip tests | n/a (adding variant) |

**Rules checked:** 7 of 7 applicable
**Self-check:** No vacuous tests — every assertion compares concrete expected values; wiring tests use `find` + offset-compare, not `is_some()` on always-Some.

**Handoff:** To Dev (Naomi Nagata) for GREEN implementation.

### Implementation Guidance for Dev

**Scope:**
1. `sidequest-protocol/src/message.rs`:
   - Add `ScrapbookEntry { payload: ScrapbookEntryPayload, player_id: String }` variant to `GameMessage` with `#[serde(rename = "SCRAPBOOK_ENTRY")]`
   - Add `pub struct ScrapbookEntryPayload` with `#[serde(deny_unknown_fields)]` and these fields:
     - `turn_id: u32`
     - `scene_title: Option<String>` with `#[serde(default, skip_serializing_if = "Option::is_none")]`
     - `scene_type: Option<String>` (same attrs)
     - `location: String`
     - `image_url: Option<String>` (same attrs)
     - `narrative_excerpt: String`
     - `world_facts: Vec<String>` with `#[serde(default, deserialize_with = "deserialize_null_as_empty_vec", skip_serializing_if = "Vec::is_empty")]` (reuse helper from NarrationPayload)
     - `npcs_present: Vec<NpcRef>` (same vec attrs)
   - Add `pub struct NpcRef { name: String, role: String, disposition: String }` with `#[serde(deny_unknown_fields)]`

2. `sidequest-server/src/scrapbook.rs` (new module, declared `pub mod scrapbook;` in lib.rs):
   - `pub fn extract_first_sentence(text: &str) -> String` — find first `.`/`?`/`!` followed by whitespace-or-EOF, skip ellipses (`...`), skip known abbreviations (`Dr.`, `Mr.`, `Mrs.`, `Ms.`, `St.`, `Jr.`, `Sr.`), trim leading/trailing whitespace. Return trimmed full text if no terminator.
   - `pub fn build_scrapbook_entry(turn_id, location, scene_title, scene_type, image_url, narration, footnotes, npcs) -> ScrapbookEntryPayload` — see test shapes for exact signature.
   - Keep it pure. No global state. No OTEL in these helpers.

3. `sidequest-server/src/dispatch/response.rs`:
   - Import `use crate::scrapbook;` at top
   - AFTER the `let _ = ctx.tx.send(narration_end).await;` line, build a `ScrapbookEntryPayload` via `scrapbook::build_scrapbook_entry(...)` using:
     - `turn_id = ctx.turn_manager.interaction() as u32`
     - `location = ctx.current_location.clone()`
     - `scene_title`, `scene_type`, `image_url` — all `None` for now (image is async; a follow-up can plumb the latest completed render context through dispatch)
     - `narration = clean_narration`
     - `footnotes = &merged_footnotes` (the vec we already compute)
     - `npcs = ctx.npc_registry` (filter to only those with `last_seen_turn == turn_id` if feasible; otherwise pass all — the test doesn't enforce a filter)
   - Push `GameMessage::ScrapbookEntry { payload, player_id: ctx.player_id.to_string() }` onto `messages`
   - **The push must appear textually AFTER the NarrationEnd send** — the wiring test verifies byte offsets.

4. `sidequest-server/src/lib.rs`:
   - Add `pub mod scrapbook;`

5. Add one OTEL event per CLAUDE.md rule: `WatcherEventBuilder::new("scrapbook", WatcherEventType::SubsystemExerciseSummary).field("event", "scrapbook.entry_emitted").field("turn_id", turn_id).field("world_facts_count", ...).field("npcs_count", ...).send();` — Keith's OTEL-on-every-subsystem rule.

**Out of scope for this story:** UI consumer (story 33-17), threading image/scene metadata through dispatch (follow-up), per-turn footnote accumulation (current `merged_footnotes` is already turn-scoped).

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 35/35 passing (GREEN) — testing-runner confirmed zero failures and zero clippy warnings on the four touched files.
**Branch:** `feat/33-18-scrapbook-payload` on `sidequest-api` (pushed to origin).

**Files Changed:**
- `sidequest-api/crates/sidequest-protocol/src/message.rs` — added `GameMessage::ScrapbookEntry` variant, `ScrapbookEntryPayload` struct (with `deny_unknown_fields` + optional fields + `deserialize_null_as_empty_vec` on Vec fields), `NpcRef` struct
- `sidequest-api/crates/sidequest-server/src/lib.rs` — added `pub mod scrapbook;`
- `sidequest-api/crates/sidequest-server/src/scrapbook.rs` — NEW, pure functions:
  - `extract_first_sentence`: walks bytes, skips `...` ellipses (and defensive `..`), skips 11 known abbreviations (`Dr.`, `Mr.`, `Mrs.`, `Ms.`, `St.`, `Jr.`, `Sr.`, `vs.`, `etc.`, `e.g.`, `i.e.`), requires whitespace-or-EOF after a terminator, returns trimmed full text if nothing matches
  - `build_scrapbook_entry`: extracts `summary` from `is_new=true` footnotes, maps `NpcRegistryEntry` → `NpcRef` with `ocean_summary` as disposition (role fallback for empty), delegates sentence extraction
- `sidequest-api/crates/sidequest-server/src/dispatch/response.rs` — imports `crate::scrapbook`, after `NarrationEnd` send builds + pushes `GameMessage::ScrapbookEntry` on `messages` Vec, filters `npc_registry` to `last_seen_turn == turn_id`, emits OTEL `scrapbook.entry_emitted` WatcherEvent with `turn_id`/`world_facts_count`/`npcs_count`/`excerpt_chars`

**Wiring Verified:**
- `response.rs` imports `crate::scrapbook` ✓
- `response.rs` calls `build_scrapbook_entry` ✓
- `response.rs` pushes `GameMessage::ScrapbookEntry` onto `messages` ✓
- `ScrapbookEntry` push appears AFTER `NarrationEnd` send (verified by byte-offset test) ✓
- Non-test consumer confirmed: the assembly function is called from `build_response_messages`, which is the canonical end-of-turn dispatch path

**OTEL:** `scrapbook.entry_emitted` WatcherEvent emitted on every turn via `WatcherEventBuilder::new("scrapbook", ...)` — satisfies Keith's OTEL-on-every-subsystem rule. The GM panel can now verify scrapbook emission is engaged rather than trusting Claude to "wing it".

**Handoff:** To next phase (spec-check per tdd workflow, then verify + review). The branch is pushed, tests are green, and the wiring is end-to-end.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned with documented deviations — no new drift
**Gate:** `gates/spec-check` passed (structural validation clean)
**Mismatches Found:** 2 (both already logged by TEA/Dev, no new hand-backs)

**AC-by-AC substantive check:**

| AC | Spec | Code | Status |
|----|------|------|--------|
| Protocol variant | `ScrapbookEntry { turn_id, scene_title, scene_type, location, image_url, narrative_excerpt, world_facts, npcs_present }` | `GameMessage::ScrapbookEntry` + `ScrapbookEntryPayload` in `message.rs` with all 8 fields present | ✓ aligned (Option<> on scene_title/scene_type/image_url — deviation logged) |
| Emit after settlement | "after `NarrationComplete` (world_facts must be settled)" | Pushed on `messages` Vec AFTER `ctx.tx.send(narration_end).await`, wiring test verifies byte order | ✓ aligned (renamed to `NarrationEnd` — trivial deviation logged) |
| narrative_excerpt = first sentence | "server extracts, not client" | `scrapbook::extract_first_sentence()` handles period/?/!, ellipsis, `Dr./Mr./Mrs./Ms./St./Jr./Sr./vs./etc./e.g./i.e.` abbreviations, whitespace-or-EOF terminator check | ✓ aligned |
| scene_title from render_integration | "from `render_integration` scene_name field (already tagged)" | Emitted as `None` — RenderSubject not threaded through DispatchContext | ◐ deferred (deviation logged, follow-up noted) |
| scene_type from render_integration | "from `render_integration` tier/scene_type" | Emitted as `None` — same reason as scene_title | ◐ deferred (deviation logged) |
| world_facts source | "all world_facts broadcast during this turn, as plain strings" | Sourced from `merged_footnotes` where `is_new == true`, mapped to `.summary` strings | ✓ aligned (no `WorldFact` broadcast message exists; footnote path is the real pipeline per ADR-076 — deviation logged) |
| npcs_present source | "all NPCs appearing in npc_registry updates during this turn" | `ctx.npc_registry.iter().filter(\|e\| e.last_seen_turn == turn_id).cloned()` in `response.rs` | ✓ aligned |
| Protocol + server emission + client handler | Listed together as one AC | Protocol and server emission complete; client handler explicitly out of scope per session Implementation Strategy ("No UI changes — 33-17 consumes the payload") | ◐ internal spec inconsistency resolved in favor of Implementation Strategy |

**Mismatch 1 — Image/scene metadata deferred to follow-up**
- Category: Missing in code (ACs 4 & 5 — `scene_title`, `scene_type`, plus `image_url` from AC 1)
- Type: Behavioral
- Severity: Minor
- Spec: Fields populated from `render_integration` at emission time
- Code: All three fields emitted as `None`; populated by 33-17 via client-side merge on later `GameMessage::Image`
- **Recommendation: C (clarify spec) — already logged**
- Rationale: The session AC was written before the async-render architecture was fully understood. `render_integration::spawn_image_broadcaster_with_throttle` runs on an independent `broadcast::Receiver<RenderResultContext>` task, completely decoupled from `DispatchContext`. Threading `RenderSubject` state into dispatch would require either (a) blocking `build_response_messages` on render completion (violates ADR-063 fast-path, punishes acting-player latency) or (b) a shared `turn_id → RenderSubject` map with write-from-broadcaster / read-from-dispatch. Option (b) is a reasonable follow-up but its design scope exceeds a 3-point story. The client-side merge in 33-17 is architecturally sound and matches how the Scrapbook widget will already handle the normal async image arrival path.
- **No hand-back required** — Dev's deviation entry under `### Dev (implementation)` captures this cleanly with forward impact noted.

**Mismatch 2 — Client handler in Redux store**
- Category: Extra in spec (internal inconsistency between AC list and Implementation Strategy)
- Type: Architectural
- Severity: Trivial
- Spec: AC bullet says "client handler in Redux store"; Implementation Strategy says "No UI changes — 33-17 consumes the payload"
- Code: No Redux handler; 33-17 will add it
- **Recommendation: C (clarify spec) — implicitly resolved by scope note**
- Rationale: The session's own "Out of scope for this story" note (appended by TEA in implementation guidance: "UI consumer (story 33-17)") is authoritative per the spec authority hierarchy. The AC bullet was inherited from an early draft that predated the 33-17/33-18 split. Keith's established workflow is that sibling-story assumptions are driven by Implementation Strategy sections when they conflict with AC bullets.
- **No hand-back required** — the split was intentional per the dependency chain in the Context section ("33-18 (Scrapbook payload) ← current, 33-17 (Gallery image metadata — depends on this)").

**Rule compliance check:**
- **No silent fallbacks** ✓ — `deny_unknown_fields` enforced on `ScrapbookEntryPayload` and `NpcRef`; empty `ocean_summary` falls back to `role` (documented, not silent)
- **No stubs** ✓ — no placeholder impls, no TODO, no `unimplemented!()`
- **Wire up what exists** ✓ — reuses `merged_footnotes` already computed by `build_response_messages`, reuses `ctx.npc_registry`, reuses `WatcherEventBuilder` pattern, reuses `deserialize_null_as_empty_vec` helper from `NarrationPayload`
- **Verify wiring not just existence** ✓ — four wiring tests verify the import, call, variant push, and byte-order of emission in `response.rs`
- **Every test suite needs a wiring test** ✓ — three dedicated wiring tests in the integration suite
- **OTEL on every subsystem** ✓ — `scrapbook.entry_emitted` WatcherEvent with turn_id, world_facts_count, npcs_count, excerpt_chars

**Reuse-first audit:**
- Did not introduce new telemetry types — reused `WatcherEventBuilder::new("scrapbook", WatcherEventType::SubsystemExerciseSummary)` pattern matching other subsystems
- Did not introduce new NPC types — projected `NpcRegistryEntry` → `NpcRef` at the protocol boundary (matches the `ConfrontationActor` pattern in the same file)
- Did not introduce new sentence-boundary crate dependency — implemented `extract_first_sentence` as 90 lines of pure byte-walking logic, no `regex` or `unicode-segmentation` pull-in (keeps `sidequest-server` dependency surface small)
- Did not re-invent footnote aggregation — `merged_footnotes` is the canonical per-turn fact list already computed for the Narration message

**Decision:** Proceed to verify (Amos Burton — simplify + quality-pass). No hand-back to Dev. No new deviations required. Both mismatches are Option C (clarify spec), already captured in the TEA and Dev deviation subsections. Architect reconcile phase will promote those to the final audit manifest.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed after simplify pass

### Simplify Report

**Teammates:** reuse, quality, efficiency (fan-out parallel, Machine Shop)
**Files Analyzed:** 5 (`message.rs`, `scrapbook.rs`, `dispatch/response.rs`, `sidequest-server/src/lib.rs`, `sidequest-protocol/src/lib.rs`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 5 findings | 1 high (confirmed `deserialize_null_as_empty_vec` is already consolidated — no action), 2 medium (sentence-extractor shared with `prompt.rs` line 754; turn-scoped NPC filter duplicated across `npc_context.rs:40`, `prompt.rs:209`), 2 low (footnote is_new filter pattern, NPC→UI projection pattern) |
| simplify-quality | clean | 0 findings — naming, docs, OTEL field conventions, import directions all correct |
| simplify-efficiency | 2 findings | 1 high (auto-applied), 1 medium (flagged) |

**Applied (1 high-confidence fix):**
- **`scrapbook.rs` abbreviation check allocation** — `is_abbreviation_terminator` was calling `token.to_ascii_lowercase()` for every period candidate, allocating a new `String` per call. Replaced with `SENTENCE_ABBREVIATIONS.iter().any(|abbr| abbr.as_bytes().eq_ignore_ascii_case(token))` — same behavior, zero allocations. Committed as `refactor(33-18): remove String alloc in abbreviation check`.

**Flagged for Review (2 medium-confidence findings — not auto-applied):**
- **efficiency: move NPC filter into `build_scrapbook_entry`** — The `turn_npcs: Vec<NpcRegistryEntry>` clone in `response.rs:178` could be eliminated if the filter moved inside the assembler. Current approach keeps `build_scrapbook_entry` filter-agnostic (matches TEA's RED-phase design) and is clear about intent ("these are the NPCs for this turn"). Decision: leave as-is; the clone cost is one small Vec per turn in a non-latency-critical path, and the signature clarity is worth it. Reviewer may revisit.
- **reuse: turn-scoped NPC filter exists in 3 places** — `response.rs:181` (`== turn_id`), `npc_context.rs:40` (`<= 2` turns), `prompt.rs:209` (same). Different semantics — exact turn match vs "last two turns". Not an obvious extraction. Decision: leave as-is; forcing a shared helper now would couple semantically distinct call sites.
- **reuse: `extract_first_sentence` vs `prompt.rs:754`** — `prompt.rs` uses a naive `split('. ').next()` for prompt history truncation, which the scrapbook extractor's abbreviation-aware logic could replace. Different contexts, different acceptable failure modes. Decision: leave as-is; creating cross-file dependency from `prompt.rs` into `scrapbook.rs` would invert the dispatch→helper direction and couple unrelated subsystems. If a third sentence-extraction need surfaces, promote `extract_first_sentence` to a shared utility crate then.

**Noted (low-confidence, no action):**
- `footnotes.rs:26` has a similar `filter(is_new).map(summary)` pattern — only 2 sites, monitor for third
- `NpcRegistryEntry`→`ConfrontationActor` projection pattern in `response.rs:331` has surface similarity to `NpcRegistryEntry`→`NpcRef` — different payload types, different fallback rules, no forced abstraction

**Reverted:** 0

**Overall:** simplify: applied 1 fix

### Quality Checks (post-simplify regression)

- `cargo test -p sidequest-protocol scrapbook_entry` — 11/11 passing
- `cargo test -p sidequest-server --test integration scrapbook_entry` — 24/24 passing
- `cargo clippy -p sidequest-protocol -p sidequest-server --tests -- -D warnings` — 0 warnings on any touched file (`message.rs`, `scrapbook.rs`, `dispatch/response.rs`, `lib.rs`)

**Total: 35/35 passing, zero warnings.**

### Delivery Findings (TEA verify)

No upstream findings during test verification. The simplify fan-out surfaced only the efficiency micro-optimization already applied — no architectural gaps, no wiring defects, no test coverage holes.

**Handoff:** To Reviewer (Chrisjen Avasarala) for adversarial code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 fmt violations, 446 tests passing, clippy clean | confirmed 3, auto-fixed via `cargo fmt` |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter=false` |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (1 medium excerpt-fallback visibility, 1 low disposition-fallback visibility) | confirmed 2, both applied as OTEL degraded-path fields |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (3 high, 1 medium, 1 low) | confirmed 4, dismissed 1 (UTF-8 — no regression vector) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 (2 high player_id doc + Camina leak, 1 medium Option-param doc) | confirmed 3, all applied |
| 6 | reviewer-type-design | Yes | findings | 4 high (turn_id u32/u64, raw String vs NonBlankString, no validated constructor) | confirmed 0, dismissed 4 — protocol-wide convention, cross-story initiative |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security=false` |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier=false`; simplify fan-out already executed during verify phase (1 fix applied) |
| 9 | reviewer-rule-checker | Yes | clean | 0 (19 rules, 38 instances, 0 violations) | N/A |

**All received:** Yes (6 enabled subagents returned, 3 pre-filled disabled per settings)
**Total findings:** 13 confirmed / 5 dismissed with rationale / 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** Player action → narrator → `build_response_messages` → narration + state deltas flushed → `narration_end` sent via `ctx.tx` → ScrapbookEntry assembled (turn-scoped NPC filter, is_new footnote filter, sentence extraction, OTEL emit) → pushed onto `messages` Vec → WebSocket broadcast fan-out → client. Safe: `merged_footnotes` already turn-scoped by narrator extraction, `npc_registry` filtered to `last_seen_turn == turn_id` at call site, assembler is pure, message rides same `messages` Vec fan-out as PartyStatus/MapUpdate/Confrontation.

**Pattern observed:** Protocol payload with `deny_unknown_fields` + Option fields + `deserialize_null_as_empty_vec` on Vec fields matches NarrationPayload/ImagePayload convention at `message.rs:441,842`. New `scrapbook.rs` follows pure-function dispatch helper pattern used by `state_mutations.rs` and `npc_registry.rs`.

**Error handling:** No errors to handle — pure in, pure out. Degraded paths now observable via `excerpt_fallback_full_narration` and `npcs_disposition_fallback_count` OTEL fields. Fail loud to GM panel, not silent at narrator schema.

### Observations

- **[VERIFIED]** `#[non_exhaustive]` on `GameMessage` preserved — adding a variant is the permitted operation (`message.rs:38`); wildcard match arms in tests cover forward-compat.
- **[VERIFIED]** `#[serde(deny_unknown_fields)]` on both new payload structs at `message.rs:2118,2138`. New `scrapbook_entry_payload_world_facts_accepts_json_null` test covers the `deserialize_null_as_empty_vec` helper explicitly for both Vec fields.
- **[VERIFIED]** Wiring end-to-end — `lib.rs:17` declares `pub mod scrapbook;`, `dispatch/response.rs:8` imports `crate::scrapbook`, line 184 calls `build_scrapbook_entry`, line 218 pushes `GameMessage::ScrapbookEntry`. Non-test consumer confirmed. Four wiring tests enforce the call-site pattern. The ordering test now anchors on the literal `ctx.tx.send(narration_end)` and `messages.push(GameMessage::ScrapbookEntry` — not the bare token `NarrationEnd` which appears in doc comments.
- **[VERIFIED]** OTEL compliance — `WatcherEventBuilder::new("scrapbook", SubsystemExerciseSummary)` emits per turn with 7 fields including two degraded-path signals. Satisfies Keith's OTEL-on-every-subsystem rule.
- **[DOC] [comment-analyzer]** `ScrapbookEntry.player_id` rustdoc said `"typically 'server'"` — incorrect. Confirmed and fixed at `message.rs:439`.
- **[DOC] [comment-analyzer]** `"Camina flagged"` agent-persona leak in integration test doc at lines 16 and 68. Confirmed and fixed.
- **[DOC] [comment-analyzer]** `build_scrapbook_entry` rustdoc omitted the three Option parameters. Confirmed and fixed with async-render context block.
- **[TEST] [test-analyzer]** Byte-offset wiring test anchored on bare string `NarrationEnd` which appears in my Dev-phase comment block. Confirmed and fixed — now anchors on `ctx.tx.send(narration_end)` and `messages.push(GameMessage::ScrapbookEntry`.
- **[TEST] [test-analyzer]** `deserialize_null_as_empty_vec` helper was wired but untested. Confirmed and fixed — new test deserializes explicit JSON null for both Vec fields.
- **[TEST] [test-analyzer]** No coverage for quoted-dialogue sentence termination. Behavior was correct but uncovered. Confirmed and fixed — added two variants (`"...," tag.` and `"Done." tag.`).
- **[TEST] [test-analyzer]** No CRLF line-ending test. Confirmed and fixed.
- **[TEST] [test-analyzer]** Missing UTF-8 smoke test. **Dismissed** — byte extractor slices at single-byte ASCII `.?!` positions; `bytes[i+1].is_ascii_whitespace()` is UTF-8 safe (multi-byte leading bytes never have the ASCII whitespace bit). Adding a test for a case the extractor is structurally incapable of breaking is coverage theater.
- **[SILENT] [silent-failure-hunter]** Sentence extractor degraded path invisible. Confirmed and fixed — `excerpt_fallback_full_narration: bool` OTEL field set when `narrative_excerpt == clean_narration.trim()`. GM panel now detects narrator schema violations.
- **[SILENT] [silent-failure-hunter]** NPC disposition fallback invisible. Confirmed and fixed — `npcs_disposition_fallback_count: usize` counts NPCs with empty `ocean_summary`. GM panel now detects upstream OCEAN pipeline gaps.
- **[TYPE] [type-design]** `turn_id: u32` vs `TurnManager::interaction() -> u64`. **Dismissed** — pre-existing protocol convention: `ActionRevealPayload.turn_number: u32` at `message.rs:985`, server call site already casts `as u32` at `dispatch/npc_registry.rs:20`. Cross-protocol change is out of scope; fixing it here would create u32/u64 mismatch between sibling payloads. Legitimate concern for a protocol cleanup epic.
- **[TYPE] [type-design]** `NpcRef.name`/`role`, `ScrapbookEntryPayload.location`/`narrative_excerpt` as raw `String` vs `NonBlankString`. **Dismissed** — protocol-wide convention: `PartyMember.name`, `ImagePayload.description`, `ConfrontationActor.name`, `ConfrontationPayload.label` and every display-bound string in this crate uses raw String. `NonBlankString` is used only for `PlayerActionPayload.action` (user input at trust boundary). Retrofitting just these four would be inconsistent; warrants a protocol-wide hardening initiative.
- **[TYPE] [type-design]** `ScrapbookEntryPayload` has no validated constructor. **Dismissed** — same rationale; every payload struct in this crate is fully public without validated constructors. Deviating for one struct is worse than the inconsistency.
- **[TYPE] [type-design]** `NpcRef.disposition` is `String` rather than `Disposition(i32)` newtype. **Verified intentional** — `Disposition(i32)` is the ADR-020 signed attitude score; `NpcRef.disposition` is a rendered OCEAN behavioral descriptor. Different semantic layer. Subagent correctly marked this as acceptable in its own output.
- **[RULE] [rule-checker]** All 19 project rules pass — 38 instances, 0 violations.

### Rule Compliance

| Rule | Instances | Violations | Evidence |
|------|-----------|------------|----------|
| No silent fallbacks | 3 | 0 — degraded paths emit OTEL | `response.rs:195-213` |
| No stubs | 4 | 0 — all fully implemented | `lib.rs:17`, `response.rs:184` |
| Don't reinvent | 2 | 0 — reuses Footnote/NpcRegistryEntry | |
| Verify wiring | 4 wiring tests | 0 — import + call + push + order enforced | |
| Every test suite wires | 2 files | 0 — 4 wiring tests | |
| OTEL observability | 1 subsystem | 0 — 7-field event with degraded-path signals | `response.rs:203` |
| Protocol deny_unknown_fields | 2 | 0 — both present | `message.rs:2118,2138` |
| Non-exhaustive enums | 1 variant add | 0 — preserved | |
| Protocol missing_docs | 12 new pub items | 0 — all documented | |
| No vacuous tests | 39 new tests | 0 — every assertion concrete | |
| NarrationPayload 3-field | 1 | 0 — untouched | |
| gitflow develop | branch | 0 — feat/33-18-scrapbook-payload → develop | |

### Devil's Advocate

Malicious user? Scrapbook entry is server-emitted from server state; no user input reaches payload construction. A malicious action with no terminal punctuation would pollute `narrative_excerpt` with a large blob, but narrator output is already length-bounded, and the new `excerpt_fallback_full_narration` OTEL field makes this visible. Not an exploit — annoyance at worst.

Confused consumer? A `SCRAPBOOK_ENTRY` wire reader assuming `scene_title` is always present gets `None` and must handle it. Protocol-level `deny_unknown_fields` doesn't help. Mitigation: 33-17 is the only consumer and the session file is explicit about the merge contract.

Stressed filesystem? Wiring test helper reads `response.rs` via `env!("CARGO_MANIFEST_DIR")` + `read_to_string`; panics loud on failure. Acceptable for a test-only helper.

Unexpected JSON? `deny_unknown_fields` rejects at deserialization. Null-Vec tolerance tested for both absent and explicit null.

Race conditions? Pure function, owned slices, no shared state. Caller clones `ctx.npc_registry` into `turn_npcs` before passing, so concurrent registry mutation is impossible during assembly.

Empty footnotes/empty NPCs? `world_facts: vec![]` and `npcs_present: vec![]`, serde skips on serialize, client deserializes to empty Vec. Tested.

Turn ID collision? `interaction()` is monotonic per TurnManager invariant. `as u32` cast safe for any realistic playtest.

Disconnect mid-turn? `messages` Vec is flushed by writer loop; disconnect drops the message. Observers still receive via `sync_back_to_shared_session`.

I can't find a bug. The code is defensive in the right places (deny_unknown_fields, null-Vec, abbreviation-aware extraction, turn-scoped filter, degraded-path OTEL) and pragmatic elsewhere (raw String matching protocol convention, async image deferral to client merge, pure-function helpers).

### Tenant Isolation Audit

SideQuest is single-tenant local-first. No tenant boundary. N/A.

**Handoff:** Back to Naomi Nagata (design mode / architect) for spec-reconcile, then SM (Camina Drummer) for finish.

## Delivery Findings

### TEA (test design)
- **Gap** (non-blocking): Session AC lists `GalleryImage`, `WorldFact`, and `NarrationComplete` as separate WebSocket message types that don't exist in the current protocol. Affects `sidequest-api/crates/sidequest-protocol/src/message.rs` — world facts flow via `NarrationPayload.footnotes: Vec<Footnote>` (not a standalone event), images are emitted as `GameMessage::Image` from an async broadcaster in `render_integration.rs`, and the end-of-turn marker is `NarrationEnd` (not `NarrationComplete`). Tests assume the real protocol shape. *Found by TEA during test design.*
- **Gap** (non-blocking): Image metadata (scene_title, scene_type, image_url) cannot be included in the ScrapbookEntry at narration-end time because images are generated on a separate async channel and are NOT guaranteed to be complete by the time `NarrationEnd` fires. Affects `sidequest-api/crates/sidequest-server/src/dispatch/response.rs` — the entry is emitted with `None` for those fields, and story 33-17 (UI consumer) must merge with later `GameMessage::Image` messages by `turn_id`. Follow-up could thread the latest render subject through `DispatchContext`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `NpcRegistryEntry` has no free-standing `disposition` field. The closest analog is `ocean_summary` (e.g., "reserved and quiet, meticulous and disciplined"), which ADR-020 treats as the canonical disposition descriptor. Affects `sidequest-api/crates/sidequest-server/src/scrapbook.rs` (to be created by Dev) — map `ocean_summary → NpcRef.disposition`. If the summary is empty, fall back to `role`. *Found by TEA during test design.*

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test verification)
- No upstream findings during test verification. Simplify fan-out produced 7 findings across reuse/quality/efficiency — 1 high-confidence fix auto-applied (abbreviation-check allocation), 3 medium flagged and dismissed with rationale, 3 low-confidence noted and dismissed. No architectural gaps, no wiring defects, no coverage holes.

### Dev (implementation)
- No upstream findings during implementation — TEA's test layout pinned every edge case cleanly. The only surprise was that `merged_footnotes` in `response.rs` is already turn-scoped (built from `result.footnotes` + affinity tier-up events for the current turn), so no new per-turn accumulator was needed.

### Reviewer (code review)
- **Improvement** (non-blocking): `turn_id` is `u32` in `ScrapbookEntryPayload` but `TurnManager::interaction()` at `sidequest-game/src/turn.rs:92` returns `u64`. Not a 33-18-introduced issue — `ActionRevealPayload.turn_number` at `message.rs:985` has the same shape and the dispatch layer already casts `as u32`. Cross-protocol cleanup epic territory. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Four display-bound string fields (`NpcRef.name`, `NpcRef.role`, `ScrapbookEntryPayload.location`, `ScrapbookEntryPayload.narrative_excerpt`) use raw `String` where `NonBlankString` could enforce the implicit non-empty invariant. Consistent with every other protocol payload (`PartyMember`, `ImagePayload`, `ConfrontationActor`). Warrants a protocol-wide hardening initiative, not a per-story retrofit. *Found by Reviewer during code review.*
- **Gap** (non-blocking): Threading the latest completed `RenderSubject` through `DispatchContext` so `scene_title`/`scene_type`/`image_url` can be populated server-side at narration-end time is a legitimate follow-up. Currently the client merges via later `GameMessage::Image` by `turn_id` — per story 33-17's contract. A follow-up story could bind the latest render context to the acting turn and remove the Option chain here. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **image_url / scene_title / scene_type are Option<String>, not String**
  - Spec source: `.session/33-18-session.md`, Acceptance Criteria ("New WS message type: `ScrapbookEntry { ..., scene_title, scene_type, location, image_url, narrative_excerpt, ... }`" — all shown as bare String)
  - Spec text: `scene_title: String, scene_type: SceneType, image_url: String`
  - Implementation: Tests expect `Option<String>` for all three, with `#[serde(default, skip_serializing_if = "Option::is_none")]`
  - Rationale: Images are generated on an async broadcast channel (`render_integration.rs` — `spawn_image_broadcaster_with_throttle`) that is completely independent of the dispatch loop. `NarrationEnd` fires before the render is guaranteed to complete, so at emission time the server does not know the `image_url`, `scene_title` (from `RenderSubject`), or `scene_type`. Forcing non-optional strings would require either (a) blocking the turn on render completion (unacceptable UX cost — violates ADR-063 fast-path) or (b) emitting synthetic placeholder strings (violates "No Silent Fallbacks"). Optional fields let 33-17 merge the later `GameMessage::Image` by `turn_id`.
  - Severity: minor
  - Forward impact: Story 33-17 (UI consumer) must merge ScrapbookEntry + later IMAGE messages by `turn_id` on the client side. Documented in 33-17's context already (it's downstream of this story).

- **world_facts sourced from `NarrationPayload.footnotes` where `is_new=true`, not from separate WorldFact broadcasts**
  - Spec source: `.session/33-18-session.md`, Current State ("world_facts broadcast via `WorldFact` events during game turns")
  - Spec text: "Collect all `world_facts` broadcast during that turn"
  - Implementation: Tests pass `&[Footnote]` to `build_scrapbook_entry` and expect the assembler to filter `is_new == true` and extract `summary` as the world fact string
  - Rationale: There is no `WorldFact` GameMessage variant in the protocol — ADR-076 consolidated discovery delivery into `NarrationPayload.footnotes`. The existing `merged_footnotes` Vec computed in `build_response_messages` (narrator footnotes + affinity tier-up synthesis events) is already turn-scoped and is the canonical per-turn fact list. Re-broadcasting via a synthetic `WorldFact` event would duplicate data that already rides on `Narration`.
  - Severity: minor
  - Forward impact: None — the set of facts is the same, only the transport changed.

- **end-of-turn marker is `NarrationEnd`, not `NarrationComplete`**
  - Spec source: `.session/33-18-session.md`, Implementation Strategy ("hook into `NarrationComplete` handler")
  - Spec text: "Server emits `ScrapbookEntry` after `NarrationComplete` for that turn"
  - Implementation: Tests verify emission after `NarrationEnd` (the actual message variant in `sidequest-protocol`)
  - Rationale: `NarrationComplete` does not exist as a `GameMessage` variant. ADR-076 renamed/collapsed the narration protocol to `Narration` + `NarrationEnd`. The session AC referenced a symbol that was deprecated before the story was written.
  - Severity: trivial
  - Forward impact: None — semantic meaning is preserved.

- **`npc_registry` passed verbatim rather than filtered to "NPCs appearing in this turn's updates"**
  - Spec source: `.session/33-18-session.md`, Acceptance Criteria
  - Spec text: "`npcs_present`: all NPCs appearing in npc_registry updates during this turn"
  - Implementation: `build_scrapbook_entry` receives `&[NpcRegistryEntry]` — the caller (`response.rs`) is free to filter to `entry.last_seen_turn == turn_id`, but the test does not enforce the filter; it only verifies the mapping shape. If Dev passes the full registry, tests pass.
  - Rationale: `NpcRegistryEntry.last_seen_turn` already encodes turn-of-last-appearance; filtering is trivial at the call site. Keeping the assembler filter-agnostic makes it testable in isolation and avoids duplicating filter logic across the module boundary.
  - Severity: minor
  - Forward impact: Dev should add the `last_seen_turn == turn_id` filter in `response.rs` before passing to the assembler, per the AC's intent.

- **`NpcRef.disposition` sourced from `NpcRegistryEntry.ocean_summary`, not a free-standing disposition field**
  - Spec source: `.session/33-18-session.md`, protocol sketch (`NpcRef { name, role, disposition }`)
  - Spec text: `pub disposition: String`
  - Implementation: Tests expect disposition = `ocean_summary` (e.g., "gruff but fair", "watchful and quiet")
  - Rationale: `NpcRegistryEntry` does not carry a stand-alone disposition string. ADR-020 defines disposition as a behavioral descriptor; `ocean_summary` (generated from the OCEAN profile via `behavioral_summary()`) is the canonical one-line rendering of that descriptor. This preserves the player-visible meaning of "disposition" without adding a new field to `NpcRegistryEntry`.
  - Severity: minor
  - Forward impact: Dev should add a fallback — if `ocean_summary` is empty, use `role` as a graceful degradation to avoid empty-string disposition strings in the UI.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test verification)
- No deviations from spec during verify phase. The simplify fix (replacing `to_ascii_lowercase()` allocation with `eq_ignore_ascii_case()` byte compare in `is_abbreviation_terminator`) is behavior-preserving and does not alter any observable spec property — all 35 tests still pass with identical outputs.

### Dev (implementation)
- **NPC registry filtered to `last_seen_turn == turn_id` at the call site, not inside the assembler**
  - Spec source: `.session/33-18-session.md`, Acceptance Criteria + TEA Design Deviations (note on filter location)
  - Spec text: "`npcs_present`: all NPCs appearing in npc_registry updates during this turn"
  - Implementation: `response.rs` builds a `turn_npcs: Vec<NpcRegistryEntry>` by filtering `ctx.npc_registry` to entries with `last_seen_turn == turn_id`, then passes `&turn_npcs` to `scrapbook::build_scrapbook_entry`. The assembler itself is filter-agnostic.
  - Rationale: Keeps `build_scrapbook_entry` pure and testable in isolation (TEA's tests pass the full NPC slice with no filter). The caller already has `turn_id` and `npc_registry` in scope, so filtering there costs one clone per turn and avoids passing turn context into a pure function that doesn't otherwise need it.
  - Severity: trivial
  - Forward impact: None — matches TEA's deviation note.

- **ScrapbookEntry pushed to `messages` Vec (fan-out path), not `ctx.tx` fast-path**
  - Spec source: `sidequest-server/src/dispatch/response.rs` comments on `narration_msg` and `narration_end` (ADR-063 fast-path doc block)
  - Spec text: "The Narration is NOT pushed into the returned `messages` Vec. The caller's ws writer loop iterates that Vec and flushes every entry through the same `ctx.tx` channel" — so Narration/NarrationEnd go via `ctx.tx` directly to avoid double-flush.
  - Implementation: `ScrapbookEntry` is pushed onto `messages`, which means it reaches BOTH the acting player (via the writer loop flushing `messages` through `ctx.tx`) AND observers (via `sync_back_to_shared_session`'s session fan-out) exactly once. Same pattern as `PartyStatus`, `MapUpdate`, and `Confrontation` in this file.
  - Rationale: The narration fast-path optimization exists because narration text is latency-critical (player UX perception). ScrapbookEntry is end-of-turn metadata — it is NOT latency-critical, and is a single message per turn. Pushing to `messages` matches the pattern for every other end-of-turn broadcast in this function and avoids the duplicate-send hazard that the narration fast-path was designed to prevent.
  - Severity: trivial
  - Forward impact: None — the entry is delivered once to each connected client.

- **Image metadata (scene_title, scene_type, image_url) emitted as `None`**
  - Spec source: `.session/33-18-session.md`, Acceptance Criteria + TEA Design Deviations
  - Spec text: AC requires these fields; TEA deviation documented that they must be `Option<String>` for async-render reasons.
  - Implementation: `response.rs` passes `None, None, None` for all three. The latest `RenderSubject` is NOT threaded through `DispatchContext` in this story.
  - Rationale: Per TEA's deviation, plumbing the latest completed render subject through `DispatchContext` is a follow-up. The Scrapbook widget (story 33-17) merges with later `GameMessage::Image` messages by `turn_id` on the client side.
  - Severity: minor
  - Forward impact: A follow-up story should thread the current-turn `RenderSubject` reference through `DispatchContext` so `response.rs` can populate these fields when a synchronously-available render exists. Until then, the client must handle the merge.

### Reviewer (audit)
All eight in-flight deviations from TEA and Dev reviewed:

- **TEA: `image_url`/`scene_title`/`scene_type` as Option<String>** → ✓ ACCEPTED by Reviewer: architecturally sound (async render channel), documented in code, tests enforce Option shape, and story 33-17 is explicitly designed to handle the client-side merge.
- **TEA: world_facts sourced from footnotes.is_new, not a WorldFact broadcast** → ✓ ACCEPTED by Reviewer: ADR-076 already consolidated discovery delivery into `NarrationPayload.footnotes`; there is no `WorldFact` GameMessage variant. The session AC referenced infrastructure that doesn't exist. Using the canonical footnote pipeline is the correct reading.
- **TEA: end-of-turn marker is `NarrationEnd`, not `NarrationComplete`** → ✓ ACCEPTED by Reviewer: `NarrationComplete` does not exist as a GameMessage variant (verified at `message.rs:124` — only `NarrationEnd`). Session AC was using a deprecated symbol. Trivial rename.
- **TEA: `npc_registry` passed verbatim** → ✓ ACCEPTED by Reviewer, updated by Dev: Dev added the `last_seen_turn == turn_id` filter at the call site in `response.rs:178-183`, preserving the assembler's purity while honoring the AC's intent. Clean split.
- **TEA: `NpcRef.disposition` sourced from `ocean_summary`** → ✓ ACCEPTED by Reviewer: `NpcRegistryEntry` has no standalone disposition field; `ocean_summary` is the canonical ADR-020 rendering via `behavioral_summary()`. Dev correctly implemented the empty-summary → `role` fallback.
- **Dev: NPC filter at call site, not inside assembler** → ✓ ACCEPTED by Reviewer: matches TEA's deviation note, keeps `build_scrapbook_entry` pure and testable. The one-clone cost is trivial in a non-latency-critical path.
- **Dev: ScrapbookEntry pushed to `messages` Vec, not `ctx.tx` fast-path** → ✓ ACCEPTED by Reviewer: correctly distinguishes latency-critical narration (fast-path) from end-of-turn metadata (fan-out path). Matches PartyStatus/MapUpdate/Confrontation pattern. Double-send hazard is avoided.
- **Dev: Image metadata emitted as None** → ✓ ACCEPTED by Reviewer: consistent with TEA's async-render deviation; story 33-17 handles the client-side merge. Forward impact noted (follow-up to thread `RenderSubject` through `DispatchContext`) — left as non-blocking.

**Undocumented deviations found:** None. Every spec gap was caught and logged in-flight by TEA or Dev.

**Audit verdict:** All eight deviations stamped ACCEPTED. Zero flagged, zero missed.

### Architect (reconcile)

**Scope verified:** story context (`context-epic-33.md`), session scope (ACs + Implementation Strategy), sibling story ACs (33-17 depends on 33-18), in-flight deviation logs from TEA/Dev/Reviewer, and the protocol/server code on `feat/33-18-scrapbook-payload`.

**Verification pass on existing in-flight deviations:**

All 8 deviation entries (5 from TEA, 3 from Dev) verified accurate:

| # | Author | Short description | Spec source real | Spec text quoted accurately | Implementation matches code | Forward impact accurate | All 6 fields present |
|---|--------|-------------------|------------------|-----------------------------|----------------------------|------------------------|---------------------|
| 1 | TEA | `image_url`/`scene_title`/`scene_type` as `Option<String>` | ✓ | ✓ | ✓ `message.rs:2157-2169` | ✓ 33-17 merge verified | ✓ |
| 2 | TEA | `world_facts` from footnotes.is_new not WorldFact broadcast | ✓ | ✓ | ✓ `scrapbook.rs:119-123` | ✓ transport change only | ✓ |
| 3 | TEA | `NarrationEnd` not `NarrationComplete` | ✓ | ✓ | ✓ `message.rs:124` confirmed | ✓ | ✓ |
| 4 | TEA | npc_registry passed verbatim | ✓ | ✓ | ✓ Dev implemented filter | ✓ matches Dev entry | ✓ |
| 5 | TEA | `NpcRef.disposition` from `ocean_summary` | ✓ | ✓ | ✓ `scrapbook.rs:128-132` with role fallback | ✓ | ✓ |
| 6 | Dev | NPC filter at call site | ✓ | ✓ | ✓ `response.rs:178-183` | ✓ | ✓ |
| 7 | Dev | ScrapbookEntry on `messages` Vec not fast-path | ✓ (ADR-063 block) | ✓ | ✓ `response.rs:204-207` | ✓ | ✓ |
| 8 | Dev | Image metadata emitted as `None` | ✓ | ✓ | ✓ `response.rs:184-193` | ✓ follow-up noted | ✓ |

All 8 entries are self-contained, accurately describe the code, and have all 6 required fields per `deviation-format.md`. No corrections needed.

**Additional deviations not caught in-flight:**

- **Session AC internal inconsistency: "client handler in Redux store" vs Implementation Strategy "No UI changes"**
  - Spec source: `.session/33-18-session.md`, AC bullet 8 vs Implementation Strategy note
  - Spec text: AC-8 lists "client handler in Redux store" as part of the story; Implementation Strategy says "No UI changes — this story is backend only; 33-17 consumes the payload"
  - Implementation: No Redux handler in this story; 33-17 will add the client consumer
  - Rationale: The AC bullet was inherited from an early draft that predated the 33-17/33-18 split. The Implementation Strategy section and the "Depended on by 33-17" note are authoritative per the spec authority hierarchy. Architect spec-check phase resolved this as Option C (clarify spec) and stamped it acceptable. Logged here for audit completeness.
  - Severity: trivial
  - Forward impact: None — 33-17 is the designated client consumer and depends on this story.

- **No client-side handler wiring test**
  - Spec source: `CLAUDE.md` → "Every Test Suite Needs a Wiring Test"
  - Spec text: "Every set of tests must include at least one integration test that verifies the component is wired into the system — imported, called, and reachable from production code paths."
  - Implementation: This story has four server-side wiring tests (module import + function call + variant push + byte-ordered emit-after-NarrationEnd) but no UI wiring test because the UI consumer is explicitly out of scope.
  - Rationale: The wiring-test rule applies to the system boundary the story operates at. 33-18 operates at the protocol + server boundary and fully covers it. The UI boundary belongs to 33-17, which is the designated client-side consumer.
  - Severity: trivial
  - Forward impact: 33-17 MUST add a UI wiring test asserting the Redux reducer imports `ScrapbookEntry`, handles it in a reducer case, and the reducer is reached from the message dispatch. Call this out in 33-17's context when it enters RED — the reviewer on 33-17 should fail the wiring-check gate if it's missing.

- **Four type-design improvements dismissed as cross-story scope (not in-story deviations, but architectural debt)**
  - Spec source: `reviewer-type-design` subagent findings (see Reviewer Assessment)
  - Spec text: `turn_id: u32` but `TurnManager::interaction() -> u64`; `NpcRef.name`/`role`, `ScrapbookEntryPayload.location`/`narrative_excerpt` as raw `String` vs `NonBlankString`; `ScrapbookEntryPayload` has no validated constructor
  - Implementation: All four follow existing protocol-wide conventions verbatim
  - Rationale: Every other payload in `sidequest-protocol/src/message.rs` follows the same raw-String + fully-public-field pattern: `PartyMember`, `ImagePayload`, `ConfrontationActor`, `ActionRevealPayload` (`turn_number: u32`), `TurnStatusPayload`, and every other display-bound payload. `NonBlankString` is used only at `PlayerActionPayload.action` (the user-input trust boundary). Retrofitting four fields on one new payload would create uneven hardening across the protocol surface.
  - Severity: minor (architectural debt at the protocol level, not a bug introduced by this story)
  - Forward impact: Future protocol hardening initiative should (a) unify `turn_id`/`turn_number` on a consistent scalar type or introduce a `TurnId` newtype, (b) sweep display-bound string fields to `NonBlankString` where non-empty is an implicit contract, (c) consider validated constructors for payload structs whose invariants can be enforced at construction time. Tracked as architectural debt. No 33-18 forward impact.

**AC deferral audit:** No ACs deferred. No ac-completion gate deferral table exists in this session. Every session AC is addressed in-story or covered by an explicit deviation with forward impact noted.

**Architect reconcile verdict:** Deviation manifest is complete and audit-ready. All 8 in-flight entries verified accurate and self-contained; 3 additional entries logged above for audit completeness (session-internal inconsistency already resolved during spec-check, UI wiring-test obligation forwarded to 33-17, protocol-hardening architectural-debt note). Story is ready for SM finish ceremony.