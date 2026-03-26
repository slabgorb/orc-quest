---
parent: context-epic-9.md
---

# Story 9-10: Wire Narrative Sheet to React Client — CHARACTER_SHEET Message

## Business Context

The narrative character sheet needs to reach the player's screen. This story adds a
`CHARACTER_SHEET` WebSocket message type that carries the `NarrativeSheet` data from
server to client, and a React component that renders it. The sheet updates when the
player uses `/status` or when abilities/knowledge change.

**Depends on:** Story 9-5 (NarrativeSheet model)
**Repos:** sidequest-api, sidequest-ui

## Technical Approach

### Protocol (sidequest-protocol)

Add the `CHARACTER_SHEET` message variant:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GameMessage {
    // ... existing variants ...
    CharacterSheet {
        sheet: NarrativeSheet,
    },
}
```

The server sends `CharacterSheet` in response to `/status`, on session join, and whenever
the character's abilities or knowledge change (post-turn update).

### Server (sidequest-server)

```rust
// In the command result handler:
fn handle_command_result(&self, result: CommandResult, player_id: &PlayerId) {
    match result {
        CommandResult::Display(text) => {
            // For /status, also send the full sheet
            if is_status_command {
                let sheet = self.state.active_character.to_narrative_sheet(&self.genre_voice);
                self.send_to(player_id, GameMessage::CharacterSheet { sheet });
            }
            self.send_to(player_id, GameMessage::CommandResponse { text });
        }
        // ...
    }
}
```

### Client (sidequest-ui)

A React component renders the narrative sheet:

```tsx
interface NarrativeSheetProps {
  sheet: NarrativeSheet;
}

function CharacterSheet({ sheet }: NarrativeSheetProps) {
  return (
    <div className="character-sheet">
      <h2>{sheet.identity}</h2>
      <section className="abilities">
        <h3>Abilities</h3>
        {sheet.abilities.map(a => (
          <div key={a.name} className="ability">
            <strong>{a.name}</strong>: {a.description}
            {a.involuntary && <span className="tag">passive</span>}
          </div>
        ))}
      </section>
      <section className="knowledge">
        <h3>What You Know</h3>
        {sheet.knowledge.map((k, i) => (
          <div key={i} className="fact">
            {k.content} <span className="confidence">({k.confidence})</span>
          </div>
        ))}
      </section>
    </div>
  );
}
```

The sheet opens as a slide-out panel or modal, not inline with the narration stream.

## Scope Boundaries

**In scope:**
- `CharacterSheet` variant in `GameMessage` enum
- Server sends sheet on /status, session join, and knowledge change
- React component rendering identity, abilities, knowledge, status
- Genre-voiced display (no mechanical stats)
- TypeScript types matching NarrativeSheet struct

**Out of scope:**
- Sheet editing by the player
- Sheet sharing between players
- Print/export layout
- Ability tooltips with mechanical details
- Animated transitions or rich formatting

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Message type | CHARACTER_SHEET message defined in protocol |
| Server sends | Sheet sent on /status, join, and knowledge change |
| React renders | Component displays identity, abilities, knowledge |
| Genre voice | All text in genre voice, no mechanical stats |
| Abilities listed | Each ability shows name and genre description |
| Knowledge listed | Known facts displayed with confidence tags |
| Type alignment | TypeScript types match Rust NarrativeSheet struct |
