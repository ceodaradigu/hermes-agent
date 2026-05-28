import pytest

from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import (
    MissionCommand,
    MissionCommandStatus,
    build_mission_command,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
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
        "status": MissionStatus.ACTIVE,
        "created_at": "2026-05-28T10:00:00+00:00",
        "updated_at": "2026-05-28T10:00:00+00:00",
        "metadata": {"source": "test"},
    }
    data.update(overrides)
    return MissionState(**data)


def _valid_command(**overrides):
    data = {
        "command_id": "command-1",
        "mission_id": "mission-1",
        "action": "research",
        "classification": ActionClassification.ALLOWED,
        "status": MissionCommandStatus.PREPARED,
        "prepared_by": "jarvis",
        "reason": "Action is allowed.",
        "requires_approval": False,
        "approval_level": MissionApprovalLevel.ALLOWED,
        "scope": ["research"],
        "inputs": {"query": "niche"},
        "metadata": {"source": "test"},
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionCommand(**data)


def test_build_allowed_action_prepares_command_without_approval():
    command = build_mission_command(_valid_state(), "research", "jarvis")

    assert command.classification == ActionClassification.ALLOWED
    assert command.status == MissionCommandStatus.PREPARED
    assert not command.requires_approval
    assert command.approval_level == MissionApprovalLevel.ALLOWED


def test_build_requires_approval_action_marks_command_for_approval():
    command = build_mission_command(_valid_state(), "file_write", "jarvis")

    assert command.classification == ActionClassification.REQUIRES_APPROVAL
    assert command.status == MissionCommandStatus.REQUIRES_APPROVAL
    assert command.requires_approval
    assert command.approval_level == MissionApprovalLevel.REQUIRES_APPROVAL


def test_build_strong_approval_action_marks_command_for_strong_approval():
    command = build_mission_command(_valid_state(), "deploy", "jarvis")

    assert command.classification == ActionClassification.STRONG_APPROVAL
    assert command.status == MissionCommandStatus.REQUIRES_STRONG_APPROVAL
    assert command.requires_approval
    assert command.approval_level == MissionApprovalLevel.STRONG_APPROVAL


def test_denied_action_never_becomes_prepared():
    command = build_mission_command(_valid_state(), "spam", "jarvis")

    assert command.classification == ActionClassification.DENIED
    assert command.status == MissionCommandStatus.DENIED
    assert command.status != MissionCommandStatus.PREPARED
    assert not command.requires_approval


def test_unknown_action_requires_review():
    command = build_mission_command(_valid_state(), "unexpected_action", "jarvis")

    assert command.classification == ActionClassification.UNKNOWN_REQUIRES_REVIEW
    assert command.status == MissionCommandStatus.REQUIRES_REVIEW
    assert command.requires_approval
    assert command.approval_level == MissionApprovalLevel.REQUIRES_REVIEW


def test_candidate_tool_is_not_treated_as_allowed_tool():
    command = build_mission_command(_valid_state(), "research", "jarvis", tool_name="Open Design")

    assert command.classification == ActionClassification.UNKNOWN_REQUIRES_REVIEW
    assert command.status == MissionCommandStatus.REQUIRES_REVIEW
    assert command.requires_approval


def test_allowed_tool_can_prepare_allowed_action_for_active_mission():
    command = build_mission_command(
        _valid_state(),
        "research",
        "jarvis",
        tool_name="approved_local_editor",
    )

    assert command.status == MissionCommandStatus.PREPARED
    assert not command.requires_approval


@pytest.mark.parametrize(
    "status",
    [
        MissionStatus.COMPLETED,
        MissionStatus.FAILED,
        MissionStatus.STOPPED,
        MissionStatus.ARCHIVED,
    ],
)
def test_terminal_mission_statuses_block_normal_command(status):
    state = _valid_state(
        status=status,
        completed_at="2026-05-28T11:00:00+00:00",
        last_error="failed" if status == MissionStatus.FAILED else None,
        stop_reason="stopped" if status == MissionStatus.STOPPED else None,
    )

    command = build_mission_command(state, "research", "jarvis")

    assert command.status == MissionCommandStatus.BLOCKED
    assert command.status != MissionCommandStatus.PREPARED


def test_blocked_mission_does_not_prepare_normal_command():
    state = _valid_state(status=MissionStatus.BLOCKED, last_error="Mission is blocked.")

    command = build_mission_command(state, "research", "jarvis")

    assert command.status == MissionCommandStatus.BLOCKED
    assert command.status != MissionCommandStatus.PREPARED


def test_builder_does_not_mutate_mission_state():
    state = _valid_state()
    before = state.to_dict()

    build_mission_command(state, "file_write", "jarvis", metadata={"source": "test"})

    assert state.to_dict() == before


def test_rejects_empty_command_id():
    with pytest.raises(ValueError, match="command_id must be a non-empty string"):
        _valid_command(command_id="  ")


def test_rejects_empty_action():
    with pytest.raises(ValueError, match="action must be a non-empty string"):
        _valid_command(action="  ")


def test_rejects_empty_prepared_by():
    with pytest.raises(ValueError, match="prepared_by must be a non-empty string"):
        _valid_command(prepared_by="  ")


@pytest.mark.parametrize("field_name", ["metadata", "inputs"])
def test_rejects_non_dict_metadata_or_inputs(field_name):
    with pytest.raises(ValueError, match=f"{field_name} must be a dict"):
        _valid_command(**{field_name: ["not", "dict"]})


@pytest.mark.parametrize("field_name", ["metadata", "inputs"])
@pytest.mark.parametrize(
    "key",
    ["password", "token", "secret", "api_key", "private_key", "authorization", "cookie", ".env"],
)
def test_rejects_secret_like_keys_in_metadata_or_inputs(field_name, key):
    with pytest.raises(ValueError, match="secret-like keys"):
        _valid_command(**{field_name: {key: "redacted"}})


@pytest.mark.parametrize(
    "phrase",
    [
        "approve_all_forever",
        "do_anything",
        "unlimited",
        "no_limits",
        "whatever_it_takes",
        "haz_todo_lo_necesario_sin_limites",
    ],
)
def test_rejects_blanket_approval_strings(phrase):
    with pytest.raises(ValueError, match="vague blanket approval"):
        _valid_command(metadata={"policy": phrase})


def test_to_dict_from_dict_preserves_main_fields():
    original = build_mission_command(
        _valid_state(),
        "file_write",
        "jarvis",
        command_id="command-1",
        tool_name="approved_local_editor",
        channel="local",
        reason="Needs approval.",
        inputs={"path": "README.md"},
        metadata={"source": "test"},
        audit_event_id="audit-1",
        approval_request_id="approval-1",
        created_at="2026-05-28T10:00:00+00:00",
    )

    restored = MissionCommand.from_dict(original.to_dict())

    assert restored.command_id == original.command_id
    assert restored.mission_id == original.mission_id
    assert restored.action == original.action
    assert restored.classification == original.classification
    assert restored.status == original.status
    assert restored.requires_approval == original.requires_approval
    assert restored.approval_level == original.approval_level
    assert restored.tool_name == original.tool_name
    assert restored.channel == original.channel
    assert restored.inputs == original.inputs
    assert restored.metadata == original.metadata
    assert restored.audit_event_id == original.audit_event_id
    assert restored.approval_request_id == original.approval_request_id
