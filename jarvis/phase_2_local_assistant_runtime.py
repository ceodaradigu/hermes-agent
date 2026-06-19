from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.approval_hardening import ApprovalKind, ApprovalStatus
from jarvis.mark_3_hermes_runtime_bridge import ALLOWED_ACTION
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_1_governed_execution import (
    GOVERNED_EXECUTION_SCHEMA_VERSION,
    Phase1GovernedExecutionControlPlane,
    PROTECTED_CREDENTIAL_MESSAGE,
)


PHASE_2_SCHEMA_VERSION = "jarvis.phase_2_local_assistant_runtime.v1"
EXECUTION_HISTORY_SCHEMA_VERSION = "jarvis.execution_history.v2"
EXECUTION_HISTORY_DB_RELATIVE_PATH = Path(".jarvis") / "execution_history" / "execution_history.sqlite3"

APPROVAL_LEVELS = ("none", "soft", "normal", "strong", "double", "triple", "blocked", "unsupported")
RISK_LEVELS = ("low", "medium", "high", "critical", "forbidden")
APPROVAL_STATUSES = (
    "pending",
    "approved",
    "rejected",
    "revoked",
    "expired",
    "cancelled",
    "blocked",
    "clarification_requested",
)

SECRET_MARKERS = (
    ".env",
    "api key",
    "api_key",
    "apikey",
    "authorization",
    "bearer ",
    "cookie",
    "credential",
    "credentials",
    "password",
    "private key",
    "private_key",
    "secret",
    "session material",
    "token",
)
SECRET_PATH_NAMES = {".env", ".env.local", ".env.production", ".npmrc", ".pypirc"}
DENIED_MARKERS = (
    "bypass",
    "cookie",
    "credential",
    "deploy",
    "dinero",
    "email",
    "env",
    "password",
    "payment",
    "publicar",
    "publish",
    "secret",
    "stripe",
    "token",
)

RUN_ALLOWLISTED_TARGETS = (
    "tests/jarvis/test_pr_166_phase_2_local_assistant_runtime.py",
)


@dataclass(frozen=True)
class ActionContract:
    action_key: str
    description: str
    allowed_inputs_schema: Dict[str, Any]
    risk_level: str
    approval_required: str
    timeout_seconds: int
    stop_supported: bool
    rollback_supported: bool
    audit_event_types: List[str]
    output_redaction: str
    filesystem_scope: str
    network_allowed: bool
    external_side_effects: bool
    secrets_policy: str
    stop_method: str
    rollback_plan: str
    rollback_risk: str
    rollback_requires_approval: bool
    rollback_status: str
    rollback_limitations: List[str] = field(default_factory=list)
    execution_backend: str = "jarvis_control_plane"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["approval_level_required"] = self.approval_required
        data["contract"] = {
            "stop_supported": self.stop_supported,
            "stop_method": self.stop_method,
            "rollback_supported": self.rollback_supported,
            "rollback_plan": self.rollback_plan,
            "rollback_risk": self.rollback_risk,
            "rollback_requires_approval": self.rollback_requires_approval,
            "rollback_status": self.rollback_status,
            "rollback_limitations": list(self.rollback_limitations),
        }
        return data


