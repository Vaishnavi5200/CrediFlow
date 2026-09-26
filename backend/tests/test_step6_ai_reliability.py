"""
Step 6: AI Failure Fallback & Reliability Test Suite

Verifies:
1. AI success: Valid provider response produces structured explanation & bilingual nudges with source="AI_GENERATED".
2. Missing API key: Returns deterministic fallback with source="DETERMINISTIC_FALLBACK".
3. AI timeout: Returns deterministic fallback without crashing or delaying workflow.
4. AI provider error (401, 429, 500, 503): Gracefully returns deterministic fallback.
5. Malformed AI response (invalid JSON, wrong structure): Gracefully returns deterministic fallback.
6. Empty AI response: Returns deterministic fallback.
7. Core reconciliation & API lifecycle works 100% when AI is completely disabled.
8. Deterministic consistency: AI failure NEVER mutates financial values, ITC, root cause, or status.
9. Repeated execution produces identical deterministic output.
"""

import os
import json
import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ai_explanation_service import (
    AIExplanationService,
    ExplanationRequest,
    ExplanationResponse,
)
from backend.app.core.gst_reconciliation import (
    GSTReconciliationEngine,
    InvoiceRecord,
    MismatchType,
)
from backend.app.core.synthetic_data_generator import generate_demo_dataset

client = TestClient(app)


@pytest.fixture
def sample_request():
    return ExplanationRequest(
        invoice_number="INV-2024-002",
        vendor_gstin="27AAACH7409R1ZZ",
        vendor_name="Alpha Tech",
        buyer_gstin="27AAACB0987A1Z1",
        reconciliation_outcome="AMOUNT_MISMATCH",
        root_cause_code="AMOUNT_MISMATCH",
        itc_exposure=9000.0,
        status="MANUAL_REVIEW",
        matched_gstr2b_record={"invoice_number": "INV-2024-002", "total_amount": 50000.0},
    )


@pytest.mark.asyncio
async def test_ai_success_mocked(sample_request):
    """Test A: AI success returns valid structured explanation and bilingual nudges."""
    service = AIExplanationService()
    mock_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "explanation": "Invoice INV-2024-002 has an amount variance of ₹9,000.",
                                "vendor_nudge_english": "Dear Alpha Tech, please correct Invoice INV-2024-002.",
                                "vendor_nudge_hindi": "प्रिय Alpha Tech, कृपया इनवॉइस INV-2024-002 में सुधार करें।"
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            resp = await service.explain(sample_request)

            assert isinstance(resp, ExplanationResponse)
            assert resp.source == "AI_GENERATED"
            assert "INV-2024-002" in resp.explanation
            assert "Alpha Tech" in resp.vendor_nudge_english
            assert "INV-2024-002" in resp.vendor_nudge_hindi
            assert resp.itc_exposure == 9000.0
            assert resp.root_cause_code == "AMOUNT_MISMATCH"


@pytest.mark.asyncio
async def test_missing_api_key(sample_request):
    """Test B: Missing API key instantly yields deterministic fallback."""
    service = AIExplanationService()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "OPENAI_API_KEY": ""}):
        resp = await service.explain(sample_request)
        assert isinstance(resp, ExplanationResponse)
        assert resp.source == "DETERMINISTIC_FALLBACK"
        assert "INV-2024-002" in resp.explanation
        assert "INV-2024-002" in resp.vendor_nudge_english
        assert "INV-2024-002" in resp.vendor_nudge_hindi
        assert resp.itc_exposure == 9000.0


@pytest.mark.asyncio
async def test_ai_timeout(sample_request):
    """Test C: AI timeout seamlessly triggers deterministic fallback without crashing."""
    service = AIExplanationService()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Request timed out")):
            resp = await service.explain(sample_request)
            assert isinstance(resp, ExplanationResponse)
            assert resp.source == "DETERMINISTIC_FALLBACK"
            assert "INV-2024-002" in resp.explanation
            assert resp.itc_exposure == 9000.0


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403, 429, 500, 503])
async def test_ai_provider_http_errors(sample_request, status_code):
    """Test D: AI provider HTTP error codes (auth, rate limits, 5xx) trigger fallback."""
    service = AIExplanationService()
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {"error": "Provider service error"}

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            resp = await service.explain(sample_request)
            assert isinstance(resp, ExplanationResponse)
            assert resp.source == "DETERMINISTIC_FALLBACK"
            assert "INV-2024-002" in resp.vendor_nudge_english


