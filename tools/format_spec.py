"""BSANHS SSLG house format baseline, encoded once for every generated document.

The values below are read back from the accepted issuances in this vault, not invented:
the letterhead, footnote and body styling of the signed office memoranda.
"""

FONT_NAME = "Bookman Old Style"
FONT_SIZE_HALFPOINTS = 24  # 12 pt

# Page geometry, in twips, as printed by the accepted memoranda.
PAGE_WIDTH = 12240
PAGE_HEIGHT = 18720
MARGIN_TOP = 1440
MARGIN_BOTTOM = 0
MARGIN_LEFT = 993
MARGIN_RIGHT = 993
HEADER_DISTANCE = 360
FOOTER_DISTANCE = 490

TEXT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
RIGHT_TEXT_EDGE_PT = (PAGE_WIDTH - MARGIN_RIGHT) / 20.0  # 562.35 pt
LEFT_TEXT_EDGE_PT = MARGIN_LEFT / 20.0

HEADER_LINES = (
    "Republic of the Philippines",
    "Department of Education",
    "REGION III",
    "SCHOOLS DIVISION OF TARLAC PROVINCE",
    "BENIGNO S. AQUINO NATIONAL HIGH SCHOOL",
    "Learner Government Coordinating Council (LGCC)",
)

FOOTER_MARKERS = (
    "A. Bonifacio St. San Nicolas",
    "Poblacion, Concepcion, Tarlac",
    "(045) 923-0303",
    "300951@deped.gov.ph",
    "Disiplina at Galing Ing Armas Ku",
    "Aquinian Ku, Pagmaragul Ku",
)

# Field order per document kind, labels only (case-insensitive, prefix match).
FIELD_ORDER = {
    "memorandum": ("MEMORANDUM", "No.", "TO:", "FROM:", "SUBJECT:", "DATE:"),
    "meeting-notice": ("NOTICE OF MEETING", "No.", "TO:", "FROM:", "SUBJECT:", "DATE:"),
    "proposal": ("PROPOSAL", "TO:", "FROM:", "SUBJECT:", "DATE:"),
    "completion-report": ("ACTIVITY COMPLETION REPORT", "TO:", "FROM:", "SUBJECT:", "DATE:"),
    "excuse-letter": ("LETTER", "TO:", "FROM:", "SUBJECT:", "DATE:"),
}

SIGNATURE_ORDER = ("Prepared by:", "Reviewed and Evaluated by:", "Concurred:")

# The header block is two columns: labels on the text margin, values on one tab stop,
# with a rule closing the block under DATE. Measured from the signed issuances.
LABEL_TAB_STOP_TWIPS = 1440
LABEL_COLUMN_PT = 49.6
VALUE_COLUMN_PT = 121.6
COLUMN_TOLERANCE_PT = 6.0
HEADER_RULE_AFTER = "DATE:"

# Body paragraphs are justified; a paragraph holding an unbreakable token
# (URL, e-mail) is left-aligned instead, because justification stretches it into
# rivers of whitespace.
UNBREAKABLE_TOKEN = r"(?:https?://|www\.|[\w.+-]+@[\w-]+\.[\w.-]+)"

# Geometry tolerances for the rendered-PDF layer, in points.
# A stretched line is judged against the document's own median inter-word gap as well as an
# absolute floor, because normal spacing differs between a 12 pt body and a 9 pt footnote.
MAX_WORD_GAP = 15.0
WORD_GAP_MULTIPLIER = 3.0
RIGHT_EDGE_TOLERANCE = 2.0
# Word lets a trailing comma or period hang outside the margin; that overhang is typography,
# not overflow.
PUNCTUATION_OVERHANG_PT = 6.0
MIN_BODY_FONT_SIZE = 10.0

# A numbered paragraph, or a signature block, must not straddle a page break.
KEEP_TOGETHER_RULES = (
    "numbered paragraph split across pages",
    "signature label separated from its name",
    "signature block split across pages",
)
