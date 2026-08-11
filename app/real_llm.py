from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from .mock_llm import FakeResponse, FakeUsage

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class RealLLM:
    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(self, prompt: str) -> FakeResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return FakeResponse(
            text=response.choices[0].message.content or "",
            usage=FakeUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            ),
            model=self.model,
        )
