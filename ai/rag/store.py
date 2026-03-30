"""
Qdrant vector store wrapper with per-tenant isolation.

Each tenant's documents are stored in a separate collection: tenant_{tenant_id}
This ensures complete data isolation between tenants.
"""

import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)


class QdrantStore:
    """
    Qdrant vector store with tenant-scoped collections.

    Each tenant has its own isolated Qdrant collection named tenant_{tenant_id}.
    This prevents cross-tenant data leakage at the database level.
    """

    VECTOR_SIZE = 768  # nomic-embed-text output dimension

    def __init__(self, qdrant_url: str):
        """
        Initialize Qdrant store.

        Args:
            qdrant_url: URL of the Qdrant service (e.g., http://localhost:6333)
        """
        self._client = QdrantClient(url=qdrant_url)

    def _collection_name(self, tenant_id: str) -> str:
        """
        Generate the collection name for a tenant.

        Args:
            tenant_id: The tenant's unique identifier

        Returns:
            Collection name in format tenant_{tenant_id}
        """
        return f"tenant_{tenant_id}"

    def _ensure_collection(self, tenant_id: str) -> None:
        """
        Create the tenant's collection if it does not exist.

        Args:
            tenant_id: The tenant's unique identifier
        """
        collection_name = self._collection_name(tenant_id)

        # Check if collection exists
        try:
            collections = self._client.get_collections()
            existing_names = [c.name for c in collections.collections]
            if collection_name not in existing_names:
                logger.info(f"Creating collection {collection_name}")
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE, distance=Distance.COSINE
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise

    def index_document(
        self,
        tenant_id: str,
        doc_id: str,
        vector: list[float],
        metadata: dict,
    ) -> None:
        """
        Index a document with its embedding vector.

        Args:
            tenant_id: The tenant's unique identifier
            doc_id: Unique document identifier within the tenant
            vector: Embedding vector (list of floats)
            metadata: Document metadata (will be stored in payload)

        Raises:
            ValueError: If vector size doesn't match expected VECTOR_SIZE
            Exception: If Qdrant operation fails
        """
        if len(vector) != self.VECTOR_SIZE:
            raise ValueError(
                f"Vector size {len(vector)} does not match expected {self.VECTOR_SIZE}"
            )

        self._ensure_collection(tenant_id)

        # Use a deterministic hash-based ID to ensure consistent IDs for same doc_id
        point_id = abs(hash((tenant_id, doc_id))) % (2**63)

        try:
            self._client.upsert(
                collection_name=self._collection_name(tenant_id),
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=metadata,
                    )
                ],
            )
            logger.debug(
                f"Indexed document {doc_id} for tenant {tenant_id} (point_id={point_id})"
            )
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            raise

    def search(
        self,
        tenant_id: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search for documents in the tenant's collection.

        Args:
            tenant_id: The tenant's unique identifier
            query_vector: Query embedding vector
            top_k: Maximum number of results to return

        Returns:
            List of dicts with 'score' and 'payload' keys

        Raises:
            ValueError: If vector size doesn't match expected VECTOR_SIZE
            Exception: If Qdrant operation fails
        """
        if len(query_vector) != self.VECTOR_SIZE:
            raise ValueError(
                f"Vector size {len(query_vector)} does not match expected {self.VECTOR_SIZE}"
            )

        self._ensure_collection(tenant_id)

        try:
            hits = self._client.search(
                collection_name=self._collection_name(tenant_id),
                query_vector=query_vector,
                limit=top_k,
            )
            results = [{"score": h.score, "payload": h.payload} for h in hits]
            logger.debug(f"Search for tenant {tenant_id} returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to search for tenant {tenant_id}: {e}")
            raise
