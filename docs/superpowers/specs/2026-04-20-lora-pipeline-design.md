# LoRA Training-to-Runtime Pipeline Design

**Date:** 2026-04-20
**Status:** Design — awaiting implementation plan
**Author:** Keith (via GM brainstorm)
**Related:** ADR-032 (genre LoRA style training), ADR-070 (MLX image renderer)

---

## Goal

Establish a repeatable pipeline for training style LoRAs for SideQuest worlds on Apple Silicon, producing artifacts that mflux (the MLX-backed image-gen library inside `sidequest-daemon`) actually applies at runtime — with automated verification that catches the silent-fallback failure mode we just hit.

## Context

### The problem we hit

On 2026-04-20, attempting to render POIs for the `spaghetti_western/dust_and_lead` world with the `leone_style_1000_lora_f32.ckpt` LoRA trained in Draw Things, we discovered:

1. mflux loads the `.ckpt` without raising an error.
2. The render completes successfully.
3. **The output is byte-identical at the pixel level to running with no LoRA at all.**

Draw Things exports LoRAs in a custom s4nnc format. mflux's `Flux1(lora_paths=[...])` accepts the file, silently matches zero keys from its internal target list, and applies zero-weight adapters — i.e., a no-op. The render claims "LoRA applied" while actually applying nothing. This violates the project's "no silent fallbacks" rule at the subsystem boundary.

A second candidate LoRA (`spaghetti_western_sq_1500_lora_f32.safetensors`, Kohya naming) failed differently — a matmul shape error on the fused QKV layer (rank 96 where mflux expected rank 32). That file is ai-toolkit-style fused-QKV; mflux doesn't handle the fusion.

Net: we have no working style LoRA for the `spaghetti_western` genre, and no guardrail that would have caught the first failure mode automatically.

### Scope of this design

Full pipeline — train → convert → verify → ship → load — for ongoing use by all worlds, with a verification gate that makes silent-fallback detectable at both training time and render time. Approach chosen: **top-down rollout** (prove the end-to-end stack with one LoRA first, formalize the gate and multi-LoRA infrastructure after).

---

## Decisions Summary

| Area | Decision |
|---|---|
| Scope | Full pipeline (not one-off for this render batch) |
| Granularity | Hybrid — genre-level base LoRAs + optional world-level additions, stacked at render time |
| Training tool | `mlx-examples/flux/` LoRA training (MLX-native on M3 Max) |
| Training output | `.npz` in MLX-specific key naming → must be remapped |
| Remapper | Custom `scripts/lora/remap_mlx_to_mflux.py` + versioned `mlx_to_mflux_keymap.yaml`, produces Kohya-convention `.safetensors` |
| Runtime loader | mflux via `sidequest-daemon`'s `flux_mlx_worker.py` |
| Tier routing | Single LoRA stack, each entry has `applies_to: [tier, ...]` filter |
| Inheritance | World visual_style.yaml **extends** genre by default, with `loras.exclude: [name]` to drop inherited entries and `loras.add: [...]` to append |
| Dataset scope | **Replacement** per LoRA — each LoRA trains on exactly one dataset dir (not concatenated genre+world) |
| Verification | (a) training-time key-match gate, (b) SSIM pixel-diff gate, (c) trigger-word discrimination, (d) runtime OTEL `render.lora` span with per-file `matched_key_count` |
| Rollout | Top-down: prove stack end-to-end with one LoRA before scaffolding; no second LoRA ships until automated gate is live |

---

## Architecture

Five subsystems with strict boundaries:

1. **Training source** (`sidequest-content/lora-datasets/...`) — curated images + paired captions.
2. **Trainer** (`scripts/lora/train.py`) — thin wrapper around `mlx-examples/flux/` Flux LoRA training.
3. **Key remapper** (`scripts/lora/remap_mlx_to_mflux.py`) — translates MLX-native `.npz` → Kohya-convention `.safetensors`.
4. **Verification gate** (`scripts/lora/verify.py`) — automated checks (key-match, SSIM, trigger discrimination) + human sign-off before a LoRA is promoted to shipped state.
5. **Runtime** — `sidequest-daemon` mflux worker composes the LoRA stack from genre + world visual_style.yaml, filters by tier, and emits OTEL spans proving engagement.

