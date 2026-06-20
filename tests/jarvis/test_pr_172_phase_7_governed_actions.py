import json
import subprocess
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionApprovalDecisionRequest,
    Mark3ExecutionDispatchRequest,
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3LocalPairingChallengeRequest,
    Mark3LocalPairingVerifyRequest,
    Mark3RemotePairingRevokeRequest,
    Mark3VoiceApprovalDecisionRequest,
    Mark3VoiceApprovalStartRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_7_governed_actions import PHASE7_ACTION_KEYS


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class FakeHermesReadAdapter:
    def __init__(self, calls):
        self.calls = calls

    def run(self, message, **kwargs):
        self.calls.append({"message": message, "kwargs": kwargs})
        return {"success": True, "completed": True}

    def interrupt(self, reason):
        return True


def _make_app(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("JARVIS_PHASE7_ALLOWED_ROOTS", str(workspace))
    state_dir = tmp_path / "state"
    monkeypatch.setenv("JARVIS_LOCAL_STATE_DIR", str(state_dir))
    ledger = PersistentAuditLedger(base_dir=state_dir)
    memory = MemoryBrainV2Store(base_dir=state_dir, audit_ledger=ledger)
    calls = []
    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=lambda _guard: FakeHermesReadAdapter(calls),
        persistent_audit_ledger=ledger,
        memory_brain_v2=memory,
    )
    return app, workspace, ledger, calls


def _route(app, path, method="GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _preview(app, **payload):
    return _route(app, "/mark-3/execution/preview", "POST").endpoint(Mark3ExecutionPreviewRequest(**payload))


def _request_approval(app, preview_id):
    return _route(app, "/mark-3/execution/request-approval", "POST").endpoint(
        Mark3ExecutionRequestApprovalRequest(preview_id=preview_id, actor="David")
    )


def _decide(app, approval_id, decision="approve", **payload):
    return _route(app, "/mark-3/execution/approval-decision", "POST").endpoint(
        Mark3ExecutionApprovalDecisionRequest(approval_id=approval_id, decision=decision, **payload)
    )


def _dispatch(app, preview_id, approval_id=None):
    return _route(app, "/mark-3/execution/dispatch", "POST").endpoint(
        Mark3ExecutionDispatchRequest(preview_id=preview_id, approval_id=approval_id, actor="David")
    )


def _pair_voice_device(app, *, public_identifier="phase7-phone"):
    challenge = _route(app, "/mark-3/local-pairing/challenge", "POST").endpoint(
        Mark3LocalPairingChallengeRequest(
            display_name="David phone",
            public_identifier=public_identifier,
            channel="local_voice_device",
            scope=["voice_approval", "normal", "strong"],
        )
    )
    return _route(app, "/mark-3/local-pairing/verify", "POST").endpoint(
        Mark3LocalPairingVerifyRequest(
            challenge_id=challenge["challenge_id"],
            nonce=challenge["nonce"],
            response_phrase=challenge["challenge_phrase"],
            public_identifier=public_identifier,
            display_name="David phone",
            scope=["voice_approval", "normal", "strong"],
        )
    )


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=600)}


