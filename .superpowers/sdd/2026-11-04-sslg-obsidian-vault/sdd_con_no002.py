import zipfile, re, json, glob, os
ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
def flat(f):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", zipfile.ZipFile(f).read("word/document.xml").decode("utf-8", "replace")))
V = json.load(open("90 Archive/File Manifest.json", encoding="utf-8"))
print("=== files per ECOLEAD No.002 record + printed number/date ===")
for f in V["files"]:
    if f["record_key"] == "om-sslg-2026-002-ecolead":
        cp = f["current_path"]
        t = flat(cp) if cp.lower().endswith(".docx") else ""
        print("  %-9s %-56s printed=%s date=%s" % (f["role"], os.path.basename(cp),
              re.findall(r"No\.\s*(\d+),\s*s\.\s*2026", t)[:2], re.findall(r"DATE:\s*([A-Za-z0-9 ,]+2026)", t)[:1]))
print()
print("=== survey-aug27 file group ===")
n = [f for f in V["files"] if f["record_key"] == "om-sslg-2026-002-survey-aug27"]
print("  count", len(n))
for f in n:
    print("   %-9s %s" % (f["role"], f["current_path"]))
print()
print("=== vault-wide DOCX printing 'No. 002, s. 2026' ===")
seen = {}
skip = ("Scheduler_v1", ".superpowers", os.path.join("docs", "superpowers"))
for f in glob.glob("**/*.docx", recursive=True):
    if any(s in f for s in skip):
        continue
    try:
        t = flat(f)
    except Exception:
        continue
    if re.search(r"No\.\s*002,\s*s\.\s*2026", t):
        d = re.findall(r"DATE:\s*([A-Za-z0-9 ,]+2026)", t)[:1]
        subj = "ECOLEAD" if re.search(r"(?i)ecolead", t) else ("SURVEY" if re.search(r"(?i)digital device", t) else "OTHER")
        seen.setdefault((subj, d[0] if d else "?"), []).append(os.path.basename(f))
for k, v in sorted(seen.items()):
    print("  ", k, "->", len(v), "copies:", v[:4])
