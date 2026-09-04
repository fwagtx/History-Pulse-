Package an already-approved video for the human's own upload, and log it.

Slug given by the human: $ARGUMENTS

1. Confirm `content/05_approved/<slug>/` exists. If it doesn't, stop and tell the human this
   slug hasn't been approved yet — direct them to `/review <slug>` instead of proceeding.
2. Assemble a single reference file `content/05_approved/<slug>/upload_checklist.md` containing:
   - Final title
   - Final description (ready to paste into YouTube Studio)
   - Final tags/hashtags (ready to paste)
   - Thumbnail file reminder (pointing to the concept/mockup file, since the human builds the
     real image themselves in Canva/Photopea/GIMP)
   - A plain checklist: [ ] video rendered, [ ] thumbnail built, [ ] uploaded to YouTube
     Studio, [ ] scheduled/published, [ ] description/tags pasted in
3. Do not call any upload API, do not open a browser automation flow, and do not mark anything
   as published. This command only prepares copy-paste-ready text for the human to use in
   YouTube Studio themselves.
4. After the human later confirms (in a future session or message) that the video is actually
   live, and only then, create `content/06_published/<slug>/published.md` noting the live URL
   and publish date they give you, and update the checklist above.
5. End by telling the human the checklist is ready and that publishing itself is entirely in
   their hands via YouTube Studio.
