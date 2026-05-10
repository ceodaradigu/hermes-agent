from jarvis.voice import UserUnderstandingProfile, VoiceIntentRouter


def _classify(text: str):
    return VoiceIntentRouter().classify(text)


def test_landing_request_classifies_as_create_asset():
    intent = _classify("crea una landing para una herramienta de afiliados")

    assert intent.intent == "create_asset"
    assert intent.status == "pending"
    assert intent.executed is False
    assert intent.confidence == "high"
    assert intent.needs_clarification is False
    assert intent.slots["asset_type"] == "landing"
    assert intent.inferred_goal == "monetization_or_affiliate_asset"
    assert intent.user_context_signals["business_or_monetization"] is True
    assert intent.recommended_next_step
    assert intent.approval_required is False


def test_web_request_classifies_as_create_asset():
    intent = _classify("hazme una web de afiliados")

    assert intent.intent == "create_asset"
    assert intent.status == "pending"
    assert intent.slots["asset_type"] == "website"


def test_ambiguous_niche_request_has_clear_reason_or_clarification():
    intent = _classify("monta algo para probar este nicho")

    assert intent.intent in {"create_asset", "create_mission"}
    assert intent.needs_clarification or "Matched" in intent.reason
    assert intent.executed is False
    assert intent.confidence in {"high", "medium"}
    assert intent.user_context_signals["business_or_monetization"] is True


def test_task_request_classifies_as_create_task():
    intent = _classify("crea una tarea para revisar el logo")

    assert intent.intent == "create_task"
    assert intent.status == "pending"
    assert intent.executed is False


def test_mission_request_classifies_as_create_mission():
    intent = _classify("crea una misión para investigar nichos")

    assert intent.intent == "create_mission"
    assert intent.status == "pending"
    assert intent.executed is False


def test_status_request_classifies_as_query_status():
    intent = _classify("resume mis tareas")

    assert intent.intent == "query_status"
    assert intent.status == "pending"
    assert intent.executed is False


def test_env_request_requires_approval():
    intent = _classify("lee mi .env")

    assert intent.intent == "requires_approval"
    assert intent.status == "requires_approval"
    assert intent.executed is False
    assert ".env" in intent.slots["sensitive_terms"]
    assert intent.approval_required is True
    assert intent.recommended_next_step == "Route through ApprovalGateway before any execution."


def test_delete_request_requires_approval():
    intent = _classify("borra el proyecto X")

    assert intent.intent == "requires_approval"
    assert intent.status == "requires_approval"
    assert intent.executed is False
    assert "borra" in intent.slots["sensitive_terms"]
    assert intent.approval_required is True


def test_frustrated_tone():
    intent = _classify("esto no funciona otra vez")

    assert intent.tone == "frustrated"


def test_urgent_tone():
    intent = _classify("hazlo ya")

    assert intent.tone == "urgent"
    assert intent.executed is False
    assert intent.user_context_signals["contrarian_review_recommended"] is True


def test_exploratory_tone():
    intent = _classify("quizá podríamos probar una idea")

    assert intent.tone == "exploratory"


def test_unsupported_text_needs_clarification_and_does_not_execute():
    intent = _classify("blu blu cosa rara")

    assert intent.intent == "unsupported"
    assert intent.status == "unsupported"
    assert intent.executed is False
    assert intent.needs_clarification is True
    assert intent.confidence == "low"


def test_default_understanding_profile_prefers_david():
    profile = UserUnderstandingProfile()

    assert profile.preferred_name == "David"


def test_default_understanding_profile_includes_generic_monetization_goals():
    profile = UserUnderstandingProfile()

    assert "crear activos digitales" in profile.business_goals
    assert "afiliación" in profile.monetization_preferences
    assert "micro saas" in profile.monetization_preferences


def test_result_has_future_learning_fields():
    intent = _classify("crea una landing para afiliados")

    assert intent.inferred_goal
    assert isinstance(intent.user_context_signals, dict)
    assert intent.recommended_next_step
    assert intent.approval_required is False
    assert intent.executed is False


def test_executed_false_for_all_basic_intent_types():
    texts = [
        "crea una landing para afiliados",
        "crea una tarea para revisar el logo",
        "crea una misión para investigar nichos",
        "resume mis tareas",
        "lee mi .env",
        "hola jarvis",
        "texto raro sin sentido",
    ]

    assert all(_classify(text).executed is False for text in texts)
