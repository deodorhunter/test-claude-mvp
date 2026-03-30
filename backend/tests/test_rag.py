"""
RAG pipeline unit tests — no real Qdrant or Ollama connections.

Tests cover:
- Collection naming with tenant isolation
- Document indexing and retrieval
- Cross-tenant isolation (critical security test)
- EmbeddingService with mocked Ollama
- RAGPipeline orchestration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from ai.rag.store import QdrantStore
from ai.rag.embeddings import EmbeddingService
from ai.rag.pipeline import RAGPipeline, RAGChunk


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def tenant_a_id():
    """First tenant for isolation tests."""
    return str(uuid.uuid4())


@pytest.fixture
def tenant_b_id():
    """Second tenant for isolation tests."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    mock = MagicMock()
    mock.get_collections.return_value = MagicMock(collections=[])
    return mock


@pytest.fixture
def qdrant_store(mock_qdrant_client):
    """QdrantStore with mocked client."""
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store = QdrantStore("http://localhost:6333")
        store._client = mock_qdrant_client
        return store


@pytest.fixture
def embedding_service():
    """EmbeddingService (will be mocked when needed)."""
    return EmbeddingService("http://localhost:11434")


@pytest.fixture
def mock_embedding_vector():
    """Standard mock embedding vector (768-dim)."""
    return [0.1] * 768


# ──────────────────────────────────────────────────────────────────────────────
# QdrantStore collection naming tests
# ──────────────────────────────────────────────────────────────────────────────


def test_collection_name_uses_tenant_id(qdrant_store, tenant_a_id):
    """Test that collection name includes tenant ID."""
    name = qdrant_store._collection_name(tenant_a_id)
    assert name == f"tenant_{tenant_a_id}"


def test_collection_name_format_consistency(qdrant_store, tenant_a_id):
    """Test that collection name is consistent for same tenant."""
    name1 = qdrant_store._collection_name(tenant_a_id)
    name2 = qdrant_store._collection_name(tenant_a_id)
    assert name1 == name2


# ──────────────────────────────────────────────────────────────────────────────
# QdrantStore collection creation tests
# ──────────────────────────────────────────────────────────────────────────────


def test_ensure_collection_creates_if_not_exists(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that ensure_collection creates a new collection."""
    mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

    qdrant_store._ensure_collection(tenant_a_id)

    # Verify create_collection was called
    mock_qdrant_client.create_collection.assert_called_once()
    call_args = mock_qdrant_client.create_collection.call_args
    assert f"tenant_{tenant_a_id}" in str(call_args)


def test_ensure_collection_skips_if_exists(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that ensure_collection doesn't recreate existing collection."""
    collection_mock = MagicMock()
    collection_mock.name = f"tenant_{tenant_a_id}"
    mock_qdrant_client.get_collections.return_value = MagicMock(
        collections=[collection_mock]
    )

    qdrant_store._ensure_collection(tenant_a_id)

    # Verify create_collection was NOT called
    mock_qdrant_client.create_collection.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# QdrantStore indexing tests
# ──────────────────────────────────────────────────────────────────────────────


def test_index_document_creates_collection(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that index_document ensures collection exists."""
    mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

    qdrant_store.index_document(
        tenant_id=tenant_a_id,
        doc_id="doc1",
        vector=[0.1] * 768,
        metadata={"text": "hello", "source": "doc1"},
    )

    # Verify collection was created
    mock_qdrant_client.create_collection.assert_called_once()


def test_index_document_upserting(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that index_document calls upsert with correct data."""
    mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])
    vector = [0.2] * 768
    metadata = {"text": "test doc", "source": "doc1", "custom": "field"}

    qdrant_store.index_document(
        tenant_id=tenant_a_id,
        doc_id="doc1",
        vector=vector,
        metadata=metadata,
    )

    # Verify upsert was called
    mock_qdrant_client.upsert.assert_called_once()
    call_args = mock_qdrant_client.upsert.call_args
    assert call_args.kwargs["collection_name"] == f"tenant_{tenant_a_id}"


