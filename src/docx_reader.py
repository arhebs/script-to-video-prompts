from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Protocol, cast
import importlib
import xml.etree.ElementTree as ET
import zipfile


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS = {"w": _W_NS}


class _DocxParagraph(Protocol):
    text: str


class _DocxDocument(Protocol):
    paragraphs: Sequence[_DocxParagraph]


class _DocxModule(Protocol):
    def Document(self, path: str) -> _DocxDocument: ...


def _read_docx_document_xml(path: Path) -> ET.Element:
    with zipfile.ZipFile(path) as zf:
        xml_bytes = zf.read("word/document.xml")
    return ET.fromstring(xml_bytes)


def _extract_text_from_paragraph(p: ET.Element) -> str:
    out: list[str] = []
    for node in p.iter():
        if node.tag == f"{{{_W_NS}}}t":
            out.append(node.text or "")
        elif node.tag == f"{{{_W_NS}}}tab":
            out.append("\t")
        elif node.tag == f"{{{_W_NS}}}br":
            out.append("\n")
    return "".join(out).strip()


def _iter_numbered_paragraph_lines(root: ET.Element) -> Iterable[str]:
    counters: dict[str, dict[int, int]] = {}

    for p in root.findall(".//w:body/w:p", _NS):
        num_pr = p.find("./w:pPr/w:numPr", _NS)
        if num_pr is None:
            continue

        num_id_el = num_pr.find("./w:numId", _NS)
        if num_id_el is None:
            continue
        num_id = num_id_el.get(f"{{{_W_NS}}}val")
        if num_id is None:
            continue

        ilvl_el = num_pr.find("./w:ilvl", _NS)
        ilvl_raw = ilvl_el.get(f"{{{_W_NS}}}val") if ilvl_el is not None else None
        ilvl = int(ilvl_raw) if ilvl_raw is not None else 0

        text = _extract_text_from_paragraph(p)
        if not text:
            continue

        per_num = counters.setdefault(num_id, {})
        if ilvl == 0:
            per_num[0] = per_num.get(0, 0) + 1
            for lvl in list(per_num.keys()):
                if lvl > 0:
                    per_num[lvl] = 0
            yield f"{per_num[0]}. {text}"
            continue

        yield text


def _read_docx_text_fallback(path: Path) -> str:
    try:
        docx_module = cast(_DocxModule, cast(object, importlib.import_module("docx")))
    except ImportError as e:
        raise RuntimeError("python-docx is required to read .docx inputs") from e

    document = docx_module.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs)


def read_docx_text(path: Path) -> str:
    root = _read_docx_document_xml(path)
    numbered_lines = list(_iter_numbered_paragraph_lines(root))
    if numbered_lines:
        return "\n".join(numbered_lines)

    return _read_docx_text_fallback(path)
