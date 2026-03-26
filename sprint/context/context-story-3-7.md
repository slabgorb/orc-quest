---
parent: context-epic-3.md
---

# Story 3-7: CLI Watcher — Just Watch Tail Mode with Colored Output and Subsystem Heatmap

## Business Context

The Game Watcher pipeline (stories 3-1 through 3-6) produces rich telemetry data and
broadcasts it over a WebSocket endpoint (`/ws/watcher`). But without a viewer, that data
goes nowhere. This story is the quick-win consumer: a terminal-based tail mode that connects
to the watcher WebSocket and renders a live, colored stream of agent decisions per turn.

This is the operator's primary debugging tool during playtesting. Instead of grepping through
logs, the operator runs `just watch` and sees a structured, color-coded view of what happened
on each turn — intent classification, agent invocation, token usage, trope beats, and
validation warnings.

The Python codebase (sq-2) has no equivalent. Debugging there means grepping server logs
for `calling_agent=` lines and mentally reconstructing the turn. Pennyfarthing's `otel-tail.py`
script is the closest prior art — it does colorized OTEL output for coding agent sessions.
This story adapts that pattern for SideQuest's game telemetry.

**Prior art:** `pf-1/scripts/otel-tail.py` (colorized OTEL tail for Pennyfarthing)
**ADR:** ADR-031 (semantic telemetry, watcher WebSocket)
**Depends on:** Story 3-6 (watcher WebSocket endpoint)

## Technical Approach

### Just Recipe

Add a `watch` recipe to the orchestrator justfile:

```just
# Stream live game telemetry to terminal
watch port="8765":
    python3 scripts/watch.py --port {{port}}
```

This follows the existing `just api-run`, `just ui-dev` pattern — orchestrator-level
recipes that coordinate subrepo services.

### WebSocket Client Script

A Python script using `websockets` and `rich` libraries. Python is the right choice here:
fast iteration, `rich` gives us effortless colored/styled terminal output, and the
orchestrator already has Python tooling. A Rust port can happen later if desired.

```python
#!/usr/bin/env python3
"""watch.py — Live telemetry viewer for SideQuest Game Watcher."""

import asyncio
import json
import websockets
from rich.console import Console
from rich.text import Text

console = Console()

async def watch(port: int):
    uri = f"ws://localhost:{port}/ws/watcher"
    async with websockets.connect(uri) as ws:
        async for raw in ws:
            event = json.loads(raw)
            render_event(event)
```

### Turn Separator

Each turn gets a prominent separator line showing turn number, classified intent, selected
agent, and turn duration:

```
═══ Turn 12 | Exploration → narrator | 2.1s ═══════════
```

Rendered via `rich`:

```python
def render_turn_separator(event: dict):
    turn_id = event["turn_id"]
    intent = event["classified_intent"]
    agent = event["agent_name"]
    duration = event["agent_duration_ms"] / 1000
    line = f"═══ Turn {turn_id} | {intent} → {agent} | {duration:.1f}s "
    console.print(line.ljust(60, "═"), style="bold cyan")
```

### Colored Event Lines

Each sub-event within a turn gets a single line, color-coded by type:

| Event Type | Color | Example |
|-----------|-------|---------|
| `intent_router` | blue | `intent_router: "search the old drawer" → Exploration (confidence: 0.85)` |
| `agent.invoke` | white | `agent.invoke: narrator, 847 tok in, 1203 tok out` |
| `json_extractor` | white | `json_extractor: tier 1 (direct parse), WorldStatePatch` |
| `state.apply_patch` | green | `state.apply_patch: quest_log, notes` |
| `trope_engine.tick` | magenta | `trope_engine.tick: suspicion 0.72→0.75, beat "evidence_found" FIRED` |
| Validation pass | green | `✓ patch_legality: all checks passed` |
| Validation warning | yellow | `⚠ entity_ref: "rusty lockbox" not in inventory or room items` |
| Validation error | red | `✗ patch_legality: hp exceeds max_hp for "Grix"` |

