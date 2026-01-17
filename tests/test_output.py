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


def test_write_csv_writes_header_once_on_append(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"

    write_csv(
        [{"id": "1", "paragraph": "p1", "prompt": "q1"}],
        out,
        CsvWriterConfig(append=False),
    )
    write_csv(
        [{"id": "2", "paragraph": "p2", "prompt": "q2"}],
        out,
        CsvWriterConfig(append=True),
    )

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "id,paragraph,prompt"
    assert lines.count("id,paragraph,prompt") == 1
    assert len(lines) == 3


def test_write_csv_quotes_commas_and_quotes(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"

    write_csv(
        [{"id": "1", "paragraph": "a, b", "prompt": 'say "hi"'}],
        out,
        CsvWriterConfig(),
    )

    text = out.read_text(encoding="utf-8")
    assert '"a, b"' in text
    assert '"say ""hi"""' in text
