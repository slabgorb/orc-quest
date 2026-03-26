---
parent: context-epic-3.md
---

# Story 3-9: GM Mode Panel — React Debug Overlay Showing Telemetry Alongside Game UI

## Business Context

The CLI watcher (story 3-7) gives the operator a terminal view of game telemetry. GM Mode
brings that same data into the React game client as an integrated debug overlay. During
playtesting, the operator can toggle a collapsible panel that shows telemetry events, game
state, subsystem activity, and trope progress alongside the running game — no need to
switch between terminal windows.

This is the most ambitious story in Epic 3, and it is p2 because the CLI watcher already
provides the essential observability functionality. GM Mode adds polish, integrated UX, and
visual richness. It is also the most natural way for a non-terminal-savvy observer (e.g.,
a genre pack author or playtester) to understand what the AI is doing.

The Python codebase (sq-2) has no equivalent. Pennyfarthing's BikeRack TUI panels show
similar telemetry data for coding agents — horizontal progress bars, event streams,
invocation counts. The React version is richer but serves the same purpose: making AI
decisions visible to humans.

**Prior art:** Pennyfarthing BikeRack TUI (pf-1)
**ADR:** ADR-031 (semantic telemetry, watcher WebSocket)
**Depends on:** Story 3-6 (watcher WebSocket endpoint), Story 2-9 (end-to-end UI integration)

## Technical Approach

### Component Architecture

A single top-level component, lazy-loaded and code-split so it has zero bundle impact when
not active:

```tsx
// src/components/GMMode/index.tsx
const GMMode = React.lazy(() => import('./GMMode'));

// In App.tsx or GameScreen
{gmModeEnabled && (
    <Suspense fallback={null}>
        <GMMode port={apiPort} />
    </Suspense>
)}
```

### Toggle Mechanism

Two activation methods:

1. **Keyboard shortcut:** `Ctrl+Shift+G` toggles the panel
2. **URL parameter:** `?gm=true` opens with GM Mode active

```tsx
function useGMMode(): [boolean, () => void] {
    const [enabled, setEnabled] = useState(() => {
        const params = new URLSearchParams(window.location.search);
        return params.get('gm') === 'true';
    });

    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'G') {
                setEnabled(prev => !prev);
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, []);

    return [enabled, () => setEnabled(prev => !prev)];
}
```

### WebSocket Connection

GM Mode connects to a separate WebSocket (`/ws/watcher`) from the game's main WebSocket
(`/ws`). This ensures telemetry traffic does not interfere with game message flow:

```tsx
function useWatcherSocket(port: number, enabled: boolean) {
    const [events, dispatch] = useReducer(watcherReducer, initialState);

    useEffect(() => {
        if (!enabled) return;

        const ws = new WebSocket(`ws://localhost:${port}/ws/watcher`);
        ws.onmessage = (e) => {
            const event = JSON.parse(e.data);
            dispatch({ type: 'EVENT_RECEIVED', payload: event });
        };
        ws.onclose = () => dispatch({ type: 'DISCONNECTED' });

        return () => ws.close();
    }, [port, enabled]);

    return events;
}
```

### Panel Layout

GM Mode renders as a collapsible side panel (or bottom panel, togglable) with five sections:

```
┌─────────────────────────────────────────────────────────┐
│ GM Mode                                    [_] [Layout] │
├─────────────────────────────────────────────────────────┤
│ ▼ Event Stream                                          │
│   ═══ Turn 12 | Exploration → narrator | 2.1s ══════   │
│     intent_router: "search drawer" → Exploration        │
│     agent.invoke: narrator, 847→1203 tok                │
│     ✓ patch_legality: passed                            │
│     ⚠ entity_ref: "rusty lockbox" not found             │
├─────────────────────────────────────────────────────────┤
│ ▼ Subsystem Activity                                    │
│   narrator      ████████████ 12                         │
│   intent_router ████████████ 12                         │
│   creature_smith███░░░░░░░░  3                          │
│   ensemble      ██░░░░░░░░░  2                          │
│   dialectician  ░░░░░░░░░░░  0 ⚠                       │
├─────────────────────────────────────────────────────────┤
│ ▼ Trope Timeline                                        │
│   suspicion    ████████████████████░░░░░ 0.75  ◆ beat   │
│   forbidden_love████████░░░░░░░░░░░░░░░ 0.33           │
│   prophecy     ██████████████████████░░░ 0.88  ◆ beat   │
├─────────────────────────────────────────────────────────┤
│ ▼ Game State Inspector                                  │
│   ▶ characters (3)                                      │
│   ▶ quest_log (2 active)                                │
│   ▶ location: "The Rusted Saloon"                       │
│   ▶ combat: null                                        │
├─────────────────────────────────────────────────────────┤
│ ▼ Validation Alerts (2)                                 │
│   ⚠ entity_ref: "rusty lockbox" not in room — Turn 12  │
│   ⚠ trope_alignment: "suspicion" beat missed — Turn 11  │
└─────────────────────────────────────────────────────────┘
```

### Panel Sections

**1. Event Stream** — Scrolling list of telemetry events per turn. Same data as the CLI
watcher, rendered as styled React components. Auto-scrolls to latest turn. Each event line
is color-coded by severity (green/yellow/red).

**2. Subsystem Activity** — Horizontal bar chart of cumulative agent invocation counts.
Uses the histogram data from story 3-5. Agents with zero invocations get a warning badge.

**3. Trope Timeline** — Horizontal progress bars for each active trope, showing current
lifecycle position (ADR-018: DORMANT 0.0, ACTIVE, PROGRESSING, RESOLVED 1.0). Diamond
marker on beats that have fired. Color shifts as progress advances (cool blue for early,
warm orange near resolution).

**4. Game State Inspector** — Collapsible tree view of the current `GameSnapshot` fields.
Characters, quest log, location, combat state, inventory. Uses a generic JSON tree component
since the shape of GameSnapshot is complex.

**5. Validation Alerts** — Filtered view showing only warning and error results from all
validation checks (patch legality, entity refs, trope alignment). Includes turn number
for reference. Alerts persist until dismissed or a new session starts.

### State Management

Local state only — `useState` and `useReducer` within the GMMode component tree. This is a
debug overlay, not part of the game's state management. No global store, no context provider
pollution:

```tsx
interface WatcherState {
    connected: boolean;
    turns: TurnEvent[];
    histogram: Record<string, number>;
    tropes: TropeStatus[];
    alerts: ValidationAlert[];
    latestSnapshot: GameSnapshot | null;
}

