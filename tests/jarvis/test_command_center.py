import pytest

from jarvis.command_center import (
    ApprovalQueueView,
    AuditTimelineView,
    CommandCenterViewModel,
    DeviceStatusView,
    HermesPayloadView,
    MissionDashboardView,
    RiskAndBudgetPanelView,
    SafetyIndicatorView,
    VoiceCameraControlsView,
    build_command_center_view_model,
)
from jarvis.missions.approval_bridge import build_approval_bridge_payload
from jarvis.missions.approval_request import build_approval_request
from jarvis.missions.audit_log import MissionAuditEventType, MissionAuditOutcome, MissionAuditRiskLevel, build_audit_event
from jarvis.missions.budget_guard import MissionBudgetGuardDecision, MissionBudgetGuardResult
from jarvis.missions.command_builder import build_mission_command
from jarvis.missions.dry_run import evaluate_mission_command_dry_run
from jarvis.missions.envelope import MissionEnvelope
from jarvis.missions.hermes_bridge import (
    HermesAgentDescriptor,
    HermesAgentRiskLevel,
    build_hermes_command_payload,
)
from jarvis.missions.state_store import MissionState, MissionStatus, add_approval_request, add_audit_event
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.voice.companion import VoiceCompanionStatus


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


def _budget_result(**overrides):
    data = {
        "result_id": "budget-1",
        "mission_id": "mission-1",
        "decision": MissionBudgetGuardDecision.REQUIRES_APPROVAL,
        "can_spend": False,
        "cost_summary": {"budget_limit": 50.0, "proposed_cost": 12.0},
        "violations": ["spending requires approval"],
        "budget_remaining": None,
        "audit_summary": "budget prepared",
        "created_at": "2026-05-28T10:00:00+00:00",
    }
    data.update(overrides)
    return MissionBudgetGuardResult(**data)


def test_command_center_view_model_round_trips_without_runtime_capabilities():
    state = _state()
    approval_request = build_approval_request(
        state.envelope,
        "file_write",
        "jarvis",
        request_id="approval-1",
        created_at="2026-05-28T10:00:00+00:00",
    )
    state = add_approval_request(state, approval_request)
    event = build_audit_event(
        "mission-1",
        MissionAuditEventType.APPROVAL_REQUESTED,
        "jarvis",
        "Approval requested for file_write.",
        event_id="event-1",
        created_at="2026-05-28T10:01:00+00:00",
        outcome=MissionAuditOutcome.REQUIRES_APPROVAL,
        risk_level=MissionAuditRiskLevel.MEDIUM,
    )
    state = add_audit_event(state, event)
    command = build_mission_command(state, "file_write", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)
    approval_payload = build_approval_bridge_payload(state, command, evaluation)
    hermes_payload = build_hermes_command_payload(state, command, evaluation, approval_payload)
    agent = HermesAgentDescriptor(
        agent_id="agent-1",
        name="Research Agent",
        role="prepare research",
        capabilities=["summarize"],
        allowed_tools=["local_editor"],
        risk_level=HermesAgentRiskLevel.LOW,
        requires_approval=False,
    )

    view = build_command_center_view_model(
        view_id="view-1",
        generated_at="2026-05-28T10:02:00+00:00",
        mission_states=[state],
        approval_payloads=[approval_payload],
        hermes_payloads=[hermes_payload],
        agent_descriptors=[agent],
        budget_results=[_budget_result()],
        metadata={"source": "test"},
    )
    restored = CommandCenterViewModel.from_dict(view.to_dict())

    restored_data = restored.to_dict()
    view_data = view.to_dict()
    assert {key: value for key, value in restored_data.items() if key != "safety_indicator"} == {
        key: value for key, value in view_data.items() if key != "safety_indicator"
    }
    assert restored.safety_indicator.approval_gateway_required is True
    assert restored.safety_indicator.policy_engine_boundary
    assert view.status.value == "needs_attention"
    assert view.safety_indicator.approval_gateway_required is True
    assert view.safety_indicator.policy_engine_boundary
    assert view.approvals
    assert all("can_approve_from_view" not in item.to_dict() for item in view.approvals)
    assert all("can_reject_from_view" not in item.to_dict() for item in view.approvals)
    assert view.hermes_payloads[0].dry_run_only is True
    assert view.hermes_payloads[0].can_execute_now is False
    assert view.metadata["approval_gateway_called"] is False
    assert view.metadata["hermes_connected"] is False


