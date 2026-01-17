from __future__ import annotations

from pathlib import Path

from generate_prompts import main
from src.openai_client import PromptResult


def test_append_fails_on_header_mismatch_include_meta(
    tmp_path: Path, monkeypatch
) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    out.write_text("id,paragraph,prompt\n", encoding="utf-8")

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        _ = paragraph_id
        _ = paragraph_text
        return PromptResult(prompt="ok", model="m", response_id="r", timestamp="t")

    monkeypatch.setattr(OpenAIClient, "generate_prompt", fake_generate_prompt)

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--input",
            str(inp),
            "--output",
            str(out),
            "--append",
            "--include-meta",
            "--limit",
            "1",
        ],
    )

    code = main()
    assert code == 1


def test_append_writes_header_when_file_exists_but_empty(
    tmp_path: Path, monkeypatch
) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")
    out.write_text("", encoding="utf-8")

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        _ = paragraph_id
        _ = paragraph_text
        return PromptResult(prompt="ok", model="m", response_id="r", timestamp="t")

    monkeypatch.setattr(OpenAIClient, "generate_prompt", fake_generate_prompt)

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--input",
            str(inp),
            "--output",
            str(out),
            "--append",
            "--limit",
            "1",
        ],
    )

    code = main()
    assert code == 0

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "id,paragraph,prompt"
    assert len(lines) == 2
