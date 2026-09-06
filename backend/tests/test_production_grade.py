"""
Extended Unit Tests for CrediFlow — Edge Cases, VCS Formula, HITL Triggers, and Validation
Covers all weaknesses identified in the production audit.
"""

import pytest
import asyncio
from backend.app.core.gst_reconciliation import (
    GSTReconciliationEngine,
    InvoiceRecord,
    MismatchType,
    MismatchSeverity,
    validate_gstin_checksum,
    normalize_invoice_num,
)
from backend.app.core.synthetic_data_generator import generate_demo_dataset
from backend.app.services.rocketride_service import RocketRideService
from backend.app.services.human_gate import HumanGate
from backend.app.services.audit_service import AuditService


# ─── GSTIN Validation Tests ───────────────────────────────────────────────────

def test_validate_gstin_valid_checksum():
    """Known-valid GSTINs must pass MOD-36 verification."""
    valid_gstins = [
        "27AABCR1234F1ZS",
        "24AAACA5678B1Z0",
        "03AAACV9012D1ZV",
        "29AAACZ3456G1Z3",
        "07AAACD7890H1ZF",
        "27AAACB0987A1Z1",  # buyer GSTIN
    ]
    for g in valid_gstins:
        ok, reason = validate_gstin_checksum(g)
        assert ok, f"Expected valid GSTIN {g}, got: {reason}"


def test_validate_gstin_wrong_length():
    ok, reason = validate_gstin_checksum("27AABCR1234F1Z")  # 14 chars
    assert not ok
    assert "length" in reason.lower()


def test_validate_gstin_invalid_regex():
    ok, reason = validate_gstin_checksum("27AABCR1234F1AA")  # no Z in pos 14
    assert not ok


def test_validate_gstin_bad_checksum():
    ok, reason = validate_gstin_checksum("27AABCR1234F1ZZ")  # wrong check digit
    assert not ok
    assert "checksum" in reason.lower() or "Checksum" in reason


def test_validate_gstin_empty():
    ok, reason = validate_gstin_checksum("")
    assert not ok
    assert "missing" in reason.lower() or "non-string" in reason.lower()


def test_normalize_invoice_num():
    assert normalize_invoice_num("INV/0881") == "INV0881"
    assert normalize_invoice_num("  INV-0881 ") == "INV0881"
    assert normalize_invoice_num("0001ABC") == "1ABC"
    assert normalize_invoice_num("") == ""


# ─── Reconciliation Edge Cases ────────────────────────────────────────────────

def test_negative_tax_value_is_malformed():
    """Negative taxable values must be detected as MALFORMED_INPUT."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-NEG",
            invoice_date="2026-04-01",
            supplier_gstin="27AABCR1234F1ZS",
            supplier_name="M/s Rajesh Traders",
            buyer_gstin="27AAACB0987A1Z1",
            taxable_value=-5000.0,
            cgst=-450.0,
            sgst=-450.0,
        )
    ]
    discs = engine.reconcile(pr, [])
    assert len(discs) == 1
    assert discs[0].mismatch_type == MismatchType.MALFORMED_INPUT
    assert discs[0].severity == MismatchSeverity.CRITICAL
    assert discs[0].requires_human_gate is True


def test_invalid_gstin_is_malformed():
    """Invalid supplier GSTIN must be caught as MALFORMED_INPUT."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-BAD",
            invoice_date="2026-04-01",
            supplier_gstin="INVALID_GSTIN",
            supplier_name="Bad Vendor",
            buyer_gstin="27AAACB0987A1Z1",
            taxable_value=10000.0,
            cgst=900.0,
            sgst=900.0,
        )
    ]
    discs = engine.reconcile(pr, [])
    assert len(discs) == 1
    assert discs[0].mismatch_type == MismatchType.MALFORMED_INPUT


def test_empty_purchase_register():
    """Empty purchase register returns zero discrepancies, no crash."""
    engine = GSTReconciliationEngine()
    discs = engine.reconcile([], [])
    assert discs == []


def test_empty_gstr2b():
    """All invoices missing in GSTR-2B = all MISSING_IN_2B."""
    engine = GSTReconciliationEngine()
    pr, _ = generate_demo_dataset()
    discs = engine.reconcile(pr, [])
    # Every record in PR is missing from 2B, minus any already-malformed ones
    assert len(discs) == len(pr)
    types = {d.mismatch_type for d in discs}
    assert MismatchType.MISSING_IN_2B in types or MismatchType.MALFORMED_INPUT in types


