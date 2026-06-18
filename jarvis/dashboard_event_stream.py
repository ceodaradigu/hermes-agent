from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List
from uuid import NAMESPACE_URL, uuid5


EVENT_STREAM_SCHEMA_VERSION = "jarvis.dashboard.events.v1"

ALLOWED_EVENT_TYPES = (
    "intake_state",
    "brain_adapter_state",
    "brain_state",
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
    "remote_state",
    "doctor_state",
    "performance_state",
    "sensor_ledger_state",
    "policy_state",
    "heartbeat",
)


def build_jarvis_event_snapshot(*, dashboard_status: Dict[str, Any], generated_at: str) -> Dict[str, Any]:
    """Return a secret-free, read-only event projection for the JARVIS presence UI.

    The stream intentionally contains state metadata only. It never includes raw
    audio, camera frames, credentials, provider payloads, or execution commands.
    """

    events = [
        _event(
            generated_at,
            "intake_state",
            "/mark-3/conversational-intake/status",
            _get(dashboard_status, "conversational_intake.state.mode", "prepare_only_conversational_intake"),
            {
                "schema_version": _get(dashboard_status, "conversational_intake.schema_version", "jarvis.conversational_intake.v1"),
                "source": _get(dashboard_status, "conversational_intake.sample.intake.source", "typed_text"),
                "language": _get(dashboard_status, "conversational_intake.sample.intake.language", "unknown"),
                "wake_phrase_detected": _bool(_get(dashboard_status, "conversational_intake.sample.intake.wake_phrase_detected", False)),
                "contains_sensitive_request": _bool(_get(dashboard_status, "conversational_intake.sample.intake.contains_sensitive_request", False)),
                "requires_clarification": _bool(_get(dashboard_status, "conversational_intake.sample.intake.requires_clarification", False)),
                "safe_to_classify": _bool(_get(dashboard_status, "conversational_intake.sample.intake.safe_to_classify", False)),
                "safe_to_prepare_preview": _bool(_get(dashboard_status, "conversational_intake.sample.intake.safe_to_prepare_preview", False)),
                "safe_to_dispatch_to_hermes": False,
                "classified_intent": _get(dashboard_status, "conversational_intake.sample.classification.intent_detected", "unknown"),
                "classified_risk": _get(dashboard_status, "conversational_intake.sample.classification.risk_level", "unknown"),
                "next_safe_action": _get(dashboard_status, "conversational_intake.sample.classification.next_safe_action", "unknown"),
                "hermes_dispatch_allowed": False,
                "external_provider_called": False,
                "raw_text_omitted": True,
            },
        ),
        _event(
            generated_at,
            "brain_adapter_state",
            "/mark-3/brain-adapter/status",
            _get(dashboard_status, "brain_adapter.state.mode", "safe_brain_adapter_prepare_only"),
            {
                "schema_version": _get(dashboard_status, "brain_adapter.schema_version", "jarvis.llm_brain_adapter.v1"),
                "default_provider": _get(dashboard_status, "brain_adapter.state.default_provider", "deterministic_local"),
                "current_provider": _get(dashboard_status, "brain_adapter.state.current_provider", "deterministic_local"),
                "provider_mode": _get(dashboard_status, "brain_adapter.providers.deterministic_local.provider_mode", "local_deterministic_prepare_only"),
                "external_llm_enabled": False,
                "external_provider_called": False,
                "provider_configuration_required": False,
                "provider_configuration_loaded": False,
                "reads_env": False,
                "network_allowed": False,
                "hermes_dispatch_allowed": False,
                "sample_intent": _get(dashboard_status, "brain_adapter.sample.brain_response.intent_detected", "unknown"),
                "sample_risk_level": _get(dashboard_status, "brain_adapter.sample.brain_response.risk_level", "unknown"),
                "sample_next_action": _get(dashboard_status, "brain_adapter.sample.brain_response.suggested_next_action", "unknown"),
                "disabled_external_provider": _get(dashboard_status, "brain_adapter.providers.disabled_external_llm.honest_status", "disabled_by_default_not_configured_not_called"),
            },
        ),
        _event(
            generated_at,
            "brain_state",
            "/mark-3/conversational-brain/status",
            _get(dashboard_status, "conversational_brain.state.mode", "local_deterministic_bridge"),
            {
                "schema_version": _get(dashboard_status, "conversational_brain.schema_version", "jarvis.conversational_brain_bridge.v2"),
                "llm_called": False,
                "external_provider_called": False,
                "memory_write": False,
                "transcript_persistence": False,
                "hermes_dispatch_allowed": False,
                "sample_intent": _get(dashboard_status, "conversational_brain.sample_analysis.intent_detected", "unknown"),
                "sample_risk_level": _get(dashboard_status, "conversational_brain.sample_analysis.risk_level", "unknown"),
                "sample_approval_level": _get(dashboard_status, "conversational_brain.sample_analysis.approval_level", "unknown"),
                "requires_approval": _bool(_get(dashboard_status, "conversational_brain.sample_analysis.requires_approval", False)),
                "can_prepare_preview": _bool(_get(dashboard_status, "conversational_brain.sample_analysis.can_prepare_preview", False)),
            },
        ),
        _event(
            generated_at,
            "voice_state",
            "/voice-runtime/status",
            _get(dashboard_status, "voice_core.state.current_state", "preview"),
            {
                "mode": _get(dashboard_status, "voice_core.state.mode", "preview"),
                "microphone_enabled": _bool(_get(dashboard_status, "voice_core.state.microphone_enabled", False)),
                "command_listening_enabled": _bool(_get(dashboard_status, "voice_core.state.command_listening_enabled", False)),
                "voice_approval_enabled": False,
                "manual_browser_voice_only": True,
            },
        ),
        _event(
            generated_at,
            "voice_session_state",
            "/voice-runtime/session-status",
            _get(dashboard_status, "voice_session.state.current_state", "idle"),
            {
                "schema_version": _get(dashboard_status, "voice_session.schema_version", "jarvis.voice_session_manager.v1"),
                "current_state": _get(dashboard_status, "voice_session.state.current_state", "idle"),
                "wake_listening_state": _get(dashboard_status, "voice_session.state.wake_listening_state", "wake_listening_disabled"),
                "conversation_active": _bool(_get(dashboard_status, "voice_session.state.conversation_active", False)),
                "manual_push_to_talk_active": _bool(_get(dashboard_status, "voice_session.state.manual_push_to_talk_active", False)),
                "raw_audio_sent_to_backend": False,
                "transcript_persistence": False,
                "background_transcription": False,
                "always_on_stt": False,
                "microphone_auto_start": False,
                "voice_approval_enabled": False,
                "hermes_dispatch_allowed": False,
            },
        ),
        _event(
            generated_at,
            "wake_state",
            "/mark-2/wake-listener/status",
            _get(dashboard_status, "wake_word_flow.state.mode", "preview"),
            {
                "wake_runtime_enabled": _bool(_get(dashboard_status, "wake_word_flow.state.wake_runtime_enabled", False)),
                "supported_phrases": _get(dashboard_status, "wake_word_flow.supported_phrases", ["Hola Jarvis", "Jarvis"]),
                "provider_adapter": _get(dashboard_status, "wake_word_flow.state.provider_adapter", "openWakeWord"),
                "provider_adapter_ready": _bool(_get(dashboard_status, "wake_word_flow.state.provider_adapter_ready", False)),
                "openwakeword_dependency_installed": _bool(_get(dashboard_status, "wake_word_flow.state.openwakeword_dependency_installed", False)),
                "auto_start_enabled": False,
                "activation_endpoint_enabled": False,
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "records_audio": False,
                "transcribes_environment": False,
            },
        ),
        _event(
            generated_at,
            "tts_state",
            "/voice-runtime/status",
            _get(dashboard_status, "voice_core.tts_state.status", "preview"),
            {
                "speaking": _bool(_get(dashboard_status, "voice_core.tts_state.speaking", False)),
                "provider": _get(dashboard_status, "voice_core.tts_state.provider", "none/not_connected"),
                "external_call": False,
                "voice_style_contract": "masculina/elegante/premium/calmada future provider; browser fallback now",
            },
        ),
        _event(
            generated_at,
            "hermes_state",
            "/mark-3/hermes-runtime/status",
            _get(dashboard_status, "hermes_execution.execution_mode", "read_only_visibility"),
            {
                "available": _get(dashboard_status, "hermes_execution.available", "unknown"),
                "active_execution": _bool(_get(dashboard_status, "hermes_execution.active_execution", False)),
                "running_sessions": _get(dashboard_status, "hermes_execution.running_sessions", "unknown"),
                "session_count": _get(dashboard_status, "hermes_execution.session_count", "unknown"),
                "supported_tool": _get(dashboard_status, "hermes_execution.supported_tool", "unknown"),
                "supported_action_type": _get(dashboard_status, "hermes_execution.runtime_status.supported_action_type", "unknown"),
                "frontend_direct_execution_allowed": False,
                "jarvis_governs": True,
                "hermes_executes": True,
            },
        ),
        _event(
            generated_at,
            "approval_state",
            "/approvals/status",
            _get(dashboard_status, "approvals.cards_state", "preview/read-only"),
            {
                "pending_count": _get(dashboard_status, "approvals.pending_count", "unknown"),
                "critical_count": _get(dashboard_status, "approvals.critical_count", "unknown"),
                "action_buttons_enabled": False,
                "wake_phrase_can_approve": False,
                "voice_approval_requires_auth_gate_and_audit": True,
            },
        ),
        _event(
            generated_at,
            "mission_state",
            "/mark-3/dashboard/status",
            _get(dashboard_status, "mission_control.state.mode", "preview"),
            {
                "input_enabled": _get(dashboard_status, "mission_control.state.input_enabled", "preview_only"),
                "execution_enabled": False,
                "hermes_dispatch_enabled": False,
                "approval_creation_enabled": False,
                "sample_request_omitted_from_stream": True,
            },
        ),
        _event(
            generated_at,
            "camera_state",
            "/camera-control/status",
            _get(dashboard_status, "camera_vision.state.mode", "browser_opt_in_preview_available"),
            {
                "camera_enabled": _bool(_get(dashboard_status, "camera_vision.state.camera_enabled", False)),
                "permission_requested": _bool(_get(dashboard_status, "camera_vision.state.camera_permission_requested", False)),
                "preview_enabled": _get(dashboard_status, "camera_vision.state.preview_enabled", "manual_opt_in_available"),
                "recording": _bool(_get(dashboard_status, "camera_vision.state.recording", False)),
                "video_recording_available": _get(dashboard_status, "camera_vision.state.video_recording_available", "browser_local_opt_in"),
                "video_recording_active": _bool(_get(dashboard_status, "camera_vision.state.video_recording_active", False)),
                "video_recording_permission_requested": _bool(_get(dashboard_status, "camera_vision.state.video_recording_permission_requested", False)),
                "video_recording_blob_ready": _bool(_get(dashboard_status, "camera_vision.state.video_recording_blob_ready", False)),
                "video_download_available_after_stop": _bool(_get(dashboard_status, "camera_vision.video_recorder.download_available_after_stop", True)),
                "video_delete_available_after_stop": _bool(_get(dashboard_status, "camera_vision.video_recorder.delete_available_after_stop", True)),
                "raw_video_sent_to_backend": False,
                "streaming": _bool(_get(dashboard_status, "camera_vision.state.streaming", False)),
                "analysis_enabled": _bool(_get(dashboard_status, "camera_vision.state.vision_analysis_enabled", False)),
                "visible_indicator_required": True,
                "people_analysis_default": False,
                "no_backend_stream": True,
                "no_backend_upload": True,
                "no_snapshot_storage": True,
            },
        ),
        _event(
            generated_at,
            "recording_state",
            "/jarvis/browser-audio-recorder",
            _get(dashboard_status, "raw_audio_recording.state.mode", "browser_local_recorder"),
            {
                "raw_audio_recording_enabled": True,
                "opt_in_required": True,
                "recording_active": _bool(_get(dashboard_status, "raw_audio_recording.state.recording_active", False)),
                "retention_policy": _get(dashboard_status, "raw_audio_recording.retention.storage", "browser_memory_blob_until_download_or_delete"),
                "delete_supported_contract": _bool(_get(dashboard_status, "raw_audio_recording.state.delete_available_after_stop", True)),
                "raw_audio_sent_to_backend": False,
                "hidden_recording_enabled": False,
            },
        ),
        _event(
            generated_at,
            "memory_state",
            "/mark-3/outcomes + /mark-3/learning/proposals + /personal-memory/status",
            _get(dashboard_status, "memory_brain.state.mode", "visible_read_only_brain"),
            {
                "visible_brain": True,
                "entity_count": len(_get(dashboard_status, "memory_brain.entities", [])),
                "decision_count": len(_get(dashboard_status, "memory_brain.decisions", [])),
                "preference_count": len(_get(dashboard_status, "memory_brain.preferences", [])),
                "contradiction_count": len(_get(dashboard_status, "memory_brain.contradictions", [])),
                "outcome_count": _get(dashboard_status, "memory_brain.counts.outcomes", 0),
                "learning_proposal_count": _get(dashboard_status, "memory_brain.counts.learning_proposals", 0),
                "compaction": _get(dashboard_status, "memory_brain.compaction.status", "contract_only"),
                "forget_delete": _get(dashboard_status, "memory_brain.forget_delete.status", "future_gated"),
                "memory_never_grants_permission": True,
            },
        ),
        _event(
            generated_at,
            "risk_state",
            "/mark-3/dashboard/status",
            _get(dashboard_status, "mission_control.intent_preview.risk_level", "preview"),
            {
                "approval_level": _get(dashboard_status, "mission_control.intent_preview.approval_level", "unknown"),
                "wake_phrase_is_permission": False,
                "critical_actions_require_readback": True,
                "money_deploy_email_credentials_blocked_from_frontend": True,
            },
        ),
        _event(
            generated_at,
            "execution_state",
            "/mark-3/dashboard/status",
            "gated",
            {
                "preview_required": True,
                "approval_required": True,
                "hermes_dispatch_after_approval_only": True,
                "rollback_or_stop_plan_required": True,
                "frontend_direct_execution_allowed": False,
                "direct_execute_route_exposed": False,
            },
        ),
        _event(
            generated_at,
            "remote_state",
            "/mobile/companion/status",
            _get(dashboard_status, "mobile_companion.state.mode", "preview"),
            {
                "pairing_required": True,
                "revocation_required": True,
                "remote_kill_switch": "future_gated",
                "telegram_is_governed_channel": True,
                "telegram_is_not_bypass": True,
                "mobile_can_call_hermes_directly": False,
            },
        ),
        _event(
            generated_at,
            "doctor_state",
            "/mark-3/local-doctor/status",
            _get(dashboard_status, "local_doctor.state.mode", "read_only_local_doctor"),
            {
                "backend_reachable": _bool(_get(dashboard_status, "local_doctor.state.backend_reachable", False)),
                "event_stream_endpoint": _bool(_get(dashboard_status, "local_doctor.state.event_stream_endpoint", False)),
                "hermes_status_endpoint": _bool(_get(dashboard_status, "local_doctor.state.hermes_status_endpoint", False)),
                "browser_stt": _get(dashboard_status, "local_doctor.state.browser_stt", "client_side_unknown"),
                "browser_tts": _get(dashboard_status, "local_doctor.state.browser_tts", "client_side_unknown"),
                "camera_support": _get(dashboard_status, "local_doctor.state.camera_support", "client_side_unknown"),
                "webgl_support": _get(dashboard_status, "local_doctor.state.webgl_support", "client_side_unknown"),
                "ffmpeg_available": _get(dashboard_status, "local_doctor.optional_dependencies.ffmpeg.available", False),
                "openwakeword_available": _get(dashboard_status, "local_doctor.optional_dependencies.openwakeword.available", False),
                "no_dependency_install_from_frontend": True,
            },
        ),
        _event(
            generated_at,
            "performance_state",
            "/jarvis",
            "client_budgeted",
            {
                "webgl_fallback": True,
                "fps_budget": "60 active / reduced in power save",
                "power_save": True,
                "ui_thread_blocking_expected": False,
                "no_webgl_sensor_dependency": True,
            },
        ),
        _event(
            generated_at,
            "sensor_ledger_state",
            "/mark-3/dashboard/status",
            _get(dashboard_status, "sensor_ledger.state.mode", "read_only_sensor_metadata_ledger"),
            {
                "schema_version": _get(dashboard_status, "sensor_ledger.schema_version", "jarvis.sensor_ledger.v1"),
                "supported_sensors": _get(dashboard_status, "sensor_ledger.state.supported_sensors", []),
                "supported_events": _get(dashboard_status, "sensor_ledger.state.supported_events", []),
                "event_count": _get(dashboard_status, "sensor_ledger.state.event_count", 0),
                "metadata_only": _bool(_get(dashboard_status, "sensor_ledger.safety.metadata_only", True)),
                "read_only_from_jarvis": True,
                "no_raw_audio": True,
                "no_camera_frames": True,
                "no_credential_material": True,
                "sensors_require_opt_in": True,
                "visible_indicator_required": True,
                "stop_cancel_required": True,
            },
        ),
        _event(
            generated_at,
            "policy_state",
            "/mark-3/dashboard/status",
            _get(dashboard_status, "policy_status.state.mode", "read_only_policy_status"),
            {
                "schema_version": _get(dashboard_status, "policy_status.schema_version", "jarvis.policy_status.v1"),
                "jarvis_governs": True,
                "hermes_executes": True,
                "frontend_never_executes_hermes_directly": True,
                "wake_phrase_never_approves": True,
                "sensors_require_opt_in": True,
                "dangerous_execution_requires_approval_gateway": True,
                "risk_classification_required": True,
                "audit_required": True,
                "rollback_or_stop_plan_required": True,
                "direct_allowed_count": len(_get(dashboard_status, "policy_status.direct_allowed", [])),
                "denied_count": len(_get(dashboard_status, "policy_status.denied", [])),
            },
        ),
        _event(
            generated_at,
            "audit_event",
            "/mark-3/dashboard/status",
            "read_only",
            {
                "audit_surfaces": [
                    "sensors",
                    "voice",
                    "camera",
                    "wake",
                    "recording",
                    "memory",
                    "execution",
                    "remote",
                ],
                "recent_read_model_events": _timeline_events(dashboard_status.get("timeline", [])),
                "secrets_logged": False,
                "raw_audio_logged": False,
                "camera_frames_logged": False,
            },
        ),
    ]
    heartbeat = _heartbeat_event(generated_at)

    return {
        "schema_version": EVENT_STREAM_SCHEMA_VERSION,
        "snapshot_id": _stable_event_id(generated_at, "snapshot", "/mark-3/dashboard/events", {"events": len(events)}),
        "generated_at": generated_at,
        "created_at": generated_at,
        "stream": {
            "endpoint": "/mark-3/dashboard/events",
            "sse_endpoint": "/mark-3/dashboard/events/stream",
            "mode": "read_only_event_projection",
            "schema_version": EVENT_STREAM_SCHEMA_VERSION,
            "read_only": True,
            "allowed_methods": ["GET"],
            "allowed_event_types": list(ALLOWED_EVENT_TYPES),
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
            "no_frontend_execution": True,
            "stream_can_execute": False,
            "no_post_put_delete": True,
        },
        "heartbeat": heartbeat,
        "events": events,
    }


