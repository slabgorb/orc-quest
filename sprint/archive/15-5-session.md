---
story_id: "15-5"
jira_key: ""
epic: "15"
workflow: "trivial"
---
# Story 15-5: Daemon client typed API — wire or remove stub types

## Story Details
- **ID:** 15-5
- **Epic:** 15 (Playtest Debt Cleanup — Stubs, Dead Code, Disabled Features)
- **Jira Key:** N/A (personal project)
- **Workflow:** trivial
- **Points:** 2
- **Priority:** p3
- **Stack Parent:** none (independent story)

## Story Description

`daemon-client/types.rs` has stub parameter types, result types, and request builder that are never used — raw HTTP calls bypass the typed layer. Either wire the typed API into the actual daemon communication or remove the stubs to avoid confusion.

### Current State

The `sidequest-daemon-client` crate defines:
- `DaemonRequest<P>`, `DaemonResponse` envelopes (used)
- `RenderParams`, `RenderResult` (used)
- `TtsParams`, `TtsResult` (used)
- `WarmUpParams`, `StatusResult` (used)
- `build_request_json()` helper (used)

The client.rs uses all these types properly. The comments in types.rs say "stubs" but the types are fully implemented. The issue is the misleading comments that suggest they're not wired.

### Decision Required

This is a 2-point trivial story. The work is likely:
1. Review types.rs comments to confirm nothing is actually stubbed
2. Update comments to reflect that types ARE implemented and actively used
3. Verify no orphaned/dead code paths exist
4. Run tests to confirm the full pipeline is wired end-to-end

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-03-30T11:43:02Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-03-30 | 2026-03-30T11:36:24Z | 11h 36m |
| implement | 2026-03-30T11:36:24Z | 2026-03-30T11:39:19Z | 2m 55s |
| review | 2026-03-30T11:39:19Z | 2026-03-30T11:43:02Z | 3m 43s |
| finish | 2026-03-30T11:43:02Z | - | - |

## Sm Assessment

Story 15-5 is a 2-point trivial cleanup. The daemon-client types are fully implemented and actively used — the story description's "stubs" framing is misleading. The real work is removing misleading comments and verifying nothing is actually orphaned. Straightforward debt cleanup with no architectural risk.

**Routing:** Dev (trivial implement phase). No design phase needed.

## Delivery Findings

No upstream findings at setup time.

### Dev (implementation)
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): `build_request_json` silently swallows param serialization failures via `unwrap_or(empty object)`. Affects `crates/sidequest-daemon-client/src/types.rs:199` (should return `Result` and propagate error). *Found by Reviewer during code review.*

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `crates/sidequest-daemon-client/src/types.rs` — removed 3 misleading "stub" section comments
- `crates/sidequest-daemon-client/tests/error_handling.rs` — clippy: use `io::Error::other()` API
- `crates/sidequest-protocol/src/tests.rs` — clippy: `assert!(!x)` instead of `assert_eq!(x, false)`

**Tests:** 659/659 passing (GREEN)
**Branch:** feat/15-5-daemon-client-typed-api (pushed)

**Handoff:** To review phase

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | deferred 1 (pre-existing) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 (self-corrected from 2) | N/A |

**All received:** Yes (3 returned, 6 disabled)
**Total findings:** 0 confirmed, 0 dismissed, 1 deferred

### Subagent Finding Details

**[SILENT] `build_request_json` unwrap_or at types.rs:199** — `serde_json::to_value(params).unwrap_or(empty object)` silently swallows serialization failures, sending `{}` params to the daemon. High confidence. **Deferred:** This is pre-existing code not introduced by this diff. The story scope is "wire or remove stub types" (comment cleanup), not refactoring error handling. Logged as delivery finding for future story.

## Reviewer Assessment

**Verdict:** APPROVED

### Observations

1. [VERIFIED] Stub comments accurately removed — `types.rs:17,155,189` previously said "stubs — Dev fills in fields" / "stub — Dev implements", now correctly read as plain section headers. The underlying types (`RenderParams`, `TtsParams`, `WarmUpParams`, `RenderResult`, `StatusResult`, `build_request_json`) are all fully implemented with real fields and doc comments. Evidence: `types.rs:22-38` (RenderParams has 5 fields), `types.rs:43-56` (TtsParams has 5 fields), `types.rs:195-201` (build_request_json is implemented).

