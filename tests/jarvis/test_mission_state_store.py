import os

import pytest

from jarvis.missions.approval_request import (
    MissionApprovalLevel,
    MissionApprovalRequest,
    build_approval_request,
)
from jarvis.missions.audit_log import (
    MissionAuditEventType,
    MissionAuditOutcome,
    MissionAuditRiskLevel,
    build_audit_event,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
from jarvis.missions.state_store import (
    MissionState,
    MissionStateStore,
    MissionStatus,
    add_audit_event,
    add_approval_request,
    set_status,
)


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
        "summary": "Mission state was created.",
        "event_id": "audit-1",
        "created_at": "2026-05-28T10:00:00+00:00",
        "outcome": MissionAuditOutcome.RECORDED,
        "risk_level": MissionAuditRiskLevel.LOW,
    }
    data.update(overrides)
    return build_audit_event(**data)


def test_valid_mission_state_can_be_created():
    state = _valid_state()

    assert state.mission_id == "mission-1"
    assert state.status == MissionStatus.DRAFT
    assert state.approval_requests == []
    assert state.audit_events == []


def test_rejects_empty_mission_id():
    with pytest.raises(ValueError, match="mission_id must be a non-empty string"):
        _valid_state(mission_id="  ")


def test_rejects_envelope_with_different_mission_id():
    with pytest.raises(ValueError, match="mission_id must match envelope.mission_id"):
        _valid_state(envelope=_valid_envelope(mission_id="mission-2"))


def test_rejects_invalid_status():
    with pytest.raises(ValueError, match="status must be a valid MissionStatus"):
        _valid_state(status="not_real")


def test_rejects_non_list_approval_requests():
    with pytest.raises(ValueError, match="approval_requests must be a list"):
        _valid_state(approval_requests="not-a-list")


def test_rejects_non_list_audit_events():
    with pytest.raises(ValueError, match="audit_events must be a list"):
        _valid_state(audit_events="not-a-list")


def test_rejects_non_dict_metadata():
    with pytest.raises(ValueError, match="metadata must be a dict"):
        _valid_state(metadata=["not", "dict"])


def test_rejects_updated_at_before_created_at():
    with pytest.raises(ValueError, match="updated_at cannot be earlier than created_at"):
        _valid_state(
            created_at="2026-05-28T11:00:00+00:00",
            updated_at="2026-05-28T10:00:00+00:00",
        )


def test_rejects_approval_request_from_other_mission():
    request = _valid_request(mission_id="mission-2")

    with pytest.raises(ValueError, match="approval_requests must match mission_id"):
        _valid_state(approval_requests=[request])


def test_rejects_audit_event_from_other_mission():
    event = _valid_event(mission_id="mission-2")

    with pytest.raises(ValueError, match="audit_events must match mission_id"):
        _valid_state(audit_events=[event])


def test_to_dict_from_dict_preserves_main_fields():
    request = _valid_request()
    event = _valid_event()
    original = _valid_state(
        status=MissionStatus.AWAITING_APPROVAL,
        approval_requests=[request],
        audit_events=[event],
        version=1,
        metadata={"source": "test"},
    )

    restored = MissionState.from_dict(original.to_dict())

    assert restored.mission_id == original.mission_id
    assert restored.envelope.mission_id == original.envelope.mission_id
    assert restored.status == original.status
    assert restored.approval_requests[0].request_id == request.request_id
    assert restored.audit_events[0].event_id == event.event_id
    assert restored.metadata == original.metadata


def test_add_approval_request_adds_matching_request():
    state = _valid_state()
    request = _valid_request()

    updated = add_approval_request(state, request)

    assert updated.approval_requests == [request]
    assert updated.status == MissionStatus.AWAITING_APPROVAL
    assert state.approval_requests == []


def test_add_audit_event_adds_matching_event():
    state = _valid_state()
    event = _valid_event()

    updated = add_audit_event(state, event)

    assert updated.audit_events == [event]
    assert state.audit_events == []


def test_stopped_requires_stop_reason():
    with pytest.raises(ValueError, match="stopped status requires stop_reason"):
        _valid_state(status=MissionStatus.STOPPED)


def test_failed_requires_last_error_or_stop_reason():
    with pytest.raises(ValueError, match="failed status requires last_error or stop_reason"):
        _valid_state(status=MissionStatus.FAILED)


def test_blocked_requires_error_reason_or_blocking_audit_event():
    with pytest.raises(ValueError, match="blocked status requires last_error"):
        _valid_state(status=MissionStatus.BLOCKED)


def test_blocked_accepts_relevant_audit_event():
    event = _valid_event(
        event_type=MissionAuditEventType.VALIDATION_FAILED,
        outcome=MissionAuditOutcome.FAILED_VALIDATION,
        reason="Envelope validation failed.",
    )

    state = _valid_state(status=MissionStatus.BLOCKED, audit_events=[event])

    assert state.status == MissionStatus.BLOCKED


def test_completed_at_only_allowed_for_terminal_statuses():
    with pytest.raises(ValueError, match="completed_at is only allowed for terminal statuses"):
        _valid_state(status=MissionStatus.ACTIVE, completed_at="2026-05-28T11:00:00+00:00")


def test_denied_approval_request_does_not_convert_mission_to_completed_or_allowed():
    request = build_approval_request(_valid_envelope(), "spam", "jarvis", duration="one_action")
    state = _valid_state()

    updated = add_approval_request(state, request)

    assert updated.status == MissionStatus.BLOCKED
    assert updated.status != MissionStatus.COMPLETED
    assert updated.last_error


def test_denied_approval_request_rejects_completed_state_by_default():
    request = _valid_request(
        action="spam",
        classification=ActionClassification.DENIED,
        approval_level=MissionApprovalLevel.DENIED,
    )

    with pytest.raises(ValueError, match="denied approval request cannot be treated as completed"):
        _valid_state(status=MissionStatus.COMPLETED, approval_requests=[request])


def test_set_status_applies_reason_for_stopped_and_terminal_timestamp():
    state = _valid_state()

    updated = set_status(state, MissionStatus.STOPPED, reason="User stopped the mission.")

    assert updated.status == MissionStatus.STOPPED
    assert updated.stop_reason == "User stopped the mission."
    assert updated.completed_at


def test_store_add_get_update_list_and_duplicate_rejection():
    store = MissionStateStore()
    state = _valid_state()

    added = store.add(state)
    fetched = store.get("mission-1")
    updated = set_status(fetched, MissionStatus.ACTIVE)
    stored_update = store.update(updated)

    assert added.mission_id == "mission-1"
    assert fetched.mission_id == "mission-1"
    assert stored_update.status == MissionStatus.ACTIVE
    assert [item.mission_id for item in store.list()] == ["mission-1"]
    with pytest.raises(ValueError, match="mission state already exists"):
        store.add(state)


def test_store_returns_copies_to_avoid_accidental_mutation():
    store = MissionStateStore()
    store.add(_valid_state())

    fetched = store.get("mission-1")
    fetched.metadata["changed"] = True

    assert store.get("mission-1").metadata == {"source": "test"}


def test_state_store_does_not_create_files_or_persistence(tmp_path):
    before = set(os.listdir(tmp_path))
    store = MissionStateStore()
    store.add(_valid_state())

    assert set(os.listdir(tmp_path)) == before
