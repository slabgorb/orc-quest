---
parent: context-epic-12.md
---

# Story 12-3: Variation Telemetry in Watcher — See Which Score Cue Was Chosen and Why

## Business Context

Stories 12-1 and 12-2 completed the cinematic audio pipeline:
- **12-1:** MusicDirector now selects the right variation type (Overture, Ambient, Sparse, Full, TensionBuild, Resolution) based on narrative context
- **12-2:** Each variation type has its own crossfade duration (e.g., Overture 5000ms, TensionBuild 1000ms) configured in the genre pack

The OTEL telemetry in `music_evaluate` span already includes two fields:
- `variation` — which variation type was selected
- `variation_reason` — why that variation was chosen

However, the watcher events (displayed in the GM panel) may not fully surface this telemetry:
1. `fade_duration_ms` may not be recorded on the OTEL span (found by rule-checker in 12-2)
2. `fade_duration_ms` not included in watcher event payload
3. Variation data potentially not visible in suppressed-cue watcher events (path where mood unchanged)

This story ensures the watcher sees the full picture: which variation was selected, why, and how long the fade will be.

**Depends on:** Story 12-1 (variation selection) and 12-2 (fade_duration_ms). Both are complete.

## Technical Approach

### 1. Verify OTEL Span Includes fade_duration_ms

In `dispatch/audio.rs`, the `music_evaluate` span should include a `fade_duration_ms` attribute
after `MusicDirector::evaluate()` completes. If missing, add it:

```rust
span.add_event("music_evaluate", vec![
    KeyValue::new("mood", mood.clone()),
    KeyValue::new("intensity", mood_classification.intensity as f64),
    KeyValue::new("variation", format!("{:?}", audio_cue.action)),
    KeyValue::new("variation_reason", derive_reason(&mood_context, &mood_classification)),
    KeyValue::new("fade_duration_ms", audio_cue.fade_duration_ms.unwrap_or(3000) as i64),
    // ... other fields
]);
```

**Rationale:** The fade_duration is now part of the `AudioCue` (from 12-2), so it's
immediately available after `evaluate()` returns.

### 2. Ensure Watcher Event Includes Variation + Fade

The watcher event handler in `dispatch/audio.rs` (post_telemetry) creates an `AgentSpanClose`
that feeds telemetry to the GM panel. Verify the event includes:
- `variation` field from span context
- `variation_reason` field from span context
- `fade_duration_ms` from span event

If any are missing, add them to the event payload.

### 3. Handle Suppressed-Cue Watcher Events

When a mood hasn't changed (or the track already playing matches), the music evaluation may
emit a "suppressed" or "no change" event instead of a full `AgentSpanClose`. Ensure
suppressed-cue events still include variation telemetry (or explicitly log "no change").

## Key Architectural Notes

- **No silent fallbacks:** If `fade_duration_ms` is missing from `AudioCue`, use the explicit
  default `3000` and log it (not a silent fallback to client defaults).
- **Span attributes:** OTEL attributes are immutable once added; verify they're added in the
  right phase (after `evaluate()` populates the cue).
- **Watcher shape:** The GM panel expects structured JSON. Check that `variation` and
  `fade_duration_ms` are serialized correctly (string and number, respectively).
- **No double-logging:** If variation is already logged elsewhere in the cue, don't re-emit it.

## Scope Boundaries

**In scope:**
- OTEL span attribute: `fade_duration_ms` on `music_evaluate` event
- Watcher event: includes `variation`, `variation_reason`, `fade_duration_ms`
- Suppressed-cue events: variation telemetry visible (or explicit no-change log)
- Backward compat: genre packs without `crossfade_by_variation` use default 3000ms

**Out of scope:**
- Client-side UI changes (GM panel display — separate story)
- Changing variation selection logic (12-1 scope)
- Changing crossfade durations (12-2 scope)
- New genre pack content updates

## Acceptance Criteria

| AC | Detail |
|----|--------|
| OTEL span updated | `music_evaluate` event includes `fade_duration_ms` attribute |
| Watcher event populated | `AgentSpanClose` includes `variation`, `variation_reason`, `fade_duration_ms` in payload |
| Suppressed events handled | No-change/suppressed-cue events include variation telemetry or explicit log |
| Backward compat | Genre packs without crossfade_by_variation default to 3000ms and log it |
| No silent fallbacks | All fallbacks to default fade duration are traced/logged |
| Tests verify wiring | Integration test: variation selection + fade duration visible in OTEL/watcher event |
