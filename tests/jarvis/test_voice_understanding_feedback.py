from jarvis.voice import UserUnderstandingFeedbackStore


def test_feedback_store_starts_empty():
    store = UserUnderstandingFeedbackStore()

    assert store.count() == 0
    assert store.list_feedback() == []


def test_add_feedback_increments_count():
    store = UserUnderstandingFeedbackStore()

    feedback = store.add_feedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    assert store.count() == 1
    assert feedback.applied_persistently is False
    assert feedback.requires_review is True


def test_list_feedback_returns_feedback():
    store = UserUnderstandingFeedbackStore()
    feedback = store.add_feedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
        correction_note="Primero quiero validar.",
        preferred_next_step="Crear misión de validación.",
    )

    assert store.list_feedback() == [feedback]
    assert store.list_feedback()[0].correction_note == "Primero quiero validar."


def test_clear_removes_feedback():
    store = UserUnderstandingFeedbackStore()
    store.add_feedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    store.clear()

    assert store.count() == 0
    assert store.list_feedback() == []


def test_feedback_defaults_are_safe_and_non_persistent():
    store = UserUnderstandingFeedbackStore()

    feedback = store.add_feedback(original_text="x", corrected_intent="create_task")

    assert feedback.source == "user"
    assert feedback.applied_persistently is False
    assert feedback.requires_review is True
