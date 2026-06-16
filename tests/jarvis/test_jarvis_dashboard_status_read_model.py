import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import create_app


class FailingAdapter:
    def run(self, *_args, **_kwargs):
        pytest.fail("legacy Hermes adapter must not be called by dashboard status")


def _app():
    return create_app(
        adapter_factory=lambda: FailingAdapter(),
        hermes_runtime_adapter_factory=lambda _guard: pytest.fail(
            "Hermes runtime adapter factory must not be called by dashboard status"
        ),
    )


def _dashboard_route(app):
    for route in app.routes:
        if route.path == "/mark-3/dashboard/status":
            return route
    raise AssertionError("missing /mark-3/dashboard/status route")


def _payload():
    app = _app()
    route = _dashboard_route(app)
    return route.endpoint(), app


def test_mark_3_dashboard_status_endpoint_responds_200():
    app = _app()
    route = _dashboard_route(app)
    payload = route.endpoint()

    assert route.methods == {"GET"}
    assert isinstance(payload, dict)
    assert payload["system"]["api_status"] == "ok"
    assert payload["system"]["mode"] == "read_only_dashboard"
    assert payload["system"]["free_autonomy_enabled"] is False
    assert payload["system"]["preview_first"] is True
    assert payload["system"]["generated_at"]


def test_mark_3_dashboard_status_declares_jarvis_hermes_contract():
    payload, _ = _payload()

    assert payload["jarvis_hermes_contract"]["jarvis_role"] == "governs/risk/approval/audit/control"
    assert payload["jarvis_hermes_contract"]["hermes_role"] == "execution_engine"
    assert payload["jarvis_hermes_contract"]["frontend_direct_execution_allowed"] is False
    assert payload["jarvis_hermes_contract"]["frontend_can_execute"] is False
    assert payload["jarvis_hermes_contract"]["frontend_can_call_hermes_execute"] is False
    assert payload["jarvis_hermes_contract"]["no_duplicate_hermes_runtime"] is True
    assert payload["release_candidate"]["not_ready_for_free_autonomy"] is True
    assert payload["release_candidate"]["restrictions_are_approval_gates_not_permanent_bans"] is True


def test_mark_3_dashboard_status_enriches_hermes_execution_contract_and_runtime_visibility():
    payload, _ = _payload()
    hermes = payload["hermes_execution"]
    contract = hermes["contract"]
    runtime = hermes["runtime_status"]

    assert contract["jarvis_role"] == "governs/risk/approval/audit/control"
    assert contract["hermes_role"] == "execution_engine"
    assert contract["no_duplicate_hermes_runtime"] is True
    assert contract["frontend_direct_execution_allowed"] is False
    assert contract["frontend_can_execute"] is False
    assert contract["frontend_can_call_hermes_execute"] is False

    assert hermes["frontend_direct_execution_allowed"] is False
    assert hermes["frontend_can_execute"] is False
    assert hermes["frontend_can_call_hermes_execute"] is False
    assert runtime["available"] in {True, False, "unknown"}
    assert runtime["connected"] in {True, False, "unknown"}
    assert runtime["active_execution"] in {False, "unknown"}
    assert runtime["execution_mode"] == "read_only_visibility"
    assert runtime["last_execution"] == "unknown"
    assert runtime["last_result"] == "unknown"
    assert runtime["last_error"] == "unknown"
    assert runtime["last_rollback"] == "unknown"
    assert runtime["last_stop_plan"] == "unknown"
    assert runtime["measured_duration"] == "unknown"
    assert runtime["measured_cost"] == "unknown"


def test_mark_3_dashboard_status_contains_required_modules_and_sources():
    payload, _ = _payload()
    modules = {item["name"]: item for item in payload["modules"]}

    for name in (
        "Mission Loop",
        "Research",
        "Product Revenue",
        "Routine Ops",
        "Moonshot Lab",
        "Voice",
        "Wake Listener",
        "Camera/Vision",
        "Mobile Companion",
        "Memory/Learning",
        "Hermes",
    ):
        assert name in modules
        assert modules[name]["status"] in {
            "ready",
            "preview",
            "prepare-only",
            "gated",
            "disabled",
            "not_connected",
            "unknown",
        }
        assert modules[name]["source"]
        assert modules[name]["risk"]
        assert modules[name]["notes"]


def test_mark_3_dashboard_status_keeps_approvals_sensors_and_execution_disabled():
    payload, _ = _payload()

    assert payload["approvals"]["pending_count"] == 0
    assert payload["approvals"]["action_buttons_enabled"] is False
    assert payload["approvals"]["all_actions_read_only"] is True
    assert payload["approvals"]["wake_phrase_can_approve"] is False
    assert payload["approvals"]["frontend_can_approve"] is False
    assert payload["approvals"]["frontend_can_reject"] is False
    assert payload["approvals"]["frontend_can_modify_scope"] is False
    assert payload["approvals"]["critical_actions_require_strong_approval"] is True
    assert payload["hermes_execution"]["frontend_direct_execution_allowed"] is False
    assert payload["voice_wake"]["wake_phrase_can_approve"] is False
    assert payload["voice_wake"]["wake_phrase_can_execute"] is False
    assert payload["voice_wake"]["audio_recording"] is False
    assert payload["voice_wake"]["raw_audio_stored"] is False
    assert payload["voice_wake"]["external_provider_called"] is False
    assert payload["camera_vision"]["recording"] is False
    assert payload["camera_vision"]["storage"] is False
    assert payload["mobile"]["direct_hermes_call_allowed"] is False


