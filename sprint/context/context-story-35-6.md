---
parent: context-epic-35.md
workflow: tdd
---

# Story 35-6: Wire guest_npc permission gating into dispatch pipeline

## Business Context

SideQuest supports a **social deduction multiplayer mode** (ADR-029) in which
one player joins the session not as a protagonist but as a consequential NPC —
"Marta the Innkeeper," say, or the suspicious stranger in the cantina. The
guest NPC sees the world from their character's perspective (motives, secrets,
hidden disposition), while the protagonist players see only visible behavior.
This asymmetric-information design is what makes guest-NPC mode compelling:
the guest is complicit in the narrative with the GM, not just another player.

**The mechanical constraint that makes the mode safe:** a guest NPC is
restricted to a small set of action categories — by default **Dialogue,
Movement, Examine** — so they cannot, for example, initiate combat against the
party on their first turn and tip the scenario. Restriction is the whole point
of the mode; without it, a guest NPC becomes a full player with extra lore.

**The wiring gap:** story 8-7 (merged long ago) shipped the `guest_npc` module
with `PlayerRole`, `ActionCategory`, `GuestNpcContext`, and
`validate_action()` all fully implemented and unit-tested. Story 35-6 is the
Epic 35 remediation pass: **nothing in the dispatch pipeline ever calls
`validate_action()`**. A guest player today is a full player with a different
narrator tag. The restriction is unenforced.

This is the canonical "built but unwired" pattern Epic 35 exists to close. The
entire receiving-end apparatus exists; the sending-end never calls it. Until
35-6 lands, the feature is a cosmetic label, not a gameplay constraint.

## Technical Guardrails

### Spec authority for this story

Per the spec hierarchy: **session scope > story context > epic context > ADRs**.

- **ADR-029 (Guest NPC Players)** is the design rationale. It is the authoritative
  source for "why" but says nothing about the dispatch insertion point — that is
  an implementation decision owned by this story.
- **ADR-010 (Intent routing)** and **ADR-067 (Unified narrator agent — no
  keyword matching)** are load-bearing for the "where does the gate go" question
  (see §Architectural decision required).
- The session file's SM Assessment is the top-level scope; the AC list there
  drives what must pass.

### The unwired module (receiving end — DO NOT modify)

`sidequest-api/crates/sidequest-game/src/guest_npc.rs` — **205 LOC, fully built,
zero production consumers** (verified: grep for `PlayerRole`/`GuestNpcContext`
returns only `lib.rs` re-export, `scenario.rs` unrelated type of the same name,
and the `guest_npc_story_8_7_tests.rs` test file).

Key types (already present — just use them):

| Type | Location | Purpose |
|---|---|---|
| `PlayerRole::{Full, GuestNpc { npc_name, allowed_actions }}` | `guest_npc.rs:14` | Per-player role tag |
| `ActionCategory` enum | `guest_npc.rs:59` | `Dialogue`, `Movement`, `Examine`, `Combat`, `Inventory` (`#[non_exhaustive]`) |
| `PlayerRole::can_perform(&ActionCategory)` | `guest_npc.rs:28` | Permission check |
| `PlayerRole::default_guest_actions()` | `guest_npc.rs:40` | Returns `{Dialogue, Movement, Examine}` |
| `GuestNpcContext::new(player_id, npc_name, allowed_actions)` | `guest_npc.rs:128` | Wraps role + metadata |
| `GuestNpcContext::validate_action(&ActionCategory)` | `guest_npc.rs:159` | Returns `Result<(), ActionError>` |
| `ActionError::RestrictedAction { category }` | `guest_npc.rs:76` | Typed rejection, `thiserror::Error` |

**All of these are `#[non_exhaustive]` and properly encapsulated. Do not add
fields, do not change signatures, do not re-derive traits.** This story is
integration, not modification of the receiving module.

### Where the PlayerRole needs to live (critical design question #1)

`PlayerRole` has **no home on the session today.** Verified:

- `MultiplayerSession` (`sidequest-game/src/multiplayer.rs:54`) stores
  `HashMap<String, Character>` — player_id → Character only. No role field.
