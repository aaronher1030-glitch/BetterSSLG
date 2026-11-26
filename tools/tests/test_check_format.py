import unittest
import zipfile
from pathlib import Path

import pymupdf

from tools import check_format, format_spec as spec

FONT = f'<w:rFonts w:ascii="{spec.FONT_NAME}" w:hAnsi="{spec.FONT_NAME}"/>'
RPR = f"<w:rPr>{FONT}<w:sz w:val=\"24\"/></w:rPr>"
TABS = f'<w:tabs><w:tab w:val="left" w:pos="{spec.LABEL_TAB_STOP_TWIPS}"/></w:tabs>'
RULE = '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="000000"/></w:pBdr>'


def para(text, jc="left", tabs=False, rule=False, tab_after_label=False):
    ppr = f"<w:pPr>{RULE if rule else ''}{TABS if tabs else ''}<w:jc w:val=\"{jc}\"/></w:pPr>"
    label, _, rest = text.partition(":")
    runs = f"<w:r>{RPR}<w:t xml:space=\"preserve\">{text}</w:t></w:r>"
    if tab_after_label:
        runs = (f"<w:r>{RPR}<w:t xml:space=\"preserve\">{label}:</w:t></w:r>"
                f"<w:r>{RPR}<w:tab/><w:t xml:space=\"preserve\">{rest}</w:t></w:r>")
    return f"<w:p>{ppr}{runs}</w:p>"


def good_body():
    return [
        para("MEMORANDUM"),
        para("No. ____, s. 2026"),
        para("TO:VICE PRESIDENT", tabs=True, tab_after_label=True),
        para("FROM:By the Authority of the SSLG President", tabs=True, tab_after_label=True),
        para("SUBJECT:"),
        para("A SURVEY"),
        para("DATE:NOVEMBER 5, 2026", tabs=True, rule=True, tab_after_label=True),
        para("1. First paragraph.", jc="both"),
        para("2. See https://example.com for details."),
        para("Prepared by:"),
        para("AARON Y. HERNANDEZ"),
        para("Reviewed and Evaluated by:"),
        para("AARON KHRISTIAN T. BANAG"),
        para("Concurred:"),
        para("AMPARO M. MUÑOZ, EDD"),
    ]


def write_docx(path, body, footer=None):
    header = '<w:hdr xmlns:w="x">' + "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>"
                                           for line in spec.HEADER_LINES) + "</w:hdr>"
    if footer is None:
        footer = '<w:ftr xmlns:w="x">' + "".join(f"<w:p><w:r><w:t>{m}</w:t></w:r></w:p>"
                                               for m in spec.FOOTER_MARKERS) + "</w:ftr>"
    document = ('<?xml version="1.0"?><w:document xmlns:w="x"><w:body>'
                + "".join(body) + "</w:body></w:document>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", document)
        z.writestr("word/header1.xml", header)
        z.writestr("word/footer1.xml", footer)


def statuses(results):
    return {(r.layer, r.rule): r.status for r in results}


def put_line(page, y, text, x=spec.LEFT_TEXT_EDGE_PT, size=12):
    page.insert_text((x, y), text, fontsize=size, fontname="helv")


def put_words(page, y, items, size=12):
    for x, text in items:
        page.insert_text((x, y), text, fontsize=size, fontname="helv")


def table_cell(jc, size=24):
    rpr = f"<w:rPr>{FONT}<w:sz w:val=\"{size}\"/></w:rPr>"
    return (f'<w:tbl><w:tr><w:tc><w:p><w:pPr><w:jc w:val="{jc}"/></w:pPr>'
            f'<w:r>{rpr}<w:t>Cell text.</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')


def draw_grid(page, x, y, col_widths, row_heights):
    """Vector grid so pymupdf's table detector sees a real table, not just columns of text."""
    width, height = sum(col_widths), sum(row_heights)
    xs, ys = [x], [y]
    for w in col_widths:
        xs.append(xs[-1] + w)
    for h in row_heights:
        ys.append(ys[-1] + h)
    for yy in ys:
        page.draw_line((x, yy), (x + width, yy))
    for xx in xs:
        page.draw_line((xx, y), (xx, y + height))


def new_pdf(path, pages):
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page(width=612, height=792)
        put_line(page, 40, spec.HEADER_LINES[4])
        for line in lines:
            line(page)
    doc.save(str(path))
    doc.close()