def test_mark_3_dashboard_status_contains_voice_core_visual_tts_state_contract():
    payload, _ = _payload()
    voice_core = payload["voice_core"]
    state = voice_core["state"]
    visual_states = voice_core["visual_states"]
    tts_state = voice_core["tts_state"]
    wake_policy = voice_core["wake_word_policy"]
    privacy = voice_core["privacy"]
    safety = voice_core["safety"]

    assert state["mode"] == "preview"
    assert state["current_state"] in {"preview", "dormant"}
    assert state["microphone_enabled"] is False
    assert state["wake_word_enabled"] is False
    assert state["command_listening_enabled"] is False
    assert state["tts_enabled"] is False
    assert state["stt_enabled"] is False
    assert state["audio_recording"] is False
    assert state["raw_audio_stored"] is False
    assert state["external_provider_called"] is False
    assert state["voice_approval_enabled"] is False
    assert state["wake_phrase_can_approve"] is False
    assert state["wake_phrase_can_execute"] is False

    expected_states = [
        "offline",
        "online",
        "preview",
        "dormant",
        "listening_wake_word",
        "listening_command",
        "thinking",
        "speaking",
        "approval_required",
        "hermes_executing",
        "paused",
        "blocked",
        "error",
        "kill_switch",
    ]
    assert [item["state"] for item in visual_states] == expected_states
    for visual_state in visual_states:
        assert visual_state["label"]
        assert visual_state["description"]
        assert visual_state["risk"]
        assert visual_state["enabled"] in {False, "preview"}
        assert isinstance(visual_state["sensor_required"], bool)
        assert visual_state["can_approve"] is False

    assert tts_state["status"] in {"disabled", "preview", "not_connected", "unknown"}
    assert tts_state["speaking"] is False
    assert "preview" in tts_state["last_utterance"]
    assert tts_state["subtitles_enabled"] is True
    assert tts_state["subtitles_source"] == "preview/read_model"
    assert tts_state["audio_output_enabled"] is False
    assert tts_state["provider"] in {"none", "not_connected", "none/not_connected"}
    assert tts_state["external_call"] is False

    assert wake_policy["supported_phrases"] == ["Hola Jarvis", "Jarvis"]
    assert wake_policy["wake_word_runtime"] in {"disabled", "not_connected", "preview", "disabled/not_connected"}
    assert wake_policy["wake_phrase_is_permission"] is False
    assert wake_policy["wake_phrase_can_approve"] is False
    assert wake_policy["wake_phrase_can_execute"] is False
    assert wake_policy["requires_authenticated_channel_for_approval"] is True
    assert wake_policy["critical_actions_require_readback"] is True
    assert wake_policy["critical_actions_require_strong_confirmation"] is True

    for key in (
        "no_microphone_activation",
        "no_audio_recording",
        "no_raw_audio_storage",
        "no_external_audio_provider",
        "no_background_listening_enabled",
        "no_voice_biometrics",
        "no_voice_approval_without_gate",
    ):
        assert privacy[key] is True

    for key in (
        "no_auto_execute",
        "no_hermes_dispatch",
        "no_tool_call",
        "no_sensor_activation",
        "no_get_user_media",
        "no_media_recorder",
        "no_audio_context_capture",
        "kill_switch_visible",
    ):
        assert safety[key] is True


def test_mark_3_dashboard_status_contains_wake_word_local_safe_flow_contract():
    payload, _ = _payload()
    flow = payload["wake_word_flow"]
    state = flow["state"]
    parse_preview = flow["wake_parse_preview"]
    approval_policy = flow["approval_policy"]
    safety = flow["safety"]

    assert state["mode"] == "preview"
    assert state["wake_runtime_enabled"] is False
    assert state["microphone_hard_off"] is True
    assert state["wake_word_only_mode"] is False
    assert state["command_window_open"] is False
    assert state["push_to_talk_preview_enabled"] is True
    assert state["typed_wake_preview_enabled"] is True
    assert state["always_on_microphone_enabled"] is False
    assert state["background_listener_enabled"] is False
    assert state["stt_enabled"] is False
    assert state["audio_recording"] is False
    assert state["raw_audio_stored"] is False
    assert state["external_provider_called"] is False

    assert "Hola Jarvis" in flow["supported_phrases"]
    assert "Jarvis" in flow["supported_phrases"]
    assert flow["stop_phrases"]
    for phrase in ("para", "cancela", "detente", "silencio", "cancelar misión", "apaga escucha"):
        assert phrase in flow["stop_phrases"]

    assert flow["mode_explanations"]["mic_hard_off"]
    assert flow["mode_explanations"]["wake_word_only"]
    assert flow["mode_explanations"]["command_listening"]
    assert flow["mode_explanations"]["push_to_talk"]
    assert flow["mode_explanations"]["typed_preview"]

    assert parse_preview["input_example"] == "Hola Jarvis, revisa el estado del proyecto"
    assert parse_preview["detected_wake_phrase"] == "Hola Jarvis"
    assert parse_preview["remaining_command_preview"] == "revisa el estado del proyecto"
    assert parse_preview["would_open_command_window"] is True
    assert parse_preview["would_execute"] is False
    assert parse_preview["would_approve"] is False
    assert parse_preview["would_call_hermes"] is False
    assert parse_preview["would_record_audio"] is False
    assert parse_preview["would_call_provider"] is False
    assert parse_preview["status"] == "preview_only"

    assert approval_policy["wake_phrase_is_permission"] is False
    assert approval_policy["wake_phrase_can_approve"] is False
    assert approval_policy["wake_phrase_can_execute"] is False
    assert approval_policy["voice_approval_requires_authenticated_channel"] is True
    assert approval_policy["sensitive_actions_require_readback"] is True
    assert approval_policy["critical_actions_require_double_or_triple_confirmation"] is True
    assert approval_policy["approval_events_must_be_audited"] is True

    for key in (
        "no_microphone_activation",
        "no_get_user_media",
        "no_media_recorder",
        "no_audio_context_capture",
        "no_background_listening",
        "no_raw_audio_storage",
        "no_external_stt",
        "no_external_tts",
        "no_hermes_dispatch",
        "no_tool_call",
        "no_auto_execute",
    ):
        assert safety[key] is True


