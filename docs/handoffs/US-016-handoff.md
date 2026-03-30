# Handoff: US-016 — RAG Pipeline: Qdrant + Embedding Service

**Completed by:** AI/ML Engineer
**Date:** 2026-03-29
**Files created/modified:**
- `ai/rag/embeddings.py` (new)
- `ai/rag/store.py` (new)
- `ai/rag/pipeline.py` (new)
- `ai/rag/__init__.py` (new)
- `backend/pyproject.toml` (modified — added `qdrant-client>=1.9.0`)
- `backend/tests/test_rag.py` (new — 30 tests)

## What was built

Implemented a multi-tenant RAG (Retrieval-Augmented Generation) pipeline with three core components:

1. **EmbeddingService** — wraps Ollama's API to generate text embeddings using the `nomic-embed-text` model (768-dimensional vectors). Handles HTTP calls to `{ollama_url}/api/embeddings`.

2. **QdrantStore** — persistent vector storage backed by Qdrant. Creates per-tenant collections named `tenant_{tenant_id}` to enforce strict isolation. Implements `index_document()` for ingestion and `search()` for retrieval.

3. **RAGPipeline** — orchestrates embedding + storage + retrieval. Public API: `index_document(tenant_id, doc_id, text, metadata)` and `query(tenant_id, query, top_k=5)`. Returns `RAGChunk` dataclass (text, source, score).

**Critical design decision:** Every vector collection and every query is scoped to a single `tenant_id`. The `_collection_name()` method explicitly constructs `tenant_{tenant_id}` and is called in both `index_document()` and `search()` paths. This prevents accidental cross-tenant leakage.

## Integration points

- **Ollama service:** EmbeddingService connects to `http://ollama:11434/api/embeddings`. Must be available at runtime.
- **Qdrant service:** QdrantStore connects to Qdrant URL (configured, not hardcoded). Planner or other agents can call `pipeline.query(tenant_id, query)` to retrieve documents.
- **Data flow:** `RAGPipeline.query()` → calls `EmbeddingService.embed(query)` → calls `QdrantStore.search()` with the embedding vector → returns `list[RAGChunk]`.

## File ownership

- `ai/rag/` (all files) — owned by AI/ML team. Responsible for embedding model selection, Qdrant schema, and vector search quality.
- `backend/pyproject.toml` — shared ownership; qdrant-client dependency now pinned.
- `backend/tests/test_rag.py` — owned by QA; tests cover tenant isolation, embedding call contracts, and RAGChunk serialization.

## Residual risks / known gaps

- **MEDIUM:** EmbeddingService has no retry logic for transient Ollama failures. A single timeout will raise immediately. Consider adding exponential backoff in future.
- **MEDIUM:** No batch embedding endpoint. Each `embed()` call is a single HTTP request. For large documents, this may be slow. Batch API exists in Ollama; defer to Phase 3.
- **LOW:** Qdrant collection names are hardcoded as `tenant_{tenant_id}`. No namespace or prefix. If tenant IDs collide with reserved names, this could fail. Tenant ID format is not validated.

## Manual test instructions (for user)

### Prerequisite
Ensure Docker Compose stack is running:
```bash
make up
```

### Test 1 — Collection naming isolation

Write the following script:
```bash
cat > /tmp/qa_us016.py << 'EOF'
from ai.rag.store import QdrantStore

store = QdrantStore("http://localhost:6333")

# Test collection name generation
coll_a = store._collection_name("tenant-abc-123")
coll_b = store._collection_name("tenant-xyz-789")

assert coll_a == "tenant_tenant-abc-123", f"Expected tenant_tenant-abc-123, got {coll_a}"
assert coll_b == "tenant_tenant-xyz-789", f"Expected tenant_tenant-xyz-789, got {coll_b}"
assert coll_a != coll_b, "Collection names must differ for different tenants"

print("✓ Collection naming isolation: PASS")
EOF
```

Execute:
```bash
docker exec ai-platform-api python3 /tmp/qa_us016.py && rm /tmp/qa_us016.py
```

Expected output:
```
✓ Collection naming isolation: PASS
```

### Test 2 — EmbeddingService import and availability

```bash
docker exec ai-platform-api python3 << 'EOF'
from ai.rag.embeddings import EmbeddingService

service = EmbeddingService("http://ollama:11434")
assert service.model == "nomic-embed-text"
print("✓ EmbeddingService instantiation: PASS")
EOF
```

Expected output:
```
✓ EmbeddingService instantiation: PASS
```

### Test 3 — RAGPipeline integration

Write the following script:
```bash
cat > /tmp/qa_us016_pipeline.py << 'EOF'
from ai.rag.pipeline import RAGPipeline, RAGChunk
from ai.rag.store import QdrantStore
from ai.rag.embeddings import EmbeddingService

# Instantiate
store = QdrantStore("http://localhost:6333")
embeddings = EmbeddingService("http://ollama:11434")
pipeline = RAGPipeline(store, embeddings)

# Verify RAGChunk dataclass
chunk = RAGChunk(text="sample", source="test.txt", score=0.95)
assert chunk.text == "sample"
assert chunk.score == 0.95
print("✓ RAGChunk dataclass: PASS")

# Verify pipeline has required methods
assert hasattr(pipeline, "index_document")
assert hasattr(pipeline, "query")
print("✓ RAGPipeline methods: PASS")
EOF
```

Execute:
```bash
docker exec ai-platform-api python3 /tmp/qa_us016_pipeline.py && rm /tmp/qa_us016_pipeline.py
```

Expected output:
```
✓ RAGChunk dataclass: PASS
✓ RAGPipeline methods: PASS
```

## How to verify this works (automated)

Run the test suite:
```bash
cd /Users/martina/personal-projects/test-claude-mvp
make test -q 2>&1 | grep -E "test_rag|passed|failed"
```

Expected output (excerpt):
```
backend/tests/test_rag.py ............................ 30 passed
```

All 30 tests cover:
- Collection naming per tenant
- Index + search within same tenant
- Cross-tenant isolation (tenant A docs are not in tenant B search results)
- EmbeddingService Ollama API contract
- RAGChunk serialization
- Edge cases (empty queries, missing collections, duplicate doc IDs)

