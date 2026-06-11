from __future__ import annotations

import builtins
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")

from jarvis.adaptive_saas_builder import (
    AdaptiveSaaSBuilder,
    AdaptiveSaaSBuilderStatus,
    adaptive_saas_builder_markers,
)
from jarvis.api.app import ProductBuilderPreviewRequest, create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_console_summary, build_operational_system_status
from jarvis.product_blueprint import CapabilityBlockPlan, RepoScaffoldPlan, SaaSProductBlueprint, TechStackRecommendation
from jarvis.product_validation_engine import DifferentiationReview, ProductIdeaIntake, ProductValidationPreview
from jarvis.publishing_deploy_control import DeployExecutionPlan, PublishingPlan
from jarvis.saas_execution_candidates import ProductExecutionCandidate
from jarvis.wake_voice_runtime import WakeVoiceRuntime


DOC = Path("docs/jarvis-post-s-adaptive-saas-builder-publishing-deploy-execution.md")
DANGEROUS_ROUTES = (
    "/product-builder/create-repo", "/product-builder/write-files", "/product-builder/publish",
    "/product-builder/deploy", "/product-builder/deploy-production", "/product-builder/run",
    "/product-builder/execute", "/product-builder/call-github", "/product-builder/call-vercel",
    "/product-builder/call-render", "/product-builder/call-stripe", "/product-builder/auto-approve",
    "/product-builder/approve-all",
)


def _route(app, path, method):
    return next((route for route in app.routes if route.path == path and method in route.methods), None)


def _ready(**overrides):
    values = {
        "valid_approval_present": True,
        "strong_approval_present": True,
        "double_confirmation_present": True,
        "context_fingerprint_matches": True,
        "permission_gates_passed": True,
        "audit_present": True,
        "rollback_or_stop_plan_present": True,
    }
    values.update(overrides)
    return values


def test_status_policy_and_safe_defaults_define_adaptive_not_template_builder():
    builder = AdaptiveSaaSBuilder()
    status = builder.status()
    policy = builder.policy()
    assert AdaptiveSaaSBuilderStatus().adaptive_saas_builder_available is True
    for name in ("adaptive_saas_builder_available", "product_builder_adaptativo_available", "reusable_patterns_are_guardrails", "capability_blocks_are_composable", "restrictions_are_approval_gates"):
        assert status[name] is True
    for name in ("template_builder_mode", "rigid_boilerplate_generation", "cloned_product_generation_allowed", "real_repo_creation_enabled", "real_filesystem_write_enabled", "real_publish_enabled", "real_deploy_enabled", "external_platform_calls_enabled"):
        assert status[name] is False
    assert "twins" in policy["quality_rule"]
    assert policy["wake_phrase_is_not_builder_or_deploy_permission"] is True
    assert policy["scheduler_due_is_not_builder_or_deploy_permission"] is True
    assert policy["memory_active_is_not_builder_or_deploy_permission"] is True


def test_idea_intake_preserves_unknowns_and_does_not_invent_budget():
    intake = ProductIdeaIntake.from_request({"idea_summary": "Reduce agency reporting time"}).to_dict()
    assert intake["budget_limit"] is None
    assert {"target_customer", "budget_limit", "timeline"} <= set(intake["unknowns"])
    assert intake["clarification_needed"] is True


def test_validation_is_contrarian_and_does_not_invent_market_demand():
    preview = ProductValidationPreview.from_request({"niche": "agencies", "target_customer": "small agencies"}).to_dict()
    assert preview["no_fake_market_claims"] is True
    assert preview["willingness_to_pay_estimate"].startswith("unknown")
    assert preview["recommendation"] in {"refine", "reject"}
    assert preview["red_flags"]


def test_differentiation_blocks_generic_clone_products():
    review = DifferentiationReview.from_request({"looks_like_common_boilerplate": True, "products_could_look_like_twins": True}).to_dict()
    assert review["generic_template_risk"] is True
    assert review["clone_risk"] is True
    assert review["quality_gate_passed"] is False
    assert review["recommendation"] in {"refine", "reject"}


def test_capability_blocks_are_composable_justified_and_not_inflated():
    plan = CapabilityBlockPlan.from_request({"frontend_block_needed": True, "tests_block_needed": True, "security_block_needed": True}).to_dict()
    assert plan["rigid_template_used"] is False
    assert plan["reusable_patterns_used_as_guardrails"] is True
    assert "frontend" in plan["selected_blocks"]
    assert "payments" in plan["omitted_blocks"]
    assert plan["why_each_block_is_needed"]["frontend"]
    assert plan["why_each_block_is_not_needed"]["payments"]


