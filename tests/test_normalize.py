from src.normalize import normalize_prompt


def test_normalize_removes_newlines_and_collapses_whitespace() -> None:
    assert normalize_prompt("a\n\n  b\t c\r\n") == "a b c"


def test_normalize_trims() -> None:
    assert normalize_prompt("  hello  ") == "hello"
