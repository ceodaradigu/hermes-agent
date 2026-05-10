from __future__ import annotations

from dataclasses import asdict, dataclass

from jarvis.voice.intent_router import UserUnderstandingProfile
from jarvis.voice.understanding_feedback import UserUnderstandingFeedback


@dataclass
class UserUnderstandingFeedbackPreview:
    original_text: str
    corrected_intent: str
    suggested_alias: str | None
    suggested_profile_area: str
    risk_level: str
    requires_review: bool
    applied: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def preview_user_understanding_feedback(
    feedback: UserUnderstandingFeedback,
) -> UserUnderstandingFeedbackPreview:
    """Build a non-persistent preview of possible future profile learning."""
    profile = UserUnderstandingProfile()
    original_text = feedback.original_text
    normalized_text = _normalize(original_text)
    suggested_alias = _suggest_alias(normalized_text)
    risk_level = _risk_level(feedback, profile)
    suggested_profile_area = _suggest_profile_area(feedback, normalized_text, profile, risk_level)

    if feedback.interpreted_intent and feedback.interpreted_intent != feedback.corrected_intent:
        reason = (
            f"Feedback suggests mapping '{suggested_alias or normalized_text}' "
            f"from {feedback.interpreted_intent} to {feedback.corrected_intent}."
        )
    else:
        reason = (
            f"Feedback suggests reviewing whether '{suggested_alias or normalized_text}' "
            f"belongs under {feedback.corrected_intent}."
        )

    if risk_level == "high":
        reason += " Sensitive wording or target intent keeps this as review-only."

    return UserUnderstandingFeedbackPreview(
        original_text=original_text,
        corrected_intent=feedback.corrected_intent,
        suggested_alias=suggested_alias,
        suggested_profile_area=suggested_profile_area,
        risk_level=risk_level,
        requires_review=True,
        applied=False,
        reason=reason,
    )


def create_feedback_preview(feedback: UserUnderstandingFeedback) -> UserUnderstandingFeedbackPreview:
    return preview_user_understanding_feedback(feedback)


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _suggest_alias(normalized_text: str) -> str | None:
    if not normalized_text:
        return None

    for marker in (" para ", " sobre ", " de "):
        if marker in normalized_text:
            candidate = normalized_text.split(marker, 1)[1].strip()
            if candidate:
                return candidate

    prefixes = (
        "crea una ",
        "crea un ",
        "crear una ",
        "crear un ",
        "hazme una ",
        "hazme un ",
        "haz una ",
        "haz un ",
        "monta algo ",
        "monta una ",
        "monta un ",
        "prepara una ",
        "prepara un ",
    )
    for prefix in prefixes:
        if normalized_text.startswith(prefix):
            return normalized_text.removeprefix(prefix).strip() or None

    return normalized_text


def _risk_level(feedback: UserUnderstandingFeedback, profile: UserUnderstandingProfile) -> str:
    searchable_text = " ".join(
        value
        for value in (
            feedback.original_text,
            feedback.corrected_intent,
            feedback.correction_note or "",
            feedback.preferred_next_step or "",
        )
        if value
    ).lower()

    if feedback.corrected_intent == "requires_approval":
        return "high"
    if any(term in searchable_text for term in profile.sensitive_words):
        return "high"
    if feedback.confidence_before == "low" or not feedback.interpreted_intent:
        return "medium"
    if feedback.interpreted_intent != feedback.corrected_intent:
        return "medium"
    return "low"


def _suggest_profile_area(
    feedback: UserUnderstandingFeedback,
    normalized_text: str,
    profile: UserUnderstandingProfile,
    risk_level: str,
) -> str:
    if risk_level == "high":
        return "sensitive_boundaries"
    if feedback.interpreted_intent != feedback.corrected_intent:
        return "intent_aliases"
    if any(term in normalized_text for term in profile.common_phrases):
        return "common_phrases"
    return "learning_notes"
