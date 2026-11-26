"""
saas_backend/app/schemas/auth.py
Pydantic schemas for authentication and user management.
"""

from typing import Optional
from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"
    tenant_id: str = "default-tenant"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
