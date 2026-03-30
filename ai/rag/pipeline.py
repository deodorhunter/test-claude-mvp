"""
RAG (Retrieval-Augmented Generation) pipeline.

Orchestrates embedding generation, vector storage, and semantic search retrieval.
Ensures complete tenant isolation: documents from tenant A never appear in tenant B's search results.
"""

import logging
from dataclasses import dataclass

from ai.rag.embeddings import EmbeddingService
from ai.rag.store import QdrantStore

logger = logging.getLogger(__name__)


@dataclass
class RAGChunk:
    """A retrieved document chunk with relevance score."""

    text: str
    source: str
    score: float


class RAGPipeline:
    """
    RAG pipeline orchestrating embeddings and retrieval.

    Responsible for:
    1. Generating embeddings from text via EmbeddingService
    2. Storing vectors in Qdrant via QdrantStore
    3. Retrieving relevant chunks based on semantic similarity
    """

    def __init__(
        self,
        store: QdrantStore,
        embeddings: EmbeddingService,
    ):
        """
        Initialize the RAG pipeline.

        Args:
            store: QdrantStore instance for vector operations
            embeddings: EmbeddingService instance for generating vectors
        """
        self._store = store
        self._embeddings = embeddings

    async def index_document(
        self,
        tenant_id: str,
        doc_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Index a document for retrieval.

        The document is embedded, stored in the tenant's Qdrant collection,
        and associated with metadata.

        Args:
            tenant_id: The tenant's unique identifier
            doc_id: Unique document identifier within the tenant
            text: Document text to embed and index
            metadata: Optional metadata dict (e.g., url, title, author)

        Raises:
            ValueError: If text is empty
            Exception: If embedding or storage fails
        """
        if not text or not text.strip():
            raise ValueError("Document text cannot be empty")

        logger.info(f"Indexing document {doc_id} for tenant {tenant_id}")

        # Generate embedding
        vector = await self._embeddings.embed(text)

        # Prepare metadata payload
        payload = {
            "text": text,
            "source": doc_id,
            **(metadata or {}),
        }

        # Store in Qdrant (tenant-scoped)
        self._store.index_document(
            tenant_id=tenant_id,
            doc_id=doc_id,
            vector=vector,
            metadata=payload,
        )

    async def query(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[RAGChunk]:
        """
        Query the RAG index for relevant documents.

        The query is embedded and used to search the tenant's Qdrant collection
        for semantically similar documents.

        Args:
            tenant_id: The tenant's unique identifier
            query: Query text
            top_k: Maximum number of results to return

        Returns:
            List of RAGChunk objects with text, source, and relevance score

        Raises:
            ValueError: If query is empty
            Exception: If embedding or search fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        logger.info(f"Querying RAG for tenant {tenant_id}: {query[:50]}...")

        # Generate query embedding
        query_vector = await self._embeddings.embed(query)

        # Search in tenant's collection
        hits = self._store.search(tenant_id, query_vector, top_k)

        # Convert to RAGChunk objects
        chunks = [
            RAGChunk(
                text=h["payload"].get("text", ""),
                source=h["payload"].get("source", "unknown"),
                score=h["score"],
            )
            for h in hits
        ]

        logger.info(
            f"RAG query for tenant {tenant_id} returned {len(chunks)} chunks"
        )
        return chunks
