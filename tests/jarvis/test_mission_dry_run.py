import pytest

from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import (
    MissionCommand,
    MissionCommandStatus,
    build_mission_command,
)
from jarvis.missions.dry_run import (
    MissionDryRunDecision,
    MissionDryRunEvaluation,
    MissionDryRunRiskLevel,
    evaluate_mission_command_dry_run,
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


def test_prepared_command_allows_prepare_only_without_later_execution():
    state = _valid_state()
    command = build_mission_command(state, "research", "jarvis")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.ALLOWED_PREPARE_ONLY
    assert evaluation.can_prepare is True
    assert evaluation.can_execute_later is False
    assert evaluation.requires_approval is False
    assert evaluation.risk_level == MissionDryRunRiskLevel.LOW


def test_requires_review_command_requires_review_and_approval_gate():
    state = _valid_state()
    command = build_mission_command(state, "unexpected_action", "jarvis")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.REQUIRES_REVIEW
    assert evaluation.requires_approval is True
    assert evaluation.approval_level == MissionApprovalLevel.REQUIRES_REVIEW
    assert evaluation.can_execute_later is False


def test_requires_approval_command_requires_approval():
    state = _valid_state()
    command = build_mission_command(state, "file_write", "jarvis")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.REQUIRES_APPROVAL
    assert evaluation.requires_approval is True
    assert evaluation.approval_level == MissionApprovalLevel.REQUIRES_APPROVAL
    assert evaluation.risk_level == MissionDryRunRiskLevel.MEDIUM


def test_requires_strong_approval_command_is_high_risk_and_strong_approval():
    state = _valid_state()
    command = build_mission_command(state, "deploy", "jarvis")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.REQUIRES_STRONG_APPROVAL
    assert evaluation.requires_approval is True
    assert evaluation.approval_level == MissionApprovalLevel.STRONG_APPROVAL
    assert evaluation.risk_level in {MissionDryRunRiskLevel.HIGH, MissionDryRunRiskLevel.CRITICAL}


def test_denied_command_has_blocked_reason():
    state = _valid_state()
    command = build_mission_command(state, "spam", "jarvis")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.DENIED
    assert evaluation.can_prepare is False
    assert evaluation.can_execute_later is False
    assert evaluation.blocked_reason


def test_blocked_command_has_blocked_reason():
    state = _valid_state(status=MissionStatus.BLOCKED, last_error="Mission is blocked.")
    command = build_mission_command(state, "research", "jarvis")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.BLOCKED
    assert evaluation.can_prepare is False
    assert evaluation.can_execute_later is False
    assert evaluation.blocked_reason


@pytest.mark.parametrize(
    "status",
    [
        MissionStatus.COMPLETED,
        MissionStatus.FAILED,
        MissionStatus.STOPPED,
        MissionStatus.ARCHIVED,
    ],
)
def test_terminal_mission_status_blocks_even_prepared_command(status):
    state = _valid_state(
        status=status,
        completed_at="2026-05-28T11:00:00+00:00",
        last_error="failed" if status == MissionStatus.FAILED else None,
        stop_reason="stopped" if status == MissionStatus.STOPPED else None,
    )
    command = _valid_command()

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.BLOCKED
    assert evaluation.can_prepare is False
    assert evaluation.can_execute_later is False
    assert evaluation.blocked_reason


def test_candidate_tool_remains_review_or_approval_not_execute():
    state = _valid_state()
    command = _valid_command(tool_name="Open Design")

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.REQUIRES_REVIEW
    assert evaluation.requires_approval is True
    assert evaluation.can_prepare is False
    assert evaluation.can_execute_later is False


@pytest.mark.parametrize("field_name", ["metadata", "inputs"])
@pytest.mark.parametrize("key", ["password", "token", "secret", "api_key", "private_key", "authorization", "cookie", ".env"])
def test_secret_like_command_data_blocks_evaluation(field_name, key):
    state = _valid_state()
    command = _valid_command()
    getattr(command, field_name)[key] = "redacted"

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.BLOCKED
    assert evaluation.blocked_reason
    assert "secret" not in evaluation.audit_summary.lower()


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
def test_blanket_approval_strings_block_evaluation_without_echoing_phrase(phrase):
    state = _valid_state()
    command = _valid_command()
    command.metadata["policy"] = phrase

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.BLOCKED
    assert evaluation.blocked_reason
    assert phrase not in evaluation.audit_summary
    assert all(phrase not in note for note in evaluation.policy_notes)


def test_invalid_mutated_command_status_blocks_conservatively():
    state = _valid_state()
    command = _valid_command()
    command.status = "not-real"

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.BLOCKED
    assert evaluation.can_prepare is False
    assert evaluation.can_execute_later is False
    assert evaluation.blocked_reason


def test_evaluator_does_not_mutate_mission_state():
    state = _valid_state()
    command = build_mission_command(state, "file_write", "jarvis", metadata={"source": "test"})
    before = state.to_dict()

    evaluate_mission_command_dry_run(state, command)

    assert state.to_dict() == before


def test_evaluator_does_not_execute_command_callable_input():
    state = _valid_state()
    called = False

    def would_execute():
        nonlocal called
        called = True

    command = _valid_command(inputs={"callable": would_execute})

    evaluation = evaluate_mission_command_dry_run(state, command)

    assert evaluation.decision == MissionDryRunDecision.ALLOWED_PREPARE_ONLY
    assert called is False


def test_to_dict_from_dict_preserves_fields():
    original = evaluate_mission_command_dry_run(_valid_state(), _valid_command(), reason="unit test")

    restored = MissionDryRunEvaluation.from_dict(original.to_dict())

    assert restored.to_dict() == original.to_dict()


def test_invalid_evaluation_id_rejected():
    with pytest.raises(ValueError, match="evaluation_id must be a non-empty string"):
        _valid_evaluation(evaluation_id="  ")


@pytest.mark.parametrize("decision", [MissionDryRunDecision.BLOCKED, MissionDryRunDecision.DENIED])
def test_blocked_or_denied_without_blocked_reason_rejected(decision):
    with pytest.raises(ValueError, match="blocked or denied evaluation requires blocked_reason"):
        _valid_evaluation(
            decision=decision,
            can_prepare=False,
            blocked_reason=None,
            risk_level=MissionDryRunRiskLevel.HIGH,
        )


def test_requires_approval_without_approval_level_rejected():
    with pytest.raises(ValueError, match="requires_approval evaluations require approval_level"):
        _valid_evaluation(
            decision=MissionDryRunDecision.REQUIRES_APPROVAL,
            requires_approval=True,
            approval_level=None,
            can_prepare=False,
            risk_level=MissionDryRunRiskLevel.MEDIUM,
        )


def test_audit_summary_required():
    with pytest.raises(ValueError, match="audit_summary must be a non-empty string"):
        _valid_evaluation(audit_summary="  ")
