"""
Human-in-the-Loop Gate — CrediFlow
Evaluates compliance risk trigger conditions and manages the approval queue + immutable audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class HumanGateTrigger(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    HIGH_ITC_EXPOSURE = "HIGH_ITC_EXPOSURE"
    MALFORMED_INPUT = "MALFORMED_INPUT"
    AGENT_DISAGREEMENT = "AGENT_DISAGREEMENT"  # Kept for backward compatibility if cited


class HumanDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class HumanGateEntry:
    """
    A single record in the human approval queue.
    Immutable once created; decision + audit_log are appended only.
    """

    def __init__(
        self,
        mismatch_id: str,
        mismatch_record: Dict[str, Any],
        pipeline_result: Dict[str, Any],
        triggers: List[HumanGateTrigger],
        trigger_reasons: List[str],
    ):
        self.gate_id: str = str(uuid.uuid4())
        self.mismatch_id = mismatch_id
        self.mismatch_record = mismatch_record
        self.pipeline_result = pipeline_result
        self.triggers = triggers
        self.trigger_reasons = trigger_reasons
        self.decision: HumanDecision = HumanDecision.PENDING
        self.edited_message: Optional[str] = None
        self.decision_by: Optional[str] = None
        self.decision_note: Optional[str] = None
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.decided_at: Optional[str] = None

        # Immutable audit log — every state change appended here
        self.audit_log: List[Dict[str, Any]] = [
            {
                "event": "QUEUED_FOR_HUMAN_REVIEW",
                "timestamp": self.created_at,
                "triggers": [t.value for t in triggers],
                "reasons": trigger_reasons,
            }
        ]

    def apply_decision(
        self,
        decision: HumanDecision,
        decided_by: str = "finance_manager",
        edited_message: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        """Record the Finance Manager's decision. Appends to audit_log (never overwrites)."""
        if self.decision != HumanDecision.PENDING:
            raise ValueError(f"Gate {self.gate_id} already has decision: {self.decision}")

        now = datetime.now(timezone.utc).isoformat()
        self.decision = decision
        self.decision_by = decided_by
        self.decision_note = note
        self.decided_at = now

        if decision == HumanDecision.EDITED and edited_message:
            self.edited_message = edited_message

        self.audit_log.append(
            {
                "event": f"DECISION_{decision.value}",
                "timestamp": now,
                "decided_by": decided_by,
                "note": note,
                "edited_message": edited_message,
            }
        )

    def mark_resolved(self, resolution_note: str = "") -> None:
        """Mark the entry as fully resolved after vendor action."""
        now = datetime.now(timezone.utc).isoformat()
        self.decision = HumanDecision.RESOLVED
        self.audit_log.append(
            {
                "event": "RESOLVED",
                "timestamp": now,
                "note": resolution_note,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        root_cause = (
            self.pipeline_result.get("root_cause_code")
            or self.mismatch_record.get("mismatch_type", "")
        )
        exp = float(
            self.mismatch_record.get("itc_exposure_rupees")
            or self.mismatch_record.get("itc_exposure_inr")
            or self.mismatch_record.get("itc_exposure")
            or 0.0
        )
        inv_no = str(self.mismatch_record.get("invoice_number") or self.mismatch_id)
        supp_name = str(self.mismatch_record.get("supplier_name") or "Vendor")
        supp_gstin = str(self.mismatch_record.get("supplier_gstin") or "")
        mismatch_type = str(self.mismatch_record.get("mismatch_type") or "")
        details = str(self.mismatch_record.get("details") or "")
        severity = str(self.mismatch_record.get("severity") or "MEDIUM")

        return {
            "gate_id": self.gate_id,
            "mismatch_id": self.mismatch_id,
            "invoice_number": inv_no,
            "decision": self.decision.value,
            "triggers": [t.value for t in self.triggers],
            "trigger_reasons": self.trigger_reasons,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
            "decision_by": self.decision_by,
            "decision_note": self.decision_note,
            "edited_message": self.edited_message,
            "itc_exposure_inr": exp,
            "itc_exposure_rupees": exp,
            "itc_exposure": exp,
            "supplier_name": supp_name,
            "supplier_gstin": supp_gstin,
            "mismatch_type": mismatch_type,
            "root_cause_code": root_cause,
            "root_cause_classification": root_cause,
            "details": details,
            "severity": severity,
            "audit_log": self.audit_log,
        }


class HumanGate:
    """
    In-memory approval queue and audit trail for compliance decisions.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.85,
        high_value_threshold_inr: float = 50_000.0,
    ):
        self.confidence_threshold = confidence_threshold
        self.high_value_threshold_inr = high_value_threshold_inr
        self._queue: Dict[str, HumanGateEntry] = {}

    def evaluate(
        self,
        mismatch_record: Dict[str, Any],
        pipeline_result: Optional[Dict[str, Any]] = None,
    ) -> Optional[HumanGateEntry]:
        """
        Evaluate human risk gate triggers:
          1. High ITC exposure — INR exposure >= high_value_threshold_inr
          2. Low confidence — classification confidence < threshold
          3. Malformed input — mismatch_type == MALFORMED_INPUT
        """
        pipeline_result = pipeline_result or {}
        triggers: List[HumanGateTrigger] = []
        reasons: List[str] = []

        # ── Trigger 1: High ITC exposure ──────────────────────────────────────
        exposure = float(mismatch_record.get("itc_exposure_rupees", 0.0))
        if exposure >= self.high_value_threshold_inr:
            triggers.append(HumanGateTrigger.HIGH_ITC_EXPOSURE)
            reasons.append(
                f"High ITC exposure: ₹{exposure:,.0f} ≥ threshold ₹{self.high_value_threshold_inr:,.0f}"
            )

        # ── Trigger 2: Low confidence ─────────────────────────────────────────
        conf = float(pipeline_result.get("confidence", 1.0))
        if conf < self.confidence_threshold:
            triggers.append(HumanGateTrigger.LOW_CONFIDENCE)
            reasons.append(
                f"Low confidence: {conf:.2f} (threshold={self.confidence_threshold})"
            )

        # ── Trigger 3: Malformed / unrecognized input ─────────────────────────
        if mismatch_record.get("mismatch_type") == "MALFORMED_INPUT":
            triggers.append(HumanGateTrigger.MALFORMED_INPUT)
            reasons.append(
                f"Malformed/unrecognized input: {mismatch_record.get('details', 'No details')}"
            )

        if not triggers:
            return None

        entry = HumanGateEntry(
            mismatch_id=mismatch_record.get("invoice_number", "UNKNOWN"),
            mismatch_record=mismatch_record,
            pipeline_result=pipeline_result,
            triggers=triggers,
            trigger_reasons=reasons,
        )
        self._queue[entry.gate_id] = entry
        return entry

    def get_pending(self) -> List[HumanGateEntry]:
        return [e for e in self._queue.values() if e.decision == HumanDecision.PENDING]

    def get_entry(self, gate_id: str) -> Optional[HumanGateEntry]:
        return self._queue.get(gate_id)

    def apply_decision(
        self,
        gate_id: str,
        decision: HumanDecision,
        decided_by: str = "finance_manager",
        edited_message: Optional[str] = None,
        note: Optional[str] = None,
    ) -> HumanGateEntry:
        entry = self._queue.get(gate_id)
        if not entry:
            raise KeyError(f"No gate entry found for gate_id={gate_id}")
        entry.apply_decision(decision, decided_by, edited_message, note)
        return entry

    def decide(
        self,
        gate_id: str,
        decision: HumanDecision,
        decided_by: str = "finance_manager",
        edited_message: Optional[str] = None,
        note: Optional[str] = None,
    ) -> HumanGateEntry:
        return self.apply_decision(gate_id, decision, decided_by, edited_message, note)

    def list_all(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._queue.values()]

    @property
    def pending_count(self) -> int:
        return sum(1 for e in self._queue.values() if e.decision == HumanDecision.PENDING)

    @property
    def total_count(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        """Clears all entries in the approval queue."""
        self._queue.clear()
