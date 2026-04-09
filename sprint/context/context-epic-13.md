# Epic 13: Sealed Letter Turn System — Simultaneous Blind Submission with Initiative Resolution

## Overview

The current multiplayer turn system is fundamentally sequential: one player acts, everyone
watches, then whoever types fastest goes next. This destroys three properties that make
multiplayer RPGs work:

1. **Asymmetric information is impossible** — everyone sees every action and result in real time
2. **Initiative is fake** — whoever types first drives the narrative, not stats or encounter context
3. **One player dominates** — the fast typist is the de facto protagonist

The sealed letter pattern fixes all three: all players compose actions simultaneously and
blindly (no one sees what others chose), the server collects all actions, then submits them
in a single narrator call. The AI narrator — which is the GM, there is no human GM —
resolves initiative based on encounter type and relevant stats, and produces one synthesized
scene. The perception rewriter (ADR-028, already working) splits per-player views if needed.

**Target: playable by 2026-04-13 playtest.** Flaky edges acceptable; reboot-as-escape-hatch
is fine. The core loop must work: blind submit → collect → one narrator call → synthesized scene.

## Design Principles

- **The AI is the GM.** There is no human DM. No DM override commands. No DM force-resolve.
  The GM panel is a developer diagnostic tool (OTEL telemetry), not a gameplay role.
- **One prompt per round, not one per player.** The AI DM gets asked one question at a time.
  N player actions → one narrator call → one synthesized scene.
- **Initiative is narrator-decided, stat-informed, encounter-dependent.** The narrator receives
  all actions (unordered, no submission-time bias), the encounter type, and each player's
  relevant stats. It decides resolution order. Different encounters weight different stats:
  combat → DEX, chase → speed/agility, social → CHA, trials → genre-specific.
- **No timeout.** The round waits for all connected players. If someone crashes, the developer
  reboots the server. Disconnect detection and auto-resolve are deferred.
- **Stats must mean something.** Initiative mapping is the first mechanical system where stats
  have concrete gameplay impact beyond HP calculation.

## Background

### What Already Exists (from Epic 8 + stories 13-1 through 13-5, 13-8 through 13-10)

| Component | Status | File |
|-----------|--------|------|
| **MultiplayerSession** | Built, disabled | `sidequest-game/src/multiplayer.rs` |
| **TurnBarrier** | Built, disabled | `sidequest-game/src/barrier.rs` |
| **TurnMode** (FreePlay/Structured/Cinematic) | Built, disabled | `sidequest-game/src/turn_mode.rs` |
| **ActionReveal** protocol message | Defined | `sidequest-protocol/src/message.rs` |
| **TurnStatusPanel** UI | Built | `sidequest-ui/src/components/TurnStatusPanel.tsx` |
| **TurnModeIndicator** UI | Built | `sidequest-ui/src/components/TurnModeIndicator.tsx` |
| **SharedGameSession** with broadcast | Working | `sidequest-server/src/shared_session.rs` |
| **Claim election** (atomic CAS) | Built | `barrier.rs` — one handler dispatches, others wait |
| **Adaptive timeout** | Built, needs removal | `barrier.rs` — currently 3-5s, must be removed |
| **Perception rewriter** (ADR-028) | **Working** | Verified session 8 playtest — per-player narration |

All infrastructure stories (13-1 through 13-5, 13-8 through 13-10) are "done" meaning code
exists, but the barrier is disabled at runtime. `should_use_barrier()` returns false in
FreePlay, and the FSM transition to Structured/Cinematic is commented out.

### Playtest Evidence

**Session 8 (2026-03-29):**
> "One player will take their turn. It will then lock for everybody until the narrator comes
> back and then it's a free-for-all. Whoever wants to type in first gets the narrator again,
> everybody else has to wait."

**Session 9 (2026-04-09):**
> Unlike a human DM, an AI DM gets asked one question at a time. So either we can ask one
> question per player that the AI has to respond to, or we can ask one question per turn.

> I find the mechanic of "player one has initiative, therefore player two gets to react to
> what they're doing" — bullshit. In practice, one person is driving all the action.

### Python Reference

sq-2's turn manager implemented sealed letter with `collect_actions()` → `compose_party_actions()`
→ `TurnSummary` reveal → single narrator call. The Rust infrastructure mirrors this but never
got activated.

## Technical Architecture

### The Sealed-Letter Turn Loop

