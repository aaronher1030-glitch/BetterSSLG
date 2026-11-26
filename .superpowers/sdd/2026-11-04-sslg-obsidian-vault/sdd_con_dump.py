import json, os, re, hashlib, zipfile
ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
OUT = open(r".superpowers/sdd/2026-11-04-sslg-obsidian-vault/sdd_con_dump.txt", "w", encoding="utf-8")

def docx_paras(p):
    xml = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8", "replace")
    out = []
    for pm in re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", xml, re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", pm, re.S))
        t = re.sub(r"<[^>]+>", "", t).replace("&amp;", "&").replace("&#8217;", "\u2019")
        t = re.sub(r"\s+", " ", t).strip()
        if t: out.append(t)
    return out

def w(s=""): OUT.write(str(s) + "\n")

targets_docx = [
 "03 Governance/Sources/OM_SSLG_2026_001.docx",
 "03 Governance/Sources/OM_SSLG_2026_001 (8).docx",
 "03 Governance/Sources/OM_SSLG_2026_001 (5).docx",
 "90 Archive/Revisions/OM_SSLG_2026_001_VP.docx",
 "90 Archive/Revisions/OM_SSLG_2026_001 (1).docx",
 "90 Archive/Revisions/OM_SSLG_2026_001 (4).docx",
 "90 Archive/Duplicates/OM_SSLG_2026_001 (3).docx",
 "03 Governance/Sources/SSLG_Governance_Memorandum_OM-SSLG-IA-2026-001.docx",
 "02 Activities/Project ECOLEAD/Sources/OM_SSLG_2026_002 (7).docx",
 "90 Archive/Revisions/OM_SSLG_2026_002 (8).docx",
 "02 Activities/Project ECOLEAD/Sources/OM_SSLG_2026_002.docx",
 "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002 (3).docx",
 "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002 (6).docx",
 "02 Activities/Project ECOLEAD/Sources/AP_SSLG_2026_002.docx",
 "02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD_proofread.docx",
]
for p in targets_docx:
    w("\n=========== DOCX %s  exists=%s" % (p, os.path.exists(p)))
    if not os.path.exists(p): continue
    ps = docx_paras(p)
    w("   paras=%d  sha=%s" % (len(ps), hashlib.sha256(open(p,"rb").read()).hexdigest()[:16]))
    for i, t in enumerate(ps):
        w("   [%d] %s" % (i, t[:230]))

def pdftext(p, extra=[]):
    import subprocess
    r = subprocess.run(["pdftotext"] + extra + [p, "-"], capture_output=True)
    return r.stdout.decode("utf-8", "replace")

targets_pdf = [
 "04 External Memoranda/Sources/Memorandum-OM-NFSSLG-2026-001_signed-2.pdf",
 "90 Archive/Revisions/Memorandum-OM-NFSSLG-2026-001_signed-2-merged.pdf",
 "90 Archive/Revisions/Memorandum-OM-NFSSLG-2026-001_signed-2-pages-deleted-compressed.pdf",
 "04 External Memoranda/Sources/OM-DFSSLG-2026-010.pdf",
 "04 External Memoranda/Sources/OM-DFSSLG-2026-003-1.pdf",
]
KEY = re.compile(r"(?i)(memorandum\s*no|series of|s\.\s*2026|august|july|june|2026|2027|school name|pursuant|division memorandum|signed|president|chairperson|secretary|treasurer|auditor|protocol|information officer|grade.level|start|rotation|rubric|consent|annex|deadline|survey|ecolead)")
for p in targets_pdf:
    w("\n=========== PDF %s exists=%s" % (p, os.path.exists(p)))
    if not os.path.exists(p): continue
    t = pdftext(p)
    w("   chars=%d lines=%d formfeeds=%d sha=%s" % (len(t), t.count("\n"), t.count("\f"), hashlib.sha256(open(p,"rb").read()).hexdigest()[:16]))
    w("   (only lines matching key terms, truncated to 160 chars)")
    n = 0
    for line in t.splitlines():
        s = line.strip()
        if s and KEY.search(s):
            w("   | " + s[:160]); n += 1
        if n > 60:
            w("   ... (truncated at 60 matching lines)"); break
OUT.close()
print("dump written")