- `PlayerState` (`sidequest-api/crates/sidequest-server/src/shared_session.rs:52`)
  has `player_name`, `session`, `builder`, `character_*`, `region_id`,
  `display_location`, `inventory` — no `role` field.
- The WebSocket connection handshake path in `dispatch/connect.rs` has no code
  that sets a PlayerRole. Guest-vs-full is currently an undefined concept at
  the server layer.

**Two reasonable places to put it:**

| Option | Pros | Cons |
|---|---|---|
| Add `role: PlayerRole` to `PlayerState` in `shared_session.rs` | Per-player state already lives here; server-layer concern stays at server layer | Requires threading role through `PlayerState::new()` and connect handshake |
| Change `MultiplayerSession` to store `HashMap<String, (Character, PlayerRole)>` | Co-locates role with character in the game crate | `MultiplayerSession` has two constructors (`new`, `with_player_ids`) plus `add_player`; all need role-aware signatures, and `TurnBarrier` uses `with_player_ids` where role makes no sense |

**Recommendation for Architect consultation:** `PlayerState.role` is the less
invasive choice. Barrier/multiplayer code doesn't care about role — only the
dispatch pipeline does. Keeping the role at the server layer (where dispatch
lives) respects crate boundaries.

**No silent fallback on missing role.** If `PlayerState.role` is `Option<PlayerRole>`
and `None`, the gate must either treat None as `PlayerRole::Full` **explicitly**
(documented contract) or panic. Do not quietly allow actions through when the
role is absent — that reintroduces the very bug this story closes.

Per CLAUDE.md and the `feedback_no_fallbacks.md` memory: **default to `Full`
explicitly with a `tracing::warn!` noting the missing role**, OR make the field
non-optional and require it at `PlayerState::new()` construction. The latter is
stronger but more invasive. Architect should choose.

### The intent-to-category mapping (critical design question #2)

The permission gate needs an `ActionCategory` to check. The dispatch pipeline
today has two things a gate could use:

1. **Raw action string** (`ctx.action: &str`) — available immediately on entry
   to `dispatch_player_action()`. **Cannot be mapped to `ActionCategory`
   without an LLM or keyword matching.** Keyword matching is explicitly
   forbidden by `feedback_no_keyword_matching.md`: "Pattern matching fails on
   natural language; use LLM only (Zork Problem)."
2. **`classified_intent: Option<String>`** — set by
   `game_service().process_action()` at `dispatch/mod.rs:787-794`. **Available
   only AFTER the full narrator LLM call completes.** Values come from
   `sidequest_agents::agents::intent_router::Intent`: `Combat | Dialogue |
   Exploration | Examine | Meta | Chase | Backstory | Accusation`.

**The `Intent` and `ActionCategory` enums were designed independently and do
not line up 1:1:**

| `Intent` variant | `ActionCategory` equivalent | Notes |
|---|---|---|
| `Combat` | `Combat` | Direct |
| `Dialogue` | `Dialogue` | Direct |
| `Examine` | `Examine` | Direct |
| `Exploration` | `Movement` | Rename gap — closest match |
| `Chase` | `Combat` or `Movement`? | Ambiguous. Chase sequences mix fleeing (movement) and pursuit (combat-adjacent). **Design decision required.** |
| `Accusation` | `Dialogue`? | Accusations are spoken, but socially they are more "gameplay action" than dialogue. |
| `Meta` | *none — /commands* | Meta is slash-commands (/save, /status). Should bypass the gate entirely (not a roleplayed action). |
| `Backstory` | *none — character establishment* | Not a turn action. Should bypass the gate. |
| — | `Inventory` | No corresponding `Intent` variant. Inventory is inferred from `result.action_flags.references_inventory`, not classified. |

**This is the load-bearing design decision for 35-6.** Options:

- **Option A — Post-LLM gate**: Gate runs AFTER `process_action()` at
  ~`dispatch/mod.rs:794`, maps `classified_intent` → `ActionCategory`, calls
  `validate_action()`, and if denied, **aborts the turn before state mutation
  and narration broadcast**. Cost: a full LLM call per denied action. Benefit:
  uses the existing LLM-backed classifier with no new code paths.