def test_blueprint_has_concrete_bounded_mvp_monetization_and_quality_gate():
    blueprint = SaaSProductBlueprint.from_request(
        {
            "product_name": "Agency Signal",
            "differentiation": "Flags client-risk changes before weekly reporting",
            "reason_to_exist": "Small agencies miss churn signals hidden across project updates",
            "mvp_scope": ["ingest weekly project status", "show client risk changes"],
            "risks": ["false positives"],
            "assumptions": ["agencies review weekly"],
            "unknowns": ["preferred integrations"],
            "pricing": {"name": "Starter", "price_amount": 19},
        }
    ).to_dict()
    assert blueprint["quality_gate_passed"] is True
    assert len(blueprint["mvp_scope"]) <= 10
    assert blueprint["differentiation"] != "unknown"
    assert blueprint["reason_to_exist"] != "unknown"
    assert blueprint["pricing_preview"]["live_billing_enabled"] is False
    failed = SaaSProductBlueprint.from_request({"mvp_scope": ["generic dashboard"]}).to_dict()
    assert failed["quality_gate_passed"] is False


def test_stack_prioritizes_low_cost_and_marks_paid_services_for_approval():
    free = TechStackRecommendation.from_request({}).to_dict()
    paid = TechStackRecommendation.from_request({"paid_services_needed": ["managed database"], "estimated_monthly_cost": 20}).to_dict()
    assert free["free_tier_possible"] is True
    assert free["why_this_stack"]
    assert paid["approval_required_for_paid_services"] is True
    assert "credentials are not assumed or loaded" in paid["risk_notes"]


def test_scaffold_is_product_specific_preview_and_never_writes_or_creates_repo():
    plan = RepoScaffoldPlan.from_request(
        {"repo_name": "agency-signal", "product_specific_files": ["risk-scoring-rules.md"], "product_specific_tests": ["test_risk_signal.py"], "secrets_required": ["DATABASE_URL"]}
    ).to_dict()
    assert plan["would_create_repo"] is False
    assert plan["would_write_files"] is False
    assert plan["secrets_required"] == ["DATABASE_URL"]
    assert plan["product_specific_files"] and plan["product_specific_tests"]


def test_landing_copy_avoids_false_claims_and_requires_differentiation_to_be_ready():
    plan = AdaptiveSaaSBuilder().preview_landing({"headline": "See client risk earlier", "target_customer": "small agencies", "differentiation_section": "Change-focused risk signals", "claims_verified": True})
    assert plan["publish_ready"] is True
    assert any("false guarantees" in note for note in plan["trust_notes"])
    assert plan["differentiation_section"]


def test_publishing_never_publishes_and_production_requires_strong_double_and_rollback():
    blocked = PublishingPlan.from_request({"environment": "production", "valid_approval_present": True}).to_dict()
    eligible = PublishingPlan.from_request({**_ready(), "environment": "production", "rollback_or_unpublish_plan": ["restore previous release"]}).to_dict()
    assert blocked["would_publish"] is False and blocked["would_call_external"] is False
    assert blocked["strong_approval_required"] is True and blocked["double_confirmation_required"] is True
    assert blocked["eligible_after_valid_approval"] is False
    assert eligible["eligible_after_valid_approval"] is True


def test_deploy_never_executes_and_production_requires_all_global_gates():
    blocked = DeployExecutionPlan.from_request({"environment": "production", "valid_approval_present": True}).to_dict()
    eligible = DeployExecutionPlan.from_request({**_ready(), "environment": "production", "rollback_plan": ["restore prior artifact"]}).to_dict()
    assert blocked["would_deploy"] is False and blocked["execution_allowed"] is False and blocked["would_touch_production"] is False
    assert "required rollback or stop plan is missing" in blocked["blocked_reasons"]
    assert eligible["eligible_after_valid_approval"] is True
    assert eligible["execution_candidate"] is True


def test_execution_candidate_integrates_semantics_but_never_executes_calls_or_writes():
    candidate = ProductExecutionCandidate.from_request({**_ready(), "action_type": "deploy_backend", "environment": "production"}).to_dict()
    assert candidate["eligible_after_valid_approval"] is True
    assert candidate["execution_allowed"] is False
    assert candidate["would_execute"] is False
    assert candidate["would_call_external"] is False
    assert candidate["would_modify_filesystem"] is False
    assert candidate["would_touch_production"] is False
    assert candidate["audit_required"] is True


