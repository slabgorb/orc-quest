# Demo Script — 35-11

**Slide 2 — Problem**
Open the repo in your editor. Point to `src/components/`. Note: these two files are no longer there. Before this change, a developer landing in that folder would see `LayoutModeSelector.tsx` and `TurnModeIndicator.tsx` and reasonably ask: "Where are these used? Should I be calling these somewhere?" The answer was nowhere — but there was no way to know that without grepping the whole codebase.

**Slide 3 — What We Built**
Show the git diff: `git show 350b1cb --stat`
Output: 4 files changed, 2 insertions(+), 161 deletions(-)
Simple point: this PR made the codebase 159 net lines smaller with zero user-visible impact.

**Slide 4 — Why This Approach**
Show the grep that confirmed zero consumers:
```bash
grep -r "LayoutModeSelector\|TurnModeIndicator" src/
```
No results. That's the whole case. If anything imports a component, it stays. If nothing does, it goes.

**Before/After Slide (optional)**
Before: `src/__tests__/layout-modes.test.tsx` had 93 lines including a describe block testing a component that was never rendered. After: 31 tests remain — all for live code.

*Fallback if live demo fails:* Show Slide 3 with the stat line above as a code block.

---
