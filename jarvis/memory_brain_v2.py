from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.persistent_audit import PersistentAuditLedger


MEMORY_BRAIN_V2_SCHEMA_VERSION = "jarvis.memory_brain_v2.v1"
MEMORY_BRAIN_V2_DB_RELATIVE_PATH = Path(".jarvis") / "memory_brain_v2" / "memory_brain_v2.sqlite3"

MEMORY_TYPES = {"entity", "fact", "preference", "decision", "project", "contradiction"}
CONFIDENCE_LEVELS = {"low", "medium", "high", "unknown"}
SENSITIVITY_LEVELS = {"normal", "private", "sensitive"}
STATUSES = {"proposed", "reviewed", "approved", "active", "deactivated", "rejected", "superseded", "forgotten", "deleted"}

_SECRET_TEXT_MARKERS: Iterable[str] = (
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
    "secret",
    "sk-",
    "token",
)

_SENSITIVE_ATTRIBUTE_MARKERS: Iterable[str] = (
    "biometric",
    "biometrico",
    "biométrico",
    "face id",
    "fingerprint",
    "health",
    "medical",
    "political",
    "politico",
    "político",
    "religion",
    "religión",
    "religious",
    "sexual",
    "salud",
)

_PRIVATE_MEMORY_MARKERS: Iterable[str] = (
    "bank",
    "banco",
    "card",
    "family",
    "familia",
    "private",
    "privado",
    "tarjeta",
)


