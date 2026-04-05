# Demo Script — 16-13

**Setup:** Have the SideQuest UI running against a local API with `spaghetti_western/the_dusty_divide` loaded. Player character should start with Luck: 4/6.

---

**Scene 1 — Opening (Slide 1: Title)**
*Timing: 0:00–0:30*
Open with the game already running. Point to the resource area: "Right now you're looking at something that didn't exist a week ago. The backend knew your Luck score. The player didn't."

---

**Scene 2 — The Problem (Slide 2: Problem)**
*Timing: 0:30–1:00*
Reference the genre pack config. Show the terminal:
```bash
cat sidequest-content/genre_packs/spaghetti_western/rules.yaml | grep -A 10 "resources:"
```
Point out the threshold values: `warn_at: 1, critical_at: 0`. "The backend was tracking this. The player saw nothing."

*Fallback if terminal fails: Slide 2 static screenshot of rules.yaml resource block.*

---

**Scene 3 — What We Built (Slide 3: What We Built)**
*Timing: 1:00–2:30*
Switch to the UI. Point to the Luck bar at the top of the HUD: "Luck: 4 out of 6. Sepia-toned fill — matches the western palette."

Then switch to `neon_dystopia/chrome_and_silence`. Point to the Humanity bar: "Same component. Now it's showing 73/100 in cyan. Different resource, different genre, different aesthetic — same code."

Then switch back to spaghetti_western. In the browser console, fire a simulated threshold crossing:
```js
window.__debugResourceCrossing({ resource: 'luck', value: 1, threshold: 'warn' })
```
Show the pulse animation on the bar, the toast appearing ("Your Luck is nearly spent"), and play the audio sting. "Visual, text, and audio — all at the same moment."

*Fallback if console injection fails: Show the recorded screen capture on Slide 3 supplemental.*

---

**Scene 4 — Why This Approach (Slide 4: Why This Approach)**
*Timing: 2:30–3:15*
Open the component file briefly:
```bash
grep -n "data-genre\|threshold\|onCrossing" sidequest-ui/src/components/GenericResourceBar.tsx | head -20
```
"One component, no genre knowledge baked in. The genre pack tells it what to show."

---

**Scene 5 — Edge Cases (optional, after Slide 4)**
*Timing: 3:15–3:45*
Demonstrate zero and max:
```js
window.__debugResourceCrossing({ resource: 'luck', value: 0, threshold: 'critical' })
```
Bar goes empty. Toast fires. Then:
```js
window.__debugResourceUpdate({ resource: 'luck', value: 6 })
```
Bar fills completely. "Both extremes render correctly — no divide-by-zero, no overflow."

---

**Scene 6 — Roadmap (Slide: Roadmap)**
*Timing: 3:45–4:15*
"Next: the HUD layout story wires this into the actual game screen alongside HP and status effects. After that, road_warrior Fuel transfers into the RigStats panel at confrontation time."

---
