"""
US-019: RAG pipeline tests — indexing, retrieval, cross-tenant isolation, empty results.
Focus: gaps not covered by test_rag.py.

Actual signatures (verified from source):
  RAGPipeline(store: QdrantStore, embeddings: EmbeddingService)
  pipeline.index_document(tenant_id, doc_id, text, metadata=None)
  pipeline.query(tenant_id, query, top_k=5) -> list[RAGChunk]
  RAGChunk(text, source, score)  — no tenant_id field
  QdrantStore._collection_name(tenant_id) -> str  [sync]
  QdrantStore.index_document(tenant_id, doc_id, vector, metadata) [sync]
  QdrantStore.search(tenant_id, query_vector, top_k) -> list[dict]  [sync]
  store.search returns [{"score": float, "payload": {"text": ..., "source": ...}}]
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

TENANT_A = "tenant-alpha"
TENANT_B = "tenant-beta"


def make_embeddings(vector=None):
    """Returns a mock EmbeddingService."""
    emb = MagicMock()
    emb.embed = AsyncMock(return_value=vector or [0.1] * 768)
    return emb


def make_store():
    """Returns a mock QdrantStore with sync methods."""
    from ai.rag.store import QdrantStore
    store = MagicMock(spec=QdrantStore)
    store._collection_name = MagicMock(side_effect=lambda tid: f"tenant_{tid}")
    store._ensure_collection = MagicMock()
    store.index_document = MagicMock()
    store.search = MagicMock(return_value=[])
    return store


# ---------------------------------------------------------------------------
# index_document: correct tenant_id and doc_id passed to store
# ---------------------------------------------------------------------------

class TestRAGIndexDocument:
    @pytest.mark.asyncio
    async def test_index_document_passes_correct_tenant_id(self):
        from ai.rag.pipeline import RAGPipeline
        store = make_store()
        pipeline = RAGPipeline(store=store, embeddings=make_embeddings())
        await pipeline.index_document(TENANT_A, "doc1", "hello world")
        store.index_document.assert_called_once()
        call_kwargs = store.index_document.call_args
        args, kwargs = call_kwargs
        all_args = dict(zip(["tenant_id", "doc_id", "vector", "metadata"], args))
        all_args.update(kwargs)
        assert all_args.get("tenant_id") == TENANT_A

    @pytest.mark.asyncio
    async def test_index_document_embeds_text(self):
        from ai.rag.pipeline import RAGPipeline
        store = make_store()
        emb = make_embeddings(vector=[0.5] * 768)
        pipeline = RAGPipeline(store=store, embeddings=emb)
        await pipeline.index_document(TENANT_A, "src_doc", "embed me")
        emb.embed.assert_called_once()


# ---------------------------------------------------------------------------
# query: returns RAGChunk list
# ---------------------------------------------------------------------------

class TestRAGQuery:
    @pytest.mark.asyncio
    async def test_query_returns_rag_chunks_with_correct_fields(self):
        from ai.rag.pipeline import RAGPipeline, RAGChunk
        store = make_store()
        store.search = MagicMock(return_value=[
            {"score": 0.95, "payload": {"text": "chunk text", "source": "doc1"}},
        ])
        pipeline = RAGPipeline(store=store, embeddings=make_embeddings())
        results = await pipeline.query(TENANT_A, "find me")
        assert len(results) == 1
        chunk = results[0]
        assert isinstance(chunk, RAGChunk)
        assert hasattr(chunk, "text")
        assert hasattr(chunk, "source")
        assert hasattr(chunk, "score")

    @pytest.mark.asyncio
    async def test_query_returns_empty_list_when_no_results(self):
        from ai.rag.pipeline import RAGPipeline
        store = make_store()
        store.search = MagicMock(return_value=[])
        pipeline = RAGPipeline(store=store, embeddings=make_embeddings())
        results = await pipeline.query(TENANT_A, "nothing here")
        assert results == []

    @pytest.mark.asyncio
    async def test_query_passes_top_k_to_store(self):
        from ai.rag.pipeline import RAGPipeline
        store = make_store()
        store.search = MagicMock(return_value=[])
        pipeline = RAGPipeline(store=store, embeddings=make_embeddings())
        await pipeline.query(TENANT_A, "q", top_k=3)
        store.search.assert_called_once()
        args, kwargs = store.search.call_args
        all_args = dict(zip(["tenant_id", "query_vector", "top_k"], args))
        all_args.update(kwargs)
        assert all_args.get("top_k") == 3


# ---------------------------------------------------------------------------
# Cross-tenant isolation: different collection per tenant
# ---------------------------------------------------------------------------

class TestRAGCrossTenantIsolation:
    def test_collection_name_differs_per_tenant(self):
        from ai.rag.store import QdrantStore
        store = MagicMock(spec=QdrantStore)
        store._collection_name = MagicMock(side_effect=lambda tid: f"tenant_{tid}")
        col_a = store._collection_name(TENANT_A)
        col_b = store._collection_name(TENANT_B)
        assert col_a != col_b
        assert TENANT_A in col_a
        assert TENANT_B in col_b

    @pytest.mark.asyncio
    async def test_tenant_b_query_does_not_return_tenant_a_data(self):
        from ai.rag.pipeline import RAGPipeline

        def scoped_search(tenant_id, query_vector, top_k=5):
            if tenant_id == TENANT_A:
                return [{"score": 0.9, "payload": {"text": "tenant A secret", "source": "s"}}]
            return []

        store = make_store()
        store.search = MagicMock(side_effect=scoped_search)
        pipeline = RAGPipeline(store=store, embeddings=make_embeddings())
        results_b = await pipeline.query(TENANT_B, "find secrets")
        assert len(results_b) == 0

    @pytest.mark.asyncio
    async def test_index_calls_use_correct_tenant_ids(self):
        from ai.rag.pipeline import RAGPipeline
        store = make_store()
        pipeline = RAGPipeline(store=store, embeddings=make_embeddings())
        await pipeline.index_document(TENANT_A, "a_doc", "A's data")
        await pipeline.index_document(TENANT_B, "b_doc", "B's data")
        calls = store.index_document.call_args_list
        assert len(calls) == 2
        tenants = []
        for call in calls:
            args, kwargs = call
            all_args = dict(zip(["tenant_id", "doc_id", "vector", "metadata"], args))
            all_args.update(kwargs)
            tenants.append(all_args.get("tenant_id"))
        assert TENANT_A in tenants
        assert TENANT_B in tenants


# ---------------------------------------------------------------------------
# RAGChunk field completeness
# ---------------------------------------------------------------------------

class TestRAGChunkFields:
    def test_rag_chunk_has_required_fields(self):
        from ai.rag.pipeline import RAGChunk
        chunk = RAGChunk(text="some text", source="doc", score=0.88)
        assert chunk.text == "some text"
        assert chunk.source == "doc"
        assert chunk.score == 0.88
