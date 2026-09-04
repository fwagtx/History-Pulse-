Write the full narration script for a History Pulse video.

Slug given by the human: $ARGUMENTS

1. Read `content/01_research/<slug>/notes.md`. If it doesn't exist, tell the human and suggest
   running `/research` first — don't invent research to fill the gap.
2. Write a full narration script following the channel's default tone (documentary,
   conversational, curiosity-first, threading back to modern relevance) unless the human has
   said otherwise for this video.
3. Structure:
   - **Hook** (first 10–15 seconds of narration) — must earn the next 30 seconds
   - **3–5 act body** covering the event
   - **Closer** that ties back to the modern relevance hook from the research notes, plus a
     natural CTA (subscribe / next video tease)
4. Include bracketed visual cues inline for the editor, e.g. `[SHOW: 1914 map of Europe,
   Austria-Hungary highlighted]`. Prefer specific archival image/map references over generic
   ones, per the visual-quality constraint in CLAUDE.md.
5. Keep sentences short and speakable — this is narration, not an essay. Avoid quoting sources
   verbatim; write everything in original wording.
6. Save the script to `content/02_scripts/<slug>/script.md`.
7. End by asking: "Script drafted for `<slug>`. Want changes, or should I move to `/seo
   <slug>`?"
