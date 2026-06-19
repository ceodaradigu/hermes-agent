from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.phase_2_local_assistant_runtime import (
    _normalize_readback,
    _safe_text,
)
from jarvis.phase_3_local_runtime import TRUSTED_CHANNEL_SCHEMA_VERSION, _is_expired
from jarvis.phase_4_local_controller_remote_pairing import (
    REMOTE_PAIRING_TTL_SECONDS,
    TERMINAL_VERIFICATION_PHRASE,
    Phase4LocalControllerRemotePairingControlPlane,
)


PHASE_5_SCHEMA_VERSION = "jarvis.phase_5_local_controller_trusted_identity_voice_approval.v1"
TRUSTED_DEVICE_STORE_SCHEMA_VERSION = "jarvis.trusted_device_identity.v1"
LOCAL_PAIRING_SCHEMA_VERSION = "jarvis.local_pairing.v1"
VOICE_APPROVAL_SCHEMA_VERSION = "jarvis.voice_approval_contract.v1"
NOTIFICATION_READINESS_SCHEMA_VERSION = "jarvis.notification_readiness.v1"
PHASE_5_STATE_DB_RELATIVE_PATH = Path(".jarvis") / "phase_5" / "phase_5.sqlite3"

PAIRING_TTL_SECONDS = 180
PAIRING_MAX_FAILED_ATTEMPTS = 3
PAIRING_LOCKOUT_SECONDS = 120
VOICE_APPROVAL_TTL_SECONDS = 180
VOICE_APPROVAL_ALLOWED_LEVELS = {"normal", "strong"}
VOICE_APPROVAL_ALLOWED_RISKS = {"low", "medium", "high"}
VOICE_APPROVAL_PHRASES = (
    "jarvis autorizo",
    "jarvis confirmo",
    "jarvis apruebo esta accion",
    "jarvis autorizo con limite de x euros",
    "jarvis autorizo durante x minutos",
)
VOICE_DENY_PHRASES = (
    "jarvis cancela",
    "jarvis deniega",
)
WAKE_ONLY_PHRASES = {"jarvis", "hola jarvis"}


@dataclass(frozen=True)
class VoiceApprovalSession:
    session_id: str
    approval_id: str
    device_id: str
    voice_session_id: str
    action_id: str
    action_key: str
    risk_level: str
    approval_level: str
    scope_fingerprint: str
    cost_summary: str
    cost_limit_eur: Optional[float]
    duration_seconds: int
    readback_text_hash: str
    expected_challenge: str
    accepted_phrases: List[str]
    created_at: str
    expires_at: str
    active: bool = True
    readback_presented: bool = False
    active_voice_session_verified: bool = True
    opened_by_wake_only: bool = False
    consumed_at: Optional[str] = None
    denied_at: Optional[str] = None
    audit_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["raw_audio_stored"] = False
        data["transcript_stored"] = False
        data["metadata_only"] = True
        return data


