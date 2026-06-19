import json
import re
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import create_app
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


def _route(app, path: str, method: str = "GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _jarvis_ui_source() -> str:
    paths = [WEB / "src/pages/JarvisCommandCenterPage.tsx"]
    paths.extend(sorted((WEB / "src/components/jarvis").glob("*.ts")))
    paths.extend(sorted((WEB / "src/components/jarvis").glob("*.tsx")))
    paths.extend(sorted((WEB / "src/hooks/jarvis").glob("*.ts")))
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_audit_ledger_creates_metadata_only_entry_and_redacts_dangerous_payloads(tmp_path):
    ledger = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")

    entry = ledger.record(
        event_type="voice_session_requested",
        surface="voice",
        source="/jarvis/local-voice",
        risk_level="sensor_privacy",
        approval_level="simple",
        session_id="session-safe-id",
        metadata={
            "provider": "browser_speech_recognition",
            "raw_audio": "RIFF raw bytes must not persist",
            "camera_frame": "frame-bytes",
            "password": "hunter2",
            "api_token": "sk-test-123",
            "cookie": "cookievalue",
            ".env": "API_KEY=value",
            "transcript_text": "full transcript must not persist",
            "duration_ms": 120,
        },
        contains_full_transcript=True,
        hermes_dispatch_allowed=True,
    )

    serialized = json.dumps(entry, sort_keys=True).lower()
    for forbidden in ("riff raw bytes", "frame-bytes", "hunter2", "sk-test-123", "cookievalue", "api_key=value", "full transcript must not persist"):
        assert forbidden not in serialized
    assert entry["contains_raw_audio"] is False
    assert entry["contains_camera_frame"] is False
    assert entry["contains_secret"] is False
    assert entry["contains_credential"] is False
    assert entry["contains_full_transcript"] is False
    assert entry["hermes_dispatch_allowed"] is False
    assert entry["correlation_id"]
    assert entry["previous_hash"] == "GENESIS"
    assert entry["entry_hash"]
    assert entry["tamper_evident"] is True
    assert entry["redaction_summary"]["blocked_field_count"] >= 7


@pytest.mark.parametrize(
    "event_type,surface",
    [
        ("wake_disabled", "wake"),
        ("stt_unavailable", "stt"),
        ("tts_speaking", "tts"),
        ("recording_local_started", "recording"),
        ("recording_local_deleted", "recording"),
        ("camera_requested", "camera"),
        ("conversational_intake_classified", "intake"),
        ("brain_adapter_response", "brain"),
        ("approval_required", "approval"),
        ("hermes_dispatch_disabled", "hermes"),
    ],
)
def test_audit_target_events_are_metadata_only(tmp_path, event_type, surface):
    ledger = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")

    entry = ledger.record(
        event_type=event_type,
        surface=surface,
        source="/mark-3/dashboard/status",
        metadata={"status": "ok", "confidence": "unknown"},
    )

    assert entry["event_type"] == event_type
    assert entry["surface"] == surface
    assert entry["metadata"] == {"status": "ok", "confidence": "unknown"}
    assert entry["contains_raw_audio"] is False
    assert entry["contains_camera_frame"] is False
    assert entry["contains_full_transcript"] is False
    assert entry["contains_credential"] is False
    assert entry["correlation_id"]


def test_audit_hash_chain_survives_reload_and_detects_tampering(tmp_path):
    ledger = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")
    first = ledger.record(event_type="voice_session_started", surface="voice", metadata={"state": "listening"})
    second = ledger.record(event_type="voice_session_stopped", surface="voice", metadata={"state": "stopped"})

    assert second["previous_hash"] == first["entry_hash"]
    assert ledger.verify_chain().valid is True
    db_path = ledger.db_path
    ledger.close()

    reloaded = PersistentAuditLedger(db_path=db_path)
    assert reloaded.status()["state"]["event_count"] == 2
    assert reloaded.verify_chain().valid is True
    reloaded.close()

    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE audit_entries SET metadata_json = ? WHERE audit_id = ?", ('{"state":"tampered"}', first["audit_id"]))
        conn.commit()
    tampered = PersistentAuditLedger(db_path=db_path)
    verification = tampered.verify_chain()
    assert verification.valid is False
    assert verification.first_invalid_audit_id == first["audit_id"]


def test_audit_export_and_default_app_do_not_write_repo_or_expose_sensitive_values(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)

    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    assert not (work / ".jarvis").exists()
    status = _route(app, "/mark-3/audit/status").endpoint()
    assert status["state"]["storage_configured"] is False

    ledger = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")
    ledger.record(
        event_type="camera_failed",
        surface="camera",
        metadata={"error": "permission_denied", "token": "sk-secret", "password": "hunter2"},
    )
    exported = ledger.export_snapshot()
    serialized = json.dumps(exported, sort_keys=True).lower()
    assert "sk-secret" not in serialized
    assert "hunter2" not in serialized
    assert exported["metadata_only"] is True
    assert exported["chain"]["valid"] is True


def test_memory_brain_v2_creates_fact_preference_decision_with_provenance(tmp_path):
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis")

    fact = store.propose_fact(
        subject="PR #164",
        predicate="implements",
        object_summary="persistent audit and Memory Brain v2",
        provenance={"source": "operator_note", "evidence": "PR scope", "evidence_state": "provided"},
        reason_to_remember="Track current implementation scope.",
        influence_summary="Helps explain dashboard memory counts.",
    )
    preference = store.propose_preference(
        subject="David",
        preference="local-first safe stores",
        provenance={"source": "operator_instruction", "evidence_state": "provided"},
    )
    decision = store.propose_decision(
        project="JARVIS",
        decision="Use SQLite before vector or graph DB",
        provenance={"source": "architecture_review", "evidence_state": "provided"},
    )

    assert fact["memory_type"] == "fact"
    assert fact["provenance"]["source"] == "operator_note"
    assert fact["provenance"]["evidence_state"] == "provided"
    assert preference["memory_type"] == "preference"
    assert decision["memory_type"] == "decision"
    counts = store.status()["counts"]
    assert counts["facts"] == 1
    assert counts["preferences"] == 1
    assert counts["decisions"] == 1
    assert counts["pending_review"] == 3


def test_memory_sensitive_requires_review_approval_and_never_grants_permissions(tmp_path):
    audit = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis", audit_ledger=audit)

    memory = store.propose_preference(
        subject="David",
        preference="private local routine context",
        sensitivity="sensitive",
        explicit_user_request=True,
        provenance={"source": "explicit_user_request", "evidence_state": "provided"},
    )

    assert memory["approval_required"] is True
    assert memory["review_required"] is True
    assert memory["approved"] is False
    assert memory["active"] is False
    with pytest.raises(ValueError):
        store.activate_memory(memory["memory_id"])

    reviewed = store.review_memory(memory["memory_id"])
    approved = store.approve_memory(memory["memory_id"])
    activated = store.activate_memory(memory["memory_id"], reason="Use only as explanatory context.")

    assert reviewed["review_required"] is False
    assert approved["approved"] is True
    assert approved["active"] is False
    assert activated["active"] is True
    assert activated["memory_grants_permission"] is False
    assert store.permission_effect(memory["memory_id"])["can_dispatch_hermes"] is False
    assert audit.status()["state"]["event_count"] >= 4


def test_memory_contradiction_supersedes_old_fact_and_unknown_is_preserved(tmp_path):
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis")
    old = store.propose_fact(
        subject="JARVIS memory backend",
        predicate="is",
        object_summary="unknown",
        provenance={"source": "operator_note"},
        reason_to_remember="Keep uncertainty visible.",
    )
    store.review_memory(old["memory_id"])
    store.approve_memory(old["memory_id"])
    store.activate_memory(old["memory_id"])

    result = store.supersede_memory(
        old["memory_id"],
        new_content_summary="JARVIS memory backend is SQLite local.",
        reason="New implementation evidence exists.",
    )

    superseded = result["superseded_memory"]
    replacement = result["replacement_memory"]
    assert old["confidence"] == "unknown"
    assert old["provenance"]["evidence_state"] == "unknown"
    assert superseded["active"] is False
    assert superseded["superseded_at"]
    assert superseded["superseded_by"] == replacement["memory_id"]
    assert store.status()["counts"]["contradictions"] == 1


def test_memory_forget_delete_deactivate_are_audited_and_persisted(tmp_path):
    audit = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis", audit_ledger=audit)
    memory = store.propose_decision(
        project="JARVIS",
        decision="Keep dashboard read-only",
        provenance={"source": "operator_note", "evidence_state": "provided"},
        reason_to_remember="Preserve safety boundary.",
        influence_summary="Explains why UI has no approve/execute buttons.",
    )
    store.review_memory(memory["memory_id"])
    store.approve_memory(memory["memory_id"])
    store.activate_memory(memory["memory_id"])
    deactivated = store.deactivate_memory(memory["memory_id"], reason="No longer needed in active context.")
    forgotten = store.forget_memory(memory["memory_id"], reason="Operator requested removal from active recall.")

    assert deactivated["active"] is False
    assert forgotten["forgotten"] is True
    assert forgotten["deleted"] is False
    assert store.why_remember(memory["memory_id"])["reason_to_remember"] == "Preserve safety boundary."
    assert store.why_used(memory["memory_id"])["used_for_permission"] is False
    audit_types = {event["event_type"] for event in store.audit_events(limit=20)}
    assert "memory_proposal_deactivated" in audit_types
    assert "memory_proposal_forgotten" in audit_types

    db_path = store.db_path
    store.close()
    reloaded = MemoryBrainV2Store(db_path=db_path)
    assert reloaded.get_memory(memory["memory_id"])["forgotten"] is True
    assert reloaded.status()["counts"]["forgotten_deleted"] == 1


def test_memory_rejects_secrets_credentials_and_sensitive_attributes_without_explicit_request(tmp_path):
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis")

    with pytest.raises(ValueError, match="secret or credential"):
        store.propose_fact(
            subject="credential",
            predicate="is",
            object_summary="password hunter2 from .env",
            provenance={"source": "operator_note"},
        )

    with pytest.raises(ValueError, match="explicit user request"):
        store.propose_fact(
            subject="David health profile",
            predicate="is",
            object_summary="medical detail",
            provenance={"source": "operator_note"},
        )

    assert store.status()["counts"]["total"] == 0


def test_memory_active_read_model_does_not_autoload_dangerously(tmp_path):
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis")
    status = store.status()

    assert status["state"]["memory_autoload_enabled"] is False
    assert status["state"]["memory_auto_activation_enabled"] is False
    assert status["state"]["memory_grants_permission"] is False
    assert status["safety"]["execution_enabled"] is False
    assert status["safety"]["hermes_dispatch_allowed"] is False


def test_dashboard_status_and_event_stream_include_persistent_audit_and_memory_brain_v2(tmp_path):
    audit = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")
    memory = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis", audit_ledger=audit)
    audit.record(event_type="wake_disabled", surface="wake", metadata={"status": "disabled"})
    fact = memory.propose_fact(
        subject="PR #164",
        predicate="is",
        object_summary="prepare-only",
        provenance={"source": "test", "evidence_state": "provided"},
        reason_to_remember="Explain PR safety scope.",
        influence_summary="No execution should be triggered.",
    )
    memory.review_memory(fact["memory_id"])

    app = create_app(
        adapter_factory=lambda: pytest.fail("Hermes must not be called"),
        persistent_audit_ledger=audit,
        memory_brain_v2=memory,
    )
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}
    assert ("/mark-3/audit/status", "GET") in routes
    assert ("/mark-3/memory-brain/status", "GET") in routes
    assert ("/mark-3/memory-brain/preview", "GET") in routes
    for path in ("/mark-3/audit/status", "/mark-3/memory-brain/status", "/mark-3/memory-brain/preview"):
        for method in ("POST", "PUT", "DELETE"):
            assert (path, method) not in routes

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["persistent_audit"]["schema_version"] == "jarvis.persistent_audit.v1"
    assert dashboard["persistent_audit"]["chain"]["valid"] is True
    assert dashboard["memory_brain_v2"]["schema_version"] == "jarvis.memory_brain_v2.v1"
    assert dashboard["memory_brain"]["counts"]["facts"] == 1
    assert dashboard["memory_brain"]["counts"]["pending_review"] == 0
    assert dashboard["local_doctor"]["state"]["persistent_audit_endpoint"] is True
    assert dashboard["local_doctor"]["state"]["memory_brain_v2_endpoint"] is True

    snapshot = build_jarvis_event_snapshot(dashboard_status=dashboard, generated_at="2026-06-19T00:00:00+00:00")
    events = {event["event_type"]: event for event in snapshot["events"]}
    assert "persistent_audit_state" in events
    assert "memory_brain_v2_state" in events
    assert events["persistent_audit_state"]["payload"]["metadata_only"] is True
    assert events["persistent_audit_state"]["payload"]["contains_raw_audio"] is False
    assert events["persistent_audit_state"]["payload"]["contains_camera_frame"] is False
    assert events["persistent_audit_state"]["payload"]["contains_credential"] is False
    assert events["memory_brain_v2_state"]["payload"]["memory_grants_permission"] is False
    serialized = json.dumps(snapshot, sort_keys=True).lower()
    for forbidden in ("audio_bytes", "frame_bytes", "password", "api_key", "cookie", "bearer ", "command_to_execute", "execute_payload"):
        assert forbidden not in serialized


