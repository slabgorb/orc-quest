---
parent: context-epic-5.md
---

# Story 5-4: Pacing Hint Generation — drama_weight to Narrator Sentence Count Guidance (1-6 Sentences)

## Business Context

The drama_weight value is useless until it changes what the narrator actually does. This
story converts drama_weight into a `PacingHint` — a struct that tells the narrator how
many sentences to write and provides metadata for downstream consumers. A miss with
drama_weight=0.1 gets "You miss." (1 sentence). A killing blow with drama_weight=1.0
gets a 6-sentence cinematic description.

In Python, `get_pacing_hint()` injects a sentence count directive into the narrator's
system prompt. The narrator treats it as a soft constraint — it can exceed the count for
dramatic effect, but the guidance keeps routine turns snappy and dramatic turns expansive.

**Python source:** `sq-2/sidequest/game/tension.py:get_pacing_hint()`
**ADR:** `sq-2/docs/prd-combat-pacing.md` (narrator length targeting section)
**Depends on:** Story 5-3 (drama_weight computation)

## Technical Approach

### PacingHint Struct

```rust
/// Guidance for the narrator and delivery system, derived from drama_weight.
pub struct PacingHint {
    /// The raw drama weight (0.0-1.0) for consumers that need the continuous value
    pub drama_weight: f64,
    /// How many sentences the narrator should target (1-6)
    pub target_sentences: u8,
    /// Text delivery mode for the client (story 5-5 adds full implementation)
    pub delivery_mode: DeliveryMode,
    /// Optional escalation beat hint for quiet stretches (story 5-6 populates this)
    pub escalation_beat: Option<String>,
}
```

### Sentence Count Formula

```rust
impl PacingHint {
    /// Linear interpolation: sentences = 1 + floor(drama_weight * 5)
    /// 0.0 -> 1, 0.2 -> 2, 0.4 -> 3, 0.6 -> 4, 0.8 -> 5, 1.0 -> 6
    pub fn from_drama_weight(drama_weight: f64) -> Self {
        let clamped = drama_weight.clamp(0.0, 1.0);
        let target_sentences = (1.0 + (clamped * 5.0)).floor() as u8;

        Self {
            drama_weight: clamped,
            target_sentences: target_sentences.min(6),
            delivery_mode: DeliveryMode::from_weight(clamped),
            escalation_beat: None, // populated by story 5-6
        }
    }
}
```

### Integration with TensionTracker

```rust
impl TensionTracker {
    /// Convenience method: observe an outcome and return a PacingHint.
    /// This is what the orchestrator calls each turn (wired in story 5-7).
    pub fn pacing_hint(&self) -> PacingHint {
        PacingHint::from_drama_weight(self.drama_weight())
    }
}
```

### Prompt Injection Format

The pacing hint gets injected into the narrator's system prompt as a directive:

```rust
impl PacingHint {
    /// Format as a narrator prompt directive.
    /// Injected into the system prompt, not the user message.
    pub fn narrator_directive(&self) -> String {
        match self.target_sentences {
            1 => "Keep your response to 1 sentence. This is a routine moment.".to_string(),
            2 => "Keep your response to about 2 sentences. Brief and functional.".to_string(),
            3 => "Write about 3 sentences. Moderate detail.".to_string(),
            4 => "Write about 4 sentences. This moment deserves attention.".to_string(),
            5 => "Write about 5 sentences. This is a dramatic moment — describe it vividly.".to_string(),
            6 | _ => "Write up to 6 sentences. This is a peak dramatic moment — give it full cinematic treatment.".to_string(),
        }
    }
}
```

Python uses a generic "Write N sentences" directive. The Rust version adds qualitative
framing ("routine moment" vs "peak dramatic moment") to give the LLM additional tone
guidance beyond just a number.

### Rust Learning Note

`PacingHint` is a value type — it gets created, passed around, and consumed. No `&mut`,
no shared ownership. This is idiomatic Rust for "computed result" types. The `from_`
constructor pattern is standard for types that are derived from another value.

## Scope Boundaries

**In scope:**
- `PacingHint` struct definition
- `from_drama_weight()` constructor with sentence count formula
- `narrator_directive()` for prompt injection text
- `pacing_hint()` convenience method on TensionTracker
- Unit tests for sentence count at each drama_weight bracket

**Out of scope:**
- DeliveryMode logic beyond basic construction (story 5-5)
- Escalation beat population (story 5-6)
- Actually injecting the directive into the orchestrator prompt (story 5-7)
- Genre-specific sentence count overrides (story 5-8)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Struct defined | PacingHint with drama_weight, target_sentences, delivery_mode, escalation_beat |
| Linear formula | drama_weight=0.0 -> 1 sentence, 0.5 -> 3 sentences, 1.0 -> 6 sentences |
| Boundary values | 0.19 -> 1 sentence, 0.20 -> 2 sentences (floor behavior correct) |
| Clamped input | drama_weight > 1.0 still produces 6 sentences max |
| Directive text | narrator_directive() returns appropriate string for each sentence count |
| Tracker integration | TensionTracker.pacing_hint() returns correct PacingHint from current state |
| Tests | Unit tests covering formula at boundaries (0.0, 0.19, 0.2, 0.5, 0.8, 1.0) |
