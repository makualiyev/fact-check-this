# fact-check-this

A knowledge base of claims the owner heard on podcasts and YouTube, checked
against real sources, plus a toolkit for thinking about claims. It is
published as a MkDocs site. The owner comes back to it over months: write
for someone who wants to **understand**, not just get a verdict.

## Working rules

- **Commit straight to `main`.** No branches or PRs unless the owner asks.
  Commit messages say what was checked, e.g. `check: Paul invented Christianity (misleading)`.
- To check a claim, follow `.claude/skills/check/SKILL.md` (`/check`). To
  score due predictions, follow `.claude/skills/resolve-predictions/SKILL.md`.
- Before every commit, run:
  ```bash
  python scripts/build_indexes.py      # regenerate auto blocks
  python scripts/validate.py           # schema + cross-references
  python -m pytest -q                  # script tests
  mkdocs build --strict                # broken links fail the build
  ```
  CI runs the same four checks and deploys to GitHub Pages from `main`.

## How to fact-check (the method)

1. **Pin down what was said.** Quote it when a transcript is available
   (`scripts/fetch_transcript.py`, or `--from-file` with a pasted transcript).
   Otherwise write it as a paraphrase and **say it's from memory**. Never
   invent quotes, episodes or timestamps.
2. **Steelman first.** State the strongest version of the speaker's point
   before judging it.
3. **Separate the layers.** Facts (did it happen?), interpretation (does the
   reading follow from the facts?), framing ("secret", "they don't want you
   to know"). Most podcast claims are a true kernel plus a stretch, so find
   both.
4. **Find out where experts stand.** Distinguish consensus, real scholarly
   disagreement, and a fringe view. A minority view isn't wrong by default,
   but needs more evidence.
5. **Source it so the owner can check without trusting you.**
   - Prefer primary sources, peer-reviewed or university material, and
     museums and archives.
   - Use encyclopedias (Britannica) for orientation.
   - Wikipedia is a starting point, not the final word.
   - Label popular sites as such.
   - Every key factual statement should be traceable to a listed source.
6. **Pick a verdict and a confidence.** The scale is defined in
   `docs/method.md`, and the allowed values live in `scripts/kb.py`.
   - Don't reflexively debunk: true claims get "True" even from
     unreliable speakers.
   - Don't soften either: a claim with a true kernel can still be
     "Misleading."
7. **Teach one habit.** End with a thinking lesson. Link an existing
   `docs/thinking/` page, or create a new one when a genuinely new
   pattern shows up.
8. **Be honest about how you checked.** Pages couldn't always be opened
   directly in this environment (web search worked, fetching didn't). Each
   page ends with a "How these sources were checked" note saying what was
   actually done.

## Page schema

Front matter is the single source of truth. Never edit text between
`<!-- auto:NAME -->` and `<!-- /auto:NAME -->`: `build_indexes.py` owns it.
Copy a file from `templates/` to start a page. File names are lowercase
kebab-case slugs, and references use slugs.

| Folder | `type` | Required fields (besides `type`, `title`, `summary`) |
|---|---|---|
| `docs/claims/` | claim | `speaker`, `source`, `claim_type`, `verdict`, `confidence`, `prior`, `topics`, `thinking`, `date_checked`; optional `timestamp` ("34:10") |
| `docs/predictions/` | prediction | `speaker`, `source`, `made_on`, `resolve_by`, `status`, `prior`, `date_checked`; `resolved_on` once resolved; optional `thinking` |
| `docs/sources/` | source | `kind` (channel/playlist/episode/article/book/other), `speakers` |
| `docs/people/` | person | none |
| `docs/topics/` | topic | none |
| `docs/thinking/` | thinking | none |

Watch out for these:

- **Quote YAML values that look like booleans,** e.g. `verdict: "true"`.
- **`prior`** is the owner's own estimate (0–100, how likely true or likely
  to happen), recorded **before** they see the verdict. Use `null` if not
  recorded. Never fill it in afterwards or guess it.
- **`date_checked`** is `YYYY-MM-DD HH:MM` in UTC (`date -u +'%Y-%m-%d %H:%M'`).
  Pages show only the date. The time keeps several checks made on the same
  day in the right order in "Latest checks". A plain date is still valid.
- **A claim's `speaker`** must be listed in its source's `speakers`.
- **Required body sections:**
  - claims: `What was said`, `Steelman`, `Short answer`, `The full picture`,
    `Sources`, `Thinking lesson`;
  - predictions: `The prediction`, `How we'll judge it`, `Resolution`,
    `Sources`.

## Style

- Plain English. Explain terms the first time (canon, Septuagint, SS...).
- Short answer first, detail after. Tables for timelines and comparisons.
- Fair to speakers: describe credentials and criticism factually, no mockery.
- The site speaks in the owner's first person ("my prior"). Pages explain
  things to the reader directly.
