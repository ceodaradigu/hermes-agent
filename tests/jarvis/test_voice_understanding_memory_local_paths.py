import builtins
import json

import pytest

from jarvis.voice import (
    VoiceRuntime,
    resolve_user_understanding_memory_local_paths,
    validate_user_understanding_memory_local_paths,
)


def test_default_base_dir_generates_paths_under_jarvis_user_understanding():
    paths = resolve_user_understanding_memory_local_paths()

    assert paths.root_dir.as_posix() == ".jarvis"
    assert paths.user_understanding_dir.as_posix() == ".jarvis/user_understanding"
    assert paths.snapshot_path.as_posix() == ".jarvis/user_understanding/memory_proposals.snapshot.json"
    assert paths.audit_log_path.as_posix() == ".jarvis/user_understanding/audit_log.jsonl"
    assert paths.backups_dir.as_posix() == ".jarvis/user_understanding/backups"


def test_custom_base_dir_generates_paths_under_that_directory(tmp_path):
    base_dir = tmp_path / "local-memory"

    paths = resolve_user_understanding_memory_local_paths(base_dir)

    assert paths.root_dir == base_dir
    assert paths.user_understanding_dir == base_dir / "user_understanding"
    assert paths.snapshot_path == base_dir / "user_understanding" / "memory_proposals.snapshot.json"
    assert paths.audit_log_path == base_dir / "user_understanding" / "audit_log.jsonl"
    assert paths.backups_dir == base_dir / "user_understanding" / "backups"


def test_as_dict_is_serializable():
    paths = resolve_user_understanding_memory_local_paths("memory-root")

    payload = paths.as_dict()

    assert paths.to_dict() == payload
    assert json.loads(json.dumps(payload)) == payload


def test_resolver_does_not_create_directories_or_files(tmp_path):
    base_dir = tmp_path / "future-memory"

    paths = resolve_user_understanding_memory_local_paths(base_dir)

    assert not base_dir.exists()
    assert not paths.user_understanding_dir.exists()
    assert not paths.snapshot_path.exists()
    assert not paths.audit_log_path.exists()
    assert not paths.backups_dir.exists()


def test_resolver_and_validator_do_not_open_files(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("local path resolver must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    paths = resolve_user_understanding_memory_local_paths("memory-root")
    result = validate_user_understanding_memory_local_paths(paths)

    assert result["valid"] is True


def test_validate_returns_guardrails_without_io_permissions():
    paths = resolve_user_understanding_memory_local_paths()

    result = validate_user_understanding_memory_local_paths(paths)

    assert result["valid"] is True
    assert result["can_write"] is False
    assert result["can_read"] is False
    assert result["persisted"] is False
    assert result["root_dir"] == ".jarvis"
    assert result["user_understanding_dir"] == ".jarvis/user_understanding"
    assert result["snapshot_path"] == ".jarvis/user_understanding/memory_proposals.snapshot.json"
    assert result["audit_log_path"] == ".jarvis/user_understanding/audit_log.jsonl"
    assert result["backups_dir"] == ".jarvis/user_understanding/backups"
    assert result["notes"]
    assert json.loads(json.dumps(result)) == result


def test_empty_base_dir_fails():
    with pytest.raises(ValueError, match="must not be empty"):
        resolve_user_understanding_memory_local_paths("")

    with pytest.raises(ValueError, match="must not be empty"):
        resolve_user_understanding_memory_local_paths("   ")


def test_base_dir_with_null_byte_fails():
    with pytest.raises(ValueError, match="null bytes"):
        resolve_user_understanding_memory_local_paths("memory\0root")


def test_base_dir_with_path_traversal_fails():
    with pytest.raises(ValueError, match="path traversal"):
        resolve_user_understanding_memory_local_paths("../memory-root")


def test_base_dir_that_looks_like_memory_file_fails():
    with pytest.raises(ValueError, match="file path"):
        resolve_user_understanding_memory_local_paths("memory_proposals.snapshot.json")


def test_snapshot_audit_and_backups_names_are_stable():
    paths = resolve_user_understanding_memory_local_paths("memory-root")

    assert paths.snapshot_path.name == "memory_proposals.snapshot.json"
    assert paths.audit_log_path.name == "audit_log.jsonl"
    assert paths.backups_dir.name == "backups"


def test_local_paths_do_not_affect_voice_runtime_transcript():
    before = VoiceRuntime().handle_transcript("monta algo para probar este nicho")

    paths = resolve_user_understanding_memory_local_paths()
    validate_user_understanding_memory_local_paths(paths)

    after = VoiceRuntime().handle_transcript("monta algo para probar este nicho")
    assert after == before


def test_local_paths_do_not_persist_memory_between_runtime_instances(tmp_path):
    paths = resolve_user_understanding_memory_local_paths(tmp_path / "future-memory")
    validate_user_understanding_memory_local_paths(paths)

    runtime = VoiceRuntime()
    fresh_runtime = VoiceRuntime()

    assert runtime.status().applied_feedback_count == 0
    assert fresh_runtime.status().applied_feedback_count == 0
    assert not paths.root_dir.exists()
