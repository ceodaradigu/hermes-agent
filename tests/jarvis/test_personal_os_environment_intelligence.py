import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import PersonalOSPreviewRequest, create_app
from jarvis.operator_console import OperatorConsoleCapabilityMatrix, OperatorConsoleSnapshot
from jarvis.personal_os.foundation import (
    AttentionProtectionPreview,
    AwarenessSourcePreview,
    ContextSourceConsentPreview,
    ContextSwitchingPreview,
    DailyStatePreview,
    EnergyFocusSupportPreview,
    GuestModeContextPreview,
    LocalFilesScopePreview,
    PCEnvironmentStatePreview,
    PersonalOSApprovalRequirements,
    PersonalOSEnvironmentStatus,
    PersonalOSPrivacyPolicy,
    PersonalRoutinePreview,
    VisibleReasonAuditPreview,
)


POST_ROUTES = (
    "/personal-os/source-consent-preview",
    "/personal-os/daily-state",
    "/personal-os/pc-environment-state",
    "/personal-os/awareness-source-preview",
    "/personal-os/local-files-scope",
    "/personal-os/context-switch",
    "/personal-os/attention-protection",
    "/personal-os/personal-routine",
    "/personal-os/energy-focus-support",
    "/personal-os/guest-mode",
    "/personal-os/visible-reason-audit",
    "/personal-os/approval-requirements",
)

DANGEROUS_ROUTES = (
    "/personal-os/read-calendar",
    "/personal-os/read-email",
    "/personal-os/read-docs",
    "/personal-os/scan-files",
    "/personal-os/scan-pc",
    "/personal-os/capture-screen",
    "/personal-os/start-camera",
    "/personal-os/start-microphone",
    "/personal-os/send-notification",
    "/personal-os/send-email",
    "/personal-os/act",
)