def encode_sse_event(event_name: str, payload: Dict[str, Any]) -> str:
    event_id = payload.get("event_id") or payload.get("snapshot_id") or event_name
    return f"event: {event_name}\nid: {event_id}\ndata: {json.dumps(payload, ensure_ascii=True, sort_keys=True)}\n\n"


def _event(
    generated_at: str,
    event_type: str,
    source: str,
    status: Any,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Unsupported JARVIS event type: {event_type}")
    safe_payload = _sanitize_payload(payload)
    event_id = _stable_event_id(generated_at, event_type, source, safe_payload)
    risk_level = _risk_level_for_event(event_type)
    return {
        "schema_version": EVENT_STREAM_SCHEMA_VERSION,
        "event_id": event_id,
        "id": event_id,
        "event_type": event_type,
        "type": event_type,
        "created_at": generated_at,
        "timestamp": generated_at,
        "source": source,
        "status": _safe_scalar(status),
        "risk_level": risk_level,
        "read_only": True,
        "can_execute": False,
        "stream_can_execute": False,
        "secret_free": True,
        "raw_audio_included": False,
        "camera_frames_included": False,
        "payload": safe_payload,
    }


def _heartbeat_event(generated_at: str) -> Dict[str, Any]:
    return _event(
        generated_at,
        "heartbeat",
        "/mark-3/dashboard/events/stream",
        "alive",
        {
            "stream_alive": True,
            "disconnect_safe": True,
            "read_only": True,
            "can_execute": False,
            "no_secrets": True,
            "no_raw_audio": True,
            "no_camera_frames": True,
        },
    )


def _get(data: Dict[str, Any], dotted_path: str, default: Any = "unknown") -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def _bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _safe_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str) and value.strip():
        return value[:240]
    return "unknown"