class DocxLayer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parents[2] / "tools" / "tests" / "_tmp_format"
        self.tmp.mkdir(exist_ok=True)
        self.path = self.tmp / "fixture.docx"

    def tearDown(self):
        for f in self.tmp.iterdir():
            f.unlink()
        self.tmp.rmdir()

    def check(self, body):
        write_docx(self.path, body)
        return statuses(check_format.check_docx(self.path))

    def test_good_fixture_passes_every_rule(self):
        result = self.check(good_body())
        self.assertEqual(set(result.values()), {check_format.PASS}, result)

    def test_malformed_xml_fails(self):
        # Word exports a truncated page instead of reporting malformed markup.
        result = self.check(["<w:p><w:r><w:t>unclosed run</w:p>"])
        self.assertEqual(result[("docx", "package XML is well-formed")], check_format.FAIL)

    def test_wrong_font_fails(self):
        body = good_body()
        body[7] = body[7].replace(spec.FONT_NAME, "Calibri")
        self.assertEqual(self.check(body)[("docx", "body font is " + spec.FONT_NAME)],
                         check_format.FAIL)

    def test_missing_tab_stop_fails(self):
        body = good_body()
        body[2] = para("TO:VICE PRESIDENT")
        rule = f"header values sit on the {spec.LABEL_TAB_STOP_TWIPS}-twip tab stop"
        self.assertEqual(self.check(body)[("docx", rule)], check_format.FAIL)

    def test_missing_date_rule_fails(self):
        body = good_body()
        body[6] = para("DATE:NOVEMBER 5, 2026", tabs=True, tab_after_label=True)
        self.assertEqual(self.check(body)[("docx", f"rule under {spec.HEADER_RULE_AFTER}")],
                         check_format.FAIL)

    def test_footer_text_split_across_runs_passes(self):
        # Word re-saves footers with words split over many runs; contiguous runs must
        # join without inventing a space, while <w:br/> still separates lines.
        footer = ('<w:ftr xmlns:w="x"><w:p>'
                  '<w:r><w:t xml:space="preserve">Address: A. </w:t></w:r>'
                  '<w:r><w:t>Bonifacio</w:t></w:r>'
                  '<w:r><w:t xml:space="preserve"> St. San Nicolas </w:t></w:r>'
                  '<w:r><w:t>Poblacion, Concepcion, Tarlac</w:t></w:r>'
                  '<w:r><w:br/><w:t>Telephone No.: (045) 923-0303</w:t></w:r>'
                  '<w:r><w:br/><w:t>Email Address: 300951@deped.gov.ph</w:t></w:r>'
                  '<w:r><w:br/><w:t>\u201cDisiplina at Galing Ing Armas Ku,</w:t></w:r>'
                  '<w:r><w:br/><w:t>Aquinian Ku, Pagmaragul Ku!\u201d</w:t></w:r>'
                  '</w:p></w:ftr>')
        write_docx(self.path, good_body(), footer=footer)
        result = statuses(check_format.check_docx(self.path))
        self.assertEqual(result[("docx", "address and motto footnote present")], check_format.PASS)

    def test_justified_url_fails(self):
        body = good_body()
        body[8] = para("2. See https://example.com for details.", jc="both")
        self.assertEqual(self.check(body)[("docx", "no justified paragraph holds a URL or e-mail")],
                         check_format.FAIL)

    def test_justified_table_cell_fails(self):
        body = good_body() + [table_cell(jc="both")]
        self.assertEqual(self.check(body)[("docx", "table cells are not justified")],
                         check_format.FAIL)

    def test_left_aligned_table_cell_passes(self):
        body = good_body() + [table_cell(jc="left")]
        self.assertEqual(self.check(body)[("docx", "table cells are not justified")],
                         check_format.PASS)

    def test_field_order_fails_when_date_precedes_subject(self):
        body = good_body()
        body[4], body[6] = body[6], body[4]
        self.assertEqual(self.check(body)[("docx", "field order (memorandum)")],
                         check_format.FAIL)

    def test_numbering_gap_fails(self):
        body = good_body()
        body[8] = para("3. See https://example.com for details.")
        self.assertEqual(self.check(body)[("docx", "numbered paragraphs run 1..n without gaps")],
                         check_format.FAIL)

    def test_condensed_table_type_passes(self):
        body = good_body() + [table_cell(jc="left", size=13)]
        self.assertEqual(self.check(body)[("docx", "body size is 12 pt")], check_format.PASS)

    def test_undersized_prose_fails(self):
        body = good_body()
        body[7] = body[7].replace('<w:sz w:val="24"/>', '<w:sz w:val="16"/>')
        self.assertEqual(self.check(body)[("docx", "body size is 12 pt")], check_format.FAIL)


