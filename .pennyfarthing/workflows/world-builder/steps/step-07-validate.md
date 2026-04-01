---
name: 'step-07-validate'
description: 'Structural validation, naming audit, schema compliance'

nextStepFile: './step-08-playtest.md'
wipFile: '{wip_file}'
---

<purpose>Verify all generated content is structurally sound, schema-compliant, and follows naming conventions before playtesting.</purpose>

<instructions>Run sq-audit, check YAML parsing, verify cross-references, audit naming against cultures.yaml.</instructions>

<output>Validation report with all issues resolved. stepsCompleted: [1, 2, 3, 4, 5, 6, 7].</output>

# Step 7: Validate

**Progress: Step 7 of 8**

## SEQUENCE

### 1. Run Audit

Use `/sq-audit` to check completeness:
```
/sq-audit <genre> [world]
```

This checks for missing files, schema violations, and structural gaps.

### 2. YAML Parse Check

Verify every generated file parses as valid YAML:
- No tab/space mixing
- Proper quoting of special characters
- Valid UTF-8 encoding

### 3. Cross-Reference Integrity

a) **Cartography:**
   - Every route endpoint references an existing region
   - Adjacency is bidirectional (A→B implies B→A)
   - No orphaned regions (every region reachable)

b) **Cultures:**
   - Corpus files exist for every culture that declares them
   - `place_patterns` reference valid corpus categories

c) **History:**
   - `session_ranges` don't overlap
   - Maturity levels progress correctly (FRESH < EARLY < MID < VETERAN)
   - NPCs referenced in history exist in archetypes

d) **Factions:**
   - Every faction's `relationships` references existing factions
   - At least one hostile relationship per faction

### 4. Naming Audit

Scan all `name` fields across generated files:
- **Settlements, landmarks, NPCs** must come from cultures.yaml naming patterns
- **English descriptive names are violations** — flag and fix
- Check against corpus files for linguistic consistency

### 5. Fix Issues

For each issue found:
1. Fix the file
2. Re-validate the fix
3. Document what was fixed

### 6. Report

Present validation results:
```
Validation: {PASS/FAIL}

Checks:
- YAML parsing: {N} files OK
- Cartography integrity: {status}
- Culture/corpus links: {status}
- History progression: {status}
- Naming audit: {N} names checked, {M} violations fixed

Issues resolved: {list}
```

Update WIP frontmatter: `stepsCompleted: [1, 2, 3, 4, 5, 6, 7]`

**If all checks pass, proceed to playtest.** If critical issues remain, **HALT and ask user for guidance.**