def test_mark_3_dashboard_status_contains_camera_vision_preview_privacy_contract():
    payload, _ = _payload()
    camera_vision = payload["camera_vision"]
    state = camera_vision["state"]
    privacy = camera_vision["privacy"]
    scope_policy = camera_vision["scope_policy"]
    timeline_events = [item["event"] for item in camera_vision["timeline"]]

    assert camera_vision["preview_only"] is True
    assert camera_vision["read_only"] is True
    assert state["mode"] == "preview"
    assert state["camera_enabled"] is False
    assert state["camera_permission_requested"] is False
    assert state["preview_enabled"] is False
    assert state["recording"] is False
    assert state["streaming"] is False
    assert state["snapshot_capture_enabled"] is False
    assert state["vision_analysis_enabled"] is False
    assert state["image_storage_enabled"] is False
    assert state["video_storage_enabled"] is False
    assert state["external_vision_provider_called"] is False
    assert state["local_vision_model_connected"] in {False, "unknown"}
    assert state["background_camera_access"] is False

    assert camera_vision["camera_state"] == "disabled"
    assert camera_vision["preview_state"] == "disabled"
    assert camera_vision["recording"] is False
    assert camera_vision["streaming"] is False
    assert camera_vision["snapshot"] == "disabled"
    assert camera_vision["vision_analysis"] == "disabled"
    assert camera_vision["storage"] is False
    assert camera_vision["provider"] == "none/not_connected"

    for key in (
        "no_camera_activation",
        "no_get_user_media",
        "no_media_stream",
        "no_recording",
        "no_snapshot_capture",
        "no_image_storage",
        "no_video_storage",
        "no_external_provider",
        "explicit_operator_permission_required",
        "visual_indicator_required_when_camera_active",
        "audit_required_for_future_vision",
    ):
        assert privacy[key] is True

    expected_states = [
        "camera_off",
        "camera_available_future",
        "preview_disabled",
        "permission_required",
        "analyzing_future",
        "recording_disabled",
        "storage_disabled",
        "blocked",
        "kill_switch",
    ]
    assert [item["state"] for item in camera_vision["states"]] == expected_states
    for visual_state in camera_vision["states"]:
        assert visual_state["label"]
        assert visual_state["description"]
        assert visual_state["enabled"] in {False, "preview", "future_gated"}
        assert visual_state["risk"]
        assert visual_state["can_execute"] is False

    assert scope_policy["allowed_scope"] == "none/unknown"
    assert scope_policy["future_scope_requires_explicit_operator_permission"] is True
    assert scope_policy["future_analysis_must_state_what_it_can_see"] is True
    assert scope_policy["future_analysis_must_not_infer_sensitive_identity"] is True
    assert scope_policy["future_analysis_must_not_store_without_permission"] is True

    for event in (
        "Camera/Vision privacy status read",
        "Camera disabled",
        "Recording disabled",
        "Vision analysis disabled",
        "No image or video captured",
        "No external vision provider called",
    ):
        assert event in timeline_events

    serialized = " ".join(timeline_events).lower()
    for forbidden in (
        "camera started",
        "camera enabled",
        "image captured and stored",
        "video recorded",
        "stream started",
        "external vision analysis completed",
    ):
        assert forbidden not in serialized


def test_mark_3_dashboard_status_contains_mobile_companion_pwa_preview_contract():
    payload, _ = _payload()
    mobile = payload["mobile_companion"]
    state = mobile["state"]
    safety = mobile["safety"]
    pwa_policy = mobile["pwa_policy"]
    timeline_events = [item["event"] for item in mobile["timeline"]]

    assert mobile["preview_only"] is True
    assert mobile["read_only"] is True
    assert state["mode"] == "preview"
    assert state["pwa_baseline"] == "preview"
    assert state["mobile_runtime_enabled"] is False
    assert state["mobile_can_execute"] is False
    assert state["mobile_can_call_hermes_directly"] is False
    assert state["mobile_can_approve_real_actions"] is False
    assert state["mobile_can_reject_real_actions"] is False
    assert state["mobile_can_modify_scope_real"] is False
    assert state["mobile_notifications_enabled"] is False
    assert state["remote_kill_switch_enabled"] is False
    assert state["remote_camera_enabled"] is False
    assert state["remote_microphone_enabled"] is False
    assert state["external_network_required"] in {False, "unknown"}

    expected_views = [
        "status",
        "approvals_preview",
        "mission_preview",
        "hermes_visibility",
        "voice_status",
        "camera_status",
        "finance_summary",
        "kill_switch_preview",
    ]
    assert [item["id"] for item in mobile["mobile_views"]] == expected_views
    for view in mobile["mobile_views"]:
        assert view["name"]
        assert view["status"] in {"preview", "future_gated", "disabled", "unknown"}
        assert view["can_execute"] is False
        assert view["can_call_hermes"] is False
        assert view["notes"]

    for key in (
        "mobile_is_interface_not_runtime",
        "no_direct_hermes_call",
        "no_mobile_execute",
        "no_mobile_sensor_activation",
        "no_mobile_camera_activation",
        "no_mobile_microphone_activation",
        "no_real_mobile_approval_in_this_pr",
        "approval_requires_backend_gate",
        "critical_approval_requires_strong_confirmation",
        "remote_kill_switch_future_gated",
    ):
        assert safety[key] is True

    assert pwa_policy["installable_pwa"] == "preview"
    assert pwa_policy["offline_cache_enabled"] is False
    assert pwa_policy["push_notifications_enabled"] is False
    assert pwa_policy["service_worker_enabled"] is False
    assert pwa_policy["no_background_sync"] is True
    assert pwa_policy["no_credentials_storage"] is True
    assert pwa_policy["no_token_storage"] is True

    assert payload["mobile"]["direct_hermes_call_allowed"] is False
    assert payload["mobile"]["approval_actions_enabled"] is False
    assert payload["mobile"]["permissions"]["can_execute"] is False
    assert payload["mobile"]["permissions"]["can_approve"] is False

    for event in (
        "Mobile Companion preview read",
        "Mobile is interface, not runtime",
        "Mobile direct Hermes call disabled",
        "Real mobile approvals disabled",
        "Remote kill switch future gated",
    ):
        assert event in timeline_events

    serialized = " ".join(timeline_events).lower()
    for forbidden in (
        "mobile runtime started",
        "mobile executed",
        "mobile approval approved",
        "mobile approval rejected",
        "remote kill switch activated",
        "push notification sent",
    ):
        assert forbidden not in serialized


