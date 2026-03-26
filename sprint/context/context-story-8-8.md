---
parent: context-epic-8.md
---

# Story 8-8: Catch-Up Narration — Generate Arrival Snapshot for Mid-Session Joining Players

## Business Context

When a player joins a session already in progress, they need context: where the party is,
what has happened, and what their character knows. Rather than replaying the entire session
log, the system generates a concise catch-up summary via a Claude call that distills
recent events into a genre-voiced arrival snapshot.

**Depends on:** Story 8-1 (MultiplayerSession join flow)

## Technical Approach

Generate a catch-up summary from recent session history when a player joins mid-session:

```rust
pub struct CatchUpGenerator {
    claude: ClaudeClient,
}

impl CatchUpGenerator {
    pub async fn generate(
        &self,
        state: &GameState,
        recent_turns: &[TurnSummary],
        character: &Character,
        genre_voice: &str,
    ) -> Result<String, CatchUpError> {
        let prompt = format!(
            "Write a brief arrival summary for {name} joining a game in progress.\n\
             Genre: {genre}\n\
             Location: {location}\n\
             Recent events:\n{events}\n\n\
             2-3 sentences, in genre voice. What does {name} see and know?",
            name = character.name,
            genre = genre_voice,
            location = state.location.name,
            events = Self::format_recent(recent_turns),
        );
        self.claude.call(&prompt).await.map_err(CatchUpError::Agent)
    }

    fn format_recent(turns: &[TurnSummary]) -> String {
        turns.iter()
            .rev()
            .take(5)  // last 5 turns
            .map(|t| format!("- {}", t.summary))
            .collect::<Vec<_>>()
            .join("\n")
    }
}
```

The catch-up is sent as a targeted `NARRATION` message to the joining player only. Other
players receive a brief `PLAYER_JOINED` notification.

`TurnSummary` is a lightweight struct maintained by the session — one line per turn,
updated as turns resolve. This avoids sending full narration history to the LLM.

## Scope Boundaries

**In scope:**
- `CatchUpGenerator` with Claude CLI call
- `TurnSummary` maintained per-turn for recent history
- Targeted narration to joining player
- PLAYER_JOINED notification to existing players
- Last-5-turns window for context

**Out of scope:**
- Full session replay
- Character-specific catch-up (what this character specifically missed)
- Catch-up for reconnecting players (they have prior context)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Summary generated | Joining player receives genre-voiced catch-up narration |
| Recent context | Summary uses last 5 turns of session history |
| Targeted delivery | Catch-up sent only to the joining player |
| Join notification | Other players notified of new arrival |
| Graceful fallback | If generation fails, player gets basic location description |
| Turn summaries | Session maintains lightweight per-turn summaries |
