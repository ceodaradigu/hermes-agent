from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.voice.understanding_memory import (
    SENSITIVE_MEMORY_TERMS,
    UserUnderstandingMemorySnapshot,
    UserUnderstandingMemoryStatus,
)
from jarvis.voice.understanding_memory_local_paths import (
    resolve_user_understanding_memory_local_paths,
)


@dataclass(frozen=True)
class UserUnderstandingMemoryLocalSaveResult:
    snapshot_path: str
    audit_log_path: str
    backup_path: str | None
    saved: bool
    persisted: bool
    proposal_count: int
    active_count: int
    sensitive_count: int
    checksum: str
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_path": self.snapshot_path,
            "audit_log_path": self.audit_log_path,
            "backup_path": self.backup_path,
            "saved": self.saved,
            "persisted": self.persisted,
            "proposal_count": self.proposal_count,
            "active_count": self.active_count,
            "sensitive_count": self.sensitive_count,
            "checksum": self.checksum,
            "notes": list(self.notes),
        }

    def to_dict(self) -> dict[str, Any]:
        return self.as_dict()


def save_user_understanding_memory_snapshot_local(
    snapshot: UserUnderstandingMemorySnapshot,
    base_dir: str | Path | None = None,
    create_backup: bool = True,
) -> UserUnderstandingMemoryLocalSaveResult:
    """Persist an exported memory snapshot only for explicit save-local actions.

    The incoming runtime snapshot must be non-persisted. This function marks the
    JSON payload as persisted only at the point of local write.
    """
    if not isinstance(snapshot, UserUnderstandingMemorySnapshot):
        raise TypeError("snapshot must be UserUnderstandingMemorySnapshot.")
    if not isinstance(create_backup, bool):
        raise TypeError("create_backup must be boolean.")
    if snapshot.persisted:
        raise ValueError("Persisted memory snapshots are not accepted for save-local input.")

    _validate_snapshot_safe_to_save(snapshot)
    paths = resolve_user_understanding_memory_local_paths(base_dir)
    paths.user_understanding_dir.mkdir(parents=True, exist_ok=True)
    paths.backups_dir.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if create_backup and paths.snapshot_path.exists():
        backup_path = paths.backups_dir / f"memory_proposals.snapshot.{_timestamp_for_filename()}.json"
        shutil.copy2(paths.snapshot_path, backup_path)

    payload = snapshot.as_dict()
    payload["persisted"] = True
    snapshot_json = json.dumps(payload, indent=2, sort_keys=True)
    snapshot_bytes = f"{snapshot_json}\n".encode("utf-8")
    checksum = hashlib.sha256(snapshot_bytes).hexdigest()

    _atomic_write_bytes(paths.snapshot_path, snapshot_bytes)

    audit_event = {
        "event": "memory_snapshot_saved",
        "timestamp": _now_iso(),
        "snapshot_path": str(paths.snapshot_path),
        "proposal_count": snapshot.proposal_count,
        "active_count": snapshot.active_count,
        "sensitive_count": snapshot.sensitive_count,
        "checksum": checksum,
        "persisted": True,
    }
    _append_jsonl_atomic(paths.audit_log_path, audit_event)

    notes = [
        "Snapshot saved only by explicit save-local action.",
        "Snapshot marked persisted=true at write time.",
        "No load-local, autoload, router application, runtime application, transcript change, task, or mission was performed.",
    ]
    return UserUnderstandingMemoryLocalSaveResult(
        snapshot_path=str(paths.snapshot_path),
        audit_log_path=str(paths.audit_log_path),
        backup_path=str(backup_path) if backup_path else None,
        saved=True,
        persisted=True,
        proposal_count=snapshot.proposal_count,
        active_count=snapshot.active_count,
        sensitive_count=snapshot.sensitive_count,
        checksum=checksum,
        notes=notes,
    )


def _validate_snapshot_safe_to_save(snapshot: UserUnderstandingMemorySnapshot) -> None:
    for proposal in snapshot.proposals:
        active_or_approved = proposal.active or proposal.status in {
            UserUnderstandingMemoryStatus.ACTIVE,
            UserUnderstandingMemoryStatus.APPROVED,
        }
        contains_secret_term = _contains_sensitive_term(proposal.alias, proposal.evidence)
        if active_or_approved and (proposal.sensitive or contains_secret_term):
            raise ValueError(
                "Sensitive active or approved memory proposals cannot be saved locally."
            )


def _contains_sensitive_term(alias: str | None, evidence: dict[str, Any]) -> bool:
    text = " ".join(
        str(value)
        for value in (alias, *evidence.values())
        if value is not None
    ).lower()
    return any(term in text for term in SENSITIVE_MEMORY_TERMS)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    try:
        with tmp_path.open("wb") as tmp_file:
            tmp_file.write(data)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _append_jsonl_atomic(path: Path, event: dict[str, Any]) -> None:
    existing = b""
    if path.exists():
        existing = path.read_bytes()
        if existing and not existing.endswith(b"\n"):
            existing += b"\n"
    line = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes(path, existing + line)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_for_filename() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