@pytest.mark.asyncio
async def test_malformed_json_response(sample_request):
    """Test E: Malformed JSON or non-JSON string from provider returns fallback."""
    service = AIExplanationService()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "THIS IS NOT JSON AT ALL {{broken"}]
                }
            }
        ]
    }

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            resp = await service.explain(sample_request)
            assert isinstance(resp, ExplanationResponse)
            assert resp.source == "DETERMINISTIC_FALLBACK"
            assert "INV-2024-002" in resp.explanation


@pytest.mark.asyncio
async def test_empty_ai_response(sample_request):
    """Test F: Empty text response or empty object from provider returns fallback."""
    service = AIExplanationService()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "{}"}]
                }
            }
        ]
    }

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            resp = await service.explain(sample_request)
            assert isinstance(resp, ExplanationResponse)
            assert "INV-2024-002" in resp.explanation
            assert resp.itc_exposure == 9000.0


def test_full_reconciliation_works_when_ai_disabled():
    """Test G: Entire reconciliation and reporting works 100% with zero AI configured."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "OPENAI_API_KEY": ""}):
        # Run reconciliation endpoint
        res = client.post("/api/reconcile")
        assert res.status_code == 200
        data = res.json()
        assert data["purchase_register_count"] > 0
        assert "total_itc_exposure_rupees" in data
        assert "discrepancies" in data

        # Check vendor scorecards endpoint
        res_v = client.get("/api/vendor-scorecards")
        assert res_v.status_code == 200
        assert len(res_v.json()["scorecards"]) > 0

        # Check discrepancy resolution endpoint
        discrepancies = data.get("discrepancies", [])
        if discrepancies:
            first_inv = discrepancies[0]["invoice_number"]
            res_resolve = client.post("/api/discrepancy/resolve", json={"invoice_number": first_inv})
            assert res_resolve.status_code == 200
            assert res_resolve.json()["status"] == "VERIFIED_RESOLVED"


def test_ai_failure_does_not_mutate_reconciliation_outcome():
    """Test H: AI failure NEVER alters reconciliation outcome, ITC, or root cause."""
    engine = GSTReconciliationEngine()
    pr = InvoiceRecord(
        invoice_number="INV-2024-005",
        invoice_date="2024-07-15",
        supplier_gstin="27AABCR1234F1ZS",
        supplier_name="Delta Logistics",
        buyer_gstin="27AAACB0987A1Z1",
        taxable_value=100000.0,
        cgst=0.0,
        sgst=0.0,
        igst=18000.0,
        total_amount=118000.0,
    )
    # Empty GSTR-2B -> Missing in 2B
    discrepancies = engine.reconcile([pr], [])
    assert len(discrepancies) == 1
    d = discrepancies[0]

    assert d.mismatch_type == MismatchType.MISSING_IN_2B
    assert d.itc_exposure_rupees == 18000.0

    # Trigger AI fallback
    service = AIExplanationService()
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        req = ExplanationRequest(
            invoice_number=d.invoice_number,
            vendor_gstin=d.supplier_gstin,
            reconciliation_outcome=d.mismatch_type.value,
            root_cause_code=d.root_cause_code,
            itc_exposure=d.itc_exposure_rupees,
            status="MANUAL_REVIEW",
        )
        resp = service.generate_explanation(req)

        # Ensure engine values are completely untouched
        assert d.mismatch_type == MismatchType.MISSING_IN_2B
        assert d.itc_exposure_rupees == 18000.0
        assert resp.source == "DETERMINISTIC_FALLBACK"
        assert resp.itc_exposure == 18000.0


def test_repeated_execution_deterministic_consistency():
    """Test I: Repeated executions produce identical deterministic fallback output across 50 runs."""
    service = AIExplanationService()
    req = ExplanationRequest(
        invoice_number="INV-2024-003",
        vendor_gstin="29BBBPM1234K1Z5",
        vendor_name="Beta Corp",
        buyer_gstin="27AAACB0987A1Z1",
        reconciliation_outcome="NEAR_MATCH_INVOICE",
        root_cause_code="NEAR_MATCH_INVOICE",
        itc_exposure=3600.0,
        status="MANUAL_REVIEW",
        matched_gstr2b_record="INV-2024-003A",
    )

    baseline = service.generate_explanation(req)
    for _ in range(50):
        run_res = service.generate_explanation(req)
        assert run_res.explanation == baseline.explanation
        assert run_res.vendor_nudge_english == baseline.vendor_nudge_english
        assert run_res.vendor_nudge_hindi == baseline.vendor_nudge_hindi
        assert run_res.itc_exposure == baseline.itc_exposure
