"""
CrediFlow Notice Generator — PDF Notice & Bilingual Nudges
Generates:
1. Statutory GST ITC Discrepancy Notice (PDF) under Rule 60 CGST / Section 16(2).
2. Professional Bilingual Nudges (English & Hindi) with exact GST portal table amendment steps.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# reportlab is imported lazily inside functions to avoid crash on Vercel serverless cold-start
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    letter = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    colors = None


def generate_bilingual_nudges(
    supplier_name: str,
    invoice_number: str,
    invoice_date: str,
    taxable_value: float,
    itc_exposure: float,
    buyer_name: str = "CrediFlow Enterprise Ltd",
    buyer_gstin: str = "27AAACB0987A1Z1",
    mismatch_type: str = "MISSING_IN_2B",
    root_cause_code: str = "B2B_FILED_AS_B2C",
) -> Dict[str, Any]:
    """Generates precise English and Hindi WhatsApp / Email nudge templates with GST portal steps."""
    
    # GST Portal Amendment Steps based on root cause
    if root_cause_code in ("B2B_FILED_AS_B2C", "INVOICE_MISSING_IN_2B"):
        steps_en = [
            "1. Log in to the GST Portal (gst.gov.in) -> Services -> Returns -> Returns Dashboard.",
            "2. Select Financial Year (2025-26) and Return Period (April 2026).",
            "3. Open GSTR-1 -> Go to Table 4A (Taxable outward supplies made to registered persons).",
            f"4. Add Invoice {invoice_number}: Enter Buyer GSTIN {buyer_gstin}, Date {invoice_date}, Taxable Value ₹{taxable_value:,.2f}.",
            "5. Save and File GSTR-1 return to reflect in our GSTR-2B credit stream.",
        ]
        steps_hi = [
            "1. GST पोर्टल (gst.gov.in) पर लॉग इन करें -> Services -> Returns -> Returns Dashboard।",
            "2. वित्तीय वर्ष (2025-26) और रिटर्न अवधि (अप्रैल 2026) चुनें।",
            "3. GSTR-1 खोलें -> Table 4A (पंजीकृत व्यक्तियों को की गई बिक्री) पर जाएं।",
            f"4. इनवॉइस {invoice_number} जोड़ें: खरीदार GSTIN {buyer_gstin}, दिनांक {invoice_date}, कर योग्य मूल्य ₹{taxable_value:,.2f} दर्ज करें।",
            "5. सेव करें और GSTR-1 रिटर्न फाइल करें ताकि यह हमारे GSTR-2B में परिलक्षित हो सके।",
        ]
    elif root_cause_code == "RATE_OR_VALUE_DISCREPANCY":
        steps_en = [
            "1. Log in to GST Portal -> GSTR-1 -> Table 9A (Amended B2B Invoices).",
            f"2. Search Original Invoice {invoice_number} and select 'Amend'.",
            f"3. Correct Taxable Value to ₹{taxable_value:,.2f} and adjust applicable GST rate.",
            "4. Save changes and file the amendment in your next GSTR-1.",
        ]
        steps_hi = [
            "1. GST पोर्टल -> GSTR-1 -> Table 9A (संशोधित B2B इनवॉइस) पर जाएं।",
            f"2. मूल इनवॉइस {invoice_number} खोजें और 'संशोधित करें' चुनें।",
            f"3. कर योग्य मूल्य को ₹{taxable_value:,.2f} पर सही करें।",
            "4. परिवर्तन सहेजें और अपने अगले GSTR-1 में संशोधन फाइल करें।",
        ]
    elif root_cause_code == "GSTIN_TYPO_OR_MISMATCH":
        steps_en = [
            "1. Log in to GST Portal -> GSTR-1 -> Table 9A (Amended B2B Invoices).",
            f"2. Update recipient GSTIN to correct Buyer GSTIN: {buyer_gstin}.",
            "3. Verify and file return to route credit to our state branch.",
        ]
        steps_hi = [
            "1. GST पोर्टल -> GSTR-1 -> Table 9A पर जाएं।",
            f"2. प्राप्तकर्ता GSTIN को सही खरीदार GSTIN: {buyer_gstin} में अपडेट करें।",
            "3. रिटर्न सत्यापित करें और फाइल करें।",
        ]
    else:
        steps_en = [
            "1. Log in to GST Portal -> Returns Dashboard -> GSTR-1.",
            f"2. Review invoice {invoice_number} details and ensure correct 6-digit HSN mapping.",
            "3. File return to validate Input Tax Credit.",
        ]
        steps_hi = [
            "1. GST पोर्टल -> GSTR-1 पर जाएं।",
            f"2. इनवॉइस {invoice_number} विवरण की समीक्षा करें और सही HSN कोड सुनिश्चित करें।",
            "3. इनपुट टैक्स क्रेडिट मान्य करने के लिए रिटर्न फाइल करें।",
        ]

    msg_en = (
        f"Dear {supplier_name},\n\n"
        f"URGENT: GST Compliance Notice regarding Invoice No. {invoice_number} (Dated {invoice_date}, Value: ₹{taxable_value:,.2f}).\n\n"
        f"During our monthly GST reconciliation under Rule 60 CGST, this invoice was NOT auto-drafted in our GSTR-2B, "
        f"placing ₹{itc_exposure:,.2f} of our Input Tax Credit (ITC) at risk.\n\n"
        f"Under Section 16(2)(aa) of the CGST Act 2017, we cannot claim ITC unless reported in GSTR-1. "
        f"Please perform the following steps on the GST Portal:\n\n"
        + "\n".join(steps_en) +
        f"\n\nKindly confirm once filed to avoid payment holds or Debit Note issuance.\n\n"
        f"Regards,\nFinance & Accounts Department\n{buyer_name}"
    )

    msg_hi = (
        f"प्रिय {supplier_name},\n\n"
        f"अति आवश्यक: इनवॉइस संख्या {invoice_number} (दिनांक {invoice_date}, मूल्य: ₹{taxable_value:,.2f}) के संबंध में GST अनुपालन सूचना।\n\n"
        f"Rule 60 CGST के तहत हमारे मासिक मिलान के दौरान यह इनवॉइस हमारे GSTR-2B में प्रदर्शित नहीं हुआ है, "
        f"जिससे हमारा ₹{itc_exposure:,.2f} का इनपुट टैक्स क्रेडिट (ITC) अवरुद्ध हो गया है।\n\n"
        f"CGST अधिनियम की धारा 16(2)(aa) के तहत ITC केवल तभी दावा किया जा सकता है जब विक्रेता द्वारा GSTR-1 में सही विवरण दर्ज किया जाए। "
        f"कृपया GST पोर्टल पर निम्नलिखित कदम उठाएं:\n\n"
        + "\n".join(steps_hi) +
        f"\n\nकृपया फाइलिंग पूर्ण होने पर सूचित करें ताकि भुगतान प्रक्रिया सुचारू रूप से जारी रह सके।\n\n"
        f"धन्यवाद,\nवित्त एवं लेखा विभाग\n{buyer_name}"
    )

    return {
        "supplier_name": supplier_name,
        "invoice_number": invoice_number,
        "itc_exposure_rupees": itc_exposure,
        "english_nudge": msg_en,
        "hindi_nudge": msg_hi,
        "amendment_steps_en": steps_en,
        "amendment_steps_hi": steps_hi,
    }


def _get_reports_dir() -> str:
    if os.environ.get("VERCEL"):
        return "/tmp/reports"
    local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/reports"))
    try:
        os.makedirs(local_dir, exist_ok=True)
        return local_dir
    except Exception:
        return "/tmp/reports"


def generate_pdf_notice(
    mismatch_data: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> str:
    """
    Generates a formal statutory GST ITC discrepancy notice in PDF format using ReportLab.
    Returns the absolute path to the generated PDF.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab is not available in this environment. PDF generation requires reportlab to be installed.")

    target_dir = output_dir or _get_reports_dir()
    os.makedirs(target_dir, exist_ok=True)
    inv = mismatch_data.get("invoice_number", "UNKNOWN")
    filename = f"GST_ITC_Notice_{inv}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(target_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e293b"),
        alignment=1, # Center
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=16
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10
    )
    alert_style = ParagraphStyle(
        'DocAlert',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#b91c1c"),
        backColor=colors.HexColor("#fef2f2"),
        borderPadding=8,
        spaceAfter=12
    )

    story = []

    # Header
    story.append(Paragraph("<b>FORMAL STATUTORY NOTICE — GST INPUT TAX CREDIT DISCREPANCY</b>", title_style))
    story.append(Paragraph("Issued under Section 16(2)(aa) & Rule 60 of the Central Goods and Services Tax (CGST) Act, 2017", subtitle_style))
    story.append(Spacer(1, 8))

    # Meta Info
    now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
    meta_text = (
        f"<b>Notice Date:</b> {now_str}<br/>"
        f"<b>Issued By:</b> CrediFlow Enterprise Ltd (GSTIN: 27AAACB0987A1Z1)<br/>"
        f"<b>To Supplier:</b> {mismatch_data.get('supplier_name', 'Vendor')} (GSTIN: {mismatch_data.get('supplier_gstin', 'N/A')})<br/>"
        f"<b>Reference Invoice:</b> {inv}"
    )
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 10))

    # Alert Box
    exposure = mismatch_data.get("itc_exposure_rupees", 0.0)
    alert_text = (
        f"<b>CRITICAL COMPLIANCE NOTICE:</b> A tax discrepancy of <b>₹{exposure:,.2f}</b> has been identified in our monthly reconciliation. "
        "Due to the invoice being absent or mismatched in GSTR-2B, the Input Tax Credit (ITC) is blocked under Rule 60 CGST zero-mismatch provisions."
    )
    story.append(Paragraph(alert_text, alert_style))

    # Discrepancy Table
    table_data = [
        ["Parameter", "Purchase Register (Buyer)", "GSTR-2B (Portal Record)", "Variance / Risk"],
        ["Invoice Number", inv, inv, "Matched" if mismatch_data.get("mismatch_type") != "MISSING_IN_2B" else "Omitted in 2B"],
        ["Supplier GSTIN", mismatch_data.get("supplier_gstin", "N/A"), mismatch_data.get("supplier_gstin", "N/A"), "Verified"],
        ["Taxable Value", f"₹{mismatch_data.get('taxable_value_diff', 0.0) + 100000:,.2f}", "₹100,000.00" if mismatch_data.get("mismatch_type") != "MISSING_IN_2B" else "₹0.00", f"₹{mismatch_data.get('taxable_value_diff', 0.0):,.2f}"],
        ["ITC Tax Amount", f"₹{mismatch_data.get('purchase_register_tax', 0.0):,.2f}", f"₹{mismatch_data.get('gstr_2b_tax', 0.0):,.2f}", f"₹{exposure:,.2f} blocked"],
        ["Mismatch Code", mismatch_data.get("mismatch_type", "N/A"), mismatch_data.get("root_cause_classification", "B2B_FILED_AS_B2C"), "Immediate Action Req."]
    ]

    t = Table(table_data, colWidths=[120, 140, 140, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor("#dc2626")),
        ('FONTNAME', (3, 1), (3, -1), 'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Required Action
    action_text = (
        "<b>MANDATORY CORRECTIVE ACTION REQUIRED WITHIN 5 BUSINESS DAYS:</b><br/>"
        "1. File Table 4A / Table 9A amendment in GSTR-1 on the GST Common Portal.<br/>"
        "2. Ensure Buyer GSTIN (27AAACB0987A1Z1) is correctly mapped to reflect in our monthly GSTR-2B return.<br/>"
        "3. Failure to regularize will mandate withholding of tax equivalent payments or issuance of commercial Debit Note.<br/>"
    )
    story.append(Paragraph(action_text, body_style))
    story.append(Spacer(1, 12))

    # Footer
    footer_text = "<i>This is a system-generated statutory document produced by CrediFlow Compliance Engine.</i>"
    story.append(Paragraph(footer_text, subtitle_style))

    doc.build(story)
    return filepath
