from src.openai_client import DEFAULT_INSTRUCTIONS, build_input


def test_default_instructions_is_single_line() -> None:
    assert "\n" not in DEFAULT_INSTRUCTIONS
    assert "\r" not in DEFAULT_INSTRUCTIONS


def test_build_input_includes_id_and_text() -> None:
    assert (
        build_input(paragraph_id=12, paragraph_text=" hello ")
        == "Paragraph ID: 12\nContent:\n<narrative_text>\nhello\n</narrative_text>"
    )
