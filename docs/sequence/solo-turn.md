# Solo Sealed Action Turn — Sequence

One complete action turn in **solo play**. The "sealed-letter" barrier stage
is architecturally present on every turn but collapses to a no-op when only
one player is in the session. See [`multiplayer-sealed-turn.md`](./multiplayer-sealed-turn.md)
(TBD) for the full sealed-envelope variant.

## Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Player
    participant UI as UI (React)<br/>App.tsx / InputBar
    participant WS as WebSocket
    participant Reader as Server Reader<br/>handle_ws_connection
    participant Disp as dispatch_player_action<br/>(dispatch/mod.rs)
    participant Narr as Narrator<br/>(claude -p subprocess)
    participant Writer as Writer Task<br/>(mpsc + broadcast)
    participant Watcher as OTEL Watcher

    Player->>UI: Types action, presses Enter
    Note over UI: handleSend(text, aside=false)<br/>optimistic: push PLAYER_ACTION into messages<br/>setCanType(false) — input locked
    UI->>WS: PLAYER_ACTION { action, aside:false }
    WS->>Reader: serde parse → dispatch_message
    Reader->>Disp: dispatch_player_action(ctx)

    Note over Disp: turn span opens<br/>turn_number = ctx.turn_manager.interaction()
    Disp->>Watcher: game / AgentSpanOpen { action, player, turn }

    Disp->>Writer: THINKING (eager, pre-LLM)
    Writer-->>WS: THINKING
    WS-->>UI: THINKING
    Note over UI: setThinking(true)

    Note over Disp: Two-pass inventory extractor<br/>classifies PREVIOUS turn's narration:<br/>Acquired / Consumed / Sold / Given / Lost / Destroyed<br/>→ mutates ctx.inventory before prompt build
    Note over Disp: Scenario between-turn processing:<br/>NPC autonomous actions, gossip spread,<br/>clue discovery, pressure & escalation beats<br/>→ appended to state_summary
    Note over Disp: build_prompt_context (state_summary)<br/>+ Monster Manual NPC/encounter injection

    rect rgba(180,180,180,0.15)
    Note over Disp: barrier::handle_barrier → None<br/>(no turn_barrier in solo —<br/>sealed-letter stage is skipped)
    end

    Disp->>Narr: GameService.process_action(you, context)
    Note over Narr: claude -p subprocess<br/>narrator agent (unified, ADR-067)
    Narr-->>Disp: ActionResult {<br/>narration, footnotes, location,<br/>items_gained, sfx_triggers,<br/>classified_intent, agent_name,<br/>action_rewrite, action_flags }

    Disp->>Watcher: agent / AgentSpanClose<br/>{ narration_len, intent, agent, tokens }
    Disp->>Watcher: prompt / PromptAssembled { zones, tokens }

    Note over Disp: State mutations (ctx-local):<br/>• extract_location_header → room transition<br/>• items_gained → inventory<br/>• trope tick → beats fired<br/>• turn_manager.record_interaction<br/>• scene_count increment

    Disp->>Writer: NARRATION { text, state_delta, footnotes }
    Writer-->>WS: NARRATION
    WS-->>UI: NARRATION
    Note over UI: setThinking(false)<br/>append NARRATION to messages<br/>⚠ canType NOT restored here —<br/>input stays locked (observed bug)

    Disp->>Writer: NARRATION_END
    Writer-->>WS: NARRATION_END
    WS-->>UI: NARRATION_END
    Note over UI: narrativeSegments inserts a<br/>separator — splits history from<br/>current-turn block

    Disp->>Writer: PARTY_STATUS { members[], resources }
    Writer-->>WS: PARTY_STATUS
    WS-->>UI: PARTY_STATUS
    Note over UI: setPartyMembers; fan out<br/>local slice → characterSheet, inventoryData

    opt Location changed
        Disp->>Writer: CHAPTER_MARKER { location }
        Writer-->>UI: CHAPTER_MARKER
    end
    opt New render queued
        Disp->>Writer: IMAGE { url, render_id, tier }
        Writer-->>UI: IMAGE (routed to gallery via ImageBus)
    end
    opt Map state changed
        Disp->>Writer: MAP_UPDATE
        Writer-->>UI: MAP_UPDATE
    end
    opt Item depleted
        Disp->>Writer: ITEM_DEPLETED { item_name, remaining_before }
        Writer-->>UI: ITEM_DEPLETED
    end

    Note over Disp: delta = compute_delta(before, after)<br/>broadcast_state_changes(delta) →<br/>typed messages per changed field<br/>(characters / npcs / quest_log / atmosphere / regions / tropes)
    Disp->>Writer: (typed state-change messages)
    Writer-->>UI: state-change broadcast
    Note over UI: useStateMirror processes<br/>state_delta into GameStateProvider

    Note over Disp: persistence::persist_game_state<br/>(SQLite save, async)
    Disp->>Watcher: TurnRecord (ADR-073)<br/>snapshot_before/after, patches, delta,<br/>intent, narration, tokens
