"""
Synthetic B2B Invoice & GSTR-2B Dataset Generator.
Supports:
1. Exact 45-invoice Demo Register (matches CrediFlow HackWithUP 2026 Round 2 pitch scenario).
2. Scalable High-Volume Batch Generator (100 to 1,000+ invoices across 30+ B2B vendors).
3. Deliberate Malformed / Stress Test Generator for resilience verification.

All GSTINs use correct MOD-36 check digits, computed by the same algorithm used in gst_reconciliation.py.
"""

import random
from typing import List, Tuple
from .gst_reconciliation import InvoiceRecord

# ── Correct GSTINs with valid MOD-36 check digits ──────────────────────────────
# Each GSTIN was validated using compute_checksum() from the reconciliation engine.
SAMPLE_VENDORS = [
    {"name": "M/s Rajesh Traders",              "gstin": "27AABCR1234F1ZS", "state": "Maharashtra",    "hsn": "847130", "email": "rajesh.traders.gst@testmail.com", "phone": "+91 98201 54321"},
    {"name": "Apex Steel & Alloys Pvt Ltd",      "gstin": "24AAACA5678B1Z0", "state": "Gujarat",        "hsn": "720810", "email": "accounts@apexsteel.test",          "phone": "+91 98795 12340"},
    {"name": "Vardhman Textiles Ltd",            "gstin": "03AAACV9012D1ZV", "state": "Punjab",         "hsn": "520811", "email": "tax@vardhmantextiles.test",         "phone": "+91 94170 88990"},
    {"name": "Zenith Logistics Corp",            "gstin": "29AAACZ3456G1Z3", "state": "Karnataka",      "hsn": "996511", "email": "billing@zenithlogistics.test",      "phone": "+91 98450 11223"},
    {"name": "Dynamic Packaging Solutions",      "gstin": "07AAACD7890H1ZF", "state": "Delhi",          "hsn": "481910", "email": "finance@dynamicpack.test",          "phone": "+91 98110 33445"},
    {"name": "Bharat Heavy Electricals Vendor",  "gstin": "23AAACB1122J1ZD", "state": "Madhya Pradesh", "hsn": "850440", "email": "gst@bhelvendor.test",              "phone": "+91 94250 66778"},
    {"name": "Premier Chemicals & Solvents",     "gstin": "33AAACP3344K1ZK", "state": "Tamil Nadu",    "hsn": "290110", "email": "compliance@premierchem.test",       "phone": "+91 98400 55667"},
    {"name": "Kolkata Precision Tools",          "gstin": "19AAACK5566L1Z1", "state": "West Bengal",    "hsn": "820750", "email": "sales@kolkatatools.test",           "phone": "+91 98300 77889"},
    {"name": "Sunrise Hardware Industries",      "gstin": "06AAACS7788M1ZM", "state": "Haryana",        "hsn": "731815", "email": "info@sunrisehardware.test",         "phone": "+91 98120 99001"},
    {"name": "Universal Industrial Supplies",    "gstin": "36AAACU9900N1ZX", "state": "Telangana",      "hsn": "848210", "email": "accounts@universalind.test",        "phone": "+91 98490 22334"},
]

# Buyer is a Maharashtra-registered MSME — valid check digit 'I'
BUYER_GSTIN = "27AAACB0987A1Z1"


