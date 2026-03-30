# Demo Script — 14-5

**Setup:** Have a SideQuest session running in a browser tab. Start from the main menu. No server-side setup required — this is entirely a frontend flow.

---

**Scene 1 — Title (0:00–0:30) → Slide 1**

Open with the slide. Say: *"We're shipping something small that matters a lot: the ability to change your mind during character creation."*

---

**Scene 2 — Problem (0:30–1:30) → Slide 2**

Walk through the problem. Say: *"Until now, character creation was a trap door. You pick a name, choose your traits, select your archetype — and the moment you hit Confirm, that's it. No preview, no going back. If you misread something or changed your mind at the last second, your only option was to close the panel and start completely over. First-time players hit this constantly."*

**Fallback:** If browser isn't available, describe a player mistyping their character name on a touch device and discovering there's no correction path.

---

**Scene 3 — What We Built (1:30–4:00) → Slide 3**

Click into the character creation flow in the browser.

1. Walk through the steps: enter a character name (use **"Aldric Vorne"**), select a trait (pick **"Cunning"**), choose an archetype (pick **"Rogue"**).
2. Instead of immediately creating the character, the UI now transitions to the **Review screen**.
3. Point to the screen: *"This is new. Before we could create a character, the player sees a summary: name, trait, archetype — everything they chose, laid out for review."*
4. Point to the **Back button**. Click it. Say: *"If they spot something wrong — say they meant to pick Duelist instead of Rogue — they press Back."*
5. The flow returns to the archetype step. Change the selection to **"Duelist"**.
6. Arrive back at the Review screen, now showing **"Duelist"** as the updated choice.
7. Click **Create Character**. The character is created. Say: *"And now they confirm with confidence."*

**Fallback:** If the browser demo fails, switch to Slide 3 and show the before/after screenshots. Walk through the Review screen screenshot pointing to: character name field, trait badge, archetype label, Back button, and Create Character button.

---

**Scene 4 — Why This Approach (4:00–5:00) → Slide 4**

Say: *"We could have added back-navigation to every single step — but that's a lot of complexity for a problem that only needs one solution: show the player everything before they commit. One review screen, one back button. Simple, predictable, hard to break."*

Point out that the review screen is live — it always shows the player's current choices, not a cached version from earlier in the session. That was the key engineering requirement: the state had to be fresh every time the review screen appeared.

---

**Scene 5 — Roadmap (5:00–5:45) → Roadmap Slide**

Say: *"This is the last piece needed before character creation is fully polished. The flow now has a clear start, middle, and confirmation step. It sets us up for future work: saving draft characters, pre-filling from a template, or supporting character editing post-creation."*

---

**Scene 6 — Questions (5:45–6:00) → Questions Slide**

---
