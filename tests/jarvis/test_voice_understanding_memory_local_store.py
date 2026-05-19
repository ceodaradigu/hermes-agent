import hashlib
import json
import subprocess

import pytest

from jarvis.voice import (
    UserUnderstandingAppliedFeedbackRule,
    UserUnderstandingMemoryProposalStore,
    UserUnderstandingMemoryStatus,
    VoiceRuntime,
    backup_user_understanding_memory_snapshot_local,
    delete_user_understanding_memory_local,
    get_user_understanding_memory_local_status,
    load_user_understanding_memory_snapshot_local,
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


def test_save_local_then_load_local_imports_proposals(tmp_path):
    snapshot, proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    target_store = UserUnderstandingMemoryProposalStore()

    result = load_user_understanding_memory_snapshot_local(target_store, base_dir=base_dir)

    assert result.loaded is True
    assert result.persisted_source is True
    assert result.applied_to_runtime is False
    assert result.imported_count == 1
    assert target_store.get_proposal(proposal.id).id == proposal.id


def test_load_local_replace_true_replaces_store(tmp_path):
    snapshot, proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    target_store = UserUnderstandingMemoryProposalStore()
    existing = target_store.propose_from_feedback_rule(
        _rule(original_text="consulta el estado", corrected_intent="query_status", suggested_alias="estado")
    )

    result = load_user_understanding_memory_snapshot_local(target_store, base_dir=base_dir, replace=True)

    assert result.memory_proposal_count == 1
    assert target_store.get_proposal(proposal.id).id == proposal.id
    with pytest.raises(KeyError):
        target_store.get_proposal(existing.id)


def test_load_local_replace_false_merges_store(tmp_path):
    snapshot, proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    target_store = UserUnderstandingMemoryProposalStore()
    existing = target_store.propose_from_feedback_rule(
        _rule(original_text="consulta el estado", corrected_intent="query_status", suggested_alias="estado")
    )

    result = load_user_understanding_memory_snapshot_local(target_store, base_dir=base_dir, replace=False)

    assert result.memory_proposal_count == 2
    assert target_store.get_proposal(proposal.id).id == proposal.id
    assert target_store.get_proposal(existing.id).id == existing.id


def test_load_local_writes_audit_event_and_checksum(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    target_store = UserUnderstandingMemoryProposalStore()

    result = load_user_understanding_memory_snapshot_local(target_store, base_dir=base_dir, replace=False)

    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    audit_path = base_dir / "user_understanding" / "audit_log.jsonl"
    audit_event = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])
    assert result.checksum == hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    assert audit_event["event"] == "memory_snapshot_loaded"
    assert audit_event["snapshot_path"] == str(snapshot_path)
    assert audit_event["imported_count"] == 1
    assert audit_event["memory_proposal_count"] == 1
    assert audit_event["checksum"] == result.checksum
    assert audit_event["replace"] is False
    assert audit_event["applied_to_runtime"] is False
    assert "proposals" not in audit_event
    assert "alias" not in audit_event
    assert "evidence" not in audit_event


def test_load_local_fails_when_snapshot_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_user_understanding_memory_snapshot_local(
            UserUnderstandingMemoryProposalStore(),
            base_dir=tmp_path / ".jarvis",
        )


def test_load_local_fails_with_corrupt_json(tmp_path):
    base_dir = tmp_path / ".jarvis"
    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON is invalid"):
        load_user_understanding_memory_snapshot_local(
            UserUnderstandingMemoryProposalStore(),
            base_dir=base_dir,
        )


def test_load_local_fails_with_non_object_json(tmp_path):
    base_dir = tmp_path / ".jarvis"
    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_user_understanding_memory_snapshot_local(
            UserUnderstandingMemoryProposalStore(),
            base_dir=base_dir,
        )


