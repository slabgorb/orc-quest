---
parent: context-epic-1.md
---

# Story 1-4: Genre Loader — Unified Loading, Two-Phase Validation, Real YAML Tests

## Business Context

This is the bridge between "we can parse YAML structs" (1-3) and "we can actually load a
genre pack from disk." Without a working loader, every downstream consumer of genre data —
game state, agents, the server — has nothing to work with. It turns static struct definitions
into a runtime capability.

The two-phase validation pattern (deserialize, then cross-reference check) is a deliberate
improvement over Python, where malformed YAML caused runtime crashes deep in game logic
rather than at load time.

**Python sources:**
- `sq-2/sidequest/genre/loader.py` — YAML loading with file map
- `sq-2/sidequest/genre/resolve.py` — trope inheritance resolution (partial, extended in 1-5)

## Technical Guardrails

- **Port lesson #13 (consistent loader):** Python has 4 different loading patterns plus
  special cases. Rust uses a single unified loader
- **Port lesson #17 (two-phase loading):** Phase 1: deserialize YAML → typed structs.
  Phase 2: validate cross-references (e.g., trope `extends` targets exist)
- **Real YAML tests:** Must load `mutant_wasteland/flickering_reach` (fully spoilable pack)
- **Error types:** `GenreError` enum covers parse failures, file-not-found, and validation
  errors with clear context about which file and which field
- **File map pattern:** Loader builds a map of all YAML files in the pack directory before
  parsing, avoiding repeated filesystem walks

## Scope Boundaries

**In scope:**
- `fn load_genre_pack(path: &Path) -> Result<GenrePack, GenreError>` unified loader
- File discovery and map building
- Two-phase validation (deserialize, then cross-reference check)
- Tests loading real genre packs from `genre_packs/`
- Clear error messages identifying file and field on failure

**Out of scope:**
- Trope inheritance resolution with cycle detection (story 1-5)
- Scenario pack loading (story 1-5)
- Lore RAG system (future epic)
- Runtime genre pack switching

## AC Context

| AC | Detail |
|----|--------|
| Unified loader | Single `load_genre_pack()` function replaces Python's 4 patterns |
| Real YAML loads | `mutant_wasteland/flickering_reach` loads without error |
| Two-phase validation | Phase 1 returns typed structs; Phase 2 checks cross-references |
| Clear errors | Parse/validation failures identify the offending file and field |
| deny_unknown_fields | YAML typos produce clear errors (from 1-3 structs) |

## Assumptions

- Genre pack YAML files from sq-2 are structurally stable and match the structs from 1-3
- `mutant_wasteland/flickering_reach` is sufficient as the test fixture (fully spoilable)
- Two-phase validation catches cross-reference errors Python misses at load time
