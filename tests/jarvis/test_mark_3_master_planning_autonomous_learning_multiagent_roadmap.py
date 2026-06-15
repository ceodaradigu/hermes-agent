from __future__ import annotations

import builtins
import json
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import create_app
from jarvis.mark_3_master_planning import (
    get_mark_3_capability_areas,
    get_mark_3_execution_principles,
    get_mark_3_guardrails,
    get_mark_3_macro_roadmap,
    get_mark_3_planning_status,
    get_mark_3_readiness,
    get_mark_3_risk_approval_model,
)


GET_ROUTES = (
    "/mark-3/planning/status",
    "/mark-3/planning/principles",
    "/mark-3/planning/risk-approval-model",
    "/mark-3/planning/capabilities",
    "/mark-3/planning/roadmap",
    "/mark-3/planning/guardrails",
    "/mark-3/planning/pilot-plan",
    "/mark-3/planning/readiness",
)
FORBIDDEN_ROUTE_PARTS = (
    "/execute",
    "/approve",
    "/deploy",
    "/pay",
    "/send-email",
    "/publish",
    "/modify-dns",
    "/run-codex",
    "/run-claude",
    "/read-env",
    "/credentials",
)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True).lower()


def _route(app, path):
    return next(route for route in app.routes if route.path == path)


def test_status_defines_mark_3_as_universal_governed_execution_not_permanent_read_only():
    status = get_mark_3_planning_status()

    assert status["current_mark"] == "Mark 3 Planning"
    assert status["mark_3_is_not_read_only"] is True
    assert status["mark_3_is_not_preview_only"] is True
    assert status["preview_first_default"] is True
    assert status["universal_governed_execution"] is True
    assert status["planning_only_in_this_pr"] is True
    assert status["real_mark_3_execution_enabled_now"] is False


def test_principles_block_by_default_but_allow_validly_approved_supported_execution():
    payload = _serialized(get_mark_3_execution_principles())

    assert "blocked by default, executable with valid approval" in payload
    assert "preview and read-only are the default starting state, not the permanent ceiling" in payload
    assert "must not be cowardly" in payload
    assert "must not be dishonest" in payload
    assert "permission cannot create a capability" in payload


def test_risk_approval_model_contains_levels_zero_through_five_and_scaled_controls():
    model = get_mark_3_risk_approval_model()
    levels = {item["level"]: item for item in model["levels"]}

    assert set(levels) == set(range(6))
    assert levels[0]["intent_inference_allowed"] is True
    assert levels[1]["approval_requirement"] == "Direct instruction or contextual approval"
    assert levels[1]["intent_inference_allowed"] is True
    assert levels[3]["approval_requirement"] == "Explicit strong approval"
    assert "strong approval" in levels[3]["required_controls"]
    for control in ("readback", "double confirmation", "rollback or stop plan", "audit", "visible human control", "kill switch"):
        assert control in levels[4]["required_controls"]
    assert "triple confirmation when very high risk" in levels[4]["required_controls"]
    assert levels[5]["executable_with_valid_approval"] is False


def test_wake_phrase_and_inferred_intent_never_authorize_sensitive_actions():
    model = get_mark_3_risk_approval_model()
    serialized = _serialized(model)

    assert model["wake_phrase_is_permission"] is False
    assert model["sensitive_actions_never_use_inferred_permission"] is True
    assert "only for low-risk, non-sensitive actions" in serialized


def test_authorized_account_recovery_is_allowed_but_security_bypass_is_permanently_denied():
    capabilities = _serialized(get_mark_3_capability_areas())
    guardrails = get_mark_3_guardrails()
    serialized = _serialized(guardrails)
    permanent = {item["guardrail_id"] for item in guardrails["guardrails"] if item["permanent_denial"]}

    assert "official recovery" in capabilities
    assert "owned or authorized accounts" in capabilities
    assert "family-authorized workflows" in capabilities
    assert "never bypass security" in capabilities
    for text in ("unauthorized access", "credential theft", "cookie or token theft", "bypassing 2fa"):
        assert text in serialized
    assert "security_bypass_denied" in permanent


