---
description: Generate ACE-Step audio tracks and mood variations for genre packs
---

# Music Generation

Generate mood-based music tracks using the ACE-Step worker in the sidequest-renderer daemon. Each genre pack defines moods (exploration, combat, tension, rest, etc.) and the script generates multiple variation types per mood.

## Parameters

| Param | Description | Default |
|-------|-------------|---------|
| `--genre <name>` | Only process this genre pack | *required* |
| `--mood <name>` | Only generate this mood | all moods |
| `--variation <type>` | Only generate this variation type | all variations |
| `--dry-run` | Preview prompts without generating | false |
| `--duration <seconds>` | Override track duration | 60 |

## Usage

```bash
# Generate all moods for a genre
python3 scripts/generate_music.py --genre pulp_noir

# One mood only
python3 scripts/generate_music.py --genre pulp_noir --mood exploration

# One specific variation
python3 scripts/generate_music.py --genre pulp_noir --mood combat --variation sparse

# Preview all prompts
python3 scripts/generate_music.py --genre pulp_noir --dry-run
```

## Prerequisites

- **Daemon must be running:** `just daemon-run` or `sidequest-renderer`
- ACE-Step worker must be warm (happens automatically on first music render)
- `ffmpeg` installed (for WAV → OGG conversion)

## Script

`scripts/generate_music.py` (ported from sq-2)

## Variation Types

| Type | Character |
|------|-----------|
| `full` | Full arrangement, complete orchestration, all instruments |
| `ambient` | Atmospheric, reverb, pads, stripped, minimal |
| `sparse` | Minimalist, solo instrument, space, silence |
| `tension_build` | Building tension, rising, crescendo, intensifying |
| `resolution` | Release, calm after storm, settling, peaceful |
| `overture` | Grand opening, introduction, establishing, cinematic |

## Mood Prompts

Each genre defines its own mood prompts in the generation script. The prompt combines:
1. Genre-specific mood description (e.g., "cool jazz, upright bass, brushed drums")
2. Variation suffix (e.g., "ambient, reverb, pads, stripped, minimal")
3. Deterministic seed from `genre + mood + variation`

## Output

- **Format:** OGG Vorbis (converted from WAV via ffmpeg)
- **Location:** `genre_packs/{genre}/audio/music/{mood}_{variation}.ogg`
- **Normalization:** Loudness normalized before conversion
- Auto-skips existing files. Delete to regenerate.

## Audio Config

Generated tracks should be registered in `genre_packs/{genre}/audio.yaml` under `themes`:

```yaml
themes:
  - name: exploration
    mood: exploration
    base_prompt: ""
    variations:
      - type: full
        path: audio/music/exploration_full.ogg
      - type: ambient
        path: audio/music/exploration_ambient.ogg
      - type: sparse
        path: audio/music/exploration_sparse.ogg
```

## Notes

- ACE-Step generation takes ~2-5 minutes per track (much slower than Flux images)
- A full genre with 7 moods x 6 variations = 42 tracks ≈ 2-3 hours
- Seeds are deterministic — same genre+mood+variation always produces same track

## Owned By

**World Builder** agent (`/sq-world-builder`). Run after defining mood prompts for a genre.
