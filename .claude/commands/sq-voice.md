---
description: Voice management — assign, create, blend, and manipulate creature/NPC voices with Kokoro TTS and conlang pronunciation
---

# Voice Management

Create, assign, and manipulate voices for NPCs and creatures. Manages both the voice presets in genre pack `audio.yaml` and the conlang-to-IPA pronunciation pipeline for Kokoro TTS.

## Parameters

| Param | Description | Default |
|-------|-------------|---------|
| `--genre <name>` | Target genre pack | *required for assign/create* |
| `--creature <type>` | Creature type to assign/create | — |
| `--blend <spec>` | Voice blend specification (e.g., `am_echo(3)+am_onyx(2)`) | — |
| `--preview <text>` | Synthesize preview text with the voice | — |
| `--dry-run` | Show configuration without writing | false |
| `--list` | List existing presets for a genre | — |

## Modes

### 1. Assign Voice

Assign an existing Kokoro voice or creature preset to an NPC or role.

```yaml
# In genre_packs/{genre}/audio.yaml → creature_voice_presets
creature_voice_presets:
  dragon:
    creature_type: dragon
    description: "Deep, rumbling voice with cavernous reverb"
    pitch: 0.6
    rate: 0.8
    effects:
      - type: reverb
        params: { room_size: 0.8 }
      - type: lowpass_filter
        params: { cutoff_frequency_hz: 2000 }
```

### 2. Create Voice (Tensor Blending)

Create new voices by blending Kokoro voice tensors. This operates BEFORE synthesis in embedding space — produces genuinely different voices, not just audio effects.

**Blend syntax:** `voice1(weight)+voice2(weight)`

```yaml
creature_voice_presets:
  droid:
    creature_type: droid
    description: "Precise, measured synthetic voice"
    blend: "am_echo(3)+am_onyx(2)+af_nova(1)"  # 50%/33%/17% tensor mix
    pitch: 1.0
    rate: 0.92
    effects:
      - type: highpass_filter
        params: { cutoff_hz: 180 }
```

**Available base voices (54 total):**
- American: af_alloy, af_aoede, af_bella, af_heart, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky, am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa
- British: bf_alice, bf_emma, bf_isabella, bf_lily, bm_daniel, bm_fable, bm_george, bm_lewis
- Other: ef_dora, em_alex, ff_siwis, hf_alpha, hf_beta, hm_omega, hm_psi, if_sara, im_nicola, jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro, jm_kumo, pf_dora, pm_alex, pm_santa, zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi, zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang

**Voice character tips:**
- Flat/measured: am_echo, am_onyx — good droid bases
- Deep/growly: am_fenrir, am_adam — good monster bases
- Cross-language blends create uncanny/alien prosody: jf_gongitsune + am_fenrir
- Extrapolation beyond [0,1] pushes past known voices into uncharted territory

### 3. Manipulate Voice (Post-Synthesis Effects)

**Three levels of voice manipulation:**

| Level | When | Technique |
|-------|------|-----------|
| **Tensor blend** | Before synthesis | Weighted voice tensor mixing in embedding space |
| **Prosody control** | During synthesis | SSML tags, speed, pitch parameters |
| **Audio effects** | After synthesis | Reverb, filters, pitch shift, formant manipulation |

**Available effect types:**
- `reverb` — params: `room_size` (0.0-1.0)
- `lowpass_filter` — params: `cutoff_frequency_hz`
- `highpass_filter` — params: `cutoff_frequency_hz` or `cutoff_hz`
- `pitch_quantize` — params: `interval_hz` (snaps pitch to regular intervals — robotic)
- `harmonic_layer` — params: `octave_offset`, `gain_db` (layer synthesis at different pitch)

**Recipes:**
- **Droid:** blend flat voices + pitch_quantize + highpass + regular SSML breaks
- **Monster:** blend deep voices + pitch shift down + reverb + lowpass
- **Alien:** cross-language blend + rate oscillation + formant narrowing
- **Ghost:** low rate + heavy reverb + highpass + reduced volume
- **Swarm/hive:** blend 3+ voices + chorus effect + irregular rate

### 4. Conlang Pronunciation

Kokoro uses the `misaki` G2P engine which supports IPA pronunciation overrides via markdown link syntax:

```
[Tsveri](/tsvˈɛɹi/) warriors guard the [Xal'thek](/zɑlθˈɛk/) passage.
```

**Without overrides, unknown words become `❓` and are silently skipped.**

**Pipeline:**
1. Conlang generator creates words with phonology rules (cultures.yaml)
2. Build `pronunciation.yaml` per genre pack mapping conlang terms → IPA
3. TTS preprocessor auto-wraps conlang words: `Tsveri` → `[Tsveri](/tsvˈɛɹi/)`
4. Kokoro/misaki picks up IPA directly — perfect pronunciation

**Stress control:**
- `[word](-1)` — lower stress by 1 level (primary → secondary)
- `[word](-2)` — lower stress by 2 levels (remove stress entirely)

**pronunciation.yaml format (proposed):**
```yaml
# genre_packs/{genre}/pronunciation.yaml
terms:
  Tsveri: "/tsvˈɛɹi/"
  Xal'thek: "/zɑlθˈɛk/"
  Kṣatavāri: "/kʃɑtɑvˈɑɹi/"
  Dignagālavā: "/dɪɡnɑɡˈɑlɑvɑ/"
```

**TODO (see docs/research/kokoro-conlang-voice-research.md):**
- [ ] Map conlang phoneme inventory against Kokoro's supported IPA symbols
- [ ] Auto-generate IPA from conlang phonology rules in cultures.yaml
- [ ] Build the TTS preprocessor that wraps conlang words before synthesis
- [ ] Test end-to-end: conlang word → IPA → markdown syntax → Kokoro audio

## Existing Creature Presets by Genre

| Genre | Presets |
|-------|---------|
| low_fantasy | dragon (0.6/0.8), goblin (1.4/1.3), undead (0.7/0.6) |
| space_opera | synthetic (1.0/0.95), xeno_deep (0.6/0.7), xeno_light (1.4/1.2) |
| mutant_wasteland | mutant_brute (0.5/0.7), rad_ghoul (0.8/1.1), sentient_ooze (0.4/0.5) |
| elemental_harmony | *(none yet)* |
| neon_dystopia | *(none yet)* |
| pulp_noir | *(empty)* |
| road_warrior | *(none yet)* |

Format: name (pitch/rate)

## Key Files

- Genre voice config: `genre_packs/{genre}/audio.yaml` → `creature_voice_presets`
- Voice engine: `sidequest-daemon/sidequest_daemon/voice/kokoro.py`
- Voice protocol: `sidequest-daemon/sidequest_daemon/voice/protocol.py`
- Genre voice config model: `sidequest-daemon/sidequest_daemon/voice/genre_config.py`
- Research doc: `docs/research/kokoro-conlang-voice-research.md`

## Key Repos (for advanced techniques)

- **Kokoro-FastAPI:** github.com/remsky/Kokoro-FastAPI — voice blending API
- **KVoiceWalk:** github.com/RobViren/kvoicewalk — random walk voice cloning
- **KokoVoiceLab:** github.com/RobViren/kokovoicelab — voice interpolation explorer
- **Misaki:** github.com/hexgrad/misaki — G2P engine with IPA override syntax

## Owned By

This skill is a responsibility of the **World Builder** agent (`/sq-world-builder`). Voice assignment and creation happens during world building and DM prep.
