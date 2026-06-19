from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import sys
from typing import Any, Callable, Dict, Iterable, List

from jarvis.mark_3_approval_path_audit import Mark3ApprovalPathAudit
from jarvis.mark_3_dangerous_route_audit import Mark3DangerousRouteAudit
from jarvis.mark_3_e2e_readiness import Mark3E2EReadinessSmoke
from jarvis.mark_3_pilot_plan import Mark3ControlledPilotPlan
from jarvis.mark_3_release_candidate import Mark3CapabilityMatrix, Mark3ReadinessMatrix, Mark3ReleaseCandidateStatus
from jarvis.mobile.companion import MobileCompanionPermissionPolicy, MobileCompanionStatus
from jarvis.sensor_ledger import build_sensor_ledger_status


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
    route_path_list = list(route_paths)

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
        lambda: Mark3DangerousRouteAudit().audit(route_path_list),
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
    personal_memory_status = _source(
        "/personal-memory/status",
        lambda: app_state.personal_memory_control.status(),
        timeline,
    )
    persistent_audit = _source(
        "/mark-3/audit/status",
        lambda: app_state.persistent_audit_ledger.status(),
        timeline,
    )
    memory_brain_v2_status = _source(
        "/mark-3/memory-brain/status",
        lambda: app_state.memory_brain_v2.status(),
        timeline,
    )
    memory_brain_v2_preview = _source(
        "/mark-3/memory-brain/preview",
        lambda: app_state.memory_brain_v2.preview(),
        timeline,
    )
    conversational_brain = _source(
        "/mark-3/conversational-brain/status",
        lambda: app_state.conversational_brain_bridge.status(),
        timeline,
    )
    conversational_intake = _source(
        "/mark-3/conversational-intake/status",
        lambda: app_state.conversational_intake_pipeline.status(),
        timeline,
    )
    brain_adapter = _source(
        "/mark-3/brain-adapter/status",
        lambda: app_state.llm_brain_adapter.status(),
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
    voice_session = _source(
        "/voice-runtime/session-status",
        lambda: app_state.voice_session_control.status(wake_listener_status=wake_listener),
        timeline,
    )
    voice_runtime_pack = _source(
        "/mark-3/voice-runtime/status",
        lambda: app_state.voice_runtime_pack.status(
            wake_listener_status=wake_listener,
            voice_session_status=voice_session,
        ),
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
    conversational_brain_timeline = _conversational_brain_timeline_events(conversational_brain)
    conversational_intake_timeline = _conversational_intake_timeline_events(conversational_intake)
    brain_adapter_timeline = _brain_adapter_timeline_events(brain_adapter)
    voice_core = _voice_core_projection(voice_runtime=voice_runtime, wake_listener=wake_listener)
    voice_core_timeline = _voice_core_timeline_events()
    voice_runtime_pack_timeline = _voice_runtime_pack_timeline_events(voice_runtime_pack)
    wake_word_flow = _wake_word_flow_projection(wake_listener=wake_listener)
    wake_word_flow_timeline = _wake_word_flow_timeline_events()
    local_voice_loop = _local_voice_loop_projection()
    local_voice_loop_timeline = _local_voice_loop_timeline_events()
    camera_vision = _camera_vision_projection(camera_control=camera_control)
    camera_vision_timeline = _camera_vision_timeline_events()
    raw_audio_recording = _raw_audio_recording_projection()
    raw_audio_recording_timeline = _raw_audio_recording_timeline_events()
    memory_brain = _memory_brain_projection(
        memory_status=memory_status,
        learning_status=learning_status,
        personal_memory_status=personal_memory_status,
        memory_brain_v2_status=memory_brain_v2_status,
        memory_brain_v2_preview=memory_brain_v2_preview,
    )
    memory_brain_timeline = _memory_brain_timeline_events(memory_brain)
    persistent_audit_timeline = _persistent_audit_timeline_events(persistent_audit)
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
    visual_command_center_pilot = _visual_command_center_pilot_projection()
    visual_command_center_pilot_timeline = _visual_command_center_pilot_timeline_events()
    local_system_contract = _local_system_contract_projection()
    local_system_contract_timeline = _local_system_contract_timeline_events()
    local_doctor = build_local_doctor_status(
        app_state=app_state,
        route_paths=route_path_list,
        generated_at=generated_at,
        health=health,
        hermes_runtime=hermes_runtime,
        voice_runtime_pack=voice_runtime_pack,
    )
    local_doctor_timeline = _local_doctor_timeline_events(local_doctor)
    sensor_ledger = build_sensor_ledger_status(
        ledger=getattr(app_state, "sensor_ledger", None),
        generated_at=generated_at,
    )
    sensor_ledger_timeline = _sensor_ledger_timeline_events(sensor_ledger)
    policy_status = _policy_status_projection()
    policy_status_timeline = _policy_status_timeline_events()

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
        "local_system_contract": local_system_contract,
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
                "Conversational Brain",
                "preview",
                "/mark-3/conversational-brain/status",
                "intent_risk_preview",
                "Local deterministic bridge only; no LLM, no memory autosave, no Hermes dispatch.",
            ),
            _module(
                "Conversational Intake",
                "preview",
                "/mark-3/conversational-intake/status",
                "intent_risk_preview",
                "Normalizes typed, voice, wake and future remote input into safe intake; never executes.",
            ),
            _module(
                "Brain Adapter",
                "preview",
                "/mark-3/brain-adapter/status",
                "llm_provider_disabled_by_default",
                "Default provider is deterministic_local; external LLM provider is disabled and not called.",
            ),
            _module(
                "Voice",
                "browser_controlled",
                "/mark-3/voice-runtime/status",
                "sensor_privacy",
                "Voice Runtime Pack exposes manual browser voice, provider contracts, transcript/TTS lifecycle and safe local provider status.",
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
                "ready" if memory_brain_v2_status.get("state", {}).get("available") else UNKNOWN,
                "/mark-3/memory-brain/status",
                "memory_never_grants_permission",
                "Persistent Memory Brain v2 is local/read-only from dashboard; proposals never authorize execution.",
            ),
            _module(
                "Persistent Audit",
                "ready" if persistent_audit.get("state", {}).get("available") else UNKNOWN,
                "/mark-3/audit/status",
                "metadata_audit",
                "Local metadata-only hash-chain ledger for voice, sensors, intake, brain, memory and approval events.",
            ),
            _module(
                "Sensor Ledger",
                "ready",
                "/mark-3/dashboard/status",
                "sensor_privacy",
                "Metadata-only local sensor/session ledger; no raw audio, frames, or credential material.",
            ),
            _module(
                "Policy Status",
                "ready",
                "/mark-3/dashboard/status",
                "approval_boundary",
                "Read-only policy projection for direct, approval-gated, strong-gated, and denied actions.",
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
        "conversational_brain": conversational_brain,
        "conversational_intake": conversational_intake,
        "brain_adapter": brain_adapter,
        "voice_runtime_pack": voice_runtime_pack,
        "voice_session": voice_session,
        "wake_architecture": voice_session.get("wake_architecture", {}),
        "voice_core": voice_core,
        "local_voice_loop": local_voice_loop,
        "wake_word_flow": wake_word_flow,
        "voice_wake": {
            "microphone_state": "disabled" if voice_core["state"]["microphone_enabled"] is False else UNKNOWN,
            "wake_word_state": voice_core["state"]["current_state"],
            "wake_phrases": voice_core["wake_word_policy"]["supported_phrases"],
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "local_voice_loop": "browser_controlled_manual_only",
            "browser_stt_supported": voice_runtime_pack.get("browser_stt_available", UNKNOWN),
            "browser_tts_supported": voice_runtime_pack.get("browser_tts_available", UNKNOWN),
            "audio_recording": False,
            "raw_audio_stored": False,
            "raw_audio_sent_to_backend": False,
            "external_provider_called": False,
            "source_endpoints": ["/mark-3/voice-runtime/status", "/voice-runtime/status", "/mark-2/wake-listener/status"],
        },
        "camera_vision": camera_vision,
        "raw_audio_recording": raw_audio_recording,
        "persistent_audit": persistent_audit,
        "sensor_ledger": sensor_ledger,
        "policy_status": policy_status,
        "memory_brain_v2": memory_brain_v2_status,
        "memory_brain": memory_brain,
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
        "visual_command_center_pilot": visual_command_center_pilot,
        "event_bus": {
            "snapshot_endpoint": "/mark-3/dashboard/events",
            "sse_endpoint": "/mark-3/dashboard/events/stream",
            "mode": "read_only_event_projection",
            "schema_version": "jarvis.dashboard.events.v1",
            "allowed_methods": ["GET"],
            "event_types": [
                "intake_state",
                "brain_adapter_state",
                "brain_state",
                "voice_runtime_state",
                "voice_state",
                "voice_session_state",
                "wake_state",
                "tts_state",
                "hermes_state",
                "approval_state",
                "mission_state",
                "camera_state",
                "recording_state",
                "memory_state",
                "risk_state",
                "execution_state",
                "audit_event",
                "persistent_audit_state",
                "memory_brain_v2_state",
                "remote_state",
                "doctor_state",
                "performance_state",
                "sensor_ledger_state",
                "policy_state",
                "heartbeat",
            ],
            "required_event_fields": [
                "schema_version",
                "event_id",
                "event_type",
                "source",
                "created_at",
                "payload",
            ],
            "heartbeat_enabled": True,
            "disconnect_safe": True,
            "no_secrets": True,
            "no_raw_audio": True,
            "no_camera_frames": True,
            "frontend_can_execute": False,
            "stream_can_execute": False,
            "preview_only": True,
            "read_only": True,
        },
        "safety": {
            "frontend_can_execute": False,
            "frontend_can_approve": False,
            "no_auto_execute": True,
            "no_frontend_execute": True,
            "no_duplicate_hermes_runtime": True,
            "no_get_user_media": False,
            "no_sensor_activation": False,
            "no_uncontrolled_sensor_activation": True,
            "no_sensor_activation_on_load": True,
            "manual_browser_voice_activation_only": True,
            "manual_browser_camera_activation_only": True,
            "manual_browser_raw_audio_recording_only": True,
            "no_hidden_voice_recording": True,
            "no_voice_recording": False,
            "no_browser_raw_audio_capture": False,
            "no_raw_audio_backend_upload": True,
            "no_camera_capture": False,
            "no_camera_activation_on_load": True,
            "no_camera_snapshot_storage": True,
            "no_camera_streaming_to_backend": True,
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
        + conversational_brain_timeline
        + conversational_intake_timeline
        + brain_adapter_timeline
        + voice_runtime_pack_timeline
        + list(voice_session.get("timeline", []))
        + voice_core_timeline
        + wake_word_flow_timeline
        + local_voice_loop_timeline
        + camera_vision_timeline
        + raw_audio_recording_timeline
        + persistent_audit_timeline
        + memory_brain_timeline
        + mobile_companion_timeline
        + finance_roi_timeline
        + adaptive_product_builder_timeline
        + frontend_pilot_timeline
        + visual_command_center_pilot_timeline
        + local_system_contract_timeline
        + local_doctor_timeline
        + sensor_ledger_timeline
        + policy_status_timeline
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
            "frontend_must_not_request_sensor_permissions": False,
            "frontend_sensor_permission_scope": "manual browser SpeechRecognition, manual camera preview, manual local raw audio recorder",
            "frontend_must_not_request_camera_permissions": False,
            "frontend_camera_permission_scope": "manual preview only; no backend stream, no analysis, no storage",
            "frontend_is_not_runtime": True,
            "web_route_is_visual_interface_only": True,
            "local_runtime_daemon_is_system": True,
            "mobile_and_vps_are_future_clients_or_bridges": True,
        },
        "local_doctor": local_doctor,
    }
    return payload


def _local_system_contract_projection() -> Dict[str, Any]:
    return {
        "name": "Local System Contract",
        "presence_ui": "JARVIS Presence UI",
        "local_runtime_daemon_is_system": True,
        "web_route": "/jarvis",
        "web_route_is_visual_interface_only": True,
        "frontend_executes_hermes_directly": False,
        "frontend_is_runtime": False,
        "frontend_can_activate_real_voice": True,
        "frontend_can_activate_real_camera": True,
        "frontend_can_record_raw_audio_locally": True,
        "frontend_can_record_video_locally": True,
        "mobile_and_vps_are_future_clients_or_bridges": True,
        "real_voice_camera_in_future_prs": False,
        "real_browser_voice_loop_in_this_pr": True,
        "real_browser_camera_preview_in_this_pr": True,
        "real_browser_raw_audio_recorder_in_this_pr": True,
        "real_browser_video_recorder_in_this_pr": True,
        "real_camera_in_future_prs": False,
        "real_vision_analysis_in_future_prs": True,
        "jarvis_governs": True,
        "hermes_executes": True,
        "no_duplicate_hermes_runtime": True,
        "visual_contract": {
            "primary_experience": "Presence UI",
            "central_core_states": [
                "idle/calmado",
                "escuchando",
                "transcribiendo",
                "pensando",
                "hablando",
                "error/no disponible",
            ],
            "smart_bar": "local voice transcript/response preview",
            "camera_placeholder": "manual opt-in local camera preview panel",
            "raw_audio_recorder": "manual opt-in local MediaRecorder panel",
            "folded_history": "collapsed preview",
        },
        "future_bridges": {
            "mobile": "future client/bridge",
            "vps": "future secure bridge",
            "voice_runtime": "future daemon/wake/always-on work; this PR is browser manual only",
            "camera_runtime": "future daemon/vision analysis PR; browser preview is local-only now",
        },
        "safety": {
            "no_post_put_delete_from_jarvis_page": True,
            "no_execute_route": True,
            "no_frontend_hermes_execution": True,
            "no_browser_sensor_permission": False,
            "browser_voice_permission_manual_only": True,
            "browser_camera_permission_manual_only": True,
            "browser_raw_audio_recording_manual_only": True,
            "no_uncontrolled_sensor_activation": True,
            "no_real_voice": False,
            "no_real_camera": False,
            "no_backend_voice_runtime": True,
            "no_backend_camera_runtime": True,
            "no_backend_audio_upload": True,
            "no_sensor_activation_on_load": True,
            "no_money": True,
            "no_deploy": True,
            "no_email": True,
            "no_credentials": True,
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "preview_only": True,
        "read_only": True,
    }


def _local_system_contract_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Local System Contract read",
            "source": "/mark-3/dashboard/status",
            "status": "read_only",
            "read_only": True,
        },
        {
            "event": "Presence UI contract read",
            "source": "/jarvis",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Smart bar preview loaded",
            "source": "/jarvis",
            "status": "disabled_preview",
            "read_only": True,
        },
        {
            "event": "Manual camera preview panel rendered",
            "source": "/jarvis",
            "status": "manual_opt_in_local_only",
            "read_only": True,
        },
        {
            "event": "Camera placeholder rendered",
            "source": "/jarvis",
            "status": "manual_opt_in_local_only",
            "read_only": True,
        },
        {
            "event": "Manual raw audio recorder panel rendered",
            "source": "/jarvis",
            "status": "manual_opt_in_local_only",
            "read_only": True,
        },
        {
            "event": "Folded history preview loaded",
            "source": "/jarvis",
            "status": "collapsed_preview",
            "read_only": True,
        },
    ]


