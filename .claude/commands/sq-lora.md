---
description: LoRA training pipeline — collect, tag, assess, train, and test genre-specific Flux LoRAs
---

# LoRA Training Pipeline

Train genre-specific LoRAs for Flux image generation. Produces separate landscape and portrait
LoRAs that feed into POI generation and character portrait rendering.

## Parameters

| Param | Description | Default |
|-------|-------------|---------|
| `--genre <name>` | Target genre pack | (required) |
| `--step <1-5>` | Resume from a specific step | 1 |
| `--landscape-only` | Skip portrait LoRA | false |
| `--portrait-only` | Skip landscape LoRA | false |

## Steps

Run steps sequentially. Each step produces artifacts the next step consumes.
Resume from any step with `--step N`.

---

### Step 1: Research & Download

**Goal:** Collect 150-200 training images per category (landscape, portrait).

**Source images from:**
- Film stills (primary) — use `yt-dlp` + `ffmpeg` frame extraction from YouTube cinematography reels
- Western art — Remington, Russell, period-appropriate paintings
- Poster art — vintage film posters with the target visual style
- Photography — reference landscape photography matching the genre's geography

**YouTube frame extraction workflow:**
```bash
# Download a cinematography reel at max quality
yt-dlp -f 'bestvideo[ext=mp4]' -o '%(title)s.%(ext)s' '<URL>'

# Extract frames every N seconds (adjust for scene density)
ffmpeg -i input.mp4 -vf "fps=1/5,scale=1024:-1" -q:v 2 output_dir/frame_%04d.jpg

# For specific timestamp ranges (e.g., a landscape-heavy sequence)
ffmpeg -i input.mp4 -ss 00:02:30 -to 00:05:00 -vf "fps=1/2,scale=1024:-1" -q:v 2 output_dir/frame_%04d.jpg
```

**Output directories:**
```
sidequest-content/{genre}-landscape/   # Wide shots, establishing shots, locations
sidequest-content/{genre}-portraits/   # Close-ups, character shots, faces
```

**Curation rules:**
- Delete blurry frames, transition frames, black frames
- Delete frames with modern anachronisms (cars, power lines, etc.)
- Delete frames with text overlays, watermarks, credits
- Keep frames that strongly express the genre's visual identity
- Landscape: favor wide establishing shots, location atmosphere, architecture
- Portrait: favor extreme close-ups, character framing, expressive lighting

---

### Step 2: Tag & Sort

**Goal:** Create a `.txt` caption file for every image, danbooru-style.

**Caption format:**
```
{trigger_word}, {style_tags}, {subject_tags}
```

**Trigger words** (two per genre, one per LoRA):
- Landscape: `{genre}_landscape` (e.g., `leone_landscape`)
- Portrait: `{genre}_portrait` (e.g., `leone_portrait`)

**Style tags** — consistent across all images in a set. Derived from the genre's
`visual_style.yaml` positive_suffix. Example for spaghetti_western:
```
film_still, cinematic, techniscope, high_contrast, film_grain, desaturated,
washed_out_color, crushed_blacks, dust
```

**Subject tags** — per-image, describe what's in the frame:
```
# Landscape examples
desert, mesa, wide_shot, establishing_shot, heat_shimmer, empty_road
saloon, interior, oil_lamp, wooden_bar, swinging_doors
canyon, sandstone, narrow_passage, deep_shadow, overhead_sun

# Portrait examples
extreme_close_up, eyes, weathered_face, hat_brim_shadow, sweat
medium_shot, poncho, gun_belt, squinting, backlit
two_shot, standoff, tension, shallow_depth_of_field
```

**Process:**
1. View each image (use Read tool on image files)
2. Classify as landscape or portrait — move to appropriate directory
3. Write matching `.txt` file with caption tags
4. Verify every `.jpg`/`.png` has a matching `.txt`

```bash
# Verify 1:1 image-to-caption ratio
ls {genre}-landscape/*.jpg | wc -l
ls {genre}-landscape/*.txt | wc -l
# These numbers must match
```

---

### Step 3: Assess

**Goal:** Verify dataset quality and completeness before committing to a 4-6 hour training run.

**Checklist:**
- [ ] **Volume:** 150+ images per category (landscape and portrait)
- [ ] **Balance:** No single source dominates (>40% of images)
- [ ] **Variety:** Multiple lighting conditions, times of day, weather
- [ ] **Consistency:** Style tags match `visual_style.yaml` language
- [ ] **Coverage:** Key location types from `cartography.yaml` are represented
- [ ] **No poison:** No modern elements, no watermarks, no text overlays
- [ ] **Caption quality:** Spot-check 10 random captions for accuracy
- [ ] **Trigger word present:** Every caption starts with the trigger word
- [ ] **File pairing:** Every image has a `.txt`, every `.txt` has an image

**Visual style cross-reference:**
Read `genre_packs/{genre}/visual_style.yaml` and verify the training data
matches the described aesthetic. If the visual_style says "Techniscope film grain"
but your training images are all clean digital, the LoRA will fight the prompts.