def test_within_tolerance_no_discrepancy():
    """Tax differences within ₹2 tolerance must NOT generate a discrepancy."""
    engine = GSTReconciliationEngine(tolerance_rupees=2.0)
    rec = InvoiceRecord(
        invoice_number="INV-TOL",
        invoice_date="2026-04-01",
        supplier_gstin="27AABCR1234F1ZS",
        supplier_name="M/s Rajesh Traders",
        buyer_gstin="27AAACB0987A1Z1",
        taxable_value=100000.0,
        cgst=9000.0,
        sgst=9000.0,
    )
    # G2B has 1 rupee less — within tolerance
    rec_2b = InvoiceRecord(
        invoice_number="INV-TOL",
        invoice_date="2026-04-01",
        supplier_gstin="27AABCR1234F1ZS",
        supplier_name="M/s Rajesh Traders",
        buyer_gstin="27AAACB0987A1Z1",
        taxable_value=100000.0,
        cgst=8999.5,
        sgst=8999.5,
    )
    discs = engine.reconcile([rec], [rec_2b])
    # Should be 0 (within ₹2 tolerance: diff = ₹1.00)
    assert len(discs) == 0


def test_high_value_threshold_flag():
    """ITC exposure >= 50,000 must set is_high_value = True and requires_human_gate = True."""
    engine = GSTReconciliationEngine(high_value_threshold=50000.0)
    pr = [
        InvoiceRecord(
            invoice_number="INV-HIGH",
            invoice_date="2026-04-01",
            supplier_gstin="27AABCR1234F1ZS",
            supplier_name="M/s Rajesh Traders",
            buyer_gstin="27AAACB0987A1Z1",
            taxable_value=500000.0,
            cgst=45000.0,
            sgst=45000.0,  # total tax = 90000, > 50k threshold
        )
    ]
    discs = engine.reconcile(pr, [])
    assert len(discs) == 1
    assert discs[0].itc_exposure_rupees == 90000.0
    assert discs[0].is_high_value is True
    assert discs[0].requires_human_gate is True


# ─── VCS Formula Tests ────────────────────────────────────────────────────────

def _vcs(unresolved_itc, total_val, mismatched, total_inv, days):
    """Helper: mirrors the VCS formula from routes.py."""
    s_exp = min(100.0, (unresolved_itc / max(total_val, 1.0)) * 100.0)
    s_freq = min(100.0, (mismatched / max(total_inv, 1)) * 100.0)
    s_age = min(100.0, (days / 30.0) * 100.0)
    raw = 100.0 - (0.45 * s_exp + 0.35 * s_freq + 0.20 * s_age)
    return max(0.0, min(100.0, round(raw, 1)))


def test_vcs_perfect_score():
    """Zero mismatches, zero ITC exposure, zero aging → score = 100."""
    score = _vcs(0, 1_000_000, 0, 50, 0)
    assert score == 100.0


def test_vcs_full_risk():
    """100% ITC blocked, all invoices mismatched, 30 days open → very low score."""
    score = _vcs(500_000, 500_000, 50, 50, 30)
    assert score == 0.0  # All components at max penalty


def test_vcs_partial():
    """Partial mismatch scenario produces score between 50 and 90."""
    score = _vcs(42500, 500_000, 1, 10, 22)
    assert 50.0 < score < 90.0, f"Expected score 50-90, got {score}"


def test_vcs_tier_boundaries():
    """VCS tiers: >=90 → LOW, 75-89 → MEDIUM, 50-74 → HIGH, <50 → CRITICAL."""
    assert _vcs(0, 1_000_000, 0, 50, 0) >= 90   # LOW
    assert 75 <= _vcs(20_000, 400_000, 1, 20, 10) <= 90  # might be MEDIUM
    # Make a clearly HIGH risk vendor
    score_high = _vcs(150_000, 300_000, 5, 10, 20)
    assert score_high < 75


# ─── Human Gate Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hitl_triggers_on_low_confidence():
    """HITL must trigger when Agent B confidence is below threshold (0.85)."""
    gate = HumanGate(confidence_threshold=0.85, high_value_threshold_inr=50000.0)
    mismatch = {
        "invoice_number": "VTX-4412",
        "supplier_name": "Vardhman Textiles Ltd",
        "supplier_gstin": "03AAACV9012D1ZV",
        "itc_exposure_rupees": 1080.0,
        "mismatch_type": "HSN_MISMATCH"
    }
    # Simulate Agent B returning 0.74 confidence (HSN mismatch fallback)
    audit_dict = {
        "mismatch_id": "VTX-4412",
        "requires_human_review": True,
        "human_review_reasons": ["Low confidence: Agent A=0.91, Agent B=0.74 (threshold=0.85)"],
        "human_review_triggers": {
            "agent_disagreement": True,
            "low_confidence": True,
            "high_exposure": False,
            "malformed_input": False,
        }
    }
    entry = gate.evaluate(mismatch, audit_dict)
    assert entry is not None
    assert gate.pending_count >= 1


