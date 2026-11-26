# -*- coding: utf-8 -*-
"""Build the Model United Nations Club activity proposal packet from AP 009."""
import re
import shutil
import zipfile
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Twips
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Activity Proposal - Disyembregalo (AP_SSLG_2026_009).docx"
DST = ROOT / "Activity Proposal - Model United Nations Club (AP_SSLG_2026_010).docx"

FONT = "Bookman Old Style"

shutil.copyfile(SRC, DST)
doc = Document(DST)
src_doc = Document(SRC)
body = doc.element.body
sectPr = body.find(qn("w:sectPr"))
for child in list(body):
    if child is not sectPr:
        body.remove(child)

P = src_doc.paragraphs
PROTO_TITLE = P[1]
PROTO_TO = P[3]
PROTO_TO2 = P[4]
PROTO_TO3 = P[5]
PROTO_SECT = P[18]
PROTO_VALUE = P[19]
PROTO_BODY = P[22]
PROTO_SUB = P[56]
PROTO_OBJ = P[31]
PROTO_PERSON = P[67]
PROTO_SIG_LABEL = P[78]
PROTO_SIG_NAME = P[79]
PROTO_TABLE = src_doc.tables[1]  # 3-column program table


def add_para(proto, text=None):
    el = deepcopy(proto._p)
    sectPr.addprevious(el)
    p = Paragraph(el, doc._body)
    if text is not None:
        set_text(p, text)
    return p


def set_text(p, text):
    runs = p.runs
    if not runs:
        r = p.add_run(text)
        r.font.name = FONT
        r.font.size = Pt(12)
        return p
    first = runs[0]
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    first.text = text
    return p


def new_para(text="", bold=False, size=12, align=None, first_indent=None,
             space_before=0, space_after=0, page_break=False, keep=False,
             italic=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Pt(0)
    pf.first_line_indent = Pt(first_indent) if first_indent else None
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.0
    if align is not None:
        p.alignment = align
    if page_break:
        pf.page_break_before = True
    if keep:
        pf.keep_with_next = True
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.name = FONT
        r.font.size = Pt(size)
    return p


def new_runs(parts, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36,
             space_before=0, space_after=6, keep=False):
    """parts: list of (text, bold)."""
    p = new_para(align=align, first_indent=first_indent,
                 space_before=space_before, space_after=space_after, keep=keep)
    for text, bold in parts:
        r = p.add_run(text)
        r.bold = bold
        r.font.name = FONT
        r.font.size = Pt(size)
    return p


def add_table(rows, cols, widths):
    t = doc.add_table(rows=rows, cols=cols)
    t._tbl.replace(t._tbl.tblPr, deepcopy(PROTO_TABLE._tbl.tblPr))
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs[1:]:
                p._p.getparent().remove(p._p)
            for r in list(cell.paragraphs[0].runs):
                r._r.getparent().remove(r._r)
    set_widths(t, widths)
    return t


def set_widths(t, widths):
    tblPr = t._tbl.tblPr
    for old in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(old)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(int(sum(widths) * 20)))
    tblW.set(qn("w:type"), "dxa")
    for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(w * 20)))
    for row in t.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = Pt(w)


def cell_text(cell, text, bold=False, size=10.5, align=None):
    p = cell.paragraphs[0]
    p.style = doc.styles["No Spacing"]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    r.bold = bold
    r.font.name = FONT
    r.font.size = Pt(size)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def fill_table(t, data, header=True, size=10.5):
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            cell_text(t.rows[i].cells[j], value, bold=(header and i == 0), size=size)


def header_repeat(t):
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)


def keep_table_rows(t):
    for i, row in enumerate(t.rows):
        if i == len(t.rows) - 1:
            continue
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True


def no_borders(t):
    tblPr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "nil")
        borders.append(e)
    tblPr.append(borders)


# ---------------------------------------------------------------- AP cover
p = add_para(PROTO_TITLE)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_text(p, "ACTIVITY PROPOSAL")
new_para("", space_after=6)

p = add_para(PROTO_TO)
set_text(p, "To:     DR. AMPARO M. MUÑOZ")
p = add_para(PROTO_TO2)
set_text(p, "            Principal IV")
p.runs[0].bold = False
p = add_para(PROTO_TO3)
set_text(p, "            Benigno S. Aquino National High School")
new_para("", space_after=6)

p = add_para(PROTO_TO)
set_text(p, "           Thru:    _________________________")
p = add_para(PROTO_TO2)
set_text(p, "                        Club Adviser")
p.runs[0].bold = False
p = add_para(PROTO_TO3)
set_text(p, "                        Benigno S. Aquino National High School")
new_para("", space_after=6)

p = add_para(PROTO_TO)
for r in list(p.runs):
    r._r.getparent().remove(r._r)
for text, bold in [
    ("From:    ", True),
    ("AARON Y. HERNANDEZ", True),
    ("\n             ELLAINE T. JACOB", True),
    ("\n             JOLEX ALEXIER S. CRUZ", True),
    ("\n             Founding Members, Model United Nations Club", False),
]:
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(12)
    r.bold = bold
    r.italic = False
new_para("", space_after=6)


def section(title):
    p = add_para(PROTO_SECT)
    set_text(p, title)
    return p


def value(text):
    p = add_para(PROTO_VALUE)
    set_text(p, text)
    return p


def bodyp(text):
    p = add_para(PROTO_BODY)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_text(p, text)
    return p


