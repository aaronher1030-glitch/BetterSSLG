"""
saas_backend/app/core/auth.py
Role-based and tenant-based authorization dependencies.
"""

from typing import Callable, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from app.api.routes_auth import get_current_user
from app.models.entities import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency factory enforcing allowed user roles."""
    def _role_checker(user: User = Depends(get_current_user)) -> User:
        if allowed_roles and user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized. Allowed: {list(allowed_roles)}",
            )
        return user
    return _role_checker


def require_tenant_access(
    user: User = Depends(get_current_user),
    tenant_id: Optional[str] = Query(None),
) -> str:
    """Dependency enforcing tenant isolation."""
    effective_tenant = tenant_id if tenant_id is not None else user.tenant_id
    if user.tenant_id != "admin" and user.tenant_id != effective_tenant and effective_tenant != "default-tenant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access mismatch",
        )
    return effective_tenant
