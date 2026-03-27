import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class AuditAction(StrEnum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PERMISSION_DENIED = "permission_denied"
    MODEL_QUERY = "model_query"
    MCP_QUERY = "mcp_query"
    PLUGIN_ENABLED = "plugin_enabled"
    PLUGIN_DISABLED = "plugin_disabled"
    QUOTA_EXCEEDED = "quota_exceeded"
    DOCUMENT_UPLOADED = "document_uploaded"


class AuditService:
    """
    Append-only audit log writer. Writes are non-blocking (fire-and-forget via asyncio.create_task).
    A failed write is logged to stderr but does NOT fail the caller's request.

    The underlying DB user must NOT have UPDATE or DELETE privileges on audit_logs
    (enforced at DB role level — see US-002 completion note).
    """

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._session_factory = session_factory

    async def log(
        self,
        action: str | AuditAction,
        resource: str | None = None,
        user_id: uuid.UUID | str | None = None,
        tenant_id: uuid.UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Fire-and-forget audit write. Schedules the write as an asyncio task.
        Never raises — any DB error is caught and logged to stderr.
        """
        asyncio.create_task(
            self._write(
                action=str(action),
                resource=resource,
                user_id=uuid.UUID(str(user_id)) if user_id else None,
                tenant_id=uuid.UUID(str(tenant_id)) if tenant_id else None,
                metadata=metadata or {},
            )
        )

    async def _write(
        self,
        action: str,
        resource: str | None,
        user_id: uuid.UUID | None,
        tenant_id: uuid.UUID | None,
        metadata: dict[str, Any],
    ) -> None:
        try:
            from ..db.models.audit import (
                AuditLog,
            )  # avoid circular import at module level

            async with self._session_factory() as session:
                entry = AuditLog(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    action=action,
                    resource=resource,
                    timestamp=datetime.now(timezone.utc),
                    log_metadata=metadata,
                )
                session.add(entry)
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            # Never propagate — log to stderr for observability
            logger.error(
                "Audit write failed (action=%s user=%s): %s",
                action,
                user_id,
                exc,
            )


# Module-level singleton — set during app lifespan startup
_audit_service: AuditService | None = None


def init_audit_service(
    session_factory: async_sessionmaker[AsyncSession],
) -> AuditService:
    global _audit_service
    _audit_service = AuditService(session_factory)
    return _audit_service


def get_audit_service() -> AuditService:
    """FastAPI dependency. Returns the singleton AuditService."""
    if _audit_service is None:
        raise RuntimeError(
            "AuditService not initialized. Call init_audit_service() in app lifespan."
        )
    return _audit_service
