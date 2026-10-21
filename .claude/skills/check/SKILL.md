---
name: check
description: Fact-check a claim (or log a prediction) heard on a podcast or video and add it to the knowledge base. Use when the owner says "check: ...", "/check ...", or describes something a speaker said that they want verified.
---

# /check: fact-check a claim

Input is usually rough: *"Jiang, Secret History ep 12, ~34:10: says the
Council of Nicaea picked the Gospels."* Follow every step in order. The
method in `CLAUDE.md` applies throughout.

## 1. Parse and ask for the prior

Work out the **speaker**, **source** (channel / playlist / episode, plus a
URL if given), **timestamp**, and the **claim** in one sentence. If it's a
forecast about the future, it's a **prediction** (see step 6).

Before doing any research or giving any hint of the answer, ask the owner
(AskUserQuestion works well):

> Before I look: how likely do you think this is true? (0–100%, or skip)

Record the number as `prior`. If they skip, `prior: null`. Never infer it.
If the input contains several claims, list them and ask which to check,
plus a prior for each.

## 2. Get the exact words (if possible)

If there's a YouTube URL, try:

```bash
python scripts/fetch_transcript.py "<url>" --grep "<keyword>" --context 2
```

If fetching fails (youtube.com is often blocked in cloud sessions), ask the
owner to paste the transcript text (YouTube → "...more" → **Show
transcript**). Save it to `.cache/transcripts/<id>.txt` and use
`--from-file`. If there's no transcript, paraphrase and mark it "from
memory".

## 3. Make sure the speaker and source pages exist

Look in `docs/people/` and `docs/sources/`. If one is missing, create it
from `templates/person.md` / `templates/source.md`, with brief factual
research (credentials, field, track record) and sources. Add the speaker to
the source's `speakers` list.

## 4. Research

- Search broadly and look for primary and scholarly sources (see `CLAUDE.md`
  §5).
- For a big topic, or for several claims at once, research them in
  parallel with subagents, then verify their key facts yourself.
- Note which sources you could actually open and which you only saw in
  search results.
- Check whether a related topic page exists (`docs/topics/`). Create one
  only if the background is reusable for future claims.

## 5. Write the claim page

Copy `templates/claim.md` to `docs/claims/<slug>.md`. Fill in every
section, keep the `<!-- auto:card -->` block empty, and choose:

- `claim_type`: fact / interpretation / conspiracy
- `verdict`: true / mostly-true / mixed / misleading / false / unproven / contested
- `confidence`: low / medium / high
- `topics`, `thinking`: existing slugs. Add a new `docs/thinking/` page only for a genuinely new habit.
- `date_checked`: the current UTC time, from `date -u +'%Y-%m-%d %H:%M'`.

## 6. Predictions instead

Copy `templates/prediction.md` to `docs/predictions/<slug>.md`.

- Write **concrete resolution criteria** in "How we'll judge it" and set a
  `resolve_by` date. If the speaker gave none, choose a fair one and say
  so.
- `status: open`, unless the date has already passed. Then resolve it now,
  as in the resolve-predictions skill.

## 7. Build, validate, commit

```bash
python scripts/build_indexes.py && python scripts/validate.py && python -m pytest -q && mkdocs build --strict
git add -A && git commit -m "check: <claim> (<verdict>)" && git push origin main
```

## 8. Report back

In the chat, give:

- the verdict and short answer;
- how it compares with their prior (if they gave one), e.g. "You said 80%; it turned out Misleading";
- the thinking lesson in one line;
- the page path.

Keep it brief: the page holds the detail.
