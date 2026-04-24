# Content Drift Triage — ADR-082 Python Port

Each row is a YAML field that the strict Python port rejects but the Rust port silently dropped. Triage each as:

- **ghost** — authored for a feature never built; delete from YAML (or file wiring story)
- **wire** — engine should consume this; add model field + engine reader + OTEL span
- **prose** — flavor for LLM prompts only; accept in model as pass-through, no consumer

Mark the correct column with `x`. After triage, run the follow-up scripts to generate content-delete PRs, model-fix stories, and pass-through fields.

Total rows: **29**

| Pack | File | Field | Error type | Example value | ghost? | wire? | prose? |
|------|------|-------|-----------|---------------|:------:|:-----:|:------:|
| elemental_harmony | `progression.yaml` | `affinities.[N].sub_paths` | extra_forbidden | `[{'name': 'Lightning Path', 'requirement': 'tier_2 Fire +…` |   |   |   |
| elemental_harmony | `progression.yaml` | `item_evolution.name_threshold` | extra_forbidden | `3` |   |   |   |
| elemental_harmony | `progression.yaml` | `item_evolution.power_bump_threshold` | extra_forbidden | `5` |   |   |   |
| elemental_harmony | `progression.yaml` | `synergies` | extra_forbidden | `[{'elements': ['Fire', 'Earth'], 'name': 'Magma', 'requir…` |   |   |   |
| elemental_harmony | `tropes.yaml` | `[N].escalation.[N].roles` | extra_forbidden | `['the-one-who-sacrifices']` |   |   |   |
| elemental_harmony | `inventory.yaml` | `currency.abbreviation` | extra_forbidden | `M` |   |   |   |
| elemental_harmony | `inventory.yaml` | `currency.description` | extra_forbidden | `Hammered copper and silver coins stamped with elemental s…` |   |   |   |
| heavy_metal | `prompts.yaml` | `ritual` | extra_forbidden | `When a character performs a pact_working, the prompt is t…` |   |   |   |
| heavy_metal | `prompts.yaml` | `debt_collection` | extra_forbidden | `When a Collector arrives to collect, the scene is not abo…` |   |   |   |
| heavy_metal | `beat_vocabulary.yaml` | `event_flavor` | extra_forbidden | `[{'event': 'gap_widens', 'descriptions': ['Your footfalls…` |   |   |   |
| heavy_metal | `beat_vocabulary.yaml` | `decision_framings` | extra_forbidden | `['The processional fills the colonnade — interrupt the ri…` |   |   |   |
| heavy_metal | `beat_vocabulary.yaml` | `chase_modes` | extra_forbidden | `['foot', 'pilgrim_road', 'colonnade']` |   |   |   |
| mutant_wasteland | `inventory.yaml` | `currency.abbreviation` | extra_forbidden | `S` |   |   |   |
| mutant_wasteland | `inventory.yaml` | `currency.description` | extra_forbidden | `There is no minted currency. Value is measured in salvage…` |   |   |   |
| mutant_wasteland | `inventory.yaml` | `currency.secondary` | extra_forbidden | `[{'name': 'Favor', 'abbreviation': 'Fv', 'description': "…` |   |   |   |
| space_opera | `rules.yaml` | `confrontations.[N].interaction_table.version` | missing | `{'_from': 'dogfight/interactions_mvp.yaml'}` |   |   |   |
| space_opera | `rules.yaml` | `confrontations.[N].interaction_table.starting_state` | missing | `{'_from': 'dogfight/interactions_mvp.yaml'}` |   |   |   |
| space_opera | `rules.yaml` | `confrontations.[N].interaction_table._from` | extra_forbidden | `dogfight/interactions_mvp.yaml` |   |   |   |
| space_opera | `inventory.yaml` | `philosophy.notes` | extra_forbidden | `Inventory is not the point of space opera. The ship carri…` |   |   |   |
| spaghetti_western | `rules.yaml` | `standoff_rules` | extra_forbidden | `{'sizing_up': {'description': "Before violence erupts, co…` |   |   |   |
| spaghetti_western | `rules.yaml` | `reputation_factions` | extra_forbidden | `[{'id': 'outlaws', 'name': 'Outlaws & Bandits', 'descript…` |   |   |   |
| spaghetti_western | `rules.yaml` | `reputation_effects` | extra_forbidden | `{'high': ['NPCs of this faction offer jobs, shelter, and …` |   |   |   |
| spaghetti_western | `rules.yaml` | `luck_rules` | extra_forbidden | `{'starting_luck': 3, 'max_luck': 5, 'spend_effects': [{'n…` |   |   |   |
| spaghetti_western | `char_creation.yaml` | `[N].choices.[N].mechanical_effects.reputation_bonus` | extra_forbidden | `intimidation` |   |   |   |
| spaghetti_western | `progression.yaml` | `affinities.[N].unlocks.novice` | extra_forbidden | `{'name': 'Steady Hand', 'description': 'The basics — you …` |   |   |   |
| spaghetti_western | `progression.yaml` | `affinities.[N].unlocks.journeyman` | extra_forbidden | `{'name': 'Dead Eye', 'description': 'You see the fight be…` |   |   |   |
| spaghetti_western | `progression.yaml` | `affinities.[N].unlocks.expert` | extra_forbidden | `{'name': 'Legendary Shot', 'description': 'Your reputatio…` |   |   |   |
| spaghetti_western | `progression.yaml` | `affinities.[N].unlocks.master` | extra_forbidden | `{'name': 'The Fastest', 'description': 'There is no one f…` |   |   |   |
| spaghetti_western | `prompts.yaml` | `session_opener_template` | extra_forbidden | `The sun sits high and white in a sky that has forgotten w…` |   |   |   |

