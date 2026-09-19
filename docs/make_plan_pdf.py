# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase.pdfmetrics import stringWidth

PAGE_W, PAGE_H = A4

DARK = colors.HexColor("#0B1F33")
NAVY = colors.HexColor("#123A5C")
ORANGE = colors.HexColor("#E8722C")
RED = colors.HexColor("#C0392B")
GREEN = colors.HexColor("#1E8449")
LIGHT_BG = colors.HexColor("#F4F6F8")
GREY_TXT = colors.HexColor("#3B3B3B")
WHITE = colors.white

doc = SimpleDocTemplate(
    "BorderWatch_Round2_Plan.pdf",
    pagesize=A4,
    leftMargin=14 * mm, rightMargin=14 * mm,
    topMargin=8 * mm, bottomMargin=8 * mm,
    title="Border-Watch Round 2 Plan",
)

story = []

title_style = ParagraphStyle(
    "title", fontName="Helvetica-Bold", fontSize=21, leading=24,
    textColor=DARK, spaceAfter=0,
)
subtitle_style = ParagraphStyle(
    "subtitle", fontName="Helvetica", fontSize=10.5, leading=13,
    textColor=NAVY, spaceAfter=0,
)
h2 = ParagraphStyle(
    "h2", fontName="Helvetica-Bold", fontSize=11.5, leading=14,
    textColor=WHITE, spaceAfter=0,
)
body = ParagraphStyle(
    "body", fontName="Helvetica", fontSize=9.6, leading=13,
    textColor=GREY_TXT, spaceAfter=0,
)
body_white = ParagraphStyle(
    "body_white", fontName="Helvetica", fontSize=9.6, leading=13,
    textColor=WHITE, spaceAfter=0,
)
small_bold = ParagraphStyle(
    "small_bold", fontName="Helvetica-Bold", fontSize=10.2, leading=13,
    textColor=DARK,
)
feature_head = ParagraphStyle(
    "feature_head", fontName="Helvetica-Bold", fontSize=9, leading=10.5,
    textColor=NAVY, alignment=1,
)
feature_body = ParagraphStyle(
    "feature_body", fontName="Helvetica", fontSize=7.8, leading=10,
    textColor=GREY_TXT, alignment=1,
)

# ---------- Header ----------
story.append(Paragraph("BORDER-WATCH &mdash; ROUND 2 PLAN", title_style))
story.append(Paragraph(
    "Team ENDGAME ENCORE &nbsp;|&nbsp; SIH 2026, PS #26187 &nbsp;|&nbsp; "
    "Ready by 20 Sep, Demo 21 Sep", subtitle_style,
))
story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=1.4, color=ORANGE))
story.append(Spacer(1, 6))

# ---------- What we're building ----------
def section_header(text, bg=NAVY):
    t = Table([[Paragraph(text, h2)]], colWidths=[doc.width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

story.append(section_header("WHAT WE ARE BUILDING"))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "Today, our system makes you <b>upload a video and wait</b> for the AI to finish before you "
    "see anything. For Round 2 we are upgrading it to run <b>LIVE</b> &mdash; like a real "
    "security control room. The camera feed appears on screen instantly, and everything the AI "
    "already does well &mdash; recognising a target person's face, reading vehicle number plates, "
    "spotting someone entering a restricted zone, flagging suspicious movement &mdash; now happens "
    "<b>in real time</b>, with instant alerts, instead of after the fact.",
    body,
))
story.append(Spacer(1, 5))

# ---------- Why not NVIDIA ----------
story.append(section_header("WHY WE ARE NOT USING NVIDIA / HEAVY ENTERPRISE SOFTWARE", bg=RED))
story.append(Spacer(1, 4))
why_rows = [
    [Paragraph("&#10007;", ParagraphStyle("x", parent=body, textColor=RED, fontName="Helvetica-Bold", fontSize=11)),
     Paragraph("<b>Wrong hardware.</b> Tools like NVIDIA DeepStream / TensorRT only run on NVIDIA "
               "graphics cards. Our laptops don't have one &mdash; it's simply not possible to run "
               "them here, no matter how much time we had.", body)],
    [Paragraph("&#10007;", ParagraphStyle("x2", parent=body, textColor=RED, fontName="Helvetica-Bold", fontSize=11)),
     Paragraph("<b>Built for a different job.</b> That stack is designed for big companies running "
               "hundreds of cameras across many sites &mdash; not a 3-day hackathon build by one person.", body)],
    [Paragraph("&#10007;", ParagraphStyle("x3", parent=body, textColor=RED, fontName="Helvetica-Bold", fontSize=11)),
     Paragraph("<b>Too slow to learn.</b> Even with the right hardware, learning and wiring up that "
               "software properly takes weeks. We have 3 days.", body)],
]
t = Table(why_rows, colWidths=[10 * mm, doc.width - 10 * mm])
t.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 2),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(t)
story.append(Spacer(1, 3))
story.append(Paragraph(
    "<b>The good news:</b> we already have a working, tested AI engine (weeks of real work: face "
    "recognition, number-plate reading, zone alerts, night-vision, behaviour analysis). Instead of "
    "throwing that away to learn brand-new complex tools in 3 days, we're keeping everything that "
    "already works and simply connecting it to a live camera instead of an uploaded file. "
    "<b>Faster, safer, and still genuinely impressive.</b>",
    body,
))
story.append(Spacer(1, 5))

