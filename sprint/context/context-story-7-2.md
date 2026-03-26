---
parent: context-epic-7.md
---

# Story 7-2: Gossip Propagation — NPCs Spread Claims Between Turns, Contradictions Decay Credibility

## Business Context

Information shouldn't teleport between NPCs. When the barkeep tells the smith "the guard
was nervous last night," that's a claim propagating through the social network. If the
smith already knows the guard was home asleep, the contradiction damages the barkeep's
credibility. This gossip mechanic makes investigation meaningful — the player can trace
who told whom what, and liars' stories eventually unravel.

**Python ref:** `sq-2/sidequest/scenario/gossip.py`
**Depends on:** Story 7-1 (BeliefState model)

## Technical Approach

Gossip runs as a between-turn phase operating on all NPC BeliefStates:

```rust
pub fn propagate_gossip(
    beliefs: &mut HashMap<String, BeliefState>,
    social_graph: &SocialGraph,
    rng: &mut impl Rng,
) {
    let pairs = social_graph.connected_pairs();
    for (npc_a, npc_b) in pairs {
        if rng.gen::<f32>() > social_graph.proximity(npc_a, npc_b) {
            continue;  // not every pair gossips every turn
        }
        let claims_to_share: Vec<Claim> = beliefs[npc_a]
            .shareable_claims()
            .cloned()
            .collect();

        for claim in claims_to_share {
            let result = beliefs.get_mut(npc_b).unwrap()
                .receive_claim(&claim, npc_a);

            if result == ClaimResult::Contradicted {
                beliefs.get_mut(npc_a).unwrap()
                    .credibility_mut()
                    .decay(CONTRADICTION_DECAY);
            }
        }
    }
}
```

`SocialGraph` tracks which NPCs can talk to each other and how likely they are to share
information (proximity 0.0-1.0). This is derived from scenario setup — NPCs in the same
location have high proximity.

The `receive_claim()` method on `BeliefState` handles the logic: if the claim contradicts
known facts, it's marked contradicted; otherwise it's accepted and the source gets
corroboration credit.

## Scope Boundaries

**In scope:**
- `propagate_gossip()` function
- `SocialGraph` struct with proximity scores
- `receive_claim()` method on `BeliefState`
- Credibility decay on contradiction
- Randomized propagation (not every pair gossips every turn)
- Unit tests with deterministic RNG

**Out of scope:**
- How the social graph is built (scenario setup, story 7-9)
- Gossip about the player's actions (future enhancement)
- Multi-hop propagation in a single turn (one hop per turn)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Claim propagation | NPC A's claims appear in NPC B's BeliefState after gossip |
| Contradiction detection | Claim contradicting B's facts → marked as contradicted |
| Credibility decay | Source NPC's credibility decays when their claim is contradicted |
| Proximity gating | NPCs with low proximity rarely share gossip |
| One hop per turn | Claims propagate one step per gossip phase, not transitively |
| Deterministic test | Tests use seeded RNG for reproducible propagation |
| No self-gossip | NPC doesn't propagate claims to themselves |