def test_moonshots_are_allowed_without_false_claims_or_fake_capability():
    capabilities = _serialized(get_mark_3_capability_areas())
    guardrails = _serialized(get_mark_3_guardrails())
    principles = _serialized(get_mark_3_execution_principles())

    for text in ("hard and unsolved problems", "hypotheses", "prototype", "evidence scoring", "uncertainty"):
        assert text in f"{capabilities}\n{guardrails}"
    assert "no overclaiming" in capabilities
    assert "never claim success, capability, evidence, costs, or revenue without proof" in principles
    assert "unsupported work may become research or a prototype" in principles


def test_capabilities_cover_multi_agent_learning_revenue_measurement_and_local_first():
    payload = get_mark_3_capability_areas()
    capabilities = {item["capability_id"]: item for item in payload["capabilities"]}
    serialized = _serialized(payload)

    for capability_id in (
        "universal_governed_execution",
        "autonomous_mission_loop",
        "continuous_learning",
        "multi_agent_orchestration",
        "product_revenue_factory",
        "routine_scheduler",
        "account_credential_assistance",
        "moonshot_lab",
        "measurement_roi",
        "local_first_infrastructure",
    ):
        assert capability_id in capabilities
    for agent in ("planneragent", "builderagent", "revieweragent", "testeragent", "operatoragent", "securityagent", "legalriskagent", "toolrouteragent"):
        assert agent in serialized
    assert "no_fake_costs" in serialized and "no_fake_revenue" in serialized
    assert "no mac mini now" in serialized and "no vps now" in serialized
    assert "revenue threshold or demonstrated technical necessity" in serialized


def test_roadmap_is_large_coherent_macro_prs_from_132_through_141():
    roadmap = get_mark_3_macro_roadmap()
    items = roadmap["items"]

    assert [item["pr_number"] for item in items] == list(range(132, 142))
    assert roadmap["roadmap_strategy"] == "Large coherent macro-PRs; no micro-PR explosion."
    assert len(items) == 10
    assert items[0]["planning_only"] is True
    assert all(item["major_deliverables"] and item["exit_criteria"] for item in items)


def test_readiness_is_honest_about_planning_and_future_execution():
    readiness = get_mark_3_readiness()

    assert readiness["planning_pr_ready"] is True
    assert readiness["mark_3_execution_ready_now"] is False
    assert readiness["free_autonomy_ready"] is False
    assert readiness["production_ready"] is False
    assert "PR #133" in readiness["next_macro_pr"]


def test_planning_endpoints_return_200_safe_payloads_without_real_tools(monkeypatch):
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
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))

    for path in GET_ROUTES:
        route = _route(app, path)
        assert route.methods == {"GET"}
        assert route.status_code in (None, 200)
        payload = route.endpoint()
        assert payload["safe_to_render"] is True


def test_mark_3_planning_routes_remain_read_only_when_mission_loop_routes_are_added():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    mark_3_routes = [route for route in app.routes if route.path.startswith("/mark-3/planning/")]

    assert {route.path for route in mark_3_routes} == set(GET_ROUTES)
    assert all(route.methods == {"GET"} for route in mark_3_routes)
    for route in mark_3_routes:
        assert not any(part in route.path for part in FORBIDDEN_ROUTE_PARTS)


def test_master_document_covers_required_mark_3_policy_and_architecture():
    document = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    serialized = document.lower()

    for text in (
        "universal governed execution",
        "jarvis no debe ser cobarde, pero tampoco mentiroso",
        "wake phrase",
        "authorized account recovery",
        "moonshot",
        "multi-agent",
        "autonomous mission loop",
        "continuous learning",
        "product and revenue factory",
        "no mac mini",
        "no vps",
        "no fake costs",
        "no fake revenue",
        "pr #132",
        "pr #140",
    ):
        assert text in serialized
