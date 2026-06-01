from copy import deepcopy

import pytest

from jarvis.missions.approval_bridge import (
    MissionApprovalBridgeDecision,
    MissionApprovalBridgePayload,
    build_approval_bridge_payload,
)
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.budget_guard import MissionBudgetGuardDecision, MissionBudgetGuardResult, evaluate_mission_budget_guard
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus, build_mission_command
from jarvis.missions.dry_run import MissionDryRunDecision, MissionDryRunEvaluation, MissionDryRunRiskLevel
from jarvis.missions.envelope import ActionClassification, MissionEnvelope
from jarvis.missions.hermes_bridge import (
    HermesAgentDescriptor,
    HermesAgentRegistryBridge,
    HermesAgentRiskLevel,
    HermesAuditIntegrationContract,
    HermesCommandPayload,
    HermesDryRunBridge,
    HermesExecutionResult,
    HermesExecutionStatus,
    HermesPayloadStatus,
    build_hermes_command_payload,
    prepare_hermes_audit_contract,
)
from jarvis.missions.policy_bridge import MissionPolicyBridgeDecision, MissionPolicyBridgeResult, evaluate_mission_policy_bridge
from jarvis.missions.safety_baseline import MissionSafetyBaselineDecision, MissionSafetyBaselineResult
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
        "channels": ["local"],
        "stop_conditions": ["approval_needed"],
        "audit_requirements": ["objective", "actions", "approvals"],
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
        "metadata": {"source": "test"},
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
        "inputs": {"query": "niche"},
        "metadata": {"source": "test"},
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
        "metadata": {"source": "test"},
    }
    data.update(overrides)
    return MissionDryRunEvaluation(**data)


