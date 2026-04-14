# LoRA Reference — World Visual Identity Map

> Status: Research / spitballing (2026-04-03)
> See also: ADR-032 (genre LoRA style training), ADR-034 (portrait identity)

## Architecture Decision

**Flux.1 D is the sole runtime model.** T5-XXL's 512-token prompt comprehension
is non-negotiable — players see images alongside narrator text, and any mismatch
("what is that?") breaks immersion. CLIP's 77-token limit causes subject
infidelity that is immediately visible during gameplay.

**SDXL / Z-Image Turbo is an offline authoring tool only:**
- Generating LoRA training corpuses (ADR-032 pipeline)
- Batch POI landscape art during world authoring
- Style exploration and A/B testing
- Never in the daemon's runtime path

**LoRA strategy (three sources, in preference order):**
1. Community Flux LoRAs — pre-made, free, immediate
2. Custom-trained Flux LoRAs via SDXL corpus — ADR-032 pipeline, ~30 min per
   world on M3 Max, full art direction control
3. Prompt-only styling — for worlds where no LoRA exists yet, fall back to
   current positive_suffix approach

### Why not SDXL at runtime?

We used SDXL previously and couldn't get subjects right. The 77-token CLIP
limit truncates scene descriptions — the model improvises the rest and produces
images that don't match the narrative. Players consistently noticed ("what is
that?"). Even POI landscapes need to match the specific location the player
arrived at, not just "a pretty scene in the right genre."

Flux defaults to photorealism, which we fight with negative prompts
(see `prompt_composer.py` line 37, commit `b114c67`). LoRAs solve this by
carrying style in the weights, freeing both the prompt budget AND eliminating
the anti-photorealism negative prompt arms race.

## Design Principle

LoRAs map at the **world level**, not genre level. Genre is mechanics, world is
flavor. The LoRA carries visual identity — pure flavor. Two worlds in the same
genre can look completely different.

```
genre_packs/{genre}/
├── visual_style.yaml                    # negative_prompt, base_seed, tag_overrides
└── worlds/{world}/
    └── visual_style.yaml                # lora, lora_trigger (world's visual voice)
```

## Memory Footprint (M3 Max 128 GB unified)

