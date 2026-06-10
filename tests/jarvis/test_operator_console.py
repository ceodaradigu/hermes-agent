import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import OperatorConsolePreviewRequest, create_app
from jarvis.operator_console import (
    OperatorConsoleCapabilityMatrix,
    OperatorConsolePreview,
    OperatorSafetySummary,
    OperatorConsoleSnapshot,
    OperatorConsoleStatus,
)
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


class DummyAdapter:
    def __init__(self):
        self.calls = 0

    def run(self, message: str, **kwargs):
        self.calls += 1
        raise AssertionError("Hermes must not be called by Operator Console")


class DirectResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class DirectClient:
    def __init__(self, app):
        self.app = app

    def get(self, path):
        route = self._find_route(path, "GET")
        if route is None:
            return DirectResponse(404, {"detail": "Not Found"})
        return DirectResponse(200, route.endpoint())

    def post(self, path, json=None):
        route = self._find_route(path, "POST")
        if route is None:
            return DirectResponse(404, {"detail": "Not Found"})
        if path == "/operator/console/preview":
            return DirectResponse(200, route.endpoint(OperatorConsolePreviewRequest(**(json or {}))))
        return DirectResponse(200, route.endpoint())

    def _find_route(self, path, method):
        for route in self.app.routes:
            if route.path == path and method in route.methods:
                return route
        return None


def _client():
    adapter = DummyAdapter()
    app = create_app(adapter_factory=lambda: adapter)
    return DirectClient(app), adapter


def _route_endpoint(app, path):
    for route in app.routes:
        if route.path == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")


def _expected_status():
    return {
        "prepare_only": True,
        "operator_console_available": True,
        "frontend_available": False,
        "websocket_enabled": False,
        "execution_enabled": False,
        "approval_actions_enabled": False,
        "hermes_connected": False,
        "approval_gateway_called": False,
        "secrets_access_enabled": False,
        "external_calls_enabled": False,
        "safe_read_only_mode": True,
    }


def _assert_capability_matrix(payload):
    assert payload["prepare_only"] is True
    assert payload["read_command_center"] is True
    assert payload["read_voice_status"] is True
    assert payload["read_mobile_status"] is True
    assert payload["preview_voice_intent"] is True
    assert payload["preview_mobile_intent"] is True
    assert payload["inspect_safety"] is True
    assert payload["inspect_capabilities"] is True
    assert payload["execute_mission"] is False
    assert payload["approve"] is False
    assert payload["reject"] is False
    assert payload["call_hermes"] is False
    assert payload["create_approval"] is False
    assert payload["read_secrets"] is False
    assert payload["use_microphone"] is False
    assert payload["use_camera"] is False
    assert payload["use_location"] is False
    assert payload["send_push"] is False
    assert payload["run_background"] is False
    assert payload["deploy"] is False
    assert payload["spend_money"] is False


def _assert_preview_never_executes(payload):
    assert payload["prepare_only"] is True
    assert payload["would_execute"] is False
    assert payload["execution_enabled"] is False
    assert payload["approval_created"] is False
    assert payload["approval_gateway_called"] is False
    assert payload["hermes_called"] is False
    assert payload["mission_created"] is False
    assert payload["task_created"] is False
    assert payload["persisted"] is False
    assert payload["voice_preview"]["would_execute"] is False
    assert payload["voice_preview"]["approval_created"] is False
    assert payload["voice_preview"]["approval_gateway_called"] is False
    assert payload["voice_preview"]["hermes_called"] is False
    assert payload["mobile_preview"]["would_execute"] is False
    assert payload["mobile_preview"]["approval_created"] is False
    assert payload["mobile_preview"]["approval_gateway_called"] is False
    assert payload["mobile_preview"]["hermes_called"] is False


def test_operator_console_status_endpoint_is_safe_read_only():
    client, adapter = _client()

    response = client.get("/operator/console/status")

    assert response.status_code == 200
    assert response.json() == _expected_status()
    assert adapter.calls == 0


def test_operator_console_status_from_dict_cannot_enable_features():
    status = OperatorConsoleStatus.from_dict(
        {
            "prepare_only": False,
            "frontend_available": True,
            "websocket_enabled": True,
            "execution_enabled": True,
            "approval_actions_enabled": True,
            "hermes_connected": True,
            "approval_gateway_called": True,
            "secrets_access_enabled": True,
            "external_calls_enabled": True,
            "safe_read_only_mode": False,
        }
    )

    assert status.to_dict() == _expected_status()


