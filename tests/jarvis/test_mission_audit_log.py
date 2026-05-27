import pytest

from jarvis.missions.approval_request import MissionApprovalLevel, MissionApprovalRequest, build_approval_request
from jarvis.missions.audit_log import (
    MissionAuditEvent,
    MissionAuditEventType,
    MissionAuditOutcome,
    MissionAuditRiskLevel,
    build_audit_event,
    build_audit_event_from_approval_request,
    validate_audit_event,
)
from jarvis.missions.envelope import ActionClassification, MissionEnvelope


def _valid_event(**overrides):
    data = {
        "event_id": "audit-1",
        "mission_id": "mission-1",
        "event_type": MissionAuditEventType.MISSION_CREATED,
        "actor": "jarvis",
        "summary": "Mission envelope was created for review.",
        "created_at": "2026-05-27T10:00:00+00:00",
        "outcome": MissionAuditOutcome.RECORDED,
        "risk_level": MissionAuditRiskLevel.LOW,
        "metadata": {"source": "test"},
    }
    data.update(overrides)
    return MissionAuditEvent(**data)


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
        "rollback_plan": "revert generated files",
    }
    data.update(overrides)
    return MissionEnvelope(**data)


def test_valid_audit_event_passes_validation():
    event = _valid_event()

    result = validate_audit_event(event)

    assert result.is_valid
    assert result.errors == []


@pytest.mark.parametrize(
    ("field_name", "message"),
    [
        ("event_id", "event_id must be a non-empty string"),
        ("mission_id", "mission_id must be a non-empty string"),
        ("actor", "actor must be a non-empty string"),
        ("summary", "summary must be a non-empty string"),
    ],
)
def test_required_text_fields_reject_empty_strings(field_name, message):
    with pytest.raises(ValueError, match=message):
        _valid_event(**{field_name: "   "})


def test_rejects_invalid_event_type():
    with pytest.raises(ValueError, match="event_type must be a valid MissionAuditEventType"):
        _valid_event(event_type="not_real")


def test_rejects_invalid_outcome():
    with pytest.raises(ValueError, match="outcome must be a valid MissionAuditOutcome"):
        _valid_event(outcome="not_real")


def test_rejects_invalid_risk_level():
    with pytest.raises(ValueError, match="risk_level must be a valid MissionAuditRiskLevel"):
        _valid_event(risk_level="not_real")


def test_to_dict_from_dict_preserves_main_fields():
    original = _valid_event(
        event_type=MissionAuditEventType.ACTION_CLASSIFIED,
        outcome=MissionAuditOutcome.REQUIRES_APPROVAL,
        risk_level=MissionAuditRiskLevel.MEDIUM,
        action="file_write",
        policy_decision="requires_approval",
        reason="Action requires approval before execution.",
        correlation_id="corr-1",
        source="mission_control",
        redacted_fields=["metadata.api_key"],
        sensitive=True,
    )

    restored = MissionAuditEvent.from_dict(original.to_dict())

    assert restored.event_id == original.event_id
    assert restored.mission_id == original.mission_id
    assert restored.event_type == original.event_type
    assert restored.outcome == original.outcome
    assert restored.risk_level == original.risk_level
    assert restored.action == original.action
    assert restored.metadata == original.metadata
    assert restored.redacted_fields == original.redacted_fields


def test_rejects_non_dict_metadata():
    with pytest.raises(ValueError, match="metadata must be a dict"):
        _valid_event(metadata=["not", "dict"])


@pytest.mark.parametrize("key", ["token", "secret", "password", "api_key", "private_key"])
def test_sensitive_metadata_rejects_secret_like_keys(key):
    with pytest.raises(ValueError, match="sensitive metadata cannot include secret-like keys"):
        _valid_event(metadata={key: "redacted"}, sensitive=True)


def test_non_sensitive_metadata_can_record_redacted_secret_key_name():
    event = _valid_event(metadata={"token": "redacted"}, sensitive=False)

    assert event.metadata == {"token": "redacted"}


