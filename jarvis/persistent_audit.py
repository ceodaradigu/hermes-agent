from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
from uuid import uuid4


PERSISTENT_AUDIT_SCHEMA_VERSION = "jarvis.persistent_audit.v1"
PERSISTENT_AUDIT_DB_RELATIVE_PATH = Path(".jarvis") / "audit" / "persistent_audit.sqlite3"
GENESIS_HASH = "GENESIS"

AUDIT_EVENT_TYPES = {
    "voice_session_requested",
    "voice_session_started",
    "voice_session_stopped",
    "voice_session_cancelled",
    "voice_session_failed",
    "wake_requested",
    "wake_available",
    "wake_disabled",
    "wake_started",
    "wake_stopped",
    "wake_cancelled",
    "wake_failed",
    "stt_status",
    "stt_provider",
    "stt_missing",
    "stt_unavailable",
    "stt_transcript_lifecycle",
    "tts_status",
    "tts_provider",
    "tts_missing",
    "tts_unavailable",
    "tts_speaking",
    "tts_cancelled",
    "tts_interrupted",
    "recording_local_requested",
    "recording_local_started",
    "recording_local_stopped",
    "recording_local_deleted",
    "recording_local_retention_updated",
    "camera_requested",
    "camera_started",
    "camera_stopped",
    "camera_cancelled",
    "camera_failed",
    "conversational_intake_created",
    "conversational_intake_classified",
    "conversational_intake_blocked",
    "conversational_intake_clarification_required",
    "brain_adapter_request",
    "brain_adapter_response",
    "memory_proposal_created",
    "memory_proposal_reviewed",
    "memory_proposal_approved",
    "memory_proposal_rejected",
    "memory_proposal_activated",
    "memory_proposal_deactivated",
    "memory_proposal_forgotten",
    "memory_proposal_deleted",
    "intake_created",
    "preview_created",
    "risk_classified",
    "approval_requested",
    "approval_approved",
    "approval_rejected",
    "approval_cancelled",
    "approval_expired",
    "dispatch_requested",
    "dispatch_started",
    "dispatch_blocked",
    "dispatch_completed",
    "dispatch_failed",
    "stop_requested",
    "stop_completed",
    "stop_unsupported",
    "rollback_plan_created",
    "rollback_requested",
    "rollback_completed",
    "rollback_unsupported",
    "rollback_failed",
    "execution_history_recorded",
    "memory_influence_used",
    "voice_session_intent_submitted",
    "ui_approval_action",
    "approval_required",
    "approval_blocked",
    "approval_expired",
    "approval_step_requested",
    "approval_step_approved",
    "approval_step_rejected",
    "approval_step_expired",
    "trusted_channel_verified",
    "trusted_channel_rejected",
    "daemon_heartbeat",
    "daemon_stop_requested",
    "daemon_restart_requested",
    "local_controller_registered",
    "local_controller_heartbeat",
    "local_controller_open_requested",
    "local_controller_stop_requested",
    "trusted_device_registered",
    "trusted_device_revoked",
    "trusted_device_seen",
    "trusted_device_import_rejected",
    "remote_pairing_prepared",
    "remote_pairing_cancelled",
    "remote_pairing_revoked",
    "local_pairing_challenge_created",
    "local_pairing_challenge_failed",
    "local_pairing_challenge_rate_limited",
    "local_pairing_challenge_consumed",
    "local_pairing_challenge_expired",
    "voice_approval_session_started",
    "voice_approval_readback_presented",
    "voice_approval_accepted",
    "voice_approval_denied",
    "voice_approval_expired",
    "voice_approval_replay_rejected",
    "voice_approval_wake_phrase_rejected",
    "notification_readiness_event",
    "local_controller_opt_in_changed",
    "local_controller_start_requested",
    "local_controller_kill_switch_changed",
    "stop_rollback_status_read",
    "rollback_dry_run_recorded",
    "hermes_dispatch_blocked",
    "hermes_dispatch_disabled",
    "preflight_completed",
    "filesystem_backup_created",
    "filesystem_write_completed",
    "phase_8_status_read",
    "remote_channel_status_read",
    "remote_channel_pairing_challenge_created",
    "remote_channel_pairing_challenge_consumed",
    "remote_channel_pairing_challenge_failed",
    "remote_channel_revoked",
    "remote_kill_switch_changed",
    "remote_approval_intent_received",
    "remote_approval_intent_rejected",
    "telegram_readiness_checked",
    "external_operation_envelope_created",
    "external_operation_candidate_prepared",
    "budget_guard_evaluated",
    "revenue_event_recorded",
}