class PdfLayer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parents[2] / "tools" / "tests" / "_tmp_format_pdf"
        self.tmp.mkdir(exist_ok=True)
        self.path = self.tmp / "fixture.pdf"

    def tearDown(self):
        for f in self.tmp.iterdir():
            f.unlink()
        self.tmp.rmdir()

    def check(self, pages):
        new_pdf(self.path, pages)
        return statuses(check_format.check_pdf(self.path))

    def test_clean_page_passes(self):
        def page(p):
            put_line(p, 100, "TO:")
            put_line(p, 100, "VICE PRESIDENT", x=spec.VALUE_COLUMN_PT)
            put_line(p, 130, "1. The survey shall be accomplished within the period.")
            put_line(p, 160, "Prepared by:")
            put_line(p, 180, "AARON Y. HERNANDEZ")
        result = self.check([[page], [lambda p: put_line(p, 100, "2. Next paragraph.")]])
        self.assertEqual(set(result.values()), {check_format.PASS}, result)

    def test_stretched_line_fails(self):
        def page(p):
            put_words(p, 100, [(49.65, "The"), (110, "survey"), (170, "shall"), (230, "be")])
            for y in (130, 160, 190):
                put_line(p, y, "1. Normal spacing on this line.")
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "no stretched justified lines")], check_format.FAIL)

    def test_column_jump_is_not_a_river(self):
        def page(p):
            put_line(p, 100, "FROM:")
            put_line(p, 100, "By the Authority of the SSLG President", x=spec.VALUE_COLUMN_PT)
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "no stretched justified lines")], check_format.PASS)
        self.assertEqual(result[("pdf", "field values share one column")], check_format.PASS)

    def test_table_column_gap_is_not_a_river(self):
        def page(p):
            draw_grid(p, 49.65, 100, (200, 200), (30, 30))
            put_line(p, 120, "Alpha", x=55)
            put_line(p, 120, "Beta", x=255)
            put_line(p, 140, "Gamma", x=55)
            put_line(p, 140, "Delta", x=255)
            put_line(p, 200, "1. Normal spacing on this prose line.")
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "no stretched justified lines")], check_format.PASS)

    def test_stretched_prose_line_outside_a_table_still_fails(self):
        def page(p):
            draw_grid(p, 49.65, 100, (200, 200), (30, 30))
            put_line(p, 120, "Alpha", x=55)
            put_line(p, 120, "Beta", x=255)
            put_words(p, 200, [(49.65, "The"), (150, "survey"), (280, "shall"), (400, "be")])
            for y in (230, 250, 270):
                put_line(p, y, "1. Normal spacing on this prose line.")
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "no stretched justified lines")], check_format.FAIL)

    def test_misaligned_value_fails(self):
        def page(p):
            put_line(p, 100, "DATE:")
            put_line(p, 100, "NOVEMBER 5, 2026", x=100)
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "field values share one column")], check_format.FAIL)

    def test_overflow_fails(self):
        def page(p):
            put_line(p, 100, "word " * 30, x=500)
        result = self.check([[page]])
        self.assertEqual(result[("pdf", f"nothing past the {spec.RIGHT_TEXT_EDGE_PT:.0f} pt text edge")],
                         check_format.FAIL)

    def test_undersized_body_fails(self):
        result = self.check([[lambda p: put_line(p, 100, "tiny body text", size=9)]])
        self.assertEqual(result[("pdf", "no undersized body text")], check_format.FAIL)

    def test_condensed_table_type_passes(self):
        def page(p):
            draw_grid(p, 49.65, 100, (200, 200), (30, 30))
            put_line(p, 120, "Alpha", x=55, size=6.5)
            put_line(p, 120, "Beta", x=255, size=6.5)
            put_line(p, 200, "1. Normal body text at twelve point.")
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "no undersized body text")], check_format.PASS)

    def test_undersized_text_outside_a_table_fails(self):
        def page(p):
            draw_grid(p, 49.65, 100, (200, 200), (30, 30))
            put_line(p, 120, "Alpha", x=55)
            put_line(p, 200, "tiny prose", size=9)
        result = self.check([[page]])
        self.assertEqual(result[("pdf", "no undersized body text")], check_format.FAIL)

    def test_cut_paragraph_fails(self):
        result = self.check([
            [lambda p: put_line(p, 100, "The survey shall be accomplished")],
            [lambda p: put_line(p, 100, "within the period stated.")],
        ])
        self.assertEqual(result[("pdf", "no paragraph cut across a page break")], check_format.FAIL)

    def test_table_continuation_is_not_a_cut_paragraph(self):
        def page_one(p):
            draw_grid(p, 49.65, 100, (200, 200), (30, 30, 30))
            put_line(p, 120, "Alpha", x=55)
            put_line(p, 150, "Beta", x=55)
            put_line(p, 180, "Gamma", x=55)

        def page_two(p):
            draw_grid(p, 49.65, 100, (200, 200), (30, 30))
            put_line(p, 120, "Club", x=55)
            put_line(p, 150, "Delta", x=55)
        result = self.check([[page_one], [page_two]])
        self.assertEqual(result[("pdf", "no paragraph cut across a page break")], check_format.PASS)

    def test_signature_label_stranded_fails(self):
        result = self.check([
            [lambda p: put_line(p, 700, "Prepared by:")],
            [lambda p: put_line(p, 100, "AARON Y. HERNANDEZ")],
        ])
        self.assertEqual(result[("pdf", "signature label kept with its name")], check_format.FAIL)

    def test_missing_letterhead_on_page_two_fails(self):
        doc = pymupdf.open()
        for _ in range(2):
            page = doc.new_page(width=612, height=792)
            put_line(page, 100, "1. Body text on this page.")
        put_line(doc[0], 40, spec.HEADER_LINES[4])
        doc.save(str(self.path))
        doc.close()
        result = statuses(check_format.check_pdf(self.path))
        self.assertEqual(result[("pdf", "letterhead on every page")], check_format.FAIL)


if __name__ == "__main__":
    unittest.main()