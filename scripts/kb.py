"""Shared helpers for the knowledge base: the schema, page loading, and the
auto-generated `<!-- auto:NAME -->` blocks that the scripts keep up to date.

Front matter is the single source of truth. Everything a script generates
(verdict cards, scorecards, indexes, calibration) is derived from it.
"""

from __future__ import annotations

import datetime as dt
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Page type -> folder under docs/. A page's `type` must match its folder.
FOLDERS = {
    "claim": "claims",
    "prediction": "predictions",
    "source": "sources",
    "person": "people",
    "topic": "topics",
    "thinking": "thinking",
}

# Verdict slug -> label, in display order (most to least supported).
VERDICTS = {
    "true": "True",
    "mostly-true": "Mostly true",
    "mixed": "Mixed",
    "misleading": "Misleading",
    "false": "False",
    "unproven": "Unproven",
    "contested": "Scholars disagree",
}

CLAIM_TYPES = {
    "fact": "Factual",
    "interpretation": "Interpretation",
    "conspiracy": "Conspiracy",
}

CONFIDENCE = ("low", "medium", "high")

PREDICTION_STATUS = {
    "open": "Open",
    "correct": "Came true",
    "partly-correct": "Partly came true",
    "wrong": "Did not happen",
    "unresolvable": "Can't be judged",
}

SOURCE_KINDS = ("channel", "playlist", "episode", "article", "book", "other")

# How each outcome scores for calibration: 1 = the claim held up, 0 = it
# didn't, None = too unclear to score.
VERDICT_OUTCOME = {
    "true": 1, "mostly-true": 1,
    "false": 0, "misleading": 0,
    "mixed": None, "unproven": None, "contested": None,
}
STATUS_OUTCOME = {
    "correct": 1, "wrong": 0,
    "partly-correct": None, "unresolvable": None, "open": None,
}

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
AUTO_RE = re.compile(
    r"(?P<open><!-- auto:(?P<name>[\w-]+) -->\n)(?P<content>.*?)(?P<close><!-- /auto:(?P=name) -->)",
    re.S,
)


@dataclass
class Page:
    path: Path
    meta: dict
    body: str
    slug: str = field(init=False)

    def __post_init__(self) -> None:
        self.slug = self.path.stem

    @property
    def type(self) -> str | None:
        return self.meta.get("type")

    @property
    def title(self) -> str:
        return str(self.meta.get("title", self.slug))


def split_front_matter(text: str) -> tuple[dict, str]:
    """Return (front matter, body). Pages without front matter get {}."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError("front matter is not a mapping")
    return meta, text[m.end():]


def load_pages(docs: Path = DOCS) -> list[Page]:
    """Every page under docs/ that declares a `type` in its front matter."""
    pages = []
    for path in sorted(docs.rglob("*.md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        if meta.get("type"):
            pages.append(Page(path, meta, body))
    return pages


def by_type(pages: list[Page], kind: str) -> list[Page]:
    return [p for p in pages if p.type == kind]


def index(pages: list[Page]) -> dict[tuple[str, str], Page]:
    """(type, slug) -> page, for resolving references like `speaker: x`."""
    return {(p.type, p.slug): p for p in pages}


def as_date(value) -> dt.date | None:
    if value is None or isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


def rel(from_file: Path, to_file: Path) -> str:
    """Relative markdown link from one docs file to another."""
    return os.path.relpath(to_file, from_file.parent).replace(os.sep, "/")


def link(from_file: Path, page: Page) -> str:
    return f"[{cell(page.title)}]({rel(from_file, page.path)})"


def cell(text) -> str:
    """Make a value safe inside a markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def prior_label(prior) -> str:
    if prior is None:
        return "not recorded"
    return f"{prior}% likely true"


def auto_blocks(text: str) -> list[str]:
    return [m.group("name") for m in AUTO_RE.finditer(text)]


def replace_block(text: str, name: str, content: str) -> str:
    """Replace the content of `<!-- auto:name -->` ... `<!-- /auto:name -->`.

    Content is normalised to end with exactly one newline so repeated runs
    are idempotent. Text without the marker is returned unchanged.
    """
    content = content.strip("\n") + "\n"

    def sub(m: re.Match) -> str:
        if m.group("name") != name:
            return m.group(0)
        return m.group("open") + content + m.group("close")

    return AUTO_RE.sub(sub, text)
