from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_3_mission_loop_models import UNKNOWN


PROPOSAL_STATUSES = {"proposed", "approved", "rejected", "superseded"}
CONFIDENCE_LEVELS = {"low", "medium", "high", "unknown"}
RISK_LEVELS = {"low", "medium", "high", "critical", "unknown"}


@dataclass(frozen=True)
class LearningProposalAuditEvent:
    event_id: str
    event_type: str
    proposal_id: str
    actor: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningProposal:
    proposal_id: str
    proposal: str
    evidence: str
    confidence: str
    risk: str
    requires_approval: bool
    status: str
    source_outcome_ids: List[str]
    source_failure_ids: List[str]
    created_at: str
    updated_at: str
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    superseded_by: Optional[str] = None
    approval_level: str = UNKNOWN
    reviewer: str = UNKNOWN
    reason: str = UNKNOWN
    sensitive_learning: bool = False
    redacted_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["usable_as_operational_rule"] = (
            self.status == "approved" and not self.sensitive_learning
        )
        data["operational_rule"] = self.proposal if data["usable_as_operational_rule"] else None
        data["grants_permission"] = False
        data["applies_automatically"] = False
        return data


class LearningProposalEngine:
    """Reviewable Mark 3 learning proposals. Approval changes state, not permissions."""

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._proposals: Dict[str, LearningProposal] = {}
        self._audit: List[LearningProposalAuditEvent] = []

    def status(self) -> Dict[str, Any]:
        counts = {status: 0 for status in PROPOSAL_STATUSES}
        for item in self._proposals.values():
            counts[item.status] = counts.get(item.status, 0) + 1
        return {
            "available": True,
            "in_memory_only": True,
            "proposal_count": len(self._proposals),
            "status_counts": counts,
            "audit_event_count": len(self._audit),
            "approved_learning_grants_permission": False,
            "sensitive_learning_auto_applies": False,
        }

    def create(self, values: Dict[str, Any]) -> Dict[str, Any]:
        safe, redacted = redact_sensitive_data(dict(values or {}))
        now = self.clock()
        sensitive_learning = bool(redacted) or _contains_redacted_marker(safe)
        proposal = LearningProposal(
            proposal_id=_safe_text(safe.get("proposal_id"), self.id_factory()),
            proposal=_safe_text(safe.get("proposal", safe.get("title")), UNKNOWN),
            evidence=_safe_text(safe.get("evidence"), UNKNOWN),
            confidence=_choice(safe.get("confidence"), CONFIDENCE_LEVELS, "unknown"),
            risk=_choice(safe.get("risk"), RISK_LEVELS, "unknown"),
            requires_approval=bool(safe.get("requires_approval", True)),
            status="proposed",
            source_outcome_ids=_items(safe.get("source_outcome_ids", safe.get("source_outcome_id"))),
            source_failure_ids=_items(safe.get("source_failure_ids", safe.get("source_failure_id"))),
            created_at=_safe_text(safe.get("created_at"), now),
            updated_at=now,
            sensitive_learning=sensitive_learning,
            redacted_fields=redacted,
        )
        self._proposals[proposal.proposal_id] = proposal
        self._append_audit(
            "proposal_created",
            proposal.proposal_id,
            "Learning proposal created for review.",
            {"risk": proposal.risk, "confidence": proposal.confidence},
            redacted,
        )
        return proposal.to_dict()

    def create_from_outcome(self, outcome: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        values = dict(overrides or {})
        next_action = _safe_text(outcome.get("next_recommended_action"), UNKNOWN)
        what_worked = _safe_text(outcome.get("what_worked"), UNKNOWN)
        what_failed = _safe_text(outcome.get("what_failed"), UNKNOWN)
        result = _safe_text(outcome.get("result_status"), UNKNOWN)
        evidence_state = _safe_text(outcome.get("evidence_state"), UNKNOWN)
        if "proposal" not in values:
            values["proposal"] = _proposal_text(next_action, what_worked, what_failed)
        if "evidence" not in values:
            values["evidence"] = (
                f"Outcome {outcome.get('outcome_id', UNKNOWN)} for mission "
                f"{outcome.get('mission_id', UNKNOWN)} ended as {result} with evidence_state={evidence_state}."
            )
        values.setdefault("source_outcome_ids", [outcome.get("outcome_id", UNKNOWN)])
        values.setdefault("confidence", _confidence_from_evidence(evidence_state))
        values.setdefault("risk", "low")
        values.setdefault("requires_approval", True)
        return self.create(values)

    def approve(
        self,
        proposal_id: str,
        *,
        actor: str = "operator",
        approval_level: str = "simple",
        reason: str = "",
    ) -> Dict[str, Any]:
        proposal = self._get(proposal_id)
        if proposal.status != "proposed":
            raise ValueError(f"proposal is {proposal.status}, not proposed")
        proposal.status = "approved"
        proposal.approved_at = self.clock()
        proposal.updated_at = proposal.approved_at
        proposal.approval_level = _safe_text(approval_level, UNKNOWN)
        proposal.reviewer = _safe_text(actor, "operator")
        proposal.reason = _safe_text(reason, UNKNOWN)
        self._append_audit(
            "proposal_approved",
            proposal_id,
            "Learning proposal approved; it still grants no execution permission.",
            {"approval_level": proposal.approval_level, "usable_as_operational_rule": not proposal.sensitive_learning},
            actor=proposal.reviewer,
        )
        return proposal.to_dict()

    def reject(
        self,
        proposal_id: str,
        *,
        actor: str = "operator",
        reason: str = "",
    ) -> Dict[str, Any]:
        proposal = self._get(proposal_id)
        if proposal.status != "proposed":
            raise ValueError(f"proposal is {proposal.status}, not proposed")
        proposal.status = "rejected"
        proposal.rejected_at = self.clock()
        proposal.updated_at = proposal.rejected_at
        proposal.reviewer = _safe_text(actor, "operator")
        proposal.reason = _safe_text(reason, UNKNOWN)
        self._append_audit(
            "proposal_rejected",
            proposal_id,
            "Learning proposal rejected by reviewer.",
            {"reason": proposal.reason},
            actor=proposal.reviewer,
        )
        return proposal.to_dict()

    def supersede(self, proposal_id: str, *, superseded_by: str) -> Dict[str, Any]:
        proposal = self._get(proposal_id)
        proposal.status = "superseded"
        proposal.superseded_by = _safe_text(superseded_by, UNKNOWN)
        proposal.updated_at = self.clock()
        self._append_audit(
            "proposal_superseded",
            proposal_id,
            "Learning proposal superseded by a newer proposal.",
            {"superseded_by": proposal.superseded_by},
        )
        return proposal.to_dict()

    def list(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in self._proposals.values()]

    def get(self, proposal_id: str) -> Dict[str, Any]:
        return self._get(proposal_id).to_dict()

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [item.to_dict() for item in self._audit],
        }

    def _get(self, proposal_id: str) -> LearningProposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise KeyError(proposal_id) from exc

    def _append_audit(
        self,
        event_type: str,
        proposal_id: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
        redacted_fields: Optional[List[str]] = None,
        actor: str = "jarvis",
    ) -> None:
        safe_metadata, audit_redacted = redact_sensitive_data(metadata or {})
        self._audit.append(LearningProposalAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            proposal_id=proposal_id,
            actor=_safe_text(actor, "jarvis"),
            created_at=self.clock(),
            summary=summary,
            metadata=safe_metadata,
            redacted_fields=list(dict.fromkeys((redacted_fields or []) + audit_redacted)),
        ))


def _proposal_text(next_action: str, what_worked: str, what_failed: str) -> str:
    if next_action != UNKNOWN:
        return f"Remember: {next_action}"
    if what_failed != UNKNOWN:
        return f"Remember failure pattern: {what_failed}"
    if what_worked != UNKNOWN:
        return f"Remember successful pattern: {what_worked}"
    return "Remember: preserve unknowns and require evidence before turning outcomes into rules."


def _confidence_from_evidence(evidence_state: str) -> str:
    lowered = evidence_state.lower()
    if lowered == "verified":
        return "high"
    if lowered in {"observed", "reported"}:
        return "medium"
    return "low"


def _choice(value: Any, allowed: set[str], fallback: str) -> str:
    text = _safe_text(value, fallback).lower()
    return text if text in allowed else fallback


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_safe_text(item, "") for item in value if _safe_text(item, "")]
    text = _safe_text(value, "")
    return [text] if text else []


def _contains_redacted_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_redacted_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_redacted_marker(item) for item in value)
    return str(value) == "[redacted sensitive text]"


def _safe_text(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    return text or fallback


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
