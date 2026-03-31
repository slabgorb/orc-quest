---
parent: context-epic-18.md
workflow: tdd
---

# Story 18-4: LoreStore Browser Tab with Per-Turn Budget Visualization

## Business Context

The LoreStore (lore.rs, 2,746 LOC) is the game's knowledge base — every place, NPC,
event, faction, and item the narrator knows about. Each turn, `select_lore_for_prompt()`
selects fragments within a token budget for the Claude prompt. Currently there's zero
visibility into what's in the store, what gets selected, and what gets cut. This is
the primary tool for catching "Claude is winging it" — if a relevant fact exists in
the store but wasn't selected, the narrator literally can't reference it.

## Technical Approach

### API: New WatcherEventType

Add `LoreSelection` variant to `WatcherEventType` enum in `lib.rs`.

Emit from `select_lore_for_prompt()` (lore.rs:354) or its caller in the prompt
framework. Fields:

```json
{
  "turn_number": 18,
  "total_fragments": 47,
  "budget_tokens": 2000,
  "tokens_used": 1847,
  "selected": [
    { "id": "place_flickering_reach", "category": "place", "tokens": 120 }
  ],
  "rejected": [
    { "id": "npc_old_gus", "category": "npc", "tokens": 85, "reason": "over_budget" }
  ],
  "relevance_keyword": "tavern"
}
```

Also emit a `LoreStoreSnapshot` event periodically (on session start + after any
`accumulate_lore` call) with the full fragment list for the browser view.

### UI: New Lore Tab

Add `LoreTab` to the dashboard tab bar alongside Timeline, State, Subsystems, etc.

**Browser view (default):**
- Table: id, category, source, content (truncated to 100 chars), token count
- Category filter dropdown (place, npc, event, faction, item, custom)
- Keyword search across content
- Sort by category, token count, or insertion order

**Budget view (per-turn):**
- Turn selector (same pattern as State tab)
- Two-column layout: Selected (green) | Rejected (red)
- Each fragment shows id, category, token count
- Summary bar: tokens_used / budget_tokens with fill indicator
- Relevance keyword highlighted

### Key Files

| File | Change |
|------|--------|
| `sidequest-server/src/lib.rs` | Add `LoreSelection`, `LoreStoreSnapshot` to WatcherEventType |
| `sidequest-game/src/lore.rs` | Emit selection event from `select_lore_for_prompt()` |
| `sidequest-ui/src/components/Dashboard/types.ts` | Add LoreSelection types to TurnProfile |
| `sidequest-ui/src/components/Dashboard/hooks/useDashboardSocket.ts` | Handle new event types |
| `sidequest-ui/src/components/Dashboard/tabs/Lore/LoreTab.tsx` | New tab component |
| `sidequest-ui/src/components/Dashboard/DashboardLayout.tsx` | Add Lore tab |

## Scope Boundaries

**In scope:**
- New WatcherEventType variants and emit points
- LoreTab with browser and budget views
- Search and filter in browser view
- Per-turn budget visualization

**Out of scope:**
- Editing lore fragments from the dashboard
- Semantic search / vector similarity display
- LoreStore persistence visualization

## Acceptance Criteria

1. **Lore tab appears** in dashboard tab bar
2. **Browser view** shows all LoreFragments with search and category filter
3. **Budget view** shows selected vs rejected fragments per turn with token counts
4. **Budget bar** visually shows tokens_used / budget_tokens ratio
5. **Events flow** — `lore_selection` events visible in Console tab
6. **No performance regression** — lore event emission doesn't slow turn processing
