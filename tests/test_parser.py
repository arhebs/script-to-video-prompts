import pytest

from src.parser import parse_numbered_paragraphs


def test_parse_accepts_multiple_header_styles() -> None:
    text = """\
1. First
2) Second
3 - Third
4: Fourth
"""
    paragraphs = parse_numbered_paragraphs(text)
    assert [p.id for p in paragraphs] == [1, 2, 3, 4]
    assert [p.text for p in paragraphs] == ["First", "Second", "Third", "Fourth"]


def test_parse_multiline_paragraphs() -> None:
    text = """\
1. First line
second line

third line
2. Next
"""
    paragraphs = parse_numbered_paragraphs(text)
    assert paragraphs[0].id == 1
    assert paragraphs[0].text == "First line second line third line"
    assert paragraphs[1].id == 2
    assert paragraphs[1].text == "Next"


def test_parse_allows_number_only_header_then_body() -> None:
    text = """\
1.
Body line
2)
Next body
"""
    paragraphs = parse_numbered_paragraphs(text)
    assert [p.text for p in paragraphs] == ["Body line", "Next body"]


def test_parse_rejects_duplicate_ids() -> None:
    text = """\
1. One
1. Duplicate
"""
    with pytest.raises(ValueError, match=r"Duplicate paragraph id 1") as exc_info:
        parse_numbered_paragraphs(text)
    assert str(exc_info.value)


def test_parse_rejects_nonempty_leading_content() -> None:
    text = """\
Intro line
1. One
"""
    with pytest.raises(ValueError, match=r"before first paragraph header") as exc_info:
        parse_numbered_paragraphs(text)
    assert str(exc_info.value)


def test_parse_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match=r"No numbered paragraphs found") as exc_info:
        parse_numbered_paragraphs("")
    assert str(exc_info.value)
