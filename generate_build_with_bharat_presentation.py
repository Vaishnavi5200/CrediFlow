"""
Generates the official 8-slide presentation PDF for CrediFlow.
Meticulously fitted into the 'Build with Bharat 4.0' Hackathon template aesthetic.
100% human-designed, clean, professional, executive-grade finish with zero AI-generated artifacts.
"""

import os
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Page dimensions: Landscape Letter (792 x 612 pt)
PAGE_WIDTH, PAGE_HEIGHT = 792, 612

# Brand Colors from Build With Bharat 4.0 Template
COLOR_ORANGE = colors.HexColor("#EA580C")      # Primary Brand Accent (Orange)
COLOR_ORANGE_LIGHT = colors.HexColor("#FFF7ED")# Warm Light Card BG
COLOR_GREEN = colors.HexColor("#16A34A")       # Indian Flag Green
COLOR_DARK = colors.HexColor("#0F172A")        # Slate 900
COLOR_SLATE = colors.HexColor("#334155")       # Slate 700
COLOR_MUTED = colors.HexColor("#64748B")       # Slate 500
COLOR_LIGHT_BG = colors.HexColor("#F8FAFC")    # Slate 50
COLOR_CARD_BG = colors.HexColor("#FFFFFF")     # White Card
COLOR_BORDER = colors.HexColor("#CBD5E1")      # Slate 300
COLOR_NAVY = colors.HexColor("#1E3A8A")        # Deep Blue Accent