```
1. Narrator presents the scene → broadcast to all players
2. ALL players compose actions simultaneously (blind to each other)
3. Player panel shows who's submitted (sealed indicator per player)
4. Once ALL connected players submit → actions stashed server-side
5. Server sends all actions + encounter type + stats to narrator (ONE call)
6. Narrator resolves initiative order based on encounter + stats
7. Narrator produces one synthesized scene
8. Perception rewriter splits per-player views if needed (ADR-028)
9. Scene broadcast → back to step 2
```

### Initiative Resolution

The narrator receives:
- All N player actions (unordered — no submission-order bias)
- The current encounter type (combat, chase, social, trial, exploration, etc.)
- Each player's relevant stats for that encounter type
- Instruction: determine initiative order, resolve actions in that order

The initiative mapping lives in the genre pack YAML:

```yaml
# genre_packs/<genre>/rules.yaml (or initiative.yaml)
initiative_rules:
  combat:
    primary_stat: DEX
    description: "Reflexes and speed determine who strikes first"
  chase:
    primary_stat: DEX
    description: "Agility and footwork set the pace"
  social:
    primary_stat: CHA
    description: "Force of personality controls the conversation"
  trial:
    primary_stat: WIS
    description: "Judgment and perception guide the defense"
  exploration:
    primary_stat: WIS
    description: "Awareness determines who notices things first"
```

Each genre defines its own encounter types and stat weights. The narrator uses these as
guidance, not rigid formulas — it makes the final call.

### Protocol Messages (existing, need activation)

```rust
// Already defined — needs to be broadcast when barrier resolves
ActionReveal {
    actions: Vec<PlayerActionEntry>,  // character_name + action_text
    turn_number: u64,
    auto_resolved: Vec<String>,       // empty for MVP (no timeout)
}
```

`DmTurnControl` message type is **deleted** — no human GM, no force-resolve.

### Key Changes to Existing Code

**`TurnBarrier` (barrier.rs):**
- Remove adaptive timeout — `wait_for_turn()` waits indefinitely for barrier
- On WebSocket disconnect, remove player from the round's expected set

**`TurnMode` (turn_mode.rs):**
- `should_use_barrier()` returns true when multiplayer (>1 connected player)
- Or: always use Structured mode for multiplayer sessions

**`dispatch_player_action()` (dispatch/mod.rs):**
- In barrier mode: submit action → broadcast TURN_STATUS → wait for barrier
- When barrier resolves: compose batched prompt with all actions + initiative context
- One narrator call with combined actions, not N separate calls

**Prompt builder:**
- New prompt section: "PARTY ACTIONS THIS ROUND" with all player actions
- Initiative context: encounter type + per-player stats + genre initiative rules
- Instruction: resolve in initiative order, produce one synthesized scene

### UI Changes

**Player panel (TurnStatusPanel):**
- Visually prominent during sealed rounds — not a subtle indicator
- Per-player sealed/submitted indicator (letter icon or similar)
- Clear "all in" transition state before narrator resolves

**Input area:**
- After submitting: locked with "Sealed — waiting for other players"
- Cannot see what others typed

## Story Dependency Graph

```
Existing infrastructure (13-1 through 13-10, all done/disabled)
 │
 ├──► 13-11 (activate barrier, remove timeout)
 │     │
 │     └──► 13-12 (prompt architecture — one call, initiative context)
 │           │
 │           └──► 13-7 (integration test — validates full loop)
 │
 ├──► 13-13 (initiative stat mapping in genre pack)
 │     │
 │     └──► 13-12 (prompt needs initiative data from genre pack)
 │
 └──► 13-14 (player panel prominence — UI)
```

## Deferred (Not in This Epic)

- **Disconnect detection** — heartbeat-based removal from round, auto-resolve for dropped players
- **Mid-session join protocol** — how a new player enters a round already in progress
- **Cinematic mode** — narrator-paced prompts distinct from Structured. Exists in FSM, needs UX.
- **Per-genre initiative formulas** — genre packs beyond caverns_and_claudes
- **Split-party turns** — independent turn cycles when players are in different locations
- **Player-to-player private messaging** — out of scope, players use voice chat

## Success Criteria

During a multiplayer session:
1. All players compose actions simultaneously without seeing each other's input
2. Player panel prominently shows who has and hasn't submitted
3. No player can "race" to submit — the round collects from everyone
4. One narrator call resolves all actions, referencing initiative order
5. Initiative order reflects encounter type and relevant stats from genre pack
6. Narrator produces one synthesized scene, not N independent responses
7. Perception rewriter delivers per-player views where appropriate
