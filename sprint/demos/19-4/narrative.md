# 19-4

## Problem

Problem: MAP_UPDATE for room graph — send discovered rooms with exits to UI. Why it matters: users needed a better interface.

## What Changed

We implemented: MAP_UPDATE for room graph — send discovered rooms with exits to UI.
This delivers the following capabilities:
  - ExploredLocation includes exits, room_type, size fields
  - MAP_UPDATE only includes discovered rooms
  - Current room flagged in payload
  - Protocol types updated in sidequest-protocol
  - {'Test': 'discover 3 rooms, verify MAP_UPDATE contains exactly 3 with correct exits'}

## Why This Approach

This approach prioritizes user experience and accessibility.
