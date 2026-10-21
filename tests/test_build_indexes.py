from conftest import ROOT, edit

import build_indexes
import kb


def build(docs):
    changed = build_indexes.Builder(docs).build()
    for path, text in changed.items():
        path.write_text(text, encoding="utf-8")
    return changed


def block(path, name):
    text = path.read_text(encoding="utf-8")
    start = text.index(f"<!-- auto:{name} -->")
    end = text.index(f"<!-- /auto:{name} -->")
    return text[start:end]


def test_build_is_idempotent(docs):
    assert build(docs)
    assert build_indexes.Builder(docs).build() == {}


def test_repository_indexes_are_up_to_date():
    stale = build_indexes.Builder(ROOT / "docs").build()
    assert not stale, f"run scripts/build_indexes.py: {sorted(map(str, stale))}"


def test_claim_card(docs):
    build(docs)
    card = block(docs / "claims/sky-is-green.md", "card")
    assert "verdict-card--false" in card
    assert ">False<" in card
    assert "[Ann](../people/ann.md)" in card
    assert "[The Show](../sources/show.md) at 12:30" in card
    assert "80% likely true" in card


def test_scorecard_counts(docs):
    build(docs)
    card = block(docs / "people/ann.md", "scorecard")
    assert "**Claims checked:** 2 · **Predictions tracked:** 1" in card
    assert "badge--true" in card and "badge--false" in card
    assert "Open: 1" in card


def test_source_lists_claims_in_timestamp_order(docs):
    build(docs)
    items = block(docs / "sources/show.md", "claims")
    assert items.index("sky-is-green") < items.index("water-is-wet")  # 12:30 before 1:02:03
    assert "rain-tomorrow" in items


def test_thinking_page_lists_tagged_claims_only(docs):
    build(docs)
    items = block(docs / "thinking/doubt.md", "claims")
    assert "sky-is-green" in items and "water-is-wet" not in items


def test_claims_grouped_by_verdict_in_scale_order(docs):
    build(docs)
    text = block(docs / "claims/index.md", "by-verdict")
    assert text.index("## True") < text.index("## False")


def test_latest_is_newest_first(docs):
    build(docs)
    text = block(docs / "index.md", "latest")
    assert text.index("rain-tomorrow") < text.index("sky-is-green") < text.index("water-is-wet")


def test_calibration_scores(docs):
    build(docs)
    text = block(docs / "calibration.md", "calibration")
    # sky-is-green: prior 80, false -> (0.8-0)^2 = 0.64; water-is-wet: prior 20, true -> 0.64
    assert "**Priors recorded:** 2 · **Scorable:** 2" in text
    assert "**Brier score:** 0.640" in text
    assert "**Leaned the right way:** 0/2 (0%)" in text
    assert "Fooled me" in text and "sky-is-green" in text.split("Fooled me")[1]
    assert "Surprised me" in text and "water-is-wet" in text.split("Surprised me")[1]


def test_calibration_skips_unscorable_verdicts(docs):
    edit(docs / "claims/sky-is-green.md", 'verdict: "false"', "verdict: contested")
    build(docs)
    text = block(docs / "calibration.md", "calibration")
    assert "**Scorable:** 1" in text


def test_calibration_empty_state(docs):
    for name in ("sky-is-green", "water-is-wet"):
        path = docs / f"claims/{name}.md"
        text = path.read_text()
        path.write_text(text.replace("prior: 80", "prior: null").replace("prior: 20", "prior: null"))
    build(docs)
    assert "No priors recorded yet" in block(docs / "calibration.md", "calibration")


def test_check_mode(docs, capsys):
    assert build_indexes.main(["--check", "--docs", str(docs)]) == 1
    assert "STALE" in capsys.readouterr().out
    assert build_indexes.main(["--docs", str(docs)]) == 0
    assert build_indexes.main(["--check", "--docs", str(docs)]) == 0


def test_replace_block_leaves_other_text_alone():
    text = "a\n<!-- auto:x -->\nold\n<!-- /auto:x -->\nb\n<!-- auto:y -->\nkeep\n<!-- /auto:y -->\n"
    out = kb.replace_block(text, "x", "new")
    assert out == "a\n<!-- auto:x -->\nnew\n<!-- /auto:x -->\nb\n<!-- auto:y -->\nkeep\n<!-- /auto:y -->\n"
    assert kb.replace_block(out, "x", "new\n\n") == out


def test_table_cells_escape_pipes(docs):
    edit(docs / "claims/sky-is-green.md", "title: The sky is green", "title: Sky | green")
    build(docs)
    assert "Sky \\| green" in block(docs / "claims/index.md", "by-verdict")
