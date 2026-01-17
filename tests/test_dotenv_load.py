from __future__ import annotations

from pathlib import Path

from generate_prompts import main
from src.openai_client import PromptResult


def test_dotenv_is_loaded(tmp_path: Path, monkeypatch) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"
    env_path = tmp_path / ".env"

    inp.write_text("1. Hello\n", encoding="utf-8")
    env_path.write_text(
        "OPENAI_MODEL=qwen-3-32b\nOPENAI_BASE_URL=https://api.cerebras.ai/v1\nOPENAI_API_MODE=chat\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_MODE", raising=False)

    monkeypatch.chdir(tmp_path)

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        assert self.config.model == "qwen-3-32b"
        assert self.config.base_url == "https://api.cerebras.ai/v1"
        assert self.config.api_mode == "chat"
        _ = paragraph_id
        _ = paragraph_text
        return PromptResult(
            prompt="ok", model="qwen-3-32b", response_id="r1", timestamp="t1"
        )

    monkeypatch.setattr(OpenAIClient, "generate_prompt", fake_generate_prompt)

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_prompts",
            "--input",
            str(inp),
            "--output",
            str(out),
            "--limit",
            "1",
        ],
    )

    code = main()
    assert code == 0