def test_mark_3_dashboard_status_contains_mission_control_preview_contract():
    payload, _ = _payload()
    mission_control = payload["mission_control"]
    state = mission_control["state"]
    supported_inputs = mission_control["supported_inputs"]
    intent_preview = mission_control["intent_preview"]
    lifecycle_states = [item["state"] for item in mission_control["command_lifecycle"]]

    assert state["mode"] == "preview"
    assert state["input_enabled"] == "preview_only"
    assert state["conversation_enabled"] == "preview_only"
    assert state["execution_enabled"] is False
    assert state["hermes_dispatch_enabled"] is False
    assert state["approval_creation_enabled"] is False
    assert state["persistence_enabled"] is False
    assert state["external_network_enabled"] is False

    assert supported_inputs["text_command"] == "preview"
    assert supported_inputs["voice_command"] == "future_gated"
    assert supported_inputs["mobile_command"] == "future_gated"
    assert supported_inputs["wake_word_command"] == "future_gated"
    assert supported_inputs["file_drop"] in {"disabled", "not_connected"}
    assert supported_inputs["camera_context"] in {"disabled", "not_connected"}

    assert mission_control["sample_command"] == "JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro."
    assert intent_preview == {
        "detected_intent": "unknown",
        "confidence": "unknown",
        "mission_type": "unknown",
        "risk_level": "unknown",
        "approval_level": "unknown",
        "blocked_reasons": [],
        "required_permissions": [],
        "next_safe_action": "unknown",
    }
    assert lifecycle_states == [
        "draft",
        "submitted_for_preview",
        "intent_detected",
        "risk_classified",
        "approval_required",
        "ready_for_operator_review",
        "blocked",
        "forbidden",
        "executable_candidate_after_valid_approval",
    ]
    assert all(item["preview_only"] is True for item in mission_control["command_lifecycle"])
    assert mission_control["read_only"] is True
    assert mission_control["source_endpoint"] == "/mark-3/dashboard/status"


def test_mark_3_dashboard_status_mission_control_conversation_preview_has_no_side_effects():
    payload, _ = _payload()
    conversation = payload["mission_control"]["conversation_preview"]
    messages = conversation["messages"]

    assert len(messages) >= 2
    assert messages[0]["speaker"] == "David"
    assert messages[0]["content"] == "JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro."
    assert messages[1]["speaker"] == "JARVIS"
    assert "pediré aprobación" in messages[1]["content"]
    assert all(message["preview_only"] is True for message in messages)
    assert conversation["assistant_status"] == "preview"
    assert conversation["transcript_persistence"] is False
    assert conversation["external_provider_called"] is False
    assert conversation["memory_write"] is False
    assert conversation["memory_read"] is False
    assert conversation["raw_audio_stored"] is False
    assert conversation["pii_redaction_required"] is True


def test_mark_3_dashboard_status_mission_control_safety_keeps_everything_preview_only():
    payload, _ = _payload()
    mission_safety = payload["mission_control"]["safety"]
    global_safety = payload["safety"]

    for key in (
        "no_auto_execute",
        "no_hermes_dispatch",
        "no_tool_call",
        "no_file_write",
        "no_network_call",
        "no_email_send",
        "no_money_movement",
        "no_deploy",
        "no_credentials",
        "no_sensor_activation",
        "no_voice_recording",
        "no_camera_capture",
        "wake_phrase_is_not_permission",
    ):
        assert mission_safety[key] is True

    for key in (
        "no_auto_execute",
        "no_tool_call",
        "no_file_write",
        "no_network_call",
        "no_sensor_activation",
    ):
        assert global_safety[key] is True


def test_mark_3_dashboard_status_hermes_capabilities_are_governed_and_not_frontend_executable():
    payload, _ = _payload()
    capabilities = payload["hermes_execution"]["governed_capabilities"]
    names = {item["name"] for item in capabilities}

    assert "local governed read" in names
    assert "local docs read" in names
    assert "repo/docs research adapter" in names
    assert "external tools" in names
    assert "deploy/email/money/credentials" in names

    allowed_statuses = {"ready", "gated", "prepare-only", "disabled", "not_connected", "forbidden", "unknown"}
    for capability in capabilities:
        assert capability["status"] in allowed_statuses
        assert isinstance(capability["approval_required"], bool)
        assert capability["approval_level"]
        assert capability["can_execute_from_frontend"] is False
        assert capability["notes"]


def test_mark_3_dashboard_status_hermes_blocked_routes_are_explicit():
    payload, _ = _payload()
    blocked = payload["hermes_execution"]["blocked_routes"]
    serialized = " ".join(
        f"{item['route_or_action']} {item['action']} {item['notes']}".lower()
        for item in blocked
    )

    for required in (
        "/execute",
        "approve/reject",
        "tool runner",
        "deploy",
        "money",
        "email",
        "credentials",
        "sensor activation",
        "camera/mic",
        "network external unless gated future",
    ):
        assert required in serialized

    for item in blocked:
        assert item["blocked"] is True
        assert item["can_execute_from_frontend"] is False


def test_mark_3_dashboard_status_contains_enriched_approval_summary_and_cards():
    payload, _ = _payload()
    approvals = payload["approvals"]
    cards = approvals["cards"]

    assert approvals["pending_count"] == 0
    assert approvals["critical_count"] >= 1
    assert approvals["blocked_count"] >= 1
    assert approvals["expired_count"] == 0
    assert approvals["preview_count"] == len(cards)
    assert approvals["cards_state"] == "preview/read-only"
    assert approvals["preview_only"] is True

    required_fields = {
        "id",
        "title",
        "action",
        "reason",
        "status",
        "risk_level",
        "approval_level",
        "touches",
        "estimated_cost",
        "measured_cost",
        "rollback_plan",
        "stop_plan",
        "expires_at",
        "scope_summary",
        "evidence_summary",
        "disabled_reason",
        "recommended_operator_action",
    }
    allowed_status = {"preview", "pending", "approved", "rejected", "expired", "blocked", "forbidden", "unknown"}
    allowed_risk = {"low", "medium", "high", "critical", "forbidden", "unknown"}
    allowed_approval = {"direct", "simple", "strong", "double", "triple", "forbidden", "unknown"}

    assert len(cards) >= 5
    for card in cards:
        assert required_fields.issubset(card)
        assert all(card[field] not in ("", None) for field in required_fields - {"touches"})
        assert card["status"] in allowed_status
        assert card["risk_level"] in allowed_risk
        assert card["approval_level"] in allowed_approval
        assert isinstance(card["touches"], list)
        assert card["touches"]
        assert card["estimated_cost"] == "unknown"
        assert card["measured_cost"] == "unknown"
        assert card["preview_only"] is True
        assert card["read_only"] is True
        assert "Preview-only" in card["disabled_reason"] or card["status"] in {"blocked", "forbidden"}


