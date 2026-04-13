# Demo Script — 29-7

**Setup (before presentation):**
- Have a test dungeon YAML loaded with a cyclic room graph (5 rooms forming a loop + 2 dead-end branches)
- Have the tactical map rendered in the browser for a tree-only dungeon (from 29-6)

---

**Slide 1: Title**
*(15 seconds)* — Open on slide. "Today we're showing the last missing piece of the tactical map engine before the GM gets a full dungeon view."

---

**Slide 2: Problem**
*(45 seconds)* — "Here's the Mawdeep dungeon the content team designed." Open the YAML or a hand-drawn sketch showing a loop: Entrance → Hall → Chamber → Back Passage → Entrance. "Every interesting dungeon has a loop. Players love shortcuts. But our engine couldn't handle this." Show the error output or crash log from attempting to load the cyclic graph before this fix: `ERROR: cycle detected, tree layout cannot proceed`. "That's the wall we're breaking through today."

---

**Slide 3: What We Built**
*(60 seconds)* — "We taught the engine to do four things in sequence."

Walk through the four phases on the slide bullet by bullet:
1. **Detect the loop** — "It finds the loop using a graph traversal — no guessing."
2. **Place the ring** — "It lays out the rooms in a circle, snapping exits to entrances."
3. **Validate closure** — "It checks the last wall actually lines up with the first."
4. **Resolve overlaps** — "If two rooms collide in the grid, it tries to nudge them apart. If it can't, it tells you exactly which two rooms are the problem."

Then run the live demo:
```bash
cd sidequest-api
cargo test -p sidequest-game layout::jaquayed -- --nocapture 2>&1 | tail -30
```
Show all tests green. Point out the test names: `cycle_detection_simple_loop`, `ring_placement_triangle`, `closure_validation_gap_mismatch`, `overlap_nudge_resolves`.

*Fallback: If tests fail to run, go to Slide 3 and show the pre-captured terminal screenshot.*

---

**Slide 4: Why This Approach**
*(30 seconds)* — "The key design decision: keep the output identical. The SVG renderer, the pathfinding, the UI — none of them know or care whether a dungeon has loops. They see the same positioned-room data either way. We extended the engine, not the contract."

---

**Before/After Slide (optional):**
- **Before:** `ERROR: cycle detected in room graph, aborting layout` — dungeon fails to load
- **After:** Tactical map rendered with all 5 rooms correctly positioned, loop closed, exits aligned

Show the SVG output side by side if 29-8 (SVG dungeon renderer) is far enough along to render it. Otherwise show the raw `DungeonLayout` JSON with room coordinates.

---

**Roadmap Slide:**
*(30 seconds)* — "This unlocks the content team. Every dungeon Mawdeep needs is now layoutable. The next story wires this into the SVG map so GMs can see it."

---

**Questions Slide:** Open floor.

---
