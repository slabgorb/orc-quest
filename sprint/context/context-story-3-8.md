---
parent: context-epic-3.md
---

# Story 3-8: Trope Alignment Check — Beat Thresholds vs Narration Content

## Business Context

The trope engine (story 2-8) advances trope progress mechanically each turn — progress
increments by `rate_per_turn` and `rate_per_day`, and beats fire when thresholds are crossed
(0.25, 0.50, 0.75, 1.0 per ADR-018). The Narrator agent receives trope context in its system
prompt and is expected to weave beat moments into its narration. But Claude may ignore the
beat entirely — producing perfectly fine prose that has no connection to the trope moment
that just fired.

This disconnect is invisible without instrumentation. The trope progresses mechanically, the
beat fires, the state updates, but the player never experiences the narrative moment the
genre pack author intended. The game "works" but loses narrative coherence.

This story adds a validation check that flags when a beat fires but the narration shows no
thematic connection to it. Like all Game Watcher checks, this is a soft signal for human
inspection — the Narrator might address the trope implicitly, through metaphor, or in ways
keyword matching cannot detect. The human judges whether the flag is meaningful.

The Python codebase (sq-2) has no equivalent. Trope beats fire and nobody checks whether the
Narrator honored them.

**ADR:** ADR-018 (trope lifecycle, beat thresholds), ADR-031 (semantic telemetry)
**Depends on:** Story 3-4 (entity reference extraction — establishes the pattern for text analysis checks), Story 2-8 (trope engine runtime — provides beat firing data)

## Technical Approach

### Trope Context in TurnRecord

When beats fire during a turn, the trope engine already records them in `TurnRecord.beats_fired`
as `Vec<(String, f32)>` (trope name, threshold). This story needs additional context: the
beat's description and keywords from the genre pack. Add a `trope_context` field:

```rust
/// Contextual data for a trope beat that fired this turn.
/// Populated from the genre pack's trope definition.
pub struct TropeContext {
    pub trope_name: String,
    pub beat_name: String,
    pub threshold: f32,
    pub description: String,        // from genre pack beat definition
    pub keywords: Vec<String>,      // extracted from description + trope tags
}

// Added to TurnRecord alongside beats_fired
pub struct TurnRecord {
    // ... existing fields ...
    pub beats_fired: Vec<(String, f32)>,
    pub trope_contexts: Vec<TropeContext>,  // NEW: one per beat fired
}
```

### Beat Definition in Genre Packs

Genre pack YAML defines tropes with beats. Example from `mutant_wasteland`:

```yaml
tropes:
  suspicion:
    description: "Growing distrust and paranoia among the survivors"
    tags: ["paranoia", "distrust", "secrets", "betrayal"]
    beats:
      - name: seeds_of_doubt
        threshold: 0.25
        description: "First hints that someone is hiding something"
      - name: evidence_found
        threshold: 0.50
        description: "A concrete clue or discovery that confirms suspicion"
      - name: confrontation
        threshold: 0.75
        description: "Direct accusation or tense standoff"
      - name: truth_revealed
        threshold: 1.0
        description: "The secret comes out, for better or worse"
```

### Keyword Extraction

Build the keyword set from the beat's description and the trope's tags:

```rust
fn extract_keywords(ctx: &TropeContext) -> Vec<String> {
    let mut keywords = ctx.keywords.clone();

    // Split description into significant words (4+ chars, lowercased)
    let desc_words: Vec<String> = ctx.description
        .split_whitespace()
        .map(|w| w.to_lowercase().trim_matches(|c: char| !c.is_alphanumeric()).to_string())
        .filter(|w| w.len() >= 4)
        .collect();

    keywords.extend(desc_words);
    keywords.sort();
    keywords.dedup();
    keywords
}
```

This is deliberately simple. No stemming, no synonym expansion, no NLP. The goal is to catch
obvious misses (beat "evidence_found" fires but narration mentions nothing about clues,
discovery, evidence, proof, etc.). Sophisticated semantic analysis is out of scope — that
would require an LLM call, which violates the "no async, no I/O" principle for validator checks.

### Alignment Check

