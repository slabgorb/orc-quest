---
story_id: "37-21"
jira_key: null
epic: "37"
workflow: "trivial"
---
# Story 37-21: Template placeholder leak in Space Opera chargen-confirm

## Story Details
- **ID:** 37-21
- **Epic:** 37 (Playtest 2 Fixes)
- **Jira Key:** None (personal project)
- **Workflow:** trivial
- **Priority:** p0
- **Points:** 1
- **Type:** bug
- **Repos:** content, api
- **Stack Parent:** none

## Issue Summary

Template placeholders in the Space Opera character creation confirmation scene render literally instead of being interpolated. The confirmation narration displays:

```
"Welcome aboard, {name}. Stow your gear in bunk seven. We jump in
an hour, and after that it's all new sky.

The {class} from {race} space. The ship hums around you, and for the
first time in a while, the sound doesn't feel like someone else's home."
```

Instead of filling in the player's actual name, class, and race values. This is a template engine mismatch or missing context keys issue.

**Affected:** sidequest-content/genre_packs/space_opera/char_creation.yaml (lines 233-250)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-04-18T11:37:35Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-04-18T06:22:00Z | 2026-04-18T10:23:16Z | 4h 1m |
| implement | 2026-04-18T10:23:16Z | 2026-04-18T10:48:48Z | 25m 32s |
| review | 2026-04-18T10:48:48Z | 2026-04-18T11:10:38Z | 21m 50s |
| implement | 2026-04-18T11:10:38Z | 2026-04-18T11:22:17Z | 11m 39s |
| review | 2026-04-18T11:22:17Z | 2026-04-18T11:28:08Z | 5m 51s |
| implement | 2026-04-18T11:28:08Z | 2026-04-18T11:32:20Z | 4m 12s |
| review | 2026-04-18T11:32:20Z | 2026-04-18T11:37:35Z | 5m 15s |
| finish | 2026-04-18T11:37:35Z | - | - |

## Delivery Findings

No upstream findings at setup.

## Design Deviations

None recorded at setup.

## Sm Assessment

**Scope:** 1-pt p0 bug. Space Opera confirmation narration at `sidequest-content/genre_packs/space_opera/char_creation.yaml` lines 233–250 contains `{name}`, `{class}`, `{race}` placeholders that render as literal curly-braced strings to the player.

**Likely root cause (for dev to confirm, not to act on blindly):** one of three:
1. The confirmation scene's text field is not passing through the same template interpolator used elsewhere in the genre pack (template engine mismatch).
2. The context object at confirmation-render time is missing the `name`/`class`/`race` keys the template expects (naming drift — maybe `character_name` vs `name`, `archetype` vs `class`).
3. The Space Opera pack authored curly-brace placeholders while the active templating engine uses a different delimiter (`{{ }}`, `$var`, etc.) — an authoring mismatch against the genre pack convention.

**Playgroup angle:** Space Opera is the pack being exercised by Keith-as-player. The confirmation scene is the first beat after character creation — this is exactly where a placeholder leak breaks immersion for someone who just built their character. Sebastien-style mechanical-visibility players will also clock this as a bug instantly. Fix is high-value for low effort.

**Approach for Dev:**
1. Read `char_creation.yaml` lines 233–250 in sidequest-content for the actual placeholder syntax used.
2. Grep other genre packs' `char_creation.yaml` files for how they write the same confirmation beat — pick the delimiter/context-key convention that already works end-to-end in another pack.
3. Trace the API-side render path to confirm which templating layer touches this scene. sidequest-api crates: genre loader, game engine, or agents — whichever owns the "render narration with character context" step.
4. Fix at the layer that's actually wrong. If it's an authoring bug in content, the content fix is one-file; if it's a wiring gap in the render path, fix in api. **Do not patch both sides defensively.**
5. Verify with a real Space Opera chargen run — not just a unit test. The playtest screenshots (`039-space-opera-select.png` through the chargen sequence, in the sq-playtest-screenshots dir after the skill fix lands) are the acceptance reference.

**Repo targeting:** Story has `repos: content,api`. Branches were created in both. Actual fix probably lands in only one — let that inform the PR scope rather than making both branches land changes.

**Wiring check:** After the fix, verify via a non-test consumer that the rendered confirmation narration contains real values, not curly-braced literals. Unit tests on a template function alone are insufficient per project "Every Test Suite Needs a Wiring Test" rule.

**No Jira.** Personal project — do not attempt any Jira transitions.

## Dev Assessment

**Implementation Complete:** Yes

**Decision trail (important — first pass was wrong):**

First attempt rewrote the space_opera YAML to drop the placeholders — a cosmetic "nerf the feature" fix. Keith pushed back correctly: the author's intent was personalization, not static prose. Reverted the content edit and implemented the actual interpolation in Rust. This is now the proper fix at the right layer.

**Root cause:** `CharacterBuilder::to_scene_message` at `builder.rs:1353` constructed the protocol payload with `scene.narration.clone()` — a byte-for-byte copy. No template engine existed. Genre packs (space_opera, heavy_metal) authored `{name}/{class}/{race}` placeholders expecting substitution that was never implemented, so the tokens rendered literally.

**Fix layer:** api (Rust), not content. Added `CharacterBuilder::interpolate_scene_narration(&self, text: &str) -> String` and invoked it where the Scene-phase payload is constructed. Substitution sources are the builder's own accessors — `character_name()`, `accumulated().class_hint`, `accumulated().race_hint` — so no new data plumbing is required. Unresolved placeholders substitute as empty strings; a literal `{name}` can never reach the client.

**OTEL:** `chargen.StateTransition` event with `action=scene_narration_interpolated`, fields `name_resolved`, `class_resolved`, `race_resolved` (only populated when the token was actually present in the narration). Severity is `Info` when every used placeholder resolved, `Warn` when at least one used placeholder was empty — so the GM panel sees silent drift (e.g. a placeholder used in a scene that renders before its source scene) without blocking gameplay.

**Wiring test:** `wiring_scene_message_payload_routes_through_interpolator` asserts the public payload constructor (`to_scene_message`) routes through the interpolator, not merely that an isolated helper exists. Satisfies project rule "Every Test Suite Needs a Wiring Test."

**Files Changed:**
- `sidequest-api/crates/sidequest-game/src/builder.rs` — added `interpolate_scene_narration` helper (~60 lines including OTEL emission + docs), wired it at `to_scene_message` Scene branch.
- `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs` (new, 4 tests) — confirmation interpolation, missing-name no-leak invariant, no-placeholder verbatim passthrough, payload-routing wiring check.

**Content repo:** no changes. The space_opera YAML was reverted to its original placeholder-bearing form. The pre-created content branch was empty and has been deleted locally.

**Tests:** 4/4 passing on the new test file. Full workspace `cargo build --workspace` succeeds.