def test_mark_3_dashboard_status_critical_approvals_require_strong_gates_and_plans():
    payload, _ = _payload()
    critical_cards = [card for card in payload["approvals"]["cards"] if card["risk_level"] == "critical"]

    assert critical_cards
    for card in critical_cards:
        assert card["approval_level"] in {"strong", "double", "triple"}
        assert card["requires_readback"] is True
        assert card["strong_confirmation_required"] is True
        assert card["double_confirmation_required"] is True or card["triple_confirmation_required"] is True
        assert card["rollback_required"] is True
        assert card["stop_plan_required"] is True
        assert card["audit_required"] is True
        assert card["rollback_plan"] != "unknown"
        assert card["stop_plan"] != "unknown"


def test_mark_3_dashboard_status_forbidden_credentials_card_is_blocked():
    payload, _ = _payload()
    cards = {card["id"]: card for card in payload["approvals"]["cards"]}
    card = cards["preview-forbidden-credentials-bypass"]

    assert card["status"] in {"forbidden", "blocked"}
    assert card["risk_level"] == "forbidden"
    assert card["approval_level"] == "forbidden"
    assert "credentials" in card["touches"]
    assert card["preview_only"] is True
    assert card["read_only"] is True
    assert card["stop_plan_required"] is True


def test_mark_3_dashboard_status_keeps_finance_unknown_and_no_fake_metrics():
    payload, _ = _payload()
    finance = payload["finance"]

    assert finance["actual_cost"] == "unknown"
    assert finance["estimated_cost"] == "unknown"
    assert finance["confirmed_revenue"] == "unknown"
    assert finance["projected_revenue"] == "unknown"
    assert finance["roi"] == "unknown"
    assert finance["no_fake_metrics"] is True


def test_mark_3_dashboard_status_contains_finance_roi_truthful_unknown_contract():
    payload, _ = _payload()
    finance_roi = payload["finance_roi"]
    truth_policy = finance_roi["truth_policy"]
    metrics = finance_roi["metrics"]
    safety = finance_roi["safety"]

    assert truth_policy["no_fake_metrics"] is True
    assert truth_policy["unknown_when_no_evidence"] is True
    assert truth_policy["measured_requires_source"] is True
    assert truth_policy["estimated_requires_label"] is True
    assert truth_policy["confirmed_revenue_requires_evidence"] is True
    assert truth_policy["projected_revenue_must_be_labelled"] is True
    assert truth_policy["roi_unknown_without_revenue_and_cost"] is True

    for metric_name in (
        "actual_cost",
        "estimated_cost",
        "confirmed_revenue",
        "projected_revenue",
        "gross_revenue",
        "expenses",
        "net_revenue",
        "roi",
        "token_cost",
        "api_cost",
        "infra_cost",
        "manual_input_cost",
        "revenue_source",
    ):
        metric = metrics[metric_name]
        assert set(metric) == {"value", "label", "source", "evidence_state", "confidence", "last_updated"}
        assert metric["value"] == "unknown"
        assert metric["source"] == "not_measured"
        assert metric["evidence_state"] == "missing"
        assert metric["confidence"] == "unknown"

    assert metrics["roi"]["value"] == "unknown"
    assert metrics["confirmed_revenue"]["value"] == "unknown"
    assert metrics["confirmed_revenue"]["evidence_state"] == "missing"
    assert finance_roi["budget"]["budget_configured"] is False
    assert finance_roi["budget"]["remaining_budget"] == "unknown"
    assert finance_roi["budget"]["monthly_limit"] == "unknown"
    assert finance_roi["budget"]["alert_threshold"] == "unknown"
    assert finance_roi["budget"]["hard_stop_enabled"] is False

    for key in (
        "no_money_movement",
        "no_stripe_live",
        "no_checkout_creation",
        "no_invoice_creation",
        "no_payment_collection",
        "no_fake_revenue",
        "no_fake_costs",
        "no_fake_roi",
        "approval_required_for_money",
        "strong_approval_required_for_live_payments",
    ):
        assert safety[key] is True


def test_mark_3_dashboard_status_contains_adaptive_product_builder_preview_contract():
    payload, _ = _payload()
    builder = payload["adaptive_product_builder"]
    state = builder["state"]
    stages = builder["stages"]
    differentiation = builder["differentiation_policy"]
    monetization = builder["monetization_policy"]
    safety = builder["safety"]

    assert state["mode"] == "preview"
    assert state["builder_enabled"] == "preview/read_only"
    assert state["product_generation_enabled"] is False
    assert state["code_generation_enabled"] is False
    assert state["deploy_enabled"] is False
    assert state["stripe_enabled"] is False
    assert state["landing_publish_enabled"] is False
    assert state["external_research_enabled"] is False
    assert state["hermes_dispatch_enabled"] is False

    assert [stage["name"] for stage in stages] == [
        "Idea",
        "Validación",
        "Blueprint",
        "Código",
        "Landing",
        "Deploy candidate",
        "Monetización",
        "Medición",
    ]
    for stage in stages:
        assert stage["status"] in {"preview", "future_gated", "disabled", "unknown"}
        assert stage["can_execute"] is False
        assert isinstance(stage["requires_approval"], bool)
        assert stage["approval_level"]
        assert stage["evidence_required"]
        assert stage["notes"]

    assert differentiation["no_template_clone"] is True
    assert differentiation["adaptive_builder_not_template_builder"] is True
    assert differentiation["each_product_needs_reason_to_exist"] is True
    assert differentiation["each_product_needs_success_metric"] is True
    assert differentiation["each_product_needs_monetization_logic"] is True
    assert differentiation["cloned_products_are_failure"] is True

    assert monetization["pricing_preview_only"] is True
    assert monetization["stripe_live_requires_strong_approval"] is True
    assert monetization["checkout_requires_strong_approval"] is True
    assert monetization["real_revenue_requires_confirmation"] is True
    assert monetization["projected_revenue_label_required"] is True
    assert monetization["no_fake_revenue"] is True

    for key in (
        "no_deploy",
        "no_publish",
        "no_domain_change",
        "no_email_send",
        "no_money_movement",
        "no_credentials",
        "no_external_network",
        "no_hermes_dispatch",
        "approval_gates_required_for_real_actions",
    ):
        assert safety[key] is True