**Report format:**
```
## LoRA Training Assessment: {genre}

### Landscape ({count} images)
Sources: {breakdown}
Coverage: {location types represented}
Gaps: {what's missing}
Quality: {pass/fail with notes}

### Portrait ({count} images)
Sources: {breakdown}
Coverage: {character types represented}
Gaps: {what's missing}
Quality: {pass/fail with notes}

### Decision: READY / NEEDS WORK
{If needs work, specify exactly what to fix}
```

---

### Step 4: Train

**Goal:** Train LoRA(s) on Flux 1 Dev via Draw Things CLI.

**Prerequisites:**
- Draw Things installed: `/opt/homebrew/bin/draw-things-cli`
- Flux 1 Dev model: `flux_1_dev_q8p.ckpt` (in Draw Things models dir)
- OQ-1: M3 Max 128GB — use `speed` mode, 768 resolution, rank 32

**Training command (M3 Max 128GB):**
```bash
draw-things-cli train lora \
  --model flux_1_dev_q8p.ckpt \
  --dataset ./sidequest-content/{genre}-stills \
  --output {trigger_word} \
  --name "{Genre} Style" \
  --steps 1000 --rank 32 --learning-rate 1e-4 \
  --use-aspect-ratio --caption-dropout 0.1 \
  --save-every 500 --noise-offset 0.1 \
  --memory-saver speed \
  --resolution 768 \
  --gradient-accumulation 4
```

Log training to `/tmp/{genre}_train.log` via `2>&1 | tee /tmp/{genre}_train.log`.

**Checkpoints:** Saved every 500 steps. If training diverges, roll back to last
good checkpoint and reduce learning rate.

**Output:** LoRA files land in Draw Things models directory.

**Hardware notes:**
- M3 Max 128GB: `--memory-saver speed`, `--resolution 768`, `--rank 32`
- M-series 16-32GB: `--memory-saver balanced`, `--resolution 512`, `--rank 16`

---

### Step 5: Test

**Goal:** Generate POI images using the new LoRA and verify quality.

**Test targets:** Read `genre_packs/{genre}/worlds/*/cartography.yaml` and select
6-8 diverse locations covering different terrain types.

**Generation:**
```bash
# Using the daemon's Flux renderer (if LoRA loading supported)
python3 scripts/generate_poi_images.py --genre {genre} --world {world} --steps 20

# Or via Draw Things CLI directly
draw-things-cli generate \
  --model flux_1_dev_q8p.ckpt \
  --lora {genre}_landscape \
  --prompt "{trigger_word}, {visual_style positive_suffix}, {location description}" \
  --negative "{visual_style negative_prompt}" \
  --width 1344 --height 768 \
  --steps 20 --guidance 3.5 \
  --seed 1966 \
  --output test_poi_{location}.png
```

**Evaluation criteria:**
- [ ] **Genre truth:** Does it look like it belongs in this genre?
- [ ] **No anachronisms:** No modern elements bleeding through
- [ ] **Style consistency:** All outputs share a coherent visual language
- [ ] **Location differentiation:** Desert looks different from canyon looks different from town
- [ ] **Prompt responsiveness:** Changing the prompt meaningfully changes the output
- [ ] **LoRA strength:** Style is present but not overwhelming (faces aren't melting, etc.)

**If LoRA is too weak:** Increase steps (try 2000) or increase rank (try 32).
**If LoRA is too strong:** Reduce LoRA weight at inference time (0.7-0.8 instead of 1.0).

**Final output:** Place approved POI images in `genre_packs/{genre}/images/poi/`.

---

## Reference

| Item | Location |
|------|----------|
| Existing LoRA ADR | `docs/adr/032-genre-lora-style-training.md` |
| Visual style configs | `genre_packs/{genre}/visual_style.yaml` |
| World visual overrides | `genre_packs/{genre}/worlds/{world}/visual_style.yaml` |
| POI generation script | `scripts/generate_poi_images.py` |
| Draw Things CLI | `/opt/homebrew/bin/draw-things-cli` |
| Models directory | `~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models/` |
| yt-dlp | `~/.local/bin/yt-dlp` |
| Ukiyo-e reference | `sidequest-content/ukiyo-e-landscape/` (tagged, trained) |

## Completed LoRAs

Track trained LoRAs here as they're completed:

| Genre | Type | Status | Trigger Word | Steps | Notes |
|-------|------|--------|--------------|-------|-------|
| elemental_harmony | landscape | trained | `ukiyo_e_landscape` | 1500 | Strong results on burning_peace POIs |
| elemental_harmony | portrait | queued | `ukiyo_e_portrait` | — | Dataset tagged, not yet trained |
| spaghetti_western | unified | trained | `leone_style` | 1000 | Rank 32, 768px, M3 Max speed mode. Excellent on dust_and_lead POIs |
| victoria | unified | dataset ready | `victorian_painting` | — | 331 images: Sargent + Grimshaw + Constable, text cards cropped |
| caverns_and_claudes | portraits | in progress | `dnd_ink` | — | SDXL→Flux distillation pipeline. img2img from B&W converted portraits |
