import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.advanced_personalization.foundation import (
    AdvancedPersonalizationStatus,
    BusinessGoalModelPreview,
    ContrarianModeProfilePreview,
    DecisionModelPreview,
    MemoryAuditReversalPreview,
    MemoryLifecyclePreview,
    MemoryProposalPreview,
    MemoryReviewPreview,
    PersonalizationApprovalRequirements,
    PersonalizationRecommendationPreview,
    SensitiveInferenceGuardPreview,
    SpeechStylePatternPreview,
    UncertaintyHandlingPreview,
    UserModelSafetyPolicy,
    UserPreferenceProfilePreview,
)
from jarvis.api.app import PersonalizationPreviewRequest, create_app
from jarvis.operator_console import OperatorConsoleCapabilityMatrix, OperatorConsoleSnapshot


POST_ROUTES = (
    "/personalization/preference-profile",
    "/personalization/speech-style",
    "/personalization/decision-model",
    "/personalization/business-goal",
    "/personalization/contrarian-mode",
    "/personalization/memory-proposal",
    "/personalization/memory-review",
    "/personalization/memory-lifecycle",
    "/personalization/memory-audit-reversal",
    "/personalization/uncertainty",
    "/personalization/recommendation",
    "/personalization/sensitive-inference-guard",
    "/personalization/approval-requirements",
)

DANGEROUS_ROUTES = (
    "/personalization/save-memory",
    "/personalization/activate-memory",
    "/personalization/deactivate-memory",
    "/personalization/delete-memory",
    "/personalization/learn",
    "/personalization/auto-learn",
    "/personalization/authorize-action",
    "/personalization/infer-sensitive",
    "/personalization/read-private-source",
)

STATUS_FALSE_FIELDS = (
    "advanced_personalization_available",
    "user_model_available",
    "opaque_learning_enabled",
    "automatic_memory_enabled",
    "memory_write_enabled",
    "memory_activation_enabled",
    "memory_deactivation_enabled",
    "sensitive_inference_enabled",
    "manipulation_enabled",
    "action_authorization_from_memory_enabled",
    "private_certainty_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "hermes_called",
    "approval_gateway_called",
    "execution_enabled",
    "persistence_enabled",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by personalization previews")


def _app():
    return create_app(adapter_factory=FailAdapter)


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path):
    return _endpoint(app, path, "GET")()


