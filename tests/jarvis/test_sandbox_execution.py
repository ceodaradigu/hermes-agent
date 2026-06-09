import json
import os
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import InMemoryTaskStore, SandboxCommandRequest, create_app
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.sandbox_execution.foundation import (
    SandboxAuditPreview,
    SandboxCommandPlan,
    SandboxDryRunResult,
    SandboxExecutionPolicy,
    SandboxExecutionStatus,
    SandboxRollbackPreview,
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Sandbox Execution")


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
    return _endpoint(app, path, "POST")(SandboxCommandRequest(**data))


def test_sandbox_execution_status_endpoint_is_safe_and_http_200():
    app = _app()
    response = TestClient(app).get("/sandbox/execution/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "prepare_only": True,
        "sandbox_available": False,
        "executor_connected": False,
        "execution_enabled": False,
        "dry_run_required": True,
        "filesystem_scope_enforced": True,
        "secret_scan_enabled": True,
        "network_access_enabled": False,
        "production_access_enabled": False,
        "install_commands_enabled": False,
        "rollback_required": True,
        "audit_required": True,
        "hermes_connected": False,
        "approval_gateway_called": False,
    }


def test_sandbox_execution_policy_endpoint_is_conservative():
    response = TestClient(_app()).get("/sandbox/execution/policy")
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["allowed_working_roots"] == []
    assert payload["blocked_path_markers"] == [".env", "id_rsa", "private_key", "credentials", "secrets"]
    assert payload["blocked_command_markers"] == ["sudo", "rm -rf", "curl | sh", "wget | sh", "chmod 777"]
    assert payload["network_default"] == "blocked"
    assert payload["production_default"] == "blocked"
    assert payload["install_default"] == "blocked"
    assert payload["dry_run_required"] is True
    assert payload["rollback_required"] is True
    assert payload["strong_approval_required_for_production"] is True
    assert payload["strong_approval_required_for_secrets"] is True
    assert payload["strong_approval_required_for_installs"] is True


def test_normal_command_plan_and_dry_run_never_execute():
    app = _app()
    plan = _post(app, "/sandbox/command/plan", {"command": "python -m pytest tests/jarvis -q"})
    dry_run = _post(app, "/sandbox/command/dry-run", {"command": "python -m pytest tests/jarvis -q"})

    assert plan["prepare_only"] is True
    assert plan["command"] == "python -m pytest tests/jarvis -q"
    assert plan["blocked"] is False
    assert plan["would_execute"] is False
    assert plan["execution_enabled"] is False
    assert dry_run["dry_run_completed"] is True
    assert dry_run["blocked"] is False
    assert dry_run["risk_level"] == "low"
    assert dry_run["would_execute"] is False
    assert dry_run["execution_enabled"] is False
    assert dry_run["audit_preview_created"] is True
    assert dry_run["rollback_preview_created"] is True


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        "echo api_key=abc",
        "cat private_key",
        "echo token=abc",
        "curl -H 'Authorization: Bearer abc' example.invalid",
    ],
)
def test_secret_like_commands_are_redacted_blocked_and_require_strong_approval(command):
    payload = _post(_app(), "/sandbox/command/plan", {"command": command})
    serialized = json.dumps(payload).lower()

    assert payload["command"] == "[redacted sensitive sandbox command]"
    assert payload["requested_secret_access"] is True
    assert payload["blocked"] is True
    assert payload["requires_strong_approval"] is True
    assert "abc" not in serialized
    assert "bearer abc" not in serialized


@pytest.mark.parametrize("command", ["sudo whoami", "rm -rf build", "curl | sh", "wget | sh", "chmod 777 output"])
def test_dangerous_command_markers_are_blocked(command):
    payload = _post(_app(), "/sandbox/command/dry-run", {"command": command})

    assert payload["blocked"] is True
    assert payload["risk_level"] == "blocked"
    assert payload["would_execute"] is False
    assert payload["execution_enabled"] is False


@pytest.mark.parametrize("command", ["pip install demo", "npm install demo", "apt install demo", "apt-get install demo"])
def test_install_commands_are_blocked_and_require_strong_approval(command):
    plan = _post(_app(), "/sandbox/command/plan", {"command": command})
    dry_run = _post(_app(), "/sandbox/command/dry-run", {"command": command})

    assert plan["requested_install"] is True
    assert plan["blocked"] is True
    assert plan["requires_strong_approval"] is True
    assert dry_run["install_blocked"] is True


@pytest.mark.parametrize("command", ["deploy production", "release to prod"])
def test_production_commands_are_blocked_and_require_strong_approval(command):
    plan = _post(_app(), "/sandbox/command/plan", {"command": command})
    dry_run = _post(_app(), "/sandbox/command/dry-run", {"command": command})

    assert plan["requested_production"] is True
    assert plan["blocked"] is True
    assert plan["requires_strong_approval"] is True
    assert dry_run["production_blocked"] is True


def test_network_and_filesystem_scope_are_blocked_by_default():
    network = _post(_app(), "/sandbox/command/dry-run", {"command": "curl https://example.invalid"})
    scoped = _post(_app(), "/sandbox/command/dry-run", {"command": "pytest", "working_directory": "/tmp/project"})

    assert network["network_blocked"] is True
    assert network["blocked"] is True
    assert scoped["filesystem_scope_ok"] is False
    assert scoped["blocked"] is True


