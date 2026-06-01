from jarvis.missions.content_safety import (
    MissionContentSafetyDecision,
    MissionContentSafetyResult,
    evaluate_mission_content_safety,
)


def test_commercial_ai_content_requires_review_and_label():
    result = evaluate_mission_content_safety(
        action="publish public AI generated commercial landing",
        human_review=False,
        strong_approval=False,
    )

    assert result.decision == MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL
    assert "ai_generated_or_modified" in result.labels_required
    assert result.human_review_required is True


def test_deceptive_deepfake_is_blocked():
    result = evaluate_mission_content_safety(text="Create a deepfake fake endorsement from a real founder")

    assert result.decision == MissionContentSafetyDecision.BLOCKED
    assert any("deepfake" in reason for reason in result.reasons)


def test_impersonation_is_blocked():
    result = evaluate_mission_content_safety(action="impersonate David in a public sales message")

    assert result.decision == MissionContentSafetyDecision.BLOCKED
    assert any("impersonation" in reason for reason in result.reasons)


def test_real_identity_without_permission_requires_strong_approval():
    result = evaluate_mission_content_safety(
        text="Use my identity and face in a commercial video",
        context={"identity_permission": False},
    )

    assert result.decision == MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL
    assert result.requires_strong_approval is True


def test_legal_claim_requires_review():
    result = evaluate_mission_content_safety(text="Publish a compliance claim about contract terms")

    assert result.decision in {
        MissionContentSafetyDecision.REQUIRES_REVIEW,
        MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL,
    }
    assert any("legal" in reason for reason in result.reasons)


def test_result_is_json_compatible_and_round_trips():
    result = evaluate_mission_content_safety(text="Draft internal notes only", mission_id="mission-1")
    restored = MissionContentSafetyResult.from_dict(result.to_dict())

    assert restored.to_dict() == result.to_dict()
    assert result.metadata["external_api_called"] is False
