#!/usr/bin/env python3
"""Get a YouTube transcript with timestamps, or search one for a quote.

Usage:
  python scripts/fetch_transcript.py URL_OR_ID [--lang en] [--grep "Paul"]
  python scripts/fetch_transcript.py --from-file pasted.txt --grep "Paul"

Fetching needs network access to youtube.com. When that is blocked, open the
video on YouTube -> "...more" -> "Show transcript", copy it all into a text
file and use --from-file; the same --grep search works on it.

Transcripts are saved to .cache/transcripts/ (git-ignored): they are working
material for quoting accurately, not content for the site.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "transcripts"

ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([\w-]{11})")
TS_RE = re.compile(r"^(\d{1,2}(?::\d{2}){1,2})\s*(.*)$")


def video_id(url_or_id: str) -> str:
    if re.fullmatch(r"[\w-]{11}", url_or_id):
        return url_or_id
    m = ID_RE.search(url_or_id)
    if not m:
        raise ValueError(f"can't find a video id in {url_or_id!r}")
    return m.group(1)


def fmt(seconds: float) -> str:
    s = int(seconds)
    h, m, s = s // 3600, s // 60 % 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def to_seconds(ts: str) -> int:
    total = 0
    for part in ts.split(":"):
        total = total * 60 + int(part)
    return total


def parse_pasted(text: str) -> list[tuple[float, str]]:
    """Parse YouTube's copied transcript: either "0:05 text" on one line, or a
    timestamp line followed by its text line(s)."""
    lines: list[tuple[float, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = TS_RE.match(line)
        if m:
            lines.append((to_seconds(m.group(1)), m.group(2)))
        elif lines:
            start, prev = lines[-1]
            lines[-1] = (start, f"{prev} {line}".strip())
    return [(s, t) for s, t in lines if t]


def fetch(vid: str, lang: str) -> list[tuple[float, str]]:
    from youtube_transcript_api import YouTubeTranscriptApi

    transcript = YouTubeTranscriptApi().fetch(vid, languages=[lang, "en"])
    return [(s.start, s.text.replace("\n", " ")) for s in transcript]


def render(snippets: list[tuple[float, str]]) -> str:
    return "\n".join(f"[{fmt(s)}] {t}" for s, t in snippets) + "\n"


def grep(snippets: list[tuple[float, str]], query: str, context: int = 1) -> list[str]:
    """Matching lines with `context` lines either side, blocks separated by ---."""
    q = query.lower()
    hits = [i for i, (_, t) in enumerate(snippets) if q in t.lower()]
    blocks, last = [], -1
    for i in hits:
        lo, hi = max(0, i - context), min(len(snippets), i + context + 1)
        if lo <= last:
            blocks[-1].extend(range(last + 1, hi))
        else:
            blocks.append(list(range(lo, hi)))
        last = hi - 1
    return ["\n".join(f"[{fmt(snippets[j][0])}] {snippets[j][1]}" for j in b) for b in blocks]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?", help="YouTube URL or 11-character id")
    ap.add_argument("--from-file", type=Path, help="transcript text copied from YouTube")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--grep", help="show only lines containing this text (case-insensitive)")
    ap.add_argument("--context", type=int, default=1, help="lines of context around --grep hits")
    args = ap.parse_args(argv)

    if args.from_file:
        snippets = parse_pasted(args.from_file.read_text(encoding="utf-8"))
    elif args.video:
        vid = video_id(args.video)
        try:
            snippets = fetch(vid, args.lang)
        except Exception as e:  # network policy, no captions, video removed...
            print(f"Could not fetch transcript for {vid}: {type(e).__name__}: {e}".strip(), file=sys.stderr)
            print("If youtube.com is blocked, paste the transcript into a file and use --from-file.",
                  file=sys.stderr)
            return 2
        CACHE.mkdir(parents=True, exist_ok=True)
        out = CACHE / f"{vid}.txt"
        out.write_text(render(snippets), encoding="utf-8")
        print(f"saved {len(snippets)} lines to {out.relative_to(ROOT)}", file=sys.stderr)
    else:
        ap.error("give a video URL/id or --from-file")

    if args.grep:
        blocks = grep(snippets, args.grep, args.context)
        print("\n---\n".join(blocks) if blocks else f"no lines contain {args.grep!r}")
    elif args.from_file:
        sys.stdout.write(render(snippets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
