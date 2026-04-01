---
name: 'step-08-playtest'
description: 'Run playtest to verify content plays well, iterate on findings'

wipFile: '{wip_file}'
---

<purpose>Verify generated content works in an actual game session. Run a playtest, interpret results, fix content issues, and iterate until the world plays well.</purpose>

<instructions>Use sq-playtest skill to run a playtest. Focus on content bugs, not engine bugs. Iterate fixes and re-test.</instructions>

<output>Playtest report with content verified. WIP archived. stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8].</output>

# Step 8: Playtest & Iterate

**Progress: Step 8 of 8**

## CONTEXT

- Content has passed validation in Step 5.
- This step verifies the content **plays well** — distinct from structural correctness.
- **Content bugs** (bad names, missing lore, broken factions) → fix here.
- **Engine bugs** (crashes, wiring issues, protocol errors) → hand off to SM via scratch file.

## SEQUENCE

### 1. Run Playtest

Use `/sq-playtest` to launch a test session:
- Select the target genre/world
- Play through character creation
- Explore 2-3 regions
- Interact with NPCs
- Trigger at least one trope beat
- Test faction dynamics

### 2. Evaluate Results

Check for:

a) **Naming consistency** — Do generated names fit the cultural voice?
b) **Lore coherence** — Do NPC dialogue and narration reference the right history/legends?
c) **Cartography flow** — Do regions connect logically? Does travel make sense?
d) **Faction presence** — Do factions appear in narration? Do their goals conflict visibly?
e) **Tone alignment** — Does the world feel like it belongs to its genre?
f) **Visual quality** — Do Flux-generated images match the visual_style.yaml direction?
g) **Audio mood** — Does music classification produce the right tracks for scenes?

### 3. Fix Content Issues

For each content issue:
1. Identify the source file
2. Make the fix
3. Re-validate with `/sq-audit`

**Engine bugs → do NOT fix.** Write to scratch file for SM routing:
```markdown
## Engine Bug: {description}
- Found during: world-builder playtest of {genre}/{world}
- Symptoms: {what happened}
- Expected: {what should happen}
- Likely location: {guess at code path}
```

### 4. Re-test if Needed

If significant fixes were made, run another playtest to verify. Iterate until satisfied.

### 5. Archive WIP

Update WIP frontmatter: `stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]`, `status: 'complete'`

Archive: move `{wipFile}` to `.session/world-builder-{genre}-{world}-complete-{date}.md`

### 6. Commit Content

Stage all new/modified content files in sidequest-content:
```bash
cd sidequest-content
git checkout -b feat/{genre}-{world}
git add genre_packs/{genre}/
git commit -m "feat: {genre}/{world} — new world content"
```

Push and create PR targeting develop.

Report final status to user.
