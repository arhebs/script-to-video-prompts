from __future__ import annotations

from dataclasses import dataclass

from src.normalize import normalize_prompt


@dataclass(frozen=True, slots=True)
class OpenAIClientConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_output_tokens: int = 300
    store: bool = False


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


@dataclass(frozen=True, slots=True)
class OpenAIClient:
    config: OpenAIClientConfig

    def generate_prompt(self, *, paragraph_id: int, paragraph_text: str) -> str:
        _ = build_input(paragraph_id=paragraph_id, paragraph_text=paragraph_text)
        raise NotImplementedError("OpenAI integration not implemented yet")

    def normalize(self, text: str) -> str:
        return normalize_prompt(text)
