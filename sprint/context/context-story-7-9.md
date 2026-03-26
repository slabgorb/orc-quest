---
parent: context-epic-7.md
---

# Story 7-9: ScenarioEngine Integration — Wire Scenario Lifecycle into Orchestrator Turn Loop

## Business Context

Stories 7-1 through 7-8 build individual scenario subsystems. This story wires them into
the orchestrator's `process_turn()` pipeline so scenarios run as part of the game loop.
The `ScenarioEngine` manages the full lifecycle: scenario start (from genre pack trigger),
per-turn processing (gossip, clue evaluation, NPC actions, tension ramp), accusation
handling, and scenario resolution with scoring.

**Depends on:** Story 7-5 (NPC autonomous actions — the last subsystem that feeds the turn loop)

## Technical Approach

The `ScenarioEngine` orchestrates all scenario subsystems per turn:

```rust
pub struct ScenarioEngine {
    pub state: Option<ScenarioState>,
    pub pacing: ScenarioPacing,
    archiver: ScenarioArchiver,
}

impl ScenarioEngine {
    /// Called by orchestrator each turn when a scenario is active.
    pub fn process_turn(
        &mut self,
        game_state: &GameSnapshot,
        rng: &mut impl Rng,
    ) -> ScenarioTurnResult {
        let state = match &mut self.state {
            Some(s) => s,
            None => return ScenarioTurnResult::NoScenario,
        };

        // 1. Evaluate clue triggers
        let new_clues = evaluate_triggers(&mut state.clues, game_state);

        // 2. Propagate gossip
        propagate_gossip(&mut state.beliefs, &state.social_graph, rng);

        // 3. Update tension
        state.tension = self.pacing.tension_at_turn(
            state.turn_count, &state.events,
        );

        // 4. NPC autonomous actions
        let npc_actions = state.npc_roles.iter().map(|(npc_id, role)| {
            let action = select_npc_action(
                npc_id, role, &state.beliefs[npc_id],
                state.tension, rng,
            );
            (npc_id.clone(), action)
        }).collect::<Vec<_>>();

        // 5. Resolve NPC actions (update beliefs, clues, locations)
        resolve_npc_actions(&npc_actions, state, game_state);

        state.turn_count += 1;

        ScenarioTurnResult::Active {
            new_clues,
            npc_actions,
            tension: state.tension,
            narrator_context: self.build_narrator_context(state),
        }
    }

    /// Handle player accusation — resolves scenario.
    pub fn handle_accusation(
        &mut self,
        accusation: Accusation,
    ) -> Option<ScenarioResolution> {
        let state = self.state.as_ref()?;
        let result = evaluate_accusation(&accusation, state);
        let score = score_scenario(state, &result);
        self.state = None;  // scenario complete
        Some(ScenarioResolution { result, score })
    }
}
```

The orchestrator calls `scenario_engine.process_turn()` after the primary agent response
but before post-turn state updates. The `ScenarioTurnResult::Active` variant provides
narrator context that the prompt composer includes in the next turn's prompt.

Scenario start is triggered by genre pack conditions (e.g., campaign maturity reaches
Mid and a mystery trope fires). The orchestrator checks for scenario triggers after
trope ticks.

## Scope Boundaries

**In scope:**
- `ScenarioEngine` struct with `process_turn()` and `handle_accusation()`
- `ScenarioTurnResult` enum for turn-by-turn output
- Lifecycle: start → per-turn processing → accusation → resolution
- Narrator context generation from scenario state
- Integration with orchestrator turn pipeline
- Auto-save via archiver after each scenario turn

**Out of scope:**
- Scenario template authoring (genre pack content, future stories)
- Multiple concurrent scenarios
- Scenario-specific narrator agents (uses existing narrator with context injection)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Turn processing | Each turn evaluates clues, gossip, tension, and NPC actions in order |
| Narrator context | Scenario state injected into narrator prompt for next turn |
| Accusation resolves | Player accusation evaluates evidence and produces score |
| Scenario lifecycle | Start → active turns → accusation → resolution |
| No scenario passthrough | When no scenario active, `process_turn()` returns `NoScenario` |
| Auto-save | Scenario state saved via archiver after each turn |
| Orchestrator wiring | `ScenarioEngine` called from within `process_turn()` pipeline |
| NPC actions resolved | Autonomous NPC actions update beliefs and game state |
