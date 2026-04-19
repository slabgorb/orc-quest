# Demo Script — 39-1

**Total time: ~8 minutes**

**Slide 1 — Title (30 sec)**
Introduce the story: "This is a housekeeping story — no new features visible to players, but it lays the foundation for everything that touches resource tracking going forward."

**Slide 2 — Problem (90 sec)**
Walk through the problem concretely. Say: "Before this change, if you searched the codebase for threshold logic, you'd find the same pattern in two places. Here's what that looked like." Show the Before/After slide (see below) with the duplicated function signatures side by side.

**Slide 3 — What We Built (2 min)**
Open `sidequest-game/src/thresholds.rs` in the editor. Point out the `EdgePool` struct fields: `current`, `max`, `base_max`, `recovery_triggers`, `thresholds`. Say: "This is now the single definition of 'a resource that can run low.' Health, stamina, mana — they all speak this language."

Then show the unit tests running:
```bash
cargo test -p sidequest-game thresholds
```
Expected output: all threshold tests green in under 2 seconds.

*Fallback if terminal unavailable: show Slide 3 with the test output screenshot pre-captured.*

**Slide 4 — Why This Approach (90 sec)**
"The Rust compiler is now our gatekeeper. Any future resource type has to implement this contract or the build breaks. We moved a runtime risk to a compile-time guarantee."

**Before/After Slide (1 min)**
Show the diff summary: two functions (`mint_threshold_lore`, `detect_crossings`) that previously lived in separate modules now call into the shared `thresholds.rs`. Line count in those modules dropped; `thresholds.rs` is the new canonical home.

**Roadmap Slide (1 min)**
"This unlocks the next stories in Epic 39 — once EdgePool is the standard contract, we can wire threshold events to the OTEL dashboard so the GM panel shows live resource state."

**Questions (open)**

---
