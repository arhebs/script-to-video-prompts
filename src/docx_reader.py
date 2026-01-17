from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast
import importlib


class _DocxParagraph(Protocol):
    text: str


class _DocxDocument(Protocol):
    paragraphs: Sequence[_DocxParagraph]


class _DocxModule(Protocol):
    def Document(self, path: str) -> _DocxDocument: ...


def read_docx_text(path: Path) -> str:
    try:
        docx_module = cast(_DocxModule, cast(object, importlib.import_module("docx")))
    except ImportError as e:
        raise RuntimeError("python-docx is required to read .docx inputs") from e

    document = docx_module.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs)