def test_jarvis_ui_shows_audit_memory_status_and_keeps_forbidden_contracts():
    source = _jarvis_ui_source()
    smart_bar = (WEB / "src/components/jarvis/JarvisSmartBar.tsx").read_text(encoding="utf-8")

    for marker in (
        "Persistent Audit",
        "Memory Brain v2",
        "hash-chain",
        "tamper-evident",
        "active memories",
        "pending review",
        "forgotten/deleted",
        "metadata-only",
    ):
        assert marker in source
    assert "No puedo hacer eso, David. Las credenciales y secretos están protegidos." in smart_bar
    assert "HermesRuntimeAdapter" not in source
    assert "AIAgent" not in source
    assert not re.search(r'fetch\([^)]*["\']/execute', source)
    assert ".getUserMedia(" not in (WEB / "src/hooks/jarvis/useLocalVoiceLoop.ts").read_text(encoding="utf-8")
    assert "beginLocalVoiceLoop()" not in (WEB / "src/pages/JarvisCommandCenterPage.tsx").read_text(encoding="utf-8")
    assert "startCameraPreview()" not in (WEB / "src/pages/JarvisCommandCenterPage.tsx").read_text(encoding="utf-8")
    assert "startRecording()" not in (WEB / "src/pages/JarvisCommandCenterPage.tsx").read_text(encoding="utf-8")
