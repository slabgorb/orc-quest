---
parent: context-epic-16.md
---

# Story 16-9: Confrontation UI — Generic Encounter Display with Genre Theming

## Business Context

Every encounter type needs visual representation. Rather than building per-type UIs
(chase UI, standoff UI, negotiation UI), build one EncounterOverlay that reads the
encounter type and genre theme to determine visual treatment. The standoff gets
letterbox framing. The chase keeps its existing look. Unknown types get a clean default.

## Technical Approach

### EncounterOverlay Component

```tsx
interface EncounterOverlayProps {
  encounter: EncounterState;      // from WebSocket EncounterUpdate
  genreTheme: GenreTheme;
  onBeatSelect: (beatId: string) => void;
}
```

### Visual Treatment by Type

| Encounter Type | Visual Treatment |
|---------------|-----------------|
| `chase_*` | Existing chase visualization (migration from current) |
| `standoff` | Letterbox (21:9 aspect), extreme close-up portraits, tension bar |
| `negotiation` | Split-screen, leverage bar centered, beat buttons below |
| `net_combat` | Matrix/grid aesthetic, trace meter as progress bar |
| `ship_combat` | Tactical display, engagement range as distance meter |
| `auction` | Bid counter, opponent reactions, purse display |
| Unknown | Generic: metric bar + beat buttons + actor list |

### Shared Elements (all encounter types)

- **Metric bar** — horizontal bar showing metric.current vs thresholds, genre-colored
- **Beat buttons** — available beats as action buttons, grayed if stat check would fail
- **Phase indicator** — current EncounterPhase (Setup/Opening/Escalation/Climax/Resolution)
- **Actor portraits** — participants with role labels
- **Secondary stats** — if present, rendered as mini stat bars

### Existing CombatOverlay

CombatOverlay.tsx stays for CombatState (actor-centric combat). EncounterOverlay is
for StructuredEncounter (scene-centric). They're separate components.

### WebSocket Messages

Reads `EncounterUpdate` message (new, replaces `CHASE_UPDATE`):
```typescript
interface EncounterUpdate {
  encounter_type: string;
  metric: { name: string; current: number; threshold_high?: number; threshold_low?: number };
  beat: number;
  phase: string;
  secondary_stats?: Record<string, { current: number; max: number }>;
  available_beats: Array<{ id: string; label: string; risk?: string }>;
}
```

### Key Files

| File | Action |
|------|--------|
| `sidequest-ui/src/components/EncounterOverlay.tsx` | NEW — main component |
| `sidequest-ui/src/components/EncounterMetricBar.tsx` | NEW — reusable metric display |
| `sidequest-ui/src/components/BeatSelector.tsx` | NEW — beat action buttons |
| `sidequest-ui/src/components/CombatOverlay.tsx` | Keep for CombatState |
| `sidequest-ui/src/types/protocol.ts` | Add EncounterUpdate type |
| `sidequest-ui/src/hooks/useGameSocket.ts` | Handle EncounterUpdate message |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Renders | EncounterOverlay displays for any StructuredEncounter type |
| Metric bar | Shows current vs threshold with genre-themed colors |
| Beat buttons | Available beats rendered as actionable buttons |
| Standoff | Letterbox framing + close-up treatment when type is "standoff" |
| Chase | Existing chase visualization preserved |
| Generic | Unknown encounter types get clean default layout |
| Phase | Current phase displayed with visual distinction |
| Secondary stats | Optional stat bars render when present |
