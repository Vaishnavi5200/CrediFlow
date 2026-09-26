"""
CrediFlow Phase 2: Core Deterministic Reconciliation Engine Tests
Tests the exact statutory matching rules, strict priority hierarchy,
boundary tolerances, ambiguous candidate handling, and zero-hallucination math.

Requirements Covered:
1. Exact Match
2. Amount-Tolerant Match (diff <= ₹2.00)
3. Near-Match (invoice-number Levenshtein distance <= 2)
4. Tax-Head Mismatch (IGST vs CGST/SGST split disparity)
5. Missing in GSTR-2B
6. Ambiguous candidate handling (multiple candidates satisfying rule -> do not guess)
7. ₹2 boundary check (exact ₹2.00 diff matches)
8. >₹2 boundary check (₹2.01 diff remains unresolved)
9. Deterministic repeated execution (identical results across 100 runs)
"""

import pytest
from backend.app.core.gst_reconciliation import (
    GSTReconciliationEngine,
    InvoiceRecord,
    MismatchType,
    MismatchSeverity,
    levenshtein_distance,
    validate_gstin_checksum,
)
from backend.app.core.synthetic_data_generator import generate_demo_dataset

BUYER_GSTIN = "27AAACB0987A1Z1"
SUPPLIER_GSTIN = "27AABCR1234F1ZS"  # Valid Maharashtra GSTIN
INTERSTATE_GSTIN = "24AAACA5678B1Z0"  # Valid Gujarat GSTIN


# ─── 1. Exact Match ──────────────────────────────────────────────────────────

def test_exact_match():
    """Exact GSTIN + exact invoice number + exact amounts + exact tax heads = matched (0 exposure)."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-2026-001",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=9000.0,
            sgst=9000.0,
            hsn_code="847130"
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-2026-001",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=9000.0,
            sgst=9000.0,
            hsn_code="847130"
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 0, "Exact match should produce 0 discrepancies"


# ─── 2. Amount-Tolerant Match ────────────────────────────────────────────────

def test_amount_tolerant_match():
    """Exact GSTIN + invoice number with tax difference <= ₹2.00 matches cleanly."""
    engine = GSTReconciliationEngine(tolerance_rupees=2.0)
    pr = [
        InvoiceRecord(
            invoice_number="INV-TOL-01",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=50000.0,
            cgst=4500.0,
            sgst=4500.0,
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-TOL-01",
            invoice_date="2026-04-10",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=50000.0,
            cgst=4499.25,
            sgst=4499.25,  # Total tax diff = ₹1.50 <= ₹2.00
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 0, "Amount difference within ₹2.00 tolerance should be matched"


# ─── 3. Near-Match (Levenshtein Distance <= 2) ───────────────────────────────

def test_levenshtein_distance_helper():
    """Verify Levenshtein edit distance calculations."""
    assert levenshtein_distance("INV-1001", "INV-1001") == 0
    assert levenshtein_distance("INV-1001", "INV/1001") == 1
    assert levenshtein_distance("INV-1001", "INV1001") == 1
    assert levenshtein_distance("INV-1001", "INV/1001A") == 2
    assert levenshtein_distance("INV-1001", "INV/1001XYZ") == 4


def test_near_match_single_candidate():
    """Single candidate in GSTR-2B with Levenshtein distance <= 2 is classified as NEAR_MATCH."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-2026-8801",
            invoice_date="2026-04-12",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=80000.0,
            cgst=7200.0,
            sgst=7200.0,
        )
    ]
    # G2B has slash instead of hyphen -> edit distance = 1
    g2b = [
        InvoiceRecord(
            invoice_number="INV/2026-8801",
            invoice_date="2026-04-12",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=80000.0,
            cgst=7200.0,
            sgst=7200.0,
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.NEAR_MATCH
    assert d.root_cause_classification == "NEAR_MATCH_INVOICE_TYPO"
    assert d.status == "NEEDS_REVIEW"
    assert d.matched_gstr2b_invoice == "INV/2026-8801"


# ─── 4. Tax-Head Mismatch ────────────────────────────────────────────────────

def test_tax_head_mismatch():
    """
    Exact GSTIN + invoice number, total tax is identical (or within tolerance),
    but tax heads differ (e.g. Buyer booked IGST, Vendor filed CGST+SGST).
    """
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-TXH-99",
            invoice_date="2026-04-15",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            igst=18000.0,  # Buyer claimed IGST (Inter-state)
            cgst=0.0,
            sgst=0.0,
        )
    ]
    g2b = [
        InvoiceRecord(
            invoice_number="INV-TXH-99",
            invoice_date="2026-04-15",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            igst=0.0,
            cgst=9000.0,  # Vendor reported CGST + SGST (Intra-state)
            sgst=9000.0,
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.TAX_HEAD_MISMATCH
    assert d.root_cause_classification == "TAX_HEAD_MISMATCH"
    assert d.itc_exposure_rupees == 18000.0
    assert d.status == "NEEDS_REVIEW"
    assert "Section 77" in d.rule_citation


# ─── 5. Missing in GSTR-2B ───────────────────────────────────────────────────

def test_missing_in_gstr_2b():
    """Invoice in Purchase Register with zero candidate records in GSTR-2B."""
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-MISSING-404",
            invoice_date="2026-04-18",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=150000.0,
            cgst=13500.0,
            sgst=13500.0,
        )
    ]
    discrepancies = engine.reconcile(pr, [])
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.MISSING_IN_2B
    assert d.itc_exposure_rupees == 27000.0
    assert d.status == "UNRESOLVED"
    assert "Rule 60" in d.rule_citation


