from __future__ import annotations

from datetime import datetime

from src.openai_client import OpenAIClient, OpenAIClientConfig


class _FakeResponses:
    def __init__(self, output_text: str) -> None:
        self._output_text = output_text

    def create(self, **kwargs: object) -> object:
        _ = kwargs

        class _Resp:
            id = "resp_1"
            output_text = self._output_text

        return _Resp()


class _FakeChatCompletions:
    def __init__(self, content: str) -> None:
        self._content = content

    def create(self, **kwargs: object) -> object:
        _ = kwargs

        class _Msg:
            def __init__(self, content: str) -> None:
                self.content = content

        class _Choice:
            def __init__(self, content: str) -> None:
                self.message = _Msg(content)

        class _Resp:
            id = "chat_1"
            choices = [_Choice(self._content)]

        return _Resp()


class _FakeClient:
    def __init__(
        self,
        *,
        responses_output_text: str,
        chat_content: str,
    ) -> None:
        self.responses = _FakeResponses(responses_output_text)

        class _Chat:
            def __init__(self, chat_content: str) -> None:
                self.completions = _FakeChatCompletions(chat_content)

        self.chat = _Chat(chat_content)


def test_generate_prompt_responses_mode_normalizes_and_sets_metadata(
    monkeypatch,
) -> None:
    client = OpenAIClient(OpenAIClientConfig(api_mode="responses"))

    def fake_get_client() -> _FakeClient:
        return _FakeClient(
            responses_output_text="  hello\nworld  ",
            chat_content="unused",
        )

    monkeypatch.setattr(OpenAIClient, "_get_client", lambda self: fake_get_client())

    result = client.generate_prompt(paragraph_id=1, paragraph_text="hi")
    assert result.prompt == "hello world"
    assert result.model == client.config.model
    assert result.response_id == "resp_1"
    _ = datetime.fromisoformat(result.timestamp)


def test_generate_prompt_chat_mode_normalizes_and_sets_metadata(monkeypatch) -> None:
    client = OpenAIClient(OpenAIClientConfig(api_mode="chat"))

    def fake_get_client() -> _FakeClient:
        return _FakeClient(
            responses_output_text="unused",
            chat_content="  hello\nworld  ",
        )

    monkeypatch.setattr(OpenAIClient, "_get_client", lambda self: fake_get_client())

    result = client.generate_prompt(paragraph_id=1, paragraph_text="hi")
    assert result.prompt == "hello world"
    assert result.model == client.config.model
    assert result.response_id == "chat_1"
    _ = datetime.fromisoformat(result.timestamp)


def test_generate_prompt_raises_on_empty_output(monkeypatch) -> None:
    client = OpenAIClient(OpenAIClientConfig(api_mode="chat"))

    def fake_get_client() -> _FakeClient:
        return _FakeClient(
            responses_output_text="unused",
            chat_content="   ",
        )

    monkeypatch.setattr(OpenAIClient, "_get_client", lambda self: fake_get_client())

    try:
        _ = client.generate_prompt(paragraph_id=1, paragraph_text="hi")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Empty model output" in str(e)
