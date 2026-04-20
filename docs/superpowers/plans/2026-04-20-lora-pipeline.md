# LoRA Training-to-Runtime Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a training → remap → verify → runtime pipeline that takes curated image datasets and produces style LoRAs that mflux actually applies at render time, with automated verification against silent-fallback.

**Architecture:** `mlx-examples/flux/` trains LoRAs natively on M3 Max, emitting `.npz` with MLX key names. A custom remapper translates to Kohya-convention `.safetensors` that mflux loads directly. A 4-check verification gate (key-match + SSIM + trigger discrimination + human sign-off) blocks promotion of silent-fallback LoRAs. At runtime, the daemon composes LoRA stacks from genre + world visual_style.yaml (extend / exclude / add), filters by render tier, and emits OTEL spans with per-file `matched_key_count` as the runtime lie-detector.

**Tech Stack:** Python 3.14, `mlx`, `mflux`, `safetensors`, `numpy`, `PIL`, `pytest`, YAML. Runs on Apple Silicon (M3 Max). The daemon is Python inside `sidequest-daemon/` (uv-managed venv). Helper scripts live in `scripts/lora/` and use the orchestrator's top-level Python environment.

**Reference spec:** `docs/superpowers/specs/2026-04-20-lora-pipeline-design.md`

---

## Phase 0 — Workshop Setup

Goal: prove mlx-examples runs on this machine and capture the real key-name conventions before writing the remapper.

### Task 0.1: Clone mlx-examples outside the project

**Files:**
- Create: `~/Projects/mlx-examples/` (checkout location — do not vendor)

- [ ] **Step 1: Clone repo**

```bash
cd ~/Projects
git clone https://github.com/ml-explore/mlx-examples.git
cd mlx-examples
git log --oneline -1   # record the commit SHA in Task 0.4 notes
```

Expected: clean clone; repo present at `~/Projects/mlx-examples`.

- [ ] **Step 2: Install the flux subdirectory's deps**

```bash
cd ~/Projects/mlx-examples/flux
cat README.md | head -40
```

Read the README's "Training" section. Identify the exact training entrypoint (most likely `dreambooth.py` or `lora_training.py`) and the required `pip` deps. Install into a fresh venv:

```bash
python3 -m venv ~/.venv/mlx-flux-training
source ~/.venv/mlx-flux-training/bin/activate
pip install -r requirements.txt
```

Expected: install completes without errors. If the README points at a different entrypoint than expected, capture that name — Task 0.4 records it.

### Task 0.2: Download the toy dataset referenced by mlx-examples

**Files:** none in our repo

- [ ] **Step 1: Follow the README's linked training example**

Most mlx-examples Flux training examples link to a small public dataset (often 4-10 images of a single subject). Download it into `~/mlx-toy-dataset/`.

```bash
mkdir -p ~/mlx-toy-dataset
# Fetch per README instructions — exact commands vary by example version
ls ~/mlx-toy-dataset/
```

Expected: at least 4 `.jpg`/`.png` images + `.txt` or `metadata.jsonl` captions.

### Task 0.3: Run training to produce a real `.npz`

**Files:** output goes to `~/mlx-toy-lora/`

- [ ] **Step 1: Kick off minimal training run**

Use the smallest step count the example supports — we only need a syntactically valid `.npz`, not a good LoRA.

```bash
source ~/.venv/mlx-flux-training/bin/activate
cd ~/Projects/mlx-examples/flux
# Exact invocation varies; follow README. Example pattern:
python dreambooth.py \
  --model dev \
  --dataset ~/mlx-toy-dataset \
  --output ~/mlx-toy-lora \
  --iterations 100 \
  --rank 4 \
  --save-every 100 2>&1 | tee /tmp/mlx-toy-train.log
```

Expected: runs to completion (~5-15 min on M3 Max at 100 steps / rank 4). Produces `~/mlx-toy-lora/adapters.npz` (exact filename depends on script).

### Task 0.4: Document findings — this blocks Phase 1

**Files:**
- Create: `docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md`

- [ ] **Step 1: Write the findings doc**

Required contents:

```markdown
# mlx-examples Flux LoRA Training Notes

**Captured:** 2026-04-20
**Commit:** <SHA from Task 0.1>

## Training entrypoint

Exact script path: `mlx-examples/flux/<filename>.py`
Required arguments: <list observed required flags>
Output filename pattern: `<observed pattern>`

## Key-name convention in the output .npz

First 20 keys:
```
<paste output of: python -c "import numpy as np; f = np.load('~/mlx-toy-lora/adapters.npz'); [print(k) for k in list(f.keys())[:20]]">
```

Total keys: <N>
Sample tensor shapes:
- `<key_name>`: shape `<...>`
- `<key_name>`: shape `<...>`

## Observations

- <any quirks, e.g., "lora_down and lora_up are stored transposed relative to Kohya">
- <anything relevant for remapper implementation>
```

- [ ] **Step 2: Commit**

```bash
cd /Users/keithavery/Projects/oq-2
git add docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md
git commit -m "docs(lora): phase 0 — mlx-examples flux training notes"
```

**Phase 0 gate:** the notes doc must be complete and committed before Phase 1 begins. Phase 1 tasks reference this doc for the actual MLX key names.

---

## Phase 1 — Key Remapper

Goal: translate MLX `.npz` → Kohya-convention `.safetensors`, verified by loading into mflux and confirming pixel-difference vs. no-LoRA baseline.

### Task 1.1: Create `scripts/lora/` module skeleton

**Files:**
- Create: `scripts/lora/__init__.py`
- Create: `tests/lora/__init__.py`
- Create: `tests/lora/conftest.py`

- [ ] **Step 1: Create empty package markers**

```bash
cd /Users/keithavery/Projects/oq-2
mkdir -p scripts/lora tests/lora
touch scripts/lora/__init__.py tests/lora/__init__.py
```

- [ ] **Step 2: Write shared test fixtures**

Create `tests/lora/conftest.py`:

```python
"""Shared fixtures for LoRA pipeline tests."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def toy_npz_path(tmp_path: Path) -> Path:
    """Write a minimal synthetic .npz mimicking mlx-examples output keys.

    Keys match the pattern observed in Phase 0 notes. Shapes are tiny so
    tests run fast; structural equivalence to real output is what matters.
    """
    path = tmp_path / "toy_adapters.npz"
    data: dict[str, np.ndarray] = {
        # Fill in keys per docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md.
        # Pattern is something like:
        #   "transformer.double_blocks.0.img_attn.proj.lora_A": np.random.randn(4, 3072).astype(np.float32),
        #   "transformer.double_blocks.0.img_attn.proj.lora_B": np.random.randn(3072, 4).astype(np.float32),
        # Exact keys from the Phase 0 notes.
    }
    np.savez(path, **data)
    return path


@pytest.fixture
def sample_keymap_path(tmp_path: Path) -> Path:
    """Minimal keymap YAML covering the fixture's keys."""
    path = tmp_path / "keymap.yaml"
    path.write_text(
        "version: 1\n"
        "rules:\n"
        "  # One rule per MLX key pattern, mapping to Kohya target pattern.\n"
        "  # Filled from Phase 0 notes.\n"
    )
    return path
```

Note: the fixture content is intentionally skeletal because the real MLX key names come from Phase 0's notes. Phase 1 tasks fill them in using that doc.

- [ ] **Step 3: Commit**

```bash
git add scripts/lora tests/lora
git commit -m "chore(lora): scaffold scripts/lora package + test fixtures"
```

### Task 1.2: Keymap YAML — first version

**Files:**
- Create: `scripts/lora/mlx_to_mflux_keymap.yaml`

- [ ] **Step 1: Translate keys per Phase 0 notes**

Read `docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md` (Phase 0 output) and write `scripts/lora/mlx_to_mflux_keymap.yaml`:

```yaml
# Versioned mapping: MLX-examples Flux LoRA key names → Kohya convention
# (which mflux's flux_lora_mapping.py consumes natively).
#
# Update `version` when structural changes are made. The remapper stamps
# this version into the output .safetensors metadata so future debugging
# can identify which mapping produced a given file.

version: 1

# Each rule defines a regex pattern over MLX key names and how to
# rewrite the key for the Kohya convention. The regex must have named
# capture groups that the `kohya_pattern` template references.
#
# `transpose: true` means the tensor must be transposed on axes [0, 1]
# during remap (MLX and Kohya disagree on the direction of lora_up/down).
# Set only if Phase 0 observations confirm the shape difference.

rules:
  - name: img_attn_proj_down
    mlx_pattern: '^transformer\.double_blocks\.(?P<block>\d+)\.img_attn\.proj\.lora_A$'
    kohya_pattern: 'lora_unet_double_blocks_{block}_img_attn_proj.lora_down.weight'
    transpose: false   # confirm from Phase 0 shape inspection

  - name: img_attn_proj_up
    mlx_pattern: '^transformer\.double_blocks\.(?P<block>\d+)\.img_attn\.proj\.lora_B$'
    kohya_pattern: 'lora_unet_double_blocks_{block}_img_attn_proj.lora_up.weight'
    transpose: false

  # ... one rule per distinct MLX key pattern. See Phase 0 notes for the
  # full list of MLX keys observed in the toy training run.
```

Do not invent patterns that Phase 0 didn't observe — any missing patterns are a gap in the notes, not a remapper fix.

- [ ] **Step 2: Commit**

```bash
git add scripts/lora/mlx_to_mflux_keymap.yaml
git commit -m "feat(lora): initial mlx→mflux keymap from phase 0 observations"
```

### Task 1.3: Remapper — key translation, unknown-key hard fail

**Files:**
- Create: `scripts/lora/remap_mlx_to_mflux.py`
- Create: `tests/lora/test_remap.py`

- [ ] **Step 1: Write failing test — unknown keys hard fail**

```python
# tests/lora/test_remap.py
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scripts.lora.remap_mlx_to_mflux import RemapError, remap_npz_to_safetensors


def test_unknown_mlx_key_hard_fails(tmp_path: Path, sample_keymap_path: Path) -> None:
    npz_path = tmp_path / "has_unknown.npz"
    np.savez(
        npz_path,
        **{
            "completely.unknown.key.lora_A": np.zeros((4, 32), dtype=np.float32),
        },
    )
    out_path = tmp_path / "out.safetensors"

    with pytest.raises(RemapError) as exc_info:
        remap_npz_to_safetensors(
            input_path=npz_path,
            output_path=out_path,
            keymap_path=sample_keymap_path,
        )

    assert "completely.unknown.key.lora_A" in str(exc_info.value)
    assert not out_path.exists(), "must not write partial output on failure"
```

