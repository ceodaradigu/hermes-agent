from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.envelope import ActionClassification, classify_action
from jarvis.missions.state_store import MissionState, MissionStatus


class MissionCommandStatus(str, Enum):
    PREPARED = "prepared"
    BLOCKED = "blocked"
    DENIED = "denied"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"


@dataclass(frozen=True)
class MissionCommandValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionCommand:
    command_id: str
    mission_id: str
    action: str
    classification: ActionClassification
    status: MissionCommandStatus
    prepared_by: str
    reason: str
    requires_approval: bool
    approval_level: MissionApprovalLevel
    scope: List[str]
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_name: Optional[str] = None
    channel: Optional[str] = None
    audit_event_id: Optional[str] = None
    approval_request_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: _now_iso())

    def __post_init__(self) -> None:
        self.classification = _coerce_enum(ActionClassification, self.classification, "classification")
        self.status = _coerce_enum(MissionCommandStatus, self.status, "status")
        self.approval_level = _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level")
        self.scope = _list_from(self.scope)

        result = validate_mission_command(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionCommand":
        return cls(
            command_id=str(data.get("command_id", "")),
            mission_id=str(data.get("mission_id", "")),
            action=str(data.get("action", "")),
            classification=data.get("classification", ""),
            status=data.get("status", ""),
            prepared_by=str(data.get("prepared_by", "")),
            reason=str(data.get("reason", "")),
            requires_approval=bool(data.get("requires_approval", False)),
            approval_level=data.get("approval_level", ""),
            tool_name=data.get("tool_name"),
            channel=data.get("channel"),
            scope=_list_from(data.get("scope")),
            inputs=data.get("inputs", {}),
            metadata=data.get("metadata", {}),
            audit_event_id=data.get("audit_event_id"),
            approval_request_id=data.get("approval_request_id"),
            created_at=str(data.get("created_at", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "mission_id": self.mission_id,
            "action": self.action,
            "classification": self.classification.value,
            "status": self.status.value,
            "prepared_by": self.prepared_by,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
            "approval_level": self.approval_level.value,
            "tool_name": self.tool_name,
            "channel": self.channel,
            "scope": list(self.scope),
            "inputs": dict(self.inputs),
            "metadata": dict(self.metadata),
            "audit_event_id": self.audit_event_id,
            "approval_request_id": self.approval_request_id,
            "created_at": self.created_at,
        }


def build_mission_command(
    state: MissionState,
    action: str,
    prepared_by: str,
    *,
    tool_name: Optional[str] = None,
    channel: Optional[str] = None,
    reason: Optional[str] = None,
    inputs: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    command_id: Optional[str] = None,
    scope: Optional[List[str]] = None,
    audit_event_id: Optional[str] = None,
    approval_request_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> MissionCommand:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")

    classification = _classify_command_action(state, action, tool_name=tool_name)
    status = _status_for(state.status, classification)
    requires_approval = status in {
        MissionCommandStatus.REQUIRES_REVIEW,
        MissionCommandStatus.REQUIRES_APPROVAL,
        MissionCommandStatus.REQUIRES_STRONG_APPROVAL,
    }

    return MissionCommand(
        command_id=command_id or str(uuid4()),
        mission_id=state.mission_id,
        action=(action or "").strip(),
        classification=classification,
        status=status,
        prepared_by=prepared_by,
        reason=reason or _default_reason(state.status, classification, status),
        requires_approval=requires_approval,
        approval_level=_approval_level_for(status, classification),
        tool_name=tool_name,
        channel=channel,
        scope=_default_scope(action, scope),
        inputs={} if inputs is None else inputs,
        metadata={} if metadata is None else metadata,
        audit_event_id=audit_event_id,
        approval_request_id=approval_request_id,
        created_at=created_at or _now_iso(),
    )


def validate_mission_command(command: MissionCommand) -> MissionCommandValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(getattr(command, "command_id", "")):
        errors.append("command_id must be a non-empty string")
    if not _is_non_empty_string(getattr(command, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(getattr(command, "action", "")):
        errors.append("action must be a non-empty string")
    if not _is_non_empty_string(getattr(command, "prepared_by", "")):
        errors.append("prepared_by must be a non-empty string")

    try:
        classification = ActionClassification(getattr(command, "classification", ""))
    except ValueError:
        errors.append("classification must be a valid ActionClassification")
        classification = None

    try:
        status = MissionCommandStatus(getattr(command, "status", ""))
    except ValueError:
        errors.append("status must be a valid MissionCommandStatus")
        status = None

    inputs = getattr(command, "inputs", None)
    if not isinstance(inputs, dict):
        errors.append("inputs must be a dict")
        inputs = {}

    metadata = getattr(command, "metadata", None)
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")
        metadata = {}

    if getattr(command, "requires_approval", False) and not getattr(command, "scope", []):
        errors.append("scope cannot be empty when requires_approval is true")

    if classification == ActionClassification.DENIED and status == MissionCommandStatus.PREPARED:
        errors.append("denied command cannot have status prepared")
    if (
        getattr(command, "approval_level", None) == MissionApprovalLevel.DENIED
        and status == MissionCommandStatus.PREPARED
    ):
        errors.append("blocked command cannot have status prepared")

    approval_statuses = {
        MissionCommandStatus.REQUIRES_REVIEW,
        MissionCommandStatus.REQUIRES_APPROVAL,
        MissionCommandStatus.REQUIRES_STRONG_APPROVAL,
    }
    if status in approval_statuses and not getattr(command, "requires_approval", False):
        errors.append("requires_approval must be true for review or approval command statuses")

    tool_name = getattr(command, "tool_name", None)
    if tool_name is not None and not _is_non_empty_string(tool_name):
        errors.append("tool_name cannot be an empty string")

    blanket_paths = _blanket_approval_paths(
        {
            "action": getattr(command, "action", ""),
            "inputs": inputs,
            "metadata": metadata,
        }
    )
    if blanket_paths:
        errors.append("command cannot contain vague blanket approval: " + ", ".join(blanket_paths))

    secret_paths = _secret_like_key_paths({"inputs": inputs, "metadata": metadata})
    if secret_paths:
        errors.append("inputs and metadata cannot include secret-like keys: " + ", ".join(secret_paths))

    return MissionCommandValidationResult(errors=errors)


def _classify_command_action(
    state: MissionState,
    action: str,
    *,
    tool_name: Optional[str] = None,
) -> ActionClassification:
    classification = classify_action(state.envelope, action)
    if classification == ActionClassification.DENIED:
        return classification

    if _is_candidate_tool_only(state, tool_name):
        if classification == ActionClassification.ALLOWED:
            return ActionClassification.UNKNOWN_REQUIRES_REVIEW
        return classification

    return classification


def _status_for(status: MissionStatus, classification: ActionClassification) -> MissionCommandStatus:
    if status in _BLOCKED_MISSION_STATUSES:
        return MissionCommandStatus.BLOCKED
    if classification == ActionClassification.ALLOWED:
        return MissionCommandStatus.PREPARED
    if classification == ActionClassification.REQUIRES_APPROVAL:
        return MissionCommandStatus.REQUIRES_APPROVAL
    if classification == ActionClassification.STRONG_APPROVAL:
        return MissionCommandStatus.REQUIRES_STRONG_APPROVAL
    if classification == ActionClassification.DENIED:
        return MissionCommandStatus.DENIED
    return MissionCommandStatus.REQUIRES_REVIEW


def _approval_level_for(
    status: MissionCommandStatus,
    classification: ActionClassification,
) -> MissionApprovalLevel:
    if status == MissionCommandStatus.BLOCKED:
        return MissionApprovalLevel.DENIED
    if classification == ActionClassification.ALLOWED:
        return MissionApprovalLevel.ALLOWED
    if classification == ActionClassification.REQUIRES_APPROVAL:
        return MissionApprovalLevel.REQUIRES_APPROVAL
    if classification == ActionClassification.STRONG_APPROVAL:
        return MissionApprovalLevel.STRONG_APPROVAL
    if classification == ActionClassification.DENIED:
        return MissionApprovalLevel.DENIED
    return MissionApprovalLevel.REQUIRES_REVIEW


def _default_reason(
    mission_status: MissionStatus,
    classification: ActionClassification,
    command_status: MissionCommandStatus,
) -> str:
    if command_status == MissionCommandStatus.BLOCKED:
        return f"Mission status is {mission_status.value}; command is prepared only as blocked metadata."
    if classification == ActionClassification.ALLOWED:
        return "Action is allowed within the Mission Envelope and command is prepared."
    if classification == ActionClassification.REQUIRES_APPROVAL:
        return "Action requires explicit mission approval before execution."
    if classification == ActionClassification.STRONG_APPROVAL:
        return "Action requires strong mission approval before execution."
    if classification == ActionClassification.DENIED:
        return "Action is denied by the Mission Envelope and must not execute."
    return "Action or tool is not declared as allowed in the Mission Envelope and requires review."


def _default_scope(action: str, scope: Optional[List[str]]) -> List[str]:
    if scope is not None:
        return _list_from(scope)
    normalized_action = (action or "").strip()
    return [normalized_action] if normalized_action else []


def _is_candidate_tool_only(state: MissionState, tool_name: Optional[str]) -> bool:
    normalized = _normalize(tool_name)
    if not normalized:
        return False
    allowed_tools = {_normalize(tool) for tool in state.envelope.allowed_tools}
    candidate_tools = {_normalize(tool) for tool in state.envelope.candidate_tools}
    return normalized in candidate_tools and normalized not in allowed_tools


def _blanket_approval_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _contains_blanket_approval(str(key)):
                paths.append(key_path)
            paths.extend(_blanket_approval_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_blanket_approval_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and _contains_blanket_approval(value):
        paths.append(prefix or "value")
    return paths


def _secret_like_key_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _normalize(str(key)) in _SECRET_LIKE_KEYS:
                paths.append(key_path)
            paths.extend(_secret_like_key_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_secret_like_key_paths(item, f"{prefix}[{index}]"))
    return paths


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


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_BLOCKED_MISSION_STATUSES = {
    MissionStatus.BLOCKED,
    MissionStatus.STOPPED,
    MissionStatus.COMPLETED,
    MissionStatus.FAILED,
    MissionStatus.ARCHIVED,
}

_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
}

_SECRET_LIKE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "private_key",
    "authorization",
    "cookie",
    ".env",
}
