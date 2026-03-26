---
parent: context-epic-4.md
---

# Story 4-9: Music Director Integration -- Mood Extraction from Narration, AUDIO_CUE Message Generation

## Business Context

The music director reads the narrative mood and tells the client what music to play.
When combat starts, drums kick in. When the party enters a quiet forest, ambient strings
fade up. When tension builds before a boss reveal, suspense tracks replace the exploration
theme. This is what makes SideQuest feel like a cinematic experience rather than a text
adventure.

In Python, `sq-2/sidequest/audio/director.py` extracts mood from narration text and
game state, then selects tracks from the genre pack's mood library. The Rust port adds
a typed `Mood` enum, generates `AudioCue` commands for the client, and integrates with
the turn pipeline to fire cues after each narration.

**Python source:** `sq-2/sidequest/audio/director.py` (MusicDirector.evaluate_mood, select_track)
**Depends on:** Story 4-1 (daemon client -- music director may request generated tracks)

## Technical Approach

### Mood Classification

```rust
#[derive(Debug, Clone, PartialEq, Hash, Eq)]
pub enum Mood {
    Combat,
    Exploration,
    Tension,
    Triumph,
    Sorrow,
    Mystery,
    Calm,
}

pub struct MoodClassification {
    pub primary: Mood,
    pub intensity: f32,      // 0.0-1.0
    pub confidence: f32,     // 0.0-1.0
}
```

### Music Director

```rust
pub struct MusicDirector {
    mood_keywords: HashMap<Mood, Vec<String>>,
    mood_tracks: HashMap<Mood, Vec<TrackInfo>>,
    current_mood: Option<Mood>,
    current_track: Option<String>,
}

pub struct TrackInfo {
    pub track_id: String,
    pub duration_secs: Option<f32>,
    pub energy: f32,  // 0.0-1.0, for intensity matching
}

impl MusicDirector {
    pub fn from_genre_pack(media_config: &MediaConfig) -> Self {
        Self {
            mood_keywords: Self::default_mood_keywords(),
            mood_tracks: media_config.mood_tracks.clone().into(),
            current_mood: None,
            current_track: None,
        }
    }

    pub fn evaluate(&mut self, narration: &str, context: &MoodContext) -> Option<AudioCue> {
        let classification = self.classify_mood(narration, context);

        // Only emit a cue if mood actually changed
        if self.current_mood.as_ref() == Some(&classification.primary)
            && classification.intensity < 0.8  // High intensity always re-cues
        {
            return None;
        }

        let track = self.select_track(&classification)?;
        let cue = AudioCue {
            channel: AudioChannel::Music,
            action: self.transition_action(&classification),
            track_id: track.track_id.clone(),
            volume: self.intensity_to_volume(classification.intensity),
        };

        self.current_mood = Some(classification.primary);
        self.current_track = Some(track.track_id);
        Some(cue)
    }
}
```

### Mood Extraction Heuristics

```rust
fn classify_mood(&self, narration: &str, context: &MoodContext) -> MoodClassification {
    // State-based overrides take priority
    if context.in_combat {
        return MoodClassification { primary: Mood::Combat, intensity: 0.8, confidence: 1.0 };
    }
    if context.in_chase {
        return MoodClassification { primary: Mood::Tension, intensity: 0.9, confidence: 1.0 };
    }

    // Keyword scoring
    let mut scores: HashMap<Mood, f32> = HashMap::new();
    let lower = narration.to_lowercase();
    for (mood, keywords) in &self.mood_keywords {
        let count = keywords.iter().filter(|kw| lower.contains(kw.as_str())).count();
        if count > 0 {
            *scores.entry(mood.clone()).or_default() += count as f32;
        }
    }

    // Highest scoring mood wins, default to Exploration
    scores.into_iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
        .map(|(mood, score)| MoodClassification {
            primary: mood,
            intensity: (score / 5.0).clamp(0.3, 1.0),
            confidence: (score / 3.0).clamp(0.0, 1.0),
        })
        .unwrap_or(MoodClassification {
            primary: Mood::Exploration,
            intensity: 0.4,
            confidence: 0.2,
        })
}
```

### MoodContext

```rust
pub struct MoodContext {
    pub in_combat: bool,
    pub in_chase: bool,
    pub party_health_pct: f32,  // Low health → Tension
    pub quest_completed: bool,  // Just completed → Triumph
    pub npc_died: bool,         // NPC death → Sorrow
}
```

### Transition Actions

Mood changes use different audio transitions:

```rust
fn transition_action(&self, classification: &MoodClassification) -> AudioAction {
    match (&self.current_mood, &classification.primary) {
        (None, _) => AudioAction::FadeIn,
        (Some(Mood::Combat), Mood::Exploration) => AudioAction::FadeOut, // Combat end: fade
        (_, Mood::Combat) => AudioAction::Play,  // Combat start: immediate
        _ => AudioAction::FadeIn,  // Default: crossfade
    }
}
```

### AudioCue Protocol Message

```rust
#[derive(Debug, Clone, Serialize)]
pub struct AudioCue {
    pub channel: AudioChannel,
    pub action: AudioAction,
    pub track_id: String,
    pub volume: f32,
}

pub enum GameMessage {
    // ... existing variants
    AudioCue(AudioCue),
}
```

## Scope Boundaries

**In scope:**
- `MusicDirector` with `evaluate()` returning `Option<AudioCue>`
- `Mood` enum with keyword-based classification
- `MoodContext` for state-based overrides (combat, chase, health)
- Track selection from genre pack's mood library
- Mood change detection (only cue on actual transitions)
- Transition action selection (fade, immediate, crossfade)
- `AudioCue` protocol message
- Unit tests for mood classification and track selection

**Out of scope:**
- MusicGen generation (daemon capability, not used in MVP)
- Crossfade timing (client decides fade curves)
- Per-player mood preferences
- Theme rotation / anti-repetition (that's story 4-11)
- Audio mixer multi-channel coordination (that's story 4-10)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Combat mood | In-combat context forces `Mood::Combat` regardless of narration |
| Keyword scoring | "sword clashes" narration scores Combat higher than Exploration |
| Mood change only | Same mood twice in a row does not emit a new cue |
| Track selection | Selected track comes from genre pack's mood_tracks for that mood |
| Transition action | Combat start uses `Play` (immediate), combat end uses `FadeOut` |
| Volume from intensity | Higher mood intensity maps to higher volume (clamped) |
| Default mood | Unclassifiable narration defaults to Exploration |
| State overrides | Chase context overrides to Tension, quest complete to Triumph |
| Protocol message | `AudioCue` serializes to correct JSON for WebSocket |
| Genre pack driven | All track IDs come from genre pack, not hardcoded |