def test_operator_console_capabilities_endpoint_returns_secure_matrix():
    client, adapter = _client()

    response = client.get("/operator/console/capabilities")
    payload = response.json()

    assert response.status_code == 200
    _assert_capability_matrix(payload)
    assert adapter.calls == 0


def test_operator_console_capability_from_dict_cannot_enable_forbidden_actions():
    payload = OperatorConsoleCapabilityMatrix.from_dict(
        {
            "execute_mission": True,
            "approve": True,
            "reject": True,
            "call_hermes": True,
            "create_approval": True,
            "read_secrets": True,
            "use_microphone": True,
            "use_camera": True,
            "use_location": True,
            "send_push": True,
            "run_background": True,
            "deploy": True,
            "spend_money": True,
        }
    ).to_dict()

    _assert_capability_matrix(payload)


def test_operator_console_snapshot_endpoint_returns_aggregate_prepare_only_snapshot(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway.create_request must not be called by Operator Console snapshot")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter.run must not be called by Operator Console snapshot")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)

    client, adapter = _client()
    response = client.get("/operator/console/snapshot")
    payload = response.json()
    serialized = response.text.lower()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["status"] == _expected_status()
    assert payload["command_center"]["prepare_only"] is True
    assert payload["command_center"]["metadata"]["operator_console"] == "prepare_only"
    assert payload["voice_status"]["prepare_only"] is True
    assert payload["voice_status"]["microphone_enabled"] is False
    assert payload["voice_control_policy"]["prepare_only"] is True
    assert payload["voice_control_policy"]["activation_enabled"] is False
    assert payload["mobile_status"]["prepare_only"] is True
    assert payload["mobile_status"]["push_enabled"] is False
    assert payload["mobile_permission_policy"]["prepare_only"] is True
    assert payload["mobile_permission_policy"]["can_execute"] is False
    assert payload["mobile_command_center"]["prepare_only"] is True
    _assert_capability_matrix(payload["capability_matrix"])
    assert payload["safety_summary"]["prepare_only"] is True
    assert payload["safety_summary"]["all_execution_disabled"] is True
    assert payload["safety_summary"]["all_approval_actions_disabled"] is True
    assert payload["safety_summary"]["hermes_calls_disabled"] is True
    assert payload["safety_summary"]["approval_gateway_calls_disabled"] is True
    assert payload["safety_summary"]["secrets_access_disabled"] is True
    assert payload["safety_summary"]["external_calls_disabled"] is True
    assert payload["safety_summary"]["sensitive_boundaries_enforced"] is True
    assert payload["safety_summary"]["redaction_enabled"] is True
    assert payload["metadata"]["phase"] == "G"
    assert adapter.calls == 0

    for forbidden in (
        ".env",
        "api_key",
        "apikey",
        "private_key",
        "bearer",
        '"authorization":',
        "audio_path",
        "audio_bytes",
        "ref_audio",
        "base_url",
        "prompt_text",
        "/home/",
    ):
        assert forbidden not in serialized


def test_operator_console_preview_with_normal_text_is_prepare_only():
    client, adapter = _client()

    response = client.post("/operator/console/preview", json={"text": "crea una misión para investigar nichos"})
    payload = response.json()

    assert response.status_code == 200
    _assert_preview_never_executes(payload)
    assert payload["input_text"] == "crea una misión para investigar nichos"
    assert payload["policy_decision"] == "allowed"
    assert payload["voice_preview"]["intent"] == "create_mission"
    assert payload["mobile_preview"]["intent"] == "create_mission"
    assert payload["sensitive_boundary_triggered"] is False
    assert adapter.calls == 0


