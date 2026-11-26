"""
saas_backend/app/api/routes_conflicts.py
Conflict item routes: list and resolve conflicts associated with build jobs.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import ConflictLog

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class ConflictOut(BaseModel):
    id: int
    conflict_type: str
    severity: str
    message: str
    affected_entries: list
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResolveRequest(BaseModel):
    resolved_by: str = "admin"


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/conflicts", response_model=List[ConflictOut])
def list_conflicts(
    tenant_id: str = Query("default-tenant"),
    severity: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List conflict logs with optional filters."""
    q = db.query(ConflictLog).filter(ConflictLog.tenant_id == tenant_id)
    if severity:
        q = q.filter(ConflictLog.severity == severity)
    if is_resolved is not None:
        q = q.filter(ConflictLog.is_resolved == is_resolved)
    return q.order_by(ConflictLog.created_at.desc()).all()


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: int,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
):
    """Mark a conflict log as resolved."""
    conflict = db.query(ConflictLog).filter(ConflictLog.id == conflict_id).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    conflict.is_resolved = True
    conflict.resolved_by = payload.resolved_by
    conflict.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(conflict)
    return {"message": "Conflict resolved", "id": conflict.id}


@router.delete("/conflicts/{conflict_id}", status_code=204)
def delete_conflict(conflict_id: int, db: Session = Depends(get_db)):
    """Delete a conflict log entry."""
    conflict = db.query(ConflictLog).filter(ConflictLog.id == conflict_id).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    db.delete(conflict)
    db.commit()
