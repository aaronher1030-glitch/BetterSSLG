### Task 1: Checksummed Migration Engine

**Files:**
- Create: `tools/sslg_migration.py`
- Create: `tools/tests/test_sslg_migration.py`

**Interfaces:**
- Consumes: the existing vault root and a `files` list whose entries contain `key`, `original_path`, `current_path`, `sha256`, `role`, and optional `record_key`.
- Produces: `sha256(path: Path) -> str`, `collect_baseline(root: Path) -> list[str]`, `preflight_moves(root: Path, files: list[dict]) -> list[str]`, `apply_moves(root: Path, files: list[dict]) -> None`, `write_manifest(root: Path, data: dict) -> None`, and `write_archive_index(root: Path, files: list[dict]) -> None`.

- [ ] **Step 1: Write failing preservation and collision tests**

```python
import json
import tempfile
import unittest
from pathlib import Path

from tools.sslg_migration import apply_moves, collect_baseline, preflight_moves, sha256


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "source.docx").write_bytes(b"original-docx")
        (self.root / "_DUPLICATES_TO_DELETE").mkdir()
        (self.root / "_DUPLICATES_TO_DELETE" / "copy.pdf").write_bytes(b"copy-pdf")
        (self.root / "OM_SSLG_2026_001").mkdir()
        (self.root / "OM_SSLG_2026_001" / "page.png").write_bytes(b"png")
        (self.root / "Scheduler_v1-main").mkdir()
        (self.root / "Scheduler_v1-main" / "App.py").write_text("unchanged", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def entry(self, **overrides):
        value = {
            "key": "source-docx",
            "original_path": "source.docx",
            "current_path": "02 Activities/Example/Sources/source.docx",
            "sha256": sha256(self.root / "source.docx"),
            "role": "primary",
            "record_key": "example-record",
        }
        value.update(overrides)
        return value

    def test_baseline_includes_only_sslg_source_and_staging_files(self):
        self.assertEqual(
            collect_baseline(self.root),
            ["OM_SSLG_2026_001/page.png", "_DUPLICATES_TO_DELETE/copy.pdf", "source.docx"],
        )

    def test_move_preserves_bytes_and_records_original_hash(self):
        files = [self.entry()]
        self.assertEqual(preflight_moves(self.root, files), [])
        apply_moves(self.root, files)
        destination = self.root / files[0]["current_path"]
        self.assertEqual(destination.read_bytes(), b"original-docx")
        self.assertEqual(sha256(destination), files[0]["sha256"])
        self.assertFalse((self.root / "source.docx").exists())

    def test_preflight_rejects_existing_destination_and_bad_hash(self):
        collision = self.entry()
        destination = self.root / collision["current_path"]
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"do-not-overwrite")
        bad_hash = self.entry(sha256="0" * 64)
        errors = preflight_moves(self.root, [collision, bad_hash])
        self.assertTrue(any("destination exists" in error for error in errors))
        self.assertTrue(any("checksum mismatch" in error for error in errors))
        self.assertEqual(destination.read_bytes(), b"do-not-overwrite")

    def test_preflight_rejects_path_escape_and_duplicate_destinations(self):
        escape = self.entry(current_path="../outside.docx")
        first = self.entry(key="first")
        second = self.entry(key="second", original_path="_DUPLICATES_TO_DELETE/copy.pdf")
        second["current_path"] = first["current_path"]
        second["sha256"] = sha256(self.root / second["original_path"])
        errors = preflight_moves(self.root, [escape, first, second])
        self.assertTrue(any("unsafe path" in error for error in errors))
        self.assertTrue(any("duplicate destination" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify the import failure**

Run: `python -m unittest tools.tests.test_sslg_migration -v`  
Expected: FAIL because `tools.sslg_migration` does not exist.

- [ ] **Step 3: Implement safe path handling, discovery, hashing, and preflight**

```python
from hashlib import sha256 as file_hash
from pathlib import Path, PurePosixPath
import json


def sha256(path: Path) -> str:
    digest = file_hash()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def collect_baseline(root: Path) -> list[str]:
    paths = []
    for path in root.iterdir():
        if path.is_file() and path.suffix.lower() in {".docx", ".pdf"}:
            paths.append(path.relative_to(root).as_posix())
    for folder in (root / "_DUPLICATES_TO_DELETE", root / "OM_SSLG_2026_001"):
        if folder.exists():
            paths.extend(
                path.relative_to(root).as_posix()
                for path in folder.rglob("*")
                if path.is_file()
            )
    return sorted(paths)


def preflight_moves(root: Path, files: list[dict]) -> list[str]:
    errors = []
    destinations = set()
    for entry in files:
        original = entry["original_path"]
        current = entry["current_path"]
        if not safe_relative(original) or not safe_relative(current):
            errors.append(f"unsafe path: {entry['key']}")
            continue
        source = root / original
        destination = root / current
        if current in destinations:
            errors.append(f"duplicate destination: {current}")
        destinations.add(current)
        if not source.is_file():
            errors.append(f"missing source: {original}")
            continue
        if sha256(source) != entry["sha256"]:
            errors.append(f"checksum mismatch: {original}")
        if original != current and destination.exists():
            errors.append(f"destination exists: {current}")
    return sorted(errors)
```

- [ ] **Step 4: Implement reversible moves and deterministic audit output**

```python
def apply_moves(root: Path, files: list[dict]) -> None:
    errors = preflight_moves(root, files)
    if errors:
        raise ValueError("Move preflight failed:\n" + "\n".join(errors))
    moved = []
    try:
        for entry in files:
            if entry["original_path"] == entry["current_path"]:
                continue
            source = root / entry["original_path"]
            destination = root / entry["current_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
            moved.append((source, destination))
            if sha256(destination) != entry["sha256"]:
                raise IOError(f"post-move checksum mismatch: {destination}")
    except Exception as error:
        rollback_errors = []
        for source, destination in reversed(moved):
            try:
                if source.exists():
                    raise IOError(f"rollback destination exists: {source}")
                source.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(source)
            except Exception as rollback_error:
                rollback_errors.append(str(rollback_error))
        message = f"Move failed and rollback was attempted: {error}"
        if rollback_errors:
            message += "; rollback errors: " + "; ".join(rollback_errors)
        raise RuntimeError(message) from error


def write_manifest(root: Path, data: dict) -> None:
    destination = root / "90 Archive" / "File Manifest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_archive_index(root: Path, files: list[dict]) -> None:
    destination = root / "90 Archive" / "Archive Index.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    lines = [
        "# Archive Index",
        "",
        "All material is preserved. SHA-256 values identify the original bytes.",
        "",
        "| Role | Original path | Current path | Record | SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for entry in sorted(files, key=lambda item: (item["role"], item["original_path"])):
        lines.append(
            f"| {entry['role']} | {entry['original_path']} | {entry['current_path']} "
            f"| {entry.get('record_key', '')} | `{entry['sha256']}` |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 5: Run migration tests and record Checkpoint 1**

Run: `python -m unittest tools.tests.test_sslg_migration -v`  
Expected: all migration tests PASS; the fixture proving collision refusal remains unchanged. Do not run migration against the real vault yet.

---
