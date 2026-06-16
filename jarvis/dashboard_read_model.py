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
    kill_switch_active = _bool(mission_loop, "kill_switch_active", default=None)
    kill_switch_state = "active" if kill_switch_active is True else "inactive" if kill_switch_active is False else "not_wired"
    running_sessions = _int(hermes_runtime.get("running_sessions"), default=None)
    session_count = _int(hermes_runtime.get("session_count"), default=None)

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
            "frontend_can_execute": False,
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
            "pending_count": pending_count,
            "action_buttons_enabled": False,
            "wake_phrase_can_approve": False,
            "critical_actions_require_strong_approval": True,
            "cards": [],
            "cards_state": "empty/read-only",
            "preview_only": True,
            "source_endpoint": "/approvals/status",
            "raw_status": _status_summary(approvals_status),
        },
        "hermes_execution": {
            "available": bool(hermes_runtime.get("available", False)),
            "active_execution": bool(running_sessions and running_sessions > 0) if running_sessions is not None else UNKNOWN,
            "last_execution": UNKNOWN,
            "frontend_direct_execution_allowed": False,
            "running_sessions": running_sessions if running_sessions is not None else UNKNOWN,
            "session_count": session_count if session_count is not None else UNKNOWN,
            "supported_tool": hermes_runtime.get("supported_tool", UNKNOWN),
            "notes": "Only governed exact local read_file exists behind mission candidate, approval, scope fingerprint, and operator authorization; the dashboard cannot trigger it.",
            "source_endpoint": "/mark-3/hermes-runtime/status",
        },
        "voice_wake": {
            "microphone_state": "disabled" if voice_runtime.get("microphone_active") is False else UNKNOWN,
            "wake_word_state": "preview" if wake_listener.get("real_wake_listener_available") else "not_connected",
            "wake_phrases": _list(wake_listener.get("supported_wake_phrases")) or ["Hola Jarvis", "Jarvis"],
            "wake_phrase_can_approve": False,
            "audio_recording": False,
            "source_endpoints": ["/voice-runtime/status", "/mark-2/wake-listener/status"],
        },
        "camera_vision": {
            "camera_state": "disabled" if camera_control.get("camera_session_active") is False else UNKNOWN,
            "preview_state": "disabled",
            "recording": False,
            "vision_analysis": "disabled",
            "storage": False,
            "source_endpoint": "/camera-control/status",
        },
        "mobile": {
            "companion_state": "not_connected" if mobile_status.get("native_app_connected") is False else UNKNOWN,
            "direct_hermes_call_allowed": False,
            "remote_kill_switch_state": "future_gated",
            "approval_actions_enabled": False,
            "source_endpoints": ["/mobile/companion/status", "/mobile/companion/permissions"],
            "permissions": {
                "can_read_command_center": bool(mobile_permissions.get("can_read_command_center", False)),
                "can_execute": False,
                "can_approve": False,
            },
        },
        "finance": {
            "actual_cost": UNKNOWN,
            "estimated_cost": UNKNOWN,
            "confirmed_revenue": UNKNOWN,
            "projected_revenue": UNKNOWN,
            "roi": UNKNOWN,
            "no_fake_metrics": True,
            "source": "No measurement evidence connected to this read model.",
        },
        "product_builder": {
            "stages": [
                "Idea",
                "Validaci\u00f3n",
                "Blueprint",
                "C\u00f3digo",
                "Landing",
                "Deploy candidate",
                "Monetizaci\u00f3n",
            ],
            "deploy_requires_strong_approval": True,
            "stripe_checkout_requires_strong_approval": True,
            "real_revenue_must_be_confirmed": True,
            "source_endpoint": "/mark-3/product-revenue/status",
        },
        "safety": {
            "no_get_user_media": True,
            "no_sensor_activation": True,
            "no_frontend_tool_runner": True,
            "no_frontend_hermes_execution": True,
            "no_money_movement": True,
            "no_deploy": True,
            "no_credentials": True,
            "no_email_send": True,
        },
        "timeline": timeline
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
