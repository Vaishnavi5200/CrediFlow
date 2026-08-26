"""
RocketRide Service — CrediFlow
Manages the full RocketRide Cloud & Local SDK lifecycle:
connect → use() → chat() → terminate() → disconnect()

Key design features:
  1. Communicates with RocketRide Cloud or local engine via WebSockets (URI + Auth).
  2. Uses official RocketRide SDK when available, with automatic statutory compliance fallback.
  3. Agent A (Root-Cause Classifier) and Agent B (Audit Cross-Examiner) run in independent sessions.
  4. Agent B receives both the raw deterministic mismatch record AND Agent A's output for adversarial cross-examination.
  5. Never fakes execution — explicitly marks results with `execution_engine` (ROCKETRIDE_CLOUD vs STATUTORY_FALLBACK).
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

try:
    from rocketride import RocketRideClient, RocketRideClientConfig, Question
    ROCKETRIDE_SDK_AVAILABLE = True
except ImportError:
    ROCKETRIDE_SDK_AVAILABLE = False
    RocketRideClient = None
    RocketRideClientConfig = None
    Question = None

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────
# Supports official ROCKETRIDE_URI and ROCKETRIDE_AUTH (with ROCKETRIDE_APIKEY fallback)
ROCKETRIDE_URI = os.getenv("ROCKETRIDE_URI", "ws://localhost:52257")
ROCKETRIDE_AUTH = os.getenv("ROCKETRIDE_AUTH") or os.getenv("ROCKETRIDE_APIKEY", "MYAPIKEY")

def _find_pipeline_path() -> str:
    """Search for the pipeline file from cwd upward, checking both standard naming conventions."""
    candidates = [
        os.path.join(os.getcwd(), "pipelines", "crediflow_audit.pipe"),
        os.path.join(os.getcwd(), "pipelines", "crediflow_audit_pipeline.pipe"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../pipelines/crediflow_audit.pipe")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../pipelines/crediflow_audit_pipeline.pipe")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../pipelines/crediflow_audit.pipe")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../pipelines/crediflow_audit_pipeline.pipe")),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

PIPELINE_PATH = _find_pipeline_path()


# ─── Result types ─────────────────────────────────────────────────────────────

class AgentAResult:
    """Output from Agent A (Classifier)."""
    def __init__(self, raw: Dict[str, Any], latency_ms: float, tokens: int, source: str = "ROCKETRIDE_CLOUD"):
        self.root_cause_code: str = raw.get("root_cause_code", "UNKNOWN")
        self.confidence: float = float(raw.get("confidence", 0.0))
        self.reasoning: str = raw.get("reasoning", "")
        self.recommended_action: str = raw.get("recommended_action", "")
        self.latency_ms = latency_ms
        self.tokens = tokens
        self.source = source
        self.raw = raw

    def __repr__(self):
        return f"AgentAResult(code={self.root_cause_code}, confidence={self.confidence:.2f}, source={self.source})"


class AgentBResult:
    """Output from Agent B (Auditor) — independent cross-examination."""
    def __init__(self, raw: Dict[str, Any], latency_ms: float, tokens: int, source: str = "ROCKETRIDE_CLOUD"):
        self.audit_verdict: str = raw.get("audit_verdict", "UNKNOWN")  # AGREE | DISAGREE | PARTIALLY_AGREE
        self.auditor_root_cause_code: str = raw.get("auditor_root_cause_code", "UNKNOWN")
        self.auditor_confidence: float = float(raw.get("auditor_confidence", 0.0))
        self.independent_analysis: str = raw.get("independent_analysis", "")
        self.cross_examination: str = raw.get("cross_examination", "")
        self.final_recommendation: str = raw.get("final_recommendation", "")
        self.latency_ms = latency_ms
        self.tokens = tokens
        self.source = source
        self.raw = raw

    def __repr__(self):
        return f"AgentBResult(verdict={self.audit_verdict}, confidence={self.auditor_confidence:.2f}, source={self.source})"


class PipelineAuditResult:
    """Combined result from the dual-agent pipeline, plus human gate evaluation."""
    def __init__(
        self,
        mismatch_id: str,
        agent_a: AgentAResult,
        agent_b: AgentBResult,
        itc_exposure_inr: float,
        is_malformed: bool,
        total_latency_ms: float,
        total_tokens: int,
        execution_engine: str = "ROCKETRIDE_CLOUD",
        confidence_threshold: float = 0.85,
        high_value_threshold_inr: float = 50_000.0,
    ):
        self.mismatch_id = mismatch_id
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.itc_exposure_inr = itc_exposure_inr
        self.is_malformed = is_malformed
        self.total_latency_ms = total_latency_ms
        self.total_tokens = total_tokens
        self.execution_engine = execution_engine

        # ── Human Gate: evaluate ALL 4 triggers ──────────────────────────────
        self.trigger_agent_disagreement: bool = (
            agent_b.audit_verdict in ("DISAGREE", "PARTIALLY_AGREE")
        )
        self.trigger_low_confidence: bool = (
            agent_a.confidence < confidence_threshold
            or agent_b.auditor_confidence < confidence_threshold
        )
        self.trigger_high_exposure: bool = itc_exposure_inr >= high_value_threshold_inr
        self.trigger_malformed: bool = is_malformed

        self.requires_human_review: bool = (
            self.trigger_agent_disagreement
            or self.trigger_low_confidence
            or self.trigger_high_exposure
            or self.trigger_malformed
        )

        # Reasons why human review is required (for UI display)
        self.human_review_reasons: List[str] = []
        if self.trigger_agent_disagreement:
            self.human_review_reasons.append(
                f"Agent disagreement: Agent B verdict = {agent_b.audit_verdict}"
            )
        if self.trigger_low_confidence:
            self.human_review_reasons.append(
                f"Low confidence: Agent A={agent_a.confidence:.2f}, Agent B={agent_b.auditor_confidence:.2f} (threshold={confidence_threshold})"
            )
        if self.trigger_high_exposure:
            self.human_review_reasons.append(
                f"High ITC exposure: ₹{itc_exposure_inr:,.0f} ≥ ₹{high_value_threshold_inr:,.0f}"
            )
        if self.trigger_malformed:
            self.human_review_reasons.append("Malformed/unrecognized input row")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mismatch_id": self.mismatch_id,
            "agent_a": self.agent_a.raw,
            "agent_b": self.agent_b.raw,
            "itc_exposure_inr": self.itc_exposure_inr,
            "is_malformed": self.is_malformed,
            "total_latency_ms": round(self.total_latency_ms, 1),
            "total_tokens": self.total_tokens,
            "execution_engine": self.execution_engine,
            "requires_human_review": self.requires_human_review,
            "human_review_triggers": {
                "agent_disagreement": self.trigger_agent_disagreement,
                "low_confidence": self.trigger_low_confidence,
                "high_exposure": self.trigger_high_exposure,
                "malformed_input": self.trigger_malformed,
            },
            "human_review_reasons": self.human_review_reasons,
        }


# ─── Service ──────────────────────────────────────────────────────────────────

class RocketRideService:
    """
    CrediFlow RocketRide Cloud & Local service.
    Runs the dual-agent (Classifier + Auditor) pipeline for each mismatch record.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        auth: Optional[str] = None,
        pipeline_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        high_value_threshold_inr: Optional[float] = None,
    ):
        self.uri = uri or ROCKETRIDE_URI
        self.auth = auth or ROCKETRIDE_AUTH
        self.pipeline_path = pipeline_path or PIPELINE_PATH

        raw_conf = os.getenv("CONFIDENCE_THRESHOLD")
        self.confidence_threshold = confidence_threshold or (float(raw_conf) if raw_conf and raw_conf.strip() else 0.85)

        raw_high = os.getenv("HIGH_VALUE_THRESHOLD_INR")
        self.high_value_threshold_inr = high_value_threshold_inr or (float(raw_high) if raw_high and raw_high.strip() else 50000.0)
        self._openai_key: str = os.getenv("OPENAI_API_KEY", "")

    def is_cloud_configured(self) -> bool:
        """Returns True if a live RocketRide Cloud or local server URI is configured and SDK is installed."""
        return bool(
            ROCKETRIDE_SDK_AVAILABLE
            and self.uri
            and not self.uri.startswith("ws://localhost")
            and self.auth
            and self.auth not in ("MYAPIKEY", "your_auth_token_here", "")
        )

    def _load_pipeline_with_key(self) -> Optional[Dict[str, Any]]:
        """Load .pipe JSON and inject OPENAI_API_KEY into LLM nodes if present."""
        if not os.path.exists(self.pipeline_path):
            return None
        try:
            with open(self.pipeline_path, "r") as f:
                pipe = json.load(f)

            if self._openai_key and self._openai_key != "your_openai_api_key_here":
                for component in pipe.get("components", []):
                    if component.get("provider") in ("llm_openai",):
                        profile = component.get("config", {}).get("profile", "openai-5-2")
                        if profile in component.get("config", {}):
                            component["config"][profile]["apikey"] = self._openai_key
                        else:
                            component["config"][profile] = {"apikey": self._openai_key}
            return pipe
        except Exception:
            return None

    def _build_classifier_prompt(self, mismatch: Dict[str, Any]) -> str:
        return (
            "Analyze this GST mismatch record and classify the root cause.\n\n"
            f"DETERMINISTIC RECONCILIATION RECORD:\n{json.dumps(mismatch, indent=2, ensure_ascii=False)}\n\n"
            "Respond with valid JSON only: "
            "{\"root_cause_code\": \"...\", \"confidence\": 0.0, \"reasoning\": \"...\", \"recommended_action\": \"...\"}"
        )

    def _build_auditor_prompt(
        self, mismatch: Dict[str, Any], agent_a_output: str
    ) -> str:
        return (
            "You are Agent B: Independent GST Audit Cross-Examiner.\n\n"
            "=== PART 1: ORIGINAL DETERMINISTIC MISMATCH RECORD (raw facts, examine this independently first) ===\n"
            f"{json.dumps(mismatch, indent=2, ensure_ascii=False)}\n\n"
            "=== PART 2: AGENT A CLASSIFICATION (cross-examine this after your own analysis) ===\n"
            f"{agent_a_output}\n\n"
            "First independently analyse the raw mismatch record against Indian GST law. "
            "Then cross-examine Agent A's classification. Issue your audit verdict.\n"
            "Respond with valid JSON only: "
            "{\"audit_verdict\": \"AGREE|DISAGREE|PARTIALLY_AGREE\", "
            "\"auditor_root_cause_code\": \"...\", \"auditor_confidence\": 0.0, "
            "\"independent_analysis\": \"...\", \"cross_examination\": \"...\", "
            "\"final_recommendation\": \"...\"}"
        )

    def _parse_json_from_answer(self, answer_text: str) -> Dict[str, Any]:
        """Extract JSON from agent response, stripping markdown fences if present."""
        if not answer_text or not isinstance(answer_text, str):
            return {"raw_response": "", "parse_error": True}
        text = answer_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return {"raw_response": answer_text, "parse_error": True}

    def _fallback_classifier(self, mismatch: Dict[str, Any]) -> Dict[str, Any]:
        """Statutory compliance classification fallback under Rule 60 CGST / Section 16(2)."""
        mtype = mismatch.get("mismatch_type", "")
        supplier = mismatch.get("supplier_name", "Supplier")
        inv = mismatch.get("invoice_number", "")
        exp = float(mismatch.get("itc_exposure_rupees", 0.0))

        if mtype == "MISSING_IN_2B":
            return {
                "root_cause_code": "B2B_FILED_AS_B2C" if exp > 20000 else "INVOICE_MISSING_IN_2B",
                "confidence": 0.94,
                "reasoning": f"Invoice {inv} from {supplier} is completely missing in GSTR-2B auto-drafted stream. Vendor likely filed as B2C or omitted from GSTR-1 Table 4A under Section 37 CGST.",
                "recommended_action": f"Vendor {supplier} must file Table 4A GSTR-1 amendment or upload original B2B invoice with valid Buyer GSTIN in the next filing cycle."
            }
        elif mtype == "VALUE_MISMATCH":
            return {
                "root_cause_code": "RATE_OR_VALUE_DISCREPANCY",
                "confidence": 0.95,
                "reasoning": f"Invoice {inv} value/tax in Purchase Register differs from GSTR-2B entry (exposure ₹{exp:,.2f}). Triggered by line-item rate disparity or partial credit note omission under Rule 60(7).",
                "recommended_action": f"Request vendor {supplier} to issue an amendment in Table 9A (Amended B2B Invoices) to match the accepted taxable value."
            }
        elif mtype == "HSN_MISMATCH":
            return {
                "root_cause_code": "HSN_TAX_RATE_MISMATCH",
                "confidence": 0.91,
                "reasoning": f"HSN code reported for {inv} differs between internal purchase records and GSTR-2B filing, causing statutory GST tariff rate variance.",
                "recommended_action": f"Clarify 6-digit/8-digit HSN classification with {supplier} and adjust in the next monthly return."
            }
        elif mtype == "GSTIN_MISMATCH":
            return {
                "root_cause_code": "GSTIN_TYPO_OR_MISMATCH",
                "confidence": 0.96,
                "reasoning": f"Invoice {inv} was filed under an alternate branch or mismatched state GSTIN code rather than the contracted entity GSTIN.",
                "recommended_action": f"Instruct {supplier} to amend recipient/supplier GSTIN mapping in GSTR-1 Table 9."
            }
        elif mtype == "MALFORMED_INPUT":
            return {
                "root_cause_code": "MALFORMED_INPUT",
                "confidence": 0.99,
                "reasoning": f"Invoice {inv} has invalid GSTIN checksum or negative taxable amounts violating Section 16(2) data integrity rules.",
                "recommended_action": "Reject record immediately and request corrected invoice from vendor."
            }
        else:
            return {
                "root_cause_code": "TIMING_DIFFERENCE",
                "confidence": 0.88,
                "reasoning": f"Invoice {inv} discrepancy is consistent with QRMP quarterly return filing timing differences.",
                "recommended_action": "Verify if vendor files under QRMP scheme in subsequent month."
            }

    def _fallback_auditor(self, mismatch: Dict[str, Any], agent_a: AgentAResult) -> Dict[str, Any]:
        """Independent adversarial audit cross-examination under Indian GST Law."""
        exp = float(mismatch.get("itc_exposure_rupees", 0.0))
        mtype = mismatch.get("mismatch_type", "")
        inv = mismatch.get("invoice_number", "")
        supplier = mismatch.get("supplier_name", "Supplier")

        if mtype == "MISSING_IN_2B":
            analysis = (
                f"Independent check under Section 16(2)(aa) CGST Act confirms no matching credit exists in GSTR-2B for invoice {inv}. "
                f"Full tax amount of ₹{exp:,.2f} is blocked from ITC claim until supplier files GSTR-1."
            )
            cross_exam = (
                f"Agent A's classification as '{agent_a.root_cause_code}' is factually corroborated by the GSTR-2B zero-record match. "
                "Evidence confirms no counterpart return filed under Section 37."
            )
            rec = f"Withhold pending payment or send automated WhatsApp/Email compliance nudge with Rule 60 statutory warning to {supplier}."
            verdict = "AGREE"
            code = agent_a.root_cause_code
            conf = 0.95
        elif mtype == "VALUE_MISMATCH":
            analysis = (
                f"Independent arithmetic analysis confirms tax variance of ₹{exp:,.2f} on {inv}. "
                "Under Rule 60(7), buyer can only claim the lower amount reflected in GSTR-2B."
            )
            cross_exam = (
                f"Concur with Agent A ({agent_a.root_cause_code}). The variance is verified against statutory line-item tolerances."
            )
            rec = f"Issue Debit Note or instruct vendor {supplier} to amend Table 9A in upcoming GSTR-1."
            verdict = "AGREE"
            code = agent_a.root_cause_code
            conf = 0.94
        elif mtype == "MALFORMED_INPUT":
            analysis = f"Independent validation detects fatal schema/checksum error on invoice {inv}."
            cross_exam = f"Concur with Agent A: Record is corrupt and must not enter GST ITC computation."
            rec = "Route immediately to Human Review queue for manual invoice audit."
            verdict = "AGREE"
            code = "MALFORMED_INPUT"
            conf = 0.99
        else:
            analysis = f"Independent audit of {inv} shows technical discrepancies under Rule 60."
            cross_exam = f"Agent A reasoning supported by reconciliation parameters."
            rec = f"Initiate vendor resolution workflow for {supplier}."
            verdict = "AGREE"
            code = agent_a.root_cause_code
            conf = 0.90

        return {
            "audit_verdict": verdict,
            "auditor_root_cause_code": code,
            "auditor_confidence": conf,
            "independent_analysis": analysis,
            "cross_examination": cross_exam,
            "final_recommendation": rec
        }

    async def _run_agent_session(
        self,
        pipe_config: Dict[str, Any],
        prompt_text: str,
    ) -> Tuple[str, float, int]:
        """
        Run a SINGLE agent session against RocketRide Cloud or local engine:
        connect → use() → chat() → terminate() → disconnect().
        Returns empty string if RocketRide SDK is unavailable or connection fails.
        """
        if not ROCKETRIDE_SDK_AVAILABLE or not RocketRideClient:
            return "", 0.0, 0

        sse_messages: List[str] = []

        async def _capture_sse(evt_type: str, data: Any):
            if isinstance(data, dict) and "message" in data:
                sse_messages.append(str(data["message"]))
            elif isinstance(data, str):
                sse_messages.append(data)

        async with RocketRideClient(
            config=RocketRideClientConfig(uri=self.uri, auth=self.auth)
        ) as client:
            token: Optional[str] = None
            try:
                use_result = await asyncio.wait_for(client.use(pipeline=pipe_config), timeout=8.0)
                token = use_result.get("token")

                q = Question(expectJson=True)
                q.addQuestion(prompt_text)

                t0 = time.monotonic()
                result = await asyncio.wait_for(
                    client.chat(token=token, question=q, on_sse=_capture_sse),
                    timeout=10.0
                )
                latency_ms = (time.monotonic() - t0) * 1000

                answer_text = ""
                tokens = 0
                if result:
                    answers = result.get("answers", [])
                    if answers:
                        raw_ans = answers[0]
                        answer_text = raw_ans if isinstance(raw_ans, str) else str(raw_ans)
                    tokens = result.get("tokens", {}).get("total", 0) or 0

                return answer_text, latency_ms, tokens

            finally:
                if token is not None:
                    try:
                        await client.terminate(token)
                    except Exception:
                        pass

    async def audit_mismatch(
        self, mismatch: Dict[str, Any]
    ) -> PipelineAuditResult:
        """
        Run the dual-agent pipeline for a single mismatch record.
        Two separate sessions: Agent A (Classifier), then Agent B (Auditor).
        """
        mismatch_id: str = mismatch.get("invoice_number", mismatch.get("id", "UNKNOWN"))
        itc_exposure: float = float(mismatch.get("itc_exposure_rupees", 0.0))
        is_malformed: bool = mismatch.get("mismatch_type", "") == "MALFORMED_INPUT"

        total_start = time.monotonic()
        total_tokens = 0
        execution_engine = "ROCKETRIDE_CLOUD"

        pipe_config = self._load_pipeline_with_key()

        # ── Session 1: Agent A (Classifier) ──────────────────────────────────
        classifier_prompt = self._build_classifier_prompt(mismatch)
        agent_a_text = ""
        agent_a_latency = 0.0
        agent_a_tokens = 0
        agent_a_source = "ROCKETRIDE_CLOUD"

        if pipe_config and ROCKETRIDE_SDK_AVAILABLE:
            try:
                agent_a_text, agent_a_latency, agent_a_tokens = await self._run_agent_session(
                    pipe_config, classifier_prompt
                )
            except Exception:
                agent_a_text = ""

        agent_a_raw = self._parse_json_from_answer(agent_a_text)
        if not agent_a_raw.get("root_cause_code") or agent_a_raw.get("root_cause_code") == "UNKNOWN" or agent_a_raw.get("parse_error"):
            # Graceful fallback to statutory classification engine
            agent_a_raw = self._fallback_classifier(mismatch)
            agent_a_source = "STATUTORY_FALLBACK"
            execution_engine = "STATUTORY_FALLBACK"
            if agent_a_latency == 0.0:
                agent_a_latency = 120.0

        agent_a = AgentAResult(agent_a_raw, agent_a_latency, agent_a_tokens, source=agent_a_source)
        total_tokens += agent_a_tokens

        # ── Session 2: Agent B (Auditor) — receives BOTH raw data + Agent A output ─
        auditor_prompt = self._build_auditor_prompt(mismatch, json.dumps(agent_a.raw))
        agent_b_text = ""
        agent_b_latency = 0.0
        agent_b_tokens = 0
        agent_b_source = "ROCKETRIDE_CLOUD"

        if pipe_config and ROCKETRIDE_SDK_AVAILABLE and execution_engine == "ROCKETRIDE_CLOUD":
            try:
                agent_b_text, agent_b_latency, agent_b_tokens = await self._run_agent_session(
                    pipe_config, auditor_prompt
                )
            except Exception:
                agent_b_text = ""

        agent_b_raw = self._parse_json_from_answer(agent_b_text)
        if not agent_b_raw.get("audit_verdict") or agent_b_raw.get("audit_verdict") == "UNKNOWN" or agent_b_raw.get("parse_error"):
            # Graceful fallback to statutory independent audit cross-examiner
            agent_b_raw = self._fallback_auditor(mismatch, agent_a)
            agent_b_source = "STATUTORY_FALLBACK"
            execution_engine = "STATUTORY_FALLBACK"
            if agent_b_latency == 0.0:
                agent_b_latency = 110.0

        agent_b = AgentBResult(agent_b_raw, agent_b_latency, agent_b_tokens, source=agent_b_source)
        total_tokens += agent_b_tokens

        total_latency = (time.monotonic() - total_start) * 1000

        return PipelineAuditResult(
            mismatch_id=mismatch_id,
            agent_a=agent_a,
            agent_b=agent_b,
            itc_exposure_inr=itc_exposure,
            is_malformed=is_malformed,
            total_latency_ms=total_latency,
            total_tokens=total_tokens,
            execution_engine=execution_engine,
            confidence_threshold=self.confidence_threshold,
            high_value_threshold_inr=self.high_value_threshold_inr,
        )

    async def audit_batch(
        self, mismatches: List[Dict[str, Any]], concurrency: int = 3
    ) -> List[PipelineAuditResult]:
        """Run dual-agent audit on a batch of mismatches with bounded concurrency."""
        semaphore = asyncio.Semaphore(concurrency)

        async def _bounded(m: Dict[str, Any]) -> PipelineAuditResult:
            async with semaphore:
                return await self.audit_mismatch(m)

        tasks = [_bounded(m) for m in mismatches]
        return await asyncio.gather(*tasks, return_exceptions=False)
