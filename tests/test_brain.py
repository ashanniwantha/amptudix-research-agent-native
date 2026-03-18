import pytest
from unittest.mock import MagicMock, patch
from src.core.llm import Brain


@pytest.mark.needs_llm
def test_real_llm_connection():
    """This test only runs locally where Ollama is active."""
    agent = Brain()
    # ... logic for real test ...


def test_researcher_logic_mocked():
    """
    This test runs in GitHub Actions.
    It 'fakes' the LLM to test if the loop works.
    """
    with patch("openai.resources.chat.completions.Completions.create") as mock_create:
        # 1. Setup a fake response from the LLM
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Research complete!", tool_calls=None))
        ]
        mock_create.return_value = mock_response

        agent = Brain()
        result = agent.researcher("Test Topic", max_iterations=1)

        # 2. Assertions: Did our code handle the fake response correctly?
        assert result == "Research complete!"
        assert mock_create.called