def recital(lead, rest):
    p = add_para(PROTO_BODY)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    for text, bold in ((lead, True), (rest, False)):
        r = p.add_run(text)
        r.font.name = FONT
        r.font.size = Pt(12)
        r.bold = bold
        r.italic = False
    return p


def subhead(text):
    p = add_para(PROTO_SUB)
    set_text(p, text)
    return p


section("ACTIVITY TITLE:")
value("Establishment of the Model United Nations (MUN) Club")

section("RATIONALE:")
recital("WHEREAS,", " the school is committed to the holistic development of learners through academic and co-curricular programs that cultivate leadership, civic responsibility, and respect for diverse perspectives;")
recital("WHEREAS,", " an increasingly interconnected world requires learners to understand global issues, weigh evidence, listen to opposing views, and resolve differences through peaceful and reasoned dialogue;")
recital("WHEREAS,", " the United Nations and its member states conduct diplomacy through research, negotiation, parliamentary procedure, and debate, and Model United Nations simulations, parliamentary debates, research, and public speaking offer learners structured opportunities to practice these skills and to deepen their understanding of the United Nations, international law, the Sustainable Development Goals, and Philippine foreign policy;")
recital("WHEREAS,", " the establishment of the Model United Nations Club is consistent with the General Plan of Action (GPOA) of the Supreme Secondary Learner Government (SSLG) for School Year 2026-2027, which sets the learner government's programmes, projects, and activities for the school year;")
recital("WHEREAS,", " the undersigned founding members have resolved to establish the Club as a recognized learner organization under the supervision of a designated faculty adviser and the SSLG and Learner Government Coordinating Council (LGCC), with a Constitution and By-Laws, Plan of Action, and founding membership attached as Annexes A, B, and C;")
recital("NOW, THEREFORE,", " in view of the foregoing, the undersigned founding members respectfully submit this Activity Proposal for the approval of the Principal IV and for the recognition of the Model United Nations Club, effective upon approval and with its first program cycle running from November 2026 to February 2027.")

section("OBJECTIVES:")
for text in [
    "Establish a recognized learner organization that promotes the study and practice of diplomacy, international relations, and debate.",
    "Develop the research, critical thinking, public speaking, negotiation, and writing skills of members through structured training and simulations.",
    "Deepen learners' understanding of the United Nations, its organs and processes, international law, the Sustainable Development Goals, and Philippine foreign policy.",
    "Provide safe, supervised, and inclusive fora for Model United Nations simulations and debate activities.",
    "Cultivate leadership, teamwork, discipline, and respect for evidence and diverse viewpoints.",
    "Represent the school in division, regional, or national Model United Nations and debate activities, subject to school approval.",
]:
    p = add_para(PROTO_OBJ)
    set_text(p, text)

section("ACTIVITY:")
bodyp("The Model United Nations Club shall be established as a recognized learner organization of Benigno S. Aquino National High School effective upon approval of this proposal, with its first program cycle running from November 2026 to February 2027.")

subhead("A. Launch and First General Assembly")
bodyp("The founding members shall convene the first general assembly in January 2027, subject to the school calendar. The assembly shall orient prospective members on the Club's Constitution and By-Laws, adopt the Plan of Action, and elect the first set of officers. The faculty adviser designated by the Principal IV shall supervise the assembly.")

subhead("B. Regular Programs and Training")
bodyp("1. Debate and Public Speaking Training. Regular sessions on argumentation, case construction, rebuttal, delivery, and parliamentary procedure, using formats such as Asian Parliamentary and World Schools debating.")
bodyp("2. Model United Nations Simulations. Practice sessions and a full simulation covering roll call, agenda setting, moderated and unmoderated caucuses, position papers, draft resolutions, amendments, and voting, using committees such as the General Assembly, Security Council, ECOSOC, and specialized agencies.")
bodyp("3. Research and Global Awareness. Member-led discussions, bulletin boards, and school-based campaigns on the Sustainable Development Goals, human rights, peace, climate action, and other United Nations observances.")
bodyp("4. Approved External Participation. Delegations to division, regional, or national Model United Nations and debate activities when invited, endorsed by the school, and covered by parental consent and the school's safety and travel requirements.")

subhead("C. Membership and Governance")
bodyp("Membership shall be open to all bona fide learners of Grades 7 to 12. No membership fee shall be imposed. The Club shall be governed by its Constitution and By-Laws (Annex A), with officers elected by the members and a faculty adviser providing supervision and guidance. The adviser shall be designated by the Principal IV.")

subhead("D. Founding Members")
bodyp("The Club is founded by AARON Y. HERNANDEZ, ELLAINE T. JACOB, and JOLEX ALEXIER S. CRUZ. They shall constitute the interim founding body, convene the first general assembly, and hold no office until the first election. Their names and the interim organization are listed in Annex C.")

subhead("E. Supervision, Safety, and Conduct")
bodyp("All Club activities shall be conducted on school premises during authorized hours unless written approval is granted for an off-campus activity. The faculty adviser shall be present in all major activities. The Club shall observe the DepEd Child Protection Policy, the Anti-Hazing Law, the Data Privacy Act, and all school rules. It shall not engage in partisan politics, religious proselytizing, unauthorized solicitation, or any activity that may endanger learners.")

section("BUDGET:")
subhead("A. Source of Funds")
bodyp("The Club shall not impose mandatory membership fees. Its operations shall be supported by voluntary contributions from members, approved fundraising activities, in-kind donations, and such support as the SSLG may extend in accordance with existing accounting and auditing rules. No collection shall be made without the written approval of the faculty adviser and the school administration.")

