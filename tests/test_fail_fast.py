from __future__ import annotations

from pathlib import Path

from generate_prompts import main


def test_cli_fail_fast_on_openai_error(tmp_path: Path, monkeypatch) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    from src.openai_client import OpenAIClient

    def boom(self, *, paragraph_id: int, paragraph_text: str) -> str:
        _ = paragraph_id
        _ = paragraph_text
        raise RuntimeError("boom")

    monkeypatch.setattr(OpenAIClient, "generate_prompt", boom)

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

    exit_code = main()
    assert exit_code == 1
    assert not out.exists()
