import pytest

import fetch_transcript as ft


@pytest.mark.parametrize("value", [
    "https://www.youtube.com/watch?v=ajFXykT9Joo",
    "https://www.youtube.com/watch?v=ajFXykT9Joo&t=120s",
    "https://youtu.be/ajFXykT9Joo?si=abc",
    "https://www.youtube.com/live/ajFXykT9Joo",
    "https://www.youtube.com/embed/ajFXykT9Joo",
    "ajFXykT9Joo",
])
def test_video_id(value):
    assert ft.video_id(value) == "ajFXykT9Joo"


def test_video_id_rejects_garbage():
    with pytest.raises(ValueError):
        ft.video_id("https://example.com/nothing")


def test_fmt():
    assert ft.fmt(5) == "0:05"
    assert ft.fmt(2050.7) == "34:10"
    assert ft.fmt(3723) == "1:02:03"


def test_parse_pasted_two_line_format():
    text = "0:00\nWelcome back\n0:05\ntoday we talk\nabout Paul\n1:02:03\nthe end\n"
    assert ft.parse_pasted(text) == [(0, "Welcome back"), (5, "today we talk about Paul"), (3723, "the end")]


def test_parse_pasted_one_line_format():
    assert ft.parse_pasted("0:00 Hello\n34:10 Paul invented it\n") == [(0, "Hello"), (2050, "Paul invented it")]


def test_grep_merges_overlapping_context():
    snippets = [(i, f"line {i}") for i in range(10)]
    snippets[3] = (3, "Paul here")
    snippets[4] = (4, "and Paul again")
    snippets[8] = (8, "PAUL at the end")
    blocks = ft.grep(snippets, "paul", context=1)
    assert len(blocks) == 2
    assert blocks[0].splitlines()[0] == "[0:02] line 2" and blocks[0].splitlines()[-1] == "[0:05] line 5"
    assert "PAUL at the end" in blocks[1]


def test_main_from_file(tmp_path, capsys):
    f = tmp_path / "t.txt"
    f.write_text("0:00\nintro\n34:10\nPaul basically invented Christianity\n")
    assert ft.main(["--from-file", str(f), "--grep", "invented", "--context", "0"]) == 0
    assert capsys.readouterr().out.strip() == "[34:10] Paul basically invented Christianity"


def test_main_fetch_failure_is_friendly(monkeypatch, capsys):
    def boom(vid, lang):
        raise ConnectionError("blocked")
    monkeypatch.setattr(ft, "fetch", boom)
    assert ft.main(["ajFXykT9Joo"]) == 2
    assert "--from-file" in capsys.readouterr().err
