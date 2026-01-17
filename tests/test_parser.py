from src.parser import parse_numbered_paragraphs


def test_parse_numbered_paragraphs_smoke() -> None:
    text = """\
1. First line
2) Second line
3 - Third line
"""
    paragraphs = parse_numbered_paragraphs(text)
    assert [p.id for p in paragraphs] == [1, 2, 3]
