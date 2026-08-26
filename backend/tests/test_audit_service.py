"""
Unit Tests for CrediFlow Audit & RocketRide Services
"""

import pytest
from backend.app.core.gst_reconciliation import GSTReconciliationEngine, InvoiceRecord, MismatchType
from backend.app.core.synthetic_data_generator import generate_demo_dataset
from backend.app.services.rocketride_service import RocketRideService
from backend.app.services.human_gate import HumanGate
from backend.app.services.audit_service import AuditService


def test_deterministic_reconciliation_math():
    """Verify 100% deterministic MOD-36 matching under Rule 60."""
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine(high_value_threshold=50000.0)
    discrepancies = engine.reconcile(pr, g2b)

    assert len(pr) == 45
    assert len(g2b) == 44
    assert len(discrepancies) == 5
    total_exp = sum(d.itc_exposure_rupees for d in discrepancies)
    assert total_exp == 70580.0


@pytest.mark.asyncio
async def test_audit_service_execution():
    """Verify AuditService orchestrates dual-agent audit and returns normalized schema."""
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine(high_value_threshold=50000.0)
    rocketride_svc = RocketRideService()
    gate = HumanGate()
    audit_svc = AuditService(engine, rocketride_svc, gate)

    result = await audit_svc.execute_audit(pr, g2b)

    assert result["processed"] == 45
    assert result["matched"] == 40
    assert result["mismatched"] == 5
    assert result["itc_exposure"] == 70580.0
    assert "execution_engine" in result
    assert len(result["findings"]) == 5
    assert len(result["evidence"]) == 5


@pytest.mark.asyncio
async def test_human_gate_trigger_evaluation():
    """Verify Human Gate triggers on high value, low confidence, or agent disagreement."""
    gate = HumanGate(confidence_threshold=0.85, high_value_threshold_inr=50000.0)
    mismatch = {
        "invoice_number": "INV-TEST",
        "supplier_name": "Test Vendor",
        "supplier_gstin": "27AABCR1234F1ZS",
        "itc_exposure_rupees": 65000.0,
        "mismatch_type": "MISSING_IN_2B"
    }
    audit_dict = {
        "mismatch_id": "INV-TEST",
        "requires_human_review": True,
        "human_review_reasons": ["High ITC exposure: ₹65,000 ≥ ₹50,000"]
    }

    entry = gate.evaluate(mismatch, audit_dict)
    assert entry is not None
    assert gate.pending_count >= 1