def build_local_doctor_status(
    *,
    app_state: Any,
    route_paths: Iterable[str],
    generated_at: str,
    health: Dict[str, Any] | None = None,
    hermes_runtime: Dict[str, Any] | None = None,
    voice_runtime_pack: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    route_path_set = set(route_paths)
    health_status = dict(health or {"status": UNKNOWN})
    hermes_status = dict(hermes_runtime or {})
    voice_pack = dict(voice_runtime_pack or {})
    psutil_status = _psutil_status()
    process_info = _process_info(psutil_status)
    browser_capabilities = {
        "webgl": {"status": "client_side_unknown", "activation_required": False, "checked_by_backend": False},
        "camera": {"status": "client_side_unknown", "activation_required": True, "checked_by_backend": False},
        "mic": {"status": "client_side_unknown", "activation_required": True, "checked_by_backend": False},
        "stt": {"status": "client_side_unknown", "activation_required": True, "checked_by_backend": False},
        "tts": {"status": "client_side_unknown", "activation_required": False, "checked_by_backend": False},
    }
    return {
        "state": {
            "mode": "read_only_local_doctor",
            "generated_at": generated_at,
            "backend_reachable": health_status.get("status") == "ok",
            "frontend_build_status": "external_validation_required",
            "frontend_route_expected": "/jarvis",
            "dashboard_status_endpoint": _route_exists(route_path_set, "/mark-3/dashboard/status"),
            "frontend_route_status": "expected_by_vite",
            "event_snapshot_endpoint": _route_exists(route_path_set, "/mark-3/dashboard/events"),
            "event_stream_endpoint": _route_exists(route_path_set, "/mark-3/dashboard/events/stream"),
            "event_stream_available": _route_exists(route_path_set, "/mark-3/dashboard/events/stream"),
            "conversational_intake_endpoint": _route_exists(route_path_set, "/mark-3/conversational-intake/status"),
            "brain_adapter_endpoint": _route_exists(route_path_set, "/mark-3/brain-adapter/status"),
            "voice_runtime_pack_endpoint": _route_exists(route_path_set, "/mark-3/voice-runtime/status"),
            "persistent_audit_endpoint": _route_exists(route_path_set, "/mark-3/audit/status"),
            "memory_brain_v2_endpoint": _route_exists(route_path_set, "/mark-3/memory-brain/status"),
            "memory_brain_v2_preview_endpoint": _route_exists(route_path_set, "/mark-3/memory-brain/preview"),
            "hermes_status_endpoint": _route_exists(route_path_set, "/mark-3/hermes-runtime/status"),
            "hermes_status": "ok" if hermes_status.get("available") is True else "not_connected" if hermes_status.get("available") is False else UNKNOWN,
            "local_doctor_endpoint": _route_exists(route_path_set, "/mark-3/local-doctor/status"),
            "browser_stt": "client_side_unknown",
            "browser_tts": "client_side_unknown",
            "camera_support": "client_side_unknown",
            "webgl_support": "client_side_unknown",
        },
        "checks": [
            _doctor_check("backend", "ok" if health_status.get("status") == "ok" else UNKNOWN, "GET /health"),
            _doctor_check(
                "dashboard_read_model",
                "ok" if _route_exists(route_path_set, "/mark-3/dashboard/status") else "missing",
                "GET /mark-3/dashboard/status",
            ),
            _doctor_check(
                "event_stream",
                "ok" if _route_exists(route_path_set, "/mark-3/dashboard/events/stream") else "missing",
                "GET /mark-3/dashboard/events/stream",
            ),
            _doctor_check(
                "conversational_intake",
                "ok" if _route_exists(route_path_set, "/mark-3/conversational-intake/status") else "missing",
                "GET /mark-3/conversational-intake/status",
            ),
            _doctor_check(
                "brain_adapter",
                "ok" if _route_exists(route_path_set, "/mark-3/brain-adapter/status") else "missing",
                "GET /mark-3/brain-adapter/status",
            ),
            _doctor_check(
                "voice_runtime_pack",
                "ok" if _route_exists(route_path_set, "/mark-3/voice-runtime/status") else "missing",
                "GET /mark-3/voice-runtime/status",
            ),
            _doctor_check(
                "persistent_audit",
                "ok" if _route_exists(route_path_set, "/mark-3/audit/status") else "missing",
                "GET /mark-3/audit/status",
            ),
            _doctor_check(
                "memory_brain_v2",
                "ok" if _route_exists(route_path_set, "/mark-3/memory-brain/status") else "missing",
                "GET /mark-3/memory-brain/status",
            ),
            _doctor_check(
                "hermes_status",
                "ok" if hermes_status.get("available") is True else "not_connected" if hermes_status.get("available") is False else UNKNOWN,
                "/mark-3/hermes-runtime/status",
            ),
            _doctor_check("browser_stt", "client_side_unknown", "window.SpeechRecognition || window.webkitSpeechRecognition"),
            _doctor_check("browser_tts", "client_side_unknown", "window.speechSynthesis"),
            _doctor_check("camera", "client_side_unknown", "navigator.mediaDevices.getUserMedia checked in browser only"),
            _doctor_check("microphone", "client_side_unknown", "navigator.mediaDevices.getUserMedia checked in browser only"),
            _doctor_check("webgl", "client_side_unknown", "canvas.getContext('webgl') checked in browser only"),
            _doctor_check("python_version", platform.python_version(), "sys.version_info"),
            _doctor_check("platform", platform.platform(), "platform.platform()"),
            _doctor_check("process", process_info["status"], "os.getpid plus psutil when installed"),
        ],
        "optional_dependencies": {
            "ffmpeg": _binary_status("ffmpeg"),
            "openwakeword": _python_dependency_status("openwakeword"),
            "faster_whisper": _python_dependency_status("faster_whisper"),
            "whisper_cpp": _binary_status("whisper-cli"),
            "piper": _python_dependency_status("piper"),
            "sounddevice": _python_dependency_status("sounddevice"),
            "torch": _python_dependency_status("torch"),
            "psutil": psutil_status,
        },
        "runtime": {
            "python_version": platform.python_version(),
            "python_executable_name": sys.executable.rsplit("/", 1)[-1],
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "process": process_info,
        },
        "ports": {
            "backend_default": 9119,
            "frontend_default": 5173,
            "expected": [
                {"name": "backend", "port": 9119, "protocol": "http", "status": "expected"},
                {"name": "frontend", "port": 5173, "protocol": "http", "status": "expected"},
            ],
            "runtime_status": "not_checked_by_read_only_doctor",
        },
        "browser_checks": browser_capabilities,
        "browser_only_capabilities": browser_capabilities,
        "safety": {
            "read_only": True,
            "no_auto_install": True,
            "no_sensor_activation": True,
            "no_sensor_permission_request": True,
            "no_camera_probe": True,
            "no_microphone_probe": True,
            "no_browser_api_probe_from_backend": True,
            "no_secret_read": True,
            "no_env_dump": True,
            "no_hermes_execution": True,
            "no_voice_provider_install": True,
            "no_voice_model_download": True,
            "persistent_audit_metadata_only": True,
            "memory_brain_v2_no_autoload": True,
        },
        "source_endpoint": "/mark-3/local-doctor/status",
        "preview_only": False,
        "read_only": True,
        "source_status": {
            "hermes": _status_summary(hermes_status),
            "personal_memory": _status_summary(getattr(app_state, "personal_memory_control", object()).status() if hasattr(getattr(app_state, "personal_memory_control", None), "status") else {}),
            "voice_runtime_pack": _status_summary(voice_pack),
        },
    }


def _local_doctor_timeline_events(local_doctor: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "event": "Local doctor status generated",
            "source": "/mark-3/local-doctor/status",
            "status": local_doctor["state"]["mode"],
            "read_only": True,
        },
        {
            "event": "Browser capability checks remain client-side",
            "source": "/mark-3/local-doctor/status",
            "status": "client_side_unknown",
            "read_only": True,
        },
        {
            "event": "No dependency installation performed",
            "source": "/mark-3/local-doctor/status",
            "status": "read_only",
            "read_only": True,
        },
    ]


