from __future__ import annotations

from pathlib import Path

from generate_prompts import main
from src.openai_client import PromptResult


def test_yandex_url_downloads_and_reads_docx(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "out.csv"

    def fake_download(public_url: str, dest: Path) -> None:
        assert public_url == "https://yandex.example/public"
        dest.write_bytes(b"fake-docx")

    monkeypatch.setattr("generate_prompts.download_public_file", fake_download)

    def fake_read_docx_text(path: Path) -> str:
        assert path.read_bytes() == b"fake-docx"
        return "1. Hello\n"

    monkeypatch.setattr("generate_prompts.read_docx_text", fake_read_docx_text)

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        _ = paragraph_id
        _ = paragraph_text
        return PromptResult(prompt="ok", model="m", response_id="r", timestamp="t")

    monkeypatch.setattr(OpenAIClient, "generate_prompt", fake_generate_prompt)

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--yandex-url",
            "https://yandex.example/public",
            "--output",
            str(out),
            "--limit",
            "1",
        ],
    )

    code = main()
    assert code == 0
    assert out.exists()
