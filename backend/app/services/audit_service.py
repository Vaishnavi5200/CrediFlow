"""
Audit Service — CrediFlow
Coordinates the end-to-end statutory compliance audit:
  1. Ingestion & Deterministic Reconciliation (Rule 60 CGST matching)
  2. ITC Risk Exposure Quantification
  3. Deterministic Root-Cause Classification
  4. Human-in-the-Loop Risk Gate Evaluation
  5. Bilingual Nudge Generation (English & Hindi)
  6. Normalized Structured Response Mapping
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from ..core.gst_reconciliation import GSTReconciliationEngine, InvoiceRecord, DiscrepancyResult
from .human_gate import HumanGate
from .notice_generator import generate_bilingual_nudges


class AuditService:
    """
    Coordinates compliance audit workflows between the deterministic GST reconciliation engine,
    statutory explanation layer, and human risk gate.
    """

    def __init__(
        self,
        reconciliation_engine: Optional[GSTReconciliationEngine] = None,
        human_gate: Optional[HumanGate] = None,
    ):
        self.engine = reconciliation_engine or GSTReconciliationEngine(high_value_threshold=50000.0)
        self.gate = human_gate or HumanGate(confidence_threshold=0.85, high_value_threshold_inr=50000.0)

    async def execute_audit(
        self,
        purchase_register: List[InvoiceRecord],
        gstr_2b: List[InvoiceRecord],
        filter_invoices: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes statutory compliance audit and returns standardized CrediFlow result schema.
        """
        t0 = time.monotonic()

        # Step 1 & 2: Deterministic Reconciliation + ITC Exposure Quantification
        discrepancies = self.engine.reconcile(purchase_register, gstr_2b)

        if filter_invoices:
            discrepancies = [d for d in discrepancies if d.invoice_number in filter_invoices]

        total_exposure = sum(d.itc_exposure_rupees for d in discrepancies)
        high_exposure_count = sum(1 for d in discrepancies if d.is_high_value)

        findings = []
        evidence = []

        for d in discrepancies:
            m_dict = {
                "invoice_number": d.invoice_number,
                "supplier_gstin": d.supplier_gstin,
                "supplier_name": d.supplier_name,
                "mismatch_type": d.mismatch_type.value,
                "itc_exposure_rupees": d.itc_exposure_rupees,
                "purchase_register_tax": d.purchase_register_tax,
                "gstr_2b_tax": d.gstr_2b_tax,
                "taxable_value_diff": d.taxable_value_diff,
                "details": d.details,
                "rule_citation": d.rule_citation,
                "severity": d.severity.value,
                "filing_period": d.id.split("-")[1] + "-" + d.id.split("-")[2] if "-" in d.id else "2026-04",
                "hsn_code": "",
            }

            # Recover actual taxable_value from purchase register for this invoice
            pr_invoice = next((r for r in purchase_register if r.invoice_number == d.invoice_number), None)
            actual_taxable_value = pr_invoice.taxable_value if pr_invoice else d.taxable_value_diff
            actual_invoice_date = pr_invoice.invoice_date if pr_invoice else "2026-04-12"
            if pr_invoice:
                m_dict["filing_period"] = pr_invoice.filing_period
                m_dict["hsn_code"] = pr_invoice.hsn_code

            # Evaluate Human Gate
            pipeline_result = {
                "root_cause_code": d.mismatch_type.value,
                "confidence": 0.95,
                "reasoning": d.details,
                "rule_citation": d.rule_citation,
            }
            gate_entry = self.gate.evaluate(m_dict, pipeline_result)

            # Generate bilingual nudge previews using accurate invoice data
            nudges = generate_bilingual_nudges(
                supplier_name=d.supplier_name,
                invoice_number=d.invoice_number,
                invoice_date=actual_invoice_date,
                taxable_value=actual_taxable_value,
                itc_exposure=d.itc_exposure_rupees,
                mismatch_type=d.mismatch_type.value,
                root_cause_code=d.mismatch_type.value,
            )

            requires_human_review = gate_entry is not None
            reasons = gate_entry.trigger_reasons if gate_entry else []

            findings.append({
                "invoice_number": d.invoice_number,
                "supplier_name": d.supplier_name,
                "supplier_gstin": d.supplier_gstin,
                "itc_exposure_rupees": d.itc_exposure_rupees,
                "mismatch_type": d.mismatch_type.value,
                "execution_engine": "DETERMINISTIC_RULE_60",
                "root_cause_code": d.mismatch_type.value,
                "requires_human_review": requires_human_review,
                "human_review_triggers": {
                    "high_exposure": d.is_high_value,
                    "malformed_input": d.mismatch_type.value == "MALFORMED_INPUT",
                },
                "human_review_reasons": reasons,
                "gate_id": gate_entry.gate_id if gate_entry else None,
                "nudge_preview": nudges,
            })

            evidence.append({
                "invoice_number": d.invoice_number,
                "purchase_register_tax": d.purchase_register_tax,
                "gstr_2b_tax": d.gstr_2b_tax,
                "rule_citation": d.rule_citation,
                "details": d.details,
                "reconciliation_outcome": d.reconciliation_outcome,
            })

        wall_clock_ms = (time.monotonic() - t0) * 1000
        human_review_required = self.gate.pending_count > 0 or any(f["requires_human_review"] for f in findings)

        # Risk Level Assessment
        if total_exposure > 100000 or high_exposure_count > 2:
            risk_level = "CRITICAL"
        elif total_exposure > 40000 or len(discrepancies) > 3:
            risk_level = "HIGH"
        elif total_exposure > 0:
            risk_level = "MODERATE"
        else:
            risk_level = "COMPLIANT"

        return {
            "processed": len(purchase_register),
            "matched": len(purchase_register) - len(discrepancies),
            "mismatched": len(discrepancies),
            "itc_exposure": round(total_exposure, 2),
            "risk_level": risk_level,
            "human_review_required": human_review_required,
            "human_gate_pending": self.gate.pending_count,
            "execution_engine": "DETERMINISTIC_RULE_60",
            "wall_clock_ms": round(wall_clock_ms, 2),
            "summary": {
                "purchase_register_count": len(purchase_register),
                "gstr_2b_count": len(gstr_2b),
                "discrepancies_count": len(discrepancies),
                "total_itc_exposure_rupees": total_exposure,
            },
            "findings": findings,
            "evidence": evidence,
        }