p = subhead("B. Budget Allocation")
p.paragraph_format.keep_with_next = True
bt = add_table(8, 3, [225, 140, 93])
fill_table(bt, [
    ["Item", "Source of Funds", "Estimated Amount (Php)"],
    ["Printing of Constitution, modules, position papers, and certificates", "Club funds / Voluntary contributions", ""],
    ["Debate supplies, placards, and simulation materials", "Club funds / In-kind donations", ""],
    ["Program materials, tarpaulin, and recognition tokens", "Club funds / SSLG support", ""],
    ["Resource speaker tokens and training expenses (optional)", "Club funds / Donations", ""],
    ["Transportation for approved external activities", "Participants / Sponsors", ""],
    ["Contingency", "Club funds", ""],
    ["TOTAL", "", ""],
])
header_repeat(bt)
keep_table_rows(bt)

section("PERSON/S INVOLVED:")
p = add_para(PROTO_BODY)
set_text(p, "The aforementioned activity will involve the following:")
for text in [
    "School Administration and Faculty Members",
    "Faculty Adviser of the Model United Nations Club (to be designated)",
    "Founding Members of the Model United Nations Club",
    "Registered Members from Grades 7 to 12",
    "Supreme Secondary Learner Government (SSLG) and Learner Government Coordinating Council (LGCC) Officers",
    "School Parent-Teacher Association (SPTA) Officers, Parents, and Guardians",
    "Resource Speakers, Judges, and Evaluators",
    "School Partners and Other Stakeholders",
]:
    p = add_para(PROTO_PERSON)
    set_text(p, text)

# ---------------------------------------------------------------- AP signatures
p = add_para(PROTO_SIG_LABEL)
set_text(p, "Prepared by:")
p.paragraph_format.keep_with_next = True

sig = add_table(1, 3, [145, 140, 173])
no_borders(sig)
for cell, name in zip(sig.rows[0].cells, ["AARON Y. HERNANDEZ", "ELLAINE T. JACOB", "JOLEX ALEXIER S. CRUZ"]):
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(30)
    p1.paragraph_format.space_after = Pt(0)
    r = p1.add_run(name)
    r.bold = True
    r.font.name = FONT
    r.font.size = Pt(10.5)
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(12)
    p2.paragraph_format.keep_with_next = True
    r = p2.add_run("Founding Member")
    r.font.name = FONT
    r.font.size = Pt(10.5)
    p1.paragraph_format.keep_with_next = True

for label, name, title in [
    ("Noted by:", "_________________________", "Club Adviser"),
    ("Recommending Approval:", "GILBERT F. POLICARPIO", "Head Teacher VI"),
    ("Approved by:", "AMPARO M. MUÑOZ, EdD", "Principal IV"),
]:
    p = add_para(PROTO_SIG_LABEL)
    set_text(p, label)
    p.paragraph_format.keep_with_next = True
    p = add_para(PROTO_SIG_NAME)
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    r = p.add_run(f"\n{name}")
    r.font.name = FONT
    r.font.size = Pt(12)
    r.bold = True
    r.italic = False
    r = p.add_run(f"\n{title}")
    r.font.name = FONT
    r.font.size = Pt(12)
    r.bold = False
    r.italic = False
    p.paragraph_format.keep_with_next = (label != "Approved by:")

# ---------------------------------------------------------------- Annex A
new_para("ANNEX A", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER,
         page_break=True, space_after=6, keep=True)
