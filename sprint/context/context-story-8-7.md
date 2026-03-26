---
parent: context-epic-8.md
---

# Story 8-7: Guest NPC Players — Human-Controlled NPC Characters with Limited Agency

## Business Context

Sometimes a player wants to control an existing NPC rather than a full player character.
Guest NPC players have restricted agency: limited action set, no inventory management, and
the narrator treats them as semi-autonomous (they can act but the narrator may override or
redirect). This lets friends drop in to a session as a tavern keeper or a guide without
needing full character creation.

**ADR:** ADR-029 (Guest NPC Players)
**Depends on:** Story 8-1 (MultiplayerSession)

## Technical Approach

Model guest players as a variant of `PlayerSlot` with restricted capabilities:

```rust
pub enum PlayerRole {
    Full,
    GuestNpc {
        npc_id: NpcId,
        allowed_actions: HashSet<ActionCategory>,
    },
}

pub enum ActionCategory {
    Dialogue,
    Movement,
    Examine,
    // Combat, Inventory, QuestAccept excluded for guests
}

impl PlayerRole {
    pub fn can_perform(&self, action: &ActionCategory) -> bool {
        match self {
            PlayerRole::Full => true,
            PlayerRole::GuestNpc { allowed_actions, .. } => allowed_actions.contains(action),
        }
    }

    pub fn default_guest_actions() -> HashSet<ActionCategory> {
        [ActionCategory::Dialogue, ActionCategory::Movement, ActionCategory::Examine]
            .into_iter().collect()
    }
}
```

The session validates actions before forwarding to the barrier:

```rust
impl MultiplayerSession {
    pub fn validate_action(&self, player_id: &PlayerId, input: &str) -> Result<(), ActionError> {
        let slot = self.players.get(player_id).ok_or(ActionError::NotInSession)?;
        if let PlayerRole::GuestNpc { .. } = &slot.role {
            let category = categorize_action(input);
            if !slot.role.can_perform(&category) {
                return Err(ActionError::RestrictedAction { category });
            }
        }
        Ok(())
    }
}
```

In the narrator prompt, guest NPCs are tagged so Claude knows they are semi-autonomous:

```
[GUEST NPC: Marta the Innkeeper — controlled by a guest player.
 Treat their dialogue as in-character but maintain NPC behavioral consistency.
 You may adjust or redirect their actions if they conflict with NPC personality.]
```

## Scope Boundaries

**In scope:**
- `PlayerRole` enum (Full vs GuestNpc)
- Action category restriction for guests
- Action validation before barrier submission
- Narrator prompt annotation for guest-controlled NPCs
- Join-as-NPC flow (player selects available NPC to control)

**Out of scope:**
- NPC personality enforcement (narrator handles via prompt)
- Guest-to-full-player promotion mid-session
- Multiple guests controlling the same NPC
- Guest NPC combat mechanics

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Guest join | Player joins session as a specific NPC |
| Action restriction | Guest cannot perform disallowed actions (combat, inventory) |
| Allowed actions | Dialogue, movement, examine permitted by default |
| Validation | Restricted action returns error before reaching barrier |
| Narrator tag | Guest NPC annotated in narrator prompt for semi-autonomous treatment |
| NPC selection | Available NPCs in current scene listed for guest to choose |
