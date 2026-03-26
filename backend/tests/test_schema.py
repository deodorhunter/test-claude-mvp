"""
Schema validation tests — no DB required.

Verifies ORM model definitions: table names, constraints, FK relationships,
and structural properties enforced at the SQLAlchemy metadata level.
"""
import uuid


# ──────────────────────────────────────────────────────────────────────────────
# Table name tests
# ──────────────────────────────────────────────────────────────────────────────

def test_tenant_model_tablename():
    from app.db.models.tenant import Tenant, TenantPlugin, TenantTokenQuota
    assert Tenant.__tablename__ == "tenants"
    assert TenantPlugin.__tablename__ == "tenant_plugins"
    assert TenantTokenQuota.__tablename__ == "tenant_token_quota"


def test_user_model_tablename():
    from app.db.models.user import User
    assert User.__tablename__ == "users"


def test_audit_log_model_tablename():
    from app.db.models.audit import AuditLog
    assert AuditLog.__tablename__ == "audit_logs"


# ──────────────────────────────────────────────────────────────────────────────
# Constraint tests
# ──────────────────────────────────────────────────────────────────────────────

def test_user_unique_constraint_defined():
    from app.db.models.user import User
    constraint_names = {c.name for c in User.__table__.constraints}
    assert "uq_users_plone_username_tenant" in constraint_names


def test_user_role_check_constraint_defined():
    from app.db.models.user import User
    constraint_names = {c.name for c in User.__table__.constraints}
    assert "ck_users_role" in constraint_names


def test_user_role_check_constraint_covers_expected_roles():
    """
    The check constraint text must include 'admin', 'member', and 'guest'.
    This documents the accepted role values and catches accidental renames.
    """
    from app.db.models.user import User
    from sqlalchemy import CheckConstraint
    check_constraints = [
        c for c in User.__table__.constraints
        if isinstance(c, CheckConstraint) and c.name == "ck_users_role"
    ]
    assert len(check_constraints) == 1
    constraint_text = str(check_constraints[0].sqltext)
    assert "admin" in constraint_text
    assert "member" in constraint_text
    assert "guest" in constraint_text


# ──────────────────────────────────────────────────────────────────────────────
# Metadata registration test
# ──────────────────────────────────────────────────────────────────────────────

def test_all_models_registered_in_metadata():
    from app.db.base import Base
    from app.db.models.tenant import Tenant, TenantPlugin, TenantTokenQuota  # noqa: F401
    from app.db.models.user import User  # noqa: F401
    from app.db.models.audit import AuditLog  # noqa: F401
    table_names = set(Base.metadata.tables.keys())
    assert {"tenants", "users", "tenant_plugins", "tenant_token_quota", "audit_logs"} == table_names


# ──────────────────────────────────────────────────────────────────────────────
# Foreign key structure tests
# ──────────────────────────────────────────────────────────────────────────────

def test_audit_log_has_no_fk_to_users():
    """
    audit_logs must have NO foreign keys.
    This is intentional: audit entries must survive even if a user or tenant is
    deleted (GDPR retention requirement). The columns user_id and tenant_id are
    plain UUID columns with no FK constraint.
    """
    from app.db.models.audit import AuditLog
    assert len(AuditLog.__table__.foreign_keys) == 0


def test_audit_log_user_id_column_is_nullable():
    """
    user_id in audit_logs is nullable — anonymous or system actions must be loggable.
    """
    from app.db.models.audit import AuditLog
    col = AuditLog.__table__.c["user_id"]
    assert col.nullable is True


def test_audit_log_tenant_id_column_is_nullable():
    """
    tenant_id in audit_logs is nullable — same rationale as user_id.
    """
    from app.db.models.audit import AuditLog
    col = AuditLog.__table__.c["tenant_id"]
    assert col.nullable is True


def test_tenant_plugin_fk_to_tenants():
    from app.db.models.tenant import TenantPlugin
    fk_targets = {fk.target_fullname for fk in TenantPlugin.__table__.foreign_keys}
    assert "tenants.id" in fk_targets


def test_tenant_token_quota_fk_to_tenants():
    from app.db.models.tenant import TenantTokenQuota
    fk_targets = {fk.target_fullname for fk in TenantTokenQuota.__table__.foreign_keys}
    assert "tenants.id" in fk_targets


def test_user_fk_to_tenants():
    from app.db.models.user import User
    fk_targets = {fk.target_fullname for fk in User.__table__.foreign_keys}
    assert "tenants.id" in fk_targets


def test_user_fk_cascade_delete():
    """
    User rows must be deleted when the parent tenant is deleted (CASCADE).
    Verifies the ondelete rule on the FK, not just its presence.
    """
    from app.db.models.user import User
    fk_to_tenant = next(
        fk for fk in User.__table__.foreign_keys
        if fk.target_fullname == "tenants.id"
    )
    assert fk_to_tenant.ondelete == "CASCADE"


def test_tenant_plugin_fk_cascade_delete():
    from app.db.models.tenant import TenantPlugin
    fk_to_tenant = next(
        fk for fk in TenantPlugin.__table__.foreign_keys
        if fk.target_fullname == "tenants.id"
    )
    assert fk_to_tenant.ondelete == "CASCADE"


# ──────────────────────────────────────────────────────────────────────────────
# Audit service append-only verification (code-level check)
# ──────────────────────────────────────────────────────────────────────────────

def test_audit_log_no_update_delete_in_service():
    """
    Verify AuditService._write does not use session.update() or session.delete().
    This is a code-level guard for the append-only enforcement requirement.
    GDPR and EU AI Act compliance depend on audit log immutability.
    """
    import inspect
    from app.audit.service import AuditService
    source = inspect.getsource(AuditService._write)
    assert "session.update" not in source
    assert "session.delete" not in source
    # No raw UPDATE or DELETE SQL strings either
    assert "UPDATE" not in source
    assert "DELETE" not in source


def test_audit_service_write_uses_only_add_and_commit():
    """
    The _write method must use session.add() followed by session.commit().
    Both must be present; no other mutation methods (merge, bulk_insert_mappings, etc.)
    should appear.
    """
    import inspect
    from app.audit.service import AuditService
    source = inspect.getsource(AuditService._write)
    assert "session.add(" in source
    assert "session.commit()" in source
    assert "session.merge" not in source
