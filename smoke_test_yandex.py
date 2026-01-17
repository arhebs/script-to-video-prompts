from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="smoke_test_yandex",
        description=(
            "End-to-end smoke test for script-to-video-prompts using a Yandex Disk public .docx URL. "
            "Runs the real CLI and validates output shape."
        ),
    )

    _ = p.add_argument(
        "--yandex-url",
        required=True,
        help="Yandex Disk public URL to a .docx with numbered list paragraphs.",
    )
    _ = p.add_argument(
        "--out",
        default="smoke_out.csv",
        help="Output CSV path (default: smoke_out.csv).",
    )
    _ = p.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of prompts to generate (default: 3).",
    )
    _ = p.add_argument(
        "--format",
        choices=["csv", "tsv"],
        default="csv",
        help="Output format passed to CLI (default: csv).",
    )
    _ = p.add_argument(
        "--include-meta",
        action="store_true",
        help="Include model metadata columns.",
    )
    _ = p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse only; do not call the model or write outputs.",
    )
    _ = p.add_argument(
        "--max-output-tokens",
        type=int,
        default=None,
        help="Override CLI --max-output-tokens.",
    )

    return p


def _run_cli(args: argparse.Namespace) -> int:
    cmd: list[str] = [
        sys.executable,
        str(Path(__file__).parent / "generate_prompts.py"),
        "--yandex-url",
        args.yandex_url,
        "--output",
        args.out,
        "--limit",
        str(args.limit),
        "--format",
        args.format,
    ]

    if args.include_meta:
        cmd.append("--include-meta")

    if args.dry_run:
        cmd.append("--dry-run")

    if args.max_output_tokens is not None:
        cmd.extend(["--max-output-tokens", str(args.max_output_tokens)])

    import subprocess

    proc = subprocess.run(cmd, text=True)
    return int(proc.returncode)


def _validate_csv(path: Path, *, include_meta: bool, delimiter: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Expected output file not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            raise RuntimeError("Output CSV missing header")

        expected = ["id", "paragraph", "prompt"]
        if include_meta:
            expected += ["model", "response_id", "timestamp"]

        missing = [c for c in expected if c not in reader.fieldnames]
        if missing:
            raise RuntimeError(
                f"Output CSV missing columns: {missing}; got: {reader.fieldnames}"
            )

        rows = list(reader)
        if not rows:
            raise RuntimeError("Output CSV has no data rows")

        first = rows[0]
        if not (first.get("id") or "").strip():
            raise RuntimeError("First row missing id")
        if not (first.get("paragraph") or "").strip():
            raise RuntimeError("First row missing paragraph")
        if not (first.get("prompt") or "").strip():
            raise RuntimeError("First row missing prompt")


def main() -> int:
    _ = load_dotenv(dotenv_path=Path(".env"), override=False)

    ns = build_arg_parser().parse_args()

    if not ns.dry_run and not os.environ.get("OPENAI_API_KEY"):
        print(
            "error: OPENAI_API_KEY is not set (required for non --dry-run)",
            file=sys.stderr,
        )
        return 2

    code = _run_cli(ns)
    if code != 0:
        return code

    if ns.dry_run:
        print("ok: dry-run completed")
        return 0

    delimiter = "\t" if ns.format == "tsv" else ","
    _validate_csv(Path(ns.out), include_meta=bool(ns.include_meta), delimiter=delimiter)
    print(f"ok: wrote and validated {ns.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
