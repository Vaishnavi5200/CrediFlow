"""
CrediFlow Deterministic Compliance & Math Engine
Zero-hallucination guarantee: All tax calculations, matching algorithms,
GSTIN checksum verifications, and ITC exposure quantifications are 100% deterministic.
LLMs are NEVER used for arithmetic or tax liabilities.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class MismatchType(str, Enum):
    MATCHED = "MATCHED"
    EXACT_MATCH = "EXACT_MATCH"
    AMOUNT_TOLERANT_MATCH = "AMOUNT_TOLERANT_MATCH"
    NEAR_MATCH = "NEAR_MATCH"
    TAX_HEAD_MISMATCH = "TAX_HEAD_MISMATCH"
    MISSING_IN_2B = "MISSING_IN_2B"            # Vendor did not file GSTR-1 or filed with wrong buyer GSTIN
    VALUE_MISMATCH = "VALUE_MISMATCH"          # Taxable value or tax amount differs (> ₹2)
    GSTIN_MISMATCH = "GSTIN_MISMATCH"          # Buyer/Supplier GSTIN format error or wrong state code
    HSN_MISMATCH = "HSN_MISMATCH"              # Wrong HSN code leading to rate dispute
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"        # Multiple candidates qualify under same rule - no guessing allowed
    TIMING_DIFFERENCE = "TIMING_DIFFERENCE"    # Invoice filed in subsequent tax period (Quarterly vs Monthly)
    MALFORMED_INPUT = "MALFORMED_INPUT"        # Corrupted row, invalid format, negative values


class MismatchSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class InvoiceRecord:
    invoice_number: str
    invoice_date: str
    supplier_gstin: str
    supplier_name: str
    buyer_gstin: str
    taxable_value: float
    igst: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    cess: float = 0.0
    total_amount: float = 0.0
    hsn_code: str = ""
    filing_period: str = "2026-04"
    doc_type: str = "INV"
    reverse_charge: bool = False

    def total_tax(self) -> float:
        return round(self.igst + self.cgst + self.sgst + self.cess, 2)

    def compute_total(self) -> float:
        if self.total_amount <= 0:
            self.total_amount = round(self.taxable_value + self.total_tax(), 2)
        return self.total_amount


@dataclass
class DiscrepancyResult:
    id: str
    invoice_number: str
    supplier_gstin: str
    supplier_name: str
    mismatch_type: MismatchType
    severity: MismatchSeverity
    itc_exposure_rupees: float
    purchase_register_tax: float
    gstr_2b_tax: float
    taxable_value_diff: float
    details: str
    rule_citation: str
    is_high_value: bool
    requires_human_gate: bool
    status: str = "PENDING_AUDIT"  # PENDING_AUDIT -> AUDITED -> HUMAN_GATE -> SENT -> RESOLVED -> VERIFIED -> NEEDS_REVIEW -> UNRESOLVED
    root_cause_classification: Optional[str] = None
    auditor_verdict: Optional[str] = None
    auditor_confidence: float = 0.0
    auditor_notes: Optional[str] = None
    nudge_english: Optional[str] = None
    nudge_hindi: Optional[str] = None
    amendment_steps: Optional[List[str]] = None
    matched_gstr2b_invoice: Optional[str] = None
    candidate_count: int = 0

    @property
    def root_cause_code(self) -> str:
        return self.root_cause_classification or self.mismatch_type.value

    @property
    def reconciliation_outcome(self) -> str:
        return self.mismatch_type.value

    @property
    def itc_exposure(self) -> float:
        return self.itc_exposure_rupees

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "supplier_gstin": self.supplier_gstin,
            "supplier_name": self.supplier_name,
            "mismatch_type": self.mismatch_type.value,
            "reconciliation_outcome": self.reconciliation_outcome,
            "severity": self.severity.value,
            "itc_exposure_rupees": self.itc_exposure_rupees,
            "itc_exposure": self.itc_exposure_rupees,
            "purchase_register_tax": self.purchase_register_tax,
            "gstr_2b_tax": self.gstr_2b_tax,
            "taxable_value_diff": self.taxable_value_diff,
            "details": self.details,
            "rule_citation": self.rule_citation,
            "is_high_value": self.is_high_value,
            "requires_human_gate": self.requires_human_gate,
            "status": self.status,
            "root_cause_classification": self.root_cause_classification,
            "root_cause_code": self.root_cause_code,
            "matched_gstr2b_invoice": self.matched_gstr2b_invoice,
            "candidate_count": self.candidate_count,
            "auditor_verdict": self.auditor_verdict,
            "auditor_confidence": self.auditor_confidence,
            "auditor_notes": self.auditor_notes,
            "nudge_english": self.nudge_english,
            "nudge_hindi": self.nudge_hindi,
            "amendment_steps": self.amendment_steps,
        }

    def resolve(self, resolution_note: str = "") -> None:
        """Marks this discrepancy as verified and resolved, setting unresolved ITC exposure to 0."""
        self.status = "VERIFIED_RESOLVED"
        self.itc_exposure_rupees = 0.0
        if resolution_note:
            self.details = f"{self.details} | Resolved: {resolution_note}"


# Indian GSTIN MOD-36 Checksum Validation Algorithm
# Format: 2 digits (State Code) + 10 chars (PAN) + 1 digit (Entity Code) + 'Z' + 1 checksum digit
GSTIN_CHAR_MAP = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def validate_gstin_checksum(gstin: str) -> Tuple[bool, str]:
    """
    Validates an Indian 15-digit GSTIN using the official statutory MOD-36 check digit algorithm.
    """
    if not gstin or not isinstance(gstin, str):
        return False, "GSTIN is missing or non-string"
    
    gstin = gstin.strip().upper()
    if len(gstin) != 15:
        return False, f"Invalid GSTIN length: {len(gstin)} (must be 15 chars)"
    
    gstin_regex = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(gstin_regex, gstin):
        return False, "GSTIN does not match statutory regex pattern (StateCode + PAN + Entity + Z + CheckDigit)"
    
    factor = 1
    total = 0
    for char in gstin[:-1]:
        if char not in GSTIN_CHAR_MAP:
            return False, f"Invalid character '{char}' in GSTIN"
        code_point = GSTIN_CHAR_MAP.index(char)
        addend = factor * code_point
        factor = 1 if factor == 2 else 2
        total += (addend // 36) + (addend % 36)
    
    remainder = total % 36
    check_code_point = (36 - remainder) % 36
    expected_char = GSTIN_CHAR_MAP[check_code_point]
    
    if gstin[-1] != expected_char:
        return False, f"Checksum verification failed: expected '{expected_char}', got '{gstin[-1]}'"
    
    return True, "Valid GSTIN"


def normalize_invoice_num(inv: str) -> str:
    """Normalizes invoice number by stripping special chars and leading zeros for fuzzy match check."""
    if not inv:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(inv).strip().upper()).lstrip("0")


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes the Levenshtein edit distance between two strings.
    100% deterministic dynamic programming.
    """
    s1 = str(s1 or "")
    s2 = str(s2 or "")
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    len1, len2 = len(s1), len(s2)
    dp = [list(range(len2 + 1))] + [[i + 1] + [0] * len2 for i in range(len1)]
    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            dp[i + 1][j + 1] = min(
                dp[i][j + 1] + 1,      # deletion
                dp[i + 1][j] + 1,      # insertion
                dp[i][j] + cost        # substitution
            )
    return dp[len1][len2]


