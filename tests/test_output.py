from pathlib import Path

from src.output import CsvWriterConfig, write_csv


def test_write_csv_smoke(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    write_csv(
        [{"id": "1", "paragraph": "hello", "prompt": "world"}],
        out,
        CsvWriterConfig(),
    )
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "id,paragraph,prompt" in text
