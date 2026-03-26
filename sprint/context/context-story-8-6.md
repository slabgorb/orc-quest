---
parent: context-epic-8.md
---

# Story 8-6: Perception Rewriter — Per-Character Narration Variants Based on Status Effects

## Business Context

A charmed player should see the vampire as a trusted friend. A blinded player should
receive narration filtered through sound and touch. The perception rewriter takes the
base narration from the orchestrator and produces per-character variants for players with
active perceptual status effects. This is the most LLM-intensive part of multiplayer,
requiring an additional Claude call per affected player.

**Python source:** `sq-2/sidequest/game/perception_rewriter.py` (rewrite_for_character)
**ADR:** ADR-028 (Perception Rewriter)
**Depends on:** Story 8-1 (MultiplayerSession for player/character mapping)

## Technical Approach

The rewriter runs after the orchestrator produces base narration, before broadcast:

```rust
pub struct PerceptionRewriter {
    claude: ClaudeClient,
}

pub struct PerceptionFilter {
    pub character_id: CharacterId,
    pub character_name: String,
    pub effects: Vec<PerceptualEffect>,
}

#[derive(Debug, Clone)]
pub enum PerceptualEffect {
    Blinded,
    Charmed { source: String },
    Dominated { controller: String },
    Hallucinating,
    Deafened,
    Custom { name: String, description: String },
}

impl PerceptionRewriter {
    pub async fn rewrite(
        &self,
        base_narration: &str,
        filter: &PerceptionFilter,
        genre_voice: &str,
    ) -> Result<String, RewriterError> {
        let prompt = format!(
            "Rewrite this narration as perceived by {name}, who is affected by: {effects}.\n\
             Maintain {genre} genre voice. Keep the same length.\n\n\
             Original:\n{narration}",
            name = filter.character_name,
            effects = Self::describe_effects(&filter.effects),
            genre = genre_voice,
            narration = base_narration,
        );
        self.claude.call(&prompt).await.map_err(RewriterError::Agent)
    }
}
```

The session broadcasts narration per-player, rewriting only for affected characters:

```rust
pub async fn broadcast_narration(
    &self,
    base: &str,
    rewriter: &PerceptionRewriter,
    genre_voice: &str,
) {
    let mut futures = Vec::new();
    for (player_id, slot) in &self.players {
        let effects = self.active_perceptual_effects(&slot.character_id);
        if effects.is_empty() {
            // Send base narration directly
            let _ = slot.ws_tx.send(narration_msg(base)).await;
        } else {
            // Spawn rewrite task
            futures.push(self.rewrite_and_send(rewriter, base, slot, effects, genre_voice));
        }
    }
    futures::future::join_all(futures).await;
}
```

Rewrite calls run concurrently for all affected players. If a rewrite fails, the player
receives the base narration (graceful degradation per ADR-006).

## Scope Boundaries

**In scope:**
- `PerceptionRewriter` with Claude CLI integration
- `PerceptualEffect` enum (Blinded, Charmed, Dominated, Hallucinating, Deafened, Custom)
- Per-player narration routing (base vs rewritten)
- Concurrent rewrite calls for multiple affected players
- Graceful degradation on rewrite failure

**Out of scope:**
- Caching rewrites for identical effect combinations
- Streaming rewritten narration (rewrites are short, full response is fine)
- Effect stacking interaction rules (e.g., blinded + deafened)
- UI indicators for "this narration was filtered"

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Rewrite call | Affected player receives rewritten narration via Claude |
| Unaffected passthrough | Players without effects receive base narration |
| Concurrent | Multiple rewrites execute in parallel |
| Graceful fallback | Failed rewrite falls back to base narration |
| Effect types | Blinded, Charmed, Dominated, Hallucinating, Deafened supported |
| Genre voice | Rewritten text maintains genre voice from genre pack |
| Custom effects | Custom perceptual effects supported via name + description |
