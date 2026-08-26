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
    MISSING_IN_2B = "MISSING_IN_2B"            # Vendor did not file GSTR-1 or filed with wrong buyer GSTIN
    VALUE_MISMATCH = "VALUE_MISMATCH"          # Taxable value or tax amount differs
    GSTIN_MISMATCH = "GSTIN_MISMATCH"          # Buyer/Supplier GSTIN format error or wrong state code
    HSN_MISMATCH = "HSN_MISMATCH"              # Wrong HSN code leading to rate dispute
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
    status: str = "PENDING_AUDIT"  # PENDING_AUDIT -> AUDITED -> HUMAN_GATE -> SENT -> RESOLVED -> VERIFIED
    root_cause_classification: Optional[str] = None
    auditor_verdict: Optional[str] = None
    auditor_confidence: float = 0.0
    auditor_notes: Optional[str] = None
    nudge_english: Optional[str] = None
    nudge_hindi: Optional[str] = None
    amendment_steps: Optional[List[str]] = None


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


class GSTReconciliationEngine:
    """
    Deterministic GST ITC Reconciliation and Exposure Engine.
    Implements Rule 60 CGST & Section 16(2)(aa) requirements.
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
        Identifies unmatched, value mismatch, GSTIN mismatch, and HSN mismatch cases.
        """
        discrepancies: List[DiscrepancyResult] = []
        
        # Build indexing dictionaries for fast lookup
        gstr2b_by_key: Dict[Tuple[str, str], InvoiceRecord] = {}
        gstr2b_by_norm_inv: Dict[str, List[InvoiceRecord]] = {}

        for rec in gstr_2b_records:
            rec.compute_total()
            key = (rec.supplier_gstin.strip().upper(), rec.invoice_number.strip().upper())
            gstr2b_by_key[key] = rec
            
            norm_inv = normalize_invoice_num(rec.invoice_number)
            if norm_inv:
                gstr2b_by_norm_inv.setdefault(norm_inv, []).append(rec)

        processed_2b_keys = set()

        for idx, pr in enumerate(purchase_register):
            pr.compute_total()
            disc_id = f"DISC-{pr.filing_period}-{idx+1:04d}"
            pr_key = (pr.supplier_gstin.strip().upper(), pr.invoice_number.strip().upper())
            pr_tax = pr.total_tax()

            # 1. First check if row is malformed
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
                    status="HUMAN_GATE"
                ))
                continue

            if pr.taxable_value < 0 or pr_tax < 0:
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
                    status="HUMAN_GATE"
                ))
                continue

            # 2. Check for exact match in GSTR-2B
            matched_2b = gstr2b_by_key.get(pr_key)

            if matched_2b:
                processed_2b_keys.add(pr_key)
                gstr2b_tax = matched_2b.total_tax()
                tax_diff = round(pr_tax - gstr2b_tax, 2)
                val_diff = round(pr.taxable_value - matched_2b.taxable_value, 2)

                # Check amount tolerance (e.g. within ₹2 rounding difference)
                if abs(tax_diff) <= self.tolerance_rupees and abs(val_diff) <= self.tolerance_rupees:
                    # Check HSN code consistency
                    if pr.hsn_code and matched_2b.hsn_code and pr.hsn_code.strip() != matched_2b.hsn_code.strip():
                        discrepancies.append(DiscrepancyResult(
                            id=disc_id,
                            invoice_number=pr.invoice_number,
                            supplier_gstin=pr.supplier_gstin,
                            supplier_name=pr.supplier_name,
                            mismatch_type=MismatchType.HSN_MISMATCH,
                            severity=MismatchSeverity.MEDIUM,
                            itc_exposure_rupees=abs(tax_diff) if abs(tax_diff) > 0 else round(pr_tax * 0.18, 2),
                            purchase_register_tax=pr_tax,
                            gstr_2b_tax=gstr2b_tax,
                            taxable_value_diff=val_diff,
                            details=f"HSN Mismatch: Purchase Register has HSN {pr.hsn_code}, but GSTR-2B reports HSN {matched_2b.hsn_code}",
                            rule_citation="Notification No. 78/2020 - Central Tax: Mandatory 6-digit HSN reporting compliance",
                            is_high_value=pr_tax >= self.high_value_threshold,
                            requires_human_gate=(pr_tax >= self.high_value_threshold)
                        ))
                    else:
                        # Full match - 0 exposure
                        pass
                else:
                    # Value Mismatch: Supplier reported different taxable value or tax rate
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
                        gstr_2b_tax=gstr2b_tax,
                        taxable_value_diff=val_diff,
                        details=f"Value Discrepancy: Buyer claimed ₹{pr_tax:,.2f} tax on ₹{pr.taxable_value:,.2f}, but vendor filed ₹{gstr2b_tax:,.2f} tax on ₹{matched_2b.taxable_value:,.2f} (Diff: ₹{tax_diff:,.2f})",
                        rule_citation="Rule 60(7) CGST - Provisional ITC blocked on excess value claimed over GSTR-2B",
                        is_high_value=exposure >= self.high_value_threshold,
                        requires_human_gate=(exposure >= self.high_value_threshold)
                    ))
            else:
                # 3. Check if invoice number exists under different GSTIN or fuzzy timing
                norm_pr_inv = normalize_invoice_num(pr.invoice_number)
                possible_matches = gstr2b_by_norm_inv.get(norm_pr_inv, [])

                if possible_matches:
                    candidate = possible_matches[0]
                    # GSTIN typo or filed under sister branch GSTIN
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
                        requires_human_gate=(pr_tax >= self.high_value_threshold)
                    ))
                else:
                    # 4. Entirely Missing in GSTR-2B (100% ITC at risk)
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
                        requires_human_gate=(pr_tax >= self.high_value_threshold)
                    ))

        return discrepancies