class Phase5IdentityStore:
    """Local SQLite store for trusted identity, pairing, voice replay, and notifications."""

    def __init__(
        self,
        *,
        base_dir: str | Path | None = None,
        db_path: str | Path | None = None,
        clock: Any = None,
    ) -> None:
        if db_path is not None and base_dir is not None:
            raise ValueError("Use either db_path or base_dir, not both.")
        self.clock = clock or _now_iso
        self._lock = RLock()
        self._persistent = db_path is not None or base_dir is not None
        self._base_dir = Path(base_dir) if base_dir is not None else None
        self._db_path = Path(db_path) if db_path is not None else (
            self._base_dir / "phase_5" / "phase_5.sqlite3" if self._base_dir else None
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
    def from_environment(cls) -> "Phase5IdentityStore":
        base_dir = os.environ.get("JARVIS_LOCAL_STATE_DIR") or os.environ.get("JARVIS_STATE_DIR")
        if base_dir:
            return cls(base_dir=base_dir)
        return cls()

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    def close(self) -> None:
        self._conn.close()

    def bootstrap_local_browser(self) -> Dict[str, Any]:
        return self.upsert_trusted_device(
            device_id="device-ui_local_browser",
            display_name="Local browser",
            channel_type="local_browser",
            public_identifier="jarvis-local-loopback-browser",
            fingerprint_material="jarvis-local-loopback-browser",
            capabilities={
                "can_grant_normal": True,
                "can_grant_strong": True,
                "can_grant_double": True,
                "can_grant_triple": True,
                "voice_approval": False,
            },
            approval_scope=["local", "approval", "readback", "ui_local_browser"],
            metadata={"source": "backend_local_loopback_bootstrap"},
            trust_source="backend_local_loopback_bootstrap",
            local_only=True,
        )

    def upsert_trusted_device(
        self,
        *,
        device_id: str,
        display_name: str,
        channel_type: str,
        public_identifier: str,
        fingerprint_material: str,
        capabilities: Mapping[str, Any],
        approval_scope: Iterable[str],
        metadata: Optional[Mapping[str, Any]] = None,
        trust_source: str,
        paired_challenge_id: str = "",
        local_only: bool = True,
    ) -> Dict[str, Any]:
        safe_device_id = _safe_slug(device_id, "device-unknown")
        now = self.clock()
        public_hash = _hash_text(public_identifier)
        fingerprint_hash = _hash_text(fingerprint_material)
        safe_capabilities = _safe_json_dict(capabilities)
        safe_scope = _safe_json_list(approval_scope)
        safe_metadata = _redacted_metadata(metadata or {})
        with self._lock:
            existing = self._device_row(safe_device_id)
            if existing and existing["trust_status"] == "revoked":
                return _row_to_device(existing)
            created_at = existing["created_at"] if existing else now
            self._conn.execute(
                """
                INSERT INTO trusted_devices (
                    device_id, display_name, channel_type, public_identifier_hash,
                    fingerprint_hash, trust_status, trusted, verified, paired,
                    local_only, created_at, last_seen_at, revoked_at,
                    revocation_reason, capabilities_json, approval_scope_json,
                    metadata_json, trust_source, paired_challenge_id,
                    imported_claimed_trust
                )
                VALUES (?, ?, ?, ?, ?, 'trusted', 1, 1, 1, ?, ?, ?, '', '', ?, ?, ?, ?, ?, 0)
                ON CONFLICT(device_id) DO UPDATE SET
                    display_name=excluded.display_name,
                    channel_type=excluded.channel_type,
                    public_identifier_hash=excluded.public_identifier_hash,
                    fingerprint_hash=excluded.fingerprint_hash,
                    trust_status=CASE WHEN trusted_devices.trust_status='revoked' THEN trusted_devices.trust_status ELSE 'trusted' END,
                    trusted=CASE WHEN trusted_devices.trust_status='revoked' THEN 0 ELSE 1 END,
                    verified=CASE WHEN trusted_devices.trust_status='revoked' THEN 0 ELSE 1 END,
                    paired=CASE WHEN trusted_devices.trust_status='revoked' THEN 0 ELSE 1 END,
                    local_only=excluded.local_only,
                    last_seen_at=excluded.last_seen_at,
                    capabilities_json=excluded.capabilities_json,
                    approval_scope_json=excluded.approval_scope_json,
                    metadata_json=excluded.metadata_json,
                    trust_source=excluded.trust_source,
                    paired_challenge_id=excluded.paired_challenge_id
                """,
                (
                    safe_device_id,
                    _safe_text(display_name, limit=120),
                    _safe_slug(channel_type, "unknown"),
                    public_hash,
                    fingerprint_hash,
                    int(bool(local_only)),
                    created_at,
                    now,
                    _json_dumps(safe_capabilities),
                    _json_dumps(safe_scope),
                    _json_dumps(safe_metadata),
                    _safe_text(trust_source, limit=120),
                    _safe_text(paired_challenge_id, limit=160),
                ),
            )
            self._conn.commit()
            return self.get_device(safe_device_id) or {}

    def mark_seen(self, device_id: str) -> Optional[Dict[str, Any]]:
        safe_device_id = _safe_slug(device_id, "device-unknown")
        with self._lock:
            row = self._device_row(safe_device_id)
            if not row:
                return None
            if row["trust_status"] != "revoked":
                self._conn.execute("UPDATE trusted_devices SET last_seen_at=? WHERE device_id=?", (self.clock(), safe_device_id))
                self._conn.commit()
            return self.get_device(safe_device_id)

    def revoke_device(self, device_id: str, *, reason: str = "operator revoke") -> Optional[Dict[str, Any]]:
        safe_device_id = _safe_slug(device_id, "device-unknown")
        with self._lock:
            row = self._device_row(safe_device_id)
            now = self.clock()
            if row:
                self._conn.execute(
                    """
                    UPDATE trusted_devices
                    SET trust_status='revoked', trusted=0, verified=0, paired=0,
                        revoked_at=?, revocation_reason=?
                    WHERE device_id=?
                    """,
                    (now, _safe_text(reason, limit=240), safe_device_id),
                )
            else:
                self._conn.execute(
                    """
                    INSERT INTO trusted_devices (
                        device_id, display_name, channel_type, public_identifier_hash,
                        fingerprint_hash, trust_status, trusted, verified, paired, local_only,
                        created_at, last_seen_at, revoked_at, revocation_reason,
                        capabilities_json, approval_scope_json, metadata_json,
                        trust_source, paired_challenge_id, imported_claimed_trust
                    )
                    VALUES (?, ?, 'unknown', '', '', 'revoked', 0, 0, 0, 1, ?, ?, ?, ?, '{}', '[]', '{}', 'operator_revoke_unknown_device', '', 0)
                    """,
                    (safe_device_id, safe_device_id, now, now, now, _safe_text(reason, limit=240)),
                )
            self._conn.commit()
            return self.get_device(safe_device_id)

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        row = self._device_row(_safe_slug(device_id, "device-unknown"))
        return _row_to_device(row) if row else None

    def list_devices(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM trusted_devices ORDER BY created_at ASC, device_id ASC").fetchall()
        return [_row_to_device(row) for row in rows]

    def import_preview(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        claimed_id = _safe_slug(payload.get("device_id") or "imported-device", "imported-device")
        return {
            "schema_version": TRUSTED_DEVICE_STORE_SCHEMA_VERSION,
            "import_status": "rejected_preview_only",
            "device_id": claimed_id,
            "claimed_trusted": bool(payload.get("trusted") or payload.get("verified") or payload.get("paired")),
            "trusted": False,
            "verified": False,
            "paired": False,
            "trust_status": "untrusted_import_preview",
            "persisted": False,
            "reason": "deserialization_import_cannot_create_trust_approval_execution_or_hermes_capability",
            "hermes_dispatch_allowed": False,
            "memory_grants_permission": False,
            "metadata_only": True,
        }

    def create_pairing_challenge(
        self,
        *,
        display_name: str,
        public_identifier: str,
        channel: str,
        scope: Iterable[str],
        capabilities: Optional[Mapping[str, Any]] = None,
        ttl_seconds: int = PAIRING_TTL_SECONDS,
        risk_limit: str = "high",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = self.clock()
        challenge_id = f"pairing-{uuid4()}"
        nonce = secrets.token_urlsafe(12)
        phrase = f"PAIR {challenge_id} {nonce}"
        expires_at = _after_seconds(max(30, min(int(ttl_seconds or PAIRING_TTL_SECONDS), REMOTE_PAIRING_TTL_SECONDS)))
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO pairing_challenges (
                    challenge_id, nonce_hash, phrase_hash, public_identifier_hash,
                    display_name, channel, scope_json, risk_limit, capabilities_json,
                    created_at, expires_at, used_at, failed_attempts, locked_until,
                    status, bound_device_id, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 0, '', 'pending', '', ?)
                """,
                (
                    challenge_id,
                    _hash_text(nonce),
                    _hash_text(phrase),
                    _hash_text(public_identifier),
                    _safe_text(display_name, limit=120),
                    _safe_slug(channel, "local_pairing"),
                    _json_dumps(_safe_json_list(scope)),
                    _safe_slug(risk_limit, "high"),
                    _json_dumps(_safe_json_dict(capabilities or _default_pairing_capabilities())),
                    now,
                    expires_at,
                    _json_dumps(_redacted_metadata(metadata or {})),
                ),
            )
            self._conn.commit()
        return {
            "schema_version": LOCAL_PAIRING_SCHEMA_VERSION,
            "pairing_status": "challenge_created",
            "challenge_id": challenge_id,
            "nonce": nonce,
            "challenge_phrase": phrase,
            "scope": _safe_json_list(scope),
            "risk_limit": _safe_slug(risk_limit, "high"),
            "created_at": now,
            "expires_at": expires_at,
            "one_time_use": True,
            "remote_execution_allowed": False,
            "remote_approval_allowed": False,
            "hermes_called": False,
            "metadata_only": True,
        }

    def verify_pairing_challenge(
        self,
        *,
        challenge_id: str,
        nonce: str,
        response_phrase: str,
        public_identifier: str,
        display_name: str,
        scope: Iterable[str],
    ) -> Dict[str, Any]:
        safe_challenge_id = _safe_text(challenge_id, limit=160)
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM pairing_challenges WHERE challenge_id=?",
                (safe_challenge_id,),
            ).fetchone()
            if not row:
                return self._pairing_failure(None, reason="pairing_challenge_not_found")
            challenge = _row_to_challenge(row)
            now = self.clock()
            if challenge["locked_until"] and not _expired_at(challenge["locked_until"], now=now):
                return self._pairing_failure(row, reason="pairing_rate_limited")
            if challenge["used_at"]:
                return self._pairing_failure(row, reason="pairing_challenge_already_used")
            if _expired_at(challenge["expires_at"], now=now):
                self._conn.execute("UPDATE pairing_challenges SET status='expired' WHERE challenge_id=?", (safe_challenge_id,))
                self._conn.commit()
                return self._pairing_failure(row, reason="pairing_challenge_expired")
            requested_scope = _safe_json_list(scope)
            exact = (
                _hash_text(nonce) == challenge["nonce_hash"]
                and _hash_text(response_phrase) == challenge["phrase_hash"]
                and _hash_text(public_identifier) == challenge["public_identifier_hash"]
                and requested_scope == challenge["scope"]
            )
            if not exact:
                return self._pairing_failure(row, reason="pairing_challenge_mismatch")
            device_id = f"device-{_hash_text(public_identifier)[:16]}"
            self._conn.execute(
                "UPDATE pairing_challenges SET used_at=?, status='consumed', bound_device_id=? WHERE challenge_id=?",
                (now, device_id, safe_challenge_id),
            )
            self._conn.commit()
        device = self.upsert_trusted_device(
            device_id=device_id,
            display_name=display_name or challenge["display_name"],
            channel_type=challenge["channel"],
            public_identifier=public_identifier,
            fingerprint_material=f"{public_identifier}:{safe_challenge_id}:{nonce}:{_json_dumps(requested_scope)}",
            capabilities=challenge["capabilities"],
            approval_scope=requested_scope,
            metadata={"paired_by": "local_pairing_challenge", "challenge_id": safe_challenge_id},
            trust_source="local_pairing_challenge",
            paired_challenge_id=safe_challenge_id,
            local_only=True,
        )
        return {
            "schema_version": LOCAL_PAIRING_SCHEMA_VERSION,
            "pairing_status": "trusted_device_bound",
            "challenge_id": safe_challenge_id,
            "device": device,
            "scope": requested_scope,
            "one_time_use_consumed": True,
            "remote_execution_allowed": False,
            "remote_approval_allowed": False,
            "hermes_called": False,
            "metadata_only": True,
        }

    def pairing_status(self) -> Dict[str, Any]:
        rows = self._conn.execute("SELECT * FROM pairing_challenges ORDER BY created_at DESC LIMIT 25").fetchall()
        challenges = [_row_to_challenge(row, public=False) for row in rows]
        return {
            "schema_version": LOCAL_PAIRING_SCHEMA_VERSION,
            "pairing_status": "local_hardened_pairing_available",
            "remote_pairing_enabled": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "challenge_ttl_seconds": PAIRING_TTL_SECONDS,
            "nonce_required": True,
            "one_time_use": True,
            "exact_scope_required": True,
            "trusted_device_binding": True,
            "rate_limit": {
                "max_failed_attempts": PAIRING_MAX_FAILED_ATTEMPTS,
                "lockout_seconds": PAIRING_LOCKOUT_SECONDS,
            },
            "pending_pairing_count": sum(1 for item in challenges if item["status"] == "pending" and not _is_expired(item["expires_at"])),
            "failed_attempt_count": sum(int(item["failed_attempts"]) for item in challenges),
            "recent_challenges": challenges,
            "metadata_only": True,
            "source_endpoint": "/mark-3/local-pairing/status",
        }

    def record_voice_decision(self, *, session_id: str, approval_id: str, transcript_hash: str, decision: str) -> bool:
        with self._lock:
            existing = self._conn.execute(
                "SELECT session_id FROM voice_decisions WHERE transcript_hash=?",
                (transcript_hash,),
            ).fetchone()
            if existing:
                return False
            self._conn.execute(
                "INSERT INTO voice_decisions (session_id, approval_id, transcript_hash, decision, used_at) VALUES (?, ?, ?, ?, ?)",
                (_safe_text(session_id, limit=160), _safe_text(approval_id, limit=160), transcript_hash, _safe_slug(decision, "unknown"), self.clock()),
            )
            self._conn.commit()
            return True

    def record_notification(self, *, event_type: str, status: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        event_id = f"notif-{uuid4()}"
        created_at = self.clock()
        safe_payload = _redacted_metadata(payload)
        with self._lock:
            self._conn.execute(
                "INSERT INTO notifications (event_id, event_type, status, created_at, payload_json) VALUES (?, ?, ?, ?, ?)",
                (event_id, _safe_slug(event_type, "notification"), _safe_slug(status, "ready"), created_at, _json_dumps(safe_payload)),
            )
            self._conn.commit()
        return {
            "event_id": event_id,
            "event_type": _safe_slug(event_type, "notification"),
            "status": _safe_slug(status, "ready"),
            "created_at": created_at,
            "payload": safe_payload,
            "metadata_only": True,
        }

    def notifications_status(self) -> Dict[str, Any]:
        rows = self._conn.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 12").fetchall()
        return {
            "schema_version": NOTIFICATION_READINESS_SCHEMA_VERSION,
            "status": "local_notification_contract_ready",
            "external_notifications_enabled": False,
            "telegram_notification_only_readiness": True,
            "remote_execution_allowed": False,
            "supported_events": [
                "approval_pending",
                "pairing_requested",
                "device_trusted",
                "device_revoked",
                "action_blocked",
                "approval_expired",
                "voice_approval_accepted",
                "voice_approval_denied",
            ],
            "recent_events": [
                {
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "payload": _json_loads(row["payload_json"]),
                    "metadata_only": True,
                }
                for row in rows
            ],
            "metadata_only": True,
            "source_endpoint": "/mark-3/notifications/status",
        }

    def status(self) -> Dict[str, Any]:
        devices = self.list_devices()
        return {
            "schema_version": TRUSTED_DEVICE_STORE_SCHEMA_VERSION,
            "state": {
                "available": True,
                "persistent": self._persistent,
                "local_only": True,
                "metadata_only": True,
                "storage_path": str(self._db_path) if self._db_path else str(PHASE_5_STATE_DB_RELATIVE_PATH),
                "device_count": len(devices),
                "trusted_device_count": sum(1 for item in devices if item["trusted"] and not item["revoked"]),
                "revoked_device_count": sum(1 for item in devices if item["revoked"]),
            },
            "safety": {
                "public_identifier_hashed": True,
                "fingerprint_hashed": True,
                "no_secret_cleartext": True,
                "memory_grants_permission": False,
                "deserialization_can_create_trust": False,
                "remote_execution_allowed": False,
                "hermes_called": False,
            },
            "source_endpoint": "/mark-3/trusted-devices/status",
        }

    def _pairing_failure(self, row: Optional[sqlite3.Row], *, reason: str) -> Dict[str, Any]:
        returned_reason = reason
        if row is not None:
            if reason in {"pairing_challenge_already_used", "pairing_challenge_expired"}:
                terminal_status = "consumed" if reason == "pairing_challenge_already_used" else "expired"
                self._conn.execute(
                    "UPDATE pairing_challenges SET status=? WHERE challenge_id=?",
                    (terminal_status, row["challenge_id"]),
                )
                self._conn.commit()
            else:
                failed_attempts = int(row["failed_attempts"] or 0) + 1
                locked_until = row["locked_until"] or ""
                status = "failed"
                if failed_attempts >= PAIRING_MAX_FAILED_ATTEMPTS:
                    locked_until = _after_seconds(PAIRING_LOCKOUT_SECONDS)
                    status = "rate_limited"
                    returned_reason = "pairing_rate_limited"
                self._conn.execute(
                    "UPDATE pairing_challenges SET failed_attempts=?, locked_until=?, status=? WHERE challenge_id=?",
                    (failed_attempts, locked_until, status, row["challenge_id"]),
                )
                self._conn.commit()
        return {
            "schema_version": LOCAL_PAIRING_SCHEMA_VERSION,
            "pairing_status": "rejected",
            "reason": returned_reason,
            "rate_limited": returned_reason == "pairing_rate_limited",
            "trusted_device_created": False,
            "remote_execution_allowed": False,
            "remote_approval_allowed": False,
            "hermes_called": False,
            "metadata_only": True,
        }

    def _device_row(self, device_id: str) -> Optional[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM trusted_devices WHERE device_id=?", (device_id,)).fetchone()

    def _initialize(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trusted_devices (
                device_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                channel_type TEXT NOT NULL,
                public_identifier_hash TEXT NOT NULL,
                fingerprint_hash TEXT NOT NULL,
                trust_status TEXT NOT NULL,
                trusted INTEGER NOT NULL,
                verified INTEGER NOT NULL,
                paired INTEGER NOT NULL,
                local_only INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                revoked_at TEXT NOT NULL,
                revocation_reason TEXT NOT NULL,
                capabilities_json TEXT NOT NULL,
                approval_scope_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                trust_source TEXT NOT NULL,
                paired_challenge_id TEXT NOT NULL,
                imported_claimed_trust INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pairing_challenges (
                challenge_id TEXT PRIMARY KEY,
                nonce_hash TEXT NOT NULL,
                phrase_hash TEXT NOT NULL,
                public_identifier_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                channel TEXT NOT NULL,
                scope_json TEXT NOT NULL,
                risk_limit TEXT NOT NULL,
                capabilities_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT NOT NULL,
                failed_attempts INTEGER NOT NULL,
                locked_until TEXT NOT NULL,
                status TEXT NOT NULL,
                bound_device_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_decisions (
                transcript_hash TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                approval_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                used_at TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        self._conn.commit()


class Phase5LocalControllerTrustedIdentityVoiceApprovalControlPlane(Phase4LocalControllerRemotePairingControlPlane):
    """Phase 5 durable trusted identity, local pairing, and governed voice approval."""

    def __init__(self, *args: Any, phase5_store: Optional[Phase5IdentityStore] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.phase5_store = phase5_store or Phase5IdentityStore.from_environment()
        self.phase5_store.bootstrap_local_browser()
        self._voice_sessions: Dict[str, VoiceApprovalSession] = {}
        self._controller_opted_in = False
        self._controller_start_requested_at: Optional[str] = None
        self._controller_stop_requested_at: Optional[str] = None
        self._local_kill_switch_enabled = False

    def status(self) -> Dict[str, Any]:
        base = super().status()
        base["schema_version"] = PHASE_5_SCHEMA_VERSION
        base["phase"] = "Phase 5"
        base["phase_5_status"] = self.phase_5_status(route_paths=())
        base["trusted_devices"] = self.trusted_devices_status()
        base["local_pairing"] = self.local_pairing_status()
        base["voice_approval"] = self.voice_approval_status()
        base["notifications"] = self.notifications_status()
        base["safety"].update({
            "phase_5_persistent_trusted_identity": True,
            "pairing_one_time_challenges": True,
            "voice_approval_governed": True,
            "wake_phrase_can_approve": False,
            "memory_grants_permission": False,
            "remote_execution_allowed": False,
            "frontend_can_execute_hermes_directly": False,
        })
        return base

    def phase_5_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        return {
            "schema_version": PHASE_5_SCHEMA_VERSION,
            "phase": "Phase 5",
            "title": "PR #170 -- Phase 5 Local Controller, Trusted Identity, Pairing & Voice Approval",
            "status": "implemented_as_local_controller_trusted_identity_voice_approval_foundation",
            "implemented_blocks": {
                "local_controller_opt_in_v1": True,
                "persistent_trusted_device_identity_v1": True,
                "hardened_local_pairing_v1": True,
                "governed_voice_approval_contract_v1": True,
                "triple_approval_persistent_identity_gate": True,
                "notification_readiness_contracts": True,
                "manual_dev_controller_script": True,
                "documentation_phase_5": True,
            },
            "route_readiness": {
                "phase_5_status": "/mark-3/phase-5/status" in routes,
                "local_pairing_status": "/mark-3/local-pairing/status" in routes,
                "voice_approval_status": "/mark-3/voice-approval/status" in routes,
                "notifications_status": "/mark-3/notifications/status" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "local_controller": self.local_controller_status(),
            "trusted_devices": self.trusted_devices_status(),
            "local_pairing": self.local_pairing_status(),
            "voice_approval": self.voice_approval_status(),
            "triple_approval_readiness": self.triple_approval_readiness_status(),
            "notifications": self.notifications_status(),
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_can_execute_hermes_directly": False,
                "persistent_identity_required": True,
                "revoked_device_stays_revoked": True,
                "pairing_bypasses_approval_gateway": False,
                "pairing_calls_hermes": False,
                "voice_approval_bypasses_policy": False,
                "voice_approval_downgrades_risk": False,
                "wake_phrase_can_approve": False,
                "memory_grants_permission": False,
                "raw_audio_stored_by_default": False,
                "remote_execution_allowed": False,
            },
            "source_endpoint": "/mark-3/phase-5/status",
            "metadata_only": True,
        }

    def local_controller_status(self) -> Dict[str, Any]:
        base = super().local_controller_status()
        base.update({
            "schema_version": PHASE_5_SCHEMA_VERSION,
            "opt_in_state": "opted_in" if self._controller_opted_in else "not_opted_in",
            "start_intent": "requested" if self._controller_start_requested_at else "not_requested",
            "stop_intent": "requested" if self._controller_stop_requested_at else "not_requested",
            "kill_switch": "enabled" if self._local_kill_switch_enabled else "disabled",
            "external_exposure": False,
            "hidden_background_behavior": False,
            "native_tray_status": "readiness_only_not_installed",
            "manual_dev_controller_available": True,
            "phase_5_contract": True,
        })
        return base

    def set_local_controller_opt_in(self, *, enabled: bool, actor: str = "David", reason: str = "operator opt-in") -> Dict[str, Any]:
        self._controller_opted_in = bool(enabled)
        audit = self._audit_v2(
            "local_controller_opt_in_changed",
            correlation_id=f"corr-{uuid4()}",
            surface="local_controller",
            metadata={"enabled": self._controller_opted_in, "actor": actor, "reason": reason, "no_autostart": True},
        )
        self._notification("local_controller_opt_in", "recorded", {"enabled": self._controller_opted_in, "actor": actor})
        return {"status": "opted_in" if enabled else "not_opted_in", "audit_id": audit.get("audit_id", ""), "controller": self.local_controller_status()}

    def local_controller_start_request(self, *, actor: str = "David", reason: str = "operator start") -> Dict[str, Any]:
        self._controller_start_requested_at = self.clock()
        audit = self._audit_v2(
            "local_controller_start_requested",
            correlation_id=f"corr-{uuid4()}",
            surface="local_controller",
            metadata={"actor": actor, "reason": reason, "manual_only": True, "autostart_enabled": False},
        )
        return {"request_status": "recorded_not_started", "started_process": False, "audit_id": audit.get("audit_id", ""), "controller": self.local_controller_status()}

    def local_controller_kill_switch(self, *, enabled: bool, actor: str = "David", reason: str = "operator kill switch") -> Dict[str, Any]:
        self._local_kill_switch_enabled = bool(enabled)
        audit = self._audit_v2(
            "local_controller_kill_switch_changed",
            correlation_id=f"corr-{uuid4()}",
            surface="local_controller",
            risk_level="high",
            approval_level="none",
            metadata={"enabled": self._local_kill_switch_enabled, "actor": actor, "reason": reason},
        )
        return {"kill_switch": "enabled" if enabled else "disabled", "audit_id": audit.get("audit_id", ""), "controller": self.local_controller_status()}

    def register_local_controller(self, **kwargs: Any) -> Dict[str, Any]:
        result = super().register_local_controller(**kwargs)
        device = result.get("trusted_device", {})
        if result.get("verified") and device.get("device_id"):
            persisted = self.phase5_store.upsert_trusted_device(
                device_id=device["device_id"],
                display_name=device.get("display_name") or "JARVIS Local Controller",
                channel_type="local_controller",
                public_identifier=str(result.get("controller_id") or device["device_id"]),
                fingerprint_material=f"local-controller:{result.get('controller_id')}:{device.get('created_at')}",
                capabilities={
                    "can_grant_normal": True,
                    "can_grant_strong": True,
                    "can_grant_double": True,
                    "can_grant_triple": True,
                    "voice_approval": False,
                },
                approval_scope=["local_controller", "approval", "readback", "stop", "cancel"],
                metadata={"controller_id": result.get("controller_id"), "local_only": True},
                trust_source="local_controller_exact_verification_phrase",
                local_only=True,
            )
            audit = self._audit_v2(
                "trusted_device_registered",
                correlation_id=f"corr-{uuid4()}",
                surface="trusted_identity",
                metadata={"device_id": persisted.get("device_id"), "channel_type": "local_controller", "trust_source": "local_controller_exact_verification_phrase"},
            )
            persisted["audit_ids"] = [audit.get("audit_id", "")]
            result["trusted_device"] = self._public_device(persisted, controller_id=str(result.get("controller_id") or ""))
            self._notification("device_trusted", "ready", {"device_id": persisted.get("device_id"), "channel_type": "local_controller"})
        return result

    def local_controller_heartbeat(self, **kwargs: Any) -> Dict[str, Any]:
        result = super().local_controller_heartbeat(**kwargs)
        controller = self._resolve_controller(kwargs.get("controller_id"), allow_missing=True)
        device_id = str(controller.get("device_id") or f"device-{controller.get('controller_id')}")
        seen = self.phase5_store.mark_seen(device_id)
        if seen:
            self._audit_v2(
                "trusted_device_seen",
                correlation_id=f"corr-{uuid4()}",
                surface="trusted_identity",
                metadata={"device_id": device_id, "channel_type": "local_controller"},
            )
        return result

    def verify_trusted_channel(self, **kwargs: Any) -> Dict[str, Any]:
        channel_id = str(kwargs.get("channel_id") or "")
        if channel_id == "terminal_local":
            actor = _safe_text(kwargs.get("actor") or "David", limit=80)
            local_presence = bool(kwargs.get("local_presence", True))
            challenge_response = kwargs.get("challenge_response")
            if challenge_response is not None and challenge_response != TERMINAL_VERIFICATION_PHRASE:
                audit = self._audit_v2(
                    "trusted_channel_rejected",
                    correlation_id=f"corr-{uuid4()}",
                    metadata={"channel_id": channel_id, "actor": actor, "challenge_valid": False},
                )
                return {
                    "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
                    "channel_id": channel_id,
                    "verified": False,
                    "reason": "terminal_challenge_invalid",
                    "audit_id": audit.get("audit_id", ""),
                }
            if not local_presence:
                audit = self._audit_v2(
                    "trusted_channel_rejected",
                    correlation_id=f"corr-{uuid4()}",
                    metadata={"channel_id": channel_id, "actor": actor, "local_presence": False},
                )
                return {
                    "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
                    "channel_id": channel_id,
                    "verified": False,
                    "reason": "local_presence_required",
                    "audit_id": audit.get("audit_id", ""),
                }
            persisted = self.phase5_store.upsert_trusted_device(
                device_id="device-terminal_local",
                display_name="Local terminal",
                channel_type="local_terminal",
                public_identifier="jarvis-local-terminal-channel",
                fingerprint_material=f"terminal:{TERMINAL_VERIFICATION_PHRASE}",
                capabilities={
                    "can_grant_normal": True,
                    "can_grant_strong": True,
                    "can_grant_double": True,
                    "can_grant_triple": True,
                    "voice_approval": False,
                },
                approval_scope=["local_terminal", "approval", "readback"],
                metadata={
                    "challenge_response_hash": _hash_text(challenge_response or "legacy_local_presence_verification"),
                    "legacy_local_presence_verification": challenge_response is None,
                },
                trust_source="terminal_exact_challenge" if challenge_response else "terminal_legacy_local_presence",
                local_only=True,
            )
            if not _device_is_trusted(persisted):
                audit = self._audit_v2(
                    "trusted_channel_rejected",
                    correlation_id=f"corr-{uuid4()}",
                    metadata={"channel_id": channel_id, "actor": actor, "reason": "persistent_device_revoked"},
                )
                return {
                    "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
                    "channel_id": channel_id,
                    "verified": False,
                    "reason": "persistent_device_revoked",
                    "audit_id": audit.get("audit_id", ""),
                }
            verified_at = self.clock()
            self._channel_verified_at[channel_id] = verified_at
            audit = self._audit_v2(
                "trusted_channel_verified",
                correlation_id=f"corr-{uuid4()}",
                metadata={"channel_id": channel_id, "actor": actor, "local_presence": True, "metadata_only": True},
            )
            self._audit_v2(
                "trusted_device_registered",
                correlation_id=f"corr-{uuid4()}",
                surface="trusted_identity",
                metadata={"device_id": persisted.get("device_id"), "channel_type": "local_terminal", "trust_source": "terminal_exact_challenge"},
            )
            return {
                "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
                "channel": self._channel(channel_id),
                "channel_id": channel_id,
                "verified": True,
                "last_verified_at": verified_at,
                "trusted_device": self._public_device(persisted),
                "audit_id": audit.get("audit_id", ""),
            }
        result = super().verify_trusted_channel(**kwargs)
        return result

    def trusted_devices_status(self) -> Dict[str, Any]:
        base = super().trusted_devices_status()
        persisted = self.phase5_store.list_devices()
        by_id = {item["device_id"]: item for item in persisted}
        merged = []
        for device in base["devices"]:
            stored = by_id.get(device["device_id"])
            merged.append(self._public_device(stored, fallback=device) if stored else device)
        known = {item["device_id"] for item in merged}
        for stored in persisted:
            if stored["device_id"] not in known:
                merged.append(self._public_device(stored))
        active = [item for item in merged if item["trusted"] and item["verified"] and item["paired"] and not item["revoked"]]
        remote_devices = [item for item in merged if not item["local_only"]]
        base.update({
            "schema_version": TRUSTED_DEVICE_STORE_SCHEMA_VERSION,
            "devices": merged,
            "persistent_store": self.phase5_store.status(),
            "trusted_device_count": len(active),
            "paired_devices_count": sum(1 for item in merged if item["paired"] and not item["revoked"]),
            "remote_devices_count": len([item for item in remote_devices if item["paired"] and not item["revoked"]]),
            "remote_trusted_devices_count": len([item for item in remote_devices if item["trusted"] and not item["revoked"]]),
            "revoked_devices_count": sum(1 for item in merged if item["revoked"]),
            "can_grant_normal": any(item["can_grant_normal"] for item in active),
            "can_grant_strong": any(item["can_grant_strong"] for item in active),
            "can_grant_double": len({item["channel_type"] for item in active if item["can_grant_double"]}) >= 2,
            "can_grant_triple": self.triple_approval_readiness_status()["can_grant_triple"],
            "identity_not_plain_frontend_claim": True,
            "public_identifier_hashed": True,
            "fingerprint_hashed": True,
            "deserialization_can_create_trust": False,
            "memory_grants_permission": False,
        })
        return base

    def trusted_device_import_preview(self, *, payload: Mapping[str, Any]) -> Dict[str, Any]:
        result = self.phase5_store.import_preview(payload)
        audit = self._audit_v2(
            "trusted_device_import_rejected",
            correlation_id=f"corr-{uuid4()}",
            surface="trusted_identity",
            risk_level="medium",
            approval_level="blocked",
            metadata={"device_id": result.get("device_id"), "claimed_trusted": result.get("claimed_trusted")},
        )
        result["audit_id"] = audit.get("audit_id", "")
        return result

    def create_local_pairing_challenge(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.phase5_store.create_pairing_challenge(**kwargs)
        audit = self._audit_v2(
            "local_pairing_challenge_created",
            correlation_id=f"corr-{uuid4()}",
            surface="local_pairing",
            risk_level="medium",
            approval_level="none",
            metadata={"challenge_id": result["challenge_id"], "scope": result["scope"], "remote_execution_allowed": False},
        )
        result["audit_id"] = audit.get("audit_id", "")
        self._notification("pairing_requested", "pending", {"challenge_id": result["challenge_id"], "scope": result["scope"]})
        return result

    def verify_local_pairing_challenge(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.phase5_store.verify_pairing_challenge(**kwargs)
        if result.get("pairing_status") == "trusted_device_bound":
            event = "local_pairing_challenge_consumed"
        elif result.get("rate_limited"):
            event = "local_pairing_challenge_rate_limited"
        elif result.get("reason") == "pairing_challenge_expired":
            event = "local_pairing_challenge_expired"
        else:
            event = "local_pairing_challenge_failed"
        audit = self._audit_v2(
            event,
            correlation_id=f"corr-{uuid4()}",
            surface="local_pairing",
            risk_level="medium",
            approval_level="none" if event == "local_pairing_challenge_consumed" else "blocked",
            metadata={"challenge_id": kwargs.get("challenge_id"), "pairing_status": result.get("pairing_status"), "reason": result.get("reason", "")},
        )
        result["audit_id"] = audit.get("audit_id", "")
        if result.get("device"):
            self._notification("device_trusted", "ready", {"device_id": result["device"].get("device_id"), "scope": result.get("scope")})
        return result

    def local_pairing_status(self) -> Dict[str, Any]:
        return self.phase5_store.pairing_status()

    def remote_pairing_revoke(self, **kwargs: Any) -> Dict[str, Any]:
        result = super().remote_pairing_revoke(**kwargs)
        device_id = kwargs.get("device_id")
        if device_id:
            persisted = self.phase5_store.revoke_device(str(device_id), reason=str(kwargs.get("reason") or "operator revoke"))
            result["trusted_device"] = self._public_device(persisted) if persisted else {}
            self._notification("device_revoked", "ready", {"device_id": device_id, "reason": kwargs.get("reason", "operator revoke")})
        return result

    def triple_approval_readiness_status(self) -> Dict[str, Any]:
        base = super().triple_approval_readiness_status()
        channels = self._triple_ready_channels()
        persistent_ready = len(channels) >= 3 and all(
            _device_is_trusted(self._trusted_device_for_channel(item["channel_id"]))
            for item in channels
        )
        base.update({
            "schema_version": PHASE_5_SCHEMA_VERSION,
            "persistent_identity_required": True,
            "persistent_identity_ready": persistent_ready,
            "trusted_device_ids": [self._device_id_for_channel(item["channel_id"]) for item in channels],
            "audit_chain_required": True,
            "scope_exact_match_required": True,
            "action_id_match_required": True,
            "no_replay": True,
            "can_grant_triple": bool(base.get("can_grant_triple") and persistent_ready),
            "triple_status": "ready_three_persistent_verified_local_channels" if base.get("can_grant_triple") and persistent_ready else "blocked_no_three_persistent_verified_channels",
        })
        if not base["can_grant_triple"] and not base.get("blocked_reason"):
            base["blocked_reason"] = "critical requires persistent trusted browser + terminal + local controller identity"
        return base

    def decide_triple_approval(
        self,
        *,
        approval_id: str,
        decision: str = "approve",
        actor: str = "David",
        channel_id: str = "ui_local_browser",
        step_id: Optional[str] = None,
        confirmation_phrase: Optional[str] = None,
        readback_text: Optional[str] = None,
        reason: str = "",
        action_id: Optional[str] = None,
        scope_fingerprint: Optional[str] = None,
    ) -> Dict[str, Any]:
        if "voice" in channel_id or "wake" in channel_id:
            raise ValueError("voice and wake phrase cannot approve")
        channel = self._channel(channel_id)
        device = self._trusted_device_for_channel(channel_id)
        if device and not _device_is_trusted(device):
            raise ValueError("persistent trusted device is required for triple approval")
        if not channel.get("can_grant_triple"):
            raise ValueError("channel cannot grant triple approval")
        if not channel.get("authenticated"):
            raise ValueError("channel must be verified before approval")
        if not _device_is_trusted(device):
            raise ValueError("persistent trusted device is required for triple approval")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            if action_id and action_id != envelope.get("action_id"):
                raise ValueError("action_id does not match approval")
            if scope_fingerprint and scope_fingerprint != _scope_fingerprint(envelope):
                raise ValueError("scope fingerprint does not match approval")
            steps = envelope.get("approval_steps", [])
            step = _select_public_step(steps, step_id)
            if step and step.get("status") != "pending":
                raise ValueError(f"approval step {step.get('step_id')} is already {step.get('status')}")
            approved_channels = [item.get("channel_id", "") for item in steps if item.get("status") == "approved"]
            approved_types = [item.get("channel_type", "") for item in steps if item.get("status") == "approved"]
            if step and (channel_id in approved_channels or channel.get("channel_type") in approved_types):
                raise ValueError("triple approval requires three separate trusted channels")
            if step and step.get("expected_channel_id") and step.get("expected_channel_id") != channel_id:
                raise ValueError("approval step requires its exact trusted channel")
        verification = self.audit_ledger.verify_chain()
        if not verification.valid:
            raise ValueError("audit chain verification failed")
        return super().decide_triple_approval(
            approval_id=approval_id,
            decision=decision,
            actor=actor,
            channel_id=channel_id,
            step_id=step_id,
            confirmation_phrase=confirmation_phrase,
            readback_text=readback_text,
            reason=reason,
        )

    def voice_approval_status(self) -> Dict[str, Any]:
        active = [session.to_dict() for session in self._voice_sessions.values() if session.active and not _is_expired(session.expires_at)]
        return {
            "schema_version": VOICE_APPROVAL_SCHEMA_VERSION,
            "voice_approval_available": True,
            "voice_approval_enabled": True,
            "wake_phrase_can_approve": False,
            "requires_active_voice_session": True,
            "requires_trusted_device": True,
            "requires_exact_readback": True,
            "requires_spoken_challenge": True,
            "risk_never_downgraded": True,
            "policy_gateway_bypass_allowed": False,
            "raw_audio_stored_by_default": False,
            "transcript_fixture_testable": True,
            "allowed_phrases": list(VOICE_APPROVAL_PHRASES),
            "spanish_spoken_limit_phrases": [
                "JARVIS, autorizo con limite de X euros",
                "JARVIS, autorizo durante X minutos",
            ],
            "deny_phrases": list(VOICE_DENY_PHRASES),
            "allowed_approval_levels": sorted(VOICE_APPROVAL_ALLOWED_LEVELS),
            "allowed_risk_levels": sorted(VOICE_APPROVAL_ALLOWED_RISKS),
            "active_session_count": len(active),
            "active_sessions": active,
            "metadata_only": True,
            "source_endpoint": "/mark-3/voice-approval/status",
        }

    def start_voice_approval_session(
        self,
        *,
        approval_id: str,
        device_id: str,
        voice_session_id: str,
        readback_text: str,
        scope: Optional[List[str]] = None,
        cost_summary: str = "unknown; operator review required",
        cost_limit_eur: Optional[float] = None,
        duration_seconds: int = VOICE_APPROVAL_TTL_SECONDS,
        voice_session_active: bool = True,
        opened_by_wake_only: bool = False,
    ) -> Dict[str, Any]:
        if not voice_session_active:
            raise ValueError("active voice session is required for voice approval")
        if opened_by_wake_only:
            raise ValueError("wake phrase alone cannot approve")
        device = self.phase5_store.get_device(device_id)
        if not _device_is_trusted(device):
            raise ValueError("trusted non-revoked device is required for voice approval")
        device_capabilities = dict((device or {}).get("capabilities") or {})
        device_scope = set((device or {}).get("approval_scope") or [])
        if not device_capabilities.get("voice_approval") or "voice_approval" not in device_scope:
            raise ValueError("trusted device is not scoped for voice approval")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            if envelope.get("status") != "pending":
                raise ValueError("voice approval requires a pending approval")
            risk = str(envelope.get("risk_level") or "unknown")
            level = str(envelope.get("approval_level_required") or envelope.get("approval_level") or "unknown")
            if risk not in VOICE_APPROVAL_ALLOWED_RISKS or level not in VOICE_APPROVAL_ALLOWED_LEVELS:
                raise ValueError("risk or approval level does not allow voice approval")
            if _normalize_readback(readback_text) != _normalize_readback(envelope.get("readback_text")):
                raise ValueError("exact readback must be presented before voice approval")
            scope_fingerprint = _hash_text(_json_dumps(_safe_json_list(scope or _scope_from_envelope(envelope))))
            challenge_code = secrets.token_hex(3).upper()
            expected = f"JARVIS, confirmo {challenge_code}" if risk == "high" or level == "strong" else ""
            session = VoiceApprovalSession(
                session_id=f"voice-approval-{uuid4()}",
                approval_id=approval_id,
                device_id=device_id,
                voice_session_id=_safe_text(voice_session_id, limit=160),
                action_id=str(envelope.get("action_id") or ""),
                action_key=str(envelope.get("action_key") or ""),
                risk_level=risk,
                approval_level=level,
                scope_fingerprint=scope_fingerprint,
                cost_summary=_safe_text(cost_summary, limit=160),
                cost_limit_eur=_safe_money_limit(cost_limit_eur),
                duration_seconds=max(10, min(int(duration_seconds or VOICE_APPROVAL_TTL_SECONDS), VOICE_APPROVAL_TTL_SECONDS)),
                readback_text_hash=_hash_text(_normalize_readback(readback_text)),
                expected_challenge=expected,
                accepted_phrases=list(VOICE_APPROVAL_PHRASES) if not expected else [expected],
                created_at=self.clock(),
                expires_at=_after_seconds(max(10, min(int(duration_seconds or VOICE_APPROVAL_TTL_SECONDS), VOICE_APPROVAL_TTL_SECONDS))),
                readback_presented=True,
                active_voice_session_verified=True,
                opened_by_wake_only=False,
            )
            self._voice_sessions[session.session_id] = session
        audit = self._audit_v2(
            "voice_approval_session_started",
            correlation_id=f"corr-{uuid4()}",
            surface="voice_approval",
            risk_level=session.risk_level,
            approval_level=session.approval_level,
            metadata={
                "approval_id": approval_id,
                "session_id": session.session_id,
                "voice_session_id": session.voice_session_id,
                "device_id": device_id,
                "readback_presented": True,
                "active_voice_session_verified": True,
                "cost_limit_eur": session.cost_limit_eur,
                "duration_seconds": session.duration_seconds,
            },
        )
        self._audit_v2(
            "voice_approval_readback_presented",
            correlation_id=f"corr-{uuid4()}",
            surface="voice_approval",
            risk_level=session.risk_level,
            approval_level=session.approval_level,
            metadata={"approval_id": approval_id, "session_id": session.session_id, "readback_hash": session.readback_text_hash},
        )
        data = session.to_dict()
        data["audit_ids"] = [audit.get("audit_id", "")]
        data["expected_challenge"] = session.expected_challenge
        return data

    def decide_voice_approval(
        self,
        *,
        session_id: str,
        device_id: str,
        transcript: str,
        readback_text: str,
        scope: Optional[List[str]] = None,
        action_id: Optional[str] = None,
        cost_summary: str = "unknown; operator review required",
    ) -> Dict[str, Any]:
        session = self._voice_sessions.get(session_id)
        if not session:
            raise KeyError(session_id)
        normalized = _normalize_phrase(transcript)
        transcript_hash = _hash_text(f"{session_id}:{normalized}")
        device = self.phase5_store.get_device(device_id)
        if not _device_is_trusted(device) or device_id != session.device_id:
            return self._voice_decision(session, "denied", "trusted_device_required", transcript_hash)
        if _is_expired(session.expires_at):
            return self._voice_decision(session, "expired", "voice_approval_expired", transcript_hash)
        if session.consumed_at:
            return self._voice_decision(session, "replay_rejected", "voice_approval_already_consumed", transcript_hash)
        if not session.readback_presented or session.readback_text_hash != _hash_text(_normalize_readback(readback_text)):
            return self._voice_decision(session, "denied", "exact_readback_required", transcript_hash)
        if action_id and action_id != session.action_id:
            return self._voice_decision(session, "denied", "action_id_mismatch", transcript_hash)
        if scope is not None and _hash_text(_json_dumps(_safe_json_list(scope))) != session.scope_fingerprint:
            return self._voice_decision(session, "denied", "scope_mismatch", transcript_hash)
        if _safe_text(cost_summary, limit=160) != session.cost_summary:
            return self._voice_decision(session, "denied", "cost_summary_mismatch", transcript_hash)
        if normalized in WAKE_ONLY_PHRASES:
            return self._voice_decision(session, "wake_phrase_rejected", "wake_phrase_alone_does_not_approve", transcript_hash)
        if normalized in VOICE_DENY_PHRASES:
            return self._voice_decision(session, "denied", "operator_denied_by_voice", transcript_hash)
        accepted = [_normalize_phrase(item) for item in session.accepted_phrases]
        spoken_limit = _parse_spoken_limit_phrase(normalized)
        limit_accepted = bool(spoken_limit and not session.expected_challenge and _spoken_limit_matches(session, spoken_limit))
        if normalized not in accepted and not limit_accepted:
            return self._voice_decision(session, "denied", "spoken_confirmation_phrase_mismatch", transcript_hash)
        if not self.phase5_store.record_voice_decision(session_id=session_id, approval_id=session.approval_id, transcript_hash=transcript_hash, decision="accepted"):
            return self._voice_decision(session, "replay_rejected", "spoken_approval_replay_detected", transcript_hash)
        envelope = self._phase2_decide_approval(
            approval_id=session.approval_id,
            decision="approved",
            actor="voice_approval_trusted_device",
            confirmation_phrase=(self._approval_envelopes.get(session.approval_id) or {}).get("confirmation_phrase"),
            readback_text=readback_text,
            reason="governed voice approval accepted after trusted identity, readback, challenge and anti-replay checks",
        )
        consumed = replace(session, consumed_at=self.clock(), active=False)
        self._voice_sessions[session_id] = consumed
        audit = self._audit_v2(
            "voice_approval_accepted",
            correlation_id=f"corr-{uuid4()}",
            surface="voice_approval",
            risk_level=session.risk_level,
            approval_level=session.approval_level,
            metadata={
                "approval_id": session.approval_id,
                "session_id": session_id,
                "voice_session_id": session.voice_session_id,
                "device_id": device_id,
                "transcript_hash": transcript_hash,
                "spoken_limit": spoken_limit or {},
            },
        )
        self._notification("voice_approval_accepted", "accepted", {"approval_id": session.approval_id, "session_id": session_id})
        return {
            "schema_version": VOICE_APPROVAL_SCHEMA_VERSION,
            "decision": "accepted",
            "status": "approved",
            "approval": envelope,
            "audit_id": audit.get("audit_id", ""),
            "raw_audio_stored": False,
            "transcript_stored": False,
            "metadata_only": True,
        }

    def notifications_status(self) -> Dict[str, Any]:
        return self.phase5_store.notifications_status()

    def _voice_decision(self, session: VoiceApprovalSession, decision: str, reason: str, transcript_hash: str) -> Dict[str, Any]:
        event = {
            "expired": "voice_approval_expired",
            "replay_rejected": "voice_approval_replay_rejected",
            "wake_phrase_rejected": "voice_approval_wake_phrase_rejected",
        }.get(decision, "voice_approval_denied")
        if decision in {"denied", "expired", "wake_phrase_rejected"}:
            self.phase5_store.record_voice_decision(session_id=session.session_id, approval_id=session.approval_id, transcript_hash=transcript_hash, decision=decision)
        audit = self._audit_v2(
            event,
            correlation_id=f"corr-{uuid4()}",
            surface="voice_approval",
            risk_level=session.risk_level,
            approval_level=session.approval_level,
            metadata={"approval_id": session.approval_id, "session_id": session.session_id, "reason": reason, "transcript_hash": transcript_hash},
        )
        if decision != "accepted":
            self._notification("voice_approval_denied", "denied", {"approval_id": session.approval_id, "reason": reason})
        return {
            "schema_version": VOICE_APPROVAL_SCHEMA_VERSION,
            "decision": decision,
            "status": "rejected" if decision not in {"expired", "replay_rejected"} else decision,
            "reason": reason,
            "audit_id": audit.get("audit_id", ""),
            "raw_audio_stored": False,
            "transcript_stored": False,
            "metadata_only": True,
        }

    def _channel(self, channel_id: str) -> Dict[str, Any]:
        data = super()._channel(channel_id)
        device = self._trusted_device_for_channel(channel_id)
        if channel_id in {"ui_local_browser", "terminal_local", "local_controller"}:
            persistent_trusted = _device_is_trusted(device)
            persistent_revoked = bool(device and device.get("revoked"))
            data.update({
                "persistent_device_id": (device or {}).get("device_id", self._device_id_for_channel(channel_id)),
                "persistent_identity_required": True,
                "persistent_identity_trusted": persistent_trusted,
                "persistent_identity_revoked": persistent_revoked,
                "persistent_identity_currently_grantable": bool(
                    persistent_trusted
                    and data.get("enabled")
                    and data.get("trusted")
                    and data.get("authenticated")
                ),
            })
            if persistent_revoked:
                data.update({
                    "trusted": False,
                    "authenticated": False,
                    "can_grant_approval": False,
                    "can_grant_strong": False,
                    "can_grant_double": False,
                    "can_grant_triple": False,
                })
        return data

    def _trusted_device_for_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        return self.phase5_store.get_device(self._device_id_for_channel(channel_id))

    def _device_id_for_channel(self, channel_id: str) -> str:
        if channel_id == "ui_local_browser":
            return "device-ui_local_browser"
        if channel_id == "terminal_local":
            return "device-terminal_local"
        if channel_id == "local_controller":
            controller = self._active_controller()
            return str(controller.get("device_id") or "device-local_controller")
        return f"device-{channel_id}"

    def _public_device(self, stored: Optional[Mapping[str, Any]], *, fallback: Optional[Mapping[str, Any]] = None, controller_id: str = "") -> Dict[str, Any]:
        if not stored:
            return dict(fallback or {})
        caps = dict(stored.get("capabilities") or {})
        revoked = bool(stored.get("revoked"))
        trusted = bool(stored.get("trusted")) and not revoked
        data = dict(fallback or {})
        data.update({
            "schema_version": TRUSTED_DEVICE_STORE_SCHEMA_VERSION,
            "device_id": stored.get("device_id", ""),
            "controller_id": controller_id or data.get("controller_id", ""),
            "display_name": stored.get("display_name", data.get("display_name", "")),
            "channel_type": stored.get("channel_type", data.get("channel_type", "unknown")),
            "local_only": bool(stored.get("local_only", True)),
            "trusted": trusted,
            "verified": bool(stored.get("verified")) and not revoked,
            "paired": bool(stored.get("paired")) and not revoked,
            "created_at": stored.get("created_at"),
            "last_seen_at": stored.get("last_seen_at"),
            "trust_level": "persistent_trusted_identity" if trusted else ("revoked" if revoked else "untrusted"),
            "risk_limit": "critical" if caps.get("can_grant_triple") and trusted else ("high" if trusted else "none"),
            "can_grant_normal": bool(caps.get("can_grant_normal")) and trusted,
            "can_grant_strong": bool(caps.get("can_grant_strong")) and trusted,
            "can_grant_double": bool(caps.get("can_grant_double")) and trusted,
            "can_grant_triple": bool(caps.get("can_grant_triple")) and trusted,
            "can_voice_approve": bool(caps.get("voice_approval")) and trusted,
            "revoked": revoked,
            "revoked_at": stored.get("revoked_at") or None,
            "revocation_reason": stored.get("revocation_reason") or "",
            "approval_scope": stored.get("approval_scope") or [],
            "public_identifier_hash": stored.get("public_identifier_hash"),
            "fingerprint_hash": stored.get("fingerprint_hash"),
            "metadata": stored.get("metadata") or {},
            "secrets_stored": False,
            "metadata_only": True,
        })
        return data

    def _notification(self, event_type: str, status: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        event = self.phase5_store.record_notification(event_type=event_type, status=status, payload=payload)
        self._audit_v2(
            "notification_readiness_event",
            correlation_id=f"corr-{uuid4()}",
            surface="notifications",
            metadata={"event_type": event["event_type"], "status": event["status"], "event_id": event["event_id"]},
        )
        return event


def _row_to_device(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "schema_version": TRUSTED_DEVICE_STORE_SCHEMA_VERSION,
        "device_id": row["device_id"],
        "display_name": row["display_name"],
        "channel_type": row["channel_type"],
        "public_identifier_hash": row["public_identifier_hash"],
        "fingerprint_hash": row["fingerprint_hash"],
        "trust_status": row["trust_status"],
        "trusted": bool(row["trusted"]) and row["trust_status"] != "revoked",
        "verified": bool(row["verified"]) and row["trust_status"] != "revoked",
        "paired": bool(row["paired"]) and row["trust_status"] != "revoked",
        "local_only": bool(row["local_only"]),
        "created_at": row["created_at"],
        "last_seen_at": row["last_seen_at"],
        "revoked": row["trust_status"] == "revoked",
        "revoked_at": row["revoked_at"] or None,
        "revocation_reason": row["revocation_reason"],
        "capabilities": _json_loads(row["capabilities_json"]),
        "approval_scope": _json_loads(row["approval_scope_json"]),
        "metadata": _json_loads(row["metadata_json"]),
        "trust_source": row["trust_source"],
        "paired_challenge_id": row["paired_challenge_id"],
        "imported_claimed_trust": bool(row["imported_claimed_trust"]),
    }


def _row_to_challenge(row: sqlite3.Row, *, public: bool = True) -> Dict[str, Any]:
    data = {
        "schema_version": LOCAL_PAIRING_SCHEMA_VERSION,
        "challenge_id": row["challenge_id"],
        "display_name": row["display_name"],
        "channel": row["channel"],
        "scope": _json_loads(row["scope_json"]),
        "risk_limit": row["risk_limit"],
        "capabilities": _json_loads(row["capabilities_json"]),
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
        "used_at": row["used_at"],
        "failed_attempts": int(row["failed_attempts"] or 0),
        "locked_until": row["locked_until"],
        "status": row["status"],
        "bound_device_id": row["bound_device_id"],
        "metadata_only": True,
    }
    if public:
        data.update({
            "nonce_hash": row["nonce_hash"],
            "phrase_hash": row["phrase_hash"],
            "public_identifier_hash": row["public_identifier_hash"],
        })
    return data


def _default_pairing_capabilities() -> Dict[str, bool]:
    return {
        "can_grant_normal": True,
        "can_grant_strong": True,
        "can_grant_double": False,
        "can_grant_triple": False,
        "voice_approval": True,
    }


def _device_is_trusted(device: Optional[Mapping[str, Any]]) -> bool:
    return bool(device and device.get("trusted") and device.get("verified") and device.get("paired") and not device.get("revoked"))


def _scope_from_envelope(envelope: Mapping[str, Any]) -> List[str]:
    preview = dict(envelope.get("preview") or {})
    return _safe_json_list([
        envelope.get("action_key"),
        envelope.get("action_id"),
        preview.get("input_fingerprint"),
        envelope.get("approval_level_required"),
    ])


def _scope_fingerprint(envelope: Mapping[str, Any]) -> str:
    return _hash_text(_json_dumps(_scope_from_envelope(envelope)))


def _select_public_step(steps: Iterable[Mapping[str, Any]], step_id: Optional[str]) -> Optional[Mapping[str, Any]]:
    for step in steps:
        if (step_id and step.get("step_id") == step_id) or (not step_id and step.get("status") == "pending"):
            return step
    return None


def _safe_json_list(values: Iterable[Any]) -> List[str]:
    return [_safe_text(item, limit=120) for item in values if _safe_text(item, limit=120)]


def _safe_json_dict(values: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(values or {}).items():
        key_text = _safe_slug(key, "unknown")
        if isinstance(value, bool) or value is None:
            safe[key_text] = value
        elif isinstance(value, (int, float)):
            safe[key_text] = value
        elif isinstance(value, (list, tuple)):
            safe[key_text] = _safe_json_list(value)
        elif isinstance(value, Mapping):
            safe[key_text] = _safe_json_dict(value)
        else:
            safe[key_text] = _safe_text(value, limit=160)
    return safe


def _redacted_metadata(values: Mapping[str, Any]) -> Dict[str, Any]:
    safe = _safe_json_dict(values)
    for key in list(safe):
        lowered = key.lower()
        if any(marker in lowered for marker in ("secret", "token", "password", "credential", "audio", "transcript", "raw")):
            safe[key] = "[redacted]"
    return safe


def _safe_money_limit(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed in {float("inf"), float("-inf")} or not parsed >= 0:
        return None
    return round(parsed, 2)


def _parse_spoken_limit_phrase(normalized: str) -> Optional[Dict[str, Any]]:
    cost_match = re.fullmatch(r"jarvis autorizo con limite de ([0-9]+) euros?", normalized)
    if cost_match:
        return {"kind": "cost_eur", "amount": float(cost_match.group(1))}
    duration_match = re.fullmatch(r"jarvis autorizo durante ([0-9]+) minutos?", normalized)
    if duration_match:
        return {"kind": "duration_minutes", "minutes": int(duration_match.group(1))}
    return None


def _spoken_limit_matches(session: VoiceApprovalSession, spoken_limit: Mapping[str, Any]) -> bool:
    if spoken_limit.get("kind") == "cost_eur":
        if session.cost_limit_eur is None:
            return False
        return float(spoken_limit.get("amount") or 0) <= float(session.cost_limit_eur)
    if spoken_limit.get("kind") == "duration_minutes":
        return int(spoken_limit.get("minutes") or 0) * 60 <= int(session.duration_seconds)
    return False


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _json_loads(value: str) -> Any:
    return json.loads(value or "{}")


def _hash_text(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _safe_slug(value: Any, fallback: str) -> str:
    text = _safe_text(value, limit=160).lower().replace(" ", "_")
    text = re.sub(r"[^a-z0-9_.:-]+", "_", text).strip("_")
    return text or fallback


def _normalize_phrase(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _after_seconds(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(seconds)))).isoformat()


def _expired_at(value: Any, *, now: Any = None) -> bool:
    if not value:
        return False
    current = _parse_iso_timestamp(now) if now is not None else datetime.now(timezone.utc)
    return current >= _parse_iso_timestamp(value)


def _parse_iso_timestamp(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
