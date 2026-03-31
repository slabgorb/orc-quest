---
parent: context-epic-16.md
---

# Story 16-14: String-Keyed Moods + Fallback Aliases — Genre Packs Declare Custom Moods

## Business Context

Genre packs define 15+ custom moods (standoff, saloon, convoy, cyberspace, etc.) with
dedicated music tracks. The MusicDirector classifies narration into 7 hardcoded Mood
enum variants. Custom moods fall through to the nearest match, wasting genre-specific
audio. Code review found that mood_tracks is already HashMap<String, Vec<MoodTrack>>
internally — this is a ~50 line fix, not a rewrite.

## Technical Approach

### Finding: MusicDirector is Already String-Keyed Internally

`mood_tracks: HashMap<String, Vec<MoodTrack>>` — track selection uses string keys.
The `Mood` enum only gates the classification step. Track lookup is already generic.

### Add mood_aliases to AudioConfig

```yaml
# In audio.yaml
mood_aliases:
  standoff: tension
  saloon: calm
  riding: exploration
  convoy: exploration
  betrayal: tension
  cyberspace: mystery
  club: exploration
  corporate: calm
  teahouse: calm
  spirit: mystery
  void: sorrow
```

### Add genre mood_keywords

```yaml
mood_keywords:
  standoff:
    - standoff
    - duel
    - draw
    - stare down
    - hands near weapons
  saloon:
    - saloon
    - bar
    - tavern
    - drinking
    - cards
    - piano
  riding:
    - gallop
    - riding
    - hooves
    - horseback
    - pursuit
```

### Resolution Chain

1. If active StructuredEncounter has `mood_override` → use that string directly
2. Classify mood from narration using mood_keywords (already string-keyed)
3. Look up classified mood string in mood_tracks HashMap
4. If not found → follow mood_aliases chain (max 3 hops to prevent cycles)
5. If still not found → fall back to "exploration"

### Changes to MusicDirector

```rust
// Add to MusicDirector struct
mood_aliases: HashMap<String, String>,

// In evaluate() — after classification
fn resolve_mood_key(&self, raw_mood: &str) -> &str {
    if self.mood_tracks.contains_key(raw_mood) {
        return raw_mood;
    }
    let mut key = raw_mood;
    for _ in 0..3 {  // max 3 alias hops
        match self.mood_aliases.get(key) {
            Some(alias) if self.mood_tracks.contains_key(alias.as_str()) => return alias,
            Some(alias) => key = alias,
            None => break,
        }
    }
    "exploration"  // safe fallback
}
```

### Key Files

| File | Action |
|------|--------|
| `sidequest-game/src/music_director.rs` | Add mood_aliases, resolve_mood_key |
| `sidequest-genre/src/models.rs` | Add mood_aliases to AudioConfig |
| `sidequest-genre/src/loader.rs` | Parse mood_aliases from audio.yaml |
| `sidequest-content/.../*/audio.yaml` | Add mood_aliases and genre mood_keywords |

## Scope Boundaries

**In scope:**
- mood_aliases in AudioConfig YAML
- Genre-specific mood_keywords
- Alias resolution chain in MusicDirector
- StructuredEncounter mood_override integration

**Out of scope:**
- Faction music routing (16-15)
- Removing the Mood enum entirely (backward compat — keep as classification helper)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Alias resolution | "standoff" resolves to "tension" via alias chain |
| Direct match | "combat" resolves directly (no alias needed) |
| Genre keywords | "saloon" classified from narration containing "whiskey" and "cards" |
| Cycle safe | Alias chain limited to 3 hops |
| Fallback | Unknown mood falls back to "exploration" |
| Encounter override | Active StructuredEncounter's mood_override takes priority |
| Backward compat | All existing mood classification tests still pass |
| Genre tracks play | spaghetti_western standoff music plays during standoff narration |
