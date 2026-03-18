import pytest
import os
import shutil
from src.memory.vault import MemoryVault

# Use a specific test database path so we don't overwrite real data
TEST_DB_PATH = "./test_vault_db"


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_db():
    """Fixture to ensure a clean database for every test run."""
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)


def test_store_and_retrieve():
    """Test that we can save a report and find it via a query."""
    vault = MemoryVault(db_path=TEST_DB_PATH)

    topic = "Modern Architecture"
    content = "The Transformer architecture uses self-attention mechanisms to process sequences."

    # Action
    vault.store_research(topic, content)

    # Retrieval (Search for a related keyword)
    results = vault.retrieve_relevant_context("What is self-attention?")

    # Assertions
    assert len(results) > 0
    assert "Transformer" in results
    assert "self-attention" in results


def test_chunking_logic():
    """Ensure long text is correctly broken into smaller pieces."""
    vault = MemoryVault(db_path=TEST_DB_PATH)
    long_text = "A" * 2500  # Should create 3 chunks if size is 1000

    chunks = vault._chunk_text(long_text, chunk_size=1000)

    assert len(chunks) == 3
    assert len(chunks[0]) == 1000


def test_hybrid_retrieval_blends_semantic_and_lexical(monkeypatch):
    vault = MemoryVault(db_path=TEST_DB_PATH)

    monkeypatch.setattr(
        vault,
        "_semantic_candidates",
        lambda query, n_results: [
            ("Semantic-only hit", 0.9),
            ("Blended hit", 0.4),
        ],
    )
    monkeypatch.setattr(
        vault,
        "_lexical_candidates",
        lambda query: [
            ("Blended hit", 1.0),
            ("Lexical-only hit", 0.8),
        ],
    )

    out = vault.retrieve_relevant_context("fresh architecture trends", n_results=2)
    assert "Blended hit" in out
    assert "Semantic-only hit" in out or "Lexical-only hit" in out


def test_retrieve_relevant_context_empty_query_returns_empty():
    vault = MemoryVault(db_path=TEST_DB_PATH)
    out = vault.retrieve_relevant_context("   ", n_results=3)
    assert out == ""
