# Demo Script — 13-8

**Setup:** Have a local multiplayer session running with 2 players. Have the narrator call log visible in a terminal pane.

**Slide 2 – Problem**
- Show the pre-fix behavior: two players submit actions simultaneously.
- Point to the terminal: narrator is invoked twice within milliseconds of each other.
- Show the two divergent narration strings — same prompt, different outputs. Say: "These two players are now in different stories."

**Slide 3 – What We Built**
- Show the updated `barrier.rs` handler election logic (the `AtomicBool` / lock acquisition).
- Walk through the flow: "First handler grabs the lock → calls narrator once → stores result in broadcast channel → second handler receives result, skips its own call."

**Slide 4 – Why This Approach**
- Diagram: N handlers → single elected narrator → broadcast result → all handlers proceed.
- Emphasize: no queue, no bottleneck, parallel resume after result is available.

**Before/After Slide**
- Left column: log showing 2 narrator calls, 2 different narration strings, world state written twice.
- Right column: log showing 1 narrator call, single narration string, world state written once.
- Exact terminal command to reproduce (post-fix): `cargo test --package sidequest-game test_single_narrator_call -- --nocapture`
- Expected output: `narrator called: 1 time` and both handler results showing identical narration text.

**Fallback:** If live demo fails, show the test output screenshot: the assertion `assert_eq!(narrator_call_count, 1)` passing, and the two handlers printing identical narration strings.

---
