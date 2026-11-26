"""Check that every local href/src in the generated site resolves.

    python -X utf8 prototype/check_links.py
"""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"

bad = []
for page in SITE.rglob("*.html"):
    text = page.read_text(encoding="utf-8")
    for match in re.finditer(r'(?:href|src)="([^"]+)"', text):
        url = match.group(1)
        if url.startswith(("#", "http", "mailto:", "data:")):
            continue
        target = (page.parent / url.split("#")[0]).resolve()
        if not target.exists():
            bad.append((str(page.relative_to(SITE)), url))

print(f"pages: {len(list(SITE.rglob('*.html')))}")
print(f"broken refs: {len(bad)}")
for page, url in bad[:30]:
    print(f"  {page} -> {url}")
