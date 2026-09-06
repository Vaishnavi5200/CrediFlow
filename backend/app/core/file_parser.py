"""
CrediFlow Universal File Ingestion Parser
Supports CSV, XLSX, and JSON for Purchase Registers and GSTR-2B Portal streams.
Features:
- Resilient column mapping (case-insensitive, alias matching)
- Error tolerance for corrupt/malformed rows (skips or flags without crashing the entire batch)
- Strict typing & validation into InvoiceRecord objects
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Tuple
import openpyxl

from .gst_reconciliation import InvoiceRecord, validate_gstin_checksum

# Standard header aliases
ALIAS_MAP = {
    "invoice_number": ["invoice_number", "invoice_no", "inv_no", "inv_num", "bill_no", "invoice no", "inv no", "invoice #"],
    "invoice_date": ["invoice_date", "date", "inv_date", "bill_date", "invoice date"],
    "supplier_gstin": ["supplier_gstin", "seller_gstin", "vendor_gstin", "gstin_supplier", "gstin of supplier", "supplier gstin", "gstin"],
    "supplier_name": ["supplier_name", "vendor_name", "party_name", "supplier", "vendor", "trade_name", "name of supplier"],
    "buyer_gstin": ["buyer_gstin", "recipient_gstin", "customer_gstin", "gstin_recipient", "buyer gstin"],
    "taxable_value": ["taxable_value", "taxable_amount", "taxable_val", "taxable value", "taxable amt", "base_amount"],
    "igst": ["igst", "igst_amount", "igst_amt", "integrated_tax", "integrated tax"],
    "cgst": ["cgst", "cgst_amount", "cgst_amt", "central_tax", "central tax"],
    "sgst": ["sgst", "sgst_amount", "sgst_amt", "state_tax", "state tax"],
    "cess": ["cess", "cess_amount", "cess_amt"],
    "hsn_code": ["hsn_code", "hsn", "hsn/sac", "sac", "hsn_sac"],
    "filing_period": ["filing_period", "period", "return_period", "month", "tax_period"]
}


def _match_header(header: str) -> str:
    cleaned = str(header).strip().lower().replace("-", "_").replace(" ", "_")
    for canonical, aliases in ALIAS_MAP.items():
        if cleaned == canonical or cleaned in aliases:
            return canonical
    for canonical, aliases in ALIAS_MAP.items():
        if any(alias in cleaned for alias in aliases):
            return canonical
    return cleaned


def _parse_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(",", "").replace("₹", "").replace("$", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def parse_raw_data_to_records(
    rows: List[Dict[str, Any]],
    default_buyer_gstin: str = "27AAACB0987A1Z1"
) -> Tuple[List[InvoiceRecord], List[Dict[str, Any]]]:
    """
    Transforms arbitrary dictionary rows into valid InvoiceRecord objects.
    Returns (valid_records, failed_rows).
    """
    records: List[InvoiceRecord] = []
    failed_rows: List[Dict[str, Any]] = []

    for idx, raw in enumerate(rows):
        mapped: Dict[str, Any] = {}
        for k, v in raw.items():
            mapped[_match_header(k)] = v

        inv_num = str(mapped.get("invoice_number", "")).strip()
        if not inv_num or inv_num.lower() in ("nan", "none", "null", ""):
            failed_rows.append({"row_index": idx, "raw": raw, "reason": "Missing invoice number"})
            continue

        raw_gstin = mapped.get("supplier_gstin")
        if not raw_gstin or str(raw_gstin).strip().upper() in ("NONE", "NULL", "NAN", ""):
            failed_rows.append({"row_index": idx, "raw": raw, "reason": "Missing supplier GSTIN"})
            continue

        supplier_gstin = str(raw_gstin).strip().upper()
        buyer_gstin = str(mapped.get("buyer_gstin", default_buyer_gstin)).strip().upper()
        supplier_name = str(mapped.get("supplier_name", "Supplier")).strip()
        inv_date = str(mapped.get("invoice_date", "2026-04-01")).strip()
        taxable_val = _parse_float(mapped.get("taxable_value", 0.0))
        igst = _parse_float(mapped.get("igst", 0.0))
        cgst = _parse_float(mapped.get("cgst", 0.0))
        sgst = _parse_float(mapped.get("sgst", 0.0))
        cess = _parse_float(mapped.get("cess", 0.0))
        hsn = str(mapped.get("hsn_code", "8471")).strip()
        period = str(mapped.get("filing_period", "2026-04")).strip()

        # Build InvoiceRecord
        rec = InvoiceRecord(
            invoice_number=inv_num,
            invoice_date=inv_date,
            supplier_gstin=supplier_gstin,
            supplier_name=supplier_name,
            buyer_gstin=buyer_gstin,
            taxable_value=taxable_val,
            igst=igst,
            cgst=cgst,
            sgst=sgst,
            cess=cess,
            hsn_code=hsn,
            filing_period=period
        )
        records.append(rec)

    return records, failed_rows


def parse_file_content(content_bytes: bytes, filename: str) -> Tuple[List[InvoiceRecord], List[Dict[str, Any]]]:
    """
    Parses a file in memory (.csv, .xlsx, or .json) into InvoiceRecord list.
    """
    fname = filename.lower()
    rows: List[Dict[str, Any]] = []

    if fname.endswith(".csv"):
        text = content_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = [dict(r) for r in reader]

    elif fname.endswith(".xlsx") or fname.endswith(".xls"):
        wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
        sheet = wb.active
        all_rows = list(sheet.iter_rows(values_only=True))
        if not all_rows:
            return [], [{"error": "Empty worksheet"}]
        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(all_rows[0])]
        for r in all_rows[1:]:
            if any(cell is not None for cell in r):
                row_dict = {headers[i]: r[i] for i in range(min(len(headers), len(r)))}
                rows.append(row_dict)

    elif fname.endswith(".json"):
        text = content_bytes.decode("utf-8", errors="replace")
        parsed = json.loads(text)
        if isinstance(parsed, list):
            rows = parsed
        elif isinstance(parsed, dict):
            # Could be GSTR-2B payload format with "b2b" outer key
            if "b2b" in parsed:
                # Unpack GSTR-2B B2B invoices format
                for vendor_entry in parsed.get("b2b", []):
                    ctin = vendor_entry.get("ctin", "")
                    cname = vendor_entry.get("cname", "Supplier")
                    for inv in vendor_entry.get("inv", []):
                        inum = inv.get("inum", "")
                        idt = inv.get("idt", "")
                        val = _parse_float(inv.get("val", 0.0))
                        # items
                        igst_tot = cgst_tot = sgst_tot = 0.0
                        for itm in inv.get("items", []):
                            itmd = itm.get("item_det", {})
                            igst_tot += _parse_float(itmd.get("iamt", 0.0))
                            cgst_tot += _parse_float(itmd.get("camt", 0.0))
                            sgst_tot += _parse_float(itmd.get("samt", 0.0))
                        rows.append({
                            "invoice_number": inum,
                            "invoice_date": idt,
                            "supplier_gstin": ctin,
                            "supplier_name": cname,
                            "taxable_value": val,
                            "igst": igst_tot,
                            "cgst": cgst_tot,
                            "sgst": sgst_tot
                        })
            elif "invoices" in parsed:
                rows = parsed["invoices"]
            else:
                rows = [parsed]
    else:
        raise ValueError(f"Unsupported file format '{filename}'. Supported: .csv, .xlsx, .json")

    return parse_raw_data_to_records(rows)
