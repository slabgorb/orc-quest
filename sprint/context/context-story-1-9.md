---
parent: context-epic-1.md
---

# Story 1-9: Prompt Framework — PromptSection, Attention Zones, Rule Taxonomy, SOUL.md Parser

## Business Context

This is the infrastructure that makes Claude useful as a game narrator rather than a generic
chatbot. The attention-zone system (primacy/early/valley/late/recency) is a proven design
from Python that controls what information Claude pays attention to in its context window.
PromptSection is the composable unit. Rule taxonomy structures game rules for consistent
agent enforcement. SOUL.md parsing loads agent personality guidelines at runtime.

Without this, agent calls are unstructured string concatenation.

**Python sources:**
- `sq-2/sidequest/prompt_composer.py` — PromptComposer, GamePromptComposer, PromptSection,
  SectionCategory, SectionZone, attention-zone assembly (~928 lines)
- `sq-2/sidequest/soul.py` — SOUL.md parser

## Technical Guardrails

- **ADR-009 (Attention-Aware Prompt Zones):** Five zones with ordering:
  - PRIMACY: agent identity, agency rules (highest attention)
  - EARLY: SOUL principles, genre tone, genre rules
  - VALLEY: lore, geography, tropes, other characters (low attention)
  - LATE: game state, active character, scene pacing (high recency)
  - RECENCY: `<before-you-respond>` self-check (highest)
- **ADR-008 (Three-Tier Prompt Taxonomy):** critical/firm/coherence rules with genre overrides
- **SOUL.md is runtime data.** Parsed from configurable path, injected as PromptSection in
  EARLY zone. Not compiled-in
- **SectionCategory enum:** Identity, Guardrail, Soul, Genre, State, Action, Format
  (from Python implementation, not originally in spec — TEA caught this deviation)

### Key Design Decision: RuleTier vs RuleSection

The original spec said `RuleSection` with variants Core/Combat/Chase/Narrative/Custom.
Python uses `RuleTier` (Critical/Firm/Coherence) which is the actual three-tier taxonomy
from ADR-009. Implementation follows Python's proven taxonomy.

## Scope Boundaries

**In scope:**
- `PromptSection` struct with content, zone, category, importance weight
- `AttentionZone` enum with ordering logic (Primacy > Early > Valley > Late > Recency)
- `SectionCategory` enum for prompt section classification
- `RuleTier` enum (Critical, Firm, Coherence)
- `SoulData` struct loaded from markdown files
- `PromptComposer` trait for composition strategies
- Full serde derives for all public types

**Out of scope:**
- Agent implementations (story 1-11)
- ClaudeClient, JsonExtractor, ContextBuilder (story 1-10)
- Format helpers (story 1-10)
- Runtime genre pack rule merging (future enhancement)

## AC Context

| AC | Detail |
|----|--------|
| Attention zones | 5 zones with Ord impl, sorted primacy→recency |
| SectionCategory | 7 variants matching Python implementation |
| RuleTier | 3 tiers (Critical/Firm/Coherence) with genre overrides |
| SOUL.md parser | Extracts principles from `**Name.** Text` markdown patterns |
| PromptComposer | Trait with zone-ordered assembly, filtering, multi-agent support |
| Token estimation | PromptSection provides rough token count estimate |

## Assumptions

- The attention-zone ordering from Python is proven and does not need redesign
- SOUL.md is pure markdown with `**Name.** Text` patterns — no YAML despite original spec
- Rule taxonomy categories are known from ADRs and do not need discovery