```rust
fn check_trope_alignment(record: &TurnRecord) -> Vec<ValidationResult> {
    let mut results = Vec::new();

    for ctx in &record.trope_contexts {
        let keywords = extract_keywords(ctx);
        let narration_lower = record.narration.to_lowercase();

        let matched: Vec<&String> = keywords.iter()
            .filter(|kw| narration_lower.contains(kw.as_str()))
            .collect();

        if matched.is_empty() {
            results.push(ValidationResult {
                check: "trope_alignment".to_string(),
                severity: Severity::Warn,
                message: format!(
                    "Beat \"{}\" fired for trope \"{}\" at {:.0}%, but narration \
                     contains none of the expected keywords: {}",
                    ctx.beat_name,
                    ctx.trope_name,
                    ctx.threshold * 100.0,
                    keywords.join(", "),
                ),
            });

            tracing::warn!(
                component = "watcher",
                check = "trope_alignment",
                trope = %ctx.trope_name,
                beat = %ctx.beat_name,
                threshold = ctx.threshold,
                keyword_count = keywords.len(),
                "Beat fired but narration shows no thematic overlap"
            );
        } else {
            tracing::debug!(
                component = "watcher",
                check = "trope_alignment",
                trope = %ctx.trope_name,
                beat = %ctx.beat_name,
                matched_keywords = ?matched,
                "Beat aligned with narration"
            );
        }
    }

    results
}
```

### Integration with Validator Task

This check slots into the same validator loop as patch legality (3-3), entity references (3-4),
and subsystem exercise (3-5):

```rust
async fn validator_task(mut rx: mpsc::Receiver<TurnRecord>) {
    let mut tracker = SubsystemTracker::new(5, 10);

    while let Some(record) = rx.recv().await {
        tracker.record(&record.agent_name);

        // Existing checks
        let legality = check_patch_legality(&record);
        let entity_refs = check_entity_references(&record);

        // New check
        let trope_alignment = check_trope_alignment(&record);

        // Broadcast all results to /ws/watcher
        broadcast_results(&legality, &entity_refs, &trope_alignment);
    }
}
```

### Populating TropeContext

The trope engine already knows which beats fired. When assembling the TurnRecord in the
orchestrator (story 3-2), look up each fired beat's definition from the genre pack:

```rust
fn build_trope_contexts(
    beats_fired: &[(String, f32)],
    genre_pack: &GenrePack,
) -> Vec<TropeContext> {
    beats_fired.iter().filter_map(|(trope_name, threshold)| {
        let trope_def = genre_pack.tropes.get(trope_name)?;
        let beat = trope_def.beats.iter()
            .find(|b| (b.threshold - threshold).abs() < 0.01)?;

        Some(TropeContext {
            trope_name: trope_name.clone(),
            beat_name: beat.name.clone(),
            threshold: *threshold,
            description: beat.description.clone(),
            keywords: trope_def.tags.clone(),
        })
    }).collect()
}
```

### False Positive Expectations

This check will produce false positives. That is by design. Common reasons a flag may
not indicate a real problem:

- The Narrator addressed the trope implicitly or through metaphor
- The beat's keywords are too generic or too specific
- The Narrator deferred the beat moment to the next turn (build-up)
- The narration uses synonyms not in the keyword list

The operator sees the flag and decides. This is ADR-031's "God lifting rocks" principle:
the watcher flags, the human judges.

## Scope Boundaries

**In scope:**
- `TropeContext` struct with trope name, beat name, threshold, description, keywords
- Adding `trope_contexts: Vec<TropeContext>` to TurnRecord
- Keyword extraction from beat description and trope tags
- Case-insensitive keyword matching against narration text
- `tracing::warn!` emission when no keywords match, tagged `check="trope_alignment"`
- `tracing::debug!` emission when keywords do match
- `ValidationResult` output for watcher broadcast
- Integration with the validator task loop

**Out of scope:**
- Stemming, lemmatization, or NLP-based matching (keep it simple)
- Synonym expansion (would need a dictionary or LLM call)
- Semantic similarity via embeddings (too heavy for a validator check)
- Automated trope adjustment (if misaligned, the watcher flags; it doesn't fix)
- Multi-turn trope tracking (beat might be addressed over several turns — deferred)
- Scoring or grading narration quality

## Acceptance Criteria

| AC | Detail |
|----|--------|
| TropeContext populated | When beats fire, TropeContext structs are built from genre pack data |
| Keyword extraction | Keywords derived from beat description (4+ char words) and trope tags |
| Alignment check runs | Every TurnRecord with non-empty trope_contexts is checked |
| Mismatch flagged | If narration contains none of a beat's keywords, a warn-level result is emitted |
| Match logged | If narration contains at least one keyword, a debug-level trace is emitted |
| Structured fields | All tracing events include `component="watcher"` and `check="trope_alignment"` |
| Case insensitive | Keyword matching is case-insensitive |
| No false negatives | A single keyword match is sufficient to pass (low bar by design) |
| Validator integration | Check runs in the validator task alongside patch legality and entity reference checks |
