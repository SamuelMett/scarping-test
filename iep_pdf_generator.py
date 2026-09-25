"""
IEP PDF Generator
Reads IEP_Test_Data.xlsx and creates:
  1. Compliance Status Report   (one per student)
  2. Parent Meeting Notice      (one per student)
  3. Case Manager Caseload      (one per case manager of those students)

Install once:  pip install -r requirements.txt
Run:           python iep_pdf_generator.py
"""

import os
import re
from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ======================== SETTINGS ========================
INPUT_FILE = "IEP_Test_Data.xlsx"
OUTPUT_DIR = "output_pdfs"
NUM_STUDENTS = 10          # change to 566 (or None) to run all students
TODAY = date.today()       # or set a fixed date, e.g. date(2026, 9, 24)
DUE_SOON_DAYS = 30         # "Due Soon" window
# ==========================================================

NAVY = colors.HexColor("#1F3864")
RED = colors.HexColor("#C00000")
YELLOW = colors.HexColor("#BF8F00")
GREEN = colors.HexColor("#2E7D32")
LIGHT = colors.HexColor("#F2F4F8")

styles = getSampleStyleSheet()
TITLE = ParagraphStyle("T", parent=styles["Title"], textColor=NAVY, fontSize=18)
SUB = ParagraphStyle("S", parent=styles["Normal"], alignment=TA_CENTER, textColor=colors.grey)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=NAVY)
BODY = ParagraphStyle("B", parent=styles["Normal"], fontSize=11, leading=16)
SMALL = ParagraphStyle("Sm", parent=styles["Normal"], fontSize=8, textColor=colors.grey)


# ---------------------- helpers ----------------------
def load_data(path):
    df = pd.read_excel(path)
    for col in ["DOB", "IEP Due Date", "IEP Reevaluation Date"]:
        df[col] = pd.to_datetime(df[col]).dt.date
    df["Grade Level"] = df["Grade Level"].astype(str)
    return df


def first_last(name):
    """'Garcia, Liam' -> 'Liam Garcia'"""
    parts = [p.strip() for p in str(name).split(",")]
    return f"{parts[1]} {parts[0]}" if len(parts) == 2 else name


def safe_filename(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


def fmt(d):
    return d.strftime("%m/%d/%Y")


def age_on(dob, on):
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


def status(due):
    days = (due - TODAY).days
    if days < 0:
        return "OVERDUE", RED, days
    if days <= DUE_SOON_DAYS:
        return "DUE SOON", YELLOW, days
    return "ON TRACK", GREEN, days


def days_text(days):
    if days < 0:
        return f"{abs(days)} days overdue"
    if days == 0:
        return "Due today"
    return f"{days} days remaining"


def grade_text(g):
    return "Kindergarten" if g == "K" else f"Grade {g}"


def info_table(rows, col_widths=(2.2 * inch, 4.3 * inch)):
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def footer():
    return Paragraph(
        f"Generated {fmt(TODAY)} | CONFIDENTIAL - Contains student information protected under FERPA/IDEA "
        f"| TEST DATA ONLY", SMALL)


def build(path, story):
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    doc.build(story)


# ---------------------- 1. Compliance report ----------------------
def compliance_report(s, out_dir):
    iep_label, iep_color, iep_days = status(s["IEP Due Date"])
    re_label, re_color, re_days = status(s["IEP Reevaluation Date"])

    story = [
        Paragraph("IEP Compliance Status Report", TITLE),
        Paragraph(s["School Name"], SUB),
        Spacer(1, 16),
        Paragraph("Student Information", H2),
        info_table([
            ["Student Name", s["Student Name"]],
            ["Date of Birth", f"{fmt(s['DOB'])}  (Age {age_on(s['DOB'], TODAY)})"],
            ["Grade Level", grade_text(s["Grade Level"])],
            ["School", s["School Name"]],
            ["Primary Disability", s["Disability"]],
            ["Case Manager", first_last(s["Case Manager"])],
        ]),
        Spacer(1, 16),
        Paragraph("Compliance Status", H2),
    ]

    t = Table([
        ["Requirement", "Due Date", "Time Remaining", "Status"],
        ["Annual IEP Review", fmt(s["IEP Due Date"]), days_text(iep_days), iep_label],
        ["Triennial Reevaluation", fmt(s["IEP Reevaluation Date"]), days_text(re_days), re_label],
    ], colWidths=[1.9 * inch, 1.3 * inch, 1.8 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (3, 1), (3, 1), iep_color),
        ("BACKGROUND", (3, 2), (3, 2), re_color),
        ("TEXTCOLOR", (3, 1), (3, 2), colors.white),
        ("FONTNAME", (3, 1), (3, 2), "Helvetica-Bold"),
    ]))
    story += [t, Spacer(1, 16), Paragraph("Action Needed", H2)]

    actions = []
    if iep_label == "OVERDUE":
        actions.append("Annual IEP review is past due. Schedule the meeting immediately.")
    elif iep_label == "DUE SOON":
        actions.append("Annual IEP review is due within 30 days. Send the parent meeting notice now.")
    if re_label == "OVERDUE":
        actions.append("Triennial reevaluation is past due. Obtain consent and begin evaluation.")
    elif re_label == "DUE SOON":
        actions.append("Triennial reevaluation is due within 30 days. Confirm evaluations are scheduled.")
    elif re_days <= 90:
        actions.append("Reevaluation due within 90 days. Request parent consent for evaluation.")
    if not actions:
        actions.append("No immediate action required. All deadlines are on track.")
    for a in actions:
        story.append(Paragraph(f"&bull; {a}", BODY))

    story += [Spacer(1, 30), footer()]
    path = os.path.join(out_dir, f"Compliance_{safe_filename(s['Student Name'])}.pdf")
    build(path, story)
    return path