```python
SEVERITY_STYLES = {
    "info": "white",
    "pass": "green",
    "warn": "yellow",
    "error": "red",
}

def render_event_line(line: dict):
    severity = line.get("severity", "info")
    style = SEVERITY_STYLES.get(severity, "white")
    prefix = {"pass": "✓", "warn": "⚠", "error": "✗"}.get(severity, " ")
    console.print(f"  {prefix} {line['text']}", style=style)
```

### Subsystem Heatmap

After each turn's events, render a simple horizontal bar chart showing cumulative agent
invocation counts. This reuses the histogram data from story 3-5:

```
─── Subsystem Activity ─────────────────────────────────
  narrator     ████████████ 12
  intent_router████████████ 12
  world_builder████████████ 12
  creature_smith███░░░░░░░░  3
  ensemble     ██░░░░░░░░░  2
  troper       █░░░░░░░░░░  1
  dialectician ░░░░░░░░░░░  0  ⚠ unused
  resonator    ░░░░░░░░░░░  0  ⚠ unused
```

```python
BAR_WIDTH = 11

def render_heatmap(histogram: dict[str, int]):
    console.print("─── Subsystem Activity " + "─" * 37, style="dim")
    max_count = max(histogram.values()) if histogram else 1
    for name, count in sorted(histogram.items(), key=lambda x: -x[1]):
        filled = round(count / max_count * BAR_WIDTH) if max_count > 0 else 0
        empty = BAR_WIDTH - filled
        bar = "█" * filled + "░" * empty
        label = f"  {name:<14}{bar} {count:>3}"
        if count == 0:
            console.print(f"{label}  ⚠ unused", style="yellow")
        else:
            console.print(label)
```

### Event Format Assumption

The watcher WebSocket (story 3-6) broadcasts JSON events. This script expects a structure
like:

```json
{
    "type": "turn_complete",
    "turn_id": 12,
    "classified_intent": "Exploration",
    "agent_name": "narrator",
    "agent_duration_ms": 2100,
    "events": [
        { "kind": "intent_router", "text": "...", "severity": "info" },
        { "kind": "validation", "text": "...", "severity": "warn" }
    ],
    "histogram": {
        "narrator": 12,
        "creature_smith": 3
    }
}
```

The exact schema is defined by story 3-6. This script adapts to whatever 3-6 produces —
the rendering logic is intentionally loose, not rigidly typed.

### Dependencies

Python dependencies are minimal and not worth a full virtualenv:

```bash
pip install websockets rich
```

If the orchestrator gains a `pyproject.toml` later, these can be pinned there. For now,
the script is self-contained with two well-known packages.

## Scope Boundaries

**In scope:**
- `just watch` recipe in orchestrator justfile
- Python script (`scripts/watch.py`) connecting to `/ws/watcher` WebSocket
- Colored terminal output via `rich` library
- Turn separator lines with turn number, intent, agent, duration
- Per-event lines with severity-based coloring (green/yellow/red)
- Subsystem heatmap bar chart refreshed each turn
- `--port` argument for non-default API port

**Out of scope:**
- Interactive features (scrollback, filtering, search)
- TUI framework (curses, Textual) — this is a tail-mode viewer, not an interactive app
- Persistence or log export
- Configuration file for colors or layout
- Rust implementation (Python is the right choice for fast iteration)
- GM Mode panel in the React UI (story 3-9)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Just recipe | `just watch` connects to the watcher WebSocket and streams output |
| Turn separators | Each turn is delimited by a visible separator with turn number, intent, agent, and duration |
| Color coding | Normal spans are green/white, warnings are yellow, errors are red |
| Event lines | Each sub-event within a turn renders as a single indented line |
| Subsystem heatmap | A bar chart of agent invocation counts renders after each turn |
| Unused agents | Agents with zero invocations are flagged with a warning marker |
| Port configurable | `just watch port=9999` connects to a non-default port |
| Graceful disconnect | Script exits cleanly with a message if the WebSocket closes |
| Minimal dependencies | Only `websockets` and `rich` Python packages required |
