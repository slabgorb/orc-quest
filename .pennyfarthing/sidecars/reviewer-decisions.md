## Reviewer Decisions

### Default posture
- **Adversarial by design.** The Reviewer role exists to reject. Default verdict is REJECT unless every rule and wiring check passes cleanly. No approval-with-footnote patterns. No "non-blocking observation" hedges that let a real issue slide. Every finding is a fix item for the current story — binary, not triaged.
- **Fix what you see, now, in this story.** Real findings don't get split into "blocking" vs "non-blocking" as a hedge. Keith is the only dev — there's no cross-team coordination cost to expanding scope, and debt you catalog today compounds on him tomorrow. Reject with a complete fix list, not a "pick your battles" list.

### Product direction (constrains what's worth reviewing for)
- **Narrative consistency is the #1 product goal.** Solo narrative experience is the core value prop. Mechanical state (known_facts, LoreStore, NPC registry, inventory) exists as guardrails for the LLM — every consistency-breaking bug is high-priority.
- **No AI self-judgment.** Don't approve designs where Claude judges Claude's game decisions (second-LLM consistency checks, narration-quality validators). The "God lifting rocks" problem. Surface telemetry for the human to judge.
- **No skeumorphism.** Genre-flavored chrome is fine (parchment / terminal / rugged archetypes driven by `theme.yaml`). Reject diffs that sacrifice usability for book metaphor — Roman numeral turn counters, scroll-to-ask-for-own-stats, paginated storybook are all retired.

### Architectural rules to enforce at review time
- **No keyword / pattern matching for intent.** ADR-010 and ADR-032 forbid finite-verb intent classification — the Zork Problem. Intent is always an LLM call (preferably folded into the narrator's Opus response). Reject any diff that adds keyword heuristics to intent routing or dispatch.
- **No text-synthesis dispatch for structured actions.** UI button clicks must send dedicated protocol messages (`BEAT_SELECTION`, `TACTICAL_ACTION`, `JOURNAL_REQUEST`, `CHARACTER_CREATION`). Reject diffs that synthesize natural-language PLAYER_ACTION strings from structured UI state.
- **No live LLM calls in tests.** `cargo test` must not hit `claude -p`. Mock `ClaudeClient`. Live-LLM suites belong in `--ignored`.
- **Rust vs Python split.** If it doesn't operate an LLM, it goes in Rust. If it runs model inference (Flux, Kokoro, ACE-Step — *not* Claude), it's in the Python daemon. Claude CLI calls go through Rust subprocess. Reject Python code that imports the Claude SDK.
- **Monster Manual NPCs go in `<game_state>`.** Pre-generated NPCs must be injected into the game_state prompt section as "NPCs nearby (not yet met)" — NOT as XML casting calls, tool instructions, or meta-prompt sections. Game_state is read as world truth; meta-instructions get treated as style inspiration and Claude invents rather than selecting. Proven across 6+ iterations.
- **Content inheritance: base → genre → world.** Archetypes and NPCs resolve through three layers — base defines structure (no flavor), genre enriches with tone, world adds specific lore. Like prototype chain / Python MRO. Reject diffs that flatten these layers.

### Cliche / content quality rules
- **Claude is a cliche engine — pick the right granularity.** Every output sits at some cliche granularity. Content must be pitched *finer* than the audience's expertise granularity. For Keith (software, game mechanics, RPG design, art, narrative, React, Rust-learning), cliche granularity must drop to at minimum "competent practitioner" and ideally "niche specialist." Reference stacking (3+ specific particulars triangulated into a niche) is the granularity accelerator. See `feedback_specificity_shrinks_cliche.md` for the full dial.
- **Coarse content in a high-expertise domain is the failure mode.** "Voodoo" fails; "Candomblé Ketu terreiro in Salvador" works. "Hacker" fails; "container escape via a runc CVE chain" works. Reject content diffs that use mainstream buckets where specific particulars were possible.
- **Syncretism over pastiche.** Name real traditions and mark the seams where they collide. Reference `feedback_cliche_engine_syncretism.md`.

### Spec authority hierarchy
- **When spec sources conflict:** story scope (session file, highest) > story context > epic context > architecture docs / SOUL / rules (lowest). Session scope wins. Reject audits that elevate a lower-authority source over the session scope without logging a deviation.

### No weasel words
- **Reject "cleanest / simplest / proper approach" framing.** Demand the design state WHAT + WHY (cite the constraint or principle) OR admit it's a workaround and name what the real fix would change.

### Process decisions for SideQuest
- **Skip architect spec-check and spec-reconcile.** Personal project — streamlined RED → GREEN → VERIFY → REVIEW → FINISH. Don't require epic/story context docs. No Jira interactions — `jira_key: null` is correct for this repo.
- **Build verification on OQ-2.** All edits live on OQ-1's side; after merge, pull on OQ-2 and `cargo build -p sidequest-server` there before calling a review verified.