def test_load_local_fails_with_empty_or_null_byte_base_dir(tmp_path):
    with pytest.raises(ValueError, match="base_dir must not be empty"):
        load_user_understanding_memory_snapshot_local(UserUnderstandingMemoryProposalStore(), base_dir=" ")
    with pytest.raises(ValueError, match="null bytes"):
        load_user_understanding_memory_snapshot_local(
            UserUnderstandingMemoryProposalStore(),
            base_dir=f"{tmp_path}\0.jarvis",
        )


def test_load_local_rejects_sensitive_active_or_approved_snapshot(tmp_path):
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
    base_dir = tmp_path / ".jarvis"
    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    snapshot_path.parent.mkdir(parents=True)
    payload = snapshot.as_dict()
    payload["persisted"] = True
    snapshot_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Sensitive active or approved"):
        load_user_understanding_memory_snapshot_local(
            UserUnderstandingMemoryProposalStore(),
            base_dir=base_dir,
        )


def test_load_local_accepts_persisted_true_from_controlled_local_file(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    target_store = UserUnderstandingMemoryProposalStore()

    result = load_user_understanding_memory_snapshot_local(target_store, base_dir=base_dir)

    assert result.persisted_source is True
    assert target_store.count() == 1


def test_voice_runtime_load_memory_snapshot_local_does_not_apply_memory_to_runtime_or_router(tmp_path):
    source = UserUnderstandingMemoryProposalStore()
    proposal = source.propose_from_feedback_rule(_rule(corrected_intent="query_status"))
    source.approve(proposal.id)
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(source.export_snapshot(), base_dir=base_dir)
    runtime = VoiceRuntime()
    before = runtime.handle_transcript("monta algo para probar este nicho")
    last_transcript = runtime.status().last_transcript

    result = runtime.load_memory_snapshot_local(base_dir=base_dir)
    after = runtime.handle_transcript("monta algo para probar este nicho")

    assert result["loaded"] is True
    assert result["applied_to_runtime"] is False
    assert after["intent"] == before["intent"]
    assert after["status"] == before["status"]
    assert "reviewed_feedback_applied" not in after["user_context_signals"]
    assert runtime.status().applied_feedback_count == 0
    assert last_transcript == "monta algo para probar este nicho"


def test_load_local_does_not_autoload_between_new_voice_runtime_instances(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    fresh_runtime = VoiceRuntime()

    assert fresh_runtime.status().memory_proposal_count == 0
    assert fresh_runtime.list_memory_proposals() == []


def test_local_status_without_jarvis_reports_missing_snapshot(tmp_path):
    result = get_user_understanding_memory_local_status(base_dir=tmp_path / ".jarvis")

    assert result.exists is False
    assert result.snapshot_exists is False
    assert result.audit_log_exists is False
    assert result.backups_dir_exists is False
    assert result.persisted is False
    assert result.checksum is None
    assert result.can_load_explicitly is False
    assert result.applied_to_runtime is False


def test_save_local_then_status_reports_persisted_checksum(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    result = get_user_understanding_memory_local_status(base_dir=base_dir)

    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    assert result.exists is True
    assert result.snapshot_exists is True
    assert result.audit_log_exists is True
    assert result.persisted is True
    assert result.can_load_explicitly is True
    assert result.checksum == hashlib.sha256(snapshot_path.read_bytes()).hexdigest()


def test_local_status_with_corrupt_json_returns_note_not_exception(tmp_path):
    base_dir = tmp_path / ".jarvis"
    snapshot_path = base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text("{invalid json", encoding="utf-8")

    result = get_user_understanding_memory_local_status(base_dir=base_dir)

    assert result.snapshot_exists is True
    assert result.persisted is False
    assert result.can_load_explicitly is False
    assert any("warning" in note for note in result.notes)


def test_backup_local_creates_file_and_audit_event(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)

    result = backup_user_understanding_memory_snapshot_local(base_dir=base_dir)

    backup_path = base_dir / "user_understanding" / "backups"
    audit_path = base_dir / "user_understanding" / "audit_log.jsonl"
    event = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])
    assert result.backed_up is True
    assert result.persisted_source is True
    assert result.proposal_count == 1
    assert result.applied_to_runtime is False
    assert len(list(backup_path.glob("memory_proposals.snapshot.*.json"))) == 1
    assert event["event"] == "memory_snapshot_backed_up"
    assert event["backup_path"] == result.backup_path
    assert event["checksum"] == result.checksum
    assert event["applied_to_runtime"] is False
    assert "proposals" not in event
    assert "alias" not in event
    assert "evidence" not in event


def test_backup_local_fails_controlled_when_snapshot_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="Local memory snapshot not found"):
        backup_user_understanding_memory_snapshot_local(base_dir=tmp_path / ".jarvis")


