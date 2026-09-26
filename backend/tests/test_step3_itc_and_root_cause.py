"""
CrediFlow Step 3: Deterministic ITC Calculation & Root-Cause Classification Tests

Requirements Tested:
1. Exact Match with ITC calculation (0 exposure, non-zero invoice tax)
2. Amount-Tolerant Case (diff <= ₹2.00 results in ₹0 exposure)
3. Amount Difference > ₹2 (diff > ₹2 results in exact arithmetic exposure & VALUE_MISMATCH)
4. Near-Match (edit distance <= 2 with matched record & NEAR_MATCH_INVOICE_TYPO root cause)
5. Tax-Head Mismatch (IGST vs CGST/SGST split variance with TAX_HEAD_MISMATCH root cause)
6. Missing in GSTR-2B (100% tax exposure with MISSING_IN_2B root cause)
7. Ambiguous Match (Multi-candidate conflict with AMBIGUOUS_CANDIDATES root cause, no guessing)
8. Successful verification reducing invoice-level ITC exposure to ₹0
9. Total blocked ITC aggregate changing correctly after resolution
10. Deterministic repeated execution producing identical outputs across 100 iterations
"""

import pytest
from backend.app.core.gst_reconciliation import (
    GSTReconciliationEngine,
    InvoiceRecord,
    MismatchType,
    MismatchSeverity,
    DiscrepancyResult,
)
from backend.app.core.synthetic_data_generator import generate_demo_dataset

BUYER_GSTIN = "27AAACB0987A1Z1"
SUPPLIER_GSTIN = "27AABCR1234F1ZS"


# ─── 1. Exact Match with ITC ──────────────────────────────────────────────────

def test_exact_match_with_itc():
    """Exact match on non-zero tax invoice produces 0 exposure."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-EXACT-01",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=200000.0,
            cgst=18000.0,
            sgst=18000.0,
            hsn_code="847130"
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-EXACT-01",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=200000.0,
            cgst=18000.0,
            sgst=18000.0,
            hsn_code="847130"
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 0
    total_blocked = engine.calculate_total_blocked_itc(discrepancies)
    assert total_blocked == 0.0


# ─── 2. Amount-Tolerant Case ─────────────────────────────────────────────────

def test_amount_tolerant_itc_exposure():
    """Rounding difference within ₹2 tolerance produces 0 exposure."""
    engine = GSTReconciliationEngine(tolerance_rupees=2.0)
    pr = [
        InvoiceRecord(
            invoice_number="INV-TOL-02",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=9000.0,
            sgst=9000.0,
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-TOL-02",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=8999.10,
            sgst=8999.10,  # Total diff = ₹1.80 <= ₹2.00
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 0
    assert engine.calculate_total_blocked_itc(discrepancies) == 0.0


# ─── 3. Amount Difference > ₹2 ───────────────────────────────────────────────

def test_amount_difference_greater_than_two_rupees():
    """Variance > ₹2 produces exact arithmetic exposure and VALUE_MISMATCH root cause."""
    engine = GSTReconciliationEngine(tolerance_rupees=2.0)
    pr = [
        InvoiceRecord(
            invoice_number="INV-VAL-03",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=150000.0,
            cgst=13500.0,
            sgst=13500.0,  # Total tax = 27,000.0
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-VAL-03",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=9000.0,
            sgst=9000.0,  # Total tax = 18,000.0 (Diff = 9,000.0)
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.VALUE_MISMATCH
    assert d.root_cause_code == "VALUE_MISMATCH"
    assert d.reconciliation_outcome == "VALUE_MISMATCH"
    assert d.itc_exposure_rupees == 9000.0
    assert d.status == "UNRESOLVED"
    assert d.matched_gstr2b_invoice == "INV-VAL-03"
    assert engine.calculate_total_blocked_itc(discrepancies) == 9000.0


# ─── 4. Near-Match ───────────────────────────────────────────────────────────

def test_near_match_classification_and_structure():
    """Near match (edit distance <= 2) exposes structured fields and NEAR_MATCH_INVOICE_TYPO root cause."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-2026-NM01",
            invoice_date="2026-04-12",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=120000.0,
            cgst=10800.0,
            sgst=10800.0,
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV/2026-NM01",
            invoice_date="2026-04-12",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=120000.0,
            cgst=10800.0,
            sgst=10800.0,
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.NEAR_MATCH
    assert d.root_cause_code == "NEAR_MATCH_INVOICE_TYPO"
    assert d.reconciliation_outcome == "NEAR_MATCH"
    assert d.status == "NEEDS_REVIEW"
    assert d.matched_gstr2b_invoice == "INV/2026-NM01"
    assert d.itc_exposure_rupees == 0.0

    # Test dictionary serialization
    d_dict = d.to_dict()
    assert d_dict["invoice_number"] == "INV-2026-NM01"
    assert d_dict["matched_gstr2b_invoice"] == "INV/2026-NM01"
    assert d_dict["root_cause_code"] == "NEAR_MATCH_INVOICE_TYPO"
    assert d_dict["reconciliation_outcome"] == "NEAR_MATCH"


# ─── 5. Tax-Head Mismatch ────────────────────────────────────────────────────