# ---------- 3-day plan ----------
story.append(section_header("THE 3-DAY PLAN", bg=NAVY))
story.append(Spacer(1, 4))

day_data = [
    [Paragraph("<b>DAY 1</b>", small_bold), Paragraph("17-18 Sep", body),
     Paragraph("Get a live camera video showing up on screen &mdash; the video plays live, "
               "just like a real CCTV monitor, with nothing uploaded or waited for.", body)],
    [Paragraph("<b>DAY 2</b>", small_bold), Paragraph("19 Sep", body),
     Paragraph("Plug in our existing AI: live face recognition, target tracking, restricted-zone "
               "alerts, number-plate reading. Add the <b>siren</b> (see below). Build the on-screen "
               "live dashboard.", body)],
    [Paragraph("<b>DAY 3</b>", small_bold), Paragraph("20 Sep", body),
     Paragraph("No new features &mdash; only testing, rehearsing the demo, and recording a backup "
               "video in case anything glitches live on stage.", body)],
]
t = Table(day_data, colWidths=[22 * mm, 22 * mm, doc.width - 44 * mm])
t.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6DCE1")),
    ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6DCE1")),
    ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 5))

# ---------- Siren + Bottom line side by side ----------
siren_block = [
    Paragraph("NEW FEATURE &mdash; THE SIREN", ParagraphStyle(
        "sh", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE)),
    Spacer(1, 3),
    Paragraph(
        "When the system spots our target person crossing into a restricted zone, a phone placed "
        "nearby <b>physically buzzes and alarms out loud</b> &mdash; just like a real border-post "
        "siren. No special hardware needed, just a spare phone.",
        body_white,
    ),
]
bottom_block = [
    Paragraph("BOTTOM LINE", ParagraphStyle(
        "bh", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE)),
    Spacer(1, 3),
    Paragraph(
        "We are not making the project smaller. We are making it <b>real</b>: live video, the "
        "same powerful AI, running on the laptops we already have &mdash; ready by 20 September.",
        body_white,
    ),
]

col_w = (doc.width - 6 * mm) / 2
t = Table([[siren_block, bottom_block]], colWidths=[col_w, col_w])
t.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (0, 0), ORANGE),
    ("BACKGROUND", (1, 0), (1, 0), GREEN),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(Table([[t]], colWidths=[doc.width], style=TableStyle([
    ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
])))
story.append(Spacer(1, 6))

# ---------- What stays exactly the same ----------
story.append(section_header("WHAT STAYS EXACTLY THE SAME (NOT THROWN AWAY)", bg=DARK))
story.append(Spacer(1, 6))
kept_items = [
    ("Face\nRecognition", "Finds a specific\nwanted person"),
    ("Number Plate\nReading (ANPR)", "Reads vehicle\nplates automatically"),
    ("Zone\nAlerts", "Flags anyone entering\na restricted area"),
    ("Night\nVision", "Enhances footage\nin the dark"),
    ("Suspicious\nBehaviour", "Loitering, pacing,\nsudden movement"),
]
cells = []
for head, sub in kept_items:
    cells.append(Table(
        [[Paragraph(head.replace("\n", "<br/>"), feature_head)],
         [Paragraph(sub.replace("\n", "<br/>"), feature_body)]],
        colWidths=[(doc.width - 16 * mm) / 5],
        style=TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]),
    ))
row = Table([cells], colWidths=[(doc.width - 16 * mm) / 5] * 5)
row.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6DCE1")),
    ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6DCE1")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(row)
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D6DCE1")))
story.append(Spacer(1, 5))
story.append(Paragraph(
    "Only the video source and the on-screen result are changing &mdash; from \"upload a file, "
    "wait, watch later\" to \"connect a live camera, see it happen now.\" Every AI module above "
    "keeps running exactly as already built and tested.",
    ParagraphStyle("footnote", fontName="Helvetica-Oblique", fontSize=9, leading=12,
                   textColor=colors.HexColor("#6B6B6B")),
))

doc.build(story)
print("done")
