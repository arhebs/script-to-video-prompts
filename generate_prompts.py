from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.openai_client import OpenAIClient, OpenAIClientConfig
from src.output import CsvWriterConfig, write_csv
from src.parser import Paragraph, parse_numbered_paragraphs


def build_arg_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="generate_prompts",
        description=(
            "Generate 1 English cinematic video prompt per numbered paragraph "
            "and export results to CSV."
        ),
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to input script file (UTF-8 text).",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to output CSV.",
    )

    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name.")
    parser.add_argument(
        "--store",
        action="store_true",
        help="Enable OpenAI response storage (default: false).",
    )
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-output-tokens", type=int, default=300)

    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Start paragraph id (inclusive).",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End paragraph id (inclusive).",
    )
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated list of paragraph ids to process (takes precedence).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process first N paragraphs in file order.",
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file if it exists (write header only once).",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "tsv"],
        default="csv",
        help="Output format.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Output encoding (e.g. utf-8-sig).",
    )

    return parser


def select_paragraphs(
    paragraphs: list[Paragraph],
    *,
    ids_csv: str | None,
    start: int | None,
    end: int | None,
    limit: int | None,
) -> list[Paragraph]:
    if ids_csv is not None:
        raw_parts = [p.strip() for p in ids_csv.split(",")]
        parts = [p for p in raw_parts if p]
        try:
            wanted = {int(p) for p in parts}
        except ValueError as e:
            raise ValueError("--ids must be a comma-separated list of integers") from e
        return [p for p in paragraphs if p.id in wanted]

    selected = paragraphs

    if start is not None or end is not None:
        if start is not None and end is not None and start > end:
            raise ValueError("--start must be <= --end")
        lo = start if start is not None else -(2**31)
        hi = end if end is not None else 2**31 - 1
        selected = [p for p in selected if lo <= p.id <= hi]

    if limit is not None:
        if limit < 0:
            raise ValueError("--limit must be >= 0")
        selected = selected[:limit]

    return selected


def main() -> int:
    args = build_arg_parser().parse_args()

    input_path: Path = args.input
    output_path: Path = args.output

    model: str = args.model
    store: bool = args.store
    temperature: float = args.temperature
    max_output_tokens: int = args.max_output_tokens

    start: int | None = args.start
    end: int | None = args.end
    ids: str | None = args.ids
    limit: int | None = args.limit

    append: bool = args.append
    format_name: str = args.format
    encoding: str = args.encoding

    try:
        text = input_path.read_text(encoding="utf-8")
        paragraphs = parse_numbered_paragraphs(text)
        selected = select_paragraphs(
            paragraphs,
            ids_csv=ids,
            start=start,
            end=end,
            limit=limit,
        )

        client = OpenAIClient(
            OpenAIClientConfig(
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                store=store,
            )
        )

        rows: list[dict[str, str]] = []
        for p in selected:
            prompt = client.generate_prompt(paragraph_id=p.id, paragraph_text=p.text)
            rows.append({"id": str(p.id), "paragraph": p.text, "prompt": prompt})

        delimiter = "\t" if format_name == "tsv" else ","
        write_csv(
            rows,
            output_path,
            CsvWriterConfig(append=append, encoding=encoding, delimiter=delimiter),
        )

        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