_SENSITIVE_KEY_MARKERS: Iterable[str] = (
    ".env",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "credential",
    "frame",
    "frames",
    "image",
    "password",
    "private_key",
    "raw_audio",
    "audio_bytes",
    "audio_blob",
    "audio_buffer",
    "secret",
    "session_material",
    "token",
    "video",
    "video_bytes",
)

_SENSITIVE_TEXT_MARKERS: Iterable[str] = (
    ".env",
    "api key",
    "api-key",
    "api_key",
    "apikey",
    "authorization:",
    "bearer ",
    "cookie",
    "credential",
    "password",
    "private key",
    "private-key",
    "private_key",
    "raw audio",
    "secret",
    "session material",
    "sk-",
    "token",
)

_RAW_TEXT_KEY_MARKERS: Iterable[str] = (
    "full_transcript",
    "raw_transcript",
    "transcript_text",
    "raw_text",
    "normalized_text",
    "prompt",
    "utterance",
)


@dataclass(frozen=True)
class AuditChainVerification:
    valid: bool
    checked_count: int
    first_invalid_audit_id: Optional[str] = None
    first_invalid_reason: Optional[str] = None
    last_entry_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "checked_count": self.checked_count,
            "first_invalid_audit_id": self.first_invalid_audit_id,
            "first_invalid_reason": self.first_invalid_reason,
            "last_entry_hash": self.last_entry_hash,
        }


