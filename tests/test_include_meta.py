from __future__ import annotations

from pathlib import Path

from generate_prompts import main
from src.openai_client import PromptResult


def test_include_meta_adds_columns(tmp_path: Path, monkeypatch) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        _ = paragraph_id
        _ = paragraph_text
        return PromptResult(
            prompt="test prompt",
            model="test-model",
            response_id="resp-123",
            timestamp="2025-01-01T00:00:00Z",
        )

    monkeypatch.setattr(OpenAIClient, "generate_prompt", fake_generate_prompt)

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--input",
            str(inp),
            "--output",
            str(out),
            "--include-meta",
            "--limit",
            "1",
        ],
    )

    code = main()
    assert code == 0
    assert out.exists()

    text = out.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert "model" in lines[0]
    assert "response_id" in lines[0]
    assert "timestamp" in lines[0]
    assert "test-model" in lines[1]
    assert "resp-123" in lines[1]
