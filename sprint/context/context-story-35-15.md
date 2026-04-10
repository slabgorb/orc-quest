---
parent: context-epic-35.md
---

# Story 35-15: Wire LoRA path from visual_style.yaml through render pipeline to daemon

## Business Context

SideQuest's visual identity is carried by genre-specific Flux image generation.
A generic Flux render of "a shootout in a dusty street" produces generic digital art.
A Flux render with a **trained spaghetti-western LoRA** produces a visual that
*feels* like the genre — grain, palette, cinematography, the whole semiotic stack.
Per ADR-032, genre LoRAs are trained on ~20-50 curated images per genre and are the
authoritative mechanism for consistent visual style across an entire campaign.

**Story 27-5 (merged 2026-04-09)** wired the daemon side: `FluxMLXWorker` now
accepts `lora_path` and `lora_scale` in render params and constructs the Flux1
model with LoRA weights baked in. The wiring is proven by mocked tests in
`sidequest-daemon/tests/test_lora_loading_story_27_5.py`.

**35-15 wires the Rust API side.** The daemon is waiting for a `lora_path` field
in the render request JSON, and today's Rust pipeline never sends one. Every render
goes out with base Flux weights regardless of what the genre pack's
`visual_style.yaml` declares. This is the exact "half-wired feature" pattern Epic 35
exists to close — the receiving end is fully built, the sending end never calls it.

**User-facing impact:** When complete, spaghetti_western renders will look like
spaghetti westerns, caverns_and_claudes renders will carry their Flux-trained
cartoon-dungeon aesthetic, and the GM panel will be able to verify the LoRA is
actually being applied (not just claimed in narration). Narrative consistency is
the #1 project value (see memory `project_narrative_consistency.md`); mechanical
visual state must back the story.

## Technical Guardrails

### Spec authority for this story

Per the spec hierarchy: **ADR-032 (genre LoRA style training) is the highest
authority** for this story after the session scope. Two facts in the session file's
Story Context section are wrong per ADR-032 and must be overridden:

| Topic | Session file says | ADR-032 (authoritative) says |
|---|---|---|
| Field name | `trigger_word` | `lora_trigger` |
| Auto-prepending | "Trigger word gets prepended to the positive prompt automatically" | Rust-side `PromptComposer` substitutes `lora_trigger` for `positive_suffix` in the CLIP prompt when LoRA is active. **Daemon does NOT auto-prepend.** |
| LoRA file location | "Draw Things models dir" | `{genre_pack_dir}/lora/*.safetensors` (genre pack relative) |

These three corrections are logged as Design Deviations in the session file.

### Code sites (verified against current code — line numbers updated)

| # | File | Verified location | Change |
|---|---|---|---|
| 1 | `sidequest-api/crates/sidequest-genre/src/models/character.rs` | `VisualStyle` struct at **line 235** (session file says 142 — stale) | Add `lora: Option<String>` and `lora_trigger: Option<String>`, both with `#[serde(default)]`. No `deny_unknown_fields` on this struct — safe to extend. |
| 2 | `sidequest-api/crates/sidequest-game/src/render_queue.rs` | `RenderJob` struct at **line 270**, `enqueue()` at **line 405**, `spawn()` closure signature at **line 305-307** | Add `lora_path: Option<String>` and `lora_scale: Option<f32>` to `RenderJob`. Extend `enqueue()` signature to accept them. **The `render_fn` closure currently takes 7 positional String/u32 args — see "Architectural smell" below.** |
| 3 | `sidequest-api/crates/sidequest-daemon-client/src/types.rs` | `RenderParams` at **line 22** | Add `lora_path: Option<String>` and `lora_scale: Option<f32>`, both with `#[serde(default, skip_serializing_if = "Option::is_none")]`. The daemon already reads these from the JSON. |
| 4 | `sidequest-api/crates/sidequest-server/src/dispatch/render.rs` | `process_render()` 3-tuple extraction at **line 110-138** | Expand from `(art_style, model, neg_prompt)` to `(art_style, model, neg_prompt, lora_path, lora_trigger)`. When `lora_trigger` is set, substitute it for `positive_suffix` in the prompt composition at line 124, per ADR-032. Pass `lora_path` through to `enqueue()`. |
| 5 | `sidequest-content/genre_packs/spaghetti_western/visual_style.yaml` and `sidequest-content/genre_packs/caverns_and_claudes/visual_style.yaml` | Existing files, verified | Add `lora:` and `lora_trigger:` fields. **WARNING: No actual `.safetensors` files exist in `sidequest-content` yet.** See "AC-3 reality check" below. |

