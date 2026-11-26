# Review package: Task 1

Workspace is not a git repository; full new-file contents are provided as the diff.

## NEW FILE: tools/sslg_migration.py
```python
   1 +from hashlib import sha256 as file_hash
   2 +from pathlib import Path, PurePosixPath
   3 +import json
   4 +
   5 +
   6 +def sha256(path: Path) -> str:
   7 +    digest = file_hash()
   8 +    with path.open("rb") as handle:
   9 +        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
  10 +            digest.update(chunk)
  11 +    return digest.hexdigest()
  12 +
  13 +
  14 +def safe_relative(value: str) -> bool:
  15 +    path = PurePosixPath(value)
  16 +    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value
  17 +
  18 +
  19 +def collect_baseline(root: Path) -> list[str]:
  20 +    paths = []
  21 +    for path in root.iterdir():
  22 +        if path.is_file() and path.suffix.lower() in {".docx", ".pdf"}:
  23 +            paths.append(path.relative_to(root).as_posix())
  24 +    for folder in (root / "_DUPLICATES_TO_DELETE", root / "OM_SSLG_2026_001"):
  25 +        if folder.exists():
  26 +            paths.extend(
  27 +                path.relative_to(root).as_posix()
  28 +                for path in folder.rglob("*")
  29 +                if path.is_file()
  30 +            )
  31 +    return sorted(paths)
  32 +
  33 +
  34 +def preflight_moves(root: Path, files: list[dict]) -> list[str]:
  35 +    errors = []
  36 +    destinations = set()
  37 +    for entry in files:
  38 +        original = entry["original_path"]
  39 +        current = entry["current_path"]
  40 +        if not safe_relative(original) or not safe_relative(current):
  41 +            errors.append(f"unsafe path: {entry['key']}")
  42 +            continue
  43 +        source = root / original
  44 +        destination = root / current
  45 +        if current in destinations:
  46 +            errors.append(f"duplicate destination: {current}")
  47 +        destinations.add(current)
  48 +        if not source.is_file():
  49 +            errors.append(f"missing source: {original}")
  50 +            continue
  51 +        if sha256(source) != entry["sha256"]:
  52 +            errors.append(f"checksum mismatch: {original}")
  53 +        if original != current and destination.exists():
  54 +            errors.append(f"destination exists: {current}")
  55 +    return sorted(errors)
  56 +
  57 +
  58 +def apply_moves(root: Path, files: list[dict]) -> None:
  59 +    errors = preflight_moves(root, files)
  60 +    if errors:
  61 +        raise ValueError("Move preflight failed:\n" + "\n".join(errors))
  62 +    moved = []
  63 +    try:
  64 +        for entry in files:
  65 +            if entry["original_path"] == entry["current_path"]:
  66 +                continue
  67 +            source = root / entry["original_path"]
  68 +            destination = root / entry["current_path"]
  69 +            destination.parent.mkdir(parents=True, exist_ok=True)
  70 +            source.rename(destination)
  71 +            moved.append((source, destination))
  72 +            if sha256(destination) != entry["sha256"]:
  73 +                raise IOError(f"post-move checksum mismatch: {destination}")
  74 +    except Exception as error:
  75 +        rollback_errors = []
  76 +        for source, destination in reversed(moved):
  77 +            try:
  78 +                if source.exists():
  79 +                    raise IOError(f"rollback destination exists: {source}")
  80 +                source.parent.mkdir(parents=True, exist_ok=True)
  81 +                destination.rename(source)
  82 +            except Exception as rollback_error:
  83 +                rollback_errors.append(str(rollback_error))
  84 +        message = f"Move failed and rollback was attempted: {error}"
  85 +        if rollback_errors:
  86 +            message += "; rollback errors: " + "; ".join(rollback_errors)
  87 +        raise RuntimeError(message) from error
  88 +
  89 +
  90 +def write_manifest(root: Path, data: dict) -> None:
  91 +    destination = root / "90 Archive" / "File Manifest.json"
  92 +    destination.parent.mkdir(parents=True, exist_ok=True)
  93 +    if destination.exists():
  94 +        raise FileExistsError(destination)
  95 +    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
  96 +
  97 +
  98 +def write_archive_index(root: Path, files: list[dict]) -> None:
  99 +    destination = root / "90 Archive" / "Archive Index.md"
 100 +    destination.parent.mkdir(parents=True, exist_ok=True)
 101 +    if destination.exists():
 102 +        raise FileExistsError(destination)
 103 +    lines = [
 104 +        "# Archive Index",
 105 +        "",
 106 +        "All material is preserved. SHA-256 values identify the original bytes.",
 107 +        "",
 108 +        "| Role | Original path | Current path | Record | SHA-256 |",
 109 +        "|---|---|---|---|---|",
 110 +    ]
 111 +    for entry in sorted(files, key=lambda item: (item["role"], item["original_path"])):
 112 +        lines.append(
 113 +            f"| {entry['role']} | {entry['original_path']} | {entry['current_path']} "
 114 +            f"| {entry.get('record_key', '')} | `{entry['sha256']}` |"
 115 +        )
 116 +    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

## NEW FILE: tools/tests/test_sslg_migration.py
```python
   1 +import json
   2 +import tempfile
   3 +import unittest
   4 +from pathlib import Path
   5 +
   6 +from tools.sslg_migration import apply_moves, collect_baseline, preflight_moves, sha256
   7 +
   8 +
   9 +class MigrationTests(unittest.TestCase):
  10 +    def setUp(self):
  11 +        self.temp = tempfile.TemporaryDirectory()
  12 +        self.root = Path(self.temp.name)
  13 +        (self.root / "source.docx").write_bytes(b"original-docx")
  14 +        (self.root / "_DUPLICATES_TO_DELETE").mkdir()
  15 +        (self.root / "_DUPLICATES_TO_DELETE" / "copy.pdf").write_bytes(b"copy-pdf")
  16 +        (self.root / "OM_SSLG_2026_001").mkdir()
  17 +        (self.root / "OM_SSLG_2026_001" / "page.png").write_bytes(b"png")
  18 +        (self.root / "Scheduler_v1-main").mkdir()
  19 +        (self.root / "Scheduler_v1-main" / "App.py").write_text("unchanged", encoding="utf-8")
  20 +
  21 +    def tearDown(self):
  22 +        self.temp.cleanup()
  23 +
  24 +    def entry(self, **overrides):
  25 +        value = {
  26 +            "key": "source-docx",
  27 +            "original_path": "source.docx",
  28 +            "current_path": "02 Activities/Example/Sources/source.docx",
  29 +            "sha256": sha256(self.root / "source.docx"),
  30 +            "role": "primary",
  31 +            "record_key": "example-record",
  32 +        }
  33 +        value.update(overrides)
  34 +        return value
  35 +
  36 +    def test_baseline_includes_only_sslg_source_and_staging_files(self):
  37 +        self.assertEqual(
  38 +            collect_baseline(self.root),
  39 +            ["OM_SSLG_2026_001/page.png", "_DUPLICATES_TO_DELETE/copy.pdf", "source.docx"],
  40 +        )
  41 +
  42 +    def test_move_preserves_bytes_and_records_original_hash(self):
  43 +        files = [self.entry()]
  44 +        self.assertEqual(preflight_moves(self.root, files), [])
  45 +        apply_moves(self.root, files)
  46 +        destination = self.root / files[0]["current_path"]
  47 +        self.assertEqual(destination.read_bytes(), b"original-docx")
  48 +        self.assertEqual(sha256(destination), files[0]["sha256"])
  49 +        self.assertFalse((self.root / "source.docx").exists())
  50 +
  51 +    def test_preflight_rejects_existing_destination_and_bad_hash(self):
  52 +        collision = self.entry()
  53 +        destination = self.root / collision["current_path"]
  54 +        destination.parent.mkdir(parents=True)
  55 +        destination.write_bytes(b"do-not-overwrite")
  56 +        bad_hash = self.entry(sha256="0" * 64)
  57 +        errors = preflight_moves(self.root, [collision, bad_hash])
  58 +        self.assertTrue(any("destination exists" in error for error in errors))
  59 +        self.assertTrue(any("checksum mismatch" in error for error in errors))
  60 +        self.assertEqual(destination.read_bytes(), b"do-not-overwrite")
  61 +
  62 +    def test_preflight_rejects_path_escape_and_duplicate_destinations(self):
  63 +        escape = self.entry(current_path="../outside.docx")
  64 +        first = self.entry(key="first")
  65 +        second = self.entry(key="second", original_path="_DUPLICATES_TO_DELETE/copy.pdf")
  66 +        second["current_path"] = first["current_path"]
  67 +        second["sha256"] = sha256(self.root / second["original_path"])
  68 +        errors = preflight_moves(self.root, [escape, first, second])
  69 +        self.assertTrue(any("unsafe path" in error for error in errors))
  70 +        self.assertTrue(any("duplicate destination" in error for error in errors))
  71 +
  72 +
  73 +if __name__ == "__main__":
  74 +    unittest.main()
```
