---
parent: context-epic-38.md
workflow: trivial
---

# Story 38-10: Tail-chase starting state

## Business Context

The MVP dogfight uses a single starting state (`merge` — head-on approach). This validates the core mechanic but doesn't prove it generalizes. A real dogfight campaign needs multiple starting geometries: ambushes from behind, beam crossings, dive attacks. The `tail_chase` starting state is the first proof that the `SealedLetterLookup` + `per_actor_state` architecture supports multiple interaction tables partitioned by starting geometry.

If this works, every future starting state follows the same pattern: author a descriptor, author a 16-cell interaction table, declare it in the confrontation def. The system generalizes. If it doesn't work, the architecture has a scalability problem that must be addressed before the dogfight subsystem can ship in a campaign.

## Technical Guardrails

**Key files to create:**
- `sidequest-content/genre_packs/space_opera/dogfight/playtest/duel_02.md` — paper playtest scaffold for tail-chase geometry
- `sidequest-content/genre_packs/space_opera/dogfight/interactions_tail_chase.yaml` — new 16-cell interaction table for the tail_chase starting state (or extend `interactions_mvp.yaml` with a second table section)

**Key files to modify:**
- `sidequest-content/genre_packs/space_opera/dogfight/descriptor_schema.yaml` — the `tail_chase` starting state is already declared as `status: future`; promote it to `status: mvp` and author the `initial_descriptor`

**Patterns to follow:**
- The merge table's cell structure: `pair`, `name`, `shape`, `red_view`, `blue_view`, `narration_hint`
- Include hit severity (from 38-7) if available
- The tail_chase geometry is asymmetric: Red starts behind Blue (advantaged position). This means the interaction table is NOT symmetric — `(straight, bank)` and `(bank, straight)` have different meanings depending on who is the pursuer vs evader
- Maneuver semantics shift with geometry: a `loop` from a tail-chase means the pursuer overshoots and the evader can reverse; a `kill_rotation` from a tail-chase means the evader flips to face their pursuer

**What NOT to touch:**
- `interactions_mvp.yaml` — the merge table is stable (pending 38-7 severity and 38-9 calibration)
- `maneuvers_mvp.yaml` — the same 4 maneuvers apply; only their geometric meaning changes
- Rust engine code — the `_from:` loader pattern (38-4) already supports multiple table files; the engine selects the correct table based on the confrontation's current starting state

## Scope Boundaries

**In scope:**
- Author the `tail_chase` initial descriptor (pursuer behind evader, close range, tail_on aspect)
- Author a 16-cell interaction table for tail_chase geometry using the same 4 maneuvers
- Create `duel_02.md` paper playtest scaffold for tail_chase
- Narration hints that reflect the asymmetric geometry (pursuer vs evader framing)

**Out of scope:**
- Additional starting states (beam, overhead) — future stories after tail_chase validates
- 8-maneuver expansion — blocked on 38-9 calibration gate
- Engine changes for starting state selection logic (how does the engine decide to start in tail_chase vs merge?) — future story
- Paper playtest runs of duel_02 — calibration is a separate concern

## AC Context

**AC1: Tail-chase initial descriptor authored**
- `descriptor_schema.yaml` starting state `tail_chase` promoted from `future` to `mvp`
- Initial descriptor defined: pursuer (Red) has `target_bearing: "12"`, `target_aspect: tail_on`, `gun_solution: false` (not yet in firing solution — close but not locked); evader (Blue) has `target_bearing: "06"`, `target_aspect: head_on`
- Starting energy: both 60 (same as merge — the geometry is different, not the resource)
- Verify: the initial descriptor is consistent with the merge state's field schema

**AC2: 16-cell interaction table authored**
- All 16 `(red_maneuver, blue_maneuver)` pairs covered for tail_chase geometry
- Each cell has: `pair`, `name`, `shape`, `red_view`, `blue_view`, `narration_hint`
- The table reflects asymmetric geometry: Red is the pursuer, Blue is the evader
- The RPS balance should differ from merge: in a tail chase, evasive maneuvers (bank) are more valuable for the evader, and passive (straight) for the pursuer is more rewarding than in a merge
- Verify: 16 cells present, all 4x4 pairs covered, no duplicates

**AC3: duel_02.md playtest scaffold created**
- Follows the same protocol as `duel_01.md`: sealed-letter commits, GM lookup, per-pilot narration, debrief
- Opening narration describes the tail-chase geometry (one ship behind the other, not head-on)
- Debrief section includes the same calibration tag framework and go/no-go assessment
- Verify: scaffold is structurally identical to `duel_01.md` with tail-chase-specific content

**AC4: Narration hints reflect asymmetric geometry**
- Pursuer narration hints describe chasing, closing, lining up shots
- Evader narration hints describe being chased, breaking free, desperate reversal attempts
- Neither pilot's hints reference the other pilot's private state
- Verify: read all 16 narration hints and confirm they consistently frame Red as pursuer and Blue as evader

## Assumptions

- The `_from:` loader pattern (38-4) can handle multiple interaction table files per confrontation type. If it currently only supports one, the loader needs extension (which would be a prerequisite, not in scope for this story).
- The engine's starting state selection logic (how a confrontation begins in tail_chase vs merge) is NOT in scope — this story only authors the content. Wiring the starting state selector is a future story.
- Hit severity (38-7) may or may not be done. If done, include `hit_severity` in the tail_chase cells. If not, omit it and add it when 38-7 ships.