**Branch:** `feat/37-21-space-opera-template-leak` (pushed to `sidequest-api` origin).

**Handoff:** To review phase — Chrisjen Avasarala.

**Scope note — out-of-story observation:** `genre_packs/heavy_metal/char_creation.yaml` lines 248, 252 use the same `{name}/{class}/{race}` pattern. The api fix lands that pack as a silent beneficiary with no code change, but heavy_metal should also get a real playtest verification in a follow-up (logged as a Delivery Finding below).

## Dev Assessment (Rework — Round 2)

**Implementation Complete:** Yes
**Reviewer findings addressed:** 9 of 9 (3 HIGH, 5 MEDIUM, 1 LOW).

### How each reviewer finding was resolved

| Severity | Finding | Resolution |
|---|---|---|
| HIGH | Clippy `unnecessary_lazy_evaluations` on three `field_opt` calls | Replaced `.then(\|\| !x.is_empty())` with `.then_some(!x.is_empty())` in `builder.rs`. Also simplified the field shape — the previous `.map(\|b\| b.to_string())` dance was addressing both the stringification concern (separate finding) and producing the Option; collapsing both in one edit yields `Option<bool>` as `field_opt` expects. |
| HIGH | `cargo fmt --check` fails | Ran `cargo fmt -p sidequest-game`. Picked up unrelated pre-existing fmt drift in `trope_encounter_handshake_story_37_15_tests.rs` — folded into the same commit per Chrisjen's preflight guidance. |
| HIGH | Vacuous wiring assertion — `contains("playername=")` passes against uninterpolated input | Replaced with `assert_eq!(prompt, "classname=Spacer\|racename=Belt\|playername=")`. Full-string equality; a no-op interpolator fails this test. |
| MEDIUM | Unknown curly-brace tokens silently pass through | Added pure helper `find_unrecognized_token(&rendered)` scanning for `{...}` substrings outside the known three keys after substitution. When found, emits `chargen.StateTransition` with `action=scene_narration_unrecognized_placeholder`, `token=<offending-substring>`, Severity::Warn. Token still passes to client (contract is known keys only), but silent drift is gone. |
| MEDIUM | `/// See story 37-21.` in doc comment | Removed. Doc now reads "Genre packs author confirmation narration with personalization placeholders" — explains the why without task references. |
| MEDIUM | `//! Story 37-21:` in test module doc | Rewrote module doc to invariants-only: what's covered, what's asserted. No story references. Kept the filename (repo convention is `<topic>_story_<N-M>_tests.rs`, matched by 50+ peer files). |
| MEDIUM | OTEL emission completely untested | Added `interpolation_emits_state_transition_event` — subscribes to `subscribe_global()`, runs the payload constructor, asserts the StateTransition fires with correct fields and Warn severity. Drain helper `drain_events` handles broadcast-channel parallel-test cross-talk. |
| MEDIUM | Boolean-as-string inside `Option` in OTEL | Fixed as part of HIGH-1 above — `field_opt` now receives `Option<bool>` (serializes as native true/false), not `Option<String>`. GM panel reads true/false/absent, not the ambiguous `"false"`/`"true"`/missing-field. |
| LOW | Misleading "Seed the character_name" comment | Rewrote to: "Name is not set at this point (no freeform name entry has run). The class-choice scene populates class_hint and race_hint; those must substitute, while `{name}` substitutes as empty. This test covers class + race resolution; the empty-name case is exercised separately." |

### Deviation audit — reviewer's ACCEPTED deviation still holds

The reviewer's round-1 audit accepted my deviation that the interpolator only runs on `BuilderPhase::InProgress` Scene narration, not on `AwaitingFollowup.hook_prompt`. That scope decision is unchanged in this rework — no genre pack authors placeholders in `hook_prompt`, and extending coverage there would be speculative scope. If it ever matters, it's a 1-line follow-up.

### Files Changed

- `sidequest-api/crates/sidequest-game/src/builder.rs`:
  - Added free function `find_unrecognized_token(&str) -> Option<String>` (pure, `pub(crate)`).
  - Rewrote `CharacterBuilder::interpolate_scene_narration` — clippy-clean `then_some`, native-bool OTEL fields, post-substitution unknown-token scan.
  - Removed story reference from doc comment; clarified contract around unrecognized tokens.
- `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs`:
  - 7 tests now (was 4): added `placeholders_appearing_more_than_once_all_substitute`, `unrecognized_token_passes_through_and_fires_warn_event`, `interpolation_emits_state_transition_event`. Fixed the vacuous wiring assertion. Removed story references from module doc and inline comment.
- `sidequest-api/crates/sidequest-game/tests/trope_encounter_handshake_story_37_15_tests.rs`:
  - fmt drift only (not touched by 37-21 logic; swept in by `cargo fmt -p sidequest-game`).

### Gate status

- `cargo build -p sidequest-game`: PASS
- `cargo test -p sidequest-game --test scene_narration_interpolation_story_37_21_tests`: **7/7 PASS**
- `cargo clippy -p sidequest-game --lib -- -D warnings`: PASS
- `cargo clippy -p sidequest-game --test scene_narration_interpolation_story_37_21_tests -- -D warnings`: PASS
- `cargo fmt -p sidequest-game -- --check`: PASS
- `cargo build -p sidequest-server -p sidequest-agents`: PASS

**Not passing:** `cargo clippy --all-targets -p sidequest-game` fails on two unrelated test files (`gm_commands_story_9_8_tests.rs`, `merchant_wiring_story_15_16_tests.rs`) with stale `Npc { ... }` struct literals missing 6 fields added to Npc since those tests were written. This is pre-existing drift, not 37-21 regression. Logged as a Dev delivery finding above.

**Branch:** `feat/37-21-space-opera-template-leak` — force-synced, commit `e164c4e` pushed.

**Handoff:** Back to Chrisjen Avasarala for re-review.

## Subagent Results (Round 2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — all four mechanical gates pass |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 1, dismissed 1 (already-addressed in round 1) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 3, dismissed 1, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 1, dismissed 1 (filename — see below) |
| 6 | reviewer-type-design | Yes | findings | 3 | confirmed 1, dismissed 2 (deferred) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | dismissed 1 (filename — see below) |

**All received:** Yes (6 returned, 3 disabled per settings)
**Total findings:** 6 confirmed, 4 dismissed (with rationale), 1 deferred

## Rule Compliance (Round 2)

Re-verified against `.pennyfarthing/gates/lang-review/rust.md` + CLAUDE.md additional rules. Cross-checked against rule-checker subagent's exhaustive round-2 pass.

