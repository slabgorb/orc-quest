---
parent: context-epic-6.md
---

# Story 6-1: Scene Directive Formatter — format_scene_directive() Composing Fired Beats + Narrative Hints + Active Stakes into MUST-Weave Narrator Block

## Business Context

The narrator currently treats trope beats and active stakes as optional flavor. When the
trope engine fires a beat ("the rival faction makes a power play"), nothing forces the
narrator to mention it. The scene directive formatter solves this by composing fired beats,
narrative hints, and active stakes into a structured `SceneDirective` that the prompt
composer injects as mandatory content.

In Python (`sq-2/docs/architecture/active-world-pacing-design.md`), this was a string
formatting step buried in prompt composition. The Rust version makes it a pure function
with typed inputs and outputs.

**Depends on:** Story 2-8 (trope engine runtime — provides fired beats)

## Technical Approach

`format_scene_directive()` is a pure function — no LLM calls, no state mutation. It
collects inputs from the trope engine and world state, then builds a `SceneDirective`:

```rust
pub fn format_scene_directive(
    fired_beats: &[FiredBeat],
    active_stakes: &[ActiveStake],
    narrative_hints: &[String],
) -> SceneDirective {
    let mut elements = Vec::new();

    for beat in fired_beats {
        elements.push(DirectiveElement {
            source: DirectiveSource::TropeBeat,
            content: beat.narrator_instruction.clone(),
            priority: DirectivePriority::from_beat_urgency(beat.urgency),
        });
    }

    for stake in active_stakes {
        elements.push(DirectiveElement {
            source: DirectiveSource::ActiveStake,
            content: stake.description.clone(),
            priority: DirectivePriority::Medium,
        });
    }

    SceneDirective {
        mandatory_elements: elements,
        faction_events: vec![],  // 6-5 wires these in
        narrative_hints: narrative_hints.to_vec(),
    }
}
```

Priority ordering ensures the highest-urgency elements appear first in the prompt block.
The formatter caps mandatory elements at a configurable limit (default 3) to avoid
overwhelming the narrator.

## Scope Boundaries

**In scope:**
- `format_scene_directive()` pure function
- `SceneDirective`, `DirectiveElement`, `DirectiveSource`, `DirectivePriority` types
- Priority sorting and element cap
- Unit tests with mock fired beats and stakes

**Out of scope:**
- Prompt injection (story 6-2)
- Faction events (story 6-5)
- Engagement multiplier (story 6-3)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Pure function | `format_scene_directive()` takes refs, returns owned `SceneDirective` |
| Beat conversion | Each `FiredBeat` becomes a `DirectiveElement` with `TropeBeat` source |
| Stake conversion | Each `ActiveStake` becomes a `DirectiveElement` with `ActiveStake` source |
| Priority ordering | Elements sorted by priority descending in output |
| Element cap | No more than configurable max mandatory elements (default 3) |
| Empty inputs | Returns `SceneDirective` with empty vecs when no beats/stakes fired |
| Narrative hints | Passed through as-is to `narrative_hints` field |
