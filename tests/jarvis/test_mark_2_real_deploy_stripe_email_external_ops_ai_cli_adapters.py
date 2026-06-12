import json

from jarvis.ai_cli_session_audit import build_external_operation_audit_event
from jarvis.api.app import Mark2ExternalOperationPreviewRequest, create_app
from jarvis.api_fallback_adapter import ApiFallbackAdapter
from jarvis.claude_code_adapter import ClaudeCodeAdapter
from jarvis.claude_cowork_adapter import ClaudeCoworkAdapter
from jarvis.codex_cli_adapter import CodexCliAdapter
from jarvis.command_center import build_command_center_view_model
from jarvis.mark_2_deploy_adapter import Mark2DeployAdapter
from jarvis.mark_2_domain_publishing_adapter import Mark2DomainPublishingAdapter
from jarvis.mark_2_email_adapter import Mark2EmailAdapter
from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine, mark_2_external_operations_markers
from jarvis.mark_2_stripe_adapter import Mark2StripeAdapter
from jarvis.operational_consolidation import build_operational_system_status
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.routine_execution_bridge import RoutineExecutionBridge
from jarvis.visual_command_center import VisualCommandCenter


SAFE_ROUTES = (
    ("GET", "/mark-2/external-ops/status"), ("GET", "/mark-2/external-ops/policy"),
    ("POST", "/mark-2/external-ops/preview-deploy"), ("POST", "/mark-2/external-ops/preview-stripe"),
    ("POST", "/mark-2/external-ops/preview-email"), ("POST", "/mark-2/external-ops/preview-domain"),
    ("GET", "/mark-2/ai-cli/status"), ("POST", "/mark-2/ai-cli/preview-codex"),
    ("POST", "/mark-2/ai-cli/preview-claude-code"), ("POST", "/mark-2/ai-cli/preview-claude-cowork"),
    ("POST", "/mark-2/ai-cli/preview-api-fallback"), ("POST", "/mark-2/routine-execution/preview"),
    ("GET", "/mark-2/external-ops/audit-preview"),
)
DANGEROUS_ROUTES = (
    "/mark-2/external-ops/deploy-real", "/mark-2/external-ops/stripe-live", "/mark-2/external-ops/pay",
    "/mark-2/external-ops/charge", "/mark-2/external-ops/send-email", "/mark-2/external-ops/modify-dns",
    "/mark-2/ai-cli/start-codex-real", "/mark-2/ai-cli/start-claude-real", "/mark-2/ai-cli/use-session-token",
    "/mark-2/ai-cli/steal-token", "/mark-2/ai-cli/use-cookies", "/mark-2/ai-cli/auto-approve",
    "/mark-2/ai-cli/approve-all", "/mark-2/routine-execution/run-any", "/mark-2/routine-execution/execute-free",
)
FORBIDDEN_COMMAND_CENTER = (
    ".env", "api_key", "apikey", "secret", "token", "password", "credential", "authorization",
    "audio_path", "audio_bytes", "ref_audio", "base_url", "prompt_text",
)


def _route(app, path, method):
    return next((route for route in app.routes if getattr(route, "path", None) == path and method in getattr(route, "methods", set())), None)


def test_all_macro_4_control_plane_endpoints_exist_and_dangerous_routes_do_not():
    app = create_app(adapter_factory=lambda: (_ for _ in ()).throw(AssertionError("Hermes called")))
    payload = Mark2ExternalOperationPreviewRequest()
    for method, path in SAFE_ROUTES:
        route = _route(app, path, method)
        assert route is not None
        result = route.endpoint() if method == "GET" else route.endpoint(payload)
        assert isinstance(result, dict)
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_status_and_markers_keep_all_real_external_operations_disabled():
    status = ExternalOperationsPolicyEngine().status()
    assert status["mark_2_macro"] == "Mark 2 Macro 4"
    for key in (
        "real_external_invocation_enabled", "real_deploy_enabled", "stripe_live_enabled", "email_send_enabled",
        "domain_publish_enabled", "codex_cli_real_invocation_enabled", "claude_code_real_invocation_enabled",
        "claude_cowork_real_invocation_enabled", "api_fallback_real_invocation_enabled", "access_material_enabled",
        "external_network_enabled", "production_operations_enabled", "money_movement_enabled",
    ):
        assert status[key] is False
    assert status["restrictions_are_approval_gates"] is True
    assert status["next_recommended_macro_pr"] == "Mark 2 Release Candidate Hardening"


def test_policy_production_payment_email_domain_and_voice_rules():
    engine = ExternalOperationsPolicyEngine()
    deploy = engine.evaluate(operation_type="deploy", environment="production")
    assert deploy.risk_level.value == "critical"
    assert deploy.strong_approval_required and deploy.double_confirmation_required and deploy.rollback_or_stop_plan_required
    assert "required rollback or stop plan is missing" in deploy.blocked_reasons
    payment = engine.evaluate(operation_type="payment", provider="stripe", money_movement=True, rollback_or_stop_plan="refund or stop")
    assert payment.strong_approval_required and payment.double_confirmation_required and payment.triple_confirmation_required
    email = Mark2EmailAdapter().preview(operation="send")
    bulk = Mark2EmailAdapter().preview(operation="bulk_send", bulk_or_marketing=True)
    assert email.approval_required and bulk.strong_approval_required
    domain = Mark2DomainPublishingAdapter().preview(operation="dns_record", production_impact=True)
    assert domain.strong_approval_required and domain.double_confirmation_required


