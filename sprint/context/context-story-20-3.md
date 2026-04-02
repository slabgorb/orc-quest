---
parent: context-epic-20.md
workflow: tdd
---

# Story 20-3: item_acquire and merchant_transact tools

## Business Context

Inventory is one of the highest-value migrations. The narrator currently decides "player picked up a sword" AND formats the `items_gained` JSON with name/description/category. The item may already exist in genre pack data or merchant inventory — the LLM is redundantly generating what a lookup could provide. Same for merchant transactions: pricing, inventory validation, and transaction structure are pure crunch.

## Technical Guardrails

- `item_acquire` takes item name + optional context (looted, bought, found). Returns `ItemGained` struct JSON. May look up genre pack `item_catalog` for canonical item data if a match exists, otherwise accepts narrator's description.
- `merchant_transact` takes transaction type (buy/sell), item_id, merchant name. Validates against merchant inventory (from `npc_registry` merchant data). Returns `MerchantTransactionExtracted` struct JSON.
- Both tools exposed via `--allowedTools Bash`. Narrator calls them when it narrates acquisition or commerce.
- Remove `items_gained` and `merchant_transactions` JSON schema documentation (~180 tokens + ~100 tokens) from narrator system prompt.
- `assemble_turn` merges into `ActionResult.items_gained` and `ActionResult.merchant_transactions`.
- Key files: `narrator.rs`, `orchestrator.rs`, `assemble_turn`, genre pack item_catalog YAML.

## Scope Boundaries

**In scope:**
- `item_acquire` tool with genre pack lookup
- `merchant_transact` tool with inventory validation
- Remove item/merchant JSON schema from narrator prompt
- `assemble_turn` integration
- OTEL events

**Out of scope:**
- Changing the `ItemGained` or `MerchantTransactionExtracted` structs
- Merchant inventory management (already wired in story 15-16)

## AC Context

1. `item_acquire` returns valid `ItemGained` JSON, optionally enriched from genre pack item_catalog
2. `merchant_transact` validates against merchant inventory and returns transaction JSON
3. Narrator prompt no longer contains item/merchant JSON schemas
4. `assemble_turn` merges results into ActionResult
5. Items not acquired via tool call don't appear in ActionResult (no fallback)
6. OTEL spans for each tool invocation with item name and transaction details
