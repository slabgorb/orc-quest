---
parent: context-epic-38.md
workflow: trivial
---

# Story 38-9: Paper playtest calibration

## Business Context

The 16-cell interaction table was designed on paper but has not been playtested with real humans making real decisions under the commit-reveal protocol. Cell balance is a design hypothesis until validated. This story runs `duel_01.md` 3-5 times with different player pairs, annotates each exercised cell with calibration tags, and adjusts deltas for any cells that tag `lopsided` or `confusing`.

This is the calibration gate ADR-077 defines: "Run it, tag each cell with `calibrated | exciting | lopsided | confusing | dull`, and only expand to 8 maneuvers after the 4-maneuver table scores clean." The dogfight subsystem does not graduate to UI integration until this gate passes.

## Technical Guardrails

**Key files:**
- `sidequest-content/genre_packs/space_opera/dogfight/playtest/duel_01.md` — the scaffold to fill out per run
- `sidequest-content/genre_packs/space_opera/dogfight/interactions_mvp.yaml` — the table whose cells get tagged and potentially adjusted

**Process:**
1. Run 3-5 paper playtests using `duel_01.md` protocol (three humans: Red pilot, Blue pilot, GM)
2. After each run, fill in the Debrief section — especially per-cell calibration tags
3. Aggregate tags across runs: a cell that tags `lopsided` twice needs delta adjustment
4. For cells needing adjustment, modify the descriptor deltas in `interactions_mvp.yaml`
5. After adjustments, run at least one more playtest to verify the fix

**Calibration tag definitions (from interactions_mvp.yaml):**
- `exciting` — produced a memorable moment, keep as-is
- `calibrated` — worked as intended, no change needed
- `lopsided` — one pilot felt forced; review the deltas
- `confusing` — players couldn't parse the result; narration_hint weak
- `dull` — no meaningful consequence; consider removing the pair

**Expected distribution:**
- Mutual-kill cells should tag `exciting` (they are the decision pressure)
- Evasive-vs-offense cells should tag `calibrated` (safety valve)
- Passive-vs-passive should tag `dull` (the safety baseline — this is fine)
- If more than 2 cells tag `lopsided`, the delta math needs rework

## Scope Boundaries

**In scope:**
- Run 3-5 paper playtests of `duel_01.md`
- Fill in debrief sections with calibration tags and notes
- Adjust cell deltas in `interactions_mvp.yaml` for any failing cells
- Apply the extend-and-return rule from 38-8 if available; if not, use the ad-hoc "reset to merge with current energy" rule from the paper playtest
- Include hit severity from 38-7 if available; if not, use the ad-hoc "graze/clean/devastating, 2 grazes = kill" house rule

**Out of scope:**
- Expanding to 8 maneuvers (post-calibration, different story)
- Tail-chase starting state (38-10)
- Code changes — this is pure content validation
- Automated test creation from playtest results

## AC Context

**AC1: Minimum 3 complete playtest runs**
- Each run follows the full `duel_01.md` protocol: 3 turns or until one pilot is dead
- Each run has a filled debrief section with per-cell calibration tags
- Verify: 3+ completed debrief sections exist in `playtest/duel_01.md` (copies or appended runs)

**AC2: All exercised cells tagged**
- Every cell encountered across all runs has at least one calibration tag
- Note: 3 runs of 3 turns each exercises at most 9 of 16 cells. Not all cells will be exercised. Unexercised cells should be noted but not tagged.
- Verify: tag count matches unique cells exercised

**AC3: Failing cells adjusted**
- Any cell that tagged `lopsided` or `confusing` in 2+ runs has its deltas adjusted in `interactions_mvp.yaml`
- Each adjustment has a brief rationale comment in the YAML
- Verify: diff `interactions_mvp.yaml` before/after — adjusted cells have updated deltas and rationale

**AC4: Go/no-go assessment**
- The debrief's "Ready to expand to 8 maneuvers?" question is answered
- If "not yet", specific blockers are documented
- Verify: the go/no-go section is filled in with a clear answer and rationale

## Assumptions

- At least 3 humans are available to run the paper playtest (two pilots + GM). The playgroup (Keith, James, Alex, Sebastien) provides the pool.
- The extend-and-return rule (38-8) may not be formalized yet. If not, use the same ad-hoc reset the initial brainstorm used: "after a no-hit opening turn, both pilots reset to merge with current energy."
- Hit severity (38-7) may not be authored yet. If not, use the ad-hoc house rules from the initial design session.
