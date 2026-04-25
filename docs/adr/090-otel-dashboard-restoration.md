---
id: 90
title: "OTEL Dashboard Restoration after Python Port"
status: accepted
date: 2026-04-25
deciders: ["Keith Avery"]
supersedes: []
superseded-by: null
related: [31, 58, 82]
tags: [observability, project-lifecycle]
implementation-status: live
implementation-pointer: null
---

# ADR-090: OTEL Dashboard Restoration after Python Port

## Status

**Accepted** — 2026-04-25.

## Context

After the Rust → Python port (ADR-082), the OTEL dashboard at `/ws/watcher`
and the React `Dashboard/` panes degraded materially. The CLAUDE.md
"OTEL Observability Principle" was no longer enforced: the GM panel — the
"lie detector" Sebastien-the-mechanics-first-player and Keith-the-builder
both depend on — surfaced almost no live signal.

A forensic audit found four failures:

1. The `just otel` recipe pointed at a deleted `playtest.py`.
2. Most `WatcherEventType` values declared in `watcher.ts` had zero or one
   emission sites in production code.
3. ~80% of `SPAN_*` constants in `telemetry/spans.py` were transcribed from
   Rust but never re-implanted into Python dispatch — the catalog was
   aspirational.
4. The translator (`WatcherSpanProcessor.on_end`) flattened every span to
   `agent_span_close` with no semantic typed-event routing.

The Python port copied the **vocabulary** and **transport** but not the
**emission discipline** or the **Layer-3 narrative validator**.

## Decision

Restore the dashboard to ADR-031's three-layer semantic-telemetry contract,
faithfully ported to Python, with three deliberate departures:

1. **`TurnRecord` shape.** Store `snapshot_before_hash + snapshot_after +
   StateDelta` rather than two full `GameSnapshot` clones. Same validation
   power, no double-clone cost.
2. **Validator transport.** `asyncio.Queue(maxsize=32)` with oldest-record
   drop on backpressure (faithful to ADR-031's "lossy by design" intent).
3. **Console exporter gating.** `ConsoleSpanExporter` defaults off; gated
   behind `SIDEQUEST_OTEL_CONSOLE=1` for debug.

The translator gains a routing table (`SPAN_ROUTES`) colocated with span
constants in `spans.py` so renaming a constant breaks the route at import
and a new constant without a routing decision trips the
`test_routing_completeness.py` lint.

A new `Validator` task consumes `TurnRecord`s and runs five deterministic
checks: entity, inventory, patch-legality, trope-alignment,
subsystem-exercise. The validator owns `turn_complete`, `coverage_gap`,
and `validation_warning`.

## Consequences

### Positive

- Every `WatcherEventType` declared in `watcher.ts` has a clear owner;
  no orphans, no double-emission.
- Adding a new span constant requires an explicit routing decision —
  catches the regression that caused this work.
- The "lie detector" property is restored: subsystem activity surfaces
  on the dashboard whether or not the LLM mentions it.
- `just otel` is CI-protected against future script renames.

### Negative

- ~24 emission families still need re-implanting (Phase 2 follow-up
  plans, one per family). The infrastructure now in place makes each
  rollout a small, repeatable change.
- Validator runs on the same event loop as dispatch. Bounded queue +
  lossy drop policy keeps it from impacting hot-path latency, but heavy
  check overhead would still serialize behind dispatch. Acceptable for
  current playtest scale (≤5 watchers, ≤1 turn/sec).

### Out of scope

- No `TurnRecord` persistence / replay.
- No second-LLM validation (ADR-031's "God lifting rocks" prohibition).
- No HTTP OTLP receiver. In-process span processor remains.

## Implementation

See `docs/superpowers/specs/2026-04-25-otel-dashboard-restoration-design.md`
for the design and `docs/superpowers/plans/2026-04-25-otel-dashboard-restoration.md`
for the task plan.

## Related

- ADR-031: Game Watcher — Semantic Telemetry (this ADR ports it to Python)
- ADR-058: Claude subprocess OTEL passthrough (unchanged)
- ADR-082: Port `sidequest-api` from Rust back to Python (this ADR closes one of its drift items)