new_para("CONSTITUTION AND BY-LAWS", bold=True, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, keep=True)
new_para("MODEL UNITED NATIONS CLUB", bold=True, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, keep=True)
new_para("Benigno S. Aquino National High School", size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, keep=True)
new_para("Concepcion, Tarlac", size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

new_para("PREAMBLE", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         space_before=6, space_after=6, keep=True)
new_para("We, the undersigned founding members of the Model United Nations Club of Benigno S. Aquino National High School, mindful of our role as learners and citizens of a global community, recognizing the value of informed dialogue, diplomacy, and the peaceful resolution of international concerns, and committed to the purposes and principles of the United Nations, do hereby ordain and promulgate this Constitution and By-Laws.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_after=6)


def article(title):
    new_para(title, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
             space_before=10, space_after=4, keep=True)


def sec(label, text):
    new_runs([(f"{label} ", True), (text, False)])


article("ARTICLE I - NAME AND DOMICILE")
sec("Section 1.", "The organization shall be known as the Model United Nations Club of Benigno S. Aquino National High School, hereinafter referred to as the Club.")
sec("Section 2.", "The Club shall be domiciled at Benigno S. Aquino National High School, A. Bonifacio Street, San Nicolas Poblacion, Concepcion, Tarlac. It shall operate within the school premises and under school policies, except during duly approved off-campus activities.")
sec("Section 3.", "The Club is a learner organization recognized by the school through the Supreme Secondary Learner Government (SSLG) and the Learner Government Coordinating Council (LGCC) and approved by the Office of the Principal. It shall remain under the supervision of a faculty adviser designated by the Principal.")

article("ARTICLE II - DECLARATION OF PRINCIPLES AND OBJECTIVES")
sec("Section 1.", "The Club shall be guided by the following principles: peaceful and reasoned dialogue; respect for human dignity and human rights; the rule of law; multilateral cooperation; academic honesty; inclusivity; non-partisanship; and the welfare of learners.")
sec("Section 2.", "The Club shall pursue the following objectives:")
for text in [
    "(a) cultivate an informed understanding of the United Nations, its organs and processes, international law, the Sustainable Development Goals, and Philippine foreign policy;",
    "(b) develop research, critical thinking, public speaking, debate, negotiation, and drafting skills;",
    "(c) provide safe, supervised, and inclusive fora for Model United Nations simulations and debates;",
    "(d) promote awareness of global issues and the value of peaceful dialogue;",
    "(e) develop leadership, teamwork, discipline, and civic responsibility; and",
    "(f) represent the school in approved Model United Nations and debate activities.",
]:
    new_para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=54, space_after=3)
sec("Section 3.", "The Club shall not engage in partisan politics, religious proselytizing, hazing, bullying, discrimination, unauthorized solicitation, or any activity contrary to law, DepEd policies, or school rules.")

article("ARTICLE III - MEMBERSHIP")
sec("Section 1.", "Regular members shall be bona fide learners of Grades 7 to 12 who are officially enrolled in the school, have registered with the Club, and accept this Constitution and By-Laws.")
sec("Section 2.", "Honorary members may be faculty members, alumni, resource speakers, or partners invited by the Club with the approval of the adviser. Honorary members shall not vote or hold office.")
sec("Section 3.", "Membership shall be voluntary and shall not be denied on the basis of sex, gender, religion, ethnicity, disability, economic status, or political affiliation. No membership fee shall be imposed.")
sec("Section 4.", "Admission shall require a duly accomplished registration form, attendance at an orientation, and the approval of the adviser. The Club shall maintain a register of members.")
sec("Section 5.", "A member may be suspended or removed only after due process under Article X. Discipline that falls within the authority of school officials shall be referred to them.")

article("ARTICLE IV - RIGHTS AND DUTIES OF MEMBERS")
sec("Section 1.", "Every regular member in good standing shall have the right to:")
for text in [
    "(a) participate in all Club meetings, trainings, and activities;",
    "(b) vote in general assemblies and elections;",
    "(c) be elected or appointed to office, subject to the qualifications in this Constitution and By-Laws;",
    "(d) access the Club's records, subject to confidentiality and data privacy rules;",
    "(e) receive due process in any complaint or proceeding; and",
    "(f) propose amendments to this Constitution and By-Laws.",
]:
    new_para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=54, space_after=3)
sec("Section 2.", "Every member shall:")
for text in [
    "(a) uphold this Constitution and By-Laws and the rules of the school;",
    "(b) attend meetings and activities regularly and inform the Secretary of unavoidable absences;",
    "(c) observe honesty, respect, and decorum in debate and in all Club activities;",
    "(d) protect the reputation and property of the Club and the school;",
    "(e) safeguard confidential information of members; and",
    "(f) report grievances through the proper channels.",
]:
    new_para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=54, space_after=3)

article("ARTICLE V - OFFICERS AND THEIR DUTIES")
sec("Section 1.", "The officers of the Club shall be the President, Vice President, Secretary, Treasurer, Auditor, Public Information Officer, and one Grade-Level Representative for each grade level from Grades 7 to 12. The faculty adviser shall be a non-voting member of the organization.")
sec("Section 2.", "All officers must be regular members in good standing, must not have a pending disciplinary case, and must be willing to serve for the full term.")
sec("Section 3.", "The President shall preside over meetings, represent the Club, coordinate with the adviser and the SSLG, and submit activity and annual reports.")
sec("Section 4.", "The Vice President shall assist the President, preside in the President's absence, oversee the standing committees, and coordinate membership development.")
sec("Section 5.", "The Secretary shall keep the minutes, maintain the membership register and records, prepare correspondence, record attendance, and maintain the Club archive.")
sec("Section 6.", "The Treasurer shall keep the financial records, collect approved contributions, prepare the budget and financial reports, and disburse funds only with the required approvals.")
sec("Section 7.", "The Auditor shall verify the accounts, conduct a periodic audit, and report the results to the members and the adviser.")
sec("Section 8.", "The Public Information Officer shall prepare announcements, publicity materials, and documentation, subject to the approval of the adviser.")
sec("Section 9.", "The Grade-Level Representatives shall serve as liaisons between their grade levels and the Club, promote membership, and monitor attendance and participation.")
sec("Section 10.", "The officers shall render reports at every general assembly and at the end of their term.")

article("ARTICLE VI - ELECTION OF OFFICERS")
sec("Section 1.", "The first election of officers shall be held at the first general assembly after the approval of this Constitution and By-Laws. The officers elected shall serve until the end of School Year 2026-2027.")
sec("Section 2.", "Subsequent annual elections shall be held not later than the last week of April of each school year. The officers-elect shall assume office at the beginning of the following school year.")
sec("Section 3.", "A Committee on Elections of three members shall be appointed by the adviser. It shall prepare the list of qualified voters and candidates, give at least five school days' notice of the election, and conduct the election by secret ballot.")
sec("Section 4.", "A candidate who obtains a majority of the valid votes cast for the position shall be proclaimed elected. In case of a tie, a run-off shall be held. If the tie persists, the winner shall be determined by drawing of lots witnessed by the adviser.")
sec("Section 5.", "The results shall be proclaimed immediately and the turnover shall be completed within five school days.")
sec("Section 6.", "The adviser and the Principal may annul an election for verified violation of this Constitution and By-Laws or school rules, after due notice and hearing.")