- **Option B — Pre-LLM fast classifier**: Run a cheap pre-classifier (Haiku
  call or deterministic LLM prompt) to get an `ActionCategory` before
  `process_action()`. Gate blocks before the expensive narrator call. Cost:
  extra LLM round-trip per turn (even for allowed actions). Benefit: denied
  actions are cheap.
- **Option C — Client-side advisory + server-side enforcement**: Client UI
  disables restricted-action affordances for guest NPCs (prevents most
  attempts); server still enforces post-LLM as a safety net. Cost: UI work
  out of scope for 35-6. Benefit: best user experience, but requires UI story.

**Recommendation for Architect consultation:** **Option A (post-LLM gate)**
for this story, with a Delivery Finding flagging Option C as a future UX
improvement. Rationale:
- Denied actions are rare in practice (guest UX will self-select away from
  Combat once they see narrator pushback)
- Post-LLM gating uses the existing classifier — no new LLM calls
- Keeps the story scope tight (dispatch only, no UI, no new agent)
- The intent classifier is already proven and maintained

**The mapping function itself** should live in `sidequest-server/src/dispatch/`
(e.g., `guest_gate.rs`) or directly in `dispatch/mod.rs`. It must:
- Be exhaustive over the `Intent` enum (not `#[non_exhaustive]` — enforced at
  compile time via exhaustive match)
- Map `Meta`/`Backstory` to "bypass gate entirely" — not a `None`, but an
  explicit `GateDecision::Bypass` variant or equivalent
- Make `Chase` and `Accusation` explicit design choices (not silently mapped)
- Panic loudly if `classified_intent` is `None` *and* the player is a guest
  (violates "no silent fallback" — a guest action must be classifiable or the
  gate is unsafe)

### Where the gate physically goes in dispatch

Entry point: `dispatch_player_action()` at
`sidequest-server/src/dispatch/mod.rs:191`. The hot path through this function
(partial — verified against the 3,022 LOC file):

```
dispatch_player_action(ctx) {                            // :191
    tracing::info_span!("turn")                          // :192
    sync_to_locals / sync_player_to_locals               // :203-223
    WatcherEvent("multiplayer", AgentSpanOpen)           // :226 (multiplayer only)
    before_snapshot = delta::snapshot(ctx.snapshot)      // :237
    WatcherEvent("game", AgentSpanOpen) [action, player] // :251 ← "action received"
    THINKING sent to player                              // :262
    prev-turn inventory extraction                       // :280
    ...
    result = game_service.process_action(...)            // :787 ← LLM call
    turn_span.record("intent", ...)                      // :793
    engagement counter update                            // :802
    WatcherEvent("agent", AgentSpanClose)                // :842
    ...state mutations, render, broadcast...
}
```

**Insertion point for Option A (post-LLM gate):** immediately after
`turn_span.record("intent", ...)` at line 794, **before** the engagement
counter update at line 803. That means:

1. LLM has classified the action → `result.classified_intent` is set
2. Gate maps intent → `ActionCategory`
3. Gate calls `player_state.role.can_perform(&category)`
4. If `Ok`: continue as normal (engagement counter, state mutations, broadcast)
5. If `Err(RestrictedAction)`:
   - Emit `WatcherEvent("guest_npc", ValidationWarning)` with
     `action`, `category`, `player_id`, `npc_name` fields
   - Send a `NarrationEnd` / `RestrictedAction` error message to the player
     (use existing error message shape — do not invent a new protocol message)
   - **Return early from `dispatch_player_action` BEFORE state mutations**
   - **Do not broadcast narration to other players**
   - **Do not advance the turn counter** (guest gets another chance to submit
     a valid action — barrier stays open for their slot)

**Important subtlety:** because we've already paid the LLM cost, the
narration *has been generated* but must be discarded. The narrator may have
written a pleasing "Marta rips out her dagger and lunges at the sheriff" —
that narration must NOT be shown to any player, because the gate rejected
the action. This is the correct behavior even though it feels wasteful: we
do not want the guest to learn "if I attempt Combat, the narrator still
describes it happening."

### OTEL requirements

Per `CLAUDE.md`'s OTEL Observability Principle and the Epic 35 per-story
checklist, every subsystem decision must emit a `WatcherEvent` so the GM panel
can see it happening.

