---
parent: context-epic-7.md
---

# Story 7-8: Scenario Scoring — Evidence Collection Metrics, Accusation Accuracy, Deduction Quality

## Business Context

After a scenario resolves, the player should see how well they investigated. Did they
find all the clues? Did they question the right NPCs? Was the accusation backed by
evidence or a lucky guess? Scoring gives closure to the mystery arc and encourages replay.
Python computed a simple score percentage. The Rust port provides a structured scorecard
with multiple dimensions.

**Depends on:** Story 7-4 (accusation system — scoring runs after accusation resolves)

## Technical Approach

```rust
pub struct ScenarioScore {
    pub evidence_coverage: f32,    // % of available clues found
    pub interrogation_breadth: f32, // % of relevant NPCs questioned
    pub deduction_quality: DeductionQuality,
    pub accusation_quality: EvidenceQuality,
    pub accusation_correct: bool,
    pub total_turns: u64,
    pub overall_grade: ScenarioGrade,
}

pub enum DeductionQuality {
    Guesswork,    // accused with minimal evidence
    Methodical,   // found most clues, questioned key NPCs
    Masterful,    // found all clues, exposed contradictions, airtight case
}

pub enum ScenarioGrade {
    Bronze,   // correct accusation with weak evidence
    Silver,   // correct with strong evidence
    Gold,     // correct with airtight evidence and high coverage
    Failed,   // wrong accusation
}

pub fn score_scenario(
    scenario: &ScenarioState,
    result: &AccusationResult,
) -> ScenarioScore {
    let total_clues = scenario.all_clues().len() as f32;
    let found_clues = scenario.activated_clues.len() as f32;
    let evidence_coverage = if total_clues > 0.0 {
        found_clues / total_clues
    } else { 1.0 };

    // ... compute other dimensions ...

    ScenarioScore {
        evidence_coverage,
        overall_grade: compute_grade(result, evidence_coverage),
        // ...
    }
}
```

The scorecard is serialized and included in the scenario archive for post-game review.

## Scope Boundaries

**In scope:**
- `ScenarioScore`, `DeductionQuality`, `ScenarioGrade` types
- `score_scenario()` function computing all dimensions
- Evidence coverage, interrogation breadth, deduction quality metrics
- Grade computation from combined metrics
- Unit tests for scoring at each grade tier

**Out of scope:**
- UI presentation of scorecard (frontend concern)
- Leaderboards or cross-session score comparison
- Scoring affecting future gameplay (score is informational only)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Evidence coverage | Percentage of available clues the player activated |
| Interrogation breadth | Percentage of relevant NPCs the player interacted with |
| Deduction quality | Guesswork/Methodical/Masterful based on evidence quality |
| Grade assignment | Gold requires correct accusation + airtight evidence + high coverage |
| Failed grade | Wrong accusation always results in Failed grade |
| Turn tracking | Total turns recorded in scorecard |
| Serializable | `ScenarioScore` serializes for archive inclusion |