| # | Rule | Round-1 status | Round-2 status | Change |
|---|------|----------------|----------------|--------|
| 1 | Silent error swallowing | PASS | PASS | `drain_events` Lagged handling is correct broadcast pattern |
| 2 | `#[non_exhaustive]` | N/A | N/A | No new pub enums |
| 3 | Hardcoded placeholder values | FAIL (story refs) | PASS | All round-1 violations removed |
| 4 | Tracing coverage + severity | PASS | PASS | Warn/Info branching correct |
| 5 | Validated constructors | N/A | N/A | No new constructors |
| 6 | Test quality | FAIL (vacuous wiring) | **FAIL** (flaky drain, OR-disjunct) | New test-quality concerns introduced by rework (see below) |
| 7 | `as` casts | PASS | PASS | |
| 8 | Deserialize bypass | N/A | N/A | |
| 9 | Public fields on types with invariants | N/A | N/A | `find_unrecognized_token` is `pub(crate)`, not `pub` |
| 10 | Tenant context | N/A (no tenant model) | N/A | |
| 11 | Workspace deps | N/A | N/A | No Cargo.toml |
| 12 | Dev-only deps | N/A | N/A | No Cargo.toml |
| 13 | Constructor/Deserialize consistency | N/A | N/A | |
| 14 | Fix-introduced regressions | N/A | **FAIL** | Multi-token silent drop introduced by the unrecognized-token fix (see below) |
| 15 | Unbounded input | PASS | PASS | Linear `str::replace`, non-recursive |
| 16 | OTEL on subsystem decisions | PASS | PASS | Two event types, correct severity |
| 17 | No Silent Fallbacks | FAIL (unknown tokens) | **FAIL** (second+ tokens) | Fixed for first token only — second and beyond still silent |
| 18 | No task references in source | FAIL (×2) | PASS | All in-body references removed; filename convention is not a Rule-18 violation (see Dismissals) |
| 19 | Wiring test | PASS | PASS | `assert_eq!` on full string; no-op interpolator cannot sneak past |

**Round-2 rule failures:** Rule 6 (test quality — flaky sleep + OR-disjunct), Rule 14 (fix-introduced regression — multi-token silent drop), Rule 17 (second unrecognized token reaches client with no OTEL Warn).

## Devil's Advocate (Round 2)

The rework made this better — 6 of 9 round-1 findings are unambiguously closed. Clippy clean, fmt clean, vacuous wiring assertion replaced with full-string equality, story references stripped, OTEL emission now has dedicated tests, bool-as-string is native bool. That is a real improvement. If a reviewer rubber-stamps this, they are not being diligent — but rejecting out of reviewer ego would also be unjust.

Now the adversarial pass.

Consider a genre-pack author who writes a confirmation scene with three typos in one narration string: `"Hello {nmae}, welcome to {origi}, enjoy the {sahip}."`. The rework's `find_unrecognized_token` scans for the first `{`, finds `{nmae}`, returns `Some("{nmae}")`, fires one Warn event. The function exits. The helper is called once from `interpolate_scene_narration` and returns `Option<String>`, so exactly one event fires regardless of how many tokens are unrecognized. The client receives a client-facing narration with three leaked typos; the GM panel sees one warning. The GM investigates `{nmae}`, fixes that one typo, redeploys — and is still leaking `{origi}` and `{sahip}` to players, invisibly, until someone reports. This is *exactly* the silent-fallback failure mode the round-1 rejection targeted. The fix addressed the single-token case and stopped.

Three independent subagents — silent-failure-hunter at high confidence, test-analyzer at high confidence, type-design at medium confidence — identified this same issue. The test at line 515 tolerates it by asserting `token == "{nmae}" || token == "{origin}"` — a disjunction that documents the first-only behavior without asserting it and without ever checking that the second token also triggered a warning. That is a test that codifies the gap rather than closing it.

Consider the `drain_events` helper at line 583. It sleeps `10ms` unconditionally before `try_recv`. The emit path is `broadcast::Sender::send()` which is a synchronous function that returns before `builder.to_scene_message()` returns. The sleep is not closing a race — there is no race to close. It is a hedge against an imagined race, and in practice it adds 10ms of pure latency to two tests. Under CI load if the OS schedules the emitting thread late, 10ms may still be insufficient; the hedge doesn't solve the problem it claims to. Either the emit is synchronous (it is) and the sleep should come out, or it isn't and the sleep should be a `tokio::time::timeout` with a receive loop.

Consider test isolation. `init_global_channel` is an `OnceLock` — every test process-wide sees the same `broadcast::Sender`. Tests that subscribe will receive events from tests that don't subscribe (if both emit the same action). The rework's filtering by `action = "scene_narration_interpolated"` works because the OTEL-subscribing tests use unique action names — but two concurrently-running tests that both call the interpolator with the same inputs can pollute each other's views. I'm noting this at medium rather than blocking because in practice the test filters are sufficient for the current set. A `#[serial_test::serial]` attribute would make it airtight. Not blocking, but worth logging as a known flake risk.

Consider the filename. `scene_narration_interpolation_story_37_21_tests.rs`. Rule-checker called this a Rule 18 violation because the story number migrated from the module doc to the filename. Comment-analyzer agreed. I have sympathy for the argument, but the repo has approximately 50 files named `<topic>_story_<N>_<M>_tests.rs` (backstory_tables_story_31_2_tests.rs, builder_story_2_3_tests.rs, etc.) — this is not 37-21's invention, it is the established convention for test fixture organization in this crate. CLAUDE.md's Rule 18 examples ("used by X", "added for the Y flow", "handles the case from issue #123") are inline-comment patterns, not filename patterns. Treating the filename as a Rule 18 violation would require a 50-file rename that is out of scope for a 1-point story. This is a process question for SM/PM about whether the convention should change, not a block on 37-21. Dismissing and logging as a delivery finding.

The code improved. It is not done.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `[SILENT]` `[TYPE]` `[RULE]` Multi-token silent drop — `find_unrecognized_token` reports the FIRST unrecognized token only; subsequent typos in the same narration string reach the client with no OTEL Warn. This is the round-1 rejection issue, partially fixed. | `builder.rs:15-30` (`find_unrecognized_token`) + `builder.rs:82-92` (caller) | Either (a) loop the caller and emit one Warn per unrecognized token, or (b) change the helper to return `Vec<String>` / `Vec<&str>` and emit a single Warn with a `tokens` array. Rule 14 (fix-introduced regressions) + Rule 17 (No Silent Fallbacks). |
| [HIGH] | `[TEST]` `[RULE]` Test at line 515 encodes the silent-drop via `token == "{nmae}" \|\| token == "{origin}"` disjunction — passes regardless of which token fires and never asserts the second fires at all. | `tests/scene_narration_interpolation_story_37_21_tests.rs:515` | After the multi-token fix above lands, assert exactly two events fire, one per unrecognized token. If the helper stays first-only (no multi-token fix), assert specifically `token == "{nmae}"` (the first token in scan order) so the first-only contract is locked. |
| [MEDIUM] | `[TEST]` `drain_events` sleeps 10ms unconditionally before `try_recv` — emit path is synchronous, sleep adds pure latency and does not close any real race. | `tests/scene_narration_interpolation_story_37_21_tests.rs:583` | Remove `std::thread::sleep(Duration::from_millis(10))`. The `broadcast::Sender::send()` returns before the builder call returns; events are already in the ring buffer by the time `drain_events` runs. |
| [LOW] | `[DOC]` Inline comment at test line 461 duplicates the interpolator's contract rationale — drifts from the single source of truth in `builder.rs`. | `tests/scene_narration_interpolation_story_37_21_tests.rs:461` | Remove the parenthetical "(scope decision: the interpolator's contract is the three known keys only)" — the `interpolate_scene_narration` docstring already owns this. |
| [LOW] | `[TYPE]` `find_unrecognized_token` returns `Option<String>` when `Option<&str>` tied to the input lifetime would avoid an allocation on the Warn path. Low priority — Warn path is cold. | `builder.rs:15` | Defer. Pair with the multi-token fix if the signature changes anyway. |