def test_mark_3_dashboard_status_contains_frontend_pilot_hardening_contract():
    payload, _ = _payload()
    pilot = payload["frontend_pilot"]
    state = pilot["state"]
    checks = {check["name"]: check for check in pilot["readiness_checks"]}
    hardening = pilot["hardening_notes"]
    limitations = pilot["pilot_limitations"]

    assert state["mode"] == "read_only_pilot"
    assert state["dashboard_route"] == "/jarvis"
    assert state["backend_status_endpoint"] == "/mark-3/dashboard/status"
    assert state["frontend_can_execute"] is False
    assert state["frontend_can_approve"] is False
    assert state["frontend_can_activate_sensors"] is False
    assert state["frontend_can_move_money"] is False
    assert state["frontend_can_deploy"] is False
    assert state["frontend_can_send_email"] is False

    for name in (
        "dashboard_route_exists",
        "read_model_connected",
        "approval_console_visible",
        "hermes_execution_visible",
        "mission_control_visible",
        "voice_core_visible",
        "wake_flow_visible",
        "camera_vision_visible",
        "mobile_companion_visible",
        "finance_roi_visible",
        "product_builder_visible",
        "kill_switch_visible",
        "no_fake_metrics",
        "no_frontend_execute",
        "no_sensor_activation",
        "no_post_put_delete",
    ):
        assert name in checks
        assert checks[name]["status"] in {"passed", "preview", "unknown", "failed"}
        assert checks[name]["evidence"]
        assert checks[name]["notes"]

    assert hardening["npm_audit_fix_not_run"] is True
    assert hardening["dependency_hardening_requires_separate_pr"] is True
    assert hardening["no_lockfile_changes_expected"] is True
    assert hardening["frontend_build_required_before_merge"] is True
    assert hardening["full_pytest_required_before_merge"] is True

    for limitation in (
        "no real approvals",
        "no real mission submit",
        "no real Hermes execution",
        "no real voice",
        "no real camera",
        "no real mobile runtime",
        "no real finance/revenue measurement",
        "no deploy/money/email/credentials",
    ):
        assert limitation in limitations


def test_mark_3_dashboard_status_declares_safety_boundaries():
    payload, _ = _payload()
    safety = payload["safety"]
    hermes_safety = payload["hermes_execution"]["safety"]

    assert safety["frontend_can_execute"] is False
    assert safety["frontend_can_approve"] is False
    assert safety["no_frontend_execute"] is True
    assert safety["no_duplicate_hermes_runtime"] is True
    assert safety["no_get_user_media"] is True
    assert safety["no_sensor_activation"] is True
    assert safety["no_frontend_tool_runner"] is True
    assert safety["no_direct_hermes_call_from_mobile"] is True
    assert safety["no_direct_hermes_call_from_voice"] is True
    assert safety["no_direct_hermes_call_from_camera"] is True
    assert safety["no_frontend_hermes_execution"] is True
    assert safety["no_post_put_delete_from_jarvis_page"] is True
    assert safety["approval_required_before_execution"] is True
    assert safety["wake_phrase_is_not_permission"] is True
    assert safety["audit_required"] is True
    assert safety["rollback_or_stop_plan_required_for_sensitive_actions"] is True
    assert safety["no_money_movement"] is True
    assert safety["no_deploy"] is True
    assert safety["no_credentials"] is True
    assert safety["no_email_send"] is True

    assert hermes_safety["approval_required_before_execution"] is True
    assert hermes_safety["audit_required"] is True
    assert hermes_safety["rollback_or_stop_plan_required_for_sensitive_actions"] is True
    assert hermes_safety["no_frontend_execute"] is True
    assert hermes_safety["no_frontend_tool_runner"] is True


def test_mark_3_dashboard_status_adds_no_dangerous_action_routes():
    app = _app()
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }

    assert ("/mark-3/dashboard/status", "GET") in routes
    for forbidden in (
        ("/mark-3/dashboard/status", "POST"),
        ("/jarvis/dashboard/status", "POST"),
        ("/jarvis/execute", "POST"),
        ("/jarvis/approve", "POST"),
        ("/jarvis/hermes/execute", "POST"),
        ("/mark-3/dashboard/execute", "POST"),
        ("/mark-3/dashboard/approve", "POST"),
        ("/mark-3/dashboard/reject", "POST"),
        ("/execute", "POST"),
        ("/hermes/execute", "POST"),
        ("/mark-3/hermes/execute", "POST"),
        ("/mark-3/dashboard/tool-runner", "POST"),
        ("/mark-3/dashboard/deploy", "POST"),
        ("/mark-3/dashboard/money", "POST"),
        ("/mark-3/dashboard/email", "POST"),
        ("/mark-3/dashboard/credentials", "POST"),
        ("/mark-3/dashboard/sensors", "POST"),
        ("/mark-3/dashboard/voice/start", "POST"),
        ("/mark-3/dashboard/voice/record", "POST"),
        ("/mark-3/dashboard/tts", "POST"),
        ("/mark-3/dashboard/stt", "POST"),
        ("/mark-3/dashboard/mission-control", "POST"),
        ("/mark-3/mission-control/submit", "POST"),
        ("/mark-3/mission-control/execute", "POST"),
        ("/jarvis/mission-control/submit", "POST"),
        ("/jarvis/mission-control/execute", "POST"),
        ("/voice-core/start", "POST"),
        ("/voice-core/record", "POST"),
        ("/wake-word/start", "POST"),
        ("/microphone/start", "POST"),
        ("/audio/record", "POST"),
    ):
        assert forbidden not in routes