def test_external_operation_candidates_never_execute_or_call_providers():
    deploy = Mark2DeployAdapter().preview(environment="production", artifact_summary="password=unsafe")
    stripe = Mark2StripeAdapter().preview(stripe_mode="live", operation="charge", money_movement=True)
    email = Mark2EmailAdapter().preview(operation="send", body_summary="api_key=not-safe")
    domain = Mark2DomainPublishingAdapter().preview(operation="dns_record", production_impact=True)
    assert deploy.would_deploy is False and deploy.would_call_external is False
    assert stripe.would_call_stripe is False and stripe.would_move_money is False
    assert email.would_send_email is False and email.would_call_external is False
    assert domain.would_publish is False and domain.would_modify_dns is False
    assert "redacted" in deploy.artifact_summary
    assert "redacted" in email.body_summary_redacted


def test_valid_voice_approval_requires_readback_and_wake_phrase_never_approves():
    adapter = Mark2DeployAdapter()
    invalid = adapter.preview(
        environment="staging", rollback_plan="rollback", valid_voice_approval_present=True, readback_completed=False
    )
    wake = adapter.preview(
        environment="staging", rollback_plan="rollback", valid_voice_approval_present=True,
        readback_completed=True, wake_phrase=True,
    )
    valid = adapter.preview(
        environment="staging", rollback_plan="rollback", valid_voice_approval_present=True, readback_completed=True
    )
    assert invalid.valid_voice_approval_present is False
    assert wake.valid_voice_approval_present is False
    assert valid.valid_voice_approval_present is True


def test_kill_switch_and_stop_phrase_block_candidates():
    killed = Mark2DeployAdapter().preview(environment="staging", rollback_plan="rollback", kill_switch_active=True)
    stopped = Mark2DeployAdapter().preview(environment="staging", rollback_plan="rollback", stop_phrase_detected=True)
    assert "kill switch active" in killed.blocked_reasons
    assert "candidate cancelled by stop phrase" in stopped.blocked_reasons


def test_ai_cli_adapters_are_governed_and_never_invoke_push_merge_deploy_or_web():
    codex = CodexCliAdapter.preview()
    claude = ClaudeCodeAdapter.preview()
    cowork = ClaudeCoworkAdapter.preview(routine_type="form_assist")
    for adapter in (codex, claude):
        assert adapter.stores_access_material is False
        assert adapter.uses_cookies is False and adapter.automates_web_ui is False
        assert adapter.would_invoke_real_cli is False
        assert adapter.would_push is False and adapter.would_merge is False and adapter.would_deploy is False
        assert adapter.cost_known is False and adapter.usage_limit_status == "manual_input_required"
    assert cowork.supervised_required is True
    assert cowork.would_submit_forms is False and cowork.would_handle_money is False and cowork.would_touch_production is False


def test_api_fallback_and_routine_bridge_choose_hybrid_adapters_without_execution():
    api = ApiFallbackAdapter.preview(provider="openai", use_case="json_router")
    coding = RoutineExecutionBridge.preview(routine_type="ai_coding")
    worker = RoutineExecutionBridge.preview(routine_type="external_api", use_case="worker")
    assert api.cost_mode == "api_tokens" and api.budget_guard_required and api.would_call_api is False
    assert api.cost_known is False
    assert coding.selected_adapter == "Codex CLI"
    assert worker.selected_adapter == "ApiFallbackAdapter"
    assert coding.would_execute is False and worker.would_execute is False


def test_audit_event_is_safe_redacted_and_records_no_effects():
    event = build_external_operation_audit_event(target_summary="password=unsafe")
    assert event.executed is False and event.external_call_made is False
    assert event.money_moved is False and event.production_touched is False
    assert event.secrets_redacted and event.audit_safe
    assert "redacted" in event.target_summary_redacted


def test_dashboard_operational_command_center_and_operator_console_reflect_macro_4_safely():
    markers = mark_2_external_operations_markers()
    operational = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="macro-4", generated_at="2026-06-12T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="macro-4", generated_at="2026-06-12T00:00:00+00:00")
    for marker, expected in markers.items():
        assert operational[marker] == expected
        assert command.metadata[marker] == expected
        assert operator.metadata[marker] == expected
    overview = VisualCommandCenter().overview()
    assert overview["external_operations_status"]["mark_2_macro_4_external_ops_ai_cli_available"] is True
    assert overview["routine_execution_bridge"]["would_execute"] is False
    serialized = json.dumps(command.to_dict()).lower()
    for forbidden in FORBIDDEN_COMMAND_CENTER:
        assert forbidden not in serialized