class MemoryBrainV2Store:
    """Local explainable memory store. Memory never grants permissions."""

    def __init__(
        self,
        *,
        base_dir: str | Path | None = None,
        db_path: str | Path | None = None,
        audit_ledger: PersistentAuditLedger | None = None,
        clock: Any = None,
        id_factory: Any = None,
    ) -> None:
        if db_path is not None and base_dir is not None:
            raise ValueError("Use either db_path or base_dir, not both.")
        self.audit_ledger = audit_ledger
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._lock = RLock()
        self._persistent = db_path is not None or base_dir is not None
        self._base_dir = Path(base_dir) if base_dir is not None else None
        self._db_path = Path(db_path) if db_path is not None else (
            self._base_dir / "memory_brain_v2" / "memory_brain_v2.sqlite3" if self._base_dir else None
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
    def from_environment(cls, *, audit_ledger: PersistentAuditLedger | None = None) -> "MemoryBrainV2Store":
        base_dir = os.environ.get("JARVIS_LOCAL_STATE_DIR") or os.environ.get("JARVIS_STATE_DIR")
        if base_dir:
            return cls(base_dir=base_dir, audit_ledger=audit_ledger)
        return cls(audit_ledger=audit_ledger)

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    def close(self) -> None:
        self._conn.close()

    def propose_entity(self, *, name: str, **values: Any) -> Dict[str, Any]:
        return self.propose_memory(memory_type="entity", entity_name=name, subject=name, **values)

    def propose_fact(self, *, subject: str, predicate: str = "is", object_summary: str = "unknown", **values: Any) -> Dict[str, Any]:
        content = values.pop("content_summary", None) or f"{subject} {predicate} {object_summary}"
        return self.propose_memory(
            memory_type="fact",
            subject=subject,
            predicate=predicate,
            object_summary=object_summary,
            content_summary=content,
            **values,
        )

    def propose_preference(self, *, subject: str, preference: str, **values: Any) -> Dict[str, Any]:
        content = values.pop("content_summary", None) or f"{subject} prefers {preference}"
        return self.propose_memory(
            memory_type="preference",
            subject=subject,
            predicate="prefers",
            object_summary=preference,
            content_summary=content,
            **values,
        )

    def propose_decision(self, *, project: str, decision: str, **values: Any) -> Dict[str, Any]:
        content = values.pop("content_summary", None) or f"{project}: {decision}"
        return self.propose_memory(
            memory_type="decision",
            entity_name=project,
            subject=project,
            predicate="decision",
            object_summary=decision,
            content_summary=content,
            **values,
        )

    def propose_project(self, *, project: str, summary: str = "unknown", **values: Any) -> Dict[str, Any]:
        return self.propose_memory(
            memory_type="project",
            entity_name=project,
            subject=project,
            predicate="summary",
            object_summary=summary,
            content_summary=values.pop("content_summary", None) or f"{project}: {summary}",
            **values,
        )

    def propose_memory(
        self,
        *,
        memory_type: str,
        content_summary: str,
        entity_name: str = "unknown",
        subject: str = "unknown",
        predicate: str = "unknown",
        object_summary: str = "unknown",
        provenance: Mapping[str, Any] | None = None,
        confidence: str = "unknown",
        sensitivity: str = "normal",
        valid_from: str | None = None,
        source: str = "unknown",
        reason_to_remember: str = "unknown",
        influence_summary: str = "unknown",
        why_used: str = "unknown",
        explicit_user_request: bool = False,
        approved: bool = False,
        active: bool = False,
        correlation_id: str | None = None,
        supersedes_memory_id: str | None = None,
    ) -> Dict[str, Any]:
        memory_type = _choice(memory_type, MEMORY_TYPES, "fact")
        clean_values = {
            "content_summary": _clean_text(content_summary, "unknown", limit=700),
            "entity_name": _clean_text(entity_name, "unknown", limit=200),
            "subject": _clean_text(subject, "unknown", limit=240),
            "predicate": _clean_text(predicate, "unknown", limit=120),
            "object_summary": _clean_text(object_summary, "unknown", limit=500),
            "source": _clean_text(source, "unknown", limit=160),
            "reason_to_remember": _clean_text(reason_to_remember, "unknown", limit=500),
            "influence_summary": _clean_text(influence_summary, "unknown", limit=500),
            "why_used": _clean_text(why_used, "unknown", limit=500),
        }
        _reject_secret_material(clean_values.values())
        contains_sensitive_attribute = _contains_any(clean_values.values(), _SENSITIVE_ATTRIBUTE_MARKERS)
        if contains_sensitive_attribute and not explicit_user_request:
            raise ValueError("Sensitive attribute memory requires an explicit user request.")
        derived_sensitivity = _derive_sensitivity(sensitivity, clean_values.values(), contains_sensitive_attribute)
        safe_provenance = _safe_provenance(provenance)
        _reject_secret_material(_flatten_values(safe_provenance))
        now = self.clock()
        review_required = True
        approval_required = derived_sensitivity in {"private", "sensitive"} or contains_sensitive_attribute
        approved = bool(approved and not approval_required)
        active = bool(active and approved and not approval_required)
        status = "approved" if approved else "proposed"
        if active:
            status = "active"
        record = {
            "schema_version": MEMORY_BRAIN_V2_SCHEMA_VERSION,
            "memory_id": f"mem-{self.id_factory()}",
            "memory_type": memory_type,
            "status": status,
            "entity_name": clean_values["entity_name"],
            "subject": clean_values["subject"],
            "predicate": clean_values["predicate"],
            "object_summary": clean_values["object_summary"],
            "content_summary": clean_values["content_summary"],
            "provenance": safe_provenance,
            "confidence": _choice(confidence, CONFIDENCE_LEVELS, "unknown"),
            "sensitivity": derived_sensitivity,
            "valid_from": valid_from or now,
            "superseded_at": None,
            "superseded_by": None,
            "supersedes_memory_id": _clean_text(supersedes_memory_id, "", limit=120) or None,
            "created_at": now,
            "updated_at": now,
            "source": clean_values["source"],
            "approved": approved,
            "active": active,
            "forgotten": False,
            "deleted": False,
            "reason_to_remember": clean_values["reason_to_remember"],
            "influence_summary": clean_values["influence_summary"],
            "why_used": clean_values["why_used"],
            "review_required": review_required,
            "approval_required": approval_required,
            "memory_grants_permission": False,
            "autoload_allowed": False,
        }
        with self._lock:
            self._insert_record(record)
            self._append_audit("memory_proposal_created", record["memory_id"], {"memory_type": memory_type, "sensitivity": derived_sensitivity}, correlation_id=correlation_id)
            return self.get_memory(record["memory_id"])

    def review_memory(self, memory_id: str, *, reviewer: str = "operator", reason: str = "reviewed", correlation_id: str | None = None) -> Dict[str, Any]:
        with self._lock:
            record = self._get_memory_row(memory_id)
            self._update_record(
                memory_id,
                status="reviewed",
                review_required=False,
                updated_at=self.clock(),
            )
            self._append_audit("memory_proposal_reviewed", memory_id, {"reviewer": _clean_text(reviewer, "operator", limit=120), "reason": _clean_text(reason, "reviewed", limit=240)}, correlation_id=correlation_id)
            return self.get_memory(record["memory_id"])

    def approve_memory(self, memory_id: str, *, approver: str = "operator", reason: str = "approved", correlation_id: str | None = None) -> Dict[str, Any]:
        with self._lock:
            record = self._get_memory_row(memory_id)
            if record["deleted"] or record["forgotten"]:
                raise ValueError("Forgotten or deleted memory cannot be approved.")
            self._update_record(
                memory_id,
                status="approved",
                approved=True,
                active=False,
                review_required=False,
                updated_at=self.clock(),
            )
            self._append_audit("memory_proposal_approved", memory_id, {"approver": _clean_text(approver, "operator", limit=120), "reason": _clean_text(reason, "approved", limit=240)}, correlation_id=correlation_id)
            return self.get_memory(memory_id)

    def reject_memory(self, memory_id: str, *, reviewer: str = "operator", reason: str = "rejected", correlation_id: str | None = None) -> Dict[str, Any]:
        with self._lock:
            self._get_memory_row(memory_id)
            self._update_record(
                memory_id,
                status="rejected",
                approved=False,
                active=False,
                updated_at=self.clock(),
            )
            self._append_audit("memory_proposal_rejected", memory_id, {"reviewer": _clean_text(reviewer, "operator", limit=120), "reason": _clean_text(reason, "rejected", limit=240)}, correlation_id=correlation_id)
            return self.get_memory(memory_id)

    def activate_memory(self, memory_id: str, *, actor: str = "operator", reason: str = "activated", correlation_id: str | None = None) -> Dict[str, Any]:
        with self._lock:
            record = self._get_memory_row(memory_id)
            if record["deleted"] or record["forgotten"]:
                raise ValueError("Forgotten or deleted memory cannot be activated.")
            if not record["approved"]:
                raise ValueError("Memory must be approved before activation.")
            self._update_record(
                memory_id,
                status="active",
                active=True,
                updated_at=self.clock(),
                why_used=_clean_text(record["why_used"] if record["why_used"] != "unknown" else reason, "activated", limit=500),
            )
            self._append_audit("memory_proposal_activated", memory_id, {"actor": _clean_text(actor, "operator", limit=120), "reason": _clean_text(reason, "activated", limit=240)}, correlation_id=correlation_id)
            return self.get_memory(memory_id)

    def deactivate_memory(self, memory_id: str, *, actor: str = "operator", reason: str = "deactivated", correlation_id: str | None = None) -> Dict[str, Any]:
        with self._lock:
            self._get_memory_row(memory_id)
            self._update_record(
                memory_id,
                status="deactivated",
                active=False,
                updated_at=self.clock(),
            )
            self._append_audit("memory_proposal_deactivated", memory_id, {"actor": _clean_text(actor, "operator", limit=120), "reason": _clean_text(reason, "deactivated", limit=240)}, correlation_id=correlation_id)
            return self.get_memory(memory_id)

    def supersede_memory(
        self,
        memory_id: str,
        *,
        new_content_summary: str,
        reason: str = "newer evidence supersedes old memory",
        source: str = "operator_review",
        correlation_id: str | None = None,
    ) -> Dict[str, Any]:
        with self._lock:
            old = self._get_memory_row(memory_id)
            replacement = self.propose_memory(
                memory_type=old["memory_type"],
                content_summary=new_content_summary,
                entity_name=old["entity_name"],
                subject=old["subject"],
                predicate=old["predicate"],
                object_summary=new_content_summary,
                provenance={"source_memory_id": memory_id, "evidence_state": "operator_review"},
                confidence="unknown",
                sensitivity=old["sensitivity"],
                source=source,
                reason_to_remember=reason,
                influence_summary="Replacement proposal created after contradiction review.",
                supersedes_memory_id=memory_id,
                correlation_id=correlation_id,
            )
            now = self.clock()
            self._update_record(
                memory_id,
                status="superseded",
                active=False,
                superseded_at=now,
                superseded_by=replacement["memory_id"],
                updated_at=now,
            )
            contradiction = self.propose_memory(
                memory_type="contradiction",
                content_summary=f"Contradiction reviewed for {memory_id}; replacement is {replacement['memory_id']}.",
                entity_name=old["entity_name"],
                subject=old["subject"],
                predicate="contradicts",
                object_summary=replacement["memory_id"],
                provenance={"superseded_memory_id": memory_id, "replacement_memory_id": replacement["memory_id"], "evidence_state": "operator_review"},
                confidence="unknown",
                sensitivity="normal",
                source=source,
                reason_to_remember=reason,
                influence_summary="Prevents stale fact from influencing future previews.",
                correlation_id=correlation_id,
            )
            self._append_audit("memory_proposal_deactivated", memory_id, {"reason": "superseded_by_newer_memory", "replacement_memory_id": replacement["memory_id"]}, correlation_id=correlation_id)
            return {
                "superseded_memory": self.get_memory(memory_id),
                "replacement_memory": replacement,
                "contradiction": contradiction,
            }

    def mark_contradiction(
        self,
        *,
        memory_id: str,
        contradicts_memory_id: str,
        reason: str = "contradiction marked for review",
        correlation_id: str | None = None,
    ) -> Dict[str, Any]:
        with self._lock:
            current = self._get_memory_row(memory_id)
            other = self._get_memory_row(contradicts_memory_id)
            contradiction = self.propose_memory(
                memory_type="contradiction",
                content_summary=f"{memory_id} contradicts {contradicts_memory_id}.",
                entity_name=current["entity_name"] if current["entity_name"] != "unknown" else other["entity_name"],
                subject=current["subject"],
                predicate="contradicts",
                object_summary=contradicts_memory_id,
                provenance={"memory_id": memory_id, "contradicts_memory_id": contradicts_memory_id, "evidence_state": "operator_review"},
                confidence="unknown",
                sensitivity="normal",
                source="operator_review",
                reason_to_remember=reason,
                influence_summary="Contradiction prevents blind autoload of conflicting facts.",
                correlation_id=correlation_id,
            )
            return contradiction

    def forget_memory(self, memory_id: str, *, actor: str = "operator", reason: str = "forgotten", delete: bool = False, correlation_id: str | None = None) -> Dict[str, Any]:
        with self._lock:
            self._get_memory_row(memory_id)
            status = "deleted" if delete else "forgotten"
            self._update_record(
                memory_id,
                status=status,
                active=False,
                forgotten=True,
                deleted=delete,
                updated_at=self.clock(),
            )
            self._append_audit(
                "memory_proposal_deleted" if delete else "memory_proposal_forgotten",
                memory_id,
                {"actor": _clean_text(actor, "operator", limit=120), "reason": _clean_text(reason, status, limit=240)},
                correlation_id=correlation_id,
            )
            return self.get_memory(memory_id)

    def delete_memory(self, memory_id: str, *, actor: str = "operator", reason: str = "deleted", correlation_id: str | None = None) -> Dict[str, Any]:
        return self.forget_memory(memory_id, actor=actor, reason=reason, delete=True, correlation_id=correlation_id)

    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        return _row_to_memory(self._get_memory_row(memory_id))

    def list_memories(self, *, limit: int = 100, include_deleted: bool = True) -> List[Dict[str, Any]]:
        limit = max(0, min(int(limit), 500))
        if limit == 0:
            return []
        where = "" if include_deleted else "WHERE deleted = 0"
        rows = self._conn.execute(
            f"SELECT * FROM memories {where} ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_memory(row) for row in rows]

    def audit_events(self, *, limit: int = 100) -> List[Dict[str, Any]]:
        limit = max(0, min(int(limit), 500))
        rows = self._conn.execute(
            "SELECT * FROM memory_audit ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_audit(row) for row in rows]

    def why_remember(self, memory_id: str) -> Dict[str, Any]:
        memory = self.get_memory(memory_id)
        return {
            "memory_id": memory_id,
            "reason_to_remember": memory["reason_to_remember"],
            "provenance": memory["provenance"],
            "confidence": memory["confidence"],
            "sensitivity": memory["sensitivity"],
            "evidence_state": memory["provenance"].get("evidence_state", "unknown"),
            "approved": memory["approved"],
            "active": memory["active"],
            "memory_grants_permission": False,
        }

    def why_used(self, memory_id: str) -> Dict[str, Any]:
        memory = self.get_memory(memory_id)
        return {
            "memory_id": memory_id,
            "why_used": memory["why_used"],
            "influence_summary": memory["influence_summary"],
            "active": memory["active"],
            "used_for_permission": False,
            "autoload_allowed": False,
        }

    def permission_effect(self, memory_id: str | None = None) -> Dict[str, Any]:
        return {
            "memory_id": memory_id,
            "grants_permission": False,
            "can_approve": False,
            "can_execute": False,
            "can_dispatch_hermes": False,
            "reason": "Memory can inform explanations only; JARVIS approval gates remain authoritative.",
        }

    def status(self) -> Dict[str, Any]:
        counts = self._counts()
        return {
            "schema_version": MEMORY_BRAIN_V2_SCHEMA_VERSION,
            "state": {
                "mode": "persistent_explainable_memory_brain_v2" if self._persistent else "in_memory_explainable_memory_brain_v2",
                "available": True,
                "persistent": self._persistent,
                "local_only": True,
                "storage_path": str(self._db_path) if self._db_path else str(MEMORY_BRAIN_V2_DB_RELATIVE_PATH),
                "storage_configured": self._db_path is not None,
                "default_relative_path": str(MEMORY_BRAIN_V2_DB_RELATIVE_PATH),
                "memory_autoload_enabled": False,
                "memory_auto_activation_enabled": False,
                "memory_grants_permission": False,
                "external_persistence_enabled": False,
                "review_required_for_sensitive": True,
                "approval_required_for_sensitive": True,
            },
            "counts": counts,
            "supported_memory_types": sorted(MEMORY_TYPES),
            "safety": {
                "memory_is_not_permission": True,
                "active_memory_does_not_authorize_sensitive_actions": True,
                "sensitive_memory_requires_approval": True,
                "sensitive_memory_auto_activation": False,
                "no_sensitive_autosave": True,
                "no_secret_storage": True,
                "no_credential_storage": True,
                "no_external_llm": True,
                "no_cloud_memory": True,
                "no_vector_db_required": True,
                "no_graph_db_required": True,
                "autoload_enabled": False,
                "execution_enabled": False,
                "hermes_dispatch_allowed": False,
            },
            "source_endpoint": "/mark-3/memory-brain/status",
            "read_only": True,
        }

    def preview(self, *, limit: int = 10) -> Dict[str, Any]:
        memories = self.list_memories(limit=limit)
        counts = self._counts()
        active = [memory for memory in memories if memory["active"] and not memory["deleted"] and not memory["forgotten"]]
        pending = [memory for memory in memories if memory["review_required"] or (memory["approval_required"] and not memory["approved"])]
        forgotten_deleted = [memory for memory in memories if memory["forgotten"] or memory["deleted"]]
        return {
            "schema_version": MEMORY_BRAIN_V2_SCHEMA_VERSION,
            "counts": counts,
            "entities": [memory for memory in memories if memory["memory_type"] == "entity"],
            "facts": [memory for memory in memories if memory["memory_type"] == "fact"],
            "preferences": [memory for memory in memories if memory["memory_type"] == "preference"],
            "decisions": [memory for memory in memories if memory["memory_type"] == "decision"],
            "projects": [memory for memory in memories if memory["memory_type"] == "project"],
            "contradictions": [memory for memory in memories if memory["memory_type"] == "contradiction"],
            "active_memories": active,
            "pending_review": pending,
            "forgotten_deleted": forgotten_deleted,
            "explanation_preview": {
                "why_jarvis_remembers": [
                    memory["reason_to_remember"]
                    for memory in memories
                    if memory["reason_to_remember"] != "unknown"
                ][:5] or ["No approved persistent memory has evidence yet; unknown is preserved."],
                "what_memory_influenced": [
                    memory["influence_summary"]
                    for memory in active
                    if memory["influence_summary"] != "unknown"
                ][:5] or ["No active memory influenced this preview."],
                "pending_approval": [
                    {
                        "memory_id": memory["memory_id"],
                        "memory_type": memory["memory_type"],
                        "sensitivity": memory["sensitivity"],
                        "approval_required": memory["approval_required"],
                        "review_required": memory["review_required"],
                    }
                    for memory in pending
                ][:5],
            },
            "permission_effect": self.permission_effect(),
            "audit": {
                "event_count": counts["audit_events"],
                "events": self.audit_events(limit=limit),
            },
            "read_only": True,
            "source_endpoint": "/mark-3/memory-brain/preview",
        }

    def _initialize(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schema_version TEXT NOT NULL,
                memory_id TEXT NOT NULL UNIQUE,
                memory_type TEXT NOT NULL,
                status TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_summary TEXT NOT NULL,
                content_summary TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                confidence TEXT NOT NULL,
                sensitivity TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                superseded_at TEXT,
                superseded_by TEXT,
                supersedes_memory_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 0,
                forgotten INTEGER NOT NULL DEFAULT 0,
                deleted INTEGER NOT NULL DEFAULT 0,
                reason_to_remember TEXT NOT NULL,
                influence_summary TEXT NOT NULL,
                why_used TEXT NOT NULL,
                review_required INTEGER NOT NULL DEFAULT 1,
                approval_required INTEGER NOT NULL DEFAULT 0,
                memory_grants_permission INTEGER NOT NULL DEFAULT 0,
                autoload_allowed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                memory_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                metadata_only INTEGER NOT NULL DEFAULT 1,
                safe_to_execute INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_status ON memories(status)")
        self._conn.commit()

    def _insert_record(self, record: Mapping[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO memories (
                schema_version, memory_id, memory_type, status, entity_name, subject,
                predicate, object_summary, content_summary, provenance_json, confidence,
                sensitivity, valid_from, superseded_at, superseded_by, supersedes_memory_id,
                created_at, updated_at, source, approved, active, forgotten, deleted,
                reason_to_remember, influence_summary, why_used, review_required,
                approval_required, memory_grants_permission, autoload_allowed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["schema_version"],
                record["memory_id"],
                record["memory_type"],
                record["status"],
                record["entity_name"],
                record["subject"],
                record["predicate"],
                record["object_summary"],
                record["content_summary"],
                _json_dumps(record["provenance"]),
                record["confidence"],
                record["sensitivity"],
                record["valid_from"],
                record["superseded_at"],
                record["superseded_by"],
                record["supersedes_memory_id"],
                record["created_at"],
                record["updated_at"],
                record["source"],
                int(record["approved"]),
                int(record["active"]),
                int(record["forgotten"]),
                int(record["deleted"]),
                record["reason_to_remember"],
                record["influence_summary"],
                record["why_used"],
                int(record["review_required"]),
                int(record["approval_required"]),
                0,
                0,
            ),
        )
        self._conn.commit()

    def _update_record(self, memory_id: str, **updates: Any) -> None:
        allowed = {
            "status",
            "approved",
            "active",
            "forgotten",
            "deleted",
            "review_required",
            "approval_required",
            "updated_at",
            "superseded_at",
            "superseded_by",
            "why_used",
        }
        filtered = {key: value for key, value in updates.items() if key in allowed}
        if not filtered:
            return
        assignments = ", ".join(f"{key} = ?" for key in filtered)
        values = [int(value) if isinstance(value, bool) else value for value in filtered.values()]
        values.append(memory_id)
        self._conn.execute(f"UPDATE memories SET {assignments} WHERE memory_id = ?", values)
        self._conn.commit()

    def _get_memory_row(self, memory_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE memory_id = ?",
            (_clean_text(memory_id, "", limit=160),),
        ).fetchone()
        if row is None:
            raise KeyError(memory_id)
        return row

    def _append_audit(self, event_type: str, memory_id: str, metadata: Mapping[str, Any], *, correlation_id: str | None = None) -> None:
        safe_metadata = {
            "memory_id": _clean_text(memory_id, "unknown", limit=160),
            "metadata_only": True,
            **{_clean_text(key, "key", limit=80): _safe_metadata_value(value) for key, value in dict(metadata).items()},
        }
        event_id = f"memory-audit-{self.id_factory()}"
        created_at = self.clock()
        self._conn.execute(
            """
            INSERT INTO memory_audit (event_id, event_type, memory_id, created_at, metadata_json, metadata_only, safe_to_execute)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, event_type, memory_id, created_at, _json_dumps(safe_metadata), 1, 0),
        )
        self._conn.commit()
        if self.audit_ledger is not None:
            self.audit_ledger.record(
                event_type=event_type,
                surface="memory_brain_v2",
                source="/mark-3/memory-brain",
                risk_level="memory_privacy",
                approval_level="simple" if event_type in {"memory_proposal_approved", "memory_proposal_activated"} else "direct",
                correlation_id=correlation_id,
                metadata=safe_metadata,
            )

    def _counts(self) -> Dict[str, int]:
        rows = self._conn.execute(
            "SELECT memory_type, status, active, review_required, forgotten, deleted FROM memories"
        ).fetchall()
        counts = {
            "entities": 0,
            "facts": 0,
            "preferences": 0,
            "decisions": 0,
            "projects": 0,
            "contradictions": 0,
            "active_memories": 0,
            "pending_review": 0,
            "forgotten_deleted": 0,
            "approved": 0,
            "rejected": 0,
            "total": len(rows),
            "audit_events": int(self._conn.execute("SELECT COUNT(*) FROM memory_audit").fetchone()[0]),
        }
        plural = {
            "entity": "entities",
            "fact": "facts",
            "preference": "preferences",
            "decision": "decisions",
            "project": "projects",
            "contradiction": "contradictions",
        }
        for row in rows:
            counts[plural.get(row["memory_type"], "facts")] += 1
            if row["active"]:
                counts["active_memories"] += 1
            if row["review_required"]:
                counts["pending_review"] += 1
            if row["forgotten"] or row["deleted"]:
                counts["forgotten_deleted"] += 1
            if row["status"] == "approved":
                counts["approved"] += 1
            if row["status"] == "rejected":
                counts["rejected"] += 1
        return counts


def _row_to_memory(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "schema_version": row["schema_version"],
        "memory_id": row["memory_id"],
        "memory_type": row["memory_type"],
        "status": row["status"],
        "entity_name": row["entity_name"],
        "subject": row["subject"],
        "predicate": row["predicate"],
        "object_summary": row["object_summary"],
        "content_summary": row["content_summary"],
        "provenance": _json_loads(row["provenance_json"]),
        "confidence": row["confidence"],
        "sensitivity": row["sensitivity"],
        "valid_from": row["valid_from"],
        "superseded_at": row["superseded_at"],
        "superseded_by": row["superseded_by"],
        "supersedes_memory_id": row["supersedes_memory_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "source": row["source"],
        "approved": bool(row["approved"]),
        "active": bool(row["active"]),
        "forgotten": bool(row["forgotten"]),
        "deleted": bool(row["deleted"]),
        "reason_to_remember": row["reason_to_remember"],
        "influence_summary": row["influence_summary"],
        "why_used": row["why_used"],
        "review_required": bool(row["review_required"]),
        "approval_required": bool(row["approval_required"]),
        "memory_grants_permission": bool(row["memory_grants_permission"]),
        "autoload_allowed": bool(row["autoload_allowed"]),
    }


def _row_to_audit(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "event_id": row["event_id"],
        "event_type": row["event_type"],
        "memory_id": row["memory_id"],
        "created_at": row["created_at"],
        "metadata": _json_loads(row["metadata_json"]),
        "metadata_only": bool(row["metadata_only"]),
        "safe_to_execute": bool(row["safe_to_execute"]),
    }


def _safe_provenance(provenance: Mapping[str, Any] | None) -> Dict[str, Any]:
    values = dict(provenance or {})
    source = _clean_text(values.get("source"), values.get("source_id", "unknown"), limit=200)
    evidence_state = _clean_text(values.get("evidence_state"), "unknown", limit=120)
    evidence = values.get("evidence", "unknown")
    if not evidence:
        evidence = "unknown"
    return {
        "source": source,
        "source_id": _clean_text(values.get("source_id"), "unknown", limit=200),
        "evidence_state": evidence_state,
        "evidence": _safe_metadata_value(evidence),
    }


def _safe_metadata_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {_clean_text(key, "key", limit=80): _safe_metadata_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_metadata_value(item) for item in value[:20]]
    if isinstance(value, tuple):
        return [_safe_metadata_value(item) for item in value[:20]]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    text = _clean_text(value, "unknown", limit=500)
    if _contains_any([text], _SECRET_TEXT_MARKERS):
        raise ValueError("Memory metadata cannot store secret or credential material.")
    return text


def _derive_sensitivity(declared: str, values: Iterable[Any], contains_sensitive_attribute: bool) -> str:
    declared_clean = _choice(declared, SENSITIVITY_LEVELS, "normal")
    if declared_clean == "sensitive" or contains_sensitive_attribute:
        return "sensitive"
    if declared_clean == "private" or _contains_any(values, _PRIVATE_MEMORY_MARKERS):
        return "private"
    return "normal"


def _reject_secret_material(values: Iterable[Any]) -> None:
    if _contains_any(values, _SECRET_TEXT_MARKERS):
        raise ValueError("Memory Brain v2 cannot store secret or credential material.")


def _contains_any(values: Iterable[Any], markers: Iterable[str]) -> bool:
    marker_list = list(markers)
    for value in values:
        text = str(value or "").lower()
        if any(marker in text for marker in marker_list):
            return True
    return False


def _flatten_values(value: Any) -> List[Any]:
    flattened: List[Any] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            flattened.append(key)
            flattened.extend(_flatten_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            flattened.extend(_flatten_values(item))
    else:
        flattened.append(value)
    return flattened


def _choice(value: Any, allowed: set[str], fallback: str) -> str:
    normalized = _clean_text(value, fallback, limit=80).lower()
    return normalized if normalized in allowed else fallback


def _clean_text(value: Any, fallback: Any, *, limit: int) -> str:
    text = " ".join(str(value if value is not None else fallback).strip().split())
    return (text or str(fallback))[:limit]


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _json_loads(value: str) -> Any:
    return json.loads(value or "{}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
