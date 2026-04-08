# Test Fixtures (backend/tests/conftest.py)
test_tenant_id: "test-tenant-001"
test_user_id: "test-user-001"
other_tenant_id: "other-tenant-999" (cross-tenant isolation)
mock_audit_service: patches backend.app.services.audit.AuditService
Setup: os.environ set at module level before app imports; get_settings.cache_clear() called