def test_action_preview_never_performs_any_builder_side_effect():
    preview = AdaptiveSaaSBuilder().preview_action({**_ready(), "action_type": "plan_deploy", "environment": "production"})
    assert preview["eligible_after_valid_approval"] is True
    for name in ("would_execute", "would_call_external", "would_write_files", "would_create_repo", "would_publish", "would_deploy"):
        assert preview[name] is False


def test_hostile_manual_construction_cannot_enable_forbidden_side_effects():
    status = AdaptiveSaaSBuilderStatus(template_builder_mode=True, real_deploy_enabled=True, external_platform_calls_enabled=True)
    candidate = ProductExecutionCandidate(
        candidate_id="hostile", action_type="deploy_backend", target="production", environment="production",
        risk_level="critical", approval_required=True, strong_approval_required=True,
        double_confirmation_required=True, valid_approval_present=True, eligible_after_valid_approval=True,
        execution_allowed=True, would_execute=True, would_call_external=True, would_modify_filesystem=True,
        would_touch_production=True, audit_required=False, rollback_or_stop_plan_required=True,
        rollback_or_stop_plan_present=True,
    )
    assert status.template_builder_mode is False
    assert status.real_deploy_enabled is False
    assert status.external_platform_calls_enabled is False
    assert candidate.execution_allowed is False
    assert candidate.would_execute is False
    assert candidate.would_call_external is False
    assert candidate.would_modify_filesystem is False
    assert candidate.would_touch_production is False
    assert candidate.audit_required is True


def test_launch_readiness_blocks_safety_differentiation_approval_and_rollback():
    review = AdaptiveSaaSBuilder().preview_launch_readiness({"environment": "production"})
    assert review["blockers"]
    assert any("legal" in item for item in review["blockers"])
    assert any("privacy" in item for item in review["blockers"])
    assert any("security" in item for item in review["blockers"])
    assert any("differentiation" in item for item in review["blockers"])
    assert any("approval" in item for item in review["blockers"])
    assert any("rollback" in item for item in review["blockers"])
    assert review["warnings"]


def test_control_plane_endpoints_exist_and_are_side_effect_free(monkeypatch):
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
    for path in ("/product-builder/status", "/product-builder/policy"):
        route = _route(app, path, "GET")
        assert route is not None and route.status_code in (None, 200)
        route.endpoint()
    for suffix in ("intake", "validation", "differentiation", "capability-blocks", "blueprint", "stack", "scaffold", "landing", "publishing", "deploy", "execution-candidate", "launch-readiness", "action"):
        route = _route(app, f"/product-builder/preview-{suffix}", "POST")
        assert route is not None and route.status_code in (None, 200)
        payload = route.endpoint(ProductBuilderPreviewRequest())
        assert payload.get("would_execute", False) is False
        assert payload.get("would_call_external", False) is False
        assert payload.get("would_write_files", False) is False
        assert payload.get("would_publish", False) is False
        assert payload.get("would_deploy", False) is False
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_expose_builder_markers():
    status = build_operational_system_status().to_dict()
    summary = build_operational_console_summary()
    command = build_command_center_view_model(view_id="builder", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="builder", generated_at="2026-06-11T00:00:00+00:00")
    for marker in adaptive_saas_builder_markers():
        assert summary["command_center"][marker] is True
        assert command.metadata[marker] is True
        assert operator.metadata[marker] is True
    assert status["adaptive_saas_builder_available"] is True
    assert status["template_builder_mode"] is False
    assert status["real_deploy_enabled"] is False


def test_wake_phrase_scheduler_due_and_memory_active_are_not_deploy_permission():
    wake = WakeVoiceRuntime().parse("Jarvis crea y despliega este SaaS").to_dict()
    policy = AdaptiveSaaSBuilder().policy()
    assert wake["wake_phrase_is_not_permission"] is True
    assert wake["execution_enabled"] is False
    assert policy["scheduler_due_is_not_builder_or_deploy_permission"] is True
    assert policy["memory_active_is_not_builder_or_deploy_permission"] is True


def test_documentation_defines_adaptive_quality_rule_boundaries_and_next_macro():
    content = DOC.read_text(encoding="utf-8")
    for text in (
        "Product Builder Adaptativo", "Adaptive SaaS Builder", "no es Phase T",
        "Restrictions are approval gates, not permanent bans", "hermanos gemelos",
        "Post-S Macro 10", "/product-builder/preview-deploy",
    ):
        assert text in content
