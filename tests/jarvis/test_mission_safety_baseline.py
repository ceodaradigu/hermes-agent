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
from jarvis.missions.safety_baseline import (
    MissionSafetyBaselineDecision,
    evaluate_mission_safety_baseline,
)
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
        "allowed_actions": ["research", "draft", "send_email", "publish_ai_post"],
        "requires_approval_actions": ["file_write", "send_email"],
        "strong_approval_actions": ["deploy", "publish_commercial"],
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


def _valid_payload(**overrides):
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
        "reason": "No approval needed.",
        "scope": ["research"],
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
    return MissionApprovalBridgePayload(**data)


def _rule_ids(result):
    return {finding.rule_id for finding in result.findings}


def test_clean_baseline_passes_prepare_only_and_never_allows_execution_later():
    state = _valid_state()
    command = build_mission_command(state, "research", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)
    payload = build_approval_bridge_payload(state, command, evaluation)

    result = evaluate_mission_safety_baseline(state, command, evaluation, payload)

    assert result.decision == MissionSafetyBaselineDecision.PASS_PREPARE_ONLY
    assert result.can_prepare is True
    assert result.can_execute_later is False
    assert result.requires_approval is False
    assert result.metadata["approval_gateway_called"] is False
    assert result.metadata["hermes_connected"] is False


def test_safety_baseline_does_not_call_approval_gateway(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by safety baseline")

    monkeypatch.setattr(ApprovalGateway, "evaluate", fail_if_called, raising=False)

    result = evaluate_mission_safety_baseline(_valid_state(), _valid_command(), _valid_evaluation(), _valid_payload())

    assert result.decision == MissionSafetyBaselineDecision.PASS_PREPARE_ONLY


def test_secrets_in_inputs_or_metadata_block_baseline():
    command = _valid_command()
    command.inputs["api_key"] = "redacted"

    result = evaluate_mission_safety_baseline(_valid_state(), command, _valid_evaluation(), _valid_payload())

    assert result.decision == MissionSafetyBaselineDecision.BLOCKED
    assert result.risk_level == MissionDryRunRiskLevel.CRITICAL
    assert "secrets_in_inputs_or_metadata" in _rule_ids(result)


def test_blanket_approval_strings_block_baseline_without_echoing_phrase():
    command = _valid_command()
    command.metadata["policy"] = "approve_all_forever"

    result = evaluate_mission_safety_baseline(_valid_state(), command, _valid_evaluation(), _valid_payload())

    assert result.decision == MissionSafetyBaselineDecision.BLOCKED
    assert "blanket_approval_language" in _rule_ids(result)
    assert "approve_all_forever" not in result.audit_summary


def test_deploy_without_rollback_blocks_baseline():
    envelope = _valid_envelope(rollback_plan=None)
    state = _valid_state(envelope=envelope)
    command = build_mission_command(state, "deploy", "jarvis")

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.BLOCKED
    assert "deploy_or_production_without_rollback" in _rule_ids(result)


def test_spending_without_budget_limit_blocks_baseline():
    envelope = _valid_envelope(budget_limit=None, allowed_actions=["purchase_ads"])
    state = _valid_state(envelope=envelope)
    command = build_mission_command(state, "purchase_ads", "jarvis")

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.BLOCKED
    assert "spend_without_budget_limit" in _rule_ids(result)


def test_external_contact_without_approval_elevates_to_approval():
    envelope = _valid_envelope(allowed_actions=["send_email"], requires_approval_actions=[])
    state = _valid_state(envelope=envelope)
    command = build_mission_command(state, "send_email", "jarvis")

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.REQUIRES_APPROVAL
    assert result.approval_level == MissionApprovalLevel.REQUIRES_APPROVAL
    assert "external_contact_without_approval" in _rule_ids(result)


def test_commercial_publication_without_strong_approval_elevates_to_strong_approval():
    envelope = _valid_envelope(allowed_actions=["publish_commercial"], strong_approval_actions=[])
    state = _valid_state(envelope=envelope)
    command = build_mission_command(state, "publish_commercial", "jarvis")

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL
    assert result.approval_level == MissionApprovalLevel.STRONG_APPROVAL
    assert "commercial_publication_without_strong_approval" in _rule_ids(result)


def test_candidate_tool_without_evaluation_requires_review():
    state = _valid_state()
    command = _valid_command(tool_name="Open Design")

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.REQUIRES_REVIEW
    assert "tool_adoption_without_evaluation" in _rule_ids(result)


def test_action_outside_scope_blocks_baseline():
    state = _valid_state()
    command = build_mission_command(state, "rewrite_production_database", "jarvis")

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.BLOCKED
    assert "action_outside_mission_scope" in _rule_ids(result)


def test_public_ai_content_needs_human_review_before_publication():
    envelope = _valid_envelope(allowed_actions=["publish_ai_post"], requires_approval_actions=[])
    state = _valid_state(envelope=envelope)
    command = build_mission_command(
        state,
        "publish_ai_post",
        "jarvis",
        inputs={"content_type": "public AI generated LinkedIn post"},
    )

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision in {
        MissionSafetyBaselineDecision.REQUIRES_REVIEW,
        MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL,
    }
    assert "public_ai_content_needs_review" in _rule_ids(result)


def test_deceptive_impersonation_or_deepfake_is_denied():
    envelope = _valid_envelope(allowed_actions=["clone_voice_deepfake"])
    state = _valid_state(envelope=envelope)
    command = build_mission_command(
        state,
        "clone_voice_deepfake",
        "jarvis",
        inputs={"intent": "fake endorsement"},
    )

    result = evaluate_mission_safety_baseline(state, command)

    assert result.decision == MissionSafetyBaselineDecision.DENIED
    assert result.risk_level == MissionDryRunRiskLevel.CRITICAL
    assert "deceptive_impersonation_or_deepfake" in _rule_ids(result)
