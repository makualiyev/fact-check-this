#!/usr/bin/env python3
"""Regenerate every `<!-- auto:NAME -->` block from front matter.

Usage:
  python scripts/build_indexes.py           # rewrite files in place
  python scripts/build_indexes.py --check   # exit 1 if anything is stale (CI)

Output depends only on the pages themselves (never on today's date), so a
clean tree stays clean until someone edits front matter.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb  # noqa: E402
from kb import cell, link, rel  # noqa: E402

NOTHING = "_Nothing here yet._"


def badge(kind: str, value: str) -> str:
    labels = kb.VERDICTS if kind == "verdict" else kb.PREDICTION_STATUS
    return f'<span class="badge badge--{value}">{labels.get(value, value)}</span>'


def result(p: kb.Page) -> str:
    """A claim's verdict badge or a prediction's status badge."""
    if p.type == "prediction":
        return badge("status", p.meta.get("status"))
    return badge("verdict", p.meta.get("verdict"))


def _checked(p: kb.Page) -> str:
    c = kb.checked_at(p.meta.get("date_checked"))
    return c.isoformat() if c else ""


def _date_key(p: kb.Page):
    return (_checked(p), p.title)


def _ts_key(p: kb.Page):
    ts = p.meta.get("timestamp")
    if ts is None:
        return (1, 0, p.title)
    secs = 0
    for part in str(ts).split(":"):
        secs = secs * 60 + int(part)
    return (0, secs, p.title)


class Builder:
    def __init__(self, docs: Path):
        self.docs = docs
        self.pages = kb.load_pages(docs)
        self.refs = kb.index(self.pages)
        self.claims = kb.by_type(self.pages, "claim")
        self.predictions = kb.by_type(self.pages, "prediction")

    def ref_link(self, here: Path, kind: str, slug) -> str:
        page = self.refs.get((kind, slug))
        return link(here, page) if page else cell(slug or "—")

    # ---- per-page blocks -------------------------------------------------

    def claim_card(self, p: kb.Page) -> str:
        m = p.meta
        v = m.get("verdict", "")
        where = f"**Said by** {self.ref_link(p.path, 'person', m.get('speaker'))} " \
                f"**in** {self.ref_link(p.path, 'source', m.get('source'))}"
        if m.get("timestamp"):
            where += f" at {m['timestamp']}"
        return "\n".join([
            f'<div class="verdict-card verdict-card--{v}" markdown>',
            f'<span class="verdict-card__label">{kb.VERDICTS.get(v, v)}</span>',
            "",
            f"**{m.get('summary', '')}**",
            "",
            where,
            "",
            f"**Claim type:** {kb.CLAIM_TYPES.get(m.get('claim_type'), m.get('claim_type'))}"
            f" · **Confidence in this verdict:** {m.get('confidence')}"
            f" · **Checked:** {kb.day(m.get('date_checked'))}"
            f" · **My prior:** {kb.prior_label(m.get('prior'))}",
            "</div>",
        ])

    def prediction_card(self, p: kb.Page) -> str:
        m = p.meta
        s = m.get("status", "")
        dates = f"**Made:** {m.get('made_on')} · **Resolve by:** {m.get('resolve_by')}"
        if m.get("resolved_on"):
            dates += f" · **Resolved:** {m['resolved_on']}"
        prior = m.get("prior")
        prior_text = "not recorded" if prior is None else f"{prior}% likely to happen"
        return "\n".join([
            f'<div class="verdict-card verdict-card--{s}" markdown>',
            f'<span class="verdict-card__label">Prediction · {kb.PREDICTION_STATUS.get(s, s)}</span>',
            "",
            f"**{m.get('summary', '')}**",
            "",
            f"**Made by** {self.ref_link(p.path, 'person', m.get('speaker'))} "
            f"**in** {self.ref_link(p.path, 'source', m.get('source'))}",
            "",
            f"{dates} · **My prior:** {prior_text}",
            "</div>",
        ])

    def claims_table(self, here: Path, claims: list[kb.Page], with_speaker=True) -> str:
        if not claims:
            return NOTHING
        head = "| Item | Result |" + (" Said by |" if with_speaker else "") + " Checked |"
        rows = [head, "|---|---|" + ("---|" if with_speaker else "") + "---|"]
        for c in claims:
            row = f"| {link(here, c)} | {result(c)} |"
            if with_speaker:
                row += f" {self.ref_link(here, 'person', c.meta.get('speaker'))} |"
            rows.append(row + f" {kb.day(c.meta.get('date_checked'))} |")
        return "\n".join(rows)

    def predictions_table(self, here: Path, preds: list[kb.Page]) -> str:
        if not preds:
            return NOTHING
        rows = ["| Prediction | Status | Made by | Resolve by |", "|---|---|---|---|"]
        for p in sorted(preds, key=lambda p: (str(p.meta.get("resolve_by")), p.title)):
            rows.append(f"| {link(here, p)} | {badge('status', p.meta.get('status'))} | "
                        f"{self.ref_link(here, 'person', p.meta.get('speaker'))} | {p.meta.get('resolve_by')} |")
        return "\n".join(rows)

    def scorecard(self, person: kb.Page) -> str:
        here = person.path
        claims = sorted((c for c in self.claims if c.meta.get("speaker") == person.slug), key=_date_key)
        preds = [p for p in self.predictions if p.meta.get("speaker") == person.slug]
        if not claims and not preds:
            return "_Nothing checked yet._"
        out = [f"**Claims checked:** {len(claims)} · **Predictions tracked:** {len(preds)}", ""]
        if claims:
            counts = Counter(c.meta.get("verdict") for c in claims)
            out += ["| Verdict | Claims |", "|---|---|"]
            out += [f"| {badge('verdict', v)} | {counts[v]} |" for v in kb.VERDICTS if counts[v]]
            out += ["", self.claims_table(here, claims, with_speaker=False)]
        if preds:
            counts = Counter(p.meta.get("status") for p in preds)
            summary = " · ".join(f"{kb.PREDICTION_STATUS[s]}: {counts[s]}" for s in kb.PREDICTION_STATUS if counts[s])
            out += ["", f"**Predictions** — {summary}", "", self.predictions_table(here, preds)]
        return "\n".join(out)

    def source_items(self, source: kb.Page) -> str:
        here = source.path
        claims = sorted((c for c in self.claims if c.meta.get("source") == source.slug), key=_ts_key)
        preds = [p for p in self.predictions if p.meta.get("source") == source.slug]
        if not claims and not preds:
            return NOTHING
        out = []
        if claims:
            rows = ["| At | Claim | Verdict | Said by |", "|---|---|---|---|"]
            for c in claims:
                rows.append(f"| {c.meta.get('timestamp') or '—'} | {link(here, c)} | "
                            f"{badge('verdict', c.meta.get('verdict'))} | "
                            f"{self.ref_link(here, 'person', c.meta.get('speaker'))} |")
            out.append("\n".join(rows))
        if preds:
            out.append("**Predictions**\n\n" + self.predictions_table(here, preds))
        return "\n\n".join(out)

    def tagged_claims(self, page: kb.Page, key: str) -> str:
        items = sorted((c for c in self.claims + self.predictions if page.slug in (c.meta.get(key) or [])),
                       key=_date_key)
        return self.claims_table(page.path, items)

    # ---- section and site-wide pages -------------------------------------

    def page_list(self, here: Path, kind: str) -> str:
        pages = sorted(kb.by_type(self.pages, kind), key=lambda p: p.title.lower())
        if not pages:
            return NOTHING
        return "\n".join(f"- {link(here, p)} — {p.meta.get('summary', '')}" for p in pages)

    def by_verdict(self, here: Path) -> str:
        if not self.claims:
            return NOTHING
        out = []
        for v, label in kb.VERDICTS.items():
            group = sorted((c for c in self.claims if c.meta.get("verdict") == v), key=_date_key)
            if group:
                out += [f"## {label}", "", self.claims_table(here, group), ""]
        return "\n".join(out)

    def predictions_index(self, here: Path) -> str:
        open_ = [p for p in self.predictions if p.meta.get("status") == "open"]
        done = [p for p in self.predictions if p.meta.get("status") != "open"]
        return "\n".join(["## Open", "", self.predictions_table(here, open_), "",
                          "## Resolved", "", self.predictions_table(here, done)])

    def stats(self, here: Path) -> str:
        counts = Counter(c.meta.get("verdict") for c in self.claims)
        parts = [f"{badge('verdict', v)} {counts[v]}" for v in kb.VERDICTS if counts[v]]
        line = f"**{len(self.claims)} claims checked** · **{len(self.predictions)} predictions tracked**"
        return line + ("\n\n" + " ".join(parts) if parts else "")

    def latest(self, here: Path, n: int = 5) -> str:
        items = sorted(self.claims + self.predictions, key=lambda p: p.title)
        items = sorted(items, key=_checked, reverse=True)[:n]
        if not items:
            return NOTHING
        rows = ["| Checked | Item | Result |", "|---|---|---|"]
        for p in items:
            rows.append(f"| {kb.day(p.meta.get('date_checked'))} | {link(here, p)} | {result(p)} |")
        return "\n".join(rows)

    def calibration(self, here: Path) -> str:
        items = [p for p in self.claims + self.predictions if p.meta.get("prior") is not None]
        if not items:
            return ("_No priors recorded yet._ From now on, `/check` asks how likely I think a claim is "
                    "before showing the verdict, and the stats start here.")
        rows = ["| Item | My prior | Outcome | Score |", "|---|---|---|---|"]
        scored, hits, decided, fooled, missed = [], 0, 0, [], []
        for p in sorted(items, key=_date_key, reverse=True):
            prior = p.meta["prior"]
            if p.type == "claim":
                outcome = kb.VERDICT_OUTCOME.get(p.meta.get("verdict"))
            else:
                outcome = kb.STATUS_OUTCOME.get(p.meta.get("status"))
            score = "—"
            if outcome is not None:
                b = (prior / 100 - outcome) ** 2
                scored.append(b)
                score = f"{b:.2f}"
                if prior != 50:
                    decided += 1
                    hits += (prior > 50) == (outcome == 1)
                if prior >= 70 and outcome == 0:
                    fooled.append(p)
                if prior <= 30 and outcome == 1:
                    missed.append(p)
            rows.append(f"| {link(here, p)} | {prior}% | {result(p)} | {score} |")
        out = [f"**Priors recorded:** {len(items)} · **Scorable:** {len(scored)}"]
        if scored:
            brier = sum(scored) / len(scored)
            out[0] += f" · **Brier score:** {brier:.3f}"
            if decided:
                out[0] += f" · **Leaned the right way:** {hits}/{decided} ({hits / decided:.0%})"
        out += ["", "\n".join(rows)]
        if fooled:
            out += ["", "**Fooled me** (I was ≥70% sure, it didn't hold up): "
                    + ", ".join(link(here, p) for p in fooled)]
        if missed:
            out += ["", "**Surprised me** (I was ≤30% sure, it held up): "
                    + ", ".join(link(here, p) for p in missed)]
        return "\n".join(out)

    # ---- dispatch --------------------------------------------------------

    def generators(self):
        """Yield (path, block name, generator) for every block we own."""
        per_type = {
            "claim": {"card": self.claim_card},
            "prediction": {"card": self.prediction_card},
            "person": {"scorecard": self.scorecard},
            "source": {"claims": self.source_items},
            "topic": {"claims": lambda p: self.tagged_claims(p, "topics")},
            "thinking": {"claims": lambda p: self.tagged_claims(p, "thinking")},
        }
        for p in self.pages:
            for name, fn in per_type.get(p.type, {}).items():
                yield p.path, name, (lambda fn=fn, p=p: fn(p))
        d = self.docs
        site = {
            d / "index.md": {"stats": self.stats, "latest": self.latest},
            d / "calibration.md": {"calibration": self.calibration},
            d / "claims" / "index.md": {"by-verdict": self.by_verdict},
            d / "predictions" / "index.md": {"predictions": self.predictions_index},
        }
        for kind in ("person", "source", "topic", "thinking"):
            site[d / kb.FOLDERS[kind] / "index.md"] = {"list": lambda here, k=kind: self.page_list(here, k)}
        for path, blocks in site.items():
            for name, fn in blocks.items():
                yield path, name, (lambda fn=fn, path=path: fn(path))

    def build(self) -> dict[Path, str]:
        """Return {path: new text} for every file whose blocks changed."""
        texts: dict[Path, str] = {}
        for path, name, gen in self.generators():
            if not path.exists():
                continue
            text = texts.get(path) or path.read_text(encoding="utf-8")
            texts[path] = kb.replace_block(text, name, gen())
        return {p: t for p, t in texts.items() if t != p.read_text(encoding="utf-8")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if any generated block is stale")
    ap.add_argument("--docs", type=Path, default=kb.DOCS)
    args = ap.parse_args(argv)

    changed = Builder(args.docs).build()
    root = args.docs.parent
    if args.check:
        for path in changed:
            print(f"STALE {rel(root / 'x', path)}")
        if changed:
            print("\nGenerated blocks are out of date. Run: python scripts/build_indexes.py")
            return 1
        print("OK: generated blocks are up to date.")
        return 0
    for path, text in changed.items():
        path.write_text(text, encoding="utf-8")
        print(f"updated {rel(root / 'x', path)}")
    if not changed:
        print("Nothing to update.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
