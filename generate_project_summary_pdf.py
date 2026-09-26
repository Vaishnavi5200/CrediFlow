"""
Generates a comprehensive, AI-optimized PDF briefing of the entire CrediFlow project.
Designed so that any LLM, AI Agent, or Engineer can understand the full context,
architecture, data flows, statutory rules, database schemas, and codebase structure.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas with clean running headers and page numbers 'Page X of Y'"""
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
            self.drawString(36, 755, "CrediFlow — Comprehensive Project Architecture & LLM Context Document")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 748, 576, 748)

        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 34, 576, 34)

        self.setFont("Helvetica", 8)
        self.drawString(36, 22, "CREDIFLOW MASTER CONTEXT BRIEFING — PREPARED FOR LLM & SYSTEM ONBOARDING")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 22, page_str)
        self.restoreState()


def build_complete_summary_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Color Palette
    PRIMARY = colors.HexColor("#0F172A")    # Deep Slate
    ACCENT = colors.HexColor("#2563EB")     # Royal Blue
    SECONDARY = colors.HexColor("#0D9488")  # Teal Accent
    DARK = colors.HexColor("#1E293B")       # Dark Charcoal
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Slate 50
    CARD_BG = colors.HexColor("#F1F5F9")    # Slate 100
    BORDER = colors.HexColor("#CBD5E1")     # Slate 300
    HIGHLIGHT = colors.HexColor("#E0E7FF")  # Indigo Light
    ALERT_BG = colors.HexColor("#FEF2F2")   # Light Red
    ALERT_BORDER = colors.HexColor("#FCA5A5")

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
        fontName='Helvetica-Bold',
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
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=DARK,
        spaceAfter=3
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=DARK,
        leftIndent=9,
        firstLineIndent=-6,
        spaceAfter=1.5
    )
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=DARK
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9.5,
        textColor=DARK
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=PRIMARY
    )
    code_snippet_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.8,
        leading=8.8,
        textColor=DARK
    )

    story = []

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 1: PROJECT IDENTITY, PROBLEM, ARCHITECTURE, TECH MATRIX
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("CrediFlow — Complete Project Master Briefing", title_style))
    story.append(Paragraph("AI Agent & Chatbot Reference Specification | End-to-End System Context", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=4))

    # Executive Overview Callout
    summary_text = (
        "<b>SYSTEM MISSION:</b> CrediFlow is an enterprise fintech and statutory compliance engine that resolves "
        "<b>GST Input Tax Credit (ITC)</b> leakage for Indian businesses under <b>Rule 60 CGST</b> and <b>Section 16(2)(aa)</b>. "
        "It ingests multi-format Purchase Registers (PR) and GST Portal returns (GSTR-2B), runs sub-millisecond deterministic "
        "matching, coordinates an adversarial Dual-Agent AI audit system, safeguards high-value exposure with a Human-in-the-Loop "
        "(HITL) gate, and executes closed-loop recovery via bilingual nudges and court-ready legal PDF notices."
    )
    sum_tbl = Table([[Paragraph(summary_text, callout_style)]], colWidths=[540])
    sum_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 3))

    # Section 1: Problem Domain & Statutory Background
    story.append(Paragraph("1. Statutory Context & The Problem CrediFlow Solves", h1_style))
    story.append(Paragraph("• <b>The GST ITC Bottleneck:</b> In India, a buyer pays GST to a supplier upon receiving goods/services. However, under Section 16(2)(aa) CGST Act, the buyer can <i>only</i> claim this Input Tax Credit if the supplier actually uploads the invoice to the government portal (GSTR-1), making it appear in the buyer's auto-generated GSTR-2B.", bullet_style))
    story.append(Paragraph("• <b>Rule 60 CGST Strictness:</b> Strict zero-mismatch rule. If a supplier delays filing, reports the wrong buyer GSTIN, enters mismatched invoice numbers, misstates taxable values/rates, or defaults on their GSTR-3B tax payment, the buyer's ITC is frozen or clawed back with 18% annual statutory interest and penalties.", bullet_style))
    story.append(Paragraph("• <b>Traditional Failure Mode:</b> Enterprise finance teams manually audit massive spreadsheets months late, causing massive working capital blockage, legal disputes, and irrecoverable tax write-offs.", bullet_style))

    # Section 2: Core Capabilities & Innovations
    story.append(Paragraph("2. CrediFlow Core System Capabilities", h1_style))
    story.append(Paragraph("• <b>Deterministic Math Engine:</b> 100% Python-based mathematical reconciliation (zero LLM hallucinations for tax amounts, CGST, SGST, IGST, and cess). Matches thousands of records in under 2 seconds.", bullet_style))
    story.append(Paragraph("• <b>Adversarial Dual-Agent AI Audit:</b> Agent A (Root-Cause Classifier) diagnoses the statutory failure; Agent B (Audit Cross-Examiner) challenges the diagnosis against legal defenses, threshold materiality, and exemptions.", bullet_style))
    story.append(Paragraph("• <b>Human-in-the-Loop (HITL) Gate:</b> Auto-routes transactions with high exposure (> INR 50,000) or low AI confidence (< 85%) to finance managers for approval, modification, or rejection before any vendor communication is sent.", bullet_style))
    story.append(Paragraph("• <b>Closed-Loop Vendor Resolution:</b> Dispatches bilingual (English & Hindi) nudges via WhatsApp & Email, and dynamically compiles formal, court-ready Section 16(2)(aa) legal demand notices in PDF format.", bullet_style))

    # Section 3: Technology Stack Reference Table
    story.append(Paragraph("3. Full Technology Stack Specification", h1_style))

    tech_matrix = [
        [Paragraph("Subsystem", table_hdr_style), Paragraph("Technologies & Libraries", table_hdr_style), Paragraph("Key Role in CrediFlow", table_hdr_style)],
        [
            Paragraph("<b>Frontend UI</b>", table_cell_bold),
            Paragraph("React 19.2, Vite 8.2, Tailwind CSS, Lucide React, Canvas Confetti, Oxlint", table_cell_style),
            Paragraph("Interactive SPA dashboard, live ledger, HITL review gate, live AI feed, benchmark runner.", table_cell_style)
        ],
        [
            Paragraph("<b>Backend API</b>", table_cell_bold),
            Paragraph("FastAPI (0.115+), Uvicorn (ASGI), Pydantic v2, HTTPX, Python-Multipart, OpenPyXL", table_cell_style),
            Paragraph("High-speed async REST endpoints, Excel/CSV/JSON file parsers, schema validation, batching.", table_cell_style)
        ],
        [
            Paragraph("<b>Database</b>", table_cell_bold),
            Paragraph("SQLite 3 (Local persistent / Vercel fallback) + FastAPI In-Memory Session Cache", table_cell_style),
            Paragraph("Stores <code>audit_ledger</code>, <code>benchmark_runs</code>, <code>human_decisions</code>, and <code>notice_dispatches</code>.", table_cell_style)
        ],
        [
            Paragraph("<b>Data Pipes</b>", table_cell_bold),
            Paragraph("Tinybird / ClickHouse SQL Pipes (<code>.pipe</code> declarative format)", table_cell_style),
            Paragraph("Streaming analytics, high-volume ingestion pipelines, and aggregate compliance reporting.", table_cell_style)
        ],
        [
            Paragraph("<b>AI Engine</b>", table_cell_bold),
            Paragraph("RocketRide Dual-Agent Pipeline (OpenAI backend) + Deterministic Python Fallback", table_cell_style),
            Paragraph("Agent A Root Cause + Agent B Cross Examiner + 100% offline statutory fallback.", table_cell_style)
        ],
        [
            Paragraph("<b>Doc Engine</b>", table_cell_bold),
            Paragraph("ReportLab 5.0.1 + Custom Bilingual Nudge Generator", table_cell_style),
            Paragraph("Generates formal legal demand PDF notices and bilingual English/Hindi notification drafts.", table_cell_style)
        ],
        [
            Paragraph("<b>DevOps</b>", table_cell_bold),
            Paragraph("Vercel Serverless (Python runtime + static Vite bundle), Pytest test suite", table_cell_style),
            Paragraph("Production serverless deployment, automated compliance test suite under Rule 60.", table_cell_style)
        ]
    ]

    t_matrix = Table(tech_matrix, colWidths=[70, 205, 265])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_matrix)

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 2: ARCHITECTURE, DIRECTORY MAP, DATABASE SCHEMA, DATA FLOW
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. End-to-End System Data Flow & Architecture", h1_style))

    flow_box = (
        "<b>DATA FLOW LIFECYCLE:</b><br/>"
        "<b>Step 1 (Ingestion):</b> User uploads Purchase Register (PR) & GSTR-2B (Excel/CSV/JSON) or generates demo batch.<br/>"
        "<b>Step 2 (Deterministic Match):</b> <code>GSTReconciliationEngine</code> compares invoices, detects discrepancies, calculates exact ITC exposure.<br/>"
        "<b>Step 3 (Dual-Agent Audit):</b> Discrepancies sent to RocketRide Webhook / Statutory Engine: Agent A classifies root-cause, Agent B cross-examines.<br/>"
        "<b>Step 4 (HITL Gate):</b> High-risk (exposure > INR 50,000 or confidence < 85%) routed to Human Gate for review.<br/>"
        "<b>Step 5 (Resolution & Dispatch):</b> Approved actions generate bilingual WhatsApp/Email nudges & ReportLab legal recovery PDFs.<br/>"
        "<b>Step 6 (Closed-Loop Update):</b> Vendor filing simulation updates ledger status, logs to SQLite DB, and settles ITC."
    )
    flow_tbl = Table([[Paragraph(flow_box, callout_style)]], colWidths=[540])
    flow_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HIGHLIGHT),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#818CF8")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(flow_tbl)
    story.append(Spacer(1, 4))

    # Section 5: Directory Structure & File Map
    story.append(Paragraph("5. Codebase Directory Structure & Key Files", h1_style))
    
    file_map_data = [
        [Paragraph("File / Directory Path", table_hdr_style), Paragraph("Module Role & Core Responsibilities", table_hdr_style)],
        [
            Paragraph("<code>backend/app/core/gst_reconciliation.py</code>", table_cell_style),
            Paragraph("Core deterministic rule engine implementing Rule 60 CGST. Classifies MATCH, VALUE_MISMATCH, RATE_MISMATCH, MISSING_IN_GSTR2B, etc.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/services/rocketride_service.py</code>", table_cell_style),
            Paragraph("Dual-agent AI orchestration. Priority: 1. RocketRide Webhook (OpenAI) -> 2. RocketRide SDK (WSS) -> 3. Deterministic Python Fallback.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/services/human_gate.py</code>", table_cell_style),
            Paragraph("Human-in-the-Loop approval gate. Manages queue, exposure thresholds, risk scoring, approvals, edits, and rejections.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/services/notice_generator.py</code>", table_cell_style),
            Paragraph("ReportLab PDF generator for formal Section 16(2)(aa) legal demand notices + bilingual Hindi/English nudge template engine.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/services/nudge_dispatcher.py</code>", table_cell_style),
            Paragraph("Simulated / active multi-channel communication gateway for WhatsApp Business API and Email SMTP delivery.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/core/db.py</code>", table_cell_style),
            Paragraph("SQLite 3 schema initialization and query operations for audit logs, benchmarks, human decisions, and notice dispatches.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/core/file_parser.py</code>", table_cell_style),
            Paragraph("Robust parser handling Excel (.xlsx), CSV, JSON files with automatic header mapping and normalization.", table_cell_style)
        ],
        [
            Paragraph("<code>backend/app/api/routes.py</code>", table_cell_style),
            Paragraph("FastAPI REST router exposing all audit, benchmark, HITL decision, dispatch, and demo dataset endpoints.", table_cell_style)
        ],
        [
            Paragraph("<code>frontend/src/App.jsx</code>", table_cell_style),
            Paragraph("Primary React single-page application orchestrating tabs, ledger tables, HITL modals, AI feeds, and live metrics.", table_cell_style)
        ],
        [
            Paragraph("<code>pipelines/crediflow_audit_pipeline.pipe</code>", table_cell_style),
            Paragraph("ClickHouse / Tinybird streaming analytics definitions for high-volume invoice processing and real-time aggregation.", table_cell_style)
        ]
    ]

    t_file_map = Table(file_map_data, colWidths=[190, 350])
    t_file_map.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_file_map)
    story.append(Spacer(1, 4))

    # Section 6: Database Schema Definitions
    story.append(Paragraph("6. SQLite Database Schemas (data/crediflow.db)", h1_style))
    story.append(Paragraph("• <b><code>audit_ledger</code>:</b> <code>id, invoice_number, supplier_name, supplier_gstin, itc_exposure_rupees, mismatch_type, execution_engine, root_cause_code, audit_verdict, requires_human_review, created_at</code>", bullet_style))
    story.append(Paragraph("• <b><code>benchmark_runs</code>:</b> <code>id, run_id, count, runtime_ms, throughput_per_sec, total_exposure_inr, discrepancies_count, cost_usd, cost_inr, retries, escalations, created_at</code>", bullet_style))
    story.append(Paragraph("• <b><code>human_decisions</code>:</b> <code>id, gate_id (UNIQUE), invoice_number, decision (APPROVED|EDITED|REJECTED), decided_by, note, decided_at</code>", bullet_style))
    story.append(Paragraph("• <b><code>notice_dispatches</code>:</b> <code>id, invoice_number, supplier_name, channel (WHATSAPP|EMAIL), pdf_path, status, dispatched_at</code>", bullet_style))

    story.append(Spacer(1, 4))

    # Section 7: Key API Endpoints
    story.append(Paragraph("7. Primary REST API Endpoints", h1_style))
    story.append(Paragraph("• <code>POST /api/upload</code>: Uploads PR and GSTR-2B files (Excel/CSV/JSON) and runs instant deterministic matching.", bullet_style))
    story.append(Paragraph("• <code>POST /api/audit</code>: Triggers the RocketRide Dual-Agent AI audit on selected or all identified discrepancies.", bullet_style))
    story.append(Paragraph("• <code>GET /api/gate/pending</code> & <code>POST /api/gate/decision</code>: Manages the Human-in-the-Loop review queue and logs decisions.", bullet_style))
    story.append(Paragraph("• <code>POST /api/dispatch/nudge</code>: Dispatches bilingual nudges & compiles legal recovery PDF notices.", bullet_style))
    story.append(Paragraph("• <code>GET /api/benchmark/run</code>: Executes high-volume stress testing (100 to 10,000+ invoices) and returns performance metrics.", bullet_style))
    story.append(Paragraph("• <code>GET /api/db/summary</code>: Returns SQLite table counts, verification status, file size, and last benchmark.", bullet_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path

if __name__ == "__main__":
    out_file = "/Users/vaishnavidwivedi/CrediFlow/CrediFlow_Complete_Project_Overview.pdf"
    build_complete_summary_pdf(out_file)
    print(f"Master Summary PDF generated at: {out_file}")
