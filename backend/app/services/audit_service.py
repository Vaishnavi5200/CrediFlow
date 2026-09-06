"""
Audit Service — CrediFlow
Coordinates the end-to-end audit process:
  1. Ingestion & Deterministic Reconciliation (MOD-36 matching)
  2. ITC Risk Exposure Quantification
  3. AI-Driven Root-Cause Classification & Audit via RocketRideService
  4. Human-in-the-Loop Risk Gate Evaluation
  5. Bilingual Nudge Generation
  6. Normalized Structured Response Mapping
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from ..core.gst_reconciliation import GSTReconciliationEngine, InvoiceRecord, DiscrepancyResult
from .rocketride_service import RocketRideService, PipelineAuditResult
from .human_gate import HumanGate
from .notice_generator import generate_bilingual_nudges


class AuditService:
    """
    Coordinates compliance audit workflows between the deterministic engine,
    RocketRide AI pipeline, and human risk gate.
    """

    def __init__(
        self,
        reconciliation_engine: Optional[GSTReconciliationEngine] = None,
        rocketride_service: Optional[RocketRideService] = None,
        human_gate: Optional[HumanGate] = None,
    ):
        self.engine = reconciliation_engine or GSTReconciliationEngine(high_value_threshold=50000.0)
        self.rocketride = rocketride_service or RocketRideService()
        self.gate = human_gate or HumanGate(confidence_threshold=0.85, high_value_threshold_inr=50000.0)

    async def execute_audit(
        self,
        purchase_register: List[InvoiceRecord],
        gstr_2b: List[InvoiceRecord],
        filter_invoices: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes full audit pipeline and returns standardized CrediFlow result schema.
        """
        t0 = time.monotonic()

        # Step 1 & 2: Deterministic Reconcile + ITC Quantification
        discrepancies = self.engine.reconcile(purchase_register, gstr_2b)

        if filter_invoices:
            discrepancies = [d for d in discrepancies if d.invoice_number in filter_invoices]

        total_exposure = sum(d.itc_exposure_rupees for d in discrepancies)
        high_exposure_count = sum(1 for d in discrepancies if d.is_high_value)

        # Step 3 & 4: Multi-Agent Audit via RocketRide
        findings = []
        evidence = []
        engine_counts = {"ROCKETRIDE_CLOUD": 0, "STATUTORY_FALLBACK": 0}

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
                "hsn_code": "",  # Not stored in DiscrepancyResult; set by invoice record
            }

            # Recover actual taxable_value from purchase register for this invoice
            pr_invoice = next((r for r in purchase_register if r.invoice_number == d.invoice_number), None)
            actual_taxable_value = pr_invoice.taxable_value if pr_invoice else d.taxable_value_diff
            actual_invoice_date = pr_invoice.invoice_date if pr_invoice else "2026-04-12"
            if pr_invoice:
                m_dict["filing_period"] = pr_invoice.filing_period
                m_dict["hsn_code"] = pr_invoice.hsn_code

            audit_res: PipelineAuditResult = await self.rocketride.audit_mismatch(m_dict)
            engine_counts[audit_res.execution_engine] = engine_counts.get(audit_res.execution_engine, 0) + 1

            # Evaluate Human Gate
            gate_entry = self.gate.evaluate(m_dict, audit_res.to_dict())

            # Generate bilingual nudge previews using accurate invoice data
            nudges = generate_bilingual_nudges(
                supplier_name=d.supplier_name,
                invoice_number=d.invoice_number,
                invoice_date=actual_invoice_date,
                taxable_value=actual_taxable_value,
                itc_exposure=d.itc_exposure_rupees,
                mismatch_type=d.mismatch_type.value,
                root_cause_code=audit_res.agent_a.root_cause_code
            )

            findings.append({
                "invoice_number": d.invoice_number,
                "supplier_name": d.supplier_name,
                "supplier_gstin": d.supplier_gstin,
                "itc_exposure_rupees": d.itc_exposure_rupees,
                "mismatch_type": d.mismatch_type.value,
                "execution_engine": audit_res.execution_engine,
                "agent_a": audit_res.agent_a.raw,
                "agent_b": audit_res.agent_b.raw,
                "requires_human_review": audit_res.requires_human_review,
                "human_review_triggers": {
                    "agent_disagreement": audit_res.trigger_agent_disagreement,
                    "low_confidence": audit_res.trigger_low_confidence,
                    "high_exposure": audit_res.trigger_high_exposure,
                    "malformed_input": audit_res.trigger_malformed
                },
                "human_review_reasons": audit_res.human_review_reasons,
                "gate_id": gate_entry.gate_id if gate_entry else None,
                "nudge_preview": nudges
            })

            evidence.append({
                "invoice_number": d.invoice_number,
                "purchase_register_tax": d.purchase_register_tax,
                "gstr_2b_tax": d.gstr_2b_tax,
                "rule_citation": d.rule_citation,
                "agent_a_reasoning": audit_res.agent_a.reasoning,
                "agent_b_cross_examination": audit_res.agent_b.cross_examination,
                "consensus": audit_res.agent_b.audit_verdict
            })

        wall_clock_ms = (time.monotonic() - t0) * 1000
        overall_engine = "ROCKETRIDE_CLOUD" if engine_counts["ROCKETRIDE_CLOUD"] > 0 else "STATUTORY_FALLBACK"
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
            "execution_engine": overall_engine,
            "wall_clock_ms": round(wall_clock_ms, 2),
            "summary": {
                "purchase_register_count": len(purchase_register),
                "gstr_2b_count": len(gstr_2b),
                "discrepancies_count": len(discrepancies),
                "total_itc_exposure_rupees": total_exposure,
            },
            "findings": findings,
            "evidence": evidence
        }
