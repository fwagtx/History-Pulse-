Compile the full video package for human review. This is the mandatory approval gate — never
skip it and never treat a video as approved without an explicit human response here.

Slug given by the human: $ARGUMENTS

1. Read everything that exists for this slug across `content/01_research/`,
   `content/02_scripts/`, `content/03_seo/`, and `content/04_thumbnails/`. If any stage is
   missing, tell the human which command to run first instead of filling gaps yourself.
2. Present a single clean summary in the chat covering:
   - Chosen angle + modern relevance hook
   - Recommended title (and the 4 alternates, briefly)
   - Script (full, or offer to show it if long)
   - Description, tags, hashtags
   - Thumbnail concept(s), noting the recommended one
3. End with exactly this kind of question, filled in for this slug:
   "Here's the full package for `<slug>`. Do you approve this for upload, or do you want
   changes to the script / titles / thumbnail?"
4. Wait for the human's explicit reply. Do not proceed, and do not move or copy any files into
   `content/05_approved/`, until the human's next message clearly approves it (e.g. says
   "approved," "yes, ship it," "good to go"). A vague or positive-sounding reply that isn't a
   clear approval ("looks nice") should be treated as feedback to discuss, not a green light —
   ask directly if unsure.
5. Once approved, copy (don't move — keep the working files) the final versions of the script,
   SEO package, and thumbnail concept into a single `content/05_approved/<slug>/` folder, and
   confirm to the human what was saved. Still do not upload, schedule, or contact YouTube in
   any way — that stays entirely human-operated.
