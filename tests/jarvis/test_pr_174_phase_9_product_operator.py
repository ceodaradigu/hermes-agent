import json
from pathlib import Path

import pytest

from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_9_product_operator import Phase9ProductOperatorControlPlane


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class FakeDeviceStore:
    def __init__(self):
        self.devices = {
            "trusted-phone": {
                "device_id": "trusted-phone",
                "trusted": True,
                "verified": True,
                "paired": True,
                "trust_status": "trusted",
            },
            "revoked-phone": {
                "device_id": "revoked-phone",
                "trusted": False,
                "verified": False,
                "paired": False,
                "trust_status": "revoked",
            },
        }

    def get_device(self, device_id):
        return self.devices.get(device_id)


class FakePhase7:
    def __init__(self):
        self.phase5_store = FakeDeviceStore()
        self.preview_calls = []

    def preview(self, **kwargs):
        self.preview_calls.append(kwargs)
        return {
            "schema_version": "jarvis.phase_7_governed_actions_browser_filesystem_github_sandbox.v1",
            "preview_id": f"preview-{len(self.preview_calls)}",
            "decision": "requires_approval",
            "requires_approval": True,
            "action": {"action_key": kwargs["action_key"]},
            "dispatch_performed": False,
            "would_write_file": False,
        }


class FakePhase8:
    def __init__(self):
        self.calls = []

    def prepare_deploy_candidate(self, **kwargs):
        self.calls.append(("deploy", kwargs))
        return {"candidate": {"category": "deploy", "prepare_only": True, "would_deploy": False, "would_call_provider": False}}

    def prepare_email_candidate(self, **kwargs):
        self.calls.append(("email", kwargs))
        return {"candidate": {"category": "email", "prepare_only": True, "would_send_email": False, "would_call_provider": False}}

    def prepare_payment_candidate(self, **kwargs):
        self.calls.append(("payment", kwargs))
        return {"candidate": {"category": "payment", "prepare_only": True, "would_create_checkout": False, "would_move_money": False}}

    def evaluate_budget_guard(self, **kwargs):
        self.calls.append(("budget", kwargs))
        return {"decision": "requires_explicit_approval", "can_spend": False}


def _operator(tmp_path):
    return Phase9ProductOperatorControlPlane(
        phase_7_actions=FakePhase7(),
        phase_8_external_ops=FakePhase8(),
        audit_ledger=PersistentAuditLedger(base_dir=tmp_path),
    )


def _valid_mission_payload(**overrides):
    payload = {
        "mission_id": "mission-alpha",
        "title": "Validate inbox triage niche",
        "goal": "Validate whether solo founders pay for a focused inbox triage assistant.",
        "expected_outcome": "A reviewed product candidate and evidence checklist.",
        "target_user_customer": "Solo founders with high support volume.",
        "hypothesis": "Founders will pay for reliable response prioritization.",
        "success_metric": "5 qualified manual validation replies.",
        "budget_limit": 25,
        "time_limit_seconds": 3600,
        "scope": ["prepare landing copy", "prepare email draft", "track evidence"],
        "allowed_tools_actions": ["product_builder", "experiment_planner", "revenue_tracker"],
        "forbidden_actions": ["send email", "deploy production", "create checkout"],
        "stop_conditions": ["budget exhausted", "time limit reached", "operator stops mission"],
    }
    payload.update(overrides)
    return payload


def test_product_mission_envelope_requires_scope_time_budget_and_stop_conditions(tmp_path):
    operator = _operator(tmp_path)

    envelope = operator.create_mission_envelope(_valid_mission_payload())

    assert envelope["schema_version"] == "jarvis.product_mission_envelope.v1"
    assert envelope["mission_id"] == "mission-alpha"
    assert envelope["budget_limit"] == 25.0
    assert envelope["time_limit_seconds"] == 3600
    assert envelope["scope"]
    assert envelope["allowed_tools_actions"]
    assert envelope["forbidden_actions"]
    assert envelope["stop_conditions"]
    assert envelope["approve_all_forever_allowed"] is False
    assert envelope["policy_engine_bypass_allowed"] is False
    assert envelope["approval_gateway_bypass_allowed"] is False
    assert envelope["budget_guard_required"] is True
    assert envelope["audit_id"]

    with pytest.raises(ValueError, match="stop_conditions"):
        operator.create_mission_envelope(_valid_mission_payload(stop_conditions=[]))

    with pytest.raises(ValueError, match="budget_limit"):
        operator.create_mission_envelope(_valid_mission_payload(budget_limit=None))

    with pytest.raises(ValueError, match="approve-all-forever|unlimited"):
        operator.create_mission_envelope(_valid_mission_payload(allowed_tools_actions=["approve all forever"]))


