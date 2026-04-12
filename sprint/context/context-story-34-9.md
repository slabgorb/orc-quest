# Story 34-9: Narrator outcome injection — RollOutcome shapes narration tone

## Overview

Make the dice roll outcome (RollOutcome) visible to the narrator (Claude) so the prose tone matches the mechanical result. A critical success gets enthusiastic narration. A failure gets dramatic setback prose.

**Status:** Setup complete. Ready for TEA (RED phase).

## Story Scope

### What Gets Built
- Narrator prompt context builder enhancement to include `RollOutcome` as a visible tag
- Test coverage for outcome context injection
- Integration test proving outcome flows through dispatcher → narrator

### What Stays Unchanged
- Dispatch flow (34-4 complete)
- Game state logic (outcome is prose-only)
- Narrator's system prompt (Claude already knows how to interpret outcome tags)
- Protocol types (outcome already on the wire)

### Dependency
- **Blocks on:** 34-4 (Dispatch integration) — SHIPPING today
- **Unblocks:** 34-11 (OTEL telemetry) can observe outcome via existing 34-4 spans

## Dice Outcome Values

From `sidequest-protocol/src/message.rs`:

```rust
#[derive(Clone, Copy, Debug, PartialEq)]
#[non_exhaustive]
pub enum RollOutcome {
    CritSuccess,
    Success,
    Fail,
    CritFail,
    #[serde(other)]
    Unknown,
}
```

**Rules (from 34-3):**
- `CritSuccess` fires iff **any d20 rolls a 20** (regardless of DC or modifier)
- `CritFail` fires iff **any d20 rolls a 1** (if both 20 and 1, CritSuccess wins)
- `Success` if total ≥ DC (and no crits)
- `Fail` if total < DC (and no crits)
- Non-d20 pools never crit; only resolve on total vs DC

## Narrator Prompt Integration

### Current State
The narrator receives:
- Character state (abilities, conditions, resources)
- Beat definition (action, flavor text, difficulty)
- Previous turn context

### What's Missing
The outcome of the dice roll is computed (34-3/34-4) but not visible to the narrator. Claude narrates the action without knowing whether the player critically succeeded or critically failed.

### What Gets Added
A **context zone tag** in the narrator prompt:

```
[DICE_OUTCOME: CritSuccess]
The player rolled a natural 20 on the d20 check.
```

Or:

```
[DICE_OUTCOME: Fail]
The player rolled below the difficulty. The attempt falters.
```

**Placement:** In the mechanical context zone alongside other roll facts (total vs DC, modifier applied). Claude's system prompt already interprets `[DICE_OUTCOME: ...]` tags; this just ensures the tag appears.

### Prompt Visibility Principle

The outcome tag must be:
1. **Unambiguous** — Claude can reliably parse it
2. **Distinct** — Different outcomes produce different tags
3. **Contextual** — Present in the mechanical facts zone, not narrative prose
4. **Stable** — Same outcome + same beat = same prompt (modulo state changes)

## Files to Modify

### Primary

- **`sidequest-api/crates/sidequest-agents/src/narrator_prompt.rs`** (or equivalent)
  - Narrator context builder function
  - Add `outcome: RollOutcome` parameter
  - Inject outcome tag into prompt context zone
  - Verify tag is present in final prompt string

### Test Coverage

- **`sidequest-api/crates/sidequest-agents/tests/narrator_context_outcomes_34_9.rs`** (NEW)
  - Unit tests: each RollOutcome variant produces correct tag
  - Integration test: outcome flows through dispatcher → context builder → prompt
  - Mock beat selection + dispatch, verify outcome tag in narration prompt

### No Changes Needed

- `sidequest-protocol` (outcome already defined + wired)
- `sidequest-server/src/dispatch/beat.rs` (34-4 complete)
- Narrator's system prompt (already knows outcome tags)
- UI or client code (outcome is server-side narration context)

## Acceptance Criteria (RED Phase Gate)

All tests must pass and be merged before GREEN phase starts.

### Unit Tests
- [ ] CritSuccess outcome produces `[DICE_OUTCOME: CritSuccess]` tag
- [ ] Success outcome produces `[DICE_OUTCOME: Success]` tag
- [ ] Fail outcome produces `[DICE_OUTCOME: Fail]` tag
- [ ] CritFail outcome produces `[DICE_OUTCOME: CritFail]` tag
- [ ] Unknown outcome is handled (forward-compat fallback)
- [ ] Outcome tag is present in the final prompt string
- [ ] Other context (damage, attributes) is unaffected by outcome injection