- [ ] **Step 2: Run test — expect import failure**

```bash
cd /Users/keithavery/Projects/oq-2
pytest tests/lora/test_remap.py::test_unknown_mlx_key_hard_fails -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.lora.remap_mlx_to_mflux'`.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/lora/remap_mlx_to_mflux.py
"""Translate mlx-examples Flux LoRA .npz → Kohya-convention .safetensors.

The output is consumable by mflux's Flux1(lora_paths=[...]) without
further conversion. Hard-fails on any source key without a keymap rule
(no silent drops).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml
from safetensors.torch import save_file


class RemapError(RuntimeError):
    """Raised when remapping cannot complete correctly."""


def _load_keymap(keymap_path: Path) -> list[dict[str, Any]]:
    with keymap_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    rules = data.get("rules") or []
    compiled = []
    for rule in rules:
        compiled.append(
            {
                "name": rule["name"],
                "mlx_re": re.compile(rule["mlx_pattern"]),
                "kohya_template": rule["kohya_pattern"],
                "transpose": bool(rule.get("transpose", False)),
            }
        )
    return compiled


def _match_rule(key: str, rules: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, str]] | None:
    for rule in rules:
        m = rule["mlx_re"].match(key)
        if m is not None:
            return rule, m.groupdict()
    return None


def remap_npz_to_safetensors(
    input_path: Path,
    output_path: Path,
    keymap_path: Path,
) -> dict[str, int]:
    """Remap MLX LoRA weights into mflux-compatible safetensors.

    Returns a summary dict with `translated` count and `rank` estimate.
    Raises RemapError on any unmapped MLX key.
    """
    rules = _load_keymap(keymap_path)
    npz = np.load(input_path)

    translated: dict[str, torch.Tensor] = {}
    unknown: list[str] = []

    for key in npz.files:
        matched = _match_rule(key, rules)
        if matched is None:
            unknown.append(key)
            continue
        rule, groups = matched
        new_key = rule["kohya_template"].format(**groups)
        tensor = torch.from_numpy(np.array(npz[key]))
        if rule["transpose"]:
            tensor = tensor.transpose(0, 1).contiguous()
        translated[new_key] = tensor

    if unknown:
        raise RemapError(
            "Unmapped MLX keys — extend scripts/lora/mlx_to_mflux_keymap.yaml:\n  "
            + "\n  ".join(unknown)
        )

    # Estimate LoRA rank from the first lora_down tensor's smaller axis.
    rank = 0
    for k, t in translated.items():
        if k.endswith("lora_down.weight"):
            rank = min(t.shape)
            break

    save_file(translated, str(output_path))
    return {"translated": len(translated), "rank": rank}


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--keymap", required=True, type=Path)
    args = parser.parse_args()

    summary = remap_npz_to_safetensors(args.input, args.output, args.keymap)
    print(f"Remap OK: {summary['translated']} keys translated, rank={summary['rank']}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/lora/test_remap.py::test_unknown_mlx_key_hard_fails -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/lora/remap_mlx_to_mflux.py tests/lora/test_remap.py
git commit -m "feat(lora): remapper hard-fails on unknown MLX keys"
```

### Task 1.4: Remapper — happy path + transpose handling

**Files:**
- Modify: `tests/lora/test_remap.py`
- Modify: `tests/lora/conftest.py` (fill in fixture with real keys from Phase 0)

- [ ] **Step 1: Fill in the toy fixture with real MLX key names**

Open `tests/lora/conftest.py` and replace the `toy_npz_path` fixture body with keys copied from Phase 0 notes. Use tiny shapes (rank 4, hidden dim 32 substituted for 3072) so tests run fast:

```python
# tests/lora/conftest.py — toy_npz_path fixture body
path = tmp_path / "toy_adapters.npz"
hidden = 32   # stand-in for Flux's 3072, scaled down for test speed
rank = 4
data: dict[str, np.ndarray] = {}
# Add one block worth of keys per the MLX pattern. Copy exact key names
# from Phase 0 notes — substitute `hidden` for 3072 and `rank` for the
# trained rank. Minimum: one lora_A + one lora_B pair for img_attn.proj.
data["transformer.double_blocks.0.img_attn.proj.lora_A"] = (
    np.random.randn(rank, hidden).astype(np.float32)
)
data["transformer.double_blocks.0.img_attn.proj.lora_B"] = (
    np.random.randn(hidden, rank).astype(np.float32)
)
np.savez(path, **data)
return path
```

Also update `sample_keymap_path` to match:

```python
# sample_keymap_path body
path.write_text(
    "version: 1\n"
    "rules:\n"
    "  - name: img_attn_proj_down\n"
    "    mlx_pattern: '^transformer\\.double_blocks\\.(?P<block>\\d+)\\.img_attn\\.proj\\.lora_A$'\n"
    "    kohya_pattern: 'lora_unet_double_blocks_{block}_img_attn_proj.lora_down.weight'\n"
    "    transpose: false\n"
    "  - name: img_attn_proj_up\n"
    "    mlx_pattern: '^transformer\\.double_blocks\\.(?P<block>\\d+)\\.img_attn\\.proj\\.lora_B$'\n"
    "    kohya_pattern: 'lora_unet_double_blocks_{block}_img_attn_proj.lora_up.weight'\n"
    "    transpose: false\n"
)
return path
```

- [ ] **Step 2: Write failing test — happy path**

Append to `tests/lora/test_remap.py`:

```python
from safetensors import safe_open


def test_happy_path_translates_known_keys(tmp_path: Path, toy_npz_path: Path, sample_keymap_path: Path) -> None:
    out_path = tmp_path / "out.safetensors"

    summary = remap_npz_to_safetensors(
        input_path=toy_npz_path,
        output_path=out_path,
        keymap_path=sample_keymap_path,
    )

    assert summary["translated"] == 2
    assert summary["rank"] == 4
    assert out_path.exists()

    with safe_open(str(out_path), framework="pt") as f:
        keys = sorted(f.keys())

    assert keys == [
        "lora_unet_double_blocks_0_img_attn_proj.lora_down.weight",
        "lora_unet_double_blocks_0_img_attn_proj.lora_up.weight",
    ]
```

- [ ] **Step 3: Run — expect pass (code already exists)**

```bash
pytest tests/lora/test_remap.py -v
```

Expected: both tests pass.

- [ ] **Step 4: Write failing test — transpose**

```python
def test_transpose_flips_axes(tmp_path: Path) -> None:
    npz_path = tmp_path / "transposable.npz"
    np.savez(
        npz_path,
        **{"transformer.double_blocks.0.img_attn.proj.lora_A": np.arange(12).reshape(3, 4).astype(np.float32)},
    )
    keymap = tmp_path / "km.yaml"
    keymap.write_text(
        "version: 1\n"
        "rules:\n"
        "  - name: r\n"
        "    mlx_pattern: '^transformer\\.double_blocks\\.(?P<block>\\d+)\\.img_attn\\.proj\\.lora_A$'\n"
        "    kohya_pattern: 'lora_unet_double_blocks_{block}_img_attn_proj.lora_down.weight'\n"
        "    transpose: true\n"
    )
    out_path = tmp_path / "out.safetensors"
    remap_npz_to_safetensors(npz_path, out_path, keymap)

    with safe_open(str(out_path), framework="pt") as f:
        t = f.get_tensor("lora_unet_double_blocks_0_img_attn_proj.lora_down.weight")

    assert tuple(t.shape) == (4, 3)   # transposed from (3, 4)
```

- [ ] **Step 5: Run — expect pass (transpose branch already in impl)**

```bash
pytest tests/lora/test_remap.py -v
```

Expected: three tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/lora/conftest.py tests/lora/test_remap.py
git commit -m "test(lora): remapper happy path + transpose verified"
```

### Task 1.5: End-to-end remapper proof — toy LoRA renders differently

**Files:**
- Create: `tests/lora/test_remap_roundtrip.py`

- [ ] **Step 1: Write the integration test**

This test is slow (~3 min total) and requires the daemon to be running. Mark it so it can be skipped in fast CI.

```python
# tests/lora/test_remap_roundtrip.py
"""End-to-end: remap the Phase 0 toy .npz, load into mflux, verify pixel diff."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

pytestmark = pytest.mark.slow


TOY_NPZ = Path.home() / "mlx-toy-lora" / "adapters.npz"   # from Phase 0


@pytest.mark.skipif(not TOY_NPZ.exists(), reason="Phase 0 toy .npz not produced")
def test_toy_lora_renders_different_from_baseline(tmp_path: Path) -> None:
    from scripts.lora.remap_mlx_to_mflux import remap_npz_to_safetensors

    safetensors_out = tmp_path / "toy.safetensors"
    remap_npz_to_safetensors(
        input_path=TOY_NPZ,
        output_path=safetensors_out,
        keymap_path=Path("scripts/lora/mlx_to_mflux_keymap.yaml"),
    )
    assert safetensors_out.stat().st_size > 0

    # Render with LoRA and without, compare. Requires daemon running at
    # /tmp/sidequest-renderer.sock — fail loudly if it is not.
    sock = Path("/tmp/sidequest-renderer.sock")
    assert sock.exists(), "start the daemon with `just daemon-run` before running this test"

    base_png = tmp_path / "baseline.png"
    lora_png = tmp_path / "with_lora.png"

    # Use the existing render_common helper directly rather than re-impl a client.
    import asyncio
    from scripts.render_common import send_render

    async def _render(lora_path: str | None, out: Path) -> None:
        params = dict(
            tier="landscape",
            positive="a stone courtyard at midday",
            clip="a stone courtyard at midday",
            negative="",
            seed=424242,
            steps=8,   # minimum useful; we need *difference*, not quality
        )
        if lora_path:
            params["lora_paths"] = [lora_path]     # NEW protocol; task 4.1 adds it
            params["lora_scales"] = [1.0]
        result = await send_render(**params)
        assert "error" not in result, result
        rendered = Path(result["result"]["image_url"] or result["result"]["image_path"])
        out.write_bytes(rendered.read_bytes())

    asyncio.run(_render(None, base_png))
    asyncio.run(_render(str(safetensors_out), lora_png))

    a = np.array(Image.open(base_png))
    b = np.array(Image.open(lora_png))
    assert a.shape == b.shape
    diff_frac = float((a != b).any(axis=-1).mean())
    assert diff_frac > 0.001, (
        f"remapped LoRA produced pixel-identical output ({diff_frac:.6f} differ). "
        f"This is the silent-fallback case the pipeline must detect."
    )