STATUS_FALSE_FIELDS = (
    "personal_os_available",
    "environment_intelligence_available",
    "pc_state_awareness_enabled",
    "calendar_reading_enabled",
    "email_reading_enabled",
    "document_reading_enabled",
    "local_file_scanning_enabled",
    "context_crossing_enabled",
    "attention_notifications_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "sensitive_inference_enabled",
    "surveillance_enabled",
    "camera_enabled",
    "microphone_enabled",
    "screen_capture_enabled",
    "hermes_called",
    "approval_gateway_called",
    "execution_enabled",
    "persistence_enabled",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Personal OS previews")


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
    return _endpoint(app, path, "POST")(PersonalOSPreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/personal-os/status")
    payload = route.endpoint()

    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for field in STATUS_FALSE_FIELDS:
        assert payload[field] is False


def test_privacy_policy_is_default_deny_and_requires_strong_approval():
    payload = _get(_app(), "/personal-os/privacy-policy")

    assert payload["prepare_only"] is True
    assert all(payload.values())
    assert payload["consent_required_per_source"] is True
    assert payload["strong_approval_required_for_sensitive_sources"] is True
    assert payload["strong_approval_required_for_cross_context"] is True
    assert payload["strong_approval_required_for_sending_or_acting"] is True
    assert payload["strong_approval_required_for_camera_microphone_screen"] is True


def test_source_consent_preview_never_reads_stores_or_crosses_context():
    payload = _post(
        _app(),
        "/personal-os/source-consent-preview",
        {"source_name": "Work calendar", "source_type": "calendar", "access_requested": True},
    )

    assert payload["access_requested"] is True
    assert payload["would_read_source"] is False
    assert payload["would_store_data"] is False
    assert payload["would_cross_context"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["visible_reason"]


def test_daily_state_uses_only_provided_data_and_reads_no_private_sources():
    payload = _post(
        _app(),
        "/personal-os/daily-state",
        {"date": "2026-06-09", "priorities": ["Ship Phase Q"], "source_data": "provided"},
    )

    assert payload["priorities"] == ["Ship Phase Q"]
    assert payload["source_data"] == "provided"
    assert payload["no_external_calendar_read"] is True
    assert payload["no_email_read"] is True
    assert payload["no_doc_read"] is True
    assert payload["would_notify"] is False
    assert payload["would_execute"] is False
    assert payload["sensitive_inference_made"] is False


def test_pc_environment_preview_does_not_capture_scan_monitor_track_or_persist():
    payload = _post(
        _app(),
        "/personal-os/pc-environment-state",
        {"device_state_summary": "Provided by user", "environment_signals": ["quiet room"]},
    )

    assert payload["no_screen_capture"] is True
    assert payload["no_process_scan"] is True
    assert payload["no_file_scan"] is True
    assert payload["no_camera_or_microphone"] is True
    assert payload["would_monitor"] is False
    assert payload["would_track"] is False
    assert payload["would_persist"] is False


def test_awareness_preview_never_reads_calendar_email_docs_or_files():
    payload = _post(
        _app(),
        "/personal-os/awareness-source-preview",
        {
            "calendar_awareness_requested": True,
            "email_awareness_requested": True,
            "document_awareness_requested": True,
            "local_file_awareness_requested": True,
        },
    )

    assert payload["would_read_calendar"] is False
    assert payload["would_read_email"] is False
    assert payload["would_read_docs"] is False
    assert payload["would_scan_local_files"] is False
    assert payload["consent_required"] is True
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["data_minimization_required"] is True


def test_local_files_scope_never_scans_indexes_stores_or_exposes_secrets():
    payload = _post(
        _app(),
        "/personal-os/local-files-scope",
        {
            "scope_name": "review only",
            "allowed_paths_preview": ["provided/project"],
            "denied_paths_preview": [".env", "private"],
            "broad_scope_requested": True,
        },
    )

    assert payload["would_scan"] is False
    assert payload["would_index"] is False
    assert payload["would_store"] is False
    assert payload["secrets_blocked"] is True
    assert payload["private_paths_blocked"] is True
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert ".env" not in json.dumps(payload).lower()


def test_context_switch_preserves_personal_professional_boundary():
    payload = _post(
        _app(),
        "/personal-os/context-switch",
        {"current_context": "personal", "target_context": "professional", "cross_context_requested": True},
    )

    assert payload["would_switch"] is False
    assert payload["would_mix_contexts"] is False
    assert payload["professional_personal_separation_required"] is True
    assert payload["approval_required"] is True
    assert payload["visible_reason"]


def test_attention_protection_never_sends_notifications_or_changes_system():
    payload = _post(
        _app(),
        "/personal-os/attention-protection",
        {"notification_requested": True, "system_change_requested": True, "contact_people_requested": True},
    )

    assert payload["would_send_notifications"] is False
    assert payload["would_mute_apps"] is False
    assert payload["would_modify_system_settings"] is False
    assert payload["would_contact_people"] is False
    assert payload["strong_approval_required"] is True


def test_personal_routine_never_schedules_executes_notifies_or_persists():
    payload = _post(
        _app(),
        "/personal-os/personal-routine",
        {"routine_name": "Morning review", "routine_type": "morning", "steps_preview": ["Review priorities"]},
    )

    assert payload["routine_type"] == "morning"
    assert payload["would_schedule"] is False
    assert payload["would_execute"] is False
    assert payload["would_notify"] is False
    assert payload["would_persist"] is False
    assert payload["approval_required"] is True


def test_energy_focus_support_makes_no_medical_or_sensitive_inference():
    payload = _post(
        _app(),
        "/personal-os/energy-focus-support",
        {"energy_state": "low", "break_suggestion": "Take a short voluntary break"},
    )

    assert payload["energy_state"] == "low"
    assert payload["sensitive_health_inference_made"] is False
    assert payload["no_medical_conclusion"] is True
    assert payload["would_notify"] is False
    assert payload["would_execute"] is False


def test_guest_mode_blocks_memory_private_context_sensitive_sources_and_cross_context():
    payload = _post(_app(), "/personal-os/guest-mode", {})

    assert payload["guest_mode_enabled_preview"] is True
    assert payload["memory_disabled"] is True
    assert payload["personal_context_hidden"] is True
    assert payload["sensitive_sources_blocked"] is True
    assert payload["cross_context_blocked"] is True
    assert payload["would_persist"] is False
    assert payload["would_use_private_context"] is False


def test_visible_reason_audit_exposes_reason_sources_approvals_and_uncertainty():
    payload = _post(
        _app(),
        "/personal-os/visible-reason-audit",
        {
            "action_or_preview_name": "daily state",
            "visible_reason": "Protect focus using only provided data.",
            "data_sources_used": ["provided priorities"],
            "data_sources_blocked": ["calendar", "email"],
            "approvals_needed": ["calendar source approval"],
            "uncertainty_notes": ["No live context was read"],
        },
    )

    assert payload["visible_reason"]
    assert payload["data_sources_used"] == ["provided priorities"]
    assert payload["data_sources_blocked"] == ["calendar", "email"]
    assert payload["approvals_needed"] == ["calendar source approval"]
    assert payload["uncertainty_notes"] == ["No live context was read"]
    assert payload["no_hidden_reasoning_claim"] is True
    assert payload["audit_required"] is True
    assert payload["would_persist_audit"] is False


@pytest.mark.parametrize(
    "risk",
    (
        "sensitive_source_requested",
        "cross_context_requested",
        "sending_requested",
        "acting_requested",
        "camera_requested",
        "microphone_requested",
        "screen_requested",
        "external_account_requested",
        "private_files_requested",
    ),
)
def test_approval_requirements_never_create_approval_and_escalate_sensitive_risks(risk):
    payload = _post(_app(), "/personal-os/approval-requirements", {risk: True})

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False


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
    source = Path("jarvis/personal_os/foundation.py").read_text().lower()
    for forbidden in (
        "subprocess", "socket", "requests", "httpx", "urllib.request", "os.getenv", "os.environ",
        "dotenv", "open(", "read_text", "write_text", "pip install", "npm install", "calendar api",
        "gmail", "imap", "smtp",
    ):
        assert forbidden not in source


def test_command_center_and_operator_console_expose_prepare_only_markers():
    command_center = _get(_app(), "/command-center")
    snapshot = OperatorConsoleSnapshot.from_dict({}).to_dict()
    capabilities = OperatorConsoleCapabilityMatrix.from_dict({}).to_dict()

    assert command_center["metadata"]["personal_os_environment_intelligence"] == "prepare_only"
    assert snapshot["metadata"]["personal_os_environment_intelligence"] == "prepare_only"
    assert snapshot["personal_os_status"]["prepare_only"] is True
    assert snapshot["personal_os_privacy_policy"]["prepare_only"] is True
    assert capabilities["read_personal_os_status"] is True
    assert capabilities["read_personal_os_privacy_policy"] is True
    assert capabilities["preview_personal_os_context"] is True
    assert capabilities["execute_mission"] is False
    assert capabilities["call_hermes"] is False


def test_from_dict_and_serialization_cannot_enable_forbidden_capabilities():
    malicious = {
        "prepare_only": False,
        **{field: True for field in STATUS_FALSE_FIELDS},
        "would_read_source": True,
        "would_store_data": True,
        "would_cross_context": True,
        "would_notify": True,
        "would_execute": True,
        "sensitive_inference_made": True,
        "would_monitor": True,
        "would_track": True,
        "would_persist": True,
        "would_read_calendar": True,
        "would_read_email": True,
        "would_read_docs": True,
        "would_scan_local_files": True,
        "would_scan": True,
        "would_index": True,
        "would_store": True,
        "would_switch": True,
        "would_mix_contexts": True,
        "would_send_notifications": True,
        "would_modify_system_settings": True,
        "would_contact_people": True,
        "would_schedule": True,
        "sensitive_health_inference_made": True,
        "would_use_private_context": True,
        "would_persist_audit": True,
        "approval_created": True,
        "approval_granted": True,
    }
    values = (
        PersonalOSEnvironmentStatus.from_dict(malicious),
        ContextSourceConsentPreview.from_dict(malicious),
        DailyStatePreview.from_dict(malicious),
        PCEnvironmentStatePreview.from_dict(malicious),
        AwarenessSourcePreview.from_dict(malicious),
        LocalFilesScopePreview.from_dict(malicious),
        ContextSwitchingPreview.from_dict(malicious),
        AttentionProtectionPreview.from_dict(malicious),
        PersonalRoutinePreview.from_dict(malicious),
        EnergyFocusSupportPreview.from_dict(malicious),
        GuestModeContextPreview.from_dict(malicious),
        VisibleReasonAuditPreview.from_dict(malicious),
        PersonalOSApprovalRequirements.from_dict(malicious),
    )

    for value in values:
        payload = value.to_dict()
        assert payload["prepare_only"] is True
        for field, item in payload.items():
            if field in malicious and field not in {"prepare_only", "approval_required", "strong_approval_required"}:
                assert item is not True


def test_policy_from_dict_cannot_disable_safety_requirements():
    payload = PersonalOSPrivacyPolicy.from_dict({
        name: False for name in PersonalOSPrivacyPolicy.__dataclass_fields__
    }).to_dict()
    assert all(payload.values())