class GSTReconciliationEngine:
    """
    Deterministic GST ITC Reconciliation and Exposure Engine.
    Implements Rule 60 CGST & Section 16(2)(aa) requirements.

    Strict Priority Matching Order:
      1. Exact Match (Exact GSTIN + Exact Invoice Number + Exact Amounts & Tax Heads)
      2. Amount-Tolerant Match (Exact GSTIN + Exact Invoice Number, amount difference <= ₹2.00)
      3. Near-Match (Exact GSTIN, Invoice Number Levenshtein distance <= 2, unconsumed single candidate)
      4. Tax-Head Mismatch (Exact GSTIN + Invoice Match, Total Tax matches within tolerance, but IGST vs CGST/SGST differs)
      5. Missing in GSTR-2B (No candidate found in GSTR-2B)

    Ambiguous candidate rule:
      If multiple candidates qualify under the same applicable rule, DO NOT GUESS.
      Flag as AMBIGUOUS_MATCH / NEEDS_REVIEW (unresolved).
    """
    def __init__(self, high_value_threshold: float = 50000.0, tolerance_rupees: float = 2.0):
        self.high_value_threshold = high_value_threshold
        self.tolerance_rupees = tolerance_rupees

    def reconcile(
        self,
        purchase_register: List[InvoiceRecord],
        gstr_2b_records: List[InvoiceRecord]
    ) -> List[DiscrepancyResult]:
        """
        Performs 100% deterministic matching between Purchase Register and GSTR-2B.
        Zero LLM arithmetic or probabilistic scoring.
        """
        discrepancies: List[DiscrepancyResult] = []

        gstr2b_indexed: List[Tuple[int, InvoiceRecord]] = list(enumerate(gstr_2b_records))
        for _, rec in gstr2b_indexed:
            rec.compute_total()

        consumed_2b_indices: set = set()

        for idx, pr in enumerate(purchase_register):
            pr.compute_total()
            disc_id = f"DISC-{pr.filing_period}-{idx+1:04d}"
            clean_pr_gstin = pr.supplier_gstin.strip().upper()
            clean_pr_inv = pr.invoice_number.strip().upper()
            pr_tax = pr.total_tax()

            # ── 0. Check Malformed Input ──────────────────────────────────────────
            is_valid_gstin, gstin_reason = validate_gstin_checksum(pr.supplier_gstin)
            if not is_valid_gstin:
                discrepancies.append(DiscrepancyResult(
                    id=disc_id,
                    invoice_number=pr.invoice_number,
                    supplier_gstin=pr.supplier_gstin,
                    supplier_name=pr.supplier_name,
                    mismatch_type=MismatchType.MALFORMED_INPUT,
                    severity=MismatchSeverity.CRITICAL,
                    itc_exposure_rupees=pr_tax,
                    purchase_register_tax=pr_tax,
                    gstr_2b_tax=0.0,
                    taxable_value_diff=pr.taxable_value,
                    details=f"Invalid Supplier GSTIN: {gstin_reason}",
                    rule_citation="Rule 60(1) CGST - Valid Supplier GSTIN mandatory for ITC credit stream",
                    is_high_value=pr_tax >= self.high_value_threshold,
                    requires_human_gate=True,
                    status="HUMAN_GATE",
                    root_cause_classification="INVALID_SUPPLIER_GSTIN_CHECKSUM"
                ))
                continue

            if pr.taxable_value < 0 or pr_tax < 0 or pr.cgst < 0 or pr.sgst < 0 or pr.igst < 0 or pr.cess < 0:
                discrepancies.append(DiscrepancyResult(
                    id=disc_id,
                    invoice_number=pr.invoice_number,
                    supplier_gstin=pr.supplier_gstin,
                    supplier_name=pr.supplier_name,
                    mismatch_type=MismatchType.MALFORMED_INPUT,
                    severity=MismatchSeverity.CRITICAL,
                    itc_exposure_rupees=abs(pr_tax),
                    purchase_register_tax=pr_tax,
                    gstr_2b_tax=0.0,
                    taxable_value_diff=pr.taxable_value,
                    details="Malformed record: Negative taxable or tax values in purchase register",
                    rule_citation="Section 16(2) CGST Act - Non-negative invoice validation constraint",
                    is_high_value=abs(pr_tax) >= self.high_value_threshold,
                    requires_human_gate=True,
                    status="HUMAN_GATE",
                    root_cause_classification="NEGATIVE_TAX_OR_VALUE"
                ))
                continue

            # ── 1 & 2. Exact Key Match (Exact GSTIN + Exact Invoice Number) ───────
            exact_key_candidates = [
                (g_idx, rec) for g_idx, rec in gstr2b_indexed
                if g_idx not in consumed_2b_indices
                and rec.supplier_gstin.strip().upper() == clean_pr_gstin
                and rec.invoice_number.strip().upper() == clean_pr_inv
            ]

            if len(exact_key_candidates) > 1:
                # Multiple identical invoice numbers for same vendor with differing values -> AMBIGUOUS
                tax_values = {round(rec.total_tax(), 2) for _, rec in exact_key_candidates}
                if len(tax_values) > 1:
                    severity = MismatchSeverity.CRITICAL if pr_tax >= self.high_value_threshold else MismatchSeverity.HIGH
                    discrepancies.append(DiscrepancyResult(
                        id=disc_id,
                        invoice_number=pr.invoice_number,
                        supplier_gstin=pr.supplier_gstin,
                        supplier_name=pr.supplier_name,
                        mismatch_type=MismatchType.AMBIGUOUS_MATCH,
                        severity=severity,
                        itc_exposure_rupees=pr_tax,
                        purchase_register_tax=pr_tax,
                        gstr_2b_tax=0.0,
                        taxable_value_diff=pr.taxable_value,
                        details=f"Ambiguous Match: Multiple conflicting records ({len(exact_key_candidates)}) found in GSTR-2B for invoice {pr.invoice_number} under supplier {pr.supplier_name}. Unresolved to prevent incorrect credit attribution.",
                        rule_citation="Rule 60 CGST - Deterministic matching: Ambiguous multi-candidate resolution requires human review",
                        is_high_value=pr_tax >= self.high_value_threshold,
                        requires_human_gate=True,
                        status="NEEDS_REVIEW",
                        root_cause_classification="AMBIGUOUS_CANDIDATES",
                        candidate_count=len(exact_key_candidates)
                    ))
                    continue
                # If all candidates have identical total tax, consume the first one deterministically
                g2b_idx, g2b = exact_key_candidates[0]
            elif len(exact_key_candidates) == 1:
                g2b_idx, g2b = exact_key_candidates[0]
            else:
                g2b_idx, g2b = None, None

            if g2b is not None:
                g2b_tax = g2b.total_tax()
                tax_diff = round(pr_tax - g2b_tax, 2)
                val_diff = round(pr.taxable_value - g2b.taxable_value, 2)
                abs_tax_diff = abs(tax_diff)
                abs_val_diff = abs(val_diff)
                igst_diff = round(abs(pr.igst - g2b.igst), 2)
                cgst_diff = round(abs(pr.cgst - g2b.cgst), 2)
                sgst_diff = round(abs(pr.sgst - g2b.sgst), 2)

                # Check if amount is within tolerance (<= ₹2.00)
                if abs_tax_diff <= self.tolerance_rupees and abs_val_diff <= self.tolerance_rupees:
                    # Check Tax-Head Mismatch (Priority 4)
                    # Total tax is equal within tolerance, but IGST vs CGST/SGST differs (> ₹2)
                    if (igst_diff > self.tolerance_rupees or cgst_diff > self.tolerance_rupees or sgst_diff > self.tolerance_rupees):
                        consumed_2b_indices.add(g2b_idx)
                        severity = MismatchSeverity.CRITICAL if pr_tax >= self.high_value_threshold else MismatchSeverity.HIGH
                        discrepancies.append(DiscrepancyResult(
                            id=disc_id,
                            invoice_number=pr.invoice_number,
                            supplier_gstin=pr.supplier_gstin,
                            supplier_name=pr.supplier_name,
                            mismatch_type=MismatchType.TAX_HEAD_MISMATCH,
                            severity=severity,
                            itc_exposure_rupees=pr_tax,
                            purchase_register_tax=pr_tax,
                            gstr_2b_tax=g2b_tax,
                            taxable_value_diff=val_diff,
                            details=f"Tax Head Mismatch: Buyer booked IGST=₹{pr.igst:,.2f}, CGST=₹{pr.cgst:,.2f}, SGST=₹{pr.sgst:,.2f} whereas Supplier reported IGST=₹{g2b.igst:,.2f}, CGST=₹{g2b.cgst:,.2f}, SGST=₹{g2b.sgst:,.2f}",
                            rule_citation="Section 77 CGST Act & Section 19 IGST Act - Tax wrongly paid under incorrect tax head (Inter-state vs Intra-state)",
                            is_high_value=pr_tax >= self.high_value_threshold,
                            requires_human_gate=(pr_tax >= self.high_value_threshold),
                            status="NEEDS_REVIEW",
                            root_cause_classification="TAX_HEAD_MISMATCH",
                            matched_gstr2b_invoice=g2b.invoice_number
                        ))
                        continue

                    # Check HSN code consistency
                    if pr.hsn_code and g2b.hsn_code and pr.hsn_code.strip() != g2b.hsn_code.strip():
                        consumed_2b_indices.add(g2b_idx)
                        hsn_exp = abs(tax_diff) if abs(tax_diff) > 0 else round(pr_tax * 0.18, 2)
                        discrepancies.append(DiscrepancyResult(
                            id=disc_id,
                            invoice_number=pr.invoice_number,
                            supplier_gstin=pr.supplier_gstin,
                            supplier_name=pr.supplier_name,
                            mismatch_type=MismatchType.HSN_MISMATCH,
                            severity=MismatchSeverity.MEDIUM,
                            itc_exposure_rupees=hsn_exp,
                            purchase_register_tax=pr_tax,
                            gstr_2b_tax=g2b_tax,
                            taxable_value_diff=val_diff,
                            details=f"HSN Mismatch: Purchase Register has HSN {pr.hsn_code}, but GSTR-2B reports HSN {g2b.hsn_code}",
                            rule_citation="Notification No. 78/2020 - Central Tax: Mandatory 6-digit HSN reporting compliance",
                            is_high_value=pr_tax >= self.high_value_threshold,
                            requires_human_gate=(pr_tax >= self.high_value_threshold),
                            status="PENDING_AUDIT",
                            root_cause_classification="HSN_CODE_DISCREPANCY",
                            matched_gstr2b_invoice=g2b.invoice_number
                        ))
                        continue

                    # Exact Match (diff == 0) or Amount-Tolerant Match (diff <= tolerance)
                    consumed_2b_indices.add(g2b_idx)
                    # 100% matched within statutory tolerance -> 0 exposure, no discrepancy
                    continue
                else:
                    # Amount difference > tolerance (e.g. > ₹2.00) -> Remains UNRESOLVED
                    consumed_2b_indices.add(g2b_idx)
                    exposure = max(0.0, tax_diff) if tax_diff > 0 else abs(tax_diff)
                    severity = MismatchSeverity.CRITICAL if exposure >= self.high_value_threshold else MismatchSeverity.HIGH
                    discrepancies.append(DiscrepancyResult(
                        id=disc_id,
                        invoice_number=pr.invoice_number,
                        supplier_gstin=pr.supplier_gstin,
                        supplier_name=pr.supplier_name,
                        mismatch_type=MismatchType.VALUE_MISMATCH,
                        severity=severity,
                        itc_exposure_rupees=exposure,
                        purchase_register_tax=pr_tax,
                        gstr_2b_tax=g2b_tax,
                        taxable_value_diff=val_diff,
                        details=f"Value Discrepancy: Buyer claimed ₹{pr_tax:,.2f} tax on ₹{pr.taxable_value:,.2f}, but vendor filed ₹{g2b_tax:,.2f} tax on ₹{g2b.taxable_value:,.2f} (Diff: ₹{tax_diff:,.2f})",
                        rule_citation="Rule 60(7) CGST - Provisional ITC blocked on excess value claimed over GSTR-2B",
                        is_high_value=exposure >= self.high_value_threshold,
                        requires_human_gate=(exposure >= self.high_value_threshold),
                        status="UNRESOLVED",
                        root_cause_classification="VALUE_MISMATCH",
                        matched_gstr2b_invoice=g2b.invoice_number
                    ))
                    continue

            # ── 3. Near-Match (Exact GSTIN, Levenshtein distance <= 2) ─────────────
            near_candidates = [
                (g_idx, rec) for g_idx, rec in gstr2b_indexed
                if g_idx not in consumed_2b_indices
                and rec.supplier_gstin.strip().upper() == clean_pr_gstin
                and levenshtein_distance(clean_pr_inv, rec.invoice_number.strip().upper()) <= 2
            ]

            if len(near_candidates) > 1:
                # Ambiguous near-matches: DO NOT GUESS
                severity = MismatchSeverity.CRITICAL if pr_tax >= self.high_value_threshold else MismatchSeverity.HIGH
                discrepancies.append(DiscrepancyResult(
                    id=disc_id,
                    invoice_number=pr.invoice_number,
                    supplier_gstin=pr.supplier_gstin,
                    supplier_name=pr.supplier_name,
                    mismatch_type=MismatchType.AMBIGUOUS_MATCH,
                    severity=severity,
                    itc_exposure_rupees=pr_tax,
                    purchase_register_tax=pr_tax,
                    gstr_2b_tax=0.0,
                    taxable_value_diff=pr.taxable_value,
                    details=f"Ambiguous Near-Match: Found {len(near_candidates)} candidate invoices in GSTR-2B for supplier {pr.supplier_name} with Levenshtein distance ≤ 2 ({', '.join(r.invoice_number for _, r in near_candidates[:3])}). Matching withheld to prevent incorrect attribution.",
                    rule_citation="Rule 60 CGST - Deterministic matching: Ambiguous multi-candidate resolution requires human review",
                    is_high_value=pr_tax >= self.high_value_threshold,
                    requires_human_gate=True,
                    status="NEEDS_REVIEW",
                    root_cause_classification="AMBIGUOUS_CANDIDATES",
                    candidate_count=len(near_candidates)
                ))
                continue

            elif len(near_candidates) == 1:
                g2b_idx, g2b = near_candidates[0]
                dist = levenshtein_distance(clean_pr_inv, g2b.invoice_number.strip().upper())
                g2b_tax = g2b.total_tax()
                tax_diff = round(pr_tax - g2b_tax, 2)
                val_diff = round(pr.taxable_value - g2b.taxable_value, 2)
                igst_diff = round(abs(pr.igst - g2b.igst), 2)
                cgst_diff = round(abs(pr.cgst - g2b.cgst), 2)
                sgst_diff = round(abs(pr.sgst - g2b.sgst), 2)

                if abs(tax_diff) <= self.tolerance_rupees and abs(val_diff) <= self.tolerance_rupees:
                    # Check Tax-Head Mismatch for near candidate
                    if (igst_diff > self.tolerance_rupees or cgst_diff > self.tolerance_rupees or sgst_diff > self.tolerance_rupees):
                        consumed_2b_indices.add(g2b_idx)
                        severity = MismatchSeverity.CRITICAL if pr_tax >= self.high_value_threshold else MismatchSeverity.HIGH
                        discrepancies.append(DiscrepancyResult(
                            id=disc_id,
                            invoice_number=pr.invoice_number,
                            supplier_gstin=pr.supplier_gstin,
                            supplier_name=pr.supplier_name,
                            mismatch_type=MismatchType.TAX_HEAD_MISMATCH,
                            severity=severity,
                            itc_exposure_rupees=pr_tax,
                            purchase_register_tax=pr_tax,
                            gstr_2b_tax=g2b_tax,
                            taxable_value_diff=val_diff,
                            details=f"Near-Match & Tax Head Mismatch: Invoice near-match '{g2b.invoice_number}' (dist={dist}) has tax head mismatch (IGST vs CGST/SGST)",
                            rule_citation="Section 77 CGST Act & Section 19 IGST Act - Tax wrongly paid under incorrect tax head",
                            is_high_value=pr_tax >= self.high_value_threshold,
                            requires_human_gate=(pr_tax >= self.high_value_threshold),
                            status="NEEDS_REVIEW",
                            root_cause_classification="TAX_HEAD_MISMATCH",
                            matched_gstr2b_invoice=g2b.invoice_number
                        ))
                        continue
                    else:
                        consumed_2b_indices.add(g2b_idx)
                        discrepancies.append(DiscrepancyResult(
                            id=disc_id,
                            invoice_number=pr.invoice_number,
                            supplier_gstin=pr.supplier_gstin,
                            supplier_name=pr.supplier_name,
                            mismatch_type=MismatchType.NEAR_MATCH,
                            severity=MismatchSeverity.LOW if pr_tax < self.high_value_threshold else MismatchSeverity.MEDIUM,
                            itc_exposure_rupees=abs(tax_diff),
                            purchase_register_tax=pr_tax,
                            gstr_2b_tax=g2b_tax,
                            taxable_value_diff=val_diff,
                            details=f"Near-Match (Levenshtein distance={dist}): Purchase Register '{pr.invoice_number}' matches GSTR-2B '{g2b.invoice_number}' for supplier {pr.supplier_name}",
                            rule_citation="Rule 60(1) CGST - Near-match invoice punctuation/typo requires verification before GSTR-3B credit claim",
                            is_high_value=pr_tax >= self.high_value_threshold,
                            requires_human_gate=(pr_tax >= self.high_value_threshold),
                            status="NEEDS_REVIEW",
                            root_cause_classification="NEAR_MATCH_INVOICE_TYPO",
                            matched_gstr2b_invoice=g2b.invoice_number
                        ))
                        continue
                else:
                    # Near candidate found but amount differs > tolerance
                    consumed_2b_indices.add(g2b_idx)
                    exposure = max(0.0, tax_diff) if tax_diff > 0 else abs(tax_diff)
                    severity = MismatchSeverity.CRITICAL if exposure >= self.high_value_threshold else MismatchSeverity.HIGH
                    discrepancies.append(DiscrepancyResult(
                        id=disc_id,
                        invoice_number=pr.invoice_number,
                        supplier_gstin=pr.supplier_gstin,
                        supplier_name=pr.supplier_name,
                        mismatch_type=MismatchType.VALUE_MISMATCH,
                        severity=severity,
                        itc_exposure_rupees=exposure,
                        purchase_register_tax=pr_tax,
                        gstr_2b_tax=g2b_tax,
                        taxable_value_diff=val_diff,
                        details=f"Near-Match Value Discrepancy: Candidate '{g2b.invoice_number}' (dist={dist}) found but value differs by ₹{tax_diff:,.2f}",
                        rule_citation="Rule 60(7) CGST - Provisional ITC blocked on excess value claimed over GSTR-2B",
                        is_high_value=exposure >= self.high_value_threshold,
                        requires_human_gate=(exposure >= self.high_value_threshold),
                        status="UNRESOLVED",
                        root_cause_classification="VALUE_MISMATCH",
                        matched_gstr2b_invoice=g2b.invoice_number
                    ))
                    continue

            # ── 4. Check for Cross-GSTIN Branch Mismatch ──────────────────────────
            norm_pr_inv = normalize_invoice_num(pr.invoice_number)
            cross_gstin_candidates = [
                (g_idx, rec) for g_idx, rec in gstr2b_indexed
                if g_idx not in consumed_2b_indices
                and (rec.invoice_number.strip().upper() == clean_pr_inv or (norm_pr_inv and normalize_invoice_num(rec.invoice_number) == norm_pr_inv))
            ]

            if len(cross_gstin_candidates) > 1:
                severity = MismatchSeverity.CRITICAL if pr_tax >= self.high_value_threshold else MismatchSeverity.HIGH
                discrepancies.append(DiscrepancyResult(
                    id=disc_id,
                    invoice_number=pr.invoice_number,
                    supplier_gstin=pr.supplier_gstin,
                    supplier_name=pr.supplier_name,
                    mismatch_type=MismatchType.AMBIGUOUS_MATCH,
                    severity=severity,
                    itc_exposure_rupees=pr_tax,
                    purchase_register_tax=pr_tax,
                    gstr_2b_tax=0.0,
                    taxable_value_diff=pr.taxable_value,
                    details=f"Ambiguous Match: Multiple cross-GSTIN candidate records found in GSTR-2B for invoice {pr.invoice_number}",
                    rule_citation="Rule 60 CGST - Ambiguous cross-entity matching constraint",
                    is_high_value=pr_tax >= self.high_value_threshold,
                    requires_human_gate=True,
                    status="NEEDS_REVIEW",
                    root_cause_classification="AMBIGUOUS_CANDIDATES",
                    candidate_count=len(cross_gstin_candidates)
                ))
                continue

            elif len(cross_gstin_candidates) == 1:
                g2b_idx, candidate = cross_gstin_candidates[0]
                consumed_2b_indices.add(g2b_idx)
                cand_tax = candidate.total_tax()
                discrepancies.append(DiscrepancyResult(
                    id=disc_id,
                    invoice_number=pr.invoice_number,
                    supplier_gstin=pr.supplier_gstin,
                    supplier_name=pr.supplier_name,
                    mismatch_type=MismatchType.GSTIN_MISMATCH,
                    severity=MismatchSeverity.HIGH,
                    itc_exposure_rupees=pr_tax,
                    purchase_register_tax=pr_tax,
                    gstr_2b_tax=cand_tax,
                    taxable_value_diff=round(pr.taxable_value - candidate.taxable_value, 2),
                    details=f"GSTIN Discrepancy: Invoice {pr.invoice_number} found in 2B under GSTIN {candidate.supplier_gstin} instead of {pr.supplier_gstin}",
                    rule_citation="Section 16(2)(aa) CGST Act - ITC restricted if tax details not furnished under correct recipient GSTIN",
                    is_high_value=pr_tax >= self.high_value_threshold,
                    requires_human_gate=(pr_tax >= self.high_value_threshold),
                    status="PENDING_AUDIT",
                    root_cause_classification="GSTIN_BRANCH_MISMATCH",
                    matched_gstr2b_invoice=candidate.invoice_number
                ))
                continue

            # ── 5. Missing in GSTR-2B ──────────────────────────────────────────────
            severity = MismatchSeverity.CRITICAL if pr_tax >= self.high_value_threshold else MismatchSeverity.HIGH
            discrepancies.append(DiscrepancyResult(
                id=disc_id,
                invoice_number=pr.invoice_number,
                supplier_gstin=pr.supplier_gstin,
                supplier_name=pr.supplier_name,
                mismatch_type=MismatchType.MISSING_IN_2B,
                severity=severity,
                itc_exposure_rupees=pr_tax,
                purchase_register_tax=pr_tax,
                gstr_2b_tax=0.0,
                taxable_value_diff=pr.taxable_value,
                details=f"Invoice Missing in GSTR-2B: Supplier {pr.supplier_name} has not uploaded invoice {pr.invoice_number} in GSTR-1/IFF, or misreported as B2C",
                rule_citation="Rule 60 CGST (Zero Mismatch Mandate) - 100% Input Tax Credit blocked until supplier uploads invoice in GSTR-1",
                is_high_value=pr_tax >= self.high_value_threshold,
                requires_human_gate=(pr_tax >= self.high_value_threshold),
                status="UNRESOLVED",
                root_cause_classification="MISSING_IN_2B"
            ))

        return discrepancies

    @staticmethod
    def calculate_total_blocked_itc(discrepancies: List[DiscrepancyResult]) -> float:
        """
        Calculates total active/blocked ITC exposure across unresolved discrepancies.
        Resolved, verified, or matched discrepancies contribute ₹0.00.
        """
        return round(sum(
            d.itc_exposure_rupees for d in discrepancies
            if d.status not in ("RESOLVED", "VERIFIED", "VERIFIED_RESOLVED", "MATCHED")
        ), 2)

    @staticmethod
    def calculate_itc_breakdown(discrepancies: List[DiscrepancyResult]) -> Dict[str, Any]:
        """
        Returns structured deterministic summary of ITC exposures by root cause and status.
        """
        unresolved = [
            d for d in discrepancies
            if d.status not in ("RESOLVED", "VERIFIED", "VERIFIED_RESOLVED", "MATCHED")
        ]
        resolved = [
            d for d in discrepancies
            if d.status in ("RESOLVED", "VERIFIED", "VERIFIED_RESOLVED")
        ]

        by_root_cause: Dict[str, float] = {}
        by_outcome: Dict[str, int] = {}
        for d in unresolved:
            rc = d.root_cause_classification or d.mismatch_type.value
            by_root_cause[rc] = round(by_root_cause.get(rc, 0.0) + d.itc_exposure_rupees, 2)
            by_outcome[d.mismatch_type.value] = by_outcome.get(d.mismatch_type.value, 0) + 1

        total_blocked = round(sum(d.itc_exposure_rupees for d in unresolved), 2)
        return {
            "total_blocked_itc": total_blocked,
            "unresolved_count": len(unresolved),
            "resolved_count": len(resolved),
            "by_root_cause": by_root_cause,
            "by_outcome": by_outcome,
            "high_value_count": sum(1 for d in unresolved if d.is_high_value),
        }

    def resolve_and_recalculate(
        self,
        purchase_register: List[InvoiceRecord],
        gstr_2b_records: List[InvoiceRecord],
        resolved_invoice_number: str,
        amended_record: Optional[InvoiceRecord] = None
    ) -> Tuple[List[DiscrepancyResult], Dict[str, Any]]:
        """
        Applies a verified vendor amendment to GSTR-2B, re-runs deterministic reconciliation,
        and computes before/after blocked ITC and recovered amounts.
        """
        initial_discrepancies = self.reconcile(purchase_register, gstr_2b_records)
        initial_exposure = self.calculate_total_blocked_itc(initial_discrepancies)

        updated_g2b = list(gstr_2b_records)
        if amended_record is None:
            pr_rec = next((r for r in purchase_register if r.invoice_number == resolved_invoice_number), None)
            if pr_rec:
                amended_record = pr_rec

        if amended_record:
            replaced = False
            for idx, r in enumerate(updated_g2b):
                if r.invoice_number == resolved_invoice_number and r.supplier_gstin == amended_record.supplier_gstin:
                    updated_g2b[idx] = amended_record
                    replaced = True
                    break
            if not replaced:
                updated_g2b.append(amended_record)

        new_discrepancies = self.reconcile(purchase_register, updated_g2b)
        new_exposure = self.calculate_total_blocked_itc(new_discrepancies)
        recovered_itc = round(max(0.0, initial_exposure - new_exposure), 2)

        summary = {
            "invoice_number": resolved_invoice_number,
            "previous_exposure_rupees": initial_exposure,
            "current_exposure_rupees": new_exposure,
            "itc_recovered_rupees": recovered_itc,
            "remaining_discrepancies_count": len(new_discrepancies),
            "status": "VERIFIED_RESOLVED"
        }
        return new_discrepancies, summary
