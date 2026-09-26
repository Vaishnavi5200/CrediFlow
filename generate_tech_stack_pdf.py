"""
Script to generate a comprehensive, executive-grade PDF report on CrediFlow's Tech Stack.
Optimized for an elegant, perfectly balanced 2-page layout.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas with header and page numbers 'Page X of Y'"""
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
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 752, "CrediFlow — Technical Architecture & Technology Stack Specification")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 745, 572, 745)

        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 36, 572, 36)

        self.setFont("Helvetica", 8)
        self.drawString(40, 24, "CONFIDENTIAL — CREDIFLOW ARCHITECTURAL SPECIFICATION")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 24, page_str)
        self.restoreState()


def create_tech_stack_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")     # Slate 900
    ACCENT = colors.HexColor("#2563EB")      # Royal Blue
    SECONDARY = colors.HexColor("#0D9488")   # Teal
    DARK = colors.HexColor("#1E293B")        # Slate 800
    LIGHT_BG = colors.HexColor("#F8FAFC")    # Slate 50
    CARD_BG = colors.HexColor("#F1F5F9")     # Slate 100
    BORDER = colors.HexColor("#CBD5E1")      # Slate 300

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=ACCENT,
        spaceAfter=6
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=7,
        spaceAfter=3
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=SECONDARY,
        spaceBefore=4,
        spaceAfter=2
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=DARK,
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=2
    )
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=DARK
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=DARK
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=PRIMARY
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("CrediFlow — Technical Architecture & Stack Deep Dive", title_style))
    story.append(Paragraph("Deterministic GST Compliance, Dual-Agent Resolution & High-Throughput Analytics", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=5))

    # Executive Summary Card
    exec_summary_text = (
        "<b>System Overview:</b> CrediFlow is an enterprise-grade GST Input Tax Credit (ITC) reconciliation and vendor "
        "resolution platform built under <b>Rule 60 CGST</b> and <b>Section 16(2)(aa)</b>. It combines a sub-millisecond "
        "deterministic reconciliation engine with an autonomous dual-agent dispute resolver, human-in-the-loop oversight, "
        "and automated bilingual recovery notice generation."
    )
    summary_table = Table([[Paragraph(exec_summary_text, callout_style)]], colWidths=[532])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4))

    # Section 1: Technology Architecture Matrix
    story.append(Paragraph("1. Technology Stack Summary Matrix", h1_style))
    
    matrix_data = [
        [
            Paragraph("Layer", table_hdr_style),
            Paragraph("Technologies & Libraries", table_hdr_style),
            Paragraph("Version / Engine", table_hdr_style),
            Paragraph("Core Functionality & Role", table_hdr_style)
        ],
        [
            Paragraph("Frontend UI", table_cell_bold),
            Paragraph("React, Vite, Tailwind CSS, Lucide React, Canvas Confetti", table_cell_style),
            Paragraph("React 19.2<br/>Vite 8.2", table_cell_style),
            Paragraph("Single-page reactive dashboard, live audit ledger, HITL modal, analytics charts.", table_cell_style)
        ],
        [
            Paragraph("Backend API", table_cell_bold),
            Paragraph("FastAPI, Uvicorn, Pydantic v2, HTTPX, Python-Multipart", table_cell_style),
            Paragraph("Python 3.10+<br/>FastAPI 0.115+", table_cell_style),
            Paragraph("Asynchronous REST microservices, file parsing, validation, batch simulation endpoints.", table_cell_style)
        ],
        [
            Paragraph("Persistence", table_cell_bold),
            Paragraph("SQLite 3, In-Memory State Store, Python Dataclasses", table_cell_style),
            Paragraph("SQLite 3<br/>In-Memory Cache", table_cell_style),
            Paragraph("Persists audit ledger, benchmarks, human decisions, and dispatches; instant live cache.", table_cell_style)
        ],
        [
            Paragraph("Data Pipes", table_cell_bold),
            Paragraph("Tinybird / ClickHouse SQL Pipes (.pipe format)", table_cell_style),
            Paragraph("ClickHouse SQL", table_cell_style),
            Paragraph("High-throughput streaming ingestion, real-time aggregation, mismatch detection pipelines.", table_cell_style)
        ],
        [
            Paragraph("AI & Multi-Agent", table_cell_bold),
            Paragraph("RocketRide Dual-Agent Pipeline (OpenAI backend), Statutory Engine", table_cell_style),
            Paragraph("Dual-Agent<br/>Statutory Fallback", table_cell_style),
            Paragraph("Agent A (Root-Cause Classifier) + Agent B (Audit Cross-Examiner) + Deterministic Math.", table_cell_style)
        ],
        [
            Paragraph("Doc Engine", table_cell_bold),
            Paragraph("ReportLab PDF Toolkit, Bilingual Template Engine", table_cell_style),
            Paragraph("ReportLab 5.0.1", table_cell_style),
            Paragraph("Dynamic generation of legal GST Rule 60 recovery notices and bilingual Hindi/English nudges.", table_cell_style)
        ],
        [
            Paragraph("Deployment", table_cell_bold),
            Paragraph("Vercel Serverless, Static Assets Build, ASGI Adapter", table_cell_style),
            Paragraph("Vercel / POSIX", table_cell_style),
            Paragraph("Cloud serverless deployment with fallback disk paths and live production routing.", table_cell_style)
        ]
    ]

    matrix_table = Table(matrix_data, colWidths=[72, 168, 88, 204])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 4))

    # Section 2: Detailed Architectural Breakdown
    story.append(Paragraph("2. Frontend & Backend Architectural Stack", h1_style))

    story.append(Paragraph("Frontend Ecosystem (React 19 + Vite 8 + Tailwind CSS)", h2_style))
    story.append(Paragraph("• <b>React 19 (v19.2.8):</b> Utilizes React 19 concurrent rendering for fluid interactions across heavy multi-thousand invoice tables.", bullet_style))
    story.append(Paragraph("• <b>Vite 8 (v8.2.2):</b> High-speed bundler with Hot Module Replacement (HMR) and optimized ES module compilation.", bullet_style))
    story.append(Paragraph("• <b>Tailwind CSS & Utilities:</b> Styled with <code>clsx</code> (v2.1.1) and <code>tailwind-merge</code> (v3.6.0) for dark/light themes and glassmorphism styling.", bullet_style))
    story.append(Paragraph("• <b>Lucide React (v1.34.0):</b> Clean icon set for financial states, status badges, and AI agent flows.", bullet_style))
    story.append(Paragraph("• <b>Oxlint (v1.79.0):</b> Rust-based high-speed linter for strict code hygiene.", bullet_style))
    story.append(Paragraph("• <b>Canvas Confetti (v1.9.4):</b> Micro-interactions celebrating resolved reconciliation mismatches.", bullet_style))

    story.append(Paragraph("Backend Framework & API Layer (Python + FastAPI)", h2_style))
    story.append(Paragraph("• <b>FastAPI (v0.115.0+):</b> Asynchronous REST API framework built on Starlette and OpenAPI specs for ultra-fast non-blocking execution.", bullet_style))
    story.append(Paragraph("• <b>Pydantic v2:</b> High-speed Rust-core serialization and schema validation for invoices, GSTINs, and audit decisions.", bullet_style))
    story.append(Paragraph("• <b>HTTPX (v0.27.0):</b> Asynchronous HTTP client powering external webhook calls to the RocketRide AI cloud.", bullet_style))
    story.append(Paragraph("• <b>OpenPyXL & Python-Multipart:</b> Multi-format data parser handling Excel (.xlsx), CSV, and JSON data uploads.", bullet_style))
    story.append(Paragraph("• <b>Uvicorn:</b> ASGI production server handling high-concurrency requests.", bullet_style))

    story.append(PageBreak())

    # Section 3: Data Layer & Persistence
    story.append(Paragraph("3. Data Layer, Storage & Streaming Pipelines", h1_style))
    story.append(Paragraph("Persistence Architecture (SQLite + In-Memory + ClickHouse Pipes)", h2_style))

    db_details = [
        [Paragraph("Component", table_hdr_style), Paragraph("Storage Type", table_hdr_style), Paragraph("Description & Table Schemas", table_hdr_style)],
        [
            Paragraph("<b>audit_ledger</b>", table_cell_style),
            Paragraph("SQLite Table", table_cell_style),
            Paragraph("Stores historical invoice audit records, supplier GSTINs, taxable amounts, tax breakdowns (CGST/SGST/IGST), mismatch flags, and statutory verdicts.", table_cell_style)
        ],
        [
            Paragraph("<b>benchmark_runs</b>", table_cell_style),
            Paragraph("SQLite Table", table_cell_style),
            Paragraph("Persists performance benchmarks: invoice counts (100 to 10,000+), runtime in ms, throughput (invoices/sec), total exposure INR, AI cost USD/INR, and retries.", table_cell_style)
        ],
        [
            Paragraph("<b>human_decisions</b>", table_cell_style),
            Paragraph("SQLite Table", table_cell_style),
            Paragraph("Audit trail of human interventions: gate IDs, invoice numbers, decisions (APPROVED/EDITED/REJECTED), reviewer identity, notes, and timestamps.", table_cell_style)
        ],
        [
            Paragraph("<b>notice_dispatches</b>", table_cell_style),
            Paragraph("SQLite Table", table_cell_style),
            Paragraph("Maintains dispatch logs for formal PDF notices: recipient supplier, delivery channel (WhatsApp/Email), PDF path, and dispatch status.", table_cell_style)
        ],
        [
            Paragraph("<b>Session State</b>", table_cell_style),
            Paragraph("In-Memory Store", table_cell_style),
            Paragraph("FastAPI in-memory singleton dictionary providing sub-millisecond query access for active frontend session reconciliation.", table_cell_style)
        ],
        [
            Paragraph("<b>Streaming Pipes</b>", table_cell_style),
            Paragraph("ClickHouse / Tinybird (.pipe)", table_cell_style),
            Paragraph("SQL analytics pipelines defined in <code>pipelines/crediflow_audit_pipeline.pipe</code> for streaming reconciliation, aggregate risk metrics, and batch ingestion.", table_cell_style)
        ]
    ]

    db_table = Table(db_details, colWidths=[105, 95, 332])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 4))

    # Section 4: Multi-Agent AI & Compliance Engine
    story.append(Paragraph("4. Multi-Agent AI & Compliance Engine", h1_style))
    story.append(Paragraph("• <b>Dual-Agent Architecture:</b>", h2_style))
    story.append(Paragraph("  - <b>Agent A (Root-Cause Classifier):</b> Ingests multi-table GST discrepancies (Tax Mismatches, Missing Invoices, B2B classification errors, GSTR-1 vs 3B default) and determines root legal causation.", bullet_style))
    story.append(Paragraph("  - <b>Agent B (Audit Cross-Examiner):</b> Adversarially challenges Agent A's classification against statutory exemptions, Rule 60 compliance deadlines, and financial materialities.", bullet_style))
    story.append(Paragraph("• <b>Tri-Tier Execution Priority:</b>", h2_style))
    story.append(Paragraph("  1. <i>RocketRide Webhook:</i> HTTPS POST to cloud multi-agent orchestration pipeline with OpenAI backend synthesis.", bullet_style))
    story.append(Paragraph("  2. <i>RocketRide SDK:</i> Direct WebSocket streaming (<code>wss://</code>) for cloud or edge execution.", bullet_style))
    story.append(Paragraph("  3. <i>Statutory Deterministic Fallback:</i> Pure Python compliance engine ensuring 100% mathematical precision (zero LLM calculation hallucinations) and 100% offline uptime.", bullet_style))
    story.append(Paragraph("• <b>Human-in-the-Loop (HITL) Gate:</b> Automatically routes high-exposure claims (> INR 50,000) or low-confidence verdicts (< 85%) to finance managers for review, modification, or rejection.", bullet_style))

    story.append(Spacer(1, 4))

    # Section 5: Document Generation & Communications
    story.append(Paragraph("5. Document Generation & Communication Engine", h1_style))
    story.append(Paragraph("• <b>ReportLab 5.0.1:</b> Programmatic generation of court-ready legal demand notices under GST Section 16(2)(aa) with custom tables, tax breakdowns, statutory citations, and formal letterheads.", bullet_style))
    story.append(Paragraph("• <b>Bilingual Nudge Engine:</b> Automated generation of dual-language communications (English & Hindi) customized with supplier risk scores and progressive escalation tones (Friendly Reminder → Urgent Statutory Warning).", bullet_style))
    story.append(Paragraph("• <b>Multi-Channel Dispatcher:</b> Dispatch simulation and connectivity for WhatsApp Business API and Email SMTP protocols.", bullet_style))

    story.append(Spacer(1, 4))

    # Section 6: DevOps & Deployment
    story.append(Paragraph("6. Deployment, Packaging & Quality Assurance", h1_style))
    story.append(Paragraph("• <b>Vercel Serverless Architecture:</b> Configured via <code>vercel.json</code> with Python serverless functions (<code>api/index.py</code>) and statically built React assets.", bullet_style))
    story.append(Paragraph("• <b>Modern Packaging:</b> Standardized with <code>pyproject.toml</code> (PEP 621) and npm modular package management.", bullet_style))
    story.append(Paragraph("• <b>Automated Test Suite:</b> Pytest suite (<code>backend/tests/test_buildathon_requirements.py</code>) validating Rule 60 compliance, reconciliation edge-cases, high-throughput scaling, and HITL gate logic.", bullet_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path

if __name__ == "__main__":
    out_file = "/Users/vaishnavidwivedi/CrediFlow/CrediFlow_Tech_Stack_Architecture.pdf"
    create_tech_stack_pdf(out_file)
    print(f"PDF successfully generated at: {out_file}")
