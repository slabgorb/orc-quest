---
parent: context-epic-38.md
workflow: wire-first
---

# Story 38-6: Narrator cockpit-POV prompt extension

## Business Context

This is the wire from engine to player experience. Stories 38-1 through 38-5 built the mechanical backbone — `SealedLetterLookup` resolves maneuver commits into per-actor descriptor deltas. But without narrator integration, those descriptors are invisible to the player. This story teaches the unified narrator (ADR-067) to render cockpit-POV prose from `per_actor_state`, making the dogfight subsystem playable.

The narrator must render **two private narration blocks per turn** — one per pilot — each grounded strictly in that pilot's descriptor fields. The SOUL principle at stake: the narrator must NEVER invent geometry not present in the descriptor. If `gun_solution` is false, the narrator cannot describe firing. If `target_bearing` is "06", the target is behind, not ahead. This is the single most SOUL-sensitive integration point in the dogfight subsystem.

## Technical Guardrails

**Key files to modify:**
- Narrator system prompt templates in `sidequest-agents/` — add cockpit-POV rendering instructions as a conditional prompt extension when the active confrontation is `SealedLetterLookup`
- `sidequest-server/src/shared_session.rs` — verify `perception_filters` can route per-pilot narration blocks
- `sidequest-server/src/dispatch/sealed_letter.rs` — the handler that passes resolved descriptors to the narrator

**Patterns to follow:**
- ADR-067: No specialist agent. The unified narrator gets a system prompt extension, not a new agent
- ADR-028: Per-player perception filtering via `SharedSession.perception_filters` — this is the existing hook for "rewrite narration per-player"
- Narration hints from `interactions_mvp.yaml` cells are the beat the narrator should hit — they are NOT optional flavor text

**Integration points:**
- Input: `per_actor_state` (descriptor fields) + cell `narration_hint` from the 38-5 resolution handler
- Output: Two narration blocks (one per pilot) delivered through the existing per-player message channel
- OTEL: Must verify existing `dogfight.cell_resolved` spans correlate with narrator output (no new spans required, but narrator must not contradict span data)

**What NOT to touch:**
- The resolution handler (38-5) — it's shipped and tested
- The interaction table format — content is owned by 38-7/38-8/38-10
- Pilot skill tiers — forward-capture only, not consumed yet

## Scope Boundaries

**In scope:**
- System prompt extension for cockpit-POV rendering when active confrontation uses `SealedLetterLookup`
- Strict SOUL enforcement: narrator MUST NOT invent geometry outside descriptor fields
- Per-pilot private narration via perception_filters
- Integration test with `duel_01` scenario end-to-end through a real narrator call
- OTEL span audit: verify narrator output is consistent with `dogfight.cell_resolved` span data

**Out of scope:**
- Hit severity narration (38-7 adds the severity column first)
- Extend-and-return multi-exchange pacing (38-8)
- UI cockpit panel component (future epic, not in 38)
- Skill tier narrative tells (pilot_skills.yaml is forward-capture)

## AC Context

**AC1: Narrator renders cockpit-POV from per_actor_state**
- Given a resolved dogfight turn with two actors' updated descriptors, the narrator produces 2-3 sentences per pilot describing the scene from that pilot's cockpit perspective
- Each narration block references only fields present in that pilot's descriptor (bearing, range, aspect, closure, energy cues, gun_solution)
- Verify: narration for a pilot with `gun_solution: false` never mentions firing; narration for `target_bearing: "06"` describes the target behind, not ahead

**AC2: Geometry strictly bounded by descriptor**
- The narrator MUST NOT hallucinate geometry. If `target_range` is "close", the narrator cannot describe a distant speck. If `environment` is "deep_space", no asteroids
- Verify: Run the `duel_01` scenario through 3 turns and confirm zero SOUL violations in narrator output (no invented geometry)

**AC3: Per-pilot private delivery via perception_filters**
- Red pilot sees only Red's cockpit narration; Blue pilot sees only Blue's
- Verify: In a multiplayer session, each player's WebSocket receives only their own cockpit block

**AC4: Integration test with duel_01 scenario**
- End-to-end test: start a dogfight confrontation with merge starting state, commit maneuvers for both pilots, verify narrator produces per-pilot output that matches the resolved cell's narration_hint beat
- This is the first live-fire test of the full dogfight pipeline: content → loader → barrier → resolution → narrator → player

## Assumptions

- 38-5's `SealedLetterLookup` handler correctly passes `per_actor_state` and `narration_hint` to the narrator dispatch path. If it doesn't, this story must wire that handoff before the prompt extension.
- `SharedSession.perception_filters` can scope to per-confrontation-actor, not just per-player. If the filter is player-granular only, this story needs to extend it to support confrontation-actor mapping.
- The narrator's existing system prompt template has a conditional extension point (e.g., `{% if confrontation_mode == "sealed_letter_lookup" %}`) or can be structured to add one.
