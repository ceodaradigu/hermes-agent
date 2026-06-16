from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

from jarvis.mark_3_approval_path_audit import Mark3ApprovalPathAudit
from jarvis.mark_3_dangerous_route_audit import Mark3DangerousRouteAudit
from jarvis.mark_3_e2e_readiness import Mark3E2EReadinessSmoke
from jarvis.mark_3_pilot_plan import Mark3ControlledPilotPlan
from jarvis.mark_3_release_candidate import Mark3CapabilityMatrix, Mark3ReadinessMatrix, Mark3ReleaseCandidateStatus
from jarvis.mobile.companion import MobileCompanionPermissionPolicy, MobileCompanionStatus


UNKNOWN = "unknown"


def build_mark_3_dashboard_status(
    *,
    app_state: Any,
    route_paths: Iterable[str],
    generated_at: str,
) -> Dict[str, Any]:
    """Build the read-only dashboard projection for the local JARVIS UI.

    This function intentionally reads only local control-plane status objects.
    It does not call Hermes execution, browser sensors, network providers,
    money/deploy/email adapters, or approval mutation paths.
    """

    timeline: List[Dict[str, Any]] = []

    health = _source("/health", lambda: {"status": "ok"}, timeline)
    release_status = _source(
        "/mark-3/release-candidate/status",
        lambda: Mark3ReleaseCandidateStatus().to_dict(),
        timeline,
    )
    capabilities = _source(
        "/mark-3/release-candidate/capabilities",
        lambda: Mark3CapabilityMatrix().to_dict(),
        timeline,
    )
    readiness = _source(
        "/mark-3/release-candidate/readiness",
        lambda: Mark3ReadinessMatrix().to_dict(),
        timeline,
    )
    dangerous_route_audit = _source(
        "/mark-3/release-candidate/dangerous-route-audit",
        lambda: Mark3DangerousRouteAudit().audit(route_paths),
        timeline,
    )
    approval_path_audit = _source(
        "/mark-3/release-candidate/approval-path-audit",
        lambda: Mark3ApprovalPathAudit().audit(),
        timeline,
    )
    e2e_smoke = _source(
        "/mark-3/release-candidate/e2e-smoke",
        lambda: Mark3E2EReadinessSmoke().run(),
        timeline,
    )
    pilot_plan = _source(
        "/mark-3/release-candidate/pilot-plan",
        lambda: Mark3ControlledPilotPlan().to_dict(),
        timeline,
    )

    mission_loop = _source(
        "/mark-3/mission-loop/status",
        lambda: app_state.mark_3_mission_loop.status(),
        timeline,
    )
    hermes_runtime = _source(
        "/mark-3/hermes-runtime/status",
        lambda: app_state.mark_3_hermes_runtime_bridge.status(),
        timeline,
    )
    research_execution = _source(
        "/mark-3/research-execution/status",
        lambda: app_state.mark_3_research_execution_bridge.status(),
        timeline,
    )
    product_revenue = _source(
        "/mark-3/product-revenue/status",
        lambda: app_state.mark_3_product_revenue_factory.status(),
        timeline,
    )
    routine_ops = _source(
        "/mark-3/routine-ops/status",
        lambda: app_state.mark_3_routine_ops.status(),
        timeline,
    )
    moonshot_lab = _source(
        "/mark-3/moonshot-lab/status",
        lambda: app_state.mark_3_moonshot_lab.status(),
        timeline,
    )
    research_radar = _source(
        "/mark-3/research-radar/status",
        lambda: app_state.mark_3_research_radar.status(),
        timeline,
    )
    memory_status = _source(
        "/mark-3/outcomes",
        lambda: app_state.mark_3_outcome_memory.status(),
        timeline,
    )
    learning_status = _source(
        "/mark-3/learning/proposals",
        lambda: app_state.mark_3_learning_proposals.status(),
        timeline,
    )
    voice_runtime = _source(
        "/voice-runtime/status",
        lambda: app_state.wake_voice_runtime.status(),
        timeline,
    )
    wake_listener = _source(
        "/mark-2/wake-listener/status",
        lambda: app_state.real_wake_listener.status(),
        timeline,
    )
    camera_control = _source(
        "/camera-control/status",
        lambda: app_state.camera_control_runtime.status(),
        timeline,
    )
    approvals_status = _source(
        "/approvals/status",
        lambda: app_state.approval_hardening.status(),
        timeline,
    )
    mobile_status = _source(
        "/mobile/companion/status",
        lambda: MobileCompanionStatus.placeholder().to_dict(),
        timeline,
    )
    mobile_permissions = _source(
        "/mobile/companion/permissions",
        lambda: MobileCompanionPermissionPolicy.placeholder().to_dict(),
        timeline,
    )

    pending_count = _pending_approval_count(app_state)
    approval_cards = _approval_preview_cards(research_execution=research_execution)
    approval_summary = _approval_summary(pending_count, approval_cards)
    kill_switch_active = _bool(mission_loop, "kill_switch_active", default=None)
    kill_switch_state = "active" if kill_switch_active is True else "inactive" if kill_switch_active is False else "not_wired"
    running_sessions = _int(hermes_runtime.get("running_sessions"), default=None)
    session_count = _int(hermes_runtime.get("session_count"), default=None)
    hermes_execution = _hermes_execution_projection(
        hermes_runtime=hermes_runtime,
        research_execution=research_execution,
        running_sessions=running_sessions,
        session_count=session_count,
    )
    hermes_timeline = _hermes_timeline_events(hermes_execution)
    mission_control = _mission_control_projection()
    mission_control_timeline = _mission_control_timeline_events()
    voice_core = _voice_core_projection(voice_runtime=voice_runtime, wake_listener=wake_listener)
    voice_core_timeline = _voice_core_timeline_events()
    wake_word_flow = _wake_word_flow_projection(wake_listener=wake_listener)
    wake_word_flow_timeline = _wake_word_flow_timeline_events()
    camera_vision = _camera_vision_projection(camera_control=camera_control)
    camera_vision_timeline = _camera_vision_timeline_events()
    mobile_companion = _mobile_companion_projection(
        mobile_status=mobile_status,
        mobile_permissions=mobile_permissions,
    )
    mobile_companion_timeline = _mobile_companion_timeline_events()
    finance_roi = _finance_roi_projection()
    finance_roi_timeline = _finance_roi_timeline_events()
    adaptive_product_builder = _adaptive_product_builder_projection()
    adaptive_product_builder_timeline = _adaptive_product_builder_timeline_events()
    frontend_pilot = _frontend_pilot_projection()
    frontend_pilot_timeline = _frontend_pilot_timeline_events()

    payload = {
        "system": {
            "api_status": health.get("status", UNKNOWN),
            "local_first": _bool(release_status, "local_first", default=True),
            "mode": "read_only_dashboard",
            "free_autonomy_enabled": False,
            "preview_first": True,
            "kill_switch_state": kill_switch_state,
            "generated_at": generated_at,
            "source_endpoint": "/health",
        },
        "jarvis_hermes_contract": {
            "jarvis_role": "governs/risk/approval/audit/control",
            "hermes_role": "execution_engine",
            "no_duplicate_hermes_runtime": True,
            "frontend_direct_execution_allowed": False,
            "frontend_can_execute": False,
            "frontend_can_call_hermes_execute": False,
            "source_endpoint": "/mark-3/release-candidate/status",
        },
        "release_candidate": {
            "status": release_status.get("release_candidate_status", UNKNOWN),
            "readiness": readiness.get("readiness", {}),
            "not_ready_for_free_autonomy": True,
            "restrictions_are_approval_gates_not_permanent_bans": True,
            "pilot_readiness": readiness.get("pilot_readiness", UNKNOWN),
            "pilot_executed": False,
            "source_endpoints": [
                "/mark-3/release-candidate/status",
                "/mark-3/release-candidate/readiness",
                "/mark-3/release-candidate/capabilities",
                "/mark-3/release-candidate/dangerous-route-audit",
                "/mark-3/release-candidate/approval-path-audit",
                "/mark-3/release-candidate/e2e-smoke",
                "/mark-3/release-candidate/pilot-plan",
            ],
        },
        "modules": [
            _module(
                "Mission Loop",
                "ready" if mission_loop.get("mission_loop_available") else UNKNOWN,
                "/mark-3/mission-loop/status",
                "risk_scaled_per_step",
                "In-memory governed mission loop; candidates are not execution.",
            ),
            _module(
                "Research",
                "gated" if research_execution.get("local_docs_repo_read_adapter_connected") else "not_connected",
                "/mark-3/research-execution/status",
                "level_2_local_read_level_3_external",
                "Exact local docs/repo read path is gated; GitHub/web remain not_connected by default.",
            ),
            _module(
                "Product Revenue",
                "prepare-only" if product_revenue.get("prepare_only") else UNKNOWN,
                "/mark-3/product-revenue/status",
                "level_4_for_money_publication_identity",
                "Prepares candidates only; no Stripe, checkout, deploy, publication, or money movement.",
            ),
            _module(
                "Routine Ops",
                "prepare-only" if routine_ops.get("prepare_only") else UNKNOWN,
                "/mark-3/routine-ops/status",
                "risk_scaled",
                "No real scheduler, email, accounts, Gmail, Calendar, Contacts, worker, or watcher.",
            ),
            _module(
                "Moonshot Lab",
                "prepare-only" if moonshot_lab.get("prepare_only") else UNKNOWN,
                "/mark-3/moonshot-lab/status",
                "risk_scaled",
                "Research and experiment plans are prepare-only; no installs, providers, deploy, money, or fake results.",
            ),
            _module(
                "Voice",
                "preview" if voice_runtime.get("voice_runtime_available") else "not_connected",
                "/voice-runtime/status",
                "sensor_privacy",
                "Voice status is a control-plane preview; microphone and recording are disabled.",
            ),
            _module(
                "Wake Listener",
                "disabled" if wake_listener.get("wake_listener_enabled") is False else "preview",
                "/mark-2/wake-listener/status",
                "sensor_privacy",
                "Wake phrases are documented but do not approve actions or access the microphone here.",
            ),
            _module(
                "Camera/Vision",
                "disabled" if camera_control.get("camera_session_active") is False else "preview",
                "/camera-control/status",
                "sensor_privacy",
                "Camera control plane is visible; no camera session, recording, face analysis, screen capture, or storage.",
            ),
            _module(
                "Mobile Companion",
                "preview",
                "/mobile/companion/status",
                "remote_surface",
                "Mobile can read safe snapshots in the future; no native runtime, approvals, or direct Hermes calls.",
            ),
            _module(
                "Memory/Learning",
                "preview" if memory_status.get("available") and learning_status.get("available") else UNKNOWN,
                "/mark-3/outcomes + /mark-3/learning/proposals",
                "memory_never_grants_permission",
                "Outcome/failure memory and learning proposals are in-memory and never authorize execution.",
            ),
            _module(
                "Hermes",
                "gated" if hermes_runtime.get("available") else "not_connected",
                "/mark-3/hermes-runtime/status",
                "exact_local_read_only_with_operator_authorization",
                "Hermes remains the execution engine; frontend direct execution is disabled.",
            ),
        ],
        "approvals": {
            **approval_summary,
            "action_buttons_enabled": False,
            "all_actions_read_only": True,
            "wake_phrase_can_approve": False,
            "frontend_can_approve": False,
            "frontend_can_reject": False,
            "frontend_can_modify_scope": False,
            "critical_actions_require_strong_approval": True,
            "cards": approval_cards,
            "cards_state": "preview/read-only",
            "preview_only": True,
            "readback_policy": {
                "wake_phrase_never_approves": True,
                "voice_approval_requires_auth_gate_and_audit": True,
                "critical_actions_require_readback": True,
                "critical_actions_require_strong_confirmation": True,
                "critical_actions_require_double_or_triple_confirmation": True,
                "critical_actions_require_rollback_and_stop_plan": True,
                "audit_required": True,
            },
            "source_endpoint": "/approvals/status",
            "raw_status": _status_summary(approvals_status),
        },
        "mission_control": mission_control,
        "hermes_execution": hermes_execution,
        "voice_core": voice_core,
        "wake_word_flow": wake_word_flow,
        "voice_wake": {
            "microphone_state": "disabled" if voice_core["state"]["microphone_enabled"] is False else UNKNOWN,
            "wake_word_state": voice_core["state"]["current_state"],
            "wake_phrases": voice_core["wake_word_policy"]["supported_phrases"],
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "audio_recording": False,
            "raw_audio_stored": False,
            "external_provider_called": False,
            "source_endpoints": ["/voice-runtime/status", "/mark-2/wake-listener/status"],
        },
        "camera_vision": camera_vision,
        "mobile_companion": mobile_companion,
        "mobile": {
            "companion_state": mobile_companion["state"]["pwa_baseline"],
            "direct_hermes_call_allowed": False,
            "remote_kill_switch_state": "future_gated",
            "approval_actions_enabled": False,
            "source_endpoints": mobile_companion["source_endpoints"],
            "permissions": {
                "can_read_command_center": bool(mobile_permissions.get("can_read_command_center", False)),
                "can_execute": False,
                "can_approve": False,
            },
        },
        "finance_roi": finance_roi,
        "finance": {
            "actual_cost": finance_roi["metrics"]["actual_cost"]["value"],
            "estimated_cost": finance_roi["metrics"]["estimated_cost"]["value"],
            "confirmed_revenue": finance_roi["metrics"]["confirmed_revenue"]["value"],
            "projected_revenue": finance_roi["metrics"]["projected_revenue"]["value"],
            "gross_revenue": finance_roi["metrics"]["gross_revenue"]["value"],
            "expenses": finance_roi["metrics"]["expenses"]["value"],
            "net_revenue": finance_roi["metrics"]["net_revenue"]["value"],
            "roi": finance_roi["metrics"]["roi"]["value"],
            "no_fake_metrics": True,
            "source": "No measurement evidence connected to this read model.",
        },
        "adaptive_product_builder": adaptive_product_builder,
        "product_builder": {
            "stages": [stage["name"] for stage in adaptive_product_builder["stages"]],
            "deploy_requires_strong_approval": True,
            "stripe_checkout_requires_strong_approval": True,
            "real_revenue_must_be_confirmed": True,
            "source_endpoint": "/mark-3/product-revenue/status",
        },
        "frontend_pilot": frontend_pilot,
        "safety": {
            "frontend_can_execute": False,
            "frontend_can_approve": False,
            "no_auto_execute": True,
            "no_frontend_execute": True,
            "no_duplicate_hermes_runtime": True,
            "no_get_user_media": True,
            "no_sensor_activation": True,
            "no_voice_recording": True,
            "no_camera_capture": True,
            "no_frontend_tool_runner": True,
            "no_tool_call": True,
            "no_file_write": True,
            "no_network_call": True,
            "no_direct_hermes_call_from_mobile": True,
            "no_direct_hermes_call_from_voice": True,
            "no_direct_hermes_call_from_camera": True,
            "no_frontend_hermes_execution": True,
            "no_hermes_dispatch": True,
            "no_post_put_delete_from_jarvis_page": True,
            "approval_required_before_execution": True,
            "wake_phrase_is_not_permission": True,
            "audit_required": True,
            "rollback_or_stop_plan_required_for_sensitive_actions": True,
            "no_money_movement": True,
            "no_deploy": True,
            "no_credentials": True,
            "no_email_send": True,
        },
        "timeline": timeline
        + hermes_timeline
        + mission_control_timeline
        + voice_core_timeline
        + wake_word_flow_timeline
        + camera_vision_timeline
        + mobile_companion_timeline
        + finance_roi_timeline
        + adaptive_product_builder_timeline
        + frontend_pilot_timeline
        + [
            {
                "event": "dashboard read model generated",
                "source": "/mark-3/dashboard/status",
                "status": "ok",
                "read_only": True,
            }
        ],
        "source_status": {
            "dangerous_route_audit": {
                "passed": bool(dangerous_route_audit.get("passed", False)),
                "dangerous_routes_registered": dangerous_route_audit.get("dangerous_routes_registered", []),
                "source_endpoint": "/mark-3/release-candidate/dangerous-route-audit",
            },
            "approval_path_audit": {
                "passed": bool(approval_path_audit.get("passed", False)),
                "approval_is_not_execution": bool(approval_path_audit.get("approval_is_not_execution", False)),
                "source_endpoint": "/mark-3/release-candidate/approval-path-audit",
            },
            "e2e_smoke": {
                "passed": bool(e2e_smoke.get("passed", False)),
                "prepare_only": bool(e2e_smoke.get("prepare_only", False)),
                "would_execute": bool(e2e_smoke.get("would_execute", True)),
                "source_endpoint": "/mark-3/release-candidate/e2e-smoke",
            },
            "pilot_plan": {
                "pilot_executed": bool(pilot_plan.get("pilot_executed", True)),
                "safe_to_render": bool(pilot_plan.get("safe_to_render", False)),
                "source_endpoint": "/mark-3/release-candidate/pilot-plan",
            },
            "capabilities_count": len(capabilities.get("capabilities", []) or []),
            "research_radar": _status_summary(research_radar),
        },
        "read_only_contract": {
            "aggregated_endpoint": "/mark-3/dashboard/status",
            "allowed_http_methods_for_frontend": ["GET"],
            "internal_sources_are_read_only_status_or_audit": True,
            "frontend_must_not_call_execute": True,
            "frontend_must_not_request_sensor_permissions": True,
        },
    }
    return payload


