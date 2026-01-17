from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from openai import OpenAI

from src.normalize import normalize_prompt


@dataclass(frozen=True, slots=True)
class OpenAIClientConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_output_tokens: int = 300
    store: bool = False

    base_url: str | None = None
    api_mode: str = "responses"

    timeout_seconds: float = 60.0
    max_retries: int = 5


@dataclass(frozen=True, slots=True)
class PromptResult:
    prompt: str
    model: str
    response_id: str
    timestamp: str


DEFAULT_INSTRUCTIONS = (
    "You are a film director, anthropologist, and visual historian creating "
    "cinematic video prompts for Google Veo 3 (fast mode). "
    "The narrative text to process is enclosed in <narrative_text> tags. "
    "Generate exactly 1 prompt in English from the provided paragraph. "
    "Start immediately with the prompt; do not output conversational filler like 'Here is the prompt:'. "
    "Return exactly one prompt as a single block of text (no bullets, no line breaks). "
    "Do not include captions, on-screen text, watermarks, or logos."
)


def build_input(*, paragraph_id: int, paragraph_text: str) -> str:
    paragraph_text = paragraph_text.strip()
    return (
        f"Paragraph ID: {paragraph_id}\n"
        "Content:\n"
        "<narrative_text>\n"
        f"{paragraph_text}\n"
        "</narrative_text>"
    )


@dataclass(slots=True)
class OpenAIClient:
    config: OpenAIClientConfig
    _client: OpenAI | None = field(default=None, repr=False)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                timeout=self.config.timeout_seconds,
                max_retries=self.config.max_retries,
                base_url=self.config.base_url,
            )
        return self._client

    def generate_prompt(
        self, *, paragraph_id: int, paragraph_text: str
    ) -> PromptResult:
        model = self.config.model
        instructions = DEFAULT_INSTRUCTIONS
        input_text = build_input(
            paragraph_id=paragraph_id, paragraph_text=paragraph_text
        )
        temperature = self.config.temperature
        max_output_tokens = self.config.max_output_tokens
        timestamp = datetime.now(timezone.utc).isoformat()

        if self.config.api_mode == "chat":
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_output_tokens,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": input_text},
                ],
            )
            content = response.choices[0].message.content or ""
            response_id = response.id
            return PromptResult(
                prompt=self._normalize(content),
                model=model,
                response_id=response_id,
                timestamp=timestamp,
            )

        client = self._get_client()
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=input_text,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            store=self.config.store,
            stream=False,
        )

        output_text = getattr(response, "output_text", "")
        response_id = getattr(response, "id", "")
        return PromptResult(
            prompt=self._normalize(output_text),
            model=model,
            response_id=response_id,
            timestamp=timestamp,
        )

    def _normalize(self, text: str) -> str:
        if not text.strip():
            raise ValueError("Empty model output")
        return normalize_prompt(text)
