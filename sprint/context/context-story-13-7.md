# Story 13-7: Sealed Letter Integration Test

## What This Story Is

The final validation story for the sealed-letter turn system. All production code is complete (stories 13-11, 13-12, 13-14 merged). This story is **test only** — no new production code, just end-to-end integration verification.

The purpose: prove that the complete flow works together:
1. Barrier collects actions from 4 simultaneous players
2. ACTION_REVEAL broadcasts all actions
3. Single narrator call resolves all actions with initiative awareness
4. Perception rewriter splits per-player views
5. Turn counter increments correctly

## Context from Completed Siblings

### 13-11: Barrier Activation
- Status: **Merged** (2026-04-09)
- What it did: Flipped `should_use_barrier()` to return true for multiplayer
- File: `crates/sidequest-game/src/barrier.rs`

### 13-12: Initiative Stat Mapping
- Status: **Done** (merged)
- What it did: Added `InitiativeRule` to genre pack schema
- File: `sidequest-content/` — caverns_and_claudes now has initiative rules

### 13-13: Player Panel Prominence
- Status: **Backlog** (was supposed to be done but isn't)
- Note: This is a UI feature. Won't block the integration test.

### 13-14: Sealed-Round Prompt Architecture
- Status: **Merged** (2026-04-09)
- What it did: Implemented `SealedRoundPrompt` — one narrator call with all actions + initiative context
- File: `crates/sidequest-game/src/sealed_round.rs`
- Test file: `crates/sidequest-server/tests/sealed_round_prompt_story_13_14_tests.rs`

## Test Architecture

### Input: 4 WebSocket Clients

Simulate 4 players using the test harness:
```
Client A (Alice, Fighter, DEX=14)
Client B (Bob, Rogue, DEX=16)
Client C (Carol, Cleric, WIS=15)
Client D (Dave, Wizard, INT=17)
```

### Test Flow

**Phase 1: Setup**
1. Connect 4 clients to session with different character IDs
2. Initialize barrier with 4 expected players
3. Broadcast initial scene

**Phase 2: Turn 1 (All Submit)**
1. Narrator presents scene
2. Alice submits "Attack the goblin"
3. Bob submits "Sneak around the side"
4. Carol submits "Cast cure light wounds on the party"
5. Dave submits "Fire bolt at the goblin"
6. All 4 received → barrier resolves

**Phase 3: Barrier Resolution**
1. Compose `SealedRoundContext` with all 4 actions + encounter type + initiative rules
2. Call narrator ONE time (not 4) with combined context
3. Narrator returns scene mentioning all 4 actions in initiative order

**Phase 4: Broadcast ACTION_REVEAL**
1. Server sends `ActionReveal` message with all 4 actions keyed by character name
2. Each client receives the same reveal
3. Verify message contains:
   - Alice → "Attack the goblin"
   - Bob → "Sneak around the side"
   - Carol → "Cast cure light wounds on the party"
   - Dave → "Fire bolt at the goblin"

**Phase 5: Verify Narrator Response**
1. Check that response mentions all 4 characters in some order
2. Check that it references the initiative order (Bob first by DEX, then Alice, etc.)
3. Verify that response came from single prompt (single entry in call_history)

**Phase 6: State Verification**
1. Turn counter incremented from 1 → 2
2. GameState reflects all 4 actions as resolved
3. Multiplayer session cleared, ready for turn 2

**Phase 7: Turn 2 (Different Mix)**
- 3 players submit, 1 is slow
- Verify no timeout occurs (round waits indefinitely)
- Verify barrier still resolves correctly

## Key Assertion Chains

### 1. Barrier Collects All Actions
```rust
assert_eq!(barrier.action_count, 4);
assert!(barrier.is_resolved());
```

### 2. Single Narrator Call
```rust
let narrator_calls = session.call_history.len();
assert_eq!(narrator_calls, 2); // Turn 1 + Turn 2
```

### 3. ACTION_REVEAL Contains All
```rust
let reveal_msg = messages.iter()
    .find(|m| matches!(m.payload, GameMessage::ActionReveal { .. }))
    .expect("ACTION_REVEAL not found");

assert_eq!(reveal_msg.actions.len(), 4);
```

### 4. Narrator References All Characters
```rust
let narration = &game_state.narration_history.last().unwrap().text;
assert!(narration.contains("Alice"));
assert!(narration.contains("Bob"));
assert!(narration.contains("Carol"));
assert!(narration.contains("Dave"));
```

### 5. OTEL Telemetry
```rust
// Verify barrier lifecycle events
assert_eq!(otel_spans.filter(|s| s.name == "barrier.added_player").count(), 4);
assert_eq!(otel_spans.filter(|s| s.name == "barrier.resolved").count(), 1);

// Verify narrator call event
assert!(otel_spans.any(|s| s.name == "narrator.sealed_round_call"));
```

## Test File Template

File: `crates/sidequest-server/tests/sealed_letter_integration_story_13_7_tests.rs`

```rust
#[tokio::test]
async fn test_sealed_letter_4_player_full_flow() {
    // 1. Setup: Create session + 4 clients
    // 2. Turn 1: All 4 submit → barrier resolves → single narrator call
    // 3. Verify ACTION_REVEAL broadcast
    // 4. Verify all actions in narrator response
    // 5. Turn 2: Partial submit → verify barrier still works
}

#[tokio::test]
async fn test_barrier_composition_with_initiative_context() {
    // Verify SealedRoundContext includes:
    // - All 4 actions
    // - Encounter type
    // - Initiative rules from genre pack
}

#[tokio::test]
async fn test_perception_rewriter_splits_per_player() {
    // If ADR-028 splitting is needed for this test, verify it works
}
```

## Dependencies & Wiring

This test depends on:
- `TurnBarrier` (barrier.rs) — active + resolving correctly
- `SealedRoundPrompt` (sealed_round.rs) — composing context + calling narrator
- `MultiplayerSession` (multiplayer.rs) — collecting actions
- `SharedGameSession` (server/shared_session.rs) — broadcast infrastructure
- Protocol message `ActionReveal` — defined + serializable

All of these are **already merged** and **working**. This test just verifies they work together.

## Success Criteria

After this test passes:
1. Sealed-letter system is validated end-to-end
2. Epic 13 is **complete and closed**
3. Playtest can focus on gameplay issues, not wiring bugs
4. Code is ready for 2026-04-13 playtest session

## Non-Goals

- **UI testing** (13-13 is not done yet — that's separate)
- **Timeout handling** (no timeout in this test — barrier waits indefinitely)
- **Disconnect recovery** (no mid-round disconnects — out of scope for MVP)
- **Chat / private messaging** (not in sealed letter scope)
