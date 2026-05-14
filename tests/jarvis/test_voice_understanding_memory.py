import json

import pytest

from jarvis.voice import (
    UserUnderstandingAppliedFeedbackRule,
    UserUnderstandingMemoryProposalStore,
    UserUnderstandingMemoryStatus,
    VoiceIntentRouter,
    VoiceRuntime,
)


def _rule(
    *,
    original_text: str = "monta algo para probar este nicho",
    corrected_intent: str = "create_mission",
    suggested_alias: str | None = "probar este nicho",
    reason: str = "Applied temporary reviewed feedback rule from David.",
) -> UserUnderstandingAppliedFeedbackRule:
    return UserUnderstandingAppliedFeedbackRule(
        original_text=original_text,
        corrected_intent=corrected_intent,
        suggested_alias=suggested_alias,
        reason=reason,
    )


def test_memory_proposal_store_starts_empty():
    store = UserUnderstandingMemoryProposalStore()

    assert store.count() == 0
    assert store.list_proposals() == []


def test_propose_from_feedback_rule_creates_proposed_inactive_proposal():
    store = UserUnderstandingMemoryProposalStore()

    proposal = store.propose_from_feedback_rule(_rule())

    assert store.count() == 1
    assert proposal.status == UserUnderstandingMemoryStatus.PROPOSED
    assert proposal.active is False
    assert proposal.type == "intent_alias"
    assert proposal.alias == "probar este nicho"
    assert proposal.target_intent == "create_mission"
    assert proposal.sensitive is False


def test_memory_proposal_has_audit():
    store = UserUnderstandingMemoryProposalStore()

    proposal = store.propose_from_feedback_rule(_rule())

    assert proposal.audit
    assert proposal.audit[0]["event"] == "proposed"
    assert proposal.audit[0]["source"] == "user_reviewed_feedback"


def test_memory_proposal_list_and_get_work():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())

    assert store.list_proposals() == [proposal]
    assert store.get_proposal(proposal.id) == proposal


def test_mark_reviewed_changes_status_without_activating():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())

    reviewed = store.mark_reviewed(proposal.id)

    assert reviewed.status == UserUnderstandingMemoryStatus.REVIEWED
    assert reviewed.active is False
    assert reviewed.audit[-1]["event"] == "reviewed"


def test_approve_changes_status_to_approved_and_active_for_non_sensitive():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())

    approved = store.approve(proposal.id)

    assert approved.status == UserUnderstandingMemoryStatus.APPROVED
    assert approved.active is True
    assert approved.approved_by == "David"
    assert approved.audit[-1]["event"] == "approved"


def test_approve_sensitive_proposal_is_rejected():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(
        _rule(
            original_text="usa el password del .env",
            corrected_intent="requires_approval",
            suggested_alias="password del .env",
        )
    )

    with pytest.raises(ValueError, match="Sensitive memory proposals"):
        store.approve(proposal.id)

    assert proposal.sensitive is True
    assert proposal.status == UserUnderstandingMemoryStatus.PROPOSED
    assert proposal.active is False
    assert proposal.audit[-1]["event"] == "approval_rejected_sensitive"
    assert "Sensitive memory proposals" in proposal.reason


def test_disable_changes_status_and_deactivates():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())
    store.approve(proposal.id)

    disabled = store.disable(proposal.id, reason="No longer useful.")

    assert disabled.status == UserUnderstandingMemoryStatus.DISABLED
    assert disabled.active is False
    assert disabled.reason == "No longer useful."
    assert disabled.audit[-1]["event"] == "disabled"


def test_delete_changes_status_and_deactivates():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())
    store.approve(proposal.id)

    deleted = store.delete(proposal.id, reason="Remove proposal.")

    assert deleted.status == UserUnderstandingMemoryStatus.DELETED
    assert deleted.active is False
    assert deleted.reason == "Remove proposal."
    assert deleted.audit[-1]["event"] == "deleted"


def test_clear_removes_memory_proposals():
    store = UserUnderstandingMemoryProposalStore()
    store.propose_from_feedback_rule(_rule())

    store.clear()

    assert store.count() == 0
    assert store.list_proposals() == []


def test_memory_proposal_store_does_not_affect_voice_intent_router():
    before = VoiceIntentRouter().classify("monta algo para probar este nicho").to_dict()
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule(corrected_intent="query_status"))
    store.approve(proposal.id)

    after = VoiceIntentRouter().classify("monta algo para probar este nicho").to_dict()

    assert after == before


def test_memory_proposal_store_does_not_affect_voice_runtime_transcript():
    runtime = VoiceRuntime()
    before = runtime.handle_transcript("monta algo para probar este nicho")
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule(corrected_intent="query_status"))
    store.approve(proposal.id)

    fresh_runtime = VoiceRuntime()
    after = fresh_runtime.handle_transcript("monta algo para probar este nicho")

    assert after == before
    assert fresh_runtime.status().applied_feedback_count == 0


def test_memory_proposal_is_serializable():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())

    payload = proposal.as_dict()

    assert json.loads(json.dumps(payload)) == payload
    assert payload["status"] == "proposed"


def test_memory_proposals_are_not_persistent_between_new_stores():
    store = UserUnderstandingMemoryProposalStore()
    store.propose_from_feedback_rule(_rule())

    fresh_store = UserUnderstandingMemoryProposalStore()

    assert store.count() == 1
    assert fresh_store.count() == 0
