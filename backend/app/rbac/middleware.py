import logging
from fastapi import Depends, HTTPException, status
from ..auth.dependencies import CurrentUser, get_current_user
from .permissions import Permission, get_permissions
from ..audit.service import AuditAction, get_audit_service

logger = logging.getLogger(__name__)


def require_permission(permission: Permission):
    """
    FastAPI dependency factory. Returns a Depends that enforces the given permission.
    Permission check uses JWT roles only — no DB query per request.
    Raises HTTP 403 if the current user lacks the permission.
    Raises HTTP 401 (via get_current_user) if not authenticated.
    Every denial is logged for audit purposes.
    """
    async def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_permissions = get_permissions(current_user.roles)
        if permission not in user_permissions:
            logger.warning(
                "Permission denied: user=%s tenant=%s required=%s user_roles=%s",
                current_user.id, current_user.tenant_id, permission, current_user.roles,
            )
            audit_svc = get_audit_service()
            await audit_svc.log(
                AuditAction.PERMISSION_DENIED,
                resource=str(permission),
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                metadata={"required": str(permission), "user_roles": current_user.roles},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required",
            )
        return current_user

    return Depends(_check)