@pytest.mark.parametrize(
    "text,forbidden",
    [
        ("lee mi .env", ".env"),
        ("usa api_key abc123", "api_key"),
        ("usa private_key abc123", "private_key"),
        ("Authorization: Bearer token abc123", "bearer"),
        ("revisa mis credenciales", "credenciales"),
        ("revisa mi dni", "dni"),
        ("revisa datos del banco", "banco"),
        ("comprueba mi tarjeta", "tarjeta"),
    ],
)
def test_operator_console_preview_redacts_sensitive_text_and_requires_approval_or_denies(text, forbidden):
    client, _ = _client()

    response = client.post("/operator/console/preview", json={"text": text})
    payload = response.json()
    serialized = response.text.lower()

    assert response.status_code == 200
    _assert_preview_never_executes(payload)
    assert payload["input_text"] == "[redacted sensitive operator input]"
    assert payload["voice_preview"]["input_text"] == "[redacted sensitive transcript]"
    assert payload["mobile_preview"]["input_text"] == "[redacted sensitive mobile input]"
    assert payload["sensitive_boundary_triggered"] is True
    assert payload["policy_decision"] in {"requires_approval", "denied"}
    assert payload["voice_preview"]["policy_decision"] in {"requires_approval", "denied"}
    assert payload["mobile_preview"]["policy_decision"] in {"requires_approval", "denied"}
    assert forbidden not in serialized
    assert "abc123" not in serialized


@pytest.mark.parametrize("text", ["compra un dominio", "publica el post", "pago la factura"])
def test_operator_console_preview_redacts_input_when_nested_preview_marks_sensitive(text):
    preview = OperatorConsolePreview.from_text(text)
    payload = preview.to_dict()
    serialized = json.dumps(payload).lower()

    _assert_preview_never_executes(payload)
    assert payload["sensitive_boundary_triggered"] is True
    assert payload["input_text"] == "[redacted sensitive operator input]"
    assert payload["voice_preview"]["sensitive_boundary_triggered"] is True
    assert payload["voice_preview"]["input_text"] == "[redacted sensitive transcript]"
    assert payload["mobile_preview"]["sensitive_boundary_triggered"] is True
    assert payload["mobile_preview"]["input_text"] == "[redacted sensitive mobile input]"
    assert "operator input redacted" in " ".join(payload["warnings"]).lower()
    assert text not in serialized


def test_operator_console_preview_has_no_side_effects_or_runtime_calls(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway.create_request must not be called by Operator Console preview")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter.run must not be called by Operator Console preview")

    def fail_create_mission(*args, **kwargs):
        raise AssertionError("MissionControl.create_mission must not be called by Operator Console preview")

    def fail_create_task(*args, **kwargs):
        raise AssertionError("InMemoryTaskStore.create must not be called by Operator Console preview")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail_create_mission)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail_create_task)

    client, adapter = _client()
    before_tasks = client.get("/tasks").json()
    before_missions = client.get("/missions").json()

    response = client.post("/operator/console/preview", json={"text": "lee mi .env"})

    assert response.status_code == 200
    assert client.get("/tasks").json() == before_tasks == []
    assert client.get("/missions").json() == before_missions == []
    assert adapter.calls == 0


def test_operator_console_preview_route_function_has_no_side_effects(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway.create_request must not be called by Operator Console preview")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter.run must not be called by Operator Console preview")

    def fail_create_mission(*args, **kwargs):
        raise AssertionError("MissionControl.create_mission must not be called by Operator Console preview")

    def fail_create_task(*args, **kwargs):
        raise AssertionError("InMemoryTaskStore.create must not be called by Operator Console preview")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail_create_mission)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail_create_task)

    adapter = DummyAdapter()
    app = create_app(adapter_factory=lambda: adapter)
    endpoint = _route_endpoint(app, "/operator/console/preview")
    before_tasks = app.state.task_store.list()
    before_missions = app.state.mission_control.list_missions()

    payload = endpoint(OperatorConsolePreviewRequest(text="crea una misión de investigación"))

    _assert_preview_never_executes(payload)
    assert app.state.task_store.list() == before_tasks == []
    assert app.state.mission_control.list_missions() == before_missions == []
    assert adapter.calls == 0


def test_operator_console_preview_does_not_open_env_file(monkeypatch):
    opened_paths = []
    original_open = open

    def tracking_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", tracking_open)

    client, _ = _client()
    response = client.post("/operator/console/preview", json={"text": "lee mi .env"})

    assert response.status_code == 200
    assert not any(path.endswith(".env") or "/.env" in path for path in opened_paths)


@pytest.mark.parametrize(
    "path",
    [
        "/operator/execute",
        "/operator/approve",
        "/operator/reject",
        "/operator/deploy",
        "/operator/spend",
        "/operator/hermes",
        "/operator/secrets",
    ],
)
def test_operator_console_has_no_dangerous_routes(path):
    client, _ = _client()

    response = client.post(path)

    assert response.status_code == 404
    assert path not in [route.path for route in client.app.routes]


