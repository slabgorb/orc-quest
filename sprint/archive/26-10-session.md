---
story_id: "26-10"
jira_key: "none"
epic: "26"
workflow: "tdd"
---

# Story 26-10: Wire map cartography data through dispatch to UI

## Story Details

- **ID:** 26-10
- **Jira Key:** none (personal project)
- **Epic:** 26 — Wiring Audit Remediation
- **Workflow:** tdd (phased: setup → red → green → spec-check → verify → review → spec-reconcile → finish)
- **Points:** 5
- **Priority:** p1
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-04-06T19:16:52Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-06T18:29:20Z | 2026-04-06T18:31:00Z | 1m 40s |
| red | 2026-04-06T18:31:00Z | 2026-04-06T18:41:28Z | 10m 28s |
| green | 2026-04-06T18:41:28Z | 2026-04-06T18:52:40Z | 11m 12s |
| spec-check | 2026-04-06T18:52:40Z | 2026-04-06T18:53:56Z | 1m 16s |
| verify | 2026-04-06T18:53:56Z | 2026-04-06T18:57:59Z | 4m 3s |
| review | 2026-04-06T18:57:59Z | 2026-04-06T19:15:51Z | 17m 52s |
| spec-reconcile | 2026-04-06T19:15:51Z | 2026-04-06T19:16:52Z | 1m 1s |
| finish | 2026-04-06T19:16:52Z | - | - |

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Gap** (non-blocking): `MapUpdatePayload.region` is set to `ctx.current_location.clone()` in narration dispatch (dispatch/mod.rs:963), which is the room/location name, not the actual region. The field semantics are confused — `region` should carry the region name from cartography, not duplicate `current_location`. Affects `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` (line 963, 2305). *Found by TEA during test design.*
- **Gap** (non-blocking): `fog_bounds` is hardcoded to `None` in all 3 MAP_UPDATE construction sites (dispatch/mod.rs:965, 2307; connect.rs:345). Affects `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` and `connect.rs`. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Gap** (non-blocking): Reconnect WatcherEvent at `connect.rs:385` lacks `has_cartography` and `navigation_mode` OTEL fields. GM panel cannot verify cartography delivery on session restore. Affects `sidequest-api/crates/sidequest-server/src/dispatch/connect.rs` (add fields to existing WatcherEventBuilder). *Found by Reviewer during code review.*
- **Gap** (non-blocking): No server-side integration test verifies DispatchContext populates `cartography_metadata` from genre pack. Protocol tests verify serde only. Affects `sidequest-api/crates/sidequest-server/tests/` (new integration test needed). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `broadcast_state_changes` in `state.rs:1047` emits MAP_UPDATE with `cartography: None`. Message ordering currently safe (broadcast fires before dispatch's cartography-carrying MAP_UPDATE) but fragile. Consider removing MAP_UPDATE from `broadcast_state_changes` long-term. Affects `sidequest-api/crates/sidequest-game/src/state.rs`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- TEA "No deviations" → ✓ ACCEPTED by Reviewer: confirms no spec drift in test design.
- Dev "No deviations" → ✓ ACCEPTED by Reviewer: implementation matches story goal — cartography wired end-to-end through protocol, dispatch, and UI.

### Architect (reconcile)
- No additional deviations found. TEA and Dev entries verified — "no deviations" is accurate for a wiring story where the implementation directly matches the story goal (extend MapUpdatePayload with cartography, wire through dispatch, render in UI). Reviewer's delivery findings (reconnect OTEL gap, missing server integration test, broadcast_state_changes fragility) are correctly classified as gaps/improvements, not spec deviations.

## Implementation Context

### Story Goal

Wire the cartography system (maps, regions, explored locations, navigation metadata) from genre packs through the dispatch pipeline to the UI. The genre loader already reads `cartography.yaml` from each world, but this data is not currently being sent to clients in the MAP_UPDATE message.

### Files Changed

**sidequest-api:**
- `crates/sidequest-protocol/src/message.rs` — Added CartographyMetadata, CartographyRegion, CartographyRoute structs; added optional cartography field to MapUpdatePayload
- `crates/sidequest-protocol/src/tests.rs` — Updated existing map_update_round_trip test for new field
- `crates/sidequest-protocol/src/cartography_wiring_story_26_10_tests.rs` — Updated wiring test struct literal
- `crates/sidequest-server/src/dispatch/mod.rs` — Added cartography_metadata to DispatchContext; wired into both MAP_UPDATE construction sites; added OTEL span
- `crates/sidequest-server/src/dispatch/connect.rs` — Built CartographyMetadata from genre pack in DispatchContext init and reconnect MAP_UPDATE
- `crates/sidequest-server/src/lib.rs` — Built CartographyMetadata in second DispatchContext construction site
- `crates/sidequest-game/src/state.rs` — Added cartography: None to delta-based MapUpdate construction

**sidequest-ui:**
- `src/components/MapOverlay.tsx` — Added CartographyMetadata/Region/Route interfaces to MapState; renders navigation mode indicator, regions panel, routes, starting region marker

## Sm Assessment

**Story readiness:** Ready for RED phase. This is a classic wiring story — the cartography system exists in the genre loader but isn't connected through dispatch to the UI.

**Scope:** Well-bounded. Protocol types exist, MAP_UPDATE exists, genre loader reads cartography.yaml. The gap is dispatch → protocol → UI. No new subsystems needed.

**Risks:** The main design question is whether to extend MapUpdatePayload or create a separate message. TEA should resolve this during RED phase based on what the tests need.

**Routing:** TEA (Han Solo) for RED phase — write failing tests that verify MAP_UPDATE includes cartography metadata from the genre pack.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Wiring story — protocol, dispatch, and UI all need changes with testable contracts.

**Test Files:**
- `sidequest-api/crates/sidequest-protocol/src/cartography_wiring_story_26_10_tests.rs` — 6 tests (4 failing, 2 passing baseline)
- `sidequest-ui/src/components/__tests__/MapOverlay.cartography.test.tsx` — 8 tests (7 failing, 1 passing baseline)

**Tests Written:** 14 tests covering 5 ACs + backward compat + wiring check
**Status:** RED (failing — ready for Dev)

**Handoff:** To Yoda (Dev) for implementation

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-api/crates/sidequest-protocol/src/message.rs` — CartographyMetadata, CartographyRegion, CartographyRoute structs + optional field on MapUpdatePayload
- `sidequest-api/crates/sidequest-server/src/dispatch/mod.rs` — cartography_metadata on DispatchContext, wired to MAP_UPDATE, OTEL span
- `sidequest-api/crates/sidequest-server/src/dispatch/connect.rs` — CartographyMetadata built from genre pack in DispatchContext init + reconnect
- `sidequest-api/crates/sidequest-server/src/lib.rs` — CartographyMetadata in second DispatchContext construction
- `sidequest-api/crates/sidequest-game/src/state.rs` — cartography: None for delta-based construction
- `sidequest-ui/src/components/MapOverlay.tsx` — CartographyMetadata types + conditional rendering

**Tests:** 27/27 passing (GREEN) — 6 protocol + 8 cartography UI + 13 original MapOverlay
**Branch:** feat/26-10-wire-map-cartography (pushed to both api and ui)

**Wiring verification:**
- Protocol: CartographyMetadata round-trips through serde, backward compat confirmed
- Dispatch: All 3 MAP_UPDATE construction sites carry cartography from genre pack
- DispatchContext: 2 construction sites (connect.rs, lib.rs) build CartographyMetadata
- UI: MapOverlay renders navigation mode, regions, routes, starting region when present
- OTEL: cartography_dispatch span emitted on location change

**Handoff:** To next phase (verify)

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 7

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | CartographyMetadata construction 3× duplication (high), UI location comparison 5× (medium), lib.rs duplicate init (high — overlaps #1) |
| simplify-quality | 2 findings | Outdated test comment (low), TypeScript optional description typing (low) |
| simplify-efficiency | 5 findings | Same duplication as reuse (high), test JSON re-serialization (medium ×2), UI location comparison (medium), connection dedup (low) |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 medium-confidence finding (test JSON re-serialization pattern — tests used JSON accessors during RED phase before types existed; could be refactored to direct struct access now)
**Noted:** 2 low-confidence observations (outdated test comment, TypeScript optional typing)
**Reverted:** 0

**Rationale for not applying high-confidence duplication fix:** Architect assessed in spec-check that the 3× CartographyMetadata construction duplication is "Acceptable for a wiring story — extracting a helper would create cross-module coupling for a 10-line closure. If a 4th site appears, extract then." Simplify defers to that judgment.

**Overall:** simplify: clean (no fixes applied, all findings triaged)

**Quality Checks:** All 27 tests passing, clippy warnings pre-existing (not introduced by this story)
**Handoff:** To Obi-Wan (Reviewer) for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** 0

The implementation correctly wires CartographyConfig from genre pack through dispatch to the UI via an optional `cartography` field on MapUpdatePayload. Key architectural observations:

1. **Protocol isolation** — CartographyMetadata uses `String` for `navigation_mode` rather than importing the `NavigationMode` enum from sidequest-genre. Correct decision — the protocol crate must remain dependency-free from domain crates. The match-based conversion at the dispatch boundary is the right pattern.

2. **deny_unknown_fields scope** — MapUpdatePayload retains `deny_unknown_fields`. CartographyMetadata intentionally omits it for forward compatibility — genre pack `Region` types use `#[serde(flatten)]` for extras, so strict field rejection at the wire level would break when genre packs add domain-specific extensions. Sound trade-off.

3. **Conversion duplication** — The CartographyConfig→CartographyMetadata conversion appears in 3 sites (connect.rs ×2, lib.rs ×1). Acceptable for a wiring story — extracting a helper would create cross-module coupling for a 10-line closure. If a 4th site appears, extract then.

4. **OTEL coverage** — Cartography dispatch span on location change is the critical observation point. Reconnect path already had a watcher event. Adequate for verifying the subsystem is engaged.

5. **Backward compatibility** — `#[serde(default, skip_serializing_if)]` on the optional field ensures existing MAP_UPDATE messages without cartography continue to deserialize. Protocol version bump not required.

**Decision:** Proceed to verify

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (conflict was working tree artifact, resolved) | N/A |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | N/A — Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | dismissed 3 (systemic .ok() pattern, not story-specific), confirmed 1 as delivery finding |
| 4 | reviewer-test-analyzer | Yes | Skipped | disabled | N/A — Disabled via settings |
| 5 | reviewer-comment-analyzer | Yes | Skipped | disabled | N/A — Disabled via settings |
| 6 | reviewer-type-design | Yes | Skipped | disabled | N/A — Disabled via settings |
| 7 | reviewer-security | Yes | Skipped | disabled | N/A — Disabled via settings |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | N/A — Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 4 | confirmed 2 (OTEL gap, dead test branch), dismissed 1 (is_some assertion adequate), noted 1 as delivery finding |

**All received:** Yes (3 returned results, 6 disabled via settings)
**Total findings:** 2 confirmed, 4 dismissed (with rationale), 2 deferred as delivery findings

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Protocol types correctly structured — `CartographyMetadata`, `CartographyRegion`, `CartographyRoute` at `message.rs:665-710`. All fields documented. `#[serde(default)]` on optional fields. `Option<CartographyMetadata>` with `skip_serializing_if` for backward compat. Complies with Rust rules #8 (no Deserialize bypass — no validating constructor), #9 (pub fields acceptable — no security invariants), #11 (no new Cargo.toml changes).

2. [VERIFIED] End-to-end wiring traced — Genre YAML → `GenreLoader` → `World.cartography` → `NavigationMode` match → `CartographyMetadata` construction (connect.rs:340-369, connect.rs:1375-1407, lib.rs:1817-1849) → `DispatchContext.cartography_metadata` → `MapUpdatePayload.cartography` (mod.rs:969, mod.rs:2317, connect.rs:376) → JSON over WebSocket → `App.tsx:494` → `MapOverlay.tsx:44` conditional rendering. Non-test consumers verified: `MapOverlay` imported by `GameLayout.tsx` and `OverlayManager.tsx`.

3. [VERIFIED] OTEL observability — `WatcherEventBuilder` at `dispatch/mod.rs:973-977` emits `cartography_dispatch` with `has_cartography` and `navigation_mode` on location change. Complies with OTEL principle.

4. [MEDIUM] [RULE] [SILENT] Missing OTEL fields on reconnect WatcherEvent — `connect.rs:385-389` emits `map_update.reconnect` but lacks `has_cartography` and `navigation_mode`. GM panel cannot verify cartography delivery on session restore. Non-blocking — cartography is still delivered, just not observable on reconnect.

5. [LOW] [RULE] Dead `is_null()` branch in test — `cartography_wiring_story_26_10_tests.rs:183-187` has `assert!(is_none() || is_null())` but `skip_serializing_if = Option::is_none` means the field is always absent, never null. The `is_null()` branch is dead code. Cosmetic.

6. [VERIFIED] Backward compatibility — Test `map_update_without_cartography_still_deserializes` at test file line 164 proves MAP_UPDATE without cartography still works. `#[serde(default)]` at `message.rs:662` handles absent field.

7. [VERIFIED] UI rendering — Conditional `{cartography && (...)}` at `MapOverlay.tsx:56` only renders cartography elements when present. Backward compat test at `MapOverlay.cartography.test.tsx:138` verifies no cartography elements without the field. No XSS risk — text content rendered, not innerHTML.

### Rule Compliance

| Rule | Instances | Status |
|------|-----------|--------|
| Rust #1 silent errors | 9 `.ok()` chains | Compliant — follows existing pattern for optional enrichment data |
| Rust #2 non_exhaustive | 0 new enums | N/A |
| Rust #3 placeholders | 1 `"none"` OTEL default | Compliant — telemetry only |
| Rust #4 tracing | 3 paths checked | 1 gap: reconnect OTEL missing cartography fields |
| Rust #5 constructors | 3 construction sites | Compliant — trusted internal data source |
| Rust #6 test quality | 6 tests checked | 1 dead branch (cosmetic) |
| Rust #7-15 | Checked | All compliant or N/A |
| TS #1-13 | Checked | All compliant; pre-existing `as unknown as MapState` noted |
| OTEL rule | 3 paths | 1 gap (reconnect, non-blocking) |
| Wiring test rule | Protocol + UI | Protocol has wiring test; server integration test missing (delivery finding) |

### Devil's Advocate

What if this code is broken? The `broadcast_state_changes` path in `state.rs:1047` emits MAP_UPDATE with `cartography: None` when regions change. If this fires after the dispatch MAP_UPDATE that carries cartography, the UI's `setMapData()` replaces the full state — clobbering cartography. However, examining the flow: `broadcast_state_changes` sends via `ctx.tx` at `mod.rs:1421-1424` during dispatch, while the dispatch's own MAP_UPDATE is returned in the Vec and sent afterward. So the broadcast fires FIRST (with None), then dispatch fires SECOND (with cartography). The UI gets the correct one last. But this ordering is fragile — it depends on the dispatch pipeline structure, not an explicit contract. A future refactor that reorders these sends could silently break cartography delivery. This is a pre-existing architectural concern that this story exposes but doesn't introduce. The correct long-term fix is to remove MAP_UPDATE from `broadcast_state_changes` and let dispatch own all MAP_UPDATE construction — but that's a separate story.

What about a malformed genre pack? If `cartography.yaml` has a region with no `name` field, `CartographyRegion.name` is a required field — `serde` will fail deserialization of the genre pack entirely (GenreLoader returns Err), which the `.ok()` converts to None. The session proceeds without cartography. This is correct degradation behavior.

What about a huge cartography? A genre pack with 1000 regions would produce a large MAP_UPDATE on every location change (cartography is cloned each time). This is theoretically wasteful but practically bounded by genre pack authorship (no user input controls region count). Not a concern.

**Data flow traced:** CartographyConfig (genre YAML) → NavigationMode match → CartographyMetadata (protocol) → MapUpdatePayload.cartography → JSON WebSocket → App.tsx setMapData → MapOverlay conditional render. Safe: no user input in cartography data, no innerHTML rendering.

**Pattern observed:** Wire-format subset pattern — protocol crate carries a simplified view of domain types for the UI, converted at the dispatch boundary. Good pattern at `connect.rs:340-369`.

**Error handling:** Genre pack load failure → `.ok()` → `None` → cartography absent from MAP_UPDATE → UI renders without cartography panel. Graceful degradation.

**Handoff:** To Grand Admiral Thrawn (SM) for finish-story