---
parent: context-epic-10.md
---

# Story 10-3: OCEAN Behavioral Summary — Scores to Narrator Prompt Text

## Business Context

The narrator agent doesn't read raw floats. It needs natural language: "reserved and meticulous,
prone to quiet anxiety." This story builds a deterministic function that converts OCEAN scores
into a short behavioral description. Same scores always produce the same text, giving the
narrator a stable personality reference.

**Python reference:** `sq-2/sprint/epic-64.yaml` — score-range-to-adjective mapping table
with low/mid/high bands per dimension. Rust reimplements the same table-driven approach.

**Depends on:** Story 10-1 (OceanProfile struct).

## Technical Approach

### Score Bands

Each dimension maps to three bands with associated descriptors:

```rust
fn descriptor(dim: OceanDimension, value: f64) -> &'static str {
    match dim {
        OceanDimension::Openness => match value {
            v if v < 3.5 => "conventional",
            v if v < 6.5 => "pragmatic",
            _ => "curious and inventive",
        },
        OceanDimension::Conscientiousness => match value {
            v if v < 3.5 => "careless",
            v if v < 6.5 => "steady",
            _ => "meticulous and driven",
        },
        // ... Extraversion, Agreeableness, Neuroticism
    }
}
```

### Summary Composition

Only extreme dimensions (low or high band) appear in the summary. Mid-range dimensions
are omitted to keep text concise:

```rust
impl OceanProfile {
    pub fn behavioral_summary(&self) -> String {
        let descriptors: Vec<&str> = OceanDimension::all()
            .filter_map(|dim| {
                let v = self.get(dim);
                if v < 3.5 || v >= 6.5 { Some(descriptor(dim, v)) }
                else { None }
            })
            .collect();
        if descriptors.is_empty() {
            return "unremarkable temperament".to_string();
        }
        descriptors.join(", ")
    }
}
```

A profile with low E (2.0) and high C (8.0) and everything else mid produces:
`"reserved and quiet, meticulous and driven"`.

## Scope Boundaries

**In scope:**
- Descriptor table: low/mid/high per dimension
- `behavioral_summary()` method returning natural language string
- Deterministic: same profile always yields same summary
- Edge case: all-mid profile returns generic fallback

**Out of scope:**
- Narrator prompt injection (10-4)
- Custom per-genre descriptor tables (future refinement)
- Compound personality descriptions beyond concatenation

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Deterministic | Same OceanProfile always produces same summary string |
| Low band | Value 2.0 on Extraversion yields "reserved and quiet" |
| High band | Value 8.0 on Conscientiousness yields "meticulous and driven" |
| Mid omitted | Value 5.0 on any dimension is not mentioned in summary |
| All mid | Profile at 5.0/5.0/5.0/5.0/5.0 returns "unremarkable temperament" |
| Concise | Summary is a single comma-separated phrase, not a paragraph |
| All extremes | Profile at 1.0/9.0/1.0/9.0/1.0 includes all five descriptors |
