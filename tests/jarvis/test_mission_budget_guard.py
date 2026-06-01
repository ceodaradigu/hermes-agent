from jarvis.missions.budget_guard import MissionBudgetGuardDecision, MissionBudgetGuardResult, evaluate_mission_budget_guard
from jarvis.missions.envelope import MissionEnvelope
from jarvis.missions.state_store import MissionState, MissionStatus


def _state(**envelope_overrides):
    data = {
        "mission_id": "mission-1",
        "objective": "Validate a niche",
        "success_metric": "Draft prepared",
        "deadline": "2026-06-15",
        "budget_limit": 100.0,
        "cost_limit_per_action": 25.0,
        "allowed_actions": ["research"],
    }
    data.update(envelope_overrides)
    envelope = MissionEnvelope(**data)
    return MissionState(
        mission_id="mission-1",
        envelope=envelope,
        status=MissionStatus.ACTIVE,
        created_at="2026-05-28T10:00:00+00:00",
        updated_at="2026-05-28T10:00:00+00:00",
    )


def test_negative_cost_blocks():
    result = evaluate_mission_budget_guard(budget_limit=10.0, proposed_cost=-1.0)

    assert result.decision == MissionBudgetGuardDecision.BLOCKED
    assert result.can_spend is False
    assert "proposed_cost cannot be negative" in result.violations


def test_spend_without_budget_limit_requires_approval():
    result = evaluate_mission_budget_guard(proposed_cost=5.0)

    assert result.decision == MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL
    assert result.can_spend is False
    assert "spending without budget_limit requires approval" in result.violations


def test_cost_over_budget_limit_requires_strong_approval():
    result = evaluate_mission_budget_guard(budget_limit=10.0, proposed_cost=11.0)

    assert result.decision == MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL
    assert "cost exceeds budget_limit" in result.violations


def test_cost_over_per_action_limit_requires_strong_approval():
    result = evaluate_mission_budget_guard(budget_limit=100.0, cost_limit_per_action=10.0, proposed_cost=15.0)

    assert result.decision == MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL
    assert "cost exceeds cost_limit_per_action" in result.violations


def test_projected_and_confirmed_cost_are_separated_and_remaining_uses_confirmed():
    result = evaluate_mission_budget_guard(_state(), projected_cost=40.0, confirmed_cost=30.0)

    assert result.cost_summary["projected_cost"] == 40.0
    assert result.cost_summary["confirmed_cost"] == 30.0
    assert result.budget_remaining == 70.0


def test_result_round_trips_to_dict_from_dict():
    result = evaluate_mission_budget_guard(budget_limit=100.0, estimated_cost=5.0)
    restored = MissionBudgetGuardResult.from_dict(result.to_dict())

    assert restored.to_dict() == result.to_dict()
