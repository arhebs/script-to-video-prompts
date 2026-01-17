from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

_BASE_FIELDNAMES = ["id", "paragraph", "prompt"]
_META_FIELDNAMES = ["model", "response_id", "timestamp"]


@dataclass(frozen=True, slots=True)
class CsvWriterConfig:
    append: bool = False
    encoding: str = "utf-8"
    delimiter: str = ","
    include_meta: bool = False


def write_csv(rows: list[dict[str, str]], path: Path, config: CsvWriterConfig) -> None:
    fieldnames = _BASE_FIELDNAMES + (_META_FIELDNAMES if config.include_meta else [])

    path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if config.append else "w"
    file_exists = path.exists()

    with path.open(mode, newline="", encoding=config.encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=config.delimiter)
        if not config.append or not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_jsonl(
    rows: list[dict[str, str]],
    path: Path,
    *,
    append: bool,
    encoding: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if append else "w"
    with path.open(mode, encoding=encoding) as f:
        for row in rows:
            _ = f.write(json.dumps(row, ensure_ascii=False) + "\n")