def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if any(blocked in lowered for blocked in ("secret", "token", "credential", "cookie", "password", "audio_bytes", "raw_audio_bytes", "frame_bytes", "image_bytes", "video_bytes")):
            sanitized[key] = "redacted"
            continue
        sanitized[key] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _sanitize_payload(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:20]]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value[:20]]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value[:500]
    return str(value)[:240]


def _timeline_events(timeline: Iterable[Any]) -> List[str]:
    events: List[str] = []
    for item in timeline:
        if isinstance(item, dict):
            events.append(_safe_scalar(item.get("event", "unknown")))
        if len(events) >= 8:
            break
    return events


def _stable_event_id(generated_at: str, event_type: str, source: str, payload: Dict[str, Any]) -> str:
    fingerprint = json.dumps(
        {
            "generated_at": generated_at,
            "event_type": event_type,
            "source": source,
            "payload": payload,
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return f"evt_{uuid5(NAMESPACE_URL, fingerprint)}"


def _risk_level_for_event(event_type: str) -> str:
    if event_type in {"intake_state", "brain_adapter_state"}:
        return "intent_risk_preview"
    if event_type in {"camera_state", "recording_state", "voice_state", "voice_session_state", "wake_state", "tts_state", "sensor_ledger_state"}:
        return "sensor_privacy"
    if event_type == "brain_state":
        return "intent_risk_preview"
    if event_type in {"approval_state", "risk_state", "execution_state", "policy_state"}:
        return "approval_gate"
    if event_type == "remote_state":
        return "remote_surface"
    if event_type == "memory_state":
        return "memory_privacy"
    return "low"