2. [VERIFIED] `io::Error::other()` API is correct — `error_handling.rs:126,158` use `std::io::Error::other("test")` which is the stable Rust 1.74+ replacement for `Error::new(ErrorKind::Other, msg)`. Semantically identical. Rust version is 1.93.

3. [VERIFIED] Boolean assertion idioms are correct — `tests.rs:536` changed `assert_eq!(payload.aside, false)` to `assert!(!payload.aside)`, and `tests.rs:610` changed `assert_eq!(payload.in_combat, true)` to `assert!(payload.in_combat)`. Both are clippy `bool_assert_comparison` fixes. Same semantics, better readability.

4. [VERIFIED] All types are wired end-to-end — `client.rs:8-11` imports `RenderParams`, `RenderResult`, `TtsParams`, `TtsResult`, `WarmUpParams`, `StatusResult`, and `build_request_json`. Methods `render()` (line 96), `synthesize()` (line 170), `warm_up()` (line 159) use them. No orphaned types.

5. [SILENT] Pre-existing silent fallback at `types.rs:199` — `unwrap_or(empty object)` on param serialization. Not introduced by this diff but worth tracking. Deferred to future story.

6. [RULE] Rule-checker confirmed all 4 project rules checked (no stubs, no half-wired, no skipped tests, code matches intent) — 0 violations after full analysis.

7. [EDGE] N/A — edge-hunter disabled via settings.
8. [TEST] N/A — test-analyzer disabled via settings.
9. [DOC] N/A — comment-analyzer disabled via settings.
10. [TYPE] N/A — type-design disabled via settings.
11. [SEC] N/A — security disabled via settings.
12. [SIMPLE] N/A — simplifier disabled via settings.

### Rule Compliance

No project rules files found (`.claude/rules/*.md` empty, no lang-review checklists). Checked against CLAUDE.md rules:

| Rule | Instances Checked | Compliant |
|------|-------------------|-----------|
| No stubs/hacks | 3 comment changes | Yes — stale stub labels removed, types are real |
| No half-wired features | build_request_json, all param/result types | Yes — all wired in client.rs |
| No skipping tests | 4 test changes | Yes — tests retained, only idioms modernized |

### Data Flow Trace

`RenderParams` → `build_request_json(method, &params)` (types.rs:195) → `serde_json::to_string(&req)` (client.rs:55) → `write_all` to Unix socket (client.rs:59) → daemon response → `DaemonResponse` (client.rs:69) → `RenderResult` (client.rs:121). All typed, all wired.

### Devil's Advocate

This is a 2-point comment cleanup story. What could go wrong? The changes are comment-only in types.rs and test-only elsewhere — no production logic changed. But let me probe.

Could removing "stub" comments cause someone to miss that `build_request_json` has the `unwrap_or` silent fallback? The old comment said "stub — Dev implements" — maybe that was a signal that the function wasn't production-ready? No — the function IS implemented and used in every daemon call. The "stub" label was actively misleading, suggesting incompleteness where none exists. Removing it is correct.

Could `io::Error::other()` behave differently than `Error::new(ErrorKind::Other, msg)`? No — `Error::other()` is a convenience constructor that calls `Error::new(ErrorKind::Other, msg)` internally. Same `ErrorKind`, same `Display` output. The tests that check `Display` output (`each_variant_has_distinct_display_message`) still pass, confirming identical behavior.

Could the `assert!(!x)` change mask a type change? If `aside` changed from `bool` to something else, `assert_eq!(aside, false)` would catch it at compile time but `assert!(!aside)` might not (if the type implements `Not`). But `aside` is `pub aside: bool` in the protocol type — checked at `sidequest-protocol/src/lib.rs`. And Rust's `!` operator on non-bool types requires explicit `Not` impl, which serde-derived structs don't get. So this is safe.

The `unwrap_or` at types.rs:199 is the one real concern in this file — but it's pre-existing, out of scope, and logged as a delivery finding.

**Handoff:** To Grand Admiral Thrawn for finish-story

## Design Deviations

### Dev (implementation)
- No deviations from spec.

### Reviewer (audit)
- No undocumented deviations found. Dev's "no deviations" claim is accurate — the changes are mechanical comment/idiom cleanup matching story scope exactly.

## Branch & Context

- **Branch:** `feat/15-5-daemon-client-typed-api`
- **Repo:** sidequest-api
- **Related Files:**
  - `crates/sidequest-daemon-client/src/types.rs` (main artifact)
  - `crates/sidequest-daemon-client/src/client.rs` (usage)
  - `crates/sidequest-server/src/lib.rs` (integration point)