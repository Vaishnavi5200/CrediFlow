"""
CrediFlow WhatsApp Delivery Service

Architecture Rules (IMMUTABLE):
1. Deterministic reconciliation remains the ONLY source of truth.
   WhatsApp sending NEVER changes: reconciliation outcome, ITC, root cause,
   verification status.
2. Phone numbers must come from the data layer — never invented here.
3. Phone numbers are validated before any send attempt.
4. API credentials are read strictly from environment variables; never logged,
   never returned to the frontend.
5. On any failure (bad credentials, timeout, rate-limit, network error, missing
   phone): do NOT raise — return a structured result so the caller falls back
   to the wa.me link.
6. Sending a message changes *communication state only*, not financial/business
   state.

Delivery order:
  Primary  → WhatsApp Business API (Meta Cloud API v20.0)
  Fallback → wa.me deep-link with the bilingual nudge pre-filled
"""

from __future__ import annotations

import logging
import os
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Phone validation ───────────────────────────────────────────────────────────

_E164_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


def _normalise_phone(raw: str) -> Optional[str]:
    """
    Strips spaces / dashes / parentheses and validates E.164 format.
    Returns the normalised number (digits only, no leading +) or None.
    Examples:
      "+91 98201 54321"  ->  "919820154321"
      "+1-800-555-0100"  ->  "18005550100"
      "abc"              ->  None
    """
    if not raw or not isinstance(raw, str):
        return None
    stripped = re.sub(r"[\s\-().]+", "", raw.strip())
    candidate = stripped if stripped.startswith("+") else f"+{stripped}"
    if _E164_RE.match(candidate):
        return candidate.lstrip("+")
    return None


# ── WhatsApp Business API delivery ────────────────────────────────────────────

_WA_API_TIMEOUT = 8.0  # seconds


async def _send_via_whatsapp_api(
    phone_e164_digits: str,
    message_body: str,
    invoice_number: str,
) -> Dict[str, Any]:
    """
    Sends a free-form text message via the Meta WhatsApp Business Cloud API.

    Required environment variables (server-side only):
      WHATSAPP_API_TOKEN       -- permanent system user token
      WHATSAPP_PHONE_NUMBER_ID -- Phone Number ID from Meta Business Manager

    Optional:
      WHATSAPP_API_VERSION     -- API version (default: v20.0)

    Returns a result dict with `success`, `message_id` (on success), or
    `error` (on failure).  Never raises.
    """
    token = os.environ.get("WHATSAPP_API_TOKEN", "").strip()
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    api_version = os.environ.get("WHATSAPP_API_VERSION", "v20.0").strip()

    if not token or not phone_number_id:
        return {
            "success": False,
            "error": "WHATSAPP_API_NOT_CONFIGURED",
            "detail": "WHATSAPP_API_TOKEN or WHATSAPP_PHONE_NUMBER_ID not set in environment.",
        }

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_e164_digits,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_body,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=_WA_API_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            messages = data.get("messages", [])
            msg_id = messages[0].get("id", "") if messages else ""
            # Safe log: mask all but last 4 digits of phone
            logger.info(
                "[WhatsApp] Delivered invoice=%s to=***%s msg_id=%s",
                invoice_number,
                phone_e164_digits[-4:],
                msg_id,
            )
            return {"success": True, "message_id": msg_id}

        # Non-200 response
        try:
            error_body = resp.json()
        except Exception:
            error_body = resp.text[:200]

        # Safe log: never log the token
        logger.warning(
            "[WhatsApp] API error invoice=%s status=%s",
            invoice_number,
            resp.status_code,
        )
        return {
            "success": False,
            "error": "WHATSAPP_API_ERROR",
            "http_status": resp.status_code,
            "detail": str(error_body)[:300],
        }

    except httpx.TimeoutException:
        logger.warning("[WhatsApp] Timeout sending invoice=%s", invoice_number)
        return {"success": False, "error": "WHATSAPP_API_TIMEOUT"}
    except Exception as exc:
        logger.warning(
            "[WhatsApp] Unexpected error invoice=%s: %s", invoice_number, type(exc).__name__
        )
        return {"success": False, "error": "WHATSAPP_API_EXCEPTION", "detail": type(exc).__name__}


# ── wa.me fallback link builder ────────────────────────────────────────────────

def build_wame_fallback_url(phone_raw: str, message: str) -> str:
    """
    Builds a wa.me deep-link with the nudge message pre-filled.
    Works even when the phone number cannot be validated — we encode it as-is
    so the operator can still open WhatsApp manually.
    """
    normalised = _normalise_phone(phone_raw)
    phone_part = normalised if normalised else re.sub(r"[\s\-().+]", "", phone_raw)
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{phone_part}?text={encoded_msg}"


# ── Public entry point ─────────────────────────────────────────────────────────

async def deliver_whatsapp_nudge(
    *,
    vendor_phone: str,
    message_english: str,
    message_hindi: str,
    invoice_number: str,
    supplier_name: str,
) -> Dict[str, Any]:
    """
    Primary delivery function called by the API route.

    Flow:
      1. Validate phone number.
      2. Build combined bilingual message (English first, then Hindi).
      3. Attempt WhatsApp Business API send.
      4. On success -> return status NUDGED + method=API.
      5. On any failure -> return status FALLBACK + wa.me URL (never raise).

    IMPORTANT: This function only changes *communication state*.
    It never touches reconciliation results, ITC amounts, or verification status.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build the combined bilingual message for delivery
    combined_message = f"{message_english}\n\n---\n\n{message_hindi}"

    # Validate phone
    normalised_phone = _normalise_phone(vendor_phone)

    if not normalised_phone:
        logger.warning(
            "[WhatsApp] Invalid/missing phone for invoice=%s supplier=%s -- using wa.me fallback",
            invoice_number,
            supplier_name,
        )
        wame_url = build_wame_fallback_url(vendor_phone or "", combined_message)
        return {
            "delivery_method": "WAME_FALLBACK",
            "communication_status": "FALLBACK_WAME_READY",
            "wame_url": wame_url,
            "reason": "INVALID_OR_MISSING_PHONE",
            "api_attempted": False,
            "timestamp": timestamp,
            "invoice_number": invoice_number,
        }

    # Attempt WhatsApp Business API
    api_result = await _send_via_whatsapp_api(
        phone_e164_digits=normalised_phone,
        message_body=combined_message,
        invoice_number=invoice_number,
    )

    if api_result.get("success"):
        return {
            "delivery_method": "WHATSAPP_API",
            "communication_status": "NUDGED",
            "message_id": api_result.get("message_id", ""),
            "api_attempted": True,
            "api_success": True,
            "timestamp": timestamp,
            "invoice_number": invoice_number,
        }

    # API failed -- prepare wa.me fallback
    wame_url = build_wame_fallback_url(vendor_phone, combined_message)
    reason = api_result.get("error", "UNKNOWN")

    logger.info(
        "[WhatsApp] Falling back to wa.me for invoice=%s reason=%s",
        invoice_number,
        reason,
    )

    return {
        "delivery_method": "WAME_FALLBACK",
        "communication_status": "FALLBACK_WAME_READY",
        "wame_url": wame_url,
        "reason": reason,
        "api_attempted": True,
        "api_success": False,
        "api_error": reason,
        "timestamp": timestamp,
        "invoice_number": invoice_number,
    }
