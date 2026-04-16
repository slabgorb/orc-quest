---
parent: context-epic-38.md
workflow: trivial
---

# Story 38-8: Extend-and-return rule

## Business Context

The MVP interaction table only authors the `merge` starting state. After a turn resolves, both pilots are in a new geometric relationship (tail_on, quartering, opening, etc.) — but the MVP has no second interaction table for those states. Without a reset rule, the game either ends after one exchange or the engine has no valid table to look up the next turn's resolution.

The extend-and-return rule provides multi-exchange continuity: after a no-hit turn where the engagement is opening (`closure: opening_fast`), both actors reset to the merge starting state with their current energy carried over. This creates the 3-exchange duel arc the paper playtest produced — commit, break, re-merge, commit again — without requiring additional 16-cell interaction tables for every possible post-turn geometry.

ADR-077 recommends starting with this as an engine rule with content override capability, not a pure content clause.

## Technical Guardrails

**Decision: Engine rule or content clause?**
- ADR-077 Open Question #5 recommends: engine rule with content override
- The rule is: "after any turn where no hit landed AND at least one actor's descriptor has `closure: opening_fast`, reset both actors to the confrontation's default starting state with current energy preserved"
- Content can override via a future `post_turn_rule` field on the confrontation def

**Key files:**
- If engine rule: `sidequest-server/src/dispatch/sealed_letter.rs` — add post-resolution step in the `SealedLetterLookup` handler
- If content clause: `sidequest-content/genre_packs/space_opera/dogfight/interactions_mvp.yaml` — add a `post_turn` section
- Either way: `descriptor_schema.yaml` starting states section defines what "reset to merge" means

**Patterns to follow:**
- The reset preserves energy — it is NOT a full state reset. Only geometric fields (bearing, range, aspect, closure, gun_solution) reset to the starting state values
- `gun_solution` MUST reset to `false` on extend-and-return (no free shots after a break)

**What NOT to touch:**
- The interaction table cell deltas — they describe the immediate post-maneuver state, not the post-reset state
- TurnBarrier — the barrier already handles commit cycles; the reset is applied between cycles

## Scope Boundaries

**In scope:**
- Define the extend-and-return rule (conditions and effects)
- Implement as either engine rule in `sealed_letter.rs` or content clause in `interactions_mvp.yaml`
- Preserve energy across resets; reset only geometric descriptor fields
- Document the rule clearly enough that the paper playtest (38-9) can apply it

**Out of scope:**
- Additional starting states beyond merge (38-10 handles tail_chase)
- Content override mechanism (`post_turn_rule` field) — future story if needed
- Damage carry-over rules (hull damage persists naturally via `per_actor_state`; no special handling)

## AC Context

**AC1: Reset triggers on correct conditions**
- The rule fires when: (a) no hit landed this turn (neither actor's `gun_solution` was true, OR gun_solution was true but the shot missed — pending damage model from 38-7), AND (b) at least one actor's post-resolution descriptor has `closure: opening_fast`
- Verify: after a `[straight, straight]` turn (Clean merge — both at `closure: opening`, not `opening_fast`), the rule should NOT fire. After a `[kill_rotation, straight]` turn where Red has `closure: opening_fast` and Blue has `closure: opening_fast`, the rule SHOULD fire if no hit landed.

**AC2: Reset preserves energy, clears geometry**
- After reset: `target_bearing: "12"`, `target_range: close`, `target_aspect: head_on`, `closure: closing_fast`, `gun_solution: false` (all from merge starting state)
- Energy values carry over from the previous turn's resolved state — NOT reset to 60
- Verify: a pilot who spent 30 energy on a loop in turn 1 enters the re-merge with 30 energy, not 60

**AC3: Rule is documented for paper playtest consumption**
- The rule must be expressible in plain language for the GM running `duel_01.md`
- Suggestion: add a `## Post-Turn Rules` section to `interactions_mvp.yaml` or to `duel_01.md` itself