# ─── 6. Ambiguous Candidate Handling ─────────────────────────────────────────

def test_ambiguous_near_match_candidates_do_not_guess():
    """
    If multiple candidates satisfy Levenshtein distance <= 2,
    do NOT guess. Mark the case AMBIGUOUS_MATCH / NEEDS_REVIEW.
    """
    engine = GSTReconciliationEngine()
    pr = [
        InvoiceRecord(
            invoice_number="INV-2026-AB1",
            invoice_date="2026-04-20",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=60000.0,
            cgst=5400.0,
            sgst=5400.0,
        )
    ]
    # Two candidates in GSTR-2B both at distance 1
    g2b = [
        InvoiceRecord(
            invoice_number="INV-2026-AB2",  # dist 1
            invoice_date="2026-04-20",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=60000.0,
            cgst=5400.0,
            sgst=5400.0,
        ),
        InvoiceRecord(
            invoice_number="INV-2026-AB3",  # dist 1
            invoice_date="2026-04-20",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=60000.0,
            cgst=5400.0,
            sgst=5400.0,
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.AMBIGUOUS_MATCH
    assert d.root_cause_classification == "AMBIGUOUS_CANDIDATES"
    assert d.status == "NEEDS_REVIEW"
    assert d.candidate_count == 2
    assert d.itc_exposure_rupees == 10800.0


# ─── 7. ₹2 Boundary (diff == ₹2.00) ──────────────────────────────────────────

def test_boundary_exact_two_rupees():
    """Difference of exactly ₹2.00 matches under Amount-Tolerant Match."""
    engine = GSTReconciliationEngine(tolerance_rupees=2.0)
    pr = [
        InvoiceRecord(
            invoice_number="INV-BOUND-2",
            invoice_date="2026-04-21",
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
            invoice_number="INV-BOUND-2",
            invoice_date="2026-04-21",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=8999.0,
            sgst=8999.0,  # Total tax diff = ₹2.00 <= ₹2.00
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 0, "Exact ₹2.00 difference should match within tolerance"


# ─── 8. >₹2 Boundary (diff == ₹2.01) ─────────────────────────────────────────

def test_boundary_greater_than_two_rupees():
    """Difference of > ₹2.00 (e.g. ₹2.01) must remain UNRESOLVED as VALUE_MISMATCH."""
    engine = GSTReconciliationEngine(tolerance_rupees=2.0)
    pr = [
        InvoiceRecord(
            invoice_number="INV-BOUND-FAIL",
            invoice_date="2026-04-21",
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
            invoice_number="INV-BOUND-FAIL",
            invoice_date="2026-04-21",
            supplier_gstin=SUPPLIER_GSTIN,
            supplier_name="M/s Rajesh Traders",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=100000.0,
            cgst=8998.995,
            sgst=8998.995,  # Total tax diff = ₹2.01 > ₹2.00
        )
    ]
    discrepancies = engine.reconcile(pr, g2b)
    assert len(discrepancies) == 1
    d = discrepancies[0]
    assert d.mismatch_type == MismatchType.VALUE_MISMATCH
    assert d.root_cause_classification == "VALUE_MISMATCH"
    assert d.status == "UNRESOLVED"
    assert d.itc_exposure_rupees == 2.01


# ─── 9. Deterministic Repeated Execution ─────────────────────────────────────

def test_deterministic_repeated_execution_100_runs():
    """Engine must return byte-for-byte identical output over 100 consecutive runs."""
    pr, g2b = generate_demo_dataset()
    engine = GSTReconciliationEngine()

    first_run = [
        (d.id, d.invoice_number, d.mismatch_type.value, d.itc_exposure_rupees, d.status, d.root_cause_classification)
        for d in engine.reconcile(pr, g2b)
    ]

    for run_idx in range(100):
        current_run = [
            (d.id, d.invoice_number, d.mismatch_type.value, d.itc_exposure_rupees, d.status, d.root_cause_classification)
            for d in engine.reconcile(pr, g2b)
        ]
        assert current_run == first_run, f"Run #{run_idx + 1} produced divergent reconciliation results!"
