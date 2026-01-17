from generate_prompts import main
from src.openai_client import PromptResult


def test_model_defaults_to_env(tmp_path, monkeypatch) -> None:
    inp = tmp_path / "script.txt"
    out = tmp_path / "out.csv"

    inp.write_text("1. Hello\n", encoding="utf-8")

    monkeypatch.setenv("OPENAI_MODEL", "qwen-3-32b")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.cerebras.ai/v1")
    monkeypatch.setenv("OPENAI_API_MODE", "chat")

    from src.openai_client import OpenAIClient

    def fake_generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        assert paragraph_id == 1
        assert paragraph_text == "Hello"
        assert self.config.model == "qwen-3-32b"
        assert self.config.base_url == "https://api.cerebras.ai/v1"
        assert self.config.api_mode == "chat"
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
    assert out.exists()