def _frontend_source():
    paths = [
        WEB / "src/lib/api.ts",
        WEB / "src/components/jarvis/JarvisDebugDrawer.tsx",
        WEB / "src/components/jarvis/types.ts",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_phase_7_routes_catalog_dashboard_events_and_frontend_contract(tmp_path, monkeypatch):
    app, _workspace, _ledger, calls = _make_app(tmp_path, monkeypatch)
    route_paths = {route.path for route in app.routes}

    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    assert "/mark-3/phase-7/status" in route_paths

    phase7 = _route(app, "/mark-3/phase-7/status").endpoint()
    assert phase7["status"] == "implemented_as_governed_local_action_pilot"
    assert phase7["implemented_blocks"]["governed_action_catalog_v2"] is True
    assert phase7["security_gates"]["jarvis_governs"] is True
    assert phase7["security_gates"]["frontend_can_execute_hermes_directly"] is False
    assert phase7["adapters"]["browser"]["status"] == "readiness_and_plan_only"
    assert phase7["adapters"]["sandbox"]["status"] == "guarded_local_command_runner_not_os_sandbox"

    catalog = _route(app, "/mark-3/execution/action-catalog").endpoint()
    assert catalog["schema_version"] == "jarvis.governed_action_catalog.v2"
    action_keys = {action["action_key"] for action in catalog["actions"]}
    assert set(PHASE7_ACTION_KEYS) <= action_keys
    assert catalog["allowlist_only"] is True
    for required in catalog["required_fields"]:
        assert required in catalog["actions"][0]
    write_action = next(action for action in catalog["actions"] if action["action_key"] == "filesystem.file.write_safe")
    assert write_action["flags"]["filesystem"] is True
    assert write_action["rollback_supported"] is True
    assert write_action["voice_approval_eligible"] is True
    assert write_action["default_state"]["enabled"] is True
    branch_create = next(action for action in catalog["actions"] if action["action_key"] == "github.branch.create_local")
    assert branch_create["default_state"]["enabled"] is False
    for denied in ("shell_freeform", "commit_unapproved", "push_unapproved", "pr_open_unapproved", "hidden_browser"):
        assert denied in catalog["denied_actions"]

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_7_status"]["source_endpoint"] == "/mark-3/phase-7/status"
    assert dashboard["filesystem_adapter"]["backup_before_overwrite"] is True
    assert dashboard["browser_automation"]["hidden_browser_allowed"] is False
    modules = {module["name"] for module in dashboard["modules"]}
    assert "Phase 7 Actions" in modules

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert "phase_7_state" in event_types
    assert "action_catalog_state" in event_types
    assert json.dumps(snapshot).find("sk_live_") == -1

    source = _frontend_source()
    assert "/mark-3/phase-7/status" in source
    assert "Phase 7 action catalog status" in source
    assert "Filesystem writes require backend approval" in source
    assert "no hidden browser" in source.lower()
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert "dispatchHermes" not in source
    assert calls == []


def test_filesystem_safe_read_list_write_backup_and_secret_blocks(tmp_path, monkeypatch):
    app, workspace, ledger, calls = _make_app(tmp_path, monkeypatch)
    safe_file = workspace / "notes.txt"
    safe_file.write_text("old safe content\n", encoding="utf-8")
    (workspace / ".env").write_text("SECRET=sk-test\n", encoding="utf-8")

    read = _preview(app, intent="Read safe file", action_key="filesystem.file.read_text", inputs={"path": str(safe_file)})
    assert read["decision"] == "allowed"
    read_result = _dispatch(app, read["preview_id"])
    assert read_result["state"] == "dispatch_completed"
    assert read_result["dispatch"]["data"]["file"]["content"] == "old safe content\n"

    listed = _preview(app, intent="List workspace", action_key="filesystem.directory.list", inputs={"path": str(workspace), "limit": 10})
    list_result = _dispatch(app, listed["preview_id"])
    items = list_result["dispatch"]["data"]["directory"]["items"]
    assert any(item["name"] == "notes.txt" for item in items)
    assert any(item["secret_like"] is True for item in items)
    assert ".env" not in json.dumps(list_result)

    traversal = _preview(app, intent="Read outside", action_key="filesystem.file.read_text", inputs={"path": "../outside.txt"})
    assert traversal["decision"] == "denied"
    assert traversal["preflight"]["blocking"] is True

    secret = _preview(app, intent="Read env", action_key="filesystem.file.read_text", inputs={"path": str(workspace / ".env")})
    assert secret["decision"] == "denied"
    assert secret["preflight"]["blocking"] is True

    write = _preview(
        app,
        intent="Update safe file",
        action_key="filesystem.file.write_safe",
        inputs={"path": str(safe_file), "content": "new safe content\n"},
    )
    assert write["decision"] == "requires_approval"
    assert write["requires_approval"] is True
    assert write["preview"]["diff_preview"]["line_count"] > 0
    assert "new safe content" in write["preview"]["diff_preview"]["diff"]
    assert "content" in write["inputs"] and write["inputs"]["content"]["omitted"] is True
    with pytest.raises(HTTPException) as no_approval:
        _dispatch(app, write["preview_id"])
    assert no_approval.value.status_code == 400
    envelope = _request_approval(app, write["preview_id"])
    approved = _decide(app, envelope["approval_id"], "approve")
    assert approved["status"] == "approved"
    result = _dispatch(app, write["preview_id"], envelope["approval_id"])
    assert result["state"] == "dispatch_completed"
    assert safe_file.read_text(encoding="utf-8") == "new safe content\n"
    backups = list((workspace / ".jarvis" / "phase_7_backups").glob("*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "old safe content\n"

    secret_write = _preview(
        app,
        intent="Write a token",
        action_key="filesystem.file.write_safe",
        inputs={"path": str(workspace / "safe.txt"), "content": "token=sk_live_1234567890123456"},
    )
    assert secret_write["decision"] == "denied"
    serialized = json.dumps(secret_write)
    assert "sk_live_1234567890123456" not in serialized
    assert secret_write["preflight"]["blocking"] is True
    assert {"filesystem_backup_created", "filesystem_write_completed", "preflight_completed"} <= _event_types(ledger)
    assert calls == []


def test_github_browser_sandbox_preflight_and_voice_approval_gates(tmp_path, monkeypatch):
    app, workspace, ledger, calls = _make_app(tmp_path, monkeypatch)

    git_status = _preview(app, intent="Repo status", action_key="github.repo.status")
    assert git_status["decision"] == "allowed"
    git_result = _dispatch(app, git_status["preview_id"])
    assert git_result["dispatch"]["data"]["git_status"]["exit_code"] == 0

    branch = _preview(app, intent="Prepare branch", action_key="github.branch.prepare", inputs={"title": "Phase 7 Safe Pilot"})
    branch_result = _dispatch(app, branch["preview_id"])
    assert branch_result["dispatch"]["data"]["branch"].startswith("jarvis/phase-7-safe-pilot")

    branch_create = _preview(app, intent="Create branch", action_key="github.branch.create_local", inputs={"branch": "unsafe real branch"})
    assert branch_create["requires_approval"] is True
    assert branch_create["preview"]["default_disabled_reason"] == "current PR workflow forbids git mutation by the agent"

    browser_submit = _preview(
        app,
        intent="Submit form",
        action_key="browser.click.submit_plan",
        inputs={"url": "https://example.com/form", "selector": "button[type=submit]"},
    )
    assert browser_submit["risk_level"] == "high"
    assert browser_submit["approval_level_required"] == "strong"
    with pytest.raises(HTTPException):
        _dispatch(app, browser_submit["preview_id"])

    with pytest.raises(HTTPException) as arbitrary_shell:
        _preview(app, intent="Run shell", action_key="sandbox.command.plan", inputs={"command_id": "rm -rf /"})
    assert arbitrary_shell.value.status_code == 400

    sandbox = _preview(app, intent="Run git status safely", action_key="sandbox.command.run_allowlisted", inputs={"command_id": "git_status"})
    assert sandbox["requires_approval"] is True
    sandbox_envelope = _request_approval(app, sandbox["preview_id"])
    _decide(app, sandbox_envelope["approval_id"], "approve")
    sandbox_result = _dispatch(app, sandbox["preview_id"], sandbox_envelope["approval_id"])
    assert sandbox_result["dispatch"]["data"]["plan"]["shell"] is False
    assert sandbox_result["dispatch"]["data"]["plan"]["inherited_secrets"] is False

    preflight = _preview(
        app,
        intent="Scan text",
        action_key="preflight.scan",
        inputs={"text": "STRIPE=sk_live_1234567890123456", "action_key": "filesystem.file.write_safe"},
    )
    assert preflight["decision"] == "denied"
    assert preflight["preflight"]["blocking"] is True
    assert "sk_live_1234567890123456" not in json.dumps(preflight)

    paired = _pair_voice_device(app)
    write_target = workspace / "voice-write.txt"
    voice_write = _preview(
        app,
        intent="Voice approve a safe write",
        action_key="filesystem.file.write_safe",
        inputs={"path": str(write_target), "content": "voice approved safe content\n"},
    )
    envelope = _request_approval(app, voice_write["preview_id"])
    session = _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
        Mark3VoiceApprovalStartRequest(
            approval_id=envelope["approval_id"],
            device_id=paired["device"]["device_id"],
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    accepted = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=paired["device"]["device_id"],
            transcript="JARVIS, autorizo",
            readback_text=envelope["readback_text"],
            action_id=envelope["action_id"],
            cost_summary="unknown; operator review required",
        )
    )
    assert accepted["decision"] == "accepted"
    _dispatch(app, voice_write["preview_id"], envelope["approval_id"])
    assert write_target.exists()

    _route(app, "/mark-3/remote-pairing/revoke", "POST").endpoint(
        Mark3RemotePairingRevokeRequest(device_id=paired["device"]["device_id"], reason="test revoke")
    )
    second_write = _preview(
        app,
        intent="Blocked voice approve",
        action_key="filesystem.file.write_safe",
        inputs={"path": str(workspace / "blocked.txt"), "content": "safe\n"},
    )
    second_envelope = _request_approval(app, second_write["preview_id"])
    with pytest.raises(HTTPException) as revoked:
        _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
            Mark3VoiceApprovalStartRequest(
                approval_id=second_envelope["approval_id"],
                device_id=paired["device"]["device_id"],
                readback_text=second_envelope["readback_text"],
            )
        )
    assert revoked.value.status_code == 400
    assert {"voice_approval_accepted", "remote_pairing_revoked", "dispatch_completed"} <= _event_types(ledger)
    assert calls == []
