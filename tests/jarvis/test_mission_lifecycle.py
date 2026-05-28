from unittest.mock import patch

import pytest

from jarvis.missions.approval_request import MissionApprovalLevel, MissionApprovalRequest
from jarvis.missions.audit_log import (
    MissionAuditEventType,
    MissionAuditOutcome,
    MissionAuditRiskLevel,
    build_audit_event,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
from jarvis.missions.lifecycle import validate_status_transition
from jarvis.missions.state_store import MissionState, MissionStatus


def _valid_envelope(**overrides):
    data = {
        "mission_id": "mission-1",
        "objective": "Crear una landing revisable para validar un nicho",
        "success_metric": "Landing draft y tres variantes comparadas",
        "deadline": "2026-06-15",
        "budget_limit": 50.0,
        "cost_limit_per_action": 10.0,
        "allowed_actions": ["research", "draft"],
        "requires_approval_actions": ["file_write"],
        "strong_approval_actions": ["deploy"],
        "denied_actions": ["spam"],
        "allowed_tools": ["approved_local_editor"],
        "candidate_tools": ["Open Design"],
        "channels": ["local", "docs"],
        "stop_conditions": ["approval_needed"],
        "audit_requirements": ["objective", "actions", "approvals"],
        "rollback_plan": "revert generated files",
    }
    data.update(overrides)
    return MissionEnvelope(**data)


def _valid_state(**overrides):
    data = {
        "mission_id": "mission-1",
        "envelope": _valid_envelope(),
        "status": MissionStatus.DRAFT,
        "created_at": "2026-05-28T10:00:00+00:00",
        "updated_at": "2026-05-28T10:00:00+00:00",
        "metadata": {"source": "test"},
    }
    data.update(overrides)
    return MissionState(**data)


def _valid_request(**overrides):
    data = {
        "request_id": "approval-1",
        "mission_id": "mission-1",
        "action": "file_write",
        "classification": ActionClassification.REQUIRES_APPROVAL,
        "reason": "Action requires approval before execution.",
        "scope": ["file_write"],
        "requested_by": "jarvis",
        "approval_level": MissionApprovalLevel.REQUIRES_APPROVAL,
        "duration": "one_action",
        "cost_limit": 10.0,
        "rollback_plan": "revert generated files",
        "audit_requirements": ["objective", "actions", "approvals"],
    }
    data.update(overrides)
    return MissionApprovalRequest(**data)


def _valid_event(**overrides):
    data = {
        "mission_id": "mission-1",
        "event_type": MissionAuditEventType.MISSION_CREATED,
        "actor": "jarvis",
        "summary": "Mission state was reviewed.",
        "event_id": "audit-1",
        "created_at": "2026-05-28T10:00:00+00:00",
        "outcome": MissionAuditOutcome.RECORDED,
        "risk_level": MissionAuditRiskLevel.LOW,
    }
    data.update(overrides)
    return build_audit_event(**data)


def test_draft_to_active_allowed():
    result = validate_status_transition(_valid_state(), MissionStatus.ACTIVE)

    assert result.allowed
    assert result.errors == []


def test_active_to_awaiting_approval_allowed():
    state = _valid_state(status=MissionStatus.ACTIVE)

    result = validate_status_transition(state, MissionStatus.AWAITING_APPROVAL)

    assert result.allowed


def test_awaiting_approval_to_active_rejects_non_denied_request_without_grant_evidence():
    state = _valid_state(status=MissionStatus.AWAITING_APPROVAL)

    without_evidence = validate_status_transition(state, MissionStatus.ACTIVE)
    with_request = validate_status_transition(
        _valid_state(status=MissionStatus.AWAITING_APPROVAL, approval_requests=[_valid_request()]),
        MissionStatus.ACTIVE,
    )

    assert not without_evidence.allowed
    assert not with_request.allowed
    assert any("awaiting_approval to active requires" in error for error in without_evidence.errors)
    assert any("awaiting_approval to active requires" in error for error in with_request.errors)


def test_awaiting_approval_to_active_allowed_with_clear_reason():
    state = _valid_state(status=MissionStatus.AWAITING_APPROVAL)

    with_reason = validate_status_transition(state, MissionStatus.ACTIVE, reason="Approval resolved manually.")

    assert with_reason.allowed


def test_awaiting_approval_to_active_allowed_with_approval_granted_audit_event():
    approval_event = _valid_event(
        event_type=MissionAuditEventType.APPROVAL_GRANTED,
        outcome=MissionAuditOutcome.ALLOWED,
        approval_request_id="approval-1",
    )
    state = _valid_state(status=MissionStatus.AWAITING_APPROVAL, audit_events=[approval_event])

    result = validate_status_transition(state, MissionStatus.ACTIVE)

    assert result.allowed


@pytest.mark.parametrize("status", [MissionStatus.STOPPED, MissionStatus.FAILED])
def test_active_to_terminal_error_status_requires_reason(status):
    state = _valid_state(status=MissionStatus.ACTIVE)

    result = validate_status_transition(state, status)

    assert not result.allowed
    assert f"transition to {status.value} requires reason" in result.errors


def test_active_to_completed_requires_reason_or_audit_event():
    state = _valid_state(status=MissionStatus.ACTIVE)

    without_evidence = validate_status_transition(state, MissionStatus.COMPLETED)
    with_reason = validate_status_transition(state, MissionStatus.COMPLETED, reason="Success metric was met.")
    with_event = validate_status_transition(
        _valid_state(status=MissionStatus.ACTIVE, audit_events=[_valid_event()]),
        MissionStatus.COMPLETED,
    )

    assert not without_evidence.allowed
    assert "transition to completed requires reason or audit event" in without_evidence.errors
    assert with_reason.allowed
    assert with_event.allowed


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (MissionStatus.COMPLETED, MissionStatus.ACTIVE),
        (MissionStatus.ARCHIVED, MissionStatus.ACTIVE),
        (MissionStatus.DRAFT, MissionStatus.COMPLETED),
        (MissionStatus.ACTIVE, MissionStatus.ARCHIVED),
    ],
)
def test_prohibited_transitions_are_denied(from_status, to_status):
    if from_status in {MissionStatus.DRAFT, MissionStatus.ACTIVE}:
        state = _valid_state(status=from_status)
    else:
        state = _valid_state(status=from_status, completed_at="2026-05-28T11:00:00+00:00")

    result = validate_status_transition(state, to_status, reason="manual check")

    assert not result.allowed
    assert f"transition from {from_status.value} to {to_status.value} is not allowed" in result.errors