def test_builder_does_not_call_approval_gateway_or_hermes(monkeypatch):
    state = _state()

    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by Command Center views")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter must not be called by Command Center views")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)

    view = build_command_center_view_model(
        view_id="view-1",
        generated_at="2026-05-28T10:02:00+00:00",
        mission_states=[state],
    )

    assert view.status.value == "ready"
    assert view.metadata["prepare_only"] is True


def test_failed_mission_does_not_produce_ready_command_center_status():
    state = _state(status=MissionStatus.FAILED, last_error="Mission failed during prepare-only validation.")

    view = build_command_center_view_model(
        view_id="view-failed",
        generated_at="2026-05-28T10:02:00+00:00",
        mission_states=[state],
    )
    data = view.to_dict()

    assert data["status"] != "ready"
    assert data["status"] == "blocked"
    assert data["safety_indicator"]["status"] == "blocked"
    assert data["missions"][0]["last_error"] == "Mission failed during prepare-only validation."
    assert data["metadata"]["prepare_only"] is True
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False
    assert data["metadata"]["approval_gateway_called"] is False


@pytest.mark.parametrize(
    "state,action",
    [
        (_state(), "spam"),
        (_state(status=MissionStatus.BLOCKED, last_error="Mission is blocked."), "research"),
    ],
)
def test_denied_or_blocked_approval_bridge_payload_is_preserved_as_blocking_signal(state, action):
    command = build_mission_command(state, action, "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)
    approval_payload = build_approval_bridge_payload(state, command, evaluation)

    view = build_command_center_view_model(
        view_id="view-denied-approval",
        generated_at="2026-05-28T10:02:00+00:00",
        approval_payloads=[approval_payload],
    )
    data = view.to_dict()

    assert data["approvals"]
    assert data["approvals"][0]["approval_level"] == "denied"
    assert data["status"] == "blocked"
    assert data["status"] != "ready"
    assert data["safety_indicator"]["status"] == "blocked"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert "can_approve_from_view" not in data["approvals"][0]
    assert "can_reject_from_view" not in data["approvals"][0]
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["approve_reject_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False
    assert data["metadata"]["approval_gateway_called"] is False


def test_blocked_budget_result_makes_command_center_non_ready():
    view = build_command_center_view_model(
        view_id="view-budget-blocked",
        generated_at="2026-05-28T10:02:00+00:00",
        mission_states=[_state()],
        budget_results=[_budget_result(decision=MissionBudgetGuardDecision.BLOCKED, violations=["budget blocked"])],
    )
    data = view.to_dict()

    assert data["status"] == "blocked"
    assert data["status"] != "ready"
    assert data["safety_indicator"]["status"] == "blocked"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["approve_reject_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False
    assert data["metadata"]["approval_gateway_called"] is False


def test_requires_approval_budget_result_makes_command_center_need_attention():
    view = build_command_center_view_model(
        view_id="view-budget-approval",
        generated_at="2026-05-28T10:02:00+00:00",
        mission_states=[_state()],
        budget_results=[_budget_result(decision=MissionBudgetGuardDecision.REQUIRES_APPROVAL)],
    )
    data = view.to_dict()

    assert data["status"] == "needs_attention"
    assert data["status"] != "ready"
    assert data["safety_indicator"]["status"] == "needs_attention"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False


def test_allowed_budget_result_does_not_force_non_ready_status():
    view = build_command_center_view_model(
        view_id="view-budget-allowed",
        generated_at="2026-05-28T10:02:00+00:00",
        mission_states=[_state()],
        budget_results=[_budget_result(decision=MissionBudgetGuardDecision.ALLOWED, violations=[])],
    )
    data = view.to_dict()

    assert data["status"] == "ready"
    assert data["safety_indicator"]["approval_gateway_required"] is False
    assert data["metadata"]["execution_enabled"] is False


def test_approval_queue_from_request_redacts_sensitive_action_reason_and_scope():
    request = build_approval_request(
        _envelope(),
        "read .env with Bearer token",
        "jarvis",
        request_id="approval-sensitive",
        reason="Contains api key material.",
        scope=["authorization header", "safe-scope"],
        created_at="2026-05-28T10:00:00+00:00",
    )

    data = ApprovalQueueView.from_approval_request(request).to_dict()

    assert data["action"] == "[redacted sensitive approval action]"
    assert data["reason"] == "[redacted sensitive approval reason]"
    assert data["scope"] == ["[redacted sensitive approval scope]", "safe-scope"]


def test_approval_queue_from_bridge_payload_redacts_sensitive_text():
    state = _state()
    command = build_mission_command(state, "file_write", "jarvis")
    evaluation = evaluate_mission_command_dry_run(state, command)
    approval_payload = build_approval_bridge_payload(
        state,
        command,
        evaluation,
        reason="client secret appears in request",
    )
    approval_payload.action = "use Bearer value"
    approval_payload.scope = ["private key path", "file_write"]

    data = ApprovalQueueView.from_bridge_payload(approval_payload).to_dict()

    assert data["action"] == "[redacted sensitive approval action]"
    assert data["reason"] == "[redacted sensitive approval reason]"
    assert data["scope"] == ["[redacted sensitive approval scope]", "file_write"]


def test_hermes_payload_view_redacts_inputs_and_metadata():
    state = _state()
    command = build_mission_command(state, "research", "jarvis", inputs={"query": "niche"})
    payload = build_hermes_command_payload(state, command, metadata={"source": "test"})

    view = HermesPayloadView.from_hermes_payload(payload)
    data = view.to_dict()

    assert "inputs" not in data
    assert "metadata" not in data
    assert data["redacted_fields"] == ["inputs", "metadata"]
    assert data["can_execute_now"] is False


def test_placeholder_controls_cannot_enable_capture_or_device_approvals():
    with pytest.raises(ValueError, match="cannot start capture"):
        VoiceCameraControlsView(can_start_voice=True)

    with pytest.raises(ValueError, match="cannot start capture"):
        VoiceCameraControlsView(voice_companion_status=VoiceCompanionStatus(voice_available=True))

    with pytest.raises(ValueError, match="cannot enable approvals"):
        DeviceStatusView(device_id="phone", label="Phone", approval_capable=True)


def test_voice_camera_controls_include_prepare_only_voice_companion_status():
    data = VoiceCameraControlsView.placeholder().to_dict()

    assert data["voice_status"] == "placeholder"
    assert data["camera_status"] == "placeholder"
    assert data["can_start_voice"] is False
    assert data["can_start_camera"] is False
    assert data["can_record"] is False
    assert data["voice_companion_status"] == {
        "prepare_only": True,
        "voice_available": False,
        "microphone_enabled": False,
        "wake_word_enabled": False,
        "recording_enabled": False,
        "streaming_enabled": False,
        "auto_start_enabled": False,
        "execution_enabled": False,
        "approval_required_for_sensitive_actions": True,
    }


def test_risk_budget_panel_cannot_enable_spending():
    with pytest.raises(ValueError, match="cannot enable spending"):
        RiskAndBudgetPanelView(
            mission_id="mission-1",
            risk_level="medium",
            budget_limit=50.0,
            cost_limit_per_action=10.0,
            can_spend=True,
        )


def test_command_center_metadata_rejects_secret_like_keys():
    with pytest.raises(ValueError, match="metadata cannot include secret-like"):
        CommandCenterViewModel(
            view_id="view-1",
            generated_at="2026-05-28T10:02:00+00:00",
            status="ready",
            metadata={"api_key": "redacted"},
        )


def test_approval_queue_from_dict_drops_approve_reject_capability_flags():
    view = ApprovalQueueView.from_dict(
        {
            "item_id": "approval-1",
            "mission_id": "mission-1",
            "action": "file_write",
            "approval_level": "requires_approval",
            "risk_level": "medium",
            "reason": "Needs approval.",
            "scope": ["file_write"],
            "challenge_required": False,
            "can_approve_from_view": True,
            "can_reject_from_view": True,
        }
    )

    data = view.to_dict()

    assert "can_approve_from_view" not in data
    assert "can_reject_from_view" not in data


def test_approval_queue_from_dict_redacts_sensitive_text():
    view = ApprovalQueueView.from_dict(
        {
            "item_id": "approval-sensitive",
            "mission_id": "mission-1",
            "action": "read .env file",
            "approval_level": "requires_approval",
            "risk_level": "medium",
            "reason": "needs api key",
            "scope": ["authorization header", "private key"],
        }
    )

    data = view.to_dict()

    assert data["action"] == "[redacted sensitive approval action]"
    assert data["reason"] == "[redacted sensitive approval reason]"
    assert data["scope"] == ["[redacted sensitive approval scope]", "[redacted sensitive approval scope]"]


@pytest.mark.parametrize("challenge_required", [None, False])
def test_strong_approval_from_dict_forces_challenge_required(challenge_required):
    payload = {
        "item_id": "approval-strong",
        "mission_id": "mission-1",
        "action": "deploy",
        "approval_level": "strong_approval",
        "risk_level": "high",
        "reason": "Strong approval is required.",
        "scope": ["deploy"],
        "can_approve_from_view": True,
        "can_reject_from_view": True,
    }
    if challenge_required is not None:
        payload["challenge_required"] = challenge_required

    view = ApprovalQueueView.from_dict(payload)
    data = view.to_dict()

    assert data["challenge_required"] is True
    assert "can_approve_from_view" not in data
    assert "can_reject_from_view" not in data


def test_caller_metadata_cannot_override_safety_invariants():
    view = build_command_center_view_model(
        view_id="view-1",
        generated_at="2026-05-28T10:02:00+00:00",
        metadata={
            "prepare_only": False,
            "approval_gateway_called": True,
            "hermes_connected": True,
            "execution_enabled": True,
            "approval_enabled": True,
            "approve_reject_enabled": True,
            "runtime_connected": True,
            "source": "test",
        },
    )

    assert view.metadata["source"] == "test"
    assert view.metadata["prepare_only"] is True
    assert view.metadata["approval_gateway_called"] is False
    assert view.metadata["hermes_connected"] is False
    assert view.metadata["execution_enabled"] is False
    assert view.metadata["approval_enabled"] is False
    assert view.metadata["approve_reject_enabled"] is False
    assert view.metadata["runtime_connected"] is False


def test_sensitive_audit_summary_is_redacted_for_ui_output():
    event = build_audit_event(
        "mission-1",
        MissionAuditEventType.NOTE_RECORDED,
        "jarvis",
        "User pasted token-like sensitive text.",
        event_id="event-sensitive",
        created_at="2026-05-28T10:01:00+00:00",
        outcome=MissionAuditOutcome.RECORDED,
        risk_level=MissionAuditRiskLevel.HIGH,
        sensitive=True,
    )

    view = AuditTimelineView.from_audit_event(event)
    restored = AuditTimelineView.from_dict({**view.to_dict(), "summary": "leaked token text"})
    redacted_by_field = AuditTimelineView.from_dict(
        {
            "event_id": "event-redacted",
            "mission_id": "mission-1",
            "event_type": "note_recorded",
            "summary": "private business detail",
            "created_at": "2026-05-28T10:01:00+00:00",
            "outcome": "recorded",
            "risk_level": "high",
            "sensitive": False,
            "redacted_fields": ["summary"],
        }
    )

    assert view.to_dict()["summary"] == "[redacted sensitive audit summary]"
    assert "summary" in view.to_dict()["redacted_fields"]
    assert restored.to_dict()["summary"] == "[redacted sensitive audit summary]"
    assert redacted_by_field.to_dict()["summary"] == "[redacted sensitive audit summary]"


def test_hermes_payload_view_redacts_secret_like_action_and_blocked_reason():
    view = HermesPayloadView(
        payload_id="payload-1",
        mission_id="mission-1",
        command_id="command-1",
        action="read .env and use token",
        status="blocked",
        dry_run_only=True,
        can_execute_now=False,
        approval_level="denied",
        allowed_tool_count=0,
        candidate_tool_count=0,
        blocked_reason="blocked because password value appeared",
    )
    restored = HermesPayloadView.from_dict(
        {
            **view.to_dict(),
            "action": "upload .env",
            "blocked_reason": "contains api_key",
        }
    )

    assert view.to_dict()["action"] == "[redacted sensitive action]"
    assert view.to_dict()["blocked_reason"] == "[redacted sensitive blocked reason]"
    assert "action" in view.to_dict()["redacted_fields"]
    assert "blocked_reason" in view.to_dict()["redacted_fields"]
    assert restored.to_dict()["action"] == "[redacted sensitive action]"
    assert restored.to_dict()["blocked_reason"] == "[redacted sensitive blocked reason]"


@pytest.mark.parametrize(
    "marker",
    [
        "Bearer abc",
        "Authorization: abc",
        "api key abc",
        "credentials abc",
        "client secret abc",
        "private key abc",
    ],
)
def test_hermes_payload_view_redacts_common_sensitive_markers(marker):
    view = HermesPayloadView(
        payload_id="payload-1",
        mission_id="mission-1",
        command_id="command-1",
        action=f"prepare request with {marker}",
        status="blocked",
        dry_run_only=True,
        can_execute_now=False,
        approval_level="denied",
        allowed_tool_count=0,
        candidate_tool_count=0,
        blocked_reason=f"blocked because {marker} appeared",
    )

    assert view.to_dict()["action"] == "[redacted sensitive action]"
    assert view.to_dict()["blocked_reason"] == "[redacted sensitive blocked reason]"


def test_safety_indicator_from_dict_is_conservative():
    view = SafetyIndicatorView.from_dict(
        {
            "status": "ready",
            "approval_gateway_required": False,
            "strong_approval_required": False,
            "policy_engine_boundary": "Everything is safe; no gateway needed.",
            "notes": ["caller-provided"],
        }
    )

    data = view.to_dict()

    assert data["status"] == "needs_attention"
    assert data["approval_gateway_required"] is True
    assert "Everything is safe" not in data["policy_engine_boundary"]
    assert "deserialized safety indicator is conservative" in data["notes"]


def test_command_center_from_dict_enforces_prepare_only_invariants():
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-1",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
            "approvals": [
                {
                    "item_id": "approval-1",
                    "mission_id": "mission-1",
                    "action": "file_write",
                    "approval_level": "requires_approval",
                    "risk_level": "medium",
                    "reason": "Needs approval.",
                    "scope": ["file_write"],
                    "can_approve_from_view": True,
                    "can_reject_from_view": True,
                }
            ],
            "metadata": {
                "prepare_only": False,
                "approval_gateway_called": True,
                "hermes_connected": True,
                "execution_enabled": True,
                "approval_enabled": True,
                "approve_reject_enabled": True,
                "runtime_connected": True,
            },
        }
    )

    data = view.to_dict()

    assert "can_approve_from_view" not in data["approvals"][0]
    assert "can_reject_from_view" not in data["approvals"][0]
    assert data["metadata"]["prepare_only"] is True
    assert data["metadata"]["approval_gateway_called"] is False
    assert data["metadata"]["hermes_connected"] is False
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["approve_reject_enabled"] is False
    assert data["metadata"]["runtime_connected"] is False
    assert data["safety_indicator"]["status"] == "needs_attention"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert "approve" in data["safety_indicator"]["policy_engine_boundary"]


def test_command_center_from_dict_missing_safety_indicator_with_pending_approval_is_conservative():
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-legacy",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
            "approvals": [
                {
                    "item_id": "approval-1",
                    "mission_id": "mission-1",
                    "action": "file_write",
                    "approval_level": "requires_approval",
                    "risk_level": "medium",
                    "reason": "Needs approval.",
                    "scope": ["file_write"],
                    "can_approve_from_view": True,
                    "can_reject_from_view": True,
                }
            ],
            "metadata": {
                "prepare_only": False,
                "approval_gateway_called": True,
                "hermes_connected": True,
                "execution_enabled": True,
            },
        }
    )

    data = view.to_dict()

    assert data["safety_indicator"]["status"] != "ready"
    assert data["safety_indicator"]["status"] == "needs_attention"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert data["safety_indicator"]["policy_engine_boundary"]
    assert "safety_indicator missing; deserialized conservatively" in data["safety_indicator"]["notes"]
    assert "can_approve_from_view" not in data["approvals"][0]
    assert "can_reject_from_view" not in data["approvals"][0]
    assert data["metadata"]["prepare_only"] is True
    assert data["metadata"]["approval_gateway_called"] is False
    assert data["metadata"]["hermes_connected"] is False
    assert data["metadata"]["execution_enabled"] is False


