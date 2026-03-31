---
parent: context-epic-16.md
---

# Story 16-13: UI Resource Display — Generic ResourceBar Component with Genre Theming

## Business Context

Players need to see their genre resources. A spaghetti western player should see their
Luck count. A cyberpunk player should see Humanity degrading. One component handles all
genres — the genre theme controls visual treatment.

## Technical Approach

### GenericResourceBar Component

```tsx
interface ResourceBarProps {
  name: string;
  label: string;
  current: number;
  max: number;
  thresholds: Array<{ at: number; label: string }>;
  genreAccentColor: string;
  voluntary: boolean;
}
```

### Placement

Character sheet footer, below existing stats. Multiple resources stack vertically.

### Visual Behavior

**v1 (this story):**
- Horizontal bar with genre accent color fill
- Label and current/max text
- Threshold markers as ticks on the bar
- Pulse animation on threshold crossing
- Toast notification with narrator_hint text
- Audio sting via existing AudioCue system

**v2 (future, not this story):**
- Revolver cylinder for Luck
- Circuit board fill for Humanity
- Mercury thermometer for Heat

### Threshold Events

Subscribe to `ResourceThresholdEvent` WebSocket message:
```typescript
interface ResourceThresholdEvent {
  resource: string;
  event_id: string;
  narrator_hint: string;
}
```

On receive: trigger bar pulse animation + toast with narrator_hint.

### WebSocket Integration

Subscribe to `ResourceUpdate` message for state sync:
```typescript
interface ResourceUpdate {
  resources: Record<string, { current: number; max: number; label: string; voluntary: boolean }>;
}
```

### Key Files

| File | Action |
|------|--------|
| `sidequest-ui/src/components/ResourceBar.tsx` | NEW — generic resource bar |
| `sidequest-ui/src/components/CharacterSheet.tsx` | Integrate ResourceBar |
| `sidequest-ui/src/types/protocol.ts` | Add ResourceUpdate, ResourceThresholdEvent |
| `sidequest-ui/src/hooks/useGameSocket.ts` | Handle new message types |

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Renders | ResourceBar displays for any resource with label, current/max |
| Multiple | Multiple resources render stacked in character sheet |
| Threshold markers | Visual ticks at threshold positions on the bar |
| Pulse | Bar pulses/flashes on threshold crossing event |
| Toast | narrator_hint displayed as toast on threshold event |
| Audio | AudioCue fires on threshold crossing |
| Genre themed | Bar color matches genre accent from theme.yaml |
| No resources | Character sheet renders normally for genres with no resources |
