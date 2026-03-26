---
parent: context-epic-9.md
---

# Story 9-6: Slash Command Router — Intercept /command Input Before Intent Classification

## Business Context

Input starting with "/" should bypass the LLM entirely. `/status` should not go through
intent classification and a Claude call — it should dispatch directly to a handler that
reads game state and returns a response. Python's slash command system intercepts input
before the orchestrator's intent router. This story builds the Rust equivalent.

**Python source:** `sq-2/sidequest/slash_commands/*.py` (command dispatch)
**Depends on:** Story 2-5 (orchestrator turn loop — interception point)

## Technical Approach

The slash router sits upstream of the intent router in the input pipeline:

```rust
pub struct SlashRouter {
    commands: HashMap<String, Box<dyn CommandHandler>>,
}

pub trait CommandHandler: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn handle(&self, state: &GameState, args: &str) -> CommandResult;
}

pub enum CommandResult {
    Display(String),
    StateMutation(StatePatch),
    Error(String),
}

impl SlashRouter {
    pub fn new() -> Self {
        Self { commands: HashMap::new() }
    }

    pub fn register(&mut self, cmd: impl CommandHandler + 'static) {
        self.commands.insert(
            cmd.name().to_string(),
            Box::new(cmd),
        );
    }

    pub fn try_dispatch(
        &self,
        input: &str,
        state: &GameState,
    ) -> Option<CommandResult> {
        if !input.starts_with('/') {
            return None;
        }
        let (cmd, args) = Self::parse(input);
        self.commands.get(cmd).map(|handler| handler.handle(state, args))
    }

    fn parse(input: &str) -> (&str, &str) {
        let trimmed = &input[1..]; // skip '/'
        match trimmed.split_once(' ') {
            Some((cmd, args)) => (cmd, args.trim()),
            None => (trimmed, ""),
        }
    }
}
```

Integration in the orchestrator:

```rust
impl Orchestrator {
    pub async fn process_input(&mut self, input: &str, player_id: &PlayerId) -> Response {
        // Slash commands intercept BEFORE intent routing
        if let Some(result) = self.slash_router.try_dispatch(input, &self.state) {
            return self.handle_command_result(result);
        }
        // Normal turn pipeline
        self.process_turn(input, player_id).await
    }
}
```

Commands are pure functions of state and arguments. They never call the LLM. The trait
object pattern allows commands to be registered dynamically, supporting future genre-specific
commands.

## Scope Boundaries

**In scope:**
- `SlashRouter` with command registry
- `CommandHandler` trait for handler implementations
- `CommandResult` enum (Display, StateMutation, Error)
- Input parsing (command name + args extraction)
- Orchestrator integration (intercept before intent routing)
- `/help` meta-command listing registered commands

**Out of scope:**
- Specific command implementations (stories 9-7, 9-8, 9-9)
- Client-side autocomplete
- Command permissions/authorization (GM commands handle their own checks)
- Command history or undo

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Intercept | Input starting with "/" bypasses intent router |
| Passthrough | Non-slash input reaches intent router unchanged |
| Parse | "/command arg1 arg2" parsed into name="command", args="arg1 arg2" |
| Registry | Commands registered by name, dispatched via HashMap lookup |
| Unknown command | Unregistered /command returns Error result |
| No LLM | Command handling involves zero Claude calls |
| Pure functions | Handlers receive immutable state reference |