**Deferred (not blocking this PR):**
- `[TYPE]` Stringly-typed three-key placeholder set still repeated across two methods (deferred from round 1, deferred again).
- `[TEST]` Missing test for narration that is ONLY a placeholder (`"{name}"` alone). Nice to have but not covering a real regression risk.
- `[TYPE]` Per-key `then_some(!x.is_empty())` triplication is the third encoding of the same domain concept — consider a `PlaceholderResolution` struct/enum when the set expands.

**Dismissed with rationale:**
- `[RULE]` `[DOC]` Filename `scene_narration_interpolation_story_37_21_tests.rs` flagged by rule-checker and comment-analyzer as Rule 18 violation — DISMISSED. Rule 18's examples in CLAUDE.md are inline-comment patterns ("used by X", "added for the Y flow", "handles the case from issue #123"), not filename conventions. The crate has 50+ test files with the `<topic>_story_<N>_<M>_tests.rs` pattern (backstory_tables_story_31_2_tests.rs, builder_story_2_3_tests.rs, trope_encounter_handshake_story_37_15_tests.rs, etc.) — this is the established convention. Enforcing Rule 18 against filenames would require a mass rename and a convention change. Logging as delivery finding for SM/PM to resolve as a process question, not as a block on 37-21.
- `[SILENT]` `unwrap_or("")` silent-default on name/class/race — DISMISSED. Round 1 already accepted this as documented contract behavior with OTEL coverage. The rework did not regress this path.
- `[TEST]` Cross-test pollution via shared global broadcast channel — DISMISSED at blocking severity, noted as risk. Current action-name filtering is sufficient for the present test set because the two OTEL-asserting tests filter on unique action strings. `#[serial_test::serial]` would make it airtight; worth doing if this test file grows.
- `[TYPE]` `find_unrecognized_token` returning `Option<&str>` — DEFERRED (above).