def _sensor_ledger_timeline_events(sensor_ledger: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "event": "Sensor Ledger status read",
            "source": "/mark-3/dashboard/status",
            "status": sensor_ledger["state"]["mode"],
            "read_only": True,
        },
        {
            "event": "Sensor Ledger stores metadata only",
            "source": "/mark-3/dashboard/status",
            "status": "metadata_only",
            "read_only": True,
        },
        {
            "event": "Sensor Ledger confirms no raw media storage",
            "source": "/mark-3/dashboard/status",
            "status": "no_raw_audio_no_frames",
            "read_only": True,
        },
    ]


def _policy_status_projection() -> Dict[str, Any]:
    return {
        "schema_version": "jarvis.policy_status.v1",
        "state": {
            "mode": "read_only_policy_status",
            "jarvis_governs": True,
            "hermes_executes": True,
            "frontend_executes_hermes_directly": False,
            "wake_phrase_never_approves": True,
            "sensors_require_opt_in": True,
            "dangerous_execution_requires_approval_gateway": True,
        },
        "direct_allowed": [
            {
                "capability": "render local dashboard/read models",
                "risk_level": "low",
                "approval_level": "direct",
                "can_execute_from_frontend": False,
                "notes": "Read-only status projection.",
            },
            {
                "capability": "prepare local previews",
                "risk_level": "low",
                "approval_level": "direct",
                "can_execute_from_frontend": False,
                "notes": "Preview/intent summaries only; no Hermes dispatch.",
            },
            {
                "capability": "read bounded local status/audit",
                "risk_level": "low",
                "approval_level": "direct",
                "can_execute_from_frontend": False,
                "notes": "Status endpoints and audit projections only.",
            },
        ],
        "requires_simple_approval": [
            {
                "capability": "bounded local file/repo read outside dashboard status",
                "risk_level": "medium",
                "approval_level": "simple",
                "requirements": ["exact scope", "read-only intent", "audit"],
            },
            {
                "capability": "sensor session start",
                "risk_level": "sensor_privacy",
                "approval_level": "simple",
                "requirements": ["operator opt-in", "visible indicator", "stop/cancel", "audit"],
            },
        ],
        "requires_strong_approval": [
            {
                "capability": "filesystem write or persistent mutation",
                "risk_level": "high",
                "approval_level": "strong",
                "requirements": ["ApprovalGateway", "risk classification", "audit", "rollback/stop plan"],
            },
            {
                "capability": "external network action with side effects",
                "risk_level": "high",
                "approval_level": "strong",
                "requirements": ["bounded target", "operator readback", "audit", "stop plan"],
            },
        ],
        "requires_double_approval": [
            {
                "capability": "production deploy/domain/publication",
                "risk_level": "critical",
                "approval_level": "double",
                "requirements": ["ApprovalGateway", "impact summary", "rollback plan", "operator confirmation"],
            }
        ],
        "requires_triple_approval": [
            {
                "capability": "money movement/live Stripe/bulk email/credentials-impacting action",
                "risk_level": "critical",
                "approval_level": "triple",
                "requirements": [
                    "ApprovalGateway",
                    "risk classification",
                    "audit",
                    "readback",
                    "rollback/stop plan",
                    "human confirmation",
                ],
            }
        ],
        "denied": [
            {
                "capability": "secret/token/cookie extraction or authorization bypass",
                "risk_level": "forbidden",
                "approval_level": "forbidden",
                "reason": "Credential material and bypass are not approval-gated capabilities.",
            },
            {
                "capability": "hidden sensor activation or background recording",
                "risk_level": "forbidden",
                "approval_level": "forbidden",
                "reason": "Sensors require opt-in, visible indicator, stop/cancel, and audit.",
            },
            {
                "capability": "frontend direct Hermes execution",
                "risk_level": "forbidden",
                "approval_level": "forbidden",
                "reason": "JARVIS governs; Hermes executes only behind backend gates.",
            },
            {
                "capability": "wake phrase approval",
                "risk_level": "forbidden",
                "approval_level": "forbidden",
                "reason": "Wake phrase can open a command window but never approves.",
            },
        ],
        "dangerous_execution_contract": {
            "approval_gateway_required": True,
            "risk_classification_required": True,
            "audit_required": True,
            "rollback_or_stop_plan_required": True,
            "wake_phrase_never_approves": True,
            "frontend_never_executes_hermes_directly": True,
            "no_duplicate_hermes_runtime": True,
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "read_only": True,
    }


def _policy_status_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Policy status read",
            "source": "/mark-3/dashboard/status",
            "status": "read_only_policy_status",
            "read_only": True,
        },
        {
            "event": "JARVIS governs and Hermes executes policy confirmed",
            "source": "/mark-3/dashboard/status",
            "status": "governed",
            "read_only": True,
        },
        {
            "event": "Wake phrase never approves policy confirmed",
            "source": "/mark-3/dashboard/status",
            "status": "forbidden",
            "read_only": True,
        },
    ]


