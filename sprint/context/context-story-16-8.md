---
parent: context-epic-16.md
---

# Story 16-8: Genre-Specific Confrontation Types — Net Combat, Ship Combat, Auction

## Business Context

Three genres have unique encounter types that don't fit the social or chase templates:
neon_dystopia (net combat / hacking), space_opera (ship-to-ship combat), and victoria
(auction / bidding war). Each uses the StructuredEncounter infrastructure with
genre-specific metrics, beats, and secondary stats.

## Technical Approach

### Net Combat (neon_dystopia)

```yaml
- type: net_combat
  label: "Net Run"
  category: combat
  metric:
    name: trace
    direction: ascending
    starting: 0
    threshold_high: 10   # traced — ICE converges
  beats:
    - id: infiltrate
      label: "Infiltrate"
      metric_delta: 1
      stat_check: NET
      effect: "advance one node deeper"
    - id: smash
      label: "Brute Force"
      metric_delta: 3
      stat_check: TECH
      risk: "ICE counterattack if failed"
    - id: mask
      label: "Mask Signal"
      metric_delta: -2
      stat_check: COOL
    - id: jack_out
      label: "Jack Out"
      resolution: true
      consequence: "safe exit, progress lost"
  secondary_stats:
    - name: firewall
      source_stat: TECH
    - name: deck_hp
      max: 10
  mood: cyberspace
```

### Ship Combat (space_opera)

```yaml
- type: ship_combat
  label: "Ship Engagement"
  category: combat
  metric:
    name: engagement_range
    direction: bidirectional
    starting: 5
    threshold_high: 10   # disengaged — escaped
    threshold_low: 0     # point blank — boarding
  secondary_stats:
    - name: shields
      max: 20
    - name: hull
      max: 30
    - name: engines
      max: 15
  beats:
    - id: broadside
      label: "Broadside"
      metric_delta: 0
      stat_check: CUNNING
      effect: "deal damage to target shields/hull"
    - id: evasive
      label: "Evasive Maneuvers"
      metric_delta: 2
      stat_check: REFLEX
    - id: close_range
      label: "Close to Boarding Range"
      metric_delta: -2
      stat_check: RESOLVE
    - id: flee
      label: "Full Retreat"
      metric_delta: 3
      stat_check: REFLEX
      risk: "exposed rear, double damage if failed"
  mood: combat
```

### Auction (victoria)

```yaml
- type: auction
  label: "Auction"
  category: social
  metric:
    name: bid
    direction: ascending
    starting: 0
    threshold_high: null  # no cap — resolved by withdrawal
  beats:
    - id: raise
      label: "Raise the Bid"
      metric_delta: 1
      stat_check: null     # no check — just money
      requires: "sufficient funds"
    - id: bluff
      label: "Feign Disinterest"
      metric_delta: 0
      stat_check: CUNNING
      effect: "opponent may over-bid or withdraw"
    - id: withdraw
      label: "Withdraw"
      resolution: true
      consequence: "lose the item, keep the money"
  secondary_stats:
    - name: purse
      source_stat: null
      spendable: true
  mood: tension
```

### Key Files

| File | Action |
|------|--------|
| `sidequest-content/.../neon_dystopia/rules.yaml` | Add net_combat confrontation |
| `sidequest-content/.../space_opera/rules.yaml` | Add ship_combat confrontation |
| `sidequest-content/.../victoria/rules.yaml` | Add auction confrontation |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Net combat loads | neon_dystopia net_combat parses from rules.yaml |
| Ship combat loads | space_opera ship_combat parses from rules.yaml |
| Auction loads | victoria auction parses from rules.yaml |
| Multi secondary stats | Ship combat with 3 secondary stats (shields, hull, engines) works |
| No threshold_high | Auction with null threshold_high resolves by withdrawal only |
| Genre validation | stat_check references valid per-genre ability scores |
