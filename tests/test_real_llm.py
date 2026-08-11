from __future__ import annotations

from types import SimpleNamespace

import pytest

from app import agent as agent_module
from app.mock_llm import FakeLLM, FakeResponse
from app.real_llm import RealLLM


class FakeCompletions:
    def __init__(self, response) -> None:
        self.response = response
        self.requests: list[dict] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.response


class FakeOpenAIClient:
    def __init__(self, response) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(response))


def test_real_llm_returns_compatible_response_with_api_usage() -> None:
    api_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Refund approved"))],
        usage=SimpleNamespace(prompt_tokens=123, completion_tokens=45),
    )
    client = FakeOpenAIClient(api_response)
    llm = RealLLM(client=client, model="gpt-4o-mini")

    result = llm.generate("How do refunds work?")

    assert isinstance(result, FakeResponse)
    assert result.text == "Refund approved"
    assert result.usage.input_tokens == 123
    assert result.usage.output_tokens == 45
    assert result.model == "gpt-4o-mini"
    assert client.chat.completions.requests == [
        {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "How do refunds work?"}],
        }
    ]


def test_real_llm_propagates_openai_errors() -> None:
    class FailingCompletions:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("OpenAI unavailable")

    client = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    llm = RealLLM(client=client, model="gpt-4o-mini")

    with pytest.raises(RuntimeError, match="OpenAI unavailable"):
        llm.generate("hello")


def test_lab_agent_uses_real_llm_when_api_key_exists(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    agent = agent_module.LabAgent()

    assert isinstance(agent.llm, RealLLM)
    assert agent.model == "gpt-4o-mini"
    assert agent.provider == "openai"


def test_lab_agent_uses_fake_llm_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    agent = agent_module.LabAgent()

    assert isinstance(agent.llm, FakeLLM)
    assert agent.model == "claude-sonnet-4-5"
    assert agent.provider == "fake"


def test_agent_estimates_cost_using_selected_model(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    agent = agent_module.LabAgent(model="gpt-4o-mini")

    assert agent._estimate_cost(tokens_in=1_000, tokens_out=2_000) == 0.00135