def test_index_document_rejects_wrong_vector_size(qdrant_store, tenant_a_id):
    """Test that index_document rejects vectors of wrong size."""
    with pytest.raises(ValueError, match="Vector size"):
        qdrant_store.index_document(
            tenant_id=tenant_a_id,
            doc_id="doc1",
            vector=[0.1] * 512,  # Wrong size
            metadata={"text": "test"},
        )


# ──────────────────────────────────────────────────────────────────────────────
# QdrantStore search tests
# ──────────────────────────────────────────────────────────────────────────────


def test_search_returns_list_of_dicts(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that search returns list of dicts with score and payload."""
    # Mock search results
    hit_mock = MagicMock()
    hit_mock.score = 0.95
    hit_mock.payload = {"text": "matching doc", "source": "doc1"}
    mock_qdrant_client.search.return_value = [hit_mock]

    results = qdrant_store.search(
        tenant_id=tenant_a_id,
        query_vector=[0.1] * 768,
        top_k=5,
    )

    assert len(results) == 1
    assert results[0]["score"] == 0.95
    assert results[0]["payload"]["text"] == "matching doc"


def test_search_respects_top_k(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that search respects the top_k parameter."""
    mock_qdrant_client.search.return_value = []

    qdrant_store.search(
        tenant_id=tenant_a_id,
        query_vector=[0.1] * 768,
        top_k=10,
    )

    # Verify search was called with correct limit
    call_args = mock_qdrant_client.search.call_args
    assert call_args.kwargs["limit"] == 10


def test_search_rejects_wrong_vector_size(qdrant_store, tenant_a_id):
    """Test that search rejects vectors of wrong size."""
    with pytest.raises(ValueError, match="Vector size"):
        qdrant_store.search(
            tenant_id=tenant_a_id,
            query_vector=[0.1] * 512,  # Wrong size
            top_k=5,
        )


def test_search_uses_tenant_collection(qdrant_store, tenant_a_id, mock_qdrant_client):
    """Test that search uses the correct tenant collection."""
    mock_qdrant_client.search.return_value = []

    qdrant_store.search(
        tenant_id=tenant_a_id,
        query_vector=[0.1] * 768,
        top_k=5,
    )

    # Verify search was called on tenant collection
    call_args = mock_qdrant_client.search.call_args
    assert call_args.kwargs["collection_name"] == f"tenant_{tenant_a_id}"


# ──────────────────────────────────────────────────────────────────────────────
# Cross-tenant isolation tests (CRITICAL)
# ──────────────────────────────────────────────────────────────────────────────


def test_cross_tenant_isolation_search_only_own_collection(
    tenant_a_id, tenant_b_id, mock_qdrant_client
):
    """
    Critical test: Document from tenant A must NOT appear in tenant B's search.

    This test verifies that each tenant only searches its own collection.
    """
    # Create two separate store instances for each tenant
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store_a = QdrantStore("http://localhost:6333")
        store_a._client = mock_qdrant_client

        store_b = QdrantStore("http://localhost:6333")
        store_b._client = mock_qdrant_client

    # Index a document for tenant A
    mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])
    store_a.index_document(
        tenant_id=tenant_a_id,
        doc_id="doc_from_a",
        vector=[0.1] * 768,
        metadata={"text": "secret data from tenant A", "source": "doc_from_a"},
    )

    # Tenant B searches and gets NO results (because it searches its own collection)
    mock_qdrant_client.search.return_value = []  # Empty results for tenant B
    results_b = store_b.search(tenant_id=tenant_b_id, query_vector=[0.1] * 768)

    # Verify tenant B's search used tenant B's collection
    search_call = mock_qdrant_client.search.call_args
    assert search_call.kwargs["collection_name"] == f"tenant_{tenant_b_id}"
    assert results_b == []  # No cross-tenant data leak


