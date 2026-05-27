from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.envelope import ActionClassification, MissionEnvelope, classify_action


class MissionApprovalLevel(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    STRONG_APPROVAL = "strong_approval"
    DENIED = "denied"


@dataclass
class MissionApprovalRequest:
    request_id: str
    mission_id: str
    action: str
    classification: ActionClassification
    reason: str
    scope: List[str]
    requested_by: str
    approval_level: MissionApprovalLevel
    duration: Optional[str]
    cost_limit: Optional[float]
    rollback_plan: Optional[str]
    audit_requirements: List[str]
    tool_name: Optional[str] = None
    channel: Optional[str] = None
    risk_notes: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.classification = _coerce_enum(ActionClassification, self.classification, "classification")
        self.approval_level = _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level")
        self.scope = _list_from(self.scope)
        self.audit_requirements = _list_from(self.audit_requirements)
        self.risk_notes = _list_from(self.risk_notes)
        self.metadata = dict(self.metadata or {})
        self._validate()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionApprovalRequest":
        return cls(
            request_id=str(data.get("request_id", "")),
            mission_id=str(data.get("mission_id", "")),
            action=str(data.get("action", "")),
            classification=data.get("classification", ""),
            reason=str(data.get("reason", "")),
            scope=_list_from(data.get("scope")),
            requested_by=str(data.get("requested_by", "")),
            approval_level=data.get("approval_level", ""),
            duration=data.get("duration"),
            cost_limit=data.get("cost_limit"),
            rollback_plan=data.get("rollback_plan"),
            audit_requirements=_list_from(data.get("audit_requirements")),
            tool_name=data.get("tool_name"),
            channel=data.get("channel"),
            risk_notes=_list_from(data.get("risk_notes")),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "mission_id": self.mission_id,
            "action": self.action,
            "classification": self.classification.value,
            "reason": self.reason,
            "scope": list(self.scope),
            "requested_by": self.requested_by,
            "approval_level": self.approval_level.value,
            "duration": self.duration,
            "cost_limit": self.cost_limit,
            "rollback_plan": self.rollback_plan,
            "audit_requirements": list(self.audit_requirements),
            "tool_name": self.tool_name,
            "channel": self.channel,
            "risk_notes": list(self.risk_notes),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "metadata": dict(self.metadata),
        }

    def _validate(self) -> None:
        errors: List[str] = []

        if not _is_non_empty_string(self.request_id):
            errors.append("request_id must be a non-empty string")
        if not _is_non_empty_string(self.mission_id):
            errors.append("mission_id must be a non-empty string")
        if not _is_non_empty_string(self.action):
            errors.append("action must be a non-empty string")
        if not _is_non_empty_string(self.requested_by):
            errors.append("requested_by must be a non-empty string")
        if self.cost_limit is not None and self.cost_limit < 0:
            errors.append("cost_limit cannot be negative")
        if self.duration is not None and _normalize(self.duration) in _FORBIDDEN_DURATIONS:
            errors.append("duration cannot grant unlimited approval")

        if self.approval_level in {
            MissionApprovalLevel.REQUIRES_APPROVAL,
            MissionApprovalLevel.STRONG_APPROVAL,
        } and not self.scope:
            errors.append("scope cannot be empty for approval requests")

        if self.approval_level == MissionApprovalLevel.STRONG_APPROVAL and not (
            _is_non_empty_string(self.rollback_plan) or _is_non_empty_string(self.reason)
        ):
            errors.append("strong_approval requires rollback_plan or clear reason")

        if self.classification == ActionClassification.DENIED and self.approval_level == MissionApprovalLevel.ALLOWED:
            errors.append("denied request cannot have approval_level allowed")

        if self.approval_level in _SENSITIVE_APPROVAL_LEVELS and not self.audit_requirements:
            errors.append("audit_requirements cannot be empty for sensitive approval requests")

        if errors:
            raise ValueError("; ".join(errors))


def build_approval_request(
    envelope: MissionEnvelope,
    action: str,
    requested_by: str,
    *,
    request_id: Optional[str] = None,
    reason: Optional[str] = None,
    scope: Optional[List[str]] = None,
    duration: Optional[str] = None,
    cost_limit: Optional[float] = None,
    rollback_plan: Optional[str] = None,
    audit_requirements: Optional[List[str]] = None,
    tool_name: Optional[str] = None,
    channel: Optional[str] = None,
    risk_notes: Optional[List[str]] = None,
    created_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MissionApprovalRequest:
    classification = _classify_request_action(envelope, action, tool_name=tool_name)
    approval_level = _approval_level_for(classification)

    return MissionApprovalRequest(
        request_id=request_id or str(uuid4()),
        mission_id=envelope.mission_id,
        action=(action or "").strip(),
        classification=classification,
        reason=reason or _default_reason(classification),
        scope=_default_scope(envelope, action, scope),
        requested_by=requested_by,
        approval_level=approval_level,
        duration=duration,
        cost_limit=envelope.cost_limit_per_action if cost_limit is None else cost_limit,
        rollback_plan=rollback_plan if rollback_plan is not None else envelope.rollback_plan,
        audit_requirements=_list_from(audit_requirements)
        if audit_requirements is not None
        else list(envelope.audit_requirements),
        tool_name=tool_name,
        channel=channel,
        risk_notes=_list_from(risk_notes),
        created_at=created_at or _now_iso(),
        expires_at=expires_at,
        metadata=dict(metadata or {}),
    )


def _classify_request_action(
    envelope: MissionEnvelope,
    action: str,
    *,
    tool_name: Optional[str] = None,
) -> ActionClassification:
    classification = classify_action(envelope, action)
    if classification == ActionClassification.DENIED:
        return classification

    if _is_candidate_tool_only(envelope, tool_name):
        if classification == ActionClassification.ALLOWED:
            return ActionClassification.UNKNOWN_REQUIRES_REVIEW
        return classification

    return classification


def _approval_level_for(classification: ActionClassification) -> MissionApprovalLevel:
    if classification == ActionClassification.ALLOWED:
        return MissionApprovalLevel.ALLOWED
    if classification == ActionClassification.REQUIRES_APPROVAL:
        return MissionApprovalLevel.REQUIRES_APPROVAL
    if classification == ActionClassification.STRONG_APPROVAL:
        return MissionApprovalLevel.STRONG_APPROVAL
    if classification == ActionClassification.DENIED:
        return MissionApprovalLevel.DENIED
    return MissionApprovalLevel.REQUIRES_REVIEW


def _default_reason(classification: ActionClassification) -> str:
    if classification == ActionClassification.ALLOWED:
        return "Action is allowed within the Mission Envelope."
    if classification == ActionClassification.REQUIRES_APPROVAL:
        return "Action requires explicit mission approval before execution."
    if classification == ActionClassification.STRONG_APPROVAL:
        return "Action requires strong mission approval before execution."
    if classification == ActionClassification.DENIED:
        return "Action is denied by the Mission Envelope and must not execute."
    return "Action is not declared as allowed in the Mission Envelope and requires review."


def _default_scope(envelope: MissionEnvelope, action: str, scope: Optional[List[str]]) -> List[str]:
    if scope is not None:
        return _list_from(scope)
    normalized_action = (action or "").strip()
    return [normalized_action] if normalized_action else []


def _is_candidate_tool_only(envelope: MissionEnvelope, tool_name: Optional[str]) -> bool:
    normalized = _normalize(tool_name)
    if not normalized:
        return False
    allowed_tools = {_normalize(tool) for tool in envelope.allowed_tools}
    candidate_tools = {_normalize(tool) for tool in envelope.candidate_tools}
    return normalized in candidate_tools and normalized not in allowed_tools


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_enum(enum_type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}") from exc


def _is_non_empty_string(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_FORBIDDEN_DURATIONS = {
    "approve_all_forever",
    "forever",
    "unlimited",
    "no_limits",
    "no limits",
    "no-limits",
}

_SENSITIVE_APPROVAL_LEVELS = {
    MissionApprovalLevel.REQUIRES_APPROVAL,
    MissionApprovalLevel.STRONG_APPROVAL,
    MissionApprovalLevel.DENIED,
}
