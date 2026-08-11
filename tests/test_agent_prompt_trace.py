from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module
from app.mock_llm import FakeResponse, FakeUsage


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.trace_updates: list[dict] = []
        self.generation_updates: list[dict] = []
        self.observations: list[tuple[str, dict]] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_trace(self, **kwargs) -> None:
        self.trace_updates.append(kwargs)

    def update_current_generation(self, **kwargs) -> None:
        self.generation_updates.append(kwargs)

    def update_current_span(self, **kwargs) -> None:
        return None

    def get_current_trace_id(self) -> str:
        return "trace-123"

    @contextmanager
    def start_as_current_span(self, **kwargs):
        self.observations.append(("span", kwargs))
        yield

    @contextmanager
    def start_as_current_generation(self, **kwargs):
        self.observations.append(("generation", kwargs))
        yield


def test_agent_links_prompt_version_to_trace_and_generation(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)

    agent = agent_module.LabAgent()
    agent.llm.generate = lambda _: FakeResponse(
        text="Send the refund to student@vinuni.edu.vn",
        usage=FakeUsage(input_tokens=100, output_tokens=20),
        model=agent.model,
    )
    result = agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
        correlation_id="req-a1b2c3d4",
    )

    trace_metadata = client.trace_updates[-1]["metadata"]
    generation_update = client.generation_updates[-1]
    assert trace_metadata == {
        "correlation_id": "req-a1b2c3d4",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
    }
    assert generation_update["prompt"] is client.prompt
    assert generation_update["metadata"]["correlation_id"] == "req-a1b2c3d4"
    assert generation_update["metadata"]["prompt_version"] == "3"
    assert generation_update["metadata"]["answer_preview"] == (
        "Send the refund to [REDACTED_EMAIL]"
    )
    assert result.trace_id == "trace-123"
    assert client.observations == [
        ("span", {"name": "rag-retrieval"}),
        (
            "generation",
            {"name": "fake-llm", "model": "claude-sonnet-4-5"},
        ),
    ]
