---
parent: context-epic-8.md
---

# Story 8-1: MultiplayerSession — Coordinate Multiple WebSocket Clients, Player-ID Mapping

## Business Context

SideQuest's core value proposition as a group experience requires multiple players to share
a single game session. In Python, `multiplayer_session.py` manages a dict of player-to-character
mappings, handles join/leave lifecycle, and routes messages to the correct WebSocket. This
story ports that coordination layer to Rust, building on the single-player session actor
from story 2-2.

**Python source:** `sq-2/sidequest/game/multiplayer_session.py` (PlayerMapping, join, leave, broadcast)
**Depends on:** Story 2-2 (session actor)

## Technical Approach

Extend the existing session actor with a `MultiplayerSession` that wraps player-to-character
mapping and per-player WebSocket handles:

```rust
pub struct MultiplayerSession {
    pub session_id: SessionId,
    pub players: HashMap<PlayerId, PlayerSlot>,
    pub host: PlayerId,
    pub max_players: usize,
}

pub struct PlayerSlot {
    pub character_id: CharacterId,
    pub display_name: String,
    pub connected: bool,
    pub ws_tx: mpsc::Sender<GameMessage>,
}

impl MultiplayerSession {
    pub fn join(&mut self, player_id: PlayerId, slot: PlayerSlot) -> Result<(), JoinError> {
        if self.players.len() >= self.max_players {
            return Err(JoinError::SessionFull);
        }
        if self.players.contains_key(&player_id) {
            return Err(JoinError::AlreadyJoined);
        }
        self.players.insert(player_id, slot);
        Ok(())
    }

    pub fn leave(&mut self, player_id: &PlayerId) -> Option<PlayerSlot> {
        self.players.remove(player_id)
    }

    pub async fn broadcast(&self, msg: &GameMessage) {
        for slot in self.players.values().filter(|s| s.connected) {
            let _ = slot.ws_tx.send(msg.clone()).await;
        }
    }

    pub async fn send_to(&self, player_id: &PlayerId, msg: &GameMessage) {
        if let Some(slot) = self.players.get(player_id) {
            let _ = slot.ws_tx.send(msg.clone()).await;
        }
    }
}
```

Python uses a plain dict with string keys. Rust uses `HashMap<PlayerId, PlayerSlot>` with
typed IDs and a dedicated `PlayerSlot` struct that bundles the WebSocket sender. The
`connected` flag supports temporary disconnection without removing the player.

The session actor message enum gains multiplayer variants:

```rust
pub enum SessionCommand {
    // ... existing variants from 2-2 ...
    JoinMultiplayer { player_id: PlayerId, slot: PlayerSlot },
    LeaveMultiplayer { player_id: PlayerId },
    PlayerAction { player_id: PlayerId, input: String },
}
```

## Scope Boundaries

**In scope:**
- `MultiplayerSession` struct with player-to-character mapping
- Join/leave lifecycle with capacity enforcement
- Per-player message routing (broadcast and targeted send)
- Session actor integration (new command variants)
- `PlayerId` newtype for type safety

**Out of scope:**
- Turn coordination (story 8-2)
- Action batching (story 8-3)
- Reconnection with state replay (future work)
- Authentication/authorization (players are trusted for now)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Join session | Player joins with character mapping, receives confirmation |
| Capacity limit | Session rejects join when at max_players |
| Leave session | Player leaves, slot removed, other players notified |
| Broadcast | Message sent to all connected players |
| Targeted send | Message routed to specific player by PlayerId |
| Disconnect flag | Disconnected player's slot retained with connected=false |
| Host tracking | Session tracks which player is the host |
