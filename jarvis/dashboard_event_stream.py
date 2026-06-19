from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List
from uuid import NAMESPACE_URL, uuid5


EVENT_STREAM_SCHEMA_VERSION = "jarvis.dashboard.events.v1"

ALLOWED_EVENT_TYPES = (
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
    "phase_1_state",
    "phase_2_state",
    "phase_3_state",
    "phase_4_state",
    "daemon_state",
    "local_controller_state",
    "trusted_channels_state",
    "trusted_devices_state",
    "remote_pairing_state",
    "telegram_bridge_state",
    "stop_rollback_v2_state",
    "action_catalog_state",
    "execution_history_state",
    "audit_event",
    "persistent_audit_state",
    "memory_brain_v2_state",
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
            "/mark-3/voice-runtime/status",
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
            "voice_runtime_state",
            "/mark-3/voice-runtime/status",
            _get(dashboard_status, "voice_runtime_pack.current_state", "idle"),
            {
                "schema_version": _get(dashboard_status, "voice_runtime_pack.schema_version", "jarvis.voice_runtime_pack.v1"),
                "runtime_id": _get(dashboard_status, "voice_runtime_pack.runtime_id", "jarvis-local-manual-voice-runtime-pack"),
                "mode": _get(dashboard_status, "voice_runtime_pack.mode", "local_manual_browser_voice_control_plane"),
                "enabled": _bool(_get(dashboard_status, "voice_runtime_pack.enabled", True)),
                "manual_push_to_talk_enabled": _bool(_get(dashboard_status, "voice_runtime_pack.manual_push_to_talk_enabled", True)),
                "browser_stt_available": _get(dashboard_status, "voice_runtime_pack.browser_stt_available", "client_side_unknown"),
                "browser_tts_available": _get(dashboard_status, "voice_runtime_pack.browser_tts_available", "client_side_unknown"),
                "local_stt_provider_status": _provider_status_summary(_get(dashboard_status, "voice_runtime_pack.local_stt_provider_status", {})),
                "local_tts_provider_status": _provider_status_summary(_get(dashboard_status, "voice_runtime_pack.local_tts_provider_status", {})),
                "wake_runtime_status": _get(dashboard_status, "voice_runtime_pack.wake_runtime_status.status", "wake_listening_disabled"),
                "active_session": _bool(_get(dashboard_status, "voice_runtime_pack.active_session.active", False)),
                "last_transcript_summary_available": _bool(_get(dashboard_status, "voice_runtime_pack.last_transcript_summary.available", False)),
                "last_response_summary_available": _bool(_get(dashboard_status, "voice_runtime_pack.last_response_summary.available", False)),
                "current_state": _get(dashboard_status, "voice_runtime_pack.current_state", "idle"),
                "can_interrupt": _bool(_get(dashboard_status, "voice_runtime_pack.can_interrupt", True)),
                "can_cancel": _bool(_get(dashboard_status, "voice_runtime_pack.can_cancel", True)),
                "raw_audio_sent_to_backend": False,
                "transcript_persistence": False,
                "voice_approval_enabled": False,
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "hermes_dispatch_allowed": False,
                "raw_text_omitted": True,
                "raw_audio_included": False,
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
            "/mark-3/execution/status",
            _get(dashboard_status, "approvals.cards_state", "governed/backend-gated"),
            {
                "pending_count": _get(dashboard_status, "approvals.pending_count", "unknown"),
                "critical_count": _get(dashboard_status, "approvals.critical_count", "unknown"),
                "action_buttons_enabled": _bool(_get(dashboard_status, "approvals.action_buttons_enabled", False)),
                "governed_backend_only": True,
                "wake_phrase_can_approve": False,
                "voice_approval_requires_auth_gate_and_audit": True,
                "frontend_direct_hermes_allowed": False,
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
            "/mark-3/memory-brain/status",
            _get(dashboard_status, "memory_brain.state.mode", "visible_read_only_brain"),
            {
                "visible_brain": True,
                "entity_count": _get(dashboard_status, "memory_brain.counts.entities", 0),
                "fact_count": _get(dashboard_status, "memory_brain.counts.facts", 0),
                "decision_count": _get(dashboard_status, "memory_brain.counts.decisions", 0),
                "preference_count": _get(dashboard_status, "memory_brain.counts.preferences", 0),
                "contradiction_count": _get(dashboard_status, "memory_brain.counts.contradictions", 0),
                "active_memory_count": _get(dashboard_status, "memory_brain.counts.active_memories", 0),
                "pending_review_count": _get(dashboard_status, "memory_brain.counts.pending_review", 0),
                "forgotten_deleted_count": _get(dashboard_status, "memory_brain.counts.forgotten_deleted", 0),
                "outcome_count": _get(dashboard_status, "memory_brain.counts.outcomes", 0),
                "learning_proposal_count": _get(dashboard_status, "memory_brain.counts.learning_proposals", 0),
                "compaction": _get(dashboard_status, "memory_brain.compaction.status", "contract_only"),
                "forget_delete": _get(dashboard_status, "memory_brain.forget_delete.status", "audited_python_store"),
                "memory_never_grants_permission": True,
            },
        ),
        _event(
            generated_at,
            "memory_brain_v2_state",
            "/mark-3/memory-brain/preview",
            _get(dashboard_status, "memory_brain_v2.state.mode", "in_memory_explainable_memory_brain_v2"),
            {
                "schema_version": _get(dashboard_status, "memory_brain_v2.schema_version", "jarvis.memory_brain_v2.v1"),
                "persistent": _bool(_get(dashboard_status, "memory_brain_v2.state.persistent", False)),
                "storage_configured": _bool(_get(dashboard_status, "memory_brain_v2.state.storage_configured", False)),
                "entities": _get(dashboard_status, "memory_brain.counts.entities", 0),
                "facts": _get(dashboard_status, "memory_brain.counts.facts", 0),
                "preferences": _get(dashboard_status, "memory_brain.counts.preferences", 0),
                "decisions": _get(dashboard_status, "memory_brain.counts.decisions", 0),
                "projects": _get(dashboard_status, "memory_brain.counts.projects", 0),
                "contradictions": _get(dashboard_status, "memory_brain.counts.contradictions", 0),
                "active_memories": _get(dashboard_status, "memory_brain.counts.active_memories", 0),
                "pending_review": _get(dashboard_status, "memory_brain.counts.pending_review", 0),
                "forgotten_deleted": _get(dashboard_status, "memory_brain.counts.forgotten_deleted", 0),
                "memory_autoload_enabled": False,
                "memory_grants_permission": False,
                "hermes_dispatch_allowed": False,
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
            "/mark-3/execution/status",
            _get(dashboard_status, "governed_execution.state.mode", "phase_1_governed_execution_control_plane"),
            {
                "preview_required": True,
                "approval_required": True,
                "hermes_dispatch_after_approval_only": True,
                "rollback_or_stop_plan_required": True,
                "frontend_direct_execution_allowed": False,
                "direct_execute_route_exposed": False,
                "governed_dispatch_endpoint": "/mark-3/execution/dispatch",
                "supported_real_dispatch": _get(dashboard_status, "governed_execution.state.supported_real_dispatch", "exact_local_file_read_via_existing_mark_3_hermes_runtime_bridge"),
                "preview_count": _get(dashboard_status, "governed_execution.counts.previews", 0),
                "approval_pending": _get(dashboard_status, "governed_execution.counts.approval_pending", 0),
                "active_execution_count": _get(dashboard_status, "governed_execution.state.active_execution_count", 0),
                "shell_freeform_allowed": False,
                "memory_grants_permission": False,
            },
        ),
        _event(
            generated_at,
            "phase_1_state",
            "/mark-3/phase-1/status",
            _get(dashboard_status, "phase_1_completion.status", "complete_for_local_governed_pilot"),
            {
                "schema_version": _get(dashboard_status, "phase_1_completion.schema_version", "jarvis.phase_1_completion.v1"),
                "status": _get(dashboard_status, "phase_1_completion.status", "unknown"),
                "governed_execution": _get(dashboard_status, "phase_1_completion.capabilities.governed_hermes_exact_local_read", "unknown"),
                "approval_ui_backend_gates": _get(dashboard_status, "phase_1_completion.capabilities.approval_ui_backend_gates", "unknown"),
                "persistent_audit_metadata_only": _get(dashboard_status, "phase_1_completion.capabilities.persistent_audit_metadata_only", "unknown"),
                "memory_brain_v2_explainable_context": _get(dashboard_status, "phase_1_completion.capabilities.memory_brain_v2_explainable_context", "unknown"),
                "critical_double_triple_approval": _get(dashboard_status, "phase_1_completion.risks.critical_double_triple_approval", "unknown"),
                "generic_execute_absent": _bool(_get(dashboard_status, "phase_1_completion.route_readiness.generic_execute_absent", True)),
            },
        ),
        _event(
            generated_at,
            "phase_2_state",
            "/mark-3/phase-2/status",
            _get(dashboard_status, "phase_2_status.status", "implemented_as_local_governed_runtime_macro_phase"),
            {
                "schema_version": _get(dashboard_status, "phase_2_status.schema_version", "jarvis.phase_2_local_assistant_runtime.v1"),
                "strong_approval_v2": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.strong_approval_v2", True)),
                "allowlisted_bridge": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.hermes_action_bridge_allowlisted", True)),
                "execution_history": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.execution_history", True)),
                "stop_rollback_contracts": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.stop_rollback_contracts", True)),
                "voice_wake_runtime_readiness": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.voice_wake_runtime_readiness", True)),
                "browser_verification": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.browser_verification", True)),
                "local_daemon_tray_readiness": _bool(_get(dashboard_status, "phase_2_status.implemented_blocks.local_daemon_tray_readiness", True)),
                "generic_execute_absent": _bool(_get(dashboard_status, "phase_2_status.route_readiness.generic_execute_absent", True)),
                "critical_double_triple": _get(dashboard_status, "phase_2_status.blocked_or_unsupported.critical_double_triple", "blocked_requires_stronger_approval_not_configured"),
                "no_commands_or_outputs": True,
            },
        ),
        _event(
            generated_at,
            "phase_3_state",
            "/mark-3/phase-3/status",
            _get(dashboard_status, "phase_3_status.status", "implemented_as_local_governed_runtime_macro_phase"),
            {
                "schema_version": _get(dashboard_status, "phase_3_status.schema_version", "jarvis.phase_3_local_runtime_daemon_trusted_approvals.v1"),
                "local_runtime_daemon_contract": _bool(_get(dashboard_status, "phase_3_status.implemented_blocks.local_runtime_daemon_contract", True)),
                "trusted_approval_channels": _bool(_get(dashboard_status, "phase_3_status.implemented_blocks.trusted_approval_channels", True)),
                "double_approval_two_steps": _bool(_get(dashboard_status, "phase_3_status.implemented_blocks.double_approval_two_steps", True)),
                "triple_honest_block": _bool(_get(dashboard_status, "phase_3_status.implemented_blocks.triple_honest_block", True)),
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
                "generic_execute_absent": _bool(_get(dashboard_status, "phase_3_status.route_readiness.generic_execute_absent", True)),
            },
        ),
        _event(
            generated_at,
            "phase_4_state",
            "/mark-3/phase-4/status",
            _get(dashboard_status, "phase_4_status.status", "implemented_as_local_controller_remote_pairing_readiness_macro_phase"),
            {
                "schema_version": _get(dashboard_status, "phase_4_status.schema_version", "jarvis.phase_4_real_local_controller_remote_pairing_readiness.v1"),
                "local_controller_opt_in": _bool(_get(dashboard_status, "phase_4_status.implemented_blocks.real_local_controller_opt_in", True)),
                "trusted_device_identity": _bool(_get(dashboard_status, "phase_4_status.implemented_blocks.trusted_device_controller_identity", True)),
                "triple_readiness": _get(dashboard_status, "phase_4_status.triple_approval_readiness.triple_status", "blocked_no_three_verified_channels"),
                "remote_pairing_enabled": False,
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
                "telegram_api_called": False,
                "generic_execute_absent": _bool(_get(dashboard_status, "phase_4_status.route_readiness.generic_execute_absent", True)),
            },
        ),
        _event(
            generated_at,
            "daemon_state",
            "/mark-3/local-daemon/status",
            _get(dashboard_status, "local_daemon.daemon_status", "unknown"),
            {
                "schema_version": _get(dashboard_status, "local_daemon.schema_version", "jarvis.local_daemon.v1"),
                "local_only": _bool(_get(dashboard_status, "local_daemon.local_only", True)),
                "bind_host": _get(dashboard_status, "local_daemon.bind_host", "127.0.0.1"),
                "auto_start_enabled": False,
                "background_listening_enabled": False,
                "mic_auto_start": False,
                "camera_auto_start": False,
                "wake_auto_start": False,
                "health_status": _get(dashboard_status, "local_daemon.health_status", "unknown"),
            },
        ),
        _event(
            generated_at,
            "local_controller_state",
            "/mark-3/local-controller/status",
            _get(dashboard_status, "local_controller.controller_status", "not_registered"),
            {
                "schema_version": _get(dashboard_status, "local_controller.schema_version", "jarvis.local_controller.v1"),
                "controller_id": _get(dashboard_status, "local_controller.controller_id", "unknown"),
                "local_only": _bool(_get(dashboard_status, "local_controller.local_only", True)),
                "bind_host": _get(dashboard_status, "local_controller.bind_host", "127.0.0.1"),
                "auto_start_enabled": False,
                "installed_as_system_service": False,
                "startup_integration_enabled": False,
                "user_opt_in_required": True,
                "no_background_capture": True,
                "verified": _bool(_get(dashboard_status, "local_controller.verified", False)),
            },
        ),
        _event(
            generated_at,
            "trusted_channels_state",
            "/mark-3/trusted-approval-channels/status",
            _get(dashboard_status, "trusted_approval_channels.triple_status", "triple_requires_additional_trusted_channel_not_configured"),
            {
                "schema_version": _get(dashboard_status, "trusted_approval_channels.schema_version", "jarvis.trusted_approval_channels.v1"),
                "trusted_enabled_channel_count": _get(dashboard_status, "trusted_approval_channels.trusted_enabled_channel_count", 0),
                "can_grant_strong": _bool(_get(dashboard_status, "trusted_approval_channels.can_grant_strong", True)),
                "can_grant_double": _bool(_get(dashboard_status, "trusted_approval_channels.can_grant_double", True)),
                "can_grant_triple": False,
                "voice_can_approve": False,
                "wake_phrase_can_approve": False,
                "remote_approval_allowed": False,
            },
        ),
        _event(
            generated_at,
            "trusted_devices_state",
            "/mark-3/trusted-devices/status",
            _get(dashboard_status, "trusted_devices.trusted_device_count", 0),
            {
                "schema_version": _get(dashboard_status, "trusted_devices.schema_version", "jarvis.trusted_devices.v1"),
                "trusted_device_count": _get(dashboard_status, "trusted_devices.trusted_device_count", 0),
                "paired_devices_count": _get(dashboard_status, "trusted_devices.paired_devices_count", 0),
                "remote_devices_count": _get(dashboard_status, "trusted_devices.remote_devices_count", 0),
                "remote_trusted_devices_count": _get(dashboard_status, "trusted_devices.remote_trusted_devices_count", 0),
                "terminal_trust_requires_challenge": True,
                "controller_trust_requires_registration_and_verification": True,
                "voice_can_approve": False,
                "wake_phrase_can_approve": False,
            },
        ),
        _event(
            generated_at,
            "remote_pairing_state",
            "/mark-3/remote-pairing/status",
            _get(dashboard_status, "remote_pairing.pairing_status", "disabled_readiness_only"),
            {
                "schema_version": _get(dashboard_status, "remote_pairing.schema_version", "jarvis.remote_pairing_readiness.v1"),
                "remote_pairing_enabled": False,
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
                "trusted_pairing_required": True,
                "pairing_code_created": _bool(_get(dashboard_status, "remote_pairing.pairing_code_created", False)),
                "pending_pairing_count": _get(dashboard_status, "remote_pairing.pending_pairing_count", 0),
                "revoked_pairing_count": _get(dashboard_status, "remote_pairing.revoked_pairing_count", 0),
                "tokens_persisted": False,
            },
        ),
        _event(
            generated_at,
            "telegram_bridge_state",
            "/mark-3/telegram-bridge/status",
            _get(dashboard_status, "telegram_bridge.telegram_bridge_status", "disabled_not_configured"),
            {
                "schema_version": _get(dashboard_status, "telegram_bridge.schema_version", "jarvis.telegram_bridge_readiness.v1"),
                "token_present": _get(dashboard_status, "telegram_bridge.token_present", "unknown_redacted"),
                "token_read": False,
                "telegram_api_called": False,
                "bot_started": False,
                "webhook_opened": False,
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
                "pairing_required": True,
            },
        ),
        _event(
            generated_at,
            "stop_rollback_v2_state",
            "/mark-3/stop-rollback/status",
            _get(dashboard_status, "stop_rollback_v2.status", "observable_metadata_only"),
            {
                "schema_version": _get(dashboard_status, "stop_rollback_v2.schema_version", "jarvis.stop_rollback_v2.v1"),
                "cooperative_stop_signal": _bool(_get(dashboard_status, "stop_rollback_v2.cooperative_stop_signal", False)),
                "bridge_stop_attempt": _get(dashboard_status, "stop_rollback_v2.bridge_stop_attempt", "not_attempted"),
                "result_observed": _bool(_get(dashboard_status, "stop_rollback_v2.result_observed", False)),
                "final_state": _get(dashboard_status, "stop_rollback_v2.final_state", "no_active_stop_request"),
                "rollback_dry_run_mode": True,
                "destructive_rollback_executed": False,
                "rollback_never_faked": True,
            },
        ),
        _event(
            generated_at,
            "action_catalog_state",
            "/mark-3/execution/action-catalog",
            "allowlist_only",
            {
                "schema_version": _get(dashboard_status, "action_catalog.schema_version", "jarvis.phase_2_local_assistant_runtime.v1"),
                "allowlist_only": _bool(_get(dashboard_status, "action_catalog.allowlist_only", True)),
                "freeform_shell_allowed": False,
                "arbitrary_command_allowed": False,
                "action_count": len(_get(dashboard_status, "action_catalog.actions", [])),
                "denied_action_count": len(_get(dashboard_status, "action_catalog.denied_actions", [])),
                "network_allowed": False,
                "external_side_effects": False,
                "frontend_direct_hermes_allowed": False,
                "no_command_text": True,
            },
        ),
        _event(
            generated_at,
            "execution_history_state",
            "/mark-3/execution/history",
            _get(dashboard_status, "execution_history.status.record_count", 0),
            {
                "schema_version": _get(dashboard_status, "execution_history.schema_version", "jarvis.execution_history.v2"),
                "read_only": True,
                "metadata_only": _bool(_get(dashboard_status, "execution_history.status.metadata_only", True)),
                "record_count": _get(dashboard_status, "execution_history.status.record_count", 0),
                "persistent": _bool(_get(dashboard_status, "execution_history.status.persistent", False)),
                "contains_secret": False,
                "contains_credential": False,
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "raw_output_included": False,
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
            "persistent_audit_state",
            "/mark-3/audit/status",
            _get(dashboard_status, "persistent_audit.state.mode", "in_memory_metadata_audit_ledger"),
            {
                "schema_version": _get(dashboard_status, "persistent_audit.schema_version", "jarvis.persistent_audit.v1"),
                "persistent": _bool(_get(dashboard_status, "persistent_audit.state.persistent", False)),
                "storage_configured": _bool(_get(dashboard_status, "persistent_audit.state.storage_configured", False)),
                "event_count": _get(dashboard_status, "persistent_audit.state.event_count", 0),
                "tamper_evident": True,
                "hash_chain_valid": _bool(_get(dashboard_status, "persistent_audit.chain.valid", True)),
                "checked_count": _get(dashboard_status, "persistent_audit.chain.checked_count", 0),
                "metadata_only": True,
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "contains_secret": False,
                "contains_credential": False,
                "contains_full_transcript": False,
                "hermes_dispatch_allowed": False,
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


def _provider_status_summary(providers: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(providers, dict):
        return {}
    summary: Dict[str, Dict[str, Any]] = {}
    for name, value in providers.items():
        if not isinstance(value, dict):
            continue
        summary[str(name)] = {
            "status": _safe_scalar(value.get("status", "unknown")),
            "enabled": _bool(value.get("enabled", False)),
            "installed": value.get("installed", "unknown") if isinstance(value.get("installed", "unknown"), bool) else _safe_scalar(value.get("installed", "unknown")),
            "local_only": _bool(value.get("local_only", True)),
            "network_required": _bool(value.get("network_required", False)),
            "external_provider": _bool(value.get("external_provider", False)),
        }
    return summary


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
            if isinstance(value, bool) and (
                lowered.startswith("no_")
                or lowered.startswith("contains_")
                or "blocked" in lowered
                or lowered.endswith("_included")
            ):
                sanitized[key] = value
                continue
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
    if event_type in {"camera_state", "recording_state", "voice_runtime_state", "voice_state", "voice_session_state", "wake_state", "tts_state", "sensor_ledger_state"}:
        return "sensor_privacy"
    if event_type == "brain_state":
        return "intent_risk_preview"
    if event_type in {"approval_state", "risk_state", "execution_state", "phase_2_state", "action_catalog_state", "policy_state"}:
        return "approval_gate"
    if event_type == "execution_history_state":
        return "metadata_audit"
    if event_type == "remote_state":
        return "remote_surface"
    if event_type in {"memory_state", "memory_brain_v2_state"}:
        return "memory_privacy"
    if event_type == "persistent_audit_state":
        return "metadata_audit"
    return "low"
