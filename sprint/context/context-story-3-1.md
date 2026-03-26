---
parent: context-epic-3.md
---

# Story 3-1: Agent Telemetry Spans — #[instrument] on All Decision Points, JSON Tracing Subscriber, RUST_LOG Filtering

## Business Context

Every turn in SideQuest is a chain of AI decisions: classify intent, pick an agent, call Claude,
extract JSON from freeform text, apply patches, tick tropes. None of these steps are deterministic.
When the narrator says something wrong — referencing a dead NPC, ignoring combat, losing a quest
thread — the operator needs to see which decision went sideways.

Story 1-12 sets up basic `tracing_subscriber::fmt::init()`. This story replaces that with a
composable subscriber stack and instruments every decision point with semantic fields that describe
what the game engine decided, not just that a function was called. The distinction matters: a span
that says `IntentRouter::classify duration=12ms` is transport telemetry. A span that says
`IntentRouter::classify intent=Combat agent=CreatureSmith confidence=0.92 fallback_used=false` is
agent telemetry. This story builds Layer 2 of the ADR-031 three-layer model.

**Python reference:** Python has no structured telemetry. It logs via `logger.info()` with
ad-hoc string formatting. Finding "why did the narrator ignore combat?" means grepping log files
and reconstructing the turn manually. The tracing crate makes this structural.

**ADR:** ADR-031 (Game Watcher — Semantic Telemetry), Layer 2
**Depends on:** Story 2-5 (orchestrator turn loop), Story 1-12 (basic tracing init)

## Technical Approach

### Composable Subscriber Stack

Replace the bare `fmt::init()` in `sidequest-server/src/main.rs` with a layered subscriber:

```rust
use tracing_subscriber::{fmt, EnvFilter, Registry};
use tracing_subscriber::prelude::*;

fn init_tracing() {
    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("sidequest=debug,tower_http=info"));

    let json_layer = fmt::layer()
        .json()
        .with_target(true)
        .with_span_list(true)
        .with_current_span(true);

    let pretty_layer = if cfg!(debug_assertions) {
        Some(fmt::layer().pretty())
    } else {
        None
    };

    Registry::default()
        .with(env_filter)
        .with(json_layer)
        .with(pretty_layer)
        .init();
}
```

The `EnvFilter` respects `RUST_LOG` so operators can zoom in: `RUST_LOG=sidequest_agents::orchestrator=trace`
shows every span in the turn loop. `RUST_LOG=sidequest=warn` silences everything except warnings.
The pretty layer activates only in debug builds for local dev readability.

### Span Instrumentation Pattern

Every decision point gets `#[instrument]` with `skip` for large/non-Display types and `fields`
for semantic game data. Fields that aren't known at span entry use `tracing::field::Empty` and
get populated via `Span::current().record()` after the decision is made:

```rust
use tracing::{instrument, Span};

#[instrument(
    skip(self, input, state),
    fields(
        player_input = %input,
        classified_intent = tracing::field::Empty,
        agent_routed_to = tracing::field::Empty,
        confidence = tracing::field::Empty,
        fallback_used = tracing::field::Empty,
    )
)]
pub fn classify(&self, input: &str, state: &GameState) -> IntentRoute {
    // ... classification logic ...
    let route = IntentRoute { intent, agent, confidence, reasoning };

    let span = Span::current();
    span.record("classified_intent", &tracing::field::display(&route.intent));
    span.record("agent_routed_to", &tracing::field::display(&route.agent));
    span.record("confidence", &route.confidence);
    span.record("fallback_used", &fallback_used);

    route
}
```

This pattern — declare fields empty, record after computation — is idiomatic tracing. The span
is open for the entire function, so timing is automatic. The semantic fields appear in the JSON
output alongside the timing data.

### Seven Decision-Point Spans

Each span targets a specific decision in the turn pipeline:

**1. IntentRouter::classify** — Why did this input go to this agent?
```rust
#[instrument(skip(self, input, state), fields(
    player_input = %input,
    classified_intent = tracing::field::Empty,
    agent_routed_to = tracing::field::Empty,
    confidence = tracing::field::Empty,
    fallback_used = tracing::field::Empty,
))]
```

**2. Agent invocation (call_agent)** — How long did Claude take? How much did it say?
```rust
#[instrument(skip(self, system_prompt, context), fields(
    agent_name = %agent,
    token_count_in = tracing::field::Empty,
    token_count_out = tracing::field::Empty,
    duration_ms = tracing::field::Empty,
    raw_response_len = tracing::field::Empty,
))]
```

