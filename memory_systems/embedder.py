"""Shared embedding + vector search using OpenAI text-embedding-3-small.

Both memory systems use this — keeps the comparison fair.
"""

import numpy as np
from openai import OpenAI


class Embedder:
    """Thin wrapper around OpenAI embeddings with cosine similarity search."""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in one API call."""
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [d.embedding for d in response.data]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    def search(self, query: str, documents: dict[str, list[float]], top_k: int = 5) -> list[tuple[str, float]]:
        """Search documents by cosine similarity to query.

        Args:
            query: Search query text.
            documents: Dict of {id: embedding_vector}.
            top_k: Number of results.

        Returns:
            List of (id, score) tuples, sorted by descending similarity.
        """
        if not documents:
            return []

        query_vec = self.embed(query)
        scores = []
        for doc_id, doc_vec in documents.items():
            score = self.cosine_similarity(query_vec, doc_vec)
            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
