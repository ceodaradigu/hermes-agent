from __future__ import annotations

import builtins
import json
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.mark_2_dangerous_route_audit import Mark2DangerousRouteAudit
from jarvis.routine_execution_bridge import RoutineExecutionBridge


PILOT_PAYLOAD = {
    "routine_type": "ai_coding",
    "task_summary": "Analizar el repo local de JARVIS y preparar un plan de mejora sin editar archivos.",
    "preferred_mode": "local_first_preview",
    "repo": "ceodaradigu/hermes-agent",
    "worktree": "/mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent",
    "allow_real_execution": False,
    "allow_file_write": False,
    "allow_network": False,
    "allow_codex_real": False,
    "allow_claude_real": False,
    "allow_deploy": False,
    "allow_money": False,
    "expected_outputs": ["summary", "improvement_plan", "risk_review", "audit"],
}


def _client() -> TestClient:
    return TestClient(create_app(adapter_factory=lambda: pytest.fail("Hermes called")))


def test_pilot_payload_returns_safe_local_first_preview(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: pytest.fail("filesystem write"))
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            pytest.fail(".env read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    response = _client().post("/mark-2/routine-execution/preview", json=PILOT_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["preferred_mode"] == "local_first_preview"
    assert payload["selected_adapter"] == "LocalScriptAdapter"
    assert payload["selected_adapter_mode"] == "preview_only"
    assert payload["adapter_selection_respected_user_flags"] is True
    assert payload["would_execute"] is False
    assert payload["real_invocation_allowed"] is False
    for name in (
        "file_write_allowed",
        "network_allowed",
        "codex_real_allowed",
        "claude_real_allowed",
        "deploy_allowed",
        "money_allowed",
    ):
        assert payload[name] is False
    assert payload["expected_outputs"] == PILOT_PAYLOAD["expected_outputs"]
    assert "AI CLI real invocation disabled by flags" in payload["reason_for_adapter_choice"]


def test_improvement_plan_is_payload_only_and_never_claims_repo_findings():
    payload = RoutineExecutionBridge.preview(**PILOT_PAYLOAD).to_dict()
    plan = payload["improvement_plan_preview"]
    serialized = json.dumps(plan).lower()

    assert plan["mode"] == "preview_only"
    assert plan["will_edit_files"] is False
    assert plan["will_invoke_ai_cli"] is False
    assert plan["requires_real_execution_for_deeper_analysis"] is True
    assert "repository not inspected" in plan["based_on"]
    assert "found bug" not in serialized
    assert "identified bug" not in serialized


def test_risk_review_and_audit_summary_confirm_no_side_effects():
    payload = RoutineExecutionBridge.preview(**PILOT_PAYLOAD).to_dict()
    risk = payload["risk_review"]
    audit = payload["audit_summary"]

    for name in (
        "no_production",
        "no_money",
        "no_deploy",
        "no_email",
        "no_dns",
        "no_codex_or_claude_real",
        "no_file_write",
        "no_network",
    ):
        assert risk[name] is True
    assert risk["would_execute"] is False
    assert audit == {
        "audit_required": True,
        "external_call_made": False,
        "real_tool_invoked": False,
        "file_write_made": False,
        "access_material_read": False,
        "safe_to_render": True,
    }


def test_subscription_cli_respects_ai_cli_flags_and_stays_preview_only():
    blocked = RoutineExecutionBridge.preview(
        routine_type="ai_coding",
        preferred_mode="subscription_cli",
        allow_codex_real=False,
        allow_claude_real=False,
    )
    codex = RoutineExecutionBridge.preview(
        routine_type="ai_coding",
        preferred_mode="subscription_cli",
        allow_codex_real=True,
        allow_real_execution=True,
    )

    assert blocked.selected_adapter == "LocalScriptAdapter"
    assert blocked.selected_adapter_mode == "preview_only"
    assert codex.selected_adapter == "Codex CLI"
    assert codex.selected_adapter_mode == "preview_only"
    assert codex.codex_real_allowed is True
    assert codex.real_invocation_allowed is False
    assert codex.would_execute is False


def test_api_fallback_without_network_is_blocked_and_unknown_mode_is_conservative():
    api = RoutineExecutionBridge.preview(
        routine_type="external_api",
        preferred_mode="api_fallback",
        allow_network=False,
        allow_real_execution=True,
    )
    unknown = RoutineExecutionBridge.preview(
        routine_type="ai_coding",
        preferred_mode="unexpected_mode",
        allow_codex_real=True,
        allow_real_execution=True,
    )

    assert api.selected_adapter == "ApiFallbackAdapter"
    assert api.selected_adapter_mode == "blocked"
    assert api.network_allowed is False
    assert api.real_invocation_allowed is False
    assert api.would_execute is False
    assert api.policy_decision == "blocked"
    assert api.eligible_after_valid_approval is False
    assert any("allow_network is required" in item for item in api.unmet_requirements)
    assert unknown.selected_adapter == "LocalScriptAdapter"
    assert unknown.selected_adapter_mode == "preview_only"
    assert unknown.would_execute is False
    assert "unknown preferred_mode" in unknown.unmet_requirements[0]


def test_external_operation_candidate_requires_network_and_operation_flag():
    deploy_without_network = RoutineExecutionBridge.preview(
        routine_type="deploy",
        allow_real_execution=True,
        allow_deploy=True,
        allow_network=False,
    )
    deploy_candidate = RoutineExecutionBridge.preview(
        routine_type="deploy",
        allow_real_execution=True,
        allow_deploy=True,
        allow_network=True,
    )

    assert deploy_without_network.selected_adapter_mode == "blocked"
    assert deploy_without_network.policy_decision == "blocked"
    assert deploy_without_network.eligible_after_valid_approval is False
    assert deploy_candidate.selected_adapter_mode == "candidate"
    assert deploy_candidate.would_execute is False
    assert deploy_candidate.real_invocation_allowed is False


def test_malformed_truthy_flag_strings_do_not_enable_real_candidates():
    payload = RoutineExecutionBridge.preview(
        routine_type="ai_coding",
        preferred_mode="subscription_cli",
        allow_real_execution="false",
        allow_codex_real="false",
        allow_claude_real="false",
        allow_network="false",
        allow_file_write="false",
    )

    assert payload.selected_adapter == "LocalScriptAdapter"
    assert payload.user_flags_summary["allow_real_execution"] is False
    assert payload.codex_real_allowed is False
    assert payload.claude_real_allowed is False
    assert payload.network_allowed is False
    assert payload.file_write_allowed is False


def test_command_center_remains_redacted_and_no_dangerous_routes_are_added():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    serialized = json.dumps(
        build_command_center_view_model(
            view_id="mark-2-pilot-findings",
            generated_at="2026-06-12T00:00:00+00:00",
        ).to_dict()
    ).lower()
    for forbidden in (
        ".env",
        "api_key",
        "apikey",
        "secret",
        "token",
        "password",
        "credential",
        "authorization",
        "audio_path",
        "audio_bytes",
        "ref_audio",
        "base_url",
        "prompt_text",
    ):
        assert forbidden not in serialized
    audit = Mark2DangerousRouteAudit().audit(route.path for route in app.routes)
    assert audit["passed"] is True
    assert audit["dangerous_routes_registered"] == []
