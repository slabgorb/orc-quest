# Demo Script — 37-24

**Setup before presenting:** Have a save file loaded in the `flickering_reach` world with at least one combat encounter in progress. Have the GM panel open in a second browser tab.

---

**Slide 2: Problem**
*(~2 min)*
Open the GM panel. Point to the narration log. Ask: "When the narrator says 'the goblin slashes at you for 4 damage' — how do we know it rolled anything?" Show that prior to this change, there are no mechanical entries in the log for NPC actions. The narration exists. The mechanics don't show up.

---

**Slide 3: What We Built**
*(~3 min)*
Trigger an NPC turn in the live session. In the GM panel, the `npc.turn` span now appears in real time:
```
npc.turn  goblin_raider  action=attack  target=player_1  roll=14  hit=true  damage=4
```
Then trigger a stealth scenario or enter a room with a trope keyword. Show the `trope.engagement_outcome` span:
```
trope.handshake  keyword="ambush"  check=passed  trope=the_ambush  activated=true
```
Point out the small indicator dot in the GM panel header — green when spans are firing, grey when idle. That dot is the "kitchen window."

*Fallback if live demo fails:* Switch to a pre-recorded screen capture of these two spans appearing. Show Slide 3 bullets while the video plays.

---

**Slide 4: Why This Approach**
*(~1 min)*
Briefly explain: "We could have built a full stats overlay. We didn't. The goal isn't to turn the GM panel into a spreadsheet — it's to give one person in the room the confidence that the system is honest." Point to the single indicator dot as the deliberate design choice.

---
