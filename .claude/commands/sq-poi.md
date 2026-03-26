---
description: Generate landscape images for Points of Interest across genre packs
---

# POI Image Generation

Generate landscape images for Points of Interest defined in genre pack history.yaml files using the sidequest-renderer daemon.

## Parameters

| Param | Description | Default |
|-------|-------------|---------|
| `--genre <name>` | Only process this genre pack | all genres |
| `--world <name>` | Only process this world | all worlds |
| `--poi <name>` | Regenerate a specific POI by name | all POIs |
| `--dry-run` | Preview prompts without rendering | false |
| `--steps <n>` | Flux inference steps (higher = better quality) | 15 |
| `--output-dir <path>` | Override output directory | `genre_packs/{genre}/images/poi/` |

## Usage

```bash
# All genres, all POIs
python3 scripts/generate_poi_images.py

# One genre
python3 scripts/generate_poi_images.py --genre elemental_harmony

# One world within a genre
python3 scripts/generate_poi_images.py --genre elemental_harmony --world shattered_accord

# Regenerate a specific POI (delete existing first)
rm genre_packs/low_fantasy/images/poi/the_sodden_boot.png
python3 scripts/generate_poi_images.py --genre low_fantasy --poi "The Sodden Boot"

# Preview prompts
python3 scripts/generate_poi_images.py --dry-run

# Higher quality
python3 scripts/generate_poi_images.py --steps 20
```

## Prerequisites

- **Daemon must be running:** `just daemon-run` or `sidequest-renderer`
- Daemon Flux worker must be warm (happens automatically on first render)

## Script

`scripts/generate_poi_images.py`

## Render Settings

- **Model:** Flux-dev | **Steps:** 15 default | **Resolution:** 1024x768 (landscape) | **Guidance:** 3.5
- **Seeds:** Deterministic from genre + world + POI name

## Monitoring

```bash
tail -f /tmp/poi-gen.log
find genre_packs/*/images/poi -name "*.png" | wc -l
```

## Finding Gaps

```bash
python3 -c "
import yaml
from pathlib import Path
genres = Path('genre_packs')
for g in sorted(d.name for d in genres.iterdir() if d.is_dir()):
    for h in (genres / g).rglob('history.yaml'):
        data = yaml.safe_load(open(h)) or {}
        pois = sum(len(ch.get('points_of_interest', [])) for ch in data.get('chapters', []))
        imgs = len(list((genres / g / 'images' / 'poi').glob('*.png'))) if (genres / g / 'images' / 'poi').exists() else 0
        print(f'{g:25s} POIs: {pois:3d}  Images: {imgs:3d}  Gap: {pois - imgs}')
"
```

## Notes

- Script auto-skips existing images. Safe to re-run after interruption.
- To regenerate a specific image, delete the PNG first then re-run with `--poi`.
- ~90-100 seconds per image on MPS (Apple Silicon).

## Owned By

**World Builder** agent (`/sq-world-builder`). Run after creating/updating POIs in history.yaml.
