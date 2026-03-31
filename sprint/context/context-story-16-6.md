---
parent: context-epic-16.md
---

# Story 16-6: Standoff Confrontation Type — Spaghetti Western Pre-Combat Encounter

## Business Context

The standoff is the spaghetti western genre's signature moment — the Mexican standoff
from *The Good, the Bad and the Ugly*. Two or more enemies face each other, hands near
weapons, tension building beat by beat until someone draws. Currently LLM-only with no
mechanical enforcement. This makes it the first genre-specific StructuredEncounter type.

## Technical Approach

### YAML Declaration (spaghetti_western/rules.yaml)

```yaml
confrontations:
  - type: standoff
    label: "Standoff"
    category: pre_combat
    metric:
      name: tension
      direction: ascending
      starting: 0
      threshold_high: 10
    beats:
      - id: size_up
        label: "Size Up"
        metric_delta: 2
        stat_check: CUNNING
        reveals: opponent_detail
      - id: bluff
        label: "Bluff"
        metric_delta: 3
        stat_check: NERVE
        risk: "opponent may call it — immediate draw"
      - id: flinch
        label: "Flinch"
        metric_delta: -1
        consequence: "lose initiative if it escalates to combat"
      - id: draw
        label: "Draw"
        resolution: true
        stat_check: DRAW
        modifier: tension_bonus
    secondary_stats:
      - name: focus
        source_stat: NERVE
        spendable: true
    escalates_to: combat
    mood: standoff
    cinematography:
      camera_override: close_up_slow_motion
      sentence_range: [2, 4]
```

### Encounter Flow

1. Narrator or game state triggers standoff (two hostile parties face off)
2. Engine creates StructuredEncounter with type "standoff", metric tension at 0
3. Each beat: player chooses size_up, bluff, flinch, or draw
4. Tension metric changes per beat. Size Up reveals one opponent detail.
5. When tension hits threshold (10) or player chooses Draw → resolution
6. Resolution: DRAW stat check + accumulated tension bonus determines who fires first
7. Escalates to CombatState with initiative informed by standoff outcome

### Narrator Context Format

```
[STANDOFF]
Phase: ESCALATION | Beat: 3 | Tension: 7/10
Focus: 4/6 (NERVE) — spendable for advantage
Opponent: [details revealed by Size Up beats]
Available:
  1. Size Up [tension +2, CUNNING check, reveals detail]
  2. Bluff [tension +3, NERVE check, risk: opponent may call it]
  3. Flinch [tension -1, lose initiative]
  4. Draw [DRAW check + tension bonus, resolves standoff]
Camera: Close-up, slow-motion | Pace: Peak intensity | Sentences: 2-4
```

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/.../spaghetti_western/rules.yaml` | Add confrontations section |
| `sidequest-game/src/encounter.rs` | Standoff convenience constructor |
| `sidequest-agents/src/agents/dialectician.rs` | Handle standoff encounter type |
| Integration test | Full standoff sequence: setup → beats → draw → combat escalation |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Loads | Standoff declaration parses from spaghetti_western rules.yaml |
| Beats work | Size Up, Bluff, Flinch, Draw all modify tension correctly |
| Reveals | Size Up reveals one opponent detail per beat |
| Resolution | Draw resolves with DRAW check + tension modifier |
| Escalation | Resolved standoff transitions to CombatState with initiative |
| Mood | MusicDirector plays "standoff" mood during encounter |
| Narrator context | Full standoff context injected into narrator prompt |
| Integration test | Complete standoff sequence from start to combat escalation |