```
sidequest-content/lora-datasets/{genre}/{kind}/
        │
        ▼
scripts/lora/train.py  ──►  .npz (MLX native keys)
        │
        ▼
scripts/lora/remap_mlx_to_mflux.py  ──►  .safetensors (Kohya keys, mflux-compatible)
        │
        ▼
scripts/lora/verify.py  ──►  SSIM + trigger + match-count checks
        │
        ▼ (on human sign-off)
sidequest-content/lora/{genre}/{name}.safetensors  +  update {genre}.yaml manifest
        │
        ▼
sidequest-daemon (flux_mlx_worker) composes stack from visual_style.yaml + emits OTEL
        │
        ▼
rendered image, GM panel shows "LoRAs engaged: N (matched X keys)"
```

---

## Dataset Layout

```
sidequest-content/lora-datasets/
├── spaghetti_western/
│   ├── landscape/                       # genre-wide landscape LoRA dataset
│   │   ├── frame_0001.jpg
│   │   ├── frame_0001.txt               # paired caption
│   │   └── ...
│   ├── portrait/                        # genre-wide portrait LoRA dataset
│   └── worlds/
│       ├── dust_and_lead/               # only if world needs divergent flavor
│       │   ├── landscape/
│       │   └── portrait/
│       └── the_real_mccoy/
│           ├── landscape/               # 1878 Pittsburgh industrial
│           └── portrait/                # Gilded Age studio photography
```

Conventions:
- **Paired files:** every `{name}.jpg` has a matching `{name}.txt`. Assessment gate verifies 1:1 before training.
- **Caption format:** `{trigger_word}, {style_tags}, {subject_tags}`
- **Trigger word:** `{genre}_{kind}` for genre-level, `{world}_{kind}` for world-level (e.g., `spaghetti_western_landscape`, `the_real_mccoy_portrait`)
- **Volume:** 150–200 images per dataset; below 150 is a hard block at the assessment gate.
- **Storage:** images tracked via Git LFS; `.txt` captions are plain text in Git.
- **Scope:** one LoRA trains on one dataset dir, no concatenation. World LoRAs train only on world-specific images and stack on top of genre LoRAs at render time (layered LoRA composition).

---

## Training Invocation

**Wrapper command** — `scripts/lora/train.py`:

```bash
scripts/lora/train.py \
  --dataset sidequest-content/lora-datasets/spaghetti_western/landscape \
  --output  sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape \
  --trigger spaghetti_western_landscape \
  --kind    landscape \
  --steps   1500 \
  --rank    32 \
  --learning-rate 1e-4 \
  --resolution 768 \
  --caption-dropout 0.1 \
  --save-every 500
```

Responsibilities:
1. Pre-flight: dataset exists, paired files present, volume ≥ 150. Hard fail otherwise.
2. Spawn `mlx-examples/flux/` Flux LoRA training with the above params. Exact script path (e.g., `flux/dreambooth.py`) pinned in implementation plan.
3. Log command line + all args to `/tmp/{trigger}_train.log`; tee to stdout.
4. On completion, produces `{output_stem}_500.npz`, `{output_stem}_1000.npz`, `{output_stem}_1500.npz` in `archive/`.

No resume-from-checkpoint in v1; each run is fresh. Add that later if real training workflows need it.

## Key Remapper

**Command** — `scripts/lora/remap_mlx_to_mflux.py`:

```bash
scripts/lora/remap_mlx_to_mflux.py \
  --input  sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_1500.npz \
  --output sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_1500.safetensors \
  --keymap scripts/lora/mlx_to_mflux_keymap.yaml
```

Responsibilities:
1. Load `.npz`; enumerate every MLX-convention key.
2. Translate each key via the `keymap` YAML to a Kohya-convention name mflux recognizes (e.g., `lora_unet_double_blocks_{N}_img_attn_proj.lora_{up,down}.weight`).
3. Handle rank + transpose differences between MLX and Kohya layouts — every dimension transformation is explicit in the keymap.
4. **Hard-fail on any source key without a target pattern.** Print the unknown keys; require the keymap to be extended before proceeding. Zero silent drops.
5. Write `.safetensors` via `safetensors.torch.save_file`.
6. Print summary: `N keys translated, rank R, output size MB`.

