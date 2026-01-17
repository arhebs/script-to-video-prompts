from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

from src.docx_reader import read_docx_text
from src.openai_client import DEFAULT_INSTRUCTIONS, OpenAIClient, OpenAIClientConfig

from src.parser import Paragraph, parse_numbered_paragraphs
from src.yandex_docx import download_public_file

__version__ = "0.1.0"


@dataclass(frozen=True, slots=True)
class Args:
    input: Path | None
    yandex_url: str | None
    output: Path

    model: str | None
    base_url: str | None
    api_mode: str | None
    store: bool
    temperature: float
    max_output_tokens: int

    start: int | None
    end: int | None
    ids: str | None
    limit: int | None

    append: bool
    format: str
    encoding: str
    jsonl: Path | None
    include_meta: bool

    dry_run: bool
    print_instructions: bool


def build_arg_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="generate_prompts",
        description=(
            "Generate 1 English cinematic video prompt per numbered paragraph "
            "and export results to CSV."
        ),
    )

    _ = parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    _ = group.add_argument(
        "--input",
        type=Path,
        help="Path to input script file (.txt or .docx).",
    )
    _ = group.add_argument(
        "--yandex-url",
        dest="yandex_url",
        help="Yandex Disk public URL to download (.docx).",
    )
    _ = parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to output CSV.",
    )

    _ = parser.add_argument(
        "--model",
        default=None,
        help="Model name (defaults to env OPENAI_MODEL or gpt-4o-mini).",
    )
    _ = parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL (defaults to env OPENAI_BASE_URL).",
    )
    _ = parser.add_argument(
        "--api-mode",
        choices=["responses", "chat"],
        default=None,
        help="API mode (defaults to env OPENAI_API_MODE or responses).",
    )
    _ = parser.add_argument(
        "--store",
        action="store_true",
        help="Enable OpenAI response storage (default: false).",
    )
    _ = parser.add_argument("--temperature", type=float, default=0.3)
    _ = parser.add_argument("--max-output-tokens", type=int, default=800)

    _ = parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Start paragraph id (inclusive).",
    )
    _ = parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End paragraph id (inclusive).",
    )
    _ = parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated list of paragraph ids to process (takes precedence).",
    )
    _ = parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process first N paragraphs in file order.",
    )

    _ = parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file if it exists (write header only once).",
    )
    _ = parser.add_argument(
        "--format",
        choices=["csv", "tsv"],
        default="csv",
        help="Output format.",
    )
    _ = parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Output encoding (e.g. utf-8-sig).",
    )
    _ = parser.add_argument(
        "--jsonl",
        default=None,
        type=Path,
        help="Optional JSONL output path (writes one JSON object per row).",
    )
    _ = parser.add_argument(
        "--include-meta",
        action="store_true",
        help="Include metadata columns: model, response_id, timestamp.",
    )

    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse + select paragraphs, but do not call OpenAI or write outputs.",
    )
    _ = parser.add_argument(
        "--print-instructions",
        action="store_true",
        help="Print the instruction block used for the model and exit.",
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


def parse_cli_args() -> Args:
    ns = build_arg_parser().parse_args()
    return Args(
        input=cast(Path | None, ns.input),
        yandex_url=cast(str | None, ns.yandex_url),
        output=cast(Path, ns.output),
        model=cast(str | None, ns.model),
        base_url=cast(str | None, ns.base_url),
        api_mode=cast(str | None, ns.api_mode),
        store=cast(bool, ns.store),
        temperature=cast(float, ns.temperature),
        max_output_tokens=cast(int, ns.max_output_tokens),
        start=cast(int | None, ns.start),
        end=cast(int | None, ns.end),
        ids=cast(str | None, ns.ids),
        limit=cast(int | None, ns.limit),
        append=cast(bool, ns.append),
        format=cast(str, ns.format),
        encoding=cast(str, ns.encoding),
        jsonl=cast(Path | None, ns.jsonl),
        include_meta=cast(bool, ns.include_meta),
        dry_run=cast(bool, ns.dry_run),
        print_instructions=cast(bool, ns.print_instructions),
    )


def read_input_text(args: Args) -> str:
    if args.input is not None:
        suffix = args.input.suffix.lower()
        if suffix == ".docx":
            return read_docx_text(args.input)
        return args.input.read_text(encoding="utf-8")

    if args.yandex_url is None:
        raise ValueError("Either --input or --yandex-url is required")

    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "input.docx"
        download_public_file(args.yandex_url, dest)
        return read_docx_text(dest)


def main() -> int:
    _ = load_dotenv(dotenv_path=Path(".env"), override=False)

    args = parse_cli_args()

    try:
        if args.print_instructions:
            print(DEFAULT_INSTRUCTIONS)
            return 0

        model = args.model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        base_url = args.base_url or os.environ.get("OPENAI_BASE_URL")
        api_mode = args.api_mode or os.environ.get("OPENAI_API_MODE") or "responses"

        text = read_input_text(args)
        paragraphs = parse_numbered_paragraphs(text)
        selected = select_paragraphs(
            paragraphs,
            ids_csv=args.ids,
            start=args.start,
            end=args.end,
            limit=args.limit,
        )

        total = len(selected)
        print(f"processing {total} paragraph(s)", file=sys.stderr)

        if total == 0:
            if args.ids is not None:
                available = ",".join(str(p.id) for p in paragraphs)
                print(
                    "warning: no paragraphs selected; check --ids or input numbering",
                    file=sys.stderr,
                )
                print(f"requested ids: {args.ids}", file=sys.stderr)
                print(f"available ids: {available}", file=sys.stderr)
            else:
                print(
                    "warning: no paragraphs selected; check --start/--end/--limit",
                    file=sys.stderr,
                )
            return 1

        if args.dry_run:
            print("dry-run: skipping model calls and output writes", file=sys.stderr)
            return 0

        client = OpenAIClient(
            OpenAIClientConfig(
                model=model,
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
                store=args.store,
                base_url=base_url,
                api_mode=api_mode,
            )
        )

        delimiter = "\t" if args.format == "tsv" else ","
        fieldnames = ["id", "paragraph", "prompt"]
        if args.include_meta:
            fieldnames += ["model", "response_id", "timestamp"]

        output_mode = "a" if args.append else "w"
        file_exists = args.output.exists()
        file_size = args.output.stat().st_size if file_exists else 0

        if args.append and file_exists and file_size > 0:
            with args.output.open("r", newline="", encoding=args.encoding) as rf:
                reader = csv.reader(rf, delimiter=delimiter)
                try:
                    existing_header = next(reader)
                except StopIteration:
                    existing_header = []

            if existing_header != fieldnames:
                print(
                    f"error: header mismatch in {args.output} during --append",
                    file=sys.stderr,
                )
                print(f"error: existing header: {existing_header}", file=sys.stderr)
                print(f"error: expected header: {fieldnames}", file=sys.stderr)
                print(
                    "error: resolution: use consistent flags (e.g. --include-meta), a new --output path, or omit --append to overwrite",
                    file=sys.stderr,
                )
                return 1

        write_header = (not args.append) or (
            args.append and (not file_exists or file_size == 0)
        )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open(output_mode, newline="", encoding=args.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            if write_header:
                writer.writeheader()
                f.flush()

            jsonl_f = None
            if args.jsonl is not None:
                jsonl_mode = "a" if args.append else "w"
                args.jsonl.parent.mkdir(parents=True, exist_ok=True)
                jsonl_f = args.jsonl.open(jsonl_mode, encoding=args.encoding)

            wrote = 0
            try:
                for i, p in enumerate(selected, start=1):
                    print(
                        f"[{i}/{total}] generating prompt for paragraph {p.id}...",
                        file=sys.stderr,
                    )
                    result = client.generate_prompt(
                        paragraph_id=p.id, paragraph_text=p.text
                    )

                    row: dict[str, str] = {
                        "id": str(p.id),
                        "paragraph": p.text,
                        "prompt": result.prompt,
                    }
                    if args.include_meta:
                        row["model"] = result.model
                        row["response_id"] = result.response_id
                        row["timestamp"] = result.timestamp

                    writer.writerow({k: row.get(k, "") for k in fieldnames})
                    f.flush()
                    wrote += 1

                    if jsonl_f is not None:
                        _ = jsonl_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                        jsonl_f.flush()
            finally:
                if jsonl_f is not None:
                    jsonl_f.close()

        print(f"generated {wrote} prompt(s)", file=sys.stderr)
        print(f"wrote {args.output}", file=sys.stderr)
        if args.jsonl is not None:
            print(f"wrote {args.jsonl}", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
