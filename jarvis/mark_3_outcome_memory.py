from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_3_mission_loop_models import UNKNOWN


FAILURE_CATEGORIES = {
    "tests_hang",
    "missing_dependency",
    "review_network_failure",
    "adapter_not_connected",
    "approval_insufficient",
    "evidence_insufficient",
    "unsupported_tool",
    "scope_error",
    "unknown",
}


@dataclass(frozen=True)
class OutcomeAuditEvent:
    event_id: str
    event_type: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OutcomeRecord:
    outcome_id: str
    mission_id: str
    step_id: str
    candidate_id: str
    goal: str
    tool_used: str
    capability_used: str
    result_status: str
    evidence_state: str
    errors: List[str]
    duration_seconds: Any
    cost: Any
    approval_level: str
    what_worked: str
    what_failed: str
    next_recommended_action: str
    created_at: str
    redacted_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailureRecord:
    failure_id: str
    category: str
    failure_signature: str
    representative_error: str
    affected_capability: str
    scope: str
    suggested_avoidance: str
    first_seen_at: str
    last_seen_at: str
    occurrences: int = 1
    mission_ids: List[str] = field(default_factory=list)
    step_ids: List[str] = field(default_factory=list)
    candidate_ids: List[str] = field(default_factory=list)
    redacted_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OutcomeMemoryStore:
    """In-memory Mark 3 outcome and failure memory with redaction and audit."""

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._outcomes: List[OutcomeRecord] = []
        self._failures_by_key: Dict[str, FailureRecord] = {}
        self._audit: List[OutcomeAuditEvent] = []

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "in_memory_only": True,
            "outcome_count": len(self._outcomes),
            "failure_count": len(self._failures_by_key),
            "audit_event_count": len(self._audit),
            "secrets_stored": False,
            "unknown_values_preserved": True,
            "external_side_effects_enabled": False,
        }

    def record(self, values: Dict[str, Any]) -> Dict[str, Any]:
        safe, redacted = redact_sensitive_data(dict(values or {}))
        now = self.clock()
        result_status = _safe_text(safe.get("result_status"), UNKNOWN)
        errors = _items(safe.get("errors"))
        if result_status.lower() in {"failed", "failure", "error", "blocked"} and not errors:
            errors = [UNKNOWN]
        outcome = OutcomeRecord(
            outcome_id=_safe_text(safe.get("outcome_id"), self.id_factory()),
            mission_id=_safe_text(safe.get("mission_id"), UNKNOWN),
            step_id=_safe_text(safe.get("step_id"), UNKNOWN),
            candidate_id=_safe_text(safe.get("candidate_id"), UNKNOWN),
            goal=_safe_text(safe.get("goal"), UNKNOWN),
            tool_used=_safe_text(safe.get("tool_used", safe.get("tool")), UNKNOWN),
            capability_used=_safe_text(safe.get("capability_used", safe.get("capability")), UNKNOWN),
            result_status=result_status,
            evidence_state=_safe_text(safe.get("evidence_state"), UNKNOWN),
            errors=errors,
            duration_seconds=safe.get("duration_seconds", safe.get("duration", UNKNOWN)),
            cost=safe.get("cost", safe.get("cost_known", UNKNOWN)),
            approval_level=_safe_text(safe.get("approval_level"), UNKNOWN),
            what_worked=_safe_text(safe.get("what_worked"), UNKNOWN),
            what_failed=_safe_text(safe.get("what_failed"), UNKNOWN),
            next_recommended_action=_safe_text(safe.get("next_recommended_action"), UNKNOWN),
            created_at=_safe_text(safe.get("created_at"), now),
            redacted_fields=redacted,
        )
        self._outcomes.append(outcome)
        self._append_audit(
            "outcome_recorded",
            "Outcome memory recorded a redacted mission result.",
            {
                "outcome_id": outcome.outcome_id,
                "mission_id": outcome.mission_id,
                "result_status": outcome.result_status,
                "evidence_state": outcome.evidence_state,
            },
            redacted,
        )
        if outcome.result_status.lower() in {"failed", "failure", "error", "blocked"}:
            self.record_failure({
                "mission_id": outcome.mission_id,
                "step_id": outcome.step_id,
                "candidate_id": outcome.candidate_id,
                "category": safe.get("failure_category"),
                "error": "; ".join(outcome.errors) if outcome.errors else outcome.what_failed,
                "affected_capability": outcome.capability_used,
                "scope": outcome.goal,
                "suggested_avoidance": outcome.next_recommended_action,
            })
        return outcome.to_dict()

    def list_outcomes(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in self._outcomes]

    def get_outcome(self, outcome_id: str) -> Dict[str, Any]:
        for item in self._outcomes:
            if item.outcome_id == outcome_id:
                return item.to_dict()
        raise KeyError(outcome_id)

    def record_failure(self, values: Dict[str, Any]) -> Dict[str, Any]:
        safe, redacted = redact_sensitive_data(dict(values or {}))
        category = _failure_category(safe)
        error = _safe_text(safe.get("error", safe.get("representative_error")), UNKNOWN)
        affected = _safe_text(safe.get("affected_capability", safe.get("capability")), UNKNOWN)
        scope = _safe_text(safe.get("scope"), UNKNOWN)
        key = _failure_key(category, affected, scope, error)
        now = self.clock()
        existing = self._failures_by_key.get(key)
        if existing:
            existing.occurrences += 1
            existing.last_seen_at = now
            _append_unique(existing.mission_ids, _safe_text(safe.get("mission_id"), ""))
            _append_unique(existing.step_ids, _safe_text(safe.get("step_id"), ""))
            _append_unique(existing.candidate_ids, _safe_text(safe.get("candidate_id"), ""))
            existing.redacted_fields = list(dict.fromkeys(existing.redacted_fields + redacted))
            self._append_audit(
                "failure_deduplicated",
                "Repeated failure memory matched an existing signature.",
                {"failure_id": existing.failure_id, "category": existing.category, "occurrences": existing.occurrences},
                redacted,
            )
            return existing.to_dict()
        record = FailureRecord(
            failure_id=_safe_text(safe.get("failure_id"), self.id_factory()),
            category=category,
            failure_signature=key,
            representative_error=error,
            affected_capability=affected,
            scope=scope,
            suggested_avoidance=_safe_text(safe.get("suggested_avoidance"), _avoidance_for(category)),
            first_seen_at=now,
            last_seen_at=now,
            mission_ids=_non_empty([_safe_text(safe.get("mission_id"), "")]),
            step_ids=_non_empty([_safe_text(safe.get("step_id"), "")]),
            candidate_ids=_non_empty([_safe_text(safe.get("candidate_id"), "")]),
            redacted_fields=redacted,
        )
        self._failures_by_key[key] = record
        self._append_audit(
            "failure_recorded",
            "Failure memory recorded a repeatable diagnostic signature.",
            {"failure_id": record.failure_id, "category": record.category},
            redacted,
        )
        return record.to_dict()

    def list_failures(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in self._failures_by_key.values()]

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [item.to_dict() for item in self._audit],
        }

    def _append_audit(
        self,
        event_type: str,
        summary: str,
        metadata: Dict[str, Any],
        redacted_fields: Optional[List[str]] = None,
    ) -> None:
        safe_metadata, audit_redacted = redact_sensitive_data(metadata)
        self._audit.append(OutcomeAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            created_at=self.clock(),
            summary=summary,
            metadata=safe_metadata,
            redacted_fields=list(dict.fromkeys((redacted_fields or []) + audit_redacted)),
        ))


