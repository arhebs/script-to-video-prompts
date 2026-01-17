from __future__ import annotations

import re

_WS_RE = re.compile(r"\s+")


def normalize_prompt(text: str) -> str:
    collapsed = text.replace("\r\n", " ").replace("\n", " ")
    return _WS_RE.sub(" ", collapsed).strip()
