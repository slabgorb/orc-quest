"""Tests for scripts.render_common protocol surface.

Task 4.1 covers the send_render signature widening from singleton
(lora_path/lora_scale) to arrays (lora_paths/lora_scales). The old
singleton parameters are removed outright — the daemon is a sidecar
with a small surface; a compat shim would outlast the cutover.

Task 4.3 covers compose_lora_stack — the pure resolver that merges
genre+world LoRA blocks into the effective per-render stack. Lives
in render_common per Architect correction #5 (not a separate module).
"""
from __future__ import annotations

import inspect

import pytest

from scripts.render_common import ComposeError, compose_lora_stack, send_render


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


# ─── Task 4.3: compose_lora_stack ─────────────────────────────────────


GENRE = {
    "loras": [
        {"name": "sw_landscape", "file": "p1.safetensors", "scale": 0.8,
         "applies_to": ["landscape", "scene"], "trigger": "sw_landscape"},
        {"name": "sw_portrait", "file": "p2.safetensors", "scale": 0.8,
         "applies_to": ["portrait"], "trigger": "sw_portrait"},
    ]
}


def test_no_world_overrides_inherits_genre() -> None:
    """Empty world style → genre LoRAs flow through, filtered by tier."""
    resolved = compose_lora_stack(GENRE, {}, tier="landscape")
    assert [e["name"] for e in resolved] == ["sw_landscape"]


def test_world_exclude_drops_inherited() -> None:
    """world.loras.exclude removes a genre entry by name before tier filter."""
    world = {"loras": {"exclude": ["sw_landscape"]}}
    resolved = compose_lora_stack(GENRE, world, tier="landscape")
    assert resolved == []


def test_world_add_appends_after_genre() -> None:
    """world.loras.add appends new entries; order is genre-first then add-order."""
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


def test_tier_filter_skips_non_matching_applies_to() -> None:
    """An entry with applies_to=[portrait] does not fire on a landscape render."""
    resolved = compose_lora_stack(GENRE, {}, tier="portrait")
    assert [e["name"] for e in resolved] == ["sw_portrait"]


def test_world_add_with_inherited_name_raises() -> None:
    """Reusing a genre name in world.add without exclude is ambiguous → fail loud."""
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


def test_empty_applies_to_fails_validation() -> None:
    """An entry that fires on no tier is always misconfiguration → fail loud."""
    bad_genre = {
        "loras": [
            {"name": "x", "file": "x.safetensors", "scale": 1.0, "applies_to": []},
        ]
    }
    with pytest.raises(ComposeError, match="applies_to"):
        compose_lora_stack(bad_genre, {}, tier="landscape")


def test_legacy_list_form_world_loras_raises() -> None:
    """A v1-schema world file (list `loras:`) is unsafe to silently inherit."""
    world = {
        "loras": [
            {"name": "x", "file": "x.safetensors", "scale": 1.0,
             "applies_to": ["landscape"]}
        ]
    }
    with pytest.raises(ComposeError, match="legacy list-form"):
        compose_lora_stack(GENRE, world, tier="landscape")
