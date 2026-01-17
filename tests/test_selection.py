import pytest

from generate_prompts import select_paragraphs
from src.parser import Paragraph


def test_ids_precedence_over_range_and_limit() -> None:
    paragraphs = [
        Paragraph(id=1, text="a"),
        Paragraph(id=2, text="b"),
        Paragraph(id=3, text="c"),
    ]
    selected = select_paragraphs(paragraphs, ids_csv="2", start=1, end=3, limit=1)
    assert [p.id for p in selected] == [2]


def test_range_selection_inclusive() -> None:
    paragraphs = [
        Paragraph(id=1, text="a"),
        Paragraph(id=2, text="b"),
        Paragraph(id=3, text="c"),
    ]
    selected = select_paragraphs(paragraphs, ids_csv=None, start=2, end=3, limit=None)
    assert [p.id for p in selected] == [2, 3]


def test_limit_applies_after_range() -> None:
    paragraphs = [
        Paragraph(id=1, text="a"),
        Paragraph(id=2, text="b"),
        Paragraph(id=3, text="c"),
    ]
    selected = select_paragraphs(paragraphs, ids_csv=None, start=1, end=3, limit=2)
    assert [p.id for p in selected] == [1, 2]


def test_invalid_range_rejected() -> None:
    paragraphs = [Paragraph(id=1, text="a")]
    with pytest.raises(ValueError, match=r"--start must be <= --end"):
        select_paragraphs(paragraphs, ids_csv=None, start=3, end=1, limit=None)


def test_invalid_ids_rejected() -> None:
    paragraphs = [Paragraph(id=1, text="a")]
    with pytest.raises(
        ValueError, match=r"--ids must be a comma-separated list of integers"
    ):
        select_paragraphs(paragraphs, ids_csv="1,abc", start=None, end=None, limit=None)


def test_negative_limit_rejected() -> None:
    paragraphs = [Paragraph(id=1, text="a")]
    with pytest.raises(ValueError, match=r"--limit must be >= 0"):
        select_paragraphs(paragraphs, ids_csv=None, start=None, end=None, limit=-1)