article("ARTICLE VII - MEETINGS AND QUORUM")
sec("Section 1.", "The Club shall hold a general assembly at least once a month during the school year. Special meetings may be called by the President, the adviser, or upon the written request of at least one-third of the regular members.")
sec("Section 2.", "Notice of a regular meeting shall be given at least three school days before the meeting. Notice of a special meeting shall state the purpose and shall be given at least two school days before the meeting.")
sec("Section 3.", "A majority of the registered regular members shall constitute a quorum for a general assembly. A majority of the officers shall constitute a quorum for an officers' meeting.")
sec("Section 4.", "Meetings shall follow simplified parliamentary procedure. Model United Nations procedure may be used during simulations and training sessions.")
sec("Section 5.", "The minutes of every meeting shall be recorded and made available to members within five school days.")

article("ARTICLE VIII - STANDING COMMITTEES")
sec("Section 1.", "The Club shall have the following standing committees: Debate and Training; Model United Nations Simulations; Research and Documentation; Membership and Welfare; and Publicity and Finance.")
sec("Section 2.", "The President shall appoint the committee chairpersons with the approval of the adviser. Committee members shall be drawn from the membership.")
sec("Section 3.", "The Debate and Training Committee shall prepare the training program and debate formats. The Model United Nations Simulations Committee shall prepare committees, topics, rules, and materials. The Research and Documentation Committee shall prepare background guides and maintain the archive. The Membership and Welfare Committee shall handle registration and member support. The Publicity and Finance Committee shall coordinate announcements, documentation, and budget preparation with the Treasurer.")
sec("Section 4.", "Ad hoc committees may be created by the President with the approval of the adviser for specific activities.")

article("ARTICLE IX - FINANCES")
sec("Section 1.", "The Club shall be funded by voluntary contributions, approved fundraising activities, in-kind donations, and such support as the SSLG may extend. No mandatory membership fee shall be imposed.")
sec("Section 2.", "The Treasurer shall keep the funds and records. Disbursements shall require the approval of the President and the adviser and shall be supported by receipts.")
sec("Section 3.", "The Treasurer shall submit a monthly financial report and a final report at the end of the school year. The Auditor shall verify the reports.")
sec("Section 4.", "Club funds shall be used exclusively for Club activities. All collections and disbursements shall comply with existing accounting and auditing rules and school policies.")
sec("Section 5.", "The financial records shall be open to the members, the adviser, the SSLG, and authorized school officials.")

article("ARTICLE X - DISCIPLINE AND GRIEVANCE")
sec("Section 1.", "Members shall observe respect, honesty, and fairness. The following shall be prohibited: hazing in any form; bullying, harassment, and discrimination; plagiarism and academic dishonesty; destruction of property; unauthorized solicitation; and partisan political activity.")
sec("Section 2.", "A complaint shall be filed in writing with the Secretary, who shall notify the respondent and the adviser. The adviser shall convene a mediation or conference within five school days.")
sec("Section 3.", "The Club may impose the following internal measures after due process: a reminder, a written warning, suspension of Club privileges, or a recommendation for removal from office or membership. The Club shall not impose penalties that are within the authority of school officials; disciplinary cases shall be referred to them in accordance with DepEd policies.")
sec("Section 4.", "Proceedings shall be confidential, and retaliation against a complainant or witness shall be prohibited.")
sec("Section 5.", "A party may appeal the decision to the adviser and, thereafter, to the Principal.")

article("ARTICLE XI - AMENDMENTS")
sec("Section 1.", "Any member, officer, the adviser, or an authorized school official may propose an amendment in writing. The proposed amendment shall be discussed at a general assembly after at least one week's notice.")
sec("Section 2.", "An amendment shall be adopted by a two-thirds vote of the regular members present at a general assembly with a quorum, subject to the review of the adviser and the approval of the Principal.")
sec("Section 3.", "The amended Constitution and By-Laws shall take effect upon approval and shall be posted or made available to all members.")

article("ARTICLE XII - DISSOLUTION")
sec("Section 1.", "The Club may be dissolved by a two-thirds vote of the regular members at a special meeting called for the purpose, subject to the approval of the adviser and the Principal.")
sec("Section 2.", "Upon dissolution, the officers shall prepare an inventory of assets and records. Club assets shall be turned over to the SSLG or the school, and records shall be archived in accordance with school policy.")
sec("Section 3.", "No dissolution shall take effect while obligations to members, suppliers, or the school remain unsettled.")

article("ARTICLE XIII - TRANSITORY PROVISIONS")
sec("Section 1.", "The founding members, namely AARON Y. HERNANDEZ, ELLAINE T. JACOB, and JOLEX ALEXIER S. CRUZ, shall constitute the interim founding body. They shall convene the first general assembly within thirty school days after the approval of this Constitution and By-Laws.")
sec("Section 2.", "No founder shall hold an office by reason of founding the Club. The first set of officers shall be elected at the first general assembly.")
sec("Section 3.", "The faculty adviser shall be designated by the Principal. Until the designation, the SSLG Adviser shall coordinate with the founding members.")
sec("Section 4.", "The first Plan of Action shall cover November 2026 to February 2027. Subsequent plans shall be prepared before the start of each school year.")
sec("Section 5.", "Existing laws, DepEd policies, and school rules shall prevail over any provision of this Constitution and By-Laws.")

article("ARTICLE XIV - EFFECTIVITY")
sec("Section 1.", "This Constitution and By-Laws shall be ratified by the founding members and shall take effect upon the approval of the Principal IV, upon the endorsement of the SSLG and LGCC.")

