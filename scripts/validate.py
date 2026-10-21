#!/usr/bin/env python3
"""Check every knowledge-base page against the schema.

Usage: python scripts/validate.py [docs_dir]

Exits 1 and lists every problem if anything is wrong. The schema itself is
described in CLAUDE.md and docs/method.md; the allowed values live in kb.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb  # noqa: E402

COMMON = ("type", "title", "summary")
REQUIRED = {
    "claim": COMMON + ("speaker", "source", "claim_type", "verdict", "confidence",
                       "prior", "topics", "thinking", "date_checked"),
    "prediction": COMMON + ("speaker", "source", "made_on", "resolve_by", "status",
                            "prior", "date_checked"),
    "source": COMMON + ("kind", "speakers"),
    "person": COMMON,
    "topic": COMMON,
    "thinking": COMMON,
}

SECTIONS = {
    "claim": ("What was said", "Steelman", "Short answer", "The full picture",
              "Sources", "Thinking lesson"),
    "prediction": ("The prediction", "How we'll judge it", "Resolution", "Sources"),
}

# Pages whose body must carry these generated blocks.
BLOCKS = {
    "claim": ("card",),
    "prediction": ("card",),
    "person": ("scorecard",),
    "source": ("claims",),
    "topic": ("claims",),
    "thinking": ("claims",),
}


def check_page(page: kb.Page, refs: dict, docs: Path) -> list[str]:
    errors = []
    m = page.meta
    kind = page.type

    def err(msg: str) -> None:
        errors.append(f"{page.path.relative_to(docs.parent)}: {msg}")

    if kind not in kb.FOLDERS:
        err(f"unknown type {kind!r} (expected one of {', '.join(kb.FOLDERS)})")
        return errors
    if page.path.parent != docs / kb.FOLDERS[kind]:
        err(f"type {kind!r} pages belong in docs/{kb.FOLDERS[kind]}/")
    if page.slug != page.slug.lower() or " " in page.slug or "_" in page.slug:
        err("file name must be a lowercase kebab-case slug")

    for key in REQUIRED[kind]:
        if key not in m:
            err(f"missing front matter field {key!r}")

    def ref(key: str, target: str, value) -> None:
        if value is not None and (target, value) not in refs:
            err(f"{key}: no {target} page named {value!r} "
                f"(expected docs/{kb.FOLDERS[target]}/{value}.md)")

    def enum(key: str, allowed) -> None:
        if key in m and isinstance(m[key], bool):
            err(f'{key}: YAML read this as a boolean; quote it, e.g. {key}: "{str(m[key]).lower()}"')
        elif key in m and m[key] not in allowed:
            err(f"{key}: {m[key]!r} is not one of {', '.join(map(str, allowed))}")

    def date(key: str) -> None:
        if m.get(key) is None:
            return
        try:
            kb.as_date(m[key])
        except ValueError:
            err(f"{key}: {m[key]!r} is not a YYYY-MM-DD date")

    def prior() -> None:
        p = m.get("prior")
        if p is not None and not (isinstance(p, int) and not isinstance(p, bool) and 0 <= p <= 100):
            err(f"prior: must be a whole number 0-100 or null, got {p!r}")

    if kind in ("claim", "prediction"):
        ref("speaker", "person", m.get("speaker"))
        ref("source", "source", m.get("source"))
        prior()
        try:
            kb.checked_at(m.get("date_checked"))
        except ValueError:
            err(f"date_checked: {m['date_checked']!r} should be YYYY-MM-DD or 'YYYY-MM-DD HH:MM' (UTC)")
        src = refs.get(("source", m.get("source")))
        known_speaker = ("person", m.get("speaker")) in refs
        if src and known_speaker and m.get("speaker") not in (src.meta.get("speakers") or []):
            err(f"speaker {m.get('speaker')!r} is not listed in the speakers of source {src.slug!r}")

    for key, target in (("topics", "topic"), ("thinking", "thinking")):
        if kind not in ("claim", "prediction") or m.get(key) is None:
            continue
        if not isinstance(m[key], list):
            err(f"{key}: must be a list")
            continue
        for value in m[key]:
            ref(key, target, value)

    if kind == "claim":
        enum("verdict", kb.VERDICTS)
        enum("claim_type", kb.CLAIM_TYPES)
        enum("confidence", kb.CONFIDENCE)
        ts = m.get("timestamp")
        if ts is not None and not _is_timestamp(str(ts)):
            err(f"timestamp: {ts!r} should look like 34:10 or 1:02:03")

    if kind == "prediction":
        enum("status", kb.PREDICTION_STATUS)
        for key in ("made_on", "resolve_by", "resolved_on"):
            date(key)
        if m.get("status") not in (None, "open") and not m.get("resolved_on"):
            err("resolved predictions need a resolved_on date")
        if m.get("status") == "open" and m.get("resolved_on"):
            err("open predictions must not have resolved_on")

    if kind == "source":
        enum("kind", kb.SOURCE_KINDS)
        speakers = m.get("speakers")
        if not isinstance(speakers, list) or not speakers:
            err("speakers: must be a non-empty list of people slugs")
        else:
            for s in speakers:
                ref("speakers", "person", s)

    for heading in SECTIONS.get(kind, ()):
        if f"\n## {heading}\n" not in "\n" + page.body:
            err(f"missing section '## {heading}'")

    present = kb.auto_blocks(page.body)
    for block in BLOCKS.get(kind, ()):
        if block not in present:
            err(f"missing generated block <!-- auto:{block} --> ... <!-- /auto:{block} -->")

    return errors


def _is_timestamp(s: str) -> bool:
    parts = s.split(":")
    return 2 <= len(parts) <= 3 and all(p.isdigit() for p in parts) and all(len(p) == 2 for p in parts[1:])


def validate(docs: Path = kb.DOCS) -> list[str]:
    errors = []
    pages = []
    for path in sorted(docs.rglob("*.md")):
        try:
            meta, body = kb.split_front_matter(path.read_text(encoding="utf-8"))
        except Exception as e:  # malformed YAML
            errors.append(f"{path.relative_to(docs.parent)}: cannot parse front matter: {e}")
            continue
        if meta.get("type"):
            pages.append(kb.Page(path, meta, body))
        elif path.parent.name in kb.FOLDERS.values() and path.name != "index.md":
            errors.append(f"{path.relative_to(docs.parent)}: missing 'type' in front matter")
    refs = kb.index(pages)
    for page in pages:
        errors.extend(check_page(page, refs, docs))
    return errors


def main(argv: list[str]) -> int:
    docs = Path(argv[1]) if len(argv) > 1 else kb.DOCS
    errors = validate(docs)
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} problem(s) found.")
        return 1
    print(f"OK: {len(kb.load_pages(docs))} pages valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