**Required events for 35-6:**

1. **Gate pass** (per turn, guest NPC only) —
   `WatcherEventBuilder::new("guest_npc", SubsystemExerciseSummary)` with
   `.field("decision", "allowed")`, `.field("player_id", ...)`,
   `.field("npc_name", ...)`, `.field("category", "Dialogue")`. Emitted on
   every allowed action, **not** for Full players (noise).
2. **Gate deny** (per turn, guest NPC only) —
   `WatcherEventBuilder::new("guest_npc", ValidationWarning)` with
   `.field("decision", "denied")`, `.field("player_id", ...)`,
   `.field("npc_name", ...)`, `.field("category", "Combat")`,
   `.field("action_raw", truncated_action)`. ValidationWarning is the correct
   event type for "the system caught a bad input" (matches the pattern used
   for `dispatch/audio.rs:296` SFX validation warnings).
3. **Gate bypass** — for `Meta` and `Backstory` intents on guest NPCs,
   optional debug-level tracing; no `WatcherEvent` needed (non-decisions).

The GM panel must be able to answer: "did the permission gate run on this
turn, and what did it decide?" Without these events, Claude can describe
restriction in the narration with zero mechanical backing — the exact failure
mode Epic 35 exists to close.

### The mandatory wiring test

Per `CLAUDE.md` — "Every Test Suite Needs a Wiring Test" — the story must ship
an integration test that:

1. Sets up a `SharedGameSession` with two `PlayerState`s: one `Full`, one
   `GuestNpc` with `{Dialogue, Movement, Examine}`.
2. Calls `dispatch_player_action()` via a real `DispatchContext`, not a unit
   harness around the gate function alone.
3. Submits a guest action that classifies as `Combat`.
4. Asserts:
   - The gate denies the action
   - A `RestrictedAction` error is delivered to the guest player (not
     broadcast)
   - No narration is broadcast to the `Full` player
   - A `WatcherEvent("guest_npc", ValidationWarning)` was emitted
   - The turn counter did NOT advance
   - `ctx.snapshot` is unchanged (no state mutations)
5. Submits a guest action that classifies as `Dialogue`.
6. Asserts:
   - The gate permits the action
   - Narration is broadcast normally
   - A `WatcherEvent("guest_npc", SubsystemExerciseSummary)` with
     `decision=allowed` was emitted
   - The turn counter advances

**This is the "new code has non-test consumers" check** — prove that the gate
is actually on the hot path of `dispatch_player_action`, not just reachable
from a unit-test-only function.

### Test LLM hygiene

Per `feedback_no_live_llm_tests.md`: the integration test MUST NOT call
`claude -p`. The integration test needs a mocked `process_action()` that
returns a predetermined `classified_intent` (`"Combat"` for the denial case,
`"Dialogue"` for the allow case) without touching the narrator. Check
`sidequest-agents` for existing test fixtures — there are likely mock
`GameService` / `ClaudeClient` patterns already in use by barrier tests.

## Scope Boundaries

### In scope