### Daemon side — already wired (story 27-5)

Verified in `sidequest-daemon/sidequest_daemon/media/workers/flux_mlx_worker.py`:

- **Lines 121-139**: `_build_lora_model(variant, lora_path, lora_scale)` constructs
  a `Flux1(model_config=..., lora_paths=[lora_path], lora_scales=[lora_scale])`.
- **Lines 155-156**: `lora_path = params.get("lora_path")`,
  `lora_scale = params.get("lora_scale", 1.0)`. Default scale is **1.0**.
- **Lines 164-171**: If `lora_path` is truthy, emits
  `span.set_attribute("render.lora_path", lora_path)` and
  `span.set_attribute("render.lora_scale", lora_scale)`, then calls
  `_build_lora_model(variant, lora_path, lora_scale)`.
- **Lines 172-174**: If no `lora_path`, falls through to `_ensure_variant(variant)`
  (base Flux rendering — no regression for non-LoRA genres).
- **Missing file handling**: `Flux1()` raises on missing `lora_path` (loud failure
  per no-silent-fallbacks rule), proven by
  `tests/test_lora_loading_story_27_5.py::TestLoRAErrorHandling`.

**Do not modify the daemon.** 35-15 is Rust-only plus YAML content additions.

### OTEL requirement

Per CLAUDE.md's OTEL Observability Principle, the GM panel is the lie detector.
The daemon already emits `render.lora_path` / `render.lora_scale` span attributes
on the subprocess span, but **daemon spans do not surface to the watcher
WebSocket** — only Rust-side `WatcherEvent`s do.

**Rust-side watcher emission required** at `dispatch/render.rs` immediately before
`queue.enqueue()` when `lora_path.is_some()`:

```rust
crate::WatcherEventBuilder::new("render", crate::WatcherEventType::SubsystemExerciseSummary)
    .field("action", "lora_activated")
    .field("lora_path", lora_path_str)
    .field("lora_trigger", lora_trigger_str)
    .field("genre", genre_slug)
    .send();
```

This gives the GM panel direct visibility: "I can see that for this render, LoRA
was activated, with this path and trigger, from this genre." Without it, Claude
could happily generate a convincing "spaghetti western" render description while
the pipeline silently rendered vanilla Flux — and no one would catch it.

### Architectural smell — log, don't fix

The `RenderQueue::spawn<F, Fut>` closure signature at `render_queue.rs:305-307`:

```rust
F: Fn(String, String, String, String, String, u32, u32) -> Fut + Send + 'static,
```

7 positional `String`/`u32` arguments. The architecturally correct shape is a
`RenderParams` struct passed by value. Adding `lora_path` + `lora_scale` brings
the positional signature to **9 arguments**, which is worse.

**For 35-15**: extend the positional signature (2 more args). Log the smell as a
Delivery Finding (Improvement, non-blocking) so a future cleanup story can
refactor to a struct. Epic 35's charter is *wire it, don't refactor it*. Don't
bloat this story's scope.

### Pre-existing silent fallback — log, don't fix

`dispatch/render.rs:133-137`:

```rust
None => (
    "oil_painting".to_string(),
    "flux-schnell".to_string(),
    String::new(),
),
```

When `ctx.visual_style` is `None`, the dispatch layer silently defaults to
`"oil_painting"` style and `"flux-schnell"` model. This violates the
**No Silent Fallbacks** rule — a missing visual_style should fail loudly, not
render with an arbitrary default.

