# Testing
Container: ai-platform-api
Command: docker exec -e PYTHONPATH=/app ai-platform-api python3 tests/.temp_qa_us_NNN.py
pytest: -q --tb=short
PYTHONPATH=/app not set by default — flag is mandatory.
Fixtures: backend/tests/conftest.py (test_tenant_id, test_user_id, other_tenant_id, mock_audit_service)
asyncio_mode = auto