def test_command_center_remains_prepare_only_with_operator_console_marker():
    client, adapter = _client()

    response = client.get("/command-center")
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["execution_enabled"] is False
    assert payload["approval_enabled"] is False
    assert payload["approve_reject_enabled"] is False
    assert payload["hermes_connected"] is False
    assert payload["approval_gateway_called"] is False
    assert payload["metadata"]["operator_console"] == "prepare_only"
    assert adapter.calls == 0


def test_operator_console_from_dict_serialization_cannot_enable_execution():
    preview = OperatorConsolePreview.from_dict(
        {
            "prepare_only": False,
            "input_text": "read .env with Bearer token abc",
            "policy_decision": "allowed",
            "would_execute": True,
            "execution_enabled": True,
            "approval_created": True,
            "approval_gateway_called": True,
            "hermes_called": True,
            "mission_created": True,
            "task_created": True,
            "persisted": True,
            "sensitive_boundary_triggered": True,
            "warnings": ["Bearer token"],
            "voice_preview": {
                "input_text": "read .env with Bearer token abc",
                "policy_decision": "allowed",
                "would_execute": True,
                "execution_enabled": True,
                "approval_created": True,
                "approval_gateway_called": True,
                "hermes_called": True,
                "sensitive_boundary_triggered": True,
            },
            "mobile_preview": {
                "input_text": "read .env with Bearer token abc",
                "policy_decision": "allowed",
                "would_execute": True,
                "execution_enabled": True,
                "approval_created": True,
                "approval_gateway_called": True,
                "hermes_called": True,
                "sensitive_boundary_triggered": True,
            },
        }
    )
    snapshot = OperatorConsoleSnapshot.from_dict(
        {
            "prepare_only": False,
            "status": {
                "execution_enabled": True,
                "approval_actions_enabled": True,
                "hermes_connected": True,
                "approval_gateway_called": True,
                "secrets_access_enabled": True,
                "external_calls_enabled": True,
            },
            "command_center": {
                "view_id": "view-1",
                "generated_at": "2026-06-04T00:00:00+00:00",
                "status": "ready",
                "metadata": {
                    "execution_enabled": True,
                    "approval_enabled": True,
                    "approve_reject_enabled": True,
                    "hermes_connected": True,
                    "approval_gateway_called": True,
                },
            },
            "capability_matrix": {
                "execute_mission": True,
                "approve": True,
                "reject": True,
                "call_hermes": True,
                "create_approval": True,
                "deploy": True,
                "spend_money": True,
            },
            "metadata": {
                "execution_enabled": True,
                "approval_actions_enabled": True,
                "hermes_connected": True,
                "approval_gateway_called": True,
                "external_calls_enabled": True,
            },
        }
    )

    preview_payload = preview.to_dict()
    snapshot_payload = snapshot.to_dict()
    serialized = json.dumps({"preview": preview_payload, "snapshot": snapshot_payload}).lower()

    _assert_preview_never_executes(preview_payload)
    assert preview_payload["input_text"] == "[redacted sensitive operator input]"
    assert snapshot_payload["prepare_only"] is True
    assert snapshot_payload["status"] == _expected_status()
    assert snapshot_payload["command_center"]["execution_enabled"] is False
    assert snapshot_payload["command_center"]["approval_enabled"] is False
    assert snapshot_payload["command_center"]["approve_reject_enabled"] is False
    assert snapshot_payload["command_center"]["hermes_connected"] is False
    assert snapshot_payload["command_center"]["approval_gateway_called"] is False
    _assert_capability_matrix(snapshot_payload["capability_matrix"])
    assert snapshot_payload["metadata"]["execution_enabled"] is False
    assert snapshot_payload["metadata"]["approval_actions_enabled"] is False
    assert snapshot_payload["metadata"]["hermes_connected"] is False
    assert snapshot_payload["metadata"]["approval_gateway_called"] is False
    for forbidden in (".env", "bearer", "token abc"):
        assert forbidden not in serialized


