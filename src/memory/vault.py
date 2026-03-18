import os
import re
import time
import uuid
from typing import cast
import chromadb
from chromadb.api.types import Embeddable, EmbeddingFunction, Metadata
from chromadb.utils import embedding_functions
from rich.console import Console


STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "is",
    "are",
    "be",
    "as",
    "with",
    "that",
    "this",
    "it",
    "by",
    "from",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {token for token in tokens if len(token) > 2 and token not in STOPWORDS}


class MemoryVault:
    def __init__(
        self, db_path="data/vault_db", collection_name="agent_research"
    ) -> None:
        # Use persists storage so memory survives a restart
        self.console = Console()
        self.client = chromadb.PersistentClient(path=db_path)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").replace(
            "/v1", ""
        )
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

        try:
            ollama_embed_fn = embedding_functions.OllamaEmbeddingFunction(
                url=f"{base_url}/api/embeddings",
                model_name=embedding_model,
            )
            embedding_fn = cast(EmbeddingFunction[Embeddable], ollama_embed_fn)
        except Exception:
            default_embed_fn = embedding_functions.DefaultEmbeddingFunction()
            embedding_fn = cast(EmbeddingFunction[Embeddable], default_embed_fn)

        self.embed_fn = embedding_fn

        # Initialize the collection with Nomic's "Math"
        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=embedding_fn
        )

    def _normalize_chunk(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split long reports into smaller searchable pieces."""
        # A simple professional approach: split by paragraph or fixed length
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def store_research(self, topic: str, content: str) -> None:
        """Chunks and stores a final report into the Vector DB."""
        normalized = self._normalize_chunk(content)
        if not normalized:
            return

        chunks = [
            self._normalize_chunk(chunk)
            for chunk in self._chunk_text(normalized)
            if self._normalize_chunk(chunk)
        ]
        if not chunks:
            return

        now_ts = int(time.time())

        ids: list[str] = [str(uuid.uuid4()) for _ in chunks]
        metadatas: list[Metadata] = [
            {
                "topic": topic,
                "chunk_index": i,
                "stored_at": now_ts,
                "char_count": len(chunks[i]),
            }
            for i in range(len(chunks))
        ]

        try:
            self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        except Exception:
            # If ids conflict or add fails unexpectedly, upsert avoids losing memory writes.
            self.collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)

    def _semantic_candidates(
        self, query: str, n_results: int
    ) -> list[tuple[str, float]]:
        expanded = max(n_results * 3, 6)
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=expanded,
                include=["documents", "distances"],
            )
        except Exception:
            return []

        docs = (results.get("documents") or [[]])[0] or []
        distances = (results.get("distances") or [[]])[0] or []

        out: list[tuple[str, float]] = []
        for i, doc in enumerate(docs):
            if not doc:
                continue
            distance = (
                distances[i] if i < len(distances) and distances[i] is not None else 1.0
            )
            semantic_score = 1.0 / (1.0 + float(distance))
            out.append((doc, semantic_score))
        return out

    def _lexical_candidates(
        self, query: str, limit: int = 120
    ) -> list[tuple[str, float]]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        try:
            rows = self.collection.get(limit=limit, include=["documents"])
        except Exception:
            return []

        docs = rows.get("documents") or []
        if not docs:
            return []

        out: list[tuple[str, float]] = []
        for doc in docs:
            if not doc:
                continue
            tokens = _tokenize(doc)
            if not tokens:
                continue
            overlap = query_tokens.intersection(tokens)
            if not overlap:
                continue
            lexical_score = len(overlap) / max(len(query_tokens), 1)
            out.append((doc, lexical_score))
        return out

    def _hybrid_rank(self, query: str, n_results: int) -> list[str]:
        semantic = self._semantic_candidates(query=query, n_results=n_results)
        lexical = self._lexical_candidates(query=query)

        score_by_doc: dict[str, float] = {}

        # Blend semantic meaning match + lexical overlap.
        for doc, score in semantic:
            score_by_doc[doc] = max(score_by_doc.get(doc, 0.0), score * 0.7)
        for doc, score in lexical:
            score_by_doc[doc] = max(
                score_by_doc.get(doc, 0.0), score_by_doc.get(doc, 0.0) + score * 0.3
            )

        ranked = sorted(score_by_doc.items(), key=lambda item: item[1], reverse=True)
        return [doc for doc, _ in ranked[:n_results]]

    def retrieve_relevant_context(self, query: str, n_results: int = 3) -> str:
        """Finds the most relevant past research to feed back into the LLM."""
        cleaned_query = self._normalize_chunk(query)
        if not cleaned_query:
            return ""

        try:
            ranked_docs = self._hybrid_rank(query=cleaned_query, n_results=n_results)
        except Exception:
            ranked_docs = []

        if not ranked_docs:
            return ""

        # Flatten the list of documents into a single context string
        return "\n---\n".join(ranked_docs)