def _psutil_status() -> Dict[str, Any]:
    if importlib.util.find_spec("psutil") is None:
        return {
            "available": False,
            "source": "python_importlib",
            "status": "unavailable",
        }
    try:
        import psutil  # type: ignore

        return {
            "available": True,
            "source": "python_importlib",
            "status": "available",
            "version": getattr(psutil, "__version__", UNKNOWN),
        }
    except Exception as exc:  # pragma: no cover - defensive optional dependency path
        return {
            "available": False,
            "source": "python_importlib",
            "status": "error",
            "error": exc.__class__.__name__,
        }


def _process_info(psutil_status: Dict[str, Any]) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "status": "basic",
        "pid": os.getpid(),
        "ppid": os.getppid() if hasattr(os, "getppid") else UNKNOWN,
        "psutil_available": bool(psutil_status.get("available")),
    }
    if not psutil_status.get("available"):
        return info
    try:
        import psutil  # type: ignore

        process = psutil.Process(os.getpid())
        memory = process.memory_info()
        info.update(
            {
                "status": "psutil",
                "name": process.name(),
                "num_threads": process.num_threads(),
                "memory_rss_bytes": getattr(memory, "rss", UNKNOWN),
                "memory_vms_bytes": getattr(memory, "vms", UNKNOWN),
            }
        )
    except Exception as exc:  # pragma: no cover - defensive optional dependency path
        info.update({"status": "psutil_error", "error": exc.__class__.__name__})
    return info


def _doctor_check(name: str, status: str, evidence: str) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "evidence": evidence,
        "read_only": True,
    }


def _binary_status(name: str) -> Dict[str, Any]:
    return {
        "available": shutil.which(name) is not None,
        "source": "PATH",
    }


def _python_dependency_status(module_name: str) -> Dict[str, Any]:
    return {
        "available": importlib.util.find_spec(module_name) is not None,
        "source": "python_importlib",
    }


def _route_exists(route_paths: Iterable[str], path: str) -> bool:
    return path in set(route_paths)


def _local_voice_loop_projection() -> Dict[str, Any]:
    return {
        "state": {
            "mode": "browser_controlled_manual_loop",
            "current_state": "idle",
            "activation": "explicit_operator_button",
            "always_listening": False,
            "manual_continuous_conversation": True,
            "conversation_active": False,
            "conversation_timeout_seconds": 180,
            "wake_listening": False,
            "wake_listening_real_enabled": False,
            "recording": False,
            "continuous_recording": False,
            "wake_listener_enabled": False,
            "wake_phrase_approval": False,
            "hermes_dispatch_enabled": False,
            "critical_action_execution_enabled": False,
        },
        "capabilities": {
            "browser_stt_supported": UNKNOWN,
            "browser_tts_supported": UNKNOWN,
            "browser_stt_detection": "window.SpeechRecognition || window.webkitSpeechRecognition",
            "browser_tts_detection": "window.speechSynthesis && window.SpeechSynthesisUtterance",
            "support_detection_location": "browser",
            "browser_may_use_external_services": True,
            "backend_stt_provider": "none/not_called",
            "backend_tts_provider": "none/not_called",
        },
        "browser_stt_supported": UNKNOWN,
        "browser_tts_supported": UNKNOWN,
        "manual_microphone_opt_in": True,
        "audio_storage": False,
        "raw_audio_sent_to_backend": False,
        "approval_by_voice_enabled": False,
        "wake_phrase_approval": False,
        "visual_states": [
            "idle",
            "listening",
            "transcribing",
            "thinking",
            "speaking",
            "error",
            "not_supported",
            "unavailable",
        ],
        "mode_contract": {
            "wake_listening": {
                "enabled_in_this_pr": False,
                "future_contract_only": True,
                "records_audio": False,
                "transcribes_full_conversation": False,
                "sends_raw_audio_to_backend": False,
                "executes": False,
                "approves": False,
                "detects_activation_only": True,
            },
            "conversation_active": {
                "enabled_in_this_pr": True,
                "activation": "manual_microphone_button",
                "transcribes_operator_speech": True,
                "keeps_loop_until_stop_or_timeout": True,
                "timeout_seconds": 180,
                "executes": False,
                "approves": False,
            },
            "recording": {
                "enabled": False,
                "raw_audio_storage": False,
                "backend_audio_upload": False,
            },
        },
        "tone_profiles": [
            {"tone": "calmado", "rate": 0.92, "pitch": 0.9, "volume": 0.86},
            {"tone": "concentrado", "rate": 0.98, "pitch": 0.92, "volume": 0.9},
            {"tone": "alerta", "rate": 1.04, "pitch": 0.86, "volume": 0.94},
            {"tone": "intenso", "rate": 1.1, "pitch": 0.82, "volume": 1.0},
        ],
        "privacy": {
            "audio_storage": False,
            "raw_audio_sent_to_backend": False,
            "raw_audio_storage": False,
            "backend_audio_upload": False,
            "transcript_temporary_in_browser": True,
            "no_media_recorder": True,
            "no_get_user_media": True,
            "no_audio_context_capture": True,
            "no_continuous_recording": True,
            "wake_listening_without_recording_future": True,
            "no_continuous_transcription": True,
        },
        "approval_policy": {
            "approval_by_voice_enabled": False,
            "wake_phrase_approval": False,
            "wake_phrase_is_permission": False,
            "wake_phrase_can_execute": False,
            "critical_actions_require_non_voice_approval": True,
            "voice_can_prepare_preview_only": True,
        },
        "safety": {
            "manual_operator_activation_required": True,
            "stop_control_required": True,
            "no_always_listening": True,
            "no_persistent_wake_listener": True,
            "no_wake_listener_real": True,
            "no_hermes_dispatch": True,
            "no_tool_call": True,
            "no_auto_execute": True,
            "no_post_put_delete": True,
            "no_money": True,
            "no_deploy": True,
            "no_email": True,
            "no_credentials": True,
            "camera_activation_enabled": False,
        },
        "wake_listening_contract": {
            "persistent_wake_listener_real": False,
            "available_in_this_pr": False,
            "future_state_name": "wake_listening",
            "supported_phrases_future": ["Hola Jarvis", "Jarvis"],
            "no_audio_storage": True,
            "no_raw_audio_backend": True,
            "no_continuous_transcription": True,
            "activation_only": True,
            "can_execute": False,
            "can_approve": False,
        },
        "response_policy": {
            "local_controlled_response_only": True,
            "intent_classification_preview_only": True,
            "can_confirm_transcript": True,
            "can_request_confirmation": True,
            "cannot_execute_missions": True,
            "cannot_create_approvals": True,
            "cannot_approve_actions": True,
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "source_endpoints": ["/mark-3/dashboard/status"],
        "preview_only": True,
        "read_only": True,
    }


def _local_voice_loop_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Local Voice Loop declared",
            "source": "/mark-3/dashboard/status",
            "status": "browser_controlled_manual_only",
            "read_only": True,
        },
        {
            "event": "Manual continuous conversation declared",
            "source": "/mark-3/dashboard/status",
            "status": "manual_opt_in_until_stop_or_timeout",
            "read_only": True,
        },
        {
            "event": "Browser STT/TTS support is unknown until /jarvis loads",
            "source": "/mark-3/dashboard/status",
            "status": UNKNOWN,
            "read_only": True,
        },
        {
            "event": "Future wake_listening contract declared without real listener",
            "source": "/mark-3/dashboard/status",
            "status": "future_contract_only",
            "read_only": True,
        },
        {
            "event": "Raw audio backend upload disabled",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Voice approval disabled",
            "source": "/mark-3/dashboard/status",
            "status": "blocked",
            "read_only": True,
        },
    ]