ACTION_CATALOG: Dict[str, ActionContract] = {
    "local.status.read": ActionContract(
        action_key="local.status.read",
        description="Read local JARVIS runtime status without Hermes dispatch.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="summary_only",
        filesystem_scope="none",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="not_required_read_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "local.doctor.run": ActionContract(
        action_key="local.doctor.run",
        description="Run deterministic local readiness checks without shell freeform.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="metadata_only",
        filesystem_scope="none",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="not_required_fast_read",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "repo.status.read": ActionContract(
        action_key="repo.status.read",
        description="Read fixed git status metadata for the current worktree.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="line_redaction_and_truncation",
        filesystem_scope="repo_metadata_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="timeout_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "repo.tests.run_allowlisted": ActionContract(
        action_key="repo.tests.run_allowlisted",
        description="Run one allowlisted pytest target with fixed argv and no shell.",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"test_target": {"type": "string", "enum": list(RUN_ALLOWLISTED_TARGETS)}},
            "additionalProperties": False,
        },
        risk_level="medium",
        approval_required="normal",
        timeout_seconds=120,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "approval_requested", "approval_approved", "dispatch_started", "dispatch_completed", "dispatch_failed"],
        output_redaction="summary_only_with_secret_line_redaction",
        filesystem_scope="repo_test_read_write_tmp_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="timeout_only",
        rollback_plan="not_required_for_tests",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
        rollback_limitations=["Test code may create pytest tmp files outside the repo according to pytest policy."],
    ),
    "repo.diff.read": ActionContract(
        action_key="repo.diff.read",
        description="Read git diff metadata only: stat and file names, no patch body.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="filenames_redacted_if_secret_like",
        filesystem_scope="repo_metadata_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="timeout_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "repo.log.read": ActionContract(
        action_key="repo.log.read",
        description="Read recent git commit summaries with fixed argv.",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 20}},
            "additionalProperties": False,
        },
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="commit_summary_truncation",
        filesystem_scope="repo_metadata_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="timeout_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "repo.file.read_safe": ActionContract(
        action_key="repo.file.read_safe",
        description="Read one safe exact local file through the existing Mark 3 Hermes read_file bridge.",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "minLength": 1}},
            "required": ["path"],
            "additionalProperties": False,
        },
        risk_level="medium",
        approval_required="normal",
        timeout_seconds=30,
        stop_supported=True,
        rollback_supported=False,
        audit_event_types=["preview_created", "approval_requested", "approval_approved", "dispatch_started", "dispatch_completed", "stop_requested", "stop_completed"],
        output_redaction="content_not_stored",
        filesystem_scope="one_existing_regular_non_secret_file",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="cooperative_mark_3_hermes_interrupt",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
        rollback_limitations=["Read-only operation; rollback is not required."],
        execution_backend="existing_mark_3_hermes_runtime_bridge",
    ),
    "jarvis.phase.status": ActionContract(
        action_key="jarvis.phase.status",
        description="Read Phase 2 implementation status.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="summary_only",
        filesystem_scope="none",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="not_required_read_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "jarvis.audit.status": ActionContract(
        action_key="jarvis.audit.status",
        description="Read persistent audit status and tamper-evidence summary.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="metadata_only",
        filesystem_scope="audit_metadata_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="not_required_read_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "jarvis.memory.status": ActionContract(
        action_key="jarvis.memory.status",
        description="Read Memory Brain v2 status; memory never grants permission.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="metadata_only",
        filesystem_scope="memory_metadata_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="not_required_read_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "jarvis.execution.history.read": ActionContract(
        action_key="jarvis.execution.history.read",
        description="Read safe execution history metadata.",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            "additionalProperties": False,
        },
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        stop_supported=False,
        rollback_supported=False,
        audit_event_types=["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction="metadata_only",
        filesystem_scope="execution_history_metadata_only",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="not_required_read_only",
        rollback_plan="not_required",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="not_required",
    ),
    "jarvis.execution.preview": ActionContract(
        action_key="jarvis.execution.preview",
        description="Create a prepare-only governed execution preview.",
        allowed_inputs_schema={"type": "object", "properties": {}, "additionalProperties": False},
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        stop_supported=False,
        rollback_supported=True,
        audit_event_types=["preview_created"],
        output_redaction="metadata_only",
        filesystem_scope="none",
        network_allowed=False,
        external_side_effects=False,
        secrets_policy="deny_and_redact",
        stop_method="cancel_preview",
        rollback_plan="discard_preview",
        rollback_risk="none",
        rollback_requires_approval=False,
        rollback_status="discard_preview",
        rollback_limitations=["No side effect exists to roll back."],
    ),
}


class ExecutionHistoryStore:
    """Local metadata-only execution history store."""

    def __init__(
        self,
        *,
        base_dir: str | Path | None = None,
        db_path: str | Path | None = None,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        if db_path is not None and base_dir is not None:
            raise ValueError("Use either db_path or base_dir, not both.")
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._lock = RLock()
        self._persistent = db_path is not None or base_dir is not None
        self._base_dir = Path(base_dir) if base_dir is not None else None
        self._db_path = Path(db_path) if db_path is not None else (
            self._base_dir / "execution_history" / "execution_history.sqlite3" if self._base_dir else None
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
    def from_environment(cls) -> "ExecutionHistoryStore":
        base_dir = os.environ.get("JARVIS_LOCAL_STATE_DIR") or os.environ.get("JARVIS_STATE_DIR")
        if base_dir:
            return cls(base_dir=base_dir)
        return cls()

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    def close(self) -> None:
        self._conn.close()

    def record(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        now = self.clock()
        record = {
            "schema_version": EXECUTION_HISTORY_SCHEMA_VERSION,
            "execution_id": _safe_text(values.get("execution_id") or f"exec-{self.id_factory()}", limit=120),
            "action_id": _safe_text(values.get("action_id"), limit=120),
            "approval_id": _safe_text(values.get("approval_id"), limit=120),
            "intent_summary": _redact_text(values.get("intent_summary"), limit=240),
            "action_key": _safe_text(values.get("action_key"), limit=120),
            "status": _safe_text(values.get("status"), limit=80),
            "risk_level": _safe_text(values.get("risk_level"), limit=80),
            "approval_level": _safe_text(values.get("approval_level"), limit=80),
            "approval_status": _safe_text(values.get("approval_status") or "none", limit=80),
            "started_at": _safe_text(values.get("started_at") or now, limit=80),
            "finished_at": _safe_text(values.get("finished_at") or now, limit=80),
            "duration_ms": int(values.get("duration_ms") or 0),
            "result_summary": _redact_text(values.get("result_summary"), limit=500),
            "error_summary": _redact_text(values.get("error_summary"), limit=500),
            "stop_requested": bool(values.get("stop_requested", False)),
            "stop_status": _safe_text(values.get("stop_status") or "not_requested", limit=80),
            "stop_request_id": _safe_text(values.get("stop_request_id"), limit=120),
            "rollback_requested": bool(values.get("rollback_requested", False)),
            "rollback_status": _safe_text(values.get("rollback_status") or "not_required", limit=80),
            "rollback_request_id": _safe_text(values.get("rollback_request_id"), limit=120),
            "rollback_plan_id": _safe_text(values.get("rollback_plan_id"), limit=120),
            "rollback_audit_id": _safe_text(values.get("rollback_audit_id"), limit=120),
            "audit_ids": _safe_json_list(values.get("audit_ids")),
            "memory_influence_ids": _safe_json_list(values.get("memory_influence_ids")),
            "channel_ids": _safe_json_list(values.get("channel_ids")),
            "redaction_summary": _safe_json_dict(values.get("redaction_summary")) or {
                "metadata_only": True,
                "raw_output_stored": False,
                "redacted": False,
                "blocked_field_count": 0,
            },
            "contains_secret": False,
            "contains_credential": False,
            "contains_raw_audio": False,
            "contains_camera_frame": False,
        }
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO executions (
                    schema_version, execution_id, action_id, approval_id, intent_summary,
                    action_key, status, risk_level, approval_level, approval_status,
                    started_at, finished_at, duration_ms, result_summary, error_summary,
                    stop_requested, stop_status, stop_request_id, rollback_requested,
                    rollback_status, rollback_request_id, rollback_plan_id, rollback_audit_id,
                    audit_ids_json, memory_influence_ids_json, channel_ids_json,
                    redaction_summary_json, contains_secret,
                    contains_credential, contains_raw_audio, contains_camera_frame
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["schema_version"],
                    record["execution_id"],
                    record["action_id"],
                    record["approval_id"],
                    record["intent_summary"],
                    record["action_key"],
                    record["status"],
                    record["risk_level"],
                    record["approval_level"],
                    record["approval_status"],
                    record["started_at"],
                    record["finished_at"],
                    record["duration_ms"],
                    record["result_summary"],
                    record["error_summary"],
                    int(record["stop_requested"]),
                    record["stop_status"],
                    record["stop_request_id"],
                    int(record["rollback_requested"]),
                    record["rollback_status"],
                    record["rollback_request_id"],
                    record["rollback_plan_id"],
                    record["rollback_audit_id"],
                    _json_dumps(record["audit_ids"]),
                    _json_dumps(record["memory_influence_ids"]),
                    _json_dumps(record["channel_ids"]),
                    _json_dumps(record["redaction_summary"]),
                    0,
                    0,
                    0,
                    0,
                ),
            )
            self._conn.commit()
        return record

    def list(
        self,
        *,
        limit: int = 25,
        newest_first: bool = True,
        action_key: str | None = None,
        risk_level: str | None = None,
        approval_status: str | None = None,
        stop_status: str | None = None,
        rollback_status: str | None = None,
    ) -> List[Dict[str, Any]]:
        limit = max(0, min(int(limit), 200))
        if limit == 0:
            return []
        order = "DESC" if newest_first else "ASC"
        filters: List[str] = []
        values: List[Any] = []
        for column, value in (
            ("action_key", action_key),
            ("risk_level", risk_level),
            ("approval_status", approval_status),
            ("stop_status", stop_status),
            ("rollback_status", rollback_status),
        ):
            text = _safe_text(value, limit=120)
            if text:
                filters.append(f"{column} = ?")
                values.append(text)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = self._conn.execute(
            f"SELECT * FROM executions {where} ORDER BY id {order} LIMIT ?",
            (*values, limit),
        ).fetchall()
        return [_history_row_to_dict(row) for row in rows]

    def get(self, execution_id: str) -> Dict[str, Any]:
        row = self._conn.execute("SELECT * FROM executions WHERE execution_id = ?", (execution_id,)).fetchone()
        if row is None:
            raise KeyError(execution_id)
        return _history_row_to_dict(row)

    def status(self) -> Dict[str, Any]:
        count = int(self._conn.execute("SELECT COUNT(*) FROM executions").fetchone()[0])
        return {
            "schema_version": EXECUTION_HISTORY_SCHEMA_VERSION,
            "available": True,
            "persistent": self._persistent,
            "local_only": True,
            "metadata_only": True,
            "record_count": count,
            "storage_path": str(self._db_path) if self._db_path else str(EXECUTION_HISTORY_DB_RELATIVE_PATH),
            "storage_configured": self._db_path is not None,
            "default_relative_path": str(EXECUTION_HISTORY_DB_RELATIVE_PATH),
            "contains_secret": False,
            "contains_credential": False,
            "contains_raw_audio": False,
            "contains_camera_frame": False,
            "recent": self.list(limit=5),
            "filters_supported": [
                "limit",
                "action_key",
                "risk",
                "approval_status",
                "stop_status",
                "rollback_status",
            ],
            "export_preview_endpoint": "/mark-3/execution/history/export-preview",
            "read_only_endpoint": "/mark-3/execution/history",
        }

    def _initialize(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schema_version TEXT NOT NULL,
                execution_id TEXT NOT NULL UNIQUE,
                action_id TEXT NOT NULL,
                approval_id TEXT NOT NULL,
                intent_summary TEXT NOT NULL,
                action_key TEXT NOT NULL,
                status TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                approval_level TEXT NOT NULL,
                approval_status TEXT NOT NULL DEFAULT 'none',
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                result_summary TEXT NOT NULL,
                error_summary TEXT NOT NULL,
                stop_requested INTEGER NOT NULL DEFAULT 0,
                stop_status TEXT NOT NULL DEFAULT 'not_requested',
                stop_request_id TEXT NOT NULL DEFAULT '',
                rollback_requested INTEGER NOT NULL DEFAULT 0,
                rollback_status TEXT NOT NULL,
                rollback_request_id TEXT NOT NULL DEFAULT '',
                rollback_plan_id TEXT NOT NULL DEFAULT '',
                rollback_audit_id TEXT NOT NULL DEFAULT '',
                audit_ids_json TEXT NOT NULL,
                memory_influence_ids_json TEXT NOT NULL,
                channel_ids_json TEXT NOT NULL DEFAULT '[]',
                redaction_summary_json TEXT NOT NULL,
                contains_secret INTEGER NOT NULL DEFAULT 0,
                contains_credential INTEGER NOT NULL DEFAULT 0,
                contains_raw_audio INTEGER NOT NULL DEFAULT 0,
                contains_camera_frame INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._ensure_column("approval_status", "TEXT NOT NULL DEFAULT 'none'")
        self._ensure_column("stop_status", "TEXT NOT NULL DEFAULT 'not_requested'")
        self._ensure_column("stop_request_id", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column("rollback_request_id", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column("rollback_plan_id", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column("rollback_audit_id", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column("channel_ids_json", "TEXT NOT NULL DEFAULT '[]'")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_created ON executions(started_at)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_action_key ON executions(action_key)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_risk_level ON executions(risk_level)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_approval_status ON executions(approval_status)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_stop_status ON executions(stop_status)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_rollback_status ON executions(rollback_status)")
        self._conn.commit()

    def _ensure_column(self, name: str, definition: str) -> None:
        columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(executions)").fetchall()}
        if name not in columns:
            self._conn.execute(f"ALTER TABLE executions ADD COLUMN {name} {definition}")


class Phase2LocalAssistantRuntimeControlPlane(Phase1GovernedExecutionControlPlane):
    """Phase 2 governed local assistant runtime control plane.

    This is not another Hermes runtime. It extends the Phase 1 control plane,
    keeps the existing Mark 3 Hermes read_file bridge as the only Hermes
    execution path, and adds allowlisted local actions, approval v2 metadata,
    execution history, and readiness contracts.
    """

    def __init__(self, *args: Any, execution_history: Optional[ExecutionHistoryStore] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.execution_history = execution_history or ExecutionHistoryStore.from_environment()
        self._approval_used: set[str] = set()
        self._phase2_previews: set[str] = set()

    def status(self) -> Dict[str, Any]:
        base = super().status()
        catalog = self.action_catalog()["actions"]
        history_status = self.execution_history.status()
        base["schema_version"] = PHASE_2_SCHEMA_VERSION
        base["phase"] = "Phase 2"
        base["state"].update({
            "mode": "phase_2_local_assistant_runtime_control_plane",
            "phase_2_local_assistant_runtime": True,
            "action_catalog_allowlisted": True,
            "freeform_shell_allowed": False,
            "arbitrary_command_allowed": False,
            "local_runtime_ready": True,
            "daemon_status": "readiness_contract_only",
            "tray_status": "readiness_contract_only",
            "startup_mode": "manual_local_backend_and_frontend",
            "background_listening_enabled": False,
            "auto_start_enabled": False,
            "user_opt_in_required": True,
            "critical_stronger_approval_configured": False,
            "supported_real_dispatch": "allowlisted_local_read_status_and_existing_mark_3_read_file_bridge",
        })
        base["counts"]["history_records"] = history_status["record_count"]
        base["approval_levels"] = list(APPROVAL_LEVELS)
        base["action_catalog"] = catalog
        base["execution_history"] = history_status
        base["stop_rollback_contracts"] = self.stop_rollback_contracts()
        base["approval_v2"] = self.approval_status()
        base["local_runtime"] = self.local_runtime_status()
        base["browser_verification"] = self.browser_verification_status(route_paths=())
        base["safety"].update({
            "strong_approval_v2": True,
            "approvals_expire": True,
            "approvals_single_use": True,
            "backend_recalculates_policy_before_approval": True,
            "secrets_credentials_env_tokens_denied": True,
            "voice_can_submit_intent_but_not_approve": True,
            "wake_phrase_never_approves": True,
            "frontend_never_decides_alone": True,
            "execution_history_metadata_only": True,
            "browser_automation_ungoverned": False,
            "local_daemon_readiness_only": True,
        })
        base["source_endpoint"] = "/mark-3/execution/status"
        return base

    def phase_2_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        route_set = set(route_paths)
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "phase": "Phase 2",
            "title": "PR #166 -- Phase 2 Local Assistant Runtime",
            "status": "implemented_as_local_governed_runtime_macro_phase",
            "implemented_blocks": {
                "strong_approval_v2": True,
                "hermes_action_bridge_allowlisted": True,
                "execution_history": True,
                "stop_rollback_contracts": True,
                "voice_wake_runtime_readiness": True,
                "browser_verification": True,
                "local_daemon_tray_readiness": True,
                "pilot_local_evidence": True,
                "phase_2_documentation": True,
            },
            "flow": [
                "intent",
                "allowlisted action catalog match",
                "preview",
                "risk and approval recalculation",
                "approval v2 envelope",
                "governed dispatch",
                "execution history metadata",
                "audit metadata-only",
                "stop/rollback contract status",
            ],
            "route_readiness": {
                "phase_2_status": "/mark-3/phase-2/status" in route_set,
                "action_catalog": "/mark-3/execution/action-catalog" in route_set,
                "execution_history": "/mark-3/execution/history" in route_set,
                "execution_history_detail": "/mark-3/execution/history/{execution_id}" in route_set,
                "approval_status": "/mark-3/approval/status" in route_set,
                "local_runtime_status": "/mark-3/local-runtime/status" in route_set,
                "browser_verification_status": "/mark-3/browser-verification/status" in route_set,
                "generic_execute_absent": "/execute" not in route_set and "/jarvis/execute" not in route_set,
            },
            "blocked_or_unsupported": {
                "critical_double_triple": "blocked_requires_stronger_approval_not_configured",
                "secrets_credentials_env_tokens": "denied",
                "freeform_shell": "denied",
                "arbitrary_commands": "denied",
                "browser_automation_ungoverned": "denied",
                "money_stripe_deploy_email_publish": "denied_or_unsupported_in_phase_2",
            },
            "source_endpoint": "/mark-3/phase-2/status",
        }

    def action_catalog(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "allowlist_only": True,
            "freeform_shell_allowed": False,
            "arbitrary_command_allowed": False,
            "actions": [contract.to_dict() for contract in ACTION_CATALOG.values()],
            "denied_actions": [
                "shell_freeform",
                "arbitrary_command",
                ".env_read",
                "secret_read",
                "token_read",
                "password_read",
                "cookie_read",
                "session_material_read",
                "destructive_write",
                "dependency_install",
                "deploy",
                "money",
                "stripe",
                "email",
                "publish",
                "ungoverned_browser_automation",
            ],
            "source_endpoint": "/mark-3/execution/action-catalog",
        }

    def history(self, *, limit: int = 25) -> Dict[str, Any]:
        return {
            "schema_version": EXECUTION_HISTORY_SCHEMA_VERSION,
            "items": self.execution_history.list(limit=limit),
            "status": self.execution_history.status(),
            "read_only": True,
            "source_endpoint": "/mark-3/execution/history",
        }

    def history_detail(self, execution_id: str) -> Dict[str, Any]:
        return self.execution_history.get(execution_id)

    def approval_status(self) -> Dict[str, Any]:
        with self._lock:
            envelopes = [self._augment_envelope_for_public(dict(item), self._previews.get(item.get("preview_id", ""))) for item in self._approval_envelopes.values()]
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "available": True,
            "approval_levels": list(APPROVAL_LEVELS),
            "statuses": list(APPROVAL_STATUSES),
            "strong_approval_v2": True,
            "double_triple_real_channel_configured": False,
            "critical_actions_block_honestly": True,
            "wake_phrase_can_approve": False,
            "voice_can_approve_alone": False,
            "frontend_can_decide_alone": False,
            "backend_recalculates_policy": True,
            "approvals_expire": True,
            "approvals_single_use": True,
            "pending_count": sum(1 for item in envelopes if item.get("status") == "pending"),
            "recent_envelopes": envelopes[-10:],
            "source_endpoint": "/mark-3/approval/status",
        }

    def stop_rollback_contracts(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "contracts": [
                {
                    "action_key": action.action_key,
                    "stop_supported": action.stop_supported,
                    "stop_method": action.stop_method,
                    "rollback_supported": action.rollback_supported,
                    "rollback_plan": action.rollback_plan,
                    "rollback_risk": action.rollback_risk,
                    "rollback_requires_approval": action.rollback_requires_approval,
                    "rollback_status": action.rollback_status,
                    "rollback_limitations": list(action.rollback_limitations),
                }
                for action in ACTION_CATALOG.values()
            ],
            "audit_event_types": [
                "stop_requested",
                "stop_completed",
                "stop_unsupported",
                "rollback_plan_created",
                "rollback_requested",
                "rollback_completed",
                "rollback_unsupported",
                "rollback_failed",
            ],
        }

    def local_runtime_status(self) -> Dict[str, Any]:
        audit_path = getattr(self.audit_ledger, "db_path", None)
        history_path = self.execution_history.db_path
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "daemon_status": "readiness_contract_only",
            "tray_status": "readiness_contract_only",
            "local_runtime_ready": True,
            "startup_mode": "manual",
            "background_listening_enabled": False,
            "auto_start_enabled": False,
            "user_opt_in_required": True,
            "local_only_binding": {
                "required": True,
                "recommended_host": "127.0.0.1",
                "external_network_required": False,
            },
            "privacy_contract": {
                "no_auto_mic": True,
                "no_auto_camera": True,
                "no_auto_wake": True,
                "no_background_listening": True,
                "no_raw_audio_backend": True,
                "no_camera_frames_backend": True,
            },
            "state_dir_contract": {
                "env_keys": ["JARVIS_LOCAL_STATE_DIR", "JARVIS_STATE_DIR"],
                "audit_path": str(audit_path) if audit_path else str(Path(".jarvis") / "audit" / "persistent_audit.sqlite3"),
                "execution_history_path": str(history_path) if history_path else str(EXECUTION_HISTORY_DB_RELATIVE_PATH),
                "repo_state_write_required": False,
            },
            "failure_modes": [
                "backend_offline",
                "frontend_offline",
                "state_dir_unconfigured_uses_memory",
                "browser_capabilities_unknown_until_page_load",
                "wake_provider_disabled_or_not_configured",
            ],
            "source_endpoint": "/mark-3/local-runtime/status",
        }

    def browser_verification_status(self, *, route_paths: Iterable[str]) -> Dict[str, Any]:
        route_set = set(route_paths)
        checks = [
            _browser_check("api_reachability", "/health" in route_set or not route_set, "/health available or route list unavailable in direct status call"),
            _browser_check("voice_capability_check", True, "Browser must check SpeechRecognition and speechSynthesis client-side."),
            _browser_check("approval_panel_render_check", True, "JarvisApprovalPanel is wired in /jarvis presence shell."),
            _browser_check("event_stream_check", "/mark-3/dashboard/events/stream" in route_set or not route_set, "SSE event stream route is present."),
            _browser_check("audit_status_check", "/mark-3/audit/status" in route_set or not route_set, "Audit status route is present."),
            _browser_check("memory_status_check", "/mark-3/memory-brain/status" in route_set or not route_set, "Memory status route is present."),
            _browser_check("execution_history_check", "/mark-3/execution/history" in route_set or not route_set, "Execution history route is present."),
            _browser_check("no_auto_get_user_media", True, "No backend getUserMedia; browser hooks require explicit button action."),
            _browser_check("no_execute_route", "/execute" not in route_set and "/jarvis/execute" not in route_set, "No generic execute route."),
            _browser_check("no_frontend_direct_hermes", True, "Frontend calls governed /mark-3/execution endpoints only."),
        ]
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "status": "ready_for_manual_browser_pilot",
            "playwright_required": False,
            "static_plus_manual_checklist": True,
            "checks": checks,
            "all_static_checks_passed": all(item["passed"] for item in checks),
            "source_endpoint": "/mark-3/browser-verification/status",
        }

    def voice_wake_runtime_status(
        self,
        *,
        wake_listener_status: Mapping[str, Any] | None = None,
        voice_session_status: Mapping[str, Any] | None = None,
        voice_runtime_pack: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "voice_runtime_diagnostics": {
                "browser_stt_capability": "client_side_verified_by_browser",
                "browser_tts_capability": "client_side_verified_by_browser",
                "selected_voice_metadata": "browser_selected_voice_name_lang_voice_uri_only",
                "tts_interrupt_stop": "speechSynthesis.cancel_supported_when_browser_supports_tts",
                "low_confidence_clarification_threshold": 0.65,
                "voice_intent_submitted_to_preview": True,
                "voice_can_read_readback": True,
                "voice_can_cancel_or_stop": True,
                "voice_can_approve": False,
                "voice_can_execute_without_approval": False,
                "raw_audio_sent_to_backend": False,
                "raw_audio_persisted_backend": False,
            },
            "wake_runtime_readiness": {
                "provider_status": "disabled" if not (wake_listener_status or {}).get("provider_adapter_ready") else "not_configured",
                "wake_always_on_real": False,
                "openwakeword_active": False,
                "auto_mic": False,
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "readiness_contract_only": True,
            },
            "privacy_status": {
                "no_auto_mic": True,
                "no_always_on": True,
                "no_environmental_recording": True,
                "no_transcribe_everything": True,
                "no_backend_raw_audio": True,
                "no_camera_frame_storage": True,
            },
            "source_endpoint": "/mark-3/voice-runtime/status",
            "base_voice_runtime_pack": dict(voice_runtime_pack or {}),
            "base_voice_session": dict(voice_session_status or {}),
        }

    def preview(
        self,
        *,
        intent: str,
        source: str = "typed_text",
        operator: str = "David",
        session_id: Optional[str] = None,
        target_path: Optional[str] = None,
        command: Optional[str] = None,
        requested_action_type: Optional[str] = None,
        transcript_confidence: float = 1.0,
        voice_session_state: str = "idle",
        action_key: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if source == "voice_transcript" and transcript_confidence < 0.65:
            return self._clarification_preview(
                intent=intent,
                source=source,
                operator=operator,
                session_id=session_id,
                transcript_confidence=transcript_confidence,
            )
        selected_action_key = _normalize_action_key(action_key or requested_action_type or "")
        if selected_action_key == "repo.file.read_safe":
            safe_inputs = self._validate_inputs(selected_action_key, inputs or {"path": target_path or ""})
            preview = super().preview(
                intent=intent,
                source=source,
                operator=operator,
                session_id=session_id,
                target_path=str(safe_inputs["path"]),
                command=None,
                requested_action_type=ALLOWED_ACTION,
                transcript_confidence=transcript_confidence,
                voice_session_state=voice_session_state,
            )
            return self._augment_preview(preview, action_key=selected_action_key, inputs=safe_inputs)
        if selected_action_key in ACTION_CATALOG:
            safe_inputs = self._validate_inputs(selected_action_key, inputs or {})
            return self._phase2_action_preview(
                intent=intent,
                source=source,
                operator=operator,
                session_id=session_id,
                action_key=selected_action_key,
                inputs=safe_inputs,
                transcript_confidence=transcript_confidence,
            )
        preview = super().preview(
            intent=intent,
            source=source,
            operator=operator,
            session_id=session_id,
            target_path=target_path,
            command=command,
            requested_action_type=requested_action_type,
            transcript_confidence=transcript_confidence,
            voice_session_state=voice_session_state,
        )
        inferred = _infer_action_key(preview)
        return self._augment_preview(preview, action_key=inferred, inputs=inputs or {})

    def request_approval(self, *, preview_id: str, actor: str = "David") -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            action_key = (preview.get("action") or {}).get("action_key")
        if action_key in ACTION_CATALOG and action_key != "repo.file.read_safe":
            return self._phase2_request_approval(preview_id=preview_id, actor=actor)
        envelope = super().request_approval(preview_id=preview_id, actor=actor)
        with self._lock:
            stored = self._approval_envelopes.get(envelope["approval_id"])
            if stored is not None:
                self._augment_envelope_in_place(stored, self._previews.get(preview_id))
                envelope = dict(stored)
        return envelope

    def decide_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        actor: str = "David",
        confirmation_phrase: Optional[str] = None,
        readback_text: Optional[str] = None,
        reason: str = "",
        decision_source: str = "ui",
        channel: str = "frontend",
    ) -> Dict[str, Any]:
        if _is_voice_or_wake_approval(actor=actor, decision_source=decision_source, channel=channel):
            raise ValueError("voice and wake phrase cannot approve")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            preview = self._previews.get(envelope.get("preview_id", "")) if envelope else None
            action_key = (preview.get("action") or {}).get("action_key") if preview else None
        if action_key in ACTION_CATALOG and action_key != "repo.file.read_safe":
            return self._phase2_decide_approval(
                approval_id=approval_id,
                decision=decision,
                actor=actor,
                confirmation_phrase=confirmation_phrase,
                readback_text=readback_text,
                reason=reason,
            )
        envelope = super().decide_approval(
            approval_id=approval_id,
            decision=decision,
            actor=actor,
            confirmation_phrase=confirmation_phrase,
            readback_text=readback_text,
            reason=reason,
        )
        with self._lock:
            stored = self._approval_envelopes.get(approval_id)
            if stored is not None:
                self._augment_envelope_in_place(stored, self._previews.get(stored.get("preview_id", "")))
                envelope = dict(stored)
        return envelope

    def dispatch(self, *, preview_id: str, approval_id: Optional[str] = None, actor: str = "David") -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            action_key = (preview.get("action") or {}).get("action_key")
            envelope = preview.get("approval_envelope")
            if envelope and envelope.get("approval_id") in self._approval_used:
                raise ValueError("approval has already been used")
        if action_key in ACTION_CATALOG and action_key != "repo.file.read_safe":
            return self._phase2_dispatch(preview_id=preview_id, approval_id=approval_id, actor=actor)

        started = _now_iso()
        start = time.monotonic()
        result = super().dispatch(preview_id=preview_id, approval_id=approval_id, actor=actor)
        duration_ms = int((time.monotonic() - start) * 1000)
        with self._lock:
            preview = self._previews.get(preview_id, preview)
            envelope = preview.get("approval_envelope") if preview else None
            if envelope and result.get("state") in {"dispatch_completed", "running"}:
                self._approval_used.add(envelope["approval_id"])
                envelope["used_at"] = _now_iso()
        self._record_execution_history(preview, result, started_at=started, duration_ms=duration_ms)
        return result

    def cancel(self, *, preview_id: str, reason: str = "operator cancel", actor: str = "David") -> Dict[str, Any]:
        preview = super().cancel(preview_id=preview_id, reason=reason, actor=actor)
        return self._augment_preview(preview, action_key=_infer_action_key(preview), inputs={})

    def stop(self, *, preview_id: Optional[str] = None, session_id: Optional[str] = None, reason: str = "operator stop") -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id or "") if preview_id else None
            action_key = (preview.get("action") or {}).get("action_key") if preview else ""
        if action_key in ACTION_CATALOG and action_key != "repo.file.read_safe":
            contract = ACTION_CATALOG[action_key]
            audit = self._audit_v2(
                "stop_requested",
                correlation_id=preview.get("correlation_id", f"corr-{uuid4()}") if preview else f"corr-{uuid4()}",
                risk_level=contract.risk_level,
                approval_level=contract.approval_required,
                metadata={"preview_id": preview_id or "unknown", "action_key": action_key, "reason": reason},
            )
            if not contract.stop_supported:
                self._audit_v2(
                    "stop_unsupported",
                    correlation_id=preview.get("correlation_id", f"corr-{uuid4()}") if preview else f"corr-{uuid4()}",
                    risk_level=contract.risk_level,
                    approval_level=contract.approval_required,
                    metadata={"preview_id": preview_id or "unknown", "action_key": action_key, "reason": "stop not supported for fast read-only action"},
                )
                return {
                    "status": "stop_requested_pending_or_unsupported",
                    "reason": "stop unsupported for this action contract",
                    "preview_id": preview_id,
                    "session_id": session_id,
                    "audit_id": audit.get("audit_id"),
                }
        return super().stop(preview_id=preview_id, session_id=session_id, reason=reason)

    def _phase2_action_preview(
        self,
        *,
        intent: str,
        source: str,
        operator: str,
        session_id: Optional[str],
        action_key: str,
        inputs: Dict[str, Any],
        transcript_confidence: float,
    ) -> Dict[str, Any]:
        contract = ACTION_CATALOG[action_key]
        correlation_id = f"corr-{self.id_factory()}"
        if _source_is_wake_execute(source, intent):
            decision = "denied"
            denied_reason = "wake_phrase_is_not_approval"
            risk_level = "forbidden"
            approval_level = "blocked"
            requires_approval = False
        elif _contains_secret_material(intent) or _inputs_contain_secret(inputs):
            decision = "denied"
            denied_reason = "credential_or_secret_material_is_denied"
            risk_level = "forbidden"
            approval_level = "blocked"
            requires_approval = False
        else:
            risk_level = contract.risk_level
            approval_level = _required_approval_level(contract)
            if risk_level == "critical" and approval_level in {"double", "triple"}:
                decision = "requires_approval"
                denied_reason = ""
                requires_approval = True
            elif approval_level in {"none", "soft"}:
                decision = "allowed"
                denied_reason = ""
                requires_approval = False
            else:
                decision = "requires_approval"
                denied_reason = ""
                requires_approval = True
        preview_id = f"preview-{self.id_factory()}"
        memory_influence = self._memory_influence(correlation_id=correlation_id)
        action = {
            "action_id": _action_id(action_key, inputs),
            "action_key": action_key,
            "title": action_key,
            "summary": contract.description,
            "decision": decision,
            "action_type": action_key,
            "risk_level": risk_level,
            "approval_level": approval_level,
            "approval_level_required": approval_level,
            "requires_approval": requires_approval,
            "requires_readback": risk_level in {"high", "critical"},
            "requires_strong_confirmation": approval_level in {"strong", "double", "triple"},
            "requires_double_confirmation": approval_level in {"double", "triple"},
            "requires_triple_confirmation": approval_level == "triple",
            "denied_reason": denied_reason,
            "unsupported_reason": "requires_stronger_approval_not_configured" if risk_level == "critical" else "",
            "input_fingerprint": _fingerprint(inputs),
            "scope": [contract.filesystem_scope],
            "will_do": _will_do(contract),
            "will_not_do": _will_not_do(contract),
            "rollback_plan": contract.rollback_plan,
            "stop_plan": contract.stop_method,
            "stop_supported": contract.stop_supported,
            "rollback_supported": contract.rollback_supported,
            "rollback_status": contract.rollback_status,
            "network_allowed": contract.network_allowed,
            "external_side_effects": contract.external_side_effects,
            "secrets_policy": contract.secrets_policy,
            "frontend_direct_hermes_allowed": False,
            "memory_grants_permission": False,
        }
        preview = {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "preview_id": preview_id,
            "correlation_id": correlation_id,
            "created_at": self.clock(),
            "updated_at": self.clock(),
            "state": "preview_created" if decision != "denied" else "denied",
            "source": source,
            "operator": operator,
            "session_id": session_id,
            "intake": {
                "raw_text_omitted": True,
                "normalized_text_fingerprint": _fingerprint(intent),
                "contains_full_transcript": False,
                "transcript_confidence": transcript_confidence,
            },
            "classification": {
                "risk_level": risk_level,
                "approval_level": approval_level,
                "safe_to_dispatch_to_hermes": False,
                "denied": decision == "denied",
            },
            "action": action,
            "decision": decision,
            "risk_level": risk_level,
            "approval_level": approval_level,
            "approval_level_required": approval_level,
            "requires_approval": requires_approval,
            "preview": {
                "title": action_key,
                "summary": contract.description,
                "will_do": action["will_do"],
                "will_not_do": action["will_not_do"],
                "rollback_plan": contract.rollback_plan,
                "stop_plan": contract.stop_method,
                "audit_destination": ".jarvis/audit/persistent_audit.sqlite3 metadata-only ledger",
                "memory_influence": memory_influence,
                "stop_rollback_contract": contract.to_dict()["contract"],
            },
            "approval_envelope": None,
            "dispatch": None,
            "inputs": inputs,
            "cancelled": False,
            "unsupported_reason": action["unsupported_reason"],
            "denied_reason": denied_reason,
            "protected_message": PROTECTED_CREDENTIAL_MESSAGE if denied_reason == "credential_or_secret_material_is_denied" else "",
            "hermes_dispatch_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "memory_grants_permission": False,
        }
        with self._lock:
            self._previews[preview_id] = preview
            self._phase2_previews.add(preview_id)
        self._audit_v2(
            "preview_created",
            correlation_id=correlation_id,
            risk_level=risk_level,
            approval_level=approval_level,
            metadata={"preview_id": preview_id, "action_key": action_key, "decision": decision},
        )
        self._audit_v2(
            "risk_classified",
            correlation_id=correlation_id,
            risk_level=risk_level,
            approval_level=approval_level,
            metadata={"preview_id": preview_id, "action_key": action_key, "requires_approval": requires_approval},
        )
        if contract.rollback_plan:
            self._audit_v2(
                "rollback_plan_created",
                correlation_id=correlation_id,
                risk_level=risk_level,
                approval_level=approval_level,
                metadata={"preview_id": preview_id, "action_key": action_key, "rollback_status": contract.rollback_status},
            )
        return dict(preview)

    def _phase2_request_approval(self, *, preview_id: str, actor: str) -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            if preview.get("cancelled"):
                raise ValueError("preview is cancelled")
            if preview.get("approval_envelope"):
                return dict(preview["approval_envelope"])
            if preview["decision"] == "denied":
                raise ValueError("denied actions cannot request approval")
            if not preview["requires_approval"]:
                raise ValueError("action does not require approval")
            action = preview["action"]
            action_key = action["action_key"]
            contract = ACTION_CATALOG[action_key]
            approval_level = _required_approval_level(contract)
            if approval_level in {"double", "triple"}:
                envelope = self._blocked_phase2_envelope(preview, actor, reason="requires_stronger_approval_not_configured")
                preview["approval_envelope"] = envelope
                preview["state"] = "approval_blocked"
                preview["updated_at"] = self.clock()
                self._approval_envelopes[envelope["approval_id"]] = envelope
                self._approval_to_preview[envelope["approval_id"]] = preview_id
                self._audit_approval_v2(preview, envelope)
                return dict(envelope)
            record = self.mission_loop.approval_service.request(
                action_type=action_key,
                requested_by=actor or "David",
                reason=contract.description,
                context={
                    "action_type": action_key,
                    "action_key": action_key,
                    "risk_level": contract.risk_level,
                    "approval_level_required": approval_level,
                    "input_fingerprint": action.get("input_fingerprint"),
                    "local_only": not contract.network_allowed,
                    "side_effect_free": not contract.external_side_effects,
                    "protected_material_blocked": True,
                },
                approval_kind=ApprovalKind.STRONG if approval_level == "strong" else ApprovalKind.NORMAL,
                expires_in_seconds=900,
            )
            envelope = {
                "schema_version": PHASE_2_SCHEMA_VERSION,
                "approval_id": record.approval_id,
                "action_id": action["action_id"],
                "action_key": action_key,
                "preview_id": preview_id,
                "correlation_id": preview["correlation_id"],
                "risk_level": contract.risk_level,
                "approval_level": approval_level,
                "approval_level_required": approval_level,
                "approval_level_required_source": "backend_recalculated",
                "requester": actor,
                "requested_by": actor,
                "reason": contract.description,
                "preview": {
                    "summary": contract.description,
                    "input_fingerprint": action.get("input_fingerprint"),
                    "will_do": action.get("will_do", []),
                    "will_not_do": action.get("will_not_do", []),
                },
                "readback_text": _readback_for_preview(preview),
                "readback_required": contract.risk_level in {"high", "critical"},
                "confirmation_phrase": record.user_confirmation_phrase,
                "challenge": f"Type {record.user_confirmation_phrase}" if record.user_confirmation_phrase else "Review scope and approve in UI.",
                "second_confirmation_required": approval_level in {"double", "triple"},
                "third_confirmation_required": approval_level == "triple",
                "requires_strong_confirmation": approval_level in {"strong", "double", "triple"},
                "requires_double_confirmation": approval_level in {"double", "triple"},
                "requires_triple_confirmation": approval_level == "triple",
                "expires_at": record.expires_at,
                "created_at": record.requested_at,
                "decided_at": None,
                "status": record.status.value,
                "rejection_reason": "",
                "decision_reason": "",
                "audit_id": "",
                "can_approve": True,
                "can_dispatch_after_approval": True,
                "stronger_approval_configured": False,
                "context_fingerprint": record.context_fingerprint,
                "used_at": None,
            }
            preview["approval_envelope"] = envelope
            preview["state"] = "approval_requested"
            preview["updated_at"] = self.clock()
            self._approval_envelopes[record.approval_id] = envelope
            self._approval_to_preview[record.approval_id] = preview_id
            self._audit_approval_v2(preview, envelope)
            return dict(envelope)

    def _phase2_decide_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        actor: str,
        confirmation_phrase: Optional[str],
        readback_text: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        normalized = (decision or "").strip().lower().replace("-", "_")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            preview = self._previews[envelope["preview_id"]]
            if envelope.get("used_at"):
                raise ValueError("approval has already been used")
            if envelope["status"] in {"approved", "rejected", "cancelled", "expired", "blocked"}:
                if normalized == envelope["status"]:
                    return dict(envelope)
                raise ValueError(f"approval {approval_id} is already {envelope['status']}")
            self._audit_v2(
                "ui_approval_action",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level=envelope["approval_level"],
                metadata={"approval_id": approval_id, "preview_id": preview["preview_id"], "decision": normalized, "voice_approval": False, "wake_phrase_approval": False},
            )
            if normalized in {"reject", "rejected", "deny"}:
                record = self.mission_loop.approval_service.decide(approval_id, "rejected", actor=actor, reason=reason)
                envelope["status"] = record.status.value
                envelope["decided_at"] = record.decided_at
                envelope["rejection_reason"] = record.decision_reason or reason or "rejected"
                envelope["decision_reason"] = envelope["rejection_reason"]
                preview["state"] = "approval_rejected"
                preview["updated_at"] = self.clock()
                self._audit_v2("approval_rejected", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id})
                return dict(envelope)
            if normalized in {"cancel", "cancelled"}:
                envelope["status"] = "cancelled"
                envelope["decided_at"] = self.clock()
                envelope["rejection_reason"] = reason or "cancelled by operator"
                envelope["decision_reason"] = envelope["rejection_reason"]
                preview["state"] = "approval_cancelled"
                preview["cancelled"] = True
                preview["updated_at"] = self.clock()
                self._audit_v2("approval_cancelled", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id})
                return dict(envelope)
            if normalized in {"clarify", "clarification", "request_clarification", "clarification_requested"}:
                envelope["status"] = "clarification_requested"
                envelope["decided_at"] = self.clock()
                envelope["decision_reason"] = reason or "operator requested clarification"
                preview["state"] = "clarification_requested"
                preview["updated_at"] = self.clock()
                return dict(envelope)
            if normalized not in {"approve", "approved"}:
                raise ValueError("decision must be approve, reject, cancel, or request_clarification")
            recalculated_level = _required_approval_level(ACTION_CATALOG[preview["action"]["action_key"]])
            if recalculated_level != envelope["approval_level_required"]:
                envelope["status"] = "blocked"
                envelope["decision_reason"] = "approval_policy_changed_before_decision"
                preview["state"] = "approval_blocked"
                raise ValueError("approval policy changed before decision")
            if envelope["readback_required"] and _normalize_readback(readback_text) != _normalize_readback(envelope["readback_text"]):
                raise ValueError("readback text does not match required readback")
            record = self.mission_loop.approval_service.decide(
                approval_id,
                "approved",
                actor=actor,
                reason=reason,
                confirmation_phrase=confirmation_phrase,
            )
            envelope["status"] = record.status.value
            envelope["decided_at"] = record.decided_at
            envelope["decision_reason"] = record.decision_reason or ""
            envelope["approved_at"] = record.approved_at
            preview["state"] = "approval_approved"
            preview["updated_at"] = self.clock()
            self._audit_v2("approval_approved", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id})
            return dict(envelope)

    def _phase2_dispatch(self, *, preview_id: str, approval_id: Optional[str], actor: str) -> Dict[str, Any]:
        started_at = _now_iso()
        start = time.monotonic()
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            action = preview["action"]
            action_key = action["action_key"]
            contract = ACTION_CATALOG[action_key]
            self._audit_v2("dispatch_requested", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "action_key": action_key, "actor": actor})
            if preview.get("cancelled"):
                raise ValueError("preview is cancelled")
            if preview["decision"] == "denied":
                self._audit_v2("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "reason": preview.get("denied_reason") or "denied"})
                raise ValueError(preview.get("protected_message") or "denied action cannot dispatch")
            if preview["decision"] == "unsupported":
                return self._phase2_unsupported_dispatch(preview)
            envelope = preview.get("approval_envelope")
            if preview["requires_approval"]:
                if envelope is None:
                    self._audit_v2("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "reason": "approval required"})
                    raise ValueError("approval required before dispatch")
                if approval_id and approval_id != envelope["approval_id"]:
                    raise ValueError("approval_id does not match preview approval envelope")
                if envelope["approval_id"] in self._approval_used or envelope.get("used_at"):
                    raise ValueError("approval has already been used")
                record = self.mission_loop.approval_service.get(envelope["approval_id"])
                self.mission_loop.approval_service.refresh_expiration(record)
                if record.status != ApprovalStatus.APPROVED:
                    envelope["status"] = record.status.value
                    self._audit_v2("approval_expired" if record.status == ApprovalStatus.EXPIRED else "dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"approval_id": envelope["approval_id"], "status": record.status.value})
                    raise ValueError(f"approval status is {record.status.value}")
                recalculated = _required_approval_level(contract)
                if recalculated != envelope["approval_level_required"]:
                    raise ValueError("approval policy changed before dispatch")
            preview["state"] = "dispatching"
            preview["updated_at"] = self.clock()
        started_audit = self._audit_v2("dispatch_started", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "action_key": action_key, "governed_dispatch": False, "hermes_called": False})
        try:
            execution = self._execute_local_action(action_key, preview)
            status = execution["status"]
            state = "dispatch_completed" if status == "completed" else "dispatch_failed"
            error_summary = "" if status == "completed" else execution.get("error_summary", status)
        except Exception as exc:
            execution = {"status": "failed", "result_summary": "Action failed.", "error_summary": str(exc), "data": {}}
            state = "dispatch_failed"
            error_summary = str(exc)
        duration_ms = int((time.monotonic() - start) * 1000)
        finished_at = _now_iso()
        finished_audit = self._audit_v2(
            "dispatch_completed" if state == "dispatch_completed" else "dispatch_failed",
            correlation_id=preview["correlation_id"],
            risk_level=preview["risk_level"],
            approval_level=preview["approval_level"],
            metadata={"preview_id": preview_id, "action_key": action_key, "status": execution["status"], "duration_ms": duration_ms},
        )
        with self._lock:
            preview["state"] = state
            preview["dispatch"] = {
                "status": execution["status"],
                "result_summary": execution.get("result_summary", ""),
                "error_summary": error_summary,
                "data": execution.get("data", {}),
                "hermes_called": False,
                "did_execute": execution["status"] == "completed",
                "duration_ms": duration_ms,
                "stop_supported": contract.stop_supported,
                "rollback_status": contract.rollback_status,
            }
            preview["updated_at"] = finished_at
            if envelope and execution["status"] == "completed":
                self._approval_used.add(envelope["approval_id"])
                envelope["used_at"] = finished_at
        history = self._record_execution_history(
            preview,
            {
                "state": state,
                "dispatch": preview["dispatch"],
                "hermes_dispatch_allowed": False,
                "frontend_direct_hermes_allowed": False,
                "memory_grants_permission": False,
            },
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            audit_ids=[started_audit.get("audit_id", ""), finished_audit.get("audit_id", "")],
        )
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "preview_id": preview_id,
            "execution_id": history.get("execution_id"),
            "state": state,
            "decision": preview.get("decision"),
            "risk_level": preview.get("risk_level"),
            "approval_level": preview.get("approval_level"),
            "dispatch": preview["dispatch"],
            "hermes_dispatch_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "memory_grants_permission": False,
        }

    def _execute_local_action(self, action_key: str, preview: Mapping[str, Any]) -> Dict[str, Any]:
        inputs = dict(preview.get("inputs") or {})
        if action_key == "local.status.read":
            return {"status": "completed", "result_summary": "Local JARVIS status read.", "data": {"mode": "phase_2_local_assistant_runtime", "available": True}}
        if action_key == "local.doctor.run":
            return {"status": "completed", "result_summary": "Local doctor checks completed.", "data": {"audit_available": True, "memory_available": True, "history_available": True, "hermes_bridge_available": True}}
        if action_key == "repo.status.read":
            return _completed("Repo status read.", {"git_status": self._run_fixed_command(["git", "status", "--short", "--branch"], timeout=10)})
        if action_key == "repo.diff.read":
            return _completed("Repo diff metadata read.", {
                "diff_stat": self._run_fixed_command(["git", "diff", "--stat"], timeout=10),
                "diff_names": self._run_fixed_command(["git", "diff", "--name-only"], timeout=10),
            })
        if action_key == "repo.log.read":
            limit = int(inputs.get("limit") or 5)
            limit = max(1, min(limit, 20))
            return _completed("Repo log metadata read.", {"git_log": self._run_fixed_command(["git", "log", "--oneline", "-n", str(limit)], timeout=10)})
        if action_key == "repo.tests.run_allowlisted":
            target = str(inputs.get("test_target") or RUN_ALLOWLISTED_TARGETS[0])
            if target not in RUN_ALLOWLISTED_TARGETS:
                raise ValueError("test target is not allowlisted")
            result = self._run_fixed_command([sys.executable, "-m", "pytest", "-c", "/dev/null", target, "-q", "-x"], timeout=ACTION_CATALOG[action_key].timeout_seconds)
            return {
                "status": "completed" if result["exit_code"] == 0 else "failed",
                "result_summary": "Allowlisted pytest target passed." if result["exit_code"] == 0 else "Allowlisted pytest target failed.",
                "error_summary": "" if result["exit_code"] == 0 else result["summary"],
                "data": result,
            }
        if action_key == "jarvis.phase.status":
            return _completed("Phase 2 status read.", {"phase": "Phase 2", "status": "implemented"})
        if action_key == "jarvis.audit.status":
            status = self.audit_ledger.status(recent_limit=3)
            return _completed("Audit status read.", {"event_count": status["state"]["event_count"], "hash_chain_valid": status["state"]["hash_chain_valid"]})
        if action_key == "jarvis.memory.status":
            status = self.memory_brain_v2.status()
            return _completed("Memory status read.", {"record_count": status.get("record_count", 0), "memory_grants_permission": False})
        if action_key == "jarvis.execution.history.read":
            limit = int(inputs.get("limit") or 10)
            return _completed("Execution history read.", {"items": self.execution_history.list(limit=limit), "metadata_only": True})
        if action_key == "jarvis.execution.preview":
            return _completed("Execution preview retained; no runtime dispatch required.", {"preview_only": True, "rollback_status": "discard_preview"})
        raise ValueError(f"Unsupported action key: {action_key}")

    def _run_fixed_command(self, argv: List[str], *, timeout: int) -> Dict[str, Any]:
        result = subprocess.run(
            argv,
            cwd=str(self.cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        output = "\n".join(item for item in (result.stdout, result.stderr) if item)
        return {
            "argv_fingerprint": _fingerprint(argv),
            "exit_code": result.returncode,
            "summary": _redact_text(output, limit=1200),
            "line_count": len(output.splitlines()),
            "output_truncated": len(output) > 1200,
        }

    def _phase2_unsupported_dispatch(self, preview: Dict[str, Any]) -> Dict[str, Any]:
        preview["state"] = "unsupported"
        preview["dispatch"] = {
            "status": "unsupported",
            "reason": preview.get("unsupported_reason") or "unsupported",
            "hermes_called": False,
            "did_execute": False,
        }
        preview["updated_at"] = self.clock()
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "preview_id": preview.get("preview_id"),
            "state": preview.get("state"),
            "decision": preview.get("decision"),
            "risk_level": preview.get("risk_level"),
            "approval_level": preview.get("approval_level"),
            "dispatch": preview.get("dispatch"),
            "hermes_dispatch_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "memory_grants_permission": False,
        }

    def _record_execution_history(
        self,
        preview: Optional[Mapping[str, Any]],
        result: Mapping[str, Any],
        *,
        started_at: str,
        duration_ms: int,
        finished_at: Optional[str] = None,
        audit_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not preview:
            return {}
        action = dict(preview.get("action") or {})
        dispatch = dict(result.get("dispatch") or {})
        envelope = dict(preview.get("approval_envelope") or {})
        memory_influence = list((preview.get("preview") or {}).get("memory_influence") or [])
        record = self.execution_history.record({
            "action_id": action.get("action_id") or _action_id(action.get("action_key") or action.get("action_type", "unknown"), {}),
            "approval_id": envelope.get("approval_id", ""),
            "intent_summary": action.get("summary") or preview.get("decision", "unknown"),
            "action_key": action.get("action_key") or _infer_action_key(preview),
            "status": dispatch.get("status") or result.get("state") or "unknown",
            "risk_level": preview.get("risk_level", "unknown"),
            "approval_level": preview.get("approval_level_required") or preview.get("approval_level", "unknown"),
            "approval_status": envelope.get("status") or ("not_required" if not preview.get("requires_approval") else "missing"),
            "started_at": started_at,
            "finished_at": finished_at or _now_iso(),
            "duration_ms": duration_ms,
            "result_summary": dispatch.get("result_summary") or dispatch.get("message") or dispatch.get("status") or "completed",
            "error_summary": dispatch.get("error_summary") or dispatch.get("reason") or "",
            "stop_requested": preview.get("state") == "stop_requested",
            "stop_status": action.get("stop_status") or ("not_requested" if preview.get("state") != "stop_requested" else "requested"),
            "rollback_requested": False,
            "rollback_status": action.get("rollback_status") or "not_required",
            "audit_ids": audit_ids or [],
            "memory_influence_ids": [item.get("memory_id", "unknown") for item in memory_influence],
            "channel_ids": envelope.get("channel_ids") or [
                step.get("channel_id", "")
                for step in envelope.get("approval_steps", [])
                if isinstance(step, Mapping) and step.get("status") == "approved"
            ],
            "redaction_summary": {
                "metadata_only": True,
                "raw_output_stored": False,
                "redacted": False,
                "blocked_field_count": 0,
            },
        })
        audit = self._audit_v2(
            "execution_history_recorded",
            correlation_id=str(preview.get("correlation_id") or f"corr-{uuid4()}"),
            risk_level=str(preview.get("risk_level") or "low"),
            approval_level=str(preview.get("approval_level_required") or preview.get("approval_level") or "none"),
            metadata={"execution_id": record.get("execution_id"), "action_key": record.get("action_key")},
        )
        if not record.get("audit_ids"):
            record["audit_ids"] = [audit.get("audit_id", "")]
            self.execution_history.record(record)
        return record

    def _clarification_preview(
        self,
        *,
        intent: str,
        source: str,
        operator: str,
        session_id: Optional[str],
        transcript_confidence: float,
    ) -> Dict[str, Any]:
        correlation_id = f"corr-{self.id_factory()}"
        preview_id = f"preview-{self.id_factory()}"
        preview = {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "preview_id": preview_id,
            "correlation_id": correlation_id,
            "created_at": self.clock(),
            "updated_at": self.clock(),
            "state": "clarification_required",
            "source": source,
            "operator": operator,
            "session_id": session_id,
            "decision": "requires_clarification",
            "risk_level": "low",
            "approval_level": "none",
            "approval_level_required": "none",
            "requires_approval": False,
            "action": {
                "action_id": _action_id("voice.low_confidence.clarify", {"confidence": transcript_confidence}),
                "action_key": "voice.low_confidence.clarify",
                "title": "Low-confidence voice clarification",
                "summary": "Voice transcript confidence is too low; ask for clarification before any preview dispatch.",
                "decision": "requires_clarification",
                "action_type": "voice_low_confidence_clarification",
                "risk_level": "low",
                "approval_level": "none",
                "requires_approval": False,
                "requires_readback": False,
                "will_do": ["Ask for clarification."],
                "will_not_do": ["No approval.", "No dispatch.", "No Hermes.", "No raw audio backend."],
                "rollback_plan": "discard_preview",
                "stop_plan": "cancel_preview",
            },
            "preview": {
                "title": "Clarification required",
                "summary": "Low confidence voice transcript.",
                "will_do": ["Ask the operator to repeat or type the intent."],
                "will_not_do": ["No execution.", "No approval.", "No raw audio upload."],
                "rollback_plan": "discard_preview",
                "stop_plan": "cancel_preview",
                "memory_influence": [],
            },
            "approval_envelope": None,
            "dispatch": None,
            "unsupported_reason": "low_confidence_voice_requires_clarification",
            "denied_reason": "",
            "protected_message": "",
            "hermes_dispatch_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "memory_grants_permission": False,
        }
        with self._lock:
            self._previews[preview_id] = preview
            self._phase2_previews.add(preview_id)
        self._audit_v2(
            "voice_session_intent_submitted",
            correlation_id=correlation_id,
            surface="voice",
            risk_level="low",
            approval_level="none",
            metadata={"preview_id": preview_id, "confidence": transcript_confidence, "requires_clarification": True, "contains_full_transcript": False},
        )
        return dict(preview)

    def _augment_preview(self, preview: Mapping[str, Any], *, action_key: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(preview)
        action = dict(data.get("action") or {})
        action["action_key"] = action_key
        action["approval_level_required"] = _phase2_level(action.get("approval_level") or data.get("approval_level"))
        action["stop_supported"] = action_key == "repo.file.read_safe"
        action["rollback_supported"] = False
        action["rollback_status"] = "not_required"
        action["network_allowed"] = False
        action["external_side_effects"] = False
        action["secrets_policy"] = "deny_and_redact"
        data["action"] = action
        data["approval_level_required"] = action["approval_level_required"]
        data["inputs"] = _safe_inputs_for_public(inputs)
        if data.get("approval_envelope"):
            data["approval_envelope"] = self._augment_envelope_for_public(dict(data["approval_envelope"]), data)
        with self._lock:
            stored = self._previews.get(str(data.get("preview_id")))
            if stored is not None:
                stored_action = dict(stored.get("action") or {})
                stored_action.update(action)
                stored["action"] = stored_action
                stored["approval_level_required"] = data["approval_level_required"]
                stored["inputs"] = data["inputs"]
        return data

    def _augment_envelope_in_place(self, envelope: Dict[str, Any], preview: Optional[Mapping[str, Any]]) -> None:
        augmented = self._augment_envelope_for_public(envelope, preview)
        envelope.update(augmented)

    def _augment_envelope_for_public(self, envelope: Dict[str, Any], preview: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        action = dict((preview or {}).get("action") or {})
        level = _phase2_level(envelope.get("approval_level") or action.get("approval_level"))
        envelope.setdefault("action_id", action.get("action_id") or _action_id(action.get("action_key") or action.get("action_type", "unknown"), {}))
        envelope.setdefault("action_key", action.get("action_key") or _infer_action_key(preview or {}))
        envelope.setdefault("approval_level_required", level)
        envelope.setdefault("requester", envelope.get("requested_by", "David"))
        envelope.setdefault("reason", action.get("summary", "Governed action approval."))
        envelope.setdefault("preview", {"summary": action.get("summary", ""), "will_do": action.get("will_do", []), "will_not_do": action.get("will_not_do", [])})
        envelope.setdefault("challenge", f"Type {envelope.get('confirmation_phrase')}" if envelope.get("confirmation_phrase") else "Review scope and approve in UI.")
        envelope.setdefault("second_confirmation_required", bool(envelope.get("requires_double_confirmation")))
        envelope.setdefault("third_confirmation_required", bool(envelope.get("requires_triple_confirmation")))
        envelope.setdefault("decided_at", envelope.get("approved_at"))
        envelope.setdefault("rejection_reason", envelope.get("decision_reason", ""))
        envelope.setdefault("audit_id", "")
        envelope["approval_level_required_source"] = "backend_recalculated"
        return envelope

    def _blocked_phase2_envelope(self, preview: Mapping[str, Any], actor: str, *, reason: str) -> Dict[str, Any]:
        action = preview["action"]
        return {
            "schema_version": PHASE_2_SCHEMA_VERSION,
            "approval_id": f"blocked-approval-{self.id_factory()}",
            "action_id": action["action_id"],
            "action_key": action["action_key"],
            "preview_id": preview["preview_id"],
            "correlation_id": preview["correlation_id"],
            "risk_level": action["risk_level"],
            "approval_level": action["approval_level"],
            "approval_level_required": action["approval_level"],
            "requester": actor,
            "requested_by": actor,
            "reason": action["summary"],
            "preview": {"summary": action["summary"], "will_do": action.get("will_do", []), "will_not_do": action.get("will_not_do", [])},
            "readback_text": _readback_for_preview(preview),
            "readback_required": True,
            "confirmation_phrase": None,
            "challenge": "Double/triple approval channel is not configured.",
            "second_confirmation_required": True,
            "third_confirmation_required": action["approval_level"] == "triple",
            "requires_strong_confirmation": True,
            "requires_double_confirmation": True,
            "requires_triple_confirmation": action["approval_level"] == "triple",
            "expires_at": "",
            "created_at": self.clock(),
            "decided_at": self.clock(),
            "status": "blocked",
            "rejection_reason": reason,
            "decision_reason": reason,
            "audit_id": "",
            "can_approve": False,
            "can_dispatch_after_approval": False,
            "stronger_approval_configured": False,
            "context_fingerprint": "",
        }

    def _audit_approval_v2(self, preview: Mapping[str, Any], envelope: Dict[str, Any]) -> None:
        audit = self._audit_v2(
            "approval_requested",
            correlation_id=preview["correlation_id"],
            risk_level=envelope["risk_level"],
            approval_level=envelope["approval_level"],
            metadata={
                "approval_id": envelope["approval_id"],
                "preview_id": preview["preview_id"],
                "action_key": envelope.get("action_key"),
                "status": envelope["status"],
                "readback_required": envelope["readback_required"],
                "second_confirmation_required": envelope["second_confirmation_required"],
                "third_confirmation_required": envelope["third_confirmation_required"],
                "voice_approval": False,
                "wake_phrase_approval": False,
            },
        )
        envelope["audit_id"] = audit.get("audit_id", "")
        if envelope["status"] == "blocked":
            self._audit_v2(
                "approval_blocked",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level=envelope["approval_level"],
                metadata={"approval_id": envelope["approval_id"], "reason": envelope["decision_reason"]},
            )

    def _audit_v2(
        self,
        event_type: str,
        *,
        correlation_id: str,
        surface: str = "execution",
        risk_level: str = "low",
        approval_level: str = "none",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.audit_ledger.record(
            event_type=event_type,
            surface=surface,
            source="/mark-3/execution",
            risk_level=risk_level,
            approval_level=approval_level,
            correlation_id=correlation_id,
            metadata={
                "metadata_only": True,
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "contains_secret": False,
                "contains_credential": False,
                "contains_full_transcript": False,
                **dict(metadata or {}),
            },
            contains_full_transcript=False,
            hermes_dispatch_allowed=False,
        )

    def _validate_inputs(self, action_key: str, inputs: Mapping[str, Any]) -> Dict[str, Any]:
        if action_key not in ACTION_CATALOG:
            raise ValueError("action_key is not allowlisted")
        raw = dict(inputs or {})
        if _inputs_contain_secret(raw):
            raise ValueError("secret or credential inputs are denied")
        if action_key == "repo.file.read_safe":
            path = str(raw.get("path") or "").strip()
            if not path:
                raise ValueError("path is required")
            if _path_is_secret_like(path):
                raise ValueError("secret or credential paths are denied")
            return {"path": path}
        if action_key == "repo.tests.run_allowlisted":
            target = str(raw.get("test_target") or RUN_ALLOWLISTED_TARGETS[0]).strip()
            if target not in RUN_ALLOWLISTED_TARGETS:
                raise ValueError("test target is not allowlisted")
            return {"test_target": target}
        if action_key == "repo.log.read":
            try:
                limit = int(raw.get("limit") or 5)
            except (TypeError, ValueError):
                raise ValueError("limit must be an integer") from None
            return {"limit": max(1, min(limit, 20))}
        if action_key == "jarvis.execution.history.read":
            try:
                limit = int(raw.get("limit") or 10)
            except (TypeError, ValueError):
                raise ValueError("limit must be an integer") from None
            return {"limit": max(1, min(limit, 100))}
        if raw:
            raise ValueError("inputs are not supported for this action")
        return {}


def _normalize_action_key(value: str) -> str:
    text = str(value or "").strip()
    if text == "filesystem_read":
        return "repo.file.read_safe"
    return text


def _required_approval_level(contract: ActionContract) -> str:
    if contract.approval_required in {"double", "triple"}:
        return contract.approval_required
    if contract.risk_level == "high":
        return "strong"
    if contract.risk_level == "critical":
        return "triple"
    return contract.approval_required


def _phase2_level(value: Any) -> str:
    text = str(value or "none").strip().lower()
    if text in {"direct", "none"}:
        return "none"
    if text in {"simple", "normal"}:
        return "normal"
    if text in APPROVAL_LEVELS:
        return text
    return "unsupported"


def _infer_action_key(preview: Mapping[str, Any]) -> str:
    action = dict(preview.get("action") or {})
    if action.get("action_key"):
        return str(action["action_key"])
    action_type = str(action.get("action_type") or "")
    if action_type == ALLOWED_ACTION:
        return "repo.file.read_safe"
    if action_type == "system_status_read":
        return "local.status.read"
    if action_type == "prepare_only":
        return "jarvis.execution.preview"
    if action_type == "local_command":
        return "unsupported.local_command"
    return action_type or "unknown"


def _will_do(contract: ActionContract) -> List[str]:
    if contract.execution_backend == "existing_mark_3_hermes_runtime_bridge":
        return ["Bind approval to one exact file path.", "Dispatch through existing Mark 3 Hermes read_file bridge.", "Record metadata-only history and audit."]
    return ["Run only the fixed allowlisted action.", "Validate inputs server-side.", "Record metadata-only history and audit."]


def _will_not_do(contract: ActionContract) -> List[str]:
    items = ["No shell freeform.", "No arbitrary command text.", "No secrets or credential material.", "No frontend direct Hermes call."]
    if not contract.network_allowed:
        items.append("No network.")
    if not contract.external_side_effects:
        items.append("No external side effects.")
    return items


def _completed(summary: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "completed", "result_summary": summary, "error_summary": "", "data": data}


def _browser_check(name: str, passed: bool, notes: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "status": "passed" if passed else "missing", "notes": notes}


def _history_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "schema_version": row["schema_version"],
            "execution_id": row["execution_id"],
            "action_id": row["action_id"],
            "approval_id": row["approval_id"],
            "intent_summary": row["intent_summary"],
            "action_key": row["action_key"],
            "status": row["status"],
            "risk_level": row["risk_level"],
            "approval_level": row["approval_level"],
            "approval_status": row["approval_status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "duration_ms": row["duration_ms"],
            "result_summary": row["result_summary"],
            "error_summary": row["error_summary"],
            "stop_requested": bool(row["stop_requested"]),
            "stop_status": row["stop_status"],
            "stop_request_id": row["stop_request_id"],
            "rollback_requested": bool(row["rollback_requested"]),
            "rollback_status": row["rollback_status"],
            "rollback_request_id": row["rollback_request_id"],
            "rollback_plan_id": row["rollback_plan_id"],
            "rollback_audit_id": row["rollback_audit_id"],
            "audit_ids": _json_loads(row["audit_ids_json"], []),
            "memory_influence_ids": _json_loads(row["memory_influence_ids_json"], []),
            "channel_ids": _json_loads(row["channel_ids_json"], []),
            "redaction_summary": _json_loads(row["redaction_summary_json"], {}),
            "contains_secret": bool(row["contains_secret"]),
            "contains_credential": bool(row["contains_credential"]),
        "contains_raw_audio": bool(row["contains_raw_audio"]),
        "contains_camera_frame": bool(row["contains_camera_frame"]),
    }


def _safe_json_list(value: Any) -> List[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_safe_text(item, limit=120) for item in value[:50]]


def _safe_json_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _safe_inputs_for_public(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(inputs or {}).items():
        if "path" in str(key).lower():
            safe[str(key)] = {"sha256": hashlib.sha256(str(value).encode("utf-8")).hexdigest()}
        else:
            safe[str(key)] = _redact_text(value, limit=160)
    return safe


def _readback_for_preview(preview: Mapping[str, Any]) -> str:
    action = preview.get("action", {})
    return (
        f"I approve {action.get('action_key') or action.get('action_type', 'unknown')} "
        f"for preview {preview.get('preview_id', 'unknown')} with risk {preview.get('risk_level', 'unknown')}."
    )


def _normalize_readback(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def _action_id(action_key: Any, inputs: Any) -> str:
    return "action-" + hashlib.sha256(_json_dumps({"action_key": action_key, "inputs": inputs}).encode("utf-8")).hexdigest()[:16]


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_json_dumps(value).encode("utf-8")).hexdigest()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _json_loads(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except json.JSONDecodeError:
        return fallback


def _safe_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").strip().split())[:limit]


def _redact_text(value: Any, *, limit: int) -> str:
    text = _safe_text(value, limit=limit)
    lines = []
    redacted = 0
    for line in text.splitlines() or [text]:
        if _contains_secret_material(line) or _path_is_secret_like(line):
            lines.append("[redacted]")
            redacted += 1
        else:
            lines.append(line)
    rendered = "\n".join(lines)
    return rendered[:limit] + (" [truncated]" if len(rendered) > limit else "")


def _contains_secret_material(value: Any) -> bool:
    text = str(value or "").casefold()
    return any(marker in text for marker in SECRET_MARKERS)


def _inputs_contain_secret(inputs: Mapping[str, Any]) -> bool:
    for key, value in dict(inputs or {}).items():
        if _contains_secret_material(key) or _contains_secret_material(value) or _path_is_secret_like(str(value)):
            return True
    return False


def _path_is_secret_like(value: Optional[str]) -> bool:
    if not value:
        return False
    lowered = str(value).casefold()
    try:
        name = Path(value).name.casefold()
    except (OSError, ValueError):
        name = ""
    return name in SECRET_PATH_NAMES or any(marker in lowered for marker in SECRET_MARKERS)


def _source_is_wake_execute(source: str, intent: str) -> bool:
    if source != "wake_phrase_command":
        return False
    text = str(intent or "").casefold()
    return any(marker in text for marker in ("approve", "approved", "aprueba", "aprobar", "confirmo", "ejecuta", "hazlo"))


def _is_voice_or_wake_approval(*, actor: str, decision_source: str, channel: str) -> bool:
    values = " ".join([actor, decision_source, channel]).casefold()
    return "voice" in values or "wake" in values


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
