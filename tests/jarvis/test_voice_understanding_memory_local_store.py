import hashlib
import json

import pytest

from jarvis.voice import (
    UserUnderstandingAppliedFeedbackRule,
    UserUnderstandingMemoryProposalStore,
    UserUnderstandingMemoryStatus,
    VoiceRuntime,
    save_user_understanding_memory_snapshot_local,
)


def _rule(
    *,
    original_text: str = "monta algo para probar este nicho",
    corrected_intent: str = "create_mission",
    suggested_alias: str | None = "probar este nicho",
) -> UserUnderstandingAppliedFeedbackRule:
    return UserUnderstandingAppliedFeedbackRule(
        original_text=original_text,
        corrected_intent=corrected_intent,
        suggested_alias=suggested_alias,
        reason="Regla revisada por David",
    )


def _snapshot_with_proposal():
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(_rule())
    return store.export_snapshot(), proposal


def test_save_local_creates_snapshot_file_directories_and_marks_persisted(tmp_path):
    snapshot, proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"

    result = save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    backups_dir = base_dir / "user_understanding" / "backups"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert result.saved is True
    assert result.persisted is True
    assert result.proposal_count == 1
    assert payload["persisted"] is True
    assert payload["proposal_count"] == 1
    assert payload["proposals"][0]["id"] == proposal.id
    assert snapshot_path.exists()
    assert backups_dir.is_dir()


def test_save_local_creates_audit_log_jsonl_without_proposal_content(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"

    result = save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    audit_path = base_dir / "user_understanding" / "audit_log.jsonl"
    lines = audit_path.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[-1])
    assert result.audit_log_path == str(audit_path)
    assert event["event"] == "memory_snapshot_saved"
    assert event["persisted"] is True
    assert event["snapshot_path"] == str(base_dir / "user_understanding" / "memory_proposals.snapshot.json")
    assert event["proposal_count"] == 1
    assert event["active_count"] == 0
    assert event["sensitive_count"] == 0
    assert event["checksum"] == result.checksum
    assert "proposals" not in event
    assert "alias" not in event
    assert "evidence" not in event


def test_save_local_checksum_matches_final_json_bytes(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"

    result = save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    snapshot_bytes = (base_dir / "user_understanding" / "memory_proposals.snapshot.json").read_bytes()
    assert result.checksum == hashlib.sha256(snapshot_bytes).hexdigest()


def test_save_local_backup_created_only_when_previous_snapshot_exists(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"

    first = save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    second = save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    assert first.backup_path is None
    assert second.backup_path is not None
    assert (base_dir / "user_understanding" / "backups").is_dir()
    assert second.backup_path.endswith(".json")
    assert len(list((base_dir / "user_understanding" / "backups").glob("*.json"))) == 1


def test_save_local_create_backup_false_does_not_create_backup(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"

    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    result = save_user_understanding_memory_snapshot_local(
        snapshot,
        base_dir=base_dir,
        create_backup=False,
    )

    assert result.backup_path is None
    assert list((base_dir / "user_understanding" / "backups").glob("*.json")) == []


def test_save_local_rejects_sensitive_active_or_approved_snapshot(tmp_path):
    store = UserUnderstandingMemoryProposalStore()
    proposal = store.propose_from_feedback_rule(
        _rule(
            original_text="usa el password del .env",
            corrected_intent="requires_approval",
            suggested_alias="password del .env",
        )
    )
    proposal.status = UserUnderstandingMemoryStatus.APPROVED
    proposal.active = True
    snapshot = store.export_snapshot()

    with pytest.raises(ValueError, match="Sensitive active or approved"):
        save_user_understanding_memory_snapshot_local(snapshot, base_dir=tmp_path / ".jarvis")

    assert not (tmp_path / ".jarvis").exists()


def test_save_local_rejects_persisted_input_snapshot(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    snapshot.persisted = True

    with pytest.raises(ValueError, match="Persisted memory snapshots"):
        save_user_understanding_memory_snapshot_local(snapshot, base_dir=tmp_path / ".jarvis")


def test_save_local_atomic_write_leaves_no_tmp_file_on_success(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"

    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    user_understanding_dir = base_dir / "user_understanding"
    assert list(user_understanding_dir.glob("*.tmp")) == []
    assert list(user_understanding_dir.glob(".*.tmp")) == []


def test_voice_runtime_save_memory_snapshot_local_does_not_apply_memory_to_runtime_or_router(tmp_path):
    runtime = VoiceRuntime()
    before = runtime.handle_transcript("monta algo para probar este nicho")
    rule = _rule(corrected_intent="query_status")
    proposal = runtime.propose_memory_from_applied_feedback(rule)
    runtime.approve_memory_proposal(proposal.id)
    last_transcript = runtime.status().last_transcript

    result = runtime.save_memory_snapshot_local(base_dir=tmp_path / ".jarvis")
    after = runtime.handle_transcript("monta algo para probar este nicho")

    assert result["persisted"] is True
    assert after["intent"] == before["intent"]
    assert after["status"] == before["status"]
    assert "reviewed_feedback_applied" not in after["user_context_signals"]
    assert runtime.status().applied_feedback_count == 0
    assert last_transcript == "monta algo para probar este nicho"