def _visual_pilot_panel(name: str, source: str, status: str, notes: str) -> Dict[str, Any]:
    return {
        "name": name,
        "expected": True,
        "source": source,
        "status": status,
        "can_execute": False,
        "notes": notes,
    }


def _visual_pilot_check(name: str, status: str, evidence: str, notes: str) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


def _visual_pilot_step(order: int, check: str, notes: str) -> Dict[str, Any]:
    return {
        "order": order,
        "check": check,
        "notes": notes,
    }


def _visual_command_center_pilot_projection() -> Dict[str, Any]:
    return {
        "state": {
            "mode": "read_only_pilot",
            "dashboard_route": "/jarvis",
            "status_endpoint": "/mark-3/dashboard/status",
            "backend_read_model_connected": True,
            "frontend_execution_enabled": False,
            "approvals_real_enabled": False,
            "hermes_direct_execution_enabled": False,
            "voice_real_enabled": True,
            "browser_local_voice_loop_enabled": True,
            "camera_real_enabled": True,
            "raw_audio_recording_enabled": True,
            "vision_analysis_enabled": False,
            "mobile_runtime_enabled": False,
            "money_enabled": False,
            "deploy_enabled": False,
            "email_enabled": False,
            "credentials_enabled": False,
        },
        "required_panels": [
            _visual_pilot_panel(
                "Header",
                "system + jarvis_hermes_contract",
                "ready",
                "Shows local read-only mode and JARVIS/Hermes separation.",
            ),
            _visual_pilot_panel(
                "Presence UI",
                "local_system_contract.visual_contract",
                "preview",
                "Dominant central JARVIS core/orb is the primary experience.",
            ),
            _visual_pilot_panel(
                "Local System Contract",
                "local_system_contract",
                "ready",
                "Declares local daemon/runtime as the system and /jarvis as visual interface only.",
            ),
            _visual_pilot_panel(
                "Smart Bar",
                "local_voice_loop + local_system_contract.visual_contract.smart_bar",
                "preview",
                "Bottom smart bar shows temporary browser transcript and controlled local response.",
            ),
            _visual_pilot_panel(
                "Camera Preview",
                "local_system_contract.visual_contract.camera_placeholder",
                "preview",
                "Manual local camera preview; no backend stream, snapshot, storage or analysis.",
            ),
            _visual_pilot_panel(
                "Raw Audio Recorder",
                "raw_audio_recording",
                "preview",
                "Manual local raw audio recording with visible stop/download/delete; no backend upload.",
            ),
            _visual_pilot_panel(
                "Folded History",
                "local_system_contract.visual_contract.folded_history",
                "preview",
                "Conversation history is collapsed preview; no new persistence or runtime flow.",
            ),
            _visual_pilot_panel(
                "Voice Core",
                "voice_core + local_voice_loop",
                "preview",
                "Browser STT/TTS may run only after explicit operator activation; backend voice runtime remains disabled.",
            ),
            _visual_pilot_panel(
                "Local Voice Loop",
                "local_voice_loop",
                "preview",
                "Manual browser-controlled STT/TTS loop; no raw audio storage, backend upload or voice approval.",
            ),
            _visual_pilot_panel(
                "Wake Word Local Safe Flow",
                "wake_word_flow",
                "preview",
                "Typed preview only; wake phrases are not permissions and do not execute.",
            ),
            _visual_pilot_panel(
                "Mission Control",
                "mission_control",
                "preview",
                "Command intake is visual preview; no mission submit or Hermes dispatch.",
            ),
            _visual_pilot_panel(
                "Approval Console",
                "approvals",
                "preview",
                "Approval cards and buttons are visible but disabled/read-only.",
            ),
            _visual_pilot_panel(
                "Hermes Execution",
                "hermes_execution",
                "preview",
                "Execution visibility only; frontend cannot call Hermes directly.",
            ),
            _visual_pilot_panel(
                "Agent / Module Radar",
                "modules",
                "ready",
                "Normalized module states degrade to preview, disabled, not_connected or unknown.",
            ),
            _visual_pilot_panel(
                "Camera / Vision",
                "camera_vision",
                "disabled",
                "Camera, capture, storage and vision analysis are disabled.",
            ),
            _visual_pilot_panel(
                "Mobile Companion",
                "mobile_companion",
                "preview",
                "Mobile is a preview interface, not a runtime or approval channel.",
            ),
            _visual_pilot_panel(
                "Finance / ROI",
                "finance_roi",
                "unknown",
                "Metrics remain unknown unless measured evidence is connected.",
            ),
            _visual_pilot_panel(
                "Product Builder Adaptativo",
                "adaptive_product_builder",
                "preview",
                "Builder stages are preview/future-gated/disabled and cannot execute.",
            ),
            _visual_pilot_panel(
                "Frontend Pilot / Hardening",
                "frontend_pilot",
                "ready",
                "Frontend pilot declares GET-only status reading and no mutation paths.",
            ),
            _visual_pilot_panel(
                "Live Timeline / Audit",
                "timeline",
                "ready",
                "Read-only audit timeline contains status/read events, not execution claims.",
            ),
            _visual_pilot_panel(
                "Kill Switch",
                "system.kill_switch_state",
                "preview",
                "Visible disabled control; no active execution exists to stop in this pilot.",
            ),
        ],
        "read_only_checks": [
            _visual_pilot_check(
                "no_post_put_delete",
                "passed",
                "read_only_contract.allowed_http_methods_for_frontend=[GET]",
                "The dashboard may read the aggregate status endpoint only.",
            ),
            _visual_pilot_check(
                "no_execute_route",
                "passed",
                "read_only_contract.frontend_must_not_call_execute=true",
                "This read model adds no execute route and no execute affordance.",
            ),
            _visual_pilot_check(
                "no_frontend_hermes_call",
                "passed",
                "jarvis_hermes_contract.frontend_can_call_hermes_execute=false",
                "Hermes remains an execution engine behind JARVIS gates, not a frontend target.",
            ),
            _visual_pilot_check(
                "no_tool_runner",
                "passed",
                "safety.no_frontend_tool_runner=true",
                "No browser-side tool runner is represented by the dashboard read model.",
            ),
            _visual_pilot_check(
                "no_uncontrolled_sensor_activation",
                "passed",
                "safety.no_uncontrolled_sensor_activation=true",
                "Only explicit browser controls can request microphone, camera preview or raw audio recorder access; no background listener.",
            ),
            _visual_pilot_check(
                "manual_get_user_media_only",
                "passed",
                "safety.no_sensor_activation_on_load=true",
                "getUserMedia/MediaRecorder are available only inside explicit sensor hooks and never on load.",
            ),
            _visual_pilot_check(
                "manual_media_recorder_only",
                "passed",
                "raw_audio_recording.privacy.manual_opt_in_required=true",
                "Raw audio recording is a separate local browser tool with visible stop/delete/download controls.",
            ),
            _visual_pilot_check(
                "no_audio_context_capture",
                "passed",
                "voice_core.safety.no_audio_context_capture=true",
                "Audio capture is disabled and not represented as active.",
            ),
            _visual_pilot_check(
                "no_camera_capture",
                "passed",
                "camera_vision.privacy.no_snapshot_capture=true",
                "Camera preview is local only; snapshot capture, streaming and storage are disabled.",
            ),
            _visual_pilot_check(
                "no_mobile_runtime",
                "passed",
                "mobile_companion.state.mobile_runtime_enabled=false",
                "Mobile is an interface preview, not a runtime.",
            ),
            _visual_pilot_check(
                "no_money_movement",
                "passed",
                "finance_roi.safety.no_money_movement=true",
                "Finance/ROI is read-only and cannot move money.",
            ),
            _visual_pilot_check(
                "no_stripe_live",
                "passed",
                "finance_roi.safety.no_stripe_live=true",
                "Stripe live and checkout creation remain disabled.",
            ),
            _visual_pilot_check(
                "no_deploy",
                "passed",
                "adaptive_product_builder.safety.no_deploy=true",
                "Product Builder cannot deploy from this pilot.",
            ),
            _visual_pilot_check(
                "no_email_send",
                "passed",
                "safety.no_email_send=true",
                "No email sending path is exposed by the dashboard.",
            ),
            _visual_pilot_check(
                "no_credentials",
                "passed",
                "safety.no_credentials=true",
                "Credential and secret access remain outside the cockpit.",
            ),
            _visual_pilot_check(
                "no_fake_metrics",
                "passed",
                "finance_roi.truth_policy.no_fake_metrics=true",
                "Values without evidence stay unknown.",
            ),
        ],
        "operator_pilot_steps": [
            _visual_pilot_step(1, "arrancar backend", "Start the local backend before opening the dashboard."),
            _visual_pilot_step(2, "abrir /jarvis", "Open the local dashboard route in the web app."),
            _visual_pilot_step(3, "comprobar estado general", "Confirm mode and endpoint show read-only pilot status."),
            _visual_pilot_step(4, "comprobar panels", "Verify all required panels are visible."),
            _visual_pilot_step(5, "comprobar unknown/disabled", "Confirm unavailable evidence remains unknown, disabled, not_connected, preview or future_gated."),
            _visual_pilot_step(6, "comprobar stop/cancel de voz", "Voice may start only from the explicit microphone button and must expose a stop control."),
            _visual_pilot_step(7, "comprobar permisos acotados", "Only manual browser SpeechRecognition may request microphone access; camera, notifications and media capture remain disabled."),
            _visual_pilot_step(8, "comprobar que no hay ejecucion Hermes", "No frontend path may invoke Hermes execution."),
            _visual_pilot_step(9, "comprobar que finance/ROI no inventa datos", "Finance values without evidence must remain unknown."),
            _visual_pilot_step(10, "comprobar timeline read-only", "Timeline events must describe reads/checks only, not execution."),
        ],
        "pilot_findings": {
            "findings": [],
            "known_limitations": [
                "real approvals not wired",
                "mission submit is preview-only",
                "voice is browser-controlled/manual-only",
                "wake word is preview-only",
                "camera is disabled",
                "camera analysis remains disabled",
                "raw audio backend audit is metadata-only/local in this phase",
                "mobile is preview-only",
                "finance is unknown without evidence",
                "Product Builder is preview-only",
                "dependency hardening may need separate PR due npm audit vulnerabilities",
            ],
        },
        "safety": {
            "pilot_is_read_only": True,
            "dashboard_may_read_status_only": True,
            "no_side_effects": True,
            "no_real_world_actions": True,
            "no_background_workers": True,
            "no_uncontrolled_sensors": True,
            "no_money": True,
            "no_production": True,
            "no_credentials": True,
            "restrictions_are_approval_gates_not_permanent_bans": True,
        },
        "timeline": _visual_command_center_pilot_timeline_events(),
        "source_endpoint": "/mark-3/dashboard/status",
        "preview_only": True,
        "read_only": True,
    }