**For 35-15**: do not fix this. It is out of scope. Log as a Delivery Finding
(Gap, non-blocking) so a future story can close it. The new LoRA fields will not
be set in the fallback branch (they'll be `None`), which is correct — but the
fallback itself is an independent bug.

### The LoRA path resolution problem

`visual_style.yaml` will contain something like:

```yaml
lora: lora/spaghetti_western_style.safetensors
lora_trigger: sw_style
```

The daemon needs an **absolute path**. Per ADR-032 architecture, the Rust dispatch
layer is responsible for resolving the relative path against the genre pack directory:

```rust
let lora_abs = genre_pack_dir.join(&visual_style.lora);
```

The genre pack dir is already available via `sidequest-genre`'s loader — check
`ctx.genre_pack` in the dispatch context for the existing access pattern.

**Do not ship an absolute path in the YAML.** It must be relative to the genre
pack dir so the content can move between machines (Keith's M3 Max → future cloud
deploy).

## Scope Boundaries

### In scope

- `VisualStyle` struct extension (2 optional fields)
- `RenderJob` + `enqueue()` signature extension
- `RenderParams` JSON serialization (optional fields with skip_serializing_if)
- `dispatch/render.rs` reads LoRA config, resolves absolute path, passes to
  `enqueue()`, substitutes `lora_trigger` for `positive_suffix` when active
- Rust-side `WatcherEvent` emission when LoRA is activated
- Adding `lora` + `lora_trigger` fields to `spaghetti_western` and
  `caverns_and_claudes` `visual_style.yaml` — values may point at non-existent
  `.safetensors` paths (see AC-3 reality check)
- Integration test in `sidequest-api` proving the wire path end-to-end (non-LoRA
  genre renders normally; LoRA genre's request JSON contains `lora_path`)
- TEA's negative test **first**: no `lora` field → no `lora_path` attribute →
  base render succeeds (AC-5 guardrail)

### Out of scope

- **Training actual LoRA files** — that's a separate epic (see Epic 32). The
  `.safetensors` files may not exist when this story ships; AC-3 is scoped to
  *wiring verification*, not end-to-end generation verification.
- **Refactoring `render_fn` closure to a struct** — architectural smell logged
  as Delivery Finding for a future story.
- **Closing the pre-existing silent fallback** at `dispatch/render.rs:133-137` —
  out of scope, logged as Delivery Finding.
- **LoRA file format validation** — the daemon raises `FileNotFoundError`
  loudly (proven by story 27-5); Rust side does not pre-validate.
- **Multiple LoRAs per render** — the mflux `Flux1` constructor accepts
  `lora_paths=[...]` as a list, but this story supports exactly one LoRA per
  render. Multi-LoRA composition is future work.
- **Daemon-side changes** — 35-15 is Rust + YAML only. Do not touch
  `sidequest-daemon`.

## AC Context

### AC-1: `visual_style.yaml` with lora field is parsed without error

- **Why it matters**: Adding fields to a deserialized struct must not break
  existing genre packs that omit the new fields. Both `lora` and `lora_trigger`
  must be `Option<String>` with `#[serde(default)]`.
- **Verification**: Test that loads `spaghetti_western/visual_style.yaml` (with
  new fields) and a fixture without new fields — both must parse successfully.
- **Watch out for**: `VisualStyle` does NOT have `#[serde(deny_unknown_fields)]`
  today (verified — only `EquipmentTables` at line 217 does). Safe to add.

### AC-2: render request to daemon includes `lora_path` when visual_style has lora

- **Why it matters**: This is the core wire. The JSON serialization must include
  `lora_path` as a top-level field the daemon reads at
  `flux_mlx_worker.py:155`.
- **Verification**: Integration test at the `sidequest-daemon-client` layer —
  build a `RenderParams` with `lora_path: Some("...")`, serialize to JSON, assert
  the resulting string contains `"lora_path":"..."`. Combine with a dispatch-
  layer test that proves `dispatch/render.rs` sets the field when
  `visual_style.lora` is present.
- **Watch out for**: `#[serde(skip_serializing_if = "Option::is_none")]` on
  `RenderParams.lora_path` so non-LoRA renders don't include the field at all
  (not just `"lora_path":null`). The daemon uses `params.get("lora_path")` which
  handles both cases, but the tests should verify both behaviors.

### AC-3: FluxMLXWorker loads LoRA and generates with it

**AC-3 reality check:** **Zero `.safetensors` files exist in `sidequest-content`
today.** `git ls-files` in the content repo returns nothing matching `*.safetensors`
or `lora*`. This means AC-3 cannot be verified with an actual trained LoRA in an
automated test as part of this story.

**Resolution:** AC-3 is **already satisfied** by story 27-5's test suite
(`test_lora_loading_story_27_5.py`), which proves FluxMLXWorker correctly
constructs `Flux1(lora_paths=[...], lora_scales=[...])` when given a
`lora_path` param. 35-15's job is to prove the Rust API *sends* the param.

For 35-15's wiring verification:
- Use a sentinel path like `/tmp/test-lora.safetensors` in integration tests
- The Rust side doesn't need to pre-validate the file — let the daemon fail
  loudly if the file is missing (per no-silent-fallbacks)
- Manual end-to-end verification with a real LoRA is deferred until a
  `.safetensors` file exists in the content repo (Epic 32 or manual training)

### AC-4: OTEL span shows lora_path attribute on render

- **Why it matters**: The GM panel is the lie detector. The Rust-side
  `WatcherEvent` is what surfaces to the watcher WebSocket — daemon spans don't.
- **Verification**: Integration test that subscribes to the watcher event stream,
  triggers a dispatch/render with LoRA set, and asserts the stream contains a
  `render` event with `action=lora_activated` and a non-empty `lora_path` field.
- **Watch out for**: `WatcherEventBuilder::send()` is fire-and-forget. The test
  must subscribe before triggering the dispatch, not after.

### AC-5: genres without LoRA continue to render normally (no regression)

- **Why it matters**: Most genres don't have trained LoRAs. Silent breakage
  there would affect every current playtest. This is the **load-bearing
  regression guardrail** — per SM assessment, TEA writes this test FIRST.
- **Verification**: Test renders a genre whose `visual_style.yaml` has no `lora`
  field. Assert:
  1. Render succeeds (no error)
  2. The JSON sent to the daemon does NOT contain `lora_path` (not just null)
  3. No `lora_activated` `WatcherEvent` is emitted
  4. Existing render behavior is byte-identical to pre-35-15 behavior for the
     no-LoRA path
- **Watch out for**: Tests that only assert "no error" are vacuous. The
  assertion must include the absence of the `lora_path` field in the serialized
  request, which is the mechanically testable version of "non-LoRA genres still
  work the same way."

## Interaction Patterns

### Dispatch → RenderQueue → DaemonClient → Daemon

```
dispatch/render.rs::process_render()
    reads ctx.visual_style                                          [existing]
    resolves visual_style.lora relative path → absolute             [new]
    substitutes visual_style.lora_trigger for positive_suffix       [new, per ADR-032]
    emits WatcherEvent("render", SubsystemExerciseSummary)          [new]
    calls queue.enqueue(subject, art_style, model, neg_prompt,
                        narration, lora_path, lora_scale)           [extended]
  ↓
RenderQueue::enqueue()
    builds RenderJob { ..., lora_path, lora_scale }                 [extended]
    sends to worker via job_tx channel
  ↓
render_fn closure (defined at AppState wiring site)
    receives lora_path, lora_scale positional args                  [extended, +2 args]
    calls DaemonClient::render(RenderParams { ..., lora_path })     [extended]
  ↓
DaemonClient::render()
    serializes RenderParams to JSON over Unix socket
    "lora_path":"/abs/path/style.safetensors" included only if Some [serde magic]
  ↓
sidequest-daemon flux_mlx_worker.py:155
    params.get("lora_path") → constructs Flux1 with LoRA            [already wired]
    emits span.set_attribute("render.lora_path", ...)               [already wired]
    renders with LoRA weights active
```

### Wiring test

Must verify the full chain as a single test, not just unit tests at each layer.
Per CLAUDE.md's "Every Test Suite Needs a Wiring Test" rule:

- Spin up the dispatch context with a genre whose `visual_style.yaml` has the
  new fields (use a test fixture genre pack, not production content).
- Call `process_render()`.
- Assert the `RenderQueue` received a `RenderJob` with `lora_path: Some(_)`.
- Assert a `WatcherEvent` with `action=lora_activated` was emitted.
- Assert the `RenderParams` JSON that would be sent to the daemon contains
  `"lora_path"`.

This is the "new code has non-test consumers" check — prove the wire is reachable
from the dispatch path, not just from a unit test fixture.

## Assumptions

- **Story 27-5 daemon wiring is stable.** FluxMLXWorker's LoRA constructor path
  is proven by its own test suite; 35-15 does not need to re-test it.
- **No `.safetensors` files will be trained as part of this story.** Training is
  Epic 32 scope; 35-15 ships the wire and uses sentinel paths in tests.
- **The genre pack directory is accessible from the dispatch context.** If it
  isn't, that's a Dev surprise — flag it as a blocking Delivery Finding and
  escalate.
- **`lora_scale` defaults to 1.0** on both sides (daemon already does at
  `flux_mlx_worker.py:156`; Rust `RenderParams.lora_scale` is `Option<f32>` with
  `None` meaning "let the daemon default it").
- **ADR-032 is the highest authority for field names and composition semantics.**
  The session file's story description is wrong in two places (documented
  above); ADR-032 wins per the spec authority hierarchy.
