---
parent: context-epic-3.md
---

# Story 3-3: Patch Legality Checks — Deterministic Validation of State Mutations Against Game Rules

## Business Context

The AI narrator generates state patches (WorldStatePatch, CombatPatch, ChasePatch) that
mutate the GameSnapshot every turn. Most of the time these are fine. But occasionally the
LLM produces patches that violate deterministic game rules — an NPC healed above max HP,
a combat action applied when nobody is in combat, an item materializing from nowhere. These
aren't subtle narrative problems; they're mechanical contradictions that a computer can catch
without understanding the story.

This is the first validation module in the Game Watcher pipeline. It runs on the cold path
after each turn, receiving TurnRecords via the tokio::mpsc channel established in story 3-2.
Every check is pure logic — no async, no I/O, no LLM calls. This makes it fast, deterministic,
and easy to test with crafted records.

The Python codebase has no equivalent. State patches in sq-2 are applied without validation;
bugs surface only when the player notices something wrong ("wait, that NPC is dead — why is
she talking?"). The Game Watcher replaces that hope-based debugging with structured flagging.

**ADR:** ADR-031 (semantic telemetry, human-judgment principle)
**Depends on:** Story 3-2 (TurnRecord assembly and mpsc channel)

## Technical Approach

### Validation Result Type

Each check returns a list of results. Warnings are suspicious but might be intentional;
violations are mechanical impossibilities.

```rust
#[derive(Debug, Clone)]
pub enum ValidationResult {
    Ok,
    Warning(String),
    Violation(String),
}
```

### Check Functions

Each check is a standalone function taking a `&TurnRecord` and returning `Vec<ValidationResult>`.
This makes them independently testable and composable.

```rust
pub fn check_hp_bounds(record: &TurnRecord) -> Vec<ValidationResult> {
    let mut results = Vec::new();
    for character in &record.snapshot_after.characters {
        if character.hp > character.max_hp {
            results.push(ValidationResult::Violation(
                format!("{}: HP {} exceeds max_hp {}", character.name, character.hp, character.max_hp)
            ));
        }
        if character.hp < 0 {
            results.push(ValidationResult::Violation(
                format!("{}: HP {} is below zero", character.name, character.hp)
            ));
        }
    }
    for npc in &record.snapshot_after.npcs {
        if npc.creature_core.hp > npc.creature_core.max_hp {
            results.push(ValidationResult::Violation(
                format!("NPC {}: HP {} exceeds max_hp {}", npc.name, npc.creature_core.hp, npc.creature_core.max_hp)
            ));
        }
    }
    results
}
```

### Dead Entity Action Check

Compares snapshot_before and snapshot_after to detect dead entities gaining new activity.

```rust
pub fn check_dead_entity_actions(record: &TurnRecord) -> Vec<ValidationResult> {
    let mut results = Vec::new();
    for npc_before in &record.snapshot_before.npcs {
        if npc_before.creature_core.statuses.contains(&"dead".to_string()) {
            // Find same NPC in snapshot_after
            if let Some(npc_after) = record.snapshot_after.npcs.iter()
                .find(|n| n.name == npc_before.name)
            {
                // Flag if dead NPC gained new statuses or HP changed upward
                if npc_after.creature_core.hp > npc_before.creature_core.hp {
                    results.push(ValidationResult::Warning(
                        format!("Dead NPC {} gained HP ({} -> {})",
                            npc_before.name, npc_before.creature_core.hp, npc_after.creature_core.hp)
                    ));
                }
            }
        }
    }
    results
}
```

### Combat/Chase State Coherence

```rust
pub fn check_combat_coherence(record: &TurnRecord) -> Vec<ValidationResult> {
    let has_combat_patch = record.patches_applied.iter()
        .any(|p| matches!(p, PatchSummary::Combat(_)));
    if has_combat_patch && !record.snapshot_before.combat.in_combat {
        return vec![ValidationResult::Violation(
            "CombatPatch applied but combat.in_combat is false".into()
        )];
    }
    vec![]
}

pub fn check_chase_coherence(record: &TurnRecord) -> Vec<ValidationResult> {
    let has_chase_patch = record.patches_applied.iter()
        .any(|p| matches!(p, PatchSummary::Chase(_)));
    if has_chase_patch && !record.snapshot_before.chase.in_chase {
        return vec![ValidationResult::Violation(
            "ChasePatch applied but chase.in_chase is false".into()
        )];
    }
    vec![]
}
```

### Location Validity

```rust
pub fn check_location_validity(record: &TurnRecord) -> Vec<ValidationResult> {
    let before_location = &record.snapshot_before.location;
    let after_location = &record.snapshot_after.location;
    if before_location != after_location {
        let known = &record.snapshot_after.discovered_regions;
        if !known.contains(after_location) {
            return vec![ValidationResult::Warning(
                format!("Location changed to '{}' which is not in discovered_regions", after_location)
            )];
        }
    }
    vec![]
}
```

### Inventory Conservation

Large inventory changes (items appearing without narrative justification) get flagged as
warnings rather than violations, since this check straddles the line between deterministic
and heuristic. A strict version counts items before and after; if the count increases by
more than a threshold (e.g., 3 items in a single turn), emit a warning.

```rust
pub fn check_inventory_conservation(record: &TurnRecord) -> Vec<ValidationResult> {
    let mut results = Vec::new();
    for char_after in &record.snapshot_after.characters {
        let items_after = char_after.inventory.items.len();
        if let Some(char_before) = record.snapshot_before.characters.iter()
            .find(|c| c.name == char_after.name)
        {
            let items_before = char_before.inventory.items.len();
            if items_after > items_before + 3 {
                results.push(ValidationResult::Warning(
                    format!("{}: inventory grew by {} items in one turn",
                        char_after.name, items_after - items_before)
                ));
            }
        }
    }
    results
}
```

### Runner

A top-level function runs all checks and emits tracing events.

```rust
pub fn run_legality_checks(record: &TurnRecord) -> Vec<ValidationResult> {
    let checks: Vec<fn(&TurnRecord) -> Vec<ValidationResult>> = vec![
        check_hp_bounds,
        check_dead_entity_actions,
        check_combat_coherence,
        check_chase_coherence,
        check_location_validity,
        check_inventory_conservation,
    ];

    let mut all_results = Vec::new();
    for check in checks {
        let results = check(record);
        for result in &results {
            match result {
                ValidationResult::Warning(msg) => {
                    tracing::warn!(component = "watcher", check = "patch_legality", %msg);
                }
                ValidationResult::Violation(msg) => {
                    tracing::warn!(component = "watcher", check = "patch_legality", severity = "violation", %msg);
                }
                ValidationResult::Ok => {}
            }
        }
        all_results.extend(results);
    }
    all_results
}
```

### Testing Strategy

Tests are pure unit tests with hand-crafted TurnRecords. No async runtime needed.

```rust
#[test]
fn hp_exceeds_max_is_violation() {
    let record = make_record_with_hp(999, 50); // hp=999, max_hp=50
    let results = check_hp_bounds(&record);
    assert!(results.iter().any(|r| matches!(r, ValidationResult::Violation(_))));
}

#[test]
fn combat_patch_without_active_combat_is_violation() {
    let record = make_record_with_combat_patch(false); // in_combat=false
    let results = check_combat_coherence(&record);
    assert!(results.iter().any(|r| matches!(r, ValidationResult::Violation(_))));
}

#[test]
fn dead_npc_gaining_hp_is_warning() {
    let record = make_record_with_dead_npc_healed();
    let results = check_dead_entity_actions(&record);
    assert!(results.iter().any(|r| matches!(r, ValidationResult::Warning(_))));
}
```

### Rust Concept: Pure Functions for Validation

This story is a good showcase for Rust's strength at pure logic. Every check function is
`fn(&TurnRecord) -> Vec<ValidationResult>` — no `&mut`, no `async`, no side effects except
tracing at the runner level. This means:
- Tests don't need tokio test runtime
- Functions are trivially composable
- Adding new checks is just writing another function and adding it to the array

Compare with Python where validation would likely be methods on a class with access to
`self.game_state`, making them harder to test in isolation.

## Scope Boundaries

**In scope:**
- `ValidationResult` enum (Ok, Warning, Violation)
- Six deterministic check functions: HP bounds, dead entity actions, combat coherence, chase coherence, location validity, inventory conservation
- Runner function that executes all checks and emits tracing events
- Unit tests with crafted TurnRecords for each check
- All tracing events tagged `component="watcher"`, `check="patch_legality"`

**Out of scope:**
- Narrative content analysis (story 3-4 — entity reference validation)
- Trope alignment checks (story 3-8)
- Automated remediation or patch rejection — watcher flags, human decides
- Persisting validation results to database
- Heuristic or ML-based validation approaches
- Integration with the watcher WebSocket (story 3-6 wires that up)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| HP bounds checked | After-patch HP exceeding max_hp or below 0 produces Violation |
| Dead entity flagged | NPC with "dead" status in snapshot_before gaining HP produces Warning |
| Combat coherence | CombatPatch applied when combat.in_combat is false produces Violation |
| Chase coherence | ChasePatch applied when chase.in_chase is false produces Violation |
| Location validity | Location change to region not in discovered_regions produces Warning |
| Inventory conservation | More than 3 items gained in a single turn produces Warning |
| Tracing events emitted | Every Warning and Violation emits tracing::warn! with component="watcher" and check="patch_legality" |
| Pure unit tests | All checks tested with hand-crafted TurnRecords, no async runtime |
| Valid turns pass clean | A well-formed TurnRecord with legal patches produces no Warnings or Violations |