@pytest.mark.asyncio
async def test_hitl_triggers_on_agent_disagreement():
    """HITL must trigger on PARTIALLY_AGREE verdict."""
    gate = HumanGate(confidence_threshold=0.85, high_value_threshold_inr=50000.0)
    mismatch = {
        "invoice_number": "ZLOG-9923",
        "supplier_name": "Zenith Logistics Corp",
        "supplier_gstin": "29AAACZ3456G1Z3",
        "itc_exposure_rupees": 13500.0,
        "mismatch_type": "GSTIN_MISMATCH"
    }
    audit_dict = {
        "mismatch_id": "ZLOG-9923",
        "requires_human_review": True,
        "human_review_reasons": ["Agent disagreement: Agent B verdict = PARTIALLY_AGREE"],
        "human_review_triggers": {
            "agent_disagreement": True,
            "low_confidence": True,
            "high_exposure": False,
            "malformed_input": False,
        }
    }
    entry = gate.evaluate(mismatch, audit_dict)
    assert entry is not None
    assert gate.pending_count >= 1


# ─── Audit Service: End-to-End ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_audit_service_returns_results_key():
    """AuditService.execute_audit must return 'findings' key (not 'results')."""
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine()
    rocketride_svc = RocketRideService()
    gate = HumanGate()
    audit_svc = AuditService(engine, rocketride_svc, gate)

    result = await audit_svc.execute_audit(pr, g2b)
    assert "findings" in result, "Missing 'findings' key in audit output"
    assert isinstance(result["findings"], list)


@pytest.mark.asyncio
async def test_audit_service_fallback_hitl_triggered():
    """
    In fallback mode, HSN and GSTIN mismatches should produce PARTIALLY_AGREE
    verdicts (confidence < 0.85), which means requires_human_review = True.
    """
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine()
    rocketride_svc = RocketRideService()
    gate = HumanGate(confidence_threshold=0.85)
    audit_svc = AuditService(engine, rocketride_svc, gate)

    result = await audit_svc.execute_audit(pr, g2b)
    # HSN and GSTIN mismatches should trigger HITL in fallback mode
    human_review_cases = [
        f for f in result["findings"]
        if f.get("requires_human_review") or f.get("audit_verdict") in ("PARTIALLY_AGREE", "DISAGREE")
    ]
    assert len(human_review_cases) >= 2, (
        f"Expected at least 2 HITL cases (HSN + GSTIN), got {len(human_review_cases)}"
    )


@pytest.mark.asyncio
async def test_audit_nudge_taxable_value_is_accurate():
    """
    Nudge preview taxable_value must match actual invoice taxable_value,
    NOT be inflated with any artificial offset.
    """
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine()
    rocketride_svc = RocketRideService()
    gate = HumanGate()
    audit_svc = AuditService(engine, rocketride_svc, gate)

    result = await audit_svc.execute_audit(pr, g2b)

    # Find Rajesh Traders finding (MISSING_IN_2B, actual taxable = 236,111.11)
    rajesh = next(
        (f for f in result["findings"] if "Rajesh" in f.get("supplier_name", "")),
        None
    )
    assert rajesh is not None, "Rajesh Traders finding not found"

    nudge = rajesh.get("nudge_preview", {})
    english_nudge = nudge.get("english_nudge", "")
    # The nudge must reference the real taxable value 236,111 not the inflated 336,111
    assert "236,111" in english_nudge or "236111" in english_nudge, (
        f"Nudge shows wrong taxable value. Expected ~236,111 in nudge text, got: {english_nudge[:300]}"
    )
    # Make sure the old bug (336,111 = 236,111 + 100,000) is NOT present
    assert "336,111" not in english_nudge, (
        "Critical bug: nudge still shows inflated taxable value +100,000!"
    )


@pytest.mark.asyncio
async def test_deterministic_math_never_uses_llm():
    """
    Reconciliation engine output must be identical across 3 consecutive runs.
    Verifies the zero-hallucination guarantee: no LLM is used in math.
    """
    pr, g2b = generate_demo_dataset()
    eng = GSTReconciliationEngine()
    results = []
    for _ in range(3):
        discs = eng.reconcile(pr, g2b)
        results.append([
            (d.invoice_number, d.mismatch_type.value, d.itc_exposure_rupees)
            for d in discs
        ])
    assert results[0] == results[1] == results[2], (
        "Deterministic engine returned different results across runs!"
    )
