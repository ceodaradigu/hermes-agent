import pytest

from jarvis.missions.envelope import (
    ActionClassification,
    MissionEnvelope,
    classify_action,
    validate_mission_envelope,
)


def _valid_envelope(**overrides):
    data = {
        "mission_id": "mission-1",
        "objective": "Crear una landing revisable para validar un nicho",
        "success_metric": "Landing draft y tres variantes comparadas",
        "deadline": "2026-06-15",
        "budget_limit": 50.0,
        "cost_limit_per_action": 10.0,
        "allowed_actions": ["research", "draft"],
        "requires_approval_actions": ["file_write"],
        "strong_approval_actions": ["deploy"],
        "denied_actions": ["spam"],
        "allowed_tools": ["approved_local_editor"],
        "candidate_tools": ["Open Design"],
        "channels": ["local", "docs"],
        "stop_conditions": ["approval_needed"],
        "audit_requirements": ["objective", "actions", "approvals"],
        "net_target": "1000 EUR",
        "reporting_frequency": "daily_or_on_blocker",
        "data_access_scope": ["project_docs"],
        "identity_use_policy": "draft_only",
        "publication_policy": "prepare_only",
        "spending_policy": "no_spend",
        "external_contact_policy": "prepare_only",
        "install_dependency_policy": "propose_only",
        "runtime_execution_policy": "no_daemon_no_docker_no_ports",
        "rollback_plan": "revert generated files",
    }
    data.update(overrides)
    return MissionEnvelope(**data)


def _errors_for(envelope):
    return validate_mission_envelope(envelope).errors


def test_valid_envelope_passes_validation():
    result = validate_mission_envelope(_valid_envelope())

    assert result.is_valid
    assert result.errors == []


@pytest.mark.parametrize(
    ("field_name", "message"),
    [
        ("mission_id", "mission_id must be a non-empty string"),
        ("objective", "objective must be a non-empty string"),
        ("success_metric", "success_metric must be a non-empty string"),
    ],
)
def test_required_text_fields_reject_empty_strings(field_name, message):
    envelope = _valid_envelope(**{field_name: "   "})

    assert message in _errors_for(envelope)


def test_negative_budget_is_rejected():
    envelope = _valid_envelope(budget_limit=-1)

    assert "budget_limit cannot be negative" in _errors_for(envelope)


def test_negative_cost_limit_per_action_is_rejected():
    envelope = _valid_envelope(cost_limit_per_action=-1)

    assert "cost_limit_per_action cannot be negative" in _errors_for(envelope)


def test_cost_limit_per_action_cannot_exceed_budget_limit():
    envelope = _valid_envelope(budget_limit=10, cost_limit_per_action=11)

    assert "cost_limit_per_action cannot exceed budget_limit" in _errors_for(envelope)


def test_repeated_action_between_allowed_and_denied_is_rejected():
    envelope = _valid_envelope(allowed_actions=["research"], denied_actions=["research"])

    assert "action 'research' appears in both allowed_actions and denied_actions" in _errors_for(envelope)


def test_denied_wins_when_classifying_overlapping_action():
    envelope = _valid_envelope(allowed_actions=["publish"], denied_actions=["publish"])

    assert classify_action(envelope, "publish") == ActionClassification.DENIED


def test_candidate_tools_are_not_allowed_tools():
    envelope = _valid_envelope(allowed_tools=["Open Design"], candidate_tools=["Open Design"])

    errors = _errors_for(envelope)
    assert any("candidate_tools are proposals only" in error for error in errors)


def test_blanket_approval_action_is_rejected():
    envelope = _valid_envelope(allowed_actions=["approve_all_forever"])

    errors = _errors_for(envelope)
    assert any("vague blanket approval" in error for error in errors)


def test_blanket_approval_policy_is_rejected():
    envelope = _valid_envelope(runtime_execution_policy="whatever_it_takes")

    assert "runtime_execution_policy cannot grant vague blanket approval" in _errors_for(envelope)


def test_requires_at_least_one_basic_control_signal():
    envelope = _valid_envelope(deadline=None, budget_limit=None, stop_conditions=[])

    assert "mission envelope must include deadline, budget_limit, or stop_conditions" in _errors_for(envelope)


def test_action_lists_reject_empty_strings():
    envelope = _valid_envelope(strong_approval_actions=["deploy", "  "])

    assert "strong_approval_actions cannot contain empty strings" in _errors_for(envelope)


def test_to_dict_from_dict_preserves_main_fields():
    original = _valid_envelope()

    restored = MissionEnvelope.from_dict(original.to_dict())

    assert restored.mission_id == original.mission_id
    assert restored.objective == original.objective
    assert restored.success_metric == original.success_metric
    assert restored.allowed_actions == original.allowed_actions
    assert restored.candidate_tools == original.candidate_tools
    assert restored.rollback_plan == original.rollback_plan


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("research", ActionClassification.ALLOWED),
        ("file_write", ActionClassification.REQUIRES_APPROVAL),
        ("deploy", ActionClassification.STRONG_APPROVAL),
        ("spam", ActionClassification.DENIED),
        ("unexpected_action", ActionClassification.UNKNOWN_REQUIRES_REVIEW),
    ],
)
def test_classify_action(action, expected):
    assert classify_action(_valid_envelope(), action) == expected