def _post(app, path, data):
    return _endpoint(app, path, "POST")(PersonalizationPreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/personalization/status")
    payload = route.endpoint()

    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for field in STATUS_FALSE_FIELDS:
        assert payload[field] is False


def test_policy_is_default_deny_reviewable_reversible_audited_and_uncertain():
    payload = _get(_app(), "/personalization/policy")

    assert payload["prepare_only"] is True
    assert all(payload.values())
    assert payload["no_memory_as_permission"] is True
    assert payload["explicit_memory_proposals_required"] is True
    assert payload["review_required_before_memory_activation"] is True
    assert payload["reversible_memory_required"] is True
    assert payload["audit_required"] is True
    assert payload["uncertainty_required"] is True
    assert payload["strong_approval_required_for_sensitive_memory"] is True
    assert payload["strong_approval_required_for_actions_based_on_personalization"] is True


def test_preference_profile_preserves_evidence_uncertainty_and_never_stores_or_activates():
    payload = _post(_app(), "/personalization/preference-profile", {
        "preference_name": "Concise answers",
        "preference_type": "format",
        "evidence_preview": ["Explicitly requested concise output"],
        "confidence": "medium",
        "uncertainty_notes": ["May vary by task"],
    })

    assert payload["preference_type"] == "format"
    assert payload["evidence_preview"]
    assert payload["uncertainty_notes"]
    assert payload["would_store_memory"] is False
    assert payload["would_activate_memory"] is False
    assert payload["approval_required"] is True
    assert payload["sensitive_inference_made"] is False


def test_speech_style_never_claims_identity_stores_or_adapts_without_approval():
    payload = _post(_app(), "/personalization/speech-style", {
        "pattern_name": "Direct phrasing",
        "observed_style_preview": "Short imperative requests",
        "preferred_response_style": "Direct",
    })

    assert payload["no_identity_claim"] is True
    assert payload["would_store_memory"] is False
    assert payload["would_adapt_response_only"] is False
    assert payload["approval_required"] is True


def test_decision_model_never_manipulates_stores_or_authorizes_action():
    payload = _post(_app(), "/personalization/decision-model", {
        "decision_axis": "speed versus certainty",
        "observed_preference": "Prefer reviewed evidence",
        "contrarian_needed": True,
    })

    assert payload["contrarian_needed"] is True
    assert payload["no_manipulation"] is True
    assert payload["would_store_memory"] is False
    assert payload["would_authorize_action"] is False
    assert payload["approval_required"] is True


def test_business_goal_never_invents_roi_or_confirmed_revenue():
    payload = _post(_app(), "/personalization/business-goal", {
        "goal_name": "Improve product sales",
        "goal_type": "revenue",
        "expected_value": "hypothesis only",
    })

    assert payload["goal_type"] == "revenue"
    assert payload["no_fake_roi"] is True
    assert payload["no_confirmed_revenue_without_evidence"] is True
    assert payload["would_store_memory"] is False
    assert payload["approval_required"] is True


def test_contrarian_mode_never_humiliates_manipulates_or_stores():
    payload = _post(_app(), "/personalization/contrarian-mode", {
        "contrarian_mode_requested": True,
        "allowed_pushback": ["Challenge unsupported assumptions"],
        "blocked_pushback": ["Humiliation"],
    })

    assert payload["contrarian_mode_requested"] is True
    assert payload["no_humiliation"] is True
    assert payload["no_manipulation"] is True
    assert payload["would_store_memory"] is False
    assert payload["approval_required"] is True


@pytest.mark.parametrize("sensitivity,strong", [("none", False), ("low", False), ("medium", True), ("high", True)])
def test_memory_proposal_is_reversible_never_stores_or_activates_and_escalates(sensitivity, strong):
    payload = _post(_app(), "/personalization/memory-proposal", {
        "proposal_id_preview": "proposal-preview-1",
        "proposed_memory": "Prefer concise output",
        "memory_category": "preference",
        "sensitivity_level": sensitivity,
    })

    assert payload["reversible"] is True
    assert payload["activation_required"] is False
    assert payload["would_store"] is False
    assert payload["would_activate"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is strong


def test_private_source_memory_proposal_requires_strong_approval():
    payload = _post(_app(), "/personalization/memory-proposal", {"private_source_requested": True})
    assert payload["strong_approval_required"] is True


def test_memory_review_never_approves_rejects_or_activates():
    payload = _post(_app(), "/personalization/memory-review", {
        "review_status": "needs_edit",
        "suggested_revision": "Narrow scope",
    })

    assert payload["review_status"] == "needs_edit"
    assert payload["would_approve"] is False
    assert payload["would_reject"] is False
    assert payload["would_activate"] is False


def test_memory_lifecycle_never_mutates_or_persists_and_requires_audit():
    payload = _post(_app(), "/personalization/memory-lifecycle", {
        "requested_action": "activate",
        "sensitivity_level": "high",
    })

    assert payload["requested_action"] == "activate"
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["audit_required"] is True
    for field in (
        "would_create_memory", "would_update_memory", "would_activate_memory",
        "would_deactivate_memory", "would_delete_memory", "would_persist",
    ):
        assert payload[field] is False


def test_memory_audit_reversal_is_available_but_never_performed():
    payload = _post(_app(), "/personalization/memory-audit-reversal", {
        "memory_id_preview": "memory-preview-1",
        "audit_reason": "User requested review",
    })

    assert payload["reversal_available"] is True
    assert payload["deactivation_available"] is True
    assert payload["deletion_available"] is False
    assert payload["would_reverse"] is False
    assert payload["would_deactivate"] is False
    assert payload["would_delete"] is False
    assert payload["would_persist"] is False


@pytest.mark.parametrize("confidence,must_ask", [("unknown", True), ("low", True), ("medium", False), ("high", False)])
def test_uncertainty_preserves_unknowns_and_never_claims_private_certainty(confidence, must_ask):
    payload = _post(_app(), "/personalization/uncertainty", {
        "claim_or_preference": "Prefers direct answers",
        "confidence": confidence,
        "unknowns": ["Whether preference applies to every task"],
        "assumptions": ["Based on provided request only"],
        "evidence_needed": ["Explicit confirmation"],
    })

    assert payload["unknowns"]
    assert payload["must_ask_user_before_using_as_fact"] is must_ask
    assert payload["no_private_certainty_claim"] is True
    assert payload["would_store_memory"] is False


def test_recommendation_never_manipulates_executes_stores_or_authorizes_action():
    payload = _post(_app(), "/personalization/recommendation", {
        "recommendation_name": "Prioritize reviewed offer",
        "recommendation_type": "monetization",
        "basis": ["Provided business goal"],
    })

    assert payload["no_manipulation"] is True
    assert payload["no_action_authorization"] is True
    assert payload["would_execute"] is False
    assert payload["would_store_memory"] is False


@pytest.mark.parametrize("risk,strong", [("none", False), ("low", False), ("medium", True), ("high", True)])
def test_sensitive_inference_guard_blocks_inference_and_escalates(risk, strong):
    payload = _post(_app(), "/personalization/sensitive-inference-guard", {
        "input_category": "provided text",
        "sensitive_attribute_risk": risk,
    })

    assert payload["requires_explicit_user_request"] is True
    assert payload["would_infer_sensitive_attribute"] is False
    assert payload["would_store_sensitive_memory"] is False
    assert payload["strong_approval_required"] is strong
    if risk in {"medium", "high"}:
        assert payload["blocked_inferences"]


@pytest.mark.parametrize(
    "risk",
    (
        "sensitive_memory_requested",
        "private_source_requested",
        "cross_context_requested",
        "action_based_on_personalization_requested",
        "private_data_requested",
        "sensitive_attribute_requested",
    ),
)
def test_approval_requirements_never_create_approval_or_authorize_and_escalate(risk):
    payload = _post(_app(), "/personalization/approval-requirements", {risk: True})

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False
    assert payload["memory_change_authorized"] is False
    assert payload["action_authorized"] is False


def test_all_preview_routes_are_local_pure_and_create_no_work(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Forbidden side effect was called")

    monkeypatch.setattr("jarvis.policy.approval_gateway.ApprovalGateway.create_request", fail)
    monkeypatch.setattr("jarvis.runtime.hermes_adapter.HermesRuntimeAdapter.run", fail, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail)
    monkeypatch.setattr("subprocess.run", fail)
    monkeypatch.setattr("subprocess.Popen", fail)
    monkeypatch.setattr("socket.create_connection", fail)

    app = _app()
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


def test_dangerous_routes_and_websocket_do_not_exist():
    app = _app()
    route_pairs = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    for path in DANGEROUS_ROUTES:
        assert (path, "POST") not in route_pairs
    assert not any(route.__class__.__name__ == "APIWebSocketRoute" for route in app.routes)


def test_foundation_source_has_no_io_network_shell_package_manager_or_env_access():
    source = Path("jarvis/advanced_personalization/foundation.py").read_text().lower()
    for forbidden in (
        "subprocess", "socket", "requests", "httpx", "urllib.request", "os.getenv", "os.environ",
        "dotenv", "open(", "read_text", "write_text", "pip install", "npm install",
    ):
        assert forbidden not in source


def test_sensitive_input_is_redacted_and_private_sources_are_not_read():
    payload = _post(_app(), "/personalization/memory-proposal", {
        "proposed_memory": "Read .env secret token",
        "evidence": ["private key"],
        "private_source_requested": True,
    })
    serialized = json.dumps(payload).lower()

    assert payload["strong_approval_required"] is True
    for forbidden in (".env", "secret token", "private key"):
        assert forbidden not in serialized


def test_command_center_and_operator_console_expose_prepare_only_markers_and_readiness():
    command_center = _get(_app(), "/command-center")
    snapshot = OperatorConsoleSnapshot.from_dict({}).to_dict()
    capabilities = OperatorConsoleCapabilityMatrix.from_dict({}).to_dict()

    assert command_center["metadata"]["advanced_personalization_user_model"] == "prepare_only"
    assert snapshot["metadata"]["advanced_personalization_user_model"] == "prepare_only"
    assert snapshot["advanced_personalization_status"]["prepare_only"] is True
    assert snapshot["advanced_personalization_status"]["memory_write_enabled"] is False
    assert snapshot["user_model_safety_policy"]["no_memory_as_permission"] is True
    assert snapshot["memory_proposal_readiness"]["would_store"] is False
    assert snapshot["memory_proposal_readiness"]["would_activate"] is False
    assert capabilities["read_advanced_personalization_status"] is True
    assert capabilities["read_user_model_safety_policy"] is True
    assert capabilities["preview_memory_proposal"] is True
    assert capabilities["execute_mission"] is False
    assert capabilities["call_hermes"] is False


def test_from_dict_and_serialization_cannot_enable_forbidden_capabilities():
    malicious = {
        "prepare_only": False,
        **{field: True for field in STATUS_FALSE_FIELDS},
        "would_store_memory": True,
        "would_activate_memory": True,
        "sensitive_inference_made": True,
        "would_adapt_response_only": True,
        "would_authorize_action": True,
        "activation_required": True,
        "would_store": True,
        "would_activate": True,
        "would_approve": True,
        "would_reject": True,
        "would_create_memory": True,
        "would_update_memory": True,
        "would_deactivate_memory": True,
        "would_delete_memory": True,
        "would_persist": True,
        "deletion_available": True,
        "would_reverse": True,
        "would_deactivate": True,
        "would_delete": True,
        "would_execute": True,
        "would_infer_sensitive_attribute": True,
        "would_store_sensitive_memory": True,
        "approval_gateway_called": True,
        "approval_created": True,
        "approval_granted": True,
        "approval_rejected": True,
        "memory_change_authorized": True,
        "action_authorized": True,
    }
    values = (
        AdvancedPersonalizationStatus.from_dict(malicious),
        UserPreferenceProfilePreview.from_dict(malicious),
        SpeechStylePatternPreview.from_dict(malicious),
        DecisionModelPreview.from_dict(malicious),
        BusinessGoalModelPreview.from_dict(malicious),
        ContrarianModeProfilePreview.from_dict(malicious),
        MemoryProposalPreview.from_dict(malicious),
        MemoryReviewPreview.from_dict(malicious),
        MemoryLifecyclePreview.from_dict(malicious),
        MemoryAuditReversalPreview.from_dict(malicious),
        UncertaintyHandlingPreview.from_dict(malicious),
        PersonalizationRecommendationPreview.from_dict(malicious),
        SensitiveInferenceGuardPreview.from_dict(malicious),
        PersonalizationApprovalRequirements.from_dict(malicious),
    )

    for value in values:
        payload = value.to_dict()
        assert payload["prepare_only"] is True
        for field in STATUS_FALSE_FIELDS:
            if field in payload:
                assert payload[field] is False
        for field in payload:
            if field.startswith("would_") or field in {
                "approval_gateway_called", "approval_created", "approval_granted", "approval_rejected",
                "memory_change_authorized", "action_authorized", "sensitive_inference_made",
                "activation_required", "deletion_available",
            }:
                assert payload[field] is False


def test_policy_from_dict_cannot_disable_safety_requirements():
    payload = UserModelSafetyPolicy.from_dict({
        name: False for name in UserModelSafetyPolicy.__dataclass_fields__
    }).to_dict()
    assert all(payload.values())