# ---------------------- 2. Parent notice ----------------------
def parent_notice(s, out_dir):
    child = first_last(s["Student Name"])
    cm = first_last(s["Case Manager"])
    _, _, re_days = status(s["IEP Reevaluation Date"])
    reeval_line = ""
    if re_days <= 120:
        reeval_line = (f" In addition, {child}'s three-year reevaluation is due by "
                       f"<b>{fmt(s['IEP Reevaluation Date'])}</b>. We will discuss this at the meeting "
                       f"and may ask for your written consent to conduct updated evaluations.")

    story = [
        Paragraph(s["School Name"], TITLE),
        Paragraph("Exceptional Student Education", SUB),
        Spacer(1, 24),
        Paragraph(TODAY.strftime("%B %d, %Y"), BODY),
        Spacer(1, 12),
        Paragraph(f"To the Parent/Guardian of <b>{child}</b>", BODY),
        Spacer(1, 12),
        Paragraph("<b>RE: Notice of Annual IEP Review Meeting</b>", BODY),
        Spacer(1, 12),
        Paragraph(
            f"Dear Parent/Guardian,<br/><br/>"
            f"This letter is to let you know that {child}'s Individualized Education Program (IEP) "
            f"is due for its annual review by <b>{fmt(s['IEP Due Date'])}</b>. At this meeting, the IEP "
            f"team will review {child}'s progress, discuss current needs, and update goals and services "
            f"for the coming year.{reeval_line}", BODY),
        Spacer(1, 12),
        Paragraph(
            "Your participation is very important. You are a key member of the IEP team, and your "
            "input helps us plan the best supports for your child. Please contact the case manager "
            "below to schedule a date and time that works for you.", BODY),
        Spacer(1, 16),
        info_table([
            ["Student", child],
            ["Grade", grade_text(s["Grade Level"])],
            ["IEP Review Due By", fmt(s["IEP Due Date"])],
            ["Case Manager", cm],
            ["School", s["School Name"]],
        ]),
        Spacer(1, 16),
        Paragraph(
            "You have the right to invite others who have knowledge or special expertise about your "
            "child to the meeting. A copy of your Procedural Safeguards is available upon request.", BODY),
        Spacer(1, 24),
        Paragraph(f"Sincerely,<br/><br/>{cm}<br/>ESE Case Manager, {s['School Name']}", BODY),
        Spacer(1, 30),
        footer(),
    ]
    path = os.path.join(out_dir, f"ParentNotice_{safe_filename(s['Student Name'])}.pdf")
    build(path, story)
    return path


# ---------------------- 3. Caseload report ----------------------
def caseload_report(cm_name, caseload, out_dir):
    caseload = caseload.sort_values("IEP Due Date")
    counts = {"OVERDUE": 0, "DUE SOON": 0, "ON TRACK": 0}

    rows = [["Student", "Grade", "Disability", "IEP Due", "Reeval Due", "Status"]]
    row_colors = []
    for i, (_, s) in enumerate(caseload.iterrows(), start=1):
        iep = status(s["IEP Due Date"])
        re_ = status(s["IEP Reevaluation Date"])
        worst = iep if iep[2] <= re_[2] else re_   # whichever deadline is closer
        counts[worst[0]] += 1
        rows.append([
            Paragraph(s["Student Name"], ParagraphStyle("c", fontSize=8.5)),
            s["Grade Level"],
            Paragraph(s["Disability"], ParagraphStyle("c", fontSize=8.5)),
            fmt(s["IEP Due Date"]),
            fmt(s["IEP Reevaluation Date"]),
            worst[0],
        ])
        row_colors.append(("BACKGROUND", (5, i), (5, i), worst[1]))

    summary = info_table([
        ["Case Manager", first_last(cm_name)],
        ["School(s)", ", ".join(sorted(caseload["School Name"].unique()))],
        ["Total Students", str(len(caseload))],
        ["Overdue / Due Soon / On Track",
         f"{counts['OVERDUE']} / {counts['DUE SOON']} / {counts['ON TRACK']}"],
    ])

    t = Table(rows, colWidths=[1.6 * inch, 0.55 * inch, 1.75 * inch, 0.9 * inch, 0.9 * inch, 0.95 * inch],
              repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (5, 1), (5, -1), colors.white),
        ("FONTNAME", (5, 1), (5, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (4, -1), [colors.white, LIGHT]),
    ] + row_colors))

    story = [
        Paragraph("Case Manager Caseload Report", TITLE),
        Paragraph(f"As of {fmt(TODAY)} - sorted by soonest IEP due date", SUB),
        Spacer(1, 16),
        summary,
        Spacer(1, 16),
        t,
        Spacer(1, 20),
        footer(),
    ]
    path = os.path.join(out_dir, f"Caseload_{safe_filename(cm_name)}.pdf")
    build(path, story)
    return path


# ---------------------- main ----------------------
def main():
    df = load_data(INPUT_FILE)
    students = df.head(NUM_STUDENTS) if NUM_STUDENTS else df

    dirs = {k: os.path.join(OUTPUT_DIR, k) for k in ["compliance", "parent_notices", "caseloads"]}
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    print(f"Loaded {len(df)} students. Processing {len(students)}...\n")

    for _, s in students.iterrows():
        compliance_report(s, dirs["compliance"])
        parent_notice(s, dirs["parent_notices"])
        print(f"  [OK] {s['Student Name']}")

    # caseload report for each case manager who has a student in this batch
    for cm in students["Case Manager"].unique():
        caseload_report(cm, df[df["Case Manager"] == cm], dirs["caseloads"])
        print(f"  [OK] Caseload: {cm}")

    print(f"\nDone. PDFs saved to ./{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
