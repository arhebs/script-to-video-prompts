from __future__ import annotations

from pathlib import Path

from generate_prompts import main


def test_empty_selection_exits_one_and_writes_no_output(
    tmp_path: Path, monkeypatch
) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--input",
            str(inp),
            "--output",
            str(out),
            "--ids",
            "9999",
        ],
    )

    code = main()
    assert code == 1
    assert not out.exists()
