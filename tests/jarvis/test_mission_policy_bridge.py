from copy import deepcopy

from jarvis.missions.approval_bridge import (
    MissionApprovalBridgeDecision,
    MissionApprovalBridgePayload,
    build_approval_bridge_payload,
)
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus, build_mission_command
from jarvis.missions.dry_run import MissionDryRunDecision, MissionDryRunEvaluation, MissionDryRunRiskLevel
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
from jarvis.missions.policy_bridge import MissionPolicyBridgeDecision, MissionPolicyBridgeResult, evaluate_mission_policy_bridge
from jarvis.missions.safety_baseline import MissionSafetyBaselineDecision, evaluate_mission_safety_baseline
from jarvis.missions.state_store import MissionState, MissionStatus


def _envelope(**overrides):
    data = {
        "mission_id": "mission-1",
        "objective": "Create a reviewable asset",
        "success_metric": "Draft prepared",
        "deadline": "2026-06-15",
        "budget_limit": 50.0,
        "cost_limit_per_action": 10.0,
        "allowed_actions": ["research", "draft"],
        "requires_approval_actions": ["file_write"],
        "strong_approval_actions": ["deploy"],
        "denied_actions": ["spam"],
        "allowed_tools": ["local_editor"],
        "candidate_tools": ["Open Design"],
        "rollback_plan": "revert files",
    }
    data.update(overrides)
    return MissionEnvelope(**data)


def _state(**overrides):
    data = {
        "mission_id": "mission-1",
        "envelope": _envelope(),
        "status": MissionStatus.ACTIVE,
        "created_at": "2026-05-28T10:00:00+00:00",
        "updated_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionState(**data)


def _command(**overrides):
    data = {
        "command_id": "command-1",
        "mission_id": "mission-1",
        "action": "research",
        "classification": ActionClassification.ALLOWED,
        "status": MissionCommandStatus.PREPARED,
        "prepared_by": "jarvis",
        "reason": "prepared",
        "requires_approval": False,
        "approval_level": MissionApprovalLevel.ALLOWED,
        "scope": ["research"],
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionCommand(**data)


def _evaluation(**overrides):
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
        "policy_notes": ["dry-run"],
        "audit_summary": "evaluated",
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionDryRunEvaluation(**data)


def _payload(**overrides):
    data = {
        "payload_id": "payload-1",
        "mission_id": "mission-1",
        "command_id": "command-1",
        "evaluation_id": "evaluation-1",
        "action": "research",
        "decision": MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED,
        "approval_level": MissionApprovalLevel.ALLOWED,
        "risk_level": MissionDryRunRiskLevel.LOW,
        "requested_by": "jarvis",
        "reason": "prepared",
        "scope": ["research"],
        "policy_notes": ["bridge"],
        "audit_summary": "payload",
        "challenge_required": False,
        "strong_approval_required": False,
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionApprovalBridgePayload(**data)


def test_safety_baseline_blocked_wins():
    state = _state(envelope=_envelope(rollback_plan=None))
    command = build_mission_command(state, "deploy", "jarvis")
    safety = evaluate_mission_safety_baseline(state, command)

    result = evaluate_mission_policy_bridge(state, command, safety_result=safety)

    assert safety.decision == MissionSafetyBaselineDecision.BLOCKED
    assert result.decision == MissionPolicyBridgeDecision.BLOCKED
    assert result.can_execute_later is False


def test_approval_bridge_denied_wins():
    state = _state()
    command = build_mission_command(state, "spam", "jarvis")
    payload = build_approval_bridge_payload(state, command)

    result = evaluate_mission_policy_bridge(state, command, payload=payload)

    assert payload.decision == MissionApprovalBridgeDecision.DENIED
    assert result.decision == MissionPolicyBridgeDecision.DENIED


def test_strong_approval_wins_over_normal_approval():
    result = evaluate_mission_policy_bridge(
        _state(),
        _command(status=MissionCommandStatus.REQUIRES_APPROVAL, requires_approval=True, approval_level=MissionApprovalLevel.REQUIRES_APPROVAL),
        _evaluation(
            decision=MissionDryRunDecision.REQUIRES_STRONG_APPROVAL,
            can_prepare=False,
            requires_approval=True,
            approval_level=MissionApprovalLevel.STRONG_APPROVAL,
            risk_level=MissionDryRunRiskLevel.HIGH,
        ),
    )

    assert result.decision == MissionPolicyBridgeDecision.REQUIRES_STRONG_APPROVAL
    assert result.approval_level == MissionApprovalLevel.STRONG_APPROVAL


def test_candidate_tool_never_becomes_allowed():
    state = _state()
    command = _command(tool_name="Open Design")

    result = evaluate_mission_policy_bridge(state, command)

    assert result.decision == MissionPolicyBridgeDecision.REQUIRES_REVIEW


def test_terminal_mission_status_blocks():
    result = evaluate_mission_policy_bridge(
        _state(status=MissionStatus.COMPLETED, completed_at="2026-05-28T11:00:00+00:00"),
        _command(),
    )

    assert result.decision == MissionPolicyBridgeDecision.BLOCKED


def test_policy_bridge_does_not_mutate_inputs_and_round_trips():
    state = _state()
    command = _command()
    payload = _payload()
    before = deepcopy((state.to_dict(), command.to_dict(), payload.to_dict()))

    result = evaluate_mission_policy_bridge(state, command, payload=payload)
    restored = MissionPolicyBridgeResult.from_dict(result.to_dict())

    assert deepcopy((state.to_dict(), command.to_dict(), payload.to_dict())) == before
    assert restored.to_dict() == result.to_dict()
    assert result.metadata["approval_gateway_called"] is False
    assert result.metadata["hermes_connected"] is False
