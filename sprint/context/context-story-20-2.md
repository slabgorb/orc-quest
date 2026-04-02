---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-2: scene_mood and scene_intent tool calls

## Business Context

This is Phase 2 of ADR-057 narrator crunch separation. Story 20-1 shipped `assemble_turn` infrastructure and action preprocessors; this story moves two simple enum fields from the narrator's JSON block to typed tool calls with single-string arguments.

**Current state:** Narrator emits JSON block with `scene_mood` and `scene_intent` fields. Extractor.rs parses these. No validation — malformed enums pass through silently.

**Target state:** Narrator calls `set_mood("tension")` and `set_intent("combat_prep")` during narration (subprocess tool calls). `assemble_turn` collects tool results and validates against enum before merging into `ActionResult`. Narrator JSON block no longer includes these fields.

This unblocks Phase 3 and shrinks the narrator system prompt by ~200 tokens of schema documentation.

## Technical Guardrails

### Tool Call Mechanism (ADR-056 + ADR-057)
Tools are subprocess binaries invoked via `claude -p --allowedTools Bash(set_mood, set_intent)`. The Claude CLI captures tool call results in structured output. The orchestrator parses the tool results and passes them to `assemble_turn`.

**Tool signatures:**
- `set_mood(mood: String)` → JSON: `{ "mood": "validated_enum_value", "valid": true }` or `{ "valid": false, "error": "..." }`
- `set_intent(intent: String)` → JSON: `{ "intent": "validated_enum_value", "valid": true }` or `{ "valid": false, "error": "..." }`

### Enum Validation
Valid `scene_mood` values: `tension`, `wonder`, `melancholy`, `triumph`, `foreboding`, `calm`, `exhilaration`, `reverence`

Valid `scene_intent` values: `dialogue`, `exploration`, `combat_prep`, `stealth`, `negotiation`, `escape`, `investigation`, `social`

### OTEL Observability
Each tool call is a discrete subprocess visible in OTEL spans. Emit:
- `tool.name` = "set_mood" or "set_intent"
- `tool.args.input` = the argument passed
- `tool.result.valid` = boolean
- `tool.result.value` = validated enum value or error

### NarratorExtraction Field Handling
Keep `scene_mood` and `scene_intent` fields in `NarratorExtraction` (for transition period). `assemble_turn` MUST override them with validated tool call results if tools fired. Tool values always take precedence.

### Narrator Prompt Shrinkage
Remove ~200 tokens of schema documentation for `scene_mood` and `scene_intent`. Replace with: "Call `set_mood(mood_string)` and `set_intent(intent_string)` during narration as appropriate."

## Scope Boundaries

**In scope:**
- Build `set_mood` and `set_intent` tools (subprocess binaries or functions)
- Validate tool arguments against enum definitions
- Wire tools into `claude -p --allowedTools` invocation in the orchestrator
- Update `assemble_turn` to accept and merge tool call results
- Override narrator's fields in `ActionResult` with validated tool call results
- Remove `scene_mood` and `scene_intent` schema documentation from narrator system prompt
- Add OTEL instrumentation for tool calls
- Write tests validating tool invocation, enum validation, and `ActionResult` override

**Out of scope:**
- Deleting the `scene_mood` and `scene_intent` fields from `NarratorExtraction` (Phase 8)
- Deleting `extractor.rs` (Phase 8)
- Moving other JSON fields to tools (Phase 3+)
- Narrator prompt refactoring beyond removing schema docs

## AC Context

### Given the narrator classifies a scene as "tension"
When the narrator calls `set_mood("tension")` during narration,
Then the `assemble_turn` function receives the tool result,
And the final `ActionResult.scene_mood` is set to "tension" (not the narrator's JSON value),
And OTEL logs the tool call with `tool.name="set_mood"`, `tool.result.value="tension"`.

### Given an invalid mood string "totally_made_up"
When the tool is invoked with that argument,
Then the tool returns `{ "valid": false, "error": "..." }`,
And `assemble_turn` either uses the narrator's fallback value or marks the turn degraded,
And OTEL logs `tool.result.valid=false`.

### Given the narrator doesn't call set_mood during a turn
When `assemble_turn` is invoked without a tool call,
Then `ActionResult.scene_mood` uses the narrator's extracted value (if present),
And no OTEL "tool fired" event is logged.

### Given the narrator's JSON block includes `scene_mood: "wonder"`
And the narrator also calls `set_mood("triumph")` during narration,
Then `ActionResult.scene_mood` = "triumph" (tool result takes precedence),
And the narrator's JSON value is discarded.

### Given all story tests pass
And `cargo build -p sidequest-server` succeeds on the feature branch,
And the branch is pushed to `github.com/slabgorb/sidequest-api/feat/20-2-scene-mood-intent-tools`,
Then the story is complete.