```

## Code path reference

| Step | File | Lines |
|---|---|---|
| UI `handleSend` | `sidequest-ui/src/App.tsx` | 467-498 |
| WebSocket reader/writer loop | `sidequest-api/crates/sidequest-server/src/lib.rs` | 916-1032 (writer), 1085-1200 (reader) |
| Dispatch entry | `sidequest-api/crates/sidequest-server/src/lib.rs` → `dispatch/mod.rs` | 1926 → 201 |
| `THINKING` eager send | `dispatch/mod.rs` | 275-288 |
| Two-pass inventory extractor | `dispatch/mod.rs` | 292-490 |
| Scenario between-turn | `dispatch/mod.rs` | 568-682 |
| Barrier (no-op solo) | `dispatch/barrier.rs` | 57-234 |
| Narrator call | `dispatch/mod.rs` (via `GameService.process_action`) | 855-858 |
| Response build (`NARRATION` / `NARRATION_END` / `PARTY_STATUS`) | `dispatch/response.rs` | 49-180 |
| Delta broadcast | `dispatch/mod.rs` | 1857-1892 |
| `TurnRecord` → OTEL | `dispatch/mod.rs` | 1906-1932 |
| Client message handler | `sidequest-ui/src/App.tsx` | 198-410 |
| Narrative segment build | `sidequest-ui/src/lib/narrativeSegments.ts` | 41-163 |

## Solo vs. sealed-letter multiplayer

Three things collapse to no-ops when only one player is in the session:

1. **No barrier wait.** `handle_barrier` returns `None` because
   `shared_session.turn_barrier` is never installed for a single player.
2. **No `TurnStatus("submitted")` broadcast.** The "sealed the envelope"
   event (`dispatch/barrier.rs:75-84`) is gated on barrier existence.
3. **No `ActionReveal`.** The reveal message is part of the barrier
   resolution path only.

So in solo, a turn is:

```
PLAYER_ACTION → THINKING → narrator → NARRATION → NARRATION_END
              → PARTY_STATUS (+ CHAPTER_MARKER / IMAGE / MAP_UPDATE / ITEM_DEPLETED)
              → typed state-change messages
```

The seal / wait / reveal ceremony only exists to keep multiplayer players
in sync and to preserve simultaneous-resolution fairness.

## Message fan-out paths

Two different fan-out paths feed the same writer task:

- **Per-connection mpsc** (`ctx.tx.send(...)`) — targeted at one player.
  Used for `NARRATION`, `NARRATION_END`, and any response tied to the
  acting player. See `lib.rs:922` (channel) and `lib.rs:958-968`
  (writer receive).
- **Global broadcast channel** (`state.broadcast(...)`) — fanned out to
  every connected WS writer. Used for world-level events like
  `ActionReveal` and typed state-change broadcasts. See `lib.rs:926`
  (subscribe) and `lib.rs:970-981` (writer receive).
- **Session broadcast** (`ss.broadcast(...)`) — scoped to players in the
  same genre:world session, with optional per-player targeting. Used for
  multiplayer session events. See `lib.rs:985-1028` (writer receive).

All three feed the same `ws_sink.send(...)` at the bottom of the writer
`tokio::select!` loop.
