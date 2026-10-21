import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CLAIM_BODY = """
# {title}

<!-- auto:card -->
<!-- /auto:card -->

## What was said
x
## Steelman
x
## Short answer
x
## The full picture
x
## Sources
x
## Thinking lesson
x
"""

PREDICTION_BODY = """
<!-- auto:card -->
<!-- /auto:card -->

## The prediction
x
## How we'll judge it
x
## Resolution
x
## Sources
x
"""


def page(meta: str, body: str) -> str:
    return f"---\n{textwrap.dedent(meta).strip()}\n---\n{body}"


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    """A minimal, valid knowledge base."""
    d = tmp_path / "docs"
    files = {
        "people/ann.md": page("""
            type: person
            title: Ann
            summary: A speaker.
            """, "\n<!-- auto:scorecard -->\n<!-- /auto:scorecard -->\n"),
        "sources/show.md": page("""
            type: source
            kind: episode
            title: The Show
            summary: An episode.
            speakers: [ann]
            """, "\n<!-- auto:claims -->\n<!-- /auto:claims -->\n"),
        "topics/history.md": page("""
            type: topic
            title: History
            summary: Context.
            """, "\n<!-- auto:claims -->\n<!-- /auto:claims -->\n"),
        "thinking/doubt.md": page("""
            type: thinking
            title: Doubt
            summary: A habit.
            """, "\n<!-- auto:claims -->\n<!-- /auto:claims -->\n"),
        "claims/sky-is-green.md": page("""
            type: claim
            title: The sky is green
            summary: No.
            speaker: ann
            source: show
            timestamp: "12:30"
            claim_type: fact
            verdict: "false"
            confidence: high
            prior: 80
            topics: [history]
            thinking: [doubt]
            date_checked: 2026-01-02
            """, CLAIM_BODY.format(title="The sky is green")),
        "claims/water-is-wet.md": page("""
            type: claim
            title: Water is wet
            summary: Yes.
            speaker: ann
            source: show
            timestamp: "1:02:03"
            claim_type: fact
            verdict: "true"
            confidence: high
            prior: 20
            topics: [history]
            thinking: []
            date_checked: 2026-01-01
            """, CLAIM_BODY.format(title="Water is wet")),
        "predictions/rain-tomorrow.md": page("""
            type: prediction
            title: It will rain tomorrow
            summary: Open.
            speaker: ann
            source: show
            made_on: 2026-01-01
            resolve_by: 2026-12-31
            status: open
            prior: null
            date_checked: 2026-01-03
            """, PREDICTION_BODY),
        "index.md": "# Home\n\n<!-- auto:stats -->\n<!-- /auto:stats -->\n\n<!-- auto:latest -->\n<!-- /auto:latest -->\n",
        "calibration.md": "# Cal\n\n<!-- auto:calibration -->\n<!-- /auto:calibration -->\n",
        "claims/index.md": "# Claims\n\n<!-- auto:by-verdict -->\n<!-- /auto:by-verdict -->\n",
        "predictions/index.md": "# P\n\n<!-- auto:predictions -->\n<!-- /auto:predictions -->\n",
    }
    for kind in ("people", "sources", "topics", "thinking"):
        files[f"{kind}/index.md"] = "# List\n\n<!-- auto:list -->\n<!-- /auto:list -->\n"
    for rel, text in files.items():
        path = d / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return d


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
