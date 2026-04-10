# Demo Script — 27-9

**Total estimated time: 8 minutes**

---

**Slide 1: Title — "Narration Protocol Cleanup (ADR-076)" [0:00–0:30]**

Open on the title slide. One sentence: "We removed 60% of dead narration infrastructure left over from the voice-acting feature."

---

**Slide 2: Problem — The Dead Mailroom [0:30–2:00]**

Walk through the mailroom analogy. Point out: before this story, the API protocol had a `NarrationChunk` message type with *zero production senders* — the server code could reference it but nothing ever sent one. The UI had a watchdog timer (`setTimeout`) running on every narration event, waiting for chunks that were never coming.

Exact data point to cite: **`grep -r "NarrationChunk" sidequest-api sidequest-ui`** returned hits in the protocol definition and UI type files — but zero hits in any message-sending code path. A live type with no senders.

*Fallback if live terminal unavailable: Slide 2 shows the before/after grep output as a code block.*

---

**Slide 3: What We Built — The Deletion [2:00–4:30]**

> **Live demo sequence:**

1. Open `sidequest-api/crates/sidequest-protocol/src/message.rs` — show the `GameMessage` enum. `NarrationChunk` is gone. The only narration-related variants are `Narration` (the full text) and `NarrationEnd` (the turn-completion marker).

2. Open `sidequest-ui/src/App.tsx` — navigate to the narration buffer section (was lines 180–264). Show that `flushNarrationBuffer` is now ~15 lines, not 85. No `buf.chunks`, no `watchdogTimer`, no `handleBinaryMessage`.

3. Run the wiring check live:
   ```bash
   grep -r "NarrationChunk\|NarrationChunkPayload\|handleBinaryMessage\|buf\.chunks" sidequest-api sidequest-ui
   ```
   Expected output: **no matches**. This is the acceptance gate from ADR-076.

4. Run the test suite:
   ```bash
   just check-all
   ```
   Expected: all green. Point out the serde round-trip test for `NarrationChunk` is also gone — the test proved a dead type serialized correctly, which was testing nothing useful.

*Fallback: if `just check-all` is slow, skip to Slide 3 which shows the CI green badge.*

---

**Slide 4: Why This Approach — Compiler as Enforcer [4:30–5:30]**

Key point: leaving dead enum variants in Rust is worse than in most languages. Rust's exhaustive pattern matching means every `match` on `GameMessage` has to handle `NarrationChunk` — or suppress the warning. By removing the variant, we turned a "please ignore this" annotation into a compile-time guarantee. The type system now reflects reality.

---

**Before/After Slide [5:30–6:30]**

| | Before | After |
|---|---|---|
| `GameMessage` variants | Included `NarrationChunk` (0 senders) | Removed |
| UI narration buffer | 85 lines, watchdog timer, chunk accumulator | ~15 lines, single flush |
| UI type definitions | `NarrationChunkPayload` interface present | Removed |
| Protocol test suite | Serde round-trip test for dead type | Removed |

---

**Roadmap Slide [6:30–7:30]** — see section below.

---

**Questions [7:30–8:00]**

---