The `keymap` YAML is the versioned interface between mlx-examples and mflux. When either project changes their key conventions, the diff is a YAML edit in one file, not a code rewrite.

---

## LoRA Storage Layout

```
sidequest-content/lora/
├── {genre}/                             # flat per-genre directory
│   ├── {genre}_landscape.safetensors    # shipped (mflux-ready)
│   ├── {genre}_portrait.safetensors
│   ├── {world}_landscape.safetensors    # world LoRAs, flat in genre dir
│   ├── {world}_portrait.safetensors
│   ├── archive/                         # intermediate checkpoints, verification artifacts
│   │   ├── {name}_500.npz
│   │   ├── {name}_1000.npz
│   │   ├── {name}_1500.npz
│   │   ├── {name}_1500.safetensors      # also kept here for reproducibility
│   │   ├── verify-{name}-{timestamp}.md # verification report
│   │   └── legacy/                      # old broken LoRAs kept as regression cases
│   │       ├── leone_style_1000_lora_f32.ckpt
│   │       └── spaghetti_western_sq_1500_lora_f32.safetensors
│   └── {genre}.yaml                     # per-genre LoRA manifest
```

### Per-genre manifest — `{genre}.yaml`

Written by `verify.py` on passing verification; consulted by the daemon on startup to log what's known-good:

```yaml
loras:
  - name: spaghetti_western_landscape
    file: spaghetti_western_landscape.safetensors
    kind: landscape
    trigger: spaghetti_western_landscape
    trained_at: 2026-04-21T03:00:00Z
    trained_steps: 1500
    trained_on: sidequest-content/lora-datasets/spaghetti_western/landscape
    dataset_image_count: 187
    verification:
      ssim_vs_baseline: 0.923
      trigger_discriminates: true
      mflux_matched_keys: 456
      pixel_diff_mean: 14.7
```

All binary files in `{genre}/` and `{genre}/archive/` tracked via Git LFS.

---

## visual_style.yaml Multi-LoRA Schema

Replaces the flat `lora:` / `lora_scale:` pair.

### Genre level

```yaml
# genre_packs/spaghetti_western/visual_style.yaml
loras:
  - name: spaghetti_western_landscape
    file: lora/spaghetti_western/spaghetti_western_landscape.safetensors
    scale: 0.8
    applies_to: [landscape, scene]
    trigger: spaghetti_western_landscape
  - name: spaghetti_western_portrait
    file: lora/spaghetti_western/spaghetti_western_portrait.safetensors
    scale: 0.8
    applies_to: [portrait]
    trigger: spaghetti_western_portrait
```

### World level (common case — inherits)

```yaml
# genre_packs/spaghetti_western/worlds/dust_and_lead/visual_style.yaml
# No loras: block — inherits the two genre LoRAs as-is.
```

### World level (divergent — excludes + adds)

```yaml
# genre_packs/spaghetti_western/worlds/the_real_mccoy/visual_style.yaml
loras:
  exclude:
    - spaghetti_western_landscape     # Almería desert fights 1878 Pittsburgh
    - spaghetti_western_portrait
  add:
    - name: the_real_mccoy_landscape
      file: lora/spaghetti_western/the_real_mccoy_landscape.safetensors
      scale: 0.85
      applies_to: [landscape, scene]
      trigger: the_real_mccoy_landscape
    - name: the_real_mccoy_portrait
      file: lora/spaghetti_western/the_real_mccoy_portrait.safetensors
      scale: 0.8
      applies_to: [portrait]
      trigger: the_real_mccoy_portrait
```

### Field contracts

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | yes | str | Unique within genre+worlds; referenced by `exclude:` |
| `file` | yes | str | Path relative to content repo root; hard fail if missing |
| `scale` | yes | float | `lora_scale` for mflux; no default |
| `applies_to` | yes | list[str] | Tier filter (`landscape`, `portrait`, `scene`, `tactical_map`, `text_overlay`, `encounter`); empty array = misconfiguration → hard fail |
| `trigger` | optional | str | If set, prepended to positive prompt when LoRA is active for the render |

### Schema validation (at visual_style.yaml load)

