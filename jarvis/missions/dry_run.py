from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus
from jarvis.missions.envelope import ActionClassification
from jarvis.missions.state_store import MissionState, MissionStatus


class MissionDryRunRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MissionDryRunDecision(str, Enum):
    ALLOWED_PREPARE_ONLY = "allowed_prepare_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"
    DENIED = "denied"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionDryRunValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionDryRunEvaluation:
    evaluation_id: str
    mission_id: str
    command_id: str
    action: str
    decision: MissionDryRunDecision
    can_prepare: bool
    can_execute_later: bool
    requires_approval: bool
    approval_level: Optional[MissionApprovalLevel]
    risk_level: MissionDryRunRiskLevel
    policy_notes: List[str]
    audit_summary: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    blocked_reason: Optional[str] = None

    def __post_init__(self) -> None:
        self.decision = _coerce_enum(MissionDryRunDecision, self.decision, "decision")
        self.risk_level = _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level")
        if self.approval_level is not None:
            self.approval_level = _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level")
        self.policy_notes = _list_from(self.policy_notes)
        self.metadata = dict(self.metadata or {})

        result = validate_mission_dry_run_evaluation(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionDryRunEvaluation":
        return cls(
            evaluation_id=str(data.get("evaluation_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=str(data.get("command_id", "")),
            action=str(data.get("action", "")),
            decision=data.get("decision", ""),
            can_prepare=bool(data.get("can_prepare", False)),
            can_execute_later=bool(data.get("can_execute_later", False)),
            requires_approval=bool(data.get("requires_approval", False)),
            approval_level=data.get("approval_level"),
            risk_level=data.get("risk_level", ""),
            blocked_reason=data.get("blocked_reason"),
            policy_notes=_list_from(data.get("policy_notes")),
            audit_summary=str(data.get("audit_summary", "")),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "action": self.action,
            "decision": self.decision.value,
            "can_prepare": self.can_prepare,
            "can_execute_later": self.can_execute_later,
            "requires_approval": self.requires_approval,
            "approval_level": self.approval_level.value if self.approval_level is not None else None,
            "risk_level": self.risk_level.value,
            "blocked_reason": self.blocked_reason,
            "policy_notes": list(self.policy_notes),
            "audit_summary": self.audit_summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


def evaluate_mission_command_dry_run(
    state: MissionState,
    command: MissionCommand,
    *,
    evaluator: str = "jarvis",
    reason: Optional[str] = None,
) -> MissionDryRunEvaluation:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if not isinstance(command, MissionCommand):
        raise ValueError("command must be a MissionCommand")

    mission_status = _coerce_optional_enum(MissionStatus, getattr(state, "status", None))
    command_status = _coerce_optional_enum(MissionCommandStatus, getattr(command, "status", None))
    classification = _coerce_optional_enum(ActionClassification, getattr(command, "classification", None))
    command_approval_level = _coerce_optional_enum(
        MissionApprovalLevel,
        getattr(command, "approval_level", None),
    )

    notes: List[str] = ["Dry-run evaluation only; no command execution was attempted."]
    if reason:
        notes.append(f"Evaluation reason: {_safe_text(reason)}")

    blocked_reason = _preflight_blocked_reason(
        state,
        command,
        mission_status=mission_status,
        command_status=command_status,
        classification=classification,
    )
    candidate_tool = _is_candidate_tool_only(state, command.tool_name)

    if blocked_reason:
        decision = MissionDryRunDecision.BLOCKED
        can_prepare = False
        requires_approval = False
        approval_level = MissionApprovalLevel.DENIED
        risk_level = (
            MissionDryRunRiskLevel.CRITICAL
            if _contains_secret_or_blanket(command)
            else MissionDryRunRiskLevel.HIGH
        )
        notes.append(blocked_reason)
    elif candidate_tool:
        decision = MissionDryRunDecision.REQUIRES_REVIEW
        can_prepare = False
        requires_approval = True
        approval_level = MissionApprovalLevel.REQUIRES_REVIEW
        risk_level = MissionDryRunRiskLevel.MEDIUM
        notes.append("Candidate tool is review-only and cannot be treated as executable.")
    else:
        decision = _decision_for(command_status)
        can_prepare = decision == MissionDryRunDecision.ALLOWED_PREPARE_ONLY
        requires_approval = decision in {
            MissionDryRunDecision.REQUIRES_REVIEW,
            MissionDryRunDecision.REQUIRES_APPROVAL,
            MissionDryRunDecision.REQUIRES_STRONG_APPROVAL,
        }
        approval_level = _approval_level_for(
            decision,
            command_approval_level or MissionApprovalLevel.DENIED,
        )
        risk_level = _risk_level_for(decision, classification)
        blocked_reason = _blocked_reason_for_decision(decision, command)
        if blocked_reason:
            notes.append(blocked_reason)

    audit_summary = _audit_summary(
        evaluator=evaluator,
        command=command,
        decision=decision,
        risk_level=risk_level,
        blocked_reason=blocked_reason,
    )

    return MissionDryRunEvaluation(
        evaluation_id=str(uuid4()),
        mission_id=state.mission_id,
        command_id=command.command_id,
        action=command.action,
        decision=decision,
        can_prepare=can_prepare,
        can_execute_later=False,
        requires_approval=requires_approval,
        approval_level=approval_level,
        risk_level=risk_level,
        blocked_reason=blocked_reason,
        policy_notes=notes,
        audit_summary=audit_summary,
        created_at=_now_iso(),
        metadata={
            "evaluator": _safe_text(evaluator or "jarvis"),
            "command_status": _enum_value(command_status, "invalid"),
            "classification": _enum_value(classification, "invalid"),
            "mission_status": _enum_value(mission_status, "invalid"),
            "tool_name": _safe_text(command.tool_name) if command.tool_name else None,
        },
    )


def validate_mission_dry_run_evaluation(
    evaluation: MissionDryRunEvaluation,
) -> MissionDryRunValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(getattr(evaluation, "evaluation_id", "")):
        errors.append("evaluation_id must be a non-empty string")
    if not _is_non_empty_string(getattr(evaluation, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(getattr(evaluation, "command_id", "")):
        errors.append("command_id must be a non-empty string")
    if not _is_non_empty_string(getattr(evaluation, "action", "")):
        errors.append("action must be a non-empty string")

    try:
        decision = MissionDryRunDecision(getattr(evaluation, "decision", ""))
    except ValueError:
        errors.append("decision must be a valid MissionDryRunDecision")
        decision = None

    try:
        MissionDryRunRiskLevel(getattr(evaluation, "risk_level", ""))
    except ValueError:
        errors.append("risk_level must be a valid MissionDryRunRiskLevel")

    policy_notes = getattr(evaluation, "policy_notes", None)
    if not isinstance(policy_notes, list):
        errors.append("policy_notes must be a list")
        policy_notes = []

    metadata = getattr(evaluation, "metadata", None)
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")
        metadata = {}
    elif not _is_simple_metadata(metadata):
        errors.append("metadata must contain only simple serializable values")

    audit_summary = getattr(evaluation, "audit_summary", "")
    if not _is_non_empty_string(audit_summary):
        errors.append("audit_summary must be a non-empty string")

    blocked_reason = getattr(evaluation, "blocked_reason", None)
    if decision in {MissionDryRunDecision.BLOCKED, MissionDryRunDecision.DENIED} and not _is_non_empty_string(
        blocked_reason
    ):
        errors.append("blocked or denied evaluation requires blocked_reason")

    if getattr(evaluation, "requires_approval", False) and not _is_non_empty_string(
        _approval_level_value(getattr(evaluation, "approval_level", None))
    ):
        errors.append("requires_approval evaluations require approval_level")

    secret_paths = _secret_like_key_paths(metadata)
    if secret_paths:
        errors.append("metadata cannot include secret-like keys: " + ", ".join(secret_paths))

    unsafe_text = {
        "audit_summary": audit_summary,
        "blocked_reason": blocked_reason or "",
        "policy_notes": policy_notes,
    }
    blanket_paths = _blanket_approval_paths(unsafe_text)
    if blanket_paths:
        errors.append("evaluation cannot contain vague blanket approval: " + ", ".join(blanket_paths))

    return MissionDryRunValidationResult(errors=errors)


def _preflight_blocked_reason(
    state: MissionState,
    command: MissionCommand,
    *,
    mission_status: Optional[MissionStatus],
    command_status: Optional[MissionCommandStatus],
    classification: Optional[ActionClassification],
) -> Optional[str]:
    if state.mission_id != command.mission_id:
        return "Command mission_id does not match mission state."
    if mission_status is None:
        return "Mission status is invalid; dry-run evaluation is blocked."
    if command_status is None:
        return "Command status is invalid; dry-run evaluation is blocked."
    if classification is None:
        return "Command classification is invalid; dry-run evaluation is blocked."
    if mission_status in _TERMINAL_MISSION_STATUSES:
        return f"Mission status is terminal ({mission_status.value}); command cannot execute later."
    if mission_status == MissionStatus.BLOCKED:
        return "Mission is blocked; command cannot be prepared for execution."

    secret_paths = _secret_like_key_paths({"inputs": command.inputs, "metadata": command.metadata})
    if secret_paths:
        return "Command contains sensitive input or metadata keys and must be blocked."

    blanket_paths = _blanket_approval_paths(
        {
            "action": command.action,
            "reason": command.reason,
            "inputs": command.inputs,
            "metadata": command.metadata,
        }
    )
    if blanket_paths:
        return "Command contains vague blanket approval language and must be blocked."

    return None


def _decision_for(status: Optional[MissionCommandStatus]) -> MissionDryRunDecision:
    if status == MissionCommandStatus.PREPARED:
        return MissionDryRunDecision.ALLOWED_PREPARE_ONLY
    if status == MissionCommandStatus.REQUIRES_REVIEW:
        return MissionDryRunDecision.REQUIRES_REVIEW
    if status == MissionCommandStatus.REQUIRES_APPROVAL:
        return MissionDryRunDecision.REQUIRES_APPROVAL
    if status == MissionCommandStatus.REQUIRES_STRONG_APPROVAL:
        return MissionDryRunDecision.REQUIRES_STRONG_APPROVAL
    if status == MissionCommandStatus.DENIED:
        return MissionDryRunDecision.DENIED
    return MissionDryRunDecision.BLOCKED


def _approval_level_for(
    decision: MissionDryRunDecision,
    command_approval_level: MissionApprovalLevel,
) -> MissionApprovalLevel:
    if decision == MissionDryRunDecision.ALLOWED_PREPARE_ONLY:
        return MissionApprovalLevel.ALLOWED
    if decision == MissionDryRunDecision.REQUIRES_REVIEW:
        return MissionApprovalLevel.REQUIRES_REVIEW
    if decision == MissionDryRunDecision.REQUIRES_APPROVAL:
        return MissionApprovalLevel.REQUIRES_APPROVAL
    if decision == MissionDryRunDecision.REQUIRES_STRONG_APPROVAL:
        return MissionApprovalLevel.STRONG_APPROVAL
    if decision == MissionDryRunDecision.DENIED:
        return MissionApprovalLevel.DENIED
    return command_approval_level


def _risk_level_for(
    decision: MissionDryRunDecision,
    classification: Optional[ActionClassification],
) -> MissionDryRunRiskLevel:
    if decision == MissionDryRunDecision.REQUIRES_STRONG_APPROVAL:
        return MissionDryRunRiskLevel.HIGH
    if decision in {MissionDryRunDecision.DENIED, MissionDryRunDecision.BLOCKED}:
        return MissionDryRunRiskLevel.HIGH
    if decision in {MissionDryRunDecision.REQUIRES_REVIEW, MissionDryRunDecision.REQUIRES_APPROVAL}:
        return MissionDryRunRiskLevel.MEDIUM
    if classification == ActionClassification.ALLOWED:
        return MissionDryRunRiskLevel.LOW
    if classification == ActionClassification.UNKNOWN_REQUIRES_REVIEW:
        return MissionDryRunRiskLevel.MEDIUM
    return MissionDryRunRiskLevel.UNKNOWN


def _blocked_reason_for_decision(
    decision: MissionDryRunDecision,
    command: MissionCommand,
) -> Optional[str]:
    if decision == MissionDryRunDecision.DENIED:
        return command.reason or "Command is denied by mission policy."
    if decision == MissionDryRunDecision.BLOCKED:
        return command.reason or "Command is blocked by mission policy."
    return None


def _audit_summary(
    *,
    evaluator: str,
    command: MissionCommand,
    decision: MissionDryRunDecision,
    risk_level: MissionDryRunRiskLevel,
    blocked_reason: Optional[str],
) -> str:
    summary = (
        f"{_safe_text(evaluator or 'jarvis')} dry-run evaluated command {command.command_id} "
        f"for action {_safe_text(command.action)!r}: decision={decision.value}, risk={risk_level.value}."
    )
    if blocked_reason:
        summary = f"{summary} Blocked reason: {_safe_text(blocked_reason)}"
    return summary


def _is_candidate_tool_only(state: MissionState, tool_name: Optional[str]) -> bool:
    normalized = _normalize(tool_name)
    if not normalized:
        return False
    allowed_tools = {_normalize(tool) for tool in state.envelope.allowed_tools}
    candidate_tools = {_normalize(tool) for tool in state.envelope.candidate_tools}
    return normalized in candidate_tools and normalized not in allowed_tools


def _contains_secret_or_blanket(command: MissionCommand) -> bool:
    return bool(
        _secret_like_key_paths({"inputs": command.inputs, "metadata": command.metadata})
        or _blanket_approval_paths({"action": command.action, "reason": command.reason})
    )


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


def _contains_blanket_approval(value: str) -> bool:
    normalized = _normalize(value)
    return any(phrase in normalized for phrase in _BLANKET_APPROVAL_PHRASES)


def _safe_text(value: Optional[str]) -> str:
    text = str(value or "")
    for phrase in _BLANKET_APPROVAL_PHRASES:
        text = text.replace(phrase, "[redacted-policy-phrase]")
    return text


def _approval_level_value(value: Any) -> str:
    if isinstance(value, MissionApprovalLevel):
        return value.value
    return str(value or "")


def _is_simple_metadata(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_simple_metadata(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_simple_metadata(item) for key, item in value.items())
    return False


def _coerce_enum(enum_type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}") from exc


def _coerce_optional_enum(enum_type, value: Any):
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        return None


def _enum_value(value: Any, fallback: str) -> str:
    return value.value if isinstance(value, Enum) else fallback


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


_TERMINAL_MISSION_STATUSES = {
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
