# Ping-Pong File Protocol

Cross-workspace coordination between OQ-2 (playtest driver) and OQ-1 (fix team).

## File Locations

| Resource | Path |
|----------|------|
| Ping-pong file | `/Users/keithavery/Projects/sq-playtest-pingpong.md` |
| Screenshots | `/Users/keithavery/Projects/sq-playtest-screenshots/` |
| Archive | `/Users/keithavery/Projects/sq-playtest-archive/` |

These are siblings to `oq-1/` and `oq-2/` under `Projects/`, accessible to both workspaces.

## Write Ownership

| Action | OQ-2 (playtest) | OQ-1 (fixes) |
|--------|-----------------|---------------|
| Add new task | YES | NO |
| Set status → `in-progress` | NO | YES |
| Set status → `fixed` | NO | YES |
| Set status → `verified` | YES | NO |
| Add `ATTENTION` signal | YES | NO |
| Remove `ATTENTION` signal | NO | YES (when picking up) |
| Delete entries | NO | NO |

**Neither side deletes.** Status transitions only. This prevents edit conflicts.

## Status Flow

```
open → in-progress → fixed → verified
 │                      │
 └── (OQ-2 adds)       └── (OQ-2 verifies)
       (OQ-1 picks up)       (OQ-1 fixes)
```

## Task Tags

| Tag | Meaning | Typical Priority |
|-----|---------|-----------------|
| `[BUG]` | Functional bug, broken behavior | blocking or high |
| `[BUG-LOW]` | Cosmetic or minor visual bug | medium or low |
| `[UX]` | Usability improvement opportunity | medium or low |
| `[GAP]` | Expected feature or feedback missing | varies |

## Blocking Bug Signal

When OQ-2 adds a blocking bug, it prepends this to the Tasks section:

```markdown
> **ATTENTION OQ-1**: Blocking bug added — {brief description}. Please prioritize.
```

OQ-1 removes the attention line when it sets the task to `in-progress`.

## Server Restart Coordination

When OQ-1 fixes a bug that requires a server restart:
1. OQ-1 adds `- **Needs restart:** yes` to the task entry
2. OQ-1 sets status to `fixed`
3. OQ-2 sees the `fixed` status and `Needs restart` flag
4. OQ-2 pulls latest code and restarts the affected service
5. OQ-2 re-tests and sets status to `verified`

## Task Entry Template

```markdown
### [{TAG}] {title}
- **Priority:** blocking | high | medium | low
- **Found by:** SM | UX Designer
- **Repro:** {step-by-step reproduction}
- **Status:** open | in-progress | fixed | verified
- **Screenshot:** /Users/keithavery/Projects/sq-playtest-screenshots/{NNN}.png
- **Notes:** {additional context}
- **Needs restart:** no (set by OQ-1 if fix requires service restart)
```
