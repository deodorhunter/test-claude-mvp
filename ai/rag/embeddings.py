"""
Embedding service — generates vector embeddings via Ollama.

Uses the nomic-embed-text model for semantic search embeddings.
"""

import httpx
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates embeddings via Ollama nomic-embed-text model."""

    def __init__(self, ollama_url: str, model: str = "nomic-embed-text"):
        """
        Initialize the embedding service.

        Args:
            ollama_url: Base URL of the Ollama service (e.g., http://ollama:11434)
            model: Model name to use for embeddings (default: nomic-embed-text)
        """
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    async def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            httpx.HTTPError: If the Ollama service fails
            ValueError: If the response is malformed
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()
                if "embedding" not in data:
                    raise ValueError("Response missing 'embedding' field")
                return data["embedding"]
            except httpx.HTTPError as e:
                logger.error(f"Ollama embedding failed: {e}")
                raise
