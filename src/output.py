from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CsvWriterConfig:
    append: bool = False
    encoding: str = "utf-8"
    delimiter: str = ","


def write_csv(rows: list[dict[str, str]], path: Path, config: CsvWriterConfig) -> None:
    fieldnames = ["id", "paragraph", "prompt"]

    path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if config.append else "w"
    file_exists = path.exists()

    with path.open(mode, newline="", encoding=config.encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=config.delimiter)
        if not config.append or not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
