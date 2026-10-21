---
title: How this works
---

# How this works

## The verdict scale

Each claim gets exactly one verdict:

| Verdict | Meaning |
|---|---|
| <span class="badge badge--true">True</span> | Accurate as stated. Nothing important is missing. |
| <span class="badge badge--mostly-true">Mostly true</span> | The core is right, but a number, framing or detail needs a correction. |
| <span class="badge badge--mixed">Mixed</span> | Roughly half right: real true and false parts that can't be separated into one call. |
| <span class="badge badge--misleading">Misleading</span> | Built on a real fact, but the conclusion or framing leaves you believing something false. |
| <span class="badge badge--false">False</span> | The evidence contradicts it. |
| <span class="badge badge--unproven">Unproven</span> | There isn't enough evidence either way, *or* it can't be tested. |
| <span class="badge badge--contested">Scholars disagree</span> | Informed experts are genuinely split, and the evidence doesn't settle it. |

"Misleading" and "Scholars disagree" are different. A view held by a small
minority of experts while most reject it is not "scholars disagree". That's
a [consensus and a fringe](thinking/consensus-vs-fringe.md), and the verdict
judges the claim against the consensus while saying the minority view exists.

Each verdict also states **how confident it is** (low / medium / high):

- **High:** multiple strong, independent sources agree.
- **Medium:** good sources, but some gaps or reliance on one line of evidence.
- **Low:** the best available, but thin. Expect to revise it.

## Claim types

How a claim gets checked depends on its type:

- **Factual**: something that did or didn't happen, or a number. Checked against records and data.
- **Interpretation**: a reading of facts ("Paul invented Christianity"). The facts can be true and the reading still a stretch, so we check both and compare with how experts read the same facts.
- **Conspiracy**: a claim that people coordinated in secret. Checked like any other claim: some were real (see [Operation Paperclip](claims/operation-paperclip-nazis-at-nasa.md)), most are not. The question is always what the evidence shows, not whether the idea sounds crazy.
- **Predictions** are kept separately in [Predictions](predictions/index.md). They can't be checked yet, so they get a "resolve by" date and are scored when it arrives.

## Anatomy of a check

Every claim page has the same sections, in this order:

1. **What was said**: the claim as close to the speaker's words as we can verify. If the wording comes from memory, the page says so.
2. **Steelman**: the strongest, most charitable version of the speaker's point. If we can't state it fairly, we haven't understood it.
3. **Short answer**: two or three sentences.
4. **The full picture**: what's true, where it goes wrong, and what experts actually think.
5. **Sources**: primary sources and scholarship first, encyclopedias next, popular sites only for minor details (and labelled).
6. **Thinking lesson**: the habit from the [toolkit](thinking/index.md) this case teaches.

## Your prior, and calibration

Before reading a verdict, I record a **prior**: how likely I thought the
claim was to be true, from 0 to 100%. After the check, the
[Calibration](calibration.md) page compares priors with outcomes:

- **Leaned the right way**: how often a prior above 50% went with a claim that held up (True or Mostly true), and a prior below 50% with one that didn't (Misleading or False).
- **Brier score**: the average of (prior − outcome)². 0 is perfect, and 0.25 is what always answering 50% gets. Lower is better.
- **Mixed**, **Unproven** and **Scholars disagree** are not scored, because there is no clean outcome to score against.

Priors not recorded at the time are left blank, never filled in afterwards.

## Updating a verdict

New evidence can change a verdict. When that happens, the page is updated,
`date_checked` changes, and the commit message explains why. The page's
history on GitHub keeps the old version.
