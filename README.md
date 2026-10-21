# Fact-check this

A growing knowledge base of claims I hear on podcasts and YouTube. Each one
is checked against real sources, given a verdict, and turned into a lesson
in thinking clearly. It is built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and published
to GitHub Pages.

**Site:** https://makualiyev.github.io/fact-check-this/ (once Pages is enabled; see below)

## How I use it

Open a Claude Code session on this repo and say what I heard:

```
/check Jiang, Secret History ep 12 ~34:10: says the Council of Nicaea picked the Gospels
```

Claude asks for my **prior** (how likely I think it's true) *before*
researching. Then it writes the claim page, updates every index and
scorecard, runs the checks, and commits to `main`. `/resolve-predictions`
scores forecasts whose date has come.

## Layout

```
docs/
  claims/        one page per checked claim (the core)
  predictions/   forecasts with resolution criteria and a resolve-by date
  sources/       channels, playlists, episodes; lists their claims by timestamp
  people/        speaker profiles with auto-generated scorecards
  topics/        background explainers
  thinking/      the critical-thinking toolkit
  calibration.md my priors vs. outcomes (auto-generated)
  method.md      verdict scale and how checks are done
templates/       starting point for each page type
scripts/
  kb.py              schema + shared helpers
  validate.py        front matter, references and required sections
  build_indexes.py   regenerates every <!-- auto:... --> block (--check for CI)
  fetch_transcript.py  YouTube transcript fetch / search (or --from-file)
tests/           pytest for the scripts
CLAUDE.md        the fact-checking method and house rules for Claude
.claude/skills/  /check and /resolve-predictions
```

Front matter is the single source of truth. Verdict cards, scorecards,
indexes and calibration are generated from it, so never edit inside
`<!-- auto:... -->` blocks by hand.

## Local commands

```bash
pip install -r requirements.txt
python scripts/build_indexes.py   # regenerate generated blocks
python scripts/validate.py        # check schema and links between pages
python -m pytest -q               # test the scripts
mkdocs serve                      # preview at http://127.0.0.1:8000
```

## Publishing

`.github/workflows/ci.yml` runs all checks on every push.
`.github/workflows/deploy.yml` publishes `main` to GitHub Pages. To turn it
on once: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
Free GitHub Pages requires the repository to be public.