def generate_demo_dataset() -> Tuple[List[InvoiceRecord], List[InvoiceRecord]]:
    """
    Generates the official 45-invoice demo dataset matching the HackWithUP presentation.
    Total value ~₹18.4 Lakhs.
    Contains:
      - 40 Fully Matched Invoices
      - 1 Missing in GSTR-2B (Rajesh Traders: INV-0881, Tax: ₹42,500)
      - 2 Value Mismatch Invoices (Apex Steel, Dynamic Packaging)
      - 1 HSN Mismatch (Vardhman Textiles)
      - 1 GSTIN Mismatch / Branch Mismatch (Zenith Logistics)
    """
    purchase_register: List[InvoiceRecord] = []
    gstr_2b_records: List[InvoiceRecord] = []

    # ── 1. Flagship Mismatch: M/s Rajesh Traders INV-0881 (MISSING IN 2B) ──────
    rajesh_inv = InvoiceRecord(
        invoice_number="INV-0881",
        invoice_date="2026-04-12",
        supplier_gstin="27AABCR1234F1ZS",    # Valid GSTIN
        supplier_name="M/s Rajesh Traders",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=236111.11,
        cgst=21250.00,
        sgst=21250.00,
        igst=0.0,
        hsn_code="847130",
        filing_period="2026-04"
    )
    rajesh_inv.compute_total()
    purchase_register.append(rajesh_inv)
    # Intentionally NOT added to GSTR-2B → MISSING_IN_2B, exposure = ₹42,500

    # ── 2. Value Mismatch: Apex Steel & Alloys ──────────────────────────────────
    apex_pr = InvoiceRecord(
        invoice_number="INV-2045",
        invoice_date="2026-04-15",
        supplier_gstin="24AAACA5678B1Z0",
        supplier_name="Apex Steel & Alloys Pvt Ltd",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=150000.00,
        igst=27000.00,
        hsn_code="720810",
        filing_period="2026-04"
    )
    apex_pr.compute_total()
    purchase_register.append(apex_pr)

    apex_2b = InvoiceRecord(
        invoice_number="INV-2045",
        invoice_date="2026-04-15",
        supplier_gstin="24AAACA5678B1Z0",
        supplier_name="Apex Steel & Alloys Pvt Ltd",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=100000.00,   # Vendor reported lower value → exposure ₹9,000
        igst=18000.00,
        hsn_code="720810",
        filing_period="2026-04"
    )
    apex_2b.compute_total()
    gstr_2b_records.append(apex_2b)

    # ── 3. Value Mismatch: Dynamic Packaging Solutions ───────────────────────────
    dyn_pr = InvoiceRecord(
        invoice_number="DPS-8891",
        invoice_date="2026-04-18",
        supplier_gstin="07AAACD7890H1ZF",
        supplier_name="Dynamic Packaging Solutions",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=85000.00,
        igst=15300.00,
        hsn_code="481910",
        filing_period="2026-04"
    )
    dyn_pr.compute_total()
    purchase_register.append(dyn_pr)

    dyn_2b = InvoiceRecord(
        invoice_number="DPS-8891",
        invoice_date="2026-04-18",
        supplier_gstin="07AAACD7890H1ZF",
        supplier_name="Dynamic Packaging Solutions",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=60000.00,
        igst=10800.00,             # Difference → exposure ₹4,500
        hsn_code="481910",
        filing_period="2026-04"
    )
    dyn_2b.compute_total()
    gstr_2b_records.append(dyn_2b)

    # ── 4. HSN Mismatch: Vardhman Textiles Ltd ──────────────────────────────────
    vardh_pr = InvoiceRecord(
        invoice_number="VTX-4412",
        invoice_date="2026-04-20",
        supplier_gstin="03AAACV9012D1ZV",
        supplier_name="Vardhman Textiles Ltd",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=120000.00,
        igst=6000.00,              # 5% rate on 520811
        hsn_code="520811",
        filing_period="2026-04"
    )
    vardh_pr.compute_total()
    purchase_register.append(vardh_pr)

    vardh_2b = InvoiceRecord(
        invoice_number="VTX-4412",
        invoice_date="2026-04-20",
        supplier_gstin="03AAACV9012D1ZV",
        supplier_name="Vardhman Textiles Ltd",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=120000.00,
        igst=6000.00,
        hsn_code="520899",         # Different HSN sub-classification → HSN_MISMATCH
        filing_period="2026-04"
    )
    vardh_2b.compute_total()
    gstr_2b_records.append(vardh_2b)

    # ── 5. GSTIN Branch Mismatch: Zenith Logistics Corp ─────────────────────────
    # Karnataka branch GSTIN in PO but filed under different state branch
    zen_pr = InvoiceRecord(
        invoice_number="ZLOG-9923",
        invoice_date="2026-04-22",
        supplier_gstin="29AAACZ3456G1Z3",   # Karnataka GSTIN
        supplier_name="Zenith Logistics Corp",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=75000.00,
        igst=13500.00,
        hsn_code="996511",
        filing_period="2026-04"
    )
    zen_pr.compute_total()
    purchase_register.append(zen_pr)

    # Compute valid Maharashtra branch GSTIN: 27AAACZ3456G1Z?
    zen_maha_gstin = "27AAACZ3456G1ZK"    # Different state code = GSTIN_MISMATCH
    zen_2b = InvoiceRecord(
        invoice_number="ZLOG-9923",
        invoice_date="2026-04-22",
        supplier_gstin=zen_maha_gstin,      # Filed under Maharashtra branch
        supplier_name="Zenith Logistics Corp",
        buyer_gstin=BUYER_GSTIN,
        taxable_value=75000.00,
        cgst=6750.00,
        sgst=6750.00,
        hsn_code="996511",
        filing_period="2026-04"
    )
    zen_2b.compute_total()
    gstr_2b_records.append(zen_2b)

    # ── 6. 40 Fully Matched Invoices (~₹11.7L) ───────────────────────────────────
    base_taxable_pool = [25000, 32000, 18500, 42000, 15000, 29000, 36000, 48000, 22000, 19500]
    for i in range(1, 41):
        v = SAMPLE_VENDORS[i % len(SAMPLE_VENDORS)]
        inv_no = f"INV-2026-{1000 + i}"
        taxable = base_taxable_pool[i % len(base_taxable_pool)] + (i * 150)
        is_interstate = not v["gstin"].startswith("27")
        rate = 0.18

        if is_interstate:
            igst = round(taxable * rate, 2)
            cgst = 0.0
            sgst = 0.0
        else:
            igst = 0.0
            cgst = round(taxable * (rate / 2), 2)
            sgst = round(taxable * (rate / 2), 2)

        inv = InvoiceRecord(
            invoice_number=inv_no,
            invoice_date=f"2026-04-{min(28, (i % 25) + 1):02d}",
            supplier_gstin=v["gstin"],
            supplier_name=v["name"],
            buyer_gstin=BUYER_GSTIN,
            taxable_value=taxable,
            igst=igst,
            cgst=cgst,
            sgst=sgst,
            hsn_code=v["hsn"],
            filing_period="2026-04"
        )
        inv.compute_total()
        purchase_register.append(inv)
        gstr_2b_records.append(inv)   # Exact match

    return purchase_register, gstr_2b_records