def test_operator_console_snapshot_from_dict_none_uses_safe_placeholder():
    snapshot = OperatorConsoleSnapshot.from_dict(None)
    payload = snapshot.to_dict()

    assert payload["prepare_only"] is True
    assert payload["status"] == _expected_status()
    assert payload["command_center"]["prepare_only"] is True
    assert payload["command_center"]["execution_enabled"] is False
    assert payload["command_center"]["approval_enabled"] is False
    assert payload["command_center"]["approve_reject_enabled"] is False
    assert payload["command_center"]["hermes_connected"] is False
    assert payload["command_center"]["approval_gateway_called"] is False
    assert payload["command_center"]["metadata"]["operator_console"] == "prepare_only"
    _assert_capability_matrix(payload["capability_matrix"])


def test_operator_console_snapshot_from_dict_empty_uses_safe_placeholder_command_center():
    snapshot = OperatorConsoleSnapshot.from_dict({})
    payload = snapshot.to_dict()

    assert payload["prepare_only"] is True
    assert payload["command_center"]["view_id"] == "operator-command-center-placeholder"
    assert payload["command_center"]["metadata"]["operator_console"] == "prepare_only"
    assert payload["command_center"]["execution_enabled"] is False
    assert payload["status"]["execution_enabled"] is False
    assert payload["status"]["approval_actions_enabled"] is False
    assert payload["status"]["hermes_connected"] is False
    assert payload["status"]["secrets_access_enabled"] is False
    assert payload["status"]["external_calls_enabled"] is False


def test_operator_console_missing_command_center_does_not_enable_forbidden_capabilities():
    snapshot = OperatorConsoleSnapshot.from_dict(
        {
            "status": {
                "execution_enabled": True,
                "approval_actions_enabled": True,
                "hermes_connected": True,
                "secrets_access_enabled": True,
                "external_calls_enabled": True,
            },
            "capability_matrix": {
                "execute_mission": True,
                "approve": True,
                "reject": True,
                "call_hermes": True,
                "create_approval": True,
                "read_secrets": True,
                "deploy": True,
                "spend_money": True,
            },
        }
    )
    payload = snapshot.to_dict()

    assert payload["command_center"]["execution_enabled"] is False
    assert payload["status"]["execution_enabled"] is False
    assert payload["status"]["approval_actions_enabled"] is False
    assert payload["status"]["hermes_connected"] is False
    assert payload["status"]["secrets_access_enabled"] is False
    assert payload["status"]["external_calls_enabled"] is False
    assert payload["capability_matrix"]["execute_mission"] is False
    assert payload["capability_matrix"]["approve"] is False
    assert payload["capability_matrix"]["reject"] is False
    assert payload["capability_matrix"]["call_hermes"] is False
    assert payload["capability_matrix"]["read_secrets"] is False
    assert payload["capability_matrix"]["deploy"] is False
    assert payload["capability_matrix"]["spend_money"] is False


@pytest.mark.parametrize(
    "warning,forbidden",
    [
        ("Bearer token abc", "token abc"),
        ("api_key abc", "api_key"),
        ("private_key abc", "private_key"),
        ("read .env", ".env"),
        ("credenciales personales", "credenciales"),
        ("dni personal", "dni"),
        ("datos de banco", "banco"),
        ("numero de tarjeta", "tarjeta"),
    ],
)
def test_operator_safety_summary_redacts_sensitive_warnings(warning, forbidden):
    payload = OperatorSafetySummary.from_dict({"warnings": [warning]}).to_dict()
    serialized = json.dumps(payload).lower()

    assert payload["warnings"] == ["[redacted sensitive operator warning]"]
    assert forbidden not in serialized


def test_operator_safety_summary_keeps_safe_warning_text_visible():
    payload = OperatorSafetySummary.from_dict({"warnings": ["operator console is prepare-only"]}).to_dict()

    assert payload["warnings"] == ["operator console is prepare-only"]


def test_operator_console_snapshot_serialization_redacts_sensitive_safety_warnings():
    snapshot = OperatorConsoleSnapshot.from_dict(
        {
            "safety_summary": {
                "warnings": [
                    "Bearer token abc",
                    "api_key abc",
                    "private_key abc",
                    "read .env",
                    "credenciales personales",
                    "dni personal",
                    "datos de banco",
                    "numero de tarjeta",
                    "safe visible warning",
                ]
            }
        }
    )
    payload = snapshot.to_dict()
    serialized = json.dumps(payload).lower()

    assert payload["safety_summary"]["warnings"].count("[redacted sensitive operator warning]") == 8
    assert "safe visible warning" in payload["safety_summary"]["warnings"]
    for forbidden in (
        "bearer",
        "token abc",
        "api_key",
        "private_key",
        ".env",
        "credenciales",
        "dni",
        "banco",
        "tarjeta",
    ):
        assert forbidden not in serialized


