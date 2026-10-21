---
name: resolve-predictions
description: Review tracked predictions, score the ones whose resolve-by date has passed or whose outcome is now clear, and update the site. Use when the owner asks to "check predictions", "score predictions", or "what's due".
---

# Resolve predictions

1. List what's due:
   ```bash
   grep -l "status: open" docs/predictions/*.md | xargs grep -H "resolve_by:"
   ```
   A prediction is due if `resolve_by` is before today, or if the event has
   clearly happened (or clearly can't happen any more).
2. For each due prediction, research what actually happened, with sources.
   Judge it **only by the criteria already written** in "How we'll judge
   it". Don't move the goalposts. If those criteria were unclear, say so in
   the page.
3. Set `status` (correct / partly-correct / wrong / unresolvable) and
   `resolved_on`, and update `date_checked`. Write the "Resolution" section:
   - what happened;
   - why it meets or misses the criteria;
   - **how impressive the call was**, considering base rates (was it
     already the expected outcome?).
4. If nothing is due, tell the owner which prediction resolves next and when.
5. Build, validate and commit as in `CLAUDE.md`. Commit message:
   `resolve: <prediction> (<status>)`.