def test_command_center_from_dict_recomputes_ready_status_with_pending_approvals():
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-pending",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
            "approvals": [
                {
                    "item_id": "approval-1",
                    "mission_id": "mission-1",
                    "action": "file_write",
                    "approval_level": "requires_approval",
                    "risk_level": "medium",
                    "reason": "Needs approval.",
                    "scope": ["file_write"],
                }
            ],
        }
    )
    data = view.to_dict()

    assert data["status"] == "needs_attention"
    assert data["status"] != "ready"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False


def test_command_center_from_dict_recomputes_ready_status_with_blocked_hermes_payload():
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-blocked-payload",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
            "hermes_payloads": [
                {
                    "payload_id": "payload-1",
                    "mission_id": "mission-1",
                    "command_id": "command-1",
                    "action": "research",
                    "status": "blocked",
                    "dry_run_only": True,
                    "can_execute_now": False,
                    "approval_level": "denied",
                    "allowed_tool_count": 0,
                    "candidate_tool_count": 0,
                    "blocked_reason": "blocked by policy",
                }
            ],
        }
    )
    data = view.to_dict()

    assert data["status"] == "blocked"
    assert data["status"] != "ready"
    assert data["hermes_payloads"][0]["can_execute_now"] is False
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False


def test_command_center_from_dict_upgrades_stale_safety_indicator_when_aggregate_is_blocked():
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-blocked-stale-safety",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
            "missions": [
                {
                    "mission_id": "mission-1",
                    "objective": "Create a reviewable asset",
                    "status": "blocked",
                    "success_metric": "Draft prepared",
                    "pending_approvals": 0,
                    "audit_event_count": 0,
                    "risk_level": "high",
                    "last_error": "Mission is blocked.",
                }
            ],
            "safety_indicator": {
                "status": "needs_attention",
                "approval_gateway_required": False,
                "strong_approval_required": False,
                "policy_engine_boundary": "Serialized stale boundary.",
            },
        }
    )
    data = view.to_dict()

    assert data["status"] == "blocked"
    assert data["safety_indicator"]["status"] == "blocked"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert data["metadata"]["prepare_only"] is True
    assert data["metadata"]["approval_gateway_called"] is False
    assert data["metadata"]["hermes_connected"] is False
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False


