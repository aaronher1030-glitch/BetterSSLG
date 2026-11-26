"""Final review E9b: honorific/person names + adviser/principal claims vs the record's own sources."""
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
fk = {e["key"]: e for e in data["files"]}
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def text_of(p: Path) -> str:
    if p.suffix.lower() == ".docx":
        out = []
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            for n in ["word/document.xml"] + [x for x in names if re.match(r"word/(header|footer)\d*\.xml$", x)]:
                if n in names:
                    r = ET.fromstring(z.read(n))
                    out.append("".join(t.text or "" for t in r.iter(NS + "t")))
        return "\n".join(out)
    if p.suffix.lower() == ".pdf":
        return subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")
    return ""


def norm(s):
    s = (s.replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-"))
    return re.sub(r"[^a-z0-9'. -]+", "", s.lower())


HON = re.compile(r"(?:Hon\.|Atty\.|Mr\.|Ms\.|Dr\.)\s+[A-Z][A-Za-z.\- ]{3,45}?(?=\s+(?:as|,|\s{2}|$|and|SSLG|LGCC|President|Vice|Adviser|Principal|Chair|Acting)|\n|$)")
LOOSE = re.compile(r"\b([A-Z][a-z]{2,})\s+([A-Z]\.\s+)?([A-Z][a-z]{2,})\s+(?:R|J|M|A|B|C|D|E|F|G|H|K|L|N|P|S|T|V|W|Y)\.\s+([A-Z][a-z]{2,})\b")

bad, ok = [], []
for r in data["records"]:
    t = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    body = t.split("---\n", 2)[2]
    srcn = norm("\n".join(text_of(ROOT / fk[k]["current_path"]) for k in r["source_keys"]))
    names = set()
    for rx in (HON, LOOSE):
        for m in rx.finditer(body):
            tok = (m.group(0) if rx is HON else m.group(0)).strip()
            tok = re.sub(r"\s+", " ", tok)
            if len(tok) > 4:
                names.add(tok)
    for tok in sorted(names):
        core = re.sub(r"^(Hon\.|Atty\.|Mr\.|Ms\.|Dr\.)\s*", "", tok)
        cn = norm(core)
        # a name is 'supported' if every surname-ish token appears in the source text
        parts = [p for p in re.split(r"[.\s-]+", cn) if len(p) > 2]
        hit = sum(1 for p in set(parts) if p in srcn)
        if hit == len(set(parts)) and hit:
            ok.append((r["key"], tok))
        elif hit:
            bad.append(("PARTIAL", r["key"], tok, f"{hit}/{len(set(parts))}"))
        else:
            bad.append(("MISSING", r["key"], tok, "0 tokens in source"))

print("E9b. person names asserted in record bodies: checked", len(ok) + len(bad),
      "| fully supported in that record's own sources:", len(ok))
print("   unsupported:", len(bad))
for v in bad:
    print("      ", v[0], "|", v[1], "|", v[2], "|", v[3])

print("\nE9c. 'Adviser' / 'Principal' role sentences per record vs source")
for r in data["records"]:
    t = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    body = t.split("---\n", 2)[2]
    lines = [l.strip() for l in body.splitlines() if re.search(r"adviser|principal", l, re.I)]
    if not lines:
        continue
    srcn = norm("\n".join(text_of(ROOT / fk[k]["current_path"]) for k in r["source_keys"]))
    verdict = "source mentions adviser/principal" if ("adviser" in srcn or "principal" in srcn) else "NEITHER WORD IN SOURCE TEXT"
    print(f"   [{r['key']}] {verdict}")
    for l in lines:
        print("        ", l[:150])
