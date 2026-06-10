from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import ApprovalAuditTrail, redact_sensitive_data
from jarvis.approval_hardening import ApprovalRecord, StrongApprovalPolicy, build_context_fingerprint
from jarvis.permission_gates import PermissionGateResult, evaluate_permission_gate


@dataclass(frozen=True)
class ApprovedMemoryRecord:
    memory_id: str
    memory_type: str
    content_summary: str
    source: str
    created_by: str
    reason: str
    sensitivity_level: str = "normal"
    approved: bool = False
    approval_id: Optional[str] = None
    active: bool = False
    reversible: bool = True
    created_at: str = ""
    approved_at: Optional[str] = None
    activated_at: Optional[str] = None
    expires_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    context_fingerprint: str = ""
    blocked_reasons: List[str] = field(default_factory=list)
    persistent: bool = False
    private_data: bool = False
    external_source: bool = False
    prepare_only: bool = True
    autoload_enabled: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    action_authorization_from_memory_enabled: bool = False

    def __post_init__(self) -> None:
        original_summary = str(self.content_summary or "")
        original_reason = str(self.reason or "")
        original_source = str(self.source or "unknown")
        safe_summary, _ = redact_sensitive_data(original_summary)
        safe_reason, _ = redact_sensitive_data(original_reason)
        safe_source, _ = redact_sensitive_data(original_source)
        object.__setattr__(self, "content_summary", _clean_text(safe_summary)[:500])
        object.__setattr__(self, "reason", _clean_text(safe_reason)[:240])
        object.__setattr__(self, "source", _clean_text(safe_source)[:160])
        object.__setattr__(self, "memory_type", _clean_text(self.memory_type) or "unknown")
        object.__setattr__(self, "created_by", _clean_text(self.created_by) or "jarvis")
        object.__setattr__(self, "sensitivity_level", _sensitivity(self.sensitivity_level))
        object.__setattr__(self, "tags", _clean_list(self.tags))
        blocked = _clean_list(self.blocked_reasons)
        if not _clean_text(safe_summary):
            blocked.append("content summary is empty")
        if any(
            safe != original
            for safe, original in (
                (safe_summary, original_summary),
                (safe_reason, original_reason),
                (safe_source, original_source),
            )
        ):
            blocked.append("sensitive content was redacted")
        object.__setattr__(self, "blocked_reasons", _deduplicate(blocked))
        object.__setattr__(self, "created_at", self.created_at or _now_iso())
        object.__setattr__(self, "reversible", True)
        object.__setattr__(self, "prepare_only", True)
        for name in (
            "autoload_enabled",
            "execution_enabled",
            "side_effects_enabled",
            "action_authorization_from_memory_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "context_fingerprint", build_context_fingerprint(self.activation_context()))

    @property
    def requires_approval(self) -> bool:
        return self.sensitivity_level in {"private", "sensitive"} or self.private_data or self.external_source

    @property
    def requires_strong_approval(self) -> bool:
        return bool(self.persistent and (self.sensitivity_level in {"private", "sensitive"} or self.private_data))

    def activation_context(self) -> Dict[str, Any]:
        context = {
            "action_type": "apply_approved_context",
            "target": self.memory_id,
            "environment": "memory_control_plane",
            "user_payload": {
                "memory_type": self.memory_type,
                "source": self.source,
                "tags": self.tags,
            },
        }
        if self.private_data or self.sensitivity_level == "private":
            context["private_data"] = True
        if self.persistent and self.sensitivity_level == "sensitive":
            context["sensitive_memory"] = True
        if self.persistent:
            context["persistent_memory"] = True
        if self.external_source:
            context["external_call"] = True
        return context

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["requires_approval"] = self.requires_approval
        data["requires_strong_approval"] = self.requires_strong_approval
        return data


@dataclass(frozen=True)
class MemoryActivationPreview:
    record: ApprovedMemoryRecord
    permission_gate: PermissionGateResult = field(default_factory=PermissionGateResult)
    ready_for_activation: bool = False
    would_activate: bool = False
    active: bool = False
    memory_is_permission: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    prepare_only: bool = True
    autoload_enabled: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocked_reasons", _clean_list(self.blocked_reasons))
        object.__setattr__(self, "audit_events", list(self.audit_events))
        object.__setattr__(self, "would_activate", False)
        object.__setattr__(self, "active", False)
        object.__setattr__(self, "memory_is_permission", False)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "autoload_enabled", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "side_effects_enabled", False)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["record"] = self.record.to_dict()
        data["permission_gate"] = self.permission_gate.to_dict()
        return data