@pytest.mark.parametrize(
    "summary",
    [
        "approve_all_forever",
        "do_anything",
        "unlimited",
        "no_limits",
        "whatever_it_takes",
        "haz_todo_lo_necesario_sin_limites",
    ],
)
def test_rejects_blanket_approval_in_summary(summary):
    with pytest.raises(ValueError, match="summary cannot contain vague blanket approval"):
        _valid_event(summary=f"David said {summary}")


def test_approval_denied_requires_reason():
    with pytest.raises(ValueError, match="approval_denied requires reason"):
        _valid_event(event_type=MissionAuditEventType.APPROVAL_DENIED)


def test_stop_condition_triggered_requires_reason():
    with pytest.raises(ValueError, match="stop_condition_triggered requires reason"):
        _valid_event(event_type=MissionAuditEventType.STOP_CONDITION_TRIGGERED)


def test_validation_failed_requires_reason():
    with pytest.raises(ValueError, match="validation_failed requires reason"):
        _valid_event(event_type=MissionAuditEventType.VALIDATION_FAILED)


def test_approval_granted_requires_approval_request_id_or_reason():
    with pytest.raises(ValueError, match="approval_granted requires approval_request_id or reason"):
        _valid_event(event_type=MissionAuditEventType.APPROVAL_GRANTED)


def test_approval_granted_accepts_approval_request_id():
    event = _valid_event(
        event_type=MissionAuditEventType.APPROVAL_GRANTED,
        approval_request_id="approval-1",
        outcome=MissionAuditOutcome.ALLOWED,
    )

    assert event.approval_request_id == "approval-1"


def test_build_audit_event_fills_generated_fields_without_runtime_side_effects():
    event = build_audit_event(
        mission_id="mission-1",
        event_type=MissionAuditEventType.NOTE_RECORDED,
        actor="jarvis",
        summary="Recorded a mission note.",
    )

    assert event.event_id
    assert event.created_at
    assert event.outcome == MissionAuditOutcome.RECORDED
    assert event.risk_level == MissionAuditRiskLevel.UNKNOWN


def test_build_audit_event_from_approval_request_only_serializes_request_data():
    request = build_approval_request(
        _valid_envelope(),
        "file_write",
        "jarvis",
        request_id="approval-1",
        duration="one_action",
        created_at="2026-05-27T10:00:00+00:00",
    )

    event = build_audit_event_from_approval_request(request, "jarvis", event_id="audit-1")

    assert event.event_id == "audit-1"
    assert event.mission_id == request.mission_id
    assert event.action == request.action
    assert event.approval_request_id == request.request_id
    assert event.event_type == MissionAuditEventType.APPROVAL_REQUESTED
    assert event.outcome == MissionAuditOutcome.REQUIRES_APPROVAL
    assert event.risk_level == MissionAuditRiskLevel.MEDIUM
    assert event.metadata == {
        "approval_level": MissionApprovalLevel.REQUIRES_APPROVAL.value,
        "classification": ActionClassification.REQUIRES_APPROVAL.value,
    }


def test_build_audit_event_from_approval_request_accepts_manual_request_without_gateway():
    request = MissionApprovalRequest(
        request_id="approval-1",
        mission_id="mission-1",
        action="deploy",
        classification=ActionClassification.STRONG_APPROVAL,
        reason="Deploy requires strong approval.",
        scope=["deploy"],
        requested_by="jarvis",
        approval_level=MissionApprovalLevel.STRONG_APPROVAL,
        duration="one_action",
        cost_limit=0,
        rollback_plan="rollback deploy",
        audit_requirements=["approvals"],
    )

    event = build_audit_event_from_approval_request(request, "jarvis")

    assert event.approval_request_id == "approval-1"
    assert event.outcome == MissionAuditOutcome.STRONG_APPROVAL
    assert event.risk_level == MissionAuditRiskLevel.HIGH