def _unknown_metric(label: str) -> Dict[str, Any]:
    return {
        "value": UNKNOWN,
        "label": label,
        "source": "not_measured",
        "evidence_state": "missing",
        "confidence": UNKNOWN,
        "last_updated": UNKNOWN,
    }


def _finance_roi_projection() -> Dict[str, Any]:
    metric_labels = {
        "actual_cost": "Coste real",
        "estimated_cost": "Coste estimado",
        "confirmed_revenue": "Revenue confirmado",
        "projected_revenue": "Revenue proyectado",
        "gross_revenue": "Gross revenue",
        "expenses": "Expenses",
        "net_revenue": "Net revenue",
        "roi": "ROI",
        "token_cost": "Token cost",
        "api_cost": "API cost",
        "infra_cost": "Infra cost",
        "manual_input_cost": "Manual input cost",
        "revenue_source": "Revenue source",
    }
    return {
        "truth_policy": {
            "no_fake_metrics": True,
            "unknown_when_no_evidence": True,
            "measured_requires_source": True,
            "estimated_requires_label": True,
            "confirmed_revenue_requires_evidence": True,
            "projected_revenue_must_be_labelled": True,
            "roi_unknown_without_revenue_and_cost": True,
        },
        "metrics": {key: _unknown_metric(label) for key, label in metric_labels.items()},
        "budget": {
            "budget_configured": False,
            "remaining_budget": UNKNOWN,
            "monthly_limit": UNKNOWN,
            "alert_threshold": UNKNOWN,
            "hard_stop_enabled": False,
            "notes": "Budget is not configured in this read model; values stay unknown until measured evidence exists.",
        },
        "safety": {
            "no_money_movement": True,
            "no_stripe_live": True,
            "no_checkout_creation": True,
            "no_invoice_creation": True,
            "no_payment_collection": True,
            "no_fake_revenue": True,
            "no_fake_costs": True,
            "no_fake_roi": True,
            "approval_required_for_money": True,
            "strong_approval_required_for_live_payments": True,
        },
        "timeline": _finance_roi_timeline_events(),
        "source_endpoint": "/mark-3/dashboard/status",
        "preview_only": True,
        "read_only": True,
    }


