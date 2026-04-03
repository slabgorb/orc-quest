## GM Patterns

- **OTEL-first diagnosis.** When something feels wrong in a playtest, check spans before content. Missing span = code bug (route to Dev). Present span with wrong values = content issue (fix it yourself).
- **Audit before playtest.** Run `/sq-audit` on the target genre/world before any playtest session. Missing content produces silent fallbacks or empty narration — catch it before you're in the middle of a session.
- **Ping-pong for code bugs.** When a playtest reveals a code bug, write it to the ping-pong file with severity, steps to reproduce, and OTEL evidence. Don't try to fix code yourself.
- **The Test is the ultimate check.** On every narrator response: "Did the narration include the player doing something they didn't ask?" If yes, it's a SOUL violation regardless of how good it sounds.
- **Sensory layering audit.** Every location description should hit 2+ senses beyond sight. If an audit finds sight-only descriptions, the world content is thin.
