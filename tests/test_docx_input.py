from __future__ import annotations

from pathlib import Path

from generate_prompts import main
from src.openai_client import PromptResult


def test_docx_input_uses_docx_reader(tmp_path: Path, monkeypatch) -> None:
    inp = tmp_path / "script.docx"
    out = tmp_path / "out.csv"

    inp.write_bytes(b"fake-docx")

    def fake_read_docx_text(path: Path) -> str:
        assert path == inp
        return "1. Hello\n"

    monkeypatch.setattr(
        "generate_prompts.read_docx_text",
        fake_read_docx_text,
    )

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        assert paragraph_id == 1
        assert paragraph_text == "Hello"
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
            "--limit",
            "1",
        ],
    )

    code = main()
    assert code == 0
    assert out.exists()