**3. JsonExtractor::extract** — Did extraction succeed on first try or fall back?
```rust
#[instrument(skip(self, raw_text), fields(
    extraction_tier = tracing::field::Empty,
    target_type = std::any::type_name::<T>(),
    success = tracing::field::Empty,
))]
```

**4. GameSnapshot::apply_world_patch / apply_combat_patch / apply_chase_patch** — What changed?
```rust
#[instrument(skip(self, patch), fields(
    patch_type = "world",  // or "combat", "chase"
    fields_changed = tracing::field::Empty,
))]
```

**5. TropeEngine::tick** — Did any story beats fire this turn?
```rust
#[instrument(skip(self, state, narration), fields(
    tropes_advanced = tracing::field::Empty,
    beats_fired = tracing::field::Empty,
    thresholds_crossed = tracing::field::Empty,
))]
```

**6. ContextBuilder::compose** — How big is the prompt? Which sections dominate?
```rust
#[instrument(skip(self, state, genre_pack), fields(
    agent = %agent,
    sections_count = tracing::field::Empty,
    total_tokens = tracing::field::Empty,
    zone_distribution = tracing::field::Empty,
))]
```

**7. compute_delta** — Did the state actually change?
```rust
#[instrument(skip(before, after), fields(
    fields_changed = tracing::field::Empty,
    is_empty = tracing::field::Empty,
))]
```

### JSON Output Shape

With the JSON layer, a single span produces output like:

```json
{
  "timestamp": "2026-03-25T14:32:01.123Z",
  "level": "INFO",
  "span": {
    "name": "classify",
    "player_input": "I attack the goblin",
    "classified_intent": "Combat",
    "agent_routed_to": "CreatureSmith",
    "confidence": 0.92,
    "fallback_used": false
  },
  "target": "sidequest_agents::agents::intent_router",
  "elapsed_ms": 12
}
```

This is greppable, parseable, and carries the semantic context a human needs to understand the
decision. Story 3-6 (watcher WebSocket) will eventually stream these as structured events to a
live dashboard.

### Rust Concept: Deferred Field Population

Python logging computes values eagerly: `logger.info(f"classified: {intent}")`. Rust's tracing
separates declaration from population. `tracing::field::Empty` declares a field exists in the
span schema but has no value yet. `Span::current().record("field", &value)` fills it in later.
This is zero-cost when the subscriber filters the span out — the field is never computed. Python
has no equivalent; every f-string is always evaluated.

## Scope Boundaries

**In scope:**
- Replace `tracing_subscriber::fmt::init()` with composable subscriber (Registry + layers)
- JSON format layer for production output
- Pretty format layer for dev builds (debug_assertions)
- `EnvFilter` for `RUST_LOG` support with sensible defaults
- `#[instrument]` on all seven decision points listed above
- Deferred field population via `Span::current().record()`
- Semantic game fields on every span (not just function name + timing)

**Out of scope:**
- TurnRecord struct (story 3-2)
- mpsc channel to validator (story 3-2)
- Validation logic (stories 3-3 through 3-5)
- Watcher WebSocket endpoint (story 3-6)
- Transport telemetry / tower-http tracing (Layer 1 — already handled by tower-http defaults)
- OpenTelemetry export (not planned; JSON logs are sufficient)
- Log rotation or log file output (ops concern, not application concern)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Subscriber composable | `init_tracing()` uses `Registry::default().with(...)` pattern, not `fmt::init()` |
| JSON output | Running with default config produces valid JSON lines to stdout |
| Pretty dev output | Debug builds show human-readable colored output |
| RUST_LOG filtering | `RUST_LOG=sidequest_agents=trace` shows agent spans; `RUST_LOG=warn` silences them |
| IntentRouter span | `classify()` span contains player_input, classified_intent, agent_routed_to, confidence, fallback_used |
| Agent invocation span | `call_agent()` span contains agent_name, token_count_in, token_count_out, duration_ms, raw_response_len |
| Extractor span | `extract()` span contains extraction_tier, target_type, success |
| Patch spans | `apply_*_patch()` spans contain patch_type and fields_changed |
| Trope tick span | Trope tick span contains tropes_advanced, beats_fired, thresholds_crossed |
| Context builder span | `compose()` span contains sections_count, total_tokens, zone_distribution |
| Delta span | `compute_delta()` span contains fields_changed and is_empty |
| Deferred fields | Spans use `tracing::field::Empty` + `Span::current().record()`, not eager computation |
| No performance regression | Spans are zero-cost when filtered out via RUST_LOG |