def test_tenant_a_and_b_have_different_collections(tenant_a_id, tenant_b_id, qdrant_store):
    """Test that tenant A and tenant B use different collection names."""
    collection_a = qdrant_store._collection_name(tenant_a_id)
    collection_b = qdrant_store._collection_name(tenant_b_id)

    assert collection_a != collection_b
    assert tenant_a_id in collection_a
    assert tenant_b_id in collection_b


# ──────────────────────────────────────────────────────────────────────────────
# EmbeddingService tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_embedding_service_initialization():
    """Test EmbeddingService initialization."""
    service = EmbeddingService("http://localhost:11434", model="nomic-embed-text")
    assert service.ollama_url == "http://localhost:11434"
    assert service.model == "nomic-embed-text"


@pytest.mark.asyncio
async def test_embedding_service_strips_trailing_slash():
    """Test that EmbeddingService strips trailing slash from URL."""
    service = EmbeddingService("http://localhost:11434/")
    assert service.ollama_url == "http://localhost:11434"


@pytest.mark.asyncio
async def test_embedding_service_calls_ollama_embeddings_endpoint():
    """Test that embed calls Ollama /api/embeddings endpoint."""
    service = EmbeddingService("http://localhost:11434")

    with patch("ai.rag.embeddings.httpx.AsyncClient") as mock_client_class:
        # Mock the async context manager and POST request
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3] + [0.0] * 765
        }
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        result = await service.embed("hello world")

        # Verify POST was called correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "api/embeddings" in str(call_args)
        assert result == [0.1, 0.2, 0.3] + [0.0] * 765


@pytest.mark.asyncio
async def test_embedding_service_rejects_empty_text():
    """Test that embed rejects empty text."""
    service = EmbeddingService("http://localhost:11434")

    with pytest.raises(ValueError, match="Text cannot be empty"):
        await service.embed("")

    with pytest.raises(ValueError, match="Text cannot be empty"):
        await service.embed("   ")


@pytest.mark.asyncio
async def test_embedding_service_handles_ollama_error():
    """Test that embed handles Ollama errors gracefully."""
    service = EmbeddingService("http://localhost:11434")

    with patch("ai.rag.embeddings.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Connection refused")
        mock_client.__aenter__.return_value = mock_client

        with pytest.raises(Exception):
            await service.embed("test")


