from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from jarvis.approval_audit import ApprovalAuditEventType, ApprovalAuditTrail


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ApprovalKind(str, Enum):
    NORMAL = "normal"
    STRONG = "strong"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRecord:
    approval_id: str
    action_type: str
    risk_level: RiskLevel
    requested_by: str
    reason: str
    context_fingerprint: str
    requested_at: str
    expires_at: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    approval_kind: ApprovalKind = ApprovalKind.NORMAL
    strong_approval_required: bool = False
    user_confirmation_phrase: Optional[str] = None
    approved_at: Optional[str] = None
    revoked_at: Optional[str] = None
    decided_at: Optional[str] = None
    decision_reason: Optional[str] = None
    context_summary: Dict[str, Any] = field(default_factory=dict)
    safe_to_execute: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        self.risk_level = RiskLevel(self.risk_level)
        self.status = ApprovalStatus(self.status)
        self.approval_kind = ApprovalKind(self.approval_kind)
        self.safe_to_execute = False
        self.prepare_only = True

    @property
    def request_id(self) -> str:
        return self.approval_id

    @property
    def action(self) -> str:
        return self.action_type

    @property
    def rationale(self) -> str:
        return self.reason

    @property
    def decision_note(self) -> Optional[str]:
        return self.decision_reason

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        data["status"] = self.status.value
        data["approval_kind"] = self.approval_kind.value
        data["request_id"] = self.approval_id
        data["action"] = self.action_type
        data["rationale"] = self.reason
        data["decision_note"] = self.decision_reason
        return data


ApprovalRequest = ApprovalRecord


@dataclass(frozen=True)
class StrongApprovalPolicy:
    prepare_only: bool = True
    strong_approval_categories: tuple[str, ...] = (
        "production",
        "deploy",
        "money_or_payments",
        "credentials_or_secrets",
        "identity_or_accounts",
        "private_or_personal_data",
        "sensitive_persistent_memory",
        "dependency_installation",
        "shell_or_subprocess",
        "external_calls",
        "email_or_messaging",
        "camera_microphone_or_screen",
        "robot_drone_or_device_control",
        "runtime_policy_or_security_changes",
    )

    def classify(self, context: Dict[str, Any]) -> tuple[RiskLevel, bool, List[str]]:
        normalized = _normalized_context(context)
        text = " ".join(f"{key} {value}".lower() for key, value in normalized.items())
        categories: List[str] = []
        for category, markers in _STRONG_CATEGORY_MARKERS.items():
            if any(_context_truthy(normalized, marker) or marker in text for marker in markers):
                categories.append(category)
        requires_strong = bool(categories)
        risk = RiskLevel.CRITICAL if any(item in categories for item in _CRITICAL_CATEGORIES) else (
            RiskLevel.HIGH if requires_strong else RiskLevel.MEDIUM
        )
        return risk, requires_strong, categories

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "strong_approval_categories": list(self.strong_approval_categories),
            "runtime_execution_enabled": False,
            "side_effects_enabled": False,
            "safe_to_execute": False,
        }


