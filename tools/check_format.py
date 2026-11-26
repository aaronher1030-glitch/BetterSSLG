"""Check a generated SSLG document against the house format baseline.

Two layers run independently so a failure names its own cause:

  docx layer  - the markup: fonts, letterhead parts, field order, alignment choices
  pdf  layer  - the rendered page: stretched lines, overflow, content cut by a page break

Usage:
    python -X utf8 tools/check_format.py <file.docx> [<file.pdf>] [--kind memorandum] [--json]

Exit code is 1 when any rule fails, so a build can be gated on it.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from types import SimpleNamespace

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import format_spec as spec

NUMBERED = re.compile(r"^\s*(\d+)\.\s")
# THRU: belongs to the routing block of a proposal, so its value sits on the same column.
FIELD_LABELS = ("TO:", "THRU:", "FROM:", "SUBJECT:", "DATE:")
# A section heading is a number or letter on a tab stop: "I.\tACTIVITY TITLE:".
ENUMERATOR = re.compile(r"^(?:[IVXLC]+|[A-Z]|\d+)\.$")
BULLET = re.compile(r"^[\u2022\u25aa\u25e6\u00b7\uf0b7\u2043-]$")
PAGE_NUMBER = re.compile(r"^Page \d+ of \d+$")
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


class Result:
    def __init__(self, layer, rule, status, detail=""):
        self.layer, self.rule, self.status, self.detail = layer, rule, status, detail

    def as_dict(self):
        return {"layer": self.layer, "rule": self.rule, "status": self.status, "detail": self.detail}


def _para_texts(document_xml):
    return ["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
            for p in re.findall(r"<w:p[ >].*?</w:p>", document_xml, re.S)]


def _part_text(raw):
    # Runs are contiguous: a word split across runs must not gain a space ("Bonifacio"
    # in two runs), while breaks, tabs and paragraph boundaries separate words and must.
    text = re.sub(r"<w:(?:br|cr|tab)\b[^>]*/>", " ", raw.decode("utf-8", "ignore"))
    paras = ["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
             for p in re.findall(r"<w:p[ >].*?</w:p>", text, re.S)]
    return re.sub(r"\s+", " ", " ".join(paras).replace("\u00a0", " "))


def check_docx(path):
    out = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if "word/document.xml" not in names:
            return [Result("docx", "package readable", FAIL, "word/document.xml missing")]
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
        # Word silently truncates the export when a part is malformed, so parse before
        # trusting any geometry measured from the render.
        bad_xml = []
        for n in names:
            if n.startswith("word/") and n.endswith(".xml"):
                try:
                    ET.fromstring(z.read(n))
                except ET.ParseError as exc:
                    bad_xml.append(f"{n}: {exc}")
        header_text = " ".join(_part_text(z.read(n)) for n in names
                               if re.match(r"word/header\d+\.xml$", n))
        footer_text = " ".join(_part_text(z.read(n)) for n in names
                               if re.match(r"word/footer\d+\.xml$", n))

    out.append(Result("docx", "package XML is well-formed",
                      FAIL if bad_xml else PASS, "; ".join(bad_xml)))
    fonts = set(re.findall(r'<w:rFonts w:ascii="([^"]+)"', xml))
    # House annex tables are set condensed (received issuances use 6.5 pt) so a wide
    # matrix fits one page; the 12 pt baseline governs prose.
    prose_xml = re.sub(r"<w:tbl[ >].*?</w:tbl>", "", xml, flags=re.S)
    sizes = set(re.findall(r'<w:sz w:val="(\d+)"', prose_xml))
    out.append(Result("docx", "body font is " + spec.FONT_NAME,
                      PASS if fonts == {spec.FONT_NAME} else FAIL,
                      "found: " + (", ".join(sorted(fonts)) or "none declared")))
    out.append(Result("docx", "body size is 12 pt",
                      PASS if sizes == {str(spec.FONT_SIZE_HALFPOINTS)} else FAIL,
                      "found half-points: " + (", ".join(sorted(sizes)) or "none declared")))

    missing_h = [line for line in spec.HEADER_LINES if line not in header_text]
    out.append(Result("docx", "BSANHS letterhead present",
                      FAIL if missing_h or not header_text else PASS,
                      "missing: " + ", ".join(missing_h) if missing_h else ""))
    missing_f = [m for m in spec.FOOTER_MARKERS if m not in footer_text]
    out.append(Result("docx", "address and motto footnote present",
                      FAIL if missing_f or not footer_text else PASS,
                      "missing: " + ", ".join(missing_f) if missing_f else ""))

    paras = [p.strip() for p in _para_texts(xml) if p.strip()]
    joined = "\n".join(paras)
    for kind, labels in spec.FIELD_ORDER.items():
        if labels[0].title().lower() in joined.lower() or (kind == "memorandum" and "MEMORANDUM" in joined):
            positions = [next((i for i, p in enumerate(paras) if p.upper().startswith(lab.upper())), None)
                         for lab in labels]
            if all(p is not None for p in positions):
                ok = positions == sorted(positions)
                out.append(Result("docx", f"field order ({kind})", PASS if ok else FAIL,
                                  "" if ok else f"{labels} found at {positions}"))
            break
    else:
        out.append(Result("docx", "field order", SKIP, "document kind not recognised"))

    # Justified text holding a URL or e-mail is the classic stretched-line tell.
    bad = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))
        if re.search(spec.UNBREAKABLE_TOKEN, text) and '<w:jc w:val="both"' in p:
            bad.append(text[:60])
    out.append(Result("docx", "no justified paragraph holds a URL or e-mail",
                      FAIL if bad else PASS, "; ".join(bad)))

    # Justified cell text stretches short last lines into rivers; the rendered-line rule
    # skips table regions, so this markup rule is the gate for cell alignment.
    justified_cells = []
    for cell in re.findall(r"<w:tc[ >].*?</w:tc>", xml, re.S):
        if '<w:jc w:val="both"' in cell:
            justified_cells.append("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", cell))[:60])
    out.append(Result("docx", "table cells are not justified",
                      FAIL if justified_cells else PASS, "; ".join(justified_cells[:4])))

    sig_positions = [next((i for i, p in enumerate(paras) if p.lower().startswith(s.lower())), None)
                     for s in spec.SIGNATURE_ORDER]
    present = [(s, i) for s, i in zip(spec.SIGNATURE_ORDER, sig_positions) if i is not None]
    if present:
        out.append(Result("docx", "signature block order",
                          PASS if [i for _, i in present] == sorted(i for _, i in present) else FAIL,
                          " ".join(s for s, _ in present)))
    else:
        out.append(Result("docx", "signature block order", SKIP, "no signature labels found"))

    # Two-column header: every field paragraph carries the value tab stop, and the block
    # closes with a rule under DATE.
    tab = f'<w:tab w:val="left" w:pos="{spec.LABEL_TAB_STOP_TWIPS}"/>'
    field_paras = [p for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
                   if re.match(r"^\s*(TO:|FROM:|DATE:)", "".join(
                       re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip(), re.I)]
    no_tab = ["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))[:20]
              for p in field_paras if tab not in p]
    out.append(Result("docx", f"header values sit on the {spec.LABEL_TAB_STOP_TWIPS}-twip tab stop",
                      FAIL if no_tab or not field_paras else PASS,
                      "missing tab stop: " + "; ".join(no_tab) if no_tab
                      else ("" if field_paras else "no field paragraphs found")))
    date_para = next((p for p in field_paras if re.match(r"^\s*DATE:", "".join(
        re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip(), re.I)), "")
    out.append(Result("docx", f"rule under {spec.HEADER_RULE_AFTER}",
                      PASS if "<w:bottom" in date_para and "pBdr" in date_para else FAIL))

    # Each numbered list restarts at 1 (the contest mechanics of a proposal are three
    # separate lists), so a reset opens a new run instead of counting as a gap.
    numbers = [int(m.group(1)) for p in paras if (m := NUMBERED.match(p))]
    runs_ok, expect = True, 1
    for n in numbers:
        if n == 1:
            expect = 2
        elif n == expect:
            expect += 1
        else:
            runs_ok = False
            break
    out.append(Result("docx", "numbered paragraphs run 1..n without gaps",
                      PASS if runs_ok else FAIL,
                      f"found: {numbers}" if numbers else "none"))
    return out


def _in_table(tables, y):
    """Table typography is gated at the docx layer (cells must not be justified), so the
    rendered-line river rule skips table regions: column gaps there are geometry, not prose."""
    return any(t.bbox[1] - 8 <= y <= t.bbox[3] + 2 for t in tables)


def _grid_regions(page):
    """Table regions from the drawn rules themselves.

    MuPDF's table finder needs a complete cell grid and silently returns nothing for some
    frames (and for the rule-drawn fixtures here), so collect horizontal rules crossed by
    two or more vertical rules; their union is the table region.
    """
    horiz, vert = [], []
    for drawing in page.get_drawings():
        for item in drawing["items"]:
            if item[0] == "l":
                a, b = item[1], item[2]
                if abs(a.y - b.y) < 0.6 and abs(a.x - b.x) > 2:
                    horiz.append((min(a.x, b.x), max(a.x, b.x), (a.y + b.y) / 2))
                elif abs(a.x - b.x) < 0.6 and abs(a.y - b.y) > 2:
                    vert.append((min(a.y, b.y), max(a.y, b.y), (a.x + b.x) / 2))
            elif item[0] == "re":
                r = item[1]
                if r.height <= 1.5 and r.width > 2:
                    horiz.append((r.x0, r.x1, (r.y0 + r.y1) / 2))
                elif r.width <= 1.5 and r.height > 2:
                    vert.append((r.y0, r.y1, (r.x0 + r.x1) / 2))
    regions = []
    for x0, x1, y in horiz:
        crossing = [v for v in vert
                    if x0 - 0.5 <= v[2] <= x1 + 0.5 and v[0] - 0.5 <= y <= v[1] + 0.5]
        if len(crossing) >= 2:
            regions.append((min([x0] + [v[2] for v in crossing]), min(v[0] for v in crossing),
                            max([x1] + [v[2] for v in crossing]), max(v[1] for v in crossing)))
    merged = []
    for r in regions:
        for i, m in enumerate(merged):
            if not (r[2] < m[0] - 1 or r[0] > m[2] + 1 or r[3] < m[1] - 1 or r[1] > m[3] + 1):
                merged[i] = (min(m[0], r[0]), min(m[1], r[1]), max(m[2], r[2]), max(m[3], r[3]))
                break
        else:
            merged.append(r)
    return [SimpleNamespace(bbox=m) for m in merged]


def _lines(pdf_path):
    """Visual lines: pymupdf splits one printed line across blocks, so merge by y."""
    import pymupdf
    raw = []
    tables_by_page = {}
    with pymupdf.open(str(pdf_path)) as doc:
        for page_no, page in enumerate(doc):
            tables_by_page[page_no + 1] = list(page.find_tables().tables) + _grid_regions(page)
            page_words = page.get_text("words")
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    text = "".join(s["text"] for s in line["spans"]).strip()
                    if not text:
                        continue
                    raw.append({"page": page_no + 1, "y": round(line["bbox"][1], 1),
                                "text": text, "x0": line["bbox"][0], "x1": line["bbox"][2],
                                "page_w": page.rect.width, "page_h": page.rect.height,
                                "size": max(s["size"] for s in line["spans"]),
                                "words": [(round(w[0], 1), round(w[2], 1), w[4]) for w in page_words
                                          if abs(w[1] - line["bbox"][1]) < 3]})
    merged = {}
    for r in raw:
        key = (r["page"], r["y"])
        if key not in merged:
            merged[key] = {"page": r["page"], "y": r["y"], "text": r["text"],
                           "x0": r["x0"], "x1": r["x1"], "size": r["size"],
                           "page_w": r["page_w"], "page_h": r["page_h"],
                           "words": r["words"]}
        else:
            m = merged[key]
            m["text"] += " " + r["text"]
            m["x0"], m["x1"], m["size"] = min(m["x0"], r["x0"]), max(m["x1"], r["x1"]), max(m["size"], r["size"])
            # Two raw lines at one height each pull in the same nearby words; counting them
            # twice would hide the very gaps this rule looks for.
            m["words"] = sorted(set(m["words"] + r["words"]))
    lines = sorted(merged.values(), key=lambda l: (l["page"], l["y"], l["x0"]))
    for line in lines:
        ws = sorted(line["words"])
        gaps = []
        line["table"] = _in_table(tables_by_page.get(line["page"], []), line["y"])
        if not line["table"]:
            for i in range(len(ws) - 1):
                # The label-to-value tab jump is a deliberate column, not a justification
                # river; merged lines pull the label word into the value line's word set.
                if ws[i][2] in FIELD_LABELS and \
                        ws[i + 1][0] >= spec.VALUE_COLUMN_PT - spec.COLUMN_TOLERANCE_PT:
                    continue
                # "I.\tACTIVITY TITLE:" is a heading, not a stretched body line.
                if ENUMERATOR.match(ws[i][2]):
                    continue
                # A bullet sits on its own tab stop; the gap to its text is the hang.
                if BULLET.match(ws[i][2]):
                    continue
                gaps.append(round(ws[i + 1][0] - ws[i][1], 1))
        line["gaps"] = gaps
    return lines


def _norm(text):
    """Rendered text loses the spaces between letterhead spans; compare on letters only."""
    return re.sub(r"[^0-9A-Z]", "", text.upper())


def _is_furniture(text):
    """Letterhead, footnote and page-number lines are styled apart from the body; body rules skip them."""
    if PAGE_NUMBER.match(text.strip()):
        return True
    norm = _norm(text)
    markers = spec.HEADER_LINES + spec.FOOTER_MARKERS
    return any(_norm(m) in norm for m in markers) or bool(
        re.search(r"SCHOOL YEAR|ADDRESS:|TELEPHONE|EMAIL", text.upper()))


def _footer_top(lines):
    """The address box wraps, so one of its lines ("Concepcion, Tarlac") carries no marker
    of its own. Anchor the block on its first line and treat everything at or below it as
    furniture, which also holds on the shorter landscape annex."""
    tops = {}
    for line in lines:
        if re.search(r"ADDRESS:", line["text"], re.I):
            tops[line["page"]] = min(tops.get(line["page"], 1e9), line["y"])
    return {page: y - 2 for page, y in tops.items()}


def _signature_top(lines):
    """Signature blocks are borderless tables: their column gaps are layout, not
    justification rivers, and the block is checked by its own rule."""
    label = re.compile(r"^(?:Prepared by|Reviewed and Evaluated by|Concurred|Noted by|"
                       r"Submitted by|Recommending Approval|Approved by):", re.I)
    tops = {}
    for line in lines:
        if label.match(line["text"].strip()):
            tops[line["page"]] = min(tops.get(line["page"], 1e9), line["y"])
    return tops


def _right_edge(line):
    """The right text edge follows the page width, so a landscape annex is measured against
    its own margin rather than the portrait one."""
    margin = 612.0 - spec.RIGHT_TEXT_EDGE_PT
    return line["page_w"] - margin


def check_pdf(path):
    out = []
    lines = _lines(path)
    if not lines:
        return [Result("pdf", "text layer", FAIL, "no extractable text - is this a scan?")]
    footer_top = _footer_top(lines)
    body = [l for l in lines
            if not _is_furniture(l["text"])
            and l["y"] < footer_top.get(l["page"], 1e9)]
    sig_top = _signature_top(lines)

    gaps = [max(l["gaps"]) for l in body
            if l["gaps"] and l["y"] < sig_top.get(l["page"], 1e9)]
    median = sorted(gaps)[len(gaps) // 2] if gaps else 0.0
    limit = max(spec.MAX_WORD_GAP, spec.WORD_GAP_MULTIPLIER * median)
    stretched = [f"p{l['page']} y{l['y']:.0f} gap {max(l['gaps']):.0f}pt vs median {median:.0f}pt: {l['text'][:44]}"
                 for l in body if l["gaps"] and max(l["gaps"]) > limit
                 and l["y"] < sig_top.get(l["page"], 1e9)]
    out.append(Result("pdf", "no stretched justified lines",
                      FAIL if stretched else PASS, f"limit {limit:.0f}pt | " + " | ".join(stretched[:4])))

    overflow = []
    for l in body:
        edge = _right_edge(l)
        limit = edge + spec.RIGHT_EDGE_TOLERANCE
        # Word hangs trailing punctuation outside the margin by one glyph.
        if l["text"].rstrip()[-1:] in ",.;:":
            limit = edge + spec.PUNCTUATION_OVERHANG_PT
        if l["x1"] > limit:
            overflow.append(f"p{l['page']} y{l['y']:.0f} ends {l['x1']:.0f}pt: {l['text'][:48]}")
    out.append(Result("pdf", f"nothing past the {spec.RIGHT_TEXT_EDGE_PT:.0f} pt text edge",
                      FAIL if overflow else PASS, " | ".join(overflow[:4])))

    small = sorted({round(l["size"], 1) for l in body
                    if not l["table"] and l["size"] < spec.MIN_BODY_FONT_SIZE})
    out.append(Result("pdf", "no undersized body text", FAIL if small else PASS,
                      f"pt sizes: {small}" if small else ""))

    pages = sorted({l["page"] for l in lines})
    school = _norm(spec.HEADER_LINES[4])
    no_head = [n for n in pages
               if school not in "".join(_norm(l["text"]) for l in lines if l["page"] == n)]
    out.append(Result("pdf", "letterhead on every page", FAIL if no_head else PASS,
                      f"absent on pages {no_head}" if no_head else ""))

    # Field labels on the margin, their values on one column. A table row that happens to
    # begin with "Date:" is not a routing field: the label must start at the label column.
    misaligned = []
    for line in lines:
        text = line["text"]
        if line["table"] or abs(line["x0"] - spec.LABEL_COLUMN_PT) > spec.COLUMN_TOLERANCE_PT:
            continue
        hit = next((l for l in FIELD_LABELS if text.upper().startswith(l)), None)
        if not hit:
            continue
        after = [w for w in line["words"] if w[0] > spec.LABEL_COLUMN_PT + 20]
        if not after:
            continue
        x = min(w[0] for w in after)
        if abs(x - spec.VALUE_COLUMN_PT) > spec.COLUMN_TOLERANCE_PT:
            misaligned.append(f"{hit} value starts at {x:.0f}pt, not {spec.VALUE_COLUMN_PT:.0f}pt")
    out.append(Result("pdf", "field values share one column",
                      FAIL if misaligned else PASS, "; ".join(misaligned)))

    # A paragraph is cut by the page break when a marker is stranded at the foot of the
    # page and its text opens the next one.
    marker_only = re.compile(r"^(?:[\u2022\u25aa\u25e6\uf0b7-]|\d{1,2}\.|[A-Za-z]\.)$")
    splits = []
    for n in pages:
        last = [l for l in body if l["page"] == n]
        first = [l for l in body if l["page"] == n + 1]
        if not last or not first:
            continue
        # Table rows are atomic, and whatever follows a table on the next page is a new
        # block, never the remainder of a row: a table ending the page is not a cut paragraph.
        if last[-1].get("table"):
            continue
        # Ordinary prose flows across a page break; the defect is a marker stranded at the
        # foot of the page, or a short line left behind while its sentence continues overleaf.
        foot = last[-1]
        if any(l is not foot and abs(l["y"] - foot["y"]) <= 4 for l in last):
            continue
        width = _right_edge(foot) - spec.LEFT_TEXT_EDGE_PT
        stranded = marker_only.match(foot["text"].strip()) or (
            foot["x1"] - foot["x0"] < 0.25 * width
            and first[0]["text"].strip()[:1].islower())
        if not stranded:
            continue
        splits.append(f"p{n} ends with '{foot['text'][:38]}' alone; "
                      f"p{n + 1} opens with '{first[0]['text'][:38]}'")
    out.append(Result("pdf", "no paragraph cut across a page break",
                      FAIL if splits else PASS, "; ".join(splits)))

    sig_breaks = []
    for i, line in enumerate(lines):
        for label in spec.SIGNATURE_ORDER:
            if line["text"].lower().startswith(label.lower()):
                following = lines[i + 1] if i + 1 < len(lines) else None
                if following and following["page"] != line["page"]:
                    sig_breaks.append(f"{label} on p{line['page']}, its name on p{following['page']}")
    out.append(Result("pdf", "signature label kept with its name",
                      FAIL if sig_breaks else PASS, "; ".join(sig_breaks)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check SSLG documents against the house format.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="print failures only")
    args = ap.parse_args(argv)

    all_results = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            all_results.append([Result(path.suffix.lstrip("."), "file found", FAIL, str(path))])
            continue
        if path.suffix.lower() == ".docx":
            all_results.append(check_docx(path))
        elif path.suffix.lower() == ".pdf":
            all_results.append(check_pdf(path))
        else:
            all_results.append([Result(path.suffix, "supported file", SKIP, "use .docx or .pdf")])

    failed = [r for group in all_results for r in group if r.status == FAIL]
    if args.json:
        print(json.dumps([r.as_dict() for group in all_results for r in group], indent=2, ensure_ascii=False))
    else:
        for group in all_results:
            for r in group:
                if args.quiet and r.status != FAIL:
                    continue
                print(f"[{r.status}] {r.layer}: {r.rule}" + (f"\n        {r.detail}" if r.detail else ""))
        print(f"\n{len(failed)} failing rule(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