def generate_batch_dataset(count: int = 500, mismatch_ratio: float = 0.08) -> Tuple[List[InvoiceRecord], List[InvoiceRecord]]:
    """
    Generates scalable high-volume batch dataset for performance benchmarking.
    Default: 500 invoices with ~8% realistic mismatch distribution.
    Seed is fixed so results are reproducible.
    """
    random.seed(42)
    purchase_register: List[InvoiceRecord] = []
    gstr_2b_records: List[InvoiceRecord] = []

    for i in range(1, count + 1):
        v = SAMPLE_VENDORS[i % len(SAMPLE_VENDORS)]
        inv_no = f"BAT-{i:05d}"
        taxable = round(random.uniform(15000, 250000), 2)
        rate = random.choice([0.05, 0.12, 0.18, 0.28])
        is_interstate = not v["gstin"].startswith("27")

        if is_interstate:
            igst = round(taxable * rate, 2)
            cgst = 0.0
            sgst = 0.0
        else:
            igst = 0.0
            cgst = round(taxable * (rate / 2), 2)
            sgst = round(taxable * (rate / 2), 2)

        pr_inv = InvoiceRecord(
            invoice_number=inv_no,
            invoice_date=f"2026-04-{random.randint(1, 28):02d}",
            supplier_gstin=v["gstin"],
            supplier_name=v["name"],
            buyer_gstin=BUYER_GSTIN,
            taxable_value=taxable,
            igst=igst, cgst=cgst, sgst=sgst,
            hsn_code=v["hsn"],
            filing_period="2026-04"
        )
        pr_inv.compute_total()
        purchase_register.append(pr_inv)

        roll = random.random()
        if roll < mismatch_ratio:
            error_type = random.choice(["missing", "value_under", "value_over", "hsn"])
            if error_type == "missing":
                pass  # Not added to 2B → MISSING_IN_2B
            elif error_type in ("value_under", "value_over"):
                factor = 0.70 if error_type == "value_under" else 1.20
                rep_taxable = round(taxable * factor, 2)
                rep_rate = rate
                g2b_inv = InvoiceRecord(
                    invoice_number=inv_no,
                    invoice_date=pr_inv.invoice_date,
                    supplier_gstin=v["gstin"],
                    supplier_name=v["name"],
                    buyer_gstin=BUYER_GSTIN,
                    taxable_value=rep_taxable,
                    igst=round(rep_taxable * rep_rate, 2) if is_interstate else 0.0,
                    cgst=0.0 if is_interstate else round(rep_taxable * (rep_rate / 2), 2),
                    sgst=0.0 if is_interstate else round(rep_taxable * (rep_rate / 2), 2),
                    hsn_code=v["hsn"],
                    filing_period="2026-04"
                )
                g2b_inv.compute_total()
                gstr_2b_records.append(g2b_inv)
            elif error_type == "hsn":
                g2b_inv = InvoiceRecord(
                    invoice_number=inv_no,
                    invoice_date=pr_inv.invoice_date,
                    supplier_gstin=v["gstin"],
                    supplier_name=v["name"],
                    buyer_gstin=BUYER_GSTIN,
                    taxable_value=taxable,
                    igst=igst, cgst=cgst, sgst=sgst,
                    hsn_code=str(int(v["hsn"]) + 5),   # Slightly different HSN
                    filing_period="2026-04"
                )
                g2b_inv.compute_total()
                gstr_2b_records.append(g2b_inv)
        else:
            gstr_2b_records.append(pr_inv)  # Exact match

    return purchase_register, gstr_2b_records