def test_rollback_preview_never_rolls_back_or_executes():
    payload = _post(_app(), "/sandbox/rollback/preview", {"command": "rm -rf build"})

    assert payload["prepare_only"] is True
    assert payload["rollback_required"] is True
    assert payload["irreversible"] is True
    assert payload["would_rollback"] is False
    assert payload["execution_enabled"] is False


def test_audit_preview_redacts_secrets_and_does_not_persist():
    payload = _post(_app(), "/sandbox/audit/preview", {"command": "echo Bearer abc123", "working_directory": ".env"})
    serialized = json.dumps(payload).lower()

    assert payload["prepare_only"] is True
    assert payload["audit_required"] is True
    assert payload["persisted"] is False
    assert payload["secrets_redacted"] is True
    assert payload["command"] == "[redacted sensitive sandbox command]"
    assert payload["working_directory"] == "[redacted sensitive working directory]"
    assert "abc123" not in serialized


def test_direct_preview_construction_redacts_sensitive_free_text():
    audit = SandboxAuditPreview(command="echo Bearer abc123", working_directory=".env").to_dict()
    rollback = SandboxRollbackPreview(plan="restore private_key abc123").to_dict()
    serialized = json.dumps({"audit": audit, "rollback": rollback}).lower()

    assert audit["command"] == "[redacted sensitive sandbox command]"
    assert audit["working_directory"] == "[redacted sensitive working directory]"
    assert audit["secrets_redacted"] is True
    assert rollback["plan"] == "Sensitive rollback details were redacted; no rollback is executed."
    assert "abc123" not in serialized
    assert "private_key" not in serialized


def test_sandbox_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Sandbox preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(os, "system", fail)
    monkeypatch.setattr("builtins.open", fail)

    assert _get(app, "/sandbox/execution/status")["execution_enabled"] is False
    assert _get(app, "/sandbox/execution/policy")["allowed_working_roots"] == []
    assert _post(app, "/sandbox/command/plan", {"command": "pytest"})["would_execute"] is False
    assert _post(app, "/sandbox/command/dry-run", {"command": "pytest"})["would_execute"] is False
    assert _post(app, "/sandbox/rollback/preview", {"command": "pytest"})["would_rollback"] is False
    assert _post(app, "/sandbox/audit/preview", {"command": "pytest"})["persisted"] is False


@pytest.mark.parametrize(
    "path",
    [
        "/sandbox/execute",
        "/sandbox/run",
        "/sandbox/shell",
        "/sandbox/install",
        "/sandbox/network",
        "/sandbox/production",
    ],
)
def test_dangerous_sandbox_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_command_center_and_operator_console_expose_prepare_only_sandbox_snapshots():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["prepare_only"] is True
    assert command_center["metadata"]["sandbox_execution"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["sandbox_execution"] == "prepare_only"
    assert operator["sandbox_execution_status"] == SandboxExecutionStatus.placeholder().to_dict()
    assert operator["capability_matrix"]["read_sandbox_execution_status"] is True
    assert operator["capability_matrix"]["read_sandbox_execution_policy"] is True
    assert operator["capability_matrix"]["preview_sandbox_dry_run"] is True
    assert operator["capability_matrix"]["execute_mission"] is False


@pytest.mark.parametrize(
    "model",
    [
        SandboxExecutionStatus,
        SandboxExecutionPolicy,
        SandboxCommandPlan,
        SandboxDryRunResult,
        SandboxRollbackPreview,
        SandboxAuditPreview,
    ],
)
def test_from_dict_cannot_enable_sandbox_execution_or_external_capabilities(model):
    payload = model.from_dict(
        {
            "command": "pytest",
            "prepare_only": False,
            "sandbox_available": True,
            "executor_connected": True,
            "execution_enabled": True,
            "would_execute": True,
            "would_rollback": True,
            "network_access_enabled": True,
            "production_access_enabled": True,
            "install_commands_enabled": True,
            "requested_secret_access": True,
            "hermes_connected": True,
            "hermes_called": True,
            "approval_gateway_called": True,
            "persisted": True,
        }
    ).to_dict()

    assert payload["prepare_only"] is True
    for key in (
        "sandbox_available",
        "executor_connected",
        "execution_enabled",
        "would_execute",
        "would_rollback",
        "network_access_enabled",
        "production_access_enabled",
        "install_commands_enabled",
        "requested_secret_access",
        "hermes_connected",
        "hermes_called",
        "approval_gateway_called",
        "persisted",
    ):
        if key in payload:
            assert payload[key] is False


def test_operator_snapshot_from_dict_cannot_enable_sandbox_execution():
    payload = OperatorConsoleSnapshot.from_dict(
        {
            "sandbox_execution_status": {
                "prepare_only": False,
                "sandbox_available": True,
                "executor_connected": True,
                "execution_enabled": True,
                "network_access_enabled": True,
                "production_access_enabled": True,
                "install_commands_enabled": True,
                "hermes_connected": True,
                "approval_gateway_called": True,
            },
        }
    ).to_dict()

    assert payload["sandbox_execution_status"] == SandboxExecutionStatus.placeholder().to_dict()