def test_failed_to_archived_allowed():
    state = _valid_state(status=MissionStatus.FAILED, last_error="Experiment failed.")

    result = validate_status_transition(state, MissionStatus.ARCHIVED)

    assert result.allowed


def test_denied_approval_request_blocks_completed():
    denied_request = _valid_request(
        action="spam",
        classification=ActionClassification.DENIED,
        approval_level=MissionApprovalLevel.DENIED,
    )
    state = _valid_state(
        status=MissionStatus.BLOCKED,
        approval_requests=[denied_request],
        last_error="Approval request was denied.",
    )

    result = validate_status_transition(state, MissionStatus.COMPLETED, reason="Trying to close.")

    assert not result.allowed
    assert "transition to completed is blocked by a denied approval request" in result.errors


def test_validate_status_transition_does_not_mutate_state():
    state = _valid_state(status=MissionStatus.ACTIVE)
    before = state.to_dict()

    validate_status_transition(state, MissionStatus.STOPPED, reason="User stopped the mission.")

    assert state.to_dict() == before


def test_invalid_to_status_fails_with_clear_error():
    result = validate_status_transition(_valid_state(), "not_real")

    assert not result.allowed
    assert "to_status must be a valid MissionStatus" in result.errors


def test_invalid_state_fails_with_clear_error():
    result = validate_status_transition(object(), MissionStatus.ACTIVE)

    assert not result.allowed
    assert "state must be a MissionState" in result.errors


def test_validator_does_not_call_set_status_or_execute_actions():
    state = _valid_state(status=MissionStatus.ACTIVE)

    with patch("jarvis.missions.state_store.set_status") as set_status:
        result = validate_status_transition(state, MissionStatus.STOPPED, reason="User stopped the mission.")

    assert result.allowed
    set_status.assert_not_called()