- Flux.1 Dev base: ~24 GB
- IP-Adapter (ADR-034): ~2 GB
- VAE: ~300 MB
- Each LoRA: 18–302 MB (only one loaded at a time)
- **Total: ~27 GB resident.** 101 GB headroom.
- LoRA swap: ~1-2s (once per session, world doesn't change mid-game)

## World → LoRA Map

All Flux.1 D base. One LoRA loaded per session.

| World | Genre | LoRA | Trigger | CivitAI | Notes |
|-------|-------|------|---------|---------|-------|
| annees_folles | pulp_noir | Art Deco Style | (check page) | [1030487](https://civitai.com/models/1030487) | 1920s Paris, jazz age geometry, jewel tones |
| the_circuit | road_warrior | Kodachrome Realism | `kdchrm` | [1318345](https://civitai.com/models/1318345/kodachrome-realism) | 70s-80s analog film, real Kodachrome slides corpus. 302 MB |
| pinwheel_coast | low_fantasy | Dreamlike Watercolour | `watercolour` | [857048](https://civitai.com/models/857048) | Waterlogged failed grandeur, comedic-tragic softness |
| shattered_reach | low_fantasy | Classic Painting Z* | `class1cpa1nt` | [2187645](https://civitai.com/models/2187645/classic-painting-z) | *Needs Flux equivalent — train via ADR-032 or find Flux oil painting LoRA |
| flickering_reach | mutant_wasteland | Beksiński | (check page) | [874231](https://civitai.com/models/874231/style-of-zdzislaw-beksinski) | Surreal post-apocalyptic horror, bone cathedrals |
| franchise_nations | neon_dystopia | Retro Future Dystopia | `RetroFutureDystopia` | [886913](https://civitai.com/models/886913) | Corporate beige dystopia, muted palettes. Or skip — Flux default may BE the aesthetic |
| aureate_span | space_opera | Baroque Space Opera | `Sci-Fi Baroque Couture Pulp` | [1778358](https://civitai.com/models/1778358/baroque-space-opera) | Boucher + Chris Foss + Mugler. Gilded rococo in space |
| coyote_reach | space_opera | Retro Ad Flux | `m1dc3ntury` | [827395](https://civitai.com/models/827395/retro-ad-flux) | 50s pulp frontier, retro-futurist mining outpost |
| dust_and_lead | spaghetti_western | Kodachrome Realism | `kdchrm` | [1318345](https://civitai.com/models/1318345/kodachrome-realism) | Leone Technicolor. Same LoRA as the_circuit, prompting diverges |
| blackthorn_moor | victoria | Victorian Gothic Horror | `vicgoth` | [785197](https://civitai.com/models/785197/victorian-gothic-horror) | Sepia-toned, fog, decaying mansions. 1k downloads, 121 positive reviews |
| mawdeep | caverns_and_claudes | Retro Dark Fantasy | `dndllstr` | [1763256](https://civitai.com/models/1763256/retro-dark-fantasy) | Crosshatched dungeon ink (lineart mode). Painting mode: `dndpntng` |
| burning_peace | elemental_harmony | Ukiyo-e / Hokusai | `Ukiyo-e style by Katsushika Hokusai` | [1078711](https://civitai.com/models/1078711/flux-ukiyo-e-by-katushika-hokusai) | Edo-period woodblock, scanned originals. Strength 0.6 |
| shattered_accord | elemental_harmony | Oriental Fantasy Illustration | `Oriental fantasy illustration` | [1637612](https://civitai.com/models/1637612/fantasy-illustration) | Surreal dreamlike, glowing brushstrokes, digital watercolor |

## Renderartist LoRAs (original research set)

Keith's initial finds from the `renderartist` creator. All use leetspeak triggers.
Z-Image ones kept for offline authoring / SDXL corpus generation.

| LoRA | Trigger | Base | CivitAI |
|------|---------|------|---------|
| Retro Ad Flux | `m1dc3ntury` | Flux.1 D | [827395](https://civitai.com/models/827395/retro-ad-flux) |
| Technically Color Z | `t3chnic4lly` | Z-Image Turbo | [2174416](https://civitai.com/models/2174416/technically-color-z) |
| Classic Painting Z | `class1cpa1nt` | Z-Image Turbo | [2187645](https://civitai.com/models/2187645/classic-painting-z) |
| Midcentury Dream Qwen | `m1dc3ntury` | Qwen | [2168950](https://civitai.com/models/2168950/midcentury-dream-qwen) |
| Inked Z | `1nk3d` | Z-Image Turbo | [2178280](https://civitai.com/models/2178280/inked-z) |
| Sketch Paint Flux | `sk3tchpa1nt` | Flux.1 D | [851965](https://civitai.com/models/851965/sketch-paint-flux) |

## Supplementary LoRAs (not mapped but worth knowing)

| LoRA | Trigger | Base | CivitAI | Use case |
|------|---------|------|---------|----------|
| Moebius Ligne Claire | `cartoon moebius illustration in mb artstyle` | Flux | [1080092](https://civitai.com/models/1080092) | Alt for space_opera or neon_dystopia worlds |
| Neon Cyberpunk Impressionism | `mad-cybrpnkimprss painting` | Flux | [361379](https://civitai.com/models/361379) | Alt for neon_dystopia worlds |
| Biomechanical H.R. Giger | `biomechanical style` | Flux | [695383](https://civitai.com/models/695383/biomechanical-hrgiger) | Layer with mawdeep for organic horror |
| Comic Book (Adel_AI) | `Zylagidam art style` | Z-Image Turbo | [830230](https://civitai.com/models/830230/comic-book) | 22k downloads. Offline authoring only — strong comic book aesthetic |
| Sumi-E Ink Wash | `in a faded smudged brush strokes calligraphy ink style` | Flux | [688690](https://civitai.com/models/688690) | Alt for burning_peace |
| Historic Ukiyo-e | `ukiyoe` | Flux | [933366](https://civitai.com/models/933366) | Alt Edo woodblock, scanned originals |
| Vintage DnD Style | `Vintage Dungeons and Dragons` | Flux | [1758499](https://civitai.com/models/1758499/vintage-dnd-style-flux) | Alt for mawdeep, more painterly |
| Adventurer's Codex | (none listed) | Flux | [1932828](https://civitai.com/models/1932828) | 80s D&D painterly covers |
| Dark Landscapes | (none listed) | Flux | [702293](https://civitai.com/models/702293) | Gothic atmosphere, brooding moors |

## ADR-032 Custom Training Pipeline (offline)

For worlds where no community Flux LoRA fits, train a custom one:

1. Use SDXL/Z-Image + style LoRA to generate 30-50 image corpus
2. Caption with BLIP-2 (content only, not style)
3. Train Flux LoRA on corpus (~30 min on M3 Max)
4. Art direction loop until it looks right

The Z-Image LoRAs above (Technically Color, Classic Painting, Inked, Comic Book)
are excellent corpus generators — they produce the style you want, then you bake
that style into Flux weights.

**Priority candidates for custom training:**
- shattered_reach — needs gritty oil painting, Classic Painting Z generates the corpus
- dust_and_lead — if Kodachrome Realism isn't Leone enough, use Technically Color Z corpus
- franchise_nations — if "no LoRA" doesn't work, generate sterile corporate imagery with SDXL

## Gaps & TODO

- [ ] **shattered_reach** — no Flux oil painting LoRA. Train custom via Classic Painting Z corpus.
- [ ] **Spaghetti western** — no dedicated LoRA exists. Kodachrome Realism is best proxy.
      Custom train from Leone film stills if needed.
- [ ] **franchise_nations** — test with no LoRA first. Flux's sterile default may be the aesthetic.
- [ ] **A/B test all picks** before committing to visual_style.yaml.
- [ ] Evaluate Moebius as genre-level default for space_opera with Baroque/Retro Ad as
      world overrides vs. purely world-level mapping.
- [ ] Download and test top candidates on M3 Max with representative prompts per world.
