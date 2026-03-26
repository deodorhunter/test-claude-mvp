# US-006: Audit Logging Service — Done

## Summary
Implemented append-only AuditService for GDPR/EU AI Act compliance logging.

## AuditAction values
| Action | Trigger |
|---|---|
| `login_success` | Successful Plone bridge login |
| `login_failure` | Failed login attempt |
| `permission_denied` | RBAC check failure |
| `model_query` | Every AI model invocation (must include metadata.sources) |
| `mcp_query` | Every MCP server query |
| `plugin_enabled` | Plugin enabled for tenant |
| `plugin_disabled` | Plugin disabled for tenant |
| `quota_exceeded` | Token quota limit hit |
| `document_uploaded` | User uploaded document to chat |

## Non-blocking Design
`AuditService.log()` schedules writes via `asyncio.create_task()` — it returns immediately without awaiting DB write. A failed DB write is caught internally and logged to stderr. This means:
- Audit write failure does NOT fail the user request
- There is a small window where a request completes but the audit entry is not yet written (in-flight task)
- **Trade-off accepted for MVP**: in production, consider a queue-backed audit writer for durability

## Append-Only Enforcement
The `audit_logs` table has no UPDATE or DELETE grant to the application DB user (enforced at DB role level per US-002). The AuditService only calls `session.add()` + `session.commit()` — no update or delete operations.

## EU AI Act Note
`MODEL_QUERY` audit entries MUST include `metadata.sources` (list of `{source, confidence}` objects for every RAG/MCP source used in the response context). This is the AI/ML Engineer's responsibility when wiring the orchestrator in Phase 2.

## Integration Points
The `get_audit_service()` FastAPI dependency must be injected into:
- `backend/app/api/v1/auth.py` — for LOGIN_SUCCESS and LOGIN_FAILURE
- `backend/app/rbac/middleware.py` — for PERMISSION_DENIED
- Future: orchestrator (MODEL_QUERY), plugin manager (PLUGIN_ENABLED/DISABLED), quota enforcer (QUOTA_EXCEEDED)

## Security Notes — Residual Risks
1. **Fire-and-forget trade-off** — if the application crashes mid-request, the asyncio task may not complete. Mitigation: add structured logging (JSON to stdout) as a secondary audit trail.
2. **No audit log retention policy yet** — GDPR requires defined retention periods. This is a Phase 4 concern.
3. **LOGIN_SUCCESS/LOGIN_FAILURE not yet wired** — US-004's auth.py currently logs to stderr only. Must wire to AuditService after this US is merged.
