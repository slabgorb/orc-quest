---
parent: context-epic-11.md
---

# Story 11-9: Narrator Name Injection — Load Name Bank into Narrator Prompt for Consistent Naming

## Business Context

The name bank (11-8) is pre-generated but the narrator needs to see it. This story injects
available names into the narrator's prompt so when new NPCs or locations need names, the
narrator picks from the bank instead of inventing ad hoc names. This eliminates linguistic
inconsistency where one Elvish name uses Germanic roots and another uses Japanese.

**Python reference:** `sq-2/sprint/epic-63.yaml` — name bank section added to narrator system
prompt with available names and their glosses. Rust hooks into the AgentContext builder.

**Depends on:** Story 11-8 (NameBank with generated names).

## Technical Approach

### Prompt Section

```rust
impl AgentContext {
    pub fn add_name_bank(&mut self, banks: &HashMap<String, NameBank>) {
        if banks.is_empty() { return; }

        let mut section = String::from("## Available Names\n");
        section.push_str("When naming new NPCs or locations, use names from these banks.\n\n");

        for (lang, bank) in banks {
            section.push_str(&format!("### {} Names\n", lang));
            for name in bank.available_names().take(10) {
                let gloss_str = name.gloss.iter()
                    .map(|(form, meaning)| format!("{}({})", form, meaning))
                    .collect::<Vec<_>>().join(" + ");
                section.push_str(&format!("- {} — {}\n", name.display, gloss_str));
            }
            section.push('\n');
        }
        self.sections.push(section);
    }
}
```

### Available Names View

```rust
impl NameBank {
    pub fn available_names(&self) -> impl Iterator<Item = &GlossedName> + '_ {
        self.names.iter().enumerate()
            .filter(|(i, _)| !self.used.contains(i))
            .map(|(_, name)| name)
    }
}
```

### Name Consumption

When the narrator uses a name, the post-turn processing marks it as used in the bank.
Name detection in narrator output uses simple string matching against the available names.

```rust
fn mark_used_names(banks: &mut HashMap<String, NameBank>, narration: &str) {
    for bank in banks.values_mut() {
        for (i, name) in bank.names.iter().enumerate() {
            if narration.contains(&name.display) {
                bank.used.insert(i);
            }
        }
    }
}
```

### Limit in Prompt

Only the first 10 unused names per language are shown in the prompt to avoid
consuming too much context window. The bank may hold more.

## Scope Boundaries

**In scope:**
- `add_name_bank()` on AgentContext
- `available_names()` iterator on NameBank
- Post-turn name consumption detection
- Limit to 10 names per language in prompt

**Out of scope:**
- Name bank replenishment (generating more when exhausted)
- Location-specific name styles (all names from same language pool)
- Language knowledge / transliteration (11-10)

## Acceptance Criteria

| AC | Detail |
|----|--------|
| Names in prompt | Narrator prompt includes "Available Names" section with glossed names |
| Gloss shown | Each name shows morpheme decomposition |
| Limited | At most 10 names per language shown in prompt |
| Consumed tracked | Name used in narration is marked as used in bank |
| No reuse | Used name does not appear in next turn's available names |
| Empty bank | Language with all names used → that language section omitted |
| No banks | Session with no languages configured → no name section added |
