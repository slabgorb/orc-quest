---
parent: context-epic-9.md
---

# Story 9-8: GM Commands — /gm set, /gm teleport, /gm spawn, /gm dmg

## Business Context

During development and playtesting, the operator needs direct game state manipulation:
teleport a character, spawn an NPC, apply damage, set a variable. These GM commands are
operator-only (not available to regular players) and produce `StateMutation` results that
modify the game.

**Python source:** `sq-2/sidequest/slash_commands/gm.py`
**Depends on:** Story 9-6 (SlashRouter)

## Technical Approach

GM commands are a single `GmCommand` handler that dispatches on subcommand:

```rust
pub struct GmCommand;

impl CommandHandler for GmCommand {
    fn name(&self) -> &str { "gm" }
    fn description(&self) -> &str { "Game master commands (operator only)" }

    fn handle(&self, state: &GameState, args: &str) -> CommandResult {
        let (sub, sub_args) = match args.split_once(' ') {
            Some((s, a)) => (s, a.trim()),
            None => (args, ""),
        };
        match sub {
            "set" => Self::handle_set(state, sub_args),
            "teleport" => Self::handle_teleport(state, sub_args),
            "spawn" => Self::handle_spawn(state, sub_args),
            "dmg" => Self::handle_dmg(state, sub_args),
            _ => CommandResult::Error(format!("Unknown GM subcommand: {}", sub)),
        }
    }
}

impl GmCommand {
    fn handle_set(_state: &GameState, args: &str) -> CommandResult {
        let (key, value) = args.split_once(' ')
            .ok_or_else(|| "Usage: /gm set <key> <value>")
            .map_err(|e| CommandResult::Error(e.to_string()))?;
        CommandResult::StateMutation(StatePatch::SetVariable {
            key: key.to_string(),
            value: value.to_string(),
        })
    }

    fn handle_teleport(_state: &GameState, args: &str) -> CommandResult {
        CommandResult::StateMutation(StatePatch::Teleport {
            location: args.to_string(),
        })
    }

    fn handle_spawn(_state: &GameState, args: &str) -> CommandResult {
        CommandResult::StateMutation(StatePatch::SpawnNpc {
            npc_template: args.to_string(),
        })
    }

    fn handle_dmg(_state: &GameState, args: &str) -> CommandResult {
        let (target, hp_str) = args.split_once(' ')
            .ok_or_else(|| "Usage: /gm dmg <target> <hp>")
            .map_err(|e| CommandResult::Error(e.to_string()))?;
        let hp: i32 = hp_str.parse()
            .map_err(|_| CommandResult::Error("HP must be a number".to_string()))?;
        CommandResult::StateMutation(StatePatch::ApplyDamage {
            target: target.to_string(),
            amount: hp,
        })
    }
}
```

Authorization is checked at the router level. The orchestrator knows which player IDs
are operators (host or configured list). Non-operators receive an error for `/gm` commands.

```rust
impl SlashRouter {
    pub fn try_dispatch(
        &self,
        input: &str,
        state: &GameState,
        is_operator: bool,
    ) -> Option<CommandResult> {
        // ... parse ...
        if cmd == "gm" && !is_operator {
            return Some(CommandResult::Error("GM commands require operator access.".to_string()));
        }
        // ... dispatch ...
    }
}
```

## Scope Boundaries

**In scope:**
- `/gm set <key> <value>` — set game state variable
- `/gm teleport <location>` — move active character to location
- `/gm spawn <npc>` — add NPC to current scene
- `/gm dmg <target> <hp>` — apply damage to entity
- Operator authorization check
- Subcommand dispatch pattern

**Out of scope:**
- GM undo/rollback
- GM logging/audit trail (structured logging covers this)
- Player-visible GM action notifications
- Custom GM commands per genre

## Acceptance Criteria

| AC | Detail |
|----|--------|
| /gm set | Sets a game state variable, confirms change |
| /gm teleport | Moves character to named location |
| /gm spawn | Adds NPC template to current scene |
| /gm dmg | Applies HP damage to target entity |
| Operator only | Non-operator receives error for /gm commands |
| Arg validation | Missing or invalid arguments return usage message |
| StateMutation | All GM commands produce StateMutation results |