class PersonalMemoryControlPlane:
    """Approved-memory previews with no autoload, persistence, or activation callback."""

    def __init__(self, *, audit_trail: Optional[ApprovalAuditTrail] = None) -> None:
        self.audit_trail = audit_trail or ApprovalAuditTrail()
        self.strong_policy = StrongApprovalPolicy()

    def status(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "approved_memory_records_available": True,
            "memory_activation_preview_available": True,
            "memory_deactivation_preview_available": True,
            "memory_autoload_enabled": False,
            "memory_auto_activation_enabled": False,
            "execution_enabled": False,
            "side_effects_enabled": False,
            "external_persistence_enabled": False,
            "memory_is_not_permission": True,
            "approval_gates_enforced": True,
            "strong_approval_enforced": True,
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "sensitive_memory_requires_approval": True,
            "private_or_sensitive_persistent_memory_requires_strong_approval": True,
            "context_fingerprint_required": True,
            "active_memory_does_not_authorize_sensitive_actions": True,
            "approval_does_not_activate": True,
            "permission_gate_does_not_activate": True,
            "no_secrets": True,
            "no_private_sources_without_approval": True,
            "no_external_sources_without_approval": True,
        }

    def preview_record(self, **values: Any) -> ApprovedMemoryRecord:
        source = dict(values)
        source["memory_id"] = _clean_text(source.get("memory_id")) or str(uuid4())
        source["memory_type"] = source.get("memory_type") or "unknown"
        source["content_summary"] = source.get("content_summary") or ""
        source["source"] = source.get("source") or "operator_provided"
        source["created_by"] = source.get("created_by") or "jarvis"
        source["reason"] = source.get("reason") or ""
        source["tags"] = source.get("tags") or []
        source["blocked_reasons"] = source.get("blocked_reasons") or []
        source["active"] = False
        source["activated_at"] = None
        return ApprovedMemoryRecord(**source)

    def preview_activation(
        self,
        record: ApprovedMemoryRecord,
        *,
        approval: Optional[ApprovalRecord] = None,
        stop_controls_blocked: bool = False,
    ) -> MemoryActivationPreview:
        gate = evaluate_permission_gate(
            record.activation_context(),
            approval,
            policy=self.strong_policy,
            audit_trail=self.audit_trail,
        )
        blocked = list(record.blocked_reasons)
        if not record.approved:
            blocked.append("memory record is not explicitly approved")
        if not record.context_fingerprint:
            blocked.append("context fingerprint missing")
        if record.requires_approval and not gate.allowed:
            blocked.extend(gate.missing_requirements)
        if record.requires_strong_approval and not gate.requires_strong_approval:
            blocked.append("strong approval policy did not classify required memory")
        if stop_controls_blocked:
            blocked.append("memory activation paused by stop controls")
        if record.external_source:
            blocked.append("external source access remains disabled")
        if record.expires_at:
            expiry = _try_parse_datetime(record.expires_at)
            if expiry is None:
                blocked.append("memory expiration is invalid")
            elif datetime.now(timezone.utc) >= expiry:
                blocked.append("memory record is expired")
        blocked = _deduplicate(blocked)
        ready = bool(record.approved and not blocked and (not record.requires_approval or gate.allowed))
        return MemoryActivationPreview(
            record=record,
            permission_gate=gate,
            ready_for_activation=ready,
            blocked_reasons=blocked,
            audit_events=[
                event.to_dict()
                for event in self.audit_trail.list_events(approval.approval_id)
            ] if approval else [],
        )

    def preview_deactivation(self, record: ApprovedMemoryRecord, *, reason: str = "") -> Dict[str, Any]:
        deactivated = replace(record, active=False, activated_at=None)
        safe_reason, _ = redact_sensitive_data(reason)
        return {
            "prepare_only": True,
            "record": deactivated.to_dict(),
            "deactivation_ready": True,
            "would_deactivate": False,
            "reversible": True,
            "execution_enabled": False,
            "side_effects_enabled": False,
            "reason": _clean_text(safe_reason)[:240],
        }


def _sensitivity(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized in {"normal", "private", "sensitive"}:
        return normalized
    return "sensitive" if normalized else "normal"


def _clean_list(values: List[Any]) -> List[str]:
    return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _deduplicate(values: List[str]) -> List[str]:
    return list(dict.fromkeys(_clean_list(values)))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _try_parse_datetime(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
