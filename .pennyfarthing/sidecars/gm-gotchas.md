## GM Gotchas

- **The narrator improvises constantly.** OTEL is the only way to catch it. If a span is missing for a subsystem, the narrator is making it up — no matter how convincing the prose sounds.
- **Spoiler protection is real.** Only `mutant_wasteland/flickering_reach` is fully spoilable. Everything else is unspoiled — don't read world secrets during audits of other genre packs.
- **Music is pre-rendered files, not daemon-generated.** Tracks live in genre_packs, not generated on the fly. Don't audit for daemon music endpoints.
- **Dinkus and drop caps are CSS-based.** Don't flag missing image assets for these — they're deprecated.
- **Content belongs at world level, not genre level.** Flavor goes in `worlds/{world}/`, mechanics go in genre root. This is the "Crunch in Genre, Flavor in World" SOUL principle in action.
- **Genre packs have 7 active genres.** spaghetti_western and victoria exist in content but aren't in the active list yet.