def _visual_command_center_pilot_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Visual Command Center pilot status read",
            "source": "/mark-3/dashboard/status",
            "status": "read_only_pilot",
            "read_only": True,
        },
        {
            "event": "Dashboard route checked",
            "source": "/jarvis",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "Dashboard read model checked",
            "source": "/mark-3/dashboard/status",
            "status": "passed",
            "read_only": True,
        },
        {
            "event": "Read-only safety checks loaded",
            "source": "/mark-3/dashboard/status",
            "status": "passed",
            "read_only": True,
        },
        {
            "event": "Presence UI panels loaded",
            "source": "/jarvis",
            "status": "preview",
            "read_only": True,
        },
        {
            "event": "No execution performed",
            "source": "/mark-3/dashboard/status",
            "status": "read_only",
            "read_only": True,
        },
    ]


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
            "frontend_can_activate_sensors": True,
            "frontend_can_move_money": False,
            "frontend_can_deploy": False,
            "frontend_can_send_email": False,
            "sensor_activation_scope": "explicit local voice, camera preview, local video recording and raw audio recording controls only",
        },
        "readiness_checks": [
            _frontend_readiness_check(
                "dashboard_route_exists",
                "preview",
                "frontend route expected at /jarvis",
                "Static frontend tests verify this shell route.",
            ),
            _frontend_readiness_check(
                "presence_ui_visible",
                "passed",
                "Presence UI central core",
                "The first viewport presents JARVIS as a living local presence, not an admin dashboard.",
            ),
            _frontend_readiness_check(
                "local_system_contract_visible",
                "passed",
                "local_system_contract projection present",
                "The dashboard declares the local daemon/runtime as the system and /jarvis as interface only.",
            ),
            _frontend_readiness_check(
                "smart_bar_visible",
                "passed",
                "smart bar local voice transcript/response",
                "The bottom bar shows temporary browser transcript and controlled local response without execution.",
            ),
            _frontend_readiness_check(
                "camera_placeholder_visible",
                "passed",
                "camera preview panel",
                "The camera panel can start a local browser preview only after explicit operator action.",
            ),
            _frontend_readiness_check(
                "folded_history_visible",
                "passed",
                "folded history",
                "History appears collapsed as preview and does not create persistence.",
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
                "Voice core can reflect manual browser STT/TTS loop states.",
            ),
            _frontend_readiness_check(
                "local_voice_loop_visible",
                "passed",
                "local_voice_loop projection present",
                "The read model declares browser-dependent support, audio privacy limits and no voice approval.",
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
                "no_uncontrolled_sensor_activation",
                "passed",
                "manual_browser_voice_activation_only=true",
                "Only explicit operator buttons may start browser SpeechRecognition, camera preview or local raw audio recording.",
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
            "browser voice support depends on SpeechRecognition/speechSynthesis",
            "browser camera preview is local-only and has no backend vision analysis",
            "browser raw audio recorder is local-only and has no backend upload",
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
            "mode": "browser_opt_in_preview_available",
            "camera_enabled": False,
            "camera_permission_requested": False,
            "preview_enabled": "manual_opt_in_available",
            "recording": False,
            "video_recording_available": "browser_local_opt_in",
            "video_recording_active": False,
            "video_recording_permission_requested": False,
            "video_recording_blob_ready": False,
            "raw_video_sent_to_backend": False,
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
            "no_camera_activation": False,
            "no_camera_activation_on_load": True,
            "manual_operator_activation_only": True,
            "no_get_user_media": False,
            "get_user_media_button_gated": True,
            "no_backend_media_stream": True,
            "no_recording": True,
            "video_recording_manual_opt_in_only": True,
            "video_recording_inactive_on_load": True,
            "video_recording_local_download_delete_only": True,
            "no_video_backend_upload": True,
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
                "camera_preview_available",
                "Preview local disponible",
                "El operador puede abrir preview local con botón explícito; no hay streaming, snapshot, storage ni análisis.",
                "preview",
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
        "video_recorder": {
            "mode": "browser_local_video_recorder",
            "available": "client_side_unknown_until_browser_loads",
            "activation": "explicit_operator_record_video_button",
            "recording_active": False,
            "permission_requested": False,
            "stop_control_required": True,
            "visible_indicator_required": True,
            "download_available_after_stop": True,
            "delete_available_after_stop": True,
            "delete_revokes_object_url": True,
            "backend_upload_enabled": False,
            "external_streaming_enabled": False,
            "external_vision_provider_called": False,
            "person_identity_analysis_enabled": False,
            "raw_video_sent_to_backend": False,
            "frames_stored": False,
            "sensor_ledger_metadata_only": True,
        },
        "timeline": _camera_vision_timeline_events(),
        "camera_state": "disabled" if camera_disabled else UNKNOWN,
        "preview_state": "manual_opt_in_available",
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
            "status": "browser_opt_in_preview_available",
            "read_only": True,
        },
        {
            "event": "Camera inactive by default",
            "source": "/camera-control/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Manual camera preview available",
            "source": "/jarvis/browser-camera",
            "status": "manual_opt_in_local_only",
            "read_only": True,
        },
        {
            "event": "Local video recorder surface declared",
            "source": "/jarvis/browser-camera",
            "status": "manual_opt_in_local_only",
            "read_only": True,
        },
        {
            "event": "Video recorder inactive by default",
            "source": "/jarvis/browser-camera",
            "status": "idle",
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


def _raw_audio_recording_projection() -> Dict[str, Any]:
    return {
        "state": {
            "mode": "browser_local_recorder",
            "available": "client_side_unknown_until_browser_loads",
            "recording_active": False,
            "activation": "explicit_operator_record_button",
            "stop_control_required": True,
            "download_available_after_stop": True,
            "delete_available_after_stop": True,
            "backend_upload_enabled": False,
            "external_streaming_enabled": False,
            "hidden_recording_enabled": False,
        },
        "retention": {
            "storage": "browser_memory_blob_until_download_or_delete",
            "default_retention": "operator_controlled_current_page_session",
            "auto_upload": False,
            "auto_persist": False,
            "delete_revokes_object_url": True,
            "operator_must_download_explicitly": True,
        },
        "audit": {
            "metadata_only": True,
            "events": [
                "recording_permission_requested",
                "recording_started",
                "recording_stopped",
                "recording_deleted",
            ],
            "raw_audio_in_audit": False,
            "backend_audit_complete": False,
            "backend_audit_gap": "browser-only recorder keeps metadata locally in this phase",
        },
        "privacy": {
            "manual_opt_in_required": True,
            "visible_indicator_required": True,
            "stop_control_required": True,
            "no_backend_upload": True,
            "no_provider_call": True,
            "no_transcription": True,
            "no_always_recording": True,
            "no_hidden_recording": True,
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "browser_source": "/jarvis/browser-audio-recorder",
        "preview_only": False,
        "read_only": True,
    }


def _raw_audio_recording_timeline_events() -> List[Dict[str, Any]]:
    return [
        {
            "event": "Raw audio recorder surface declared",
            "source": "/mark-3/dashboard/status",
            "status": "browser_local_recorder",
            "read_only": True,
        },
        {
            "event": "Raw audio backend upload disabled",
            "source": "/mark-3/dashboard/status",
            "status": "disabled",
            "read_only": True,
        },
        {
            "event": "Raw audio recording inactive by default",
            "source": "/jarvis/browser-audio-recorder",
            "status": "idle",
            "read_only": True,
        },
    ]


def _memory_brain_projection(
    *,
    memory_status: Dict[str, Any],
    learning_status: Dict[str, Any],
    personal_memory_status: Dict[str, Any],
    memory_brain_v2_status: Dict[str, Any] | None = None,
    memory_brain_v2_preview: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    outcome_count = _int(memory_status.get("outcome_count"), default=0) or 0
    failure_count = _int(memory_status.get("failure_count"), default=0) or 0
    proposal_count = _int(learning_status.get("proposal_count"), default=0) or 0
    v2_status = dict(memory_brain_v2_status or {})
    v2_preview = dict(memory_brain_v2_preview or {})
    v2_counts = dict(v2_status.get("counts", {}) or v2_preview.get("counts", {}) or {})
    explanation = dict(v2_preview.get("explanation_preview", {}) or {})
    return {
        "state": {
            "mode": "visible_read_only_brain",
            "memory_brain_v2_mode": v2_status.get("state", {}).get("mode", "in_memory_explainable_memory_brain_v2"),
            "outcome_memory_available": bool(memory_status.get("available", False)),
            "learning_proposals_available": bool(learning_status.get("available", False)),
            "personal_memory_control_available": bool(personal_memory_status.get("approved_memory_records_available", False)),
            "memory_brain_v2_available": bool(v2_status.get("state", {}).get("available", False)),
            "persistent": bool(v2_status.get("state", {}).get("persistent", False)),
            "storage_configured": bool(v2_status.get("state", {}).get("storage_configured", False)),
            "storage_path": v2_status.get("state", {}).get("storage_path", ".jarvis/memory_brain_v2/memory_brain_v2.sqlite3"),
            "in_memory_only": not bool(v2_status.get("state", {}).get("persistent", False)),
            "compaction_available": False,
            "forget_delete_available": "future_gated",
            "memory_brain_v2_store_forget_delete_available": "python_store_audited",
            "memory_autoload_enabled": False,
            "memory_grants_permission": False,
        },
        "entities": list(v2_preview.get("entities", [])),
        "facts": list(v2_preview.get("facts", [])),
        "preferences": list(v2_preview.get("preferences", [])),
        "decisions": list(v2_preview.get("decisions", [])),
        "projects": list(v2_preview.get("projects", [])),
        "contradictions": list(v2_preview.get("contradictions", [])),
        "active_memories": list(v2_preview.get("active_memories", [])),
        "pending_review": list(v2_preview.get("pending_review", [])),
        "forgotten_deleted": list(v2_preview.get("forgotten_deleted", [])),
        "counts": {
            "outcomes": outcome_count,
            "failures": failure_count,
            "learning_proposals": proposal_count,
            "audit_events": (_int(memory_status.get("audit_event_count"), default=0) or 0)
            + (_int(learning_status.get("audit_event_count"), default=0) or 0)
            + (_int(v2_counts.get("audit_events"), default=0) or 0),
            "entities": _int(v2_counts.get("entities"), default=0) or 0,
            "facts": _int(v2_counts.get("facts"), default=0) or 0,
            "preferences": _int(v2_counts.get("preferences"), default=0) or 0,
            "decisions": _int(v2_counts.get("decisions"), default=0) or 0,
            "projects": _int(v2_counts.get("projects"), default=0) or 0,
            "contradictions": _int(v2_counts.get("contradictions"), default=0) or 0,
            "active_memories": _int(v2_counts.get("active_memories"), default=0) or 0,
            "pending_review": _int(v2_counts.get("pending_review"), default=0) or 0,
            "forgotten_deleted": _int(v2_counts.get("forgotten_deleted"), default=0) or 0,
        },
        "why_jarvis_remembers": list(explanation.get("why_jarvis_remembers", []))[:5]
        or [
            "JARVIS muestra outcome/failure memory, learning proposals y Memory Brain v2 para explicar aprendizaje operativo.",
            "Si no hay evidencia, los campos quedan en unknown.",
            "La memoria nunca concede permisos ni autoriza ejecución.",
        ],
        "explanation_preview": {
            "why_jarvis_remembers": list(explanation.get("why_jarvis_remembers", []))[:5],
            "what_memory_influenced": list(explanation.get("what_memory_influenced", []))[:5],
            "pending_approval": list(explanation.get("pending_approval", []))[:5],
        },
        "compaction": {
            "status": "contract_only",
            "available_now": False,
            "requires_policy": True,
            "must_explain_source_records": True,
            "must_preserve_contradictions": True,
        },
        "forget_delete": {
            "status": "future_gated",
            "memory_brain_v2_store_status": "audited_python_store",
            "available_now": True,
            "requires_operator_review": True,
            "audit_required": True,
        },
        "safety": {
            "sensitive_memory_requires_approval": True,
            "private_or_sensitive_persistent_memory_requires_strong_approval": True,
            "no_sensitive_autosave": True,
            "no_external_persistence": True,
            "memory_is_not_permission": True,
            "active_memory_does_not_authorize_sensitive_actions": True,
            "memory_brain_v2_autoload_enabled": False,
            "memory_brain_v2_external_persistence_enabled": False,
            "execution_enabled": False,
            "side_effects_enabled": False,
        },
        "source_endpoints": [
            "/mark-3/outcomes",
            "/mark-3/learning/proposals",
            "/personal-memory/status",
            "/mark-3/memory-brain/status",
            "/mark-3/memory-brain/preview",
        ],
        "source_status": {
            "outcome_memory": _status_summary(memory_status),
            "learning_proposals": _status_summary(learning_status),
            "personal_memory": _status_summary(personal_memory_status),
            "memory_brain_v2": _status_summary(v2_status),
        },
        "preview_only": False,
        "read_only": True,
    }


def _memory_brain_timeline_events(memory_brain: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "event": "Memory brain read model generated",
            "source": "/mark-3/outcomes + /mark-3/learning/proposals + /personal-memory/status",
            "status": "visible_read_only_brain",
            "read_only": True,
        },
        {
            "event": "Memory Brain v2 read model generated",
            "source": "/mark-3/memory-brain/status",
            "status": str(memory_brain.get("state", {}).get("memory_brain_v2_mode", "in_memory_explainable_memory_brain_v2")),
            "read_only": True,
        },
        {
            "event": "Memory Brain v2 counts read",
            "source": "/mark-3/memory-brain/preview",
            "status": str(memory_brain.get("counts", {}).get("active_memories", UNKNOWN)),
            "read_only": True,
        },
        {
            "event": "Outcome and learning memory counts read",
            "source": "/mark-3/outcomes + /mark-3/learning/proposals",
            "status": str(memory_brain.get("counts", {}).get("outcomes", UNKNOWN)),
            "read_only": True,
        },
        {
            "event": "Memory cannot authorize execution",
            "source": "/personal-memory/status",
            "status": "blocked",
            "read_only": True,
        },
    ]


def _persistent_audit_timeline_events(persistent_audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    chain = dict(persistent_audit.get("chain", {}) or {})
    return [
        {
            "event": "Persistent Audit status read",
            "source": "/mark-3/audit/status",
            "status": persistent_audit.get("state", {}).get("mode", "metadata_audit_ledger"),
            "read_only": True,
        },
        {
            "event": "Persistent Audit hash-chain verified",
            "source": "/mark-3/audit/status",
            "status": "valid" if chain.get("valid", True) else "tamper_detected",
            "read_only": True,
        },
        {
            "event": "Persistent Audit stores metadata only",
            "source": "/mark-3/audit/status",
            "status": "metadata_only",
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
            "provider_adapter": wake_listener.get("provider_adapter", "openWakeWord"),
            "provider_adapter_ready": bool(wake_listener.get("provider_adapter_ready", False)),
            "openwakeword_dependency_installed": bool(wake_listener.get("openwakeword_dependency_installed", False)),
            "auto_start_enabled": False,
            "activation_endpoint_enabled": False,
            "implementation_status": wake_listener.get("implementation_status", "adapter_contract_only"),
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
        "adapter_contract": {
            "provider": wake_listener.get("provider_adapter", "openWakeWord"),
            "dependency_installed": bool(wake_listener.get("openwakeword_dependency_installed", False)),
            "auto_start_enabled": False,
            "activation_endpoint_enabled": False,
            "requires_operator_start": True,
            "status": wake_listener.get("implementation_status", "adapter_contract_only"),
            "test_plan": _list(wake_listener.get("test_plan")),
        },
        "ephemeral_buffer_contract": wake_listener.get(
            "ephemeral_buffer_contract",
            {
                "in_memory_only": True,
                "persisted": False,
                "sent_to_backend": False,
                "transcribed_before_valid_activation": False,
                "cleared_after_activation_or_timeout": True,
                "no_audio_retention": True,
            },
        ),
        "safety": {
            "no_microphone_activation": True,
            "no_get_user_media": True,
            "no_media_recorder": True,
            "no_audio_context_capture": True,
            "no_background_listening": True,
            "no_raw_audio_storage": True,
            "no_audio_persistence": True,
            "no_transcription_until_valid_activation": True,
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
            "provider_adapter": "openWakeWord",
            "provider_adapter_ready": bool(wake_listener.get("provider_adapter_ready", False)),
            "openwakeword_dependency_installed": bool(wake_listener.get("openwakeword_dependency_installed", False)),
            "auto_start_enabled": False,
            "activation_endpoint_enabled": False,
            "implementation_status": "adapter_contract_only",
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


def _voice_runtime_pack_timeline_events(voice_runtime_pack: Dict[str, Any]) -> List[Dict[str, Any]]:
    provider_statuses = [
        item.get("status", UNKNOWN)
        for item in list(voice_runtime_pack.get("local_stt_provider_status", {}).values())
        + list(voice_runtime_pack.get("local_tts_provider_status", {}).values())
        if isinstance(item, dict)
    ]
    status_summary = "disabled_or_missing" if provider_statuses and all(status in {"missing", "disabled_by_default"} for status in provider_statuses) else UNKNOWN
    return [
        {
            "event": "Voice Runtime Pack status read",
            "source": "/mark-3/voice-runtime/status",
            "status": voice_runtime_pack.get("current_state", "idle"),
            "read_only": True,
        },
        {
            "event": "Browser STT/TTS declared client-side",
            "source": "/mark-3/voice-runtime/status",
            "status": "client_side_unknown",
            "read_only": True,
        },
        {
            "event": "Local STT/TTS providers remain disabled or missing",
            "source": "/mark-3/voice-runtime/status",
            "status": status_summary,
            "read_only": True,
        },
        {
            "event": "Voice runtime safety gates confirmed",
            "source": "/mark-3/voice-runtime/status",
            "status": "no_raw_audio_no_transcript_persistence_no_hermes_dispatch",
            "read_only": True,
        },
    ]


def _conversational_brain_timeline_events(conversational_brain: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "event": "Conversational Brain Bridge v2 read",
            "source": "/mark-3/conversational-brain/status",
            "status": conversational_brain.get("state", {}).get("mode", "local_deterministic_bridge"),
            "read_only": True,
        },
        {
            "event": "Conversational brain LLM disabled",
            "source": "/mark-3/conversational-brain/status",
            "status": "no_llm_no_external_api",
            "read_only": True,
        },
        {
            "event": "Conversational brain Hermes dispatch disabled",
            "source": "/mark-3/conversational-brain/status",
            "status": "disabled",
            "read_only": True,
        },
    ]


def _conversational_intake_timeline_events(conversational_intake: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "event": "Conversational Intake status read",
            "source": "/mark-3/conversational-intake/status",
            "status": conversational_intake.get("state", {}).get("mode", "prepare_only_conversational_intake"),
            "read_only": True,
        },
        {
            "event": "Conversational Intake Hermes dispatch disabled",
            "source": "/mark-3/conversational-intake/status",
            "status": "safe_to_dispatch_to_hermes_false",
            "read_only": True,
        },
        {
            "event": "Conversational Intake credential material gate active",
            "source": "/mark-3/conversational-intake/status",
            "status": "credential_material_blocked",
            "read_only": True,
        },
    ]


def _brain_adapter_timeline_events(brain_adapter: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "event": "LLM Brain Adapter status read",
            "source": "/mark-3/brain-adapter/status",
            "status": brain_adapter.get("state", {}).get("mode", "safe_brain_adapter_prepare_only"),
            "read_only": True,
        },
        {
            "event": "Brain default provider deterministic_local",
            "source": "/mark-3/brain-adapter/status",
            "status": brain_adapter.get("state", {}).get("default_provider", "deterministic_local"),
            "read_only": True,
        },
        {
            "event": "External LLM provider disabled",
            "source": "/mark-3/brain-adapter/status",
            "status": "external_provider_called_false",
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