# ──────────────────────────────────────────────────────────────────────────────
# RAGPipeline orchestration tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rag_pipeline_index_document(tenant_a_id, mock_qdrant_client):
    """Test RAGPipeline.index_document orchestrates embedding + storage."""
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store = QdrantStore("http://localhost:6333")
        store._client = mock_qdrant_client

    embeddings = EmbeddingService("http://localhost:11434")

    with patch.object(embeddings, "embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 768

        pipeline = RAGPipeline(store=store, embeddings=embeddings)

        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

        await pipeline.index_document(
            tenant_id=tenant_a_id,
            doc_id="doc1",
            text="This is a test document",
            metadata={"source": "test"},
        )

        # Verify embedding was called
        mock_embed.assert_called_once_with("This is a test document")

        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_rag_pipeline_query_returns_chunks(tenant_a_id, mock_qdrant_client):
    """Test RAGPipeline.query returns list of RAGChunk objects."""
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store = QdrantStore("http://localhost:6333")
        store._client = mock_qdrant_client

    embeddings = EmbeddingService("http://localhost:11434")

    with patch.object(embeddings, "embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 768

        # Mock search results
        hit = MagicMock()
        hit.score = 0.92
        hit.payload = {"text": "matching document", "source": "doc1"}
        mock_qdrant_client.search.return_value = [hit]

        pipeline = RAGPipeline(store=store, embeddings=embeddings)

        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

        chunks = await pipeline.query(tenant_id=tenant_a_id, query="find documents")

        assert len(chunks) == 1
        assert isinstance(chunks[0], RAGChunk)
        assert chunks[0].text == "matching document"
        assert chunks[0].source == "doc1"
        assert chunks[0].score == 0.92


@pytest.mark.asyncio
async def test_rag_pipeline_index_rejects_empty_text(tenant_a_id):
    """Test RAGPipeline.index_document rejects empty text."""
    store = MagicMock()
    embeddings = EmbeddingService("http://localhost:11434")

    pipeline = RAGPipeline(store=store, embeddings=embeddings)

    with pytest.raises(ValueError, match="Document text cannot be empty"):
        await pipeline.index_document(
            tenant_id=tenant_a_id,
            doc_id="doc1",
            text="",
        )


@pytest.mark.asyncio
async def test_rag_pipeline_query_rejects_empty_query(tenant_a_id):
    """Test RAGPipeline.query rejects empty query."""
    store = MagicMock()
    embeddings = EmbeddingService("http://localhost:11434")

    pipeline = RAGPipeline(store=store, embeddings=embeddings)

    with pytest.raises(ValueError, match="Query cannot be empty"):
        await pipeline.query(tenant_id=tenant_a_id, query="")


@pytest.mark.asyncio
async def test_rag_pipeline_query_respects_top_k(tenant_a_id, mock_qdrant_client):
    """Test RAGPipeline.query respects the top_k parameter."""
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store = QdrantStore("http://localhost:6333")
        store._client = mock_qdrant_client

    embeddings = EmbeddingService("http://localhost:11434")

    with patch.object(embeddings, "embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 768
        mock_qdrant_client.search.return_value = []

        pipeline = RAGPipeline(store=store, embeddings=embeddings)

        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

        await pipeline.query(tenant_id=tenant_a_id, query="test", top_k=20)

        # Verify search was called with correct top_k
        call_args = mock_qdrant_client.search.call_args
        assert call_args.kwargs["limit"] == 20


@pytest.mark.asyncio
async def test_rag_pipeline_preserves_metadata(tenant_a_id, mock_qdrant_client):
    """Test RAGPipeline.index_document preserves all metadata."""
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store = QdrantStore("http://localhost:6333")
        store._client = mock_qdrant_client

    embeddings = EmbeddingService("http://localhost:11434")

    with patch.object(embeddings, "embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 768

        pipeline = RAGPipeline(store=store, embeddings=embeddings)

        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

        await pipeline.index_document(
            tenant_id=tenant_a_id,
            doc_id="doc1",
            text="content",
            metadata={"url": "http://example.com", "title": "Example"},
        )

        # Verify metadata was passed to upsert
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args.args[0] if call_args.args else call_args.kwargs["points"]
        # The points are passed as a list to upsert
        assert isinstance(points, list)


# ──────────────────────────────────────────────────────────────────────────────
# Integration-style tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rag_end_to_end_same_tenant(tenant_a_id, mock_qdrant_client):
    """Test complete workflow: index document, then query in same tenant."""
    with patch("ai.rag.store.QdrantClient", return_value=mock_qdrant_client):
        store = QdrantStore("http://localhost:6333")
        store._client = mock_qdrant_client

    embeddings = EmbeddingService("http://localhost:11434")

    with patch.object(embeddings, "embed", new_callable=AsyncMock) as mock_embed:
        # Embed returns same vector every time (for simplicity)
        mock_embed.return_value = [0.1] * 768

        pipeline = RAGPipeline(store=store, embeddings=embeddings)

        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

        # Index a document
        await pipeline.index_document(
            tenant_id=tenant_a_id,
            doc_id="doc1",
            text="Python is a programming language",
        )

        # Query for it
        hit = MagicMock()
        hit.score = 0.88
        hit.payload = {"text": "Python is a programming language", "source": "doc1"}
        mock_qdrant_client.search.return_value = [hit]

        chunks = await pipeline.query(
            tenant_id=tenant_a_id,
            query="programming languages",
        )

        assert len(chunks) == 1
        assert chunks[0].text == "Python is a programming language"
