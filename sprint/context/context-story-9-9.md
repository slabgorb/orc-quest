---
parent: context-epic-9.md
---

# Story 9-9: Tone Command — /tone Adjusts Genre Alignment Axes

## Business Context

Players and operators can nudge the genre tone mid-session. "/tone dark +1" shifts narration
toward darker themes. The genre alignment axes (light/dark, action/mystery, serious/whimsy)
are already part of the genre pack; this command lets them be adjusted at runtime so the
narrator reflects the shift.

**Depends on:** Story 9-6 (SlashRouter)

## Technical Approach

Genre alignment is stored as numeric axes in the game state:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToneAlignment {
    pub light_dark: i8,        // -2 (light) to +2 (dark)
    pub action_mystery: i8,    // -2 (action) to +2 (mystery)
    pub serious_whimsy: i8,    // -2 (serious) to +2 (whimsy)
}

impl ToneAlignment {
    pub fn adjust(&mut self, axis: &str, delta: i8) -> Result<(), ToneError> {
        let field = match axis {
            "dark" | "light" => &mut self.light_dark,
            "action" | "mystery" => &mut self.action_mystery,
            "serious" | "whimsy" => &mut self.serious_whimsy,
            _ => return Err(ToneError::UnknownAxis(axis.to_string())),
        };
        *field = (*field + delta).clamp(-2, 2);
        Ok(())
    }

    pub fn to_prompt_hint(&self) -> String {
        format!(
            "Tone: light/dark={}, action/mystery={}, serious/whimsy={}",
            self.light_dark, self.action_mystery, self.serious_whimsy
        )
    }
}
```

The command handler:

```rust
pub struct ToneCommand;

impl CommandHandler for ToneCommand {
    fn name(&self) -> &str { "tone" }
    fn description(&self) -> &str { "Adjust genre tone (e.g., /tone dark +1)" }

    fn handle(&self, _state: &GameState, args: &str) -> CommandResult {
        let (axis, value_str) = args.split_once(' ')
            .ok_or_else(|| "Usage: /tone <axis> <-2..+2>")
            .map_err(|e| CommandResult::Error(e.to_string()))?;
        let delta: i8 = value_str.parse()
            .map_err(|_| CommandResult::Error("Value must be -2 to +2".to_string()))?;
        CommandResult::StateMutation(StatePatch::AdjustTone {
            axis: axis.to_string(),
            delta,
        })
    }
}
```

The `ToneAlignment` is included in the narrator system prompt via `to_prompt_hint()`,
so Claude adjusts its narration style accordingly. A shift toward "dark +2" produces
grimmer descriptions; "whimsy +2" produces lighter, more playful text.

## Scope Boundaries

**In scope:**
- `ToneAlignment` struct with three axes
- `/tone` command parsing axis and delta
- Clamping to -2..+2 range
- `to_prompt_hint()` for narrator prompt injection
- StateMutation result for state update

**Out of scope:**
- Automatic tone detection from narration
- Per-player tone preferences
- Genre pack tone presets
- Tone history or drift tracking

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Axes supported | light/dark, action/mystery, serious/whimsy |
| Delta applied | /tone dark +1 increments light_dark by 1 |
| Clamped | Values clamped to -2..+2 range |
| Prompt hint | ToneAlignment included in narrator system prompt |
| Narrator shift | Tone changes reflected in subsequent narration style |
| Validation | Invalid axis or non-numeric value returns error |
