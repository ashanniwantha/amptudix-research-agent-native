from src.agents.researcher import ResearcherAgent
from src.agents.summarizer import SummarizerAgent


class Brain:
    """Backward-compatible adapter over the newer multi-agent architecture."""

    def __init__(self) -> None:
        self.scribe = SummarizerAgent()
        self.scout = ResearcherAgent(scribe=self.scribe)

    def researcher(self, user_prompt: str, max_iterations: int = 5) -> str:
        return self.scout.execute_task(user_prompt, max_iterations=max_iterations)
