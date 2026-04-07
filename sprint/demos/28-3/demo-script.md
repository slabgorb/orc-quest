# Demo Script — 28-3

**Scene 1 (0:00–0:45) — Slide 2: Problem**
Open the confrontation overlay screenshot or recorded clip showing the empty beat panel. Point out: "The overlay appeared, the health bar tracked, but there were zero buttons. Players had no way to engage with the confrontation mechanics. This wasn't a style choice — it was a hardcoded empty list in the code."

**Scene 2 (0:45–2:00) — Slide 3: What We Built (live terminal)**
From the repo root:
```bash
just api-test
```
Watch the `confrontation_beats_wiring_story_28_3_tests` suite pass. Call out the test names in the output:
- `beats_populated_from_known_def` — 2 beats returned for a standoff def
- `beat_def_maps_to_confrontation_beat_fields` — id="draw", label="Draw", stat_check="REFLEX", risk="Miss and take damage"
- `spaghetti_western_standoff_beats_map_to_protocol` — real genre pack, 4 beats: **Size Up**, **Bluff**, **Flinch**, **Draw**

*Fallback if tests fail:* Show Slide 3 with the test output screenshot.

**Scene 3 (2:00–3:00) — Slide 4: Why This Approach**
Show the `sidequest-content/genre_packs/spaghetti_western/rules.yaml` confrontations block (visible above). "The data was already here. We connected it."

**Scene 4 (3:00–4:00) — Optional Before/After Slide**
Show side-by-side: old protocol message with `beats: []` vs. new message with 4 populated beat objects. Key field: `beat_count: 4`, `beat_ids: ["size_up", "bluff", "flinch", "draw"]`.

**Scene 5 (4:00–4:30) — GM Panel OTEL**
In the GM panel watcher stream, point to the `encounter.beats_sent` event: `encounter_type=standoff`, `beat_count=4`. "This is the lie detector. If beats aren't flowing, this event is absent and you know immediately."

---
