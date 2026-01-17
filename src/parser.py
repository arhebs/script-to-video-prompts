from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class Paragraph:
    id: int
    text: str


_HEADER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(\d+)\.(\s+)(.+)$"),
    re.compile(r"^\s*(\d+)\)(\s+)(.+)$"),
    re.compile(r"^\s*(\d+)\s*[-:]\s+(.+)$"),
]


def parse_numbered_paragraphs(text: str) -> list[Paragraph]:
    lines = text.splitlines()

    current_id: int | None = None
    current_parts: list[str] = []
    out: list[Paragraph] = []

    def flush() -> None:
        nonlocal current_id, current_parts
        if current_id is None:
            return
        joined = " ".join(x.strip() for x in current_parts if x.strip()).strip()
        out.append(Paragraph(id=current_id, text=joined))
        current_id = None
        current_parts = []

    for line in lines:
        matched = None
        for pat in _HEADER_PATTERNS:
            m = pat.match(line)
            if m:
                matched = (pat, m)
                break

        if matched is None:
            if current_id is None:
                continue
            current_parts.append(line)
            continue

        _, m = matched
        flush()

        current_id = int(m.group(1))
        if m.lastindex == 3:
            current_parts.append(m.group(3))
        else:
            current_parts.append(m.group(2))

    flush()
    return out