class PersistentAuditLedger:
    """Local metadata-only audit ledger with a simple SHA-256 hash chain."""

    def __init__(
        self,
        *,
        base_dir: str | Path | None = None,
        db_path: str | Path | None = None,
        clock: Any = None,
        id_factory: Any = None,
    ) -> None:
        if db_path is not None and base_dir is not None:
            raise ValueError("Use either db_path or base_dir, not both.")
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._lock = Lock()
        self._persistent = db_path is not None or base_dir is not None
        self._base_dir = Path(base_dir) if base_dir is not None else None
        self._db_path = Path(db_path) if db_path is not None else (
            self._base_dir / "audit" / "persistent_audit.sqlite3" if self._base_dir else None
        )
        if self._db_path is None:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            if any(part == ".." for part in self._db_path.parts):
                raise ValueError("db_path/base_dir must not contain path traversal.")
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._initialize()

    @classmethod
    def from_environment(cls) -> "PersistentAuditLedger":
        base_dir = os.environ.get("JARVIS_LOCAL_STATE_DIR") or os.environ.get("JARVIS_STATE_DIR")
        if base_dir:
            return cls(base_dir=base_dir)
        return cls()

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    def close(self) -> None:
        self._conn.close()

    def record(
        self,
        *,
        event_type: str,
        surface: str = "control_plane",
        source: str = "jarvis",
        risk_level: str = "low",
        approval_level: str = "direct",
        session_id: str | None = None,
        correlation_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        created_at: str | None = None,
        contains_full_transcript: bool = False,
        hermes_dispatch_allowed: bool = False,
    ) -> Dict[str, Any]:
        normalized_event_type = _safe_slug(event_type)
        if normalized_event_type not in AUDIT_EVENT_TYPES:
            raise ValueError(f"Unsupported audit event type: {event_type}")

        safe_metadata, redaction_summary = sanitize_audit_metadata(metadata or {})
        if contains_full_transcript:
            redaction_summary = _merge_redaction_summary(redaction_summary, blocked_field_count=1, category="raw_text_payload")
        governed_dispatch_allowed = (
            bool(hermes_dispatch_allowed)
            and normalized_event_type in {"dispatch_started", "dispatch_completed"}
            and safe_metadata.get("governed_dispatch") is True
        )
        if hermes_dispatch_allowed and not governed_dispatch_allowed:
            redaction_summary = _merge_redaction_summary(redaction_summary, blocked_field_count=1, category="dispatch_gate_forced_closed")

        with self._lock:
            previous_hash = self._last_entry_hash()
            audit_id = f"audit-{self.id_factory()}"
            row = {
                "schema_version": PERSISTENT_AUDIT_SCHEMA_VERSION,
                "audit_id": audit_id,
                "created_at": created_at or self.clock(),
                "event_type": normalized_event_type,
                "surface": _safe_text(surface, "control_plane", limit=120),
                "source": _safe_text(source, "jarvis", limit=160),
                "risk_level": _safe_text(risk_level, "low", limit=80),
                "approval_level": _safe_text(approval_level, "direct", limit=80),
                "session_id": _safe_text(session_id, "unknown", limit=120),
                "correlation_id": _safe_text(correlation_id, self.id_factory(), limit=120),
                "metadata": safe_metadata,
                "redaction_summary": redaction_summary,
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "contains_secret": False,
                "contains_credential": False,
                "contains_full_transcript": False,
                "hermes_dispatch_allowed": governed_dispatch_allowed,
                "previous_hash": previous_hash,
                "tamper_evident": True,
            }
            entry_hash = _entry_hash(row)
            row["entry_hash"] = entry_hash
            self._conn.execute(
                """
                INSERT INTO audit_entries (
                    schema_version, audit_id, created_at, event_type, surface, source,
                    risk_level, approval_level, session_id, correlation_id, metadata_json,
                    redaction_summary_json, contains_raw_audio, contains_camera_frame,
                    contains_secret, contains_credential, contains_full_transcript,
                    hermes_dispatch_allowed, previous_hash, entry_hash, tamper_evident
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["schema_version"],
                    row["audit_id"],
                    row["created_at"],
                    row["event_type"],
                    row["surface"],
                    row["source"],
                    row["risk_level"],
                    row["approval_level"],
                    row["session_id"],
                    row["correlation_id"],
                    _json_dumps(row["metadata"]),
                    _json_dumps(row["redaction_summary"]),
                    0,
                    0,
                    0,
                    0,
                    0,
                    int(governed_dispatch_allowed),
                    row["previous_hash"],
                    row["entry_hash"],
                    1,
                ),
            )
            self._conn.commit()
            return dict(row)

    def list_entries(self, *, limit: int = 25, newest_first: bool = True) -> List[Dict[str, Any]]:
        limit = max(0, min(int(limit), 200))
        if limit == 0:
            return []
        order = "DESC" if newest_first else "ASC"
        rows = self._conn.execute(
            f"SELECT * FROM audit_entries ORDER BY id {order} LIMIT ?",
            (limit,),
        ).fetchall()
        entries = [_row_to_entry(row) for row in rows]
        return entries

    def status(self, *, recent_limit: int = 5) -> Dict[str, Any]:
        count = int(self._conn.execute("SELECT COUNT(*) FROM audit_entries").fetchone()[0])
        verification = self.verify_chain()
        return {
            "schema_version": PERSISTENT_AUDIT_SCHEMA_VERSION,
            "state": {
                "mode": "persistent_metadata_audit_ledger" if self._persistent else "in_memory_metadata_audit_ledger",
                "available": True,
                "persistent": self._persistent,
                "local_only": True,
                "metadata_only": True,
                "event_count": count,
                "storage_path": str(self._db_path) if self._db_path else str(PERSISTENT_AUDIT_DB_RELATIVE_PATH),
                "storage_configured": self._db_path is not None,
                "default_relative_path": str(PERSISTENT_AUDIT_DB_RELATIVE_PATH),
                "tamper_evident": True,
                "hash_chain_valid": verification.valid,
                "last_entry_hash": verification.last_entry_hash,
            },
            "chain": verification.to_dict(),
            "supported_event_types": sorted(AUDIT_EVENT_TYPES),
            "recent_entries": self.list_entries(limit=recent_limit),
            "retention": {
                "policy": "append_only_metadata_until_operator_rotation",
                "raw_media_retention": "not_applicable",
                "safe_export_available": True,
                "hard_delete_policy": "not_implemented_for_audit_entries",
            },
            "safety": {
                "metadata_only": True,
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "contains_secret": False,
                "contains_credential": False,
                "contains_full_transcript": False,
                "hermes_dispatch_allowed": False,
                "frontend_can_mutate": False,
                "read_only_from_jarvis": True,
            },
            "source_endpoint": "/mark-3/audit/status",
            "read_only": True,
        }

    def export_snapshot(self, *, limit: int = 100) -> Dict[str, Any]:
        verification = self.verify_chain()
        return {
            "schema_version": PERSISTENT_AUDIT_SCHEMA_VERSION,
            "exported_at": self.clock(),
            "metadata_only": True,
            "tamper_evident": True,
            "chain": verification.to_dict(),
            "entries": self.list_entries(limit=limit, newest_first=False),
            "safety": {
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "contains_secret": False,
                "contains_credential": False,
                "contains_full_transcript": False,
                "hermes_dispatch_allowed": False,
            },
        }

    def verify_chain(self) -> AuditChainVerification:
        rows = self._conn.execute("SELECT * FROM audit_entries ORDER BY id ASC").fetchall()
        previous = GENESIS_HASH
        last_hash: Optional[str] = None
        for index, row in enumerate(rows, start=1):
            entry = _row_to_entry(row)
            if entry["previous_hash"] != previous:
                return AuditChainVerification(
                    valid=False,
                    checked_count=index,
                    first_invalid_audit_id=entry["audit_id"],
                    first_invalid_reason="previous_hash_mismatch",
                    last_entry_hash=last_hash,
                )
            expected = _entry_hash({key: value for key, value in entry.items() if key != "entry_hash"})
            if entry["entry_hash"] != expected:
                return AuditChainVerification(
                    valid=False,
                    checked_count=index,
                    first_invalid_audit_id=entry["audit_id"],
                    first_invalid_reason="entry_hash_mismatch",
                    last_entry_hash=last_hash,
                )
            previous = entry["entry_hash"]
            last_hash = entry["entry_hash"]
        return AuditChainVerification(valid=True, checked_count=len(rows), last_entry_hash=last_hash)

    def _initialize(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schema_version TEXT NOT NULL,
                audit_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                surface TEXT NOT NULL,
                source TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                approval_level TEXT NOT NULL,
                session_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                redaction_summary_json TEXT NOT NULL,
                contains_raw_audio INTEGER NOT NULL DEFAULT 0,
                contains_camera_frame INTEGER NOT NULL DEFAULT 0,
                contains_secret INTEGER NOT NULL DEFAULT 0,
                contains_credential INTEGER NOT NULL DEFAULT 0,
                contains_full_transcript INTEGER NOT NULL DEFAULT 0,
                hermes_dispatch_allowed INTEGER NOT NULL DEFAULT 0,
                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL,
                tamper_evident INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_entries_created_at ON audit_entries(created_at)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_entries_correlation_id ON audit_entries(correlation_id)")
        self._conn.commit()

    def _last_entry_hash(self) -> str:
        row = self._conn.execute(
            "SELECT entry_hash FROM audit_entries ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return str(row[0]) if row else GENESIS_HASH


def sanitize_audit_metadata(metadata: Mapping[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    blocked_count = 0
    categories: List[str] = []

    def sanitize_mapping(values: Mapping[str, Any]) -> Dict[str, Any]:
        nonlocal blocked_count
        safe: Dict[str, Any] = {}
        for key, value in values.items():
            key_text = _safe_text(key, "unknown_key", limit=80)
            if _is_sensitive_key(key_text):
                blocked_count += 1
                _append_unique(categories, "credential_material")
                continue
            if _is_raw_text_key(key_text):
                blocked_count += 1
                _append_unique(categories, "raw_text_payload")
                continue
            safe[key_text] = sanitize_value(value)
        return safe

    def sanitize_value(value: Any) -> Any:
        nonlocal blocked_count
        if isinstance(value, Mapping):
            return sanitize_mapping(value)
        if isinstance(value, list):
            return [sanitize_value(item) for item in value[:20]]
        if isinstance(value, tuple):
            return [sanitize_value(item) for item in value[:20]]
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, (int, float)):
            return value
        text = _safe_text(value, "unknown", limit=500)
        if _contains_sensitive_text(text):
            blocked_count += 1
            _append_unique(categories, "credential_material")
            return "[redacted]"
        return text

    safe_metadata = sanitize_mapping(metadata)
    summary = {
        "metadata_only": True,
        "redacted": blocked_count > 0,
        "blocked_field_count": blocked_count,
        "blocked_categories": categories,
        "raw_payload_stored": False,
    }
    return safe_metadata, summary


def _row_to_entry(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "schema_version": row["schema_version"],
        "audit_id": row["audit_id"],
        "created_at": row["created_at"],
        "event_type": row["event_type"],
        "surface": row["surface"],
        "source": row["source"],
        "risk_level": row["risk_level"],
        "approval_level": row["approval_level"],
        "session_id": row["session_id"],
        "correlation_id": row["correlation_id"],
        "metadata": _json_loads(row["metadata_json"]),
        "redaction_summary": _json_loads(row["redaction_summary_json"]),
        "contains_raw_audio": bool(row["contains_raw_audio"]),
        "contains_camera_frame": bool(row["contains_camera_frame"]),
        "contains_secret": bool(row["contains_secret"]),
        "contains_credential": bool(row["contains_credential"]),
        "contains_full_transcript": bool(row["contains_full_transcript"]),
        "hermes_dispatch_allowed": bool(row["hermes_dispatch_allowed"]),
        "previous_hash": row["previous_hash"],
        "entry_hash": row["entry_hash"],
        "tamper_evident": bool(row["tamper_evident"]),
    }


def _entry_hash(entry: Mapping[str, Any]) -> str:
    payload = _json_dumps(dict(entry))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _json_loads(value: str) -> Any:
    return json.loads(value or "{}")


def _merge_redaction_summary(summary: Dict[str, Any], *, blocked_field_count: int, category: str) -> Dict[str, Any]:
    merged = dict(summary)
    merged["redacted"] = True
    merged["blocked_field_count"] = int(merged.get("blocked_field_count", 0)) + blocked_field_count
    categories = list(merged.get("blocked_categories", []))
    _append_unique(categories, category)
    merged["blocked_categories"] = categories
    return merged


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_").replace(" ", "_")
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _is_raw_text_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_").replace(" ", "_")
    return any(marker in normalized for marker in _RAW_TEXT_KEY_MARKERS)


def _contains_sensitive_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _SENSITIVE_TEXT_MARKERS)


def _safe_slug(value: Any) -> str:
    return _safe_text(value, "unknown", limit=120).lower().replace("-", "_").replace(" ", "_")


def _safe_text(value: Any, fallback: str, *, limit: int) -> str:
    text = " ".join(str(value or "").strip().split())
    return (text or fallback)[:limit]


def _append_unique(values: List[str], item: str) -> None:
    if item not in values:
        values.append(item)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
