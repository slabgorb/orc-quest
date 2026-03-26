---
parent: context-epic-4.md
---

# Story 4-10: Audio Mixer Coordination -- 3-Channel Mixing Commands, Ducking During Speech

## Business Context

The client plays audio on three channels simultaneously: music (background score),
SFX (combat hits, spell sounds), and ambience (wind, tavern chatter, forest crickets).
The audio mixer coordinator on the Rust server decides how these channels interact --
most importantly, ducking music volume when TTS voice is playing so the player can hear
the narration clearly.

In Python, `sq-2/sidequest/audio/mixer.py` tracks channel states and emits volume
commands. The Rust port models the mixer as a state machine that produces `AudioCue`
commands for each channel, coordinating with TTS streaming events.

**Python source:** `sq-2/sidequest/audio/mixer.py` (AudioMixer)
**Depends on:** Story 4-9 (music director provides the mood-based music cues)

## Technical Approach

### Channel Model

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum AudioChannel {
    Music,
    Sfx,
    Ambience,
}

#[derive(Debug, Clone)]
pub enum AudioAction {
    Play,
    FadeIn { duration_ms: u32 },
    FadeOut { duration_ms: u32 },
    Duck { target_volume: f32, duration_ms: u32 },
    Restore { duration_ms: u32 },
    Stop,
}

#[derive(Debug, Clone)]
pub struct ChannelState {
    pub track_id: Option<String>,
    pub volume: f32,
    pub base_volume: f32,  // Pre-duck volume to restore to
    pub is_ducked: bool,
}
```

### AudioMixer

```rust
pub struct AudioMixer {
    channels: HashMap<AudioChannel, ChannelState>,
    duck_config: DuckConfig,
}

pub struct DuckConfig {
    pub duck_volume: f32,      // Volume during TTS (default 0.15)
    pub duck_fade_ms: u32,     // Fade down duration (default 300)
    pub restore_fade_ms: u32,  // Fade up duration (default 500)
    pub sfx_duck_volume: f32,  // SFX during TTS (default 0.3)
}

impl AudioMixer {
    pub fn new(config: DuckConfig) -> Self {
        let mut channels = HashMap::new();
        channels.insert(AudioChannel::Music, ChannelState::default());
        channels.insert(AudioChannel::Sfx, ChannelState::default());
        channels.insert(AudioChannel::Ambience, ChannelState::default());
        Self { channels, duck_config: config }
    }

    /// Apply a music director cue to the appropriate channel
    pub fn apply_cue(&mut self, cue: AudioCue) -> Vec<AudioCue> {
        let channel = self.channels.get_mut(&cue.channel).unwrap();
        channel.track_id = Some(cue.track_id.clone());
        channel.volume = cue.volume;
        channel.base_volume = cue.volume;
        vec![cue]  // Pass through; mixer may add supplementary cues
    }

    /// Duck all channels for TTS playback
    pub fn on_tts_start(&mut self) -> Vec<AudioCue> {
        let mut cues = Vec::new();
        for (channel, state) in &mut self.channels {
            if state.track_id.is_some() && !state.is_ducked {
                let target = match channel {
                    AudioChannel::Music => self.duck_config.duck_volume,
                    AudioChannel::Sfx => self.duck_config.sfx_duck_volume,
                    AudioChannel::Ambience => self.duck_config.duck_volume,
                };
                state.base_volume = state.volume;
                state.volume = target;
                state.is_ducked = true;
                cues.push(AudioCue {
                    channel: channel.clone(),
                    action: AudioAction::Duck {
                        target_volume: target,
                        duration_ms: self.duck_config.duck_fade_ms,
                    },
                    track_id: state.track_id.clone().unwrap_or_default(),
                    volume: target,
                });
            }
        }
        cues
    }

    /// Restore channels after TTS ends
    pub fn on_tts_end(&mut self) -> Vec<AudioCue> {
        let mut cues = Vec::new();
        for (channel, state) in &mut self.channels {
            if state.is_ducked {
                state.volume = state.base_volume;
                state.is_ducked = false;
                cues.push(AudioCue {
                    channel: channel.clone(),
                    action: AudioAction::Restore {
                        duration_ms: self.duck_config.restore_fade_ms,
                    },
                    track_id: state.track_id.clone().unwrap_or_default(),
                    volume: state.base_volume,
                });
            }
        }
        cues
    }
}
```

### Integration with TTS Pipeline

The mixer hooks into the TTS streaming lifecycle:

```rust
// When TTS starts streaming
let duck_cues = mixer.on_tts_start();
for cue in duck_cues {
    let _ = ws_tx.send(GameMessage::AudioCue(cue));
}

// ... TTS chunks stream ...

// When TTS finishes
let restore_cues = mixer.on_tts_end();
for cue in restore_cues {
    let _ = ws_tx.send(GameMessage::AudioCue(cue));
}
```

### Ambience Track Support

Ambience tracks are set based on location, not mood. The mixer accepts ambience cues
separately from music director cues:

```rust
impl AudioMixer {
    pub fn set_ambience(&mut self, track_id: &str, volume: f32) -> AudioCue {
        let state = self.channels.get_mut(&AudioChannel::Ambience).unwrap();
        state.track_id = Some(track_id.to_string());
        state.volume = volume;
        state.base_volume = volume;
        AudioCue {
            channel: AudioChannel::Ambience,
            action: AudioAction::FadeIn { duration_ms: 1000 },
            track_id: track_id.to_string(),
            volume,
        }
    }
}
```

## Scope Boundaries

**In scope:**
- `AudioMixer` with 3-channel state tracking
- `on_tts_start()` / `on_tts_end()` ducking lifecycle
- `apply_cue()` for music director integration
- `set_ambience()` for location-based ambience
- `DuckConfig` with configurable volumes and fade durations
- `AudioAction` enum with Duck/Restore variants
- Channel state tracking (volume, base_volume, is_ducked)
- Unit tests for ducking, restoration, and cue pass-through

**Out of scope:**
- Client-side audio implementation (client owns Web Audio API)
- Actual audio mixing (server sends commands, client mixes)
- Volume normalization across tracks
- SFX triggering from game events (deferred to later epic)
- Crossfade between music tracks (client handles fade curves)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Three channels | Mixer tracks Music, SFX, and Ambience independently |
| Duck on TTS start | `on_tts_start()` reduces all active channels to duck volume |
| Restore on TTS end | `on_tts_end()` restores channels to pre-duck base volume |
| Music cue passthrough | Music director cues applied to Music channel state |
| Ambience separate | `set_ambience()` sets ambience track independently of mood |
| Duck config | Duck volumes and fade durations configurable |
| SFX duck level | SFX ducks to higher volume than music (still audible) |
| Idempotent duck | Calling `on_tts_start()` twice does not double-duck |
| No-track skip | Channels with no active track are not ducked |
| Cue output | All methods return `Vec<AudioCue>` for WebSocket broadcast |
