"""Tests for scripts.render_common protocol surface.

Task 4.1 covers the send_render signature widening from singleton
(lora_path/lora_scale) to arrays (lora_paths/lora_scales). The old
singleton parameters are removed outright — the daemon is a sidecar
with a small surface; a compat shim would outlast the cutover.
"""
from __future__ import annotations

import inspect

from scripts.render_common import send_render


def test_send_render_accepts_lora_lists() -> None:
    sig = inspect.signature(send_render)
    assert "lora_paths" in sig.parameters
    assert "lora_scales" in sig.parameters


def test_send_render_drops_legacy_singleton_params() -> None:
    """lora_path / lora_scale were removed — clean cutover per ADR-083."""
    sig = inspect.signature(send_render)
    assert "lora_path" not in sig.parameters
    assert "lora_scale" not in sig.parameters


def test_lora_paths_default_is_none() -> None:
    """Absent-LoRA is the common case; default should be optional."""
    sig = inspect.signature(send_render)
    assert sig.parameters["lora_paths"].default is None
    assert sig.parameters["lora_scales"].default is None
