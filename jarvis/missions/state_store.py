from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from jarvis.missions.approval_request import MissionApprovalLevel, MissionApprovalRequest
from jarvis.missions.audit_log import MissionAuditEvent, MissionAuditEventType, MissionAuditOutcome
from jarvis.missions.envelope import ActionClassification, MissionEnvelope


class MissionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    AWAITING_APPROVAL = "awaiting_approval"
    BLOCKED = "blocked"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class MissionStateValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionState:
    mission_id: str
    envelope: MissionEnvelope
    status: MissionStatus
    approval_requests: List[MissionApprovalRequest] = field(default_factory=list)
    audit_events: List[MissionAuditEvent] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_error: Optional[str] = None
    stop_reason: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, MissionEnvelope):
            result = validate_mission_state(self)
            raise ValueError("; ".join(result.errors))

        self.status = _coerce_status(self.status)
        if self.approval_requests is None:
            self.approval_requests = []
        if self.audit_events is None:
            self.audit_events = []
        if self.metadata is None:
            self.metadata = {}
        elif isinstance(self.metadata, dict):
            self.metadata = dict(self.metadata)

        result = validate_mission_state(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionState":
        return cls(
            mission_id=str(data.get("mission_id", "")),
            envelope=MissionEnvelope.from_dict(data.get("envelope") or {}),
            status=data.get("status", ""),
            approval_requests=[
                MissionApprovalRequest.from_dict(item) for item in data.get("approval_requests", []) or []
            ],
            audit_events=[MissionAuditEvent.from_dict(item) for item in data.get("audit_events", []) or []],
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            version=int(data.get("version", 1)),
            metadata=dict(data.get("metadata") or {}),
            last_error=data.get("last_error"),
            stop_reason=data.get("stop_reason"),
            completed_at=data.get("completed_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "envelope": self.envelope.to_dict(),
            "status": self.status.value,
            "approval_requests": [request.to_dict() for request in self.approval_requests],
            "audit_events": [event.to_dict() for event in self.audit_events],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "last_error": self.last_error,
            "stop_reason": self.stop_reason,
            "completed_at": self.completed_at,
        }


def validate_mission_state(state: MissionState) -> MissionStateValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(getattr(state, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")

    envelope = getattr(state, "envelope", None)
    if not isinstance(envelope, MissionEnvelope):
        errors.append("envelope must be a MissionEnvelope")
    elif state.mission_id != envelope.mission_id:
        errors.append("mission_id must match envelope.mission_id")

    try:
        status = _coerce_status(getattr(state, "status", ""))
    except ValueError:
        errors.append("status must be a valid MissionStatus")
        status = None

    approval_requests = getattr(state, "approval_requests", None)
    if not isinstance(approval_requests, list):
        errors.append("approval_requests must be a list")
        approval_requests = []

    audit_events = getattr(state, "audit_events", None)
    if not isinstance(audit_events, list):
        errors.append("audit_events must be a list")
        audit_events = []

    for request in approval_requests:
        if not isinstance(request, MissionApprovalRequest):
            errors.append("approval_requests must contain MissionApprovalRequest items")
            continue
        if request.mission_id != getattr(state, "mission_id", None):
            errors.append("approval_requests must match mission_id")

    for event in audit_events:
        if not isinstance(event, MissionAuditEvent):
            errors.append("audit_events must contain MissionAuditEvent items")
            continue
        if event.mission_id != getattr(state, "mission_id", None):
            errors.append("audit_events must match mission_id")

    if not isinstance(getattr(state, "metadata", None), dict):
        errors.append("metadata must be a dict")

    created_at = getattr(state, "created_at", None)
    updated_at = getattr(state, "updated_at", None)
    if _is_before(updated_at, created_at):
        errors.append("updated_at cannot be earlier than created_at")

    completed_at = getattr(state, "completed_at", None)
    if completed_at is not None and status not in _TERMINAL_STATUSES:
        errors.append("completed_at is only allowed for terminal statuses")

    stop_reason = getattr(state, "stop_reason", None)
    last_error = getattr(state, "last_error", None)
    if status == MissionStatus.STOPPED and not _is_non_empty_string(stop_reason):
        errors.append("stopped status requires stop_reason")
    if status == MissionStatus.FAILED and not (_is_non_empty_string(last_error) or _is_non_empty_string(stop_reason)):
        errors.append("failed status requires last_error or stop_reason")
    if status == MissionStatus.BLOCKED and not (
        _is_non_empty_string(last_error) or _is_non_empty_string(stop_reason) or _has_blocking_audit_event(audit_events)
    ):
        errors.append("blocked status requires last_error, stop_reason, or a blocking audit event")

    if status in {MissionStatus.COMPLETED, MissionStatus.ACTIVE} and _has_denied_approval_request(approval_requests):
        errors.append("denied approval request cannot be treated as completed or active by default")

    return MissionStateValidationResult(errors=errors)


def add_approval_request(state: MissionState, request: MissionApprovalRequest) -> MissionState:
    if request.mission_id != state.mission_id:
        raise ValueError("approval request mission_id must match mission state")

    next_status = state.status
    if request.approval_level in {
        MissionApprovalLevel.REQUIRES_REVIEW,
        MissionApprovalLevel.REQUIRES_APPROVAL,
        MissionApprovalLevel.STRONG_APPROVAL,
    }:
        next_status = MissionStatus.AWAITING_APPROVAL
    if request.approval_level == MissionApprovalLevel.DENIED or request.classification == ActionClassification.DENIED:
        next_status = MissionStatus.BLOCKED
        last_error = "Approval request was denied by mission policy."
    else:
        last_error = state.last_error

    return replace(
        state,
        status=next_status,
        approval_requests=list(state.approval_requests) + [request],
        updated_at=_now_iso(),
        last_error=last_error,
    )


def add_audit_event(state: MissionState, event: MissionAuditEvent) -> MissionState:
    if event.mission_id != state.mission_id:
        raise ValueError("audit event mission_id must match mission state")

    return replace(
        state,
        audit_events=list(state.audit_events) + [event],
        updated_at=_now_iso(),
    )


def set_status(state: MissionState, status: MissionStatus, reason: Optional[str] = None) -> MissionState:
    next_status = _coerce_status(status)
    completed_at = state.completed_at
    stop_reason = state.stop_reason
    last_error = state.last_error

    if next_status in _TERMINAL_STATUSES and completed_at is None:
        completed_at = _now_iso()
    if next_status == MissionStatus.STOPPED and reason is not None:
        stop_reason = reason
    if next_status in {MissionStatus.FAILED, MissionStatus.BLOCKED} and reason is not None:
        last_error = reason

    return replace(
        state,
        status=next_status,
        updated_at=_now_iso(),
        completed_at=completed_at,
        stop_reason=stop_reason,
        last_error=last_error,
    )


class MissionStateStore:
    def __init__(self) -> None:
        self._states: Dict[str, MissionState] = {}

    def add(self, state: MissionState) -> MissionState:
        if state.mission_id in self._states:
            raise ValueError(f"mission state already exists: {state.mission_id}")
        self._states[state.mission_id] = deepcopy(state)
        return deepcopy(state)

    def get(self, mission_id: str) -> MissionState:
        try:
            return deepcopy(self._states[mission_id])
        except KeyError as exc:
            raise KeyError(f"mission state not found: {mission_id}") from exc

    def update(self, state: MissionState) -> MissionState:
        if state.mission_id not in self._states:
            raise KeyError(f"mission state not found: {state.mission_id}")
        self._states[state.mission_id] = deepcopy(state)
        return deepcopy(state)

    def list(self) -> List[MissionState]:
        return [deepcopy(state) for state in self._states.values()]


_TERMINAL_STATUSES = {
    MissionStatus.STOPPED,
    MissionStatus.COMPLETED,
    MissionStatus.FAILED,
    MissionStatus.ARCHIVED,
}


def _has_denied_approval_request(approval_requests: List[MissionApprovalRequest]) -> bool:
    return any(
        isinstance(request, MissionApprovalRequest)
        and (
            request.approval_level == MissionApprovalLevel.DENIED
            or request.classification == ActionClassification.DENIED
        )
        for request in approval_requests
    )


def _has_blocking_audit_event(audit_events: List[MissionAuditEvent]) -> bool:
    blocking_event_types = {
        MissionAuditEventType.APPROVAL_DENIED,
        MissionAuditEventType.STOP_CONDITION_TRIGGERED,
        MissionAuditEventType.VALIDATION_FAILED,
    }
    blocking_outcomes = {
        MissionAuditOutcome.DENIED,
        MissionAuditOutcome.FAILED_VALIDATION,
        MissionAuditOutcome.STOPPED,
    }
    return any(
        isinstance(event, MissionAuditEvent)
        and (event.event_type in blocking_event_types or event.outcome in blocking_outcomes)
        for event in audit_events
    )


def _coerce_status(value: Any) -> MissionStatus:
    try:
        return MissionStatus(value)
    except ValueError as exc:
        raise ValueError("status must be a valid MissionStatus") from exc


def _is_before(left: Any, right: Any) -> bool:
    left_dt = _parse_datetime(left)
    right_dt = _parse_datetime(right)
    if left_dt is None or right_dt is None:
        return False
    return left_dt < right_dt


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _is_non_empty_string(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
