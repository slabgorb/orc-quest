---
parent: context-epic-18.md
workflow: tdd
---

# Story 18-6: Prompt Inspector Tab

## Business Context

When narration doesn't match expectations — Claude ignores lore, forgets a character's
personality, misses combat context — the first question is "what did Claude actually
see?" Currently there's no way to inspect the assembled prompt. The prompt framework
(1,484 LOC) builds zone-ordered prompts (Primacy, Situational, Anchoring, Grounding)
but the final product is invisible. This tab makes the prompt a first-class debugging
artifact.

## Technical Approach

### API: New WatcherEventType

Add `PromptAssembled` variant to `WatcherEventType` enum in `lib.rs`.

Emit from the ContextBuilder after zone assembly completes, in the prompt framework
code (`sidequest-agents/src/prompt_framework/`). Fields:

```json
{
  "turn_number": 18,
  "agent": "narrator",
  "total_tokens": 4200,
  "zones": [
    { "name": "Primacy", "content": "You are the narrator...", "token_count": 800 },
    { "name": "Situational", "content": "[LOCATION] The tavern...", "token_count": 1200 },
    { "name": "Anchoring", "content": "[RULES] Combat resolution...", "token_count": 1400 },
    { "name": "Grounding", "content": "[HISTORY] Last 3 turns...", "token_count": 800 }
  ]
}
```

**Token counting:** Use the existing token estimation (word_count * 1.3 or whatever
the codebase uses). Exact counts aren't needed — relative proportions matter more.

**Note:** The full prompt text may be large. Consider emitting zone boundaries +
content separately, or truncating content in the event and providing a fetch endpoint
for the full text.

### UI: New Prompt Tab

Add `PromptTab` to the dashboard tab bar.

**Layout:**
- **Turn selector** — dropdown matching Timeline tab turns
- **Zone summary bar** — horizontal stacked bar showing token allocation per zone,
  color-coded (Primacy=blue, Situational=green, Anchoring=amber, Grounding=gray)
- **Prompt text area** — full prompt with zone boundary markers as colored left
  borders, same colors as summary bar
- **Search** — find text within the prompt (highlights matches)
- **Zone filter** — toggle zones on/off to focus on specific sections

**Turn comparison (stretch):**
- Side-by-side view of two turns' prompts
- Diff highlighting showing what changed between turns

### Key Files

| File | Change |
|------|--------|
| `sidequest-server/src/lib.rs` | Add `PromptAssembled` to WatcherEventType |
| `sidequest-agents/src/prompt_framework/` | Emit prompt event after assembly |
| `sidequest-agents/src/context_builder.rs` | Emit point — after build_context() |
| `sidequest-ui/src/components/Dashboard/types.ts` | Add PromptProfile type |
| `sidequest-ui/src/components/Dashboard/hooks/useDashboardSocket.ts` | Handle prompt events |
| `sidequest-ui/src/components/Dashboard/tabs/Prompt/PromptTab.tsx` | New tab |
| `sidequest-ui/src/components/Dashboard/DashboardLayout.tsx` | Add Prompt tab |

### Wiring Consideration

The prompt framework lives in `sidequest-agents`, which doesn't have access to
`AppState::send_watcher_event()`. Options:
1. Pass a watcher callback/channel into the agent pipeline
2. Use tracing spans + the existing span→watcher bridge in main.rs
3. Return the prompt metadata from the agent call and emit in dispatch/mod.rs

Option 3 is simplest — the orchestrator returns the prompt as part of ActionResult,
dispatch emits the watcher event. Keeps the dependency direction clean.

## Scope Boundaries

**In scope:**
- New WatcherEventType variant and emit point
- PromptTab with zone-labeled text and summary bar
- Search within prompt
- Turn selector

**Out of scope:**
- Turn comparison / diff view (stretch goal, not required)
- Editing prompts from the dashboard
- Token counting accuracy (estimation is fine)
- Prompt caching or replay

## Acceptance Criteria

1. **Prompt tab appears** in dashboard tab bar
2. **Zone summary bar** shows token allocation per zone with color coding
3. **Prompt text** displays with zone boundary markers (colored left borders)
4. **Turn selector** allows viewing prompts from different turns
5. **Search** highlights matches within prompt text
6. **Agent name shown** — which agent (narrator, ensemble, creature_smith) received this prompt
7. **Events flow** — `prompt_assembled` events visible in Console tab
