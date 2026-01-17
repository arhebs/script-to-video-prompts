from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from src.openai_client import OpenAIClient, OpenAIClientConfig
from src.output import CsvWriterConfig, write_csv, write_jsonl
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

    parser.add_argument(
        "--model",
        default=None,
        help="Model name (defaults to env OPENAI_MODEL or gpt-4o-mini).",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL (defaults to env OPENAI_BASE_URL).",
    )
    parser.add_argument(
        "--api-mode",
        choices=["responses", "chat"],
        default=None,
        help="API mode (defaults to env OPENAI_API_MODE or responses).",
    )
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
    parser.add_argument(
        "--jsonl",
        default=None,
        type=Path,
        help="Optional JSONL output path (writes one JSON object per row).",
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
    load_dotenv(dotenv_path=Path(".env"), override=False)

    args = build_arg_parser().parse_args()

    input_path: Path = args.input
    output_path: Path = args.output

    env_model = os.environ.get("OPENAI_MODEL")
    env_base_url = os.environ.get("OPENAI_BASE_URL")
    env_api_mode = os.environ.get("OPENAI_API_MODE")

    model: str = args.model or env_model or "gpt-4o-mini"
    base_url: str | None = args.base_url or env_base_url
    api_mode: str = args.api_mode or env_api_mode or "responses"
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
    jsonl_path: Path | None = args.jsonl

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
                base_url=base_url,
                api_mode=api_mode,
            )
        )

        total = len(selected)
        print(f"processing {total} paragraph(s)", file=sys.stderr)

        rows: list[dict[str, str]] = []
        for i, p in enumerate(selected, start=1):
            print(
                f"[{i}/{total}] generating prompt for paragraph {p.id}...",
                file=sys.stderr,
            )
            prompt = client.generate_prompt(paragraph_id=p.id, paragraph_text=p.text)
            rows.append({"id": str(p.id), "paragraph": p.text, "prompt": prompt})

        print(f"generated {len(rows)} prompt(s)", file=sys.stderr)

        delimiter = "\t" if format_name == "tsv" else ","
        write_csv(
            rows,
            output_path,
            CsvWriterConfig(append=append, encoding=encoding, delimiter=delimiter),
        )
        print(f"wrote {output_path}", file=sys.stderr)

        if jsonl_path is not None:
            write_jsonl(rows, jsonl_path, append=append, encoding=encoding)
            print(f"wrote {jsonl_path}", file=sys.stderr)

        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
