# Demo Script — 25-3

**Total runtime:** ~6 minutes

---

**Slide 1: Title** *(30 seconds)*
Introduce the story: "This sprint we cleaned up one of the central routing components in the game UI. Small change, meaningful impact on maintainability."

---

**Slide 2: Problem** *(1 minute)*
"Here's what the old `OverlayManager` looked like at the call site." Show the before block — 8 props being passed in: `characterData`, `inventoryData`, `mapData`, `journalEntries`, `knowledgeEntries`, `settingsProps`, `activeOverlay`, `onOverlayChange`. Ask the audience: "How many of those belong to a settings panel?" Answer: one. `settingsProps`. The other seven were squatters.

---

**Slide 3: What We Built** *(1 minute)*
Show the new `SettingsOverlay` call site — 3 props: `settingsProps`, `isOpen`, `onToggle`, `onClose`. "This is what a focused component looks like. Every prop earns its place."

Open `src/components/SettingsOverlay.tsx` in the editor. Walk through the 57-line file. Point out:
- `isTextInput()` helper: prevents Escape from firing while the player is typing
- `useEffect` + `useCallback` for keyboard listener lifecycle
- The backdrop `div` with click-to-dismiss and a nested panel that stops click propagation

---

**Slide 4: Why This Approach** *(1 minute)*
"Single responsibility isn't just a design principle — it's a cost-reduction strategy." Reference the before/after prop count: 8 → 4. Reference the test count: 28 tests, zero ambiguity about what's being tested.

---

**Before/After Slide** *(1 minute)*
Side-by-side: old `<OverlayManager>` block (8 props) vs new `<SettingsOverlay>` block (4 props). "The game data props were never the overlay's job. Now they're not its problem."

If live demo: run the test suite.
```bash
npx vitest run src/components/__tests__/SettingsOverlay.test.tsx
```
Expected output: 28 tests, all passing. If the command fails, fall back to the Before/After slide and show the passing test run screenshot.

---

**Roadmap Slide** *(1 minute)*
See Roadmap & Integration section below.

---

**Questions** *(remainder)*

---
