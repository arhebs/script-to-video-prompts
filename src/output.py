from __future__ import annotations

import csv
from dataclasses import dataclass
import json
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
            obj = {
                "id": row.get("id", ""),
                "paragraph": row.get("paragraph", ""),
                "prompt": row.get("prompt", ""),
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
