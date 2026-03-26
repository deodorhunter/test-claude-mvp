import uuid
from datetime import datetime
from sqlalchemy import Text, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    name: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="NOW()")

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    plugins: Mapped[list["TenantPlugin"]] = relationship("TenantPlugin", back_populates="tenant")
    quota: Mapped["TenantTokenQuota"] = relationship("TenantTokenQuota", back_populates="tenant", uselist=False)


class TenantPlugin(Base):
    __tablename__ = "tenant_plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    plugin_name: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="plugins")


class TenantTokenQuota(Base):
    __tablename__ = "tenant_token_quota"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reset_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="quota")
