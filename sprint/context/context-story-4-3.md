---
parent: context-epic-4.md
---

# Story 4-3: Beat Filter -- Suppress Image Renders for Low-Narrative-Weight Actions

## Business Context

GPU cycles are expensive. Every image render takes 2-8 seconds on the daemon and ties
up the pipeline. The beat filter is the second gate in the image pipeline (after subject
extraction) -- it decides whether a narration moment is worth rendering based on narrative
weight, recency of last render, and configurable thresholds. Without it, every turn
produces an image, most of which are "you walk down the hallway" variants that waste
time and break immersion.

In Python, `sq-2/sidequest/renderer/filter.py` implements this as a stateful filter
that tracks render history and applies threshold logic. The Rust port adds typed
configuration from the genre pack and makes the filter's decision auditable via a
`FilterDecision` enum.

**Python source:** `sq-2/sidequest/renderer/filter.py` (BeatFilter.should_render)
**Depends on:** Story 4-2 (subject extraction provides the `RenderSubject` with narrative weight)

## Technical Approach

### Filter Decision Type

Python returns a boolean. Rust returns a decision with reasoning:

```rust
#[derive(Debug, Clone)]
pub enum FilterDecision {
    Render { reason: String },
    Suppress { reason: String },
}

impl FilterDecision {
    pub fn should_render(&self) -> bool {
        matches!(self, FilterDecision::Render { .. })
    }
}
```

### BeatFilter Struct

```rust
pub struct BeatFilter {
    config: BeatFilterConfig,
    render_history: VecDeque<RenderRecord>,
}

struct RenderRecord {
    timestamp: Instant,
    subject_hash: u64,
    narrative_weight: f32,
}

pub struct BeatFilterConfig {
    pub weight_threshold: f32,       // Minimum narrative weight to render (default 0.4)
    pub cooldown: Duration,          // Minimum time between renders (default 15s)
    pub combat_threshold: f32,       // Lower threshold during combat (default 0.25)
    pub max_history: usize,          // Rolling history window size (default 20)
    pub burst_limit: u32,            // Max renders in burst_window (default 3)
    pub burst_window: Duration,      // Window for burst limiting (default 60s)
}
```

### Decision Logic

```rust
impl BeatFilter {
    pub fn evaluate(&mut self, subject: &RenderSubject, context: &FilterContext) -> FilterDecision {
        // 1. Weight threshold -- is this moment significant enough?
        let threshold = if context.in_combat {
            self.config.combat_threshold
        } else {
            self.config.weight_threshold
        };
        if subject.narrative_weight < threshold {
            return FilterDecision::Suppress {
                reason: format!("weight {:.2} below threshold {:.2}", subject.narrative_weight, threshold),
            };
        }

        // 2. Cooldown -- rendered too recently?
        if let Some(last) = self.render_history.back() {
            if last.timestamp.elapsed() < self.config.cooldown {
                return FilterDecision::Suppress {
                    reason: format!("cooldown: {}ms since last render", last.timestamp.elapsed().as_millis()),
                };
            }
        }

        // 3. Burst limit -- too many renders in the window?
        let recent_count = self.count_recent_renders(self.config.burst_window);
        if recent_count >= self.config.burst_limit {
            return FilterDecision::Suppress {
                reason: format!("burst limit: {} renders in last {}s", recent_count, self.config.burst_window.as_secs()),
            };
        }

        // 4. Duplicate subject -- same entity rendered recently?
        let hash = hash_subject(subject);
        if self.render_history.iter().any(|r| r.subject_hash == hash) {
            return FilterDecision::Suppress {
                reason: "duplicate subject in recent history".into(),
            };
        }

        // Record and approve
        self.record_render(hash, subject.narrative_weight);
        FilterDecision::Render {
            reason: format!("weight {:.2} passes, no suppression rules triggered", subject.narrative_weight),
        }
    }
}
```

### FilterContext

```rust
pub struct FilterContext {
    pub in_combat: bool,
    pub scene_transition: bool,  // Force-render on scene transitions
    pub player_requested: bool,  // "look around" -- player wants to see something
}
```

Scene transitions and explicit player requests can bypass the weight threshold:

```rust
if context.scene_transition || context.player_requested {
    self.record_render(hash, subject.narrative_weight);
    return FilterDecision::Render {
        reason: "forced: scene transition or player request".into(),
    };
}
```

### Genre Pack Configuration

Thresholds come from the genre pack's media config, allowing genre-specific tuning:

```yaml
media:
  beat_filter:
    weight_threshold: 0.4
    cooldown_seconds: 15
    combat_threshold: 0.25
    burst_limit: 3
    burst_window_seconds: 60
```

## Scope Boundaries

**In scope:**
- `BeatFilter` struct with `evaluate()` returning `FilterDecision`
- Weight threshold comparison with combat-specific override
- Cooldown timer (minimum interval between renders)
- Burst rate limiting (max renders per time window)
- Duplicate subject suppression via content hash
- Scene transition and player request force-render bypass
- `BeatFilterConfig` loaded from genre pack YAML
- Unit tests for each suppression rule

**Out of scope:**
- Adaptive threshold learning (adjusting based on session history)
- Per-player render preferences
- Priority queue interaction (that's story 4-4)
- Logging/telemetry for filter decisions (useful but deferred)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Weight gate | Subject with weight 0.3 suppressed when threshold is 0.4 |
| Combat override | Same subject passes during combat with threshold 0.25 |
| Cooldown | Second render within 15s suppressed regardless of weight |
| Burst limit | 4th render within 60s suppressed when burst_limit is 3 |
| Dedup | Same subject hash within history window suppressed |
| Scene transition | Force-render on scene change even if weight is low |
| Player request | "Look around" bypasses weight threshold |
| Decision audit | `FilterDecision` includes human-readable reason string |
| Config from YAML | Thresholds loaded from genre pack media config |
| History pruning | Render history stays within `max_history` bounds |
