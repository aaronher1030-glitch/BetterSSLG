"""
build_exe.py — PyInstaller packaging script for ASCS_Scheduler.exe
Run from the project root:  python build_exe.py
"""
import PyInstaller.__main__
import os

datas = [
    ("Streamlit/App.py", "Streamlit"),
]

hidden_imports = [
    # Streamlit core
    "streamlit",
    "streamlit.web.cli",
    "streamlit.runtime",
    "streamlit.components.v1",
    # Data
    "pandas",
    "numpy",
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    # OR-Tools
    "ortools",
    "ortools.sat",
    "ortools.sat.python",
    "ortools.sat.python.cp_model",
    # PDF export
    "fpdf",
    "fpdf.fpdf",
    # SQLAlchemy / Alembic
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "alembic",
    # FastAPI / Uvicorn
    "fastapi",
    "uvicorn",
    "uvicorn.main",
    "uvicorn.config",
    # Auth
    "jose",
    "jose.jwt",
    "passlib",
    "passlib.context",
    # Pydantic
    "pydantic",
    "pydantic.v1",
    # HTTP
    "requests",
    "httpx",
    # Misc
    "multipart",
    "python_multipart",
    "anyio",
    "starlette",
]

collect_all = [
    "streamlit",
    "altair",
    "pandas",
    "ortools",
    "fpdf",
]

args = [
    "run_app.py",
    f"--name=ASCS_Scheduler",
    "--onefile",
    "--windowed",
    "--icon=NONE",
    "--log-level=WARN",
]

for src, dst in datas:
    args.append(f"--add-data={src}{os.pathsep}{dst}")

for hi in hidden_imports:
    args.append(f"--hidden-import={hi}")

for pkg in collect_all:
    args.append(f"--collect-all={pkg}")

if __name__ == "__main__":
    print("Building ASCS_Scheduler executable...")
    print(f"Args:\n  " + "\n  ".join(args))
    PyInstaller.__main__.run(args)
    print("\nBuild complete. Check the dist/ folder.")
