"""Shared fixtures for LoRA pipeline tests.

The `toy_npz_path` and `sample_keymap_path` fixtures are skeletal here.
Once Phase 0 (docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md)
captures the real MLX key names observed in the mlx-examples/flux/ toy
training run, Task 1.4 fills these fixtures with realistic key patterns.
Until then, they remain empty scaffolds and tests that depend on their
contents will be written but skipped or marked xfail.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def toy_npz_path(tmp_path: Path) -> Path:
    """Write a minimal synthetic .npz mimicking mlx-examples output keys.

    Phase 0 observations determine the real key patterns. Until Task 1.4
    updates this fixture, it produces an empty .npz — adequate for testing
    the remapper's "unknown key" and "empty input" paths only.
    """
    path = tmp_path / "toy_adapters.npz"
    data: dict[str, np.ndarray] = {
        # Filled from docs/superpowers/notes/2026-04-20-mlx-examples-flux-notes.md
        # during Task 1.4. Skeleton for Task 1.1.
    }
    np.savez(path, **data)
    return path


@pytest.fixture
def sample_keymap_path(tmp_path: Path) -> Path:
    """Minimal keymap YAML with no rules.

    Used by tests that check the remapper's empty-input / unknown-key
    behaviour. Task 1.4 adds a populated variant alongside this one.
    """
    path = tmp_path / "keymap.yaml"
    path.write_text(
        "version: 1\n"
        "rules: []\n",
        encoding="utf-8",
    )
    return path
