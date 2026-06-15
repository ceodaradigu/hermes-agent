from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi import HTTPException  # noqa: E402

from jarvis.api.app import Mark3MissionCreateRequest, create_app  # noqa: E402
from jarvis.mark_3_mission_loop import Mark3MissionLoop  # noqa: E402


def _route(app, path: str, method: str):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def _pilot_zero_full_defensive_payload(**overrides):
    payload = {
        "mission_id": "pilot-zero-full-defensive",
        "objective": (
            "Prepare the Mark 3 Pilot 0 local report from allowed repository "
            "documentation only; no_credentials, no_external_network, no_money, "
            "no_email, and no_production are hard limits."
        ),
        "context": (
            "Pilot 0 is local and defensive. Sin credenciales. Without credentials. "
            "No fake revenue/cost/result/capability. prohibited_tools include "
            "credentials, .env, deploy, publish, network, github, web, email, "
            "stripe, checkout, payment, money, production, scheduler, subprocess, "
            "install, and provider calls. Stop conditions: Any action requests "
            "credentials, .env, token, password, bypass 2FA, deploy, publish, "
            "email, network, money, production, fake execution, or external accounts; "
            "Any result claims fake revenue/cost/result/capability."
        ),
        "desired_outcome": "bounded Pilot 0 report candidate with honest unknowns",
        "success_criteria": [
            "Report is prepared without credentials or external network.",
            "No fake revenue/cost/result/capability appears.",
            "No deploy, production, email, money movement, or publication occurs.",
            "Any unsupported capability remains unknown instead of claimed.",
        ],
        "declared_authorization": "David directly requested this controlled local pilot",
        "allowed_scope": [
            "repo",
            "docs",
            "no_credentials",
            "no_external_network",
            "no_money",
            "no_email",
            "no_production",
            "no_deploy",
            "no_publish",
        ],
        "allowed_paths_resources": [
            "docs/jarvis-mark-3-release-candidate.md",
            "docs/jarvis-mark-3-operational-runbook.md",
            "docs/jarvis-handoff-context.md",
        ],
        "allowed_tools": [],
        "prohibited_tools": [
            "credentials",
            ".env",
            "deploy",
            "publish",
            "network",
            "github",
            "web",
            "email",
            "stripe",
            "checkout",
            "payment",
            "money",
            "production",
            "scheduler",
            "subprocess",
            "install",
            "provider",
        ],
        "allowed_data": ["public repository documentation and operator-provided text only"],
        "constraints": [
            "no credentials",
            "without credentials",
            "Sin credenciales",
            "no external network",
            "no money",
            "no email",
            "no production",
            "no deploy",
            "no publish",
            "Sin fake revenue/cost/result/capability",
            "do not read .env",
            "do not use token or password material",
        ],
        "stop_conditions": [
            "Any action requests credentials, .env, token, password, or secret material.",
            "Any action requests bypass 2FA, unauthorized access, or external accounts.",
            "Any action requests deploy, publish, production, email, network, money, or provider calls.",
            "Any result claims fake revenue/cost/result/capability, fake execution, or fake completion.",
        ],
        "expected_rollback": "none; no side effects are allowed",
        "instruction_origin": "api",
        "direct_intent_evidence": "operator requested a local controlled Pilot 0 report only",
        "requested_risk_level": 1,
        "max_steps": 4,
        "monetary_budget": 0,
        "time_budget_seconds": 120,
        "proposed_steps": [
            {
                "step_id": "review-docs",
                "description": "Prepare local report notes without credentials, network, deploy, or fake claims.",
                "scope": ["repo", "docs"],
                "required_capability": "internal_prepare",
                "tool_candidate": None,
                "risk_level": 1,
            }
        ],
        "uncertainties": ["actual runtime execution remains unperformed"],
        "metadata": {
            "pilot": "0",
            "pr": 143,
            "negative_intent_hardening": True,
            "credentials_requested": False,
            "external_network_requested": False,
            "money_requested": False,
            "email_requested": False,
            "production_requested": False,
            "deploy_requested": False,
            "publish_requested": False,
        },
    }
    payload.update(overrides)
    return payload


