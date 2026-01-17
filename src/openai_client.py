from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from openai import OpenAI

from src.normalize import normalize_prompt


@dataclass(frozen=True, slots=True)
class OpenAIClientConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_output_tokens: int = 300
    store: bool = False

    timeout_seconds: float = 60.0
    max_retries: int = 5


DEFAULT_INSTRUCTIONS = (
    "You are a film director, anthropologist, and visual historian creating cinematic video prompts "
    "for Google Veo 3 (fast mode). "
    "Generate exactly 1 prompt in English from the provided paragraph. "
    "Return exactly one prompt as a single block of text (no bullets, no line breaks). "
    "Do not include captions, on-screen text, watermarks, or logos."
)


def build_input(*, paragraph_id: int, paragraph_text: str) -> str:
    paragraph_text = paragraph_text.strip()
    return f"Paragraph {paragraph_id}: {paragraph_text}"


class _ResponseWithText(Protocol):
    @property
    def output_text(self) -> str: ...


class _ResponsesCreateFn(Protocol):
    def __call__(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        temperature: float,
        max_output_tokens: int,
        store: bool,
        stream: bool,
    ) -> _ResponseWithText: ...


@dataclass(frozen=True, slots=True)
class OpenAIClient:
    config: OpenAIClientConfig
    _responses_create: _ResponsesCreateFn | None = None

    def generate_prompt(self, *, paragraph_id: int, paragraph_text: str) -> str:
        payload = {
            "model": self.config.model,
            "instructions": DEFAULT_INSTRUCTIONS,
            "input": build_input(
                paragraph_id=paragraph_id, paragraph_text=paragraph_text
            ),
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_output_tokens,
            "store": self.config.store,
            "stream": False,
        }

        if self._responses_create is not None:
            response = self._responses_create(**payload)
        else:
            client = OpenAI(
                timeout=self.config.timeout_seconds, max_retries=self.config.max_retries
            )
            response = cast(_ResponseWithText, client.responses.create(**payload))

        output_text = response.output_text
        if not output_text.strip():
            raise ValueError(f"Empty model output for paragraph id {paragraph_id}")

        return self.normalize(output_text)

    def normalize(self, text: str) -> str:
        return normalize_prompt(text)