```

- [ ] **Step 2: Run it (daemon must be up)**

```bash
just daemon-run &   # if not already running
pytest tests/lora/test_remap_roundtrip.py -v -m slow
```

Expected: PASS. `diff_frac` should be substantially > 0.001 (usually > 0.3 for a trained toy LoRA).

If this FAILS: the remapper or keymap is wrong. Iterate on `mlx_to_mflux_keymap.yaml` until mflux sees a pixel-level effect. Common fixes:
- Add missing key rules (inspect `unknown` list in error messages)
- Flip `transpose` on a rule whose shapes don't match mflux's expectation
- Cross-reference `.venv/lib/python3.14/site-packages/mflux/models/flux/weights/flux_lora_mapping.py` for the exact Kohya target name expected

- [ ] **Step 3: Commit**

```bash
git add tests/lora/test_remap_roundtrip.py scripts/lora/mlx_to_mflux_keymap.yaml
git commit -m "test(lora): end-to-end remap proves mflux applies the LoRA"
```

**Phase 1 checkpoint:** `pytest tests/lora/ -v` passes. Any mlx-examples-trained LoRA can be remapped and will visibly affect mflux output.

---

## Phase 2 — First Real Training Run

Goal: produce `spaghetti_western_landscape.safetensors` from a curated dataset, remap it, render one test POI manually, eyeball.

### Task 2.1: Trainer wrapper — preflight + invocation

**Files:**
- Create: `scripts/lora/train.py`
- Create: `tests/lora/test_train.py`

- [ ] **Step 1: Write failing test — preflight rejects missing dataset**

```python
# tests/lora/test_train.py
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lora.train import PreflightError, preflight_dataset


def test_preflight_rejects_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(PreflightError, match="does not exist"):
        preflight_dataset(tmp_path / "missing")


def test_preflight_rejects_unpaired_files(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"fake-jpg")
    (tmp_path / "b.jpg").write_bytes(b"fake-jpg")
    (tmp_path / "a.txt").write_text("caption a")
    # b.txt deliberately missing
    with pytest.raises(PreflightError, match="unpaired"):
        preflight_dataset(tmp_path)


def test_preflight_rejects_low_volume(tmp_path: Path) -> None:
    # 10 pairs — well below 150
    for i in range(10):
        (tmp_path / f"{i}.jpg").write_bytes(b"fake")
        (tmp_path / f"{i}.txt").write_text(f"caption {i}")
    with pytest.raises(PreflightError, match="150"):
        preflight_dataset(tmp_path)


def test_preflight_passes_on_valid_dataset(tmp_path: Path) -> None:
    for i in range(150):
        (tmp_path / f"{i}.jpg").write_bytes(b"fake")
        (tmp_path / f"{i}.txt").write_text(f"caption {i}")
    # No raise
    preflight_dataset(tmp_path)
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/lora/test_train.py -v
```

- [ ] **Step 3: Minimal implementation**

```python
# scripts/lora/train.py
"""Wrapper around mlx-examples/flux/ LoRA training.

Handles preflight checks on the dataset, then shells out to the
upstream training script with pinned arguments. Training commands are
captured to a log for reproducibility.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


MIN_IMAGES = 150
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


class PreflightError(RuntimeError):
    """Raised when the dataset can't be used for training."""