def _approval_payload(**overrides):
    data = {
        "payload_id": "approval-payload-1",
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
        "audit_summary": "approval bridge prepared",
        "challenge_required": False,
        "strong_approval_required": False,
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionApprovalBridgePayload(**data)


def _safety_result(**overrides):
    data = {
        "result_id": "safety-1",
        "mission_id": "mission-1",
        "command_id": "command-1",
        "evaluation_id": "evaluation-1",
        "payload_id": "approval-payload-1",
        "decision": MissionSafetyBaselineDecision.PASS_PREPARE_ONLY,
        "can_prepare": True,
        "can_execute_later": False,
        "requires_approval": False,
        "approval_level": MissionApprovalLevel.ALLOWED,
        "risk_level": MissionDryRunRiskLevel.LOW,
        "findings": [],
        "policy_notes": ["safe"],
        "audit_summary": "safety passed",
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionSafetyBaselineResult(**data)


def _policy_result(**overrides):
    data = {
        "result_id": "policy-1",
        "mission_id": "mission-1",
        "command_id": "command-1",
        "evaluation_id": "evaluation-1",
        "payload_id": "approval-payload-1",
        "safety_result_id": "safety-1",
        "decision": MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY,
        "can_prepare": True,
        "can_execute_later": False,
        "requires_approval": False,
        "approval_level": MissionApprovalLevel.ALLOWED,
        "risk_level": MissionDryRunRiskLevel.LOW,
        "reasons": ["allowed"],
        "audit_summary": "policy prepared",
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionPolicyBridgeResult(**data)


def _budget_result(**overrides):
    data = {
        "result_id": "budget-1",
        "mission_id": "mission-1",
        "decision": MissionBudgetGuardDecision.ALLOWED,
        "can_spend": False,
        "cost_summary": {},
        "violations": [],
        "budget_remaining": None,
        "audit_summary": "budget prepared",
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionBudgetGuardResult(**data)


def test_payload_prepare_only_valid_round_trips():
    payload = build_hermes_command_payload(
        _state(),
        _command(),
        _evaluation(),
        _approval_payload(),
        _safety_result(),
        _policy_result(),
        _budget_result(),
        metadata={"source": "test"},
    )

    restored = HermesCommandPayload.from_dict(payload.to_dict())

    assert payload.status == HermesPayloadStatus.PREPARED
    assert payload.dry_run_only is True
    assert payload.can_execute_now is False
    assert restored.to_dict() == payload.to_dict()
    assert payload.metadata["hermes_connected"] is False
    assert payload.metadata["approval_gateway_called"] is False


def test_can_execute_now_is_always_false_even_for_allowed_payload():
    payload = build_hermes_command_payload(_state(), _command())

    assert payload.can_execute_now is False
    assert payload.dry_run_only is True


def test_candidate_tools_do_not_become_allowed_tools():
    state = _state()
    command = build_mission_command(state, "research", "jarvis", tool_name="Open Design")

    payload = build_hermes_command_payload(state, command)

    assert "Open Design" in payload.candidate_tools
    assert "Open Design" not in payload.allowed_tools


@pytest.mark.parametrize(
    "safety_decision",
    [MissionSafetyBaselineDecision.DENIED, MissionSafetyBaselineDecision.BLOCKED],
)
def test_denied_or_blocked_safety_blocks_payload(safety_decision):
    payload = build_hermes_command_payload(
        _state(),
        _command(),
        safety_result=_safety_result(
            decision=safety_decision,
            can_prepare=False,
            requires_approval=False,
            approval_level=MissionApprovalLevel.DENIED,
            risk_level=MissionDryRunRiskLevel.HIGH,
            audit_summary="safety blocked",
        ),
    )

    assert payload.status == HermesPayloadStatus.BLOCKED
    assert payload.blocked_reason
    assert payload.can_execute_now is False


@pytest.mark.parametrize(
    "approval_decision",
    [MissionApprovalBridgeDecision.DENIED, MissionApprovalBridgeDecision.BLOCKED],
)
def test_denied_or_blocked_approval_blocks_payload(approval_decision):
    payload = build_hermes_command_payload(
        _state(),
        _command(),
        approval_payload=_approval_payload(
            decision=approval_decision,
            approval_level=MissionApprovalLevel.DENIED,
            risk_level=MissionDryRunRiskLevel.HIGH,
            blocked_reason="approval blocked",
        ),
    )

    assert payload.status == HermesPayloadStatus.BLOCKED
    assert "approval blocked" in payload.blocked_reason


@pytest.mark.parametrize(
    "policy_decision",
    [MissionPolicyBridgeDecision.DENIED, MissionPolicyBridgeDecision.BLOCKED],
)
def test_denied_or_blocked_policy_blocks_payload(policy_decision):
    payload = build_hermes_command_payload(
        _state(),
        _command(),
        policy_result=_policy_result(
            decision=policy_decision,
            can_prepare=False,
            requires_approval=False,
            approval_level=MissionApprovalLevel.DENIED,
            risk_level=MissionDryRunRiskLevel.HIGH,
            audit_summary="policy blocked",
        ),
    )

    assert payload.status == HermesPayloadStatus.BLOCKED
    assert "policy blocked" in payload.blocked_reason


def test_budget_blocked_blocks_payload():
    payload = build_hermes_command_payload(
        _state(),
        _command(),
        budget_result=_budget_result(
            decision=MissionBudgetGuardDecision.BLOCKED,
            violations=["bad budget"],
            audit_summary="budget blocked",
        ),
    )

    assert payload.status == HermesPayloadStatus.BLOCKED
    assert "budget blocked" in payload.blocked_reason


def test_requires_approval_and_strong_approval_never_execute():
    approval_payload = build_hermes_command_payload(_state(), build_mission_command(_state(), "file_write", "jarvis"))
    strong_payload = build_hermes_command_payload(_state(), build_mission_command(_state(), "deploy", "jarvis"))

    assert approval_payload.approval_level == MissionApprovalLevel.REQUIRES_APPROVAL
    assert approval_payload.can_execute_now is False
    assert strong_payload.approval_level == MissionApprovalLevel.STRONG_APPROVAL
    assert strong_payload.can_execute_now is False


def test_terminal_mission_blocks_payload():
    payload = build_hermes_command_payload(
        _state(status=MissionStatus.COMPLETED, completed_at="2026-05-28T11:00:00+00:00"),
        _command(),
    )

    assert payload.status == HermesPayloadStatus.BLOCKED


def test_mismatch_mission_id_fails():
    with pytest.raises(ValueError, match="command mission_id must match mission state"):
        build_hermes_command_payload(_state(), _command(mission_id="mission-2"))


def test_builder_does_not_mutate_state_or_command():
    state = _state()
    command = _command()
    before = deepcopy((state.to_dict(), command.to_dict()))

    build_hermes_command_payload(state, command)

    assert deepcopy((state.to_dict(), command.to_dict())) == before


@pytest.mark.parametrize("field_name", ["inputs", "metadata"])
@pytest.mark.parametrize("key", ["password", "token", "secret", "api_key", "private_key", "authorization", "cookie", ".env"])
def test_payload_rejects_secret_like_keys(field_name, key):
    data = build_hermes_command_payload(_state(), _command()).to_dict()
    data[field_name] = {key: "redacted"}

    with pytest.raises(ValueError, match="secret-like"):
        HermesCommandPayload.from_dict(data)


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
def test_payload_rejects_blanket_approval_strings(phrase):
    data = build_hermes_command_payload(_state(), _command()).to_dict()
    data["metadata"] = {"approval": phrase}

    with pytest.raises(ValueError, match="vague blanket approval"):
        HermesCommandPayload.from_dict(data)


def test_dry_run_bridge_does_not_execute():
    payload = build_hermes_command_payload(_state(), _command())
    dry_run = HermesDryRunBridge().prepare(payload)

    assert dry_run.payload_id == payload.payload_id
    assert dry_run.can_execute_later is False
    assert dry_run.metadata["tools_executed"] is False
    assert dry_run.metadata["hermes_connected"] is False
    assert HermesDryRunBridge().prepare(payload).can_execute_later is False


def test_execution_result_not_executed_and_dry_run_only_are_json_compatible():
    payload = build_hermes_command_payload(_state(), _command())
    not_executed = HermesExecutionResult.not_executed(payload)
    dry_run_only = HermesExecutionResult.dry_run_only(payload)

    assert HermesExecutionResult.from_dict(not_executed.to_dict()).to_dict() == not_executed.to_dict()
    assert HermesExecutionResult.from_dict(dry_run_only.to_dict()).to_dict() == dry_run_only.to_dict()
    assert not_executed.status == HermesExecutionStatus.NOT_EXECUTED
    assert dry_run_only.status == HermesExecutionStatus.DRY_RUN_ONLY
    assert not_executed.metadata["tools_executed"] is False


def test_completed_execution_result_is_manual_only_json_compatible():
    completed = HermesExecutionResult.from_dict(
        {
            "result_id": "result-1",
            "mission_id": "mission-1",
            "command_id": "command-1",
            "payload_id": "payload-1",
            "status": "completed",
            "started_at": "2026-05-28T10:00:00+00:00",
            "completed_at": "2026-05-28T10:01:00+00:00",
            "output_summary": "manual test fixture",
            "error": None,
            "artifacts": [],
            "logs": [],
            "metadata": {"source": "manual-test"},
        }
    )

    assert completed.status == HermesExecutionStatus.COMPLETED
    assert completed.to_dict()["status"] == "completed"


def test_audit_contract_is_prepare_only_and_serializable():
    payload = build_hermes_command_payload(_state(), _command())
    dry_run = HermesDryRunBridge().prepare(payload)
    result = HermesExecutionResult.not_executed(payload)

    audit = prepare_hermes_audit_contract(payload, dry_run, result)
    restored = HermesAuditIntegrationContract.from_dict(audit.to_dict())

    assert restored.to_dict() == audit.to_dict()
    assert audit.audit_metadata["audit_log_written"] is False
    assert audit.audit_metadata["hermes_connected"] is False
    assert audit.audit_metadata["tools_executed"] is False


def test_agent_registry_models_available_agents_without_executing_tools():
    agent = HermesAgentDescriptor(
        agent_id="agent-1",
        name="Research Agent",
        role="research",
        capabilities=["summarize"],
        allowed_tools=["local_editor"],
        risk_level=HermesAgentRiskLevel.LOW,
        requires_approval=False,
    )
    registry = HermesAgentRegistryBridge([agent])

    restored = registry.get("agent-1")

    assert restored.to_dict() == agent.to_dict()
    assert registry.to_dict()["metadata"]["registry_executes_tools"] is False
    with pytest.raises(RuntimeError, match="does not execute tools"):
        registry.execute_tool("agent-1", "local_editor")


def test_agent_registry_requires_non_empty_agent_id_and_lists():
    with pytest.raises(ValueError, match="agent_id must be a non-empty string"):
        HermesAgentDescriptor(
            agent_id=" ",
            name="Broken",
            role="research",
            capabilities=[],
            allowed_tools=[],
            risk_level=HermesAgentRiskLevel.LOW,
            requires_approval=False,
        )

    agent = HermesAgentDescriptor(
        agent_id="agent-2",
        name="Disabled",
        role="research",
        capabilities=["summarize"],
        allowed_tools=[],
        risk_level=HermesAgentRiskLevel.LOW,
        requires_approval=False,
        enabled=False,
    )
    registry = HermesAgentRegistryBridge([agent])

    assert registry.list_agents(enabled_only=True) == []


def test_agent_with_sensitive_tool_requires_approval():
    with pytest.raises(ValueError, match="sensitive tools requires approval"):
        HermesAgentDescriptor(
            agent_id="agent-sensitive",
            name="Terminal Agent",
            role="runtime",
            capabilities=["run commands"],
            allowed_tools=["terminal"],
            risk_level=HermesAgentRiskLevel.HIGH,
            requires_approval=False,
        )


def test_integrated_policy_and_approval_outputs_still_do_not_execute():
    state = _state()
    command = build_mission_command(state, "file_write", "jarvis")
    approval_payload = build_approval_bridge_payload(state, command)
    policy_result = evaluate_mission_policy_bridge(state, command, payload=approval_payload)
    budget_result = evaluate_mission_budget_guard(state, projected_cost=5.0)

    payload = build_hermes_command_payload(
        state,
        command,
        approval_payload=approval_payload,
        policy_result=policy_result,
        budget_result=budget_result,
    )

    assert payload.policy_decision == MissionPolicyBridgeDecision.REQUIRES_APPROVAL.value
    assert payload.can_execute_now is False
    assert payload.metadata["approval_gateway_called"] is False
    assert payload.metadata["mission_control_connected"] is False
