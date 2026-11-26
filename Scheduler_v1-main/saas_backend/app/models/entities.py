"""
saas_backend/app/models/entities.py
SQLAlchemy ORM models for all SCAS domain entities.
"""

import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, TEXT

from app.db.database import Base


# ── JSON column helper (SQLite-compatible) ────────────────────────────────────
class JSONType(TypeDecorator):
    """Stores Python dict/list as JSON text in SQLite; uses native JSON in Postgres."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


# ── User ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role            = Column(String(30), nullable=False, default="viewer")
    tenant_id       = Column(String(120), nullable=False, default="default-tenant", index=True)
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── Faculty ───────────────────────────────────────────────────────────────────
class Faculty(Base):
    __tablename__ = "faculty"

    id                       = Column(Integer, primary_key=True, index=True)
    name                     = Column(String(150), nullable=False, index=True)
    department               = Column(String(100), nullable=False, default="General")
    employment_type          = Column(String(20), nullable=False, default="Full-time")
    binary_availability_mask = Column(JSONType, nullable=False, default=lambda: [True] * 40)
    tenant_id                = Column(String(120), nullable=False, default="default-tenant", index=True)
    created_at               = Column(DateTime, default=datetime.utcnow, nullable=False)

    schedule_entries = relationship("ScheduleEntry", back_populates="faculty", passive_deletes=True)


# ── Room ──────────────────────────────────────────────────────────────────────
class Room(Base):
    __tablename__ = "rooms"

    id           = Column(Integer, primary_key=True, index=True)
    room_number  = Column(String(50), nullable=False, index=True)
    capacity     = Column(Integer, nullable=False, default=40)
    floor        = Column(Integer, nullable=False, default=1)
    is_available = Column(Boolean, nullable=False, default=True)
    tenant_id    = Column(String(120), nullable=False, default="default-tenant", index=True)
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    schedule_entries = relationship("ScheduleEntry", back_populates="room", passive_deletes=True)


# ── Subject ───────────────────────────────────────────────────────────────────
class Subject(Base):
    __tablename__ = "subjects"

    id                      = Column(Integer, primary_key=True, index=True)
    code                    = Column(String(20), nullable=False, index=True)
    title                   = Column(String(200), nullable=False)
    units                   = Column(Integer, nullable=False, default=1)
    year_level              = Column(String(20), nullable=False, default="Grade 7")
    required_hours_per_week = Column(Integer, nullable=False, default=5)
    tenant_id               = Column(String(120), nullable=False, default="default-tenant", index=True)
    created_at              = Column(DateTime, default=datetime.utcnow, nullable=False)

    schedule_entries = relationship("ScheduleEntry", back_populates="subject", passive_deletes=True)


# ── ScheduleEntry ─────────────────────────────────────────────────────────────
class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id           = Column(Integer, primary_key=True, index=True)
    subject_id   = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id   = Column(Integer, ForeignKey("faculty.id",  ondelete="SET NULL"), nullable=True,  index=True)
    room_id      = Column(Integer, ForeignKey("rooms.id",    ondelete="SET NULL"), nullable=True,  index=True)
    section_name = Column(String(100), nullable=False, index=True)
    day_of_week  = Column(Integer, nullable=False)          # 0=Mon … 4=Fri
    time_slot    = Column(Integer, nullable=False)           # period number 1–8
    status       = Column(String(20), nullable=False, default="pending")  # pending | finalized
    job_id       = Column(String(64), nullable=True, index=True)
    tenant_id    = Column(String(120), nullable=False, default="default-tenant", index=True)
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    subject = relationship("Subject", back_populates="schedule_entries")
    faculty = relationship("Faculty", back_populates="schedule_entries")
    room    = relationship("Room",    back_populates="schedule_entries")


# ── ConflictLog ───────────────────────────────────────────────────────────────
class ConflictLog(Base):
    __tablename__ = "conflict_logs"

    id               = Column(Integer, primary_key=True, index=True)
    conflict_type    = Column(String(60), nullable=False, index=True)
    severity         = Column(String(20), nullable=False, default="error")   # error | warning
    message          = Column(Text, nullable=False)
    affected_entries = Column(JSONType, nullable=False, default=list)
    is_resolved      = Column(Boolean, nullable=False, default=False)
    resolved_by      = Column(String(100), nullable=True)
    resolved_at      = Column(DateTime, nullable=True)
    tenant_id        = Column(String(120), nullable=False, default="default-tenant", index=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── BuildJob ──────────────────────────────────────────────────────────────────
class BuildJob(Base):
    __tablename__ = "build_jobs"

    id           = Column(String(64), primary_key=True, index=True)
    status       = Column(String(30), nullable=False, default="queued")   # queued | running | done | failed
    request_json = Column(JSONType, nullable=False, default=dict)
    result_json  = Column(JSONType, nullable=True)
    error_msg    = Column(Text, nullable=True)
    tenant_id    = Column(String(120), nullable=False, default="default-tenant", index=True)
    school_id    = Column(String(120), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ── ScheduleVersion ───────────────────────────────────────────────────────────
class ScheduleVersion(Base):
    __tablename__ = "schedule_versions"

    id             = Column(Integer, primary_key=True, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    schedule_data  = Column(JSONType, nullable=False, default=dict)
    is_active      = Column(Boolean, nullable=False, default=True)
    tenant_id      = Column(String(120), nullable=False, default="default-tenant", index=True)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