- Add a `role: PlayerRole` field somewhere on the server-side per-player state
  (likely `PlayerState` in `shared_session.rs` — see §critical design question #1).
- Thread the role through `connect.rs` so a WebSocket client can join as a
  guest NPC. (The handshake message shape may need a new optional field; if
  so, that is a protocol change — flag it as a design deviation and document
  in the session.)
- Create an `Intent → ActionCategory` mapping function (likely in a new
  `dispatch/guest_gate.rs` submodule) with an exhaustive match.
- Insert the permission gate at `dispatch_player_action` post-LLM classification
  (see §Where the gate physically goes).
- Emit `WatcherEvent` for gate allow/deny decisions (see §OTEL requirements).
- Send a `RestrictedAction` error message to the guest player on denial
  (reuse existing error message shape — do not invent a new protocol variant
  unless unavoidable).
- Abort the turn cleanly on denial: no state mutations, no broadcast, no
  turn counter advance.
- Integration test in `sidequest-server` per §The mandatory wiring test.
- Unit test for the `Intent → ActionCategory` mapping function, including
  each of the 8 Intent variants.

### Out of scope

- **Modifying `guest_npc.rs`.** The module is fully built. Do not add methods,
  change variants, or re-derive traits.
- **Unifying `Intent` and `ActionCategory` into one enum.** Logged as a
  Delivery Finding (Improvement, non-blocking) — a future story can consolidate.
- **Client-side UI for guest-vs-full role selection.** Server-side enforcement
  ships first; UI affordances come in a separate story.
- **Per-guest custom allowed-actions (non-default).** 35-6 uses
  `PlayerRole::default_guest_actions()` only. Custom action sets per guest are
  a later feature — the data model supports it (`HashSet<ActionCategory>`),
  but there's no configuration path yet.
- **Narrator-prompt injection of the `NarratorTag`.** `GuestNpcContext::narrator_tag()`
  and `NarratorTag::to_prompt_string()` exist (guest_npc.rs:96-114). Wiring
  those into `dispatch/prompt.rs` is a **separate wire** — log as a Delivery
  Finding (Gap, non-blocking). 35-6 is strictly about the permission gate.
- **Inverted `PerceptionRewriter` for guest NPCs.** ADR-029 calls for this,
  but `perception.rs` is a PARTIAL module (per `sidequest-game/CLAUDE.md`).
  Out of scope; not a prerequisite for the gate.
- **Disposition merging** (`GuestNpcContext::merge_disposition`). Fully built,
  zero consumers. Separate future wiring story.
- **Barrier-level rejection.** Rejecting at the barrier (before `submit_action`)
  would be cheaper but requires the barrier to know `ActionCategory`, which
  requires intent classification upstream. Out of scope for this story —
  post-LLM gate is the shipping target.

## AC Context

Acceptance criteria restated from the SM assessment, with testable detail.

### AC-1: Guest NPC with allowed action → passes

- **Why it matters**: The default case for a guest NPC. Must not regress —
  Dialogue, Movement, and Examine actions must flow through unchanged except
  for the added WatcherEvent emission.
- **Verification**: Integration test submits a guest action classified as
  `Dialogue` (mocked) and asserts:
  - `dispatch_player_action` returns normally
  - Narration is broadcast
  - `WatcherEvent("guest_npc", SubsystemExerciseSummary)` with
    `decision=allowed` and `category=Dialogue` is captured
  - Turn counter advances
- **Watch out for**: The allowed-path test is the regression guardrail. A
  test that only covers denial can pass while the gate silently blocks
  everything.

### AC-2: Guest NPC with disallowed action → `ActionError::RestrictedAction`

- **Why it matters**: The whole point of the story. A guest NPC attempting
  Combat (or any non-default category) must be rejected before state mutation
  and broadcast.
- **Verification**: Integration test submits a guest action classified as
  `Combat` (mocked) and asserts:
  - A `RestrictedAction`-shaped error message is sent to the guest player
  - No narration broadcast to any other player
  - `ctx.snapshot` is byte-identical to pre-dispatch state
  - Turn counter does not advance
  - `WatcherEvent("guest_npc", ValidationWarning)` with `decision=denied`
    and `category=Combat` is captured
- **Watch out for**: Vacuous assertions. `assert!(result.is_err())` is not
  enough — the error must specifically be `ActionError::RestrictedAction`
  (or its wire-protocol equivalent), and the side-effect absence must be
  checked positively (snapshot equality, no broadcast).

### AC-3: Full player → unaffected

- **Why it matters**: The gate must be a no-op for `PlayerRole::Full`. A
  regression here would affect every current session, not just multiplayer.
- **Verification**: Integration test submits a Full player's action
  classified as `Combat` (which would be denied if they were a guest) and
  asserts:
  - Narration broadcast proceeds normally
  - Turn advances
  - NO `WatcherEvent("guest_npc", ...)` is emitted — Full players should
    not pollute the guest-npc watcher channel
  - All existing state mutations run
- **Watch out for**: Do not "check if guest then skip" — use
  `role.can_perform()` which returns `true` for `Full` unconditionally. This
  keeps the code path uniform and makes future role additions (e.g.,
  spectator) easier.

### AC-4: End-to-end integration test proves the gate is on the hot path

- **Why it matters**: The Epic 35 wiring rule. Unit tests on the gate
  function alone are insufficient — Epic 16-1 (the kitchen-sink wiring gate
  failure in memory `feedback_wiring_gate_failure.md`) proved that passing
  unit tests with zero production consumers is the exact pattern this epic
  exists to close.
- **Verification**: The wiring test must exercise
  `dispatch_player_action()` directly (or a close wrapper that calls it),
  not the gate function in isolation. Grep after implementation:
  `rg -n "validate_action|can_perform" sidequest-server/src/` must return
  the gate call site — and it must be inside the dispatch hot path, not a
  helper function with no callers.
- **Watch out for**: "Wiring test" that actually imports the gate function
  and calls it directly. That is still a unit test — rename it and add a
  real integration test. The check is: does a request entering the server
  at the `dispatch_player_action` seam actually reach the gate?

### AC-5: OTEL watcher events for allow/deny

- **Why it matters**: The GM panel is the lie detector. Without
  `WatcherEvent` emission, you cannot tell whether the gate ran or whether
  Claude is describing restriction with zero mechanical backing.
- **Verification**: The integration test subscribes to the watcher event
  stream BEFORE triggering dispatch, then asserts:
  - Allow path emits `("guest_npc", SubsystemExerciseSummary)` with
    `decision=allowed`
  - Deny path emits `("guest_npc", ValidationWarning)` with `decision=denied`
  - Full-player path emits NO `guest_npc` events
  - Event fields include `player_id`, `npc_name` (for guest), `category`,
    and for denials, a truncated `action_raw` for debugging
- **Watch out for**: `WatcherEventBuilder::send()` is fire-and-forget. The
  test must subscribe before triggering dispatch, not after. See
  `dispatch/audio.rs:296` for the existing emission pattern.

### AC-6: No silent fallback on unclassified guest action

- **Why it matters**: CLAUDE.md rule. If the intent classifier returns
  `None` for a guest NPC, the gate must panic (or return a loud error) —
  NOT default to "allow." Silent fallback would reintroduce the exact bug
  this story closes.
- **Verification**: Unit test on the mapping function: when called with
  `classified_intent: None` and `PlayerRole::GuestNpc { .. }`, the function
  must return `Err(GateError::UnclassifiedGuestAction)` (or equivalent) —
  not `Ok(Bypass)` and not a default category.
- **Watch out for**: The Full-player path should handle `None` gracefully
  (intent classification failure is a pre-existing soft failure for full
  players and doesn't need to become a hard error). Only the guest path
  must hard-fail.

## Assumptions

- **The Intent classifier is reliable enough.** `process_action()`'s
  `classified_intent` is the canonical source of truth for action category.
  If it returns `"Combat"`, we treat the action as Combat. If that mapping is
  wrong (false positive), the guest has a legitimate grievance — but the fix
  is better classification, not a weaker gate.
- **Guest NPCs are a rare configuration.** The code path for Full players is
  the hot path and must not regress in latency. The guest-only gate branch
  can afford a tiny amount of extra work (WatcherEvent emission) because it
  applies only when role is `GuestNpc`.
- **No existing tests exercise the unwired `guest_npc` module in integration.**
  The only tests are `tests/guest_npc_story_8_7_tests.rs` which unit-test the
  module in isolation. 35-6 must add integration tests alongside the new
  wiring code — do not pretend the old unit tests count as integration
  coverage.
- **`sidequest-server` tests can construct a `DispatchContext` in isolation.**
  If they cannot (e.g., the context requires a real `AppState` with live
  genre loaders), flag as a blocking Delivery Finding and escalate to
  Architect — the test shape may need a `DispatchContext::for_testing()`
  helper. Check existing dispatch tests (e.g., barrier tests) for the
  established pattern before inventing a new one.
- **Client protocol can carry a "join as guest NPC" signal today.** If the
  connect handshake message has no field for this, 35-6 may need a protocol
  change. Verify early — if the protocol doesn't support joining as a guest
  at all, the scope of 35-6 expands and this is a blocking Delivery Finding
  for Architect/BA. (Quick check: grep for `role` or `guest` in
  `sidequest-protocol/src/` before writing tests.)