**Round-trip count:** 2. The remaining blockers are genuinely a small incremental fix (loop over the helper's return and emit per token, remove one `sleep`, strengthen one assertion). Not another full rework pass.

**Handoff:** Back to Naomi Nagata (Dev) for targeted rework. Per the trivial workflow (no RED phase), route via `review → implement rework`.

## Dev Assessment (Rework — Round 3)

**Implementation Complete:** Yes
**Reviewer round-2 findings addressed:** 5 of 5 (2 HIGH, 1 MEDIUM, 2 LOW).

### How each round-2 finding was resolved

| Severity | Finding | Resolution |
|---|---|---|
| HIGH | Multi-token silent drop — `find_unrecognized_token` returned Option on first match only | Renamed to `find_unrecognized_tokens`, return type is now `Vec<&str>` borrowed from the input. Rewrote as an exhaustive byte-level scanner that walks the entire rendered string and returns every non-`{name}/{class}/{race}` brace group (including unclosed `{foo` as a single trailing group). Caller loops and emits one Warn event per offending token. The borrowed-slice return also removes the allocation flagged as a type-design LOW — doing it now because the signature was changing anyway. |
| HIGH | OR-disjunct assertion encoded the silent-drop gap | Replaced with `tokens.contains(&"{nmae}") && tokens.contains(&"{origin}")`. Test now fails if either unrecognized token is dropped. Every Warn event's severity and token field are asserted for all events in the filter. |
| MEDIUM | `drain_events` 10ms sleep | Removed. `broadcast::Sender::send` is synchronous; by the time the code-under-test returns, emitted events are in the receiver's ring buffer. Updated helper docstring to document this. |
| LOW | Duplicate contract comment in typo-scene fixture | Removed the parenthetical "(scope decision: …)". The `interpolate_scene_narration` docstring is the single source of truth for the token contract. |
| LOW | `find_unrecognized_token` returned `Option<String>` with unnecessary allocation | Fixed as part of the HIGH-1 refactor — `Vec<&str>` borrows from the input. Zero heap allocation on the Warn path. |

### Scope decisions I did NOT act on (deferred per reviewer)

- **Filename Rule-18 question** — Reviewer dismissed the filename finding and logged it as a process question for SM/PM. I did not rename the file.
- **`PlaceholderResolution` enum / three-key const array** — Still deferred; a real refactor when the set expands.
- **`#[serial_test::serial]` on OTEL tests** — Not blocking; tests pass reliably because the two OTEL-asserting tests filter on distinct action strings. Noted as risk if the test file grows.

### Files Changed (round-3)

- `sidequest-api/crates/sidequest-game/src/builder.rs`:
  - Renamed `find_unrecognized_token` → `find_unrecognized_tokens`, signature now `pub(crate) fn find_unrecognized_tokens(rendered: &str) -> Vec<&str>`. Exhaustive scanner; doc comment explains why first-only was wrong.
  - Caller in `interpolate_scene_narration` loops and emits per-token.
- `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs`:
  - `unrecognized_token_passes_through_and_fires_warn_event` now asserts both tokens fire.
  - `drain_events` no sleep. Dropped unused `std::time::Duration` import.
  - Removed duplicate contract comment from the typo-scene fixture.

### Gate status

- `cargo test -p sidequest-game --test scene_narration_interpolation_story_37_21_tests`: **7/7 PASS**
- `cargo clippy -p sidequest-game --lib --test scene_narration_interpolation_story_37_21_tests -- -D warnings`: PASS
- `cargo fmt -p sidequest-game -- --check`: PASS

**Branch:** `feat/37-21-space-opera-template-leak`, commit `2390fa7` pushed.

**Handoff:** Back to Chrisjen Avasarala for round-3 review.

## Subagent Results (Round 3)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — 7/7 tests, clippy + fmt all green |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 | All six verification questions pass; multi-token gap closed; no new silent-failure paths |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 2 (severity-loop vacuous + missing zero-warns case), deferred 2 (precondition doc, cardinality assert) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 (misleading severity-loop comment, stale "old test" comment) |
| 6 | reviewer-type-design | Yes | findings | 2 | confirmed 1 (pub(crate) too wide), deferred 1 (Vec→Iterator) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 (Rule 6 vacuous severity loop — same as test-analyzer finding) |

**All received:** Yes (6 returned, 3 disabled per settings)
**Total findings:** 6 confirmed, 3 deferred, 0 dismissed

## Rule Compliance (Round 3)

Re-verified against `.pennyfarthing/gates/lang-review/rust.md` + CLAUDE.md additional rules.

| # | Rule | Round-2 | Round-3 | Change |
|---|------|---------|---------|--------|
| 1 | Silent error swallowing | PASS | PASS | Byte scanner has explicit arms for closed + unclosed branches |
| 2 | `#[non_exhaustive]` | N/A | N/A | |
| 3 | Hardcoded placeholder values | PASS | PASS | |
| 4 | Tracing coverage + severity | PASS | PASS | Warn severity preserved on per-token emission |
| 5 | Validated constructors | N/A | N/A | |
| 6 | Test quality | FAIL (vacuous wiring + OR-disjunct) | **DOWNGRADE** (severity loop vacuous when warns empty; cardinality unchecked) — see below |
| 7 | `as` casts | PASS | PASS | Byte-index arithmetic uses pure `usize`, no casts |
| 8 | Deserialize bypass | N/A | N/A | |
| 9 | Public fields on types with invariants | N/A | N/A | |
| 10 | Tenant context | N/A | N/A | |
| 11 | Workspace deps | N/A | N/A | |
| 12 | Dev-only deps | N/A | N/A | |
| 13 | Constructor/Deserialize consistency | N/A | N/A | |
| 14 | Fix-introduced regressions | FAIL | **PASS** | Round-3 exhaustive scanner closes the multi-token gap without introducing new rule violations |
| 15 | Unbounded recursive/nested input | PASS | PASS | Non-recursive, `i` advances monotonically; input bounded by narration length |
| 16 | OTEL on subsystem decisions | PASS | PASS | Per-token emission strengthens the GM lie-detector |
| 17 | No Silent Fallbacks | FAIL (second+ tokens) | **PASS** | Exhaustive scanner emits one Warn per offending token; unclosed braces take the explicit `(rendered.len(), rendered.len())` arm and are reported |
| 18 | No task references in source | PASS | PASS | No new round/review/story references in production code |
| 19 | No stubbing | PASS | PASS | |

**Rule 6 severity downgrade rationale:** the severity loop at test line ~154 (`for warn in &warns { assert!(matches!(warn.severity, Severity::Warn)) }`) IS vacuously true when `warns` is empty — per test-analyzer and rule-checker, both HIGH. However, the subsequent `tokens.contains(&"{nmae}")` and `tokens.contains(&"{origin}")` assertions DO fail with useful output when `warns` is empty (tokens vec ends up empty, contains returns false, assert fails with message "got tokens: []"). So the real-world regression scenarios — zero events fired, wrong token fired — are caught. The gap is narrow: a scanner that double-fires a known token AND fires the other (e.g. `[{nmae}, {nmae}, {origin}]`) would pass. That's a hypothetical regression, not a live bug. Downgrading from HIGH to MEDIUM and approving the story — the blocker class is closed and remaining finding is a quality refinement that belongs in a delivery finding, not another rejection round for a 1-point story.

## Devil's Advocate (Round 3)

Three rounds of review on a one-point story is already friction. The adversarial question is: would a fourth rejection catch anything that a playtest wouldn't also catch within one minute?

Round-3 findings:
- Severity loop vacuous when warns is empty — but the subsequent `contains()` asserts catch the zero-events case. The only genuine gap is a scanner that emits duplicates of a known token. That failure mode has no live instance and no intuitive path to introduce.
- No test for recognized-tokens-only → zero Warn events. Real gap, but not a regression of anything that currently works — the happy path is exercised by the three-token confirmation scene test already, and the lack of a Warn event in those passing tests IS the zero-case check (implicitly: if scanner wrongly emitted for known tokens, the OTEL tests would see those events and the `find_unrecognized_placeholder` action filter would catch an extra event the test didn't expect). Not airtight, but covered.
- `pub(crate)` visibility too wide — `find_unrecognized_tokens` is only called from `interpolate_scene_narration` in the same file. Narrowing to private is a one-character change. Real but cosmetic.
- Misleading comment at test line 153 — "carry a token field" promises a check the loop doesn't do (the token check is in the next block). Minor doc drift.
- Stale "old test" reference in comment at line 128 — describes replaced behavior, adjacent to Rule 18 territory but below the threshold.

A malicious user cannot exploit any of these. A confused user would not be misled about any invariant that changes code behavior. A stressed filesystem would not break the scanner. A malformed narration string is exercised by the unclosed-brace path which IS tested. The OTEL channel is sound.

The round-2 HIGH findings are demonstrably closed. Three independent subagents (silent-failure-hunter, rule-checker, preflight) returned clean or positive-confirmation results for the core fix. The remaining findings are across-the-grain quality improvements that can be swept into a follow-up without risk to 37-21's player-facing outcome.

Keith's playgroup does not see `pub(crate)`. Sebastien's mechanical-visibility lens sees the new per-token Warn events — which is a net improvement. Alex, reading the confirmation scene after character creation, now sees their character's name substituted in Space Opera narration. Heavy_metal gets the fix for free. That is the story as designed, and it's done.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** Genre-pack YAML (`space_opera/char_creation.yaml:240,243`) → `GenrePack` loader → `CharacterBuilder.scenes` → `to_scene_message()` (`builder.rs:1416`) → `interpolate_scene_narration(&scene.narration)` → `replace("{name}", ...).replace("{class}", ...).replace("{race}", ...)` → `find_unrecognized_tokens` post-scan → per-token Warn emission via `WatcherEventBuilder` → `CharacterCreationPayload.prompt` → WebSocket to client. Every hop has test coverage. The dispatch wiring test (`wiring_scene_message_payload_routes_through_interpolator`) asserts the full post-interpolation string byte-for-byte; a no-op interpolator cannot pass.

**Pattern observed:** Exhaustive byte-scanner with monotonically advancing index (`builder.rs:254-289`), matched against a closed set of known-good tokens. The pattern correctly handles closed braces, unclosed trailing braces, bare `{`, and `{}`. UTF-8 safety is reasoned about explicitly in the comment and verified by two independent subagents — ASCII bytes `0x7B`/`0x7D` cannot appear as UTF-8 continuation bytes, so byte-index boundaries always land on valid codepoint boundaries.

**Error handling:** Infallible by design — empty input passes the fast-path, absent optional state substitutes empty-string with OTEL Warn, unknown tokens surface per-token Warn events. No panics, no silent drops.

**Observed issues resolved across three rounds:**
- Round-1 rejection (clippy, fmt, vacuous wiring, story references, untested OTEL, bool-as-string) — all closed.
- Round-2 rejection (multi-token silent drop, OR-disjunct, drain sleep) — all closed.

**Handoff:** To Camina Drummer (SM) for finish-story ceremony.

## Delivery Findings (Round 3)

<!-- reviewer-approved follow-ups; not blocking 37-21 -->

### Reviewer (code review — round 3)

- **Improvement** (non-blocking): test `unrecognized_token_passes_through_and_fires_warn_event` could add `assert_eq!(warns.len(), 2, "expected exactly two Warn events, got: {warns:?}")` before the severity loop. Currently the severity loop is vacuously true when `warns` is empty, though the subsequent `tokens.contains()` assertions still fail correctly in that case. The uncovered hypothetical is a scanner that double-fires a known token.
  Affects `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs:~152`.
  *Found by Reviewer during round-3 code review. Flagged independently by reviewer-test-analyzer (HIGH) and reviewer-rule-checker (Rule 6).*

- **Improvement** (non-blocking): narrow `find_unrecognized_tokens` visibility from `pub(crate)` to file-private. Its correctness depends on the three-token whitelist staying in sync with the interpolator; only `interpolate_scene_narration` in the same file is a safe caller. Exposing it crate-wide invites future callers that won't update the whitelist.
  Affects `sidequest-api/crates/sidequest-game/src/builder.rs:254`.
  *Found by Reviewer during round-3 code review. Flagged by reviewer-type-design at medium confidence.*

- **Improvement** (non-blocking): rewrite misleading test comment that reads "Every warn must be Warn severity and carry a token field" — the loop only asserts severity; the token-field check happens in the subsequent block. Narrow to: "Every matched event must be Warn severity."
  Affects `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs:~153`.
  *Found by Reviewer during round-3 code review. Flagged by reviewer-comment-analyzer at high confidence.*

- **Improvement** (non-blocking): drop "first-only scan would satisfy the old test" phrasing at test line ~128 — describes replaced behavior in terms of what was previously wrong. Rewrite to state the invariant directly.
  Affects `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs:~128`.
  *Found by Reviewer during round-3 code review. Flagged by reviewer-comment-analyzer at medium confidence.*

- **Improvement** (non-blocking): add a negative test — narration containing ONLY recognized tokens (`"Hello {name}, the {class}."`) must emit zero `scene_narration_unrecognized_placeholder` events. Guards against a scanner regression that wrongly emits for known tokens.
  Affects `sidequest-api/crates/sidequest-game/tests/scene_narration_interpolation_story_37_21_tests.rs`.
  *Found by Reviewer during round-3 code review. Flagged by reviewer-test-analyzer at medium confidence.*

- **Question** (non-blocking): test-filename convention question — the `.rs` test files in `sidequest-api/crates/*/tests/` follow `<topic>_story_<N>_<M>_tests.rs` (50+ peer files). CLAUDE.md Rule 18 ("no task references in source") was flagged by rule-checker and comment-analyzer against these filenames in rounds 2 and 3. Reviewer dismissed in-context as established repo convention, but SM/PM should resolve the process question: should the convention change, or should Rule 18 be explicitly scoped to inline comments only? Not a 37-21 block either way.
  Affects `.pennyfarthing/gates/lang-review/rust.md` (Rule 18 scope clarification) and the entire `sidequest-api/crates/*/tests/` tree (if a rename is adopted).
  *Found by Reviewer across rounds 2 and 3. Process question, not a code fix.*

## Delivery Findings

<!-- append-only — do not edit prior agents' entries -->

### Dev (implementation)

- **Improvement** (non-blocking): heavy_metal's char_creation confirmation narration uses the same `{name}/{class}/{race}` interpolation pattern as space_opera (lines 248, 252). The 37-21 api fix makes these render correctly without content changes, but heavy_metal was not exercised in a playtest, so the visual outcome is unverified.
  Affects `sidequest-content/genre_packs/heavy_metal/char_creation.yaml` (verify via a heavy_metal chargen playtest, no code change required).
  *Found by Dev during implementation.*

- **Gap** (non-blocking): there is no author-facing validation that a genre pack's `char_creation.yaml` placeholders reference only `{name}/{class}/{race}`. A future pack author writing `{character}` or `{archetype}` will get silent empty-string substitution rather than a loud failure at validation time.
  Affects `sidequest-api/crates/sidequest-validate/` (add a char_creation placeholder audit pass that flags unknown tokens).
  *Found by Dev during implementation.*

### Reviewer (code review)

- **Gap** (non-blocking): `sidequest-telemetry`'s `emit()` silently drops WatcherEvents when no GM-panel subscriber is attached or when the global channel is uninitialized (`let _ = tx.send(event)`). This means any Warn severity event — including the new `chargen.StateTransition` unresolved-placeholder warning — is fire-and-forget with no stderr fallback. A telemetry-hardening story should add a Warn-severity-or-higher stderr fallback when the channel is empty or uninitialized.
  Affects `sidequest-api/crates/sidequest-telemetry/src/lib.rs:196` (add an eprintln! fallback in `emit()` for Severity::Warn and Severity::Error when `GLOBAL_TX` is None or send returns Err).
  *Found by Reviewer during code review.*

### Dev (rework)

- **Gap** (non-blocking): two unrelated test files in `sidequest-game` — `gm_commands_story_9_8_tests.rs` and `merchant_wiring_story_15_16_tests.rs` — have stale `Npc { ... }` struct literals missing 6 fields that have since been added (`jungian_id`, `non_transactional_interactions`, `npc_role_id`, and three others). Both files block `cargo clippy --all-targets -p sidequest-game` on this crate, surfaced during 37-21 rework. The 37-21 diff does not touch Npc or these files, but a near-term story should fix the drift so `--all-targets` is a usable gate.
  Affects `sidequest-api/crates/sidequest-game/tests/gm_commands_story_9_8_tests.rs:94` and `sidequest-api/crates/sidequest-game/tests/merchant_wiring_story_15_16_tests.rs:63` (update the Npc literals to include the six added fields, or switch to a test-fixture helper).
  *Found by Dev during 37-21 rework.*

- **Improvement** (non-blocking): the three chargen placeholder keys (`{name}`, `{class}`, `{race}`) are stringly-typed literals repeated six times in `interpolate_scene_narration`. A future expansion to `{location}` or `{faction}` will need to keep the detection guard and replacement chain in lockstep. A const-array of `(&str, fn(&CharacterBuilder) -> &str)` or a small enum with `key()` + `resolve()` would make the set authoritative at a single site.
  Affects `sidequest-api/crates/sidequest-game/src/builder.rs:486-548` (refactor when the next placeholder key is added).
  *Found by Reviewer during code review.*

## Design Deviations

### Dev (implementation)

- **Interpolation only runs on Scene-phase renders, not on `AwaitingFollowup.hook_prompt`.**
  - Spec source: session file SM Assessment, step 3 ("Trace the API-side render path to confirm which templating layer touches this scene").
  - Spec text: SM assessment did not specify whether `hook_prompt` (the `AwaitingFollowup` branch at `builder.rs:1375`) should also interpolate.
  - Implementation: Applied the interpolator only at the `BuilderPhase::InProgress` Scene branch (the one that renders `scene.narration`), not at the `AwaitingFollowup` branch (which renders `hook_prompt`).
  - Rationale: `hook_prompt` text is a static follow-up question like "Tell me about your past" that doesn't accept or require character-state substitution in any current genre pack. Applying the interpolator there would be speculative scope — it would change nothing today but would silently substitute any future author-added placeholder. I judged the smaller scope correct per minimalist-discipline. Trivial to extend later if a pack authors it.
  - Severity: minor
  - Forward impact: minor — if a future genre pack author adds `{name}` to a `hook_prompt`, it will render literally. The 37-21 OTEL watcher won't catch this because it fires only on the Scene branch. A follow-up story could extend the interpolator to the follow-up path and add a matching OTEL emission.

### Reviewer (audit)

- **Dev's deviation about `AwaitingFollowup` not calling the interpolator** → ✓ ACCEPTED by Reviewer: hook_prompt text is dynamically generated and does not currently carry placeholder syntax from any genre pack. Scoping the fix to the one real call-site is correct per minimalist-discipline. The deviation is properly logged with rationale and forward impact. Acceptable as-is.

- **Undocumented deviation flagged by Reviewer:** Dev Assessment claims "interpolate via str::replace — supports {name}, {class}, {race}" but does not document the **silent pass-through of any unrecognized curly-brace token** (e.g. `{origin}`, `{ship}`, `{}`, `{name` with no close). A genre author who typos a key name gets no error — the token renders literally with no OTEL signal. Severity: M. This is a No-Silent-Fallback rule concern, not merely a test gap. Add to the rework list (see Reviewer Assessment).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (clippy + fmt) | confirmed 2, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 2, dismissed 1, deferred 1 |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 3, dismissed 1, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Yes | findings | 4 | confirmed 1, dismissed 1, deferred 2 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (Rule 18 × 2) | confirmed 2, dismissed 0, deferred 0 |

**All received:** Yes (6 returned, 3 disabled per settings)
**Total findings:** 13 confirmed, 3 dismissed (with rationale), 3 deferred

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/rust.md` (15 rules) + CLAUDE.md additional rules (4). Cross-checked against rule-checker subagent's exhaustive pass.

| # | Rule | Instances | Result |
|---|------|-----------|--------|
| 1 | Silent error swallowing | 5 (`unwrap_or("")` ×3, `.expect()` ×2 in tests) | PASS — deliberate documented fallback with OTEL emission; test `.expect()` is integrity-assert. |
| 2 | Missing `#[non_exhaustive]` on public enums | 0 new enums | N/A |
| 3 | Hardcoded placeholder values | 4 (`""`, `"chargen"`, story refs ×2) | **FAIL on story refs** (see Rule 18 below); `""` is documented behavior, `"chargen"` is correct subsystem label. |
| 4 | Tracing coverage + correct severity | 3 (Warn branch, Info branch, no-error paths) | PASS — 4xx-style warn for unresolved, info for resolved, no error paths introduced. |
| 5 | Unvalidated constructors at trust boundaries | 0 new constructors | N/A |
| 6 | Test quality (vacuous/zero-assertion) | 4 tests | **FAIL** — `wiring_scene_message_payload_routes_through_interpolator` line 341 asserts `prompt.contains("playername=")` which is literally true of the UN-interpolated input (`"playername={name}"` contains `"playername="`). The wiring test is vacuous — would pass against a no-op interpolator. |
| 7 | `as` casts on user input | 2 (`scene_index as u32`, `scenes.len() as u32`) | PASS — pre-existing, builder-internal, bounded. |
| 8 | `#[derive(Deserialize)]` bypass | 0 | N/A |
| 9 | Public fields on types with invariants | 0 new structs | N/A |
| 10 | Tenant context in trait signatures | 0 | N/A (project has no tenant model) |
| 11 | Workspace deps | 0 Cargo.toml changes | N/A |
| 12 | Dev-only deps in `[dependencies]` | 0 Cargo.toml changes | N/A |
| 13 | Constructor/Deserialize validation consistency | 0 | N/A |
| 14 | Fix-introduced regressions | 1 (call-site change) | PASS on logic; Rule 18 violations carried forward. |
| 15 | Unbounded recursive/nested input | 1 (interpolate_scene_narration takes unbounded `&str`) | PASS — non-recursive, linear `str::replace`, input is bounded genre YAML. |
| 16 | OTEL for every subsystem fix (CLAUDE.md) | 1 | PASS — WatcherEvent emits `chargen.StateTransition` with resolved/missing fields. |
| 17 | No Silent Fallbacks (CLAUDE.md) | 2 (`unwrap_or("")` for knowns, `else` branch for unknowns) | **FAIL on unknown tokens** — `{origin}`/`{ship}`/typos pass through silently with no Warn; the guard only fires for the three known keys. |
| 18 | No task-reference comments (CLAUDE.md) | 2 (`builder.rs:493` "See story 37-21", test file `:1` "Story 37-21:") | **FAIL** — both flagged by comment-analyzer AND rule-checker independently. |
| 19 | No stubbing (CLAUDE.md) | 1 (interpolate_scene_narration) | PASS — fully implemented, no todo!/unimplemented!. |

**Applicable rule failures:** Rule 6 (vacuous wiring assertion), Rule 17 (silent unknown-token pass-through), Rule 18 (task references × 2).

## Devil's Advocate

I'm going to argue this code is broken. Consider a malicious or confused genre-pack author typos `{name}` as `{nmae}`. The interpolator's `had_name || had_class || had_race` guard is false, the early-return on line 511 fires, and the literal `{nmae}` reaches the client unchanged. The OTEL watcher — the supposed "lie detector" — says nothing, because the code never noticed. A future pack authoring `{origin}` (perfectly natural token name for a sci-fi pack) gets the same silent drop. That is exactly the No-Silent-Fallbacks failure mode CLAUDE.md warns against.

Consider a stressed reader of the wiring test. They see `assert!(prompt.contains("playername="))`. They assume this proves the interpolator fires. It does not. It would pass if `to_scene_message` forgot to call `interpolate_scene_narration` entirely, because the raw narration literally contains the substring `"playername="`. The "wiring test" — the single test that was supposed to prove the payload constructor routes through the interpolator per the project rule "Every Test Suite Needs a Wiring Test" — does not actually prove wiring. A future refactor that drops the call silently passes. This is the exact class of bug the project rule exists to prevent, and the test that was written to satisfy the rule has a hole in it.

Consider the OTEL event. It fires into `WatcherEventBuilder` which routes to `GLOBAL_TX.broadcast::Sender`. If no GM panel is subscribed (any non-server context, any test that doesn't install a watcher, any production run before the panel connects), `tx.send()` returns `Err(SendError)` and `let _ =` eats it. The Warn event described in the Dev Assessment as "the loud failure signal" is not loud — it is fire-and-forget into a potentially-empty channel. In tests, the emission is a complete no-op because `GLOBAL_TX` is never initialized.

Consider the OTEL payload itself. The `field_opt` pattern emits `name_resolved: Option<String>` where the string is literally `"true"` or `"false"`. A GM panel reader sees `name_resolved: "false"` and cannot distinguish "placeholder was in the template and was unresolved" from "field was not emitted at all." The telemetry that is supposed to be human-readable is encoded as booleans-as-strings inside Options.

Consider the doc comment. `/// See story 37-21.` This is literally the pattern CLAUDE.md forbids — "Don't reference the current task, fix, or callers ('used by X', 'added for the Y flow', 'handles the case from issue #123')." The module-level doc on the test file opens with `//! Story 37-21:`. Two independent subagents (comment-analyzer and rule-checker) flagged this. The project rule is explicit. This is not a judgment call.

Consider preflight. `cargo clippy -- -D warnings` — the standard gate — fails on three `clippy::unnecessary_lazy_evaluations` lints in the new code. `cargo fmt --check` fails on the new test file. These alone block CI and block the story from being merged. The Dev Assessment claimed "Full workspace `cargo build --workspace` succeeds" — which is true, but `build` is not `clippy -D warnings` and is not `fmt --check`. The assessment described the easier-to-pass gate.

This code is not ready. Six findings are confirmed by adversarial analysis; three of them are blocking.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `[RULE]` `cargo clippy -- -D warnings` fails — 3× `clippy::unnecessary_lazy_evaluations` | `builder.rs:524,528,532` | Replace `.then(\|\| !x.is_empty())` with `.then_some(!x.is_empty())` on all three `field_opt` calls |
| [HIGH] | `[RULE]` `cargo fmt --check` fails | test file line 190 (`assert_eq!` formatting); unrelated 37-15 test file drift also surfaces — fold both into the fmt pass | Run `cargo fmt -p sidequest-game` and commit |
| [HIGH] | `[TEST]` Vacuous wiring assertion — test passes against a no-op interpolator | `tests/scene_narration_interpolation_story_37_21_tests.rs:341` | Replace `assert!(prompt.contains("playername="))` with `assert_eq!(prompt, "classname=Spacer\|racename=Belt\|playername=")` so the test fails if interpolation does not run |
| [MEDIUM] | `[SILENT]` `[RULE]` Unknown curly-brace tokens silently pass through — `{origin}`, `{ship}`, typos render literally with no OTEL signal | `builder.rs:509-511` early-return after known-key guard | After the three known replacements, scan the rendered string for remaining `{` and emit a Warn WatcherEvent with the unrecognized substring. Violates CLAUDE.md No-Silent-Fallbacks |
| [MEDIUM] | `[DOC]` `[RULE]` Doc comment references story number | `builder.rs:493` `/// See story 37-21.` | Remove the sentence. The surrounding prose already explains the why |
| [MEDIUM] | `[DOC]` `[RULE]` Test module doc header references story number | `tests/scene_narration_interpolation_story_37_21_tests.rs:1-12` `//! Story 37-21:` + body references | Trim module doc to what/why/invariants. Remove story references. Consider renaming file to drop `_story_37_21` suffix (consistent with CLAUDE.md "don't reference current task"), though this is a larger convention change and should be confirmed with SM |
| [MEDIUM] | `[TEST]` OTEL emission is completely untested | `tests/scene_narration_interpolation_story_37_21_tests.rs` — 0 tests for `chargen.StateTransition` | Add a test that captures the WatcherEvent stream and asserts the event fires with `action=scene_narration_interpolated` and the correct `name_resolved`/`class_resolved`/`race_resolved` fields |
| [MEDIUM] | `[TYPE]` OTEL `field_opt` emits boolean-as-string inside Option — unreadable in GM panel | `builder.rs:520-533` | Emit two separate bool fields per key — `name_present: bool` and `name_resolved: bool` — so the GM panel can distinguish "placeholder was absent" from "placeholder present but unresolved" |
| [LOW] | `[DOC]` Misleading inline comment — claims to seed character_name but does not | `tests/scene_narration_interpolation_story_37_21_tests.rs:204` | Replace with accurate prose: "Name has not been entered yet; this call exercises class + race interpolation only. The empty-name case is the second test." |

**Deferred (not blocking this PR):**
- `[TYPE]` Stringly-typed three-key placeholder set repeated 6× — extract to a const array or enum when the set grows (currently 3 keys, future pack authors will want more; refactor with the next pack that authorizes new keys)
- `[SIMPLE]` `String` return could be `Cow<str>` for the no-placeholder fast path — low-priority, not a hot path
- `[SEC]` OTEL emit silent-drop when no subscriber or uninitialized channel — this is a telemetry-infrastructure concern in `sidequest-telemetry/src/lib.rs:196`, not a 37-21 problem. File as delivery finding for a telemetry-hardening story

**Dismissed with rationale:**
- `[SILENT]` `unwrap_or("")` for `name/class/race` on pre-name scenes — DISMISSED: intended, documented behavior per Dev Assessment. Empty-string substitution for a scene that renders before the name-entry scene is correct (see `missing_name_substitutes_empty_string_rather_than_leaking_literal` test). The OTEL Warn event records the miss.
- `[SILENT]` Double-brace `{{name}}` escaping not supported — DISMISSED: no genre pack uses this syntax. Not a regression. Add to escape-syntax story if ever needed.
- `[TYPE]` `NonBlank` newtype on narration param — DISMISSED: larger type-system convention change, out of scope for a 1-pt story. Correct destination is a follow-up story.
- `[TEST]` Negative wiring test (first-scene-no-leak) — DISMISSED: covered by `scene_without_placeholders_is_returned_verbatim`.
- `[TEST]` Multiple occurrences of same placeholder — DISMISSED: `str::replace` replaces all occurrences by stdlib contract; testing stdlib is not the project's job.

**Handoff:** Back to Naomi Nagata (Dev) for rework. The trivial workflow has no RED phase, so route via `green rework`.