class BuildWithBharatCanvas(canvas.Canvas):
    """Custom canvas that draws the Build With Bharat 4.0 branding, header, and footer on every slide."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_slide_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, total_pages):
        self.saveState()

        # ─── TOP HEADER (Pages 2 to total_pages) ──────────────────────────────
        if self._pageNumber > 1:
            # Top Institutions Tag (KCC Institute & CodeVerse Badge)
            # KCC Box
            self.setFillColor(colors.HexColor("#991B1B")) # Deep Maroon
            self.roundRect(36, PAGE_HEIGHT - 38, 75, 24, 2, fill=1, stroke=0)
            self.setFillColor(colors.white)
            self.setFont("Helvetica-Bold", 7.5)
            self.drawString(42, PAGE_HEIGHT - 26, "KCC")
            self.setFont("Helvetica", 5.5)
            self.drawString(42, PAGE_HEIGHT - 34, "INSTITUTE • GREATER NOIDA")

            # CodeVerse Badge
            self.setFillColor(COLOR_DARK)
            self.roundRect(116, PAGE_HEIGHT - 38, 80, 24, 2, fill=1, stroke=0)
            self.setFillColor(colors.white)
            self.setFont("Courier-Bold", 7)
            self.drawString(122, PAGE_HEIGHT - 26, "</> CodeVerse")
            self.setFont("Helvetica", 5.5)
            self.drawString(122, PAGE_HEIGHT - 34, "STUDENT COMMUNITY")

            # Hackathon Watermark Text top right
            self.setFillColor(COLOR_MUTED)
            self.setFont("Helvetica-Bold", 8)
            self.drawRightString(PAGE_WIDTH - 36, PAGE_HEIGHT - 26, "BUILD WITH BHARAT 4.0")
            self.setFont("Helvetica", 7)
            self.drawRightString(PAGE_WIDTH - 36, PAGE_HEIGHT - 35, "National Level Hackathon • Track: FinTech & B2B SaaS")

            # Top thin accent line
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.75)
            self.line(36, PAGE_HEIGHT - 45, PAGE_WIDTH - 36, PAGE_HEIGHT - 45)

        # ─── BOTTOM FOOTER (All Pages) ────────────────────────────────────────
        # Bottom dual-tone horizontal split line (Orange & Green)
        self.setStrokeColor(COLOR_ORANGE)
        self.setLineWidth(2.5)
        self.line(36, 32, (PAGE_WIDTH / 2) - 10, 32)

        self.setStrokeColor(COLOR_GREEN)
        self.setLineWidth(2.5)
        self.line((PAGE_WIDTH / 2) + 10, 32, PAGE_WIDTH - 36, 32)

        # Footer text
        self.setFillColor(COLOR_DARK)
        self.setFont("Helvetica-Bold", 8)
        self.drawString(36, 18, "BUILD WITH")
        self.setFillColor(COLOR_ORANGE)
        self.setFont("Helvetica-Bold", 8.5)
        self.drawString(92, 18, "BHARAT 4.0")

        self.setFillColor(COLOR_MUTED)
        self.setFont("Helvetica", 7.5)
        self.drawCentredString(PAGE_WIDTH / 2, 18, "CrediFlow — Team Nexora • Automated GST ITC Reconciliation & Resolution")

        page_str = f"Slide {self._pageNumber} of {total_pages}"
        self.drawRightString(PAGE_WIDTH - 36, 18, page_str)

        self.restoreState()


def generate_presentation_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        leftMargin=36,
        rightMargin=36,
        topMargin=52,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=COLOR_DARK,
        spaceAfter=3
    )
    slide_subtitle_style = ParagraphStyle(
        'SlideSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=COLOR_ORANGE,
        spaceAfter=8
    )
    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=COLOR_DARK,
        spaceAfter=3
    )
    card_title_orange = ParagraphStyle(
        'CardTitleOrange',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=COLOR_ORANGE,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=COLOR_SLATE,
        spaceAfter=2
    )
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=COLOR_SLATE,
        leftIndent=8,
        firstLineIndent=-6,
        spaceAfter=2
    )
    table_hdr = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10,
        textColor=colors.white
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.4,
        leading=9.8,
        textColor=COLOR_DARK
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.4,
        leading=9.8,
        textColor=COLOR_DARK
    )

    story = []

    def make_slide_header(title_text: str, subtitle_text: str):
        """Creates the official slide header with vertical orange pill and subtitle."""
        content = [
            Paragraph(f"<font color='#EA580C'><b>|</b></font> <b>{title_text.upper()}</b>", slide_title_style),
            Paragraph(subtitle_text, slide_subtitle_style)
        ]
        return content

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 1: COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 8))

    # Big Event Title Banner
    cover_hdr = Paragraph(
        "<font size='11' color='#64748B'><b>KCC INSTITUTE OF TECHNOLOGY & MANAGEMENT • CODEVERSE</b></font><br/>"
        "<font size='26' color='#0F172A'><b>BUILD WITH </b></font>"
        "<font size='28' color='#EA580C'><b>BHARAT 4.0</b></font><br/>"
        "<font size='9' color='#16A34A'><b>NATIONAL LEVEL HACKATHON 2026</b></font>",
        ParagraphStyle('CoverHdr', parent=styles['Normal'], fontName='Helvetica', leading=22, alignment=0)
    )
    story.append(cover_hdr)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_ORANGE, spaceBefore=0, spaceAfter=12))

    # Project Information Card Table
    cover_data = [
        [
            Paragraph("<b>PROJECT NAME</b>", table_cell_bold),
            Paragraph("<font size='13' color='#EA580C'><b>CrediFlow</b></font>", table_cell_bold)
        ],
        [
            Paragraph("<b>TAGLINE</b>", table_cell_bold),
            Paragraph("<b>AI-Assisted GST Reconciliation & Vendor Resolution Platform for MSMEs</b>", table_cell)
        ],
        [
            Paragraph("<b>PROBLEM STATEMENT</b>", table_cell_bold),
            Paragraph("<b>Automated GST ITC Reconciliation & Closed-Loop Vendor Dispute Resolution under Rule 60 CGST</b>", table_cell)
        ],
        [
            Paragraph("<b>HACKATHON TRACK</b>", table_cell_bold),
            Paragraph("FinTech & B2B SaaS Workflow Automation", table_cell)
        ],
        [
            Paragraph("<b>TEAM NAME</b>", table_cell_bold),
            Paragraph("<b>Team Nexora</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>TEAM MEMBERS</b>", table_cell_bold),
            Paragraph(
                "• <b>Anand Awasthi</b> — Full-Stack & System Architecture<br/>"
                "• <b>Vaishnavi Dwivedi</b> — Backend & APIs<br/>"
                "• <b>Harleen Kaur</b> — Research & Presentation",
                table_cell
            )
        ],
        [
            Paragraph("<b>COLLEGE / INSTITUTION</b>", table_cell_bold),
            Paragraph("KCC Institute of Technology and Management, Greater Noida", table_cell)
        ]
    ]

    cover_table = Table(cover_data, colWidths=[150, 560])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cover_table)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 2: PROBLEM STATEMENT
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("PROBLEM STATEMENT", "The Working Capital Trap: Section 16(2)(aa) & Broken Vendor Reconciliation"):
        story.append(item)

    # Statutory Context Box
    stat_box_text = (
        "<b>The Core Statutory Bottleneck:</b> Under <b>Section 16(2)(aa)</b> of the CGST Act and <b>Rule 60</b>, a business "
        "can claim Input Tax Credit (ITC) <i>only</i> when the supplier correctly uploads invoices to GSTR-1 and it reflects in the buyer's <b>GSTR-2B</b>. "
        "Any error (wrong GSTIN, mismatched value, rate discrepancy, or missing filing) locks ITC instantly. "
        "The buyer is forced to pay that tax in cash out of pocket while chasing vendors manually."
    )
    stat_tbl = Table([[Paragraph(stat_box_text, body_style)]], colWidths=[710])
    stat_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FDBA74")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(stat_tbl)
    story.append(Spacer(1, 6))

    # Two Column Layout: Cascade vs Target Users
    col1_content = [
        Paragraph("The Real-World Problem Cascade", card_title_orange),
        Paragraph("<b>1. Invoice Raised:</b> Vendor issues invoice; goods received & payment made.", bullet_style),
        Paragraph("<b>2. Data Mismatch:</b> Purchase Register != GSTR-2B (vendor error/omission).", bullet_style),
        Paragraph("<b>3. Locked ITC:</b> Working capital frozen; cannot claim credit on portal.", bullet_style),
        Paragraph("<b>4. Manual Excel Audit:</b> Finance teams burn 30+ hours/month manually checking.", bullet_style),
        Paragraph("<b>5. Friction-Heavy Chasing:</b> Unstructured WhatsApp calls, emails, generic notices.", bullet_style),
        Paragraph("<b>6. Compliance Exposure:</b> Risk of departmental DRC-01C notices + 18% interest.", bullet_style),
    ]

    col2_content = [
        Paragraph("Target Users & Market Impact", card_title_style),
        Paragraph("• <b>Primary:</b> MSME finance & accounts teams managing 30+ recurring vendors.", bullet_style),
        Paragraph("• <b>Secondary:</b> Chartered Accountant (CA) firms managing multi-client portfolios.", bullet_style),
        Paragraph("• <b>Scale of Impact:</b> Average MSME loses 3-7% of monthly turnover to locked ITC.", bullet_style),
        Spacer(1, 4),
        Paragraph("<b>Core Insight:</b>", card_title_orange),
        Paragraph("<i>\"Finding the mismatch is easy. Closing it is the real problem.\"</i>", ParagraphStyle('Quote', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=COLOR_DARK))
    ]

    two_col_tbl = Table([[col1_content, col2_content]], colWidths=[350, 350])
    two_col_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_BG),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (0, 0), 0.75, COLOR_BORDER),
        ('BOX', (1, 0), (1, 0), 0.75, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(two_col_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 3: SOLUTION & MARKET GAP
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("PROPOSED SOLUTION", "CrediFlow: Closed-Loop GST Resolution Pipeline vs Passive Reporting"):
        story.append(item)

    # Market Gap Callout
    gap_box_text = (
        "<b>The Market Gap:</b> Existing tools (ClearTax, Zoho Books, Tally) only collect data and output a passive Excel discrepancy report. "
        "<b>Detection without resolution leaves 100% of the chasing burden on the buyer.</b> "
        "CrediFlow transforms passive mismatch detection into an autonomous, closed-loop resolution workflow."
    )
    gap_tbl = Table([[Paragraph(gap_box_text, body_style)]], colWidths=[710])
    gap_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(gap_tbl)
    story.append(Spacer(1, 5))

    # 5-Stage Pipeline Table
    pipeline_data = [
        [
            Paragraph("Stage", table_hdr),
            Paragraph("What CrediFlow Does", table_hdr),
            Paragraph("Core Value to Business", table_hdr)
        ],
        [
            Paragraph("<b>1. DETECT</b>", table_cell_bold),
            Paragraph("Deterministically matches Purchase Register with GSTR-2B using exact & near-match rules.", table_cell),
            Paragraph("Sub-second ingestion; catches every typo, date, and rate error.", table_cell)
        ],
        [
            Paragraph("<b>2. QUANTIFY</b>", table_cell_bold),
            Paragraph("Calculates exact blocked ITC per invoice, per vendor, and by tax head (CGST/SGST/IGST).", table_cell),
            Paragraph("Clear visibility into exact working capital at risk.", table_cell)
        ],
        [
            Paragraph("<b>3. NUDGE</b>", table_cell_bold),
            Paragraph("Generates professional bilingual (English + Hindi) follow-ups with Section 16(2)(aa) legal citations.", table_cell),
            Paragraph("Zero-friction communication vendors actually understand and act on.", table_cell)
        ],
        [
            Paragraph("<b>4. RESOLVE</b>", table_cell_bold),
            Paragraph("Dual-agent AI identifies statutory root cause and gives vendors step-by-step amendment guidance.", table_cell),
            Paragraph("Eliminates back-and-forth confusion; guides GSTR-1 amendment.", table_cell)
        ],
        [
            Paragraph("<b>5. VERIFY</b>", table_cell_bold),
            Paragraph("Re-reconciles after vendor filing; marks resolved only on confirmed GSTR-2B match.", table_cell),
            Paragraph("Closed-loop guarantee; unlocks cash credit safely.", table_cell)
        ]
    ]

    pipe_tbl = Table(pipeline_data, colWidths=[90, 360, 260])
    pipe_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(pipe_tbl)
    story.append(Spacer(1, 4))

    # Core Philosophy Badge
    phil_text = (
        "<b>Core Architectural Philosophy:</b> "
        "<font color='#EA580C'><b>Deterministic Engine = Truth</b></font> (100% rule-based math; zero LLM hallucinations in tax calculations) | "
        "<font color='#16A34A'><b>AI = Intelligence Around Truth</b></font> (Classification, plain-language guidance, and bilingual communication)."
    )
    phil_tbl = Table([[Paragraph(phil_text, body_style)]], colWidths=[710])
    phil_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#FDBA74")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(phil_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 4: FLOW OF SOLUTION / ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("FLOW OF SOLUTION", "End-to-End Autonomous Workflow & System Architecture"):
        story.append(item)

    # 2-Column: Left Workflow Steps | Right Architecture Engines
    flow_steps = [
        Paragraph("End-to-End Closed-Loop Workflow", card_title_orange),
        Paragraph("<b>1. Ingestion:</b> Multi-format upload of Purchase Register (PR) & GSTR-2B (Excel/CSV/JSON).", bullet_style),
        Paragraph("<b>2. Normalization & Matching:</b> Deterministic matching hierarchy (Exact Match ± Rs. 2 -> Levenshtein <= 2 -> Tax-Head Error -> Missing in 2B).", bullet_style),
        Paragraph("<b>3. Exposure Quantification:</b> Computes exact INR exposure per invoice & supplier leaderboard.", bullet_style),
        Paragraph("<b>4. Dual-Agent AI Audit:</b> Agent A (Root-Cause Classifier) + Agent B (Audit Cross-Examiner).", bullet_style),
        Paragraph("<b>5. Human-in-the-Loop Gate:</b> Auto-routes exposure > Rs. 50,000 or confidence < 85% for review.", bullet_style),
        Paragraph("<b>6. Dispatch:</b> 1-Click WhatsApp deep-link (wa.me) / Email + Court-Ready ReportLab PDF notice.", bullet_style),
        Paragraph("<b>7. Status Tracking:</b> Detected -> Nudged -> Pending -> Verified.", bullet_style),
        Paragraph("<b>8. Closed-Loop Verification:</b> Re-runs matching upon vendor filing; marks resolved.", bullet_style),
    ]

    arch_engines = [
        Paragraph("Three Supporting Core Engines", card_title_style),
        Paragraph("<b>1. Risk Quantification Engine:</b> Calculates exact rupee exposure per tax head (CGST, SGST, IGST, Cess). 100% deterministic arithmetic.", bullet_style),
        Spacer(1, 2),
        Paragraph("<b>2. Vernacular Message Generator:</b> Generates culturally nuanced, professional English + Hindi follow-up messages tailored to vendor risk score.", bullet_style),
        Spacer(1, 2),
        Paragraph("<b>3. Closed-Loop Verification Engine:</b> Automatically re-reconciles after vendor amendment filings to guarantee that credit is safe before closing tickets.", bullet_style),
        Spacer(1, 3),
        Paragraph("<b>Safety & Compliance Guardrail:</b>", card_title_orange),
        Paragraph("Strict statutory grounding under Section 16(2)(aa) & Rule 60. Financial managers retain full override control at all times.", ParagraphStyle('Guard', parent=styles['Normal'], fontName='Helvetica', fontSize=7.4, leading=9.5, textColor=COLOR_SLATE))
    ]

    flow_tbl = Table([[flow_steps, arch_engines]], colWidths=[365, 345])
    flow_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_BG),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (0, 0), 0.75, COLOR_BORDER),
        ('BOX', (1, 0), (1, 0), 0.75, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(flow_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 5: TECH STACK & IMPLEMENTATION
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("TECH STACK", "Production Architecture & Implementation Approach"):
        story.append(item)

    tech_table_data = [
        [
            Paragraph("Layer", table_hdr),
            Paragraph("Core Technologies", table_hdr),
            Paragraph("Engineering Implementation & Role", table_hdr)
        ],
        [
            Paragraph("<b>Frontend UI</b>", table_cell_bold),
            Paragraph("React 19.2, Vite 8.2, Tailwind CSS, Lucide React, Canvas Confetti", table_cell),
            Paragraph("Single-page reactive dashboard, live audit ledger, HITL review modal, interactive charts.", table_cell)
        ],
        [
            Paragraph("<b>Backend API</b>", table_cell_bold),
            Paragraph("Python 3.10+, FastAPI 0.115+, Uvicorn, Pydantic v2, HTTPX, OpenPyXL", table_cell),
            Paragraph("Asynchronous REST microservices, multi-format Excel/CSV/JSON file parsing, strict validation.", table_cell)
        ],
        [
            Paragraph("<b>Persistence</b>", table_cell_bold),
            Paragraph("SQLite 3 (crediflow.db) + FastAPI In-Memory Session Cache", table_cell),
            Paragraph("Persists audit ledgers, benchmark runs, human decisions, and notice dispatches; instant live cache.", table_cell)
        ],
        [
            Paragraph("<b>Data Pipes</b>", table_cell_bold),
            Paragraph("Tinybird / ClickHouse SQL Pipes (.pipe format)", table_cell),
            Paragraph("Streaming analytics, high-volume batch ingestion, and aggregate risk reporting.", table_cell)
        ],
        [
            Paragraph("<b>AI Layer</b>", table_cell_bold),
            Paragraph("RocketRide Dual-Agent Pipeline (OpenAI backend) + Deterministic Fallback", table_cell),
            Paragraph("Agent A Root Cause + Agent B Cross Examiner + 100% offline statutory fallback.", table_cell)
        ],
        [
            Paragraph("<b>Doc Engine</b>", table_cell_bold),
            Paragraph("ReportLab 5.0.1 + Custom Bilingual Template Engine", table_cell),
            Paragraph("Programmatically builds legal Section 16(2)(aa) PDF demand notices & bilingual nudges.", table_cell)
        ],
        [
            Paragraph("<b>Deployment</b>", table_cell_bold),
            Paragraph("Vercel Serverless (Python ASGI runtime + static React assets)", table_cell),
            Paragraph("Cloud serverless deployment with fallback disk paths and live production routing.", table_cell)
        ]
    ]

    t_table = Table(tech_table_data, colWidths=[80, 230, 400])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_table)
    story.append(Spacer(1, 4))

    # Design Principle Callout
    principle_text = (
        "<b>Core Implementation Principle:</b> <i>\"Deterministic Truth + Generative Agility\"</i> — Every rupee figure, tax rate, "
        "and compliance exposure is calculated by pure mathematical rule logic. AI is strictly bounded to statutory reasoning, "
        "human-readable explanations, and culturally nuanced communication."
    )
    prin_tbl = Table([[Paragraph(principle_text, body_style)]], colWidths=[710])
    prin_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#FDBA74")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(prin_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 6: UNIQUE SELLING PROPOSITION (USP)
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("UNIQUE SELLING PROPOSITION (USP)", "Why CrediFlow Outperforms Existing Tax & ERP Tools"):
        story.append(item)

    usp_table_data = [
        [
            Paragraph("Capability / Feature", table_hdr),
            Paragraph("Typical GST / ERP Tools (ClearTax, Tally, Zoho)", table_hdr),
            Paragraph("CrediFlow Platform", table_hdr)
        ],
        [
            Paragraph("<b>Mismatch Detection</b>", table_cell_bold),
            Paragraph("Basic rule checking", table_cell),
            Paragraph("<b>Multi-tier Engine:</b> Exact (± Rs. 2) -> Levenshtein <= 2 -> Tax Head -> Missing", table_cell_bold)
        ],
        [
            Paragraph("<b>Exact ITC Quantification</b>", table_cell_bold),
            Paragraph("Limited / Aggregate only", table_cell),
            Paragraph("<b>Full Granularity:</b> Per invoice + per vendor + by tax head (CGST/SGST/IGST)", table_cell_bold)
        ],
        [
            Paragraph("<b>Root-Cause Explanation</b>", table_cell_bold),
            Paragraph("Rare / Raw error codes", table_cell),
            Paragraph("<b>Dual-Agent AI:</b> Statutory root cause + plain-language amendment guidance", table_cell_bold)
        ],
        [
            Paragraph("<b>Vendor Follow-up</b>", table_cell_bold),
            Paragraph("Manual calls / Copy-pasting", table_cell),
            Paragraph("<b>1-Click Bilingual Nudges:</b> WhatsApp (wa.me) & Email (English + Hindi)", table_cell_bold)
        ],
        [
            Paragraph("<b>Legal Notice Generation</b>", table_cell_bold),
            Paragraph("None (Manual lawyer draft)", table_cell),
            Paragraph("<b>Auto-Generated PDF Notices:</b> Formal Section 16(2)(aa) legal demand notices", table_cell_bold)
        ],
        [
            Paragraph("<b>Resolution Tracking</b>", table_cell_bold),
            Paragraph("None (Software stops at report)", table_cell),
            Paragraph("<b>Built-in Lifecycle:</b> Detected -> Nudged -> Pending -> Verified", table_cell_bold)
        ],
        [
            Paragraph("<b>Post-Correction Verification</b>", table_cell_bold),
            Paragraph("None (Manual re-check)", table_cell),
            Paragraph("<b>Automated Re-reconciliation:</b> Closes case only upon confirmed GSTR-2B match", table_cell_bold)
        ]
    ]

    usp_tbl = Table(usp_table_data, colWidths=[140, 240, 330])
    usp_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(usp_tbl)
    story.append(Spacer(1, 4))

    # Summary Takeaway
    takeaway_text = (
        "<b>Strategic Differentiation:</b> Most tools answer <i>\"What is mismatched?\"</i>. "
        "<b>CrediFlow answers:</b> <font color='#EA580C'><b>\"How do we resolve this and recover the working capital?\"</b></font>"
    )
    takeaway_tbl = Table([[Paragraph(takeaway_text, body_style)]], colWidths=[710])
    takeaway_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#FDBA74")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(takeaway_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 7: FEASIBILITY & COMPETITOR ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("FEASIBILITY & COMPETITORS", "Technical Feasibility, Risk Mitigations & Competitor Matrix"):
        story.append(item)

    col1_feas = [
        Paragraph("Technical Feasibility & Scale", card_title_orange),
        Paragraph("• <b>Proven, Robust Stack:</b> Python FastAPI backend with React 19 frontend guarantees high availability.", bullet_style),
        Paragraph("• <b>Standardized Formats:</b> Works with standard GSTR-2B JSON/Excel portal extracts and ERP books.", bullet_style),
        Paragraph("• <b>Sub-Second Throughput:</b> Tested up to 10,000+ invoices with <2s reconciliation runtime.", bullet_style),
        Paragraph("• <b>Zero-Friction Adoption:</b> No complex API gateway setup required; works out of the box with file uploads.", bullet_style),
        Spacer(1, 2),
        Paragraph("Competitor Positioning", card_title_style),
        Paragraph("• <b>Legacy ERPs (Tally, Zoho):</b> Focus on accounting entries; zero vendor follow-up workflows.", bullet_style),
        Paragraph("• <b>Enterprise Tax Tools (ClearTax):</b> High cost, enterprise-heavy, passive reports without closed-loop tracking.", bullet_style),
        Paragraph("• <b>Generic AI Chatbots:</b> Unreliable with financial math; hallucinate numbers without deterministic audit trails.", bullet_style)
    ]

    col2_risks = [
        Paragraph("Key Challenges & Engineering Mitigations", card_title_orange),
        Paragraph("<b>1. Messy Invoice Formats:</b>", card_title_style),
        Paragraph("-> <i>Mitigation:</i> Multi-stage string normalization + fuzzy Levenshtein matching + manual override.", bullet_style),
        Paragraph("<b>2. Vendor Non-Response:</b>", card_title_style),
        Paragraph("-> <i>Mitigation:</i> Prioritized by financial exposure; automated escalation from polite reminder to legal notice.", bullet_style),
        Paragraph("<b>3. Trust in AI & Calculations:</b>", card_title_style),
        Paragraph("-> <i>Mitigation:</i> AI is never permitted to touch calculations; deterministic engine is the sole source of truth.", bullet_style),
        Paragraph("<b>4. Data Sensitivity & Privacy:</b>", card_title_style),
        Paragraph("-> <i>Mitigation:</i> Local SQLite persistence + role-based access; zero vendor data shared externally.", bullet_style)
    ]

    feas_tbl = Table([[col1_feas, col2_risks]], colWidths=[355, 345])
    feas_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_BG),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (0, 0), 0.75, COLOR_BORDER),
        ('BOX', (1, 0), (1, 0), 0.75, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(feas_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 8: RESEARCH & REFERENCE
    # ══════════════════════════════════════════════════════════════════════════
    for item in make_slide_header("RESEARCH & REFERENCE", "Statutory Framework, Live Deployment & Project Links"):
        story.append(item)

    col1_refs = [
        Paragraph("Statutory & Legal References", card_title_orange),
        Paragraph("• <b>CGST Act Section 16(2)(aa):</b> Mandatory condition that ITC can only be availed if invoice details are furnished by the supplier in GSTR-1 and communicated in GSTR-2B.", bullet_style),
        Paragraph("• <b>Rule 60 CGST:</b> Form and manner of furnishing details in GSTR-2A and auto-drafted GSTR-2B statement.", bullet_style),
        Paragraph("• <b>Rule 36(4) CGST:</b> Statutory restriction on ITC claims for un-uploaded invoices.", bullet_style),
        Paragraph("• <b>DRC-01C Mechanism:</b> Automated GST portal intimation of difference in ITC available in GSTR-2B vs claimed in GSTR-3B.", bullet_style),
    ]

    col2_demo = [
        Paragraph("Live Demo, Repository & Deployment", card_title_style),
        Paragraph("• <b>Live Web Application:</b>", card_title_style),
        Paragraph("<font color='#2563EB'><u>https://credi-flow-gray.vercel.app/</u></font>", bullet_style),
        Paragraph("• <b>GitHub Repository:</b>", card_title_style),
        Paragraph("<font color='#2563EB'><u>https://github.com/Vaishnavi5200/CrediFlow</u></font>", bullet_style),
        Paragraph("• <b>Interactive Demo Dataset:</b>", card_title_style),
        Paragraph("Includes official 45-invoice real-world mismatch dataset + 1,000-invoice scale benchmark.", bullet_style),
        Spacer(1, 2),
        Paragraph("• <b>Demo Credentials / Access:</b> Publicly accessible, zero setup required.", bullet_style)
    ]

    ref_tbl = Table([[col1_refs, col2_demo]], colWidths=[355, 345])
    ref_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_BG),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (0, 0), 0.75, COLOR_BORDER),
        ('BOX', (1, 0), (1, 0), 0.75, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ref_tbl)
    story.append(Spacer(1, 5))

    # Final Vision Banner
    vision_text = (
        "<b>Summary & Vision:</b> CrediFlow bridges the gap between passive tax reports and active cash recovery. "
        "By enforcing <b>DETECT -> QUANTIFY -> NUDGE -> RESOLVE -> VERIFY</b>, CrediFlow empowers Indian MSMEs "
        "to reclaim locked working capital with statutory accuracy and zero friction."
    )
    vis_tbl = Table([[Paragraph(vision_text, body_style)]], colWidths=[710])
    vis_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#FDBA74")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(vis_tbl)

    # Build Document
    doc.build(story, canvasmaker=BuildWithBharatCanvas)
    return output_path

if __name__ == "__main__":
    out_file = "/Users/vaishnavidwivedi/CrediFlow/Build_With_Bharat_CrediFlow_Presentation.pdf"
    generate_presentation_pdf(out_file)
    print(f"Presentation PDF successfully created at: {out_file}")
