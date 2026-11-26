"""Rebuild the derived vault layer from tools/sslg_content.json.

Deletes exactly the manifest-declared note/hub paths plus NAVIGATION_PATHS, then
regenerates them, then rewrites the delivered File Manifest and Archive Index.
Proves that nothing outside the declared set changed, by hashing the whole vault
before and after (originals, Scheduler and docs excluded from the claim by design:
they must be byte-identical).
"""
import hashlib
import json
from pathlib import Path

from tools.sslg_migration import write_archive_index, write_manifest
from tools.sslg_navigation import NAVIGATION_PATHS, generate_navigation
from tools.sslg_notes import generate_notes

ROOT = Path(__file__).resolve().parents[3]
SKIP_TREES = {"Scheduler_v1-main", "docs", ".superpowers", "tools", ".git"}


def snapshot():
    digests = {}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.split("/")[0] in SKIP_TREES or "__pycache__" in relative:
            continue
        digests[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def declared(data):
    paths = {record["note_path"] for record in data["records"]}
    paths.update(activity["hub_path"] for activity in data["activities"])
    paths.update(NAVIGATION_PATHS)
    paths.add("90 Archive/File Manifest.json")
    paths.add("90 Archive/Archive Index.md")
    return sorted(paths)


def main():
    data = json.loads((ROOT / "tools" / "sslg_content.json").read_text(encoding="utf-8"))
    targets = declared(data)
    before = snapshot()
    removed = 0
    for relative in targets:
        path = ROOT / relative
        if path.exists():
            path.unlink()
            removed += 1
    print(f"removed {removed} of {len(targets)} declared derived files")
    write_manifest(ROOT, data)
    write_archive_index(ROOT, data["files"])
    notes = generate_notes(ROOT, data)
    navigation = generate_navigation(ROOT, data)
    print(f"regenerated notes {len(notes)} navigation {len(navigation)}")
    after = snapshot()
    changed = {p for p, h in after.items() if before.get(p) != h} | {p for p in before if p not in after}
    allowed = set(targets)
    unexpected = sorted(changed - allowed)
    print(f"changed {len(changed)} files; outside the declared set: {len(unexpected)}")
    for path in unexpected[:20]:
        print("   UNEXPECTED:", path)
    if unexpected:
        raise SystemExit("rebuild touched undeclared files")


if __name__ == "__main__":
    main()
