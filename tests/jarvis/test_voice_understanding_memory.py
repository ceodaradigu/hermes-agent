import builtins
import json

import pytest

from jarvis.voice import (
    UserUnderstandingAppliedFeedbackRule,
    UserUnderstandingMemorySnapshot,
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


def test_export_snapshot_empty_store():
    store = UserUnderstandingMemoryProposalStore()

    snapshot = store.export_snapshot()

    assert snapshot.version == 1
    assert snapshot.proposals == []
    assert snapshot.proposal_count == 0
    assert snapshot.active_count == 0
    assert snapshot.sensitive_count == 0
    assert snapshot.source == "user_understanding_memory_proposal_store"
    assert snapshot.persisted is False


def test_export_snapshot_counts_proposals_active_and_sensitive():
    store = UserUnderstandingMemoryProposalStore()
    active_proposal = store.propose_from_feedback_rule(_rule())
    store.approve(active_proposal.id)
    sensitive_proposal = store.propose_from_feedback_rule(
        _rule(
            original_text="usa el token del .env",
            corrected_intent="requires_approval",
            suggested_alias="token del .env",
        )
    )

    snapshot = store.export_snapshot()

    assert snapshot.proposal_count == 2
    assert snapshot.active_count == 1
    assert snapshot.sensitive_count == 1
    assert sensitive_proposal.sensitive is True


def test_snapshot_to_json_produces_valid_json():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())

    payload = json.loads(store.export_snapshot_json())

    assert payload["proposal_count"] == 1
    assert payload["persisted"] is False
    assert payload["proposals"][0]["id"] == proposal.id


def test_snapshot_from_json_reconstructs_snapshot():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())
    snapshot_json = store.export_snapshot_json()

    snapshot = UserUnderstandingMemorySnapshot.from_json(snapshot_json)

    assert snapshot.proposal_count == 1
    assert snapshot.proposals[0].id == proposal.id
    assert snapshot.proposals[0].status == UserUnderstandingMemoryStatus.PROPOSED


def test_import_snapshot_merge_adds_proposals_without_replacing_existing():
    source_store = UserUnderstandingMemoryProposalStore()
    source_proposal = source_store.propose_from_feedback_rule(_rule())
    target_store = UserUnderstandingMemoryProposalStore()
    existing_proposal = target_store.propose_from_feedback_rule(
        _rule(suggested_alias="consulta estado", corrected_intent="query_status")
    )

    imported_count = target_store.import_snapshot(source_store.export_snapshot())

    assert imported_count == 1
    assert target_store.count() == 2
    assert target_store.get_proposal(existing_proposal.id) == existing_proposal
    assert target_store.get_proposal(source_proposal.id).id == source_proposal.id


def test_import_snapshot_replace_replaces_existing_proposals():
    source_store = UserUnderstandingMemoryProposalStore()
    source_proposal = source_store.propose_from_feedback_rule(_rule())
    target_store = UserUnderstandingMemoryProposalStore()
    existing_proposal = target_store.propose_from_feedback_rule(
        _rule(suggested_alias="consulta estado", corrected_intent="query_status")
    )

    imported_count = target_store.import_snapshot(
        source_store.export_snapshot_json(),
        replace=True,
    )

    assert imported_count == 1
    assert target_store.count() == 1
    assert target_store.get_proposal(source_proposal.id).id == source_proposal.id
    with pytest.raises(KeyError):
        target_store.get_proposal(existing_proposal.id)


def test_import_snapshot_does_not_affect_voice_intent_router_or_runtime():
    before_router = VoiceIntentRouter().classify("monta algo para probar este nicho").to_dict()
    before_runtime = VoiceRuntime().handle_transcript("monta algo para probar este nicho")
    source_store = UserUnderstandingMemoryProposalStore()
    proposal = source_store.propose_from_feedback_rule(_rule(corrected_intent="query_status"))
    source_store.approve(proposal.id)
    target_store = UserUnderstandingMemoryProposalStore()

    target_store.import_snapshot(source_store.export_snapshot_json())

    after_router = VoiceIntentRouter().classify("monta algo para probar este nicho").to_dict()
    after_runtime = VoiceRuntime().handle_transcript("monta algo para probar este nicho")

    assert after_router == before_router
    assert after_runtime == before_runtime


def test_import_snapshot_rejects_active_sensitive_proposals():
    source_store = UserUnderstandingMemoryProposalStore()
    proposal = source_store.propose_from_feedback_rule(
        _rule(
            original_text="usa el password del .env",
            corrected_intent="requires_approval",
            suggested_alias="password del .env",
        )
    )
    payload = source_store.export_snapshot().as_dict()
    payload["proposals"][0]["status"] = "approved"
    payload["proposals"][0]["active"] = True
    payload["active_count"] = 1

    target_store = UserUnderstandingMemoryProposalStore()
    with pytest.raises(ValueError, match="Sensitive memory proposals"):
        target_store.import_snapshot(payload)

    assert proposal.sensitive is True
    assert target_store.count() == 0


def test_import_snapshot_rejects_invalid_format():
    store = UserUnderstandingMemoryProposalStore()

    with pytest.raises(ValueError):
        store.import_snapshot({"version": 1, "exported_at": "2026-05-18T00:00:00Z"})

    with pytest.raises(ValueError):
        store.import_snapshot("{invalid json")


def test_import_snapshot_rejects_persisted_snapshots():
    source_store = UserUnderstandingMemoryProposalStore()
    source_store.propose_from_feedback_rule(_rule())
    payload = source_store.export_snapshot().as_dict()
    payload["persisted"] = True
    target_store = UserUnderstandingMemoryProposalStore()

    with pytest.raises(ValueError, match="Persisted memory snapshots"):
        target_store.import_snapshot(payload)

    assert target_store.count() == 0


def test_snapshot_export_import_does_not_open_files(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("snapshot export/import must not open files")

    source_store = UserUnderstandingMemoryProposalStore()
    source_store.propose_from_feedback_rule(_rule())
    target_store = UserUnderstandingMemoryProposalStore()

    monkeypatch.setattr(builtins, "open", fail_open)

    snapshot_json = source_store.export_snapshot_json()
    assert target_store.import_snapshot(snapshot_json) == 1


def test_memory_proposals_are_not_persistent_between_new_stores_without_explicit_import():
    source_store = UserUnderstandingMemoryProposalStore()
    source_store.propose_from_feedback_rule(_rule())
    snapshot_json = source_store.export_snapshot_json()
    fresh_store = UserUnderstandingMemoryProposalStore()

    assert fresh_store.count() == 0

    assert fresh_store.import_snapshot(snapshot_json) == 1
    assert fresh_store.count() == 1
