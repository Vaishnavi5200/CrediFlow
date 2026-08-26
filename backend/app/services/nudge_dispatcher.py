"""
CrediFlow Nudge Dispatcher & Closed-Loop Resolution Simulator
Handles:
1. Multi-channel dispatch (Email via SMTP, WhatsApp webhook simulation).
2. Action history and vendor communication tracking.
3. Closed-loop resolution simulation (vendor files GSTR-1 amendment -> re-audit verifies ₹0 risk).
"""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .notice_generator import generate_bilingual_nudges, generate_pdf_notice


class NudgeDispatcher:
    """Manages outgoing compliance notices and vendor action simulation."""

    def __init__(self):
        self._dispatch_log: List[Dict[str, Any]] = []
        self._resolved_invoices: Dict[str, Dict[str, Any]] = {}

    def dispatch_nudge(
        self,
        mismatch_record: Dict[str, Any],
        channels: List[str] = ["WHATSAPP", "EMAIL"],
        include_pdf: bool = True,
        sender_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches bilingual compliance nudges via specified channels.
        Generates formal PDF notice and logs the dispatch event.
        """
        inv = mismatch_record.get("invoice_number", "UNKNOWN")
        supplier = mismatch_record.get("supplier_name", "Vendor")
        exposure = float(mismatch_record.get("itc_exposure_rupees", 0.0))
        taxable = float(mismatch_record.get("taxable_value_diff", 0.0)) + 100000.0
        inv_date = mismatch_record.get("invoice_date", "2026-04-12")

        # 1. Generate bilingual nudge messages & steps
        nudge_content = generate_bilingual_nudges(
            supplier_name=supplier,
            invoice_number=inv,
            invoice_date=inv_date,
            taxable_value=taxable,
            itc_exposure=exposure,
            mismatch_type=mismatch_record.get("mismatch_type", "MISSING_IN_2B"),
            root_cause_code=mismatch_record.get("root_cause_classification", "B2B_FILED_AS_B2C"),
        )

        # 2. Generate PDF notice
        pdf_path = None
        if include_pdf:
            try:
                pdf_path = generate_pdf_notice(mismatch_record)
            except Exception as e:
                print(f"[WARN] PDF generation error: {e}")

        # 3. Simulate WhatsApp Payload
        whatsapp_payload = {
            "to": mismatch_record.get("supplier_phone", "+91 98201 54321"),
            "template_name": "gst_rule60_itc_discrepancy_v2",
            "language": ["en_US", "hi_IN"],
            "header": f"GST Rule 60 Compliance Notice: {inv}",
            "body": nudge_content["english_nudge"],
            "hindi_body": nudge_content["hindi_nudge"],
            "quick_reply_buttons": [
                "I have filed amendment",
                "Need clarification",
                "Contact Finance Team"
            ],
            "pdf_attachment": pdf_path
        }

        # 4. Email Dispatch (Real if SMTP configured, simulated fallback)
        email_sent = False
        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASSWORD", "")
        target_email = mismatch_record.get("supplier_email", "vendor@example.com")

        if smtp_host and smtp_user and smtp_pass and smtp_pass != "your_smtp_app_password_here":
            try:
                msg = MIMEMultipart()
                msg["From"] = smtp_user
                msg["To"] = target_email
                msg["Subject"] = f"URGENT: GST Rule 60 ITC Discrepancy Notice — Invoice {inv}"
                msg.attach(MIMEText(nudge_content["english_nudge"], "plain"))

                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
                        msg.attach(part)

                with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", 587))) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                email_sent = True
            except Exception as e:
                print(f"[WARN] SMTP delivery failed: {e}. Falling back to simulation log.")

        dispatch_event = {
            "dispatch_id": f"DSP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "invoice_number": inv,
            "supplier_name": supplier,
            "channels": channels,
            "itc_exposure_rupees": exposure,
            "whatsapp_payload": whatsapp_payload,
            "email_status": "SENT_LIVE" if email_sent else "SIMULATED_DISPATCH",
            "pdf_path": pdf_path,
            "nudge_content": nudge_content,
            "status": "SENT"
        }

        self._dispatch_log.append(dispatch_event)
        return dispatch_event

    def simulate_vendor_amendment(self, invoice_number: str, filing_arn: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulates the vendor logging into the GST Portal and filing Table 4A/Table 9A amendment.
        Transitions the invoice to 'AMENDED_PENDING_VERIFICATION'.
        """
        now = datetime.now(timezone.utc).isoformat()
        arn = filing_arn or f"AA270426{datetime.now().strftime('%H%M%S')}123"

        resolution = {
            "invoice_number": invoice_number,
            "status": "AMENDED_BY_VENDOR",
            "filing_arn": arn,
            "amended_at": now,
            "return_period": "2026-04",
            "table_filed": "Table 4A (Amended B2B)",
            "message": f"Vendor successfully uploaded invoice {invoice_number} in GSTR-1 (ARN: {arn}). Credit is now eligible in GSTR-2B."
        }
        self._resolved_invoices[invoice_number] = resolution
        return resolution

    def get_dispatch_history(self) -> List[Dict[str, Any]]:
        return self._dispatch_log

    def get_resolved_invoices(self) -> Dict[str, Dict[str, Any]]:
        return self._resolved_invoices