new_para("ADOPTED this ______ day of ____________________ 2027 at Benigno S. Aquino National High School, Concepcion, Tarlac.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_before=12, space_after=10)

at = add_table(4, 3, [205, 145, 108])
fill_table(at, [
    ["Name", "Role", "Signature"],
    ["AARON Y. HERNANDEZ", "Founding Member", ""],
    ["ELLAINE T. JACOB", "Founding Member", ""],
    ["JOLEX ALEXIER S. CRUZ", "Founding Member", ""],
], size=10.5)
keep_table_rows(at)

for label, name, title in [
    ("Attested by:", "_________________________", "Club Adviser"),
    ("Noted by:", "AARON KHRISTIAN T. BANAG", "SSLG Adviser"),
    ("Recommending Approval:", "GILBERT F. POLICARPIO", "Head Teacher VI"),
    ("Approved by:", "AMPARO M. MUÑOZ, EdD", "Principal IV"),
]:
    new_para(label, italic=True, space_before=10, space_after=0, keep=True)
    head = name if name.startswith("_") else f"_________________________\n{name}"
    p = new_para("", space_before=6, space_after=6,
                 keep=(label != "Approved by:"))
    r = p.add_run(head)
    r.font.name = FONT
    r.font.size = Pt(12)
    r.bold = True
    r.italic = False
    r = p.add_run(f"\n{title}")
    r.font.name = FONT
    r.font.size = Pt(12)
    r.bold = False
    r.italic = False

# ---------------------------------------------------------------- Annex B
land = doc.add_section(WD_SECTION.NEW_PAGE)
land.orientation = WD_ORIENT.LANDSCAPE
land.page_width = Twips(18720)
land.page_height = Twips(12240)
land.left_margin = Twips(1080)
land.right_margin = Twips(1080)
land.top_margin = Twips(1440)
land.bottom_margin = Twips(1080)
land.header_distance = Twips(360)
land.footer_distance = Twips(490)
for el in land._sectPr.findall(qn("w:pgNumType")):
    land._sectPr.remove(el)

new_para("ANNEX B", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER,
         space_after=6, keep=True)
new_para("PLAN OF ACTION AND CALENDAR OF ACTIVITIES", bold=True, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, keep=True)
new_para("Model United Nations Club", bold=True, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, keep=True)
new_para("School Year 2026-2027 (November 2026 - February 2027)", size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

new_para("This Plan of Action operationalizes Article II of the Constitution and By-Laws. It sets the Club's goals, activities, target outputs, resource requirements, and accountabilities for its first program cycle, which runs from November 2026 to February 2027. Dates are indicative and shall be adjusted to the official school calendar and the approval of the faculty adviser.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_after=8)


def shade_cell(cell, fill="D9D9D9"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def tight_cells(t, lr=70):
    mar = OxmlElement("w:tblCellMar")
    for edge, w in (("top", 30), ("left", lr), ("bottom", 30), ("right", lr)):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:w"), str(w))
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    t._tbl.tblPr.append(mar)


plan_blocks = [
    ("TERM", "TERM 2 (SEPTEMBER 2026 - DECEMBER 2026)"),
    ("ROW", ("Membership Drive and Pre-Registration of Prospective Members",
             "To recruit and pre-register prospective members from Grades 7 to 12 and build the initial membership base of the Club.",
             "November 2026",
             "\u2022 List of pre-registered prospective members\n\u2022 Membership promotion materials\n\u2022 Activity Completion Report",
             "TBD", "Club Funds / Voluntary Contributions",
             "Lead: Founding Members\nAssist: SSLG Officers, Class Advisers")),
    ("ROW", ("Approval, Recognition, and Designation of the Faculty Adviser",
             "To secure the approval of the Principal IV, the formal recognition of the Club, and the designation of its faculty adviser.",
             "December 2026",
             "\u2022 Approved Activity Proposal\n\u2022 Designated faculty adviser\n\u2022 Listing of the Club among recognized learner organizations",
             "TBD", "School Funds / Club Funds",
             "Lead: Founding Members\nAssist: SSLG Adviser, Faculty Adviser")),
    ("TERM", "TERM 3 (JANUARY 2027 - APRIL 2027)"),
    ("ROW", ("First General Assembly, Orientation, and Ratification of the Constitution and By-Laws",
             "To orient the members, ratify the Constitution and By-Laws, and adopt the Plan of Action.",
             "January 2027",
             "\u2022 Ratified Constitution and By-Laws\n\u2022 Minutes and attendance\n\u2022 Activity Completion Report",
             "TBD", "Club Funds",
             "Lead: Founding Members, Faculty Adviser\nAssist: SSLG Officers")),
    ("ROW", ("Election of Officers and Committee Chairpersons",
             "To elect the first set of officers and committee chairpersons under the Constitution and By-Laws.",
             "January 2027",
             "\u2022 Proclaimed officers\n\u2022 Committee assignments\n\u2022 Turnover of interim functions",
             "TBD", "Club Funds",
             "Lead: Committee on Elections\nAssist: Faculty Adviser")),
    ("ROW", ("Debate Fundamentals and Parliamentary Procedure Training",
             "To develop argumentation, case construction, rebuttal, delivery, and parliamentary procedure skills.",
             "January 2027",
             "\u2022 At least four training sessions\n\u2022 Attendance and evaluation sheets",
             "TBD", "Club Funds / Voluntary Contributions",
             "Lead: Debate and Training Committee\nAssist: Faculty Adviser")),
    ("ROW", ("Resolution-Drafting and Position-Paper Workshops",
             "To train members in research, position-paper writing, resolution drafting, and amendment procedure.",
             "January 2027",
             "\u2022 At least two workshop outputs per member\n\u2022 Sample position papers and draft resolutions",
             "TBD", "Club Funds / Voluntary Contributions",
             "Lead: Model UN Simulations Committee\nAssist: Secretary")),
    ("ROW", ("Internal Debate Tournament",
             "To apply debate skills in a supervised competitive format and identify representatives for external activities.",
             "January 2027",
             "\u2022 At least eight participating teams\n\u2022 Results and certificates",
             "TBD", "Club Funds / SSLG Support",
             "Lead: Debate and Training Committee\nAssist: Faculty Adviser, Judges")),
    ("ROW", ("Model United Nations Simulation",
             "To simulate United Nations proceedings with at least two committees and produce position papers and draft resolutions.",
             "January 2027",
             "\u2022 Simulation with at least two committees\n\u2022 Position papers and draft resolutions\n\u2022 Activity Completion Report",
             "TBD", "Club Funds / Voluntary Contributions",
             "Lead: Model UN Simulations Committee\nAssist: Faculty Adviser, Secretary")),
    ("ROW", ("Global Awareness Campaign on a United Nations Observance",
             "To promote awareness of the Sustainable Development Goals and a United Nations observance among learners.",
             "January 2027",
             "\u2022 One school-based campaign or bulletin\n\u2022 Documentation and reach report",
             "TBD", "Club Funds / SSLG Support",
             "Lead: Public Information Officer\nAssist: Research and Documentation Committee")),
    ("ROW", ("Culminating Activity, Recognition, and Turnover of Records",
             "To recognize members' accomplishments, evaluate the first program cycle, and turn over records and financial reports.",
             "February 2027",
             "\u2022 Culminating activity\n\u2022 Annual and financial reports\n\u2022 Turnover of records",
             "TBD", "Club Funds / SSLG Support",
             "Lead: President, Secretary, Treasurer, Auditor\nAssist: Faculty Adviser")),
]

GPOA_W = [118, 186, 72, 136, 56, 92, 162]
plan = add_table(2 + len(plan_blocks), 7, GPOA_W)
tight_cells(plan)
plan.alignment = WD_TABLE_ALIGNMENT.CENTER

for r in (0, 1):
    hdr = plan.rows[r]._tr.get_or_add_trPr()
    hdr.append(OxmlElement("w:tblHeader"))

plan.cell(0, 0).merge(plan.cell(1, 0))
plan.cell(0, 1).merge(plan.cell(1, 1))
plan.cell(0, 2).merge(plan.cell(1, 2))
plan.cell(0, 3).merge(plan.cell(1, 3))
plan.cell(0, 4).merge(plan.cell(0, 5))
plan.cell(0, 6).merge(plan.cell(1, 6))

header_cells = [
    (0, 0, "Programs, Projects, and Activities"),
    (0, 1, "Objectives"),
    (0, 2, "Timeline / Target Date"),
    (0, 3, "Target Output"),
    (0, 4, "Resource Requirement"),
    (1, 4, "Financial"),
    (1, 5, "Source of Funds"),
    (0, 6, "Person/s Responsible (indicate who is the lead and assist)"),
]
for r, c, text in header_cells:
    cell_text(plan.cell(r, c), text, bold=True, size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    shade_cell(plan.cell(r, c))

row = 2
for kind, payload in plan_blocks:
    if kind == "TERM":
        cell = plan.cell(row, 0).merge(plan.cell(row, 6))
        cell_text(cell, payload, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.LEFT)
        shade_cell(cell)
    else:
        for j, val in enumerate(payload):
            cell = plan.cell(row, j)
            cell_text(cell, val, size=9, align=WD_ALIGN_PARAGRAPH.LEFT)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    row += 1

new_para("", space_after=6)

new_para("GOALS AND SUCCESS INDICATORS", bold=True, space_before=6, space_after=4, keep=True)
goals = add_table(7, 3, [205, 390, 155])
goals.alignment = WD_TABLE_ALIGNMENT.CENTER
fill_table(goals, [
    ["Goal", "Success Indicator", "Target"],
    ["Institutionalize the Club", "Recognition, adviser designated, Constitution ratified, officers elected", "By December 2026"],
    ["Build a strong membership base", "Registered regular members from Grades 7 to 12", "At least 30"],
    ["Develop debate and diplomacy skills", "Members completing the training program; debate teams formed", "80% of members; 8 teams"],
    ["Deepen global awareness", "Model UN simulation, position papers, resolutions, and awareness campaign completed", "1 simulation; 2 resolutions; 1 campaign"],
    ["Practice transparent governance", "Monthly assemblies held; financial and activity reports submitted", "Monthly; 100% submission"],
    ["Represent the school", "Approved participation in an external Model UN or debate activity", "At least 1, if available; by February 2027"],
], size=9.5)
keep_table_rows(goals)

new_para("MONITORING AND EVALUATION", bold=True, space_before=12, space_after=4, keep=True)
new_para("The President and the faculty adviser shall monitor the implementation of this Plan of Action every month. The Secretary shall maintain a monitoring log of activities, attendance, and outputs, while the Treasurer and the Auditor shall keep the financial records open for review. A mid-cycle review shall be held in January 2027 to assess progress and adjust the remaining activities.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_after=6)
new_para("At the end of the cycle in February 2027, the officers shall submit an annual report containing the accomplishments against the targets, the financial report, and recommendations for the next school year. The report shall be noted by the faculty adviser and furnished to the SSLG and the Office of the Principal.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_after=6)

port = doc.add_section(WD_SECTION.NEW_PAGE)
port.orientation = WD_ORIENT.PORTRAIT
port.page_width = Twips(12240)
port.page_height = Twips(18720)
port.left_margin = Twips(994)
port.right_margin = Twips(994)
port.top_margin = Twips(1440)
port.bottom_margin = Twips(1512)
for el in port._sectPr.findall(qn("w:pgNumType")):
    port._sectPr.remove(el)

# ---------------------------------------------------------------- Annex C
new_para("ANNEX C", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER,
         space_after=6, keep=True)
new_para("FOUNDING MEMBERS AND INTERIM ORGANIZATION", bold=True, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, keep=True)
new_para("Model United Nations Club", bold=True, size=12,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

new_para("The following learners founded the Model United Nations Club. Under Article XIII of the Constitution and By-Laws, they constitute the interim founding body, shall convene the first general assembly, and shall hold no office until the first election.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_after=8)

founders = add_table(4, 3, [205, 145, 108])
fill_table(founders, [
    ["Name", "Role", "Signature"],
    ["AARON Y. HERNANDEZ", "Founding Member", ""],
    ["ELLAINE T. JACOB", "Founding Member", ""],
    ["JOLEX ALEXIER S. CRUZ", "Founding Member", ""],
], size=10.5)
keep_table_rows(founders)

new_para("", space_after=4)
new_para("INTERIM ORGANIZATION", bold=True, space_before=6, space_after=4, keep=True)
new_para("The following positions shall be filled at the first general assembly. Until then, the founders shall perform only the preparatory functions necessary to convene the assembly.",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=36, space_after=6)

positions = add_table(9, 3, [195, 105, 158])
fill_table(positions, [
    ["Position", "Term", "Status"],
    ["President", "One school year", "Vacant - to be elected"],
    ["Vice President", "One school year", "Vacant - to be elected"],
    ["Secretary", "One school year", "Vacant - to be elected"],
    ["Treasurer", "One school year", "Vacant - to be elected"],
    ["Auditor", "One school year", "Vacant - to be elected"],
    ["Public Information Officer", "One school year", "Vacant - to be elected"],
    ["Grade 7 to 12 Representatives (one per grade level)", "One school year", "Vacant - to be elected"],
    ["Faculty Adviser (non-voting)", "Until replaced", "To be designated by the Principal"],
], size=10)
keep_table_rows(positions)

doc.save(DST)

# Restore header/footer parts byte-for-byte after python-docx rewrites them.
def rewrite_parts(src, dst, prefixes):
    with zipfile.ZipFile(src) as zs, zipfile.ZipFile(dst) as zd:
        items = {i.filename: zs.read(i.filename) for i in zs.infolist()}
        out = {i.filename: zd.read(i.filename) for i in zd.infolist()}
        for name in list(out):
            if any(name.startswith(p) for p in prefixes):
                if name in items:
                    out[name] = items[name]
        tmp = dst.with_suffix(".tmp")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zw:
            for name, data in out.items():
                zw.writestr(name, data)
    tmp.replace(dst)

rewrite_parts(SRC, DST, ("word/header", "word/footer"))


def add_landscape_footer(path):
    """Give the Annex B landscape section a footer recentred for a 13-inch page."""
    with zipfile.ZipFile(path) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}

    foot = parts["word/footer1.xml"].decode("utf-8")
    foot = foot.replace(
        '<wp:positionH relativeFrom="page"><wp:posOffset>5693410</wp:posOffset>',
        '<wp:positionH relativeFrom="page"><wp:posOffset>9807580</wp:posOffset>')
    foot = foot.replace(
        '<wp:positionH relativeFrom="margin"><wp:posOffset>2269490</wp:posOffset>',
        '<wp:positionH relativeFrom="margin"><wp:posOffset>3851910</wp:posOffset>')
    parts["word/footer2.xml"] = foot.encode("utf-8")
    parts["word/_rels/footer2.xml.rels"] = parts["word/_rels/footer1.xml.rels"]

    rels = parts["word/_rels/document.xml.rels"].decode("utf-8")
    rels = rels.replace(
        "</Relationships>",
        '<Relationship Id="rIdLandscapeFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer2.xml"/></Relationships>')
    parts["word/_rels/document.xml.rels"] = rels.encode("utf-8")

    types = parts["[Content_Types].xml"].decode("utf-8")
    if "/word/footer2.xml" not in types:
        types = types.replace(
            "</Types>",
            '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
    parts["[Content_Types].xml"] = types.encode("utf-8")

    doc = parts["word/document.xml"].decode("utf-8")

    def landscape_sect(m):
        s = m.group(0)
        ref = "rIdLandscapeFooter" if 'w:orient="landscape"' in s else "rId10"
        if '<w:footerReference w:type="default"' in s or "<w:pgSz " not in s:
            return s
        return s.replace(
            "<w:pgSz ",
            f'<w:footerReference w:type="default" r:id="{ref}"/><w:pgSz ', 1)

    doc = re.sub(r"<w:sectPr[^>]*>.*?</w:sectPr>", landscape_sect, doc, flags=re.S)
    parts["word/document.xml"] = doc.encode("utf-8")

    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zw:
        for name, data in parts.items():
            zw.writestr(name, data)
    tmp.replace(path)


add_landscape_footer(DST)
print("built", DST)
