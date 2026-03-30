"""
RAG (Retrieval-Augmented Generation) pipeline package.

Exports:
- QdrantStore: Vector database wrapper with tenant isolation
- EmbeddingService: Embedding generation via Ollama
- RAGPipeline: Orchestrator for embedding + retrieval
- RAGChunk: Retrieved document chunk with score
"""

from ai.rag.store import QdrantStore
from ai.rag.embeddings import EmbeddingService
from ai.rag.pipeline import RAGPipeline, RAGChunk

__all__ = [
    "QdrantStore",
    "EmbeddingService",
    "RAGPipeline",
    "RAGChunk",
]