def test_tax_head_mismatch_exposure():
    """Place of supply / head split mismatch calculates full exposed credit and TAX_HEAD_MISMATCH root cause."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-THM-01",
            invoice_date="2026-04-14",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            igst=18000.0,
            cgst=0.0,
            sgst=0.0,
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-THM-01",
            invoice_date="2026-04-14",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            igst=0.0,
            cgst=9000.0,
            sgst=9000.0,
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.TAX_HEAD_MISMATCH
    assert d.root_cause_code == "TAX_HEAD_MISMATCH"
    assert d.itc_exposure_rupees == 18000.0
    assert d.status == "NEEDS_REVIEW"
    assert d.matched_gstr2b_invoice == "INV-THM-01"


# ─── 6. Missing in GSTR-2B ───────────────────────────────────────────────────

def test_missing_in_gstr_2b_full_exposure():
    """Unfiled invoice produces 100% tax exposure and MISSING_IN_2B root cause."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-MISSING-99",
            invoice_date="2026-04-15",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=250000.0,
            cgst=22500.0,
            sgst=22500.0,
        )
    ]
    discrepancies = engine.reconcile(pr, [])
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.MISSING_IN_2B
    assert d.root_cause_code == "MISSING_IN_2B"
    assert d.itc_exposure_rupees == 45000.0
    assert d.status == "UNRESOLVED"
    assert d.matched_gstr2b_invoice is None


# ─── 7. Ambiguous Match ──────────────────────────────────────────────────────

def test_ambiguous_candidate_root_cause():
    """Multiple candidate invoices result in AMBIGUOUS_CANDIDATES root cause and unassigned matching."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-AMB-100",
            invoice_date="2026-04-16",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=70000.0,
            cgst=6300.0,
            sgst=6300.0,
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-AMB-101",
            invoice_date="2026-04-16",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=70000.0,
            cgst=6300.0,
            sgst=6300.0,
        ),
        InvoiceRecord(
            invoice_number="INV-AMB-102",
            invoice_date="2026-04-16",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=70000.0,
            cgst=6300.0,
            sgst=6300.0,
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.AMBIGUOUS_MATCH
    assert d.root_cause_code == "AMBIGUOUS_CANDIDATES"
    assert d.status == "NEEDS_REVIEW"
    assert d.candidate_count == 2
    assert d.itc_exposure_rupees == 12600.0


# ─── 8. Successful Verification Reducing ITC to ₹0 ────────────────────────────

def test_invoice_verification_reduces_itc_to_zero():
    """Resolving/verifying an invoice sets its unresolved ITC exposure to ₹0.00."""
    disc = DiscrepancyResult(
        id="DISC-2026-04-0001",
        invoice_number="INV-RESOLVE-01",
        supplier_gstin=SUPPLIER_GSTIN,
        supplier_name="M/s Rajesh Traders",
        mismatch_type=MismatchType.MISSING_IN_2B,
        severity=MismatchSeverity.HIGH,
        itc_exposure_rupees=35000.0,
        purchase_register_tax=35000.0,
        gstr_2b_tax=0.0,
        taxable_value_diff=194444.44,
        details="Missing in 2B",
        rule_citation="Rule 60 CGST",
        is_high_value=False,
        requires_human_gate=False,
        status="UNRESOLVED",
        root_cause_classification="MISSING_IN_2B"
    )
    assert disc.itc_exposure_rupees == 35000.0
    disc.resolve("Vendor uploaded in Table 4B GSTR-1, verified via ARN-998811")
    assert disc.itc_exposure_rupees == 0.0
    assert disc.status == "VERIFIED_RESOLVED"
    assert "ARN-998811" in disc.details


# ─── 9. Total Blocked ITC Changes After Resolution ────────────────────────────

def test_total_blocked_itc_changes_after_resolution():
    """Total blocked ITC aggregate decreases by exact invoice amount after resolution."""
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine()

    initial_discrepancies = engine.reconcile(pr, g2b)
    initial_total_blocked = engine.calculate_total_blocked_itc(initial_discrepancies)
    assert initial_total_blocked == 70580.0

    # Resolve Rajesh Traders missing invoice (₹42,500.0)
    new_discs, summary = engine.resolve_and_recalculate(
        purchase_register=pr,
        gstr_2b_records=g2b,
        resolved_invoice_number="INV-0881"
    )

    new_total_blocked = engine.calculate_total_blocked_itc(new_discs)
    expected_new_total = 70580.0 - 42500.0  # 28,080.0
    assert new_total_blocked == expected_new_total
    assert summary["itc_recovered_rupees"] == 42500.0
    assert summary["previous_exposure_rupees"] == 70580.0
    assert summary["current_exposure_rupees"] == 28080.0
    assert summary["remaining_discrepancies_count"] == 4

    # Resolve Apex Steel value mismatch (₹9,000.0)
    new_discs_2, summary_2 = engine.resolve_and_recalculate(
        purchase_register=pr,
        gstr_2b_records=g2b,  # with both resolved
        resolved_invoice_number="INV-2045"
    )
    assert summary_2["itc_recovered_rupees"] == 9000.0


# ─── 10. Repeated Execution Producing Identical Results ───────────────────────

def test_deterministic_repeated_execution_zero_variance():
    """100 repeated executions produce identical results with zero variance."""
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine()

    base_results = [
        (d.id, d.invoice_number, d.mismatch_type.value, d.root_cause_code, d.itc_exposure_rupees, d.status)
        for d in engine.reconcile(pr, g2b)
    ]
    base_blocked = engine.calculate_total_blocked_itc(engine.reconcile(pr, g2b))

    for i in range(100):
        current_discs = engine.reconcile(pr, g2b)
        current_results = [
            (d.id, d.invoice_number, d.mismatch_type.value, d.root_cause_code, d.itc_exposure_rupees, d.status)
            for d in current_discs
        ]
        current_blocked = engine.calculate_total_blocked_itc(current_discs)
        assert current_results == base_results, f"Iteration {i} produced mismatched discrepancy results"
        assert current_blocked == base_blocked, f"Iteration {i} produced mismatched aggregate ITC"
