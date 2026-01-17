from __future__ import annotations

from pathlib import Path
import zipfile

from src.docx_reader import read_docx_text


def _build_minimal_numbered_docx(path: Path) -> None:
    xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:body>
    <w:p>
      <w:r><w:t>Introduction</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:numPr>
          <w:ilvl w:val='0'/>
          <w:numId w:val='42'/>
        </w:numPr>
      </w:pPr>
      <w:r><w:t>First item</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:numPr>
          <w:ilvl w:val='0'/>
          <w:numId w:val='42'/>
        </w:numPr>
      </w:pPr>
      <w:r><w:t>Second item</w:t></w:r>
    </w:p>
    <w:sectPr />
  </w:body>
</w:document>
"""

    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", xml)


def test_read_docx_text_extracts_numbered_list_and_skips_headings(
    tmp_path: Path,
) -> None:
    docx_path = tmp_path / "input.docx"
    _build_minimal_numbered_docx(docx_path)

    text = read_docx_text(docx_path)

    assert text.splitlines() == [
        "1. First item",
        "2. Second item",
    ]
