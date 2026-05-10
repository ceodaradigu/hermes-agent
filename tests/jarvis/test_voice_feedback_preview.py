import json
from dataclasses import asdict

from jarvis.voice import (
    UserUnderstandingFeedback,
    UserUnderstandingProfile,
    VoiceIntentRouter,
    create_feedback_preview,
)


def test_preview_does_not_apply_feedback_automatically():
    feedback = UserUnderstandingFeedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    preview = create_feedback_preview(feedback)

    assert preview.applied is False
    assert feedback.applied_persistently is False


def test_preview_requires_review_by_default():
    feedback = UserUnderstandingFeedback(
        original_text="hazme una landing",
        interpreted_intent="create_asset",
        corrected_intent="create_asset",
    )

    preview = create_feedback_preview(feedback)

    assert preview.requires_review is True


def test_preview_does_not_change_original_feedback():
    feedback = UserUnderstandingFeedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
        correction_note="Primero quiero validar.",
    )
    before = feedback.to_dict()

    create_feedback_preview(feedback)

    assert feedback.to_dict() == before


def test_preview_detects_intent_alias_profile_area_and_alias():
    feedback = UserUnderstandingFeedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    preview = create_feedback_preview(feedback)

    assert preview.original_text == "monta algo para probar este nicho"
    assert preview.corrected_intent == "create_mission"
    assert preview.suggested_alias == "probar este nicho"
    assert preview.suggested_profile_area == "intent_aliases"


def test_sensitive_feedback_marks_high_risk_without_execution():
    feedback = UserUnderstandingFeedback(
        original_text="borra las credenciales antiguas",
        interpreted_intent="create_task",
        corrected_intent="requires_approval",
    )
    profile_before = asdict(UserUnderstandingProfile())
    intent_before = VoiceIntentRouter().classify("monta algo para probar este nicho").to_dict()

    preview = create_feedback_preview(feedback)

    intent_after = VoiceIntentRouter().classify("monta algo para probar este nicho").to_dict()
    profile_after = asdict(UserUnderstandingProfile())
    assert preview.risk_level == "high"
    assert preview.suggested_profile_area == "sensitive_boundaries"
    assert preview.applied is False
    assert intent_after == intent_before
    assert profile_after == profile_before


def test_preview_is_serializable():
    feedback = UserUnderstandingFeedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    preview = create_feedback_preview(feedback)
    payload = preview.to_dict()

    assert json.loads(json.dumps(payload)) == payload
