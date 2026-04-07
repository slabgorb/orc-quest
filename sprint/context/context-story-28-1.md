---
parent: context-epic-28.md
---

# Story 28-1: Load ConfrontationDefs into Server

## Business Context

Genre packs declare confrontation types in `rules.yaml`. sidequest-genre parses them
into `Vec<ConfrontationDef>` at pack load time. The server never holds a reference to
these defs — so apply_beat(), format_encounter_context(), and beat population all have
no ConfrontationDef to work with at runtime. This is the foundation story that unblocks
everything else.

## Technical Approach

The genre pack is already loaded in `dispatch_connect()` when the player selects a
genre/world. The `GenrePack` struct has `rules.confrontations: Vec<ConfrontationDef>`.
The defs need to be accessible in `DispatchContext` throughout the turn pipeline.

### Where ConfrontationDefs are parsed
- `sidequest-genre/src/models/rules.rs:411` — `pub confrontations: Vec<ConfrontationDef>`
- Loaded during genre pack initialization in `sidequest-genre/src/loader.rs`

### Where they need to be available
- `DispatchContext` — every dispatch function needs to look up a def by encounter_type
- Add a field: `confrontation_defs: &'a [ConfrontationDef]` or equivalent
- Lookup function: `fn find_confrontation_def(encounter_type: &str) -> Option<&ConfrontationDef>`

### Wiring path
1. In `dispatch_connect()` (dispatch/connect.rs) where the genre pack is loaded, extract
   `genre_pack.rules.confrontations` and store on `DispatchContext`
2. Add a convenience method on DispatchContext for lookup by type string

## Key Files

| File | Action |
|------|--------|
| `sidequest-server/src/dispatch/connect.rs` | Extract confrontation defs from genre pack, store on context |
| `sidequest-server/src/dispatch/mod.rs` | Add confrontation_defs field to DispatchContext |
| `sidequest-genre/src/models/rules.rs` | Reference only — ConfrontationDef already defined here |

## Acceptance Criteria

| AC | Detail | Wiring Verification |
|----|--------|---------------------|
| Defs loaded | DispatchContext holds confrontation_defs after genre pack is loaded | Grep: `confrontation_defs` appears in DispatchContext struct AND is populated in dispatch_connect |
| Lookup works | Can find a ConfrontationDef by encounter_type string | Unit test + non-test call site in dispatch |
| OTEL | `encounter.defs_loaded` event emitted with genre, count, and type names | Grep: WatcherEventBuilder with "encounter.defs_loaded" in connect.rs |
| Non-empty | At least one genre pack's confrontation defs load successfully | Integration test loading spaghetti_western (has 3 types) |
| Wiring | confrontation_defs has a non-test consumer in dispatch/ | `grep -r "confrontation_defs" crates/sidequest-server/src/dispatch/ --include="*.rs" | grep -v test` returns results |

## Scope Boundaries

**In scope:** Loading defs into dispatch context, lookup by type
**Out of scope:** Using the defs for anything — that's 28-3, 28-4, 28-5
