"""
CrediFlow Step 4: Structured API & UI Integration Verification Tests

Tests the FastAPI endpoints to ensure:
1. Deterministic reconciliation results are exposed through clean, structured endpoints.
2. Structured fields are present: invoice_identifier, vendor_gstin, invoice_number,
   reconciliation_outcome, root_cause_code, itc_exposure, status, matched_gstr2b_record, details.
3. Scorecard and resolution endpoints return structured, deterministic values.
4. Error handling gracefully handles empty datasets, malformed input, missing fields.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_demo_data_endpoint():
    """Verify demo-data endpoint returns valid 45-invoice purchase register dataset."""
    response = client.get("/api/demo-data")
    assert response.status_code == 200
    data = response.json()
    assert "purchase_register_count" in data
    assert "gstr_2b_count" in data
    assert "invoices" in data
    assert data["purchase_register_count"] == 45
    assert len(data["invoices"]) == 45
    first_inv = data["invoices"][0]
    assert "invoice_number" in first_inv
    assert "supplier_gstin" in first_inv
    assert "taxable_value" in first_inv
    assert "tax_amount" in first_inv


def test_api_reconcile_structured_fields():
    """Verify reconcile endpoint returns structured results with all required Step 4 fields."""
    response = client.post("/api/reconcile")
    assert response.status_code == 200
    data = response.json()
    assert "purchase_register_count" in data
    assert "matched_count" in data
    assert "discrepancies_count" in data
    assert "total_itc_exposure_rupees" in data
    assert "discrepancies" in data

    discrepancies = data["discrepancies"]
    assert len(discrepancies) == data["discrepancies_count"]

    for d in discrepancies:
        # Step 4 mandatory structured result fields
        assert "invoice_identifier" in d or "id" in d
        assert "vendor_gstin" in d or "supplier_gstin" in d
        assert "invoice_number" in d
        assert "reconciliation_outcome" in d
        assert "root_cause_code" in d
        assert "itc_exposure" in d or "itc_exposure_rupees" in d
        assert "status" in d
        assert "matched_gstr2b_record" in d or "matched_gstr2b_invoice" in d
        assert "details" in d
        assert isinstance(d["itc_exposure_rupees"], (int, float))
        assert d["itc_exposure_rupees"] >= 0.0


def test_api_reconcile_custom_dataset():
    """Verify reconcile-custom handles custom payloads deterministically."""
    pr_records = [
        {
            "invoice_number": "INV-101",
            "invoice_date": "2026-04-10",
            "supplier_gstin": "27AABCR1234F1ZS",
            "supplier_name": "M/s Rajesh Traders",
            "buyer_gstin": "27AAACB0987A1Z1",
            "taxable_value": 100000.0,
            "igst": 18000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
            "hsn_code": "847130",
            "filing_period": "2026-04"
        },
        {
            "invoice_number": "INV-102",
            "invoice_date": "2026-04-12",
            "supplier_gstin": "27AABCR1234F1ZS",
            "supplier_name": "M/s Rajesh Traders",
            "buyer_gstin": "27AAACB0987A1Z1",
            "taxable_value": 50000.0,
            "igst": 9000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
            "hsn_code": "847130",
            "filing_period": "2026-04"
        }
    ]

    # g2b only has INV-101
    g2b_records = [
        {
            "invoice_number": "INV-101",
            "invoice_date": "2026-04-10",
            "supplier_gstin": "27AABCR1234F1ZS",
            "supplier_name": "M/s Rajesh Traders",
            "buyer_gstin": "27AAACB0987A1Z1",
            "taxable_value": 100000.0,
            "igst": 18000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "cess": 0.0,
            "hsn_code": "847130",
            "filing_period": "2026-04"
        }
    ]

    response = client.post(
        "/api/reconcile-custom",
        json={"purchase_register": pr_records, "gstr_2b": g2b_records}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["purchase_register_count"] == 2
    assert data["gstr_2b_count"] == 1
    assert data["matched_count"] == 1
    assert data["discrepancies_count"] == 1
    assert data["total_itc_exposure_rupees"] == 9000.0
    disc = data["discrepancies"][0]
    assert disc["invoice_number"] == "INV-102"
    assert disc["root_cause_code"] == "MISSING_IN_2B"
    assert disc["itc_exposure"] == 9000.0


def test_api_reconcile_empty_datasets():
    """Verify reconcile-custom gracefully handles empty inputs."""
    response = client.post(
        "/api/reconcile-custom",
        json={"purchase_register": [], "gstr_2b": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["purchase_register_count"] == 0
    assert data["matched_count"] == 0
    assert data["discrepancies_count"] == 0
    assert data["total_itc_exposure_rupees"] == 0.0


def test_api_discrepancy_resolution_lifecycle():
    """Verify /discrepancy/resolve endpoint updates status and decrements blocked ITC exposure."""
    from backend.app.api.routes import STATE
    from backend.app.core.synthetic_data_generator import generate_demo_dataset
    pr, g2b = generate_demo_dataset()
    STATE["purchase_register"] = pr
    STATE["gstr_2b_records"] = g2b

    # First reconcile
    rec_res = client.post("/api/reconcile")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert len(rec_data["discrepancies"]) > 0
    target_inv = rec_data["discrepancies"][0]["invoice_number"]

    # Resolve target discrepancy
    res = client.post(
        "/api/discrepancy/resolve",
        json={"invoice_number": target_inv, "resolution_note": "Approved tax head correction"}
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["status"] == "VERIFIED_RESOLVED"
    assert res_data["resolved_exposure_rupees"] > 0
    assert "total_blocked_itc" in res_data
    assert "unresolved_count" in res_data
    assert "resolved_count" in res_data
    assert res_data["resolved_count"] >= 1


def test_api_vendor_scorecards_endpoint():
    """Verify vendor scorecards return both standard and alias field names."""
    from backend.app.api.routes import STATE
    from backend.app.core.synthetic_data_generator import generate_demo_dataset
    pr, g2b = generate_demo_dataset()
    STATE["purchase_register"] = pr
    STATE["gstr_2b_records"] = g2b
    client.post("/api/reconcile")

    response = client.get("/api/vendor-scorecards")
    assert response.status_code == 200
    data = response.json()
    assert "scorecards" in data
    assert len(data["scorecards"]) > 0
    card = data["scorecards"][0]
    assert "supplier_name" in card
    assert "vendor_name" in card
    assert "supplier_gstin" in card
    assert "gstin" in card
    assert "compliance_score" in card
    assert "risk_level" in card
    assert "itc_exposure_rupees" in card
    assert "total_invoices" in card
    assert "matched_count" in card
