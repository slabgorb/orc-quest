# Demo Script — 18-2

**Setup before presenting:** Start the game server and UI. Open the GM dashboard. Have a save with at least 3 completed turns ready to load.

---

**Slide 1: Title** *(30 seconds)*
Introduce the story: "This is a two-point bug fix from Epic 18 — the OTEL Dashboard sprint. The fix is one line of code. The impact is that the entire State tab now works."

---

**Slide 2: Problem** *(60 seconds)*
Pull up the dashboard in a browser pointed at the pre-fix build (or show the screenshot in the slide). Navigate to the State tab. It reads: *"Waiting for GameStateSnapshot event…"*

Say: "This has never worked. Every turn, the server sends a full snapshot of game state — characters, HP, inventory, location, everything. The dashboard received every one of those packets and threw them away because it was looking for a label that didn't match."

Show the Console tab. Point out the incoming `game_state_snapshot` events in the raw event stream. "The data was always here. The tab just couldn't see it."

*Fallback if live demo unavailable: Slide 2 screenshot of the stuck "Waiting…" message alongside the Console tab showing `game_state_snapshot` events arriving.*

---

**Slide 3: What We Built** *(90 seconds)*
Switch to the fixed build. Load the saved game with 3 turns. Navigate to the State tab.

The tab now shows a JSON tree. Say: "Same server. Same data. One string changed."

Expand the tree: navigate to `characters → [first character name] → hp`. Show the current HP value. Then navigate to `inventory → items`. Show at least one item.

Switch to the Diff view. Select Turn 1 vs Turn 3 from the dropdown. Show the highlighted diff — any field that changed between those turns will be marked. Say: "This is the lie detector. If combat ran, HP changes here. If an item was picked up, it appears here. If nothing changed despite narration saying otherwise, this view catches it."

*Fallback if live demo fails: Switch to Slide 3 slide showing the State tab screenshot with the tree expanded and the Diff view side-by-side.*

---

**Slide 4: Why This Approach** *(45 seconds)*
"The fix is one line. We changed `state_transition` to `game_state_snapshot` on line 139 of the dashboard hook. We wrote six tests first that failed with the old string and pass with the new one. The negative test — the one that confirms the *wrong* event type is rejected — will catch this exact bug if it ever tries to come back."

---

**Before/After slide** *(30 seconds)*
Point to the side-by-side. Left: stuck tab. Right: live tree. "Same game. Same session. Same server output. One word."

---

**Roadmap slide** *(60 seconds)*
"The State tab is now the foundation for the next three stories in this epic…" *(see Roadmap section below)*

---

**Questions** — open floor.

---
