---
parent: context-epic-5.md
---

# Story 5-7: Wire Pacing into Orchestrator — drama_weight Flows from TensionTracker Through Turn Pipeline to Narrator Prompt

## Business Context

Stories 5-1 through 5-6 built the pacing engine in isolation. This story wires it into
the real turn pipeline from story 2-5. After this, every combat turn automatically gets
drama-aware narration length and delivery mode — no manual tuning, no flags to set.

In Python, the tension tracker is a property on the orchestrator that gets called inline
during `handle_player_input()`. The Rust version takes the same approach but with explicit
data flow — the TensionTracker produces a PacingHint, the orchestrator injects it into
the narrator prompt, and the server uses the delivery mode for text reveal.

**Python source:** `sq-2/sidequest/orchestrator.py` (tension tracker integration points)
**Depends on:** Story 5-4 (PacingHint generation), Story 2-5 (orchestrator turn pipeline)

## Technical Approach

### TensionTracker as Orchestrator Field

```rust
pub struct Orchestrator {
    state: GameState,
    intent_router: IntentRouter,
    prompt_composer: PromptComposer,
    store: SessionStore,
    tension: TensionTracker,           // NEW: pacing engine
    drama_thresholds: DramaThresholds, // NEW: genre-tunable config
    // ... other fields
}
```

The tracker lives on the orchestrator, not on GameState. It is *derived from* game state
but is not part of it — drama_weight is an ephemeral observation, not persisted state.
Python makes the same distinction (`self.tension_tracker` vs `self.state`).

### Turn Pipeline Integration Points

The orchestrator's `process_turn()` from story 2-5 gains three new steps:

```rust
impl Orchestrator {
    pub async fn process_turn(
        &mut self,
        input: &str,
        player_id: &PlayerId,
    ) -> Result<TurnResult, OrchestrationError> {
        // Steps 1-4 unchanged (sanitize, route, compose prompt, build context)
        let clean_input = sanitize_player_text(input);
        let route = self.intent_router.classify(&clean_input, &self.state);

        // === NEW: Step 4.5 — Compute pacing hint from current state ===
        let pacing = self.tension.pacing_hint(&self.drama_thresholds);

        // Step 3 (compose prompt) now includes pacing directive
        let system_prompt = self.prompt_composer.compose(
            route.agent,
            &self.state,
            &self.genre_pack,
            Some(&pacing),  // NEW: inject pacing guidance
        );

        let context = self.build_agent_context(route.agent, &clean_input);

        // Step 5: Call agent
        let response = self.call_agent(route.agent, &system_prompt, &context).await?;

        // Step 6-7: Extract patches, apply
        let (narration, patches) = self.extract_patches(route.agent, &response)?;
        let pre_state = self.state.snapshot_for_delta();
        self.apply_patches(&patches)?;

        // === NEW: Step 7.5 — Observe combat outcome for next turn's pacing ===
        if let Some(outcome) = patches.combat_outcome() {
            let lowest_hp = self.state.lowest_friendly_hp_ratio();
            self.tension.observe(&outcome, lowest_hp);
        }

        // Steps 8-10 unchanged (post-turn update, delta, return)
        self.post_turn_update(&clean_input, &narration).await?;
        let delta = self.state.compute_delta(&pre_state);

        Ok(TurnResult {
            narration,
            narration_chunks: vec![],
            state_delta: delta,
            combat_events: patches.combat_events(),
            delivery_mode: pacing.delivery_mode,  // NEW: included in result
            is_degraded: false,
        })
    }
}
```

### Prompt Composer Changes

```rust
impl PromptComposer {
    pub fn compose(
        &self,
        agent: AgentKind,
        state: &GameState,
        genre_pack: &GenrePack,
        pacing: Option<&PacingHint>,
    ) -> String {
        let mut prompt = self.base_prompt(agent, state, genre_pack);

        // Inject pacing guidance for narrator and combat agents
        if let Some(hint) = pacing {
            if matches!(agent, AgentKind::Narrator | AgentKind::CreatureSmith) {
                prompt.push_str("\n\n## Pacing Guidance\n");
                prompt.push_str(&hint.narrator_directive());
                if let Some(ref beat) = hint.escalation_beat {
                    prompt.push_str("\n\n## Escalation Beat\n");
                    prompt.push_str(beat);
                }
            }
        }

        prompt
    }
}
```

### TurnResult Changes

```rust
pub struct TurnResult {
    pub narration: String,
    pub narration_chunks: Vec<String>,
    pub state_delta: Option<StateDelta>,
    pub combat_events: Vec<CombatEvent>,
    pub delivery_mode: DeliveryMode,  // NEW: server uses for text reveal
    pub is_degraded: bool,
}
```

### Server Reads delivery_mode

```rust
// In the WebSocket handler (story 1-7):
let result = orchestrator.process_turn(input, player_id).await?;

// Send NARRATION_START with delivery mode
tx.send(GameMessage::NarrationStart {
    delivery_mode: result.delivery_mode,
}).ok();

// Deliver text according to mode
session.deliver_narration(&result.narration, result.delivery_mode, &tx).await;
```

### Lowest HP Ratio Helper

```rust
impl GameState {
    /// Find the lowest HP ratio among friendly (player-controlled) characters.
    /// Returns 1.0 if no characters are in combat.
    pub fn lowest_friendly_hp_ratio(&self) -> f64 {
        self.characters
            .iter()
            .filter(|c| c.is_friendly && c.in_combat)
            .map(|c| c.current_hp as f64 / c.max_hp as f64)
            .fold(1.0, f64::min)
    }
}
```

### Timing: Observe After Apply

The observe call happens *after* patches are applied (step 7.5, not before). This is
deliberate — we want the tension tracker to see the result of this turn's combat, not
the state before it. A killing blow should inject a spike for *this* turn's narration
delivery, and the next turn's pacing hint will reflect the decayed spike.

Wait — actually the pacing hint is computed *before* the agent call (step 4.5) and the
observe happens *after* (step 7.5). This means the pacing for turn N reflects the
outcome of turn N-1. This is correct and matches Python's behavior: you can not know
the drama of the current turn before it happens. The narrator writes turn N's text
based on the tension state going *into* turn N.

## Scope Boundaries

**In scope:**
- TensionTracker field on Orchestrator
- PacingHint computation injected into turn pipeline
- PromptComposer accepts optional PacingHint, injects pacing + escalation directives
- observe() called after combat patches applied
- delivery_mode added to TurnResult
- lowest_friendly_hp_ratio() helper on GameState
- Integration tests: full turn pipeline with pacing

**Out of scope:**
- Non-combat pacing (exploration narration length is not drama-driven yet)
- Game Watcher telemetry for drama_weight (Epic 3 integration, follow-up)
- Client-side delivery rendering (sidequest-ui)
- Persisting TensionTracker across save/load (it resets per encounter)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Tracker on orchestrator | Orchestrator has TensionTracker field, initialized on encounter start |
| Pacing in prompt | Narrator system prompt includes sentence count directive when in combat |
| Escalation in prompt | Escalation beat hint appears in prompt when boring_streak >= threshold |
| Observe after apply | tension.observe() called with combat outcome after patches applied |
| delivery_mode in result | TurnResult includes delivery_mode, server uses it for text reveal |
| HP ratio helper | lowest_friendly_hp_ratio() returns correct value from GameState |
| Non-combat passthrough | Non-combat turns skip pacing injection (no sentence count directive) |
| Timing correct | Pacing for turn N based on outcomes of turns 1..N-1, not turn N |
| Integration test | Simulated 3-turn combat shows boring ramp -> dramatic spike -> decay in pacing hints |