@pytest.mark.parametrize(
    "budget_decision,expected_status",
    [
        ("blocked", "blocked"),
        ("requires_approval", "needs_attention"),
    ],
)
def test_command_center_from_dict_recomputes_ready_status_from_budget_panels(budget_decision, expected_status):
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-budget-legacy",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
            "risk_budget_panels": [
                {
                    "mission_id": "mission-1",
                    "risk_level": "medium",
                    "budget_limit": 50.0,
                    "cost_limit_per_action": 10.0,
                    "budget_decision": budget_decision,
                    "can_spend": False,
                    "violations": ["budget issue"],
                }
            ],
        }
    )
    data = view.to_dict()

    assert data["status"] == expected_status
    assert data["status"] != "ready"
    assert data["safety_indicator"]["approval_gateway_required"] is True
    assert data["metadata"]["execution_enabled"] is False
    assert data["metadata"]["approval_enabled"] is False
    assert data["metadata"]["hermes_connected"] is False


@pytest.mark.parametrize(
    "last_error",
    [
        "Read failed while opening .env",
        "Authorization failed for Bearer token abc123",
    ],
)
def test_mission_dashboard_redacts_sensitive_last_error_markers(last_error):
    view = MissionDashboardView(
        mission_id="mission-1",
        objective="Create a reviewable asset",
        status=MissionStatus.FAILED,
        success_metric="Draft prepared",
        risk_level="high",
        last_error=last_error,
    )

    assert view.to_dict()["last_error"] == "[redacted sensitive mission error]"


def test_mission_dashboard_keeps_safe_last_error_visible():
    view = MissionDashboardView(
        mission_id="mission-1",
        objective="Create a reviewable asset",
        status=MissionStatus.FAILED,
        success_metric="Draft prepared",
        risk_level="high",
        last_error="Mission failed during prepare-only validation.",
    )

    assert view.to_dict()["last_error"] == "Mission failed during prepare-only validation."


def test_command_center_from_dict_missing_devices_preserves_placeholder():
    view = CommandCenterViewModel.from_dict(
        {
            "view_id": "view-legacy",
            "generated_at": "2026-05-28T10:02:00+00:00",
            "status": "ready",
        }
    )

    data = view.to_dict()

    assert data["devices"] == [
        {
            "device_id": "device-placeholder",
            "label": "Device runtime not connected",
            "trusted": False,
            "online": False,
            "approval_capable": False,
            "status": "placeholder",
        }
    ]
