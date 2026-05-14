from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class UserUnderstandingFeedback:
    original_text: str
    interpreted_intent: str | None
    corrected_intent: str
    correction_note: str | None = None
    preferred_next_step: str | None = None
    confidence_before: str | None = None
    source: str = "user"
    applied_persistently: bool = False
    requires_review: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UserUnderstandingAppliedFeedbackRule:
    original_text: str
    corrected_intent: str
    suggested_alias: str | None
    reason: str
    source: str = "user_reviewed_feedback"
    applied_persistently: bool = False
    requires_review: bool = False
    approval_required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class UserUnderstandingFeedbackStore:
    """In-memory feedback buffer for future user-understanding learning.

    This store intentionally does not persist to disk, read files, use a
    database, or apply feedback to the intent router.
    """

    def __init__(self) -> None:
        self._items: list[UserUnderstandingFeedback] = []

    def add_feedback(
        self,
        *,
        original_text: str,
        corrected_intent: str,
        interpreted_intent: str | None = None,
        correction_note: str | None = None,
        preferred_next_step: str | None = None,
        confidence_before: str | None = None,
        source: str = "user",
    ) -> UserUnderstandingFeedback:
        feedback = UserUnderstandingFeedback(
            original_text=original_text,
            interpreted_intent=interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=correction_note,
            preferred_next_step=preferred_next_step,
            confidence_before=confidence_before,
            source=source,
            applied_persistently=False,
            requires_review=True,
        )
        self._items.append(feedback)
        return feedback

    def list_feedback(self) -> list[UserUnderstandingFeedback]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()

    def count(self) -> int:
        return len(self._items)


class UserUnderstandingAppliedFeedbackStore:
    """In-memory rules explicitly applied from reviewed feedback.

    Rules are intentionally process-local and do not read or write files,
    databases, external APIs, or persistent memory.
    """

    def __init__(self) -> None:
        self._rules: list[UserUnderstandingAppliedFeedbackRule] = []

    def apply_feedback(self, feedback: UserUnderstandingFeedback) -> UserUnderstandingAppliedFeedbackRule:
        from jarvis.voice.feedback_preview import preview_user_understanding_feedback

        preview = preview_user_understanding_feedback(feedback)
        normalized_original = self._normalize(feedback.original_text)
        suggested_alias = self._normalize(preview.suggested_alias or "") or None
        rule = UserUnderstandingAppliedFeedbackRule(
            original_text=feedback.original_text,
            corrected_intent=feedback.corrected_intent,
            suggested_alias=suggested_alias,
            reason=(
                "Applied temporary reviewed feedback rule from David: "
                f"{preview.reason}"
            ),
            source="user_reviewed_feedback",
            applied_persistently=False,
            requires_review=False,
            approval_required=False,
        )
        if not rule.suggested_alias and normalized_original:
            rule.suggested_alias = normalized_original
        self._rules.append(rule)
        return rule

    def list_rules(self) -> list[UserUnderstandingAppliedFeedbackRule]:
        return list(self._rules)

    def clear(self) -> None:
        self._rules.clear()

    def count(self) -> int:
        return len(self._rules)

    def find_matching_intent(self, text: str) -> UserUnderstandingAppliedFeedbackRule | None:
        normalized_text = self._normalize(text)
        if not normalized_text:
            return None

        for rule in reversed(self._rules):
            candidates = (
                self._normalize(rule.suggested_alias or ""),
                self._normalize(rule.original_text),
            )
            if any(candidate and candidate in normalized_text for candidate in candidates):
                return rule
        return None

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.strip().lower().split())
