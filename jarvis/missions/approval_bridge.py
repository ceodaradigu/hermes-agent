from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus
from jarvis.missions.dry_run import MissionDryRunDecision, MissionDryRunEvaluation, MissionDryRunRiskLevel
from jarvis.missions.state_store import MissionState, MissionStatus


class MissionApprovalBridgeDecision(str, Enum):
    NO_APPROVAL_NEEDED = "no_approval_needed"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"
    DENIED = "denied"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionApprovalBridgeValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionApprovalBridgePayload:
    payload_id: str
    mission_id: str
    command_id: str
    action: str
    decision: MissionApprovalBridgeDecision
    approval_level: MissionApprovalLevel
    risk_level: MissionDryRunRiskLevel
    requested_by: str
    reason: str
    scope: List[str]
    policy_notes: List[str]
    audit_summary: str
    challenge_required: bool
    strong_approval_required: bool
    created_at: str
    evaluation_id: Optional[str] = None
    blocked_reason: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.decision = _coerce_enum(MissionApprovalBridgeDecision, self.decision, "decision")
        self.approval_level = _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level")
        self.risk_level = _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level")
        self.scope = _list_from(self.scope)
        self.policy_notes = _list_from(self.policy_notes)
        self.metadata = dict(self.metadata or {})

        result = validate_approval_bridge_payload(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionApprovalBridgePayload":
        return cls(
            payload_id=str(data.get("payload_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=str(data.get("command_id", "")),
            evaluation_id=data.get("evaluation_id"),
            action=str(data.get("action", "")),
            decision=data.get("decision", ""),
            approval_level=data.get("approval_level", ""),
            risk_level=data.get("risk_level", ""),
            requested_by=str(data.get("requested_by", "")),
            reason=str(data.get("reason", "")),
            scope=_list_from(data.get("scope")),
            blocked_reason=data.get("blocked_reason"),
            policy_notes=_list_from(data.get("policy_notes")),
            audit_summary=str(data.get("audit_summary", "")),
            challenge_required=bool(data.get("challenge_required", False)),
            strong_approval_required=bool(data.get("strong_approval_required", False)),
            created_at=str(data.get("created_at", "")),
            expires_at=data.get("expires_at"),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payload_id": self.payload_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "evaluation_id": self.evaluation_id,
            "action": self.action,
            "decision": self.decision.value,
            "approval_level": self.approval_level.value,
            "risk_level": self.risk_level.value,
            "requested_by": self.requested_by,
            "reason": self.reason,
            "scope": list(self.scope),
            "blocked_reason": self.blocked_reason,
            "policy_notes": list(self.policy_notes),
            "audit_summary": self.audit_summary,
            "challenge_required": self.challenge_required,
            "strong_approval_required": self.strong_approval_required,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "metadata": dict(self.metadata),
        }


def build_approval_bridge_payload(
    state: MissionState,
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation] = None,
    requested_by: str = "jarvis",
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MissionApprovalBridgePayload:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if not isinstance(command, MissionCommand):
        raise ValueError("command must be a MissionCommand")
    if evaluation is not None and not isinstance(evaluation, MissionDryRunEvaluation):
        raise ValueError("evaluation must be a MissionDryRunEvaluation")
    if command.mission_id != state.mission_id:
        raise ValueError("command mission_id must match mission state")
    if evaluation is not None and evaluation.mission_id != state.mission_id:
        raise ValueError("evaluation mission_id must match mission state")
    if evaluation is not None and evaluation.command_id != command.command_id:
        raise ValueError("evaluation command_id must match command")

    decision, blocked_reason = _bridge_decision(state, command, evaluation)
    approval_level = _approval_level_for(decision)
    risk_level = _risk_level_for(decision, evaluation)
    strong_approval_required = decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL
    challenge_required = strong_approval_required or (
        decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW
        and risk_level in {MissionDryRunRiskLevel.HIGH, MissionDryRunRiskLevel.CRITICAL}
    )
    policy_notes = _policy_notes(command, evaluation, blocked_reason)

    return MissionApprovalBridgePayload(
        payload_id=str(uuid4()),
        mission_id=state.mission_id,
        command_id=command.command_id,
        evaluation_id=evaluation.evaluation_id if evaluation is not None else None,
        action=command.action,
        decision=decision,
        approval_level=approval_level,
        risk_level=risk_level,
        requested_by=requested_by,
        reason=reason or _default_reason(decision, command, evaluation, blocked_reason),
        scope=list(command.scope),
        blocked_reason=blocked_reason,
        policy_notes=policy_notes,
        audit_summary=_audit_summary(command, decision, risk_level, blocked_reason),
        challenge_required=challenge_required,
        strong_approval_required=strong_approval_required,
        created_at=_now_iso(),
        metadata=dict(metadata or {}),
    )


def validate_approval_bridge_payload(
    payload: MissionApprovalBridgePayload,
) -> MissionApprovalBridgeValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(getattr(payload, "payload_id", "")):
        errors.append("payload_id must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "command_id", "")):
        errors.append("command_id must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "action", "")):
        errors.append("action must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "requested_by", "")):
        errors.append("requested_by must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "reason", "")):
        errors.append("reason must be a non-empty string")

    try:
        decision = MissionApprovalBridgeDecision(getattr(payload, "decision", ""))
    except ValueError:
        errors.append("decision must be a valid MissionApprovalBridgeDecision")
        decision = None

    try:
        approval_level = MissionApprovalLevel(getattr(payload, "approval_level", ""))
    except ValueError:
        errors.append("approval_level must be a valid MissionApprovalLevel")
        approval_level = None

    try:
        MissionDryRunRiskLevel(getattr(payload, "risk_level", ""))
    except ValueError:
        errors.append("risk_level must be a valid MissionDryRunRiskLevel")

    policy_notes = getattr(payload, "policy_notes", None)
    if not isinstance(policy_notes, list):
        errors.append("policy_notes must be a list")
        policy_notes = []

    metadata = getattr(payload, "metadata", None)
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")
        metadata = {}
    elif not _is_simple_metadata(metadata):
        errors.append("metadata must contain only simple serializable values")

    if not _is_non_empty_string(getattr(payload, "audit_summary", "")):
        errors.append("audit_summary must be a non-empty string")

    blocked_reason = getattr(payload, "blocked_reason", None)
    if decision in {MissionApprovalBridgeDecision.DENIED, MissionApprovalBridgeDecision.BLOCKED}:
        if not _is_non_empty_string(blocked_reason):
            errors.append("denied or blocked bridge payload requires blocked_reason")
        if decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED:
            errors.append("denied or blocked bridge payload cannot be no_approval_needed")

    if decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL and not getattr(
        payload, "challenge_required", False
    ):
        errors.append("requires_strong_approval requires challenge_required true")

    if getattr(payload, "strong_approval_required", False) and approval_level != MissionApprovalLevel.STRONG_APPROVAL:
        errors.append("strong_approval_required requires approval_level strong_approval")

    if decision in {
        MissionApprovalBridgeDecision.REQUIRES_APPROVAL,
        MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL,
    } and not getattr(payload, "scope", []):
        errors.append("scope cannot be empty when bridge decision requires approval")

    if _is_before(getattr(payload, "expires_at", None), getattr(payload, "created_at", None)):
        errors.append("expires_at cannot be earlier than created_at")

    secret_paths = _secret_like_key_paths(metadata)
    if secret_paths:
        errors.append("metadata cannot include secret-like keys: " + ", ".join(secret_paths))

    blanket_paths = _blanket_approval_paths(
        {
            "reason": getattr(payload, "reason", ""),
            "scope": getattr(payload, "scope", []),
            "audit_summary": getattr(payload, "audit_summary", ""),
            "policy_notes": policy_notes,
            "metadata": metadata,
        }
    )
    if blanket_paths:
        errors.append("bridge payload cannot contain vague blanket approval: " + ", ".join(blanket_paths))

    return MissionApprovalBridgeValidationResult(errors=errors)


def _bridge_decision(
    state: MissionState,
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation],
) -> tuple[MissionApprovalBridgeDecision, Optional[str]]:
    if state.status in _BLOCKING_MISSION_STATUSES:
        return (
            MissionApprovalBridgeDecision.BLOCKED,
            f"Mission status is {state.status.value}; approval bridge cannot prepare execution approval.",
        )

    command_decision = _decision_from_command(command)
    if _is_candidate_tool_only(state, command.tool_name) and command_decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED:
        command_decision = MissionApprovalBridgeDecision.REQUIRES_REVIEW

    if command_decision in {MissionApprovalBridgeDecision.DENIED, MissionApprovalBridgeDecision.BLOCKED}:
        return command_decision, command.reason or f"Command is {command_decision.value}."

    if evaluation is not None:
        evaluation_decision = _decision_from_evaluation(evaluation)
        if evaluation_decision in {MissionApprovalBridgeDecision.DENIED, MissionApprovalBridgeDecision.BLOCKED}:
            return evaluation_decision, evaluation.blocked_reason or f"Evaluation is {evaluation_decision.value}."
        return _max_decision(command_decision, evaluation_decision), None

    return command_decision, None


def _decision_from_command(command: MissionCommand) -> MissionApprovalBridgeDecision:
    if command.status == MissionCommandStatus.PREPARED:
        return MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED
    if command.status == MissionCommandStatus.REQUIRES_REVIEW:
        return MissionApprovalBridgeDecision.REQUIRES_REVIEW
    if command.status == MissionCommandStatus.REQUIRES_APPROVAL:
        return MissionApprovalBridgeDecision.REQUIRES_APPROVAL
    if command.status == MissionCommandStatus.REQUIRES_STRONG_APPROVAL:
        return MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL
    if command.status == MissionCommandStatus.DENIED:
        return MissionApprovalBridgeDecision.DENIED
    return MissionApprovalBridgeDecision.BLOCKED


def _decision_from_evaluation(evaluation: MissionDryRunEvaluation) -> MissionApprovalBridgeDecision:
    if evaluation.decision == MissionDryRunDecision.ALLOWED_PREPARE_ONLY:
        return MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED
    if evaluation.decision == MissionDryRunDecision.REQUIRES_REVIEW:
        return MissionApprovalBridgeDecision.REQUIRES_REVIEW
    if evaluation.decision == MissionDryRunDecision.REQUIRES_APPROVAL:
        return MissionApprovalBridgeDecision.REQUIRES_APPROVAL
    if evaluation.decision == MissionDryRunDecision.REQUIRES_STRONG_APPROVAL:
        return MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL
    if evaluation.decision == MissionDryRunDecision.DENIED:
        return MissionApprovalBridgeDecision.DENIED
    return MissionApprovalBridgeDecision.BLOCKED


def _max_decision(
    left: MissionApprovalBridgeDecision,
    right: MissionApprovalBridgeDecision,
) -> MissionApprovalBridgeDecision:
    order = {
        MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED: 0,
        MissionApprovalBridgeDecision.REQUIRES_REVIEW: 1,
        MissionApprovalBridgeDecision.REQUIRES_APPROVAL: 2,
        MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL: 3,
    }
    return left if order[left] >= order[right] else right


def _approval_level_for(decision: MissionApprovalBridgeDecision) -> MissionApprovalLevel:
    if decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED:
        return MissionApprovalLevel.ALLOWED
    if decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW:
        return MissionApprovalLevel.REQUIRES_REVIEW
    if decision == MissionApprovalBridgeDecision.REQUIRES_APPROVAL:
        return MissionApprovalLevel.REQUIRES_APPROVAL
    if decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL:
        return MissionApprovalLevel.STRONG_APPROVAL
    return MissionApprovalLevel.DENIED


def _risk_level_for(
    decision: MissionApprovalBridgeDecision,
    evaluation: Optional[MissionDryRunEvaluation],
) -> MissionDryRunRiskLevel:
    if evaluation is not None:
        return evaluation.risk_level
    if decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL:
        return MissionDryRunRiskLevel.HIGH
    if decision in {MissionApprovalBridgeDecision.DENIED, MissionApprovalBridgeDecision.BLOCKED}:
        return MissionDryRunRiskLevel.HIGH
    if decision in {MissionApprovalBridgeDecision.REQUIRES_REVIEW, MissionApprovalBridgeDecision.REQUIRES_APPROVAL}:
        return MissionDryRunRiskLevel.MEDIUM
    return MissionDryRunRiskLevel.LOW


def _policy_notes(
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation],
    blocked_reason: Optional[str],
) -> List[str]:
    notes = ["Approval bridge payload prepared only; no approval, gateway call, or execution was attempted."]
    if command.reason:
        notes.append(f"Command reason: {_safe_text(command.reason)}")
    if evaluation is not None:
        notes.extend(_safe_text(note) for note in evaluation.policy_notes)
    if blocked_reason:
        notes.append(f"Blocked reason: {_safe_text(blocked_reason)}")
    return notes


def _default_reason(
    decision: MissionApprovalBridgeDecision,
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation],
    blocked_reason: Optional[str],
) -> str:
    if blocked_reason:
        return _safe_text(blocked_reason)
    if decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED:
        return "Command and dry-run evaluation do not require approval."
    if decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW:
        return "Command or dry-run evaluation requires human review before any future execution."
    if decision == MissionApprovalBridgeDecision.REQUIRES_APPROVAL:
        return "Command or dry-run evaluation requires explicit approval before any future execution."
    if decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL:
        return "Command or dry-run evaluation requires strong approval before any future execution."
    if evaluation is not None and evaluation.blocked_reason:
        return _safe_text(evaluation.blocked_reason)
    return _safe_text(command.reason or "Approval bridge payload is not executable.")


def _audit_summary(
    command: MissionCommand,
    decision: MissionApprovalBridgeDecision,
    risk_level: MissionDryRunRiskLevel,
    blocked_reason: Optional[str],
) -> str:
    summary = (
        f"Approval bridge prepared payload for command {command.command_id}: "
        f"decision={decision.value}, risk={risk_level.value}; no approval or execution occurred."
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


def _is_simple_metadata(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_simple_metadata(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_simple_metadata(item) for key, item in value.items())
    return False


def _is_before(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    try:
        left_dt = datetime.fromisoformat(left)
        right_dt = datetime.fromisoformat(right)
    except ValueError:
        return False
    return left_dt < right_dt


def _safe_text(value: Optional[str]) -> str:
    text = str(value or "")
    for phrase in _BLANKET_APPROVAL_PHRASES:
        text = text.replace(phrase, "[redacted-policy-phrase]")
    return text


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


_TERMINAL_MISSION_STATUSES = {
    MissionStatus.STOPPED,
    MissionStatus.COMPLETED,
    MissionStatus.FAILED,
    MissionStatus.ARCHIVED,
}

_BLOCKING_MISSION_STATUSES = _TERMINAL_MISSION_STATUSES | {MissionStatus.BLOCKED}

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
