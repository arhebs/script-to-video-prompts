from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class Paragraph:
    id: int
    text: str


_HEADER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(\d+)\.(?:\s+(.*))?$"),
    re.compile(r"^\s*(\d+)\)(?:\s+(.*))?$"),
    re.compile(r"^\s*(\d+)\s*[-:]\s*(.*)$"),
]


def parse_numbered_paragraphs(text: str) -> list[Paragraph]:
    lines = text.splitlines()

    out: list[Paragraph] = []
    seen_ids: set[int] = set()

    current_id: int | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_id, current_parts
        if current_id is None:
            return
        paragraph_text = " ".join(s.strip() for s in current_parts if s.strip())
        paragraph_text = re.sub(r"\s+", " ", paragraph_text).strip()
        out.append(Paragraph(id=current_id, text=paragraph_text))
        current_id = None
        current_parts = []

    for idx, line in enumerate(lines, start=1):
        matched = None
        for pat in _HEADER_PATTERNS:
            m = pat.match(line)
            if m:
                matched = m
                break

        if matched is None:
            if current_id is None:
                if line.strip():
                    raise ValueError(
                        f"Unexpected content before first paragraph header at line {idx}"
                    )
                continue
            current_parts.append(line)
            continue

        flush()

        paragraph_id = int(matched.group(1))
        if paragraph_id in seen_ids:
            raise ValueError(f"Duplicate paragraph id {paragraph_id} at line {idx}")
        seen_ids.add(paragraph_id)

        current_id = paragraph_id
        header_text = (
            matched.group(2) if matched.lastindex and matched.lastindex >= 2 else ""
        )
        if header_text is not None:
            current_parts.append(header_text)

    flush()

    if not out:
        raise ValueError("No numbered paragraphs found")

    return out
