from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from jarvis.missions.approval_request import MissionApprovalLevel, MissionApprovalRequest
from jarvis.missions.audit_log import MissionAuditEvent, MissionAuditEventType
from jarvis.missions.envelope import ActionClassification
from jarvis.missions.state_store import MissionState, MissionStatus, validate_mission_state


@dataclass(frozen=True)
class MissionLifecycleValidationResult:
    allowed: bool
    from_status: Optional[MissionStatus]
    to_status: Any
    reason: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


_ALLOWED_TRANSITIONS = {
    (MissionStatus.DRAFT, MissionStatus.ACTIVE),
    (MissionStatus.DRAFT, MissionStatus.ARCHIVED),
    (MissionStatus.ACTIVE, MissionStatus.AWAITING_APPROVAL),
    (MissionStatus.ACTIVE, MissionStatus.BLOCKED),
    (MissionStatus.ACTIVE, MissionStatus.STOPPED),
    (MissionStatus.ACTIVE, MissionStatus.COMPLETED),
    (MissionStatus.ACTIVE, MissionStatus.FAILED),
    (MissionStatus.AWAITING_APPROVAL, MissionStatus.ACTIVE),
    (MissionStatus.AWAITING_APPROVAL, MissionStatus.BLOCKED),
    (MissionStatus.AWAITING_APPROVAL, MissionStatus.STOPPED),
    (MissionStatus.BLOCKED, MissionStatus.ACTIVE),
    (MissionStatus.BLOCKED, MissionStatus.STOPPED),
    (MissionStatus.BLOCKED, MissionStatus.FAILED),
    (MissionStatus.STOPPED, MissionStatus.ARCHIVED),
    (MissionStatus.COMPLETED, MissionStatus.ARCHIVED),
    (MissionStatus.FAILED, MissionStatus.ARCHIVED),
}


def validate_status_transition(
    state: Any,
    to_status: Any,
    reason: Optional[str] = None,
) -> MissionLifecycleValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    normalized_reason = reason.strip() if isinstance(reason, str) else reason

    mission_state, from_status = _validate_state(state, errors)
    next_status = _coerce_to_status(to_status, errors)

    if mission_state is not None and next_status is not None:
        if (from_status, next_status) not in _ALLOWED_TRANSITIONS:
            errors.append(f"transition from {from_status.value} to {next_status.value} is not allowed")

        if next_status in {MissionStatus.STOPPED, MissionStatus.FAILED} and not _has_reason(normalized_reason):
            errors.append(f"transition to {next_status.value} requires reason")

        if next_status == MissionStatus.BLOCKED and not (
            _has_reason(normalized_reason) or _has_audit_evidence(mission_state)
        ):
            errors.append("transition to blocked requires reason or audit evidence")

        if next_status == MissionStatus.COMPLETED:
            if _has_denied_approval_request(mission_state):
                errors.append("transition to completed is blocked by a denied approval request")
            if not (_has_reason(normalized_reason) or _has_audit_evidence(mission_state)):
                errors.append("transition to completed requires reason or audit event")

        if from_status == MissionStatus.AWAITING_APPROVAL and next_status == MissionStatus.ACTIVE:
            if not (_has_reason(normalized_reason) or _has_approval_granted_audit_event(mission_state)):
                errors.append(
                    "transition from awaiting_approval to active requires reason or approval_granted audit event"
                )

    return MissionLifecycleValidationResult(
        allowed=not errors,
        from_status=from_status,
        to_status=next_status if next_status is not None else to_status,
        reason=normalized_reason,
        errors=errors,
        warnings=warnings,
    )


def _validate_state(state: Any, errors: List[str]) -> Tuple[Optional[MissionState], Optional[MissionStatus]]:
    if not isinstance(state, MissionState):
        errors.append("state must be a MissionState")
        return None, None

    validation = validate_mission_state(state)
    if not validation.is_valid:
        errors.extend(validation.errors)
        return None, state.status if isinstance(state.status, MissionStatus) else None

    return state, state.status


def _coerce_to_status(value: Any, errors: List[str]) -> Optional[MissionStatus]:
    try:
        return MissionStatus(value)
    except ValueError:
        errors.append("to_status must be a valid MissionStatus")
        return None


def _has_reason(reason: Optional[str]) -> bool:
    return bool((reason or "").strip())


def _has_audit_evidence(state: MissionState) -> bool:
    return bool(state.audit_events)


def _has_denied_approval_request(state: MissionState) -> bool:
    return any(
        isinstance(request, MissionApprovalRequest)
        and (
            request.approval_level == MissionApprovalLevel.DENIED
            or request.classification == ActionClassification.DENIED
        )
        for request in state.approval_requests
    )


def _has_approval_granted_audit_event(state: MissionState) -> bool:
    return any(
        isinstance(event, MissionAuditEvent)
        and event.mission_id == state.mission_id
        and event.event_type == MissionAuditEventType.APPROVAL_GRANTED
        for event in state.audit_events
    )
