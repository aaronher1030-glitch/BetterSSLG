"""
saas_backend/app/schemas/conflicts.py
Pydantic schemas for conflict management.
"""

from typing import Optional
from pydantic import BaseModel


class ResolveConflictRequest(BaseModel):
    resolved_by: str = "admin"


class ConflictResolutionResponse(BaseModel):
    message: str
    id: int
