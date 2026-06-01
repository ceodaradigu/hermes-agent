from copy import deepcopy

from jarvis.missions.approval_bridge import MissionApprovalBridgeDecision, MissionApprovalBridgePayload
from jarvis.missions.approval_hardening import (
    MissionApprovalHardeningDecision,
    MissionApprovalHardeningResult,
    harden_approval_bridge_payload,
)
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.dry_run import MissionDryRunRiskLevel


def _payload(**overrides):
    data = {
        "payload_id": "payload-1",
        "mission_id": "mission-1",
        "command_id": "command-1",
        "evaluation_id": "evaluation-1",
        "action": "deploy landing",
        "decision": MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL,
        "approval_level": MissionApprovalLevel.STRONG_APPROVAL,
        "risk_level": MissionDryRunRiskLevel.HIGH,
        "requested_by": "jarvis",
        "reason": "Needs strong approval.",
        "scope": ["deploy landing"],
        "policy_notes": ["Bridge only."],
        "audit_summary": "Bridge payload prepared.",
        "challenge_required": True,
        "strong_approval_required": True,
        "created_at": "2026-05-28T10:00:00+00:00",
        "expires_at": "2026-05-28T10:05:00+00:00",
        "metadata": {"rollback_plan": "revert deployment"},
    }
    data.update(overrides)
    return MissionApprovalBridgePayload(**data)


def test_strong_approval_without_challenge_fails():
    payload = _payload()
    payload.challenge_required = False

    result = harden_approval_bridge_payload(payload)

    assert result.decision == MissionApprovalHardeningDecision.BLOCKED
    assert "strong approval requires challenge_required=true" in result.errors


def test_strong_approval_with_empty_scope_fails():
    payload = _payload()
    payload.scope = []

    result = harden_approval_bridge_payload(payload)

    assert result.decision == MissionApprovalHardeningDecision.BLOCKED
    assert "strong approval requires non-empty scope" in result.errors


def test_approve_all_forever_is_blocked_after_payload_mutation():
    payload = _payload()
    payload.metadata["policy"] = "approve_all_forever"

    result = harden_approval_bridge_payload(payload)

    assert result.decision == MissionApprovalHardeningDecision.BLOCKED
    assert "approve-all-forever or blanket approval language is blocked" in result.errors


def test_deploy_or_publication_without_rollback_is_blocked():
    payload = _payload(metadata={})

    result = harden_approval_bridge_payload(payload)

    assert result.decision == MissionApprovalHardeningDecision.BLOCKED
    assert "deploy, production, or publication payload requires rollback_plan or blocked_reason" in result.errors


def test_payload_with_cost_requires_max_cost():
    payload = _payload(metadata={"rollback_plan": "revert", "projected_cost": 12.0})

    result = harden_approval_bridge_payload(payload)

    assert result.decision == MissionApprovalHardeningDecision.BLOCKED
    assert "payload with cost requires max_cost or cost_limit" in result.errors


def test_hardening_does_not_mutate_payload_and_round_trips():
    payload = _payload()
    before = deepcopy(payload.to_dict())

    result = harden_approval_bridge_payload(payload)
    restored = MissionApprovalHardeningResult.from_dict(result.to_dict())

    assert payload.to_dict() == before
    assert result.is_valid is True
    assert restored.to_dict() == result.to_dict()
    assert result.metadata["approval_gateway_called"] is False
