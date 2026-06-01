import pytest

from jarvis.missions.approval_bridge import (
    MissionApprovalBridgeDecision,
    MissionApprovalBridgePayload,
    build_approval_bridge_payload,
)
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus, build_mission_command
from jarvis.missions.dry_run import (
    MissionDryRunDecision,
    MissionDryRunEvaluation,
    MissionDryRunRiskLevel,
    evaluate_mission_command_dry_run,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
from jarvis.missions.state_store import MissionState, MissionStatus
from jarvis.policy.approval_gateway import ApprovalGateway


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


def _payload_dict(**overrides):
    data = {
        "payload_id": "payload-1",
        "mission_id": "mission-1",
        "command_id": "command-1",
        "evaluation_id": "evaluation-1",
        "action": "file_write",
        "decision": MissionApprovalBridgeDecision.REQUIRES_APPROVAL,
        "approval_level": MissionApprovalLevel.REQUIRES_APPROVAL,
        "risk_level": MissionDryRunRiskLevel.MEDIUM,
        "requested_by": "jarvis",
        "reason": "Needs approval.",
        "scope": ["file_write"],
        "blocked_reason": None,
        "policy_notes": ["Bridge only."],
        "audit_summary": "Bridge payload prepared.",
        "challenge_required": False,
        "strong_approval_required": False,
        "created_at": "2026-05-28T10:00:00+00:00",
        "expires_at": None,
        "metadata": {"source": "test"},
    }
    data.update(overrides)
    return data


def test_prepared_command_without_approval_builds_no_approval_needed_payload():
    state = _valid_state()
    command = build_mission_command(state, "research", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED
    assert payload.approval_level == MissionApprovalLevel.ALLOWED
    assert payload.strong_approval_required is False
    assert payload.challenge_required is False


def test_requires_review_builds_review_payload():
    state = _valid_state()
    command = build_mission_command(state, "unexpected_action", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW
    assert payload.approval_level == MissionApprovalLevel.REQUIRES_REVIEW
    assert payload.challenge_required is False


def test_high_risk_review_requires_challenge():
    command = _valid_command(status=MissionCommandStatus.REQUIRES_REVIEW, requires_approval=True)
    evaluation = _valid_evaluation(
        decision=MissionDryRunDecision.REQUIRES_REVIEW,
        can_prepare=False,
        requires_approval=True,
        approval_level=MissionApprovalLevel.REQUIRES_REVIEW,
        risk_level=MissionDryRunRiskLevel.HIGH,
    )

    payload = build_approval_bridge_payload(_valid_state(), command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW
    assert payload.challenge_required is True


def test_requires_approval_builds_approval_payload():
    state = _valid_state()
    command = build_mission_command(state, "file_write", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.REQUIRES_APPROVAL
    assert payload.approval_level == MissionApprovalLevel.REQUIRES_APPROVAL


def test_requires_strong_approval_sets_strong_flags():
    state = _valid_state()
    command = build_mission_command(state, "deploy", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL
    assert payload.approval_level == MissionApprovalLevel.STRONG_APPROVAL
    assert payload.strong_approval_required is True
    assert payload.challenge_required is True


def test_denied_command_builds_denied_payload_with_blocked_reason():
    state = _valid_state()
    command = build_mission_command(state, "spam", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.DENIED
    assert payload.blocked_reason
    assert payload.decision != MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED


def test_blocked_command_builds_blocked_payload_with_blocked_reason():
    state = _valid_state(status=MissionStatus.BLOCKED, last_error="Mission is blocked.")
    command = build_mission_command(state, "research", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.BLOCKED
    assert payload.blocked_reason
    assert payload.decision != MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED


@pytest.mark.parametrize("decision", [MissionDryRunDecision.DENIED, MissionDryRunDecision.BLOCKED])
def test_denied_or_blocked_evaluation_wins_over_prepared_command(decision):
    command = _valid_command()
    evaluation = _valid_evaluation(
        decision=decision,
        can_prepare=False,
        blocked_reason="Evaluation blocked.",
        risk_level=MissionDryRunRiskLevel.HIGH,
    )

    payload = build_approval_bridge_payload(_valid_state(), command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision(decision.value)
    assert payload.blocked_reason == "Evaluation blocked."


@pytest.mark.parametrize(
    "status,expected",
    [
        (MissionCommandStatus.DENIED, MissionApprovalBridgeDecision.DENIED),
        (MissionCommandStatus.BLOCKED, MissionApprovalBridgeDecision.BLOCKED),
    ],
)
def test_command_denied_or_blocked_wins_over_permissive_evaluation(status, expected):
    command = _valid_command(
        status=status,
        classification=ActionClassification.DENIED,
        approval_level=MissionApprovalLevel.DENIED,
        reason="Command blocked.",
    )
    evaluation = _valid_evaluation()

    payload = build_approval_bridge_payload(_valid_state(), command, evaluation)

    assert payload.decision == expected
    assert payload.blocked_reason == "Command blocked."


@pytest.mark.parametrize(
    "status",
    [
        MissionStatus.COMPLETED,
        MissionStatus.FAILED,
        MissionStatus.STOPPED,
        MissionStatus.ARCHIVED,
    ],
)
def test_terminal_mission_status_blocks_payload(status):
    state = _valid_state(
        status=status,
        completed_at="2026-05-28T11:00:00+00:00",
        last_error="failed" if status == MissionStatus.FAILED else None,
        stop_reason="stopped" if status == MissionStatus.STOPPED else None,
    )

    payload = build_approval_bridge_payload(state, _valid_command(), _valid_evaluation())

    assert payload.decision == MissionApprovalBridgeDecision.BLOCKED
    assert payload.blocked_reason


def test_command_from_other_mission_fails():
    with pytest.raises(ValueError, match="command mission_id must match mission state"):
        build_approval_bridge_payload(_valid_state(), _valid_command(mission_id="mission-2"))


def test_evaluation_from_other_mission_fails():
    with pytest.raises(ValueError, match="evaluation mission_id must match mission state"):
        build_approval_bridge_payload(_valid_state(), _valid_command(), _valid_evaluation(mission_id="mission-2"))


def test_evaluation_from_other_command_fails():
    with pytest.raises(ValueError, match="evaluation command_id must match command"):
        build_approval_bridge_payload(_valid_state(), _valid_command(), _valid_evaluation(command_id="command-2"))


def test_candidate_tool_does_not_become_no_approval_needed():
    state = _valid_state()
    command = build_mission_command(state, "research", "jarvis", tool_name="Open Design")
    evaluation = evaluate_mission_command_dry_run(state, command)

    payload = build_approval_bridge_payload(state, command, evaluation)

    assert payload.decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW
    assert payload.decision != MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED


def test_bridge_does_not_mutate_mission_state():
    state = _valid_state()
    command = build_mission_command(state, "file_write", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)
    before = state.to_dict()

    build_approval_bridge_payload(state, command, evaluation, metadata={"source": "test"})

    assert state.to_dict() == before


def test_bridge_does_not_call_approval_gateway(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by the bridge")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_if_called)

    payload = build_approval_bridge_payload(_valid_state(), _valid_command(), _valid_evaluation())

    assert payload.decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED


def test_to_dict_from_dict_preserves_main_fields():
    original = build_approval_bridge_payload(
        _valid_state(),
        _valid_command(),
        _valid_evaluation(),
        requested_by="jarvis-test",
        reason="unit test",
        metadata={"source": "test"},
    )

    restored = MissionApprovalBridgePayload.from_dict(original.to_dict())

    assert restored.to_dict() == original.to_dict()


@pytest.mark.parametrize("key", ["password", "token", "secret", "api_key", "private_key", "authorization", "cookie", ".env"])
def test_metadata_secret_like_keys_are_rejected(key):
    with pytest.raises(ValueError, match="secret-like keys"):
        MissionApprovalBridgePayload.from_dict(_payload_dict(metadata={key: "redacted"}))


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
        MissionApprovalBridgePayload.from_dict(_payload_dict(reason=phrase))


@pytest.mark.parametrize(
    "decision",
    [MissionApprovalBridgeDecision.DENIED, MissionApprovalBridgeDecision.BLOCKED],
)
def test_denied_or_blocked_without_blocked_reason_is_rejected(decision):
    with pytest.raises(ValueError, match="requires blocked_reason"):
        MissionApprovalBridgePayload.from_dict(
            _payload_dict(
                decision=decision,
                approval_level=MissionApprovalLevel.DENIED,
                risk_level=MissionDryRunRiskLevel.HIGH,
                blocked_reason=None,
            )
        )


def test_strong_approval_without_challenge_required_is_rejected():
    with pytest.raises(ValueError, match="requires challenge_required true"):
        MissionApprovalBridgePayload.from_dict(
            _payload_dict(
                decision=MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL,
                approval_level=MissionApprovalLevel.STRONG_APPROVAL,
                risk_level=MissionDryRunRiskLevel.HIGH,
                challenge_required=False,
                strong_approval_required=True,
            )
        )


def test_requires_approval_with_empty_scope_is_rejected():
    with pytest.raises(ValueError, match="scope cannot be empty"):
        MissionApprovalBridgePayload.from_dict(_payload_dict(scope=[]))
