from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4


class ApprovalAuditEventType(str, Enum):
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_REVOKED = "approval_revoked"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_CONTEXT_MISMATCH = "approval_context_mismatch"
    APPROVAL_GATE_DENIED = "approval_gate_denied"
    APPROVAL_GATE_ALLOWED_FOR_FUTURE_EXECUTION = "approval_gate_allowed_for_future_execution"


@dataclass(frozen=True)
class ApprovalAuditEvent:
    event_id: str
    event_type: ApprovalAuditEventType
    approval_id: str
    actor: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    prepare_only: bool = True
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ApprovalAuditTrail:
    """In-memory append-only audit trail for approval control-plane events."""

    def __init__(self) -> None:
        self._events: List[ApprovalAuditEvent] = []

    def append(
        self,
        event_type: ApprovalAuditEventType,
        approval_id: str,
        *,
        actor: str = "jarvis",
        summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> ApprovalAuditEvent:
        safe_metadata, redacted_fields = redact_sensitive_data(metadata or {})
        event = ApprovalAuditEvent(
            event_id=str(uuid4()),
            event_type=ApprovalAuditEventType(event_type),
            approval_id=str(approval_id),
            actor=_safe_text(actor, "jarvis"),
            created_at=created_at or _now_iso(),
            summary=_redact_text(summary)[:240],
            metadata=safe_metadata,
            redacted_fields=redacted_fields,
        )
        self._events.append(event)
        return event

    def list_events(self, approval_id: Optional[str] = None) -> List[ApprovalAuditEvent]:
        if approval_id is None:
            return list(self._events)
        return [event for event in self._events if event.approval_id == approval_id]

    def preview(self, approval_id: Optional[str] = None) -> Dict[str, Any]:
        events = self.list_events(approval_id)
        return {
            "prepare_only": True,
            "append_only": True,
            "external_persistence_enabled": False,
            "safe_to_execute": False,
            "events": [event.to_dict() for event in events],
        }


def redact_sensitive_data(value: Any, path: str = "") -> tuple[Any, List[str]]:
    redacted: List[str] = []
    if isinstance(value, dict):
        safe: Dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path}.{key_text}" if path else key_text
            if _is_sensitive_key(key_text):
                safe[key_text] = "[redacted]"
                redacted.append(item_path)
            else:
                safe_item, item_redacted = redact_sensitive_data(item, item_path)
                safe[key_text] = safe_item
                redacted.extend(item_redacted)
        return safe, redacted
    if isinstance(value, (list, tuple)):
        safe_items = []
        for index, item in enumerate(value):
            safe_item, item_redacted = redact_sensitive_data(item, f"{path}[{index}]")
            safe_items.append(safe_item)
            redacted.extend(item_redacted)
        return safe_items, redacted
    if isinstance(value, str):
        return _redact_text(value), redacted
    if value is None or isinstance(value, (bool, int, float)):
        return value, redacted
    return _safe_text(value, "[redacted]"), redacted


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_").replace(" ", "_")
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _redact_text(value: Any) -> str:
    text = _safe_text(value, "")
    lowered = text.lower()
    if any(marker in lowered for marker in _SENSITIVE_TEXT_MARKERS):
        return "[redacted sensitive text]"
    return text


def _safe_text(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    return text or fallback


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_SENSITIVE_KEY_MARKERS: Iterable[str] = (
    ".env",
    "api_key",
    "authorization",
    "cookie",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)
_SENSITIVE_TEXT_MARKERS: Iterable[str] = (
    ".env",
    "api_key",
    "authorization:",
    "bearer ",
    "password",
    "private_key",
    "secret",
    "token",
)
