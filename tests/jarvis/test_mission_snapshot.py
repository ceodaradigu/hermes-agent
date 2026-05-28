import json

import pytest

from jarvis.missions.approval_request import (
    MissionApprovalLevel,
    MissionApprovalRequest,
)
from jarvis.missions.audit_log import (
    MissionAuditEventType,
    MissionAuditOutcome,
    MissionAuditRiskLevel,
    build_audit_event,
)
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus
from jarvis.missions.dry_run import (
    MissionDryRunDecision,
    MissionDryRunEvaluation,
    MissionDryRunRiskLevel,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
from jarvis.missions.snapshot import (
    MissionSnapshot,
    build_mission_snapshot,
    validate_mission_snapshot,
)
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


def _valid_state(**overrides):
    data = {
        "mission_id": "mission-1",
        "envelope": _valid_envelope(),
        "status": MissionStatus.ACTIVE,
        "approval_requests": [_valid_request()],
        "audit_events": [_valid_event()],
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


def _valid_evaluation(**overrides):
    data = {
        "evaluation_id": "evaluation-1",
        "mission_id": "mission-1",
        "command_id": "command-1",
        "action": "research",
        "decision": MissionDryRunDecision.ALLOWED_PREPARE_ONLY,
        "can_prepare": True,
        "can_execute_later": False,
        "requires_approval": False,
        "approval_level": MissionApprovalLevel.ALLOWED,
        "risk_level": MissionDryRunRiskLevel.LOW,
        "policy_notes": ["Dry-run only."],
        "audit_summary": "Dry-run evaluated command.",
        "created_at": "2026-05-28T10:00:00+00:00",
        "metadata": {"source": "test"},
    }
    data.update(overrides)
    return MissionDryRunEvaluation(**data)


def test_build_snapshot_valid_from_mission_state():
    snapshot = build_mission_snapshot(_valid_state())

    assert snapshot.snapshot_id
    assert snapshot.mission_id == "mission-1"
    assert snapshot.state["mission_id"] == "mission-1"
    assert snapshot.status == "active"
    assert snapshot.version == "1"
    assert validate_mission_snapshot(snapshot).is_valid


def test_snapshot_includes_approval_requests_and_audit_events():
    snapshot = build_mission_snapshot(_valid_state())

    assert snapshot.approval_requests[0]["request_id"] == "approval-1"
    assert snapshot.audit_events[0]["event_id"] == "audit-1"
    assert snapshot.audit_summary["approval_request_count"] == 1
    assert snapshot.audit_summary["audit_event_count"] == 1


def test_snapshot_includes_optional_command():
    command = _valid_command()

    snapshot = build_mission_snapshot(_valid_state(), commands=[command])

    assert snapshot.commands[0]["command_id"] == "command-1"
    assert snapshot.audit_summary["command_count"] == 1


def test_snapshot_includes_optional_dry_run_evaluation():
    evaluation = _valid_evaluation()

    snapshot = build_mission_snapshot(_valid_state(), dry_run_evaluations=[evaluation])

    assert snapshot.dry_run_evaluations[0]["evaluation_id"] == "evaluation-1"
    assert snapshot.risk_summary["dry_run_evaluation_count"] == 1
    assert snapshot.risk_summary["risk_counts"]["low"] == 1


def test_rejects_command_from_other_mission():
    command = _valid_command(mission_id="mission-2")

    with pytest.raises(ValueError, match="commands must match mission_id"):
        build_mission_snapshot(_valid_state(), commands=[command])


def test_rejects_dry_run_evaluation_from_other_mission():
    evaluation = _valid_evaluation(mission_id="mission-2")

    with pytest.raises(ValueError, match="dry_run_evaluations must match mission_id"):
        build_mission_snapshot(_valid_state(), dry_run_evaluations=[evaluation])


def test_to_dict_from_dict_preserves_main_fields():
    original = build_mission_snapshot(
        _valid_state(),
        commands=[_valid_command()],
        dry_run_evaluations=[_valid_evaluation()],
        metadata={"source": "test"},
    )

    restored = MissionSnapshot.from_dict(original.to_dict())

    assert restored.snapshot_id == original.snapshot_id
    assert restored.mission_id == original.mission_id
    assert restored.state == original.state
    assert restored.commands == original.commands
    assert restored.dry_run_evaluations == original.dry_run_evaluations
    assert restored.metadata == original.metadata


def test_snapshot_to_dict_is_json_serializable():
    snapshot = build_mission_snapshot(
        _valid_state(),
        commands=[_valid_command()],
        dry_run_evaluations=[_valid_evaluation()],
    )

    json.dumps(snapshot.to_dict())


def test_builder_does_not_mutate_mission_state():
    state = _valid_state()
    before = state.to_dict()

    build_mission_snapshot(state, metadata={"nested": {"api_key": "redacted"}})

    assert state.to_dict() == before


def test_builder_does_not_mutate_command():
    command = _valid_command()
    before = command.to_dict()

    build_mission_snapshot(_valid_state(), commands=[command], metadata={"token": "redacted"})

    assert command.to_dict() == before


def test_builder_does_not_mutate_dry_run_evaluation():
    evaluation = _valid_evaluation()
    before = evaluation.to_dict()

    build_mission_snapshot(_valid_state(), dry_run_evaluations=[evaluation], metadata={"cookie": "redacted"})

    assert evaluation.to_dict() == before


@pytest.mark.parametrize(
    "key",
    ["password", "token", "secret", "api_key", "private_key", "authorization", "cookie", ".env"],
)
def test_redacted_true_removes_secret_like_keys(key):
    snapshot = build_mission_snapshot(_valid_state(), metadata={"safe": {"nested": {key: "dont-expose"}}})
    data = snapshot.to_dict()

    assert key not in data["metadata"]["safe"]["nested"]
    assert snapshot.redacted_fields == [f"metadata.safe.nested.{key}"]
    assert "dont-expose" not in json.dumps(data)


def test_redacted_true_redacts_secret_like_keys_in_substructures():
    command = _valid_command()
    command.metadata["api_key"] = "dont-expose"
    evaluation = _valid_evaluation()
    evaluation.metadata["token"] = "dont-expose-either"

    snapshot = build_mission_snapshot(
        _valid_state(metadata={"authorization": "dont-expose-state"}),
        commands=[command],
        dry_run_evaluations=[evaluation],
    )
    encoded = json.dumps(snapshot.to_dict())

    assert "dont-expose" not in encoded
    assert "state.metadata.authorization" in snapshot.redacted_fields
    assert "commands[0].metadata.api_key" in snapshot.redacted_fields
    assert "dry_run_evaluations[0].metadata.token" in snapshot.redacted_fields


def test_redacted_false_does_not_allow_secret_like_keys_in_v1():
    with pytest.raises(ValueError, match="secret-like keys"):
        build_mission_snapshot(_valid_state(), redacted=False, metadata={"api_key": "dont-expose"})


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
def test_blanket_approval_strings_are_rejected(phrase):
    with pytest.raises(ValueError, match="vague blanket approval"):
        build_mission_snapshot(_valid_state(), metadata={"policy": phrase})


def test_summary_and_audit_summary_do_not_contain_secrets():
    snapshot = build_mission_snapshot(_valid_state(), metadata={"private_key": "dont-expose"})
    encoded_summaries = json.dumps({"summary": snapshot.summary, "audit_summary": snapshot.audit_summary})

    assert "dont-expose" not in encoded_summaries
    assert "private_key" not in encoded_summaries


def test_rejects_non_dict_metadata():
    with pytest.raises(ValueError, match="metadata must be a dict"):
        build_mission_snapshot(_valid_state(), metadata=["not", "dict"])


def test_rejects_non_list_commands():
    with pytest.raises(ValueError, match="commands must be a list"):
        build_mission_snapshot(_valid_state(), commands=_valid_command())


def test_rejects_non_list_dry_run_evaluations():
    with pytest.raises(ValueError, match="dry_run_evaluations must be a list"):
        build_mission_snapshot(_valid_state(), dry_run_evaluations=_valid_evaluation())


def test_validation_rejects_empty_snapshot_id():
    with pytest.raises(ValueError, match="snapshot_id must be a non-empty string"):
        MissionSnapshot.from_dict({**build_mission_snapshot(_valid_state()).to_dict(), "snapshot_id": " "})


def test_validation_rejects_secret_like_keys_in_snapshot_dict():
    data = build_mission_snapshot(_valid_state()).to_dict()
    data["metadata"] = {"api_key": "dont-expose"}

    with pytest.raises(ValueError, match="secret-like keys"):
        MissionSnapshot.from_dict(data)


def test_validation_rejects_summary_blanket_approval_strings():
    data = build_mission_snapshot(_valid_state()).to_dict()
    data["summary"] = "approve_all_forever"

    with pytest.raises(ValueError, match="vague blanket approval"):
        MissionSnapshot.from_dict(data)
