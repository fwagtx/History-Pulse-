Produce the SEO package for a History Pulse video.

Slug given by the human: $ARGUMENTS

1. Read `content/01_research/<slug>/notes.md` and `content/02_scripts/<slug>/script.md`. If
   either is missing, tell the human and suggest the right prior step instead of guessing.
2. Use web search to sanity-check current search/trend signals for this topic (what people
   actually search for, how similar videos are titled) before finalizing keywords.
3. Produce and save to `content/03_seo/<slug>/seo.md`:
   - **5 title options** — front-loaded keywords, under 60 characters, curiosity-driven but
     factually honest (no false clickbait)
   - **1 recommended primary title** with a one-line reason why
   - **YouTube description** (150–300 words): keyword-rich first two lines, a short summary,
     a placeholder timestamp block, a placeholder links block
   - **10–15 tags/keywords**
   - **3–5 hashtags**
   - Suggested category, and whether this fits long-form, Shorts, or both
4. End by asking: "SEO package saved for `<slug>`. Move to `/thumbnail <slug>`?"
