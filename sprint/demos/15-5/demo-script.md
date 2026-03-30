# Demo Script — 15-5

**Total runtime:** ~6 minutes

**Slide 1 — Title (0:00–0:30)**
Open with: "This is a 2-point cleanup story from our post-playtest debt audit. Small surface area, but it closes a confusion trap that would have cost us real time."

**Slide 2 — Problem (0:30–1:30)**
Walk through the problem: "Our daemon client had comment labels saying 'stub — Dev fills in fields' on types that were 100% implemented. Show a before/after of `types.rs` lines 17, 155, and 189. The old labels said 'Stub Types' and 'Stub Results.' The new labels just name the section — 'Request Types,' 'Result Types.'"

If live terminal available:
```bash
cd ~/Projects/sidequest-api
git show feat/15-5-daemon-client-typed-api:crates/sidequest-daemon-client/src/types.rs | head -30
```
Fallback: Slide 3 (Before/After code snippet).

**Slide 3 — What We Built (1:30–3:00)**
"We confirmed the full data flow. Let me show you the wire path:"
```bash
grep -n "RenderParams\|TtsParams\|WarmUpParams\|build_request_json" \
  crates/sidequest-daemon-client/src/client.rs
```
Expected output: lines 8–11 (imports) and lines 96, 159, 170 (method usage). Point out: "Every type appears twice — once imported, once used in a real method. No orphans."

**Slide 4 — Why This Approach (3:00–4:00)**
"We had three options: wire what's missing, delete what's dead, or correct the labels. Investigation showed it was option three — the code was already correct. Touching working code for no reason is how you introduce bugs."

**Slide 5 — Test Results (4:00–5:00)**
```bash
cd ~/Projects/sidequest-api
cargo test 2>&1 | tail -5
```
Expected: `test result: ok. 659 passed; 0 failed; 0 ignored`
Fallback: Slide 5 screenshot showing 659/659 green.

**Slide 6 — Roadmap (5:00–6:00)**
"One item was flagged but deferred — a silent fallback at `types.rs:199` that swallows serialization errors. It's pre-existing, not introduced here, and logged for a future story. No new technical debt added."

---
