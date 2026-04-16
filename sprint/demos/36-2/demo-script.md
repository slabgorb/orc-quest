# Demo Script — 36-2

### Scene 1 — Title (0:00–0:30) · Slide 1

Open with the story title on screen. Introduce the theme: "We cleaned up the wiring behind the walls."

### Scene 2 — The Problem (0:30–1:30) · Slide 2

Show a terminal with the old function signature. Display it raw:

```bash
cd ~/Projects/oq-2/sidequest-api
git show HEAD~1 -- crates/sidequest-server/src/dispatch/connect.rs | head -50
```

Walk the audience through the wall of arguments ending at argument 29. Point out the suppression comment: `// 29 args — way over clippy's limit of 7`. Explain what "clippy" is in one sentence: Rust's built-in code quality checker, equivalent to a linter.

*Fallback: If terminal fails, switch to Slide 2 showing a screenshot of the old signature.*

### Scene 3 — What We Built (1:30–3:00) · Slide 3

Switch to the new version:

```bash
git show HEAD -- crates/sidequest-server/src/dispatch/connect.rs | head -60
```

Show `ConnectContext<'a>` — the same 29 fields, now named and grouped in a struct. Show the call site: one object constructed, one argument passed. Highlight that the `#[allow(clippy::too_many_arguments)]` line is gone.

*Fallback: Slide 3 showing before/after side-by-side.*

### Scene 4 — Tests Confirm No Regression (3:00–4:00) · Slide 4

Run the test suite live:

```bash
cd ~/Projects/oq-2 && just api-test 2>&1 | tail -20
```

Show green. Explain: 22 structural tests were written first in RED (failing), then the refactor was written to make them GREEN. This is TDD as a safety net, not documentation theater.

*Fallback: Slide 4 showing test output screenshot.*

### Scene 5 — Roadmap (4:00–4:30) · Roadmap Slide

This story unblocks a pattern that will be reused across the dispatch layer. Point to story 36-3 (if applicable) or the broader ADR-063 dispatch handler splitting work.

---
