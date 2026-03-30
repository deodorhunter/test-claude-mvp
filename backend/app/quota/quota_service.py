import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class QuotaService:
    """Tracks and enforces monthly token quota per tenant."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        audit_service=None,
    ):
        """
        Initialize the quota service.

        Args:
            session_factory: SQLAlchemy async session factory
            audit_service: Optional AuditService for logging quota exceeded events
        """
        self.session_factory = session_factory
        self.audit_service = audit_service

    async def check_quota(
        self, tenant_id: uuid.UUID, tokens_estimated: int
    ) -> bool:
        """
        Check if quota is available for estimated token consumption.

        Args:
            tenant_id: The tenant UUID
            tokens_estimated: Estimated tokens for the upcoming operation

        Returns:
            True if quota available, False if would exceed limit.
            If no quota row exists: returns True (unlimited).
            On check failure: logs warning and returns True (fail-open).
        """
        try:
            from ..db.models.tenant import TenantTokenQuota
            from ..audit.service import AuditAction

            async with self.session_factory() as session:
                quota = await session.execute(
                    select(TenantTokenQuota).where(
                        TenantTokenQuota.tenant_id == tenant_id
                    )
                )
                quota_row = quota.scalar_one_or_none()

                # No quota configured = unlimited
                if not quota_row:
                    return True

                # Check if consumption would exceed limit
                if (
                    quota_row.tokens_used + tokens_estimated
                    > quota_row.max_tokens
                ):
                    logger.warning(
                        "Quota exceeded for tenant=%s: "
                        "tokens_used=%d tokens_estimated=%d max_tokens=%d",
                        tenant_id,
                        quota_row.tokens_used,
                        tokens_estimated,
                        quota_row.max_tokens,
                    )

                    # Emit audit entry
                    if self.audit_service:
                        await self.audit_service.log(
                            action=AuditAction.QUOTA_EXCEEDED,
                            tenant_id=tenant_id,
                            metadata={
                                "tokens_used": quota_row.tokens_used,
                                "tokens_estimated": tokens_estimated,
                                "max_tokens": quota_row.max_tokens,
                            },
                        )

                    return False

                return True

        except Exception as exc:
            # Fail-open on quota service failure
            logger.warning(
                "Quota check failed for tenant=%s: %s. Allowing request.",
                tenant_id,
                exc,
            )
            return True

    async def consume_quota(
        self, tenant_id: uuid.UUID, tokens_used: int
    ) -> None:
        """
        Consume tokens from the tenant's quota and check for 80% alert.

        Args:
            tenant_id: The tenant UUID
            tokens_used: Number of tokens to consume

        Side effects:
            - Updates tokens_used in DB for the tenant
            - Logs warning if quota usage exceeds 80%
            - Uses its own session (doesn't depend on caller's transaction state)
        """
        try:
            from ..db.models.tenant import TenantTokenQuota

            async with self.session_factory() as session:
                quota = await session.execute(
                    select(TenantTokenQuota).where(
                        TenantTokenQuota.tenant_id == tenant_id
                    )
                )
                quota_row = quota.scalar_one_or_none()

                if not quota_row:
                    # No quota configured; silently return
                    return

                # Update tokens_used
                quota_row.tokens_used += tokens_used
                session.add(quota_row)
                await session.commit()

                # Check 80% threshold
                pct_used = (quota_row.tokens_used / quota_row.max_tokens) * 100
                if pct_used >= 80.0:
                    logger.warning(
                        "Tenant %s has used %.1f%% of quota "
                        "(tokens_used=%d max_tokens=%d)",
                        tenant_id,
                        pct_used,
                        quota_row.tokens_used,
                        quota_row.max_tokens,
                    )

        except Exception as exc:
            # Log but don't raise; quota consumption failure should not block the operation
            logger.error(
                "Quota consumption failed for tenant=%s tokens=%d: %s",
                tenant_id,
                tokens_used,
                exc,
            )
