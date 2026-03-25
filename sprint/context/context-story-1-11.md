---
parent: context-epic-1.md
---

# Story 1-11: Agent Implementations + Orchestrator — All 8 Agents, State Machine, GameService Trait

## Business Context

This is the story that makes the engine "think." All 8 agents get concrete implementations
on the Agent trait from 1-10. The Orchestrator is the state machine that routes player
actions to the right agent, processes responses, and applies state mutations. GameService
is the trait facade that the server calls — enforcing the boundary Python violated (35+
direct state accesses).

This is the highest-value story remaining: the difference between "a collection of types"
and "a game engine."

**Python sources:**
- `sq-2/sidequest/agents/narrator.py` — exploration, description (495 lines)
- `sq-2/sidequest/agents/world_state.py` — state patches, continuity
- `sq-2/sidequest/agents/npc.py` — NPC dialogue, social encounters
- `sq-2/sidequest/agents/combat.py` — combat resolution, dice
- `sq-2/sidequest/agents/chase.py` — chase sequences, pursuit
- `sq-2/sidequest/agents/intent_router.py` — LLM intent classification
- `sq-2/sidequest/agents/hook_refiner.py` — character hook refinement
- `sq-2/sidequest/agents/perception_rewriter.py` — per-character perception
- `sq-2/sidequest/orchestrator.py` — state machine (~1200 lines)

## Technical Guardrails

### Agent Mapping (Rust Names → Python Sources)

| Rust Agent | Python Source | Role |
|---|---|---|
| Narrator | `agents/narrator.py` | Exploration, description, story progression |
| WorldBuilder | `agents/world_state.py` | Game truth, state patches, continuity |
| Ensemble | `agents/npc.py` | NPC dialogue, social encounters |
| CreatureSmith | `agents/combat.py` | Combat resolution, dice, tactical encounters |
| Troper | Trope methods on `orchestrator.py` | Trope progression, beat injection |
| Dialectician | `agents/chase.py` | Chase sequences, pursuit, decision points |
| Resonator | `agents/hook_refiner.py` + `perception_rewriter.py` | Character perception, ability filtering |
| Orchestrator | `orchestrator.py` | State machine, agent routing, turn lifecycle |

### Infrastructure Already Built (1-10)

- `Agent` trait: `name()`, `system_prompt()`
- `ClaudeClient`: subprocess wrapper with timeout, builder pattern
- `JsonExtractor`: 3-tier extraction (direct/fence/freeform)
- `ContextBuilder`: composable sections with attention zones
- `format_helpers`: character_block, location_block, npc_block, inventory_summary
- `prompt_framework`: PromptSection, SectionCategory, AttentionZone, SOUL loading

### Each Agent Implementation Pattern

```rust
struct NarratorAgent {
    system_prompt: String,
}

impl Agent for NarratorAgent {
    fn name(&self) -> &str { "narrator" }
    fn system_prompt(&self) -> &str { &self.system_prompt }
}

impl NarratorAgent {
    fn build_context(&self, snapshot: &GameSnapshot, builder: &mut ContextBuilder) { ... }
    async fn execute(&self, client: &ClaudeClient, context: &str) -> Result<AgentResponse> { ... }
}
```

### GameService Trait (Facade — Port Lesson #1)

```rust
#[async_trait]
pub trait GameService: Send + Sync {
    async fn handle_action(&self, player_id: &str, action: &str) -> Result<ActionResult>;
    fn get_snapshot(&self) -> GameSnapshot;
    async fn request_greeting(&self) -> Result<String>;
}
```

### Orchestrator State Machine Flow

1. Player action arrives
2. Sanitize input (reuse `sanitize` from protocol crate)
3. Classify intent via IntentRouter (Claude CLI call)
4. Dispatch to appropriate agent (Claude CLI call)
5. Parse agent response (narrative text + optional JSON patch)
6. Apply patch to GameSnapshot
7. Compute state delta
8. Tick trope passive progression
9. Return ActionResult { narration, state_delta, combat_events, ... }

- **ADR-001 (Claude CLI Only):** `claude -p` subprocess, no API SDK
- **ADR-005 (Graceful Degradation):** Timeout → degraded response, not error
- **ADR-010 (Intent-Based Agent Routing):** LLM classifies intent to specialist agent
- **ADR-011 (World State JSON Patches):** Structured patches, not freeform text
- **ADR-012 (Agent Session Management):** Persistent sessions via `--session-id`

### Critical: Strip the Python Orchestrator

Python's orchestrator is 1200+ lines because it includes media pipeline, voice routing,
render queue, scene interpreter, music director, audio mixer, TTS. The Rust Orchestrator
handles ONLY: intent routing, agent dispatch, state patch application, state delta
computation, turn lifecycle, trope ticking, and pacing detection.

## Scope Boundaries

**In scope:**
- 8 agent struct implementations with system prompts and context builders
- `WorldStatePatch`, `CombatPatch`, `ChasePatch` struct definitions (agent output types)
- `IntentRouter` with `classify()` method, `Intent` enum, `IntentRoute` struct
- `Orchestrator` struct: state machine, agent dispatch, turn lifecycle
- `GameService` trait definition
- `ActionResult` struct (narration + state_delta + events)

**Out of scope:**
- Infrastructure (Agent trait, ClaudeClient, JsonExtractor, etc.) — built in 1-10
- Media pipeline, voice/TTS, audio — stays in Python daemon
- Character creation agents (freeform_creator, guided_creator) — future story
- Slash command router — server layer (1-12) or client
- Lore/RAG retrieval — not in Rust port scope
- narrator_continuity.py (drift detection) — nice-to-have, not MVP

## AC Context

| AC | Detail |
|----|--------|
| All 8 agents implement Agent trait | name() non-empty, system_prompt() has structural markers |
| Each agent has request/response types | Dedicated typed payloads per agent |
| JsonExtractor validates payloads | WorldStatePatch, CombatPatch, ChasePatch parse from LLM output |
| ContextBuilder feeds all agents | Genre, character, state context assembled per agent |
| GameService sequences agents | Orchestrator routes intent → agent → patch → delta |
| GameService manages snapshots | State delta computed after each action |
| Error handling graceful | Timeout → degraded response ("The narrator pauses..."), not error |
| GameService is the facade | Server depends on trait, never on Orchestrator directly |

## Assumptions

- 8 agents are sufficiently similar that the Agent trait handles them all
- Orchestrator can be tested with mock ClaudeClient (no real Claude calls in tests)
- GameService trait does not need multiplayer design yet (single-player first)
- Stories 1-7 and 1-8 provide the game state types the orchestrator manages
