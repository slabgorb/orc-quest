# 29-7

## Problem

**Problem:** Dungeons built with looping layouts — rooms you can circle back through, shortcuts between areas, hub-and-spoke designs — couldn't be rendered on the tactical map. The map engine only understood straight-line room chains. Any dungeon designed with a loop would crash or refuse to load.

**Why it matters:** Looping dungeon designs (called "jaquayed" layouts in tabletop RPG theory) are the gold standard for interesting, replayable encounters. They give players agency — multiple paths, tactical choices, flanking routes. Without them, every dungeon is a railroad. This blocks the content team from authoring any room graph that isn't a dead-simple corridor.

---

## What Changed

Picture the dungeon map as a connect-the-dots puzzle. Previously, the engine could only draw the dots in a straight line or a branching tree — like a family tree. If you tried to connect Room A back to Room C after going through B, it would get confused and crash.

This story teaches the engine to recognize loops, place the rooms that form the loop as a ring (like beads on a necklace), snap the walls together so exits align, and then verify the ring actually closes without gaps or collisions. Once the loop is locked in, it hangs any dead-end branches off the ring exactly like before. If anything doesn't fit — walls don't line up, rooms overlap — it fails with a clear error pointing at the exact rooms that are incompatible, so the content team can fix the dungeon design.

---

## Why This Approach

The engine already knew how to place rooms by chaining exit-to-entrance offsets — each room's position is derived from the previous one. For loops, we extended that same math: place rooms one by one around the ring using the same offset logic, then check whether the last room's exit actually lands where the first room's entrance is. If the ring closes, great. If not, the dungeon is geometrically impossible with those room shapes, and we say so immediately rather than silently breaking.

This keeps the output identical to the previous system — downstream rendering code (the SVG map, pathfinding, UI) sees the same data structure regardless of whether the dungeon has loops or not. It's a clean extension, not a rewrite.

---
