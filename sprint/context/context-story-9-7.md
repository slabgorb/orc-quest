---
parent: context-epic-9.md
---

# Story 9-7: Core Slash Commands — /status, /inventory, /map, /save, /help

## Business Context

The five core commands give players direct access to game state without an LLM round trip.
`/status` shows character condition, `/inventory` lists items, `/map` shows known locations,
`/save` triggers persistence, and `/help` lists commands. These are the most frequently
used commands in the Python version.

**Python source:** `sq-2/sidequest/slash_commands/status.py`, `inventory.py`, etc.
**Depends on:** Story 9-6 (SlashRouter)

## Technical Approach

Each command implements the `CommandHandler` trait. Commands are pure reads of game state
except `/save` which triggers persistence:

```rust
pub struct StatusCommand;

impl CommandHandler for StatusCommand {
    fn name(&self) -> &str { "status" }
    fn description(&self) -> &str { "Show your character's current condition" }

    fn handle(&self, state: &GameState, _args: &str) -> CommandResult {
        let character = &state.active_character;
        let sheet = character.to_narrative_sheet(&state.genre_pack.voice);
        CommandResult::Display(format!(
            "**{}**\n{}\n\nConditions: {}",
            character.name,
            sheet.status.narrative_summary(),
            Self::format_conditions(&character.conditions),
        ))
    }
}

pub struct InventoryCommand;

impl CommandHandler for InventoryCommand {
    fn name(&self) -> &str { "inventory" }
    fn description(&self) -> &str { "List your carried items" }

    fn handle(&self, state: &GameState, _args: &str) -> CommandResult {
        let items: Vec<String> = state.active_character.inventory.iter()
            .map(|item| format!("- **{}**: {}", item.name, item.genre_description))
            .collect();
        if items.is_empty() {
            CommandResult::Display("You carry nothing of note.".to_string())
        } else {
            CommandResult::Display(items.join("\n"))
        }
    }
}

pub struct HelpCommand {
    commands: Vec<(String, String)>, // (name, description)
}

impl CommandHandler for HelpCommand {
    fn name(&self) -> &str { "help" }
    fn description(&self) -> &str { "List available commands" }

    fn handle(&self, _state: &GameState, _args: &str) -> CommandResult {
        let lines: Vec<String> = self.commands.iter()
            .map(|(name, desc)| format!("/{} — {}", name, desc))
            .collect();
        CommandResult::Display(lines.join("\n"))
    }
}
```

`/save` is the only command that produces a `StateMutation` result:

```rust
impl CommandHandler for SaveCommand {
    fn handle(&self, _state: &GameState, _args: &str) -> CommandResult {
        CommandResult::StateMutation(StatePatch::Save)
    }
}
```

The orchestrator handles `StateMutation` results by applying the patch and confirming.

## Scope Boundaries

**In scope:**
- `/status` — character condition in genre voice
- `/inventory` — item list with genre descriptions
- `/map` — known locations and current position
- `/save` — trigger state persistence
- `/help` — list registered commands with descriptions

**Out of scope:**
- GM commands (story 9-8)
- Tone command (story 9-9)
- Command argument parsing beyond simple strings
- Rich formatting (markdown-like, not HTML)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| /status | Returns genre-voiced character condition |
| /inventory | Lists items with narrative descriptions |
| /inventory empty | Empty inventory returns flavor text, not empty string |
| /map | Shows known locations and current position |
| /save | Triggers game state persistence, confirms to player |
| /help | Lists all registered commands with descriptions |
| No LLM | All five commands resolve without Claude calls |
