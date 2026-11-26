"""
saas_backend/app/schemas/imports.py
Pydantic schemas for CSV imports.
"""

from typing import List, Dict, Any
from pydantic import BaseModel


class ImportValidationResponse(BaseModel):
    success: bool
    rows_parsed: int
    errors: List[str]
    preview: List[Dict[str, Any]]
