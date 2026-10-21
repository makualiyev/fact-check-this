import pytest
from conftest import ROOT, edit

import validate


def errors_for(docs):
    return validate.validate(docs)


def test_fixture_is_valid(docs):
    assert errors_for(docs) == []


def test_repository_docs_are_valid():
    assert validate.validate(ROOT / "docs") == []


@pytest.mark.parametrize("old,new,expected", [
    ('verdict: "false"', "verdict: wrongish", "verdict: 'wrongish' is not one of"),
    ('verdict: "false"', "verdict: false", "YAML read this as a boolean"),
    ("speaker: ann", "speaker: bob", "no person page named 'bob'"),
    ("topics: [history]", "topics: [geography]", "no topic page named 'geography'"),
    ("prior: 80", "prior: 120", "prior: must be a whole number 0-100"),
    ("prior: 80", "prior: 0.8", "prior: must be a whole number 0-100"),
    ('timestamp: "12:30"', 'timestamp: "12m30"', "timestamp:"),
    ("date_checked: 2026-01-02", "date_checked: soon", "is not a YYYY-MM-DD date"),
    ("confidence: high", "confidence: total", "confidence:"),
    ("claim_type: fact\n", "", "missing front matter field 'claim_type'"),
    ("## Steelman\n", "## Steel man\n", "missing section '## Steelman'"),
    ("<!-- auto:card -->\n<!-- /auto:card -->\n", "", "missing generated block <!-- auto:card -->"),
])
def test_claim_errors(docs, old, new, expected):
    edit(docs / "claims/sky-is-green.md", old, new)
    errs = errors_for(docs)
    assert any(expected in e for e in errs), errs


def test_speaker_must_belong_to_source(docs):
    (docs / "people/bob.md").write_text(
        (docs / "people/ann.md").read_text().replace("title: Ann", "title: Bob"))
    edit(docs / "claims/sky-is-green.md", "speaker: ann", "speaker: bob")
    assert any("not listed in the speakers of source 'show'" in e for e in errors_for(docs))


def test_resolved_prediction_needs_date(docs):
    edit(docs / "predictions/rain-tomorrow.md", "status: open", "status: correct")
    assert any("need a resolved_on date" in e for e in errors_for(docs))


def test_open_prediction_must_not_have_resolution_date(docs):
    edit(docs / "predictions/rain-tomorrow.md", "status: open", "status: open\nresolved_on: 2026-02-01")
    assert any("must not have resolved_on" in e for e in errors_for(docs))


def test_page_in_wrong_folder(docs):
    src = docs / "claims/sky-is-green.md"
    (docs / "topics/sky-is-green.md").write_text(src.read_text())
    src.unlink()
    assert any("belong in docs/claims/" in e for e in errors_for(docs))


def test_untyped_page_in_kb_folder(docs):
    (docs / "claims/notes.md").write_text("# just notes\n")
    assert any("missing 'type'" in e for e in errors_for(docs))


def test_bad_yaml_is_reported_not_raised(docs):
    (docs / "claims/broken.md").write_text("---\ntitle: [unclosed\n---\n")
    assert any("cannot parse front matter" in e for e in errors_for(docs))


def test_main_exit_codes(docs, capsys):
    assert validate.main(["validate.py", str(docs)]) == 0
    edit(docs / "claims/sky-is-green.md", "speaker: ann", "speaker: bob")
    assert validate.main(["validate.py", str(docs)]) == 1
    assert "1 problem(s) found" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["claim", "prediction", "source", "person", "topic", "thinking"])
def test_templates_match_schema(kind):
    import kb
    meta, body = kb.split_front_matter((ROOT / "templates" / f"{kind}.md").read_text())
    assert meta["type"] == kind
    for key in validate.REQUIRED[kind]:
        assert key in meta, f"templates/{kind}.md lacks {key}"
    for heading in validate.SECTIONS.get(kind, ()):
        assert f"## {heading}\n" in body
    for block in validate.BLOCKS[kind]:
        assert f"<!-- auto:{block} -->" in body
