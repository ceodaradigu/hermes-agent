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
