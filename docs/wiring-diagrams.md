# SideQuest — Wiring Diagrams

> End-to-end signal traces for every major feature. Each diagram shows the path from
> visible UI feature through server layers to storage, with file paths and function names.
>
> **Last updated:** 2026-03-30
> **Source of truth:** `sidequest-api/crates/` — traced from actual code, not design docs.

---

## Table of Contents

1. [Core Turn Loop](#1-core-turn-loop) — Action → Narration → State Delta
2. [Image Generation](#2-image-generation) — Narration → Subject → Beat Filter → Daemon → IMAGE
3. [TTS Voice Pipeline](#3-tts-voice-pipeline) — Narration → Segments → Kokoro → Audio Chunks
4. [Music & Audio](#4-music--audio) — Narration → Mood → Track Selection → AUDIO_CUE
5. [Multiplayer Turn Barrier](#5-multiplayer-turn-barrier) — Sealed Letter Collection → Resolution
6. [Combat Flow](#6-combat-flow) — Detection → State Machine → COMBAT_EVENT
7. [Character Creation](#7-character-creation) — Builder State Machine → Character
8. [Pacing & Drama Engine](#8-pacing--drama-engine) — TensionTracker → Delivery Mode → Prompt
9. [Knowledge Pipeline](#9-knowledge-pipeline) — Footnotes → KnownFacts → Lore → Prompt
10. [NPC Personality (OCEAN)](#10-npc-personality-ocean) — Profiles → Behavioral Summary → Prompt
11. [Faction Agendas & Scene Directives](#11-faction-agendas--scene-directives) — Agendas → Directives → Narrator
12. [Slash Commands](#12-slash-commands) — /command → Router → Response
13. [Trope Engine](#13-trope-engine) — Tick → Beat Firing → Narrator Injection
14. [Session Persistence](#14-session-persistence) — GameSnapshot → SQLite → Recovery
15. [Genre Pack Loading](#15-genre-pack-loading) — YAML → Typed Structs → Session State

---

## 1. Core Turn Loop

The central pipeline from player input to narrated response.

```mermaid
flowchart TD
    A["Client: PLAYER_ACTION<br/>(WebSocket JSON)"] --> B["ws.rs:169<br/>serde_json::from_str"]
    B --> C["ws.rs:171<br/>dispatch_message()"]
    C --> D["dispatch.rs:331<br/>dispatch_player_action()"]

    D --> E["dispatch.rs:1541<br/>Slash command check"]
    E -->|"/command"| F["slash_router.rs:63<br/>try_dispatch()"]
    F --> Z2["Early return:<br/>NARRATION response"]
    E -->|"normal action"| G["dispatch.rs:2130<br/>preprocess_action()"]

    G --> H["dispatch.rs:1731<br/>Build state_summary<br/>(HP, location, inventory,<br/>NPCs, tropes, lore, axes,<br/>narration history)"]
    H --> I["dispatch.rs:2140<br/>TurnContext creation"]
    I --> J["orchestrator.rs:133<br/>IntentRouter::classify_with_state()"]

    J -->|"state override"| K1["Combat → CreatureSmith"]
    J -->|"state override"| K2["Chase → Dialectician"]
    J -->|"keyword match"| K3["Dialogue → Ensemble"]
    J -->|"default"| K4["Exploration → Narrator"]

    K1 & K2 & K3 & K4 --> L["orchestrator.rs:144<br/>agent.build_context()<br/>+ PromptBuilder.compose()"]
    L --> M["client.rs:195<br/>Command::new('claude')<br/>.arg('-p').arg(prompt)<br/>120s timeout"]
    M --> N["orchestrator.rs:177<br/>extract_structured_from_response()<br/>(footnotes, items, NPCs, quests)"]

    N --> O["dispatch.rs:2178<br/>extract_location_header()"]
    O --> P["dispatch.rs:2263<br/>Update NPC registry"]
    P --> Q["dispatch.rs:2374<br/>Apply combat patches"]
    Q --> R["dispatch.rs:2405<br/>Merge quest updates"]
    R --> S["dispatch.rs:2413<br/>XP + level progression"]
    S --> T["dispatch.rs:2570<br/>Extract items → inventory"]

    T --> U["dispatch.rs:2698<br/>GameMessage::Narration{<br/>text, state_delta, footnotes}"]
    U --> V["dispatch.rs:2741<br/>GameMessage::NarrationEnd"]
    V --> W["+ PARTY_STATUS<br/>+ INVENTORY<br/>+ MAP_UPDATE<br/>+ COMBAT_EVENT<br/>+ CHAPTER_MARKER"]

    W --> X["ws.rs:207<br/>tx.send(resp) → mpsc"]
    X --> Y["ws.rs:51<br/>writer_handle:<br/>rx.recv() → ws_sink.send()"]
    Y --> Z["Client: NARRATION<br/>(WebSocket JSON)"]

    style A fill:#4a9eff,color:#fff
    style Z fill:#4a9eff,color:#fff
    style Z2 fill:#4a9eff,color:#fff
    style M fill:#ff6b6b,color:#fff
```

**Key files:** `ws.rs` → `dispatch.rs` (1950 LOC monolith) → `orchestrator.rs` → `client.rs` → back through `dispatch.rs`

**Storage touched:** NPC registry, quest log, inventory, XP/level, narration history, lore store

---

## 2. Image Generation

Background pipeline — narration triggers render, result arrives asynchronously.

```mermaid
flowchart TD
    A["Narration text<br/>(clean_narration)"] --> B["dispatch.rs:3126<br/>SubjectExtractor::extract()<br/>(subject.rs)"]
    B --> C{"RenderSubject?"}
    C -->|"None"| Z1["No image this turn"]
    C -->|"Some(subject)"| D["dispatch.rs:3141<br/>BeatFilter::evaluate()<br/>(beat_filter.rs:212)"]

    D --> E{"FilterDecision"}
    E -->|"Suppress"| Z2["Filtered: low weight,<br/>cooldown, or duplicate"]
    E -->|"Render"| F["dispatch.rs:3148<br/>queue.enqueue()"]

    F --> G["state.rs:65<br/>Art style routing<br/>(visual_style overrides)"]
    G --> H["daemon-client/client.rs:89<br/>DaemonClient::render()<br/>Unix socket → /tmp/sidequest-renderer.sock<br/>300s timeout"]

    H --> I["sidequest-daemon (Python)<br/>Flux.1 schnell/dev<br/>GPU inference"]
    I --> J["RenderResult<br/>{image_url, generation_ms}"]

    J --> K["render_integration.rs:80<br/>Build ImagePayload<br/>(url, tier, scene_type, generation_ms)"]
    K --> L["render_integration.rs:108<br/>broadcast::send()<br/>GameMessage::Image"]
    L --> M["Client: IMAGE<br/>(async, arrives after narration)"]

    style A fill:#6c5ce7,color:#fff
    style M fill:#4a9eff,color:#fff
    style I fill:#00b894,color:#fff
```

**Beat filter gates:** weight threshold, cooldown timer, burst rate, duplicate hash suppression

**Render tiers:** portrait, scene, landscape, abstract, text, cartography, tactical

---

## 3. TTS Voice Pipeline

Parallel to narration delivery — segments synthesized and streamed as audio chunks.

```mermaid
flowchart TD
    A["Narration text"] --> B["dispatch.rs:3334<br/>SentenceSegmenter::segment()<br/>(segmenter.rs:56)"]
    B --> C["dispatch.rs:3345<br/>strip_markdown_for_tts()<br/>(narration.rs:205)"]
    C --> D["VoiceRouter::route(speaker)<br/>(voice_router.rs:106)<br/>→ VoiceAssignment"]

    D --> E["dispatch.rs:3383<br/>tokio::spawn TTS task"]
    E --> F["TtsMessage::Start<br/>→ AudioMixer::on_tts_start()<br/>→ duck music/ambience"]
    F --> G["GameMessage::TtsStart<br/>{total_segments}"]

    E --> H["Per segment loop"]
    H --> I["dispatch.rs:3806<br/>DaemonSynthesizer::synthesize()"]
    I --> J["daemon-client/client.rs:165<br/>DaemonClient::synthesize()<br/>Unix socket"]
    J --> K["sidequest-daemon (Python)<br/>Kokoro TTS engine<br/>24kHz PCM s16le"]
    K --> L["TtsResult<br/>{audio_bytes, duration_ms}"]

    L --> M["dispatch.rs:3484<br/>GameMessage::NarrationChunk<br/>(text to acting player)"]
    L --> N["dispatch.rs:3493<br/>Binary voice frame:<br/>[4B header len][JSON header][PCM bytes]"]
    N --> O["broadcast_binary() to all clients"]

    H --> P["After last segment"]
    P --> Q["AudioMixer::on_tts_end()<br/>→ restore volumes"]
    Q --> R["GameMessage::TtsEnd"]

    style A fill:#6c5ce7,color:#fff
    style G fill:#4a9eff,color:#fff
    style M fill:#4a9eff,color:#fff
    style O fill:#4a9eff,color:#fff
    style R fill:#4a9eff,color:#fff
    style K fill:#00b894,color:#fff
```

**Audio ducking:** Music and ambience volumes reduced during speech, restored after TTS_END

**Frame format:** `[uint32 header_len][JSON: {type, segment_id, sample_rate, format}][raw PCM]`

---

## 4. Music & Audio

Mood classification drives track selection with anti-repetition rotation.

```mermaid
flowchart TD
    A["Narration text"] --> B["dispatch.rs:3209<br/>MusicDirector::classify_mood()<br/>(music_director.rs:145)"]

    B --> C["MoodContext:<br/>in_combat, in_chase,<br/>party_health_pct,<br/>quest_completed, npc_died"]
    C --> D["MoodClassification:<br/>{primary: Mood, intensity, confidence}"]

    D --> E["MusicDirector::evaluate()<br/>(music_director.rs:156)"]
    E --> F["Look up mood_tracks<br/>from genre pack AudioConfig"]
    F --> G["ThemeRotator::select()<br/>(theme_rotator.rs:68)"]

    G --> H{"Anti-repetition<br/>filter"}
    H -->|"all exhausted"| I["Reset history"]
    H -->|"candidates remain"| J["Score by<br/>energy-to-intensity<br/>distance"]
    I --> J
    J --> K["Top candidate<br/>(randomize from top 3)"]

    K --> L["AudioMixer::apply_cue()<br/>(audio_mixer.rs)"]
    L --> M["dispatch.rs:3822<br/>audio_cue_to_game_message()"]
    M --> N["GameMessage::AudioCue<br/>{mood, music_track,<br/>channel, action, volume}"]
    N --> O["Client: AUDIO_CUE"]

    style A fill:#6c5ce7,color:#fff
    style O fill:#4a9eff,color:#fff
```

**Moods:** Combat, Exploration, Tension, Triumph, Sorrow, Mystery, Calm

**3 channels:** music, sfx, ambience — each with independent volume and action (play/fade_in/fade_out/duck/restore/stop)

**Rotation depth:** 3 tracks per mood before repeat allowed

---

## 5. Multiplayer Turn Barrier

Sealed letter pattern — all players submit, one handler resolves.

```mermaid
flowchart TD
    A["Player A: PLAYER_ACTION"] --> B["dispatch.rs:2039<br/>turn_mode.should_use_barrier()?"]
    A2["Player B: PLAYER_ACTION"] --> B2["dispatch.rs:2039<br/>should_use_barrier()?"]

    B -->|"Structured/Cinematic"| C["barrier.rs:255<br/>submit_action(player_a, action_a)"]
    B2 -->|"Structured/Cinematic"| C2["barrier.rs:255<br/>submit_action(player_b, action_b)"]

    C --> D["multiplayer.rs:292<br/>record_action() → HashMap"]
    C2 --> D

    D --> E["multiplayer.rs:305<br/>is_barrier_met()?<br/>actions.len() >= players.len()"]
    E -->|"yes"| F["inner.notify.notify_one()"]
    E -->|"no, wait"| G["barrier.rs:303<br/>wait_for_turn()<br/>tokio::select!{<br/>  notify.notified(),<br/>  sleep(adaptive_timeout)<br/>}"]

    G -->|"timeout"| H["barrier.rs:342<br/>force_resolve_turn()<br/>'hesitates, waiting'"]
    F --> I["barrier.rs:329<br/>resolution_lock.lock()"]
    H --> I

    I --> J["barrier.rs:365<br/>try_claim_resolution()"]
    J -->|"true (first caller)"| K["Elected handler:<br/>Gets combined actions<br/>Calls narrator with<br/>PARTY ACTIONS block"]
    J -->|"false (others)"| L["Non-elected:<br/>Receives narration<br/>via session broadcast"]

    K --> M["dispatch.rs:2698<br/>Narrator result"]
    M --> N["dispatch.rs:3661<br/>Broadcast to co-located players"]
    N --> O["Per-player perception filter<br/>(if effects active)"]
    O --> P["All players: NARRATION"]

    M --> Q["dispatch.rs:3717<br/>TURN_STATUS 'resolved'<br/>(global broadcast)"]

    style A fill:#4a9eff,color:#fff
    style A2 fill:#4a9eff,color:#fff
    style P fill:#4a9eff,color:#fff
```

**Adaptive timeout:** 3s for 2-3 players, 5s for 4+ (configurable tiers)

**Resolution lock:** `Mutex` ensures exactly one tokio task calls the narrator — others receive broadcast

**Perception filter:** If a player has perceptual effects, their narration copy is prefixed with `[Your perception is altered: ...]`

---

## 6. Combat Flow

Intent-based and keyword-fallback detection, with state machine transitions.

```mermaid
flowchart TD
    A["ActionResult from narrator"] --> B{"classified_intent<br/>== 'Combat'?"}
    B -->|"yes"| C["dispatch.rs:2826<br/>combat_state.set_in_combat(true)"]
    B -->|"no"| D{"Keyword scan:<br/>'attacks', 'lunges',<br/>'initiative'?"}
    D -->|"match"| C
    D -->|"no match"| E{"Keyword scan:<br/>'defeated', 'retreats',<br/>'surrender'?"}
    E -->|"match"| F["combat_state.set_in_combat(false)"]
    E -->|"no match"| G["No combat change"]

    C --> H["turn_mode.rs:36<br/>TurnMode::apply(<br/>CombatStarted)<br/>FreePlay → Structured"]
    F --> I["turn_mode.rs:36<br/>TurnMode::apply(<br/>CombatEnded)<br/>Structured → FreePlay"]

    C --> J["dispatch.rs:2370<br/>Apply CombatPatch<br/>(HP deltas, effects)"]
    J --> K["combat.rs:57<br/>advance_round()"]
    K --> L["combat.rs:140<br/>tick_effects()<br/>(decay status durations)"]

    L --> M["dispatch.rs:2950<br/>GameMessage::CombatEvent<br/>{in_combat, enemies,<br/>turn_order, current_turn}"]
    M --> N["Client: CombatOverlay"]

    style A fill:#6c5ce7,color:#fff
    style N fill:#4a9eff,color:#fff
```

**Turn mode FSM:** `FreePlay` ↔ `Structured` (on combat start/end), `FreePlay` → `Cinematic` (on cutscene)

**CombatState tracks:** round counter, damage log, status effects (with duration decay), drama_weight

---

## 7. Character Creation

Genre-driven scene-based state machine with bidirectional messages.

```mermaid
flowchart TD
    A["SESSION_EVENT{connect}<br/>genre, world, player_name"] --> B["dispatch.rs:439<br/>persistence.exists()?"]
    B -->|"returning"| C["Load GameSnapshot<br/>→ skip creation<br/>→ Playing state"]
    B -->|"new"| D["SESSION_EVENT{connected,<br/>has_character: false}"]

    D --> E["builder.rs<br/>CharacterBuilder::try_new()<br/>(genre scenes + rules)"]
    E --> F["builder.to_scene_message()<br/>→ CHARACTER_CREATION<br/>{phase: 'scene', scene_index,<br/>choices, allows_freeform}"]

    F --> G["Client: show scene"]
    G --> H["Client: CHARACTER_CREATION<br/>{phase: 'scene', choice}"]
    H --> I["dispatch.rs:983<br/>builder.apply_choice(index)"]
    I --> J{"More scenes?"}
    J -->|"yes"| F
    J -->|"no"| K["CHARACTER_CREATION<br/>{phase: 'confirmation',<br/>character_preview}"]

    K --> L["Client: confirm"]
    L --> M["dispatch.rs:996<br/>builder.build(player_name)"]
    M --> N["AccumulatedChoices →<br/>Character with CreatureCore<br/>(HP, AC, abilities, inventory)"]
    N --> O["CHARACTER_CREATION<br/>{phase: 'complete', character}"]
    O --> P["Session → Playing state"]
    P --> Q["LoreStore seeded from<br/>creation choices (story 11-3)"]

    style A fill:#4a9eff,color:#fff
    style G fill:#4a9eff,color:#fff
    style L fill:#4a9eff,color:#fff
```

**Accumulated from scenes:** class, race, personality, items, affinity, backstory fragments, stat bonuses, pronouns, rig type, catch phrase

**3 creation modes (ADR-016):** Menu (pick from list), Guided (follow prompts), Freeform (describe anything)

---

## 8. Pacing & Drama Engine

Dual-track tension model drives narration length and delivery speed.

```mermaid
flowchart TD
    A["Each turn: combat events,<br/>HP changes, action results"] --> B["tension_tracker.rs:397<br/>TensionTracker::observe()"]
    B --> C["Classify: Boring/Dramatic/Normal"]
    C --> D["Update action_tension<br/>(gambler's ramp)"]
    D --> E["Inject event spikes<br/>(critical hit, death save)"]

    F["Each turn"] --> G["tension_tracker.rs:209<br/>TensionTracker::tick()"]
    G --> H["action_tension *= 0.9<br/>(ACTION_DECAY)"]
    H --> I["Age existing spikes<br/>(linear decay)"]

    I --> J["tension_tracker.rs:137<br/>drama_weight =<br/>max(action, stakes, spike)"]
    J --> K["tension_tracker.rs:214<br/>pacing_hint()"]

    K --> L{"drama_weight<br/>thresholds"}
    L -->|"> streaming_min"| M["DeliveryMode::Streaming<br/>(word-by-word)"]
    L -->|">= sentence_min"| N["DeliveryMode::Sentence<br/>(sentence-by-sentence)"]
    L -->|"< sentence_min"| O["DeliveryMode::Instant<br/>(full text)"]

    K --> P["PacingHint::<br/>narrator_directive()"]
    P --> Q["'Target N sentences.<br/>Drama level: X%.'"]

    K --> R{"boring_streak >=<br/>escalation_streak?"}
    R -->|"yes"| S["Inject escalation beat"]
    R -->|"no"| T["No escalation"]

    Q --> U["prompt_framework/mod.rs:82<br/>register_pacing_section()<br/>Late attention zone"]
    S --> U
    U --> V["Narrator prompt<br/>(length + urgency guidance)"]

    style V fill:#ff6b6b,color:#fff
```

**Genre-tunable:** `pacing.yaml` in genre pack sets `streaming_delivery_min`, `sentence_delivery_min`, `escalation_streak`

**Dual tracks:** Action tension (gambler's ramp from boring streaks) + Stakes tension (HP ratio) + Event spikes (discrete dramatic moments)

---

## 9. Knowledge Pipeline

Narrator footnotes become persistent facts that feed back into future prompts.

```mermaid
flowchart TD
    A["Narrator response:<br/>prose + JSON block"] --> B["orchestrator.rs:325<br/>extract_structured_from_response()"]
    B --> C["footnotes: Vec&lt;Footnote&gt;<br/>{marker, summary, category,<br/>is_new, fact_id}"]

    C --> D["dispatch.rs:2698<br/>Attach to NarrationPayload<br/>(sent to client)"]
    D --> E["Client: render [N] superscripts<br/>+ footnote entries below narration"]

    C --> F["dispatch.rs:2723<br/>footnotes_to_discovered_facts()<br/>(footnotes.rs:20)"]
    F --> G{"is_new?"}
    G -->|"true"| H["Create DiscoveredFact<br/>{content, category, turn,<br/>source: Discovery,<br/>confidence: Certain}"]
    G -->|"false"| I["Callback to existing<br/>KnownFact via fact_id"]

    H --> J["Character.known_facts<br/>accumulation"]
    J --> K["Next turn:<br/>prompt_framework/mod.rs:173<br/>register_knowledge_section()"]
    K --> L["[CHARACTER's KNOWLEDGE]<br/>Top 20 facts by recency<br/>with confidence tags<br/>Valley attention zone"]
    L --> M["Narrator prompt<br/>(don't-repeat constraint)"]

    H --> N["lore.rs:430<br/>accumulate_lore()<br/>→ LoreStore"]
    N --> O["lore.rs:354<br/>select_lore_for_prompt()<br/>(budget-aware, keyword-hinted)"]
    O --> P["Narrator/agent prompts<br/>(grounding zone)"]

    style A fill:#6c5ce7,color:#fff
    style E fill:#4a9eff,color:#fff
    style M fill:#ff6b6b,color:#fff
    style P fill:#ff6b6b,color:#fff
```

**FactCategory:** Lore, Place, Person, Quest, Ability

**Lore budget:** Token-aware selection prevents prompt bloat (content.len / 4 token estimate)

**Feedback loop:** Footnotes → KnownFacts → prompt injection → narrator avoids repeating → new footnotes

---

## 10. NPC Personality (OCEAN)

Big Five profiles loaded from genre packs, summarized into narrator prompts.

```mermaid
flowchart TD
    A["Genre pack YAML<br/>archetypes.yaml"] --> B["GenreLoader<br/>(sidequest-genre)"]
    B --> C["NPC struct<br/>ocean: Option&lt;OceanProfile&gt;"]

    C --> D["models.rs:119<br/>OceanProfile::behavioral_summary()"]
    D --> E{"Score thresholds"}
    E -->|"<= 3.0"| F["Low descriptor<br/>(e.g., 'reserved', 'blunt')"]
    E -->|">= 7.0"| G["High descriptor<br/>(e.g., 'gregarious', 'meticulous')"]
    E -->|"3.1 - 6.9"| H["Omitted (neutral)"]

    F & G --> I["Joined string:<br/>'reserved and meticulous,<br/>curious and imaginative'"]
    H --> J["Fallback:<br/>'balanced temperament'"]

    I --> K["prompt_framework/mod.rs:109<br/>register_ocean_personalities_section()"]
    J --> K
    K --> L["## NPC Personalities<br/>- Grimjaw: cautious and stubborn<br/>- Lyra: gregarious and creative<br/>Valley attention zone"]
    L --> M["Narrator prompt"]

    C --> N["ocean_shift_proposals.rs<br/>propose_ocean_shifts()<br/>(IMPLEMENTED but NOT WIRED<br/>to game flow — story 15-2)"]
    N -.->|"future"| O["Post-narration pipeline:<br/>detect PersonalityEvents →<br/>apply shifts → log"]

    style A fill:#fdcb6e,color:#333
    style M fill:#ff6b6b,color:#fff
    style N fill:#b2bec3,color:#333
```

**5 dimensions:** Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism (0.0-10.0)

**Agreeableness → Disposition:** A-dimension feeds the existing -15 to +15 disposition system

**Gap:** OCEAN shift proposals are implemented but not wired into the game flow (Epic 15, story 15-2)

---

## 11. Faction Agendas & Scene Directives

Factions pursue goals that inject into every narrator turn.

```mermaid
flowchart TD
    A["Genre pack world YAML<br/>factions section"] --> B["faction_agenda.rs:71<br/>FactionAgenda::try_new()"]
    B --> C["FactionAgenda<br/>{faction_name, goal,<br/>urgency, event_text}"]

    C --> D{"urgency"}
    D -->|"Dormant"| E["Filtered out"]
    D -->|"Simmering/Pressing/Critical"| F["scene_directive.rs:123<br/>agenda.scene_injection()"]

    F --> G["scene_directive.rs:94<br/>format_scene_directive()"]

    H["Trope engine:<br/>fired_beats"] --> G
    I["Active stakes"] --> G

    G --> J["SceneDirective<br/>{trope_beats, faction_events,<br/>active_stakes, hints}"]
    J --> K["prompt_framework/mod.rs:148<br/>register_scene_directive()"]
    K --> L["render_scene_directive()<br/>(mod.rs:26)"]
    L --> M["[SCENE DIRECTIVES — MANDATORY]<br/>Priority-sorted elements:<br/>- TropeBeat instructions<br/>- FactionEvent injections<br/>- ActiveStake markers<br/>Early attention zone"]
    M --> N["Narrator prompt<br/>(high priority, after identity)"]

    style A fill:#fdcb6e,color:#333
    style N fill:#ff6b6b,color:#fff
```

**Urgency levels:** Dormant (filtered), Simmering, Pressing, Critical

**Mandatory weave:** Scene directives use EARLY attention zone — narrator must incorporate them

---

## 12. Slash Commands

Server-side interception before intent classification.

```mermaid
flowchart TD
    A["PLAYER_ACTION<br/>{action: '/status'}"] --> B["dispatch.rs:1541<br/>slash_router check"]
    B --> C["slash_router.rs:63<br/>try_dispatch(input, state)"]
    C --> D{"starts with '/'?"}
    D -->|"no"| E["Pass through to<br/>intent classification"]
    D -->|"yes"| F["Parse: command + args"]

    F --> G{"command"}
    G --> H["/status → StatusCommand<br/>(commands.rs:11)"]
    G --> I["/inventory → InventoryCommand<br/>(commands.rs:44)"]
    G --> J["/map → MapCommand"]
    G --> K["/save → SaveCommand"]
    G --> L["/help → Built-in list"]
    G --> M["/tone → ToneChange"]
    G --> N["/gm → GM suite<br/>(set, teleport, spawn, dmg)"]

    H --> O["CommandResult::Display(text)"]
    I --> P["CommandResult::Display(text)"]
    N --> Q["CommandResult::StateMutation(patch)"]
    M --> R["CommandResult::ToneChange(axes)"]

    O --> S["NARRATION response<br/>(early return)"]
    P --> T["INVENTORY response"]
    Q --> U["Apply patch + NARRATION"]
    R --> V["Update axis_values + NARRATION"]

    style A fill:#4a9eff,color:#fff
    style S fill:#4a9eff,color:#fff
    style T fill:#4a9eff,color:#fff
    style U fill:#4a9eff,color:#fff
    style V fill:#4a9eff,color:#fff
```

**No LLM call:** Slash commands resolve mechanically — no Claude subprocess, no intent classification

**GM commands:** Protected by role check, allow direct state manipulation for debugging

---

## 13. Trope Engine

Genre-defined narrative pacing via trope lifecycle and beat injection.

```mermaid
flowchart TD
    A["Genre pack tropes.yaml<br/>+ world overrides"] --> B["TropeDefinition<br/>{id, name, beats at thresholds,<br/>stakes, NPCs, themes}"]
    B --> C["Session init:<br/>TropeState per definition<br/>(progression: 0.0)"]

    D["Each turn"] --> E["Passive tick:<br/>progression += genre_rate"]
    E --> F{"progression crosses<br/>beat threshold?"}
    F -->|"yes"| G["Fire beat:<br/>FiredBeat{name, event,<br/>stakes, npcs, hints}"]
    F -->|"no"| H["No beat this turn"]

    G --> I["troper.rs:132<br/>build_beats_context()"]
    I --> J["[TROPE BEATS — MANDATORY WEAVE]<br/>Per beat:<br/>  TROPE: name + threshold%<br/>  BEAT EVENT: instruction<br/>  STAKES: what's at risk<br/>  NPCS INVOLVED: list<br/>  NARRATIVE HINTS: enriched<br/>Early attention zone"]

    K["Active tropes (progressing)"] --> L["troper.rs:174<br/>active trope summary"]
    L --> M["Background context on<br/>progressing narrative arcs"]

    J --> N["Narrator prompt"]
    M --> N

    G --> O["scene_directive.rs:94<br/>Also injected into<br/>SceneDirective.trope_beats"]

    style A fill:#fdcb6e,color:#333
    style N fill:#ff6b6b,color:#fff
```

**Trope lifecycle:** Progression 0.0 → 1.0 with beats firing at defined thresholds

**Engagement multiplier:** Scale progression rate by player engagement (turns_since_meaningful)

---

## 14. Session Persistence

Atomic save after every turn, full recovery on reconnect.

```mermaid
flowchart TD
    A["Turn completes"] --> B["dispatch.rs:3273<br/>Build GameSnapshot<br/>(all session state)"]
    B --> C["dispatch.rs:3308<br/>persistence.save()"]
    C --> D["PersistenceHandle<br/>(async wrapper)"]
    D --> E["oneshot channel →<br/>PersistenceWorker<br/>(dedicated OS thread)"]

    E --> F["persistence.rs:242<br/>SqliteStore::save()"]
    F --> G["serde_json::to_string<br/>(full GameSnapshot)"]
    G --> H["rusqlite transaction:<br/>INSERT OR REPLACE<br/>game_state(snapshot_json)"]

    I["Narration text"] --> J["persistence.rs:288<br/>append_narrative()"]
    J --> K["INSERT narrative_log<br/>(round, author, content, tags)"]

    L["Client reconnects<br/>SESSION_EVENT{connect}"] --> M["dispatch.rs:439<br/>persistence.exists()?"]
    M -->|"true"| N["persistence.rs:261<br/>SqliteStore::load()"]
    N --> O["SELECT snapshot_json<br/>FROM game_state"]
    O --> P["serde_json::from_str<br/>→ GameSnapshot"]
    P --> Q["Restore all session state:<br/>character, location, quests,<br/>NPCs, tropes, inventory,<br/>axis values, lore"]
    Q --> R["persistence.rs:284<br/>Generate recap from<br/>recent narrative_log entries"]
    R --> S["SESSION_EVENT{ready}<br/>with initial_state + recap"]

    style A fill:#6c5ce7,color:#fff
    style L fill:#4a9eff,color:#fff
    style S fill:#4a9eff,color:#fff
    style H fill:#e17055,color:#fff
    style K fill:#e17055,color:#fff
```

**Schema:** 3 tables — `session_meta`, `game_state` (single row, full JSON), `narrative_log` (append-only)

**Actor pattern:** `rusqlite::Connection` is `!Send` — wrapped in dedicated OS thread with mpsc command channel

**One DB per session:** `{save_dir}/{genre}/{world}/{player}/save.db`

**GameSnapshot includes:** characters, NPCs, combat, chase, tropes (full TropeState), quests, lore, axis values, achievements, campaign maturity, world history, NPC registry

---

## 15. Genre Pack Loading

Lazy binding — packs loaded per-session on connect, not at startup.

```mermaid
flowchart TD
    A["Server starts<br/>main.rs:36<br/>genre_packs_path from CLI"] --> B["AppState stores path<br/>(no eager loading)"]

    C["Player connects<br/>SESSION_EVENT{connect}<br/>{genre: 'mutant_wasteland',<br/>world: 'flickering_reach'}"] --> D["dispatch.rs:355<br/>GenreLoader::load(genre_slug)"]

    D --> E["loader.rs:19<br/>load_genre_pack(path)"]
    E --> F["Read YAML files:"]
    F --> G["pack.yaml → PackMeta"]
    F --> H["rules.yaml → RulesConfig"]
    F --> I["lore.yaml → Lore"]
    F --> J["archetypes.yaml → NpcArchetypes"]
    F --> K["char_creation.yaml → Scenes"]
    F --> L["visual_style.yaml → VisualStyle"]
    F --> M["audio.yaml → AudioConfig"]
    F --> N["axes.yaml → AxesConfig"]
    F --> O["tropes.yaml → TropeDefinitions"]
    F --> P["cultures.yaml, pacing.yaml,<br/>voice_presets.yaml, etc."]
    F --> Q["worlds/ → World per slug"]

    E --> R["GenrePack (fully typed)"]

    R --> S["Initialize session state:"]
    S --> T["axes_config ← pack.axes"]
    S --> U["trope_defs ← pack.tropes + world overrides"]
    S --> V["visual_style ← pack + world overrides"]
    S --> W["music_director ← pack.audio"]
    S --> X["lore_store ← seeded from pack.lore"]
    S --> Y["voice_router ← pack.voice_presets"]
    S --> Z["beat_filter ← pack.pacing thresholds"]

    style C fill:#4a9eff,color:#fff
    style R fill:#fdcb6e,color:#333
```

**15+ YAML files** per genre pack, all deserialized into typed Rust structs via serde_yaml

**World inheritance:** World-level overrides merge with genre-level defaults (tropes, visual style)

**Lazy binding (ADR-004):** Server starts genre-agnostic; genre bound at runtime on player connect

---

## Color Legend

```
Blue   (#4a9eff)  — Client/WebSocket messages (visible to player)
Purple (#6c5ce7)  — Internal data (narration text, results)
Red    (#ff6b6b)  — Claude CLI subprocess / narrator prompt
Green  (#00b894)  — Python daemon (Flux, Kokoro)
Orange (#e17055)  — SQLite persistence
Yellow (#fdcb6e)  — YAML configuration (genre packs)
Gray   (#b2bec3)  — Not yet wired / stub
```
