"""
create_test_user.py — SCAS Bootstrap Script
Seeds: 1 admin user, 3 faculty, 5 rooms, 9 Grade-7 subjects.
Run from project root:  python create_test_user.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "saas_backend"))

from app.db.database import Base, SessionLocal, engine
from app.models.entities import Faculty, Room, Subject, User
from app.core.security import hash_password

TENANT = "deped-national"


def _ensure_tables():
    Base.metadata.create_all(bind=engine)
    print("OK  Database tables verified / created.")


def _seed_user(db):
    uname = "admin@deped.gov.ph"
    if db.query(User).filter(User.username == uname).first():
        print(f"--  User '{uname}' already exists — skipped.")
        return
    db.add(User(
        username=uname,
        hashed_password=hash_password("password123"),
        role="admin",
        tenant_id=TENANT,
    ))
    print(f"OK  User '{uname}' created  (password: password123).")


def _seed_faculty(db):
    sample = [
        {
            "name": "Maria Santos",
            "department": "Science",
            "employment_type": "Full-time",
            # Mon P5-8 blocked, Wed P5-8 blocked, rest available
            "binary_availability_mask": (
                [True]*4 + [False]*4 +  # Mon
                [True]*8 +              # Tue
                [True]*4 + [False]*4 +  # Wed
                [True]*8 +              # Thu
                [True]*8                # Fri
            ),
        },
        {
            "name": "Jose Reyes",
            "department": "Mathematics",
            "employment_type": "Full-time",
            "binary_availability_mask": [True] * 40,
        },
        {
            "name": "Ana Lim",
            "department": "Language",
            "employment_type": "Part-time",
            # Only Mon-Wed mornings (P1-4)
            "binary_availability_mask": (
                [True]*4 + [False]*4 +
                [True]*4 + [False]*4 +
                [True]*4 + [False]*4 +
                [False]*8 +
                [False]*8
            ),
        },
    ]
    for f in sample:
        if db.query(Faculty).filter(Faculty.name == f["name"], Faculty.tenant_id == TENANT).first():
            print(f"--  Faculty '{f['name']}' already exists — skipped.")
            continue
        db.add(Faculty(**f, tenant_id=TENANT))
        print(f"OK  Faculty '{f['name']}' created.")


def _seed_rooms(db):
    sample = [
        {"room_number": "101", "capacity": 45, "floor": 1, "is_available": True},
        {"room_number": "102", "capacity": 45, "floor": 1, "is_available": True},
        {"room_number": "103", "capacity": 40, "floor": 1, "is_available": True},
        {"room_number": "201", "capacity": 50, "floor": 2, "is_available": True},
        {"room_number": "202", "capacity": 35, "floor": 2, "is_available": False},
    ]
    for r in sample:
        if db.query(Room).filter(Room.room_number == r["room_number"], Room.tenant_id == TENANT).first():
            print(f"--  Room '{r['room_number']}' already exists — skipped.")
            continue
        db.add(Room(**r, tenant_id=TENANT))
        print(f"OK  Room {r['room_number']}  floor={r['floor']}  cap={r['capacity']}.")


def _seed_subjects(db):
    sample = [
        {"code": "ENG7",   "title": "English 7",           "units": 1, "year_level": "Grade 7", "required_hours_per_week": 5},
        {"code": "MATH7",  "title": "Mathematics 7",        "units": 1, "year_level": "Grade 7", "required_hours_per_week": 5},
        {"code": "SCI7",   "title": "Science 7",            "units": 1, "year_level": "Grade 7", "required_hours_per_week": 5},
        {"code": "FIL7",   "title": "Filipino 7",           "units": 1, "year_level": "Grade 7", "required_hours_per_week": 4},
        {"code": "AP7",    "title": "Araling Panlipunan 7", "units": 1, "year_level": "Grade 7", "required_hours_per_week": 4},
        {"code": "TLE7",   "title": "TLE 7",                "units": 1, "year_level": "Grade 7", "required_hours_per_week": 4},
        {"code": "MAPEH7", "title": "MAPEH 7",              "units": 1, "year_level": "Grade 7", "required_hours_per_week": 4},
        {"code": "VE7",    "title": "Values Education 7",   "units": 1, "year_level": "Grade 7", "required_hours_per_week": 4},
        {"code": "HG7",    "title": "Homeroom Guidance 7",  "units": 1, "year_level": "Grade 7", "required_hours_per_week": 1},
    ]
    for s in sample:
        if db.query(Subject).filter(Subject.code == s["code"], Subject.tenant_id == TENANT).first():
            print(f"--  Subject '{s['code']}' already exists — skipped.")
            continue
        db.add(Subject(**s, tenant_id=TENANT))
        print(f"OK  Subject {s['code']} — {s['title']}.")


def main():
    print("\nSCAS Bootstrap")
    print("=" * 44)
    _ensure_tables()
    with SessionLocal() as db:
        _seed_user(db)
        _seed_faculty(db)
        _seed_rooms(db)
        _seed_subjects(db)
        db.commit()
    print("=" * 44)
    print("Bootstrap complete.  Login: admin@deped.gov.ph / password123\n")


if __name__ == "__main__":
    main()
