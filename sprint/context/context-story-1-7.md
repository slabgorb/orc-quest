---
parent: context-epic-1.md
---

# Story 1-7: Game Subsystems — CombatState, ChaseState, NarrativeEntry, Progression

## Business Context

Port the game state machinery that handles combat, chase sequences, narrative tracking, and progression. The Python implementation spans `game/combat_models.py`, `game/chase.py`, `game/progression.py`, and `game/narrative_*.py` (~1,400 lines total). This story builds directly on story 1-6 (core types) and establishes the state structures that story 1-8 will compose.

**Python sources:**
- `sq-2/sidequest/game/combat_models.py` — CombatState, RoundResult, DamageCalculator
- `sq-2/sidequest/game/chase.py` — ChaseState, ChaseRound, escape/capture logic
- `sq-2/sidequest/game/progression.py` — level/XP, skill unlock, HP scaling, equipment progression
- `sq-2/sidequest/game/narrative_*.py` — NarrativeEntry, narration log, scene state
- `sq-2/sidequest/game/turn_manager.py` — turn tracking, action queuing

## Technical Guardrails

- **Port lesson #4 (god object decomposition):** The Python GameState is 255+ lines and handles all mutations. The Rust version decomposes into domain-specific types: CombatState (owns combat), ChaseState (owns chase), ProgressionState (owns level/XP), NarrativeState (owns narration). Each has a clear responsibility and mutation interface
- **Port lesson #13 (HP clamping bug):** Python's `progression.py` is missing a floor in the HP scaling function. The Rust implementation uses a single `clamp_hp(base: i32, level: i32) -> i32` function that always returns `base.max(1)`
- **ADR-006 (Turn-based timing):** Turns advance in discrete phases: input collection → intent routing → agent execution → state patch → broadcast. Turn counts always increment, never reset
- **ADR-017 (Chase Engine):** Chases have escape threshold (50%), capture check (enemy wins if player can't escape), and cinematic narration per round. Three chase types: footrace, stealth, negotiation
- **Narrative immutability:** NarrativeEntry is append-only. Scene events never mutate previous entries. Query via iteration (newest → oldest)

### Python → Rust Translation

| Python | Rust |
|--------|------|
| `CombatState` class with mutable fields | `CombatState { round: u32, combatants: Vec<Combatant>, damage_log: Vec<DamageEvent> }` |
| `RoundResult = namedtuple(...)` | `struct RoundResult { ... }` with serde |
| `ChaseState` with escape threshold | `ChaseState { escape_threshold: f32, rounds: Vec<ChaseRound> }` |
| `NarrativeEntry` in ordered list | Append-only `Vec<NarrativeEntry>` with timestamps |
| `progression.apply_level()` | Pure fn `level_to_stats(level: u32) -> Stats` |
| `clamp_hp()` buggy | Pure fn `clamp_hp(base: i32, level: u32) -> i32` with floor check |
| `TurnManager` state counter | Passed to handlers, not stored globally |

### Combat Mechanics

Combat state tracks:
- **Round counter** (starts at 1, increments each combat action)
- **Active combatants** (Character + NPCs, order from speed stat)
- **Damage log** (DamageEvent: attacker, target, damage, roll result)
- **Status effects** (poison, stun, bless, curse — duration tracked per round)

**Round flow:**
1. Initiative resolved (speed stat + roll)
2. Actor takes action (attack, defend, skill)
3. DamageCalculator resolves (base damage + defense + random)
4. Status effects decrement
5. Check victory/defeat conditions

### Chase Mechanics

Chase state tracks:
- **Chase type** (footrace, stealth, negotiation)
- **Escape threshold** (default 50%, genre override possible)
- **Round counter** (1+ per chase round)
- **Escape rolls** (player's roll history)
- **Capture check** (50% + player speed vs enemy speed)

**Chase round flow:**
1. Player attempts escape via agent narration
2. Roll compared against threshold
3. If below threshold, continue
4. If above, escape succeeds
5. If enemy catches (50% check), capture forced

### Progression Mechanics

Pure functions that map level → stats:
- `level_to_hp(base_hp: i32, level: u32) -> i32` — scales with soft cap (diminishing returns at level 10+)
- `level_to_damage(base_damage: i32, level: u32) -> i32` — linear +0.1 per level
- `level_to_defense(base_defense: i32, level: u32) -> i32` — soft cap like HP
- `clamp_hp(base: i32, level: u32) -> i32` — **CRITICAL FIX** — always returns `base.max(1)` to prevent negative HP

**XP and leveling:**
- XP awarded per combat round/chase success
- Level threshold: `100 * level` (100 @ L1, 200 @ L2, etc.)
- Level up triggers: skill unlock, stat recalculation, narrative event

### Narrative Tracking

NarrativeEntry struct:
```rust
pub struct NarrativeEntry {
    pub timestamp: u64,      // ms since game start
    pub round: u32,
    pub author: String,      // "narrator", "combat", "chase", etc.
    pub content: String,     // Narration text
    pub tags: Vec<String>,   // For scene filtering
}
```

**Immutability:** Scene narrative is append-only. No edits or deletes. Query via reverse iteration.

## Scope Boundaries

**In scope:**
- CombatState struct (round, combatants, status effects, damage log)
- RoundResult and DamageEvent types
- DamageCalculator (pure functions: base damage, defense reduction, random variance)
- ChaseState struct (escape threshold, type, round history)
- ChaseRound result tracking
- Progression functions (level_to_hp, level_to_damage, level_to_defense, clamp_hp)
- XP and level thresholds
- Skill unlock triggers
- NarrativeEntry and narrative log (append-only)
- TurnManager for turn counting and phase tracking
- Status effect types and duration tracking
- Complete test suite for all state machines

**Out of scope:**
- Game snapshot composition (story 1-8)
- Agent execution of combat/chase (story 1-10)
- Server dispatch of combat actions (story 1-11)
- Combat AI (future epic)

## AC Context

| AC | Detail |
|----|--------|
| CombatState works | Create, track rounds, add combatants, log damage, apply effects |
| RoundResult resolves | Damage calculated, effects applied, status checked |
| DamageCalculator | Base + defense + variance formula matches Python |
| ChaseState works | Create, track rounds, check escape roll vs threshold |
| Chase capture logic | 50% chance if threshold not met |
| Progression functions | Level → stats conversion, soft cap at L10 |
| HP clamping fixed | Always returns `.max(1)`, never negative |
| XP and leveling | Threshold 100*level, level up triggers skill unlock |
| NarrativeEntry | Append-only, immutable, queryable by reverse iteration |
| TurnManager | Tracks phase, round counter, never resets |
| Status effects | Duration tracked per round, decrement each round |
| Full test coverage | All state machines tested with Python-aligned fixtures |