### Integration Tests
- [ ] Mock dispatch with known beat + outcome
- [ ] Verify narrator context builder receives the outcome
- [ ] Verify outcome tag appears in narration prompt
- [ ] Full round-trip: beat selection → dice resolution → narrator context → prompt

### No Regressions
- [ ] Existing narrator tests still pass
- [ ] No changes to game state logic
- [ ] No changes to dispatch flow
- [ ] No changes to protocol types

## Testing Strategy

### Structure
```
sidequest-api/crates/sidequest-agents/tests/
  ├── narrator_context_outcomes_34_9.rs
  │   ├── test_crit_success_outcome_tag
  │   ├── test_success_outcome_tag
  │   ├── test_fail_outcome_tag
  │   ├── test_crit_fail_outcome_tag
  │   ├── test_unknown_outcome_handled
  │   ├── test_outcome_in_final_prompt
  │   └── test_full_dispatch_to_narration_flow
```

### Unit Test Pattern
```rust
#[test]
fn test_crit_success_outcome_tag() {
    let outcome = RollOutcome::CritSuccess;
    let context = build_narrator_context(
        beat,
        character_state,
        outcome,
    );
    assert!(context.contains("[DICE_OUTCOME: CritSuccess]"));
}
```

### Integration Test Pattern
```rust
#[tokio::test]
async fn test_full_dispatch_to_narration_flow() {
    // Mock beat selection with known outcome
    let roll_outcome = RollOutcome::Fail;
    
    // Call dispatcher
    let narrative_context = dispatcher.build_narrator_context(
        beat,
        character,
        roll_outcome,
    );
    
    // Verify outcome is visible
    assert!(narrative_context.contains("[DICE_OUTCOME: Fail]"));
}
```

## OTEL Observability (34-11 Scope)

This story does NOT add OTEL telemetry. However:
- 34-4 already emits `dice.result_broadcast` span (includes outcome)
- This story makes outcome visible in the prompt
- 34-11 can add `narrator.outcome_injected` event if desired (post-hoc observability)

The outcome is already observable through:
1. `DiceResult` payload on the wire (34-4 span)
2. Prompt inspection (outcome tag in context zone)
3. Narration text (Claude's prose reflects the tone)

## Design Constraints

1. **Outcome is input, not output.** The narrator receives the outcome as a given fact, not a decision. The outcome drives tone, not story content.

2. **Outcome does not override mechanics.** A critical success still applies the same stat bonus. The outcome is aesthetic (prose tone), not mechanical.

3. **No prompt system change.** Claude's system prompt stays fixed. Outcome injection is context enrichment, not system prompt modification.

4. **No state pollution.** The outcome is for narration only. It does not affect character state, turn order, or future decisions.

5. **Stable outcome per roll.** Same seed + same dice pool = same outcome. Once the outcome is broadcast (34-4), it cannot change.

## Key References

- **Epic context:** `sprint/context/context-epic-34.md` — full architecture, data flow, scope boundaries
- **34-4 dispatch:** `sidequest-api/crates/sidequest-server/src/dispatch/beat.rs` — where outcome is generated and broadcast
- **Protocol outcome:** `sidequest-api/crates/sidequest-protocol/src/message.rs` — `RollOutcome` enum, `DiceResultPayload`
- **Narrator crate:** `sidequest-api/crates/sidequest-agents/src/` — prompt context builder
- **ADRs:** 074 (protocol), 075 (rendering), referenced in epic context

## Notes for TEA (RED Phase)

### Focus Areas
1. **Outcome visibility:** Tests must prove the outcome tag is unambiguous and present in the prompt
2. **Context stability:** Same outcome should produce the same prompt tag (deterministic)
3. **No side effects:** Outcome injection must not affect game state or other narrative context
4. **Integration:** Full path from dice resolution → narrator context → prompt must be covered

### Questions to Resolve
- What is the exact tag format? (suggested: `[DICE_OUTCOME: {variant}]`)
- Where in the prompt does the tag go? (answer: mechanical context zone, near other roll facts)
- How does Claude's system prompt interpret the tag? (answer: already does; this is known from existing promptcraft)

### Watch Out For
- **Silent outcome.** If the outcome is wired but the tag doesn't appear in the prompt, tests fail to catch it.
- **Dead code.** The outcome builder must have a non-test consumer (the narrator context builder).
- **Prompt leakage.** The tag must not appear in the narrative prose itself — only in context.

## Ready for TEA
Session file complete. Branch ready. This story awaits RED phase test development.