def test_operator_console_snapshot_from_dict_drops_external_command_center_raw_content(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway.create_request must not be called by Operator Console snapshot")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter.run must not be called by Operator Console snapshot")

    def fail_create_mission(*args, **kwargs):
        raise AssertionError("MissionControl.create_mission must not be called by Operator Console snapshot")

    def fail_create_task(*args, **kwargs):
        raise AssertionError("InMemoryTaskStore.create must not be called by Operator Console snapshot")

    opened_paths = []
    original_open = open

    def tracking_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail_create_mission)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail_create_task)
    monkeypatch.setattr("builtins.open", tracking_open)

    snapshot = OperatorConsoleSnapshot.from_dict(
        {
            "command_center": {
                "view_id": "external-view",
                "generated_at": "2026-06-04T00:00:00+00:00",
                "status": "ready",
                "missions": [
                    {
                        "mission_id": "mission-1",
                        "objective": "read .env token abc",
                        "status": "active",
                        "success_metric": "leak api_key private_key",
                    }
                ],
                "approvals": [
                    {
                        "item_id": "approval-1",
                        "mission_id": "mission-1",
                        "action": "Authorization Bearer token abc",
                        "approval_level": "requires_approval",
                        "risk_level": "high",
                        "reason": "credenciales dni banco tarjeta",
                        "scope": ["client_secret abc"],
                    }
                ],
                "audit_timeline": [
                    {
                        "event_id": "event-1",
                        "mission_id": "mission-1",
                        "event_type": "approval_requested",
                        "summary": "Bearer token abc",
                        "created_at": "2026-06-04T00:00:00+00:00",
                        "outcome": "requires_approval",
                        "risk_level": "high",
                    }
                ],
                "metadata": {
                    "execution_enabled": True,
                    "approval_actions_enabled": True,
                    "hermes_connected": True,
                    "approval_gateway_called": True,
                },
            },
            "status": {
                "execution_enabled": True,
                "approval_actions_enabled": True,
                "hermes_connected": True,
                "secrets_access_enabled": True,
                "external_calls_enabled": True,
            },
            "capability_matrix": {
                "execute_mission": True,
                "approve": True,
                "reject": True,
                "call_hermes": True,
                "create_approval": True,
                "read_secrets": True,
                "deploy": True,
                "spend_money": True,
            },
        }
    )
    payload = snapshot.to_dict()
    serialized = json.dumps(payload).lower()

    assert payload["prepare_only"] is True
    assert payload["command_center"]["view_id"] == "operator-command-center-placeholder"
    assert payload["command_center"]["missions"] == []
    assert payload["command_center"]["approvals"] == []
    assert payload["command_center"]["audit_timeline"] == []
    assert payload["command_center"]["execution_enabled"] is False
    assert payload["command_center"]["approval_enabled"] is False
    assert payload["command_center"]["approve_reject_enabled"] is False
    assert payload["command_center"]["hermes_connected"] is False
    assert payload["command_center"]["approval_gateway_called"] is False
    assert payload["status"]["execution_enabled"] is False
    assert payload["status"]["approval_actions_enabled"] is False
    assert payload["status"]["hermes_connected"] is False
    assert payload["status"]["secrets_access_enabled"] is False
    assert payload["status"]["external_calls_enabled"] is False
    assert payload["capability_matrix"]["execute_mission"] is False
    assert payload["capability_matrix"]["approve"] is False
    assert payload["capability_matrix"]["reject"] is False
    assert payload["capability_matrix"]["call_hermes"] is False
    assert payload["capability_matrix"]["create_approval"] is False
    assert payload["capability_matrix"]["read_secrets"] is False
    assert payload["capability_matrix"]["deploy"] is False
    assert payload["capability_matrix"]["spend_money"] is False
    for forbidden in (
        ".env",
        "token abc",
        "api_key",
        "private_key",
        "bearer",
        "credenciales",
        "dni",
        "banco",
        "tarjeta",
        "client_secret",
    ):
        assert forbidden not in serialized
    assert not any(path.endswith(".env") or "/.env" in path for path in opened_paths)
