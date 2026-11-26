"""Shared read-only extraction helpers for the final review (Part E)."""
import re
import subprocess
import zipfile
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def h(p: Path) -> str:
    d = sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            d.update(c)
    return d.hexdigest()


def docx_paragraphs(p: Path):
    with zipfile.ZipFile(p) as z:
        tree = ET.fromstring(z.read("word/document.xml"))
    out = []
    for para in tree.findall(".//w:p", NS):
        t = "".join(n.text or "" for n in para.findall(".//w:t", NS)).strip()
        if t:
            out.append(t)
    return out


def docx_text(p: Path) -> str:
    return "\n".join(docx_paragraphs(p))


def docx_media(p: Path):
    with zipfile.ZipFile(p) as z:
        return sorted(n for n in z.namelist() if n.startswith("word/media/"))


def pdf_page_objects(p: Path) -> int:
    raw = p.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", raw))


def pdf_pages_pandas(p: Path):
    """page count by counting 'Pages:' with pdftotext metadata is unavailable; use trailer scan"""
    raw = p.read_bytes()
    m = re.findall(rb"/Count\s+(\d+)", raw)
    return [int(x) for x in m]


def pdftotext(p: Path) -> str:
    out = subprocess.run(["pdftotext", str(p), "-"], capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def pdf_formfeed_pages(p: Path) -> int:
    return pdftotext(p).count("\f")
