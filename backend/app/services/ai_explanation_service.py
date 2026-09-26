"""
CrediFlow AI Explanation & Bilingual Vendor Nudge Service

Architecture & Discipline Rules:
1. Downstream Presentation Layer ONLY:
   - Receives ONLY structured deterministic reconciliation results.
   - Does NOT decide matching, does NOT calculate ITC, does NOT change root causes or statuses.
   - Never overrides or modifies deterministic engine values.
2. Structured Input -> Structured Output Contract:
   - Returns:
     {
       "explanation": "...",
       "vendor_nudge_english": "...",
       "vendor_nudge_hindi": "...",
       "source": "AI_GENERATED" | "DETERMINISTIC_FALLBACK",
       "root_cause_code": "...",
       "itc_exposure": 0.0
     }
3. 100% Reliable Fallback:
   - If AI credentials are missing, API call fails, or rate limit occurs, immediately
     returns deterministic template output matching the root cause without crashing.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExplanationRequest(BaseModel):
    invoice_number: str
    vendor_gstin: Optional[str] = "27AABCR1234F1ZS"
    vendor_name: Optional[str] = "Supplier"
    buyer_gstin: Optional[str] = "27AAACB0987A1Z1"
    reconciliation_outcome: Optional[str] = "UNRESOLVED"
    root_cause_code: Optional[str] = "MISSING_IN_2B"
    itc_exposure: Optional[float] = 0.0
    status: Optional[str] = "MANUAL_REVIEW"
    matched_gstr2b_record: Optional[Any] = None
    comparison_details: Optional[Dict[str, Any]] = None
    details: Optional[str] = ""
    taxable_value: Optional[float] = 0.0


class ExplanationResponse(BaseModel):
    explanation: str
    vendor_nudge_english: str
    vendor_nudge_hindi: str
    source: str  # "AI_GENERATED" or "DETERMINISTIC_FALLBACK"
    root_cause_code: str
    itc_exposure: float
    invoice_number: str
    status: str


class AIExplanationService:
    """
    AI explanation & bilingual communication generator with 100% deterministic fallback.
    """

    def __init__(self, timeout_seconds: float = 6.0):
        self.timeout_seconds = timeout_seconds

    def generate_fallback_explanation(self, req: ExplanationRequest) -> ExplanationResponse:
        """
        Generates deterministic, root-cause-specific explanation and bilingual vendor nudges.
        Guarantees 100% availability with zero external API dependencies.
        """
        code = (req.root_cause_code or req.reconciliation_outcome or "UNKNOWN").upper()
        inv = req.invoice_number
        vendor = req.vendor_name or "Supplier"
        itc = req.itc_exposure
        buyer = req.buyer_gstin or "27AAACB0987A1Z1"

        if code in ("MISSING_IN_2B", "MISSING_IN_GSTR_2B", "INVOICE_MISSING_IN_2B"):
            explanation = (
                f"Invoice {inv} from supplier {vendor} (GSTIN: {req.vendor_gstin}) was found in your Purchase Register "
                f"with an ITC exposure of ₹{itc:,.2f}, but is absent from the auto-drafted GSTR-2B statement. "
                f"This occurs when the supplier has not uploaded the invoice in their GSTR-1 return or reported it as B2C. "
                f"Recommended action: Nudge the vendor to add Invoice {inv} under Table 4A in their GSTR-1 filing."
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"During our GST reconciliation, Invoice No. {inv} (ITC: ₹{itc:,.2f}) was not found in our GSTR-2B statement. "
                f"Please verify if this invoice has been reported under Table 4A of your GSTR-1 return for Buyer GSTIN {buyer}. "
                f"Once uploaded, we will re-run reconciliation to confirm Input Tax Credit clearance.\n\n"
                f"Thank you,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"हमारे GST मिलान के दौरान, इनवॉइस संख्या {inv} (ITC: ₹{itc:,.2f}) हमारे GSTR-2B में नहीं पाया गया है। "
                f"कृपया जांचें कि क्या यह इनवॉइस खरीदार GSTIN {buyer} के तहत आपके GSTR-1 के Table 4A में दर्ज किया गया है। "
                f"आपके सुधार के बाद, हम इनपुट टैक्स क्रेडिट की पुष्टि के लिए पुन: मिलान करेंगे।\n\n"
                f"धन्यवाद,\nवित्त विभाग"
            )

        elif code in ("AMOUNT_MISMATCH", "VALUE_MISMATCH", "RATE_OR_VALUE_DISCREPANCY"):
            explanation = (
                f"Invoice {inv} has an amount variance between your Purchase Register and the supplier's GSTR-2B record. "
                f"The unresolved ITC exposure at risk is ₹{itc:,.2f}. The recorded tax values differ, blocking full credit claim. "
                f"Recommended action: Request the vendor to verify invoice values and file an amendment (Table 9A) in GSTR-1."
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"We identified a tax amount mismatch for Invoice No. {inv} between our Purchase Register and GSTR-2B "
                f"(Variance ITC at risk: ₹{itc:,.2f}). Please review the taxable value and tax rate reported in your GSTR-1 return "
                f"and issue an amendment (Table 9A) if required. We will re-run reconciliation after the correction.\n\n"
                f"Thank you,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"हमारे परचेज रजिस्टर और GSTR-2B के बीच इनवॉइस संख्या {inv} के टैक्स मूल्य में अंतर पाया गया है "
                f"(जोखिम में ITC: ₹{itc:,.2f})। कृपया अपने GSTR-1 में दर्ज कर योग्य मूल्य और टैक्स दर की समीक्षा करें "
                f"और आवश्यक होने पर संशोधन (Table 9A) फाइल करें। सुधार के बाद हम पुन: मिलान करेंगे।\n\n"
                f"धन्यवाद,\nवित्त विभाग"
            )

        elif code in ("TAX_HEAD_MISMATCH", "TAX_HEAD_DIFFERENCE"):
            explanation = (
                f"Invoice {inv} has a tax-head mismatch between the Purchase Register and GSTR-2B (e.g. IGST vs CGST/SGST). "
                f"Total blocked ITC is ₹{itc:,.2f}. The tax was reported under a different head in GSTR-1 than on the physical invoice. "
                f"Recommended action: Request the vendor to verify the Place of Supply and amend the tax head in GSTR-1."
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"We noticed a tax-head mismatch for Invoice No. {inv} (ITC at risk: ₹{itc:,.2f}). The tax type reported in GSTR-1 "
                f"does not align with the invoice classification (e.g., IGST vs CGST/SGST). Please review the Place of Supply and "
                f"tax heads in your GSTR-1 filing and amend accordingly so we can re-reconcile.\n\n"
                f"Thank you,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"इनवॉइस संख्या {inv} के लिए टैक्स-हेड (IGST बनाम CGST/SGST) में विसंगति पाई गई है (जोखिम में ITC: ₹{itc:,.2f})। "
                f"कृपया अपने GSTR-1 में सप्लाई का स्थान (Place of Supply) और टैक्स हेड की जांच करें और सुधार करें ताकि हम पुन: मिलान कर सकें।\n\n"
                f"धन्यवाद,\nवित्त विभाग"
            )

        elif code in ("NEAR_MATCH_INVOICE", "INVOICE_NUMBER_MISMATCH", "NEAR_MATCH"):
            matched_rec = f" (similar to {req.matched_gstr2b_record})" if req.matched_gstr2b_record else ""
            explanation = (
                f"Invoice {inv} has an invoice reference discrepancy{matched_rec}. "
                f"The invoice number in your records differs slightly (e.g., typos, prefixes, slashes) from GSTR-2B. "
                f"Unresolved ITC exposure is ₹{itc:,.2f}. "
                f"Recommended action: Ask the vendor to confirm the exact invoice reference uploaded in GSTR-1."
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"We found a potential invoice reference discrepancy for Invoice No. {inv} during GST reconciliation "
                f"(ITC: ₹{itc:,.2f}). A similar invoice was auto-drafted in GSTR-2B{matched_rec}. "
                f"Please confirm the exact invoice number reported in your GSTR-1 and amend if necessary so we can complete reconciliation.\n\n"
                f"Thank you,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"GST मिलान में इनवॉइस संख्या {inv} के संदर्भ में संभावित संख्या भिन्नता पाई गई है (ITC: ₹{itc:,.2f})। "
                f"कृपया अपने GSTR-1 में दर्ज सटीक इनवॉइस नंबर की पुष्टि करें और आवश्यकतानुसार संशोधन करें ताकि हम मिलान पूरा कर सकें।\n\n"
                f"धन्यवाद,\nवित्त विभाग"
            )

        elif code in ("AMBIGUOUS_CANDIDATES", "NEEDS_REVIEW", "MULTIPLE_CANDIDATES"):
            explanation = (
                f"Invoice {inv} has multiple possible matching candidate records in GSTR-2B. "
                f"To maintain deterministic compliance, the engine flagged this invoice for human review rather than guessing. "
                f"ITC at risk is ₹{itc:,.2f}. "
                f"Recommended action: Review the candidate invoices with the vendor to verify the exact transaction record."
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"Regarding Invoice No. {inv} (ITC: ₹{itc:,.2f}), our system detected multiple similar records in GSTR-2B. "
                f"Please share the exact invoice copy and filing confirmation so we can verify and reconcile the appropriate record.\n\n"
                f"Thank you,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"इनवॉइस संख्या {inv} (ITC: ₹{itc:,.2f}) के संबंध में, हमारे सिस्टम ने GSTR-2B में एक से अधिक समान रिकॉर्ड पाए हैं। "
                f"कृपया सटीक इनवॉइस प्रति और फाइलिंग विवरण साझा करें ताकि हम सही रिकॉर्ड का मिलान कर सकें।\n\n"
                f"धन्यवाद,\nवित्त विभाग"
            )

        elif code in ("EXACT_MATCH", "AMOUNT_TOLERANT_MATCH", "MATCHED"):
            explanation = (
                f"Invoice {inv} is fully reconciled with GSTR-2B. "
                f"Reconciliation outcome: {req.reconciliation_outcome}. "
                f"100% Input Tax Credit is verified and compliant. No action required."
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"Invoice No. {inv} is fully verified and reconciled with our GSTR-2B. "
                f"No action is required. Thank you for your prompt GST filing.\n\n"
                f"Best regards,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"इनवॉइस संख्या {inv} का GSTR-2B से पूर्ण मिलान और सत्यापन हो चुका है। "
                f"किसी कार्रवाई की आवश्यकता नहीं है। समय पर GST फाइलिंग के लिए धन्यवाद।\n\n"
                f"सादर,\nवित्त विभाग"
            )

        else:
            explanation = (
                f"Invoice {inv} has a discrepancy classified under root cause '{code}'. "
                f"Total unresolved ITC exposure is ₹{itc:,.2f}. "
                f"Details: {req.details or 'Requires verification under statutory Rule 60 CGST guidelines.'}"
            )
            nudge_en = (
                f"Dear {vendor},\n\n"
                f"We detected a GST compliance variance for Invoice No. {inv} (ITC: ₹{itc:,.2f}). "
                f"Please review your GSTR-1 filing details for this invoice and let us know if an amendment is required. "
                f"We will re-run reconciliation upon confirmation.\n\n"
                f"Thank you,\nFinance Team"
            )
            nudge_hi = (
                f"प्रिय {vendor},\n\n"
                f"इनवॉइस संख्या {inv} (ITC: ₹{itc:,.2f}) के लिए GST अनुपालन में विसंगति पाई गई है। "
                f"कृपया इस इनवॉइस के लिए अपने GSTR-1 फाइलिंग विवरण की समीक्षा करें और हमें बताएं कि क्या संशोधन की आवश्यकता है। "
                f"पुष्टि के बाद हम पुन: मिलान करेंगे।\n\n"
                f"धन्यवाद,\nवित्त विभाग"
            )

        return ExplanationResponse(
            explanation=explanation,
            vendor_nudge_english=nudge_en,
            vendor_nudge_hindi=nudge_hi,
            source="DETERMINISTIC_FALLBACK",
            root_cause_code=code,
            itc_exposure=itc,
            invoice_number=inv,
            status=req.status
        )

    async def explain(self, req: ExplanationRequest) -> ExplanationResponse:
        """
        Attempts to generate an explanation and bilingual vendor nudges using configured LLM API.
        If no API key exists, request times out, provider returns error, or response is malformed,
        seamlessly returns the deterministic fallback with zero disruption.
        """
        gemini_api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
        openai_api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()

        if not gemini_api_key and not openai_api_key:
            return self.generate_fallback_explanation(req)

        # Build strict structured prompt containing only deterministic facts
        facts = {
            "invoice_number": req.invoice_number,
            "vendor_name": req.vendor_name,
            "vendor_gstin": req.vendor_gstin,
            "buyer_gstin": req.buyer_gstin,
            "reconciliation_outcome": req.reconciliation_outcome,
            "root_cause_code": req.root_cause_code,
            "itc_exposure_inr": req.itc_exposure,
            "status": req.status,
            "matched_gstr2b_record": req.matched_gstr2b_record,
            "engine_details": req.details
        }

        system_instruction = (
            "You are a professional GST compliance explanation and communication assistant. "
            "Your role is STRICTLY to explain the deterministic reconciliation result provided in JSON. "
            "RULES:\n"
            "1. Do NOT calculate or change financial amounts or ITC values.\n"
            "2. Do NOT change the root-cause code or reconciliation status.\n"
            "3. Do NOT invent missing GST rules, penalty amounts, or unverified claims.\n"
            "4. Generate a concise explanation (2-3 sentences), a polite English vendor nudge, and a fluent Hindi vendor nudge.\n"
            "5. Both nudges must state: (a) invoice number, (b) detected issue, (c) what to check/correct in GSTR-1, (d) that buyer will re-run reconciliation after correction.\n"
            "6. Output MUST be valid JSON with keys: 'explanation', 'vendor_nudge_english', 'vendor_nudge_hindi'."
        )

        prompt_user = f"Deterministic Reconciliation Result:\n{json.dumps(facts, indent=2)}\n\nGenerate JSON response."

        try:
            if gemini_api_key:
                # Call Gemini REST API
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt_user}"}]}],
                    "generationConfig": {
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                        "maxOutputTokens": 800
                    }
                }
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text_content = parts[0].get("text", "").strip()
                                if text_content:
                                    parsed = json.loads(text_content)
                                    if isinstance(parsed, dict) and any(parsed.values()):
                                        fallback = self.generate_fallback_explanation(req)
                                        exp_text = str(parsed.get("explanation", "")).strip() or fallback.explanation
                                        en_text = str(parsed.get("vendor_nudge_english", "")).strip() or fallback.vendor_nudge_english
                                        hi_text = str(parsed.get("vendor_nudge_hindi", "")).strip() or fallback.vendor_nudge_hindi
                                        return ExplanationResponse(
                                            explanation=exp_text,
                                            vendor_nudge_english=en_text,
                                            vendor_nudge_hindi=hi_text,
                                            source="AI_GENERATED",
                                            root_cause_code=req.root_cause_code,
                                            itc_exposure=req.itc_exposure,
                                            invoice_number=req.invoice_number,
                                            status=req.status
                                        )

            elif openai_api_key:
                # Call OpenAI REST API
                url = "https://api.openai.com/v1/chat/completions"
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt_user}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 800
                }
                headers = {"Authorization": f"Bearer {openai_api_key}"}
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            text_content = choices[0].get("message", {}).get("content", "").strip()
                            if text_content:
                                parsed = json.loads(text_content)
                                if isinstance(parsed, dict) and any(parsed.values()):
                                    fallback = self.generate_fallback_explanation(req)
                                    exp_text = str(parsed.get("explanation", "")).strip() or fallback.explanation
                                    en_text = str(parsed.get("vendor_nudge_english", "")).strip() or fallback.vendor_nudge_english
                                    hi_text = str(parsed.get("vendor_nudge_hindi", "")).strip() or fallback.vendor_nudge_hindi
                                    return ExplanationResponse(
                                        explanation=exp_text,
                                        vendor_nudge_english=en_text,
                                        vendor_nudge_hindi=hi_text,
                                        source="AI_GENERATED",
                                        root_cause_code=req.root_cause_code,
                                        itc_exposure=req.itc_exposure,
                                        invoice_number=req.invoice_number,
                                        status=req.status
                                    )
        except Exception as e:
            logger.warning("AI explanation provider error or timeout: %s. Falling back to deterministic statutory templates.", e.__class__.__name__)

        # Seamless Fallback on any failure
        return self.generate_fallback_explanation(req)

    def generate_explanation(self, req: ExplanationRequest) -> ExplanationResponse:
        """
        Synchronous helper for explanation generation using deterministic statutory templates.
        """
        return self.generate_fallback_explanation(req)


# Global singleton instance
ai_explanation_service = AIExplanationService()
ai_explanation_svc = ai_explanation_service