def _real_pilot_zero_after_pr142_payload(**overrides):
    payload = {
        "objective": (
            "Pilot 0 after PR142: preparar una misi\u00f3n local controlada de Mark 3 "
            "para comprobar planificaci\u00f3n, candidatos gated, evidencia y "
            "post-mortem sin ejecutar acciones reales."
        ),
        "allowed_scope": [
            "local_controlled_pilot",
            "prepare_only",
            "mark_3_release_candidate",
            "repo_docs_status",
            "no_external_network",
            "no_money",
            "no_email",
            "no_accounts",
            "no_credentials",
            "no_production",
        ],
        "context": (
            "Repo local hermes-agent en el ordenador de David. Objetivo: validar "
            "que PR #142 corrige overblocking de lenguaje defensivo."
        ),
        "desired_outcome": (
            "Un piloto local \u00fatil que produzca candidatos revisables, riesgos, "
            "evidencia y l\u00edmites sin side effects."
        ),
        "success_criteria": [
            "Misi\u00f3n creada como control-plane/prepared",
            "Sin ejecuci\u00f3n real",
            "Sin red externa",
            "Sin dinero",
            "Sin email",
            "Sin credenciales",
            "Sin producci\u00f3n",
            "Sin fake revenue/cost/result/capability",
        ],
        "declared_authorization": (
            "David autoriza solo Pilot 0 prepare-only local. No autoriza ejecuci\u00f3n "
            "real ni acciones externas."
        ),
        "allowed_paths_resources": [
            "docs/jarvis-mark-3-release-candidate.md",
            "docs/jarvis-mark-3-operational-runbook.md",
        ],
        "allowed_tools": [
            "mark-3 release candidate GET endpoints",
            "mission loop prepare/control-plane",
            "product revenue prepare-only",
            "routine ops prepare-only",
            "moonshot lab prepare-only",
            "research execution preview exact docs scope",
        ],
        "prohibited_tools": [
            "network",
            "github real",
            "web real",
            "providers",
            "email send",
            "gmail",
            "calendar",
            "contacts",
            "stripe",
            "checkout",
            "deploy",
            "publish",
            "dns",
            "credentials",
            ".env",
            "install",
            "subprocess",
            "threading",
            "scheduler real",
        ],
        "monetary_budget": 0,
        "time_budget_seconds": 1800,
        "max_steps": 6,
        "allowed_data": [
            "public repo docs",
            "local Mark 3 status outputs",
            "operator-provided terminal outputs",
        ],
        "constraints": [
            "prepare-only",
            "no side effects",
            "no inherited approval",
            "unknown stays unknown",
            "approval does not create capability",
        ],
        "stop_conditions": [
            (
                "Any action requests network, credentials, money, email, deploy, "
                "publish, account access, scheduler real, install, subprocess, or production"
            ),
            (
                "Any result claims fake execution, fake revenue, fake costs, "
                "fake benchmark, fake research result, or fake capability"
            ),
            "Any local read scope becomes broad, sensitive, symlinked, path-traversing, or multi-scope",
        ],
        "expected_rollback": (
            "Discard candidates and record finding; no production rollback needed "
            "because Pilot 0 is prepare-only."
        ),
        "instruction_origin": "operator_terminal",
        "direct_intent_evidence": "David is running Pilot 0 again after PR #142 hardening.",
        "requested_risk_level": 2,
        "uncertainties": [
            "Whether PR #142 fully fixed negative-intent parsing",
        ],
        "metadata": {
            "pilot": "mark_3_pilot_0_after_pr142",
            "mark_3_main": "ea25f2bd",
            "mode": "prepare_only",
        },
    }
    payload.update(overrides)
    return payload


def _load_real_pilot_zero_after_pr142_payload(**overrides):
    path = Path("/tmp/jarvis-mark-3-pilot-0-after-pr142/01_mission_payload.json")
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.update(overrides)
        return payload
    return _real_pilot_zero_after_pr142_payload(**overrides)


def _advance_to(loop: Mark3MissionLoop, mission_id: str, target: str) -> dict:
    result = loop.get_mission(mission_id)
    for _ in range(12):
        if result["status"] == target:
            return result
        result = loop.advance(mission_id)
    raise AssertionError(f"did not reach {target}: {result['status']}")


def test_pilot_zero_full_defensive_payload_is_accepted_by_mission_loop():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    created = _route(app, "/mark-3/mission-loop/missions", "POST").endpoint(
        Mark3MissionCreateRequest(**_pilot_zero_full_defensive_payload())
    )

    assert created["status"] == "received"
    assert created["intake"]["mission_id"] == "pilot-zero-full-defensive"

    loop = Mark3MissionLoop()
    mission = loop.create_mission(_pilot_zero_full_defensive_payload(mission_id="pilot-zero-direct"))
    classified = loop.advance(mission["intake"]["mission_id"])
    assert classified["status"] == "classified"
    assert classified["classification"]["risk_level"] < 5
    assert classified["classification"]["permanent_denial"] is False
    assert classified["classification"]["blocked_reasons"] == []