type WatcherAction =
    | { type: 'EVENT_RECEIVED'; payload: WatcherEvent }
    | { type: 'DISCONNECTED' }
    | { type: 'CLEAR_ALERTS' };

function watcherReducer(state: WatcherState, action: WatcherAction): WatcherState {
    switch (action.type) {
        case 'EVENT_RECEIVED':
            return processEvent(state, action.payload);
        case 'DISCONNECTED':
            return { ...state, connected: false };
        case 'CLEAR_ALERTS':
            return { ...state, alerts: [] };
    }
}
```

### Performance Considerations

GM Mode must not degrade game performance when hidden:

- **Lazy loading:** Component is code-split via `React.lazy`. When GM Mode is off, none of
  its code is loaded or parsed.
- **WebSocket lifecycle:** The watcher WebSocket only connects when GM Mode is toggled on.
  When toggled off, the connection closes. No background traffic.
- **Event buffer:** Keep only the last 100 turns in memory. Older turns are discarded to
  prevent memory growth during long sessions.
- **Render throttling:** Subsystem bars and trope timeline re-render at most once per second,
  not on every WebSocket message. Event stream appends immediately.

### Existing UI Patterns

The game client already has panel-based UI for combat, inventory, and map. GM Mode follows
the same patterns:

- Collapsible section headers (click to expand/collapse)
- Consistent color palette from the game's theme
- Responsive layout (panel collapses to an icon on narrow viewports)
- The game already uses WebSocket connections — adding a second one for `/ws/watcher`
  follows established patterns in the codebase

### Package Location

Keep GM Mode in `sidequest-ui` behind a lazy import. It is a dev tool that ships with the
client but only activates on demand. A separate package would add build complexity for no
benefit — the lazy loading already ensures zero cost when inactive.

```
sidequest-ui/src/components/GMMode/
├── index.tsx           # Lazy export
├── GMMode.tsx          # Main component
├── EventStream.tsx     # Turn event list
├── SubsystemBars.tsx   # Agent invocation histogram
├── TropeTimeline.tsx   # Trope progress bars
├── StateInspector.tsx  # GameSnapshot tree view
├── AlertList.tsx       # Validation warnings
├── useWatcherSocket.ts # WebSocket hook
└── types.ts            # WatcherState, WatcherEvent, etc.
```

## Scope Boundaries

**In scope:**
- `<GMMode />` React component with lazy loading and code splitting
- WebSocket connection to `/ws/watcher` (separate from game WebSocket)
- Toggle via `Ctrl+Shift+G` keyboard shortcut and `?gm=true` URL parameter
- Event Stream panel: scrolling, color-coded telemetry events per turn
- Subsystem Activity panel: horizontal bar chart of agent invocations
- Trope Timeline panel: progress bars with beat markers per active trope
- Game State Inspector panel: collapsible tree view of GameSnapshot
- Validation Alerts panel: filtered warning/error list with turn references
- Local state management (useState/useReducer, no global store)
- Event buffer limited to 100 turns for memory safety
- Zero performance impact when GM Mode is hidden

**Out of scope:**
- Session replay (viewing past sessions — deferred)
- SQLite query interface (querying persisted telemetry data)
- Export or share functionality (saving telemetry snapshots)
- Editing game state from the panel (read-only observation)
- Custom theming or layout persistence
- Mobile layout optimization (this is a desktop dev tool)
- Automated testing of the GM Mode component (standard React testing applies)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Toggle works | `Ctrl+Shift+G` toggles GM Mode panel visibility |
| URL activation | `?gm=true` opens with GM Mode active |
| WebSocket connects | Panel connects to `/ws/watcher` when activated |
| WebSocket disconnects | Panel closes WebSocket when deactivated |
| Event stream renders | Telemetry events display per turn with color-coded severity |
| Subsystem bars render | Agent invocation histogram displays as horizontal bars |
| Trope timeline renders | Active tropes show progress bars with beat markers |
| State inspector renders | Current GameSnapshot displays as a collapsible tree |
| Validation alerts render | Warning and error results display with turn numbers |
| Lazy loaded | GM Mode bundle chunk is not loaded until first activation |
| No game impact | Game WebSocket, rendering, and input are unaffected when GM Mode is hidden |
| Buffer bounded | Event history is capped at 100 turns to prevent memory growth |
