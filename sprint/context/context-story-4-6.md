---
parent: context-epic-4.md
---

# Story 4-6: TTS Voice Routing -- Map Character/NPC IDs to Voice Presets from Genre Pack Config

## Business Context

Different characters should sound different. The narrator gets a deep, measured voice;
a goblin NPC gets a raspy, high-pitched one. Voice routing maps character and NPC IDs
to voice presets defined in the genre pack's YAML config. This is the entry point for
the TTS pipeline -- before we can synthesize speech, we need to know which voice to use.

In Python, `sq-2/sidequest/voice/router.py` maintains a mapping of character names to
voice presets, with fallback to a default NPC voice. The Rust port adds type safety with
a `VoiceAssignment` struct and an explicit `TtsModel` enum (Kokoro vs Piper), making
it impossible to pass an invalid model string to the daemon.

**Python source:** `sq-2/sidequest/voice/router.py` (VoiceRouter.route)
**Depends on:** Story 4-1 (daemon client -- voice assignments are used when calling /tts)

## Technical Approach

### Voice Preset Configuration

Genre packs define voice presets in YAML:

```yaml
media:
  voice_presets:
    narrator: { model: "kokoro", voice: "en_male_deep", speed: 0.95 }
    default_npc: { model: "piper", voice: "en_US-lessac-medium", speed: 1.0 }
    # Character-specific overrides (optional)
    characters:
      grimjaw: { model: "kokoro", voice: "en_male_gruff", speed: 0.9 }
      whisper: { model: "piper", voice: "en_GB-alba-medium", speed: 1.1 }
```

### Types

```rust
#[derive(Debug, Clone, PartialEq)]
pub enum TtsModel {
    Kokoro,
    Piper,
}

#[derive(Debug, Clone)]
pub struct VoicePreset {
    pub model: TtsModel,
    pub voice_id: String,
    pub speed: f32,
}

#[derive(Debug, Clone)]
pub struct VoiceAssignment {
    pub character_id: String,
    pub preset: VoicePreset,
    pub source: AssignmentSource,
}

#[derive(Debug, Clone)]
pub enum AssignmentSource {
    GenrePackExplicit,    // Character listed in genre pack
    GenrePackDefault,     // Fell back to default_npc
    SessionOverride,      // Runtime override (future use)
}
```

### VoiceRouter

```rust
pub struct VoiceRouter {
    narrator_preset: VoicePreset,
    default_npc_preset: VoicePreset,
    character_presets: HashMap<String, VoicePreset>,
}

impl VoiceRouter {
    pub fn from_genre_pack(media_config: &MediaConfig) -> Self {
        Self {
            narrator_preset: media_config.voice_presets.narrator.clone().into(),
            default_npc_preset: media_config.voice_presets.default_npc.clone().into(),
            character_presets: media_config.voice_presets.characters
                .iter()
                .map(|(k, v)| (k.clone(), v.clone().into()))
                .collect(),
        }
    }

    pub fn route(&self, speaker: &Speaker) -> VoiceAssignment {
        match speaker {
            Speaker::Narrator => VoiceAssignment {
                character_id: "narrator".into(),
                preset: self.narrator_preset.clone(),
                source: AssignmentSource::GenrePackExplicit,
            },
            Speaker::Character(id) => {
                if let Some(preset) = self.character_presets.get(id) {
                    VoiceAssignment {
                        character_id: id.clone(),
                        preset: preset.clone(),
                        source: AssignmentSource::GenrePackExplicit,
                    }
                } else {
                    VoiceAssignment {
                        character_id: id.clone(),
                        preset: self.default_npc_preset.clone(),
                        source: AssignmentSource::GenrePackDefault,
                    }
                }
            }
        }
    }
}
```

### Speaker Identification

The router needs to know who is speaking. Narration text uses conventions like
`"Grimjaw says: ..."` or italicized narrator prose. A simple classifier:

```rust
#[derive(Debug, Clone)]
pub enum Speaker {
    Narrator,
    Character(String),
}

pub fn identify_speaker(text: &str, known_npcs: &[String]) -> Speaker {
    // Check for "NAME says:" or "NAME:" dialogue patterns
    for npc in known_npcs {
        if text.starts_with(&format!("{} says:", npc))
            || text.starts_with(&format!("{}:", npc))
        {
            return Speaker::Character(npc.clone());
        }
    }
    Speaker::Narrator
}
```

## Scope Boundaries

**In scope:**
- `VoiceRouter` struct with `route()` method
- `VoiceAssignment`, `VoicePreset`, `TtsModel` types
- Genre pack YAML parsing for voice presets
- Character-specific preset lookup with default fallback
- Speaker identification from narration text patterns
- `AssignmentSource` tracking (explicit vs default)
- Unit tests for routing logic and speaker identification

**Out of scope:**
- Voice cloning or training custom voices
- Runtime voice reassignment UI
- Emotional tone modulation (same voice, different emotion)
- Multi-language voice support
- Text segmentation (that's story 4-7)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Narrator routing | Narrator text routes to `narrator` voice preset |
| Known NPC routing | NPC with explicit preset gets that preset |
| Default fallback | Unknown NPC falls back to `default_npc` preset |
| Model typing | `TtsModel::Kokoro` and `TtsModel::Piper` -- no raw strings |
| Speed preserved | Voice speed from genre pack config passed through |
| Source tracking | `AssignmentSource` indicates whether explicit or default |
| Speaker detection | "Grimjaw says: hello" identifies speaker as Grimjaw |
| Genre pack load | `VoiceRouter::from_genre_pack()` parses media config correctly |
| Empty config | Missing `characters` section defaults all NPCs to default_npc |
| Test coverage | Tests for narrator, known NPC, unknown NPC, and speaker identification |