def _failure_category(values: Dict[str, Any]) -> str:
    declared = _safe_text(values.get("category"), "").lower()
    if declared in FAILURE_CATEGORIES:
        return declared
    text = json.dumps(values, sort_keys=True, default=str).lower()
    if "hang" in text or "timeout" in text or "stuck" in text:
        return "tests_hang"
    if "missing dependency" in text or "module not found" in text or "importerror" in text:
        return "missing_dependency"
    if "review" in text and "network" in text:
        return "review_network_failure"
    if "adapter" in text and ("not connected" in text or "unavailable" in text):
        return "adapter_not_connected"
    if "approval" in text:
        return "approval_insufficient"
    if "evidence" in text:
        return "evidence_insufficient"
    if "unsupported" in text or "not supported" in text:
        return "unsupported_tool"
    if "scope error" in text or "outside scope" in text or "outside mission scope" in text:
        return "scope_error"
    return "unknown"


def _failure_key(category: str, affected: str, scope: str, error: str) -> str:
    payload = {
        "category": category,
        "affected": _normalize(affected),
        "scope": _normalize(scope),
        "error": _normalize(error),
    }
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _avoidance_for(category: str) -> str:
    return {
        "tests_hang": "Prefer focused tests first and record exact hang point before retrying the same suite.",
        "missing_dependency": "Check existing environment capabilities before assuming a dependency is installed.",
        "review_network_failure": "Separate code review from network-dependent checks and record network limitations.",
        "adapter_not_connected": "Return setup_required until a real adapter is connected and approved.",
        "approval_insufficient": "Request the exact approval level bound to the exact action before advancing.",
        "evidence_insufficient": "Downgrade claims to unknown/reported until compatible evidence is available.",
        "unsupported_tool": "Do not retry unsupported tools; propose adapter work if the capability is needed.",
        "scope_error": "Re-read allowed scope before proposing another candidate.",
    }.get(category, "Record the blocker and avoid repeating the same diagnostic assumption.")


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_safe_text(item, "") for item in value if _safe_text(item, "")]
    text = _safe_text(value, "")
    return [text] if text else []


def _safe_text(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    return text or fallback


def _normalize(value: Any) -> str:
    return _safe_text(value, UNKNOWN).lower()[:500]


def _non_empty(values: List[str]) -> List[str]:
    return [item for item in values if item]


def _append_unique(values: List[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
