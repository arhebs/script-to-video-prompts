# script-to-video-prompts

CLI tool that turns a numbered script (one paragraph per number) into 1 cinematic English video prompt per paragraph
using an OpenAI-compatible API (Responses API or Chat Completions). Exports results to CSV/TSV and optionally JSONL.

## What It Does

- Reads an input script from:
    - Local `.txt`
    - Local `.docx`
    - A public Yandex Disk URL pointing to a `.docx`
- Parses numbered paragraphs (e.g. `1.`, `1)`, `1 -`, `1:`)
- Calls a model once per selected paragraph
- Writes an export mapping:
    - `id`: paragraph number
    - `paragraph`: normalized paragraph text (single line)
    - `prompt`: model output (single line)
    - Optional metadata: `model`, `response_id`, `timestamp`

## Requirements

- Python 3.12+

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Dev tools:

```bash
pip install -e ".[dev]"
```

## Configuration

Set these environment variables (or put them in `.env` in the repo root):

- `OPENAI_API_KEY` (required for live runs)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` (optional; for OpenAI-compatible providers)
- `OPENAI_API_MODE` (`responses` or `chat`; default: `responses`)

Example `.env`:

```bash
OPENAI_API_KEY=...
OPENAI_API_MODE=chat
OPENAI_BASE_URL=https://api.cerebras.ai/v1
OPENAI_MODEL=gpt-oss-120b
```

## Usage

### From a Yandex Disk public URL (DOCX)

```bash
.venv/bin/python generate_prompts.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --output out.csv \
  --limit 10
```

### From a local file

```bash
.venv/bin/python generate_prompts.py --input script.txt --output out.csv
.venv/bin/python generate_prompts.py --input script.docx --output out.csv
```

### Output formats

```bash
# TSV
.venv/bin/python generate_prompts.py --input script.txt --output out.tsv --format tsv

# Optional JSONL (one object per row)
.venv/bin/python generate_prompts.py \
  --input script.txt \
  --output out.csv \
  --jsonl out.jsonl
```

### Selection

- `--ids 1,5,12`: explicit list (highest precedence)
- `--start N --end M`: inclusive range
- `--limit K`: first K paragraphs in file order

### Metadata

```bash
.venv/bin/python generate_prompts.py \
  --input script.txt \
  --output out.csv \
  --include-meta
```

## DOCX Notes (Word Numbering)

Word numbered lists often store the visible `1.`, `2.`, ... markers as formatting, not literal text.

This repo extracts numbered-list items from `.docx` by reading Word's internal structure and synthesizing `N. <text>`
lines. Headings that are not part of a numbered list are ignored.

For best results, ensure the script paragraphs use Word's native numbering (not manual typing).

## Common Issues

- `Empty model output`
    - Most commonly: output got truncated.
    - Fix: increase `--max-output-tokens`.
    - Default is 800; for verbose providers/models you can bump to 1000+.

- Rate limits (HTTP 429)
    - Fix: run in batches with `--start/--end` or smaller `--limit`, and use `--append` to build one CSV.
    - Note: when using `--append`, keep output columns consistent across runs (e.g. don't toggle `--include-meta`).

## End-to-End Smoke Test (for demo)

A single script that runs the real CLI against a real model, using a Yandex URL directly.

The smoke test script loads `.env` from the repo root (same behavior as the main CLI).

Defaults (script-level):

- `--limit 3`
- `--out smoke_out.csv`
- `--format csv`
- `--include-meta` off
- `--dry-run` off (note: selection errors still exit non-zero)
- `--max-output-tokens` not set (the script uses the CLI default unless you override it)

How to override: pass flags to `smoke_test_yandex.py`.

```bash
# Dry-run (parsing/selection only; no model calls and no output writes)
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --dry-run

# Dry-run, parse more paragraphs
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --dry-run \
  --limit 133

# Live run (requires OPENAI_API_KEY)
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --limit 3 \
  --include-meta \
  --out smoke_out.csv

# Live run with token override and TSV
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --limit 5 \
  --max-output-tokens 1000 \
  --format tsv \
  --out smoke_out.tsv
```

Demo Matrix

```bash
# 1) CSV, no metadata
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --limit 1 \
  --out demo_nometa.csv

# 2) TSV + metadata columns
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --limit 1 \
  --include-meta \
  --format tsv \
  --out demo_meta.tsv

# 3) Higher output token budget
.venv/bin/python smoke_test_yandex.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --limit 2 \
  --include-meta \
  --max-output-tokens 1000 \
  --out demo_tokens.csv

# 4) CLI JSONL export in the same run
.venv/bin/python generate_prompts.py \
  --yandex-url "https://disk.yandex.ru/i/UEBvT8gBETe8Kg" \
  --limit 2 \
  --include-meta \
  --output demo_cli.csv \
  --jsonl demo_cli.jsonl
```

The smoke test validates:

- CLI invocation works end-to-end
- The output file exists
- The header contains expected columns
- The first row has non-empty `id`, `paragraph`, and `prompt`

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Lint

```bash
.venv/bin/ruff check .
```
