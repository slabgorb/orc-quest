---
parent: context-epic-7.md
---

# Story 7-4: Accusation System — Player Accuses NPC, System Evaluates Evidence Quality and Resolves

## Business Context

The climax of a whodunit: the player points a finger. The accusation system gathers all
evidence — activated clues, corroborated claims, contradictions, credibility scores — and
evaluates whether the accusation holds. The result isn't binary (right/wrong) but graded:
circumstantial, strong, or airtight. This lets the narrator dramatize a weak accusation
differently from an airtight case.

**Python ref:** `sq-2/sidequest/scenario/accusation.py`
**Depends on:** Story 7-3 (clue activation — provides activated clues for evidence)

## Technical Approach

```rust
pub struct Accusation {
    pub accuser: String,       // player character
    pub accused_npc: String,
    pub stated_reason: String, // player's explanation
}

pub struct AccusationResult {
    pub quality: EvidenceQuality,
    pub correct: bool,
    pub evidence_summary: EvidenceSummary,
    pub narrative_prompt: String,  // for narrator to dramatize
}

pub enum EvidenceQuality {
    Circumstantial,  // 1-2 clues, weak corroboration
    Strong,          // 3+ clues, corroborated claims, some contradictions exposed
    Airtight,        // physical evidence + contradictions + confession/witness
}

pub fn evaluate_accusation(
    accusation: &Accusation,
    scenario: &ScenarioState,
) -> AccusationResult {
    let evidence = gather_evidence(accusation, scenario);

    let quality = match evidence.score() {
        0..=2  => EvidenceQuality::Circumstantial,
        3..=5  => EvidenceQuality::Strong,
        _      => EvidenceQuality::Airtight,
    };

    let correct = scenario.guilty_npc() == accusation.accused_npc;

    AccusationResult {
        quality,
        correct,
        evidence_summary: evidence,
        narrative_prompt: build_narrative_prompt(correct, &quality),
    }
}
```

Evidence scoring considers: number of activated clues pointing to the accused, claims
corroborated by multiple NPCs, contradictions in the accused's story, and the accused's
credibility score. The `gather_evidence()` function collects all relevant signals into an
`EvidenceSummary` that the scoring function evaluates.

## Scope Boundaries

**In scope:**
- `Accusation`, `AccusationResult`, `EvidenceQuality` types
- `evaluate_accusation()` function with evidence gathering and scoring
- `EvidenceSummary` aggregation of clues, claims, contradictions
- Narrative prompt generation for narrator dramatization
- Tests for each evidence quality tier

**Out of scope:**
- Player UI for making accusations (frontend concern)
- Multiple accusations per scenario (one accusation resolves the scenario)
- Scoring/metrics (story 7-8)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Evidence gathering | Collects activated clues, claims, and credibility for accused NPC |
| Quality grading | Score maps to Circumstantial/Strong/Airtight |
| Correctness check | Compares accused against scenario's actual guilty NPC |
| Narrative prompt | Generates narrator-facing text appropriate to quality and correctness |
| Weak accusation | Few clues + no corroboration → Circumstantial |
| Strong accusation | Multiple clues + corroborated claims → Strong |
| Airtight accusation | Physical evidence + exposed contradictions → Airtight |