def test_delete_local_deletes_snapshot_audit_and_backups(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    backup_user_understanding_memory_snapshot_local(base_dir=base_dir)

    result = delete_user_understanding_memory_local(base_dir=base_dir, include_backups=True)

    user_understanding_dir = base_dir / "user_understanding"
    assert result.deleted is True
    assert result.snapshot_deleted is True
    assert result.audit_log_deleted is True
    assert result.backups_deleted is True
    assert not (user_understanding_dir / "memory_proposals.snapshot.json").exists()
    assert not (user_understanding_dir / "audit_log.jsonl").exists()
    assert not (user_understanding_dir / "backups").exists()


def test_delete_local_preserves_backups_when_requested(tmp_path):
    snapshot, _proposal = _snapshot_with_proposal()
    base_dir = tmp_path / ".jarvis"
    save_user_understanding_memory_snapshot_local(snapshot, base_dir=base_dir)
    backup_user_understanding_memory_snapshot_local(base_dir=base_dir)

    result = delete_user_understanding_memory_local(base_dir=base_dir, include_backups=False)

    assert result.deleted is True
    assert result.snapshot_deleted is True
    assert result.audit_log_deleted is True
    assert result.backups_deleted is False
    assert (base_dir / "user_understanding" / "backups").is_dir()


def test_delete_local_does_not_fail_when_memory_missing(tmp_path):
    result = delete_user_understanding_memory_local(base_dir=tmp_path / ".jarvis")

    assert result.deleted is False
    assert result.snapshot_deleted is False
    assert result.audit_log_deleted is False
    assert result.backups_deleted is False
    assert any("No local memory" in note for note in result.notes)


def test_status_backup_delete_do_not_change_runtime_transcript_or_router(tmp_path):
    runtime = VoiceRuntime()
    before = runtime.handle_transcript("monta algo para probar este nicho")
    last_transcript = runtime.status().last_transcript
    proposal = runtime.propose_memory_from_applied_feedback(_rule(corrected_intent="query_status"))
    runtime.approve_memory_proposal(proposal.id)
    runtime.save_memory_snapshot_local(base_dir=tmp_path / ".jarvis")

    status = runtime.get_memory_local_status(base_dir=tmp_path / ".jarvis")
    backup = runtime.backup_memory_snapshot_local(base_dir=tmp_path / ".jarvis")
    delete = runtime.delete_memory_local(base_dir=tmp_path / ".jarvis")
    after = runtime.handle_transcript("monta algo para probar este nicho")

    assert status["applied_to_runtime"] is False
    assert backup["applied_to_runtime"] is False
    assert delete["applied_to_runtime"] is False
    assert after["intent"] == before["intent"]
    assert after["status"] == before["status"]
    assert "reviewed_feedback_applied" not in after["user_context_signals"]
    assert runtime.status().applied_feedback_count == 0
    assert last_transcript == "monta algo para probar este nicho"


def test_cli_bash_syntax_is_valid():
    result = subprocess.run(
        ["bash", "-n", "scripts/local/voice-runtime-control.sh"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
