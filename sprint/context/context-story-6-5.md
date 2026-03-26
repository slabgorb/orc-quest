---
parent: context-epic-6.md
---

# Story 6-5: Wire Faction Agendas into Scene Directive — Faction-Driven Events Appear in Narrator Prompt

## Business Context

Story 6-4 defines the `FactionAgenda` model and evaluation. Story 6-1 defines the scene
directive formatter. This story connects them — evaluated faction events flow into the
`SceneDirective` and appear in the narrator prompt as world-driven events the narrator
must acknowledge.

**Depends on:** Story 6-4 (FactionAgenda model)

## Technical Approach

The scene directive formatter gains a faction events parameter:

```rust
pub fn format_scene_directive(
    fired_beats: &[FiredBeat],
    active_stakes: &[ActiveStake],
    narrative_hints: &[String],
    faction_events: &[FactionEvent],  // NEW
) -> SceneDirective {
    // ... existing beat/stake logic ...

    let directive_faction_events: Vec<FactionEvent> = faction_events
        .iter()
        .filter(|e| e.urgency >= FACTION_DISPLAY_THRESHOLD)
        .cloned()
        .collect();

    SceneDirective {
        mandatory_elements: elements,
        faction_events: directive_faction_events,
        narrative_hints: narrative_hints.to_vec(),
    }
}
```

The prompt composer renders faction events as a subsection of the directive block:

```rust
if !directive.faction_events.is_empty() {
    block.push_str("\n[WORLD EVENTS — Factions acting independently]\n");
    for event in &directive.faction_events {
        block.push_str(&format!(
            "- {}: {}\n",
            event.faction_id, event.event_description
        ));
    }
}
```

Faction events are labeled separately from trope beats to help the narrator distinguish
player-driven story from world-driven story.

## Scope Boundaries

**In scope:**
- Extend `format_scene_directive()` signature with faction events
- Faction event filtering by urgency threshold
- Prompt composer rendering of faction events subsection
- Integration tests: agenda evaluation → directive → prompt output

**Out of scope:**
- FactionAgenda model (story 6-4)
- Genre pack content (stories 6-7, 6-8)
- Turn loop wiring (story 6-9)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Events in directive | Evaluated faction events appear in `SceneDirective.faction_events` |
| Urgency filtering | Events below threshold excluded from directive |
| Prompt rendering | Faction events render as `[WORLD EVENTS]` subsection |
| Faction labeled | Each event shows faction name for narrator context |
| No events | No `[WORLD EVENTS]` section when no faction events |
| Integration | End-to-end: YAML agenda → evaluate → directive → prompt string |
