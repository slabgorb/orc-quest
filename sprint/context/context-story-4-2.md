---
parent: context-epic-4.md
---

# Story 4-2: Subject Extraction -- Parse Narration for Image Render Subjects, Tier Classification

## Business Context

Not every piece of narration deserves a rendered image. When the narrator says "You enter
a vast underground cavern lit by bioluminescent fungi," that's a landscape worth rendering.
When it says "You nod," it isn't. Subject extraction is the first filter in the image
pipeline -- it parses narration text and extracts structured render subjects with tier
classification (Portrait, Scene, Landscape, Abstract).

In Python, this lives in `sq-2/sidequest/renderer/subject.py` and uses a mix of regex
patterns and heuristic scoring to identify entities, classify scene types, and decide
the image composition tier. The Rust port keeps the same heuristics but adds typed
subject tiers and a structured `RenderSubject` output.

**Python source:** `sq-2/sidequest/renderer/subject.py` (SubjectExtractor.extract)
**Depends on:** Story 4-1 (daemon client -- extracted subjects get sent to the render endpoint)

## Technical Approach

### Subject Tier Classification

```rust
#[derive(Debug, Clone, PartialEq)]
pub enum SubjectTier {
    Portrait,    // Single character close-up (1 entity, dialogue/examine context)
    Scene,       // 2-4 entities interacting (combat, conversation)
    Landscape,   // Environment focus (entering new area, descriptive passage)
    Abstract,    // Mood/atmosphere (tension, dread, wonder)
}

#[derive(Debug, Clone, PartialEq)]
pub enum SceneType {
    Combat,
    Dialogue,
    Exploration,
    Discovery,
    Transition,
}
```

### RenderSubject Output

```rust
pub struct RenderSubject {
    pub entities: Vec<String>,
    pub scene_type: SceneType,
    pub tier: SubjectTier,
    pub prompt_fragment: String,
    pub narrative_weight: f32,  // 0.0-1.0, used by beat filter (4-3)
}
```

### Extraction Pipeline

The extractor runs three passes over the narration text:

```rust
pub struct SubjectExtractor {
    entity_patterns: Vec<Regex>,
    scene_keywords: HashMap<SceneType, Vec<String>>,
    tier_rules: TierRules,
}

impl SubjectExtractor {
    pub fn extract(&self, narration: &str, context: &ExtractionContext) -> Option<RenderSubject> {
        // 1. Entity extraction -- named entities, pronouns resolved against context
        let entities = self.extract_entities(narration, &context.known_npcs);

        // 2. Scene type classification -- keyword matching + context state
        let scene_type = self.classify_scene(narration, context);

        // 3. Tier assignment -- entity count + scene type → tier
        let tier = self.tier_rules.assign(&entities, &scene_type);

        // 4. Prompt fragment -- compose a render-ready description
        let prompt_fragment = self.compose_prompt(narration, &entities, &tier);

        // 5. Narrative weight -- how "significant" is this moment?
        let weight = self.compute_weight(narration, &entities, &scene_type);

        if weight < self.tier_rules.minimum_weight {
            return None;  // Too mundane to even consider rendering
        }

        Some(RenderSubject { entities, scene_type, tier, prompt_fragment, narrative_weight: weight })
    }
}
```

### Narrative Weight Heuristics

Python uses a scoring system based on:
- Entity count (more entities = higher weight)
- Action verbs (combat verbs score higher than movement verbs)
- Descriptive density (adjective/adverb ratio)
- Scene transition markers ("you enter", "before you lies")
- First-mention bonus (new NPC or location appearing for the first time)

```rust
fn compute_weight(&self, narration: &str, entities: &[String], scene_type: &SceneType) -> f32 {
    let mut weight = 0.0;
    weight += (entities.len() as f32 * 0.15).min(0.45);
    weight += self.action_verb_score(narration);
    weight += self.descriptive_density(narration);
    weight += self.transition_bonus(narration);
    weight.clamp(0.0, 1.0)
}
```

### ExtractionContext

The extractor needs game state context to resolve pronouns and identify known NPCs:

```rust
pub struct ExtractionContext {
    pub known_npcs: Vec<String>,
    pub current_location: String,
    pub in_combat: bool,
    pub recent_subjects: Vec<String>,  // For dedup with recent renders
}
```

## Scope Boundaries

**In scope:**
- `SubjectExtractor` with `extract()` method
- `RenderSubject` struct with entities, tier, scene type, prompt fragment, weight
- Entity extraction via regex patterns and NPC name matching
- Scene type classification from keywords and game state
- Tier assignment rules (entity count + scene type)
- Narrative weight scoring heuristics
- Prompt fragment composition for the daemon render endpoint
- Unit tests for each extraction stage

**Out of scope:**
- LLM-based subject extraction (heuristics only for now)
- Pronoun resolution beyond simple context matching
- Beat filter threshold logic (that's story 4-3)
- Actually sending subjects to the daemon (that's 4-4 and 4-5)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Entity extraction | Named NPCs from context are identified in narration text |
| Scene classification | Combat narration classifies as `SceneType::Combat` |
| Tier assignment | Single-entity dialogue -> Portrait; multi-entity combat -> Scene |
| Landscape detection | "You enter a vast cavern..." -> `SubjectTier::Landscape` |
| Prompt composition | Output `prompt_fragment` is a daemon-ready image description |
| Weight scoring | High-action combat scores > 0.7; "you nod" scores < 0.2 |
| Minimum threshold | Narration below minimum weight returns `None` |
| Context awareness | Known NPC names resolved from `ExtractionContext` |
| Dedup signal | `recent_subjects` prevents re-extracting the same entity |
| Test coverage | Unit tests for each tier, scene type, and weight edge case |
