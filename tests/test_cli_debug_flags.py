from __future__ import annotations

from pathlib import Path

from generate_prompts import main


def test_print_instructions_exits_zero_without_io(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--print-instructions",
            "--input",
            str(inp),
            "--output",
            str(out),
        ],
    )

    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert captured.out.strip() != ""
    assert not out.exists()


def test_dry_run_does_not_call_openai_or_write_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    from src.openai_client import OpenAIClient

    def should_not_be_called(self, *, paragraph_id: int, paragraph_text: str) -> str:
        raise AssertionError("OpenAI should not be called during --dry-run")

    monkeypatch.setattr(OpenAIClient, "generate_prompt", should_not_be_called)

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--dry-run",
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

    captured = capsys.readouterr()
    assert "dry-run" in captured.err
    assert not out.exists()