def test_product_builder_prepares_candidates_and_governed_file_previews_without_side_effects(tmp_path):
    operator = _operator(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    operator.create_mission_envelope(_valid_mission_payload())

    candidate = operator.prepare_product_builder(
        {
            "mission_id": "mission-alpha",
            "product_name": "Founder Inbox Radar",
            "problem": "Important customer replies are missed.",
            "target_customer": "solo founders",
            "value_proposition": "Prioritize customer replies before churn risk grows.",
            "local_project_path": str(workspace),
            "price_amount": 19,
            "projected_revenue": 500,
        }
    )

    assert candidate["prepare_only"] is True
    assert candidate["files_written"] is False
    assert candidate["would_publish"] is False
    assert candidate["would_deploy"] is False
    assert candidate["would_send_email"] is False
    assert candidate["would_create_checkout"] is False
    assert candidate["would_call_provider"] is False
    assert candidate["would_call_hermes"] is False
    assert candidate["local_project_scaffold_plan"]["phase_7_filesystem_action_key"] == "filesystem.file.write_safe"
    assert candidate["local_project_scaffold_plan"]["phase_7_governed_previews"]
    assert not any(workspace.rglob("PRODUCT_BRIEF.md"))
    assert {call[0] for call in operator.phase_8_external_ops.calls} >= {"deploy", "email", "payment"}


def test_money_roi_separates_projected_confirmed_cost_effort_confidence_and_risk(tmp_path):
    operator = _operator(tmp_path)

    decision = operator.evaluate_roi(
        {
            "title": "Founder Inbox Radar",
            "projected_revenue": 1000,
            "confirmed_revenue": 300,
            "cost_estimate": 50,
            "effort_estimate_hours": 10,
            "human_time_required_hours": 8,
            "confidence": "medium",
            "risks": ["crowded market", "deliverability unknown"],
            "dependencies": ["landing copy", "manual outreach"],
            "evidence": ["Stripe export row rev-1"],
        }
    )

    assert decision["decision_state"] in {"prepare", "build candidate", "launch candidate", "watch"}
    assert decision["financials"]["projected_revenue"]["is_projection"] is True
    assert decision["financials"]["confirmed_revenue"]["counts_as_confirmed"] is True
    assert decision["financials"]["projected_is_not_confirmed"] is True
    assert decision["score_inputs"]["cost_included"] is True
    assert decision["score_inputs"]["effort_included"] is True
    assert decision["score_inputs"]["confidence_included"] is True
    assert decision["score_inputs"]["risk_included"] is True

    missing_evidence = operator.evaluate_roi({"title": "fake claim", "confirmed_revenue": 999})
    assert missing_evidence["decision_state"] == "blocked"
    assert "confirmed revenue requires evidence/source" in missing_evidence["blocked_reasons"]
    assert missing_evidence["financials"]["confirmed_revenue"]["amount"] == "unknown"

    unknown_cost = operator.evaluate_roi({"title": "paid ads test", "spending_requested": True})
    assert unknown_cost["decision_state"] == "needs approval"
    assert unknown_cost["financials"]["unknown_cost_blocks_or_requires_strong_approval"] is True


def test_revenue_tracker_counts_only_confirmed_events_with_evidence_and_calculates_net(tmp_path):
    operator = _operator(tmp_path)

    projected = operator.record_revenue_event({"type": "projected", "amount": 1000, "currency": "EUR"})
    unconfirmed = operator.record_revenue_event({"type": "confirmed", "amount": 200, "currency": "EUR"})
    confirmed = operator.record_revenue_event(
        {"type": "confirmed", "amount": 300, "currency": "EUR", "evidence": ["Stripe test export row"]}
    )
    fee = operator.record_revenue_event({"type": "fee", "amount": 30, "currency": "EUR", "evidence": ["fee schedule"]})
    cost = operator.record_revenue_event({"type": "cost", "amount": 70, "currency": "EUR", "evidence": ["provider invoice"]})

    summary = operator.revenue_summary()

    assert projected["projected_revenue_counts_as_confirmed"] is False
    assert unconfirmed["status"] == "unconfirmed_missing_evidence"
    assert unconfirmed["counts_as_confirmed"] is False
    assert confirmed["counts_as_confirmed"] is True
    assert fee["type"] == "fee"
    assert cost["type"] == "cost"
    assert summary["projected_revenue"] == 1000.0
    assert summary["confirmed_revenue"] == 300.0
    assert summary["gross_revenue"] == 300.0
    assert summary["fees"] == 30.0
    assert summary["costs"] == 70.0
    assert summary["net_revenue"] == 200.0


def test_budget_guard_blocks_unknown_and_over_limit_cost_and_never_spends(tmp_path):
    operator = _operator(tmp_path)

    unknown = operator.evaluate_budget_guard({"spending_requested": True})
    assert unknown["decision"] == "blocked_unknown_cost"
    assert unknown["can_spend"] is False
    assert unknown["hard_stop"] is True

    over = operator.evaluate_budget_guard(
        {
            "global_monthly_product_budget": 100,
            "per_mission_budget": 50,
            "per_action_spending_limit": 25,
            "provider_cost_estimate": 80,
            "explicit_approval_present": True,
        }
    )
    assert over["decision"] in {
        "blocked_over_per_mission_budget",
        "blocked_over_per_action_limit",
        "blocked_over_global_monthly_product_budget",
    }
    assert over["can_spend"] is False
    assert over["memory_preferences_can_expand_budget"] is False
    assert over["phase_8_budget_guard"]["can_spend"] is False


def test_experiment_planner_is_prepare_only_and_external_channels_go_through_phase_8(tmp_path):
    operator = _operator(tmp_path)

    experiment = operator.plan_experiment(
        {
            "experiment_id": "exp-email",
            "hypothesis": "Founders reply to a narrow pain-point email.",
            "channel": "cold email",
            "target_audience": "solo founders",
            "asset_needed": "email draft",
            "cost_cap": 0,
            "time_window": "7 days",
            "success_metric": "3 replies",
            "expected_signal": "qualified pain confirmation",
            "send_requested": True,
        }
    )

    assert experiment["status"] == "approval_required"
    assert experiment["approval_requirement"] == "strong"
    assert experiment["prepare_only"] is True
    assert experiment["would_post"] is False
    assert experiment["would_email"] is False
    assert experiment["would_scrape"] is False
    assert experiment["would_publish"] is False
    assert experiment["would_spend"] is False
    assert experiment["phase_8_candidate"]["would_send_email"] is False


def test_self_improvement_cannot_weaken_policy_auto_merge_or_auto_deploy(tmp_path):
    operator = _operator(tmp_path)

    blocked = operator.propose_self_improvement(
        {
            "proposal_title": "Remove gates",
            "summary": "Remove ApprovalGateway, bypass tests, auto merge and auto deploy.",
        }
    )
    assert blocked["status"] == "blocked"
    assert blocked["would_remove_approval_gateway"] is False
    assert blocked["would_auto_merge"] is False
    assert blocked["would_auto_deploy"] is False
    assert blocked["would_bypass_tests"] is False
    assert blocked["blocked_reasons"]

    candidate = operator.propose_self_improvement(
        {
            "proposal_title": "Add product report tests",
            "summary": "Prepare tests for product operator report coverage.",
            "expected_value_score": 70,
        }
    )
    assert candidate["status"] == "prepared_candidate"
    assert candidate["can_prepare_patch_plan"] is True
    assert candidate["would_commit_push_open_pr_merge"] is False


def test_operator_report_manual_only_operating_loop_scoped_and_voice_approval_gated(tmp_path):
    operator = _operator(tmp_path)

    report = operator.generate_operator_report({"report_type": "daily_operator_report"})
    assert report["manual_trigger"] is True
    assert report["hidden_background_scheduler"] is False
    assert report["would_schedule_background_job"] is False
    assert report["would_execute"] is False

    blocked_loop = operator.prepare_operating_loop({"mission_id": "missing"})
    assert blocked_loop["status"] == "blocked"
    assert blocked_loop["run_forever"] is False

    mission = operator.create_mission_envelope(_valid_mission_payload(mission_id="mission-voice"))
    prepared_loop = operator.prepare_operating_loop({"mission_id": "mission-voice"})
    assert prepared_loop["status"] == "prepared"
    assert prepared_loop["stoppable"] is True
    assert prepared_loop["external_side_effects_without_approval"] is False

    not_trusted = operator.voice_approval_readiness(
        {
            "operation_id": mission["mission_id"],
            "device_id": "revoked-phone",
            "active_voice_session": True,
            "readback_text": mission["readback_text"],
            "challenge_phrase": mission["challenge_phrase"],
        }
    )
    assert not_trusted["voice_approval_available"] is False
    assert not_trusted["reason"] == "trusted_device_required"

    eligible = operator.voice_approval_readiness(
        {
            "operation_id": mission["mission_id"],
            "device_id": "trusted-phone",
            "active_voice_session": True,
            "readback_text": mission["readback_text"],
            "challenge_phrase": mission["challenge_phrase"],
        }
    )
    assert eligible["voice_approval_available"] is True
    assert eligible["wake_phrase_can_approve"] is False

    wrong_challenge = operator.voice_approval_readiness(
        {
            "operation_id": mission["mission_id"],
            "device_id": "trusted-phone",
            "active_voice_session": True,
            "readback_text": mission["readback_text"],
            "challenge_phrase": "wrong",
        }
    )
    assert wrong_challenge["voice_approval_available"] is False
    assert wrong_challenge["reason"] == "exact_challenge_required"


def test_frontend_exposes_phase_9_read_only_status_without_direct_product_execution_calls():
    sources = "\n".join(
        [
            (WEB / "src/lib/api.ts").read_text(encoding="utf-8"),
            (WEB / "src/components/jarvis/types.ts").read_text(encoding="utf-8"),
            (WEB / "src/components/jarvis/JarvisDebugDrawer.tsx").read_text(encoding="utf-8"),
        ]
    )

    assert "getJarvisPhase9Status" in sources
    assert "getJarvisProductOperatorStatus" in sources
    assert "Phase 9 Product Operator" in sources
    assert "Projected revenue is never counted as confirmed revenue." in sources
    assert "phase_9_state" in sources
    assert "product_operator_state" in sources
    for forbidden in (
        'fetchJSON("/mark-3/product-operator/missions"',
        'fetchJSON("/mark-3/product-operator/builder"',
        'fetchJSON("/mark-3/product-operator/operating-loop"',
        'fetchJSON("/execute"',
        'fetchJSON("/jarvis/execute"',
        "dispatchHermes",
    ):
        assert forbidden not in sources


def test_phase_9_api_dashboard_and_event_stream_contracts_when_fastapi_available(tmp_path, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    assert fastapi

    from jarvis.api.app import Mark3ProductOperatorRequest, create_app

    state_dir = tmp_path / "state"
    monkeypatch.setenv("JARVIS_LOCAL_STATE_DIR", str(state_dir))
    ledger = PersistentAuditLedger(base_dir=state_dir)
    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called by Phase 9"),
        hermes_runtime_adapter_factory=lambda _guard: pytest.fail("Hermes runtime adapter must not be created by Phase 9"),
        persistent_audit_ledger=ledger,
    )
    routes = {route.path for route in app.routes}

    assert "/mark-3/phase-9/status" in routes
    assert "/mark-3/product-operator/status" in routes
    assert "/execute" not in routes
    assert "/jarvis/execute" not in routes
    for route in routes:
        if route.startswith("/mark-3/product-operator"):
            assert not any(forbidden in route for forbidden in ("/execute", "/pay", "/deploy", "/send", "/publish", "/checkout"))

    def route(path, method="GET"):
        return next(item for item in app.routes if item.path == path and method in getattr(item, "methods", set()))

    phase9 = route("/mark-3/phase-9/status").endpoint()
    assert phase9["status"] == "implemented_as_governed_product_operator_prepare_only"
    assert phase9["security_gates"]["no_fake_revenue"] is True
    assert phase9["phase_integrations"]["phase_7_filesystem_action"] == "filesystem.file.write_safe"

    with pytest.raises(Exception):
        route("/mark-3/product-operator/missions", "POST").endpoint(
            Mark3ProductOperatorRequest(**_valid_mission_payload(stop_conditions=[]))
        )

    mission = route("/mark-3/product-operator/missions", "POST").endpoint(
        Mark3ProductOperatorRequest(**_valid_mission_payload(mission_id="api-mission"))
    )
    assert mission["mission_id"] == "api-mission"

    dashboard = route("/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_9_status"]["source_endpoint"] == "/mark-3/product-operator/status"
    assert dashboard["product_operator"]["security_gates"]["frontend_direct_hermes_allowed"] is False
    assert "Phase 9 Product Operator" in {module["name"] for module in dashboard["modules"]}

    events = route("/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in events["events"]}
    assert {
        "phase_9_state",
        "product_operator_state",
        "product_mission_state",
        "product_builder_state",
        "money_roi_state",
        "experiment_state",
        "revenue_tracker_state",
        "self_improvement_state",
        "operator_report_state",
    } <= event_types
    assert "sk_live_" not in json.dumps(events)