def _finance_roi_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Finance/ROI panel read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Metrics defaulted to unknown without evidence",
            "source": "/mark-3/dashboard/status",
            "status": "missing_evidence",
            "read_only": True,
        },
        {
            "event": "No money movement performed",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
        {
            "event": "No Stripe live action performed",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
        {
            "event": "No fake ROI generated",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
    ]


def _adaptive_product_builder_projection() -> Dict[str, Any]:
    return {
        "state": {
            "mode": "preview",
            "builder_enabled": "preview/read_only",
            "product_generation_enabled": False,
            "code_generation_enabled": False,
            "deploy_enabled": False,
            "stripe_enabled": False,
            "landing_publish_enabled": False,
            "external_research_enabled": False,
            "hermes_dispatch_enabled": False,
        },
        "stages": [
            _product_builder_stage(
                "Idea",
                "preview",
                False,
                "none",
                "reason_to_exist",
                "Idea stays as a read-only preview and must justify why the product should exist.",
            ),
            _product_builder_stage(
                "Validación",
                "preview",
                False,
                "none",
                "validation_signal",
                "Validation is only a placeholder; no external research or customer outreach is performed.",
            ),
            _product_builder_stage(
                "Blueprint",
                "preview",
                False,
                "none",
                "success_metric_and_scope",
                "Blueprint remains a preview of required evidence, not code generation.",
            ),
            _product_builder_stage(
                "Código",
                "future_gated",
                True,
                "strong",
                "approved_scope_and_diff_plan",
                "Future code generation requires explicit approval, scope and review.",
            ),
            _product_builder_stage(
                "Landing",
                "future_gated",
                True,
                "strong",
                "approved_copy_offer_and_publish_gate",
                "Landing work is not published and cannot create a public page from this panel.",
            ),
            _product_builder_stage(
                "Deploy candidate",
                "disabled",
                True,
                "strong",
                "rollback_stop_plan_owner_and_build_evidence",
                "Deploy candidates are not executed in this PR.",
            ),
            _product_builder_stage(
                "Monetización",
                "disabled",
                True,
                "strong",
                "pricing_logic_revenue_confirmation_and_payment_gate",
                "Stripe, checkout and real revenue collection remain disabled.",
            ),
            _product_builder_stage(
                "Medición",
                "future_gated",
                True,
                "simple",
                "measured_source_before_metric",
                "Metrics must come from evidence; unknown is shown when evidence is absent.",
            ),
        ],
        "differentiation_policy": {
            "no_template_clone": True,
            "adaptive_builder_not_template_builder": True,
            "each_product_needs_reason_to_exist": True,
            "each_product_needs_success_metric": True,
            "each_product_needs_monetization_logic": True,
            "cloned_products_are_failure": True,
        },
        "monetization_policy": {
            "pricing_preview_only": True,
            "stripe_live_requires_strong_approval": True,
            "checkout_requires_strong_approval": True,
            "real_revenue_requires_confirmation": True,
            "projected_revenue_label_required": True,
            "no_fake_revenue": True,
        },
        "safety": {
            "no_deploy": True,
            "no_publish": True,
            "no_domain_change": True,
            "no_email_send": True,
            "no_money_movement": True,
            "no_credentials": True,
            "no_external_network": True,
            "no_hermes_dispatch": True,
            "approval_gates_required_for_real_actions": True,
        },
        "timeline": _adaptive_product_builder_timeline_events(),
        "source_endpoint": "/mark-3/dashboard/status",
        "preview_only": True,
        "read_only": True,
    }


def _product_builder_stage(
    name: str,
    status: str,
    requires_approval: bool,
    approval_level: str,
    evidence_required: str,
    notes: str,
) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "can_execute": False,
        "requires_approval": requires_approval,
        "approval_level": approval_level,
        "evidence_required": evidence_required,
        "notes": notes,
    }


def _adaptive_product_builder_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Product Builder panel read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Product stages loaded as preview",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "No product generated",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
        {
            "event": "No deploy candidate executed",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
        {
            "event": "No monetization action performed",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
    ]


def _frontend_pilot_projection() -> Dict[str, Any]:
    return {
        "state": {
            "mode": "read_only_pilot",
            "dashboard_route": "/jarvis",
            "backend_status_endpoint": "/mark-3/dashboard/status",
            "frontend_can_execute": False,
            "frontend_can_approve": False,
            "frontend_can_activate_sensors": False,
            "frontend_can_move_money": False,
            "frontend_can_deploy": False,
            "frontend_can_send_email": False,
        },
        "readiness_checks": [
            _frontend_readiness_check(
                "dashboard_route_exists",
                "preview",
                "frontend route expected at /jarvis",
                "Static frontend tests verify this shell route.",
            ),
            _frontend_readiness_check(
                "read_model_connected",
                "passed",
                "GET /mark-3/dashboard/status",
                "The dashboard read model is exposed as a GET route.",
            ),
            _frontend_readiness_check(
                "approval_console_visible",
                "passed",
                "approvals projection present",
                "Approval controls are disabled preview affordances.",
            ),
            _frontend_readiness_check(
                "hermes_execution_visible",
                "passed",
                "hermes_execution projection present",
                "Hermes is visible only as a governed execution engine behind JARVIS gates.",
            ),
            _frontend_readiness_check(
                "mission_control_visible",
                "passed",
                "mission_control projection present",
                "Mission Control remains preview-only with no Hermes dispatch.",
            ),
            _frontend_readiness_check(
                "voice_core_visible",
                "passed",
                "voice_core projection present",
                "Voice core is visual preview only.",
            ),
            _frontend_readiness_check(
                "wake_flow_visible",
                "passed",
                "wake_word_flow projection present",
                "Wake word flow is typed preview only.",
            ),
            _frontend_readiness_check(
                "camera_vision_visible",
                "passed",
                "camera_vision projection present",
                "Camera and vision stay disabled.",
            ),
            _frontend_readiness_check(
                "mobile_companion_visible",
                "passed",
                "mobile_companion projection present",
                "Mobile is an interface, not a runtime.",
            ),
            _frontend_readiness_check(
                "finance_roi_visible",
                "passed",
                "finance_roi projection present",
                "Finance metrics default to unknown without evidence.",
            ),
            _frontend_readiness_check(
                "product_builder_visible",
                "passed",
                "adaptive_product_builder projection present",
                "Product Builder is adaptive preview, not product generation.",
            ),
            _frontend_readiness_check(
                "kill_switch_visible",
                "passed",
                "system.kill_switch_state is exposed",
                "Kill Switch remains visible while no execution is available to stop.",
            ),
            _frontend_readiness_check(
                "no_fake_metrics",
                "passed",
                "finance_roi.truth_policy.no_fake_metrics=true",
                "Unknown is required when evidence is missing.",
            ),
            _frontend_readiness_check(
                "no_frontend_execute",
                "passed",
                "frontend_can_execute=false",
                "Frontend is a read-only pilot surface.",
            ),
            _frontend_readiness_check(
                "no_sensor_activation",
                "passed",
                "frontend_can_activate_sensors=false",
                "No microphone, camera or browser permission path is exposed.",
            ),
            _frontend_readiness_check(
                "no_post_put_delete",
                "passed",
                "allowed_http_methods_for_frontend=[GET]",
                "The /jarvis dashboard consumes only the read model.",
            ),
        ],
        "hardening_notes": {
            "npm_audit_vulnerabilities_observed": UNKNOWN,
            "npm_audit_fix_not_run": True,
            "dependency_hardening_requires_separate_pr": True,
            "no_lockfile_changes_expected": True,
            "frontend_build_required_before_merge": True,
            "full_pytest_required_before_merge": True,
        },
        "pilot_limitations": [
            "no real approvals",
            "no real mission submit",
            "no real Hermes execution",
            "no real voice",
            "no real camera",
            "no real mobile runtime",
            "no real finance/revenue measurement",
            "no deploy/money/email/credentials",
        ],
        "timeline": _frontend_pilot_timeline_events(),
        "source_endpoint": "/mark-3/dashboard/status",
        "preview_only": True,
        "read_only": True,
    }


def _frontend_readiness_check(name: str, status: str, evidence: str, notes: str) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


def _frontend_pilot_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Frontend pilot status read",
            "source": "/mark-3/dashboard/status",
            "status": "read_only_pilot",
            "read_only": True,
        },
        {
            "event": "Dashboard route expected at /jarvis",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Read model expected at /mark-3/dashboard/status",
            "source": "/mark-3/dashboard/status",
            "status": "passed",
            "read_only": True,
        },
        {
            "event": "Pilot remains read-only",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
        {
            "event": "Dependency hardening deferred to separate PR if needed",
            "source": "/mark-3/dashboard/status",
            "status": "deferred",
            "read_only": True,
        },
    ]


def _camera_vision_projection(*, camera_control: Dict[str, Any]) -> Dict[str, Any]:
    camera_disabled = camera_control.get("camera_session_active") is False
    local_vision_model_connected: bool | str = UNKNOWN
    return {
        "state": {
            "mode": "preview",
            "camera_enabled": False,
            "camera_permission_requested": False,
            "preview_enabled": False,
            "recording": False,
            "streaming": False,
            "snapshot_capture_enabled": False,
            "vision_analysis_enabled": False,
            "image_storage_enabled": False,
            "video_storage_enabled": False,
            "external_vision_provider_called": False,
            "local_vision_model_connected": local_vision_model_connected,
            "background_camera_access": False,
        },
        "privacy": {
            "no_camera_activation": True,
            "no_get_user_media": True,
            "no_media_stream": True,
            "no_recording": True,
            "no_snapshot_capture": True,
            "no_image_storage": True,
            "no_video_storage": True,
            "no_external_provider": True,
            "explicit_operator_permission_required": True,
            "visual_indicator_required_when_camera_active": True,
            "audit_required_for_future_vision": True,
        },
        "states": [
            _camera_vision_state(
                "camera_off",
                "Cámara apagada",
                "Estado actual seguro: no hay cámara activa ni sesión de cámara.",
                "preview",
                "none",
            ),
            _camera_vision_state(
                "camera_available_future",
                "Cámara disponible futura",
                "Capacidad futura solo tras permiso explícito, indicador visual y auditoría.",
                "future_gated",
                "sensor_privacy",
            ),
            _camera_vision_state(
                "preview_disabled",
                "Preview deshabilitado",
                "No hay previsualización real de cámara en esta PR.",
                False,
                "sensor_privacy",
            ),
            _camera_vision_state(
                "permission_required",
                "Permiso requerido",
                "Cualquier visión futura debe pedir permiso explícito al operador.",
                "future_gated",
                "approval_gate",
            ),
            _camera_vision_state(
                "analyzing_future",
                "Análisis futuro",
                "El análisis visual futuro deberá declarar qué puede ver y no inferir identidad sensible.",
                "future_gated",
                "vision_privacy",
            ),
            _camera_vision_state(
                "recording_disabled",
                "Grabación desactivada",
                "No se graba vídeo ni audio desde cámara.",
                False,
                "storage_privacy",
            ),
            _camera_vision_state(
                "storage_disabled",
                "Almacenamiento desactivado",
                "No se guarda imagen ni vídeo.",
                False,
                "storage_privacy",
            ),
            _camera_vision_state(
                "blocked",
                "Bloqueado",
                "Cualquier intento de activar cámara, captura, streaming o provider queda bloqueado.",
                "preview",
                "blocked",
            ),
            _camera_vision_state(
                "kill_switch",
                "Kill switch",
                "Parada visible futura para cortar cámara/visión si alguna vez se habilita bajo gates.",
                "preview",
                "stop_control",
            ),
        ],
        "scope_policy": {
            "allowed_scope": "none/unknown",
            "future_scope_requires_explicit_operator_permission": True,
            "future_analysis_must_state_what_it_can_see": True,
            "future_analysis_must_not_infer_sensitive_identity": True,
            "future_analysis_must_not_store_without_permission": True,
        },
        "timeline": _camera_vision_timeline_events(),
        "camera_state": "disabled" if camera_disabled else UNKNOWN,
        "preview_state": "disabled",
        "recording": False,
        "streaming": False,
        "snapshot": "disabled",
        "vision_analysis": "disabled",
        "storage": False,
        "provider": "none/not_connected",
        "source_endpoint": "/camera-control/status",
        "source_endpoints": ["/camera-control/status"],
        "preview_only": True,
        "read_only": True,
    }


def _camera_vision_state(
    state: str,
    label: str,
    description: str,
    enabled: bool | str,
    risk: str,
) -> Dict[str, Any]:
    return {
        "state": state,
        "label": label,
        "description": description,
        "enabled": enabled,
        "risk": risk,
        "can_execute": False,
    }


def _camera_vision_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Camera/Vision privacy status read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Camera disabled",
            "source": "/camera-control/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Recording disabled",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Vision analysis disabled",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "No image or video captured",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
        {
            "event": "No external vision provider called",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
    ]


def _mobile_companion_projection(
    *,
    mobile_status: Dict[str, Any],
    mobile_permissions: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "state": {
            "mode": "preview",
            "pwa_baseline": "preview",
            "mobile_runtime_enabled": False,
            "mobile_can_execute": False,
            "mobile_can_call_hermes_directly": False,
            "mobile_can_approve_real_actions": False,
            "mobile_can_reject_real_actions": False,
            "mobile_can_modify_scope_real": False,
            "mobile_notifications_enabled": False,
            "remote_kill_switch_enabled": False,
            "remote_camera_enabled": False,
            "remote_microphone_enabled": False,
            "external_network_required": False,
        },
        "mobile_views": [
            _mobile_view(
                "status",
                "Estado",
                "preview",
                "Solo lectura del estado agregado de JARVIS.",
            ),
            _mobile_view(
                "approvals_preview",
                "Approvals preview",
                "preview",
                "Muestra approvals futuros como preview; no aprueba ni rechaza.",
            ),
            _mobile_view(
                "mission_preview",
                "Mission preview",
                "preview",
                "Vista futura de misión en modo preview sin crear ejecución.",
            ),
            _mobile_view(
                "hermes_visibility",
                "Hermes visibility",
                "preview",
                "Visibilidad read-only de Hermes detrás de gates JARVIS.",
            ),
            _mobile_view(
                "voice_status",
                "Voice status",
                "preview",
                "Estado de voz sin activar micrófono ni runtime móvil.",
            ),
            _mobile_view(
                "camera_status",
                "Camera status",
                "preview",
                "Estado de cámara/visión sin activar cámara móvil.",
            ),
            _mobile_view(
                "finance_summary",
                "Finance summary",
                "preview",
                "Resumen financiero solo con datos unknown o evidencia futura.",
            ),
            _mobile_view(
                "kill_switch_preview",
                "Kill switch preview",
                "future_gated",
                "Control remoto futuro; no hay kill switch remoto real en esta PR.",
            ),
        ],
        "safety": {
            "mobile_is_interface_not_runtime": True,
            "no_direct_hermes_call": True,
            "no_mobile_execute": True,
            "no_mobile_sensor_activation": True,
            "no_mobile_camera_activation": True,
            "no_mobile_microphone_activation": True,
            "no_real_mobile_approval_in_this_pr": True,
            "approval_requires_backend_gate": True,
            "critical_approval_requires_strong_confirmation": True,
            "remote_kill_switch_future_gated": True,
        },
        "pwa_policy": {
            "installable_pwa": "preview",
            "offline_cache_enabled": False,
            "push_notifications_enabled": False,
            "service_worker_enabled": False,
            "no_background_sync": True,
            "no_credentials_storage": True,
            "no_token_storage": True,
        },
        "timeline": _mobile_companion_timeline_events(),
        "source_endpoints": ["/mobile/companion/status", "/mobile/companion/permissions"],
        "source_status": {
            "native_app_connected": bool(mobile_status.get("native_app_connected", False)),
            "can_read_command_center": bool(mobile_permissions.get("can_read_command_center", False)),
            "prepare_only": bool(mobile_status.get("prepare_only", True)),
        },
        "preview_only": True,
        "read_only": True,
    }


def _mobile_view(
    view_id: str,
    name: str,
    status: str,
    notes: str,
) -> Dict[str, Any]:
    return {
        "id": view_id,
        "name": name,
        "status": status,
        "can_execute": False,
        "can_call_hermes": False,
        "notes": notes,
    }


def _mobile_companion_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Mobile Companion preview read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Mobile is interface, not runtime",
            "source": "/mobile/companion/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Mobile direct Hermes call disabled",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Real mobile approvals disabled",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Remote kill switch future gated",
            "source": "/mark-3/dashboard/status",
            "status": "future_gated",
            "read_only": True,
        },
    ]


