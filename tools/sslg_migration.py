from hashlib import sha256 as file_hash
from pathlib import Path, PurePosixPath
import json
import ntpath


def sha256(path: Path) -> str:
    digest = file_hash()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> bool:
    if not value or "\\" in value or ntpath.splitdrive(value)[0]:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


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