def preflight_dataset(dataset_dir: Path) -> dict[str, int]:
    if not dataset_dir.exists() or not dataset_dir.is_dir():
        raise PreflightError(f"Dataset directory does not exist: {dataset_dir}")

    images = sorted(p for p in dataset_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    captions = {p.stem for p in dataset_dir.iterdir() if p.suffix.lower() == ".txt"}

    unpaired = [p.name for p in images if p.stem not in captions]
    if unpaired:
        raise PreflightError(
            f"Images without paired .txt captions (unpaired): {unpaired[:5]}"
            + (f" ... and {len(unpaired) - 5} more" if len(unpaired) > 5 else "")
        )

    if len(images) < MIN_IMAGES:
        raise PreflightError(
            f"Dataset has {len(images)} images; minimum {MIN_IMAGES} required. "
            f"See /sq-lora Step 3 assessment gate."
        )

    return {"images": len(images), "captions": len(captions)}


def build_training_command(
    dataset_dir: Path,
    output_stem: Path,
    steps: int,
    rank: int,
    lr: float,
    resolution: int,
    caption_dropout: float,
    save_every: int,
    mlx_examples_dir: Path,
    venv_python: Path,
) -> list[str]:
    """Return the command to exec. Exact entrypoint filename comes from Phase 0 notes."""
    train_script = mlx_examples_dir / "flux" / "dreambooth.py"   # confirm per Phase 0
    if not train_script.exists():
        raise PreflightError(
            f"mlx-examples flux training script not found at {train_script}. "
            f"Check docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md "
            f"for the actual filename from Phase 0."
        )
    return [
        str(venv_python),
        str(train_script),
        "--dataset", str(dataset_dir),
        "--output", str(output_stem),
        "--iterations", str(steps),
        "--rank", str(rank),
        "--learning-rate", str(lr),
        "--resolution", str(resolution),
        "--caption-dropout", str(caption_dropout),
        "--save-every", str(save_every),
    ]


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Output stem (no suffix)")
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--kind", required=True, choices=["landscape", "portrait", "scene"])
    parser.add_argument("--steps", type=int, default=1500)
    parser.add_argument("--rank", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--resolution", type=int, default=768)
    parser.add_argument("--caption-dropout", type=float, default=0.1)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument(
        "--mlx-examples-dir",
        type=Path,
        default=Path.home() / "Projects" / "mlx-examples",
    )
    parser.add_argument(
        "--venv-python",
        type=Path,
        default=Path.home() / ".venv" / "mlx-flux-training" / "bin" / "python",
    )
    args = parser.parse_args()

    summary = preflight_dataset(args.dataset)
    print(f"Preflight OK: {summary['images']} paired image/caption files.")

    cmd = build_training_command(
        dataset_dir=args.dataset,
        output_stem=args.output,
        steps=args.steps,
        rank=args.rank,
        lr=args.learning_rate,
        resolution=args.resolution,
        caption_dropout=args.caption_dropout,
        save_every=args.save_every,
        mlx_examples_dir=args.mlx_examples_dir,
        venv_python=args.venv_python,
    )

    log_path = Path("/tmp") / f"{args.trigger}_train.log"
    print(f"Training command: {shlex.join(cmd)}")
    print(f"Logging to: {log_path}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as logf:
        logf.write(f"# Training command:\n# {shlex.join(cmd)}\n\n")
        logf.flush()
        proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT, check=False)

    if proc.returncode != 0:
        print(f"Training failed (exit {proc.returncode}). See {log_path}.", file=sys.stderr)
        return proc.returncode

    print(f"Training complete. Outputs under {args.output.parent}.")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/lora/test_train.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/lora/train.py tests/lora/test_train.py
git commit -m "feat(lora): training wrapper with dataset preflight checks"
```

### Task 2.2: Curate `spaghetti_western/landscape/` dataset

**Files:**
- Create: `sidequest-content/lora-datasets/spaghetti_western/landscape/` (directory of images + captions)
- Modify: `sidequest-content/.gitattributes` (LFS tracking for new path)

- [ ] **Step 1: Ensure LFS tracks the new dataset path**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
cat .gitattributes   # check current rules
```

If the pattern `lora-datasets/**/*.jpg` is not yet present, append:

```bash
cat >> .gitattributes <<'EOF'
lora-datasets/**/*.jpg filter=lfs diff=lfs merge=lfs -text
lora-datasets/**/*.jpeg filter=lfs diff=lfs merge=lfs -text
lora-datasets/**/*.png filter=lfs diff=lfs merge=lfs -text
EOF
git add .gitattributes
git commit -m "chore(lora): LFS-track lora-datasets images"
```

- [ ] **Step 2: Populate the dataset**

Follow the existing `/sq-lora` skill Steps 1-3 (research / tag / assess) to collect ≥150 landscape-oriented stills from Leone/Almería film sources, with paired `.txt` captions using the trigger word `spaghetti_western_landscape`.

Target directory: `sidequest-content/lora-datasets/spaghetti_western/landscape/`

This is human work; no code. When done:

```bash
cd /Users/keithavery/Projects/oq-2
python3 -c "from scripts.lora.train import preflight_dataset; \
  print(preflight_dataset(__import__('pathlib').Path('sidequest-content/lora-datasets/spaghetti_western/landscape')))"
```

Expected: `{'images': <n>, 'captions': <n>}` with n ≥ 150.

- [ ] **Step 3: Commit the dataset**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
git add lora-datasets/spaghetti_western/landscape/
git commit -m "content(lora): spaghetti_western landscape training dataset"
```

### Task 2.3: Run training

**Files:** no repo changes this task — it's a long-running command whose output becomes the input for Task 2.4.

- [ ] **Step 1: Kick off overnight training**

```bash
cd /Users/keithavery/Projects/oq-2
python3 scripts/lora/train.py \
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

Expected overnight runtime; final artifacts at:
- `sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_500.npz`
- `..._1000.npz`
- `..._1500.npz`

### Task 2.4: Remap + manual render proof

**Files:** no repo changes; output is an inspection artifact.

- [ ] **Step 1: Remap the final step**

```bash
python3 scripts/lora/remap_mlx_to_mflux.py \
  --input  sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_1500.npz \
  --output sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_1500.safetensors \
  --keymap scripts/lora/mlx_to_mflux_keymap.yaml
```

Expected: `Remap OK: N keys translated, rank=32` with N > 0.

- [ ] **Step 2: Render one test POI manually**

Temporarily wire the new `.safetensors` into `dust_and_lead/visual_style.yaml` under the current single-LoRA schema (we haven't done the multi-LoRA protocol change yet — Phase 4 handles that):

```yaml
# sidequest-content/genre_packs/spaghetti_western/worlds/dust_and_lead/visual_style.yaml
# Temporary single-LoRA wiring for Phase 2 eyeball test
lora: /absolute/path/to/sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_1500.safetensors
lora_scale: 0.8
```

Render one POI via the existing script:

```bash
just daemon-run &   # if not already running
python3 scripts/generate_poi_images.py --genre spaghetti_western --dry-run | head -20
# Then the real render for one POI:
rm -f sidequest-content/genre_packs/spaghetti_western/images/poi/sangre_del_paso_main_street.png
python3 scripts/generate_poi_images.py --genre spaghetti_western 2>&1 | head -3
# Kill after first render completes
```

- [ ] **Step 3: Confirm visible effect**

Open the rendered PNG and visually compare to the (no-LoRA) render from 2026-04-20 at `/private/var/folders/9c/.../sq-daemon-*/flux/render_d9ec40b4.png`. There should be a clear Leone/Almería tonal and compositional shift.

If the image looks identical to the baseline → the remapper or keymap is wrong. Return to Task 1.5 and iterate.

- [ ] **Step 4: Revert the temporary visual_style.yaml edit**

```bash
git checkout sidequest-content/genre_packs/spaghetti_western/worlds/dust_and_lead/visual_style.yaml
```

The real wiring comes in Phase 4 under the new multi-LoRA schema. This temporary edit only existed to prove Phase 2 end-to-end.

**Phase 2 checkpoint:** a real, trained spaghetti_western_landscape LoRA remaps cleanly and visibly changes rendered POI output. We have proof-of-stack before building any more infrastructure.

---

## Phase 3 — Verification Gate

Goal: formalize the 4 checks from the spec as `scripts/lora/verify.py`, calibrate SSIM thresholds against the Phase 2 artifact, and make the gate a hard prerequisite for any future LoRA promotion.

### Task 3.1: Verify — Check 1 (key-match gate)

**Files:**
- Create: `scripts/lora/verify.py`
- Create: `tests/lora/test_verify.py`

- [ ] **Step 1: Write failing test — zero matched keys fails loudly**

```python
# tests/lora/test_verify.py
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import torch
from safetensors.torch import save_file

from scripts.lora.verify import VerifyError, check_key_match


def test_zero_matched_keys_fails(tmp_path: Path) -> None:
    # A safetensors with keys mflux will not recognize at all.
    bogus = {"totally.unknown.key": torch.zeros(4, 4)}
    bogus_path = tmp_path / "bogus.safetensors"
    save_file(bogus, str(bogus_path))

    with pytest.raises(VerifyError, match="zero matched"):
        check_key_match(bogus_path, min_match_fraction=0.8)
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/lora/test_verify.py::test_zero_matched_keys_fails -v
```

- [ ] **Step 3: Implementation**

```python
# scripts/lora/verify.py
"""LoRA verification gate — 4 checks enforced before promotion.

Check 1: key-match (static inspection)
Check 2: SSIM vs. no-LoRA baseline
Check 3: trigger-word discrimination
Check 4: report writer + human sign-off
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
from safetensors import safe_open


class VerifyError(RuntimeError):
    """Raised when a verification check fails."""


def _mflux_target_patterns() -> list[str]:
    """Collect every pattern string mflux uses to recognize LoRA keys."""
    # Import lazily — this module is importable without mflux installed so
    # unit tests can monkeypatch the pattern list.
    from mflux.models.flux.weights.flux_lora_mapping import FluxLoRAMapping

    patterns: list[str] = []
    for target in FluxLoRAMapping.get_mapping():
        patterns.extend(target.possible_up_patterns)
        patterns.extend(target.possible_down_patterns)
        patterns.extend(target.possible_alpha_patterns)
    return patterns


def _key_matches_any(key: str, patterns: Iterable[str]) -> bool:
    """A key matches a pattern if replacing `{block}` with any int produces equality."""
    for p in patterns:
        if "{block}" not in p:
            if key == p:
                return True
            continue
        # Try reasonable block indices (Flux has < 60 blocks).
        for b in range(64):
            if key == p.format(block=b):
                return True
    return False


def check_key_match(
    lora_path: Path, *, min_match_fraction: float = 0.8
) -> dict[str, int | float | list[str]]:
    patterns = _mflux_target_patterns()
    with safe_open(str(lora_path), framework="pt") as f:
        file_keys = list(f.keys())

    matched = [k for k in file_keys if _key_matches_any(k, patterns)]
    match_frac = (len(matched) / len(file_keys)) if file_keys else 0.0

    if len(matched) == 0:
        raise VerifyError(
            f"Check 1 FAIL: zero matched keys. mflux will silently ignore this LoRA. "
            f"File has {len(file_keys)} keys; none match any known target pattern."
        )
    if match_frac < min_match_fraction:
        raise VerifyError(
            f"Check 1 FAIL: only {match_frac:.1%} of file keys match mflux patterns "
            f"(below {min_match_fraction:.0%} floor). {len(file_keys) - len(matched)} keys "
            f"will be silently dropped."
        )

    digest = hashlib.sha256("\n".join(sorted(matched)).encode("utf-8")).hexdigest()
    return {
        "file_keys": len(file_keys),
        "matched_keys": len(matched),
        "match_fraction": match_frac,
        "matched_keys_sha256": digest,
    }
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/lora/test_verify.py::test_zero_matched_keys_fails -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/lora/verify.py tests/lora/test_verify.py
git commit -m "feat(lora): verify Check 1 — key-match gate"
```

### Task 3.2: Verify — Check 2 (SSIM vs baseline)

**Files:**
- Create: `scripts/lora/verify_prompts/landscape.yaml`
- Create: `scripts/lora/verify_prompts/portrait.yaml`
- Create: `scripts/lora/verify_prompts/scene.yaml`
- Modify: `scripts/lora/verify.py`
- Modify: `tests/lora/test_verify.py`

- [ ] **Step 1: Define canonical verify prompts**

```yaml
# scripts/lora/verify_prompts/landscape.yaml
prompt: "a wide street at noon, buildings on both sides, empty ground"
clip: "wide establishing shot"
tier: landscape
seed: 808080
steps: 15
resolution: [1024, 768]
```

```yaml
# scripts/lora/verify_prompts/portrait.yaml
prompt: "a person facing the camera, shoulders up, plain background"
clip: "close-up portrait"
tier: portrait
seed: 808080
steps: 15
resolution: [768, 1024]
```

```yaml
# scripts/lora/verify_prompts/scene.yaml
prompt: "two people talking at a table inside a room"
clip: "two-shot interior"
tier: scene
seed: 808080
steps: 15
resolution: [1024, 768]
```

- [ ] **Step 2: Write failing test — identical images fail SSIM gate**

```python
# tests/lora/test_verify.py — append
from PIL import Image

from scripts.lora.verify import check_ssim_vs_baseline


def test_identical_images_fail_ssim_gate(tmp_path: Path) -> None:
    arr = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    img_a = tmp_path / "a.png"
    img_b = tmp_path / "b.png"
    Image.fromarray(arr).save(img_a)
    Image.fromarray(arr).save(img_b)

    with pytest.raises(VerifyError, match="SSIM"):
        check_ssim_vs_baseline(img_a, img_b, ssim_threshold=0.999)


def test_different_images_pass_ssim_gate(tmp_path: Path) -> None:
    rng = np.random.default_rng(0)
    Image.fromarray((rng.random((64, 64, 3)) * 255).astype(np.uint8)).save(tmp_path / "a.png")
    Image.fromarray((rng.random((64, 64, 3)) * 255).astype(np.uint8)).save(tmp_path / "b.png")
    result = check_ssim_vs_baseline(tmp_path / "a.png", tmp_path / "b.png", ssim_threshold=0.999)
    assert result["ssim"] < 0.999
```

- [ ] **Step 3: Run — expect ImportError**

```bash
pytest tests/lora/test_verify.py -v
```

- [ ] **Step 4: Implementation — append to `scripts/lora/verify.py`**

```python
# Append to scripts/lora/verify.py
from PIL import Image


def _ssim(a: np.ndarray, b: np.ndarray) -> float:
    """Simple SSIM implementation over grayscale. Returns scalar in [-1, 1]."""
    if a.ndim == 3:
        a = a.mean(axis=-1)
    if b.ndim == 3:
        b = b.mean(axis=-1)
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    mu_a = a.mean()
    mu_b = b.mean()
    var_a = a.var()
    var_b = b.var()
    cov = ((a - mu_a) * (b - mu_b)).mean()
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    num = (2 * mu_a * mu_b + c1) * (2 * cov + c2)
    den = (mu_a**2 + mu_b**2 + c1) * (var_a + var_b + c2)
    return float(num / den)


def check_ssim_vs_baseline(
    baseline_png: Path, lora_png: Path, *, ssim_threshold: float = 0.999
) -> dict[str, float]:
    a = np.array(Image.open(baseline_png).convert("RGB"))
    b = np.array(Image.open(lora_png).convert("RGB"))
    if a.shape != b.shape:
        raise VerifyError(f"SSIM FAIL: shape mismatch {a.shape} vs {b.shape}")
    score = _ssim(a, b)
    if score >= ssim_threshold:
        raise VerifyError(
            f"Check 2 FAIL: SSIM {score:.4f} ≥ {ssim_threshold:.4f}. "
            f"LoRA had no meaningful pixel effect (silent-fallback suspected)."
        )
    return {"ssim": score}
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/lora/test_verify.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scripts/lora/verify.py scripts/lora/verify_prompts/ tests/lora/test_verify.py
git commit -m "feat(lora): verify Check 2 — SSIM pixel-diff gate"
```

### Task 3.3: Verify — Check 3 (trigger discrimination)

**Files:**
- Modify: `scripts/lora/verify.py`
- Modify: `tests/lora/test_verify.py`

- [ ] **Step 1: Write failing test**

```python
# tests/lora/test_verify.py — append
from scripts.lora.verify import check_trigger_discrimination


def test_trigger_ssim_under_threshold_passes(tmp_path: Path) -> None:
    rng = np.random.default_rng(42)
    img_triggered = tmp_path / "trig.png"
    img_control = tmp_path / "ctrl.png"
    Image.fromarray((rng.random((64, 64, 3)) * 255).astype(np.uint8)).save(img_triggered)
    Image.fromarray((rng.random((64, 64, 3)) * 255).astype(np.uint8)).save(img_control)

    result = check_trigger_discrimination(img_triggered, img_control, ssim_threshold=0.97)
    assert result["ssim"] < 0.97


def test_trigger_ssim_too_high_fails(tmp_path: Path) -> None:
    arr = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    Image.fromarray(arr).save(tmp_path / "a.png")
    Image.fromarray(arr).save(tmp_path / "b.png")
    with pytest.raises(VerifyError, match="trigger"):
        check_trigger_discrimination(tmp_path / "a.png", tmp_path / "b.png", ssim_threshold=0.97)
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/lora/test_verify.py -v
```

- [ ] **Step 3: Implementation — append to `scripts/lora/verify.py`**

```python
def check_trigger_discrimination(
    triggered_png: Path, control_png: Path, *, ssim_threshold: float = 0.97
) -> dict[str, float]:
    a = np.array(Image.open(triggered_png).convert("RGB"))
    b = np.array(Image.open(control_png).convert("RGB"))
    if a.shape != b.shape:
        raise VerifyError(f"trigger FAIL: shape mismatch {a.shape} vs {b.shape}")
    score = _ssim(a, b)
    if score >= ssim_threshold:
        raise VerifyError(
            f"Check 3 FAIL: trigger vs control SSIM {score:.4f} ≥ {ssim_threshold:.4f}. "
            f"Trigger word isn't affecting output — trigger unlearned or dropout too aggressive."
        )
    return {"ssim": score}
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/lora/test_verify.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/lora/verify.py tests/lora/test_verify.py
git commit -m "feat(lora): verify Check 3 — trigger discrimination gate"
```

### Task 3.4: Verify — Check 4 (report writer + CLI orchestration)

**Files:**
- Modify: `scripts/lora/verify.py`
- Modify: `tests/lora/test_verify.py`

- [ ] **Step 1: Write failing test — report is written on success**

```python
# tests/lora/test_verify.py — append
from scripts.lora.verify import write_verification_report


def test_report_written_with_all_checks(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    write_verification_report(
        report_path=report_path,
        lora_name="fake_landscape",
        lora_file=tmp_path / "fake.safetensors",
        check_results={
            "key_match": {"matched_keys": 456, "file_keys": 500, "match_fraction": 0.912, "matched_keys_sha256": "abc123"},
            "ssim_vs_baseline": {"ssim": 0.81},
            "trigger_discrimination": {"ssim": 0.74},
        },
        rendered_images={
            "baseline": tmp_path / "b.png",
            "with_lora": tmp_path / "l.png",
            "with_trigger": tmp_path / "t.png",
            "control": tmp_path / "c.png",
        },
    )
    text = report_path.read_text()
    assert "fake_landscape" in text
    assert "matched_keys" in text
    assert "0.81" in text   # SSIM baseline number
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/lora/test_verify.py -v
```

- [ ] **Step 3: Implementation — append to `scripts/lora/verify.py`**

```python
def write_verification_report(
    report_path: Path,
    lora_name: str,
    lora_file: Path,
    check_results: dict[str, dict],
    rendered_images: dict[str, Path],
) -> None:
    lines = [
        f"# LoRA Verification Report — {lora_name}",
        "",
        f"**File:** `{lora_file}`",
        "",
        "## Check 1 — Key match",
        "",
        f"- file_keys: {check_results['key_match']['file_keys']}",
        f"- matched_keys: {check_results['key_match']['matched_keys']}",
        f"- match_fraction: {check_results['key_match']['match_fraction']:.3f}",
        f"- matched_keys_sha256: `{check_results['key_match']['matched_keys_sha256']}`",
        "",
        "## Check 2 — SSIM vs baseline",
        "",
        f"- ssim: **{check_results['ssim_vs_baseline']['ssim']:.4f}**",
        f"- baseline: `{rendered_images['baseline']}`",
        f"- with_lora: `{rendered_images['with_lora']}`",
        "",
        "## Check 3 — Trigger discrimination",
        "",
        f"- ssim: **{check_results['trigger_discrimination']['ssim']:.4f}**",
        f"- with_trigger: `{rendered_images['with_trigger']}`",
        f"- control: `{rendered_images['control']}`",
        "",
        "## Human Sign-off",
        "",
        "- [ ] Verified visually that the LoRA effect is present and appropriate",
        "- [ ] Approve promotion to shipped `{genre}/` directory",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/lora/test_verify.py -v
```

- [ ] **Step 5: Add the `verify` CLI driver — append to `scripts/lora/verify.py`**

```python
def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lora", required=True, type=Path, help=".safetensors to verify")
    parser.add_argument("--name", required=True, help="Logical LoRA name (e.g., spaghetti_western_landscape)")
    parser.add_argument("--trigger", default="", help="Trigger word (optional; skips Check 3 if empty)")
    parser.add_argument("--kind", required=True, choices=["landscape", "portrait", "scene"])
    parser.add_argument("--scale", type=float, default=0.8)
    parser.add_argument("--report-dir", required=True, type=Path)
    parser.add_argument("--ssim-baseline-threshold", type=float, default=0.999)
    parser.add_argument("--ssim-trigger-threshold", type=float, default=0.97)
    parser.add_argument("--min-match-fraction", type=float, default=0.8)
    args = parser.parse_args()

    print(f"Verifying {args.name} at {args.lora}")

    # Check 1 — static
    km = check_key_match(args.lora, min_match_fraction=args.min_match_fraction)
    print(f"Check 1 OK: matched {km['matched_keys']}/{km['file_keys']} keys ({km['match_fraction']:.1%})")

    # Check 2 — render + SSIM
    prompt_yaml = Path(__file__).parent / "verify_prompts" / f"{args.kind}.yaml"
    baseline_png, lora_png = asyncio.run(_render_with_and_without(prompt_yaml, args.lora, args.scale))
    s2 = check_ssim_vs_baseline(baseline_png, lora_png, ssim_threshold=args.ssim_baseline_threshold)
    print(f"Check 2 OK: SSIM {s2['ssim']:.4f} < {args.ssim_baseline_threshold}")

    # Check 3 — trigger discrimination (if trigger supplied)
    s3 = {"ssim": 0.0}
    triggered_png = control_png = None
    if args.trigger:
        triggered_png, control_png = asyncio.run(
            _render_trigger_pair(prompt_yaml, args.lora, args.scale, args.trigger)
        )
        s3 = check_trigger_discrimination(
            triggered_png, control_png, ssim_threshold=args.ssim_trigger_threshold
        )
        print(f"Check 3 OK: trigger SSIM {s3['ssim']:.4f} < {args.ssim_trigger_threshold}")

    # Check 4 — write report
    args.report_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = args.report_dir / f"verify-{args.name}-{ts}.md"
    write_verification_report(
        report_path=report_path,
        lora_name=args.name,
        lora_file=args.lora,
        check_results={
            "key_match": km,
            "ssim_vs_baseline": s2,
            "trigger_discrimination": s3,
        },
        rendered_images={
            "baseline": baseline_png,
            "with_lora": lora_png,
            "with_trigger": triggered_png or baseline_png,
            "control": control_png or baseline_png,
        },
    )
    print(f"Report: {report_path}")
    return 0


async def _render_with_and_without(prompt_yaml: Path, lora_path: Path, scale: float) -> tuple[Path, Path]:
    """Render the canonical prompt twice — with LoRA and without. Uses the new multi-LoRA protocol."""
    import yaml
    from scripts.render_common import send_render
    spec = yaml.safe_load(prompt_yaml.read_text())

    async def _do(with_lora: bool) -> Path:
        params: dict = dict(
            tier=spec["tier"],
            positive=spec["prompt"],
            clip=spec["clip"],
            negative="",
            seed=spec["seed"],
            steps=spec["steps"],
        )
        if with_lora:
            params["lora_paths"] = [str(lora_path)]
            params["lora_scales"] = [scale]
        result = await send_render(**params)
        if "error" in result:
            raise VerifyError(f"render failed: {result['error']}")
        return Path(result["result"].get("image_path") or result["result"]["image_url"])

    return await _do(False), await _do(True)


async def _render_trigger_pair(
    prompt_yaml: Path, lora_path: Path, scale: float, trigger: str
) -> tuple[Path, Path]:
    import yaml
    from scripts.render_common import send_render
    spec = yaml.safe_load(prompt_yaml.read_text())

    async def _do(prefix: str) -> Path:
        params = dict(
            tier=spec["tier"],
            positive=f"{prefix}, {spec['prompt']}",
            clip=spec["clip"],
            negative="",
            seed=spec["seed"],
            steps=spec["steps"],
            lora_paths=[str(lora_path)],
            lora_scales=[scale],
        )
        result = await send_render(**params)
        if "error" in result:
            raise VerifyError(f"render failed: {result['error']}")
        return Path(result["result"].get("image_path") or result["result"]["image_url"])

    return await _do(trigger), await _do("an unrelated word")


if __name__ == "__main__":
    sys.exit(_cli())
```

- [ ] **Step 6: Commit**

```bash
git add scripts/lora/verify.py tests/lora/test_verify.py
git commit -m "feat(lora): verify Check 4 — report writer + CLI driver"
```

### Task 3.5: Calibrate SSIM thresholds against the Phase 2 artifact

**Files:**
- Modify: `scripts/lora/verify.py` (update default threshold constants if needed)

Note: this task depends on the Phase 4 protocol change being done first — the verify CLI passes `lora_paths=[...]` to `send_render`. If Phase 4 hasn't landed, run this task AFTER Task 4.1 completes.

- [ ] **Step 1: Run verify against the Phase 2 LoRA**

```bash
python3 scripts/lora/verify.py \
  --lora sidequest-content/lora/spaghetti_western/archive/spaghetti_western_landscape_1500.safetensors \
  --name spaghetti_western_landscape \
  --trigger spaghetti_western_landscape \
  --kind landscape \
  --scale 0.8 \
  --report-dir sidequest-content/lora/spaghetti_western/archive/
```

Expected: all three dynamic checks pass (or report actual SSIM numbers).

- [ ] **Step 2: Inspect the actual SSIM numbers**

Open the generated report. Record:
- SSIM vs baseline (should be well below 0.999)
- Trigger SSIM (should be well below 0.97)

If either number is suspiciously close to the threshold (e.g., baseline SSIM = 0.998 — narrowly passing), tighten the default by 0.001 and document why in a comment. If either number is comfortably below, leave the threshold as-is.

- [ ] **Step 3: Commit any threshold tuning**

```bash
git add scripts/lora/verify.py
git commit -m "tune(lora): calibrate SSIM defaults against first real LoRA (N=1)"
```

**Phase 3 checkpoint:** `verify.py` gates future LoRAs. No second LoRA is trained until this is in place.

---

## Phase 4 — Daemon Multi-LoRA + Schema Migration

Goal: widen the daemon protocol + worker to multi-LoRA, build the genre/world resolver, migrate all three `visual_style.yaml` files to the new schema, emit OTEL spans proving engagement.

### Task 4.1: Protocol widening — `render_common.send_render`

**Files:**
- Modify: `scripts/render_common.py`
- Create: `tests/test_render_common.py` (if not present)

- [ ] **Step 1: Inspect the current send_render signature**

```bash
grep -n "async def send_render\|lora_path\|lora_scale" scripts/render_common.py | head -20
```

Capture the current signature. The migration replaces `lora_path: str = ""` and `lora_scale: float = 1.0` with `lora_paths: list[str] | None = None` and `lora_scales: list[float] | None = None`.

- [ ] **Step 2: Write failing test — new protocol arguments**

```python
# tests/test_render_common.py
from __future__ import annotations

import inspect

from scripts.render_common import send_render


def test_send_render_accepts_lora_lists() -> None:
    sig = inspect.signature(send_render)
    assert "lora_paths" in sig.parameters
    assert "lora_scales" in sig.parameters
    # Old single-value params are gone
    assert "lora_path" not in sig.parameters
    assert "lora_scale" not in sig.parameters
```

- [ ] **Step 3: Run — expect failure (old signature still in place)**

```bash
pytest tests/test_render_common.py -v
```

- [ ] **Step 4: Edit `scripts/render_common.py`**

Replace the lora-related parameter block:

```python
# scripts/render_common.py — send_render signature
async def send_render(
    tier: str,
    positive: str,
    clip: str,
    negative: str,
    seed: int,
    steps: int = 15,
    *,
    art_style: str = "",
    visual_tag_overrides: dict | None = None,
    lora_paths: list[str] | None = None,
    lora_scales: list[float] | None = None,
    variant: str = "",
) -> dict:
    ...
```

In the body, replace the single-LoRA block:

```python
# BEFORE
if lora_path:
    params["lora_path"] = lora_path
    params["lora_scale"] = lora_scale

# AFTER
if lora_paths:
    if lora_scales is None or len(lora_scales) != len(lora_paths):
        raise ValueError(
            "lora_scales must be provided with same length as lora_paths"
        )
    params["lora_paths"] = list(lora_paths)
    params["lora_scales"] = list(lora_scales)
```

Also update `render_batch()` in the same file (around line 256):

```python
# BEFORE
lora_path=visual_style.get("lora", ""),
lora_scale=visual_style.get("lora_scale", 1.0),

# AFTER — read the new array schema; see Task 4.4 for how visual_style is pre-composed
loras = visual_style.get("resolved_loras", [])
lora_paths_arg = [e["file"] for e in loras] if loras else None
lora_scales_arg = [e["scale"] for e in loras] if loras else None
# ... pass lora_paths=lora_paths_arg, lora_scales=lora_scales_arg
```

(`resolved_loras` is the flat list after `compose_lora_stack()` runs; see Task 4.4.)

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/test_render_common.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scripts/render_common.py tests/test_render_common.py
git commit -m "feat(render): protocol widening to lora_paths[] / lora_scales[]"
```

### Task 4.2: Daemon worker — multi-LoRA + matched_key_count + OTEL

**Files:**
- Modify: `sidequest-daemon/sidequest_daemon/media/workers/flux_mlx_worker.py`
- Create: `sidequest-daemon/tests/media/test_flux_mlx_worker_multilora.py`

- [ ] **Step 1: Read the current `_build_lora_model` + `render`**

```bash
grep -n "_build_lora_model\|lora_path\|lora_scale" sidequest-daemon/sidequest_daemon/media/workers/flux_mlx_worker.py
```

Capture the current shape so the edits are surgical.

- [ ] **Step 2: Write failing test — worker accepts lora_paths[]**

```python
# sidequest-daemon/tests/media/test_flux_mlx_worker_multilora.py
from __future__ import annotations

import inspect

from sidequest_daemon.media.workers.flux_mlx_worker import FluxMlxWorker


def test_build_lora_model_accepts_lists() -> None:
    sig = inspect.signature(FluxMlxWorker._build_lora_model)
    assert "lora_paths" in sig.parameters
    assert "lora_scales" in sig.parameters
    assert "lora_path" not in sig.parameters
```

- [ ] **Step 3: Run — expect failure**

```bash
cd sidequest-daemon
uv run pytest tests/media/test_flux_mlx_worker_multilora.py -v
```

- [ ] **Step 4: Edit `flux_mlx_worker.py`**

Replace `_build_lora_model`:

```python
def _build_lora_model(
    self, variant: str, lora_paths: list[str], lora_scales: list[float]
) -> object:
    """Construct a Flux1 instance with one or more LoRAs applied."""
    from mflux.models.flux.variants.txt2img.flux import Flux1
    from mflux.models.common.config.model_config import ModelConfig

    config_factory = {"dev": ModelConfig.dev, "schnell": ModelConfig.schnell}
    if variant not in config_factory:
        raise ValueError(f"Unknown variant for LoRA: {variant!r}")

    return Flux1(
        model_config=config_factory[variant](),
        quantize=self.QUANTIZE,
        lora_paths=list(lora_paths),
        lora_scales=list(lora_scales),
    )
```

In `render()`, replace the singleton params with arrays + key-match accounting:

```python
# Inside render(), replacing the current single-LoRA block
lora_paths: list[str] = list(params.get("lora_paths") or [])
lora_scales: list[float] = list(params.get("lora_scales") or [])

span.set_attribute("render.tier", tier_name)
span.set_attribute("render.seed", seed)
span.set_attribute("render.variant", variant)
span.set_attribute("render.width", tier_cfg["w"])
span.set_attribute("render.height", tier_cfg["h"])

if lora_paths:
    if len(lora_scales) != len(lora_paths):
        raise ValueError("lora_paths and lora_scales length mismatch")
    matched_counts = self._count_matched_keys(lora_paths)
    span.set_attribute("render.lora.stack_size", len(lora_paths))
    span.set_attribute("render.lora.files", lora_paths)
    span.set_attribute("render.lora.scales", lora_scales)
    span.set_attribute("render.lora.matched_keys", matched_counts)
    if any(c == 0 for c in matched_counts):
        span.set_status(
            trace.StatusCode.ERROR,
            "at least one LoRA file had zero matched keys; output will be identical to no-LoRA for those files",
        )
        log.error(
            "FLUX MLX RENDER [%s] LoRA matched_counts=%s — ZERO match detected. "
            "Silent-fallback risk.",
            tier_name, matched_counts,
        )
    log.info(
        "FLUX MLX RENDER [%s] seed=%s loras=%s scales=%s matched_keys=%s",
        tier_name, seed, lora_paths, lora_scales, matched_counts,
    )
    model = self._build_lora_model(variant, lora_paths, lora_scales)
else:
    span.set_attribute("render.lora.stack_size", 0)
    log.info("FLUX MLX RENDER [%s] seed=%s (no LoRA)", tier_name, seed)
    self._ensure_variant(variant)
    model = self.models[variant]
```

Add the helper:

```python
def _count_matched_keys(self, lora_paths: list[str]) -> list[int]:
    """Count, per file, how many of its keys match mflux's known patterns.

    Zero for a file means the file will be silently ignored at inference.
    """
    from mflux.models.flux.weights.flux_lora_mapping import FluxLoRAMapping
    from safetensors import safe_open

    patterns: list[str] = []
    for target in FluxLoRAMapping.get_mapping():
        patterns.extend(target.possible_up_patterns)
        patterns.extend(target.possible_down_patterns)
        patterns.extend(target.possible_alpha_patterns)

    def _matches(key: str) -> bool:
        for p in patterns:
            if "{block}" not in p:
                if key == p:
                    return True
                continue
            for b in range(64):
                if key == p.format(block=b):
                    return True
        return False

    counts: list[int] = []
    for path in lora_paths:
        with safe_open(path, framework="pt") as f:
            counts.append(sum(1 for k in f.keys() if _matches(k)))
    return counts
```

- [ ] **Step 5: Run — expect pass**

```bash
cd sidequest-daemon
uv run pytest tests/media/test_flux_mlx_worker_multilora.py -v
```

- [ ] **Step 6: Run the daemon's existing test suite to catch regressions**

```bash
cd sidequest-daemon
uv run pytest tests/ -v -k "lora or worker"
```

Expected: all pass (any existing single-LoRA tests will need to be updated to the new signature — update them in this task or the test file's next edit).

- [ ] **Step 7: Commit**

```bash
cd /Users/keithavery/Projects/oq-2
git add sidequest-daemon/
git commit -m "feat(daemon): multi-LoRA rendering with matched_key_count OTEL"
```

### Task 4.3: `compose_lora_stack` — pure-function resolver

**Files:**
- Create: `scripts/lora/compose.py`
- Create: `tests/lora/test_compose.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/lora/test_compose.py
from __future__ import annotations

import pytest

from scripts.lora.compose import ComposeError, compose_lora_stack


GENRE = {
    "loras": [
        {"name": "sw_landscape", "file": "p1.safetensors", "scale": 0.8,
         "applies_to": ["landscape", "scene"], "trigger": "sw_landscape"},
        {"name": "sw_portrait", "file": "p2.safetensors", "scale": 0.8,
         "applies_to": ["portrait"], "trigger": "sw_portrait"},
    ]
}


def test_no_world_overrides_inherits_genre() -> None:
    world: dict = {}
    resolved = compose_lora_stack(GENRE, world, tier="landscape")
    assert [e["name"] for e in resolved] == ["sw_landscape"]


def test_world_exclude_drops_inherited() -> None:
    world = {"loras": {"exclude": ["sw_landscape"]}}
    resolved = compose_lora_stack(GENRE, world, tier="landscape")
    assert resolved == []


def test_world_add_appends() -> None:
    world = {
        "loras": {
            "add": [
                {"name": "mccoy_landscape", "file": "p3.safetensors", "scale": 0.85,
                 "applies_to": ["landscape"], "trigger": "mccoy_landscape"}
            ]
        }
    }
    resolved = compose_lora_stack(GENRE, world, tier="landscape")
    assert [e["name"] for e in resolved] == ["sw_landscape", "mccoy_landscape"]


def test_tier_filter_skips_non_matching() -> None:
    resolved = compose_lora_stack(GENRE, {}, tier="portrait")
    assert [e["name"] for e in resolved] == ["sw_portrait"]


def test_world_add_with_duplicate_name_fails() -> None:
    world = {
        "loras": {
            "add": [
                {"name": "sw_landscape", "file": "dup.safetensors", "scale": 0.5,
                 "applies_to": ["landscape"]}
            ]
        }
    }
    with pytest.raises(ComposeError, match="duplicate"):
        compose_lora_stack(GENRE, world, tier="landscape")


def test_applies_to_empty_fails_validation() -> None:
    bad_genre = {
        "loras": [
            {"name": "x", "file": "x.safetensors", "scale": 1.0, "applies_to": []},
        ]
    }
    with pytest.raises(ComposeError, match="applies_to"):
        compose_lora_stack(bad_genre, {}, tier="landscape")
```

- [ ] **Step 2: Run — expect ImportError**

```bash
pytest tests/lora/test_compose.py -v
```

- [ ] **Step 3: Implementation**

```python
# scripts/lora/compose.py
"""Compose the effective LoRA stack from genre + world visual_style.yaml.

Pure function — no I/O beyond the already-loaded dicts. Caller passes
the YAML-parsed dicts and the current render tier; returns a flat list
of LoRA entries filtered by `applies_to`.
"""
from __future__ import annotations

from typing import Any


class ComposeError(RuntimeError):
    """Raised when genre+world LoRA composition violates schema rules."""


def _validate_entry(entry: dict[str, Any], source: str) -> None:
    for required in ("name", "file", "scale", "applies_to"):
        if required not in entry:
            raise ComposeError(f"{source}: LoRA entry missing required field {required!r}")
    if not isinstance(entry["applies_to"], list) or not entry["applies_to"]:
        raise ComposeError(
            f"{source}: LoRA {entry.get('name', '?')} has empty applies_to — misconfiguration."
        )


def compose_lora_stack(
    genre_style: dict[str, Any],
    world_style: dict[str, Any],
    tier: str,
) -> list[dict[str, Any]]:
    base: list[dict[str, Any]] = list(genre_style.get("loras") or [])
    for entry in base:
        _validate_entry(entry, source="genre")

    world_loras = world_style.get("loras") or {}
    # World's `loras:` is a DICT (exclude/add). If it's a list, that's a
    # v1-schema file that hasn't been migrated — loud failure rather than
    # silently ignoring.
    if isinstance(world_loras, list):
        raise ComposeError(
            "world visual_style.yaml has legacy list-form `loras:`; "
            "expected {exclude: [...], add: [...]} schema."
        )

    excluded = set(world_loras.get("exclude") or [])
    base = [e for e in base if e["name"] not in excluded]

    added = list(world_loras.get("add") or [])
    for entry in added:
        _validate_entry(entry, source="world")

    existing_names = {e["name"] for e in base}
    for add_entry in added:
        if add_entry["name"] in existing_names:
            raise ComposeError(
                f"world.loras.add declares duplicate name {add_entry['name']!r}; "
                f"use world.loras.exclude first to drop the inherited entry."
            )

    composed = base + added
    return [e for e in composed if tier in e["applies_to"]]
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/lora/test_compose.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/lora/compose.py tests/lora/test_compose.py
git commit -m "feat(lora): compose_lora_stack pure resolver (extend+exclude+add)"
```

### Task 4.4: Wire `compose_lora_stack` into `render_common.load_visual_style`

**Files:**
- Modify: `scripts/render_common.py`
- Modify: `tests/test_render_common.py`

- [ ] **Step 1: Read the current load_visual_style**

```bash
grep -n "load_visual_style\|def.*visual_style" scripts/render_common.py | head -10
```

- [ ] **Step 2: Write failing test — load_visual_style returns resolved_loras**

```python
# tests/test_render_common.py — append
from pathlib import Path
import yaml

from scripts.render_common import load_visual_style


def test_load_visual_style_composes_lora_stack(tmp_path: Path) -> None:
    genre_dir = tmp_path / "genre"
    genre_dir.mkdir()
    (genre_dir / "visual_style.yaml").write_text(yaml.safe_dump({
        "positive_suffix": "",
        "loras": [
            {"name": "sw_landscape", "file": "a.safetensors", "scale": 0.8,
             "applies_to": ["landscape"], "trigger": "sw_landscape"},
        ],
    }))

    world_dir = genre_dir / "worlds" / "w1"
    world_dir.mkdir(parents=True)
    (world_dir / "visual_style.yaml").write_text(yaml.safe_dump({
        "loras": {"exclude": ["sw_landscape"]},
    }))

    resolved = load_visual_style(genre_dir=genre_dir, world_dir=world_dir, tier="landscape")
    assert resolved["resolved_loras"] == []
```

- [ ] **Step 3: Run — expect failure**

```bash
pytest tests/test_render_common.py::test_load_visual_style_composes_lora_stack -v
```

- [ ] **Step 4: Implementation**

Add to `scripts/render_common.py`:

```python
from scripts.lora.compose import compose_lora_stack


def load_visual_style(
    *,
    genre_dir: Path,
    world_dir: Path | None = None,
    tier: str,
) -> dict:
    """Load + merge genre and (optional) world visual_style.yaml; resolve LoRA stack for tier."""
    import yaml as _yaml

    genre_style: dict = _yaml.safe_load((genre_dir / "visual_style.yaml").read_text()) or {}
    world_style: dict = {}
    if world_dir is not None and (world_dir / "visual_style.yaml").exists():
        world_style = _yaml.safe_load((world_dir / "visual_style.yaml").read_text()) or {}

    merged = dict(genre_style)
    # Most keys use world-overrides-genre, except `loras` which has its own resolver.
    for key, value in world_style.items():
        if key == "loras":
            continue
        merged[key] = value

    merged["resolved_loras"] = compose_lora_stack(genre_style, world_style, tier=tier)
    return merged
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/test_render_common.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scripts/render_common.py tests/test_render_common.py
git commit -m "feat(render): wire compose_lora_stack into load_visual_style"
```

### Task 4.5: Archive old LoRAs + move datasets into new layout

**Files:**
- Move: existing `.ckpt` / `.safetensors` in `sidequest-content/lora/spaghetti-western/` → `sidequest-content/lora/spaghetti_western/archive/legacy/`
- The directory rename from kebab-case to snake_case matches the genre pack naming (consistency).

- [ ] **Step 1: Create new layout + move legacy files**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
mkdir -p lora/spaghetti_western/archive/legacy
git mv lora/spaghetti-western/*.ckpt lora/spaghetti_western/archive/legacy/
git mv lora/spaghetti-western/*.safetensors lora/spaghetti_western/archive/legacy/
rmdir lora/spaghetti-western
ls lora/spaghetti_western/archive/legacy/
```

Expected: three files (leone_style_500, leone_style_1000, spaghetti_western_sq_1500).

- [ ] **Step 2: Move other genre dirs to snake_case for consistency**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
git mv lora/caverns-and-claudes lora/caverns_and_claudes
git mv lora/elemental-harmony lora/elemental_harmony
```

- [ ] **Step 3: Commit**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
git commit -m "chore(lora): snake_case genre dirs; archive legacy LoRAs"
```

### Task 4.6: Migrate `visual_style.yaml` files to multi-LoRA schema

**Files:**
- Modify: `sidequest-content/genre_packs/spaghetti_western/visual_style.yaml`
- Modify: `sidequest-content/genre_packs/spaghetti_western/worlds/dust_and_lead/visual_style.yaml`
- Modify: `sidequest-content/genre_packs/spaghetti_western/worlds/the_real_mccoy/visual_style.yaml`

- [ ] **Step 1: Genre-level — add `loras:` list**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
```

Append (or insert, per file structure) to `genre_packs/spaghetti_western/visual_style.yaml`:

```yaml
loras:
  - name: spaghetti_western_landscape
    file: lora/spaghetti_western/spaghetti_western_landscape.safetensors
    scale: 0.8
    applies_to: [landscape, scene]
    trigger: spaghetti_western_landscape
  # portrait LoRA is added when trained — leave commented as placeholder:
  # - name: spaghetti_western_portrait
  #   file: lora/spaghetti_western/spaghetti_western_portrait.safetensors
  #   scale: 0.8
  #   applies_to: [portrait]
  #   trigger: spaghetti_western_portrait
```

- [ ] **Step 2: Remove the legacy `lora:` / `lora_scale:` flat keys**

Open `genre_packs/spaghetti_western/worlds/dust_and_lead/visual_style.yaml` and delete any residual `lora:` / `lora_scale:` / `lora_path:` keys. Do the same for the_real_mccoy and any portrait LoRA refs left over.

For `the_real_mccoy/visual_style.yaml`, replace the prospective `lora_triggers:` block with:

```yaml
loras:
  exclude:
    - spaghetti_western_landscape   # Almería desert fights 1878 Pittsburgh
    # portrait LoRA also excluded once it exists
```

(`add:` is populated later when `the_real_mccoy_landscape` is trained in Phase 5.)

- [ ] **Step 3: Promote the Phase 2 `.safetensors` to the shipped path**

Only do this once `verify.py` against the LoRA passed all checks (Task 3.5 confirms). The shipped file is the one referenced by `genre_packs/spaghetti_western/visual_style.yaml`:

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
cp lora/spaghetti_western/archive/spaghetti_western_landscape_1500.safetensors \
   lora/spaghetti_western/spaghetti_western_landscape.safetensors
```

- [ ] **Step 4: Commit**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
git add lora/spaghetti_western/spaghetti_western_landscape.safetensors genre_packs/
git commit -m "feat(content): multi-LoRA visual_style schema + ship sw_landscape"
```

### Task 4.7: Render all 28 spaghetti_western POIs with LoRA engaged

**Files:** no code changes — an end-to-end exercise.

- [ ] **Step 1: Restart the daemon to pick up worker changes**

```bash
cd /Users/keithavery/Projects/oq-2
# Kill any running daemon
pkill -f sidequest-renderer || true
sleep 2
just daemon-run &
sleep 30   # warmup
curl -s --unix-socket /tmp/sidequest-renderer.sock http://.../health 2>&1 | head -5 || ls -la /tmp/sidequest-renderer.sock
```

- [ ] **Step 2: Delete any stale POI images generated without LoRA**

```bash
ls sidequest-content/genre_packs/spaghetti_western/images/poi/
rm -f sidequest-content/genre_packs/spaghetti_western/images/poi/*.png
```

- [ ] **Step 3: Run the POI generator**

```bash
nohup python3 scripts/generate_poi_images.py --genre spaghetti_western > /tmp/poi-gen.log 2>&1 &
echo "PID: $!"
```

- [ ] **Step 4: Monitor + verify OTEL spans report matched_keys > 0**

```bash
# Follow progress
tail -f /tmp/poi-gen.log
```

In a second terminal, watch daemon logs for the `FLUX MLX RENDER` lines — they now report `matched_keys=[N]` per LoRA. Any `matched_keys=[0]` means the pipeline failed silently and this is a regression.

Expected: 28 images rendered, each log line showing a non-zero `matched_keys` count.

- [ ] **Step 5: Commit the POI renders**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
git add genre_packs/spaghetti_western/images/poi/
git commit -m "content(images): spaghetti_western POIs (28) rendered with LoRA applied"
```

**Phase 4 checkpoint:** every render goes through the new multi-LoRA pipeline; daemon OTEL proves per-LoRA engagement; POI images render with the Leone look actually applied.

---

## Phase 5 — Skill Update + Second World

Goal: update `/sq-lora` to document the new pipeline and prove it end-to-end on `the_real_mccoy` worlds.

### Task 5.1: Rewrite `/sq-lora` skill

**Files:**
- Modify: `.claude/commands/sq-lora.md`

- [ ] **Step 1: Edit sq-lora.md**

Replace the existing Step 4 (Draw Things CLI) and Step 5 (Test) sections with:

```markdown
### Step 4: Train

**Goal:** Train LoRA on Flux 1 Dev via `mlx-examples/flux/` (MLX-native on Apple Silicon).

**Prerequisites:**
- `mlx-examples` cloned at `~/Projects/mlx-examples/`
- `~/.venv/mlx-flux-training/` with `mlx-examples/flux/requirements.txt` installed
- Dataset passes `scripts/lora/train.py`'s preflight (150+ paired images)

**Training command:**

```bash
python3 scripts/lora/train.py \
  --dataset sidequest-content/lora-datasets/{genre}/{kind} \
  --output  sidequest-content/lora/{genre}/archive/{genre}_{kind} \
  --trigger {genre}_{kind} \
  --kind    {kind} \
  --steps   1500 --rank 32 --learning-rate 1e-4 --resolution 768 \
  --caption-dropout 0.1 --save-every 500
```

Log lives at `/tmp/{trigger}_train.log`. Expect overnight runtime on M3 Max.

---

### Step 5: Remap + Verify + Promote

After training, convert MLX `.npz` → mflux-compatible `.safetensors`, then run the
4-check verification gate, then promote if approved.

```bash
# 1. Remap
python3 scripts/lora/remap_mlx_to_mflux.py \
  --input  sidequest-content/lora/{genre}/archive/{name}_1500.npz \
  --output sidequest-content/lora/{genre}/archive/{name}_1500.safetensors \
  --keymap scripts/lora/mlx_to_mflux_keymap.yaml

# 2. Verify (requires daemon running — see `just daemon-run`)
python3 scripts/lora/verify.py \
  --lora sidequest-content/lora/{genre}/archive/{name}_1500.safetensors \
  --name {name} \
  --trigger {name} \
  --kind {kind} \
  --scale 0.8 \
  --report-dir sidequest-content/lora/{genre}/archive/
```

Open the generated report. If checks pass and the images look right, promote:

```bash
# 3. Promote — copy .safetensors to the shipped path
cp sidequest-content/lora/{genre}/archive/{name}_1500.safetensors \
   sidequest-content/lora/{genre}/{name}.safetensors

# 4. Wire it into visual_style.yaml
# (Edit the genre or world YAML, add entry under `loras:`)
```

**Never ship a LoRA that failed any of the 4 checks.** The SSIM baseline gate
specifically catches silent-fallback — a LoRA that loads without error but has
zero rendering effect. Those LoRAs don't go to `{genre}/`, they stay in `archive/`
with the failing verify report attached.
```

- [ ] **Step 2: Delete any residual Draw Things references in the skill**

```bash
grep -n "draw-things\|draw_things" .claude/commands/sq-lora.md
```

Remove every hit.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/sq-lora.md
git commit -m "docs(sq-lora): replace Draw Things CLI with mlx-examples + verify pipeline"
```

### Task 5.2: Train `the_real_mccoy_landscape` (second world, exercise exclude+add)

**Files:** content-authoring task; same Phase 2 flow applied to a different dataset.

- [ ] **Step 1: Curate `the_real_mccoy/landscape` dataset**

Target: `sidequest-content/lora-datasets/spaghetti_western/worlds/the_real_mccoy/landscape/` — 150+ paired images sourced from 1878 Pittsburgh industrial references (Harper's Weekly engravings, Detroit Publishing Co. photochroms, Hine industrial photography). Trigger: `the_real_mccoy_landscape`.

- [ ] **Step 2: Train**

```bash
python3 scripts/lora/train.py \
  --dataset sidequest-content/lora-datasets/spaghetti_western/worlds/the_real_mccoy/landscape \
  --output  sidequest-content/lora/spaghetti_western/archive/the_real_mccoy_landscape \
  --trigger the_real_mccoy_landscape \
  --kind    landscape \
  --steps   1500 --rank 32 --learning-rate 1e-4 --resolution 768 \
  --caption-dropout 0.1 --save-every 500
```

- [ ] **Step 3: Remap + Verify + Promote**

Follow Step 5 from the updated `/sq-lora` skill verbatim, substituting `{name}=the_real_mccoy_landscape`, `{genre}=spaghetti_western`, `{kind}=landscape`.

- [ ] **Step 4: Wire into `the_real_mccoy/visual_style.yaml`**

```yaml
# genre_packs/spaghetti_western/worlds/the_real_mccoy/visual_style.yaml
loras:
  exclude:
    - spaghetti_western_landscape
  add:
    - name: the_real_mccoy_landscape
      file: lora/spaghetti_western/the_real_mccoy_landscape.safetensors
      scale: 0.85
      applies_to: [landscape, scene]
      trigger: the_real_mccoy_landscape
```

- [ ] **Step 5: Render all 12 the_real_mccoy POIs**

```bash
# After confirming daemon is up and current:
rm -f sidequest-content/genre_packs/spaghetti_western/images/poi/the_*.png \
      sidequest-content/genre_packs/spaghetti_western/images/poi/*monongahela* \
      sidequest-content/genre_packs/spaghetti_western/images/poi/*duquesne* \
      sidequest-content/genre_packs/spaghetti_western/images/poi/*wylie* \
      sidequest-content/genre_packs/spaghetti_western/images/poi/*edgar*
# Then re-run the POI generator
python3 scripts/generate_poi_images.py --genre spaghetti_western 2>&1 | tail -20
```

Expected: the 12 the_real_mccoy POIs render with the Pittsburgh LoRA engaged (OTEL `render.lora.matched_keys` > 0) and visibly different from the dust_and_lead Leone look.

- [ ] **Step 6: Commit**

```bash
cd /Users/keithavery/Projects/oq-2/sidequest-content
git add lora/spaghetti_western/the_real_mccoy_landscape.safetensors \
        genre_packs/spaghetti_western/worlds/the_real_mccoy/visual_style.yaml \
        genre_packs/spaghetti_western/images/poi/
git commit -m "content(lora): the_real_mccoy landscape — validates exclude+add schema"
```

**Phase 5 checkpoint:** two worlds in the same genre render with distinct LoRAs, proving the extend+exclude+add inheritance model works end-to-end. Pipeline is now ready to absorb every other genre.

---

## Plan Self-Review

**Spec coverage check:**

- Architecture (spec §Architecture) — covered by Phase 0-5 collectively ✓
- Dataset Layout (§Dataset Layout) — Task 2.2 creates the first one; convention documented in sq-lora skill update (Task 5.1) ✓
- Training Invocation (§Training Invocation) — Task 2.1 (wrapper) + Task 2.3 (real run) ✓
- Key Remapper (§Key Remapper) — Tasks 1.2-1.5 ✓
- LoRA Storage Layout (§LoRA Storage Layout) — Task 4.5 ✓
- visual_style.yaml Multi-LoRA Schema (§visual_style.yaml Multi-LoRA Schema) — Tasks 4.3, 4.4, 4.6 ✓
- Schema validation (§Schema validation (at visual_style.yaml load)) — covered by `compose_lora_stack` validation in Task 4.3 ✓
- Verification Gate (§Verification Gate) — Tasks 3.1-3.5 ✓
- Runtime — Daemon Changes (§Runtime — Daemon Changes) — Tasks 4.1 (protocol), 4.2 (worker + OTEL), 4.3-4.4 (resolver), 4.7 (end-to-end proof) ✓
- Migration Plan (§Migration Plan) — the entire plan structure IS the migration, phases 0-5 ✓

**Placeholder scan:** no TBD/TODO/FIXME in task bodies. Phase 0's notes doc is a legitimate Phase 1 prerequisite, not a placeholder — it's work product from Phase 0 that Phase 1 consumes.

**Type consistency:**
- `remap_npz_to_safetensors` signature stable across Tasks 1.3, 1.4, 1.5 ✓
- `PreflightError` raised by Task 2.1 and referenced nowhere else (OK) ✓
- `VerifyError` consistent across Tasks 3.1-3.4 ✓
- `ComposeError` consistent in Task 4.3 ✓
- `compose_lora_stack(genre_style, world_style, tier)` signature stable between Task 4.3 (define) and Task 4.4 (call) ✓
- `lora_paths`/`lora_scales` parameter names consistent between `send_render` (Task 4.1) and `_build_lora_model` (Task 4.2) and daemon worker `render` body (Task 4.2) ✓

**Plan is self-consistent and covers the spec.**

---

## References

- Spec: `docs/superpowers/specs/2026-04-20-lora-pipeline-design.md`
- Phase 0 notes (written by Task 0.4): `docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md`
- mflux LoRA key mapping: `sidequest-daemon/.venv/lib/python3.14/site-packages/mflux/models/flux/weights/flux_lora_mapping.py`
- Existing sq-lora skill (pre-rewrite): `.claude/commands/sq-lora.md`