def test_mark_3_dashboard_status_sources_are_declared_get_read_only_routes():
    payload, app = _payload()
    methods_by_path = {
        route.path: set(getattr(route, "methods", set()))
        for route in app.routes
    }
    source_endpoints = set(payload["release_candidate"]["source_endpoints"])
    source_endpoints.update(payload["voice_core"]["source_endpoints"])
    source_endpoints.update(payload["wake_word_flow"]["source_endpoints"])
    source_endpoints.update(payload["voice_wake"]["source_endpoints"])
    source_endpoints.update(payload["camera_vision"]["source_endpoints"])
    source_endpoints.update(payload["mobile_companion"]["source_endpoints"])
    source_endpoints.update(payload["mobile"]["source_endpoints"])
    source_endpoints.add(payload["approvals"]["source_endpoint"])
    source_endpoints.add(payload["camera_vision"]["source_endpoint"])
    source_endpoints.add(payload["hermes_execution"]["source_endpoint"])
    source_endpoints.add(payload["system"]["source_endpoint"])

    for endpoint in source_endpoints:
        assert endpoint in methods_by_path
        assert methods_by_path[endpoint] == {"GET"}

    assert payload["read_only_contract"]["allowed_http_methods_for_frontend"] == ["GET"]
    assert payload["read_only_contract"]["internal_sources_are_read_only_status_or_audit"] is True