def _wake_word_flow_projection(*, wake_listener: Dict[str, Any]) -> Dict[str, Any]:
    supported_phrases = _list(wake_listener.get("supported_wake_phrases")) or ["Hola Jarvis", "Jarvis"]
    stop_phrases = _merge_unique(
        _list(wake_listener.get("stop_phrases")),
        ["para", "cancela", "detente", "silencio", "cancelar misión", "apaga escucha"],
    )
    return {
        "state": {
            "mode": "preview",
            "wake_runtime_enabled": False,
            "microphone_hard_off": True,
            "wake_word_only_mode": False,
            "command_window_open": False,
            "push_to_talk_preview_enabled": True,
            "typed_wake_preview_enabled": True,
            "always_on_microphone_enabled": False,
            "background_listener_enabled": False,
            "stt_enabled": False,
            "audio_recording": False,
            "raw_audio_stored": False,
            "external_provider_called": False,
        },
        "supported_phrases": supported_phrases,
        "stop_phrases": stop_phrases,
        "mode_explanations": {
            "mic_hard_off": "Micrófono completamente apagado; JARVIS no escucha nada.",
            "wake_word_only": "Futuro modo que detectaría solo la wake phrase, sin procesar una orden completa.",
            "command_listening": "Futura ventana corta de comando después de un wake válido y explícitamente gateado.",
            "push_to_talk": "Futuro modo manual iniciado por el operador, no por always-on listening.",
            "typed_preview": "Modo actual seguro: preview escrito sin audio real, micrófono, STT, TTS ni provider.",
        },
        "wake_parse_preview": {
            "input_example": "Hola Jarvis, revisa el estado del proyecto",
            "detected_wake_phrase": "Hola Jarvis",
            "remaining_command_preview": "revisa el estado del proyecto",
            "would_open_command_window": True,
            "would_execute": False,
            "would_approve": False,
            "would_call_hermes": False,
            "would_record_audio": False,
            "would_call_provider": False,
            "status": "preview_only",
        },
        "approval_policy": {
            "wake_phrase_is_permission": False,
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "voice_approval_requires_authenticated_channel": True,
            "sensitive_actions_require_readback": True,
            "critical_actions_require_double_or_triple_confirmation": True,
            "approval_events_must_be_audited": True,
        },
        "safety": {
            "no_microphone_activation": True,
            "no_get_user_media": True,
            "no_media_recorder": True,
            "no_audio_context_capture": True,
            "no_background_listening": True,
            "no_raw_audio_storage": True,
            "no_external_stt": True,
            "no_external_tts": True,
            "no_hermes_dispatch": True,
            "no_tool_call": True,
            "no_auto_execute": True,
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "source_endpoints": ["/voice-runtime/status", "/mark-2/wake-listener/status"],
        "preview_only": True,
        "read_only": True,
    }


def _wake_word_flow_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Wake word flow preview read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Microphone hard-off confirmed",
            "source": "/voice-runtime/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Typed wake preview available",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Wake phrase cannot approve",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
        {
            "event": "Wake phrase cannot execute",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
        {
            "event": "No background listener started",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
    ]


def _voice_core_projection(*, voice_runtime: Dict[str, Any], wake_listener: Dict[str, Any]) -> Dict[str, Any]:
    supported_phrases = _list(wake_listener.get("supported_wake_phrases")) or _list(
        voice_runtime.get("wake_phrases")
    ) or ["Hola Jarvis", "Jarvis"]
    current_state = "preview" if voice_runtime.get("voice_runtime_available") else "dormant"
    preview_subtitle = "David, estoy en modo preview. No estoy escuchando ni grabando audio."

    return {
        "state": {
            "mode": "preview",
            "current_state": current_state,
            "microphone_enabled": False,
            "wake_word_enabled": False,
            "command_listening_enabled": False,
            "tts_enabled": False,
            "stt_enabled": False,
            "audio_recording": False,
            "raw_audio_stored": False,
            "external_provider_called": False,
            "voice_approval_enabled": False,
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
        },
        "visual_states": [
            _voice_visual_state(
                "offline",
                "Offline",
                "JARVIS voice surface unavailable or backend offline; no sensors are active.",
                "none",
                False,
                False,
                "not_connected",
            ),
            _voice_visual_state(
                "online",
                "Online",
                "Future connected voice core state; not enabled by this read model.",
                "sensor_privacy",
                False,
                False,
                "future_gated",
            ),
            _voice_visual_state(
                "preview",
                "Preview",
                "Visual/read-model state only; no microphone, STT, TTS or provider call.",
                "none",
                "preview",
                False,
                "preview",
            ),
            _voice_visual_state(
                "dormant",
                "Dormido",
                "Safe dormant presentation; voice remains off and audio is not captured.",
                "none",
                "preview",
                False,
                "preview",
            ),
            _voice_visual_state(
                "listening_wake_word",
                "Escuchando wake word",
                "Future gated wake-word listening; would require explicit sensor approval.",
                "sensor_privacy",
                False,
                True,
                "future_gated",
            ),
            _voice_visual_state(
                "listening_command",
                "Escuchando orden",
                "Future gated short command window; disabled in this PR.",
                "sensor_privacy",
                False,
                True,
                "future_gated",
            ),
            _voice_visual_state(
                "thinking",
                "Pensando",
                "Future intent processing indicator; no provider or Hermes dispatch here.",
                "approval_gate",
                False,
                False,
                "future_gated",
            ),
            _voice_visual_state(
                "speaking",
                "Hablando",
                "Future TTS output indicator; subtitles are preview-only and audio output is off.",
                "audio_output",
                False,
                False,
                "not_connected",
            ),
            _voice_visual_state(
                "approval_required",
                "Esperando aprobación",
                "Future approval handoff state; voice cannot approve actions.",
                "approval_gate",
                False,
                False,
                "future_gated",
            ),
            _voice_visual_state(
                "hermes_executing",
                "Hermes ejecutando",
                "Future read-only execution visibility after valid JARVIS approval gates.",
                "execution",
                False,
                False,
                "future_gated",
            ),
            _voice_visual_state(
                "paused",
                "Pausado",
                "Future paused governed flow; no active voice session exists in this PR.",
                "stop_control",
                False,
                False,
                "future_gated",
            ),
            _voice_visual_state(
                "blocked",
                "Bloqueado",
                "Unsafe or unavailable voice flows stay blocked.",
                "blocked",
                False,
                False,
                "preview",
            ),
            _voice_visual_state(
                "error",
                "Error",
                "Future runtime error display; no voice runtime is started here.",
                "runtime_error",
                False,
                False,
                "not_connected",
            ),
            _voice_visual_state(
                "kill_switch",
                "Kill Switch",
                "Visible stop control relationship; there is no real audio to stop in this PR.",
                "stop_control",
                "preview",
                False,
                "preview",
            ),
        ],
        "tts_state": {
            "status": "preview",
            "speaking": False,
            "last_utterance": preview_subtitle,
            "subtitles_enabled": True,
            "subtitles_source": "preview/read_model",
            "preview_subtitle": preview_subtitle,
            "audio_output_enabled": False,
            "provider": "none/not_connected",
            "external_call": False,
        },
        "wake_word_policy": {
            "supported_phrases": supported_phrases,
            "wake_word_runtime": "disabled",
            "wake_phrase_is_permission": False,
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "requires_authenticated_channel_for_approval": True,
            "critical_actions_require_readback": True,
            "critical_actions_require_strong_confirmation": True,
        },
        "privacy": {
            "no_microphone_activation": True,
            "no_audio_recording": True,
            "no_raw_audio_storage": True,
            "no_external_audio_provider": True,
            "no_background_listening_enabled": True,
            "no_voice_biometrics": True,
            "no_voice_approval_without_gate": True,
        },
        "safety": {
            "no_auto_execute": True,
            "no_hermes_dispatch": True,
            "no_tool_call": True,
            "no_sensor_activation": True,
            "no_get_user_media": True,
            "no_media_recorder": True,
            "no_audio_context_capture": True,
            "kill_switch_visible": True,
        },
        "relationship": {
            "voice_can_prepare_future_intention": True,
            "approval_console_handles_required_approval": True,
            "hermes_executes_only_after_valid_approval": True,
            "frontend_or_voice_can_call_hermes_directly": False,
            "jarvis_governs": True,
            "hermes_executes": True,
        },
        "kill_switch": {
            "visible": True,
            "real_audio_to_stop": False,
            "future_must_cut_listening_tts_and_governed_execution": True,
        },
        "source_endpoints": ["/voice-runtime/status", "/mark-2/wake-listener/status"],
        "source_endpoint": "/mark-3/dashboard/status",
        "preview_only": True,
        "read_only": True,
    }


def _voice_visual_state(
    state: str,
    label: str,
    description: str,
    risk: str,
    enabled: bool | str,
    sensor_required: bool,
    connection: str,
) -> Dict[str, Any]:
    return {
        "state": state,
        "label": label,
        "description": description,
        "risk": risk,
        "enabled": enabled,
        "sensor_required": sensor_required,
        "can_approve": False,
        "connection": connection,
    }


def _voice_core_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Voice Core visual state read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Voice/TTS state preview generated",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Microphone disabled",
            "source": "/voice-runtime/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Wake word runtime not active",
            "source": "/mark-2/wake-listener/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "No audio recording performed",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
    ]


def _mission_control_projection() -> Dict[str, Any]:
    sample_command = "JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro."
    return {
        "state": {
            "mode": "preview",
            "input_enabled": "preview_only",
            "conversation_enabled": "preview_only",
            "execution_enabled": False,
            "hermes_dispatch_enabled": False,
            "approval_creation_enabled": False,
            "persistence_enabled": False,
            "external_network_enabled": False,
        },
        "supported_inputs": {
            "text_command": "preview",
            "voice_command": "future_gated",
            "mobile_command": "future_gated",
            "wake_word_command": "future_gated",
            "file_drop": "not_connected",
            "camera_context": "not_connected",
        },
        "sample_command": sample_command,
        "intent_preview": {
            "detected_intent": UNKNOWN,
            "confidence": UNKNOWN,
            "mission_type": UNKNOWN,
            "risk_level": UNKNOWN,
            "approval_level": UNKNOWN,
            "blocked_reasons": [],
            "required_permissions": [],
            "next_safe_action": UNKNOWN,
        },
        "command_lifecycle": [
            {
                "state": "draft",
                "description": "Operator-visible command text before any preview.",
                "preview_only": True,
            },
            {
                "state": "submitted_for_preview",
                "description": "Future read-only intake would normalize the request without creating work.",
                "preview_only": True,
            },
            {
                "state": "intent_detected",
                "description": "JARVIS would identify intent and keep confidence unknown until a safe classifier exists.",
                "preview_only": True,
            },
            {
                "state": "risk_classified",
                "description": "Risk would be classified before any approval or Hermes handoff.",
                "preview_only": True,
            },
            {
                "state": "approval_required",
                "description": "Sensitive work would require explicit operator approval before execution eligibility.",
                "preview_only": True,
            },
            {
                "state": "ready_for_operator_review",
                "description": "The operator reviews scope, risk, permissions, rollback and stop plan.",
                "preview_only": True,
            },
            {
                "state": "blocked",
                "description": "Unsafe, ambiguous or unavailable capabilities remain blocked.",
                "preview_only": True,
            },
            {
                "state": "forbidden",
                "description": "Credentials, bypass, deception and illegal or unsafe requests cannot be approved here.",
                "preview_only": True,
            },
            {
                "state": "executable_candidate_after_valid_approval",
                "description": "A future candidate may become executable only after valid JARVIS approval gates.",
                "preview_only": True,
            },
        ],
        "conversation_preview": {
            "messages": [
                {
                    "role": "user",
                    "speaker": "David",
                    "content": sample_command,
                    "preview_only": True,
                },
                {
                    "role": "assistant",
                    "speaker": "JARVIS",
                    "content": (
                        "Puedo preparar una misión de revisión. Antes de ejecutar cualquier acción sensible, "
                        "pediré aprobación."
                    ),
                    "preview_only": True,
                },
            ],
            "assistant_status": "preview",
            "transcript_persistence": False,
            "memory_write": False,
            "memory_read": False,
            "pii_redaction_required": True,
            "raw_audio_stored": False,
            "external_provider_called": False,
        },
        "safety": {
            "no_auto_execute": True,
            "no_hermes_dispatch": True,
            "no_tool_call": True,
            "no_file_write": True,
            "no_network_call": True,
            "no_email_send": True,
            "no_money_movement": True,
            "no_deploy": True,
            "no_credentials": True,
            "no_sensor_activation": True,
            "no_voice_recording": True,
            "no_camera_capture": True,
            "wake_phrase_is_not_permission": True,
        },
        "operator_guidance": {
            "can_do": (
                "David can inspect how JARVIS would receive a command, preview intent/risk placeholders, "
                "review gates and understand the next safe operator review step."
            ),
            "cannot_do_yet": (
                "This panel cannot submit commands, create missions, create approvals, call providers, "
                "write memory, dispatch Hermes, activate sensors or execute actions."
            ),
            "future_next_step": (
                "A later PR can add a safe read-only preview/intake classifier before any governed mission "
                "proposal flow is connected."
            ),
            "sensitive_requires_approval": (
                "Every sensitive action remains blocked until JARVIS has explicit operator approval, scope, "
                "risk, rollback/stop plan and audit gates."
            ),
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "read_only": True,
    }


def _mission_control_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Mission Control preview read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Conversation preview read",
            "source": "/mark-3/dashboard/status",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "No command execution performed",
            "source": "/mark-3/dashboard/status",
            "status": "blocked_by_preview",
            "read_only": True,
        },
        {
            "event": "Hermes dispatch disabled from Mission Control",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
    ]


def _source(endpoint: str, getter: Callable[[], Dict[str, Any]], timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        data = getter()
        timeline.append({"event": _event_name(endpoint), "source": endpoint, "status": "ok", "read_only": True})
        return dict(data or {})
    except Exception as exc:
        timeline.append(
            {
                "event": _event_name(endpoint),
                "source": endpoint,
                "status": "error",
                "read_only": True,
                "error": type(exc).__name__,
            }
        )
        return {"status": UNKNOWN, "error": type(exc).__name__, "source_endpoint": endpoint}


def _event_name(endpoint: str) -> str:
    mapping = {
        "/health": "backend status read",
        "/mark-3/release-candidate/status": "release candidate status read",
        "/mark-3/release-candidate/readiness": "readiness read",
        "/mark-3/release-candidate/dangerous-route-audit": "dangerous route audit read",
        "/mark-3/release-candidate/approval-path-audit": "approval path audit read",
        "/mark-3/release-candidate/e2e-smoke": "e2e smoke read",
        "/mark-3/release-candidate/pilot-plan": "pilot plan read",
    }
    return mapping.get(endpoint, f"{endpoint.strip('/').replace('/', ' ')} read")


def _module(name: str, status: str, source: str, risk: str, notes: str) -> Dict[str, str]:
    allowed = {"ready", "preview", "prepare-only", "gated", "disabled", "not_connected", "unknown"}
    return {
        "name": name,
        "status": status if status in allowed else UNKNOWN,
        "source": source,
        "risk": risk,
        "notes": notes,
    }


def _hermes_execution_projection(
    *,
    hermes_runtime: Dict[str, Any],
    research_execution: Dict[str, Any],
    running_sessions: int | None,
    session_count: int | None,
) -> Dict[str, Any]:
    runtime_available = _known_bool(hermes_runtime.get("available"))
    connected = runtime_available if runtime_available in {True, False} else UNKNOWN
    active_execution: bool | str = bool(running_sessions and running_sessions > 0) if running_sessions is not None else UNKNOWN

    contract = {
        "jarvis_role": "governs/risk/approval/audit/control",
        "hermes_role": "execution_engine",
        "no_duplicate_hermes_runtime": True,
        "frontend_direct_execution_allowed": False,
        "frontend_can_execute": False,
        "frontend_can_call_hermes_execute": False,
    }
    runtime_status = {
        "available": runtime_available,
        "connected": connected,
        "active_execution": active_execution,
        "execution_mode": "read_only_visibility",
        "last_execution": UNKNOWN,
        "last_result": UNKNOWN,
        "last_error": UNKNOWN,
        "last_rollback": UNKNOWN,
        "last_stop_plan": UNKNOWN,
        "measured_duration": UNKNOWN,
        "measured_cost": UNKNOWN,
        "running_sessions": running_sessions if running_sessions is not None else UNKNOWN,
        "session_count": session_count if session_count is not None else UNKNOWN,
        "supported_tool": hermes_runtime.get("supported_tool", UNKNOWN),
        "supported_action_type": hermes_runtime.get("supported_action_type", UNKNOWN),
        "supported_capability": hermes_runtime.get("supported_capability", UNKNOWN),
        "source_endpoint": "/mark-3/hermes-runtime/status",
    }
    governed_capabilities = [
        _hermes_capability(
            "local governed read",
            "gated" if runtime_available is True else "not_connected" if runtime_available is False else UNKNOWN,
            True,
            "direct",
            "Hermes can only be represented as a bounded local read candidate after JARVIS scope, risk and audit gates.",
        ),
        _hermes_capability(
            "local docs read",
            "ready" if research_execution.get("local_docs_repo_read_adapter_connected") else "not_connected",
            True,
            "direct",
            "Local docs/repo visibility is exact-path and read-only; broad scans and secrets remain blocked.",
        ),
        _hermes_capability(
            "repo/docs research adapter",
            "ready" if research_execution.get("local_docs_repo_read_adapter_connected") else "not_connected",
            True,
            "level_2_local_read",
            "Research control plane can prepare exact local docs/repo reads; GitHub/web providers are not connected here.",
        ),
        _hermes_capability(
            "mission-gated execution candidate",
            "gated",
            True,
            "risk_scaled",
            "A mission candidate is eligibility only; it is not execution and cannot be launched by the dashboard.",
        ),
        _hermes_capability(
            "approval-gated execution",
            "gated",
            True,
            "risk_scaled_strong_when_sensitive",
            "A valid approval is required before any future Hermes execution path; approval alone is not execution.",
        ),
        _hermes_capability(
            "external tools",
            "not_connected",
            True,
            "strong",
            "Browser, network, GitHub, provider and authenticated external tools are not connected to this panel.",
        ),
        _hermes_capability(
            "deploy/email/money/credentials",
            "forbidden",
            True,
            "level_4_or_forbidden",
            "Frontend access is forbidden; production, money and email require future governed backend gates, while secrets remain blocked.",
        ),
    ]
    return {
        **runtime_status,
        "available": runtime_status["available"],
        "connected": runtime_status["connected"],
        "active_execution": runtime_status["active_execution"],
        "last_execution": runtime_status["last_execution"],
        "last_result": runtime_status["last_result"],
        "last_error": runtime_status["last_error"],
        "measured_duration": runtime_status["measured_duration"],
        "measured_cost": runtime_status["measured_cost"],
        "frontend_direct_execution_allowed": False,
        "frontend_can_execute": False,
        "frontend_can_call_hermes_execute": False,
        "running_sessions": runtime_status["running_sessions"],
        "session_count": runtime_status["session_count"],
        "supported_tool": runtime_status["supported_tool"],
        "notes": (
            "Read-only visibility only: Hermes remains the execution engine behind JARVIS gates; "
            "the dashboard cannot call an execution route, run tools, approve, stop a real session, or duplicate Hermes."
        ),
        "contract": contract,
        "runtime_status": runtime_status,
        "governed_capabilities": governed_capabilities,
        "blocked_routes": [
            _blocked_route("/execute", "frontend execution route", "No generic execution route is available to the frontend."),
            _blocked_route("approve/reject", "approval mutation", "Approval decisions are displayed as disabled preview controls only."),
            _blocked_route("tool runner", "frontend tool runner", "The browser is not a tool runner and has no registry or tool invocation path."),
            _blocked_route("deploy", "production deploy", "Deploy remains blocked from this panel and requires future governed backend gates."),
            _blocked_route("money", "payments or spend", "Money movement, Stripe live and checkout remain blocked."),
            _blocked_route("email", "real email send", "The dashboard cannot send email or contact external recipients."),
            _blocked_route("credentials", "secrets and access material", "Credentials, tokens, cookies, sessions and bypass requests stay forbidden."),
            _blocked_route("sensor activation", "browser or device sensors", "The dashboard cannot activate microphone, camera, recording or sensor permissions."),
            _blocked_route("camera/mic", "camera or microphone runtime", "Voice and camera surfaces are status-only here."),
            _blocked_route(
                "network external unless gated future",
                "external network",
                "External network access is not connected to this panel and must be gated in future backend work.",
            ),
        ],
        "safety": {
            "no_frontend_execute": True,
            "no_frontend_tool_runner": True,
            "no_direct_hermes_call_from_mobile": True,
            "no_direct_hermes_call_from_voice": True,
            "no_direct_hermes_call_from_camera": True,
            "approval_required_before_execution": True,
            "wake_phrase_is_not_permission": True,
            "audit_required": True,
            "rollback_or_stop_plan_required_for_sensitive_actions": True,
        },
        "source_endpoint": "/mark-3/hermes-runtime/status",
    }


def _hermes_capability(
    name: str,
    status: str,
    approval_required: bool,
    approval_level: str,
    notes: str,
) -> Dict[str, Any]:
    allowed = {"ready", "gated", "prepare-only", "disabled", "not_connected", "forbidden", "unknown"}
    return {
        "name": name,
        "status": status if status in allowed else UNKNOWN,
        "approval_required": approval_required,
        "approval_level": approval_level,
        "can_execute_from_frontend": False,
        "notes": notes,
    }


def _blocked_route(route_or_action: str, action: str, notes: str) -> Dict[str, Any]:
    return {
        "route_or_action": route_or_action,
        "action": action,
        "blocked": True,
        "can_execute_from_frontend": False,
        "notes": notes,
    }


def _hermes_timeline_events(hermes_execution: Dict[str, Any]) -> List[Dict[str, Any]]:
    active_execution = hermes_execution["runtime_status"]["active_execution"]
    if active_execution is False:
        active_event = {
            "event": "No active Hermes execution",
            "source": "/mark-3/hermes-runtime/status",
            "status": "ok",
            "read_only": True,
        }
    elif active_execution is True:
        active_event = {
            "event": "Active Hermes execution reported by status read",
            "source": "/mark-3/hermes-runtime/status",
            "status": "read_only_observation",
            "read_only": True,
        }
    else:
        active_event = {
            "event": "Hermes active execution state unknown",
            "source": "/mark-3/hermes-runtime/status",
            "status": UNKNOWN,
            "read_only": True,
        }
    return [
        {
            "event": "Hermes execution visibility read",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
        active_event,
        {
            "event": "Frontend direct execution disabled",
            "source": "/mark-3/dashboard/status",
            "status": "ok",
            "read_only": True,
        },
        {
            "event": "Approval gates required before Hermes execution",
            "source": "/approvals/status",
            "status": "ok",
            "read_only": True,
        },
    ]


def _known_bool(value: Any) -> bool | str:
    return value if isinstance(value, bool) else UNKNOWN


def _pending_approval_count(app_state: Any) -> int | str:
    try:
        records = app_state.approval_hardening.list_records()
    except Exception:
        return UNKNOWN
    count = 0
    for record in records:
        status = getattr(record, "status", UNKNOWN)
        value = getattr(status, "value", status)
        if value == "pending":
            count += 1
    return count


def _approval_preview_cards(*, research_execution: Dict[str, Any]) -> List[Dict[str, Any]]:
    local_read_level = "direct" if research_execution.get("local_docs_repo_read_adapter_connected") else "simple"
    local_read_evidence = (
        "local_docs_repo_read_adapter_connected="
        f"{bool(research_execution.get('local_docs_repo_read_adapter_connected', False))}"
    )

    cards = [
        {
            "id": "preview-local-docs-repo-read",
            "title": "Lectura local exacta de docs/repo",
            "action": "Leer una ruta local exacta ya acotada.",
            "reason": "Lectura local bounded: bajo riesgo si el alcance es exacto y no muta estado.",
            "status": "preview",
            "risk_level": "low",
            "approval_level": local_read_level,
            "touches": ["filesystem", "local_docs"],
            "estimated_cost": UNKNOWN,
            "measured_cost": UNKNOWN,
            "rollback_plan": "No hay mutacion; rollback no aplica.",
            "stop_plan": "Parar si la ruta no es exacta, local y dentro del scope aprobado.",
            "expires_at": UNKNOWN,
            "scope_summary": "Un archivo o ruta local de docs/repo en modo lectura.",
            "evidence_summary": local_read_evidence,
            "disabled_reason": "Preview-only: approval execution is not wired in this PR.",
            "recommended_operator_action": "Verificar path exacto y mantenerlo read-only.",
            "requires_readback": False,
            "strong_confirmation_required": False,
            "double_confirmation_required": False,
            "triple_confirmation_required": False,
            "rollback_required": False,
            "stop_plan_required": True,
            "audit_required": True,
            "preview_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/research-execution/status",
        },
        {
            "id": "preview-local-file-write",
            "title": "Escritura de archivo local",
            "action": "Crear o modificar un archivo local.",
            "reason": "Cambia estado local y requiere scope, diff y rollback antes de cualquier ejecucion futura.",
            "status": "blocked",
            "risk_level": "medium",
            "approval_level": "simple",
            "touches": ["filesystem", "local_docs"],
            "estimated_cost": UNKNOWN,
            "measured_cost": UNKNOWN,
            "rollback_plan": "Exigir diff, backup o patch de reversion antes de una escritura futura.",
            "stop_plan": "Parar por path amplio, glob, diff ausente o cancelacion humana.",
            "expires_at": UNKNOWN,
            "scope_summary": "Un path local explicito y un diff exacto; sin escrituras recursivas.",
            "evidence_summary": "La consola no tiene endpoint de escritura.",
            "disabled_reason": "Blocked/read-only: la consola visual no tiene ruta de escritura.",
            "recommended_operator_action": "Pedir diff preview y aprobar solo un write bounded futuro.",
            "requires_readback": True,
            "strong_confirmation_required": False,
            "double_confirmation_required": False,
            "triple_confirmation_required": False,
            "rollback_required": True,
            "stop_plan_required": True,
            "audit_required": True,
            "preview_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/dashboard/status",
        },
        {
            "id": "preview-external-web-github-search",
            "title": "Busqueda externa web/GitHub",
            "action": "Consultar web o GitHub fuera del entorno local.",
            "reason": "Puede filtrar intencion, consumir cuota o traer contenido no confiable.",
            "status": "blocked",
            "risk_level": "high",
            "approval_level": "strong",
            "touches": ["web", "github"],
            "estimated_cost": UNKNOWN,
            "measured_cost": UNKNOWN,
            "rollback_plan": "No llamar proveedores externos hasta aprobar query, proveedor y manejo de datos.",
            "stop_plan": "Parar ante secrets, repos privados, scopes de cuenta o intencion ambigua.",
            "expires_at": UNKNOWN,
            "scope_summary": "Query/proveedor/fuentes especificos; sin acciones autenticadas.",
            "evidence_summary": "Web/GitHub no esta conectado a esta consola.",
            "disabled_reason": "Blocked/not connected: no hay ejecucion de approval web o GitHub aqui.",
            "recommended_operator_action": "Exigir approval fuerte antes de cualquier llamada externa futura.",
            "requires_readback": True,
            "strong_confirmation_required": True,
            "double_confirmation_required": False,
            "triple_confirmation_required": False,
            "rollback_required": True,
            "stop_plan_required": True,
            "audit_required": True,
            "preview_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/dashboard/status",
        },
        {
            "id": "preview-production-money-deploy-email",
            "title": "Produccion, dinero, deploy o email real",
            "action": "Deploy, Stripe/dinero o envio de email real.",
            "reason": "Tiene impacto externo o irreversible y requiere confirmacion fuerte.",
            "status": "blocked",
            "risk_level": "critical",
            "approval_level": "triple",
            "touches": ["money", "deploy", "email", "web"],
            "estimated_cost": UNKNOWN,
            "measured_cost": UNKNOWN,
            "rollback_plan": "Exigir rollback verificado, owner, blast radius y stop condition.",
            "stop_plan": "Parar ante coste no verificado, credencial viva, smoke fallido o cancelacion.",
            "expires_at": UNKNOWN,
            "scope_summary": "Cuenta, entorno, destinatario o importe nominal; sin scope amplio.",
            "evidence_summary": "Product/Revenue sigue prepare-only; finance queda unknown sin evidencia medida.",
            "disabled_reason": "Blocked/critical: este PR no conecta produccion, dinero, deploy, Stripe ni email.",
            "recommended_operator_action": "Requerir readback, doble/triple confirmacion, rollback, stop plan y auditoria.",
            "requires_readback": True,
            "strong_confirmation_required": True,
            "double_confirmation_required": True,
            "triple_confirmation_required": True,
            "rollback_required": True,
            "stop_plan_required": True,
            "audit_required": True,
            "preview_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/product-revenue/status",
        },
        {
            "id": "preview-forbidden-credentials-bypass",
            "title": "Credenciales, secrets, tokens o bypass",
            "action": "Leer secrets, tokens, cookies, sesiones, credenciales o saltar autorizacion.",
            "reason": "Credenciales, bypass, deception y fake metrics son limites forbidden.",
            "status": "forbidden",
            "risk_level": "forbidden",
            "approval_level": "forbidden",
            "touches": ["credentials"],
            "estimated_cost": UNKNOWN,
            "measured_cost": UNKNOWN,
            "rollback_plan": "No se ejecuta; redisenar como status/audit sin secretos.",
            "stop_plan": "Parar y rechazar si pide secrets, cookies, tokens, bypass, deception o metricas falsas.",
            "expires_at": UNKNOWN,
            "scope_summary": "Scope forbidden; ningun acceso a credenciales, tokens, cookies, sesiones o bypass.",
            "evidence_summary": "Safety boundary declara no_credentials=true y no fake metrics.",
            "disabled_reason": "Forbidden/blocked: esto no se puede aprobar desde la consola visual.",
            "recommended_operator_action": "Rechazar y pedir alternativa segura sin secretos.",
            "requires_readback": True,
            "strong_confirmation_required": True,
            "double_confirmation_required": True,
            "triple_confirmation_required": True,
            "rollback_required": False,
            "stop_plan_required": True,
            "audit_required": True,
            "preview_only": True,
            "read_only": True,
            "source_endpoint": "/mark-3/dashboard/status",
        },
    ]
    return cards


def _approval_summary(pending_count: int | str, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "pending_count": pending_count,
        "critical_count": sum(1 for card in cards if card.get("risk_level") == "critical"),
        "blocked_count": sum(1 for card in cards if card.get("status") in {"blocked", "forbidden"}),
        "expired_count": sum(1 for card in cards if card.get("status") == "expired"),
        "preview_count": sum(1 for card in cards if card.get("preview_only") is True),
    }


def _bool(source: Dict[str, Any], key: str, *, default: bool | None) -> bool | None:
    value = source.get(key, default)
    return value if isinstance(value, bool) else default


def _int(value: Any, *, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _merge_unique(*items: List[Any]) -> List[Any]:
    merged: List[Any] = []
    for group in items:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged


def _status_summary(source: Dict[str, Any]) -> Dict[str, Any]:
    keys = (
        "available",
        "prepare_only",
        "safe_to_render",
        "record_count",
        "candidate_count",
        "audit_event_count",
        "approval_alone_never_enables_execution",
        "runtime_execution_enabled",
        "side_effects_enabled",
    )
    return {key: source[key] for key in keys if key in source}
