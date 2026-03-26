---
parent: context-epic-6.md
---

# Story 6-6: World Materialization — Campaign Maturity Levels and History Chapter Application to GameSnapshot

## Business Context

A fresh campaign should feel sparse — the world is new, unexplored. A veteran campaign
should feel rich with accumulated history. World materialization determines campaign
maturity from turn count and story beats fired, then bootstraps the `GameSnapshot` with
appropriate history chapters. In Python, this was implicit — the world just accumulated
state. The Rust port makes maturity an explicit enum that controls what context the
narrator receives.

**Python ref:** `sq-2/docs/architecture/active-world-pacing-design.md` (materialization section)
**Depends on:** Story 2-5 (orchestrator turn loop — provides GameSnapshot and turn infrastructure)

## Technical Approach

Campaign maturity is derived from game state:

```rust
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum CampaignMaturity {
    Fresh,    // turns 0-5: minimal history, world is new
    Early,    // turns 6-20: factions introduced, stakes emerging
    Mid,      // turns 21-50: established relationships, escalating tensions
    Veteran,  // turns 51+: deep history, faction conflicts in motion
}

impl CampaignMaturity {
    pub fn from_snapshot(snapshot: &GameSnapshot) -> Self {
        let turn = snapshot.turn_number;
        let beats_fired = snapshot.total_beats_fired();
        // Beats can accelerate maturity — a dramatic early game matures faster
        let effective_turns = turn + (beats_fired / 2);
        match effective_turns {
            0..=5   => Self::Fresh,
            6..=20  => Self::Early,
            21..=50 => Self::Mid,
            _       => Self::Veteran,
        }
    }
}
```

History chapters are materialized per maturity level:

```rust
pub fn materialize_world(snapshot: &mut GameSnapshot, genre_pack: &GenrePack) {
    let maturity = CampaignMaturity::from_snapshot(snapshot);
    let chapters = genre_pack.history_chapters_for(maturity);
    snapshot.world_history = chapters;
    snapshot.campaign_maturity = maturity;
}
```

Genre packs define history chapters keyed by maturity in YAML. The `Fresh` level gets
a one-line setting description; `Veteran` gets faction conflicts and established lore.

## Scope Boundaries

**In scope:**
- `CampaignMaturity` enum with `from_snapshot()` derivation
- `materialize_world()` function applying history chapters
- `campaign_maturity` and `world_history` fields on `GameSnapshot`
- Genre pack YAML schema for maturity-keyed history chapters
- Tests for maturity derivation and chapter application

**Out of scope:**
- Dynamic history generation by LLM (chapters are from genre pack YAML)
- Cross-session maturity persistence (uses turn count from current session)
- Faction agendas (story 6-4, parallel concern)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Maturity derivation | `from_snapshot()` returns correct level for turn ranges |
| Beat acceleration | Beats fired contribute to effective turn count |
| History application | `materialize_world()` populates `world_history` from genre pack |
| Fresh is sparse | Fresh maturity yields minimal history (1-2 lines) |
| Veteran is rich | Veteran maturity yields full history chapters with faction lore |
| Idempotent | Calling `materialize_world()` twice produces same result |
| Genre pack schema | History chapters deserialize from YAML keyed by maturity level |
