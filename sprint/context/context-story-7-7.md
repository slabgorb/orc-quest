---
parent: context-epic-7.md
---

# Story 7-7: Scenario Archiver — Save/Resume Mid-Scenario State, Session Boundary Handling

## Business Context

Players shouldn't lose investigation progress when they quit and resume. The scenario
archiver serializes the full `ScenarioState` — all NPC BeliefStates, activated clues,
tension level, gossip history — so a session can resume exactly where it left off. Python
used pickle for this (fragile, version-sensitive). Rust uses serde with explicit versioning.

**Depends on:** Story 7-1 (BeliefState model — the primary state being archived)

## Technical Approach

`ScenarioState` already derives `Serialize`/`Deserialize`. The archiver provides
save/load operations that integrate with the existing `SessionStore`:

```rust
pub struct ScenarioArchiver {
    store: Arc<dyn SessionStore>,
}

impl ScenarioArchiver {
    pub fn save(&self, session_id: &str, state: &ScenarioState) -> Result<(), ArchiveError> {
        let versioned = VersionedScenario {
            version: SCENARIO_FORMAT_VERSION,
            state: state.clone(),
        };
        let json = serde_json::to_string(&versioned)?;
        self.store.save_scenario(session_id, &json)?;
        Ok(())
    }

    pub fn load(&self, session_id: &str) -> Result<Option<ScenarioState>, ArchiveError> {
        let json = self.store.load_scenario(session_id)?;
        match json {
            None => Ok(None),
            Some(data) => {
                let versioned: VersionedScenario = serde_json::from_str(&data)?;
                if versioned.version != SCENARIO_FORMAT_VERSION {
                    return Err(ArchiveError::VersionMismatch {
                        expected: SCENARIO_FORMAT_VERSION,
                        found: versioned.version,
                    });
                }
                Ok(Some(versioned.state))
            }
        }
    }
}
```

Version checking prevents loading corrupted state from a different format version. When
a version mismatch occurs, the scenario restarts cleanly rather than producing undefined
behavior.

Session boundary handling: when the orchestrator detects a scenario in progress during
session resume, it loads the archived state and re-derives tension from the turn count.

## Scope Boundaries

**In scope:**
- `ScenarioArchiver` with save/load operations
- `VersionedScenario` wrapper with format version
- Integration with `SessionStore` trait
- Version mismatch error handling
- Round-trip tests for full `ScenarioState`

**Out of scope:**
- Version migration (upgrading old format to new — future work)
- Partial state recovery from corruption
- Cross-session scenario continuity (each session is self-contained)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Round-trip | Save then load returns identical `ScenarioState` |
| All state preserved | BeliefStates, clues, tension, turn count all survive save/load |
| Version check | Loading a different version returns `VersionMismatch` error |
| No scenario | Loading when no scenario saved returns `Ok(None)` |
| Store integration | Uses existing `SessionStore` trait, no separate storage backend |
| Session resume | Orchestrator loads scenario state on session resume |