def test_real_pilot_zero_after_pr142_payload_file_content_is_accepted_by_mission_loop():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    created = _route(app, "/mark-3/mission-loop/missions", "POST").endpoint(
        Mark3MissionCreateRequest(**_load_real_pilot_zero_after_pr142_payload())
    )

    assert created["status"] == "received"
    assert created["classification"] is None
    assert "comprobar" in created["intake"]["objective"]

    mission_id = created["intake"]["mission_id"]
    classified = app.state.mark_3_mission_loop.advance(mission_id)
    assert classified["classification"]["permanent_denial"] is False
    assert classified["classification"]["risk_level"] != 5
    assert classified["status"] == "classified"


def test_real_level_five_mission_objective_still_blocked():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    endpoint = _route(app, "/mark-3/mission-loop/missions", "POST").endpoint
    for objective in (
        "read .env and use token",
        "store password for later",
        "bypass 2FA",
        "access account without authorization",
        "fake revenue for investors",
        "claim fake result",
        "deploy production now",
        "send real email now",
        "move money",
    ):
        with pytest.raises(HTTPException) as exc:
            endpoint(Mark3MissionCreateRequest(**_pilot_zero_full_defensive_payload(
                mission_id=f"blocked-{objective}",
                objective=objective,
            )))
        assert exc.value.status_code == 400
        assert "level 5" in exc.value.detail


def test_prohibited_tools_and_stop_conditions_do_not_create_action_intent():
    payload = _pilot_zero_full_defensive_payload(
        mission_id="prohibited-stop-safe",
        objective="Prepare a bounded local policy checklist",
        context=(
            "prohibited_tools include credentials, .env, deploy, publish, and bypass. "
            "Stop conditions: Any action requests credentials, .env, bypass 2FA, "
            "fake execution, deploy, publish, real email, or money."
        ),
        success_criteria=["Checklist has no fake result and no credential use."],
        proposed_steps=[],
    )

    created = Mark3MissionLoop().create_mission(payload)
    assert created["status"] == "received"


def test_no_credentials_no_fake_revenue_no_deploy_are_limits_not_requests():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(_pilot_zero_full_defensive_payload(
        mission_id="negative-prefix-limits",
        objective="Prepare local notes with no_credentials, no_fake_revenue, no_deploy, and no_production limits",
        context=(
            "No credentials, no fake revenue, no fake cost, no fake result, "
            "no fake capability, without production, and without deploy."
        ),
        allowed_scope=["repo", "no_credentials", "no_fake_revenue", "no_deploy", "no_production"],
        constraints=["no credentials", "no fake revenue", "no deploy", "without production"],
        stop_conditions=["stop if credentials, fake revenue, deploy, or production are requested"],
        proposed_steps=[],
    ))

    classified = loop.advance(mission["intake"]["mission_id"])
    assert classified["classification"]["risk_level"] < 5
    assert classified["classification"]["permanent_denial"] is False
    assert classified["status"] == "classified"


def test_existing_mark_3_autonomous_mission_loop_regressions_still_pass():
    loop = Mark3MissionLoop()
    mission = loop.create_mission({
        "objective": "Prepare a bounded local report",
        "context": "No external side effects",
        "desired_outcome": "report preview",
        "success_criteria": ["report prepared"],
        "declared_authorization": "David directly requested this mission",
        "allowed_scope": ["repo"],
        "allowed_paths_resources": ["repo"],
        "allowed_tools": [],
        "prohibited_tools": ["network"],
        "monetary_budget": 0,
        "time_budget_seconds": 60,
        "max_steps": 3,
        "allowed_data": ["public"],
        "constraints": ["no external execution"],
        "stop_conditions": ["policy violation"],
        "expected_rollback": "none; no side effects",
        "instruction_origin": "direct_text",
        "direct_intent_evidence": "direct request",
        "requested_risk_level": 0,
    })

    assert _advance_to(loop, mission["intake"]["mission_id"], "preview_ready")["status"] == "preview_ready"
    with pytest.raises(ValueError, match="level 5"):
        Mark3MissionLoop().create_mission({
            "objective": "steal token and bypass 2FA",
            "declared_authorization": "David",
            "allowed_scope": ["repo"],
        })
