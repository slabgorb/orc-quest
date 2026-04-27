# Demo Script — 37-49

**Total runtime:** 4 minutes

---

**Slide 1 — Title (0:00–0:20)**
Introduce: "Today we're closing a gap that was silently hiding test failures across five parts of the codebase."

---

**Slide 2 — Problem (0:20–1:15)**
Reference Slide 2 directly. Say: "Here's what our test output looked like before the fix." Open a terminal and run:

```bash
cd /path/to/sidequest-ui && npx vitest run --reporter=verbose 2>&1 | grep "useLoader"
```

Point to the output lines showing `TypeError: useLoader is not a function` repeating across multiple files. Note that this error appears in the character creation flow, the confrontation system, and the dice overlay — three distinct product areas, one shared root cause.

*Fallback: If the pre-fix environment isn't available, show the screenshot on Slide 2 of the error log.*

---

**Slide 3 — What We Built (1:15–2:00)**
Reference Slide 3. "The fix was surgical — one change to the shared test configuration." Show the diff (or describe it): a single mock entry added to the test setup file telling the test runner "when any component asks for `useLoader`, hand it this lightweight substitute."

---

**Slide 4 — Why This Approach (2:00–2:30)**
Reference Slide 4. "We could have patched each of the five files individually. We didn't, because that would mean five places to break again. One fix, one location, permanent solution."

---

**Before/After slide (2:30–3:00)**
Run the test suite live:

```bash
npx vitest run src/__tests__/character-creation-wiring.test.tsx src/__tests__/confrontation-wiring.test.tsx src/__tests__/dice-overlay-wiring-34-5.test.tsx src/__tests__/deterministicReplay.test.tsx src/__tests__/DiceOverlay.test.tsx --reporter=verbose
```

Point to all five files showing green. "Forty-five tests, all passing. Nothing added, nothing changed in the product — just the safety net restored."

*Fallback: Show the before/after slide with the pass count comparison (0 → 45).*

---

**Roadmap slide (3:00–3:30)**
"This unblocks the multiplayer work. The dice system is central to confrontations, and confrontations are central to combat — which is exactly where the next sprint is headed."

---

**Questions (3:30–4:00)**

---