class ApprovalHardeningService:
    """Prepare-only approval state machine. It has no execution callback."""

    def __init__(
        self,
        *,
        audit_trail: Optional[ApprovalAuditTrail] = None,
        strong_policy: Optional[StrongApprovalPolicy] = None,
    ) -> None:
        self.audit_trail = audit_trail or ApprovalAuditTrail()
        self.strong_policy = strong_policy or StrongApprovalPolicy()
        self._records: Dict[str, ApprovalRecord] = {}

    def request(
        self,
        *,
        action_type: str,
        requested_by: str = "jarvis",
        reason: str = "",
        context: Optional[Dict[str, Any]] = None,
        approval_kind: ApprovalKind | str = ApprovalKind.NORMAL,
        expires_in_seconds: int = 900,
        requested_at: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> ApprovalRecord:
        action_type = _required_text(action_type, "action_type")
        requested_by = _required_text(requested_by, "requested_by")
        context = dict(context or {})
        context["action_type"] = action_type
        risk, requires_strong, categories = self.strong_policy.classify(context)
        kind = ApprovalKind(approval_kind)
        approval_id = str(uuid4())
        requested_time = _parse_datetime(requested_at) if requested_at else _now()
        expiry_time = _parse_datetime(expires_at) if expires_at else requested_time + timedelta(seconds=max(1, expires_in_seconds))
        phrase = f"APPROVE {approval_id}" if requires_strong or kind == ApprovalKind.STRONG else None
        record = ApprovalRecord(
            approval_id=approval_id,
            action_type=action_type,
            risk_level=risk,
            requested_by=requested_by,
            reason=_safe_reason(reason),
            context_fingerprint=build_context_fingerprint(context),
            context_summary=build_safe_context_summary(context),
            requested_at=requested_time.isoformat(),
            expires_at=expiry_time.isoformat(),
            approval_kind=kind,
            strong_approval_required=requires_strong,
            user_confirmation_phrase=phrase,
        )
        self._records[approval_id] = record
        self.audit_trail.append(
            ApprovalAuditEventType.APPROVAL_REQUESTED,
            approval_id,
            actor=requested_by,
            summary="Approval requested.",
            metadata={"action_type": action_type, "risk_level": risk.value, "strong_categories": categories},
        )
        return record

    def decide(
        self,
        approval_id: str,
        decision: str,
        *,
        actor: str = "operator",
        reason: str = "",
        confirmation_phrase: Optional[str] = None,
        decided_at: Optional[str] = None,
    ) -> ApprovalRecord:
        record = self.get(approval_id)
        normalized = decision.strip().lower()
        if normalized == "revoked":
            return self.revoke(approval_id, actor=actor, reason=reason, revoked_at=decided_at)
        self.refresh_expiration(record, now=decided_at)
        if record.status != ApprovalStatus.PENDING:
            raise ValueError(f"approval {approval_id} is already {record.status.value}")
        now = (_parse_datetime(decided_at) if decided_at else _now()).isoformat()
        if normalized == "approved":
            if record.approval_kind == ApprovalKind.STRONG and confirmation_phrase != record.user_confirmation_phrase:
                raise ValueError("strong approval confirmation phrase does not match")
            record.status = ApprovalStatus.APPROVED
            record.approved_at = now
            event_type = ApprovalAuditEventType.APPROVAL_APPROVED
        elif normalized == "rejected":
            record.status = ApprovalStatus.REJECTED
            event_type = ApprovalAuditEventType.APPROVAL_REJECTED
        else:
            raise ValueError("decision must be approved, rejected, or revoked")
        record.decided_at = now
        record.decision_reason = _safe_reason(reason)
        self.audit_trail.append(event_type, approval_id, actor=actor, summary=f"Approval {normalized}.")
        return record

    def revoke(self, approval_id: str, *, actor: str = "operator", reason: str = "", revoked_at: Optional[str] = None) -> ApprovalRecord:
        record = self.get(approval_id)
        if record.status != ApprovalStatus.APPROVED:
            raise ValueError("only approved approvals can be revoked")
        record.status = ApprovalStatus.REVOKED
        record.revoked_at = (_parse_datetime(revoked_at) if revoked_at else _now()).isoformat()
        record.decision_reason = _safe_reason(reason)
        self.audit_trail.append(ApprovalAuditEventType.APPROVAL_REVOKED, approval_id, actor=actor, summary="Approval revoked.")
        return record

    def refresh_expiration(self, record: ApprovalRecord, *, now: Optional[str] = None) -> ApprovalRecord:
        current = _parse_datetime(now) if now else _now()
        if record.status in {ApprovalStatus.PENDING, ApprovalStatus.APPROVED} and current >= _parse_datetime(record.expires_at):
            record.status = ApprovalStatus.EXPIRED
            self.audit_trail.append(
                ApprovalAuditEventType.APPROVAL_EXPIRED,
                record.approval_id,
                summary="Approval expired.",
            )
        return record

    def get(self, approval_id: str) -> ApprovalRecord:
        try:
            return self._records[approval_id]
        except KeyError as exc:
            raise KeyError(f"Approval request not found: {approval_id}") from exc

    def list_records(self) -> List[ApprovalRecord]:
        return list(self._records.values())

    def status(self) -> Dict[str, Any]:
        for record in self._records.values():
            self.refresh_expiration(record)
        return {
            "prepare_only": True,
            "approval_hardening_available": True,
            "approval_audit_available": True,
            "strong_approval_policy_available": True,
            "permission_gates_available": True,
            "runtime_execution_enabled": False,
            "side_effects_enabled": False,
            "safe_to_execute": False,
            "record_count": len(self._records),
        }


def build_context_fingerprint(context: Dict[str, Any]) -> str:
    canonical = json.dumps(build_safe_context_summary(context), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_safe_context_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    source = _normalized_context(context)
    summary: Dict[str, Any] = {}
    for key in _FINGERPRINT_FIELDS:
        if key not in source:
            continue
        value = source[key]
        if key in {"command", "target", "user_payload"} or _is_sensitive_key(key):
            summary[key] = _hashed_value(value)
        elif isinstance(value, (dict, list, tuple)):
            summary[key] = _hashed_value(value)
        elif isinstance(value, str):
            summary[key] = _hashed_value(value) if _looks_sensitive(value) or len(value) > 160 else value
        elif value is None or isinstance(value, (bool, int, float)):
            summary[key] = value
        else:
            summary[key] = _hashed_value(value)
    return summary


def _hashed_value(value: Any) -> Dict[str, str]:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True)
    return {"sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


def _normalized_context(context: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {str(key).strip().lower(): value for key, value in dict(context or {}).items()}
    if "payload" in normalized and "user_payload" not in normalized:
        normalized["user_payload"] = normalized["payload"]
    return normalized


def _context_truthy(context: Dict[str, Any], marker: str) -> bool:
    value = context.get(marker)
    if isinstance(value, bool):
        return value
    return bool(value) and str(value).lower() not in {"false", "none", "0", "unknown"}


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(marker in normalized for marker in ("secret", "token", "password", "credential", ".env", "private_key"))


def _looks_sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in (".env", "api_key", "authorization:", "bearer ", "password", "secret", "token"))


def _safe_reason(value: Any) -> str:
    text = " ".join(str(value or "").strip().split())
    return "[redacted sensitive reason]" if _looks_sensitive(text) else text[:240]


def _required_text(value: Any, name: str) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        raise ValueError(f"{name} must be a non-empty string")
    return text


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


_FINGERPRINT_FIELDS: Iterable[str] = (
    "action_type",
    "target",
    "command",
    "amount",
    "budget",
    "environment",
    "production",
    "production_flag",
    "tool_name",
    "secret_access",
    "secret_access_flag",
    "external_call",
    "external_call_flag",
    "user_payload",
)
_CRITICAL_CATEGORIES = {"production", "money_or_payments", "credentials_or_secrets", "runtime_policy_or_security_changes"}
_STRONG_CATEGORY_MARKERS: Dict[str, tuple[str, ...]] = {
    "production": ("production", "production_flag"),
    "deploy": ("deploy", "deployment"),
    "money_or_payments": ("payment", "payments", "money", "amount", "budget", "spend", "payout", "refund"),
    "credentials_or_secrets": ("secret_access", "secret_access_flag", "secret", "credential", ".env", "token"),
    "identity_or_accounts": ("identity", "account", "impersonation"),
    "private_or_personal_data": ("private_data", "personal_data", "private", "pii"),
    "sensitive_persistent_memory": ("memory_activation", "persistent_memory", "sensitive_memory"),
    "dependency_installation": ("install", "dependency", "dependencies"),
    "shell_or_subprocess": ("command", "shell", "subprocess"),
    "external_calls": ("external_call", "external_call_flag", "network"),
    "email_or_messaging": ("email", "messaging", "message", "send"),
    "camera_microphone_or_screen": ("camera", "microphone", "screen", "capture"),
    "robot_drone_or_device_control": ("robot", "drone", "device_control", "physical"),
    "runtime_policy_or_security_changes": ("runtime_change", "policy_change", "security_change", "runtime", "policy", "security"),
}
