# Demo Script — 19-8

**Scene 1 — Set the stage (0:00–0:30)**
*Slide 2: Problem*
Open the game without the automapper. Say: "Right now, players have no persistent record of where they've been. Every room is new territory with no way back." Show the blank sidebar where the map will live.

**Scene 2 — First room discovered (0:30–1:00)**
*Slide 3: What We Built*
Start a new session in `mutant_wasteland/flickering_reach`. Enter the starting room. Point to the sidebar: a single labeled square appears on the graph-paper grid. Say: "The moment you enter a room, it draws itself."

**Scene 3 — Fog of war (1:00–1:45)**
*Slide 3: What We Built*
Move to the second room. The first room stays visible; adjacent undiscovered rooms appear as dark/greyed squares. Say: "You can see that exits exist — but not what's behind them until you go there."

**Scene 4 — Typed exits (1:45–2:30)**
*Slide 3: What We Built*
Navigate through a door and then find the stairs. Point out the door icon on the door connection and the staircase symbol on the vertical exit. Say: "The map tells you *what kind* of passage connects each room — a door, an open corridor, or stairs to another level."

**Scene 5 — Five-room render test (2:30–3:00)**
*Slide 4: Why This Approach*
Run in the browser console:
```
document.querySelectorAll('[data-room-node]').length
```
Output should read `5`. Say: "Five rooms, five nodes, all correctly wired from live game data."

**Fallback:** If the live demo environment is unavailable, show the static screenshot on Slide 3 and narrate the walkthrough against it.

**Scene 6 — Responsive check (3:00–3:30)**
*Slide 3: What We Built*
Drag the browser window narrower. The sidebar panel reflows; the map scales down without distortion. Say: "Works at any screen size — laptop, tablet, or a second monitor panel."

---
