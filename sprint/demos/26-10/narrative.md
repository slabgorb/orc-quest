# 26-10

## Problem

Problem: The game already knew the full layout of every world — regions, routes, navigation mode — but that data was locked inside the server and never sent to the browser. The UI was flying blind on map structure.

Why it matters: Without map data, the client can't render a meaningful world map, show the player where they are relative to where they've been, or display travel routes between regions. The cartography system existed in full detail in the genre packs (authored by content designers), but it was dead weight from the UI's perspective — loaded, validated, and then discarded before the network message left the server.

---

## What Changed

Imagine the server as a librarian who has a detailed atlas of the game world. Before this change, when a player connected or moved to a new location, the librarian handed them a note that said "you're in the Dark Cave, in the Shadowlands region" — but kept the atlas locked in the back room.

Now, the librarian photocopies the relevant pages from the atlas and slips them into that same note. The UI receives: which navigation style the world uses (open regions, room-by-room dungeons, or hierarchical zones), all named regions with their descriptions and neighbors, and all named routes between them.

This happens at three moments: when a player first connects, when the narrator finishes a turn, and at end-of-turn bookkeeping. Every `MAP_UPDATE` message now carries the full world structure alongside the player's current position.

---

## Why This Approach

The cartography data was already loaded from genre pack YAML files on every request — this change adds zero new I/O. It's pure wiring: translate the internal genre pack format into the wire protocol format, attach it to a message that was already being sent, and emit an observability event so the GM panel can confirm it's flowing.

The data is marked optional in the protocol, so old UI clients that don't know about cartography yet just ignore the extra field. No breaking changes. Three construction sites in the server all needed updating; all three were found and patched.

---
