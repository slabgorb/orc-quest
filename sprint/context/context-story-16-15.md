---
parent: context-epic-16.md
---

# Story 16-15: Faction Music Routing — Trigger Faction Themes by Context

## Business Context

road_warrior has 10 faction music themes (Bosozoku, Cafe Racers, Dekotora, Lowriders,
Matatu, Mods, One Percenters, Raggare, Rockers, Tuk Tuk) — 147 tracks sitting unused
because nothing tells the MusicDirector "play the Bosozoku theme when the player enters
Bosozoku territory." This story adds faction-aware music selection.

## Technical Approach

### YAML Declaration (audio.yaml)

```yaml
faction_themes:
  bosozoku:
    trigger:
      location_faction: bosozoku    # play when in bosozoku-controlled region
      npc_faction: bosozoku         # play when speaking with bosozoku NPC
      reputation_above: 20          # only if reputation is positive
    tracks:
      - path: audio/music/faction_bosozoku.ogg
        title: "Bosozoku Thunder"
        bpm: 150
  lowriders:
    trigger:
      location_faction: lowriders
      npc_faction: lowriders
    tracks:
      - path: audio/music/faction_lowriders.ogg
        title: "Lowrider Cruise"
        bpm: 85
```

### MusicDirector Integration

Add faction context to MoodContext:

```rust
pub struct MoodContext {
    // ... existing fields
    pub location_faction: Option<String>,     // NEW
    pub interacting_npc_faction: Option<String>,  // NEW
    pub faction_reputations: HashMap<String, i32>, // NEW
}
```

In `evaluate()`, check faction_themes before mood classification:
1. If location_faction matches a faction_theme trigger → use faction track
2. If interacting_npc_faction matches → use faction track
3. If reputation condition met → use faction track
4. Otherwise → proceed with normal mood classification

Faction themes take priority over mood classification but below encounter mood_override.

### Priority Chain (updated)

1. StructuredEncounter mood_override (highest)
2. Faction theme trigger
3. Narration mood classification + alias resolution
4. "exploration" fallback (lowest)

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/music_director.rs` | Faction theme checking in evaluate() |
| `sidequest-genre/src/models.rs` | FactionTheme, FactionTrigger structs |
| `sidequest-genre/src/loader.rs` | Parse faction_themes from audio.yaml |
| `sidequest-content/.../road_warrior/audio.yaml` | Add faction_themes section |
| `sidequest-server/src/shared_session.rs` | Populate MoodContext faction fields |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Trigger by location | Entering bosozoku territory plays Bosozoku Thunder |
| Trigger by NPC | Talking to a lowrider NPC plays Lowrider Cruise |
| Reputation gate | Faction theme only plays if reputation condition met |
| Priority | Encounter override > faction > mood classification |
| No faction themes | Genres without faction_themes work normally |
| road_warrior | All 10 faction themes routable via YAML triggers |