Daemon validates each world+genre pair once on session start, not per-render. A visual_style.yaml that fails any of these checks causes a loud failure before any rendering happens:

- Every `loras[].name` is unique within the merged (genre + world) set.
- `world.loras.add[].name` does not collide with any `genre.loras[].name` (use `exclude:` first).
- Every `file` path resolves to an existing file on disk.
- Every `applies_to` is a non-empty list.
- Every `scale` is a number (warn on `scale == 0`; it's allowed but wastes a pass).

### Resolution logic (daemon, per render)

1. Load genre visual_style.yaml's `loras:` → base list.
2. Apply world visual_style.yaml's `loras.exclude:` (drop by `name`).
3. Append world's `loras.add:`.
4. Filter remaining entries by `applies_to` containing current tier.
5. Pass `[file, scale]` tuples to mflux as `lora_paths[]`, `lora_scales[]`.
6. Prepend `trigger`s (deduped, in stack order) to positive prompt.
7. Emit OTEL `render.lora` span.

### Edge cases

- World's `add:` declares a `name` that already exists in the base list → hard fail (use `exclude:` first).
- `scale: 0` → allowed but `verify.py` warns (waste).
- Duplicate triggers in active stack → dedupe, log warning.

---

## Verification Gate

`scripts/lora/verify.py` — runs after training + remap, before a LoRA is promoted to the shipped `{genre}/` directory. Four checks; any failure blocks promotion.

### Check 1 — Key-match (static)

Load candidate `.safetensors` via `Flux1(lora_paths=[path], lora_scales=[1.0])`; count keys mflux's target patterns actually matched.

- **Fail** if `matched_keys == 0` (silent-fallback guaranteed).
- **Fail** if `matched_keys < 80%` of file keys (likely partial load — something structural is off).

### Check 2 — Pixel-diff SSIM (dynamic)

Render the same (canonical prompt, seed, tier, resolution) pair twice — once with LoRA at nominal scale, once without. Compute SSIM between the PNGs.

- **Fail if SSIM ≥ 0.999** — LoRA had no meaningful effect.
- Canonical prompts live at `scripts/lora/verify_prompts/{kind}.yaml`; deliberately generic (e.g., `"a street at noon"`) so any LoRA that targets the tier should visibly change the output.

### Check 3 — Trigger discrimination (semantic)

If the LoRA declares a `trigger`, render two more pairs:
- `{trigger}, a street at noon`
- `a random word, a street at noon`

Compute SSIM between these two.

- **Fail if SSIM ≥ 0.97** — trigger word isn't doing anything; trigger wasn't learned or dropout was too aggressive.
- Skipped if no trigger declared.

### Check 4 — Report + human sign-off

Writes `sidequest-content/lora/{genre}/archive/verify-{name}-{timestamp}.md`:
- All 4 test render PNGs embedded/linked.
- SSIM numbers + per-check pass/fail.
- `matched_key_count` + hash of matched-keys list.
- Dataset metadata (image count, training steps).

On all checks passing: prompts `promote this LoRA? [y/n]`. `y` → appends `verification:` block to `{genre}.yaml`, copies `.safetensors` from `archive/` to shipped location. `n` → report stays for analysis; nothing moves.

### SSIM thresholds

The 0.999 and 0.97 floors are **empirical seeds, not sacred numbers** — they are calibrated against the first real LoRA's output in Phase 3 of the migration. If a legitimately-subtle LoRA (e.g., scale 0.3) scores 0.995, loosen Check 2's floor. If trivial prompt variations score 0.98 without any LoRA involved, tighten Check 3's floor. The point of each check is catching its failure mode, not enforcing a specific number.

### Cost

~6 minutes total per verify run on M3 Max (4 renders × ~85s — matches empirically observed POI render times on 2026-04-20: 90.3s, 86.8s, 81.6s). Runs once per new LoRA, not on every commit.

---

## Runtime — Daemon Changes

Scoped tight. Three concrete changes to `sidequest-daemon`.

### Change 1 — Protocol: lists instead of singletons

`scripts/render_common.py` + daemon Unix-socket protocol:

```python
# BEFORE
params["lora_path"]  = "path/to/one.safetensors"
params["lora_scale"] = 0.8

# AFTER
params["lora_paths"]  = ["path/to/one.safetensors", "path/to/two.safetensors"]
params["lora_scales"] = [0.8, 0.65]
```

Old single-path path deleted outright. The daemon is a sidecar; nothing outside our repo speaks its protocol, no compat shim needed.

### Change 2 — `flux_mlx_worker.py`: multi-LoRA + match accounting

```python
def _build_lora_model(self, variant, lora_paths, lora_scales):
    model = Flux1(
        model_config=...,
        lora_paths=lora_paths,
        lora_scales=lora_scales,
    )
    matched_counts = _extract_matched_key_counts(model, lora_paths)
    return model, matched_counts
```

`matched_counts` aligned with `lora_paths`. Zero entries trigger:
- `log.error` at worker level.
- Span attribute on `render.lora` so GM panel highlights the render.
- Runtime does **not** refuse the render — production rendering should not hard-fail on degraded LoRA. It screams loudly and proceeds with what it has. Verification gate's job is to prevent bad LoRAs reaching production.

### Change 3 — `compose_lora_stack(genre_style, world_style, tier)`

Pure function; no I/O beyond the already-loaded visual_style dicts.

```python
def compose_lora_stack(genre_style, world_style, tier):
    base = list(genre_style.get("loras", []))
    world_loras = world_style.get("loras", {})
    excluded = set(world_loras.get("exclude", []))
    base = [l for l in base if l["name"] not in excluded]
    base.extend(world_loras.get("add", []))
    return [l for l in base if tier in l["applies_to"]]
```

Returns filtered list of LoRA entries. Caller extracts `file`, `scale`, `trigger` as needed.

### Change 4 — OTEL span: `render.lora`

Emitted per render:

```
span name: render.lora
attributes:
  render.lora.stack_size: 2
  render.lora.names:          ["spaghetti_western_landscape", "spaghetti_western_grain"]
  render.lora.files:          ["lora/...", "lora/..."]
  render.lora.scales:         [0.8, 0.35]
  render.lora.matched_keys:   [456, 220]
  render.lora.triggers:       ["spaghetti_western_landscape"]
  render.lora.tier_filter:    "landscape"
  render.lora.excluded:       []
status: if any matched_keys == 0 → error with message
```

GM panel surfaces "LoRAs engaged: N (matched X keys)" per render — visual proof of engagement at the dashboard level.

### What is NOT changing

Tier routing (exists), PromptComposer internals, CLIP budget logic, seed handling, output path conventions. Multi-LoRA widens two types (str → list, float → list) and adds one resolver. Minimal blast radius.

---

## Migration Plan

Top-down rollout (Approach 2). Each phase ends in a user-visible checkpoint before moving on.

### Phase 0 — Workshop setup

1. Clone `ml-explore/mlx-examples` to `~/Projects/mlx-examples/`; do not vendor into SideQuest repo.
2. Run stock `flux/` training script on its toy dataset to prove training runs on M3 Max.
3. Inspect the `.npz` output keys → seed the remapper's keymap YAML with real MLX naming.

**Checkpoint:** mlx-examples runs on this machine and its output key shape is documented.

### Phase 1 — Remapper (isolated development)

4. Write `scripts/lora/remap_mlx_to_mflux.py` + `scripts/lora/mlx_to_mflux_keymap.yaml`.
5. Translate the Phase 0 toy `.npz` to `.safetensors`.
6. Load into mflux; render one image at nominal scale.
7. Render without LoRA, pixel-diff. **SSIM must be < 0.999.** If not, remapper is broken — iterate.

**Checkpoint:** any mlx-examples-trained LoRA can be remapped and visibly applied in mflux.

### Phase 2 — First real training run (overnight)

8. Curate `spaghetti_western/landscape` dataset; pass existing `/sq-lora` Step 3 assessment gate.
9. Write `scripts/lora/train.py` wrapper.
10. Kick off overnight training.
11. Morning: `.npz` → `.safetensors` → render one test POI manually, eyeball.

**Checkpoint:** `spaghetti_western_landscape` trained, remapped, visibly applying to a POI render.

### Phase 3 — Gate formalization

12. Write `scripts/lora/verify.py` implementing Section 6's four checks.
13. Run against the Phase 2 LoRA retroactively to calibrate SSIM thresholds.
14. Commit the real observed numbers as the defaults with a comment noting they're empirical seeds.

**Checkpoint:** `verify.py` gates every future LoRA automatically; no second LoRA ships before this.

### Phase 4 — Daemon multi-LoRA

15. Protocol: `lora_path` → `lora_paths[]`.
16. `_build_lora_model` handles arrays + emits `matched_key_count`.
17. `compose_lora_stack(genre_style, world_style, tier)` resolver.
18. New OTEL `render.lora` span.
19. Schema migration: rewrite `dust_and_lead/visual_style.yaml` to `loras:` array. Replace `the_real_mccoy`'s prospective `lora_triggers:` block with real `loras.exclude:` (+ `add:` when world LoRAs arrive).
20. Re-render all 28 spaghetti_western POIs with LoRA actually applied + OTEL proving it.

**Checkpoint:** every render goes through the new pipeline; GM panel shows live LoRA engagement.

### Phase 5 — Skill update + second world

21. Update `/sq-lora` skill: remove Draw Things CLI; document trainer + remapper + verify flow.
22. Train `the_real_mccoy_landscape` (1878 Pittsburgh) + `the_real_mccoy_portrait` (Gilded Age). Validates `loras.exclude:` + `loras.add:` end-to-end.

**Checkpoint:** second genre/world LoRA ships without the author thinking about plumbing.

### Discipline

**Pre-commit: no second LoRA ships until Phase 3's gate is live.** That's the discipline that keeps Approach 2 from degrading into a one-off that leaves the silent-fallback trap intact for the next world.

---

## Out of Scope

- **SDXL, SD3, other model families.** Flux.1-dev only.
- **Character LoRAs** (specific people/creatures). This design handles *style* LoRAs; character LoRAs may need a different trigger/dropout scheme, addressed separately.
- **Runtime LoRA swap / hot-reload.** Daemon reloads visual_style.yaml on session start; live-swap during a session is not supported.
- **Cross-genre LoRA stacking.** A world in genre A cannot pull a LoRA from genre B. Hard constraint to keep the storage layout flat per-genre.
- **Non-MLX backends.** No fallback to CUDA, CPU, or other backends. M3 Max / MLX only.
- **Draw Things interop.** Existing Draw Things-trained `.ckpt` files are archived as legacy references; no effort to make them load.

## Open Questions / Risks

- **mlx-examples Flux LoRA training evolution.** The repo is active; its training script, output format, or key naming may change between when the keymap is written and when a new LoRA is trained. Mitigation: version the keymap, test it against every new LoRA on load, fail loudly on unknown keys.
- **SSIM threshold calibration against subtle LoRAs.** First-run thresholds are seeds. Calibration is part of Phase 3's deliverable, not a pre-commit concern.
- **mflux `matched_key_count` extraction.** This may require inspecting mflux internals (the LoRA target registry isn't a public API). Worst case: add a small patch via monkey-patch or a PR upstream. Verification gate has a fallback using the SSIM check alone if `matched_key_count` can't be extracted cleanly.
- **Training dataset authorship bandwidth.** The bottleneck on second and third genre LoRAs isn't pipeline infrastructure — it's the human curation step. This design doesn't speed that up; it just makes sure the curated output actually ships.

## References

- Perplexity research (2026-04-20): mlx-examples Flux LoRA training at `flux/`, produces MLX-specific `.npz`, not directly loadable by mflux without key remap.
- Earlier perplexity research (same session): Draw Things uses custom s4nnc format, no public converter, retrain on mflux-compatible tool is the canonical path.
- Empirical observation (same session): `leone_style_1000_lora_f32.ckpt` in mflux → 0 / 786,432 pixels differ vs. baseline. Silent-fallback confirmed.
- Existing `/sq-lora` skill at `.claude/commands/sq-lora.md` — Steps 1-3 (Research, Tag, Assess) retained; Step 4 (Draw Things CLI train) replaced by mlx-examples wrapper; Step 5 test retained and extended via verify.py.
- ADR-032 (genre LoRA style training) — this design operationalizes that ADR.
- ADR-070 (MLX image renderer) — the renderer this pipeline feeds.
