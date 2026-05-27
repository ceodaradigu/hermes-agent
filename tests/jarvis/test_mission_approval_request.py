import pytest

from jarvis.missions.approval_request import (
    MissionApprovalLevel,
    MissionApprovalRequest,
    build_approval_request,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope


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


def test_build_request_for_requires_approval_action():
    request = build_approval_request(_valid_envelope(), "file_write", "jarvis", duration="one_action")

    assert request.mission_id == "mission-1"
    assert request.classification == ActionClassification.REQUIRES_APPROVAL
    assert request.approval_level == MissionApprovalLevel.REQUIRES_APPROVAL
    assert request.scope == ["file_write"]
    assert request.cost_limit == 10.0


def test_build_request_for_strong_approval_action():
    request = build_approval_request(_valid_envelope(), "deploy", "jarvis", duration="one_action")

    assert request.classification == ActionClassification.STRONG_APPROVAL
    assert request.approval_level == MissionApprovalLevel.STRONG_APPROVAL
    assert request.rollback_plan == "revert generated files"


def test_denied_action_does_not_become_allowed():
    request = build_approval_request(_valid_envelope(), "spam", "jarvis", duration="one_action")

    assert request.classification == ActionClassification.DENIED
    assert request.approval_level == MissionApprovalLevel.DENIED


def test_unknown_action_requires_review_conservatively():
    request = build_approval_request(_valid_envelope(), "unexpected_action", "jarvis", duration="one_action")

    assert request.classification == ActionClassification.UNKNOWN_REQUIRES_REVIEW
    assert request.approval_level == MissionApprovalLevel.REQUIRES_REVIEW


def test_allowed_action_does_not_generate_strong_approval_unnecessarily():
    request = build_approval_request(_valid_envelope(), "research", "jarvis", duration="one_action")

    assert request.classification == ActionClassification.ALLOWED
    assert request.approval_level == MissionApprovalLevel.ALLOWED


def test_rejects_empty_request_id():
    with pytest.raises(ValueError, match="request_id must be a non-empty string"):
        _valid_request(request_id="  ")


def test_rejects_empty_action():
    with pytest.raises(ValueError, match="action must be a non-empty string"):
        _valid_request(action="  ")


def test_rejects_empty_requested_by():
    with pytest.raises(ValueError, match="requested_by must be a non-empty string"):
        _valid_request(requested_by="  ")


def test_rejects_negative_cost_limit():
    with pytest.raises(ValueError, match="cost_limit cannot be negative"):
        _valid_request(cost_limit=-1)


@pytest.mark.parametrize("duration", ["forever", "unlimited", "approve_all_forever", "no_limits"])
def test_rejects_unlimited_duration(duration):
    with pytest.raises(ValueError, match="duration cannot grant unlimited approval"):
        _valid_request(duration=duration)


@pytest.mark.parametrize(
    "approval_level",
    [MissionApprovalLevel.REQUIRES_APPROVAL, MissionApprovalLevel.STRONG_APPROVAL],
)
def test_requires_scope_for_approval_requests(approval_level):
    with pytest.raises(ValueError, match="scope cannot be empty"):
        _valid_request(approval_level=approval_level, scope=[])


@pytest.mark.parametrize(
    "approval_level",
    [
        MissionApprovalLevel.REQUIRES_APPROVAL,
        MissionApprovalLevel.STRONG_APPROVAL,
        MissionApprovalLevel.DENIED,
    ],
)
def test_requires_audit_requirements_for_sensitive_requests(approval_level):
    with pytest.raises(ValueError, match="audit_requirements cannot be empty"):
        _valid_request(approval_level=approval_level, audit_requirements=[])


def test_strong_approval_requires_rollback_plan_or_reason():
    with pytest.raises(ValueError, match="strong_approval requires rollback_plan or clear reason"):
        _valid_request(
            classification=ActionClassification.STRONG_APPROVAL,
            approval_level=MissionApprovalLevel.STRONG_APPROVAL,
            reason="",
            rollback_plan=None,
        )


def test_candidate_tool_is_not_treated_as_allowed_tool():
    request = build_approval_request(
        _valid_envelope(),
        "research",
        "jarvis",
        tool_name="Open Design",
        duration="one_action",
    )

    assert request.classification == ActionClassification.UNKNOWN_REQUIRES_REVIEW
    assert request.approval_level == MissionApprovalLevel.REQUIRES_REVIEW


def test_to_dict_from_dict_preserves_fields():
    original = build_approval_request(
        _valid_envelope(),
        "file_write",
        "jarvis",
        duration="one_action",
        tool_name="approved_local_editor",
        channel="local",
        risk_notes=["writes files"],
        metadata={"source": "test"},
    )

    restored = MissionApprovalRequest.from_dict(original.to_dict())

    assert restored.request_id == original.request_id
    assert restored.mission_id == original.mission_id
    assert restored.action == original.action
    assert restored.classification == original.classification
    assert restored.approval_level == original.approval_level
    assert restored.tool_name == original.tool_name
    assert restored.metadata == original.metadata
