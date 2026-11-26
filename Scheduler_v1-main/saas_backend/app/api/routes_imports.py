"""
saas_backend/app/api/routes_imports.py
CSV import/validation routes for bulk onboarding of faculty, rooms, and subjects.
"""

import csv
import io
from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class ImportResult(BaseModel):
    success: bool
    rows_parsed: int
    errors: List[str]
    preview: List[dict]


REQUIRED_FACULTY_COLS = {"name", "department", "employment_type"}
REQUIRED_ROOM_COLS    = {"room_number", "capacity", "floor"}
REQUIRED_SUBJECT_COLS = {"code", "title", "units", "year_level", "required_hours_per_week"}


def _validate_csv(content: bytes, required_cols: set) -> ImportResult:
    """Parse and validate a CSV upload, returning a preview of the first 10 rows."""
    try:
        text = content.decode("utf-8-sig")  # handle BOM
        reader = csv.DictReader(io.StringIO(text))
        headers = set(reader.fieldnames or [])
        missing = required_cols - headers
        if missing:
            return ImportResult(
                success=False,
                rows_parsed=0,
                errors=[f"Missing required columns: {', '.join(sorted(missing))}"],
                preview=[],
            )
        rows = []
        errors = []
        for i, row in enumerate(reader, start=2):  # row 1 is header
            for col in required_cols:
                if not row.get(col, "").strip():
                    errors.append(f"Row {i}: '{col}' is empty")
            rows.append(dict(row))

        return ImportResult(
            success=len(errors) == 0,
            rows_parsed=len(rows),
            errors=errors[:20],  # cap at 20 errors
            preview=rows[:10],
        )
    except Exception as exc:
        return ImportResult(success=False, rows_parsed=0, errors=[str(exc)], preview=[])


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/imports/faculty", response_model=ImportResult)
async def import_faculty_csv(file: UploadFile = File(...)):
    """
    Validate a faculty CSV file.
    Required columns: name, department, employment_type
    """
    content = await file.read()
    return _validate_csv(content, REQUIRED_FACULTY_COLS)


@router.post("/imports/rooms", response_model=ImportResult)
async def import_rooms_csv(file: UploadFile = File(...)):
    """
    Validate a rooms CSV file.
    Required columns: room_number, capacity, floor
    """
    content = await file.read()
    return _validate_csv(content, REQUIRED_ROOM_COLS)


@router.post("/imports/subjects", response_model=ImportResult)
async def import_subjects_csv(file: UploadFile = File(...)):
    """
    Validate a subjects CSV file.
    Required columns: code, title, units, year_level, required_hours_per_week
    """
    content = await file.read()
    return _validate_csv(content, REQUIRED_SUBJECT_COLS)


@router.post("/imports/csv", response_model=ImportResult)
async def import_generic_csv(
    file: UploadFile = File(...),
    resource_type: str = Query("faculty", enum=["faculty", "rooms", "subjects"]),
):
    """
    Generic CSV import endpoint. Specify resource_type to determine validation rules.
    """
    content = await file.read()
    col_map = {
        "faculty":  REQUIRED_FACULTY_COLS,
        "rooms":    REQUIRED_ROOM_COLS,
        "subjects": REQUIRED_SUBJECT_COLS,
    }
    return _validate_csv(content, col_map[resource_type])
