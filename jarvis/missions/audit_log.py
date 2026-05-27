from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_request import MissionApprovalLevel, MissionApprovalRequest
from jarvis.missions.envelope import ActionClassification


class MissionAuditEventType(str, Enum):
    MISSION_CREATED = "mission_created"
    MISSION_VALIDATED = "mission_validated"
    ACTION_CLASSIFIED = "action_classified"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_GRANTED = "approval_granted"
    STOP_CONDITION_TRIGGERED = "stop_condition_triggered"
    VALIDATION_FAILED = "validation_failed"
    TOOL_ADOPTION_PROPOSED = "tool_adoption_proposed"
    REVENUE_METRIC_RECORDED = "revenue_metric_recorded"
    NOTE_RECORDED = "note_recorded"


class MissionAuditOutcome(str, Enum):
    RECORDED = "recorded"
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    STRONG_APPROVAL = "strong_approval"
    DENIED = "denied"
    FAILED_VALIDATION = "failed_validation"
    STOPPED = "stopped"
    UNKNOWN_REQUIRES_REVIEW = "unknown_requires_review"


class MissionAuditRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MissionAuditValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionAuditEvent:
    event_id: str
    mission_id: str
    event_type: MissionAuditEventType
    actor: str
    summary: str
    created_at: str
    outcome: MissionAuditOutcome
    risk_level: MissionAuditRiskLevel
    metadata: Dict[str, Any] = field(default_factory=dict)
    action: Optional[str] = None
    approval_request_id: Optional[str] = None
    policy_decision: Optional[str] = None
    reason: Optional[str] = None
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    redacted_fields: List[str] = field(default_factory=list)
    sensitive: bool = False

    def __post_init__(self) -> None:
        self.event_type = _coerce_enum(MissionAuditEventType, self.event_type, "event_type")
        self.outcome = _coerce_enum(MissionAuditOutcome, self.outcome, "outcome")
        self.risk_level = _coerce_enum(MissionAuditRiskLevel, self.risk_level, "risk_level")
        self.redacted_fields = _list_from(self.redacted_fields)

        result = validate_audit_event(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionAuditEvent":
        return cls(
            event_id=str(data.get("event_id", "")),
            mission_id=str(data.get("mission_id", "")),
            event_type=data.get("event_type", ""),
            actor=str(data.get("actor", "")),
            summary=str(data.get("summary", "")),
            created_at=str(data.get("created_at", "")),
            outcome=data.get("outcome", ""),
            risk_level=data.get("risk_level", ""),
            metadata=data.get("metadata", {}),
            action=data.get("action"),
            approval_request_id=data.get("approval_request_id"),
            policy_decision=data.get("policy_decision"),
            reason=data.get("reason"),
            correlation_id=data.get("correlation_id"),
            source=data.get("source"),
            redacted_fields=_list_from(data.get("redacted_fields")),
            sensitive=bool(data.get("sensitive", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "mission_id": self.mission_id,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "summary": self.summary,
            "created_at": self.created_at,
            "outcome": self.outcome.value,
            "risk_level": self.risk_level.value,
            "metadata": dict(self.metadata),
            "action": self.action,
            "approval_request_id": self.approval_request_id,
            "policy_decision": self.policy_decision,
            "reason": self.reason,
            "correlation_id": self.correlation_id,
            "source": self.source,
            "redacted_fields": list(self.redacted_fields),
            "sensitive": self.sensitive,
        }


def validate_audit_event(event: MissionAuditEvent) -> MissionAuditValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(event.event_id):
        errors.append("event_id must be a non-empty string")
    if not _is_non_empty_string(event.mission_id):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(event.actor):
        errors.append("actor must be a non-empty string")
    if not _is_non_empty_string(event.summary):
        errors.append("summary must be a non-empty string")
    if not isinstance(event.metadata, dict):
        errors.append("metadata must be a dict")
    elif event.sensitive:
        forbidden_keys = _forbidden_sensitive_metadata_keys(event.metadata)
        if forbidden_keys:
            errors.append("sensitive metadata cannot include secret-like keys: " + ", ".join(forbidden_keys))

    if _contains_blanket_approval(event.summary):
        errors.append("summary cannot contain vague blanket approval")

    if event.event_type == MissionAuditEventType.APPROVAL_GRANTED and not (
        _is_non_empty_string(event.approval_request_id) or _is_non_empty_string(event.reason)
    ):
        errors.append("approval_granted requires approval_request_id or reason")
    if event.event_type == MissionAuditEventType.APPROVAL_DENIED and not _is_non_empty_string(event.reason):
        errors.append("approval_denied requires reason")
    if event.event_type == MissionAuditEventType.STOP_CONDITION_TRIGGERED and not _is_non_empty_string(event.reason):
        errors.append("stop_condition_triggered requires reason")
    if event.event_type == MissionAuditEventType.VALIDATION_FAILED and not _is_non_empty_string(event.reason):
        errors.append("validation_failed requires reason")

    return MissionAuditValidationResult(errors=errors)


def build_audit_event(
    mission_id: str,
    event_type: MissionAuditEventType,
    actor: str,
    summary: str,
    *,
    event_id: Optional[str] = None,
    created_at: Optional[str] = None,
    outcome: MissionAuditOutcome = MissionAuditOutcome.RECORDED,
    risk_level: MissionAuditRiskLevel = MissionAuditRiskLevel.UNKNOWN,
    metadata: Optional[Dict[str, Any]] = None,
    action: Optional[str] = None,
    approval_request_id: Optional[str] = None,
    policy_decision: Optional[str] = None,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
    source: Optional[str] = None,
    redacted_fields: Optional[List[str]] = None,
    sensitive: bool = False,
) -> MissionAuditEvent:
    return MissionAuditEvent(
        event_id=event_id or str(uuid4()),
        mission_id=mission_id,
        event_type=event_type,
        actor=actor,
        summary=summary,
        created_at=created_at or _now_iso(),
        outcome=outcome,
        risk_level=risk_level,
        metadata=dict(metadata or {}),
        action=action,
        approval_request_id=approval_request_id,
        policy_decision=policy_decision,
        reason=reason,
        correlation_id=correlation_id,
        source=source,
        redacted_fields=_list_from(redacted_fields),
        sensitive=sensitive,
    )


def build_audit_event_from_approval_request(
    request: MissionApprovalRequest,
    actor: str,
    *,
    event_id: Optional[str] = None,
    summary: Optional[str] = None,
    created_at: Optional[str] = None,
    correlation_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MissionAuditEvent:
    event_metadata = {
        "approval_level": request.approval_level.value,
        "classification": request.classification.value,
    }
    event_metadata.update(dict(metadata or {}))

    return build_audit_event(
        mission_id=request.mission_id,
        event_type=MissionAuditEventType.APPROVAL_REQUESTED,
        actor=actor,
        summary=summary or f"Approval requested for mission action: {request.action}",
        event_id=event_id,
        created_at=created_at or request.created_at,
        outcome=_outcome_for_classification(request.classification),
        risk_level=_risk_level_for_approval_level(request.approval_level),
        metadata=event_metadata,
        action=request.action,
        approval_request_id=request.request_id,
        reason=request.reason,
        correlation_id=correlation_id,
        source=source,
    )


_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
}

_DANGEROUS_METADATA_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "private_key",
    "authorization",
    "cookie",
    ".env",
}


def _outcome_for_classification(classification: ActionClassification) -> MissionAuditOutcome:
    if classification == ActionClassification.ALLOWED:
        return MissionAuditOutcome.ALLOWED
    if classification == ActionClassification.REQUIRES_APPROVAL:
        return MissionAuditOutcome.REQUIRES_APPROVAL
    if classification == ActionClassification.STRONG_APPROVAL:
        return MissionAuditOutcome.STRONG_APPROVAL
    if classification == ActionClassification.DENIED:
        return MissionAuditOutcome.DENIED
    return MissionAuditOutcome.UNKNOWN_REQUIRES_REVIEW


def _risk_level_for_approval_level(approval_level: MissionApprovalLevel) -> MissionAuditRiskLevel:
    if approval_level == MissionApprovalLevel.ALLOWED:
        return MissionAuditRiskLevel.LOW
    if approval_level in {MissionApprovalLevel.REQUIRES_REVIEW, MissionApprovalLevel.REQUIRES_APPROVAL}:
        return MissionAuditRiskLevel.MEDIUM
    if approval_level in {MissionApprovalLevel.STRONG_APPROVAL, MissionApprovalLevel.DENIED}:
        return MissionAuditRiskLevel.HIGH
    return MissionAuditRiskLevel.UNKNOWN


def _forbidden_sensitive_metadata_keys(metadata: Dict[str, Any]) -> List[str]:
    forbidden = []
    for key in metadata:
        normalized = _normalize(str(key))
        if normalized in _DANGEROUS_METADATA_KEYS:
            forbidden.append(str(key))
    return sorted(forbidden)


def _contains_blanket_approval(value: str) -> bool:
    normalized = _normalize(value)
    return any(phrase in normalized for phrase in _BLANKET_APPROVAL_PHRASES)


def _coerce_enum(enum_type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}") from exc


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _is_non_empty_string(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
