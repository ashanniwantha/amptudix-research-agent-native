from unittest.mock import MagicMock

from src.agents.supervisor import SamuraiSupervisor


class _FakeVault:
    def retrieve_relevant_context(self, query: str) -> str:
        return "cached context"

    def store_research(self, topic: str, content: str) -> None:
        return None


def test_supervisor_skips_research_when_not_needed(monkeypatch):
    monkeypatch.setattr("src.agents.supervisor.MemoryVault", lambda: _FakeVault())

    supervisor = SamuraiSupervisor()
    supervisor.scout = MagicMock()
    supervisor._should_research = MagicMock(return_value=False)
    supervisor.generate_direct_response = MagicMock(return_value="direct answer")

    out = supervisor.run("Explain OOP basics")

    assert out == "direct answer"
    supervisor.scout.execute_task_bundle.assert_not_called()


def test_supervisor_strips_invalid_citations_and_keeps_verified_bibliography(
    monkeypatch,
):
    monkeypatch.setattr("src.agents.supervisor.MemoryVault", lambda: _FakeVault())

    supervisor = SamuraiSupervisor()
    supervisor._should_research = MagicMock(return_value=True)

    supervisor.scout.execute_task_bundle = MagicMock(
        return_value=(
            "Raw research text",
            [
                {
                    "index": 1,
                    "title": "Official docs",
                    "url": "https://docs.example.com",
                    "domain": "docs.example.com",
                    "category": "official",
                },
                {
                    "index": 2,
                    "title": "",
                    "url": "https://invalid.example.com",
                    "domain": "invalid.example.com",
                    "category": "other",
                },
            ],
        )
    )

    # LLM draft includes one valid citation and one invalid citation.
    supervisor.generate_reply = MagicMock(
        return_value=(
            "Claim from source [1]. Unsupported claim [99].\n\n"
            "--- 📜 ARCHIVAL SOURCES ---\n[99] Invalid - https://invalid.example.com"
        )
    )

    out = supervisor.run("Give me latest architecture guidance")

    assert "[99]" not in out
    assert "--- 📜 ARCHIVAL SOURCES ---" in out
    assert "[1] Official docs - https://docs.example.com" in out


def test_supervisor_routes_memory_through_summarizer_on_retrieve_and_store(monkeypatch):
    fake_vault = _FakeVault()
    fake_vault.retrieve_relevant_context = MagicMock(return_value="raw archive context")
    fake_vault.store_research = MagicMock()
    monkeypatch.setattr("src.agents.supervisor.MemoryVault", lambda: fake_vault)

    supervisor = SamuraiSupervisor()
    supervisor._should_research = MagicMock(return_value=False)
    supervisor.generate_direct_response = MagicMock(return_value="final direct answer")

    def _summarize_side_effect(topic: str, content: str) -> str:
        if topic.startswith("Relevant archived context"):
            return "condensed retrieval context"
        if topic.startswith("Memory summary"):
            return "condensed storage memory"
        return "condensed"

    supervisor.scribe.summarize = MagicMock(side_effect=_summarize_side_effect)

    out = supervisor.run("Explain Python classes")

    assert out == "final direct answer"
    assert supervisor.scribe.summarize.call_count >= 2
    fake_vault.store_research.assert_called_once_with(
        topic="Explain Python classes", content="condensed storage memory"
    )


def test_supervisor_applies_memory_budget(monkeypatch):
    monkeypatch.setattr("src.agents.supervisor.MemoryVault", lambda: _FakeVault())

    supervisor = SamuraiSupervisor()
    supervisor.retrieval_summary_char_budget = 40
    supervisor.storage_summary_char_budget = 50

    supervisor.scribe.summarize = MagicMock(return_value=("x" * 200))

    retrieval = supervisor._summarize_for_memory_retrieval(
        user_input="topic",
        content="raw retrieval content",
    )
    storage = supervisor._summarize_for_memory_storage(
        user_input="topic",
        content="raw storage content",
    )

    assert len(retrieval) <= 44
    assert len(storage) <= 54


def test_supervisor_reads_budget_values_from_env(monkeypatch):
    monkeypatch.setattr("src.agents.supervisor.MemoryVault", lambda: _FakeVault())
    monkeypatch.setenv("MEMORY_RETRIEVAL_CHAR_BUDGET", "123")
    monkeypatch.setenv("MEMORY_STORAGE_CHAR_BUDGET", "456")
    monkeypatch.setenv("MEMORY_LINE_BUDGET", "9")

    supervisor = SamuraiSupervisor()

    assert supervisor.retrieval_summary_char_budget == 123
    assert supervisor.storage_summary_char_budget == 456
    assert supervisor.memory_line_budget == 9
