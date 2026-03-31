---
parent: context-epic-18.md
workflow: tdd
---

# Story 18-5: Structured NPC Registry and Inventory Panels in State Tab

## Business Context

Once 18-2 fixes the State tab, GameSnapshot data flows to the dashboard — but as a
raw JSON tree. The GM needs to quickly scan "who's in play" and "what do they have"
without expanding nested JSON nodes. Structured table views for NPCs and inventory
make the State tab actually usable as a GM tool during live play.

## Technical Approach

### UI Only — No API Changes

All data already exists on GameSnapshot:
- `snapshot.npcs[]` — Vec<Npc> with name, pronouns, role, location, disposition
- `snapshot.characters[]` — Vec<Character> with inventory (items + gold), HP, stats
- NpcRegistryEntry (name, pronouns, role, location, last_seen_turn) is on the
  server-side session but may not be in the snapshot — check if it's serialized

### NPC Registry Panel

Render within the State tab as a collapsible section above the raw tree view.

**Table columns:**
| Column | Source | Notes |
|--------|--------|-------|
| Name | `npc.core.name` | Bold, primary identifier |
| Role | `npc.core.role` or extracted | Brief descriptor |
| Location | `npc.location` or snapshot context | Last known |
| Disposition | `npc.disposition` | Color-coded: green (Friendly >10), gray (Neutral), red (Hostile <-10) |
| HP | `npc.core.hp` / `npc.core.max_hp` | Bar or fraction |
| Pronouns | `npc.pronouns` | For GM reference |

Sortable by name, disposition, location. Clickable row expands full NPC JSON.

### Inventory Panel

Per-character section within State tab.

**Character header:** Name, class, HP bar, gold amount

**Items table:**
| Column | Source | Notes |
|--------|--------|-------|
| Name | `item.name` | With evolution indicator |
| Weight | `item.narrative_weight` | 0.0-1.0 bar |
| Stage | Derived from weight | unnamed (<0.5), named (0.5-0.7), evolved (>0.7) |
| Description | `item.description` | Truncated, expandable |

### Key Files

| File | Change |
|------|--------|
| `sidequest-ui/src/components/Dashboard/tabs/State/StateTab.tsx` | Add panel sections above tree |
| `sidequest-ui/src/components/Dashboard/tabs/State/NpcPanel.tsx` | New component |
| `sidequest-ui/src/components/Dashboard/tabs/State/InventoryPanel.tsx` | New component |

## Scope Boundaries

**In scope:**
- NPC table with sort and expand
- Per-character inventory table with evolution stage
- Integrated into existing State tab (not a new tab)

**Out of scope:**
- Editing NPCs or items from the dashboard
- NPC relationship graphs or faction grouping
- Historical NPC tracking (who appeared when) — that's a future enhancement

## Acceptance Criteria

1. **NPC table renders** with all active NPCs from the snapshot
2. **Disposition color-coded** — visual at-a-glance attitude assessment
3. **Inventory table renders** per character with item evolution stages
4. **Gold displayed** per character
5. **Sortable** — NPC table sorts by name, disposition, location
6. **Row expansion** — clicking an NPC or item row shows full JSON detail
7. **Depends on 18-2** — panels only appear when snapshots are flowing
