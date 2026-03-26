---
parent: context-epic-6.md
---

# Story 6-9: Wire Scene Directive into Orchestrator Turn Loop — Directive Generation and Prompt Injection Per Turn

## Business Context

Stories 6-1 through 6-6 build the individual pieces: directive formatting, MUST-weave
prompt injection, engagement multiplier, faction agendas, and world materialization. This
story wires everything into the orchestrator's `process_turn()` pipeline so that every
turn generates and injects a scene directive. This is the integration story that makes
the active world come alive.

**Depends on:** Story 6-2 (MUST-weave instruction in prompt)

## Technical Approach

The orchestrator's turn pipeline gains two new steps between context building and agent
call:

```rust
impl Orchestrator {
    pub async fn process_turn(&mut self, input: &str, player_id: &PlayerId)
        -> Result<TurnResult, OrchestrationError>
    {
        let clean_input = sanitize_player_text(input);
        let route = self.intent_router.classify(&clean_input, &self.state);

        // NEW: Update engagement tracking
        if route.is_meaningful() {
            self.state.turns_since_meaningful = 0;
        } else {
            self.state.turns_since_meaningful += 1;
        }

        // NEW: Apply engagement multiplier to trope tick
        let multiplier = engagement_multiplier(self.state.turns_since_meaningful);
        self.trope_engine.tick(self.base_tick * multiplier);

        // NEW: Evaluate faction agendas
        let faction_events = evaluate_agendas(
            &self.genre_pack.faction_agendas,
            &self.state,
        );

        // NEW: Generate scene directive
        let directive = format_scene_directive(
            &self.trope_engine.fired_beats(),
            &self.state.active_stakes,
            &self.trope_engine.narrative_hints(),
            &faction_events,
        );

        // Existing: compose prompt (now includes directive)
        let system_prompt = self.prompt_composer.compose(
            route.agent, &self.state, &self.genre_pack, Some(&directive),
        );

        // ... rest of pipeline unchanged ...
    }
}
```

The key design choice: directive generation happens **after** trope tick (so newly fired
beats are included) but **before** prompt composition (so the directive is available for
injection).

## Scope Boundaries

**In scope:**
- Wire `format_scene_directive()` into `process_turn()` pipeline
- Wire engagement multiplier into trope tick
- Wire faction agenda evaluation into turn loop
- Pass `SceneDirective` to prompt composer
- Integration tests: full turn with directive in prompt output

**Out of scope:**
- Changing any of the component implementations (6-1 through 6-6)
- Narrator compliance verification
- Media pipeline integration

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Directive per turn | Every `process_turn()` call generates a `SceneDirective` |
| Prompt contains directive | Narrator prompt includes `[SCENE DIRECTIVES]` block |
| Engagement tracked | `turns_since_meaningful` updates per turn based on intent |
| Multiplier applied | Trope tick uses engagement multiplier |
| Faction events included | Evaluated faction events appear in directive |
| Ordering correct | Trope tick → directive generation → prompt composition |
| No directive agents | Non-narrator agents (Combat, Chase) do not receive directives |
| Backward compatible | Turns with no fired beats/stakes produce empty directive (no block) |