def test_mark_3_dashboard_status_does_not_call_execution_sensors_or_money(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("dashboard status must not call active execution, sensors, or money adapters")

    monkeypatch.setattr("jarvis.runtime.hermes_adapter.HermesRuntimeAdapter.run", fail)
    monkeypatch.setattr("jarvis.mark_3_hermes_runtime_bridge.Mark3HermesRuntimeBridge.execute_read", fail)
    monkeypatch.setattr("jarvis.mark_3_hermes_runtime_bridge.Mark3HermesRuntimeBridge.stop", fail)
    monkeypatch.setattr("jarvis.camera_control_runtime.CameraControlRuntime.preview_session", fail)
    monkeypatch.setattr("jarvis.wake_voice_runtime.WakeVoiceRuntime.parse", fail)
    monkeypatch.setattr("jarvis.mark_2_deploy_adapter.Mark2DeployAdapter.preview", fail)
    monkeypatch.setattr("jarvis.mark_2_stripe_adapter.Mark2StripeAdapter.preview", fail)
    monkeypatch.setattr("jarvis.mark_2_email_adapter.Mark2EmailAdapter.preview", fail)

    payload, _ = _payload()

    assert payload["source_status"]["e2e_smoke"]["would_execute"] is False
    assert payload["source_status"]["dangerous_route_audit"]["dangerous_routes_registered"] == []


def test_mark_3_dashboard_status_contains_visual_command_center_pilot_contract():
    payload, _ = _payload()
    pilot = payload["visual_command_center_pilot"]
    state = pilot["state"]
    safety = pilot["safety"]

    assert state["mode"] == "read_only_pilot"
    assert state["dashboard_route"] == "/jarvis"
    assert state["status_endpoint"] == "/mark-3/dashboard/status"
    assert state["backend_read_model_connected"] is True
    assert state["frontend_execution_enabled"] is False
    assert state["approvals_real_enabled"] is False
    assert state["hermes_direct_execution_enabled"] is False
    assert state["voice_real_enabled"] is False
    assert state["camera_real_enabled"] is False
    assert state["mobile_runtime_enabled"] is False
    assert state["money_enabled"] is False
    assert state["deploy_enabled"] is False
    assert state["email_enabled"] is False
    assert state["credentials_enabled"] is False

    assert safety["pilot_is_read_only"] is True
    assert safety["dashboard_may_read_status_only"] is True
    assert safety["no_side_effects"] is True
    assert safety["no_real_world_actions"] is True
    assert safety["no_background_workers"] is True
    assert safety["no_sensors"] is True
    assert safety["no_money"] is True
    assert safety["no_production"] is True
    assert safety["no_credentials"] is True
    assert safety["restrictions_are_approval_gates_not_permanent_bans"] is True


def test_mark_3_dashboard_status_visual_command_center_pilot_required_panels_are_non_executable():
    payload, _ = _payload()
    panels = {item["name"]: item for item in payload["visual_command_center_pilot"]["required_panels"]}

    expected = {
        "Header",
        "Voice Core",
        "Wake Word Local Safe Flow",
        "Mission Control",
        "Approval Console",
        "Hermes Execution",
        "Agent / Module Radar",
        "Camera / Vision",
        "Mobile Companion",
        "Finance / ROI",
        "Product Builder Adaptativo",
        "Frontend Pilot / Hardening",
        "Live Timeline / Audit",
        "Kill Switch",
    }
    assert set(panels) == expected

    for panel in panels.values():
        assert panel["expected"] is True
        assert panel["source"]
        assert panel["status"] in {"ready", "preview", "disabled", "unknown"}
        assert panel["can_execute"] is False
        assert panel["notes"]


def test_mark_3_dashboard_status_visual_command_center_pilot_read_only_checks_and_findings():
    payload, _ = _payload()
    pilot = payload["visual_command_center_pilot"]
    checks = {item["name"]: item for item in pilot["read_only_checks"]}

    for name in (
        "no_post_put_delete",
        "no_execute_route",
        "no_get_user_media",
        "no_money_movement",
        "no_fake_metrics",
    ):
        assert name in checks
        assert checks[name]["status"] in {"passed", "preview", "unknown"}
        assert checks[name]["evidence"]
        assert checks[name]["notes"]

    for name in (
        "no_frontend_hermes_call",
        "no_tool_runner",
        "no_sensor_activation",
        "no_media_recorder",
        "no_audio_context_capture",
        "no_camera_capture",
        "no_mobile_runtime",
        "no_stripe_live",
        "no_deploy",
        "no_email_send",
        "no_credentials",
    ):
        assert name in checks

    assert pilot["pilot_findings"]["findings"] == []
    assert "real approvals not wired" in pilot["pilot_findings"]["known_limitations"]
    assert "dependency hardening may need separate PR due npm audit vulnerabilities" in pilot["pilot_findings"]["known_limitations"]


def test_mark_3_dashboard_status_visual_command_center_pilot_timeline_does_not_invent_execution():
    payload, _ = _payload()
    timeline = payload["visual_command_center_pilot"]["timeline"]
    events = [item["event"] for item in timeline]

    for event in (
        "Visual Command Center pilot status read",
        "Dashboard route checked",
        "Dashboard read model checked",
        "Read-only safety checks loaded",
        "No execution performed",
    ):
        assert event in events

    assert all(item["read_only"] is True for item in timeline)
    serialized = " ".join(event.lower() for event in events)
    for forbidden in (
        "browser opened",
        "david tested",
        "manual pilot completed",
        "hermes executed",
        "camera started",
        "microphone started",
        "money moved",
        "deploy completed",
        "email sent",
    ):
        assert forbidden not in serialized


def test_mark_3_dashboard_status_timeline_contains_only_read_model_events():
    payload, _ = _payload()
    events = payload["timeline"]

    assert any(item["event"] == "backend status read" for item in events)
    assert any(item["event"] == "release candidate status read" for item in events)
    assert any(item["event"] == "readiness read" for item in events)
    assert any(item["event"] == "dangerous route audit read" for item in events)
    assert any(item["event"] == "Hermes execution visibility read" for item in events)
    assert any(item["event"] == "No active Hermes execution" for item in events)
    assert any(item["event"] == "Frontend direct execution disabled" for item in events)
    assert any(item["event"] == "Approval gates required before Hermes execution" for item in events)
    assert any(item["event"] == "Mission Control preview read" for item in events)
    assert any(item["event"] == "Conversation preview read" for item in events)
    assert any(item["event"] == "No command execution performed" for item in events)
    assert any(item["event"] == "Hermes dispatch disabled from Mission Control" for item in events)
    assert any(item["event"] == "Voice Core visual state read" for item in events)
    assert any(item["event"] == "Voice/TTS state preview generated" for item in events)
    assert any(item["event"] == "Microphone disabled" for item in events)
    assert any(item["event"] == "Wake word runtime not active" for item in events)
    assert any(item["event"] == "No audio recording performed" for item in events)
    assert any(item["event"] == "Wake word flow preview read" for item in events)
    assert any(item["event"] == "Microphone hard-off confirmed" for item in events)
    assert any(item["event"] == "Typed wake preview available" for item in events)
    assert any(item["event"] == "Wake phrase cannot approve" for item in events)
    assert any(item["event"] == "Wake phrase cannot execute" for item in events)
    assert any(item["event"] == "No background listener started" for item in events)
    assert any(item["event"] == "Camera/Vision privacy status read" for item in events)
    assert any(item["event"] == "Camera disabled" for item in events)
    assert any(item["event"] == "Recording disabled" for item in events)
    assert any(item["event"] == "Vision analysis disabled" for item in events)
    assert any(item["event"] == "No image or video captured" for item in events)
    assert any(item["event"] == "No external vision provider called" for item in events)
    assert any(item["event"] == "Mobile Companion preview read" for item in events)
    assert any(item["event"] == "Mobile is interface, not runtime" for item in events)
    assert any(item["event"] == "Mobile direct Hermes call disabled" for item in events)
    assert any(item["event"] == "Real mobile approvals disabled" for item in events)
    assert any(item["event"] == "Remote kill switch future gated" for item in events)
    assert any(item["event"] == "Finance/ROI panel read" for item in events)
    assert any(item["event"] == "Metrics defaulted to unknown without evidence" for item in events)
    assert any(item["event"] == "No money movement performed" for item in events)
    assert any(item["event"] == "No Stripe live action performed" for item in events)
    assert any(item["event"] == "No fake ROI generated" for item in events)
    assert any(item["event"] == "Product Builder panel read" for item in events)
    assert any(item["event"] == "Product stages loaded as preview" for item in events)
    assert any(item["event"] == "No product generated" for item in events)
    assert any(item["event"] == "No deploy candidate executed" for item in events)
    assert any(item["event"] == "No monetization action performed" for item in events)
    assert any(item["event"] == "Frontend pilot status read" for item in events)
    assert any(item["event"] == "Dashboard route expected at /jarvis" for item in events)
    assert any(item["event"] == "Read model expected at /mark-3/dashboard/status" for item in events)
    assert any(item["event"] == "Pilot remains read-only" for item in events)
    assert any(item["event"] == "Dependency hardening deferred to separate PR if needed" for item in events)
    assert any(item["event"] == "Visual Command Center pilot status read" for item in events)
    assert any(item["event"] == "Dashboard route checked" for item in events)
    assert any(item["event"] == "Dashboard read model checked" for item in events)
    assert any(item["event"] == "Read-only safety checks loaded" for item in events)
    assert any(item["event"] == "No execution performed" for item in events)
    assert any(item["event"] == "dashboard read model generated" for item in events)
    assert all(item["read_only"] is True for item in events)

    serialized = " ".join(item["event"].lower() for item in events)
    for forbidden in (
        "money movement completed",
        "stripe live action completed",
        "fake roi generated successfully",
        "product generated successfully",
        "deploy candidate completed",
        "monetization action completed",
        "frontend executed",
        "hermes executed from frontend",
    ):
        assert forbidden not in serialized
    assert not any("microphone started" in item["event"].lower() for item in events)
    assert not any(item["event"].lower() == "background listener started" for item in events)
    assert not any("wake word detected" in item["event"].lower() for item in events)
    assert not any("audio recorded" in item["event"].lower() for item in events)
    assert not any("tts played" in item["event"].lower() for item in events)
    assert not any("spoken conversation" in item["event"].lower() for item in events)
    assert not any("camera started" in item["event"].lower() for item in events)
    assert not any("stream started" in item["event"].lower() for item in events)
    assert not any("image stored" in item["event"].lower() for item in events)
    assert not any("video recorded" in item["event"].lower() for item in events)
    assert not any("mobile runtime started" in item["event"].lower() for item in events)
    assert not any("mobile approval approved" in item["event"].lower() for item in events)
    assert not any("mobile approval rejected" in item["event"].lower() for item in events)