def generate_deliberate_error_dataset() -> Tuple[List[InvoiceRecord], List[InvoiceRecord]]:
    """
    Generates dataset with deliberately corrupted/malformed entries to verify pipeline resilience (§7):
      - Bad GSTIN check digit
      - Negative taxable value
      - Special / garbage characters in supplier name
    The normal 45-invoice demo is included as a base (all valid).
    """
    normal_pr, normal_2b = generate_demo_dataset()

    malformed_rows = [
        # Bad GSTIN check digit (S→9 is wrong)
        InvoiceRecord(
            invoice_number="ERR-GSTIN-BAD",
            invoice_date="2026-04-10",
            supplier_gstin="27AABCR1234F1Z9",   # Correct is 27AABCR1234F1ZS
            supplier_name="Malformed GSTIN Vendor Corp",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=50000.0,
            igst=9000.0,
            hsn_code="847130"
        ),
        # Negative taxable value — illegal under GST
        InvoiceRecord(
            invoice_number="ERR-NEG-VAL",
            invoice_date="2026-04-11",
            supplier_gstin="24AAACA5678B1Z0",    # Valid GSTIN but value is wrong
            supplier_name="Negative Value Supplier",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=-25000.0,
            igst=-4500.0,
            hsn_code="720810"
        ),
        # Garbage characters in vendor name / invoice number
        InvoiceRecord(
            invoice_number="ERR-SPECIAL-!@#$%",
            invoice_date="2026-04-12",
            supplier_gstin="03AAACV9012D1ZV",    # Valid GSTIN
            supplier_name="Garbage äöüß\x00 Vendor",
            buyer_gstin=BUYER_GSTIN,
            taxable_value=30000.0,
            igst=5400.0,
            hsn_code="520811"
        ),
    ]

    for m in malformed_rows:
        m.compute_total()
        normal_pr.append(m)

    return normal_pr, normal_2b
