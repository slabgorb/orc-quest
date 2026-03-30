# 14-5

## Problem

**Problem:** When creating a character in SideQuest, players had no way to go back and change their choices. Once you picked a name, selected a trait, or chose an archetype, you were locked in — the only escape was abandoning the whole process and starting over. **Why it matters:** Character creation is the first impression the game makes. If a player mis-taps a choice or changes their mind, being forced to restart from scratch is frustrating and erodes confidence in the product before the game even begins.

---

## What Changed

Think of it like filling out a paper form that now has an "Edit" button before you hit Submit.

Before this change, character creation was a one-way street — each screen moved forward only. There was no way to reconsider.

Now, before a player finalizes their character, they land on a **Review screen** that shows all of their choices in one place. From that screen, they can hit a **Back button** to return to any earlier step and change something. Only when they're satisfied do they confirm and create the character.

The player experience is:
1. Walk through the character creation steps as before
2. Arrive at a new Review screen showing everything — name, traits, archetype, all of it
3. If something looks wrong, press **Back** and fix it
4. When it all looks right, press **Create Character** to confirm

---

## Why This Approach

The simplest reliable solution: add a review step at the end of the flow with a clear back path, rather than trying to insert back-navigation into every individual step.

This keeps the forward flow intact (no changes to how each step works), adds a single safe "escape hatch" before the point of no return, and makes the review state explicit so there's no ambiguity about what the player is about to commit to.

The engineering challenge was making sure the review screen reflects the player's actual current choices — not a stale snapshot from an earlier moment. The fix also eliminated a brief bug where the back button appeared twice (once too many), which was cleaned up before shipping.

---
