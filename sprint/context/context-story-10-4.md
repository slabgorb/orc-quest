---
parent: context-epic-10.md
---

# Story 10-4: Narrator Reads OCEAN — Adjust NPC Voice and Behavior Based on Personality

## Business Context

The behavioral summary from 10-3 is useless until the narrator actually sees it. This story
injects OCEAN summaries into the narrator's system prompt so the LLM adjusts NPC dialogue and
actions to match their personality. A high-neuroticism NPC panics under pressure every time,
not just when the LLM happens to generate that.

**Python reference:** `sq-2/sidequest/orchestrator.py` — personality descriptors injected into
NPC registry block of narrator prompt. Rust hooks into the prompt composer's NPC section.

**Depends on:** Story 10-3 (behavioral_summary method).

## Technical Approach

### Prompt Composer Integration

The existing `AgentContext::add_npc_registry()` method gains personality annotations:

```rust
impl AgentContext {
    pub fn add_npc_registry(&mut self, npcs: &[Npc]) {
        let mut section = String::from("## NPCs Present\n");
        for npc in npcs {
            section.push_str(&format!(
                "- **{}** (disposition: {}) — {}\n",
                npc.name,
                npc.disposition,
                npc.ocean.behavioral_summary(),
            ));
        }
        self.sections.push(section);
    }
}
```

### Narrator System Prompt Addition

A brief instruction tells the narrator how to use personality data:

```
Each NPC has a personality profile. Use these descriptors to guide their
dialogue tone, body language, and reactions. A "reserved" NPC speaks less
and avoids eye contact. An "anxious" NPC fidgets and catastrophizes.
Do not mention the personality system directly — show it through behavior.
```

### Multiple NPCs in Scene

When multiple NPCs are present, each gets their own summary. The narrator should
differentiate their behavior based on contrasting profiles.

## Scope Boundaries

**In scope:**
- Inject `behavioral_summary()` into NPC registry section of narrator prompt
- Add narrator instruction paragraph for using personality descriptors
- Works for all NPCs present in current scene

**Out of scope:**
- Fine-grained dialogue style (word choice, sentence length per personality)
- Player-visible personality display in UI
- Non-narrator agents reading OCEAN (world state agent is separate, 10-6)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Summary in prompt | Narrator system prompt includes behavioral summary for each NPC |
| Instruction present | Narrator prompt contains guidance on using personality descriptors |
| Multiple NPCs | Scene with 3 NPCs shows 3 distinct personality annotations |
| No raw scores | Prompt contains natural language, not float values |
| Behavioral effect | In playtest, NPC with low-E profile speaks with reserved tone across turns |
| No meta-reference | Narrator does not say "their OCEAN profile indicates..." |
